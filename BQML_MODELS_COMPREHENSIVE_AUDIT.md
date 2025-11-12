# BQML MODELS COMPREHENSIVE AUDIT REPORT
**Date:** November 5, 2025  
**Models Audited:** `bqml_1w`, `bqml_1m`, `bqml_3m`, `bqml_6m`  
**Status:** COMPLETE

---

## EXECUTIVE SUMMARY

**All 4 BQML models exist and have been successfully trained.** However, **model evaluation cannot be performed** because target columns are missing from the base training table. The models use 257-275 features each, with significant NULL rates in many features.

| Model | Status | Features | Training Loss | Eval Loss | Training Data Source |
|-------|--------|----------|---------------|-----------|---------------------|
| **bqml_1w** | ✅ Trained | 275 | 0.303414 | 1.289940 | `training_dataset_super_enriched` |
| **bqml_1m** | ✅ Trained | 274 | 0.304444 | 1.372880 | `training_dataset_super_enriched` |
| **bqml_3m** | ✅ Trained | 267 | 0.299826 | 1.260420 | `training_dataset_super_enriched` |
| **bqml_6m** | ✅ Trained | 257 | 0.287881 | 1.234020 | `training_dataset_super_enriched` |

**Critical Issues:**
1. ❌ Cannot evaluate models (target columns missing from base table)
2. ⚠️ High eval loss vs training loss (potential overfitting)
3. ⚠️ Many features have high NULL rates (45-99% NULLs)
4. ⚠️ No predictions found in production tables

---

## PART 1: MODEL TRAINING DETAILS

### 1.1 Model: bqml_1w

**Training Configuration:**
- **Model Type:** BOOSTED_TREE_REGRESSOR
- **Target:** `target_1w`
- **Iterations:** 100 (full run, no early stopping)
- **Learning Rate:** 0.1
- **Training Loss:** 0.303414
- **Eval Loss:** 1.289940 (4.25x higher than training loss)
- **Duration:** < 1 second (possibly truncated in display)

**Training Progress:**
- Iteration 1: Loss = 47.85, EvalLoss = 49.51
- Iteration 100: Loss = 0.30, EvalLoss = 1.29
- **Loss reduction:** 99.4% improvement
- **Eval loss reduction:** 97.4% improvement

**Training Data:**
- **Source:** `cbi-v14.models_v4.training_dataset_super_enriched`
- **Filter:** `WHERE target_1w IS NOT NULL`
- **Excluded Columns:** 6 (target_1w, target_1m, target_3m, target_6m, date, volatility_regime)

### 1.2 Model: bqml_1m

**Training Configuration:**
- **Model Type:** BOOSTED_TREE_REGRESSOR
- **Target:** `target_1m`
- **Iterations:** 100
- **Learning Rate:** 0.1
- **Training Loss:** 0.304444
- **Eval Loss:** 1.372880 (4.51x higher than training loss)
- **Duration:** < 1 second

**Training Progress:**
- Iteration 1: Loss = 49.50, EvalLoss = 48.97
- Iteration 100: Loss = 0.30, EvalLoss = 1.37
- **Loss reduction:** 99.4% improvement
- **Eval loss reduction:** 97.2% improvement

**Training Data:**
- **Source:** `cbi-v14.models_v4.training_dataset_super_enriched`
- **Filter:** `WHERE target_1m IS NOT NULL`
- **Excluded Columns:** 6 (same as 1W)

### 1.3 Model: bqml_3m

**Training Configuration:**
- **Model Type:** BOOSTED_TREE_REGRESSOR
- **Target:** `target_3m`
- **Iterations:** 100
- **Learning Rate:** 0.1
- **Training Loss:** 0.299826
- **Eval Loss:** 1.260420 (4.20x higher than training loss)
- **Duration:** < 1 second

**Training Progress:**
- Iteration 1: Loss = 49.70, EvalLoss = 48.26
- Iteration 100: Loss = 0.30, EvalLoss = 1.26
- **Loss reduction:** 99.4% improvement
- **Eval loss reduction:** 97.4% improvement

**Training Data:**
- **Source:** `cbi-v14.models_v4.training_dataset_super_enriched`
- **Filter:** `WHERE target_3m IS NOT NULL`
- **Excluded Columns:** 7 (includes additional NULL columns)

### 1.4 Model: bqml_6m

**Training Configuration:**
- **Model Type:** BOOSTED_TREE_REGRESSOR
- **Target:** `target_6m`
- **Iterations:** 100
- **Learning Rate:** 0.1
- **Training Loss:** 0.287881
- **Eval Loss:** 1.234020 (4.28x higher than training loss)
- **Duration:** < 1 second

**Training Progress:**
- Iteration 1: Loss = 50.19, EvalLoss = 48.99
- Iteration 100: Loss = 0.29, EvalLoss = 1.23
- **Loss reduction:** 99.4% improvement
- **Eval loss reduction:** 97.5% improvement

**Training Data:**
- **Source:** `cbi-v14.models_v4.training_dataset_super_enriched`
- **Filter:** `WHERE target_6m IS NOT NULL`
- **Excluded Columns:** 7 (same as 3M)

---

## PART 2: FEATURES USED

### 2.1 Feature Counts by Model

| Model | Total Features | Fully Populated | With NULLs | NULL Rate |
|-------|---------------|-----------------|------------|-----------|
| **bqml_1w** | 275 | 27 | 248 | 90.2% |
| **bqml_1m** | 274 | 32 | 242 | 88.3% |
| **bqml_3m** | 267 | 27 | 240 | 89.9% |
| **bqml_6m** | 257 | 27 | 230 | 89.5% |

**Key Finding:** All models have 88-90% of features with NULL values, indicating significant data sparsity.

### 2.2 Top Features by Variance (All Models)

**Common High-Variance Features:**
1. **soybean_weekly_sales** / **china_soybean_sales** - Highest variance (stddev: 400K-1M), 43-45% NULLs
2. **cftc_open_interest** - Very high variance (stddev: 24K-44K), 40-42% NULLs
3. **cftc_commercial_net** - High variance (stddev: 38K-42K), 40-42% NULLs
4. **cftc_commercial_short** - High variance (stddev: 34K-39K), 40-42% NULLs
5. **zl_volume** - High variance (stddev: 29K-31K), **0% NULLs** (fully populated)
6. **cftc_commercial_long** - Moderate variance (stddev: 18K-20K), 40-42% NULLs
7. **oil_price_per_cwt** - Moderate variance (stddev: 1.1K-1.2K), 4-7% NULLs
8. **palm_lag1/lag2/lag3** - Moderate variance (stddev: 438-452), 4-7% NULLs
9. **usd_ars_rate** - Moderate variance (stddev: 336-435), **0% NULLs** (fully populated)
10. **wheat_lag1** - Moderate variance (stddev: 294-307), 4-7% NULLs

### 2.3 Feature Categories

**All models include:**

**Price Features:**
- `zl_price_current`, `zl_price_lag1`, `zl_price_lag7`, `zl_price_lag30`
- `crude_price`, `palm_price`, `corn_price`, `wheat_price`
- `crush_margin`, `bean_price_per_bushel`, `meal_price_per_ton`, `oil_price_per_cwt`

**Technical Indicators:**
- `ma_7d`, `ma_30d`, `ma_90d`, `volatility_30d`
- `rsi_14`, `macd_line`, `macd_signal`, `macd_histogram`
- `bb_upper`, `bb_lower`, `bb_middle`, `bb_width`

**Correlations:**
- `corr_zl_crude_7d/30d/90d/180d/365d`
- `corr_zl_palm_7d/30d/90d/180d/365d`
- `corr_zl_vix_7d/30d/90d/180d/365d`
- `corr_zl_dxy_7d/30d/90d/180d/365d`
- `corr_zl_corn_7d/30d/90d/365d`
- `corr_zl_wheat_7d/30d`

**Lag Features:**
- `palm_lag1/2/3`, `crude_lag1/2`, `vix_lag1/2`, `dxy_lag1/2`
- `corn_lag1`, `wheat_lag1`

**CFTC Data:**
- `cftc_open_interest`, `cftc_commercial_long/short/net`
- `cftc_managed_long/short/net`
- `cftc_commercial_extreme`, `cftc_spec_extreme`

**China/Policy Features:**
- `china_mentions`, `china_posts`, `china_sentiment`
- `china_soybean_sales`, `china_tariff_rate`
- `trump_mentions`, `trump_policy_events`
- `trump_soybean_sentiment_7d`

**Weather Features:**
- `brazil_temp_c`, `brazil_precip_mm`
- `argentina_temp_c`, `argentina_precip_mm`
- `us_midwest_temp_c`, `us_midwest_precip_mm`

**Economic Indicators:**
- `gdp_growth`, `cpi_yoy`, `unemployment_rate`
- `fed_funds_rate`, `treasury_10y_yield`
- `vix_level`, `dxy_level`

**Seasonal Features:**
- `seasonal_index`, `monthly_zscore`
- `seasonal_cos`, `seasonal_sin`
- `day_of_week`, `day_of_month`, `month`, `quarter`

**Event Features:**
- `is_wasde_day`, `is_fomc_day`, `is_crop_report_day`
- `days_to_next_event`, `days_since_last_event`
- `event_impact_level`, `event_vol_mult`

**Feature Engineering:**
- `big8_composite_score`
- `feature_vix_stress`, `feature_harvest_pace`
- `feature_china_relations`, `feature_tariff_threat`
- `feature_geopolitical_volatility`
- `feature_biofuel_cascade`, `feature_biofuel_ethanol`
- `feature_hidden_correlation`

---

## PART 3: MODEL EVALUATION

### 3.1 Evaluation Status

**Status:** ❌ **CANNOT EVALUATE**

**Reason:** Target columns (`target_1w`, `target_1m`, `target_3m`, `target_6m`) do not exist in the base table `training_dataset_super_enriched`.

**Error Message:**
```
400 Unrecognized name: target_X at [11:22]
```

**Impact:**
- Cannot calculate MAE, MSE, R², or other evaluation metrics
- Cannot verify model performance on validation data
- Cannot compare model performance across horizons

### 3.2 Training vs Eval Loss Analysis

**Eval Loss vs Training Loss Ratio:**

| Model | Training Loss | Eval Loss | Ratio | Status |
|-------|---------------|-----------|-------|--------|
| **bqml_1w** | 0.303414 | 1.289940 | 4.25x | ⚠️ **Potential Overfitting** |
| **bqml_1m** | 0.304444 | 1.372880 | 4.51x | ⚠️ **Potential Overfitting** |
| **bqml_3m** | 0.299826 | 1.260420 | 4.20x | ⚠️ **Potential Overfitting** |
| **bqml_6m** | 0.287881 | 1.234020 | 4.28x | ⚠️ **Potential Overfitting** |

**Analysis:**
- All models show **4-4.5x higher eval loss than training loss**
- This suggests **potential overfitting** to training data
- Models may not generalize well to new data
- **Recommendation:** Enable early stopping or reduce max_iterations

---

## PART 4: PREDICTIONS

### 4.1 Prediction Status

**Status:** ✅ **PREDICTIONS FOUND**

**Prediction Table:** `cbi-v14.predictions_uc1.production_forecasts`

**Recent Predictions (Last 5 Days):**

| Model | Forecast Date | Horizon | Target Date | Predicted Value | Confidence | MAPE Historical | Created At |
|-------|--------------|---------|-------------|----------------|------------|-----------------|------------|
| **bqml_1w** | 2025-11-04 | 1W | 2025-11-10 | $48.07 | 75.0% | 1.21% | 2025-11-04 21:56:18 |
| **bqml_1m** | 2025-11-04 | 1M | 2025-12-03 | $46.00 | 70.0% | 1.29% | 2025-11-04 21:56:18 |
| **bqml_3m** | 2025-11-04 | 3M | 2026-02-01 | $44.22 | 65.0% | 0.70% | 2025-11-04 21:56:18 |
| **bqml_6m** | 2025-11-04 | 6M | 2026-05-02 | $47.37 | 60.0% | 1.21% | 2025-11-04 21:56:18 |

**Key Findings:**
- ✅ All 4 models generated predictions on November 4, 2025
- ✅ Predictions created at 21:56:18 UTC (same batch)
- ✅ Confidence scores: 60-75% (decreasing with horizon length)
- ✅ Historical MAPE: 0.70-1.29% (excellent accuracy)
- ⚠️ No predictions in the last 24 hours (as of Nov 5 audit)

**Prediction Generation:**
- Predictions are generated via `GENERATE_PRODUCTION_FORECASTS.sql` or `GENERATE_CLEAN_FORECASTS.sql`
- Uses `ML.PREDICT()` on BQML models with latest row from `training_dataset_super_enriched`
- Predictions stored in `predictions_uc1.production_forecasts` table

**Impact:**
- ✅ Models are actively being used for predictions
- ✅ Predictions are being generated and stored
- ⚠️ Last predictions are 1 day old (may need refresh)

---

## PART 5: TRAINING DATA SOURCE

### 5.1 Data Source Analysis

**All models use:** `cbi-v14.models_v4.training_dataset_super_enriched`

**Filters Applied:**
- **bqml_1w:** `WHERE target_1w IS NOT NULL`
- **bqml_1m:** `WHERE target_1m IS NOT NULL`
- **bqml_3m:** `WHERE target_3m IS NOT NULL`
- **bqml_6m:** `WHERE target_6m IS NOT NULL`

**Excluded Columns:**
- All target columns (target_1w, target_1m, target_3m, target_6m)
- `date`
- `volatility_regime` (STRING type)
- Additional NULL columns for longer horizons (news data, trump data)

### 5.2 Data Source Mismatch

**Issue:** SQL files reference `training_dataset_super_enriched` expecting target columns, but the base table currently has only 11 feature columns with NO targets.

**Possible Explanations:**
1. Models were trained when targets existed in the table
2. Table was truncated/modified after training
3. Training views should be used instead of base table
4. Models are using cached/stale training data

**Recommendation:** Verify when models were created and whether the table structure has changed since training.

---

## PART 6: CRITICAL ISSUES & RECOMMENDATIONS

### Issue #1: Cannot Evaluate Models
**Severity:** 🔴 **CRITICAL**

**Problem:** Target columns missing from base table prevents evaluation.

**Impact:**
- Cannot verify model performance
- Cannot compare models
- Cannot detect model degradation

**Recommendation:**
1. Restore target columns to `training_dataset_super_enriched`
2. OR use training views (`train_1w`, `train_1m`, `train_3m`, `train_6m`) for evaluation
3. Implement evaluation on validation set

### Issue #2: Potential Overfitting
**Severity:** 🟡 **WARNING**

**Problem:** Eval loss is 4-4.5x higher than training loss.

**Impact:**
- Models may not generalize well
- Predictions may be less accurate on new data

**Recommendation:**
1. Enable early stopping with validation split
2. Reduce max_iterations (try 50 instead of 100)
3. Tune learning rate
4. Add regularization

### Issue #3: High Feature NULL Rates
**Severity:** 🟡 **WARNING**

**Problem:** 88-90% of features have NULL values.

**Impact:**
- Models may rely heavily on fully populated features
- Missing feature patterns may not be learned effectively

**Recommendation:**
1. Implement feature imputation
2. Remove features with >90% NULLs
3. Create indicator features for missingness
4. Focus on fully populated features

### Issue #4: Predictions Found But Not Recent
**Severity:** 🟢 **INFO** (Updated from Warning)

**Status:** ✅ Predictions exist in `predictions_uc1.production_forecasts` table.

**Finding:**
- Last predictions generated: November 4, 2025 at 21:56:18 UTC
- All 4 models generated predictions in same batch
- Predictions are 1+ days old (as of Nov 5 audit)

**Impact:**
- ✅ Models are deployed and generating predictions
- ⚠️ Predictions may need refresh for current date

**Recommendation:**
1. Verify if daily prediction job is running
2. Check if predictions need to be refreshed for Nov 5
3. Monitor prediction generation schedule

### Issue #5: Training Data Source Mismatch
**Severity:** 🟡 **WARNING**

**Problem:** SQL files reference base table with targets that don't exist.

**Impact:**
- Cannot retrain models with current SQL
- Training data source unclear

**Recommendation:**
1. Verify table structure at training time
2. Document training data source
3. Consider using training views for consistency

---

## PART 7: MODEL COMPARISON

### 7.1 Training Loss Comparison

| Model | Training Loss | Rank |
|-------|---------------|------|
| **bqml_6m** | 0.287881 | 1 (best) |
| **bqml_3m** | 0.299826 | 2 |
| **bqml_1w** | 0.303414 | 3 |
| **bqml_1m** | 0.304444 | 4 |

**Finding:** Longer horizons (6M, 3M) have slightly lower training loss than shorter horizons (1W, 1M).

### 7.2 Eval Loss Comparison

| Model | Eval Loss | Rank |
|-------|-----------|------|
| **bqml_6m** | 1.234020 | 1 (best) |
| **bqml_3m** | 1.260420 | 2 |
| **bqml_1w** | 1.289940 | 3 |
| **bqml_1m** | 1.372880 | 4 |

**Finding:** Longer horizons also have lower eval loss, suggesting better generalization.

### 7.3 Feature Count Comparison

| Model | Features | Difference from 1W |
|-------|----------|-------------------|
| **bqml_1w** | 275 | Baseline |
| **bqml_1m** | 274 | -1 |
| **bqml_3m** | 267 | -8 |
| **bqml_6m** | 257 | -18 |

**Finding:** Longer horizons have fewer features due to more NULL columns (news data, trump data only available from Oct 2024).

---

## PART 8: KEY METRICS SUMMARY

### Training Metrics

| Metric | bqml_1w | bqml_1m | bqml_3m | bqml_6m |
|--------|---------|---------|---------|---------|
| **Status** | ✅ Trained | ✅ Trained | ✅ Trained | ✅ Trained |
| **Features** | 275 | 274 | 267 | 257 |
| **Training Loss** | 0.303 | 0.304 | 0.300 | 0.288 |
| **Eval Loss** | 1.290 | 1.373 | 1.260 | 1.234 |
| **Eval/Train Ratio** | 4.25x | 4.51x | 4.20x | 4.28x |
| **Iterations** | 100 | 100 | 100 | 100 |
| **Learning Rate** | 0.1 | 0.1 | 0.1 | 0.1 |

### Data Quality Metrics

| Metric | bqml_1w | bqml_1m | bqml_3m | bqml_6m |
|--------|---------|---------|---------|---------|
| **Features with NULLs** | 248 (90%) | 242 (88%) | 240 (90%) | 230 (90%) |
| **Fully Populated** | 27 (10%) | 32 (12%) | 27 (10%) | 27 (11%) |

### Evaluation Status

| Model | Can Evaluate | Reason |
|-------|-------------|--------|
| **bqml_1w** | ❌ | Target column missing |
| **bqml_1m** | ❌ | Target column missing |
| **bqml_3m** | ❌ | Target column missing |
| **bqml_6m** | ❌ | Target column missing |

### Prediction Status

| Model | Has Predictions | Latest Prediction Date | Latest Predicted Value | Confidence |
|-------|----------------|----------------------|----------------------|------------|
| **bqml_1w** | ✅ | 2025-11-04 | $48.07 | 75.0% |
| **bqml_1m** | ✅ | 2025-11-04 | $46.00 | 70.0% |
| **bqml_3m** | ✅ | 2025-11-04 | $44.22 | 65.0% |
| **bqml_6m** | ✅ | 2025-11-04 | $47.37 | 60.0% |

---

## CONCLUSION

**Summary:**
- ✅ All 4 BQML models exist and have been successfully trained
- ✅ Models use 257-275 features with comprehensive coverage
- ✅ **Predictions found:** All 4 models generated predictions on Nov 4, 2025
- ⚠️ Eval loss is 4-4.5x higher than training loss (potential overfitting)
- ❌ Cannot evaluate models (target columns missing from base table)
- ⚠️ 88-90% of features have NULL values
- ⚠️ Last predictions are 1+ days old (may need refresh)

**Critical Actions Required:**
1. Restore target columns to base table OR use training views for evaluation
2. Address overfitting (enable early stopping, reduce iterations)
3. Implement feature imputation or remove high-NULL features
4. Verify prediction pipeline and create prediction tracking
5. Document training data source and verify table structure

**Status:** ✅ **MODELS TRAINED AND GENERATING PREDICTIONS** - Predictions found in `predictions_uc1.production_forecasts`. Critical issue: cannot evaluate due to missing target columns.

---

**Report Generated:** 2025-11-05 12:23:31  
**Audit Method:** Direct BigQuery ML queries + SQL file analysis

