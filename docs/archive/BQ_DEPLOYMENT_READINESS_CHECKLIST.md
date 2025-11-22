---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# BigQuery Deployment Readiness Checklist
**Date:** November 18, 2025  
**Status:** Pre-Deployment - Action Items Required

---

## ✅ Pre-Deployment Sign-Off

**IMPORTANT:** All items must be signed off before deployment proceeds.

### Validation & Testing
- [ ] **Schema SQL validated** (sqlfluff/dry-run passed)  
  Owner: _____________ Date: _________  
  Evidence: `DEPLOYMENT_VALIDATION_REPORT.md`

- [ ] **Scripts linted** (shellcheck passed)  
  Owner: _____________ Date: _________  
  Evidence: Linting report in validation output

- [ ] **Python tests passed** (unit tests completed)  
  Owner: _____________ Date: _________  
  Evidence: Test execution logs

- [ ] **Environment diff audit reviewed**  
  Owner: _____________ Date: _________  
  Evidence: `BQ_CURRENT_STATE_REPORT.md`

### Safety & Recovery
- [ ] **Idempotency verified** (scripts can run multiple times safely)  
  Owner: _____________ Date: _________  
  Evidence: Code review of deployment scripts

- [ ] **Rollback plan documented**  
  Owner: _____________ Date: _________  
  Evidence: Backup datasets created, restore procedures documented

- [ ] **Backups verified**  
  Owner: _____________ Date: _________  
  Evidence: Backup datasets exist with row counts matching

### Dry Run Execution
- [ ] **Dry run executed and reviewed**  
  Owner: _____________ Date: _________  
  Evidence: `DEPLOYMENT_DRY_RUN_RESULTS.md`  
  Command: `./scripts/deployment/deploy_bq_schema.sh --dry-run`

- [ ] **Validation script dry-run passed**  
  Owner: _____________ Date: _________  
  Evidence: Validation output logs

### Approvals
- [ ] **Technical Lead Approval**  
  Name: _____________ Date: _________

- [ ] **Deployment Window Scheduled**  
  Date/Time: _____________ Duration: _________

---

## 🎯 Current State Summary

✅ **Confirmed:** Assessment accurate - key gaps identified  
❌ **Missing:** 4 datasets, 40+ tables, overlay views, live folders  
⚠️ **Legacy:** Old tables with unprefixed columns need migration

---

## 📋 Pre-Deployment Actions Required

### Phase 1: Create Missing Datasets (4 datasets)

**Action:** Run `PRODUCTION_READY_BQ_SCHEMA.sql` to create:

```sql
CREATE SCHEMA IF NOT EXISTS regimes;
CREATE SCHEMA IF NOT EXISTS drivers;
CREATE SCHEMA IF NOT EXISTS dim;
CREATE SCHEMA IF NOT EXISTS ops;
```

**Status:** ❌ **NOT DONE**  
**Command:** `bq query --use_legacy_sql=false < PRODUCTION_READY_BQ_SCHEMA.sql`

---

### Phase 2: Create Missing Tables (40+ tables)

#### `market_data` Dataset (9 tables missing)
- ❌ `databento_futures_ohlcv_1m`
- ❌ `databento_futures_ohlcv_1d`
- ❌ `databento_futures_continuous_1d`
- ❌ `roll_calendar`
- ❌ `futures_curve_1d`
- ❌ `cme_indices_eod`
- ❌ `fx_daily`
- ❌ `orderflow_1m`
- ❌ `yahoo_zl_historical_2000_2010`

**Action:** Run schema script - these tables are defined in `PRODUCTION_READY_BQ_SCHEMA.sql`

#### `raw_intelligence` Dataset (9 tables missing)
- ❌ `fred_economic`
- ❌ `eia_biofuels`
- ❌ `usda_granular`
- ❌ `weather_segmented`
- ❌ `weather_weighted`
- ❌ `cftc_positioning`
- ❌ `policy_events`
- ❌ `volatility_daily`
- ❌ `news_intelligence`
- ❌ `news_bucketed`

**Action:** Run schema script

#### `signals` Dataset (6 tables missing)
- ❌ `big_eight_live` ⚠️ **CRITICAL** (dashboard dependency)
- ❌ `calendar_spreads_1d`
- ❌ `crush_oilshare_daily`
- ❌ `energy_proxies_daily`
- ❌ `calculated_signals`
- ❌ `hidden_relationship_signals` (exists in schema, needs creation)

**Action:** Run schema script

#### `training` Dataset (12 MES tables missing)
- ❌ `mes_training_prod_allhistory_1min`
- ❌ `mes_training_prod_allhistory_5min`
- ❌ `mes_training_prod_allhistory_15min`
- ❌ `mes_training_prod_allhistory_30min`
- ❌ `mes_training_prod_allhistory_1hr`
- ❌ `mes_training_prod_allhistory_4hr`
- ❌ `mes_training_prod_allhistory_1d`
- ❌ `mes_training_prod_allhistory_7d`
- ❌ `mes_training_prod_allhistory_30d`
- ❌ `mes_training_prod_allhistory_3m`
- ❌ `mes_training_prod_allhistory_6m`
- ❌ `mes_training_prod_allhistory_12m`

**Action:** Run schema script

#### `features` Dataset (1 table needs rebuild)
- ⚠️ `master_features` - **EXISTS as `master_features_canonical`** but has OLD column names
  - Current: `yahoo_open`, `alpha_open` (not prefixed)
  - Required: `yahoo_zl_open`, `databento_zl_open` (prefixed)

**Action:** 
1. Create new `master_features` table with correct schema
2. Migrate/rebuild data with prefixed columns
3. Update all references

#### `regimes` Dataset (1 table missing)
- ❌ `market_regimes`

**Action:** Run schema script

#### `drivers` Dataset (2 tables missing)
- ❌ `primary_drivers`
- ❌ `meta_drivers`

**Action:** Run schema script

#### `neural` Dataset (1 table missing)
- ❌ `feature_vectors`

**Action:** Run schema script

#### `dim` Dataset (3 tables missing)
- ❌ `instrument_metadata`
- ❌ `production_weights`
- ❌ `crush_conversion_factors`

**Action:** Run schema script

#### `ops` Dataset (2 tables missing)
- ❌ `ingestion_runs`
- ❌ `data_quality_events`

**Action:** Run schema script

---

### Phase 3: Create External Drive Folders

**Action:** Create live data collection folders

```bash
mkdir -p "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/live"
mkdir -p "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/live_continuous"
```

**Status:** ❌ **NOT DONE**

**Structure:**
```
TrainingData/
├── live/
│   ├── ZL/
│   │   └── 1m/
│   │       └── date=YYYY-MM-DD/
│   ├── MES/
│   │   └── 1m/
│   │       └── date=YYYY-MM-DD/
│   └── ES/
│       └── 1m/
│           └── date=YYYY-MM-DD/
└── live_continuous/
    ├── ZL/
    │   └── 1m/
    │       └── date=YYYY-MM-DD/
    └── MES/
        └── 1m/
            └── date=YYYY-MM-DD/
```

---

### Phase 4: Create Overlay Views (31 views)

**Action:** Create `scripts/deployment/create_overlay_views.sql`

**Views Required:**
- 17 API overlay views (`api.vw_futures_overlay_*`)
- 5 Prediction overlay views (`predictions.vw_zl_*_latest`)
- 1 Regime overlay view (`regimes.vw_live_regime_overlay`)
- 5 Compatibility views (`training.vw_zl_training_*`)
- 1 Signals composite view (`signals.vw_big_seven_signals`)
- 2 MES overlay views (`features.vw_mes_*`)

**Status:** ❌ **NOT DONE** (SQL file needs creation)

---

### Phase 5: Update Legacy Tables

#### Tables Needing Migration/Rebuild

1. **`features.master_features_canonical`** → **`features.master_features`**
   - **Issue:** Old column names (`yahoo_open`, `alpha_open`)
   - **Action:** Rebuild with prefixed columns (`yahoo_zl_open`, `databento_zl_open`)
   - **Method:** 
     - Create new table with correct schema
     - Migrate data with column mapping
     - Update all view references

2. **`neural.vw_big_eight_signals`** (VIEW)
   - **Issue:** References old signal views, not `signals.big_eight_live` table
   - **Action:** Update view to read from `signals.big_eight_live` table
   - **Or:** Drop view and use table directly

3. **ZL Training Tables** (5 tables exist with old naming)
   - **Status:** ✅ Tables exist but need verification
   - **Action:** Verify schema matches new naming convention
   - **Check:** Column names, partitioning, clustering

---

### Phase 6: Data Migration Strategy

#### Step 1: Backup Legacy Tables
```bash
# Create backup datasets
bq mk cbi-v14:market_data_backup_20251118
bq mk cbi-v14:features_backup_20251118
bq mk cbi-v14:training_backup_20251118
```

#### Step 2: Map Old → New Tables
- `yahoo_finance_enhanced` → `market_data.yahoo_zl_historical_2000_2010`
- `master_features_canonical` → `features.master_features` (with column mapping)
- Old signal views → `signals.big_eight_live` table

#### Step 3: Migrate Data
- Use `bq cp` for simple copies
- Use `bq query` with `INSERT INTO ... SELECT` for column mapping
- Verify row counts match

#### Step 4: Update References
- Update all views to point to new tables
- Update dashboard queries
- Update training export scripts

---

## ✅ Deployment Readiness Checklist

### Prerequisites
- [ ] Run `PRODUCTION_READY_BQ_SCHEMA.sql` to create all datasets and tables
- [ ] Create external drive folders (`live/`, `live_continuous/`)
- [ ] Create overlay views SQL script
- [ ] Backup legacy tables to `*_backup_YYYYMMDD` datasets

### Data Migration
- [ ] Migrate `master_features_canonical` → `master_features` with prefixed columns
- [ ] Verify ZL training tables have correct schema
- [ ] Map and migrate old signal views → `signals.big_eight_live`
- [ ] Verify row counts match between old and new tables

### View Updates
- [ ] Update `neural.vw_big_eight_signals` to use new table
- [ ] Create all 31 overlay views
- [ ] Test view queries return expected results

### Validation
- [ ] Verify all 12 datasets exist
- [ ] Verify all 55+ tables exist with correct schema
- [ ] Verify partitioning and clustering are correct
- [ ] Verify all views can query successfully
- [ ] Test Big 8 refresh job end-to-end

### Documentation
- [ ] Update table mapping matrix with old → new mappings
- [ ] Document migration steps taken
- [ ] Update deployment scripts

---

## 🚀 Deployment Command Sequence

### Step 1: Create Schema
```bash
cd /Users/kirkmusick/Documents/GitHub/CBI-V14
bq query --use_legacy_sql=false < PRODUCTION_READY_BQ_SCHEMA.sql
```

### Step 2: Create Folders
```bash
mkdir -p "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/live"
mkdir -p "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/live_continuous"
```

### Step 3: Create Overlay Views
```bash
# After creating scripts/deployment/create_overlay_views.sql
bq query --use_legacy_sql=false < scripts/deployment/create_overlay_views.sql
```

### Step 4: Migrate Data
```bash
# Run migration scripts (to be created)
python3 scripts/migration/migrate_master_features.py
python3 scripts/migration/migrate_signals.py
```

### Step 5: Validate
```bash
python3 scripts/validation/validate_bq_deployment.py
```

---

## ⚠️ Critical Dependencies

1. **`signals.big_eight_live`** - Dashboard reads from this (must exist)
2. **`features.master_features`** - Training exports read from this (must have prefixed columns)
3. **All MES training tables** - Training pipeline requires all 12 horizons
4. **Overlay views** - Dashboard queries depend on these views

---

## 📊 Current vs. Required State

| Component | Current | Required | Status |
|-----------|---------|----------|--------|
| Datasets | 8/12 | 12/12 | ❌ 4 missing |
| Market Data Tables | 4 legacy | 9 new | ❌ All missing |
| Training Tables | 5 ZL | 17 total | ❌ 12 MES missing |
| Signals Tables | Views only | 6 tables | ❌ All missing |
| Features Table | Old cols | Prefixed | ⚠️ Needs rebuild |
| Overlay Views | 0 | 31 | ❌ All missing |
| Live Folders | 0 | 2 | ❌ Missing |

---

## 🎯 Ready for Deployment?

**Current Status:** ❌ **NOT READY**

**Blockers:**
1. Missing 4 datasets (regimes, drivers, dim, ops)
2. Missing 40+ tables
3. Missing overlay views
4. Missing live folders
5. Legacy tables need migration

**Estimated Time to Ready:**
- Schema creation: 15 minutes
- Folder creation: 2 minutes
- Overlay views creation: 30 minutes
- Data migration: 2-4 hours (depending on data volume)
- Validation: 30 minutes

**Total:** ~3-5 hours to deployment-ready state

---

## 🔒 Deployment Approval Gate

**STOP:** Before executing deployment, verify all sign-offs above are complete.

**Run pre-flight validation:**
```bash
./scripts/deployment/pre_flight_validation.sh
```

**If all checks pass:**
```bash
# 1. Dry run first
./scripts/deployment/deploy_bq_schema.sh --dry-run

# 2. Review dry run results

# 3. Execute actual deployment
./scripts/deployment/deploy_bq_schema.sh
```

---
**Next Action:** Complete pre-deployment sign-offs above, then run pre-flight validation

**See:** `DEPLOYMENT_EXECUTION_PLAN.md` for step-by-step execution guide

