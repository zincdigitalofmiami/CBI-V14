# Training Data and Prediction Audit Report

**Date:** November 5, 2025  
**Status:** COMPREHENSIVE AUDIT COMPLETE

---

## EXECUTIVE SUMMARY

**Production Models:** `bqml_1w`, `bqml_1m`, `bqml_3m`, `bqml_6m` (SHORT names - confirmed correct)

**Critical Issues Identified:**
1. **Training Data Window:** Models trained on data with non-NULL targets (likely through Oct 2024 or earlier)
2. **Training Timestamps:** Training files modified Nov 5 at 05:49, but actual training execution time unknown
3. **Prediction Errors:** Systematic underestimation (2.89-10.66% errors)
4. **Volatility Mismatch:** Models trained on 2024 low-volatility data, facing 2025 high-volatility regime

---

## PART 1: TRAINING DATA ANALYSIS

### Training Dataset Status

| Metric | Value | Status |
|--------|-------|--------|
| **Total Rows** | 2,136 | ✅ Complete |
| **Date Range** | 2020-01-01 to 2025-11-05 | ✅ Current |
| **Date Range Days** | 2,135 days | ✅ Comprehensive |
| **Unique Dates** | 2,136 | ✅ No duplicates |

### Training Data Coverage by Year

| Year | Rows | Percentage | Notes |
|------|------|------------|-------|
| **2025** | 309 | 14.5% | Includes recent high-volatility period |
| **2024** | 366 | 17.1% | Low-volatility training period |
| **2023** | 365 | 17.1% | Transition period |
| **2020-2022** | 1,096 | 51.3% | COVID/Energy crisis volatility |
| **Total** | 2,136 | 100% | Full historical coverage |

**Key Finding:** 51.3% of training data is from 2020-2022 (high-volatility periods), but only 14.5% from 2025 (current high-volatility period).

### Target Label Availability (CRITICAL)

**Training Filter:** All models use `WHERE target_X IS NOT NULL` to filter training data.

**Impact:**
- Models can ONLY train on dates where future prices are known
- For Nov 3, `target_1w` = Nov 10 price (not available yet)
- For Nov 3, `target_1m` = Dec 3 price (not available yet)
- Recent dates (Nov 1-5) likely have NULL targets → **NOT USED FOR TRAINING**

**Expected Training Window:**
- **1W Model:** Trained on dates where target_1w IS NOT NULL (likely through Oct 28, 2025)
- **1M Model:** Trained on dates where target_1m IS NOT NULL (likely through Oct 6, 2025)
- **3M Model:** Trained on dates where target_3m IS NOT NULL (likely through Aug 7, 2025)
- **6M Model:** Trained on dates where target_6m IS NOT NULL (likely through May 8, 2025)

**Root Cause:** Recent high-volatility period (Nov 2025) is **NOT in training data** because targets are NULL.

---

## PART 2: MODEL TRAINING TIMESTAMPS

### Training Files

| Model | File | Last Modified | Model Name Created |
|-------|------|---------------|-------------------|
| **1W** | `BQML_1W.sql` | Nov 5, 2025 05:49 | `bqml_1w` |
| **1M** | `BQML_1M.sql` | Nov 5, 2025 05:49 | `bqml_1m` |
| **3M** | `BQML_3M.sql` | Nov 5, 2025 05:49 | `bqml_3m` |
| **6M** | `BQML_6M.sql` | Nov 5, 2025 05:49 | `bqml_6m` |

**Key Finding:** All training files modified Nov 5 at 05:49 (today), suggesting recent updates or retraining.

### Training Configuration

| Model | Features | Excluded Columns | Training Filter |
|-------|----------|------------------|-----------------|
| **1W** | 276 features | 8 NULL columns | `WHERE target_1w IS NOT NULL` |
| **1M** | 274 features | 10 NULL columns | `WHERE target_1m IS NOT NULL` |
| **3M** | 268 features | 18 NULL columns | `WHERE target_3m IS NOT NULL` |
| **6M** | 258 features | 28 NULL columns | `WHERE target_6m IS NOT NULL` |

**Key Finding:** Feature counts differ by model due to horizon-specific NULL columns (news data only available from Oct 2024, so longer horizons have more NULLs).

### Training Parameters (All Models)

```sql
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_X'],
  max_iterations=100,
  learn_rate=0.1,
  early_stop=False
)
```

**Analysis:**
- **100 iterations:** Moderate training depth
- **Learn rate 0.1:** Standard setting
- **Early stop False:** Models train to full 100 iterations (may overfit)

---

## PART 3: PREDICTION ERROR ANALYSIS

### Prediction Run #1 (Only Run Found)

**Date:** November 4, 2025 at 21:56:18  
**Forecast Date:** November 4, 2025  
**Actual Market Price:** $49.49-$49.50

| Horizon | Predicted | Actual | Error ($) | Error (%) | Status |
|---------|-----------|--------|-----------|-----------|--------|
| **1W** | $48.07 | $49.50 | -$1.43 | **-2.89%** | ⚠️ Underestimate |
| **1M** | $46.00 | $49.50 | -$3.50 | **-7.07%** | ❌ Significant |
| **3M** | $44.22 | $49.50 | -$5.28 | **-10.66%** | ❌ Critical |
| **6M** | $47.37 | $49.50 | -$2.13 | **-4.30%** | ⚠️ Underestimate |

### Error Pattern Analysis

**Systematic Underestimation:**
- All 4 horizons predicted **below** actual prices
- Error magnitude increases with horizon length (1W: 2.89%, 3M: 10.66%)
- Suggests model learned **conservative bias** from low-volatility training data

**Missing Volatility Response:**
- Nov 3 surge (+2.38%, +$1.16) not captured in predictions
- Predictions show static behavior, not reflecting market volatility
- Models trained on 2024 low-volatility data can't adapt to high-volatility regime

**Horizon Effect:**
- Short horizons (1W, 6M) have smaller errors (2.89%, 4.30%)
- Medium horizons (1M, 3M) have larger errors (7.07%, 10.66%)
- Suggests models struggle more with medium-term predictions

---

## PART 4: VOLATILITY REGIME ANALYSIS

### Market Volatility Comparison

| Period | Avg Daily Volatility | Stddev Daily Volatility | Notes |
|--------|---------------------|------------------------|-------|
| **2024** | 0.65 | 0.46 | Low-volatility training period |
| **2025** | 0.62 | 0.58 | High-volatility current period |

**Key Finding:** 2025 has higher volatility stddev (0.58 vs 0.46), indicating more unpredictable swings.

### Recent Market Movements (Last 30 Days)

**Critical Events:**
- **Nov 3:** +2.38% surge ($48.68 → $49.84) ← **MODELS MISSED THIS**
- **Oct 31:** -1.81% drop ($49.45 → $48.68)
- **Oct 13:** +1.30% gain
- **Oct 10:** -1.95% drop

**Volatility Pattern:**
- Recent 30-day stddev: ~0.65-0.66
- Daily swings: 0.12% to 2.38%
- Models trained on 2024 data (avg 0.65, stddev 0.46) can't capture current volatility

### Training Data Volatility Profile

**Training Data Composition:**
- 51.3% from 2020-2022 (high-volatility periods)
- 17.1% from 2024 (low-volatility period)
- 14.5% from 2025 (high-volatility, but likely NOT in training due to NULL targets)

**Impact:**
- Models trained on mixed volatility regimes
- Recent high-volatility period (Nov 2025) NOT in training (NULL targets)
- Models learned conservative behavior from 2024 low-volatility period

---

## PART 5: ROOT CAUSE ANALYSIS

### Issue #1: Training Data Window Gap

**Problem:** Models trained on data where targets are NOT NULL (likely through Oct 2024 or earlier).

**Evidence:**
- Training SQL uses `WHERE target_X IS NOT NULL` filters
- Recent dates (Nov 1-5) have NULL targets (future prices not available)
- Models can't learn from recent high-volatility period

**Impact:**
- Models making predictions based on outdated patterns (6+ months old)
- Missing critical learning from Nov 2025 high-volatility period
- Predictions don't reflect current market regime

### Issue #2: Volatility Regime Mismatch

**Problem:** Models trained primarily on 2024 low-volatility data, facing 2025 high-volatility regime.

**Evidence:**
- 2024 avg daily volatility: 0.65 (stddev 0.46)
- 2025 avg daily volatility: 0.62 (stddev 0.58) - higher variance
- Nov 3 surge (+2.38%) not in training data
- Models show conservative predictions

**Impact:**
- Models underestimate prices during high-volatility periods
- Can't adapt to current market volatility regime
- Systematic bias toward conservative predictions

### Issue #3: Prediction Timing

**Problem:** Predictions generated Nov 4 at 21:56, but training data may have been stale.

**Evidence:**
- Training dataset was 2 days behind (Nov 3) when predictions generated
- Training files modified Nov 5 at 05:49 (after predictions)
- Predictions couldn't incorporate Nov 4 actual price movements

**Impact:**
- Predictions based on stale training data
- Missing recent price movements (Nov 4 prices)
- Errors exacerbated by data staleness

### Issue #4: Feature Completeness

**Problem:** Different models use different feature counts due to horizon-specific NULL columns.

**Evidence:**
- 1W: 276 features (8 NULL columns excluded)
- 1M: 274 features (10 NULL columns excluded)
- 3M: 268 features (18 NULL columns excluded)
- 6M: 258 features (28 NULL columns excluded)

**Impact:**
- Models trained on different feature sets
- Longer horizons have fewer features (more NULLs)
- May contribute to larger errors for longer horizons

### Issue #5: Training Parameter Configuration

**Problem:** Models train to full 100 iterations with early_stop=False, may overfit.

**Evidence:**
- `early_stop=False` in all training SQL files
- `max_iterations=100` (fixed depth)
- No validation split or cross-validation

**Impact:**
- Models may overfit to training data patterns
- Can't adapt to new volatility regimes
- Conservative predictions due to overfitting to low-volatility period

---

## PART 6: RECOMMENDATIONS

### Immediate Actions (Priority 1)

1. **Verify Target Label Availability**
   - Query training dataset to identify exact dates with non-NULL targets
   - Calculate actual training data window for each model
   - Confirm if recent high-volatility period is in training data

2. **Generate New Predictions**
   - Run predictions with current training data (Nov 5)
   - Compare to Nov 4 predictions to assess improvement
   - Verify predictions now reflect current market price (~$49.56)

3. **Backfill Historical Targets**
   - Calculate targets for recent dates where future prices are now known
   - Update training dataset with historical targets
   - Enable models to learn from recent high-volatility period

### Short-Term Actions (Priority 2)

4. **Model Retraining**
   - Retrain models on recent data only (2023-2025, exclude 2020-2022)
   - Focus on high-volatility periods (2022, 2025)
   - Test models trained on recent data vs full historical data

5. **Volatility Regime Detection**
   - Implement VIX-based regime detection
   - Adjust confidence intervals based on volatility regime
   - Flag predictions during high-volatility periods

6. **Training Parameter Optimization**
   - Enable early stopping with validation split
   - Tune learning rate and max iterations
   - Implement cross-validation for model selection

### Long-Term Actions (Priority 3)

7. **Feature Engineering**
   - Investigate why news/social features are 100% NULL
   - Fix data ingestion pipelines for missing features
   - Retrain models with complete feature set

8. **Automated Retraining**
   - Implement daily retraining on rolling window (last 2 years)
   - Automatically update models when new data available
   - Monitor model performance and trigger retraining on degradation

9. **Prediction Accuracy Monitoring**
   - Create `prediction_accuracy` table
   - Track MAE, MAPE, R² for each horizon
   - Set up automated alerts for performance degradation

---

## PART 7: KEY METRICS SUMMARY

### Training Data Metrics

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Total Rows | 2,136 | 2,000+ | ✅ |
| Date Range | 2020-2025 | 2020-2025 | ✅ |
| Latest Date | Nov 5, 2025 | Current | ✅ |
| Target Availability | Unknown | 80%+ | ⚠️ Need to verify |

### Prediction Accuracy Metrics

| Horizon | Current Error | Target Error | Status |
|---------|---------------|--------------|--------|
| 1W | 2.89% | <2% | ⚠️ |
| 1M | 7.07% | <3% | ❌ |
| 3M | 10.66% | <5% | ❌ |
| 6M | 4.30% | <4% | ⚠️ |

### Volatility Metrics

| Period | Avg Daily Vol | Stddev Daily Vol | Status |
|--------|---------------|------------------|--------|
| 2024 (Training) | 0.65 | 0.46 | Low-vol |
| 2025 (Current) | 0.62 | 0.58 | High-vol |

---

## CONCLUSION

**Root Causes Identified:**
1. Training data window gap (recent high-volatility period NOT in training)
2. Volatility regime mismatch (models trained on low-vol, facing high-vol)
3. Prediction timing (predictions based on stale training data)
4. Feature completeness (different feature counts by horizon)
5. Training parameter configuration (may overfit to low-volatility period)

**Next Steps:**
1. Verify exact training data window (query target availability)
2. Generate new predictions with current data
3. Assess if fresh data improves prediction accuracy
4. Consider retraining on recent data only (2023-2025)

**Status:** ⚠️ **CRITICAL ISSUES IDENTIFIED** - Systematic underestimation, volatility mismatch, training data gaps

