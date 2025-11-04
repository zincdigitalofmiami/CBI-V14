# Why 3M Model Performed Better - Analysis

**Date:** November 4, 2025  
**Question:** Why did 3M model have better MAPE (0.69%) than others?

---

## ACTUAL MAPE VALUES

| Model | MAPE | Rank |
|-------|------|------|
| **6M** | **0.67%** | 🥇 Best |
| **3M** | **0.69%** | 🥈 Second |
| **1M** | **0.70%** | 🥉 Third |
| **1W** | **0.72%** | 4th |

**Note:** 6M is actually the best, but 3M is close second.

---

## WHY 3M (AND 6M) PERFORMED BETTER

### 1. Feature Selection (Fewer NULL Features)

**3M Model:**
- **268 features** (excludes 18 NULL columns)
- Excludes: 8 standard NULLs + 7 news NULLs + 1 trump NULL
- **More focused feature set** - only features with actual data

**1W Model:**
- **276 features** (excludes 8 NULL columns)
- Includes more features, some may have sparse data
- **More noise** from features with limited data

**6M Model:**
- **258 features** (excludes 28 NULL columns - most aggressive)
- Excludes: 8 standard + 7 news + 11 trump NULLs
- **Most focused** - only features with real data

**Impact:** Fewer features with sparse/NULL data = less noise = better predictions

### 2. Training Data Quality

**3M Training Data:**
- Excludes news columns (100% NULL for 3M timeframe)
- Excludes trump columns that don't exist in 3M window
- **Cleaner feature set** focused on actual available data

**1W/1M Training Data:**
- Includes some features with partial/sparse data
- More features but some may be noisy

### 3. Horizon-Specific Signal Strength

**3-Month Horizon:**
- Medium-term signals are more stable
- Less noise from daily/weekly volatility
- Better signal-to-noise ratio for 90-day predictions

**1-Week Horizon:**
- More affected by daily volatility
- Short-term noise harder to predict
- More unpredictable movements

### 4. Model Configuration

**All models have same config:**
- max_iterations=100
- early_stop=False
- learn_rate=0.1

**But 3M benefits from:**
- Better feature selection (fewer NULLs)
- Cleaner training data
- More stable prediction target (90 days vs 7 days)

---

## KEY INSIGHT

**3M performs better because:**
1. ✅ **Excludes more NULL features** (18 vs 8 for 1W)
2. ✅ **Cleaner feature set** - only features with actual data in 3M timeframe
3. ✅ **Medium-term horizon** - more stable signals, less noise
4. ✅ **Better signal-to-noise ratio** - 90-day predictions are more predictable than 7-day

**6M is even better (0.67%)** because it excludes the most NULL features (28), making it the most focused model.

---

## CONCLUSION

**3M is better because of:**
- **Feature selection** - Excludes 18 NULL columns vs 8 for 1W
- **Data quality** - Only uses features with actual data in 3M window
- **Horizon stability** - 90-day predictions have less noise than 7-day

**Best model is actually 6M (0.67%)** because it's the most aggressive at excluding NULL features (28 excluded).

