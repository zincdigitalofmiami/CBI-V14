# Alpha Vantage Historical Data Strategy
**Date**: November 16, 2025  
**Purpose**: Historical data collection options and limits  
**Status**: Analysis Complete

---

## Historical Data Availability

### ✅ **Available Historical Depth**
- **20+ years** of historical data (since 2000-01)
- Available for:
  - Daily, Weekly, Monthly time series
  - Intraday data (1min, 5min, 15min, 30min, 60min)
  - Commodities, Forex, Economic Indicators
  - Technical Indicators (calculated on historical data)

---

## Free Tier Limitations

### API Request Limits
- **25 API requests per day** (not 500 as previously estimated)
- This is the **critical constraint** for historical data collection

### What This Means for Historical Collection
- **25 requests/day** = ~750 requests/month
- If you need 20 years of daily data for 10 symbols:
  - Daily data: 1 request per symbol = 10 requests
  - **Can collect ~2-3 symbols per day** on free tier
  - **20-year backfill would take months** at this rate

---

## Historical Data Collection Options

### Option 1: **Daily/Weekly/Monthly Time Series** (Easiest)

**API Endpoint**: `TIME_SERIES_DAILY`, `TIME_SERIES_WEEKLY`, `TIME_SERIES_MONTHLY`

**Parameters**:
- `outputsize=compact` → Returns **latest 100 data points** (default)
- `outputsize=full` → Returns **full historical series** (20+ years)

**Example**:
```
https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&outputsize=full&apikey=demo
```

**Strategy**:
- ✅ **One request per symbol** gets full 20+ year history
- ✅ **Most efficient** for historical collection
- ✅ **Free tier sufficient** for ~25 symbols/day

**Use Case**: Perfect for commodity prices, stock prices, forex rates

---

### Option 2: **Intraday Historical Data** (More Complex)

**API Endpoint**: `TIME_SERIES_INTRADAY`

**Parameters**:
- `outputsize=compact` → Returns **latest 100 data points**
- `outputsize=full` → Returns **trailing 30 days** (if no month specified)
- `month=YYYY-MM` → Returns **full month** of intraday data

**Example**:
```
https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=IBM&interval=5min&month=2009-01&outputsize=full&apikey=demo
```

**Strategy for Full Historical**:
- ❌ **Requires multiple requests** (one per month)
- ❌ **20 years × 12 months = 240 requests per symbol**
- ❌ **Free tier (25/day) = ~9 days per symbol** for full backfill
- ⚠️ **Not practical on free tier** for multiple symbols

**Use Case**: Only if you need intraday granularity (probably not needed for your use case)

---

### Option 3: **Technical Indicators** (Efficient)

**API Endpoints**: `SMA`, `EMA`, `RSI`, `MACD`, etc. (50+ indicators)

**Parameters**:
- `interval=daily|weekly|monthly` → Uses underlying time series
- Historical depth depends on underlying data (20+ years)

**Strategy**:
- ✅ **One request per indicator per symbol** gets full history
- ✅ **Calculated on historical data** automatically
- ✅ **Free tier sufficient** for core indicators

**Example**:
```
https://www.alphavantage.co/query?function=RSI&symbol=IBM&interval=daily&time_period=14&series_type=close&apikey=demo
```

**Use Case**: Perfect for replacing custom indicator calculations

---

### Option 4: **Commodities Historical** (Efficient)

**API Endpoints**: `WTI`, `BRENT`, `NATURAL_GAS`, `WHEAT`, `CORN`, etc.

**Parameters**:
- Similar to daily time series
- `outputsize=full` → Full historical series

**Strategy**:
- ✅ **One request per commodity** gets full history
- ✅ **Free tier sufficient** for ~25 commodities/day

---

## Recommended Historical Collection Strategy

### Phase 1: **Daily/Weekly/Monthly Data** (Free Tier - Efficient)

**Priority Symbols** (Commodities):
1. ZL (Soybean Oil) - Daily
2. ZS (Soybeans) - Daily
3. ZC (Corn) - Daily
4. ZW (Wheat) - Daily
5. CL (Crude Oil WTI) - Daily
6. NG (Natural Gas) - Daily
7. GC (Gold) - Daily
8. Brent Crude - Daily (new)
9. Sugar - Daily (new)
10. Coffee - Daily (new)

**Collection Plan**:
- **10 symbols × 1 request each = 10 requests**
- **Remaining 15 requests** for technical indicators
- **Can collect full 20+ year history in 1 day** ✅

**Technical Indicators** (15 requests available):
- RSI, MACD, SMA, EMA, ADX, AROON, BBANDS, etc.
- **1 request per indicator per symbol**
- **Can get 1-2 indicators for 10 symbols** per day

**Total Time**: **1-2 days** to collect full historical dataset ✅

---

### Phase 2: **Technical Indicators Expansion** (Free Tier - Staggered)

**Strategy**: Collect indicators over multiple days
- Day 1: RSI for all 10 symbols (10 requests)
- Day 2: MACD for all 10 symbols (10 requests)
- Day 3: SMA for all 10 symbols (10 requests)
- ...continue for 50+ indicators

**Total Time**: **5-10 days** to collect all 50+ indicators for 10 symbols

---

## Premium Tier Options (If Needed)

### Premium Plans Available:
- **Plan30**: 30 requests/minute
- **Plan75**: 75 requests/minute
- **Plan150**: 150 requests/minute
- **Plan300**: 300 requests/minute
- **Plan600**: 600 requests/minute
- **Plan1200**: 1,200 requests/minute

### When Premium Makes Sense:

1. **Faster Historical Collection**
   - Free tier: 25 requests/day = ~750/month
   - Plan30: 30 requests/minute = **43,200 requests/day** (if used continuously)
   - **Can backfill 20 years of intraday data in hours instead of months**

2. **Real-Time Data**
   - Free tier: Delayed data only
   - Premium: Real-time or 15-minute delayed (regulatory requirement)

3. **Higher Frequency Updates**
   - Free tier: Daily collection sufficient
   - Premium: Hourly/intraday updates possible

4. **Bulk Operations**
   - Free tier: Sequential requests
   - Premium: Parallel requests possible

---

## Cost-Benefit Analysis

### Free Tier Assessment:

**✅ Sufficient For:**
- Daily/Weekly/Monthly historical collection (one-time backfill)
- Technical indicators collection (staggered over days)
- Daily updates (25 symbols/day is plenty)

**❌ Insufficient For:**
- Intraday historical backfill (would take months)
- Real-time data needs
- High-frequency updates
- Large-scale parallel operations

### Premium Tier Assessment:

**Cost**: Unknown (need to contact Alpha Vantage for pricing)

**Benefits**:
- **100x+ faster** historical collection
- Real-time data access
- Higher rate limits
- Premium endpoints (VWAP, bulk quotes)

**ROI**: Only worth it if:
- You need intraday historical data
- You need real-time updates
- You're doing large-scale backfills frequently

---

## Recommended Approach

### ✅ **Start with Free Tier**

1. **Collect Daily Historical Data** (Day 1)
   - 10 commodities × 1 request = 10 requests
   - Get full 20+ year history ✅

2. **Collect Technical Indicators** (Days 2-10)
   - Stagger over multiple days
   - 10-15 requests per day
   - Build up indicator library gradually

3. **Daily Updates** (Ongoing)
   - 10 symbols × 1 request = 10 requests/day
   - 15 requests remaining for new indicators or symbols

### ⚠️ **Upgrade to Premium If:**

- Need intraday historical data (not likely for your use case)
- Need real-time data (not critical for forecasting)
- Need faster backfill (one-time cost, might be worth it)
- Pricing is reasonable (<$50/month)

---

## Implementation Plan

### Step 1: Test Historical Collection (Free Tier)
```python
# Test single symbol with full history
url = 'https://www.alphavantage.co/query'
params = {
    'function': 'TIME_SERIES_DAILY',
    'symbol': 'ZL',  # Soybean Oil futures symbol
    'outputsize': 'full',  # Get full 20+ year history
    'apikey': YOUR_API_KEY
}
```

### Step 2: Collect Core Commodities (Day 1)
- ZL, ZS, ZC, ZW, CL, NG, GC, Brent, Sugar, Coffee
- 10 requests total
- Full historical data collected ✅

### Step 3: Collect Technical Indicators (Days 2-10)
- Prioritize: RSI, MACD, SMA, EMA, ADX, AROON, BBANDS
- 10 symbols × 1 indicator = 10 requests/day
- Collect over multiple days

### Step 4: Evaluate Premium Need
- If free tier sufficient → Continue with free
- If need faster collection → Consider premium for one-time backfill
- If need real-time → Consider premium for ongoing

---

## Summary

### Historical Data Options:

| Data Type | Free Tier Strategy | Time Required | Premium Needed? |
|-----------|-------------------|---------------|-----------------|
| Daily/Weekly/Monthly | 1 request per symbol | 1-2 days | ❌ No |
| Technical Indicators | Staggered collection | 5-10 days | ❌ No |
| Intraday Historical | Multiple requests/month | Months | ✅ Yes |
| Real-time Data | Not available | N/A | ✅ Yes |

### Recommendation:

**✅ Start with Free Tier** - It's sufficient for:
- Daily historical collection (20+ years)
- Technical indicators (staggered collection)
- Daily updates

**Consider Premium** only if:
- Need intraday historical data
- Need real-time data
- Premium pricing is reasonable for one-time backfill speed

---

## Next Steps

1. **Test free tier** with single symbol full history
2. **Collect core commodities** (10 symbols, 1 day)
3. **Collect technical indicators** (staggered over days)
4. **Evaluate premium** based on actual needs and pricing

---

**Last Updated**: November 16, 2025  
**Status**: Ready for implementation



