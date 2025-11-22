---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# BigQuery Deployment Execution Plan
**Date:** November 18, 2025  
**Status:** Ready to Execute  
**Estimated Time:** 3-5 hours

Reference: `docs/plans/BIGQUERY_CENTRIC_MIGRATION_PLAN.md` — deployment aligns with the BigQuery‑centric data plane (ingest/orchestrate/serve), Mac‑centric model plane, and 5‑minute batch ingestion policy.

## 🎯 Pre-Deployment Status

**Current State:** ❌ NOT READY  
**Blockers Identified:** ✅ All documented in `BQ_DEPLOYMENT_READINESS_CHECKLIST.md`

---

## 📋 Execution Sequence

### Phase 1: Schema Deployment (15 minutes)

**Step 1.1: Create All Datasets & Tables**
```bash
cd /Users/kirkmusick/Documents/GitHub/CBI-V14

# Option A: Use deployment script (recommended)
chmod +x scripts/deployment/deploy_bq_schema.sh
./scripts/deployment/deploy_bq_schema.sh

# Option B: Direct bq command
bq query --use_legacy_sql=false < PRODUCTION_READY_BQ_SCHEMA.sql
```

**Expected Output:**
- ✅ 12 datasets created/verified
- ✅ 55+ tables created
- ✅ Critical tables validated

**Step 1.2: Apply Dataset Labels**
```bash
# Apply organizational labels to all datasets
./scripts/deployment/apply_bq_labels.sh
```

**Expected Output:**
- ✅ 12 datasets labeled with tier/category/purpose/data_type
- ✅ Datasets organized into 5 tiers (raw, derived, ml, production, ops)

**Verification:**
```bash
# Check datasets
bq ls cbi-v14 | grep -E "(regimes|drivers|dim|ops)"

# Check labels
bq ls --project_id=cbi-v14 --filter 'labels.tier:ml'

# Check critical tables
bq ls cbi-v14:signals | grep big_eight_live
bq ls cbi-v14:training | grep mes_training
bq ls cbi-v14:features | grep master_features
```

---

### Phase 2: Create External Drive Folders (2 minutes)

**Step 2.1: Create Live Data Folders**
```bash
# Create main folders
mkdir -p "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/live"
mkdir -p "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/live_continuous"

# Create symbol-specific structure
mkdir -p "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/live/ZL/1m"
mkdir -p "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/live/MES/1m"
mkdir -p "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/live/ES/1m"

mkdir -p "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/live_continuous/ZL/1m"
mkdir -p "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/live_continuous/MES/1m"
```

**Verification:**
```bash
ls -R "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/live" | head -10
ls -R "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/live_continuous" | head -10
```

---

### Phase 3: Create Overlay Views (30 minutes)

**Step 3.1: Create Overlay Views SQL File**

**Status:** ✅ **CREATED** - `scripts/deployment/create_overlay_views.sql`

**Required Views (31 total):**
- 17 API overlay views (`api.vw_futures_overlay_*`)
- 5 Prediction overlay views (`predictions.vw_zl_*_latest`)
- 1 Regime overlay view (`regimes.vw_live_regime_overlay`)
- 5 Compatibility views (`training.vw_zl_training_*`)
- 1 Signals composite view (`signals.vw_big_seven_signals`)
- 2 MES overlay views (`features.vw_mes_*`)

**Step 3.2: Execute Overlay Views**
```bash
# After creating the SQL file
bq query --use_legacy_sql=false < scripts/deployment/create_overlay_views.sql
```

**Verification:**
```bash
# Check view counts
bq ls cbi-v14:api | grep vw_futures_overlay | wc -l
bq ls cbi-v14:predictions | grep vw_zl | wc -l
bq ls cbi-v14:regimes | grep vw_live_regime_overlay
```

---

### Phase 4: Data Migration (2-4 hours)

**Step 4.1: Backup Legacy Tables**
```bash
# Create backup datasets
bq mk cbi-v14:market_data_backup_20251118
bq mk cbi-v14:features_backup_20251118
bq mk cbi-v14:training_backup_20251118
bq mk cbi-v14:signals_backup_20251118

# Copy legacy tables
bq cp cbi-v14:market_data.yahoo_finance_enhanced \
        cbi-v14:market_data_backup_20251118.yahoo_finance_enhanced

bq cp cbi-v14:features.master_features_canonical \
        cbi-v14:features_backup_20251118.master_features_canonical
```

**Step 4.2: Migrate master_features**
```bash
# Migration script ready
python3 scripts/migration/migrate_master_features.py
```

**Migration Steps:**
1. Read `features.master_features_canonical`
2. Map columns: `yahoo_open` → `yahoo_zl_open`, `alpha_open` → `databento_zl_open`
3. Insert into `features.master_features` with correct schema
4. Verify row counts match

**Step 4.3: Update Views**
```bash
# Update neural.vw_big_eight_signals to use signals.big_eight_live table
bq query --use_legacy_sql=false <<EOF
CREATE OR REPLACE VIEW cbi-v14.neural.vw_big_eight_signals AS
SELECT * FROM cbi-v14.signals.big_eight_live
ORDER BY signal_timestamp DESC;
EOF
```

**Step 4.4: Historical Data Backfill**
```bash
# Yahoo ZL 2000-2010
python3 scripts/backfill/load_yahoo_historical.py

# DataBento 2010-present
python3 scripts/backfill/load_databento_historical.py

# FRED/USDA/EIA/CFTC
python3 scripts/backfill/load_government_data.py
```

---

### Phase 5: Validation (30 minutes)

**Step 5.1: Run Validation Script**
```bash
# Validation script ready
python3 scripts/validation/validate_bq_deployment.py
```

**Validation Checks:**
- ✅ All 12 datasets exist
- ✅ All 55+ tables exist with correct schema
- ✅ All 31 overlay views exist
- ✅ Partitioning and clustering correct
- ✅ Row counts match between old and new tables
- ✅ Column names are prefixed correctly
- ✅ Critical tables have data

**Step 5.2: Manual Verification**
```bash
# Check table counts
bq ls cbi-v14:market_data | grep TABLE | wc -l  # Should be 9+
bq ls cbi-v14:training | grep TABLE | wc -l    # Should be 17+
bq ls cbi-v14:signals | grep TABLE | wc -l    # Should be 6+

# Check critical table exists
bq show cbi-v14:signals.big_eight_live

# Check master_features columns
bq query --use_legacy_sql=false \
  "SELECT COUNT(*) FROM \`cbi-v14.features.INFORMATION_SCHEMA.COLUMNS\` 
   WHERE table_name = 'master_features'"
```

---

## 🚨 Critical Dependencies

### Must Exist Before Dashboard Can Work:
1. ✅ `signals.big_eight_live` - Dashboard reads from this
2. ✅ `features.master_features` - Training exports read from this
3. ✅ `api.vw_futures_overlay_*` - Dashboard queries these views
4. ✅ `predictions.vw_zl_*_latest` - Dashboard reads predictions from these

### Must Exist Before Training Can Work:
1. ✅ All 17 training tables (5 ZL + 12 MES)
2. ✅ `features.master_features` with prefixed columns
3. ✅ `training.regime_calendar` and `training.regime_weights`

---

## 📊 Success Criteria

### Schema Deployment Complete When:
- [ ] All 12 datasets exist
- [ ] All 55+ tables created with correct schema
- [ ] All 31 overlay views created
- [ ] Partitioning and clustering verified
- [ ] No schema errors in BigQuery console

### Data Migration Complete When:
- [ ] `master_features` has prefixed columns
- [ ] Row counts match between old and new tables
- [ ] Historical data backfilled (2000-2025)
- [ ] Regime tables populated
- [ ] Big 8 refresh job can run successfully

### Deployment Ready When:
- [ ] All validation checks pass
- [ ] Dashboard can query overlay views
- [ ] Training exports can read from tables
- [ ] Big 8 refresh job runs without errors
- [ ] Live data folders exist and are writable

---

## 🔄 Rollback Plan

If deployment fails:

1. **Keep Backup Datasets:** All legacy tables backed up to `*_backup_20251118`
2. **Drop New Tables:** `bq rm -t` for any failed table creations
3. **Restore Views:** Revert `neural.vw_big_eight_signals` to original definition
4. **Document Issues:** Log all errors for retry

---

## 📝 Post-Deployment Tasks

1. **Update Dashboard Queries:** Point to new overlay views
2. **Update Training Scripts:** Use new table names
3. **Schedule Big 8 Refresh:** Set up cron for 15-minute refresh
4. **Monitor Performance:** Check query costs and performance
5. **Document Changes:** Update all documentation with new table names

---

## 🎯 Quick Start Command

```bash
# One-command deployment (full sequence)
cd /Users/kirkmusick/Documents/GitHub/CBI-V14 && \
./scripts/deployment/deploy_bq_schema.sh && \
./scripts/deployment/apply_bq_labels.sh && \
mkdir -p "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/live" && \
mkdir -p "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/live_continuous" && \
bq query --use_legacy_sql=false < scripts/deployment/create_overlay_views.sql && \
echo "✅ Schema deployment complete. Next: Run data migration scripts."
```

---
**Status:** Ready to execute Phase 1 (Schema Deployment)  
**Next Action:** Run `./scripts/deployment/deploy_bq_schema.sh`
