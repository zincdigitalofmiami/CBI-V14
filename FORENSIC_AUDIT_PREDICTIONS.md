# FORENSIC AUDIT: Past Two Training and Prediction Outcomes

**Date:** November 5, 2025  
**Status:** CRITICAL ISSUES IDENTIFIED

---

## EXECUTIVE SUMMARY

**Only ONE prediction run exists** (Nov 4, 2025), not two. Predictions are significantly underestimating actual prices, with errors ranging from **2.87% to 10.66%**. The training dataset is **2 days behind** (latest: Nov 3), and models were trained on low-volatility 2024 data, causing them to miss the current high-volatility regime.

---

## TRAINING OUTCOMES

### Model Training Dates
- **Training Files Last Modified:** November 4, 2025 at 16:41
- **Models Created:** `bqml_1w`, `bqml_1m`, `bqml_3m`, `bqml_6m`
- **Training Dataset Latest Date:** November 3, 2025 (2 days behind current date)
- **Training Dataset Total Rows:** 2,043 rows

### Training Configuration
- **Model Type:** `BOOSTED_TREE_REGRESSOR`
- **Features:** 258 features (excluding 100% NULL columns)
- **Max Iterations:** 100
- **Learn Rate:** 0.1
- **Early Stop:** False

### Training Data Issues
1. **Stale Training Dataset:** Latest date is Nov 3, but today is Nov 5 (2 days behind)
2. **Missing Recent Volatility:** Training data doesn't include Nov 4-5 high-volatility days
3. **Low-Volatility Training Regime:** Models trained primarily on 2024 data with lower volatility

---

## PREDICTION OUTCOMES

### Prediction Run #1 (ONLY RUN FOUND)

**Date:** November 4, 2025 at 21:56:18  
**Forecast Date:** November 4, 2025

| Horizon | Predicted Price | Actual Price | Error ($) | Error (%) | Status |
|---------|----------------|--------------|-----------|-----------|--------|
| **1W** | $48.07 | $49.49-$49.50 | $1.42-$1.43 | **2.87-2.89%** | ⚠️ UNDERESTIMATE |
| **1M** | $46.00 | $49.49-$49.50 | $3.49-$3.50 | **7.05-7.07%** | ❌ SIGNIFICANT UNDERESTIMATE |
| **3M** | $44.22 | $49.49-$49.50 | $5.27-$5.28 | **10.64-10.66%** | ❌ CRITICAL UNDERESTIMATE |
| **6M** | $47.37 | $49.49-$49.50 | $2.12-$2.13 | **4.28-4.30%** | ⚠️ UNDERESTIMATE |

**Key Findings:**
- All 4 horizons **underestimated** actual prices
- Error increases with horizon length (1W: 2.87%, 3M: 10.66%)
- Predictions were generated **before** training dataset was updated with Nov 4 data
- Confidence intervals were NULL (not calculated)

### Prediction Run #2
**STATUS:** ❌ **DOES NOT EXIST**

Only one prediction run found in the database. No second run to compare.

---

## MARKET MOVEMENT ANALYSIS

### Actual Market Prices (Last 7 Days)

| Date | Avg Price | Price Range | Daily Volatility | Price Change vs Previous |
|------|-----------|-------------|------------------|--------------------------|
| **Nov 5** | $49.56 | $49.52-$49.61 | 0.18% | +0.06 (+0.12%) |
| **Nov 4** | $49.50 | $49.49-$49.50 | 0.02% | -0.34 (-0.68%) |
| **Nov 3** | $49.84 | $49.84 (static) | 0.00% | +1.16 (**+2.38% SURGE**) |
| **Oct 31** | $48.68 | $48.68 (static) | 0.00% | -0.90 (-1.81%) |
| **Oct 30** | $49.58 | $49.45-$49.65 | 0.40% | -0.52 (-1.04%) |
| **Oct 29** | $50.10 | $49.76-$50.26 | 1.00% | Baseline |

### Critical Market Events
1. **Oct 31:** Significant drop (-1.81%) to $48.68
2. **Nov 3:** **Major surge (+2.38%)** to $49.84 (models missed this)
3. **Nov 4:** Slight correction (-0.68%) to $49.50

---

## ROOT CAUSE ANALYSIS

### Issue #1: Training Dataset Staleness
- **Current Status:** Training dataset latest date = Nov 3 (2 days behind)
- **Impact:** Predictions generated on Nov 4 used data from Nov 3, missing Nov 4 price movements
- **Root Cause:** Training dataset rebuild not completed (started Nov 4, still running)

### Issue #2: Model Volatility Mismatch
- **Training Regime:** Models trained on 2024 low-volatility data (stddev ~$2.56)
- **Current Market:** High volatility with 2.38% daily swings
- **Impact:** Models learned conservative behavior, underestimate prices in high-volatility environment

### Issue #3: Prediction Timing
- **Prediction Generated:** Nov 4 at 21:56:18
- **Training Data Available:** Only through Nov 3
- **Impact:** Predictions couldn't incorporate Nov 4 actual price movements

### Issue #4: Missing Confidence Intervals
- **Status:** `lower_bound_80`, `upper_bound_80`, `lower_bound_95`, `upper_bound_95` are all NULL
- **Impact:** No uncertainty quantification, can't assess prediction reliability

### Issue #5: Only One Prediction Run
- **Status:** Only one prediction run exists (Nov 4)
- **Impact:** Cannot compare prediction accuracy over time or assess model degradation

---

## PREDICTION VS ACTUAL COMPARISON

### Nov 4 Predictions (Generated Nov 4, 21:56:18)

**Actual Market Price on Nov 4:** $49.49-$49.50

| Horizon | Predicted | Actual | Gap | % Error | Assessment |
|---------|-----------|--------|-----|---------|------------|
| 1W | $48.07 | $49.50 | -$1.43 | -2.89% | Underestimated, but closer |
| 1M | $46.00 | $49.50 | -$3.50 | -7.07% | **Significantly low** |
| 3M | $44.22 | $49.50 | -$5.28 | -10.66% | **Critically low** |
| 6M | $47.37 | $49.50 | -$2.13 | -4.30% | Underestimated |

**Pattern:** Longer horizons have larger underestimation errors.

---

## DATA PIPELINE STATUS

### Soybean Oil Prices (ZL Futures)
- **Latest Date:** Nov 5, 2025
- **Status:** ✅ Up-to-date (fixed Nov 4)
- **Data Quality:** Good (includes Nov 3 surge)

### Palm Oil Prices
- **Latest Date:** Nov 5, 2025
- **Status:** ✅ Up-to-date (fixed Nov 4)
- **Data Quality:** Good

### Training Dataset
- **Latest Date:** Nov 3, 2025
- **Status:** ❌ **2 days behind**
- **Impact:** Predictions can't use most recent data
- **Action Required:** Complete training dataset rebuild

---

## CRITICAL FINDINGS

### 1. Prediction Accuracy Degradation
- **1W Horizon:** 2.87% error (acceptable for short-term)
- **1M Horizon:** 7.07% error (unacceptable)
- **3M Horizon:** 10.66% error (**critically unacceptable**)
- **6M Horizon:** 4.30% error (unacceptable)

### 2. Systematic Underestimation
- All predictions are **below** actual prices
- Error magnitude increases with horizon length
- Suggests model learned conservative bias from low-volatility training data

### 3. Missing Volatility Response
- Models didn't capture Nov 3 surge (+2.38%)
- Predictions show static behavior, not reflecting market volatility
- Training data doesn't include recent high-volatility regime

### 4. Single Prediction Run
- Only one prediction run exists (Nov 4)
- Cannot assess model performance over time
- No historical comparison possible

---

## RECOMMENDATIONS

### Immediate Actions (Priority 1)

1. **Complete Training Dataset Rebuild**
   - Verify rebuild completed with data through Nov 5
   - Ensure all 258 features calculated correctly
   - Include fresh palm oil and ZL price data

2. **Generate New Predictions**
   - Run predictions with fresh training data
   - Compare to Nov 4 predictions to assess improvement
   - Verify predictions now reflect current market price (~$49.56)

3. **Calculate Prediction Errors**
   - Compare new predictions to actual prices
   - Document error rates for each horizon
   - Identify if underestimation persists

### Short-Term Actions (Priority 2)

4. **Model Retraining Assessment**
   - Evaluate if models need retraining on recent high-volatility data
   - Consider retraining on 2023-2025 only (exclude low-volatility 2020-2022)
   - Test models trained on recent data only

5. **Volatility Regime Detection**
   - Implement VIX-based regime detection
   - Adjust confidence intervals based on volatility regime
   - Flag predictions during high-volatility periods

6. **Automated Prediction Generation**
   - Deploy Cloud Function for daily predictions
   - Set up monitoring for prediction accuracy
   - Alert on prediction errors >5%

### Long-Term Actions (Priority 3)

7. **Backtesting Framework**
   - Implement systematic backtesting against historical prices
   - Track prediction accuracy over time
   - Identify model degradation patterns

8. **Model Performance Monitoring**
   - Create prediction_accuracy table
   - Track MAE, MAPE, R² for each horizon
   - Set up automated alerts for performance degradation

9. **Volatility-Adjusted Models**
   - Train separate models for high-volatility vs low-volatility regimes
   - Use ensemble approach combining regime-specific models
   - Implement dynamic model selection based on current volatility

---

## NEXT STEPS

1. **Verify training dataset rebuild** (check if completed overnight)
2. **Generate new predictions** with fresh data
3. **Compare new predictions to actuals** (Nov 5 price: $49.56)
4. **Assess if underestimation persists** or if fresh data fixes the issue
5. **Document findings** and update plan accordingly

---

## FILES REFERENCED

- `HANDOFF_NOV5_END_OF_DAY.md` - Previous day's findings
- `bigquery-sql/BQML_*_PRODUCTION.sql` - Model training scripts
- `cbi-v14.predictions_uc1.production_forecasts` - Prediction table
- `cbi-v14.models_v4.training_dataset_super_enriched` - Training dataset
- `cbi-v14.forecasting_data_warehouse.soybean_oil_prices` - ZL futures data

---

**Status:** ⚠️ **CRITICAL ISSUES IDENTIFIED** - Predictions significantly underestimating actual prices, training dataset 2 days behind, only one prediction run exists.







