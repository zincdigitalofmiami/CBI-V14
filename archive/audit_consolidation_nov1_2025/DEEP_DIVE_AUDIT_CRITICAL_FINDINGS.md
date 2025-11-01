# DEEP DIVE AUDIT - CRITICAL FINDINGS
**Date:** November 1, 2025  
**Status:** 🚨 **CRITICAL ISSUES FOUND - PLAN WILL FAIL WITHOUT FIXES**

---

## 🚨 CRITICAL ISSUE #1: BQML BOOSTED_TREE DOES NOT SUPPORT QUANTILE REGRESSION

### **The Problem:**
The plan assumes we can train 3 separate BOOSTED_TREE models (q10, mean, q90) per horizon by setting `objective='quantile'` or using different loss functions. **THIS IS FALSE.**

**BQML BOOSTED_TREE_REGRESSOR:**
- Only supports **mean regression** (squared error loss)
- Does NOT have `objective` parameter
- Does NOT have `alpha` parameter for quantiles
- Does NOT support quantile loss functions

### **Evidence:**
- Plan says: "Train 3 models per horizon (q10, mean, q90) using `objective='quantile'`"
- BQML BOOSTED_TREE documentation: Only supports mean regression
- Existing BQML models in dataset: All are mean-only models

### **Impact:**
❌ **PLAN CANNOT BE EXECUTED AS WRITTEN**  
- Cannot create q10/q90 models using BOOSTED_TREE
- Need alternative approach for quantile predictions

### **Solutions:**

#### **Option A: Train Mean-Only, Compute Quantiles Post-Hoc** ⚠️ WEAK
- Train 1 mean model per horizon (4 models total, not 12)
- Use prediction variance/volatility to estimate q10/q90
- Formula: `q10 = mean - 1.28 * stddev`, `q90 = mean + 1.28 * stddev`
- **Problem:** BQML BOOSTED_TREE doesn't output prediction variance directly

#### **Option B: Use BQML DNN_REGRESSOR** ✅ BETTER
- Train 3 DNN models per horizon with custom loss (if supported)
- Check if DNN supports quantile loss
- **Problem:** DNN may not support quantile loss either

#### **Option C: Use BQML XGBOOST** ✅ BEST IF AVAILABLE
- Check if BQML supports XGBoost (might not)
- XGBoost can do quantile regression
- **Problem:** BQML may only support BOOSTED_TREE (not raw XGBoost)

#### **Option D: Hybrid Approach** ✅ RECOMMENDED
- Train 4 mean models (1W, 1M, 3M, 6M) using BQML BOOSTED_TREE
- Use historical residuals to compute empirical quantiles
- Store residual distribution per horizon
- At prediction time: `q10 = mean - residual_q90`, `q90 = mean + residual_q90`
- **Requires:** Residual tracking table

#### **Option E: Export to Vertex AI** ❌ DEFEATS PURPOSE
- Train LightGBM models with quantile loss outside BQML
- Deploy to Vertex AI endpoints
- **Problem:** Back to $180/month cost

### **Recommendation:**
**Option D (Hybrid Approach)** - Train mean-only BQML models, compute quantiles from residuals.

---

## 🚨 CRITICAL ISSUE #2: COLUMN COUNT MISMATCH

### **The Problem:**
Plan claims 206 feature columns, but actual count is **205**.

**Actual:**
- Total columns: 210
- Target columns: 4 (target_1w, target_1m, target_3m, target_6m)
- Date column: 1
- **Feature columns: 210 - 4 - 1 = 205** ❌

**Plan Claims:**
- Feature columns: 206 ✅ (incorrect)

### **Impact:**
⚠️ **MINOR** - Only affects documentation, not functionality. Actual training will work with 205 features.

### **Fix:**
Update plan to say "205 features" instead of "206".

---

## 🚨 CRITICAL ISSUE #3: EXISTING SCRIPTS INCOMPATIBLE

### **The Problem:**
Existing scripts (`1m_feature_assembler.py`, `1w_signal_computer.py`) are designed for:
- Vertex AI endpoint calls
- AutoML schema contracts
- Manual feature validation

BQML requires:
- Direct SQL queries
- No schema contracts (BigQuery enforces schema)
- ML.PREDICT syntax instead of endpoint calls

### **Impact:**
⚠️ **MAJOR** - Scripts need complete rewrite, not just updates.

### **Files Requiring Rewrite:**
1. `scripts/1m_feature_assembler.py` - Currently assembles for Vertex endpoints
2. `scripts/1w_signal_computer.py` - May work, but needs verification
3. `scripts/1m_predictor_job_bqml.py` - Needs to be created from scratch (not exists)

### **Fix:**
Rewrite scripts to use:
- BigQuery client for ML.PREDICT calls
- SQL-based feature assembly
- Direct table writes (no endpoint calls)

---

## ✅ RESOLVED: ML.PREDICT AND ML.EXPLAIN_PREDICT WORK

### **Test Results:**
✅ **ML.PREDICT works!**
- Output column: `predicted_target_1m` (single value, mean prediction)
- Returns all 205 feature columns in output (for reference)
- Works with existing BOOSTED_TREE models
- Syntax correct: `ML.PREDICT(MODEL ..., (SELECT ...))`

✅ **ML.EXPLAIN_PREDICT works!**
- Output column: `top_feature_attributions` (ARRAY of STRUCT with `feature` and `attribution`)
- Provides feature-level attribution (similar to SHAP, but top-K only)
- Default top_k=5, can specify more
- Example output: `[{'feature': 'corn_price', 'attribution': -8.18}, ...]`
- Also includes: `baseline_prediction_value`, `prediction_value`, `approximation_error`

### **Impact:**
✅ **MINOR** - ML.EXPLAIN_PREDICT provides attributions, not full SHAP values, but usable for explainability.

### **Note:**
- Attribution values are signed (positive = increases prediction, negative = decreases)
- Top-K only (default 5), but can increase top_k parameter
- Good enough for dashboard tooltips

---

## ⚠️ WARNING #1: DATA QUALITY ISSUES

### **Findings:**
- **1M target:** 23 NULL rows (out of 1,251 total) = 1.84% missing
- **3M target:** 83 NULL rows = 6.6% missing
- **6M target:** 173 NULL rows = 13.8% missing

### **Impact:**
⚠️ **MINOR** - BQML will automatically filter WHERE target_* IS NOT NULL, so training will work, just with fewer rows for longer horizons.

### **Fix:**
Plan already accounts for this with `WHERE target_1m IS NOT NULL` filter. No action needed.

---

## ⚠️ WARNING #2: VIEW DEPENDENCIES

### **The Problem:**
Plan creates `features_1m_clean` view, but:
1. View doesn't exist yet (verified)
2. All 12 training scripts depend on this view
3. If view creation fails, all training fails

### **Impact:**
⚠️ **MINOR** - Easy to fix, but needs verification step after view creation.

### **Fix:**
Add verification step: After creating view, run `SELECT COUNT(*) FROM features_1m_clean` to confirm it works.

---

## ⚠️ WARNING #3: EXISTING BQML MODELS

### **Findings:**
Found 15 existing BQML models, including:
- 4 BOOSTED_TREE_REGRESSOR models (1W, 1M, 3M, 6M) - mean-only
- Created: October 28, 2025
- May have been trained with label leakage (need to verify)

### **Impact:**
⚠️ **MAJOR** - If existing models are broken (label leakage), need to retrain anyway. If they work, could use them for mean predictions.

### **Fix:**
1. Test existing models: `ML.PREDICT` with clean features (no targets)
2. If they work: Use them for mean predictions, only train new models for q10/q90 (if quantiles supported)
3. If broken: Retrain all models

---

## ⚠️ WARNING #4: PREDICTION TABLE SCHEMA MISMATCH

### **The Problem:**
`predictions_1m` table schema exists, but:
- Has `q10`, `q90` columns
- Plan assumes these can be populated from BQML models
- **If BQML doesn't support quantiles, these columns can't be populated as expected**

### **Impact:**
⚠️ **MAJOR** - Table schema assumes quantile predictions, but BQML may not provide them.

### **Fix:**
If using residual-based quantiles (Option D):
- Populate `q10` and `q90` from mean prediction + residual quantiles
- Update prediction job to compute quantiles post-hoc

---

## ⚠️ WARNING #5: FEATURE ASSEMBLY COMPLEXITY

### **The Problem:**
Plan assumes 1W signals can be "injected" as features into 1M model. But:
1. 1W signals come from `signals_1w` table (pivoted format)
2. Feature assembler needs to join this table
3. If `signals_1w` is empty on first run, prediction fails

### **Impact:**
⚠️ **MINOR** - Bootstrap problem: Can't compute 1W signals without 1W model, but 1W model needs features. Circular dependency.

### **Fix:**
1. Train 1W model first (without 1W signal features)
2. Generate initial predictions
3. Compute 1W signals
4. Retrain 1M model with 1W signals as features
5. Generate 1M predictions

---

## 📊 SCHEMA AUDIT RESULTS

### **Training Dataset:**
- **Total columns:** 210 ✅
- **Target columns:** 4 ✅
- **Date column:** 1 ✅
- **Feature columns:** 205 ⚠️ (plan says 206)
- **Total rows:** 1,251 ✅
- **Date range:** 2020-10-21 to 2025-10-13 ✅
- **No duplicate dates:** ✅

### **Target Column Completeness:**
- **target_1w:** 100% complete (1,251 rows) ✅
- **target_1m:** 98.16% complete (1,228 rows) ⚠️
- **target_3m:** 93.37% complete (1,168 rows) ⚠️
- **target_6m:** 86.17% complete (1,078 rows) ⚠️

### **Data Quality:**
- **No NaN in key columns:** ✅ (verified for numeric types)
- **Variance present:** ✅ (all targets have >900 unique values)
- **Stddev reasonable:** ✅ (11-12 for all targets)

---

## 🔍 MECHANISM AUDIT

### **BQML Training Mechanism:**
1. ✅ `CREATE MODEL` syntax correct
2. ✅ `EXCEPT` clause works for excluding targets
3. ✅ `WHERE target_* IS NOT NULL` filter works
4. ❌ **Quantile training NOT supported**

### **Prediction Mechanism:**
1. ⚠️ `ML.PREDICT` syntax needs testing
2. ⚠️ Output format unknown (need to test)
3. ❌ **Quantile predictions NOT available directly**

### **Explainability Mechanism:**
1. ⚠️ `ML.EXPLAIN_PREDICT` needs testing
2. ⚠️ Output format unknown (need to test)
3. ⚠️ SHAP values availability unknown

---

## 📋 SCRIPT AUDIT

### **Existing Scripts:**
1. `scripts/1m_feature_assembler.py` - ❌ Incompatible (Vertex AI focused)
2. `scripts/1w_signal_computer.py` - ⚠️ May work, needs verification
3. `scripts/calculate_shap_drivers_bqml.py` - ❌ Doesn't exist, needs creation

### **Required Scripts (Missing):**
1. `scripts/train_all_bqml_models.py` - ❌ Doesn't exist
2. `scripts/validate_bqml_models.py` - ❌ Doesn't exist
3. `scripts/export_bqml_feature_schema.py` - ❌ Doesn't exist
4. `scripts/1m_predictor_job_bqml.py` - ❌ Doesn't exist

---

## 🚨 REQUIRED FIXES BEFORE EXECUTION

### **Priority 1: CRITICAL (Plan Cannot Proceed Without These)**

1. **Fix Quantile Training Approach** ⚠️ **STILL REQUIRED**
   - Decision: Option A (mean-only), Option D (residual quantiles), or Option E (Vertex AI)
   - Update plan with chosen approach
   - Update training scripts accordingly
   - **Tested:** Confirmed BOOSTED_TREE only does mean regression (no quantile support)

2. ✅ **RESOLVED: ML.EXPLAIN_PREDICT** - Works, provides attributions (top-K)
   - ✅ Tested on existing model
   - ✅ Output format confirmed
   - ⚠️ Provides attributions (not full SHAP), but usable

3. ✅ **RESOLVED: ML.PREDICT** - Works, returns mean predictions
   - ✅ Tested on existing model
   - ✅ Output format confirmed: `predicted_target_1m` column
   - ⚠️ Only mean predictions (no quantiles)

### **Priority 2: MAJOR (Script Rewrites Required)**

4. **Rewrite Feature Assembler**
   - Remove Vertex AI endpoint calls
   - Add SQL-based feature assembly
   - Add 1W signal join logic

5. **Create Prediction Job**
   - Use ML.PREDICT instead of endpoint calls
   - Compute quantiles if using residual approach
   - Write to predictions_1m table

6. **Create SHAP Calculator**
   - Use ML.EXPLAIN_PREDICT or alternative
   - Map to business labels
   - Store in shap_drivers table

### **Priority 3: MINOR (Documentation/Validation)**

7. **Fix Column Count**
   - Update plan: 205 features (not 206)

8. **Add View Verification Step**
   - After creating features_1m_clean, verify it works

9. **Test Existing Models**
   - Check if existing BOOSTED_TREE models work
   - If yes, can use for mean predictions

---

## 📊 REALISTIC FEASIBILITY ASSESSMENT

### **Can This Plan Actually Work?**

**Current State:** ❌ **NO - Critical blockers exist**

**After Fixes:** ✅ **YES - With modifications**

### **Required Modifications:**

1. **Quantile Training:** Cannot train q10/q90 models directly. Must use:
   - Mean-only training + residual quantiles, OR
   - Alternative model type (if BQML supports), OR
   - External training + Vertex AI deployment

2. **Script Updates:** All prediction/assembly scripts need BQML rewrite (not just updates)

3. **Testing:** Must test ML.PREDICT and ML.EXPLAIN_PREDICT before assuming they work

### **Estimated Additional Work:**
- Quantile solution design: 2-4 hours
- Script rewrites: 4-6 hours
- Testing & validation: 2-3 hours
- **Total: 8-13 hours additional work before execution**

---

## ✅ REVIEW CHECKPOINTS RECOMMENDED

### **After Phase 1 (Training):**
1. ✅ Verify all models trained successfully
2. ✅ Run ML.EVALUATE on each model
3. ✅ Test ML.PREDICT on one model
4. ✅ Verify quantile approach (if using residuals)
5. ✅ Check training costs (should be $0)

### **After Phase 2 (Predictions):**
1. ✅ Verify predictions_1m table populated
2. ✅ Check q10/mean/q90 values are reasonable
3. ✅ Verify no NULL predictions
4. ✅ Test prediction job runs end-to-end

### **After Phase 9 (SHAP):**
1. ✅ Verify ML.EXPLAIN_PREDICT works
2. ✅ Check SHAP values stored in shap_drivers
3. ✅ Verify business labels mapped correctly
4. ✅ Test explainability API route

---

## 🎯 RECOMMENDED NEXT STEPS

1. **IMMEDIATE:** Test ML.PREDICT and ML.EXPLAIN_PREDICT on existing BOOSTED_TREE models
2. **IMMEDIATE:** Decide quantile approach (Option A, D, or E)
3. **BEFORE EXECUTION:** Rewrite feature assembler and prediction scripts
4. **BEFORE EXECUTION:** Test view creation and feature count
5. **DURING EXECUTION:** Add checkpoints after each phase

---

**Status:** 🚨 **PLAN NEEDS CRITICAL FIXES BEFORE EXECUTION**

