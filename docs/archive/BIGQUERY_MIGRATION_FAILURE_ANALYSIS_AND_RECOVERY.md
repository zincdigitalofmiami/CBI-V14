# BigQuery Migration Failure Analysis & Recovery Plan
**Date:** November 19, 2025  
**Status:** CRITICAL - Migration Recovery Required
**Previous Failure Date:** November 17, 2025 (2 days ago)

---

## 🔴 WHAT WENT WRONG (Root Cause Analysis)

### 1. **Data Flow Direction Was Wrong**
- **❌ FAILED:** We were ingesting to External Drive FIRST, then trying to sync to BigQuery
- **✅ CORRECT:** Per FRESH_START_MASTER_PLAN: BigQuery is system of record - ingest there FIRST
- **Impact:** Data scattered across drive/BQ with no single source of truth

### 2. **Placeholder Data Contamination**
- **Critical Issue:** `training.zl_training_prod_allhistory_1m` has 100% placeholder data
  - All 1,404 rows have `market_regime='allhistory'` and `training_weight=1`
- **Missing Data:** ALL training tables missing 2000-2019 data (20 years)
- **Regime Failure:** Only 1-3 regimes instead of expected 7+

### 3. **Missing Core Tables**
- `raw_intelligence.commodity_soybean_oil_prices` - Referenced but doesn't exist
- `forecasting_data_warehouse.vix_data` - Referenced but doesn't exist
- `api.vw_ultimate_adaptive_signal` - View doesn't exist

### 4. **Wrong Dataset Names**
- Used `forecasting_data_warehouse` instead of `market_data`
- Referenced `curated` dataset that doesn't exist
- Confusion between 5 datasets vs actual 12 datasets needed

---

## 📊 CURRENT STATE ASSESSMENT

### External Drive Status (/Volumes/Satechi Hub/)
```
TrainingData/
├── raw/           ✅ Has data (databento_mes, databento_zl, fred, etc.)
├── staging/       ✅ Has 25 parquet files (mes_*, zl_*, etc.)
├── features/      ❌ EMPTY (critical failure)
├── exports/       ⚠️  Only mes_15min_training.parquet
├── quarantine/    ✅ Contains contaminated data (correctly isolated)
└── precalc/       ✅ Has regimes, metrics
```

### BigQuery Status
- **Total Data:** 1.87M rows across 453 tables
- **Datasets:** 29 datasets exist (many legacy, need cleanup)
- **Critical Tables:**
  - ✅ `yahoo_finance_comprehensive`: 801K rows (good)
  - ❌ `training.*`: Contaminated with placeholders
  - ⚠️ `features.master_features`: Needs rebuild
  - ❌ Missing MES-specific tables

---

## 🎯 RECOVERY PLAN (NO PLACEHOLDERS, NO FAKE DATA)

### Phase 1: BigQuery Foundation (TODAY - URGENT)

#### 1A. Deploy Core Datasets & Tables
```bash
# Run the deployment script we already have
cd /Users/kirkmusick/Documents/GitHub/CBI-V14
bq mk --location=us-central1 --project_id=cbi-v14 raw_intelligence
bq mk --location=us-central1 --project_id=cbi-v14 market_data
bq mk --location=us-central1 --project_id=cbi-v14 features
bq mk --location=us-central1 --project_id=cbi-v14 training
bq mk --location=us-central1 --project_id=cbi-v14 predictions
bq mk --location=us-central1 --project_id=cbi-v14 monitoring
bq mk --location=us-central1 --project_id=cbi-v14 api
bq mk --location=us-central1 --project_id=cbi-v14 dim
bq mk --location=us-central1 --project_id=cbi-v14 ops
```

#### 1B. Create Essential Tables
```sql
-- Run config/bigquery/migration/02_create_core_tables.sql
-- Run config/bigquery/mes_specific_tables.sql
```

#### 1C. Set Up GCS Buckets for Transfer
```bash
gsutil mb -p cbi-v14 -c STANDARD -l us-central1 gs://cbi-v14-training-exports/
gsutil mb -p cbi-v14 -c STANDARD -l us-central1 gs://cbi-v14-predictions-import/
gsutil mb -p cbi-v14 -c STANDARD -l us-central1 gs://cbi-v14-market-data/
```

### Phase 2: Data Ingestion Pipeline (IMMEDIATE)

#### 2A. DataBento → BigQuery Direct
```python
# Modify databento_live_poller.py to write to BQ FIRST
# Line 264-278: Enable mirror_to_bq by default
# Set up 5-minute cron for public symbols
# Set up 1-minute cron for MES
```

#### 2B. Load External Drive Data to BigQuery
```python
# Use scripts/migration/load_all_external_drive_data.py
# But VALIDATE each file first - NO PLACEHOLDERS
import pandas as pd
from google.cloud import bigquery

def validate_and_load(file_path, table_id):
    df = pd.read_parquet(file_path)
    
    # CRITICAL VALIDATIONS
    assert not df.empty, "Empty DataFrame"
    assert 'symbol' not in df.columns or not df['symbol'].str.contains('-').any(), "Contains spreads"
    assert not (df == 0.5).any().any(), "Contains 0.5 placeholders"
    assert not (df == 1.0).all().any(), "Contains all 1.0 values"
    assert df.select_dtypes(include=['float']).std().min() > 0, "No variance in data"
    
    # Load to BigQuery
    client = bigquery.Client()
    job = client.load_table_from_dataframe(df, table_id)
    job.result()
    print(f"Loaded {len(df)} rows to {table_id}")
```

#### 2C. Fix Training Tables
```sql
-- Fix regime assignments
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  market_regime = rc.regime,
  training_weight = rw.weight
FROM `cbi-v14.training.regime_calendar` rc
JOIN `cbi-v14.training.regime_weights` rw ON rc.regime = rw.regime
WHERE t.date = rc.date;

-- Load pre-2020 data
INSERT INTO `cbi-v14.training.zl_training_prod_allhistory_1m`
SELECT * FROM `cbi-v14.models_v4.pre_crisis_2000_2007_historical`
WHERE date < '2020-01-01';
```

### Phase 3: Validation Gates

#### 3A. Data Quality Checks (MANDATORY)
```sql
-- Check for placeholders
SELECT COUNT(*) as placeholder_count
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
WHERE market_regime = 'allhistory' 
   OR training_weight = 1
   OR close = 0.5;
-- MUST RETURN 0

-- Check date coverage
SELECT MIN(date) as earliest, MAX(date) as latest, COUNT(*) as total_rows
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`;
-- MUST show 2000-2025 range

-- Check regime diversity
SELECT market_regime, COUNT(*) as cnt
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
GROUP BY market_regime;
-- MUST show 7+ regimes
```

#### 3B. MES Data Isolation Check
```sql
-- Verify MES data access control
SELECT COUNT(*) 
FROM `cbi-v14.features.master_features`
WHERE symbol = 'MES';
-- Should only be accessible to authorized users
```

### Phase 4: Dashboard Integration

#### 4A. Create API Views
```sql
-- ZL Public View
CREATE OR REPLACE VIEW `cbi-v14.api.vw_zl_dashboard` AS
SELECT * FROM `cbi-v14.features.master_features`
WHERE symbol = 'ZL' 
  AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY);

-- MES Private View (with access control)
CREATE OR REPLACE VIEW `cbi-v14.api.vw_mes_private` AS
SELECT * FROM `cbi-v14.features.master_features`
WHERE symbol = 'MES'
  AND SESSION_USER() IN ('kirkmusick@gmail.com', 'mes-viewer@cbi-v14.iam');
```

---

## ⚠️ CRITICAL SUCCESS FACTORS

### 1. **NO FAKE DATA**
- Every load must validate: No 0.5, no all-1.0, no static columns
- Use checksums to verify data integrity
- Reject any file that fails validation

### 2. **BigQuery First**
- ALL ingestion goes to BigQuery FIRST
- External drive is backup/training workspace ONLY
- Single source of truth: BigQuery

### 3. **Proper Access Control**
- MES data must be isolated (private page only)
- Use Row-Level Security policies
- Audit access logs

### 4. **Complete Data Coverage**
- Must have 2000-2025 data (25 years)
- Must have all 7+ regimes properly assigned
- Must have regime weights (50-5000 scale)

---

## 📈 MONITORING & VERIFICATION

### Daily Health Checks
```sql
-- Run this query daily
WITH health AS (
  SELECT 
    'training_rows' as metric,
    COUNT(*) as value,
    CASE WHEN COUNT(*) > 30000 THEN '✅' ELSE '❌' END as status
  FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
  UNION ALL
  SELECT 
    'date_coverage_years' as metric,
    DATE_DIFF(MAX(date), MIN(date), YEAR) as value,
    CASE WHEN DATE_DIFF(MAX(date), MIN(date), YEAR) >= 24 THEN '✅' ELSE '❌' END
  FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
  UNION ALL
  SELECT 
    'unique_regimes' as metric,
    COUNT(DISTINCT market_regime) as value,
    CASE WHEN COUNT(DISTINCT market_regime) >= 7 THEN '✅' ELSE '❌' END
  FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
)
SELECT * FROM health;
```

### Migration Checklist
- [ ] Core datasets created in BigQuery
- [ ] DataBento → BQ pipeline active (5-min batches)
- [ ] External drive data validated and loaded to BQ
- [ ] Training tables fixed (regimes + pre-2020 data)
- [ ] MES tables created with access control
- [ ] API views created for dashboard
- [ ] No placeholders in ANY table (verified)
- [ ] Date coverage 2000-2025 (verified)
- [ ] 7+ regimes properly assigned (verified)

---

## 🚨 NEXT IMMEDIATE ACTIONS

1. **NOW:** Deploy BigQuery datasets and tables (30 min)
2. **NOW:** Set up GCS buckets (5 min)
3. **NOW:** Fix DataBento ingestion to go to BQ first (1 hour)
4. **TODAY:** Load and validate external drive data (2-3 hours)
5. **TODAY:** Fix training table contamination (1 hour)
6. **TODAY:** Create MES tables with proper isolation (30 min)
7. **TODAY:** Run full validation suite (30 min)

**Total Time to Recovery: 6-8 hours**

---

## 📝 LESSONS LEARNED

1. **Always validate data** - No assumptions, check everything
2. **BigQuery first** - Don't try to sync from external drive
3. **Regime assignments** - Must be applied, not just defined
4. **Access control** - Set up from day one, not after
5. **Documentation** - Keep single source of truth (FRESH_START_MASTER_PLAN)

---

**Remember:** NO PLACEHOLDERS, NO FAKE DATA, VALIDATE EVERYTHING!




