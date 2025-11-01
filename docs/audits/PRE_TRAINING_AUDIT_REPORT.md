# PRE-TRAINING AUDIT REPORT - NOVEMBER 1, 2025
**THE SINGLE SOURCE OF TRUTH FOR ALL AUDIT FINDINGS**

**Date:** November 1, 2025  
**Auditor:** AI Assistant  
**Purpose:** Comprehensive deep-dive audit of BQML migration plan before execution  
**Scope:** All schemas, tables, rows, mechanisms, scripts, datasets + multiple review checkpoints

---

## EXECUTIVE SUMMARY

**STATUS:** 🟡 **1 CRITICAL BLOCKER FOUND** - Plan requires fix before execution

**Current Plan:** BQML BOOSTED_TREE migration (4 horizons × 3 quantiles = 12 models)  
**Reality Check:** BQML BOOSTED_TREE does NOT support quantile regression - only mean regression  
**Critical Finding:** Cannot train q10/q90 models directly. Must use residual-based quantiles.

**Tested & Verified:**
- ✅ ML.PREDICT works (returns mean predictions)
- ✅ ML.EXPLAIN_PREDICT works (returns feature attributions)
- ✅ Data quality excellent (1,251 rows, 205 features, no duplicates)
- ✅ Existing models available (4 BOOSTED_TREE models exist)

**Required Fix:** Change from 12 models to 4 models + residual quantiles (Option D)

---

## 🚨 CRITICAL BLOCKER #1: QUANTILE REGRESSION NOT SUPPORTED

### **Problem:**
Plan assumes training 12 models (4 horizons × 3 quantiles: q10, mean, q90), but **BQML BOOSTED_TREE_REGRESSOR only supports mean regression**.

### **Evidence (TESTED):**
- ✅ **ML.PREDICT tested:** Only returns `predicted_target_1m` (mean prediction)
- ✅ **Model options verified:** No `objective`, `alpha`, or quantile parameters available
- ✅ **Existing models checked:** All 4 BOOSTED_TREE models are mean-only
- ✅ **BQML documentation:** BOOSTED_TREE_REGRESSOR only supports squared error loss (mean regression)

### **Impact:**
❌ **PLAN CANNOT BE EXECUTED AS WRITTEN**

### **Recommended Fix: Option D - Residual-Based Quantiles** ✅

**How it works:**
1. Train 4 mean-only models (1W, 1M, 3M, 6M) instead of 12
2. Generate predictions on training set
3. Compute residuals: `residual = actual - predicted`
4. Store residual distributions (q10/q90 percentiles) per horizon
5. At prediction time: `q10 = mean - residual_q90`, `q90 = mean + residual_q90`

**Pros:**
- ✅ Uses existing BQML mean models
- ✅ No additional training cost
- ✅ Quantiles reflect actual model uncertainty
- ✅ Simple to implement

**Cons:**
- ⚠️ Assumes residual distribution is stable
- ⚠️ May not capture heteroskedasticity perfectly

**Implementation Required:**
- Create `residual_distributions` table: `horizon`, `q10_residual`, `q90_residual`, `mean_residual`, `stddev_residual`
- Update prediction job to compute quantiles post-hoc
- Populate `q10` and `q90` columns in `predictions_1m` from residuals

---

## ⚠️ MAJOR ISSUES FOUND

### **Issue #2: Column Count Mismatch**
- **Plan claims:** 206 features
- **Actual count:** 205 features (210 total - 4 targets - 1 date = 205)
- **Impact:** Minor (documentation fix only)
- **Fix:** Update plan to say "205 features"

### **Issue #3: Script Incompatibility**
- **Problem:** Existing scripts designed for Vertex AI endpoints
- **Files needing rewrite:**
  - `scripts/1m_feature_assembler.py` - Currently assembles for Vertex endpoints
  - `scripts/1m_predictor_job_bqml.py` - Doesn't exist, needs creation
- **Fix:** Rewrite to use `ML.PREDICT` instead of endpoint calls

### **Issue #4: Prediction Table Assumes Quantiles**
- **Problem:** `predictions_1m` table has `q10` and `q90` columns
- **Fix:** Update prediction job to compute quantiles from residuals (Option D approach)

---

## ✅ POSITIVE FINDINGS (TESTED & VERIFIED)

### **1. ML.PREDICT Works** ✅
**Test Result:**
```
✅ Syntax correct
✅ Returns predicted_target_1m column (mean predictions)
✅ Works with existing BOOSTED_TREE models
✅ No label leakage detected in tests
✅ Output includes all 205 feature columns (for reference)
```

### **2. ML.EXPLAIN_PREDICT Works** ✅
**Test Result:**
```
✅ Provides feature attributions (top-K)
✅ Output format: top_feature_attributions array with feature and attribution
✅ Good enough for dashboard tooltips (can increase top_k parameter)
✅ Example: [{'feature': 'corn_price', 'attribution': -8.18}, ...]
✅ Also includes: baseline_prediction_value, prediction_value, approximation_error
```

### **3. Data Quality Excellent** ✅
- ✅ 1,251 rows total
- ✅ 1,251 unique dates (no duplicates - old issue fixed)
- ✅ Date range: 2020-10-21 to 2025-10-13
- ✅ 205 features clean
- ✅ Targets have good variance (stddev ~11 for all horizons)

### **4. Existing Models Available** ✅
- ✅ 4 BOOSTED_TREE models exist (1W, 1M, 3M, 6M)
- ✅ Created: October 28, 2025
- ✅ Can be used for mean predictions immediately (tested - no label leakage)

### **5. Target Coverage Good** ✅
| Target | Rows Available | Coverage | Status |
|--------|---------------|----------|--------|
| target_1w | 1,251 | 100% | ✅ Perfect |
| target_1m | 1,228 | 98.16% | ✅ Excellent |
| target_3m | 1,168 | 93.37% | ✅ Good |
| target_6m | 1,078 | 86.17% | ✅ Acceptable |

---

## 📊 SCHEMA AUDIT RESULTS

### **Training Dataset:**
- **Total columns:** 210 ✅
- **Target columns:** 4 ✅ (target_1w, target_1m, target_3m, target_6m)
- **Date column:** 1 ✅
- **Feature columns:** 205 ✅ (plan incorrectly says 206)
- **Total rows:** 1,251 ✅
- **Unique dates:** 1,251 ✅ (no duplicates - old issue was fixed)
- **Date range:** 2020-10-21 to 2025-10-13 ✅

### **Features View (to be created):**
- **View name:** `models_v4.features_1m_clean`
- **SQL:** `SELECT * EXCEPT(date, target_1w, target_1m, target_3m, target_6m) FROM training_dataset_super_enriched`
- **Expected columns:** 205 features ✅
- **Status:** ⏳ Not created yet (Phase 1)

---

## 🔍 MECHANISM AUDIT (ALL TESTED)

### **BQML Training Mechanism:**
- ✅ `CREATE MODEL` syntax correct
- ✅ `EXCEPT` clause works for excluding targets (tested)
- ✅ `WHERE target_* IS NOT NULL` filter works
- ❌ **Quantile training NOT supported** (critical blocker)

### **Prediction Mechanism:**
- ✅ `ML.PREDICT` syntax works (tested on existing model)
- ✅ Output format confirmed: `predicted_target_1m` column
- ❌ **Quantile predictions NOT available directly** (need residual approach)

### **Explainability Mechanism:**
- ✅ `ML.EXPLAIN_PREDICT` works (tested on existing model)
- ✅ Output format confirmed: `top_feature_attributions` array
- ✅ Provides feature-level attributions (good enough for dashboard)

---

## 📋 SCRIPT AUDIT

### **Existing Scripts Status:**

| Script | Status | Issue | Action Required |
|--------|--------|-------|-----------------|
| `scripts/1m_feature_assembler.py` | ⚠️ Exists | Designed for Vertex AI | Rewrite for BQML |
| `scripts/1w_signal_computer.py` | ✅ Exists | May work as-is | Verify compatibility |
| `scripts/train_all_bqml_models.py` | ❌ Missing | Doesn't exist | Create |
| `scripts/validate_bqml_models.py` | ❌ Missing | Doesn't exist | Create |
| `scripts/export_bqml_feature_schema.py` | ❌ Missing | Doesn't exist | Create |
| `scripts/1m_predictor_job_bqml.py` | ❌ Missing | Doesn't exist | Create |
| `scripts/calculate_shap_drivers_bqml.py` | ❌ Missing | Doesn't exist | Create |

### **Scripts Requiring Rewrite:**
1. **Feature Assembler:** Remove Vertex AI endpoint calls, add SQL-based assembly
2. **Predictor Job:** Create new script using `ML.PREDICT` + residual quantiles
3. **SHAP Calculator:** Use `ML.EXPLAIN_PREDICT` (already tested, works)

---

## 🗂️ TABLE AUDIT

### **Existing Tables:**

| Table | Status | Schema | Notes |
|-------|--------|--------|-------|
| `predictions_1m` | ✅ Exists | Has q10/mean/q90 columns | Needs residual quantile population |
| `signals_1w` | ✅ Exists | Has signal_name/value structure | Compatible |
| `agg_1m_latest` | ⏳ View | Aggregates predictions | Needs creation/update |
| `shap_drivers` | ✅ Exists | Has feature/attribution columns | Compatible |

### **Tables to Create:**
- ⏳ `residual_distributions` (NEW - for residual-based quantiles)
  - Columns: `horizon`, `q10_residual`, `q90_residual`, `mean_residual`, `stddev_residual`

---

## ✅ REVIEW CHECKPOINTS (MULTIPLE REVIEWS BETWEEN PHASES)

### **After Phase 1 (Training):**
1. ✅ Verify all 4 models trained successfully (not 12)
2. ✅ Run `ML.EVALUATE` on each model (MAE, RMSE, R²)
3. ✅ Test `ML.PREDICT` on one model (verify output format)
4. ✅ Compute residual distributions (verify q10/q90 residuals calculated)
5. ✅ Check training costs (should be $0 - within free tier)
6. ✅ Verify no label leakage (test prediction with clean features)

### **After Phase 2 (Predictions):**
1. ✅ Verify `predictions_1m` table populated with D+1 to D+30 rows
2. ✅ Check q10/mean/q90 values are reasonable (q10 < mean < q90)
3. ✅ Verify no NULL predictions
4. ✅ Test prediction job runs end-to-end
5. ✅ Verify residual quantiles applied correctly
6. ✅ Test gate blend for D+1-7 (verify blended flag)

### **After Phase 3 (1W Signals):**
1. ✅ Verify `signals_1w` table populated
2. ✅ Check all 4 signals computed correctly
3. ✅ Verify rolled_forecast_7d_json has 7 elements

### **After Phase 4 (Aggregation):**
1. ✅ Verify `agg_1m_latest` view returns data
2. ✅ Check aggregation logic correct (AVG, not PERCENTILE_CONT)

### **After Phase 9 (SHAP):**
1. ✅ Verify `ML.EXPLAIN_PREDICT` works
2. ✅ Check SHAP values stored in `shap_drivers` table
3. ✅ Verify business labels mapped correctly (226 features)
4. ✅ Test explainability API route

---

## 📋 REQUIRED FIXES BEFORE EXECUTION

### **Priority 1: CRITICAL (Blocks Execution)**

1. **Choose and Implement Quantile Approach** ⚠️ **REQUIRED**
   - **Recommended:** Option D (Residual-Based Quantiles)
   - Update plan: Change from 12 models to 4 models
   - Add residual distribution calculation step
   - Update prediction job for quantile computation

### **Priority 2: MAJOR (Script Rewrites)**

2. **Rewrite Feature Assembler**
   - Remove Vertex AI endpoint calls
   - Add SQL-based feature assembly
   - Add 1W signal join logic

3. **Create BQML Predictor Job**
   - Use `ML.PREDICT` for mean predictions
   - Compute quantiles from residuals
   - Apply gate blend logic
   - Write to `predictions_1m`

4. **Create Missing Scripts**
   - `train_all_bqml_models.py`
   - `validate_bqml_models.py`
   - `calculate_shap_drivers_bqml.py`

### **Priority 3: MINOR (Documentation)**

5. **Fix Column Count**
   - Update plan: 205 features (not 206)

---

## 🎯 REALISTIC FEASIBILITY ASSESSMENT

### **Can This Plan Work?**

**Current State:** ❌ **NO - Quantile blocker**

**After Fixes (Option D):** ✅ **YES - With residual-based quantiles**

### **Estimated Additional Work:**
- Quantile solution design: 1 hour (Option D)
- Residual distribution calculation: 1 hour
- Prediction job update (quantile computation): 1 hour
- Script rewrites: 4-6 hours
- Testing & validation: 2-3 hours
- **Total: 9-12 hours additional work**

---

## ✅ GO/NO-GO DECISION

### 🟡 **CONDITIONAL GO** - Can proceed after quantile fix

**Reason:** Plan is 90% ready, but quantile approach must be fixed first

**Time to Fix:** 9-12 hours (includes script rewrites)

**Once Fixed:** Platform ready for BQML training and predictions

---

## 📊 EXPECTED OUTCOMES (AFTER FIXES)

### **Models to Train:**
```
1. bqml_1w_mean (mean-only)
2. bqml_1m_mean (mean-only)
3. bqml_3m_mean (mean-only)
4. bqml_6m_mean (mean-only)
-------------------------------------------------
TOTAL: 4 models (not 12)
```

### **Quantile Generation:**
- Residual distributions computed per horizon
- q10/q90 computed post-hoc from residuals
- Quantiles reflect actual model uncertainty

### **Expected Performance:**
- Mean predictions: Similar to existing BOOSTED_TREE models
- Quantile coverage: Based on historical residuals (should be ~80% coverage)
- Training time: ~2-3 hours total (4 models)
- Cost: $0 (within free tier)

---

## 🔄 CHANGES FROM OLD AUDITS

### **Resolved Issues (October 22, 2025 Audit):**
- ✅ **Duplicate dates:** Fixed (no duplicates found in current dataset)
- ✅ **Seasonality view:** Issue resolved or view no longer used
- ✅ **Dataset structure:** Now uses `training_dataset_super_enriched` (clean)

### **New Issues Found (November 1, 2025 Audit):**
- ❌ **Quantile regression:** Not supported (critical blocker)
- ⚠️ **Column count:** Plan says 206, actual is 205 (minor)
- ⚠️ **Script compatibility:** Needs BQML rewrite (major)

### **Plan Evolution:**
- **Old (Oct 22):** 16 models (4 horizons × 4 algorithms: LightGBM, DNN, ARIMA, Linear)
- **Current (Nov 1):** 4 models (4 horizons × 1 algorithm: BQML BOOSTED_TREE mean-only) + residual quantiles

---

**Report Generated:** November 1, 2025  
**Next Action:** Implement residual-based quantile approach  
**Time to Execution:** ~9-12 hours after fix

**THIS IS THE SINGLE SOURCE OF TRUTH FOR ALL AUDIT FINDINGS**  
**All other audit files have been archived to `archive/audit_consolidation_nov1_2025/`**
