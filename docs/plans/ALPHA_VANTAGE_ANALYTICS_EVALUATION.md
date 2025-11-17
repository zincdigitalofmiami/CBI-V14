# Alpha Vantage Analytics Features - Evaluation
**Date**: November 17, 2025  
**Purpose**: Evaluate Analytics (Fixed & Sliding Window) endpoints  
**Status**: ✅ **HIGH VALUE** - Can Replace Manual Calculations

---

## Summary

**✅ ZL Futures**: Not available in Alpha Vantage (use Yahoo Finance)  
**✅ Analytics Sliding Window**: **EXCELLENT** - Can automate correlation/variance calculations  
**✅ Analytics Fixed Window**: **EXCELLENT** - Can automate statistical metrics

---

## 1. ZL Futures Status

### ❌ **Not Available**
- Alpha Vantage doesn't recognize "ZL" as a valid symbol
- Symbol search returns no matches for "ZL futures"
- **Recommendation**: Continue using Yahoo Finance (`ZL=F`) for ZL futures prices

### ✅ **Alternative Available**
- **SOYB** (Teucrium Soybean ETF) works perfectly
- Tracks soybean prices closely
- Can be used as proxy for soybean oil analysis
- All technical indicators work with SOYB

---

## 2. Analytics Sliding Window - **HIGH VALUE**

### What It Provides:

**Running Calculations Over Sliding Windows:**
- **VARIANCE**: Moving variance over time (e.g., 30-day rolling variance)
- **STDDEV**: Moving standard deviation (volatility)
- **CORRELATION**: Correlation matrices between symbols over sliding windows
- **MEAN/MEDIAN**: Moving averages
- **CUMULATIVE_RETURN**: Total return over window

### Test Results:

**Successfully Retrieved:**
- ✅ Running variance for SOYB (30-day window)
- ✅ Running stddev for SOYB (30-day window)
- ✅ Correlation matrix between SOYB and ES
- ✅ Date range: Nov 18, 2024 to Nov 14, 2025

**Example Output Structure:**
```json
{
  "VARIANCE": {
    "RUNNING_VARIANCE": {
      "SOYB": {
        "2025-01-02": 8.41e-05,
        "2025-01-03": 9.65e-05,
        ...
      }
    }
  },
  "CORRELATION": {
    "RUNNING_CORRELATION": {
      "SOYB-ES": {
        "2025-01-02": 0.45,
        ...
      }
    }
  }
}
```

---

## 3. Analytics Fixed Window - **HIGH VALUE**

### What It Provides:

**Single Calculation Over Entire Range:**
- **VARIANCE**: Population variance
- **STDDEV**: Population standard deviation
- **CUMULATIVE_RETURN**: Total return over period
- **MEAN/MEDIAN**: Average values

### Test Results:

**Successfully Retrieved for SOYB (1 year):**
- ✅ **VARIANCE**: 8.88e-05
- ✅ **STDDEV**: 0.0094 (0.94%)
- ✅ **CUMULATIVE_RETURN**: 0.0815 (8.15% return over 1 year)

---

## 4. Current Manual Calculations (What You're Doing Now)

### From `feature_calculations.py`:

**Volatility Features** (Manual):
```python
# Realized volatility (annualized)
df[f'vol_realized_{period}d'] = df['returns'].rolling(window=period).std() * np.sqrt(252)

# Volatility of volatility
df['vol_of_vol_30d'] = df['vol_realized_30d'].rolling(window=30).std()
```

**Correlation Features** (Manual):
- `corr_zl_crude_7d/30d/90d/180d/365d`
- `corr_zl_palm_7d/30d/90d/180d/365d`
- `corr_zl_vix_7d/30d/90d/180d/365d`
- Multiple correlation pairs calculated manually

---

## 5. How Analytics Can Replace Manual Calculations

### ✅ **Replace Volatility Calculations**

**Current (Manual)**:
```python
df['vol_realized_30d'] = df['returns'].rolling(30).std() * np.sqrt(252)
```

**With Alpha Vantage**:
```python
# One API call gets running stddev for 30-day window
analytics = alpha_vantage.analytics_sliding_window(
    symbols=['SOYB', 'ES'],
    window_size=30,
    calculations=['STDDEV'],
    interval='DAILY'
)
# Returns stddev for every date automatically
```

**Benefits**:
- ✅ Standardized calculations (industry standard)
- ✅ No manual coding
- ✅ Handles multiple symbols simultaneously
- ✅ Can annualize automatically

### ✅ **Replace Correlation Calculations**

**Current (Manual)**:
```python
# Calculate correlations manually for each pair
corr_zl_crude_7d = df['zl_price'].rolling(7).corr(df['crude_price'])
corr_zl_crude_30d = df['zl_price'].rolling(30).corr(df['crude_price'])
# ... repeat for all pairs
```

**With Alpha Vantage**:
```python
# One API call gets correlation matrix for all symbol pairs
analytics = alpha_vantage.analytics_sliding_window(
    symbols=['SOYB', 'ES', 'WTI', 'CORN'],
    window_size=30,
    calculations=['CORRELATION'],
    interval='DAILY'
)
# Returns correlation matrix: SOYB-ES, SOYB-WTI, SOYB-CORN, ES-WTI, etc.
```

**Benefits**:
- ✅ **One API call** gets all correlation pairs
- ✅ No manual pairwise calculations
- ✅ Supports multiple correlation methods (PEARSON, KENDALL, SPEARMAN)
- ✅ Can handle up to 50 symbols (premium tier)

---

## 6. Available Analytics Metrics

### Fixed Window Metrics:
- `MEAN` - Mean of returns
- `MEDIAN` - Median of returns
- `CUMULATIVE_RETURN` - Total return
- `VARIANCE` - Population variance
- `STDDEV` - Population standard deviation
- `COVARIANCE` - Covariance matrix
- `CORRELATION` - Correlation matrix

### Sliding Window Metrics:
- `RUNNING_VARIANCE` - Moving variance over time
- `RUNNING_STDDEV` - Moving standard deviation
- `RUNNING_CORRELATION` - Moving correlation matrix
- `RUNNING_COVARIANCE` - Moving covariance matrix

### Advanced Options:
- **Annualization**: `VARIANCE(annualized=True)`, `STDDEV(annualized=True)`
- **Correlation Methods**: `CORRELATION(method=PEARSON|KENDALL|SPEARMAN)`
- **Window Sizes**: Any integer ≥ 10 (recommended: 30+ for significance)

---

## 7. Use Cases for Your Forecasting Model

### Current Features That Could Be Replaced:

1. **Volatility Features** (28 features currently):
   - `vol_realized_30d`, `vol_realized_90d`
   - `vol_of_vol_30d`
   - `vol_percentile_30d`, `vol_percentile_90d`
   - **→ Replace with Analytics Sliding Window**

2. **Correlation Features** (28 features currently):
   - `corr_zl_crude_7d/30d/90d/180d/365d`
   - `corr_zl_palm_7d/30d/90d/180d/365d`
   - `corr_zl_vix_7d/30d/90d/180d/365d`
   - **→ Replace with Analytics Sliding Window**

3. **Return Features**:
   - Cumulative returns over periods
   - **→ Replace with Analytics Fixed Window**

---

## 8. API Efficiency Comparison

### Current Approach (Manual):

**For 10 symbols × 5 correlation pairs × 5 timeframes:**
- 250 manual calculations
- Custom code maintenance
- Potential calculation errors
- Time-consuming

### Alpha Vantage Approach:

**For 10 symbols × 1 API call:**
- 1 API call gets all correlation pairs
- Up to 50 symbols per call (premium)
- Standardized calculations
- **Much more efficient**

**Example**:
```python
# Get correlations for all pairs in one call
analytics = alpha_vantage.analytics_sliding_window(
    symbols=['SOYB', 'ES', 'WTI', 'BRENT', 'CORN', 'WHEAT', 'GC', 'NG', 'CT', 'SUGAR'],
    window_size=30,
    calculations=['CORRELATION'],
    interval='DAILY'
)
# Returns: 45 correlation pairs (10 choose 2) automatically!
```

---

## 9. Implementation Strategy

### Phase 1: Replace Correlation Calculations

**Current**: Manual pairwise correlations
**Replace With**: Analytics Sliding Window

**Benefits**:
- ✅ Reduces code complexity
- ✅ Standardized calculations
- ✅ Handles multiple symbols efficiently

### Phase 2: Replace Volatility Calculations

**Current**: Manual rolling stddev
**Replace With**: Analytics Sliding Window

**Benefits**:
- ✅ Annualization built-in
- ✅ Consistent with industry standards
- ✅ Less code to maintain

### Phase 3: Add New Analytics

**New Features**:
- Covariance matrices
- Multiple correlation methods (KENDALL, SPEARMAN)
- Running mean/median
- Cumulative returns

---

## 10. Cost-Benefit Analysis

### API Calls Needed:

**Daily Collection**:
- Analytics Sliding Window: 1 call per symbol group (up to 50 symbols)
- For 10 symbols: **1 API call** gets all correlations
- For volatility: **1 API call** gets all stddevs

**Total**: **2-3 API calls/day** for analytics (vs. 250+ manual calculations)

### Premium Tier Benefits:

- **Free tier**: 1 metric per call, up to 5 symbols
- **Premium tier**: Multiple metrics per call, up to 50 symbols

**With Premium Plan75**:
- ✅ Get all metrics in one call
- ✅ Handle all 10+ symbols in one call
- ✅ Much more efficient

---

## 11. Limitations & Considerations

### Limitations:

1. **ZL Futures Not Available**
   - Must use Yahoo Finance for ZL
   - SOYB works as proxy

2. **Symbol Format**
   - Must use Alpha Vantage symbol format
   - SOYB (not ZL), ES (not ES=F)

3. **Window Size**
   - Minimum: 10 data points
   - Recommended: 30+ for statistical significance

4. **Data Delay**
   - Latest data: Nov 14 (2-3 days old)
   - Updates after market close

### Considerations:

1. **Hybrid Approach**
   - Use Alpha Vantage for analytics (correlations, volatility)
   - Use Yahoo Finance for ZL futures prices
   - Best of both worlds

2. **Data Consistency**
   - Alpha Vantage calculations are standardized
   - May differ slightly from manual calculations
   - Need to validate before full replacement

---

## 12. Recommendation

### ✅ **USE ANALYTICS FEATURES** - High ROI

**Priority Order**:

1. **Correlation Calculations** (Highest ROI)
   - Currently: 250+ manual calculations
   - With Analytics: 1-2 API calls
   - **Massive code reduction**

2. **Volatility Calculations** (High ROI)
   - Currently: Manual rolling stddev
   - With Analytics: 1 API call
   - **Standardized & annualized**

3. **New Analytics** (Medium ROI)
   - Covariance matrices
   - Multiple correlation methods
   - **Adds new capabilities**

### Implementation:

**Start Small**:
1. Test Analytics Sliding Window for correlations
2. Compare results with manual calculations
3. Validate accuracy
4. Gradually replace manual code

**Full Replacement**:
- Once validated, replace all manual correlation/volatility calculations
- Keep Yahoo Finance for ZL futures prices
- Use Alpha Vantage for analytics

---

## 13. Example Implementation

### Current Code (Manual):
```python
# Calculate correlations manually
for symbol_pair in [('zl', 'crude'), ('zl', 'palm'), ...]:
    for window in [7, 30, 90, 180, 365]:
        df[f'corr_{symbol_pair[0]}_{symbol_pair[1]}_{window}d'] = \
            df[symbol_pair[0]].rolling(window).corr(df[symbol_pair[1]])
```

### New Code (Alpha Vantage):
```python
from src.utils.keychain_manager import get_api_key
import requests

def get_correlations_alpha_vantage(symbols, window_size=30):
    """Get correlation matrix from Alpha Vantage"""
    api_key = get_api_key('ALPHA_VANTAGE_API_KEY')
    
    url = 'https://www.alphavantage.co/query'
    params = {
        'function': 'ANALYTICS_SLIDING_WINDOW',
        'symbols': ','.join(symbols),
        'range': '1year',
        'interval': 'DAILY',
        'window_size': window_size,
        'calculations': 'CORRELATION',
        'ohlc': 'close',
        'apikey': api_key
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    # Extract correlation matrix
    correlations = data['payload']['RETURNS_CALCULATIONS']['CORRELATION']['RUNNING_CORRELATION']
    
    return correlations

# Usage: Get all correlations in one call
symbols = ['SOYB', 'ES', 'WTI', 'BRENT', 'CORN']
correlations = get_correlations_alpha_vantage(symbols, window_size=30)
# Returns: SOYB-ES, SOYB-WTI, SOYB-BRENT, SOYB-CORN, ES-WTI, etc.
```

---

## Summary

### ✅ **ZL Futures**: Not available (use Yahoo Finance)

### ✅ **Analytics Sliding Window**: **EXCELLENT VALUE**
- Can replace 250+ manual correlation calculations
- Can replace volatility calculations
- Standardized, industry-standard metrics
- **Highly recommended**

### ✅ **Analytics Fixed Window**: **EXCELLENT VALUE**
- Cumulative returns
- Population statistics
- **Useful for validation**

### Next Steps:

1. ✅ **Test Analytics** with your symbol list
2. ✅ **Validate** results vs. manual calculations
3. ✅ **Implement** correlation replacement first
4. ✅ **Gradually replace** volatility calculations
5. ✅ **Keep Yahoo Finance** for ZL futures prices

---

**Last Updated**: November 17, 2025  
**Status**: Ready for implementation - High ROI opportunity

