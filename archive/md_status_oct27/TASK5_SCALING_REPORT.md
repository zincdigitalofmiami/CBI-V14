# TASK 5 FEATURE SCALING REPORT

**Date:** 2025-10-23 19:56:01

## Summary

- Features scaled: 98
- Training samples: 1000
- Test samples: 251
- Scaler type: StandardScaler (mean=0, std=1)

## Train/Test Split

### Training Set
- Rows: 1000
- Date range: 2020-10-21 to 2024-10-11
- Percentage: 79.9%

### Test Set
- Rows: 251
- Date range: 2024-10-14 to 2025-10-13
- Percentage: 20.1%

## Scaling Verification

- Training set mean: -0.010204 (target: ~0)
- Training set std: 0.980082 (target: ~1)
- Status: ⚠️ Check

## Feature Statistics (Before Scaling)

### Top 10 Features by Range

- `zl_volume`: [0.00, 128535.00] (range: 128535.00)

- `wheat_price`: [498.00, 1425.25] (range: 927.25)

- `corn_price`: [362.00, 818.25] (range: 456.25)

- `meal_price_per_ton`: [303.40, 521.90] (range: 218.50)

- `zl_price_lag30`: [0.00, 90.60] (range: 90.60)

- `crude_price`: [35.79, 123.70] (range: 87.91)

- `zl_price_current`: [33.06, 90.60] (range: 57.54)

- `bean_price_per_bushel`: [9.39, 17.69] (range: 8.30)

- `volatility_30d`: [0.00, 8.06] (range: 8.06)

- `corr_zl_dxy_365d`: [-0.91, 1.00] (range: 1.91)

## Files Created

- `TRAIN_SCALED.csv` - Scaled training set
- `TEST_SCALED.csv` - Scaled test set
- `feature_scaler.pkl` - Fitted scaler object

## ✅ Scaling Complete

Features are now normalized for neural network training.

No data leakage: Scaler fitted on training data only.