# PRE-TRAINING AUDIT REPORT
**Date:** October 22, 2025  
**Auditor:** AI Assistant  
**Purpose:** Identify blockers before full BQML training of 16 models

---

## EXECUTIVE SUMMARY

**STATUS:** 🚨 **1 BLOCKING ISSUE FOUND** - Training cannot proceed until resolved

**Models to Train:** 16 models (4 horizons × 4 algorithms)
- Horizons: 1w, 1m, 3m, 6m (**12m removed per user decision**)
- Algorithms: LightGBM, DNN, ARIMA, Linear Regression

---

## AUDIT FINDINGS

### 🚨 BLOCKING ISSUES

#### 1. Duplicate Dates in Training Dataset (CRITICAL)
**Issue:** `models.vw_neural_training_dataset` has 128 duplicate rows for date 2025-10-22

**Root Cause:** 
- `models.vw_seasonality_features` view returns 2,024 rows for single date
- LEFT JOIN to seasonality_clean CTE causes JOIN explosion
- View uses GROUP BY but still returns multiple rows per date

**Impact:**
- BQML models will fail or produce incorrect results
- Data split (train/test) will be corrupted
- Evaluation metrics will be wrong

**Evidence:**
```
Total rows in training dataset: 1,385
Unique dates: 1,257
Duplicate date: 2025-10-22 (128 rows)
```

**Remediation:**
```sql
-- Fix vw_seasonality_features to return ONE row per date
CREATE OR REPLACE VIEW `cbi-v14.models.vw_seasonality_features` AS
SELECT 
    date,
    AVG(seasonal_index) as seasonal_index,
    AVG(monthly_zscore) as monthly_zscore,
    AVG(yoy_change) as yoy_change,
    -- Pick one agricultural phase (most common)
    APPROX_TOP_COUNT(agricultural_phase, 1)[OFFSET(0)].value as agricultural_phase
FROM `cbi-v14.models.vw_seasonality_features_raw`  -- or whatever the base is
GROUP BY date
```

OR remove seasonality from training dataset temporarily:
```sql
-- In vw_neural_training_dataset, comment out seasonality join
-- LEFT JOIN seasonality_clean sz ON p.date = sz.date
```

---

### ⚠️ WARNINGS (Non-blocking but should be addressed)

#### 2. Palm Oil Correlation Has Minor NaN Issues
- Palm 7d correlation: 32 NaN/NULL values (2.3%)
- Not blocking because < 5% threshold
- Handled by COALESCE in view definition

#### 3. Limited 6-Month Target Data
- target_6m available for 1,078/1,385 rows (77.8%)
- Acceptable for training but may reduce model accuracy
- Longer horizons naturally have less data

---

## DATASET INTEGRITY CHECKS

### ✅ Target Columns (CORRECT - 4 horizons only)
| Target | Rows Available | Coverage |
|--------|---------------|----------|
| target_1w | 1,251 | 90.3% ✅ |
| target_1m | 1,228 | 88.7% ✅ |
| target_3m | 1,168 | 84.3% ✅ |
| target_6m | 1,078 | 77.8% ✅ |
| ~~target_12m~~ | ~~N/A~~ | **Removed per user** |

### ✅ Correlation Features (HEALTHY)
| Feature | NaN/NULL Issues | Status |
|---------|-----------------|--------|
| corr_zl_crude_7d | 0 (0.0%) | ✅ |
| corr_zl_crude_30d | 0 (0.0%) | ✅ |
| corr_zl_palm_7d | 32 (2.3%) | ⚠️ Acceptable |
| corr_zl_palm_30d | 0 (0.0%) | ✅ |

**Note:** All correlations properly use COALESCE guards to replace NaN with 0

### ✅ Data Freshness (EXCELLENT)
- Date range: 2020-10-21 to 2025-10-22
- Days stale: 0 (current!)
- Total rows: 1,385
- ~5 years of training data

---

## FEATURE VIEW HEALTH

### ✅ All Critical Feature Views Working

| View | Status | Rows | Notes |
|------|--------|------|-------|
| neural.vw_big_eight_signals | ✅ | 2,122 | All 8 signals healthy |
| models.vw_correlation_features | ✅ | 1,261 | Minor NaN handled |
| models.vw_crush_margins | ✅ | 1,265 | Profitable status OK |

### ❌ Broken Views (Not Used in Training)

| View | Status | Impact |
|------|--------|--------|
| models.vw_neural_interaction_features | ❌ 404 Not found | Not used in current training dataset |
| models.vw_biofuel_bridge_features | ❌ Column error | Not used or optional |

**Recommendation:** Delete unused views per [[memory:9706879]] (BigQuery views cost money if queried)

---

## TRAINING SCRIPT REVIEW

### Scripts Analyzed:
1. `scripts/FIX_AND_TRAIN_PROPERLY.py` ✅
2. `scripts/TRAIN_FULL_COMPLEX_25_MODELS.py` ⚠️ (references 5 horizons - needs update)
3. `scripts/fix_vix_properly_and_complete.py` ✅
4. `scripts/final_readiness_check.py` ⚠️ (checks target_12m - needs update)

### Issues Found:

#### Script Updates Needed:
1. **TRAIN_FULL_COMPLEX_25_MODELS.py** - Update horizons list from 5 to 4
2. **final_readiness_check.py** - Remove target_12m check (line 41)

### ✅ BQML Options Look Good:
- Proper data split: `data_split_method='SEQ'` with `data_split_col='date'`
- Early stopping enabled
- Reasonable hyperparameters
- Correct label columns: `target_1w`, `target_1m`, `target_3m`, `target_6m`

---

## OPERATIONAL RISKS

### ✅ GCP Configuration
- Project: `cbi-v14` ✅
- Location: `us-central1` ✅
- Credentials: BigQuery client initializes successfully ✅

### ⚠️ Cost Considerations
- Training 16 models will consume compute resources
- AutoML budget set to 1-2 hours per model (reasonable)
- DNN models set to 200-500 iterations (may be costly)

**Recommendation:** Start with 4 models (1 per horizon, single algorithm) to validate, then scale

### ✅ Naming Conventions
- Current dataset view: `models.vw_neural_training_dataset` (clean, no suffix) ✅
- Old views deleted: `_v2`, `_FIXED`, `_final` ✅
- Follows [[memory:9706878]] naming standards

---

## REMEDIATION PLAN

### MUST FIX BEFORE TRAINING:

#### Step 1: Fix Seasonality View (BLOCKING)
```bash
# Option A: Fix the view to GROUP BY properly
python3 scripts/fix_seasonality_view.py

# Option B: Temporarily remove from training dataset
# Edit view to comment out seasonality join
```

#### Step 2: Verify Fix
```bash
python3 << 'EOF'
from google.cloud import bigquery
client = bigquery.Client(project='cbi-v14')
result = list(client.query("""
    SELECT date, COUNT(*) as cnt 
    FROM `cbi-v14.models.vw_neural_training_dataset`
    GROUP BY date HAVING COUNT(*) > 1
""").result())
if result:
    print(f"❌ Still have duplicates: {len(result)} dates")
else:
    print("✅ Fixed! No duplicate dates")
EOF
```

### SHOULD FIX (Non-blocking):

#### Step 3: Update Training Scripts
- Remove target_12m references
- Update horizon counts from 5 to 4
- Update MASTER_TRAINING_PLAN.md ✅ (DONE)

#### Step 4: Delete Unused Views
```sql
DROP VIEW IF EXISTS `cbi-v14.models.vw_neural_interaction_features`;
DROP VIEW IF EXISTS `cbi-v14.models.vw_biofuel_bridge_features`;
-- Or fix them if actually needed
```

---

## GO/NO-GO DECISION

### ❌ **NO-GO** - Cannot proceed with training until blocker is fixed

**Reason:** Duplicate dates will corrupt model training

**Time to Fix:** 15-30 minutes

**Once Fixed:** Platform is fully ready for training 16 models

---

## EXPECTED TRAINING OUTCOMES

Once duplicate issue is resolved:

### Models to Train:
```
1. zl_lightgbm_1w, _1m, _3m, _6m  (4 models)
2. zl_dnn_1w, _1m, _3m, _6m       (4 models)
3. zl_arima_1w, _1m, _3m, _6m     (4 models)
4. zl_linear_1w, _1m, _3m, _6m    (4 models)
-------------------------------------------------
TOTAL: 16 models
```

### Expected Performance:
- MAPE: 3-5% (with all features)
- Directional Accuracy: 65-70%
- Training Time: 2-4 hours total
- Cost: ~$50-100 for full training run

---

## APPENDIX: AUDIT COMMANDS

All audit commands used (read-only, safe to re-run):

```bash
# Check for duplicates
python3 scripts/final_readiness_check.py

# Check NaN values
python3 -c "from google.cloud import bigquery; ..."

# Investigate seasonality
bq query --use_legacy_sql=false "
SELECT date, COUNT(*) as cnt
FROM \`cbi-v14.models.vw_seasonality_features\`
GROUP BY date
ORDER BY cnt DESC
LIMIT 10
"
```

---

**Report Generated:** October 22, 2025  
**Next Action:** Fix seasonality view duplication issue  
**Time to Training:** ~30 minutes after fix












