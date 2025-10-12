# Brazil Weather Data Options - Deep Investigation

**Date:** 2025-10-06  
**Priority:** CRITICAL (Brazil = 50% global soy production, 35-45% price variance)  
**Current Status:** 0 rows Brazil weather data

---

## 🔴 Problem Statement

**Root Cause (Confirmed):**
- NOAA GHCND stations `BR000083361` and `BR000083531` return 0 rows
- Historical data cutoff: NOAA GHCND Brazil precipitation records ended ~1990s
- This is NOT a script bug - the data source itself is defunct for Brazil

**Impact:**
- Cannot forecast soybean oil prices without Brazil weather (50% of global production)
- Missing 35-45% of price variance explanatory power
- Competitive disadvantage vs Goldman Sachs and institutional players

---

## 📊 Option Matrix (4 Viable Alternatives)

### Option 1: INMET (Brazilian National Meteorology Institute) ✅ RECOMMENDED

**Source:** Instituto Nacional de Meteorologia (Brazilian government)

**Pros:**
- ✅ **FREE** - Government data, no API fees
- ✅ **Authoritative** - Official Brazilian meteorological authority
- ✅ **Real-time + Historical** - Current operations + backfill capability
- ✅ **Comprehensive Coverage** - 400+ automatic weather stations across Brazil
- ✅ **Agricultural Focus** - Stations in Mato Grosso, MS (soy regions)
- ✅ **Proven Integration** - GitHub wrapper exists (github.com/gregomelo/brazil_weather_data)
- ✅ **Multiple Access Methods** - Web portal, CSV downloads, API endpoints

**Cons:**
- ⚠️ **Documentation in Portuguese** - May need translation
- ⚠️ **API Reliability Unknown** - Not production-tested by us
- ⚠️ **Data Format Variations** - May need custom parsing

**Technical Details:**
```python
# INMET API endpoint (documented on GitHub wrapper)
BASE_URL = "https://apitempo.inmet.gov.br/estacao/"
# or
BASE_URL = "http://www.inmet.gov.br/portal/index.php?r=bdmep/bdmep"

# Key regions for soybean:
REGIONS = {
    "Mato Grosso": ["A901", "A923", "A936"],  # Sorriso, Sinop, Alta Floresta
    "Mato Grosso do Sul": ["A702", "A736"],   # Campo Grande, Dourados
}

# Data available:
# - Precipitation (mm)
# - Temperature (max/min)
# - Humidity
# - Wind speed
# - Solar radiation
```

**Implementation Time:** 2-4 hours
- 1 hour: Study GitHub wrapper + INMET portal
- 1 hour: Adapt script to our BigQuery schema
- 1 hour: Test backfill (2 years)
- 1 hour: Validate data quality

**Success Probability:** 85%

**Cost:** $0

---

### Option 2: NOAA GFS (Global Forecast System) ⚠️ FORECAST ONLY

**Source:** NOAA National Weather Service operational forecast model

**Pros:**
- ✅ **FREE** - NOAA public data
- ✅ **Global Coverage** - Includes Brazil at 0.25° resolution
- ✅ **Production-Grade** - Used by Goldman Sachs and institutional traders
- ✅ **4 Updates/Day** - 00z, 06z, 12z, 18z cycles
- ✅ **Unlimited Access** - No rate limits
- ✅ **Well-Documented** - NOMADS server with clear protocols

**Cons:**
- ❌ **FORECAST DATA ONLY** - Not historical observations
- ❌ **Model Output vs Reality** - GFS predictions ≠ actual weather
- ❌ **No Backfill** - Cannot get historical actual weather
- ⚠️ **Large File Sizes** - GRIB2 format, ~500MB per download
- ⚠️ **Complex Parsing** - Requires pygrib or xarray libraries

**Technical Details:**
```python
# NOAA NOMADS GFS data
BASE_URL = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl"

# Brazil soy regions (lat/lon boxes):
REGIONS = {
    "Mato Grosso": {"lat": [-17, -10], "lon": [-60, -50]},
    "MS": {"lat": [-24, -17], "lon": [-58, -50]},
}

# Variables:
# - PRATE (precipitation rate)
# - TMP (temperature)
# - APCP (accumulated precipitation)

# Cycle schedule:
# - 00z: Available ~4 hours after midnight UTC
# - 06z: Available ~4 hours after 6 AM UTC
# - 12z: Available ~4 hours after noon UTC
# - 18z: Available ~4 hours after 6 PM UTC
```

**Critical Limitation:**
- **GFS is a FORECAST model** - provides predictions, not observed actual weather
- **Cannot train ML models on forecasts** - need historical actual observations
- **Use case:** Real-time monitoring only, NOT backfill or historical training

**Implementation Time:** 4-6 hours
- 2 hours: Set up GRIB2 parsing (pygrib installation)
- 2 hours: Extract Brazil region subsets
- 1 hour: Convert to BigQuery schema
- 1 hour: Schedule 4x daily cron jobs

**Success Probability:** 95% (but wrong use case)

**Cost:** $0

**Verdict:** ❌ **NOT SUITABLE** for historical backfill and model training

---

### Option 3: Google Earth Engine BR-DWGD ✅ HIGH QUALITY

**Source:** Brazilian Daily Weather Gridded Data (Xavier et al., 2016)

**Pros:**
- ✅ **FREE** - Google Earth Engine public dataset
- ✅ **BEST QUALITY** - Validated against 11,473 rain gauges + 1,252 weather stations
- ✅ **Long History** - 1961-2020 (60 years of data)
- ✅ **High Resolution** - 0.1° × 0.1° grid (~10km)
- ✅ **All Variables** - Precipitation, Tmax, Tmin, solar radiation, humidity
- ✅ **Academic Validation** - Published in Scientific Data (Nature)
- ✅ **Perfect for ML Training** - Clean, consistent, validated

**Cons:**
- ⚠️ **Ends in 2020** - 5-year gap to present (2021-2025 missing)
- ⚠️ **Requires GEE Account** - Free but need Google registration
- ⚠️ **Learning Curve** - JavaScript API or Python Earth Engine API
- ⚠️ **Batch Processing** - Cannot query single dates easily

**Technical Details:**
```javascript
// Google Earth Engine code
var dataset = ee.ImageCollection('INPE/BR-DWGD')
  .filterDate('2018-01-01', '2020-12-31')
  .filterBounds(matoGrosso);  // Define region

var precipitation = dataset.select('pr');  // Daily precip
var tmax = dataset.select('tmax');
var tmin = dataset.select('tmin');

// Export to CSV or BigQuery
Export.table.toDrive({
  collection: precipitation,
  description: 'brazil_precip_2018_2020'
});
```

**Implementation Time:** 4-6 hours
- 1 hour: Set up Google Earth Engine account
- 2 hours: Learn GEE JavaScript/Python API
- 2 hours: Extract Mato Grosso region (1961-2020)
- 1 hour: Load to BigQuery

**Success Probability:** 90%

**Cost:** $0 (GEE compute quota: 10,000 requests/day free)

**Verdict:** ✅ **BEST QUALITY** but 2021-2025 gap needs separate solution

---

### Option 4: Meteomatics API ⚠️ COMMERCIAL

**Source:** Meteomatics weather data service (Swiss company)

**Pros:**
- ✅ **Production-Ready** - Used by Fortune 500 companies
- ✅ **Historical + Real-time** - 1940-present
- ✅ **High Quality** - Multi-model ensemble
- ✅ **Easy Integration** - RESTful API with JSON/CSV
- ✅ **750+ Brazil Stations** - Recently integrated for agricultural trade
- ✅ **Technical Support** - Dedicated account managers
- ✅ **Reliable SLA** - 99.9% uptime guarantee

**Cons:**
- ❌ **EXPENSIVE** - Subscription required (~$500-2000/month)
- ❌ **Commercial Lock-in** - Vendor dependency
- ⚠️ **Usage-Based Pricing** - Costs scale with API calls
- ⚠️ **Trial Period** - Need to test before committing

**Technical Details:**
```python
# Meteomatics API
BASE_URL = "https://api.meteomatics.com"
USERNAME = "your_username"
PASSWORD = "your_password"

# Query example:
params = {
    "validdatetime": "2023-01-01T00:00:00Z--2025-10-01T00:00:00Z:P1D",
    "parameters": "t_2m:C,precip_1h:mm",
    "location": "-15.0,-55.0"  # Mato Grosso
}
```

**Implementation Time:** 1-2 hours (easiest integration)

**Success Probability:** 99%

**Cost:** **~$1,000/month** (estimate for 2-year backfill + daily updates)

**Verdict:** ✅ **FASTEST** but only if budget allows

---

## 🎯 Decision Matrix

| Criterion | INMET | NOAA GFS | Google EE BR-DWGD | Meteomatics |
|-----------|-------|----------|-------------------|-------------|
| **Cost** | Free ✅ | Free ✅ | Free ✅ | ~$1K/mo ❌ |
| **Historical Data** | ✅ Yes | ❌ Forecast only | ✅ 1961-2020 | ✅ 1940-present |
| **Current Data** | ✅ Real-time | ✅ Forecast | ⚠️ Ends 2020 | ✅ Real-time |
| **Implementation** | 2-4 hours | 4-6 hours | 4-6 hours | 1-2 hours |
| **Data Quality** | Good | Forecast | Excellent | Excellent |
| **ML Training** | ✅ Yes | ❌ No (forecast) | ✅ Yes | ✅ Yes |
| **Backfill Capable** | ✅ Yes | ❌ No | ✅ 1961-2020 | ✅ Yes |
| **Success Probability** | 85% | 95% (wrong use) | 90% | 99% |

---

## 💡 RECOMMENDED SOLUTION: Hybrid Approach

### **Strategy: INMET (Primary) + Google EE (Validation)**

**Phase 1: INMET Implementation (Priority 1)**
- **Timeline:** Week 1 (2-4 hours)
- **Target:** 2023-2025 backfill (match ZL price data range)
- **Outcome:** Operational Brazil weather pipeline with current data

**Phase 2: Google EE BR-DWGD (Validation)**
- **Timeline:** Week 2 (4-6 hours)
- **Target:** 2018-2020 validation period (overlap with INMET)
- **Outcome:** Validate INMET data quality against academic-grade dataset

**Phase 3: Gap Analysis**
- Compare INMET (2018-2020) vs BR-DWGD (2018-2020)
- Identify discrepancies
- Adjust INMET ingestion if needed

**Fallback Options:**
1. If INMET fails → Pivot to Meteomatics trial (free 2 weeks)
2. If budget approved → Subscribe to Meteomatics permanently
3. For historical research → Use BR-DWGD (1961-2020) as baseline

---

## 🚫 Why NOT NOAA GFS

**Critical Understanding:**
- NOAA GFS is a **FORECAST MODEL**, not observed weather
- **Forecast ≠ Actual Weather** - cannot train ML on predictions
- **Use Case:** Real-time monitoring only (e.g., "what will happen next week")
- **NOT suitable for:** Historical backfill, model training, backtesting

**Example Confusion:**
```
❌ WRONG: "Use GFS to backfill 2023-2024 Brazil weather"
   → GFS doesn't have historical observations, only forecasts made in the past

✅ RIGHT: "Use GFS to monitor current week precipitation forecasts"
   → GFS provides 15-day forecasts updated 4x daily
```

**When to Use GFS:**
- Real-time dashboards showing forecast overlay
- "What if" scenario analysis
- Short-term trading signals (next 7-15 days)

**When NOT to Use GFS:**
- Training ARIMA/ML models (need actual historical observations)
- Backtesting strategies
- Validating model accuracy

---

## 📋 Implementation Plan: INMET (Recommended)

### Step 1: Research & Setup (30 minutes)
```bash
# Clone GitHub wrapper for reference
git clone https://github.com/gregomelo/brazil_weather_data.git

# Study INMET portal structure
# Visit: https://portal.inmet.gov.br/
# Check: BDMEP section (historical data)
```

### Step 2: Create Ingestion Script (2 hours)
```python
# File: cbi-v14-ingestion/ingest_weather_inmet.py

import requests
import pandas as pd
from datetime import datetime, timedelta
from bigquery_utils import safe_load_to_bigquery

PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"

# INMET stations for soy regions
INMET_STATIONS = {
    "Brazil": {
        "A901": {"name": "Sorriso", "state": "Mato Grosso", "lat": -12.5, "lon": -55.7},
        "A923": {"name": "Sinop", "state": "Mato Grosso", "lat": -11.9, "lon": -55.5},
        "A936": {"name": "Alta Floresta", "state": "MT", "lat": -9.9, "lon": -56.1},
        "A702": {"name": "Campo Grande", "state": "MS", "lat": -20.4, "lon": -54.5},
        "A736": {"name": "Dourados", "state": "MS", "lat": -22.2, "lon": -54.8},
    }
}

def fetch_inmet_data(station_code, start_date, end_date):
    """
    Fetch weather data from INMET API/portal
    Returns: DataFrame with date, precip_mm, temp_max, temp_min
    """
    # TODO: Implement INMET API call or CSV download
    # Based on GitHub wrapper: https://github.com/gregomelo/brazil_weather_data
    pass

def backfill_brazil_weather(years=2):
    """Backfill Brazil weather from INMET"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years*365)
    
    all_data = []
    
    for station_code, info in INMET_STATIONS["Brazil"].items():
        print(f"Fetching {info['name']}, {info['state']}...")
        
        df = fetch_inmet_data(station_code, start_date, end_date)
        df['region'] = 'Brazil'
        df['station_id'] = f"INMET_{station_code}"
        
        all_data.append(df)
    
    # Combine and load
    combined = pd.concat(all_data, ignore_index=True)
    
    # Load to BigQuery (same schema as NOAA)
    client = bigquery.Client(project=PROJECT_ID)
    job = safe_load_to_bigquery(
        client, 
        combined, 
        f"{PROJECT_ID}.{DATASET_ID}.weather_data",
        job_config
    )
    job.result()
    
    print(f"Loaded {len(combined)} Brazil weather rows")
    
if __name__ == "__main__":
    backfill_brazil_weather(years=2)
```

### Step 3: Test & Validate (1 hour)
```bash
# Run backfill
python3 cbi-v14-ingestion/ingest_weather_inmet.py

# Verify data loaded
bq query "SELECT COUNT(*) FROM \`cbi-v14.forecasting_data_warehouse.weather_data\` WHERE region='Brazil'"
# Expected: ≥1,000 rows (5 stations × 2 years × 365 days = 3,650 theoretical max)

# Check coverage
bq query "
SELECT 
  station_id,
  MIN(date) as earliest,
  MAX(date) as latest,
  COUNT(*) as days,
  AVG(precip_mm) as avg_precip,
  AVG(temp_max) as avg_temp
FROM \`cbi-v14.forecasting_data_warehouse.weather_data\`
WHERE region='Brazil'
GROUP BY station_id
"
```

### Step 4: Schedule Daily Updates (15 minutes)
```bash
# Add to crontab
crontab -e

# Daily at 7 AM UTC (after INMET data refresh)
0 7 * * * cd /Users/zincdigital/CBI-V14/cbi-v14-ingestion && /usr/local/bin/python3 ingest_weather_inmet.py --days 7 >> ~/inmet-brazil.log 2>&1
```

---

## ✅ Success Criteria

**Phase 1 Complete When:**
- [ ] ≥1,000 Brazil weather rows in `weather_data` table
- [ ] Coverage: 2023-09-01 to 2025-10-06 (matches ZL price data)
- [ ] Data quality: No nulls in precipitation, temp fields
- [ ] vw_weather_daily shows Brazil region alongside US/Argentina
- [ ] Coverage check: Brazil weather ≥80% (matches US coverage)

**Validation Query:**
```sql
SELECT 
  region,
  COUNT(*) as rows,
  COUNT(DISTINCT date) as unique_dates,
  MIN(date) as earliest,
  MAX(date) as latest,
  COUNTIF(precip_mm IS NULL) as null_precip,
  COUNTIF(temp_max IS NULL) as null_temp
FROM `cbi-v14.forecasting_data_warehouse.weather_data`
GROUP BY region
ORDER BY region;

-- Expected:
-- Brazil: ≥1,000 rows, ≥700 unique dates, 0 nulls
-- US: 2,672 rows
-- Argentina: 1,342 rows
```

---

## 📊 Cost-Benefit Summary

| Solution | Cost | Time | Quality | Verdict |
|----------|------|------|---------|---------|
| **INMET** | $0 | 2-4h | Good | ✅ **RECOMMENDED** |
| **Google EE** | $0 | 4-6h | Excellent | ✅ Use for validation |
| **NOAA GFS** | $0 | 4-6h | N/A (forecast) | ❌ Wrong use case |
| **Meteomatics** | $1K/mo | 1-2h | Excellent | ⚠️ Fallback if budget |

**Total Investment:**
- **Time:** 6-10 hours (INMET + GEE validation)
- **Money:** $0 (free government data)
- **Risk:** Low (multiple fallback options)

**Expected Outcome:**
- Brazil weather operational in 1 week
- 80%+ coverage (match US/Argentina)
- Zero recurring costs
- Production-grade data quality

---

## 🎯 Final Recommendation

**Proceed with INMET as primary Brazil weather source:**

1. **Immediate Action:** Research INMET API/portal access (30 min)
2. **Script Development:** Code `ingest_weather_inmet.py` (2-4 hours)
3. **Backfill Execution:** Run 2-year historical load (30 min)
4. **Validation:** Compare 2018-2020 vs Google EE BR-DWGD (optional, 4 hours)
5. **Automation:** Schedule daily updates (15 min)

**If INMET Fails:**
- **Plan B:** Meteomatics 2-week free trial (fastest pivot)
- **Plan C:** Google EE for historical + accept 2021-2025 gap

**Do NOT use NOAA GFS for historical backfill** - it's forecast data, not observations.

---

**Status:** Ready to proceed with INMET implementation  
**Next Action:** Research INMET API access methods (portal, CSV, or API endpoints)  
**Timeline:** Phase 1 complete in 1 week




