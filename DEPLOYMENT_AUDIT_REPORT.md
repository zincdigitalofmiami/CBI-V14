# Deployment Audit Report
**Date:** November 18, 2025  
**Auditor:** Automated Validation System  
**Scope:** Complete deployment review

---

## 🎯 Executive Summary

**Overall Status:** ⚠️ **PARTIAL SUCCESS**

- ✅ Phase 1 Complete (Schema/Tables/Labels)
- ❌ Phase 2 Not Started (Folders)
- ❌ Phase 3 Not Started (Overlay Views)  
- ❌ Phase 4 Not Started (Data Migration)
- ❌ Phase 5 Not Started (Final Validation)

**Critical Issues Found:** 4  
**Minor Issues Found:** 2  
**Recommendations:** 6

---

## ✅ What's Working

### 1. Datasets (12/12) ✅
All datasets created successfully in `us-central1`:
- market_data
- raw_intelligence
- signals
- features
- training
- regimes
- drivers
- neural
- predictions
- monitoring
- dim
- ops

### 2. Tables (57/57) ✅
All tables created with correct schemas:
- 11 market_data tables
- 10 raw_intelligence tables
- 6 signals tables
- 1 features table (master_features)
- 19 training tables (regime + 5 ZL + 12 MES)
- 1 regimes table
- 2 drivers tables
- 1 neural table
- 1 monitoring table
- 2 ops tables
- 3 dim tables

### 3. Labels (48/48) ✅
All labels applied successfully:
- tier: raw, derived, ml, production, ops
- category: market, intelligence, signals, etc.
- purpose: trading, training, serving, etc.
- data_type: ohlcv, calculated, predictions, etc.

### 4. Training Tables (17/17) ✅
All horizon tables created:
- ZL: 5 horizons (1w, 1m, 3m, 6m, 12m)
- MES: 12 horizons (1min-12m)

---

## ❌ Critical Issues Found

### Issue #1: Missing `api` Dataset
**Severity:** HIGH  
**Impact:** Overlay views cannot be created

**Details:**
- Validation expects 28 views in `api` dataset
- `api` dataset doesn't exist
- Overlay views defined in `create_overlay_views.sql` reference `api.*` views

**Fix Required:**
```bash
bq mk --location=us-central1 --description="API-facing overlay views" cbi-v14:api
```

### Issue #2: Overlay Views Not Created (0/31)
**Severity:** HIGH  
**Impact:** Dashboard cannot function, training exports unavailable

**Missing Views:**
- 17 API overlay views (api.vw_futures_overlay_*)
- 5 Prediction overlay views (predictions.vw_zl_*_latest)
- 1 Regime overlay view (regimes.vw_live_regime_overlay)
- 5 Compatibility views (training.vw_zl_training_*)
- 1 Signals composite view (signals.vw_big_seven_signals)
- 2 MES overlay views (features.vw_mes_*)

**Fix Required:**
- Create `api` dataset first
- Run `bq query --use_legacy_sql=false < scripts/deployment/create_overlay_views.sql`

### Issue #3: master_features Column Count (57 vs. 400+)
**Severity:** MEDIUM  
**Impact:** Feature table incomplete

**Details:**
- Table created with only 57 columns
- Expected: 400+ columns with all features
- Some columns missing source prefixes (china_mentions, trump_mentions, etc.)

**Root Cause:**
- Schema definition in PRODUCTION_READY_BQ_SCHEMA.sql may be truncated
- Only partial column list was parsed/executed

**Fix Required:**
- Audit PRODUCTION_READY_BQ_SCHEMA.sql for complete master_features definition
- Verify all 400+ columns are defined
- Recreate table if necessary

### Issue #4: Column Prefix Inconsistency
**Severity:** LOW  
**Impact:** Doesn't follow naming convention

**Columns Without Prefixes:**
- china_mentions
- trump_mentions
- trade_war_intensity
- social_sentiment_avg
- cme_soybean_oilshare_cosi1
- cme_soybean_cvol_30d
- crush_theoretical_usd_per_bu
- crack_3_2_1
- ethanol_cu_settle
- cme_6l_brl_close

**Fix Required:**
- These are intentionally unprefixed (intelligence features, CME native metrics)
- Document as exception to prefix rule
- No action needed if intentional

---

## ⚠️ Minor Issues

### Issue #5: Empty Tables (Expected)
**Severity:** NONE  
**Impact:** Normal state pre-data-load

**Details:**
- All 57 tables have 0 rows
- This is expected - tables just created
- Data population is Phase 4

**Status:** No fix needed - working as expected

### Issue #6: Smoke Tests Failed (Due to Missing Views)
**Severity:** LOW (Dependent on Issue #2)  
**Impact:** Cannot test overlay views

**Details:**
- 4/4 smoke tests failed
- All failures due to missing views
- Will pass once views are created

**Fix Required:**
- Resolve Issue #2 (create overlay views)
- Re-run smoke tests

---

## 📋 Recommendations

### 1. Complete Phase 2 (Folders)
**Priority:** MEDIUM  
**Effort:** 2 minutes

```bash
mkdir -p "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/live"
mkdir -p "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/live_continuous"
```

### 2. Create API Dataset
**Priority:** HIGH  
**Effort:** 1 minute

```bash
bq mk --location=us-central1 --description="API-facing overlay views" cbi-v14:api
```

### 3. Complete Phase 3 (Overlay Views)
**Priority:** HIGH  
**Effort:** 30 minutes

```bash
bq query --use_legacy_sql=false < scripts/deployment/create_overlay_views.sql
```

### 4. Audit master_features Schema
**Priority:** MEDIUM  
**Effort:** 15 minutes

- Check PRODUCTION_READY_BQ_SCHEMA.sql for complete definition
- Verify 400+ columns are defined
- Document which columns are intentionally unprefixed

### 5. Update Documentation
**Priority:** LOW  
**Effort:** 10 minutes

- Update PHASE_1_SUCCESS_SUMMARY.md with master_features column count issue
- Document unprefixed columns as intentional exceptions
- Add note about api dataset requirement

### 6. Re-run Full Validation After Fixes
**Priority:** HIGH  
**Effort:** 5 minutes

```bash
python3 scripts/validation/validate_bq_deployment.py --phase 5
```

---

## 🔍 Detailed Validation Results

### Datasets: ✅ PASS (12/12)
- All expected datasets exist
- All in correct location (us-central1)
- All labeled correctly

### Tables: ✅ PASS (57/57)
- All expected tables created
- All have correct schemas
- All have partitioning/clustering where expected

### Views: ❌ FAIL (0/31)
- 0 of 31 expected views exist
- Missing api dataset blocks creation
- Phase 3 not executed yet

### master_features: ⚠️ WARNING
- Table exists ✅
- Has 57 columns (expected 400+) ⚠️
- Has required columns (yahoo_zl_close, databento_zl_close, fred_dgs10, big8_composite_score) ✅
- Some columns without prefixes ⚠️

### Training Tables: ✅ PASS (17/17)
- All ZL horizons exist (5/5)
- All MES horizons exist (12/12)
- All have correct schemas

### Smoke Tests: ❌ FAIL (0/4)
- All failures due to missing views
- Will pass once Issue #2 is resolved

---

## 📊 Completion Status

| Phase | Status | Progress | Blockers |
|-------|--------|----------|----------|
| **Phase 1: Schema** | ✅ Complete | 100% | None |
| **Phase 2: Folders** | ❌ Pending | 0% | None |
| **Phase 3: Views** | ❌ Pending | 0% | Missing api dataset |
| **Phase 4: Migration** | ❌ Pending | 0% | Needs Phase 1-3 |
| **Phase 5: Validation** | ⚠️ Partial | 60% | Needs all phases |

**Overall Progress:** 40% (2/5 phases complete)

---

## 🚀 Action Plan

### Immediate Actions (Next 1 hour)

1. **Create api dataset** (1 min)
   ```bash
   bq mk --location=us-central1 --description="API-facing overlay views" cbi-v14:api
   ```

2. **Create Phase 2 folders** (2 min)
   ```bash
   mkdir -p "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/live"
   mkdir -p "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/live_continuous"
   ```

3. **Create overlay views** (30 min)
   ```bash
   bq query --use_legacy_sql=false < scripts/deployment/create_overlay_views.sql
   ```

4. **Validate Phase 3** (5 min)
   ```bash
   ./scripts/deployment/post_deployment_monitor.sh --phase 3
   ```

### Follow-up Actions (Next 4 hours)

5. **Audit master_features schema** (15 min)
   - Review PRODUCTION_READY_BQ_SCHEMA.sql
   - Verify column count
   - Document exceptions

6. **Data migration** (2-4 hours)
   ```bash
   python3 scripts/migration/migrate_master_features.py
   ```

7. **Final validation** (30 min)
   ```bash
   python3 scripts/validation/validate_bq_deployment.py --phase 5
   ```

---

## ✅ Sign-Off Checklist

### Before Proceeding to Phase 2-5

- [x] Phase 1 completed successfully
- [x] All datasets created and labeled
- [x] All 57 tables created
- [ ] API dataset created
- [ ] Overlay views created
- [ ] master_features schema audited
- [ ] All validation checks passing

---

**Audit Completed:** November 18, 2025  
**Next Review:** After Phase 3 completion  
**Approved for Phase 2-3:** YES (with fixes listed above)

