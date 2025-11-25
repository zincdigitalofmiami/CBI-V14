# 📊 Baseline v1 Analysis & Next Steps
**Date:** November 24, 2025

---

## ✅ Data Health Check: PASSED

| Metric | Value | Status |
|--------|-------|--------|
| Total rows with target | 3,900 | ✅ Healthy |
| Date range | 2010-08-18 → 2025-10-24 | ✅ 15 years |
| NULL targets | 21 (last 21 days) | ✅ Expected |
| Avg 1-month return | +0.35% | ✅ Reasonable |
| Stddev | 6.9% | ✅ Normal |
| Range | -30.5% to +30.4% | ✅ Realistic |

**Conclusion: Data pipeline is working correctly.**

---

## ⚠️ Model Issue: Underpowered

### What Happened:
```
Early stopping, best iteration is:
[9] train's l1: 0.0469536  val's l1: 0.0692373
```

Model stopped at **iteration 9** out of 1000 because:
1. Only **9 features** - not enough signal
2. Only **250 val rows** - early stopping triggered too fast
3. Default settings - not tuned for this problem

### Current Features (9 total):
```
return_1d, return_5d, return_21d
ma_5, ma_21, ma_63
volatility_21d, rsi_14
close
```

**These are all single-instrument TA features. No cross-asset, no macro, no fundamentals.**

---

## 🔧 Fixes Needed

### 1. Expand Feature Set (Priority #1)

**Add these feature categories:**

| Category | Features | Source |
|----------|----------|--------|
| **Cross-asset** | ZS, ZM, CL, HO correlations/betas | Databento |
| **Crush margin** | `(ZM*11 + ZL*11) - ZS` | Calculated |
| **FX** | DXY, USDBRL, USDCNY levels & returns | Databento/FRED |
| **Macro** | VIX proxy, Fed Funds, yields, CPI | FRED |
| **Seasonality** | Month, day of week, harvest flags | Calendar |
| **More TA** | Bollinger bands, MACD, ATR | Calculated |
| **Volume** | Volume z-score, OBV | Databento |

**Target: 50-100 features minimum**

### 2. Improve Val Split

**Current:**
- Train: 3,214 rows (2010-2022)
- Val: 250 rows (2023)
- Test: 436 rows (2024-2025)

**Better options:**

**Option A: Larger Val Window**
```python
# Use 2 years for val instead of 1
CASE
    WHEN trade_date < DATE '2022-01-01' THEN 'train'
    WHEN trade_date < DATE '2024-01-01' THEN 'val'  # 2 years
    ELSE 'test'
END
```

**Option B: Time-Series CV (Recommended)**
```python
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5)
for train_idx, val_idx in tscv.split(X):
    # Train on expanding window
    # Validate on next chunk
```

### 3. Relax Early Stopping

**Current:**
```python
params = {
    'learning_rate': 0.05,
    'num_leaves': 31,
}
callbacks=[lgb.early_stopping(stopping_rounds=50)]
```

**Better:**
```python
params = {
    'learning_rate': 0.01,      # Slower learning
    'num_leaves': 63,           # More complexity
    'max_depth': 8,             # Allow deeper trees
    'min_data_in_leaf': 50,     # Prevent overfitting
    'feature_fraction': 0.8,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'lambda_l1': 0.1,           # L1 regularization
    'lambda_l2': 0.1,           # L2 regularization
}
callbacks=[
    lgb.early_stopping(stopping_rounds=100),  # More patience
    lgb.log_evaluation(period=50)
]
num_boost_round = 3000  # More trees
```

---

## 📋 Action Plan

### Phase 1: More Features (Next)
1. Add ZS, ZM, CL to Databento pull
2. Calculate crush margin
3. Add FRED macro (VIX proxy, rates)
4. Add calendar features
5. Expand TA set

### Phase 2: Better Training Setup
1. Implement TimeSeriesSplit CV
2. Lower learning rate, more trees
3. Increase early stopping patience
4. Add feature importance tracking

### Phase 3: Model Comparison
1. LightGBM with full features
2. XGBoost comparison
3. TFT (Temporal Fusion Transformer)
4. Ensemble

---

## 📊 Expected Improvement

| Stage | Features | Expected MAE | Direction Acc |
|-------|----------|--------------|---------------|
| Current (v1) | 9 | 6.16% | 49.3% |
| + Cross-asset | ~30 | 5.5% | 52% |
| + Macro/FX | ~50 | 5.0% | 54% |
| + Full feature set | ~100 | 4.5% | 56% |
| + Tuned hyperparams | ~100 | 4.0% | 58% |
| + Ensemble | ~100 | 3.5% | 60% |

**Target: MAE < 4%, Direction Accuracy > 58%**

---

## ✅ Summary

**The baseline worked.** It proved:
- ✅ Data pipeline BQ → Mac works
- ✅ Feature calculations work
- ✅ Regime stamping works
- ✅ Training infrastructure works

**Now we need:**
- More features (cross-asset, macro, crush)
- Better CV strategy
- Tuned hyperparameters

**This is exactly where we should be after v1.**

