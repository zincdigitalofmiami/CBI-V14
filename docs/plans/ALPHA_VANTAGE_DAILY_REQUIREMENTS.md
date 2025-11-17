# Alpha Vantage Daily Requirements Analysis
**Date**: November 16, 2025  
**Purpose**: Calculate API requirements for daily technical indicators + ES futures  
**Status**: Premium Tier Required

---

## Your Requirements

### Daily Collection Needed:
1. **All technical indicators** (50+) for each symbol
2. **Price data** for each symbol
3. **ES futures contract** (S&P 500 futures) - hidden page
4. **Daily updates** (not one-time backfill)

---

## Current Symbol List

Based on codebase analysis:

### Core Commodities (10 symbols):
1. ZL (Soybean Oil)
2. ZS (Soybeans)
3. ZM (Soybean Meal)
4. ZC (Corn)
5. ZW (Wheat)
6. CL (Crude Oil WTI)
7. NG (Natural Gas)
8. GC (Gold)
9. CT (Cotton)
10. Brent Crude (new)

### Additional (1 symbol):
11. **ES (S&P 500 Futures)** - Hidden page requirement

**Total: 11 symbols**

---

## API Request Calculation

### Daily Requirements:

#### Option 1: Separate Price + Indicators (Current Approach)
- **Price data**: 11 symbols × 1 request = **11 requests**
- **Technical indicators**: 11 symbols × 50 indicators = **550 requests**
- **Total: 561 requests/day** ❌

#### Option 2: Indicators Include Price Data (Alpha Vantage)
- **Technical indicators**: 11 symbols × 50 indicators = **550 requests**
- (Price data included in indicator response)
- **Total: 550 requests/day** ❌

**Both approaches exceed free tier (25/day) by 22x**

---

## Free Tier Assessment

### Free Tier: 25 requests/day
- ❌ **Insufficient** for your requirements
- Would take **22 days** to collect one day's worth of data
- **Not viable** for daily updates

---

## Premium Tier Options

### Available Plans:
| Plan | Requests/Minute | Requests/Day* | Cost |
|------|----------------|----------------|------|
| Free | 25/day | 25 | Free |
| Plan30 | 30/min | 43,200 | Unknown |
| Plan75 | 75/min | 108,000 | Unknown |
| Plan150 | 150/min | 216,000 | Unknown |
| Plan300 | 300/min | 432,000 | Unknown |
| Plan600 | 600/min | 864,000 | Unknown |
| Plan1200 | 1,200/min | 1,728,000 | Unknown |

*If used continuously (theoretical maximum)

### Your Actual Needs:
- **550 requests/day** for daily updates
- **Spread over 24 hours** = ~23 requests/hour = **0.38 requests/minute**

**Minimum Required: Plan30 (30 requests/minute)** ✅

---

## Optimization Strategies

### Strategy 1: Batch Collection (Recommended)
**Collect all indicators for one symbol at once, then move to next**

- Hour 1: ZL (50 indicators) = 50 requests
- Hour 2: ZS (50 indicators) = 50 requests
- ...continue for 11 symbols
- **Total time: 11 hours** (well within 24-hour window)

**Benefit**: Spreads load, avoids rate limits

### Strategy 2: Priority Indicators
**Collect only high-value indicators daily, others weekly**

- **Daily (20 indicators)**: RSI, MACD, SMA, EMA, ADX, AROON, BBANDS, etc.
- **Weekly (30 indicators)**: Less critical indicators
- **Daily requests**: 11 symbols × 20 indicators = **220 requests/day**
- **Weekly requests**: 11 symbols × 30 indicators = **330 requests/week**

**Benefit**: Reduces daily load, still maintains core indicators

### Strategy 3: Symbol Prioritization
**Core symbols daily, others less frequently**

- **Daily (5 symbols)**: ZL, ZS, ES, CL, GC = 5 × 50 = 250 requests/day
- **Every 2 days (3 symbols)**: ZM, ZC, ZW = 3 × 50 = 150 requests/2 days
- **Weekly (3 symbols)**: NG, CT, Brent = 3 × 50 = 150 requests/week

**Benefit**: Focuses on most critical symbols

---

## Recommended Approach

### ✅ **Hybrid Strategy** (Best Balance)

**Daily Collection (220 requests/day)**:
- **11 symbols** × **20 core indicators** = 220 requests
- Core indicators: RSI, MACD, SMA, EMA, ADX, AROON, BBANDS, STOCH, CCI, MOM, ROC, OBV, ATR, NATR, WILLR, MFI, TRIX, ULTOSC, DX, SAR

**Weekly Collection (330 requests/week)**:
- **11 symbols** × **30 additional indicators** = 330 requests
- Additional indicators: WMA, DEMA, TEMA, TRIMA, KAMA, MAMA, VWAP, MACDEXT, STOCHF, STOCHRSI, etc.

**Benefits**:
- ✅ Maintains core indicators daily
- ✅ Reduces daily load to **220 requests/day**
- ✅ Still collects all 50+ indicators weekly
- ✅ Requires **Plan30** minimum (30/min = sufficient)

---

## Implementation Plan

### Phase 1: Setup Premium Account
1. Contact Alpha Vantage for **Plan30 pricing**
2. Evaluate if Plan75 needed (if want faster collection)
3. Set up API key in Keychain

### Phase 2: Daily Collection Script
```python
# Daily core indicators (20 per symbol)
DAILY_INDICATORS = [
    'RSI', 'MACD', 'SMA', 'EMA', 'ADX', 'AROON', 
    'BBANDS', 'STOCH', 'CCI', 'MOM', 'ROC', 'OBV',
    'ATR', 'NATR', 'WILLR', 'MFI', 'TRIX', 'ULTOSC', 'DX', 'SAR'
]

SYMBOLS = [
    'ZL', 'ZS', 'ZM', 'ZC', 'ZW', 'CL', 'NG', 'GC', 'CT', 'BRENT', 'ES'
]

# 11 symbols × 20 indicators = 220 requests/day
```

### Phase 3: Weekly Collection Script
```python
# Weekly additional indicators (30 per symbol)
WEEKLY_INDICATORS = [
    'WMA', 'DEMA', 'TEMA', 'TRIMA', 'KAMA', 'MAMA',
    'VWAP', 'MACDEXT', 'STOCHF', 'STOCHRSI', ...
    # ... 30 total
]

# 11 symbols × 30 indicators = 330 requests/week
```

### Phase 4: ES Futures Special Handling
- ES futures symbol: `ES` or `ES=F` (verify Alpha Vantage symbol)
- Collect same indicators as other symbols
- Store in separate table for hidden page
- Same collection schedule (daily core, weekly full)

---

## Cost-Benefit Analysis

### Premium Tier Cost:
- **Unknown** - Need to contact Alpha Vantage
- Estimate: $50-200/month for Plan30-Plan75

### Benefits:
- ✅ **All 50+ technical indicators** available
- ✅ **Daily updates** for core indicators
- ✅ **Standardized calculations** (matches TradingView)
- ✅ **Reduced code maintenance** (no custom indicator code)
- ✅ **ES futures support** (hidden page requirement)

### ROI:
- **Time saved**: No custom indicator code maintenance
- **Accuracy**: Industry-standard calculations
- **Scalability**: Easy to add new indicators
- **Reliability**: Official API vs. custom calculations

---

## Alternative: Keep Custom Indicators?

### Current Approach:
- Custom calculations in `scripts/features/feature_calculations.py`
- ~10-15 indicators calculated locally
- **No API costs**
- **But**: Limited indicators, maintenance burden

### Alpha Vantage Approach:
- 50+ indicators via API
- Standardized calculations
- **Premium cost** (~$50-200/month)
- **But**: More indicators, less maintenance

### Recommendation:
**✅ Use Alpha Vantage Premium** - The value of 50+ standardized indicators outweighs the cost, especially for production forecasting system.

---

## Next Steps

1. **Contact Alpha Vantage** for Plan30 pricing
2. **Verify ES futures symbol** in Alpha Vantage (ES, ES=F, or other?)
3. **Test API** with free tier first (collect 1 symbol × 20 indicators = 20 requests)
4. **Implement daily collection** script (220 requests/day)
5. **Implement weekly collection** script (330 requests/week)
6. **Set up ES futures** special handling for hidden page

---

## Summary

### Requirements:
- ✅ **11 symbols** (10 commodities + ES futures)
- ✅ **50+ technical indicators** per symbol
- ✅ **Daily updates**

### Solution:
- ❌ **Free tier insufficient** (25/day vs. 550/day needed)
- ✅ **Premium Plan30 minimum** (30/min = sufficient for 220/day)
- ✅ **Hybrid strategy**: 20 core indicators daily, 30 additional weekly

### Cost:
- **Unknown** - Need Alpha Vantage pricing
- **Estimate**: $50-200/month

### Recommendation:
**✅ Subscribe to Premium Plan30** (or Plan75 if want faster collection)

---

**Last Updated**: November 16, 2025  
**Status**: Premium tier required - Awaiting pricing information



