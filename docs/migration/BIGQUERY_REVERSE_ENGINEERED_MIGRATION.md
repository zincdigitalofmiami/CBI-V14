---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# BigQuery Reverse-Engineered Migration Plan
**Date:** November 19, 2025
**Status:** CRITICAL - Proper Migration Required
**Objective:** Fix the scattered mess and organize properly

---

## 🔴 CURRENT STATE ANALYSIS (The Mess)

### Location Problems
```
❌ WRONG LOCATION (US multi-region):
- archive_backup_20251115
- dashboard_backup_20251115_final  
- features_backup_20251115
- model_backups_oct27
- models_v5

✅ CORRECT LOCATION (us-central1):
- Most other datasets
```

### Dataset Chaos
```
DUPLICATES & CONFUSION:
- forecasting_data_warehouse (old) vs market_data (new)
- models vs models_v4 vs models_v5
- features vs features_backup_20251115 vs features_backup_20251117
- Too many backups cluttering the project
```

### Table Organization Issues
```
WRONG TABLES IN WRONG PLACES:
- Soybean oil prices split across multiple datasets
- Training tables contaminated with placeholders
- MES data mixed with public ZL data
- No clear separation of concerns
```

---

## 🎯 TARGET STATE (Clean Architecture)

### Core Datasets Only (12 Essential)
```sql
cbi-v14.raw_intelligence      -- External API data (FRED, USDA, EIA, NOAA)
cbi-v14.market_data           -- Futures OHLCV (DataBento, Yahoo historical)
cbi-v14.features              -- Master features table (400+ columns)
cbi-v14.training              -- Training datasets by horizon
cbi-v14.predictions           -- Model outputs
cbi-v14.monitoring            -- Data quality & performance
cbi-v14.api                   -- Dashboard views
cbi-v14.dim                   -- Reference data
cbi-v14.ops                   -- Operations & ingestion logs
cbi-v14.signals               -- Derived signals (Big 8, crush, spreads)
cbi-v14.regimes               -- Market regime classifications
cbi-v14.neural                -- Neural network features
```

### Proper Table Placement
```yaml
raw_intelligence:
  - fred_*           # All FRED series
  - usda_*           # USDA reports
  - eia_*            # EIA energy data
  - noaa_*           # Weather data
  - cftc_*           # CFTC positioning
  - databento_raw_*  # Raw API responses

market_data:
  - databento_futures_ohlcv_1m    # 1-minute bars
  - databento_futures_ohlcv_1d    # Daily bars
  - databento_futures_continuous  # Front month continuous
  - yahoo_zl_historical_2000_2010 # Historical bridge
  - roll_calendar                 # Contract rolls
  - futures_curve                 # Term structure

features:
  - master_features                # THE canonical table
  - mes_volume_profile            # MES-specific
  - mes_pivots                    # MES-specific
  - mes_fibonacci                 # MES-specific
  - mes_garch_vol                 # MES volatility
  - mes_ms_egarch_vol             # Markov-switching

training:
  - zl_training_prod_allhistory_1w
  - zl_training_prod_allhistory_1m
  - zl_training_prod_allhistory_3m
  - zl_training_prod_allhistory_6m
  - zl_training_prod_allhistory_12m
  # MES training tables (12 horizons)

predictions:
  - zl_predictions_latest
  - mes_predictions_view_only
  - forecast_metadata

monitoring:
  - data_quality_checks
  - model_performance
  - mes_zl_correlation
  - ingestion_health

api:
  - vw_zl_dashboard        # Public ZL view
  - vw_mes_private         # Private MES view
  - vw_system_health       # Monitoring view
```

---

## 📋 STEP-BY-STEP MIGRATION EXECUTION

### Phase 1: Clean Up The Mess (30 minutes)

```bash
# 1. Archive all backups to a single archive dataset
bq mk --location=us-central1 cbi-v14.z_archive_20251119

# 2. Move all backup tables there
for dataset in archive_backup_20251115 dashboard_backup_20251115_final \
               features_backup_20251115 features_backup_20251117 \
               model_backups_oct27 models_v4_backup_20251117 \
               forecasting_data_warehouse_backup_20251117 \
               raw_intelligence_backup_20251115 raw_intelligence_backup_20251117 \
               training_backup_20251115 training_backup_20251117 \
               monitoring_backup_20251115 predictions_backup_20251115; do
  echo "Archiving ${dataset}..."
  # Copy tables to archive
  for table in $(bq ls -n 1000 cbi-v14.${dataset} | tail -n +3 | awk '{print $1}'); do
    bq cp -f cbi-v14.${dataset}.${table} cbi-v14.z_archive_20251119.${dataset}__${table}
  done
  # Delete the backup dataset
  bq rm -r -f -d cbi-v14.${dataset}
done

# 3. Delete deprecated/unused datasets
for dataset in curated dashboard_tmp deprecated bkp \
               export_evaluated_data_items_cbi_v14_automl_pilot_1w_2025_10_28T10_08_35_327Z; do
  bq rm -r -f -d cbi-v14.${dataset}
done
```

### Phase 2: Consolidate Duplicates (45 minutes)

```bash
# 1. Merge forecasting_data_warehouse into market_data
echo "Merging forecasting_data_warehouse → market_data..."

# List all tables and copy to market_data with validation
for table in $(bq ls -n 1000 cbi-v14.forecasting_data_warehouse | tail -n +3 | awk '{print $1}'); do
  echo "Processing ${table}..."
  
  # Check if table has real data (not placeholders)
  row_count=$(bq query --use_legacy_sql=false --format=csv \
    "SELECT COUNT(*) FROM \`cbi-v14.forecasting_data_warehouse.${table}\`" | tail -1)
  
  if [ "$row_count" -gt "0" ]; then
    # Check for placeholder values
    placeholder_check=$(bq query --use_legacy_sql=false --format=csv \
      "SELECT COUNT(*) FROM \`cbi-v14.forecasting_data_warehouse.${table}\` 
       WHERE CAST(close AS STRING) = '0.5' 
          OR CAST(price AS STRING) = '0.5' 
          OR CAST(value AS STRING) = '1.0'
       LIMIT 1" 2>/dev/null | tail -1)
    
    if [ "$placeholder_check" = "0" ]; then
      echo "  ✓ Copying ${table} (${row_count} rows, no placeholders)"
      bq cp -f cbi-v14.forecasting_data_warehouse.${table} cbi-v14.market_data.fwd_${table}
    else
      echo "  ⚠️  Skipping ${table} - contains placeholders"
    fi
  fi
done

# 2. Handle models consolidation
echo "Consolidating models datasets..."
# Keep models_v4 as the primary, archive others
bq cp -r cbi-v14.models cbi-v14.z_archive_20251119.models_legacy
bq cp -r cbi-v14.models_v5 cbi-v14.z_archive_20251119.models_v5_legacy
```

### Phase 3: Create Proper Structure (1 hour)

```python
#!/usr/bin/env python3
"""
deploy_proper_bigquery_structure.py
Creates the correct BigQuery structure with proper validation
"""

from google.cloud import bigquery
import sys

client = bigquery.Client(project='cbi-v14')
LOCATION = 'us-central1'

# Define proper table structure
TABLES = {
    'raw_intelligence.databento_futures_ohlcv_1m': """
        CREATE TABLE IF NOT EXISTS `cbi-v14.raw_intelligence.databento_futures_ohlcv_1m` (
            ts_event TIMESTAMP NOT NULL,
            symbol STRING NOT NULL,
            open FLOAT64,
            high FLOAT64,
            low FLOAT64,
            close FLOAT64,
            volume INT64,
            trades INT64,
            vwap FLOAT64,
            as_of TIMESTAMP NOT NULL,
            collection_timestamp TIMESTAMP
        ) 
        PARTITION BY DATE(ts_event) 
        CLUSTER BY symbol
        OPTIONS(description='DataBento 1-minute bars - PRIMARY ingestion point')
    """,
    
    'market_data.roll_calendar': """
        CREATE TABLE IF NOT EXISTS `cbi-v14.market_data.roll_calendar` (
            root STRING NOT NULL,
            roll_date DATE NOT NULL,
            from_contract STRING NOT NULL,
            to_contract STRING NOT NULL,
            roll_method STRING,
            roll_window_days INT64,
            as_of TIMESTAMP NOT NULL
        ) 
        PARTITION BY roll_date 
        CLUSTER BY root
        OPTIONS(description='Contract roll schedule')
    """,
    
    'features.master_features': """
        CREATE TABLE IF NOT EXISTS `cbi-v14.features.master_features` (
            date DATE NOT NULL,
            symbol STRING NOT NULL,
            
            -- DataBento features (prefixed)
            databento_open FLOAT64,
            databento_high FLOAT64,
            databento_low FLOAT64,
            databento_close FLOAT64,
            databento_volume INT64,
            
            -- Yahoo features (prefixed)  
            yahoo_close FLOAT64,
            yahoo_volume INT64,
            yahoo_rsi_14 FLOAT64,
            yahoo_macd FLOAT64,
            
            -- FRED features (prefixed)
            fred_vix_close FLOAT64,
            fred_dgs10_yield FLOAT64,
            fred_dgs2_yield FLOAT64,
            fred_t10y2y_spread FLOAT64,
            fred_dff FLOAT64,
            
            -- Derived features
            returns_1d FLOAT64,
            returns_5d FLOAT64,
            returns_20d FLOAT64,
            vol_realized_5d FLOAT64,
            vol_realized_20d FLOAT64,
            
            -- Regime
            market_regime STRING,
            training_weight INT64,
            
            -- MES-specific (NULL for ZL)
            mes_poc_distance FLOAT64,
            mes_pivot_confluence INT64,
            mes_fib_618_distance FLOAT64,
            ms_egarch_current_regime STRING,
            prob_crash_next_5d FLOAT64,
            
            -- Tracking
            as_of TIMESTAMP NOT NULL,
            created_at TIMESTAMP
        ) 
        PARTITION BY date 
        CLUSTER BY symbol, market_regime
        OPTIONS(description='Master feature table - SINGLE source of truth')
    """,
    
    'ops.ingestion_runs': """
        CREATE TABLE IF NOT EXISTS `cbi-v14.ops.ingestion_runs` (
            run_id STRING NOT NULL,
            source STRING NOT NULL,
            status STRING NOT NULL,
            rows_processed INT64,
            started_at TIMESTAMP NOT NULL,
            completed_at TIMESTAMP,
            error_message STRING
        ) 
        PARTITION BY DATE(started_at)
        CLUSTER BY source, status
        OPTIONS(description='Track all ingestion runs')
    """,
    
    'monitoring.data_quality_checks': """
        CREATE TABLE IF NOT EXISTS `cbi-v14.monitoring.data_quality_checks` (
            check_timestamp TIMESTAMP NOT NULL,
            table_name STRING NOT NULL,
            check_type STRING NOT NULL,
            check_result STRING NOT NULL,
            issues_found INT64
        ) 
        PARTITION BY DATE(check_timestamp)
        CLUSTER BY table_name
        OPTIONS(description='Data quality results')
    """
}

# Create tables with validation
for table_id, ddl in TABLES.items():
    print(f"Creating {table_id}...")
    try:
        query_job = client.query(ddl, location=LOCATION)
        query_job.result()
        print(f"  ✓ {table_id} created")
    except Exception as e:
        print(f"  ❌ {table_id} failed: {e}")

# Create proper views
VIEWS = {
    'api.vw_zl_dashboard': """
        CREATE OR REPLACE VIEW `cbi-v14.api.vw_zl_dashboard` AS
        SELECT 
            date,
            databento_close as current_price,
            returns_1d,
            returns_5d,
            vol_realized_20d,
            fred_vix_close as vix_level,
            market_regime
        FROM `cbi-v14.features.master_features`
        WHERE symbol = 'ZL'
          AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
        ORDER BY date DESC
    """,
    
    'api.vw_mes_private': """
        CREATE OR REPLACE VIEW `cbi-v14.api.vw_mes_private` AS
        SELECT 
            date,
            databento_close as current_price,
            returns_1d,
            mes_poc_distance,
            mes_pivot_confluence,
            prob_crash_next_5d
        FROM `cbi-v14.features.master_features`
        WHERE symbol = 'MES'
          AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
        ORDER BY date DESC
    """
}

for view_id, ddl in VIEWS.items():
    print(f"Creating view {view_id}...")
    try:
        query_job = client.query(ddl, location=LOCATION)
        query_job.result()
        print(f"  ✓ {view_id} created")
    except Exception as e:
        print(f"  ❌ {view_id} failed: {e}")
```

### Phase 4: Data Migration & Validation (2 hours)

```python
#!/usr/bin/env python3
"""
migrate_and_validate_data.py
Move data to proper locations with validation
"""

import pandas as pd
from google.cloud import bigquery
import numpy as np

client = bigquery.Client(project='cbi-v14')

def validate_data(df, table_name):
    """No placeholders, no fake data"""
    issues = []
    
    # Check for empty
    if df.empty:
        issues.append("Empty DataFrame")
    
    # Check for placeholder values
    for col in df.select_dtypes(include=[np.number]).columns:
        if (df[col] == 0.5).any():
            issues.append(f"Column {col} contains 0.5 placeholders")
        if (df[col] == 1.0).all():
            issues.append(f"Column {col} is all 1.0")
        if df[col].std() == 0:
            issues.append(f"Column {col} has no variance")
    
    # Check for date coverage
    if 'date' in df.columns:
        min_date = pd.to_datetime(df['date'].min())
        max_date = pd.to_datetime(df['date'].max())
        if min_date.year > 2000:
            issues.append(f"Missing pre-2020 data (starts {min_date})")
    
    # Check for regime diversity
    if 'market_regime' in df.columns:
        unique_regimes = df['market_regime'].nunique()
        if unique_regimes < 7:
            issues.append(f"Only {unique_regimes} regimes (need 7+)")
    
    return issues

def migrate_table(source_table, target_table):
    """Migrate with validation"""
    print(f"\nMigrating {source_table} → {target_table}")
    
    # Read source
    query = f"SELECT * FROM `{source_table}`"
    df = client.query(query).to_dataframe()
    
    # Validate
    issues = validate_data(df, source_table)
    if issues:
        print(f"  ⚠️  Validation issues:")
        for issue in issues:
            print(f"     - {issue}")
        response = input("  Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("  Skipped")
            return
    
    # Load to target
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION]
    )
    
    job = client.load_table_from_dataframe(
        df, target_table, job_config=job_config
    )
    job.result()
    
    print(f"  ✓ Migrated {len(df)} rows")

# Key migrations
MIGRATIONS = [
    ('cbi-v14.yahoo_finance_comprehensive.yahoo_normalized', 
     'cbi-v14.market_data.yahoo_historical'),
    
    ('cbi-v14.staging.mes_futures_daily',
     'cbi-v14.market_data.mes_daily'),
    
    ('cbi-v14.staging.zl_daily_aggregated',
     'cbi-v14.market_data.zl_daily'),
    
    ('cbi-v14.training.regime_calendar',
     'cbi-v14.regimes.regime_calendar'),
    
    ('cbi-v14.training.regime_weights',
     'cbi-v14.regimes.regime_weights')
]

for source, target in MIGRATIONS:
    try:
        migrate_table(source, target)
    except Exception as e:
        print(f"  ❌ Failed: {e}")
```

---

## ✅ VALIDATION CHECKLIST

### 1. Location Check
```sql
-- All datasets should be in us-central1
SELECT 
  schema_name,
  location
FROM `cbi-v14.INFORMATION_SCHEMA.SCHEMATA`
WHERE location != 'us-central1';
-- Should return 0 rows
```

### 2. Table Placement Check
```sql
-- Verify tables are in correct datasets
SELECT 
  table_schema,
  table_name
FROM `cbi-v14.INFORMATION_SCHEMA.TABLES`
WHERE table_schema NOT IN (
  'raw_intelligence', 'market_data', 'features', 'training',
  'predictions', 'monitoring', 'api', 'dim', 'ops', 'signals',
  'regimes', 'neural', 'z_archive_20251119'
)
ORDER BY table_schema, table_name;
-- Should only show archive datasets
```

### 3. Data Quality Check
```sql
-- No placeholders
SELECT COUNT(*) as placeholder_count
FROM `cbi-v14.features.master_features`
WHERE databento_close = 0.5
   OR training_weight = 1
   OR market_regime = 'allhistory';
-- Must return 0
```

### 4. MES Isolation Check
```bash
# Verify MES data has proper access control
bq show --format=prettyjson cbi-v14.api.vw_mes_private | grep -A 5 access
```

---

## 🎯 SUCCESS CRITERIA

1. ✅ Only 12 core datasets + 1 archive dataset
2. ✅ All datasets in us-central1
3. ✅ No duplicate/redundant datasets
4. ✅ Tables in proper datasets
5. ✅ No placeholder data
6. ✅ MES data properly isolated
7. ✅ Clear naming conventions
8. ✅ Proper partitioning & clustering
9. ✅ Views for dashboard access
10. ✅ Ingestion tracking in place

---

## 📝 LESSONS FROM FAILURES

1. **Location Matters**: Always specify us-central1, never use multi-region US
2. **Organize First**: Define structure before creating anything
3. **Validate Everything**: Every data load must be validated
4. **No Duplicates**: One dataset for each purpose
5. **Clear Naming**: Prefixed columns, descriptive table names
6. **Access Control**: Set up from the beginning
7. **Archive Don't Delete**: Keep backups in archive dataset
8. **Document Everything**: Clear mapping of what goes where

---

**THIS IS THE WAY. NO GUESSING. FOLLOW THIS EXACTLY.**
