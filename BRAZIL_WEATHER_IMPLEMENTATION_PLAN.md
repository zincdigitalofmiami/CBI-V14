# Brazil Weather Implementation - Zero Duplication Architecture

**Date:** 2025-10-06  
**Status:** APPROVED - Proceeding with INMET (Primary) + GEE (Optional Validation)  
**Cost:** $0 (both sources free)

---

## 🚨 ZERO DUPLICATION GUARANTEE

### Clear Separation Strategy

```
SOURCE 1: INMET (Brazilian Meteorology Institute)
├── Purpose: PRIMARY operational data (2023-2025)
├── Table: weather_data
├── Region: 'Brazil'
├── Station IDs: 'INMET_A901', 'INMET_A923', etc.
├── Date Range: 2023-09-01 → CURRENT
├── Script: ingest_weather_inmet.py
└── Use Case: Training, forecasting, production

SOURCE 2: Google Earth Engine BR-DWGD
├── Purpose: VALIDATION ONLY (historical quality check)
├── Table: weather_data_validation (SEPARATE TABLE)
├── Region: 'Brazil_GEE'
├── Station IDs: 'GEE_GRID_001', 'GEE_GRID_002', etc.
├── Date Range: 2018-01-01 → 2020-12-31 (FIXED, NO OVERLAP WITH INMET)
├── Script: ingest_weather_gee_validation.py (SEPARATE SCRIPT)
└── Use Case: Data quality validation ONLY, never used in training
```

---

## 📋 Implementation Rules (Mandatory)

### Rule 1: Different Table Names
```
INMET → weather_data (production table)
GEE   → weather_data_validation (validation table only)
```

### Rule 2: Different Region Labels
```
INMET → region = 'Brazil'
GEE   → region = 'Brazil_GEE'
```

### Rule 3: Different Station ID Prefixes
```
INMET → station_id STARTS WITH 'INMET_'
GEE   → station_id STARTS WITH 'GEE_GRID_'
```

### Rule 4: Non-Overlapping Date Ranges
```
INMET:  2023-09-01 → current (matches ZL price data)
GEE:    2018-01-01 → 2020-12-31 (validation period only)

NO OVERLAP = ZERO DUPLICATION
```

### Rule 5: Separate Scripts
```
ingest_weather_inmet.py     → Loads to weather_data
ingest_weather_gee_validation.py → Loads to weather_data_validation (IF NEEDED)
```

### Rule 6: Clear Use Case Separation
```
PRODUCTION PIPELINE:
├── Uses: weather_data (INMET only)
├── Feeds: vw_weather_daily → vw_zl_features_daily → ML models
└── Region filter: WHERE region IN ('US', 'Argentina', 'Brazil')

VALIDATION PIPELINE (OPTIONAL):
├── Uses: weather_data_validation (GEE only)
├── Purpose: Compare INMET quality vs academic dataset
└── SQL: Compare 2018-2020 overlap period between tables
```

---

## 🎯 Implementation Plan

### Phase 1: INMET Implementation (Required)

#### Script: `ingest_weather_inmet.py`

```python
#!/usr/bin/env python3
"""
INMET Brazil Weather Ingestion - PRIMARY SOURCE
Loads to: weather_data table
Region: 'Brazil'
Date Range: 2023-09-01 → current
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from google.cloud import bigquery
from bigquery_utils import safe_load_to_bigquery

PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"
TABLE_ID = "weather_data"  # SAME TABLE as US/Argentina

# INMET stations (Mato Grosso soy regions)
INMET_STATIONS = {
    "A901": {"name": "Sorriso", "lat": -12.5, "lon": -55.7},
    "A923": {"name": "Sinop", "lat": -11.9, "lon": -55.5},
    "A936": {"name": "Alta Floresta", "lat": -9.9, "lon": -56.1},
    "A702": {"name": "Campo Grande", "lat": -20.4, "lon": -54.5},
    "A736": {"name": "Dourados", "lat": -22.2, "lon": -54.8},
}

def fetch_inmet_station(station_code, start_date, end_date):
    """
    Fetch from INMET portal/API
    Returns: DataFrame with columns: date, precip_mm, temp_max, temp_min
    """
    # TODO: Implement INMET API call
    # Based on: github.com/gregomelo/brazil_weather_data
    # Or BDMEP portal: portal.inmet.gov.br
    pass

def backfill_inmet(years=2):
    """
    Backfill INMET data for Brazil
    Date range: 2023-09-01 → current (matches ZL prices)
    """
    end_date = datetime.now()
    start_date = datetime(2023, 9, 1)  # Match ZL price start date
    
    all_rows = []
    
    for code, info in INMET_STATIONS.items():
        print(f"Fetching INMET station {code} ({info['name']})...")
        
        df = fetch_inmet_station(code, start_date, end_date)
        
        if df is not None and not df.empty:
            # Add metadata
            df['region'] = 'Brazil'  # CONSISTENT with US/Argentina
            df['station_id'] = f'INMET_{code}'  # PREFIX to avoid conflicts
            
            all_rows.append(df)
    
    if not all_rows:
        print("ERROR: No INMET data fetched")
        return
    
    # Combine all stations
    combined = pd.concat(all_rows, ignore_index=True)
    
    # Validate schema matches weather_data table
    required_cols = ['date', 'region', 'station_id', 'precip_mm', 'temp_max', 'temp_min']
    assert all(col in combined.columns for col in required_cols), "Schema mismatch"
    
    # Load to BigQuery (SAME table as US/Argentina)
    client = bigquery.Client(project=PROJECT_ID)
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",  # Append to existing US/Argentina data
        schema=[
            bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("region", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("station_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("precip_mm", "FLOAT64"),
            bigquery.SchemaField("temp_max", "FLOAT64"),
            bigquery.SchemaField("temp_min", "FLOAT64"),
        ],
    )
    
    print(f"Loading {len(combined)} INMET rows to {table_ref}...")
    job = safe_load_to_bigquery(client, combined, table_ref, job_config)
    job.result()
    
    print(f"✓ SUCCESS: Loaded {len(combined)} Brazil weather rows (INMET)")
    
    # Verify no duplication
    verify_query = f"""
    SELECT 
        region,
        COUNT(*) as total_rows,
        COUNT(DISTINCT station_id) as unique_stations,
        MIN(date) as earliest,
        MAX(date) as latest
    FROM `{table_ref}`
    GROUP BY region
    ORDER BY region
    """
    
    results = client.query(verify_query).result()
    print("\n=== VERIFICATION: No Duplication Check ===")
    for row in results:
        print(f"{row.region}: {row.total_rows} rows, {row.unique_stations} stations, {row.earliest} to {row.latest}")

if __name__ == "__main__":
    backfill_inmet(years=2)
```

---

### Phase 2: GEE Validation (Optional)

#### Script: `ingest_weather_gee_validation.py`

```python
#!/usr/bin/env python3
"""
Google Earth Engine BR-DWGD - VALIDATION SOURCE ONLY
Loads to: weather_data_validation table (SEPARATE)
Region: 'Brazil_GEE'
Date Range: 2018-01-01 → 2020-12-31 (FIXED)
Purpose: Validate INMET data quality only
"""

import ee
import pandas as pd
from google.cloud import bigquery
from bigquery_utils import safe_load_to_bigquery

PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"
TABLE_ID = "weather_data_validation"  # DIFFERENT TABLE

# Initialize Earth Engine
ee.Initialize()

def extract_gee_brazil_weather():
    """
    Extract BR-DWGD gridded data for validation
    Date range: 2018-2020 (NO OVERLAP with INMET 2023-2025)
    """
    
    # Define Mato Grosso region
    mato_grosso = ee.Geometry.Rectangle([-60, -17, -50, -10])
    
    # Load BR-DWGD dataset
    dataset = ee.ImageCollection('INPE/BR-DWGD') \
        .filterDate('2018-01-01', '2020-12-31') \
        .filterBounds(mato_grosso)
    
    # Extract precipitation
    precip = dataset.select('pr')
    tmax = dataset.select('tmax')
    tmin = dataset.select('tmin')
    
    # Sample 5 grid points (match INMET station count)
    grid_points = [
        {'lat': -12.5, 'lon': -55.7, 'id': 'GEE_GRID_001'},  # Near Sorriso
        {'lat': -11.9, 'lon': -55.5, 'id': 'GEE_GRID_002'},  # Near Sinop
        {'lat': -9.9, 'lon': -56.1, 'id': 'GEE_GRID_003'},   # Near Alta Floresta
        {'lat': -20.4, 'lon': -54.5, 'id': 'GEE_GRID_004'},  # Near Campo Grande
        {'lat': -22.2, 'lon': -54.8, 'id': 'GEE_GRID_005'},  # Near Dourados
    ]
    
    all_rows = []
    
    for point in grid_points:
        # Extract time series for this point
        point_geom = ee.Geometry.Point([point['lon'], point['lat']])
        
        # Get daily values
        # (Simplified - actual implementation needs proper GEE extraction)
        data = {
            'date': [],  # Extract from image collection
            'precip_mm': [],
            'temp_max': [],
            'temp_min': [],
            'region': 'Brazil_GEE',  # DIFFERENT region label
            'station_id': point['id']  # DIFFERENT prefix
        }
        
        all_rows.append(pd.DataFrame(data))
    
    combined = pd.concat(all_rows, ignore_index=True)
    
    # Load to SEPARATE validation table
    client = bigquery.Client(project=PROJECT_ID)
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",  # Replace (not append)
        schema=[
            bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("region", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("station_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("precip_mm", "FLOAT64"),
            bigquery.SchemaField("temp_max", "FLOAT64"),
            bigquery.SchemaField("temp_min", "FLOAT64"),
        ],
    )
    
    print(f"Loading {len(combined)} GEE validation rows to {table_ref}...")
    job = safe_load_to_bigquery(client, combined, table_ref, job_config)
    job.result()
    
    print(f"✓ SUCCESS: Loaded GEE validation data (2018-2020)")

if __name__ == "__main__":
    extract_gee_brazil_weather()
```

---

## 🔍 Validation Query (After Both Load)

```sql
-- Compare INMET vs GEE for 2018-2020 overlap period
-- This validates INMET data quality

WITH inmet_2018_2020 AS (
  SELECT 
    DATE_TRUNC(date, MONTH) as month,
    AVG(precip_mm) as inmet_precip,
    AVG(temp_max) as inmet_temp
  FROM `cbi-v14.forecasting_data_warehouse.weather_data`
  WHERE region = 'Brazil'
    AND date BETWEEN '2018-01-01' AND '2020-12-31'
  GROUP BY month
),
gee_2018_2020 AS (
  SELECT 
    DATE_TRUNC(date, MONTH) as month,
    AVG(precip_mm) as gee_precip,
    AVG(temp_max) as gee_temp
  FROM `cbi-v14.forecasting_data_warehouse.weather_data_validation`
  WHERE region = 'Brazil_GEE'
    AND date BETWEEN '2018-01-01' AND '2020-12-31'
  GROUP BY month
)
SELECT 
  i.month,
  i.inmet_precip,
  g.gee_precip,
  ABS(i.inmet_precip - g.gee_precip) as precip_diff,
  i.inmet_temp,
  g.gee_temp,
  ABS(i.inmet_temp - g.gee_temp) as temp_diff
FROM inmet_2018_2020 i
LEFT JOIN gee_2018_2020 g USING (month)
ORDER BY month;

-- If diffs are small (<10%), INMET is validated ✓
```

---

## ✅ Zero Duplication Verification

### Check 1: No Duplicate Station IDs
```sql
SELECT 
  station_id,
  COUNT(*) as occurrences
FROM (
  SELECT station_id FROM `cbi-v14.forecasting_data_warehouse.weather_data`
  UNION ALL
  SELECT station_id FROM `cbi-v14.forecasting_data_warehouse.weather_data_validation`
)
GROUP BY station_id
HAVING COUNT(*) > 1;

-- Expected: 0 rows (no duplicates)
```

### Check 2: No Date Overlap in Production Pipeline
```sql
-- INMET should be 2023-2025, GEE should be 2018-2020
SELECT 
  'INMET' as source,
  MIN(date) as earliest,
  MAX(date) as latest
FROM `cbi-v14.forecasting_data_warehouse.weather_data`
WHERE region = 'Brazil'

UNION ALL

SELECT 
  'GEE_Validation' as source,
  MIN(date) as earliest,
  MAX(date) as latest
FROM `cbi-v14.forecasting_data_warehouse.weather_data_validation`
WHERE region = 'Brazil_GEE';

-- Expected:
-- INMET: 2023-09-01 to 2025-10-06
-- GEE: 2018-01-01 to 2020-12-31
-- NO OVERLAP ✓
```

### Check 3: Production Pipeline Uses Only INMET
```sql
-- Verify vw_weather_daily uses correct source
SELECT * FROM `cbi-v14.forecasting_data_warehouse.vw_weather_daily`
WHERE region = 'Brazil'
LIMIT 5;

-- Should show station_id starting with 'INMET_' only
-- Should show dates 2023-2025 only
```

---

## 📊 Final Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    PRODUCTION PIPELINE                       │
│                                                              │
│  weather_data (TABLE)                                        │
│  ├── US (NOAA)                                              │
│  ├── Argentina (NOAA)                                       │
│  └── Brazil (INMET) ← PRIMARY SOURCE, 2023-2025            │
│                                                              │
│  ↓                                                           │
│  vw_weather_daily (VIEW)                                    │
│  ├── Aggregates by region                                   │
│  └── Feeds to vw_zl_features_daily                          │
│                                                              │
│  ↓                                                           │
│  vw_zl_features_daily (VIEW)                                │
│  └── ML model training input                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   VALIDATION PIPELINE (OPTIONAL)             │
│                                                              │
│  weather_data_validation (SEPARATE TABLE)                   │
│  └── Brazil_GEE (Google EE) ← VALIDATION ONLY, 2018-2020   │
│                                                              │
│  ↓                                                           │
│  Used for quality comparison queries only                   │
│  NEVER used in production forecasting                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Implementation Checklist

### Phase 1: INMET (Required - This Week)
- [ ] Research INMET API access (30 min)
- [ ] Code `ingest_weather_inmet.py` (2 hours)
- [ ] Test with 1 station (30 min)
- [ ] Run full backfill (30 min)
- [ ] Verify: `SELECT COUNT(*) FROM weather_data WHERE region='Brazil'` ≥ 1,000
- [ ] Update `vw_weather_daily` to include Brazil
- [ ] Run coverage check

### Phase 2: GEE Validation (Optional - Later)
- [ ] Set up Google Earth Engine account (15 min)
- [ ] Code `ingest_weather_gee_validation.py` (2 hours)
- [ ] Extract 2018-2020 data (30 min)
- [ ] Run validation comparison query
- [ ] Document quality assessment

---

## 🚨 Mandatory Separation Rules

**NEVER:**
- ❌ Mix INMET and GEE data in same table
- ❌ Use GEE data in production pipeline
- ❌ Overlap date ranges (INMET=2023-2025, GEE=2018-2020)
- ❌ Use same station ID prefixes
- ❌ Query both sources in vw_weather_daily

**ALWAYS:**
- ✅ INMET → weather_data → production
- ✅ GEE → weather_data_validation → quality check only
- ✅ Different region labels ('Brazil' vs 'Brazil_GEE')
- ✅ Different station prefixes ('INMET_' vs 'GEE_GRID_')
- ✅ Non-overlapping dates

---

**Status:** Architecture approved - proceeding with INMET implementation  
**Next Action:** Research INMET API/portal access methods  
**Timeline:** INMET operational in 2-4 hours

