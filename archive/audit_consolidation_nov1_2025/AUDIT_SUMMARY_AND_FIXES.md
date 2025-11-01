# DEEP DIVE AUDIT SUMMARY - EXECUTION BLOCKERS & FIXES

**Date:** November 1, 2025  
**Status:** 🚨 **1 CRITICAL BLOCKER + 3 MAJOR ISSUES FOUND**  
**Recommendation:** Fix quantile approach BEFORE execution

---

## 🚨 CRITICAL BLOCKER #1: QUANTILE TRAINING NOT SUPPORTED

### **Problem:**
BQML BOOSTED_TREE_REGRESSOR **does not support quantile regression**. Plan assumes we can train 12 models (4 horizons × 3 quantiles), but only mean regression is possible.

### **Evidence:**
- ✅ Tested ML.PREDICT: Only returns `predicted_target_1m` (mean)
- ✅ Verified model options: No `objective`, `alpha`, or quantile parameters
- ✅ Existing models: All are mean-only
- ✅ Plan incorrectly states: "Train 3 models per horizon (q10, mean, q90) using `objective='quantile'`"

### **Solutions Ranked:**

#### **Option D: Residual-Based Quantiles** ✅ **RECOMMENDED**
**How it works:**
1. Train 4 mean-only BQML models (1W, 1M, 3M, 6M)
2. Generate predictions on training set
3. Compute residuals: `residual = actual - predicted`
4. Store residual distribution (percentiles) per horizon
5. At prediction time:
   - Get mean prediction from BQML
   - Look up residual q10 and q90 for that horizon
   - Compute: `q10 = mean - residual_q90`, `q90 = mean + residual_q90`

**Pros:**
- ✅ Uses existing BQML mean models
- ✅ No additional training cost
- ✅ Quantiles reflect actual model uncertainty
- ✅ Simple to implement

**Cons:**
- ⚠️ Quantiles assume residual distribution is stable
- ⚠️ May not capture heteroskedasticity well

**Implementation:**
- Create `residual_distributions` table: `horizon`, `q10_residual`, `q90_residual`
- Update prediction job to compute quantiles post-hoc
- Populate `q10` and `q90` columns in `predictions_1m`

#### **Option A: Mean-Only (No Quantiles)** ⚠️ **WEAK**
**How it works:**
1. Train 4 mean-only models
2. Use fixed spread (e.g., ±5%) for all predictions
3. Or: Use volatility-based spread (volatility_score_1w × 0.15)

**Pros:**
- ✅ Simplest
- ✅ No additional complexity

**Cons:**
- ❌ No true quantiles
- ❌ Fixed spread doesn't reflect model uncertainty

#### **Option E: Export to Vertex AI** ❌ **DEFEATS PURPOSE**
**How it works:**
- Train LightGBM models with quantile loss outside BQML
- Deploy to Vertex AI endpoints
- Back to $180/month cost

**Pros:**
- ✅ True quantile models

**Cons:**
- ❌ Defeats purpose of BQML migration (cost savings)
- ❌ Adds deployment complexity

---

## ⚠️ MAJOR ISSUE #2: COLUMN COUNT MISMATCH

### **Problem:**
Plan claims 206 features, actual is **205**.

**Actual:** 210 total - 4 targets - 1 date = **205 features** ✅  
**Plan:** Claims 206 ❌

### **Fix:**
Update documentation to say "205 features" (minor, but fixes confusion).

---

## ⚠️ MAJOR ISSUE #3: SCRIPT INCOMPATIBILITY

### **Problem:**
Existing scripts designed for Vertex AI, need BQML rewrite.

**Files requiring rewrite:**
1. `scripts/1m_feature_assembler.py` - Currently assembles for Vertex endpoints
2. `scripts/1m_predictor_job_bqml.py` - Doesn't exist, needs creation

### **Fix:**
Rewrite to use:
- `ML.PREDICT` instead of endpoint calls
- SQL-based feature assembly
- Direct BigQuery table writes

---

## ⚠️ MAJOR ISSUE #4: PREDICTION TABLE ASSUMES QUANTILES

### **Problem:**
`predictions_1m` table has `q10` and `q90` columns, but BQML doesn't provide them directly.

### **Fix (if using Option D):**
- Update prediction job to compute quantiles from residuals
- Populate `q10` and `q90` columns with computed values

---

## ✅ POSITIVE FINDINGS

### **1. ML.PREDICT Works** ✅
- Syntax correct
- Returns `predicted_target_1m` column
- Works with existing models
- No label leakage detected in tests

### **2. ML.EXPLAIN_PREDICT Works** ✅
- Provides feature attributions (top-K)
- Output format: `top_feature_attributions` array
- Good enough for dashboard tooltips
- Can increase top_k if needed

### **3. Data Quality Good** ✅
- 1,251 rows total
- 205 features clean
- Targets have good variance
- Date range complete (2020-2025)

### **4. Existing Models Work** ✅
- 4 BOOSTED_TREE models exist (1W, 1M, 3M, 6M)
- Created October 28, 2025
- Can be used for mean predictions immediately

---

## 📋 REQUIRED FIXES (BEFORE EXECUTION)

### **Priority 1: CRITICAL (Blocks Execution)**

1. **Choose Quantile Approach** ⏳ **DECISION REQUIRED**
   - Recommended: Option D (Residual-Based Quantiles)
   - Alternative: Option A (Mean-Only)
   - Update plan with chosen approach

2. **Update Training Plan**
   - Change from 12 models (4 horizons × 3 quantiles) to 4 models (4 horizons × mean only)
   - Add residual distribution calculation step
   - Add residual lookup table creation

3. **Update Prediction Job**
   - Compute quantiles post-hoc using residuals
   - Populate `q10` and `q90` columns

### **Priority 2: MAJOR (Script Rewrites)**

4. **Rewrite Feature Assembler**
   - Remove Vertex AI endpoint calls
   - Add SQL-based assembly
   - Add 1W signal join logic

5. **Create BQML Predictor Job**
   - Use `ML.PREDICT` for mean predictions
   - Compute quantiles from residuals
   - Apply gate blend logic
   - Write to `predictions_1m`

6. **Update SHAP Calculator**
   - Use `ML.EXPLAIN_PREDICT` (already tested, works)
   - Parse `top_feature_attributions` array
   - Map to business labels
   - Store in `shap_drivers` table

### **Priority 3: MINOR (Documentation)**

7. **Fix Column Count**
   - Update plan: 205 features (not 206)

8. **Add Review Checkpoints**
   - After Phase 1: Verify models trained, test ML.PREDICT
   - After Phase 2: Verify predictions generated, quantiles computed
   - After Phase 9: Verify SHAP attributions stored

---

## 🎯 RECOMMENDED EXECUTION PLAN (UPDATED)

### **Phase 1: Train BQML Mean Models + Compute Residuals** (2.5h)
1. Create `features_1m_clean` view (205 features)
2. Train 4 mean-only models (1W, 1M, 3M, 6M)
3. Generate predictions on training set
4. Compute residuals per horizon
5. Store residual distributions in `residual_distributions` table
6. **REVIEW CHECKPOINT:** Verify models trained, residuals computed

### **Phase 2: BQML Predictions with Residual Quantiles** (1.5h)
1. Rewrite feature assembler (BQML-compatible)
2. Create BQML predictor job:
   - Call `ML.PREDICT` for mean
   - Look up residual q10/q90
   - Compute quantiles: `q10 = mean - residual_q90`, `q90 = mean + residual_q90`
   - Apply gate blend for D+1-7
3. Write to `predictions_1m` table
4. **REVIEW CHECKPOINT:** Verify predictions generated, quantiles reasonable

### **Phase 3-14: Continue as planned** (with updated scripts)

---

## 📊 REALISTIC FEASIBILITY ASSESSMENT

### **Can This Plan Work?**

**Current State:** ❌ **NO - Quantile blocker**

**After Fixes (Option D):** ✅ **YES - With residual-based quantiles**

### **Estimated Additional Work:**
- Quantile solution design: 1 hour (Option D chosen)
- Residual distribution calculation: 1 hour
- Prediction job update (quantile computation): 1 hour
- Script rewrites: 4-6 hours
- Testing & validation: 2-3 hours
- **Total: 9-12 hours additional work**

---

## ✅ FINAL RECOMMENDATION

**1. Choose Option D (Residual-Based Quantiles)**
   - Best balance of simplicity and accuracy
   - Uses BQML mean models
   - Provides quantile predictions

**2. Update Plan Accordingly**
   - Change training from 12 models to 4 models
   - Add residual calculation step
   - Update prediction job for quantile computation

**3. Add Review Checkpoints**
   - After Phase 1 (training)
   - After Phase 2 (predictions)
   - After Phase 9 (SHAP)

**4. Then Execute**
   - All other components verified and ready
   - Only quantile approach needs fix

---

**Status:** 🟡 **READY AFTER QUANTILE FIX**

