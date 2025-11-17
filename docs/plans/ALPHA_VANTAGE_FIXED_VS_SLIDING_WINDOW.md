# Fixed Window vs Sliding Window Analytics - Decision Guide
**Date**: November 17, 2025  
**Purpose**: Determine which analytics endpoint to use (or neither)  
**Status**: ✅ **RECOMMENDATION: SLIDING WINDOW**

---

## Your Use Case Analysis

### Current Feature Requirements:

**Rolling Correlations** (Daily Features):
- `corr_zl_crude_7d` - 7-day rolling correlation
- `corr_zl_crude_30d` - 30-day rolling correlation
- `corr_zl_crude_90d` - 90-day rolling correlation
- `corr_zl_crude_180d` - 180-day rolling correlation
- `corr_zl_crude_365d` - 365-day rolling correlation
- **Same for**: palm, vix, dxy, corn, wheat
- **Total**: ~30 correlation features that **change daily**

**Rolling Volatility** (Daily Features):
- `vol_realized_30d` - 30-day rolling volatility
- `vol_realized_90d` - 90-day rolling volatility
- **These change daily**

**Key Requirement**: **Features must change daily** for forecasting model

---

## Fixed Window Analytics

### What It Provides:

**Single calculation over entire range:**
- One value for entire period (e.g., 1 year)
- Example: "SOYB variance over last year = 8.88e-05"
- Example: "SOYB-ES correlation over last year = 0.117"

### Test Results:

**Retrieved for SOYB & ES (1 year)**:
- ✅ VARIANCE: 8.88e-05 (SOYB), 0.000238 (ES)
- ✅ STDDEV: 0.0094 (SOYB), 0.0154 (ES)
- ✅ CORRELATION: 0.117 (SOYB-ES)
- ✅ MAX_DRAWDOWN: -5.7% (SOYB), -13.4% (ES)
- ✅ AUTOCORRELATION: 0.082 (SOYB), -0.024 (ES)

### Use Cases:

**✅ Good For:**
- **Validation/Backtesting**: Overall statistics for model validation
- **MAX_DRAWDOWN**: Useful feature (largest peak-to-trough)
- **AUTOCORRELATION**: Useful feature (you use this in `es_futures_predictor.py`)
- **One-time analysis**: Overall performance metrics

**❌ Bad For:**
- **Daily features**: Only gives one value, not daily values
- **Rolling windows**: Can't get 7d/30d/90d rolling values
- **Time-series features**: Doesn't change over time

---

## Sliding Window Analytics

### What It Provides:

**Running calculations over time:**
- Value for every date in the range
- Example: "SOYB variance on 2025-01-02 = X, on 2025-01-03 = Y, ..."
- Example: "SOYB-ES correlation on each date"

### Test Results:

**Retrieved for SOYB & ES (30-day window)**:
- ✅ RUNNING_VARIANCE: Value for every date
- ✅ RUNNING_STDDEV: Value for every date
- ✅ RUNNING_CORRELATION: Correlation matrix for every date

### Use Cases:

**✅ Perfect For:**
- **Daily features**: Values change daily (matches your needs)
- **Rolling windows**: Can specify window size (7, 30, 90, 180, 365)
- **Time-series features**: Values evolve over time
- **Multiple windows**: Can call multiple times for different window sizes

**❌ Limitations:**
- Requires multiple API calls for different window sizes (7d, 30d, 90d, etc.)
- More API calls than Fixed Window

---

## Comparison Matrix

| Feature | Fixed Window | Sliding Window | Your Need |
|---------|--------------|----------------|-----------|
| **Daily correlation values** | ❌ Single value | ✅ Daily values | ✅ **Need daily** |
| **Rolling 7d correlation** | ❌ No | ✅ Yes (window=7) | ✅ **Need this** |
| **Rolling 30d correlation** | ❌ No | ✅ Yes (window=30) | ✅ **Need this** |
| **Rolling 90d correlation** | ❌ No | ✅ Yes (window=90) | ✅ **Need this** |
| **Daily volatility** | ❌ Single value | ✅ Daily values | ✅ **Need daily** |
| **MAX_DRAWDOWN** | ✅ Yes | ❌ No | ⚠️ Could use |
| **AUTOCORRELATION** | ✅ Yes | ❌ No | ⚠️ Could use |
| **API calls needed** | 1 per symbol group | 1 per window size | - |

---

## Recommendation: **SLIDING WINDOW** ✅

### Why Sliding Window:

1. **Matches Your Requirements**
   - You need **daily features** that change over time
   - You need **rolling windows** (7d, 30d, 90d, 180d, 365d)
   - Sliding Window provides exactly this

2. **Replaces Manual Calculations**
   - Currently: Manual rolling correlations for each pair × each window
   - With Sliding Window: API call per window size gets all pairs

3. **Efficient**
   - 1 API call gets all symbol pairs for one window size
   - Example: `window_size=30` → gets all 30-day correlations in one call

### Implementation Strategy:

**For Correlations** (5 window sizes):
```python
# Get correlations for all symbol pairs, 30-day window
correlations_30d = analytics_sliding_window(
    symbols=['SOYB', 'ES', 'WTI', 'BRENT', 'CORN', 'WHEAT'],
    window_size=30,
    calculations=['CORRELATION']
)
# Returns: All pairs (SOYB-ES, SOYB-WTI, etc.) for every date

# Repeat for other windows: 7, 90, 180, 365
```

**Total API Calls**: 5 calls (one per window size) vs. 250+ manual calculations ✅

---

## When to Use Fixed Window

### ✅ **Use Fixed Window For:**

1. **MAX_DRAWDOWN Feature**
   - Useful for risk assessment
   - Can be calculated periodically (not daily)
   - Example: "What's the max drawdown over last year?"

2. **AUTOCORRELATION Feature**
   - You use this in `es_futures_predictor.py`
   - Can be calculated periodically
   - Example: "What's the autocorrelation over last year?"

3. **Validation Metrics**
   - Overall statistics for model validation
   - Not used as daily features
   - Example: "What's the overall variance over training period?"

### ⚠️ **Don't Use Fixed Window For:**

- Daily correlation features (need Sliding Window)
- Daily volatility features (need Sliding Window)
- Rolling window calculations (need Sliding Window)

---

## Hybrid Approach (Best Solution)

### Use Both:

**Sliding Window** (Primary):
- Daily correlation features (7d, 30d, 90d, 180d, 365d)
- Daily volatility features (30d, 90d)
- **5-6 API calls/day** for all rolling windows

**Fixed Window** (Secondary):
- MAX_DRAWDOWN (periodic calculation, e.g., weekly)
- AUTOCORRELATION (periodic calculation, e.g., weekly)
- **1-2 API calls/week** for validation metrics

---

## API Call Efficiency

### Current Approach (Manual):
- 250+ manual calculations
- Custom code maintenance
- Potential errors

### Sliding Window Only:
- **5 API calls** (one per window: 7, 30, 90, 180, 365)
- Gets all symbol pairs automatically
- Standardized calculations

### Sliding Window + Fixed Window:
- **5-6 API calls/day** (Sliding Window for daily features)
- **1-2 API calls/week** (Fixed Window for validation)
- **Total: ~35-40 API calls/week** ✅ Well within Plan75 limits

---

## Final Recommendation

### ✅ **USE SLIDING WINDOW** (Primary)

**For:**
- Daily correlation features (all window sizes)
- Daily volatility features
- All rolling window calculations

**API Calls**: 5-6 per day (one per window size)

### ✅ **USE FIXED WINDOW** (Secondary)

**For:**
- MAX_DRAWDOWN (weekly calculation)
- AUTOCORRELATION (weekly calculation)
- Validation metrics

**API Calls**: 1-2 per week

### ❌ **DON'T USE NEITHER**

Both provide value:
- **Sliding Window**: Essential for daily features
- **Fixed Window**: Useful for validation metrics

---

## Implementation Priority

### Phase 1: Sliding Window (High Priority)
1. Replace correlation calculations (7d, 30d, 90d, 180d, 365d)
2. Replace volatility calculations (30d, 90d)
3. **Impact**: Reduces 250+ manual calculations to 5-6 API calls

### Phase 2: Fixed Window (Low Priority)
1. Add MAX_DRAWDOWN feature (weekly calculation)
2. Add AUTOCORRELATION feature (weekly calculation)
3. **Impact**: Adds new capabilities, not replacing existing

---

## Summary

| Endpoint | Use? | Priority | API Calls | Value |
|----------|------|----------|-----------|-------|
| **Sliding Window** | ✅ **YES** | **HIGH** | 5-6/day | Replaces 250+ manual calculations |
| **Fixed Window** | ✅ **YES** | **LOW** | 1-2/week | Adds MAX_DRAWDOWN, AUTOCORRELATION |

**Recommendation**: **Use both, prioritize Sliding Window**

---

**Last Updated**: November 17, 2025  
**Status**: Sliding Window = Essential, Fixed Window = Nice to have

