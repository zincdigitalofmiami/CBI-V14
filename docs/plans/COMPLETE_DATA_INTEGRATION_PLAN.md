# 🎯 COMPLETE DATA INTEGRATION PLAN
**Date:** November 12, 2025  
**Goal:** Pull ALL intelligence data back into training + fix forensic audit gaps  
**Status:** READY TO EXECUTE

---

## PHASE 1: FIX FORENSIC AUDIT GAPS (6 hours)

### 1.1 Create Baltic Dry Index Table (2 hours)
**Location:** `forecasting_data_warehouse.baltic_dry_index`

```sql
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.baltic_dry_index` (
  time TIMESTAMP NOT NULL,
  index_value INT64,
  change_value FLOAT64,
  pct_change FLOAT64,
  source_name STRING DEFAULT 'investing.com',
  ingest_timestamp_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  provenance_uuid STRING
)
PARTITION BY DATE(time)
OPTIONS(
  description="Baltic Dry Index - Daily shipping rates"
);
```

**Actions:**
- Run DDL
- Execute: `python3 scripts/backfill_baltic_dry_index_historical.py`
- Target: 2006-2025 data (~5,000 rows)

### 1.2 Backfill China Soybean Imports (4 hours)
**Current:** 22 rows  
**Target:** 500+ rows (monthly 2017-2025)

**Actions:**
- Execute: `python3 scripts/backfill_china_imports_historical.py`
- Verify: `SELECT COUNT(*), MIN(time), MAX(time) FROM forecasting_data_warehouse.china_soybean_imports`

---

## PHASE 2: STANDARDIZE SCHEMAS (4 hours)

### 2.1 Priority Tables for `time TIMESTAMP` Migration

**High Priority (Top 20 most-queried):**
1. `cftc_cot` (date → time)
2. `news_intelligence` (published → time)
3. `news_advanced` (published_date → time)
4. `social_intelligence_unified` (ingested_at → time)
5. `trump_policy_intelligence` (ingested_at → time)
6. `biofuel_policy` (date → time)
7. `usda_export_sales` (report_date → time)
8. `usda_harvest_progress` (harvest_date → time)
9. `breaking_news_hourly` (timestamp → time)
10. `canola_oil_prices` (date → time)
11. `corn_prices` (date → time)
12. `wheat_prices` (date → time)
13. Plus 7 more commodity tables

**Migration Method (per table):**
```sql
-- Example for cftc_cot
CREATE TABLE `cbi-v14.forecasting_data_warehouse.cftc_cot_new` AS
SELECT 
  TIMESTAMP(report_date) as time,
  * EXCEPT(report_date)
FROM `cbi-v14.forecasting_data_warehouse.cftc_cot`;

-- Swap tables
DROP TABLE `cbi-v14.forecasting_data_warehouse.cftc_cot`;
ALTER TABLE `cbi-v14.forecasting_data_warehouse.cftc_cot_new`
RENAME TO cftc_cot;
```

**Can be done table-by-table without downtime.**

---

## PHASE 3: REBUILD TRAINING TABLES WITH ALL INTELLIGENCE (8 hours)

### 3.1 Verify Source Data Completeness

**Check each intelligence source:**
```sql
-- News
SELECT 'news_intelligence' as table, COUNT(*) as rows, MIN(published) as earliest, MAX(published) as latest
FROM `forecasting_data_warehouse.news_intelligence`
UNION ALL
SELECT 'social_intelligence', COUNT(*), MIN(ingested_at), MAX(ingested_at)
FROM `forecasting_data_warehouse.social_intelligence_unified`
UNION ALL
SELECT 'trump_policy', COUNT(*), MIN(ingested_at), MAX(ingested_at)
FROM `forecasting_data_warehouse.trump_policy_intelligence`
UNION ALL
SELECT 'staging_social', COUNT(*), MIN(created_at), MAX(created_at)
FROM `staging.comprehensive_social_intelligence`;
```

### 3.2 Update Feature Engineering SQL

**Files to update:**
- `config/bigquery/bigquery-sql/BUILD_PRODUCTION_TRAINING_1W.sql`
- `config/bigquery/bigquery-sql/BUILD_PRODUCTION_TRAINING_1M.sql`
- `config/bigquery/bigquery-sql/BUILD_PRODUCTION_TRAINING_3M.sql`
- `config/bigquery/bigquery-sql/BUILD_PRODUCTION_TRAINING_6M.sql`
- `config/bigquery/bigquery-sql/BUILD_PRODUCTION_TRAINING_12M.sql`

**Ensure these features are included:**

#### News/Social Features (from `news_intelligence` + `social_intelligence_unified`)
- `china_sentiment` (rolling average)
- `china_sentiment_30d_ma`
- `china_sentiment_volatility`
- `avg_sentiment`
- `sentiment_volume`
- `sentiment_volatility`
- `news_article_count`
- `news_avg_score`
- `co_mention_sentiment`

#### Trump/Policy Features (from `trump_policy_intelligence`)
- `trump_mentions`
- `china_policy_impact`
- `trumpxi_china_mentions`
- `trump_xi_co_mentions`
- `trumpxi_sentiment_volatility`
- `trumpxi_volatility_30d_ma`
- `trumpxi_policy_impact`
- `max_policy_impact`

#### Tariff/Trade Features (from `trade_war_2017_2019_historical` + signals)
- `feature_tariff_threat`
- `tariff_mentions`
- `china_tariff_rate`
- `trade_war_intensity`
- `trade_war_impact_score`
- `tradewar_event_vol_mult`

#### ICE Intelligence (from `ice_enforcement_intelligence`)
- `ice_enforcement_actions`
- `ice_policy_shift_indicator`

#### FX Features (already included, verify completeness)
- `usd_cny_rate`
- `usd_brl_rate`
- `usd_cny_7d_change`
- `usd_brl_7d_change`
- `dxy_lag1`, `dxy_lag2`

### 3.3 Create Unified Intelligence View

**New view:** `forecasting_data_warehouse.vw_unified_intelligence_daily`

```sql
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.vw_unified_intelligence_daily` AS
WITH news_daily AS (
  SELECT 
    DATE(published) as date,
    AVG(sentiment_score) as avg_sentiment,
    STDDEV(sentiment_score) as sentiment_volatility,
    COUNT(*) as article_count
  FROM `forecasting_data_warehouse.news_intelligence`
  GROUP BY DATE(published)
),
social_daily AS (
  SELECT 
    DATE(ingested_at) as date,
    COUNT(*) as social_volume,
    AVG(sentiment_score) as social_sentiment
  FROM `forecasting_data_warehouse.social_intelligence_unified`
  WHERE sentiment_score IS NOT NULL
  GROUP BY DATE(ingested_at)
),
trump_daily AS (
  SELECT 
    DATE(ingested_at) as date,
    COUNT(*) as trump_mentions,
    AVG(policy_impact_score) as avg_policy_impact,
    MAX(policy_impact_score) as max_policy_impact
  FROM `forecasting_data_warehouse.trump_policy_intelligence`
  GROUP BY DATE(ingested_at)
)
SELECT 
  COALESCE(n.date, s.date, t.date) as date,
  n.* EXCEPT(date),
  s.* EXCEPT(date),
  t.* EXCEPT(date)
FROM news_daily n
FULL OUTER JOIN social_daily s ON n.date = s.date
FULL OUTER JOIN trump_daily t ON COALESCE(n.date, s.date) = t.date
ORDER BY date;
```

### 3.4 Rebuild Production Training Tables

**Execute in order:**
```bash
# 1. Backup existing tables
bq cp models_v4.production_training_data_1w models_v4.production_training_data_1w_backup_$(date +%Y%m%d)
bq cp models_v4.production_training_data_1m models_v4.production_training_data_1m_backup_$(date +%Y%m%d)
bq cp models_v4.production_training_data_3m models_v4.production_training_data_3m_backup_$(date +%Y%m%d)
bq cp models_v4.production_training_data_6m models_v4.production_training_data_6m_backup_$(date +%Y%m%d)
bq cp models_v4.production_training_data_12m models_v4.production_training_data_12m_backup_$(date +%Y%m%d)

# 2. Rebuild with all intelligence
bq query --use_legacy_sql=false < config/bigquery/bigquery-sql/BUILD_PRODUCTION_TRAINING_1W.sql
bq query --use_legacy_sql=false < config/bigquery/bigquery-sql/BUILD_PRODUCTION_TRAINING_1M.sql
bq query --use_legacy_sql=false < config/bigquery/bigquery-sql/BUILD_PRODUCTION_TRAINING_3M.sql
bq query --use_legacy_sql=false < config/bigquery/bigquery-sql/BUILD_PRODUCTION_TRAINING_6M.sql
bq query --use_legacy_sql=false < config/bigquery/bigquery-sql/BUILD_PRODUCTION_TRAINING_12M.sql
```

### 3.5 Verify Rebuild

```sql
-- Check column counts increased
SELECT 
  '1w' as horizon,
  COUNT(*) as total_columns,
  COUNTIF(column_name LIKE '%sentiment%' OR column_name LIKE '%news%') as news_cols,
  COUNTIF(column_name LIKE '%trump%' OR column_name LIKE '%policy%') as trump_cols,
  COUNTIF(column_name LIKE '%tariff%' OR column_name LIKE '%trade%') as tariff_cols
FROM `models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'production_training_data_1w'
UNION ALL
-- Repeat for 1m, 3m, 6m, 12m
...
```

---

## PHASE 4: EXPORT TO EXTERNAL DRIVE (1 hour)

```bash
# Export fresh training data with all intelligence
python3 scripts/export_training_data.py

# Verify files on external drive
ls -lh /Volumes/Satechi\ Hub/Projects/CBI-V14/TrainingData/exports/
```

**Expected output:**
- `historical_full.parquet` (6,057 rows, 2000-2025)
- `regime_*.parquet` (5 regime files)
- All files <2 hours old

---

## PHASE 5: VALIDATE EVERYTHING (2 hours)

### 5.1 Run Verification Suite
```bash
# 1. Verify calculated features
python3 scripts/verify_calculated_features.py

# 2. Check data freshness
python3 scripts/check_stale_data.py

# 3. Comprehensive system audit
python3 scripts/full_system_audit.py
```

### 5.2 Check Training Table Quality

```sql
-- Ensure no NULL proliferation
SELECT 
  '1w' as horizon,
  COUNT(*) as total_rows,
  COUNTIF(china_sentiment IS NULL) as null_sentiment,
  COUNTIF(trump_mentions IS NULL) as null_trump,
  COUNTIF(feature_tariff_threat IS NULL) as null_tariff,
  COUNTIF(usd_cny_rate IS NULL) as null_fx
FROM `models_v4.production_training_data_1w`
UNION ALL
-- Repeat for other horizons
...
```

**Acceptable NULL rates:** <20% per column (due to data availability dates)

---

## SCHEMA PROTECTION CHECKLIST

### ✅ DO NOT CHANGE:
- Primary key: `time TIMESTAMP` (or `date` for tables not yet migrated)
- Core price columns: `open`, `high`, `low`, `close`, `volume`
- Target columns: `target_1w`, `target_1m`, etc.
- Existing feature names that training scripts depend on

### ✅ SAFE TO ADD:
- New intelligence features (append to end of schema)
- Derived features from existing columns
- Rolling averages / lag features

### ⚠️ CAREFUL WITH:
- Changing column names (breaks downstream scripts)
- Changing data types (breaks feature engineering)
- Removing columns (check if any scripts reference them)

---

## ROLLBACK PLAN

If anything breaks:

```bash
# 1. Restore training tables from backup
bq cp models_v4.production_training_data_1w_backup_YYYYMMDD models_v4.production_training_data_1w
# Repeat for all horizons

# 2. Check logs
cat Logs/training/training_rebuild_$(date +%Y%m%d).log

# 3. Verify exports still work
python3 scripts/export_training_data.py
```

---

## SUCCESS CRITERIA

### ✅ Phase 1 Complete When:
- Baltic Dry Index table exists with 5,000+ rows
- China imports table has 500+ rows
- All 3 forensic audit gaps resolved

### ✅ Phase 2 Complete When:
- Top 20 tables migrated to `time TIMESTAMP` standard
- No broken joins or queries
- Documentation updated

### ✅ Phase 3 Complete When:
- Training tables have 350+ columns (up from 300)
- All intelligence features present and non-NULL where data exists
- Row counts unchanged (~1,400-1,500 per table)

### ✅ Phase 4 Complete When:
- External drive has fresh Parquet files
- Files validated and readable
- `train_with_fresh_data.sh` wrapper works

### ✅ Phase 5 Complete When:
- All verification tests pass
- No schema errors in linter
- Training can run successfully on Mac M4

---

## EXECUTION ORDER

**Day 1 (Today):**
1. Create Baltic Dry Index table + backfill (2 hrs)
2. Backfill China imports (4 hrs)
3. Verify fixes (30 min)

**Day 2:**
4. Schema standardization for top 10 tables (4 hrs)
5. Create unified intelligence view (1 hr)
6. Update training SQL files (2 hrs)

**Day 3:**
7. Rebuild training tables (4 hrs)
8. Export to external drive (1 hr)
9. Run full validation suite (2 hrs)

**Total Time:** ~20 hours across 3 days

---

**Status:** READY TO EXECUTE  
**Risk Level:** LOW (all backups in place)  
**Confidence:** HIGH (following proven patterns)  
**Next Step:** Execute Phase 1.1 - Create Baltic Dry Index table

