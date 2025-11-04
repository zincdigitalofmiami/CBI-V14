# ARIMA Models Assessment - Read-Only Review

**Date:** November 4, 2025  
**Purpose:** Assess existing ARIMA models for forecast generation  
**Status:** Read-Only Analysis

---

## EXECUTIVE SUMMARY

**✅ ARIMA Models Exist:** Yes, we have 8 ARIMA_PLUS models already trained  
**❌ ARIMA Models Evaluated:** No, they haven't been evaluated yet  
**❓ ARIMA+ (ARIMA_PLUS_XREG):** No, we only have simple ARIMA_PLUS  
**⏳ Should We Do It Now?** **NO - Evaluate existing ARIMA first, then decide**

---

## EXISTING ARIMA MODELS FOUND

### ARIMA Baseline Models (4 models - Created Oct 28, 2025)

| Model | Type | Created | Status | Purpose |
|-------|------|---------|--------|---------|
| `arima_baseline_1w` | ARIMA_PLUS | Oct 28 | ✅ Exists | 1-week baseline |
| `arima_baseline_1m` | ARIMA_PLUS | Oct 28 | ✅ Exists | 1-month baseline |
| `arima_baseline_3m` | ARIMA_PLUS | Oct 28 | ✅ Exists | 3-month baseline |
| `arima_baseline_6m` | ARIMA_PLUS | Oct 28 | ✅ Exists | 6-month baseline |

**Location:** `cbi-v14.models_v4.*`  
**Age:** 7 days old (recent)  
**Credibility:** ✅ Credible (from audit report)

### ARIMA V4 Models (4 models - Created Oct 22, 2025)

| Model | Type | Created | Status | Purpose |
|-------|------|---------|--------|---------|
| `zl_arima_1w_v4` | ARIMA_PLUS | Oct 22 | ✅ Exists | 1-week forecast |
| `zl_arima_1m_v4` | ARIMA_PLUS | Oct 22 | ✅ Exists | 1-month forecast |
| `zl_arima_3m_v4` | ARIMA_PLUS | Oct 22 | ✅ Exists | 3-month forecast |
| `zl_arima_6m_v4` | ARIMA_PLUS | Oct 22 | ✅ Exists | 6-month forecast |

**Location:** `cbi-v14.models_v4.*`  
**Age:** 12 days old  
**Credibility:** ✅ Credible

---

## ARIMA vs ARIMA_PLUS vs ARIMA_PLUS_XREG

### What We Have: ARIMA_PLUS (Simple Time Series)

**ARIMA_PLUS:**
- ✅ BigQuery's auto-tuned ARIMA model
- ✅ Automatic parameter selection (auto_arima=TRUE)
- ✅ Handles seasonality, trends, holidays
- ✅ Uses ONLY time series data (date + price)
- ❌ Does NOT use external features (China, Trump, Weather, etc.)

**What It Does:**
- Looks at historical price patterns
- Extracts trends, seasonality, autocorrelation
- Forecasts based on time-series patterns only

**Example:**
```sql
CREATE MODEL arima_baseline_1w
OPTIONS(
  model_type='ARIMA_PLUS',
  time_series_timestamp_col='date',
  time_series_data_col='zl_price_current',
  horizon=7,
  auto_arima=TRUE
) AS
SELECT date, zl_price_current
FROM training_dataset
ORDER BY date;
```

### What We DON'T Have: ARIMA_PLUS_XREG (With External Regressors)

**ARIMA_PLUS_XREG:**
- Uses time series data + external features
- Can incorporate China imports, Trump policy, weather, etc.
- More sophisticated than simple ARIMA_PLUS
- Better for capturing external drivers

**Example:**
```sql
CREATE MODEL arima_1w_xreg
OPTIONS(
  model_type='ARIMA_PLUS_XREG',
  time_series_timestamp_col='date',
  time_series_data_col='zl_price_current',
  horizon=7,
  xreg_cols=['china_imports_from_us_mt', 'vix_current', 'palm_spread', ...]
) AS
SELECT date, zl_price_current, china_imports_from_us_mt, vix_current, ...
FROM training_dataset
ORDER BY date;
```

---

## CURRENT STATUS: ARIMA MODELS NOT EVALUATED

### From Audit Report:
- **"All ARIMA models - Need ML.FORECAST evaluation"**
- **"ARIMA models - Cannot use ML.EVALUATE/ML.PREDICT (must use ML.FORECAST)"**

### Why They're Not Evaluated:
1. ARIMA uses different prediction method (`ML.FORECAST` vs `ML.PREDICT`)
2. No evaluation scripts exist for ARIMA models
3. No MAPE/Metrics calculated for ARIMA models
4. Unknown if ARIMA is better/worse than BOOSTED_TREE

---

## SHOULD WE USE ARIMA NOW?

### Recommendation: **NO - NOT YET**

**Reasons:**
1. **✅ BOOSTED_TREE models are ready** (MAPE: 0.70-1.29%)
2. **❌ ARIMA models not evaluated** (unknown performance)
3. **❌ No ensemble framework ready** (would need to combine both)
4. **⏳ Forecast generation ready** (7-stage protocol complete)
5. **⏳ Time constraint** (Nov 10 launch deadline)

### What We Should Do Instead:

**Phase 1: Launch with BOOSTED_TREE (Now)**
- Use existing `bqml_1w/1m/3m/6m` models (already trained, evaluated)
- Generate forecasts with 7-stage protocol
- Launch dashboard Nov 10
- **Status:** ✅ Ready to go

**Phase 2: Evaluate ARIMA (Post-Launch)**
- Test existing ARIMA models with `ML.FORECAST`
- Calculate MAPE for ARIMA models
- Compare ARIMA vs BOOSTED_TREE performance
- **Effort:** 4-8 hours
- **Timeline:** Week after launch

**Phase 3: Consider Ensemble (If ARIMA Performs Well)**
- If ARIMA MAPE < 1.5%, consider ensemble
- Train ARIMA_PLUS_XREG (with external features) if needed
- Combine BOOSTED_TREE + ARIMA in weighted ensemble
- **Effort:** 8-16 hours
- **Timeline:** 2-3 weeks post-launch

---

## IF WE WANTED TO USE ARIMA NOW (Not Recommended)

### Option 1: Use Simple ARIMA_PLUS (What We Have)

**Pros:**
- ✅ Models already trained
- ✅ No training time needed
- ✅ Fast to implement

**Cons:**
- ❌ Doesn't use external features (China, Trump, Weather)
- ❌ Unknown performance (not evaluated)
- ❌ May perform worse than BOOSTED_TREE
- ❌ Different prediction method (ML.FORECAST vs ML.PREDICT)

**Implementation:**
```sql
-- Generate ARIMA forecast
SELECT forecast_value
FROM ML.FORECAST(
  MODEL `cbi-v14.models_v4.arima_baseline_1w`,
  STRUCT(7 AS horizon)
);
```

**Effort:** 2-4 hours to integrate into forecast generation  
**Risk:** Medium (unknown performance, different API)

### Option 2: Train ARIMA_PLUS_XREG (Better, But Slower)

**Pros:**
- ✅ Uses external features (like BOOSTED_TREE)
- ✅ Better than simple ARIMA_PLUS
- ✅ More comparable to BOOSTED_TREE

**Cons:**
- ❌ Need to train new models (5-15 min each)
- ❌ Need to evaluate performance
- ❌ More complex integration
- ❌ Time constraint (Nov 10 launch)

**Effort:** 8-16 hours (training + evaluation + integration)  
**Risk:** Low (known approach, but adds complexity)

---

## COMPARISON: BOOSTED_TREE vs ARIMA

| Aspect | BOOSTED_TREE (Current) | ARIMA_PLUS (Existing) | ARIMA_PLUS_XREG (New) |
|--------|----------------------|----------------------|----------------------|
| **Status** | ✅ Trained & Evaluated | ✅ Trained, ❌ Not Evaluated | ❌ Not Trained |
| **MAPE** | 0.70-1.29% | ❓ Unknown | ❓ Unknown |
| **Features** | 276 features | 0 features (time only) | 20-30 features |
| **API** | ML.PREDICT | ML.FORECAST | ML.FORECAST |
| **Integration** | ✅ Ready | ⚠️ Needs testing | ❌ Needs training |
| **Launch Ready** | ✅ YES | ⚠️ Maybe | ❌ NO |

---

## FINAL RECOMMENDATION

### ✅ DO NOW: Launch with BOOSTED_TREE

**Why:**
1. Models are trained, evaluated, and ready
2. 7-stage forecast protocol complete
3. Dashboard views ready
4. Nov 10 launch deadline
5. Proven performance (0.70-1.29% MAPE)

### ⏳ DO LATER: Evaluate ARIMA for Ensemble

**Timeline:**
- **Week 1 (Post-Launch):** Evaluate existing ARIMA models
- **Week 2:** If ARIMA performs well, train ARIMA_PLUS_XREG
- **Week 3:** Build ensemble combining BOOSTED_TREE + ARIMA
- **Week 4:** A/B test ensemble vs BOOSTED_TREE alone

**Expected Outcome:**
- If ARIMA MAPE < 1.5%: Ensemble might improve to 0.5-0.9% MAPE
- If ARIMA MAPE > 2.0%: Skip ensemble, stick with BOOSTED_TREE

---

## TECHNICAL DETAILS: ARIMA FORECAST GENERATION

### How ARIMA Forecasts Work (Different from BOOSTED_TREE)

**BOOSTED_TREE (Current):**
```sql
SELECT predicted_target_1w
FROM ML.PREDICT(
  MODEL `bqml_1w`,
  (SELECT * FROM latest_data)
);
```

**ARIMA_PLUS (Existing Models):**
```sql
SELECT forecast_value
FROM ML.FORECAST(
  MODEL `arima_baseline_1w`,
  STRUCT(7 AS horizon)  -- Days to forecast
);
```

**Key Differences:**
- ARIMA doesn't need input data (uses historical training data)
- ARIMA returns forecast_value (not predicted_target_1w)
- ARIMA uses horizon parameter (days forward)
- ARIMA can't be integrated into current 7-stage protocol easily

---

## SUMMARY

**Question:** Should we use ARIMA now?

**Answer:** **NO - Not for v1.0 launch**

**Reasons:**
1. ✅ BOOSTED_TREE models are ready and proven
2. ❌ ARIMA models not evaluated (unknown performance)
3. ⏳ Time constraint (Nov 10 launch)
4. ⏳ Different API (ML.FORECAST vs ML.PREDICT)
5. ⏳ Integration complexity

**Recommendation:**
- **Launch with BOOSTED_TREE** (Nov 10)
- **Evaluate ARIMA post-launch** (Week 1-2)
- **Consider ensemble if ARIMA performs well** (Week 3-4)

**Files Ready:**
- ✅ Forecast generation: `GENERATE_PRODUCTION_FORECASTS_V3.sql`
- ✅ Dashboard views: `CREATE_DASHBOARD_VIEWS_STAGE6_WITH_REASONING.sql`
- ⏳ ARIMA evaluation: Not created yet (post-launch task)

**Next Step:** Proceed with BOOSTED_TREE forecast generation. ARIMA can wait.

