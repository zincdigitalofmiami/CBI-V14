---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# BigQuery Migration Action Plan - What Needs to Be Done
**Date:** November 19, 2025  
**Status:** CRITICAL - Action Required  
**Based On:** Fresh Audit (Nov 19) + Reverse-Engineered Migration Plan + Failure Analysis

---

## 🔴 CURRENT STATE (From Latest Audit)

### What Exists Now
- ✅ **Staging Files**: 19 parquet files, 523,291 rows (healthy)
- ✅ **Join Pipeline**: Working (2,025 rows × 1,175 columns output)
- ⚠️ **BigQuery Datasets**: Created but EMPTY (30 tables, 0 rows)
- ⚠️ **Legacy Datasets**: Still active (`forecasting_data_warehouse`, `models_v4`)
- ❌ **News Tables**: Not created yet (DDL ready, not executed)
- ❌ **Signals Dataset**: Not found in audit (may not exist)

### Critical Gaps
1. **Empty New Datasets**: `raw_intelligence`, `training`, `predictions`, `monitoring` - all tables exist but have 0 rows
2. **Data Not Loaded**: Staging files exist but haven't been loaded to BigQuery
3. **Legacy Still Active**: Old datasets still being used, causing confusion
4. **Missing Structure**: Some datasets (`signals`) may not exist
5. **News Integration**: Tables defined but not created

---

## 🎯 WHAT NEEDS TO BE DONE (Prioritized)

### PHASE 1: IMMEDIATE FOUNDATION (Do First - 2-3 hours)

#### 1.1 Verify/Create Core Datasets ✅
**Status**: Partially done - datasets exist but empty

```bash
# Verify all 12 core datasets exist in us-central1
bq ls --project_id=cbi-v14 --location=us-central1

# Expected datasets:
# - raw_intelligence ✅ (exists, empty)
# - market_data ⚠️ (may not exist - check)
# - features ⚠️ (may not exist - check)
# - training ✅ (exists, empty)
# - predictions ✅ (exists, empty)
# - monitoring ✅ (exists, empty)
# - api ⚠️ (may not exist - check)
# - dim ⚠️ (may not exist - check)
# - ops ⚠️ (may not exist - check)
# - signals ❌ (NOT FOUND in audit - needs creation)
# - regimes ⚠️ (may not exist - check)
# - neural ⚠️ (may not exist - check)
```

**Action**: Create missing datasets, verify all are in `us-central1`

#### 1.2 Execute News Collection DDL ✅
**Status**: DDL file ready, not executed

```bash
# Run the DDL to create news tables
bq query --use_legacy_sql=false \
  --location=us-central1 \
  < config/bigquery/bigquery-sql/create_alpha_news_tables.sql
```

**Action**: Execute DDL to create:
- `raw_intelligence.intelligence_news_alpha_raw_daily`
- `raw_intelligence.intelligence_news_alpha_classified_daily`
- `signals.hidden_relationship_signals`
- `monitoring.alpha_news_cursor`

#### 1.3 Load Staging Files to BigQuery 🔥 CRITICAL
**Status**: 19 staging files ready, 0 loaded to BigQuery

**Priority Files** (load these first):
1. `yahoo_historical_prefixed.parquet` → `market_data.yahoo_historical_prefixed` (6,380 rows)
2. `fred_macro_expanded.parquet` → `raw_intelligence.fred_macro_expanded` (9,452 rows)
3. `weather_granular.parquet` → `raw_intelligence.weather_granular` (9,438 rows)
4. `cftc_commitments.parquet` → `raw_intelligence.cftc_commitments` (522 rows)
5. `alpha_vantage_features.parquet` → `raw_intelligence.alpha_vantage_features` (10,719 rows)

**Action**: Create/run load script:
```python
# scripts/migration/load_staging_to_bigquery.py
# Load all 19 staging files to appropriate BigQuery tables
# Use MERGE pattern for incremental updates
# Validate no placeholders before loading
```

---

### PHASE 2: DATA MIGRATION (Do Next - 4-6 hours)

#### 2.1 Migrate Legacy Data to New Structure
**Status**: Legacy data exists in `forecasting_data_warehouse`, `models_v4`

**Key Migrations**:
- `forecasting_data_warehouse.*` → `market_data.*` (with `fwd_` prefix initially)
- `models_v4.production_training_data_*` → `training.zl_training_prod_allhistory_*`
- `yahoo_finance_comprehensive.*` → `market_data.yahoo_historical_*`

**Action**: 
1. Create backup datasets first
2. Copy legacy tables to new structure
3. Validate row counts match
4. Update references

#### 2.2 Fix Training Table Issues
**Status**: Training tables have placeholder data (from audit findings)

**Issues to Fix**:
- Remove placeholder data (regime='allhistory', weight=1)
- Add pre-2020 data (currently missing 2000-2019)
- Fix regime assignments (need 7+ regimes, not 1-3)
- Fix training weights (should be 50-1000, not all 1)

**Action**:
```sql
-- Fix regime assignments
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  regime = rc.regime,
  training_weight = rw.weight
FROM `cbi-v14.regimes.regime_calendar` rc
JOIN `cbi-v14.regimes.regime_weights` rw ON rc.regime = rw.regime
WHERE t.date = rc.date;

-- Load pre-2020 data from archive
INSERT INTO `cbi-v14.training.zl_training_prod_allhistory_1m`
SELECT * FROM `cbi-v14.archive.pre_crisis_2000_2007_historical`
WHERE date < '2020-01-01';
```

#### 2.3 Build Master Features Table
**Status**: `features.master_features` needs to be built from joined data

**Action**:
1. Run join_executor to create final joined dataset
2. Export to parquet
3. Load to `features.master_features` in BigQuery
4. Validate: 400+ columns, no placeholders, proper date range

---

### PHASE 3: CLEANUP & CONSOLIDATION (Do After Data Loaded - 2-3 hours)

#### 3.1 Archive Legacy Datasets
**Status**: Multiple backup datasets cluttering project

**Action**:
```bash
# Create single archive dataset
bq mk --location=us-central1 cbi-v14.z_archive_20251119

# Move all backups there
# Then delete backup datasets
```

**Datasets to Archive**:
- `archive_backup_20251115`
- `dashboard_backup_20251115_final`
- `features_backup_20251115`
- `features_backup_20251117`
- `model_backups_oct27`
- `models_v5`
- Any other `*_backup_*` datasets

#### 3.2 Consolidate Duplicate Datasets
**Status**: `forecasting_data_warehouse` vs `market_data` confusion

**Action**:
1. Migrate all real data from `forecasting_data_warehouse` to `market_data`
2. Validate no data loss
3. Archive `forecasting_data_warehouse` (don't delete yet)
4. Update all references

#### 3.3 Fix Location Issues
**Status**: Some datasets may be in wrong region (US multi-region vs us-central1)

**Action**:
```sql
-- Check all dataset locations
SELECT schema_name, location
FROM `cbi-v14.INFORMATION_SCHEMA.SCHEMATA`
WHERE location != 'us-central1';
```

**Note**: Can't change location after creation - must recreate if wrong

---

### PHASE 4: PIPELINE INTEGRATION (Do After Structure Fixed - 3-4 hours)

#### 4.1 Update Ingestion Scripts
**Status**: Scripts may still write to old datasets

**Action**: Update all ingestion scripts to write to new structure:
- `scripts/ingest/*.py` → Write to `raw_intelligence.*`
- `scripts/ingest/collect_databento_*.py` → Write to `market_data.*`
- `scripts/ingest/collect_alpha_*.py` → Write to `raw_intelligence.*`

#### 4.2 Create Sync Scripts
**Status**: Need automated sync from staging → BigQuery

**Action**: Create:
- `scripts/sync/sync_staging_to_bigquery.py` - MERGE staging files to BQ
- `scripts/sync/sync_features_to_bigquery.py` - MERGE features to BQ
- Use MERGE pattern (not WRITE_TRUNCATE) for incremental updates

#### 4.3 Set Up Scheduled Queries
**Status**: Need automated feature engineering in BigQuery

**Action**: Create scheduled queries for:
- Daily feature aggregation
- Regime assignments
- Signal calculations
- Hidden relationship signals (from news)

---

### PHASE 5: VALIDATION & MONITORING (Ongoing)

#### 5.1 Data Quality Checks
**Status**: Need automated validation

**Action**: Create validation queries:
```sql
-- No placeholders
SELECT COUNT(*) FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
WHERE regime = 'allhistory' OR training_weight = 1;
-- Must return 0

-- Date coverage
SELECT MIN(date), MAX(date), COUNT(*) 
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`;
-- Must show 2000-2025

-- Regime diversity
SELECT regime, COUNT(*) 
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
GROUP BY regime;
-- Must show 7+ regimes
```

#### 5.2 Create Monitoring Dashboard
**Status**: Need visibility into data health

**Action**: Create views/tables for:
- Data quality metrics
- Ingestion health
- Table row counts
- Date coverage
- Regime distribution

---

## 📋 EXECUTION CHECKLIST

### Immediate (Today)
- [ ] Verify all 12 core datasets exist in us-central1
- [ ] Create missing datasets (`signals`, `regimes`, `neural`, etc.)
- [ ] Execute news collection DDL
- [ ] Load top 5 priority staging files to BigQuery
- [ ] Validate loaded data (no placeholders)

### This Week
- [ ] Load all 19 staging files to BigQuery
- [ ] Migrate legacy data from `forecasting_data_warehouse`
- [ ] Fix training table placeholder issues
- [ ] Build `features.master_features` table
- [ ] Archive legacy/backup datasets
- [ ] Update ingestion scripts to new structure

### Next Week
- [ ] Set up scheduled queries for feature engineering
- [ ] Create sync scripts for automated updates
- [ ] Set up monitoring and validation
- [ ] Update dashboard to use new views
- [ ] Complete cutover from legacy to new structure

---

## 🚨 CRITICAL SUCCESS FACTORS

1. **NO PLACEHOLDERS**: Every data load must be validated
2. **BIGQUERY FIRST**: All ingestion goes to BigQuery first (not external drive)
3. **PROPER LOCATION**: All datasets must be in `us-central1`
4. **VALIDATION GATES**: Every migration step must pass validation
5. **BACKUP FIRST**: Always backup before migrating
6. **MERGE NOT TRUNCATE**: Use MERGE for incremental updates

---

## 📊 EXPECTED OUTCOMES

After completion:
- ✅ 12 core datasets in us-central1 (clean structure)
- ✅ All staging data loaded to BigQuery
- ✅ Legacy data migrated and archived
- ✅ Training tables fixed (no placeholders, full date range, proper regimes)
- ✅ Master features table built (400+ columns)
- ✅ Automated sync pipelines running
- ✅ Monitoring and validation in place

---

## 🔗 RELATED DOCUMENTS

- `docs/migration/BIGQUERY_REVERSE_ENGINEERED_MIGRATION.md` - Detailed migration plan
- `docs/migration/BIGQUERY_MIGRATION_FAILURE_ANALYSIS_AND_RECOVERY.md` - Recovery plan
- `docs/plans/FRESH_START_MASTER_PLAN.md` - Overall project plan
- `docs/audit/FRESH_AUDIT_20251119_191350.md` - Latest audit findings
- `docs/plans/TABLE_MAPPING_MATRIX.md` - Complete mapping reference

---

**Priority**: 🔥 CRITICAL - Start with Phase 1 immediately

