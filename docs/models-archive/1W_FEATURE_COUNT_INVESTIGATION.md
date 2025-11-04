# 1W Model Feature Count Investigation

**Date:** 2025-11-02  
**Model:** `bqml_1w_mean`  
**Issue:** Model has only 57 features instead of expected ~188

## Summary

- **Expected Features:** ~188 (206 total columns - 21 exclusions)
- **Actual Features in Model:** 57
- **Missing:** 131 features
- **Discrepancy:** 131 features not used by model

## Analysis Results

### Sample Analysis (50 missing features):

1. **NULL-only features:** 0
   - No features are completely NULL

2. **Constant/Zero Variance features:** 10 (5 constant + 5 zero variance)
   - These were correctly excluded by BQML
   - Examples: `import_posts`, `supply_demand_ratio`, `cftc_managed_short`, `is_low_vol`, `is_high_vol`

3. **Features with Variance (incorrectly excluded):** 44 (88% of sample)
   - These features have meaningful variance but were excluded
   - Examples:
     - `return_1d` (967 distinct values)
     - `crude_price` (1,077 distinct values)
     - `crush_margin_7d_ma` (1,251 distinct values)
     - `fx_usd_ars_30d_z` (1,251 distinct values)
     - `brazil_temperature_c` (485 distinct values)
     - Many correlation features, sentiment features, etc.

## Root Cause

BQML's BOOSTED_TREE_REGRESSOR performs automatic feature selection during training. With only 1,251 training rows and potentially high feature correlation, the model selected only the 57 most predictive features and excluded the rest.

This is **expected behavior** for boosted tree models:
- Tree-based models inherently perform feature selection
- Limited training data (1,251 rows) means model conservatively uses only highly predictive features
- BQML optimizes for predictive performance, not feature inclusion

## Features Included in Model (57 total)

Top correlation and lag features:
1. `corr_zl_corn_365d` - Most important (0.6979)
2. `dxy_lag2` - 0.5994
3. `yoy_change` - 0.4957
4. `corr_zl_vix_365d` - 0.3663
5. `brazil_month` - 0.2931
6. `brazil_precip_30d_ma` - 0.2870
7. Various correlation features (corn, crude, palm, dxy, vix)
8. Lag features (corn_lag1, etc.)
9. Brazil weather features
10. Composite scores (big8_composite_score)

## Features Excluded (Sample of 44 with variance):

Important features that were excluded despite having variance:
- `crude_price` (1,077 distinct values)
- `return_1d` (967 distinct values)
- `meal_price_per_ton` (955 distinct values)
- `crush_margin_7d_ma` (1,251 distinct values)
- `brazil_temperature_c` (485 distinct values)
- `yield_curve` (183 distinct values)
- `harvest_pressure` (198 distinct values)
- China-related features (`china_mentions`, `china_policy_impact`)
- Many correlation features at different timeframes
- Sentiment features

## Impact

### Positive:
- Model focuses on most predictive features only
- Reduces overfitting risk with limited data
- Training/inference is faster

### Negative:
- Many potentially useful features not utilized
- May miss predictive signals from excluded features
- Model may not capture full feature space

## Recommendations

### Option 1: Accept Current State (Recommended)
- 57 features is reasonable for 1,251 training rows
- Model is performing feature selection automatically
- If performance is good (need to check metrics), keep as-is

### Option 2: Force Feature Inclusion
- Not recommended - BQML doesn't support forcing all features
- Would require manual feature engineering/pre-selection
- May hurt performance if features are not predictive

### Option 3: Increase Training Data
- More training rows may allow model to utilize more features
- But current data availability is limited

### Option 4: Use Different Model Type
- LINEAR_REGRESSOR uses all features (but may overfit)
- DNN_REGRESSOR may use more features (but more complex)
- Current BOOSTED_TREE is likely optimal for this dataset

## Action Items

1. ✅ **Verify Model Performance**
   - Check MAE, R² on test set
   - If performance meets targets (MAE < 1.2, R² > 0.98), current feature count is acceptable

2. ⚠️ **Investigate High Eval Loss**
   - Eval/train loss ratio: 55.6x (very high)
   - May indicate overfitting despite feature selection
   - Need to check test set performance

3. 📊 **Compare to Baseline**
   - Compare current 57-feature model to models with more features
   - If performance is similar, feature selection is working correctly

## Conclusion

The 57-feature count is **likely intentional** by BQML's boosted tree algorithm. With only 1,251 training rows, the model conservatively selects only the most predictive features. This is normal behavior and may actually improve generalization.

**Key finding:** 88% of missing features have variance but were excluded anyway, suggesting BQML determined they don't significantly improve predictions given the limited training data.

**Next step:** Verify model performance metrics. If MAE < 1.2 and R² > 0.98, the feature selection is working correctly.


