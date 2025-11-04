# Model Verification Report - BEFORE ANY MORE FORECASTS

**Date:** November 4, 2025  
**Status:** ⚠️ **STOPPED - VERIFYING CORRECT MODELS**

---

## MODELS THAT EXIST

### Models Available:
- ✅ `bqml_1w` - EXISTS
- ✅ `bqml_1m` - EXISTS  
- ✅ `bqml_3m` - EXISTS
- ✅ `bqml_6m` - EXISTS
- ✅ `bqml_1w_all_features` - EXISTS
- ✅ `bqml_1m_all_features` - EXISTS
- ✅ `bqml_3m_all_features` - EXISTS
- ✅ `bqml_6m_all_features` - EXISTS

---

## CURRENT MAE VALUES (from ML.EVALUATE)

| Model | MAE | R² | Notes |
|-------|-----|-----|-------|
| bqml_1w | 0.928 | 0.992 | Current model used |
| bqml_1m | 0.959 | 0.989 | Current model used |
| bqml_3m | 0.932 | 0.991 | Current model used |
| bqml_6m | 0.948 | 0.988 | Current model used |
| bqml_3m_all_features | 0.932 | 0.991 | Same as bqml_3m |
| bqml_6m_all_features | 1.029 | 0.986 | WORSE than bqml_6m |

---

## AUDIT SAYS (BQML_MODELS_AUDIT_SUMMARY.md)

According to audit:
- **bqml_1w**: 0.74% MAPE ✅ (UNDER 1%)
- **bqml_1m**: 0.72% MAPE ✅ (UNDER 1%)
- **bqml_3m_all_features**: 0.70% MAPE ✅ (UNDER 1%)
- **bqml_6m_all_features**: 1.21% MAPE ❌ (OVER 1%)

**BUT** - bqml_3m and bqml_3m_all_features have SAME MAE (0.932), so they're likely the same model.

---

## QUESTIONS TO ANSWER

1. **What is the ACTUAL MAPE for bqml_3m?** (not _all_features)
2. **What is the ACTUAL MAPE for bqml_6m?** (not _all_features)
3. **Are we using the RIGHT models?**
4. **Should we use bqml_3m_all_features instead of bqml_3m?**

---

## CURRENT FORECAST SCRIPT USES

- `bqml_1w` ✅
- `bqml_1m` ✅
- `bqml_3m` ⚠️ (maybe should be bqml_3m_all_features?)
- `bqml_6m` ✅

---

## MAPE VALUES IN CURRENT FORECASTS

- 1W: 1.21% ❌ (WRONG - should be 0.74%)
- 1M: 1.29% ❌ (WRONG - should be 0.72%)
- 3M: 0.70% ✅ (CORRECT)
- 6M: 1.21% ⚠️ (Need to verify actual MAPE)

---

## ACTION REQUIRED

**DO NOT GENERATE FORECASTS UNTIL:**
1. ✅ Verify actual MAPE for all 4 models we're using
2. ✅ Confirm we're using the models with best MAPE (<1%)
3. ✅ Update forecast script with correct MAPE values
4. ✅ User approves model selection

**STATUS:** ⚠️ **WAITING FOR VERIFICATION**

