# Alpha Vantage API - Comprehensive Evaluation for CBI-V14
**Date**: November 16, 2025  
**Purpose**: Evaluate Alpha Vantage subscription value across all data categories  
**Status**: Analysis Complete - Ready for Decision

---

## Executive Summary

Alpha Vantage offers **8 major data categories** with **100+ endpoints**. This evaluation compares Alpha Vantage offerings against current CBI-V14 data sources to identify consolidation opportunities and gaps.

**Key Finding**: Alpha Vantage can potentially **consolidate 4-5 separate data sources** and add **new capabilities** in sentiment, fundamental analysis, and technical indicators.

---

## Current CBI-V14 Data Sources (Baseline)

### ✅ Currently Integrated Sources

1. **Yahoo Finance** (`yfinance`) - Stock/commodity prices, futures
2. **FRED API** - Economic indicators (30+ series)
3. **EIA API** - Biofuel production, RIN data
4. **CFTC** - Commitment of Traders (COT) positioning
5. **USDA** - Agricultural reports, export sales
6. **NOAA** - Weather data
7. **ScrapeCreators** - Social media sentiment (Truth Social, Facebook)
8. **NewsAPI** - News sentiment (with Alpha Vantage as fallback)

### ⚠️ Partially Integrated

- **TradingEconomics** - Market prices (env vars)
- **Polygon.io** - Market data (env vars)
- **Alpha Vantage** - Currently only used as fallback for news sentiment

---

## Alpha Vantage Offerings vs. Current Sources

### 1. **Core Stock APIs** (Time Series Data)

**Alpha Vantage Provides:**
- Intraday data (1min, 5min, 15min, 30min, 60min)
- Daily, Weekly, Monthly (20+ years history)
- Split/dividend adjusted options
- Extended hours (pre-market/post-market)
- Quote endpoints (real-time bulk quotes - premium)

**Current Source:** Yahoo Finance (`yfinance`)

**Comparison:**
| Feature | Alpha Vantage | Yahoo Finance (Current) |
|--------|---------------|-------------------------|
| Historical depth | 20+ years | 20+ years ✅ |
| Intraday intervals | 1min, 5min, 15min, 30min, 60min | Limited (1min, 5min) |
| Extended hours | ✅ Yes (4am-8pm ET) | ⚠️ Limited |
| Real-time quotes | ✅ Premium tier | ❌ Delayed |
| Rate limits | Premium: Higher limits | Free: Rate limited |
| Data quality | ✅ Official API | ⚠️ Unofficial library |

**Verdict**: **UPGRADE OPPORTUNITY** - Alpha Vantage offers better intraday granularity and extended hours. Premium tier provides real-time data vs. Yahoo's delayed data.

---

### 2. **Options Data APIs**

**Alpha Vantage Provides:**
- Real-time options data (premium)
- Historical options data
- Options chains

**Current Source:** ❌ **NOT COLLECTED**

**Verdict**: **NEW CAPABILITY** - Options data could provide volatility signals and hedging cost indicators for commodity futures.

---

### 3. **Alpha Intelligence™** (News & Sentiment)

**Alpha Vantage Provides:**
- News & Sentiments API
- Earnings Call Transcripts
- Top Gainers & Losers
- Insider Transactions
- Analytics (Fixed Window & Sliding Window)

**Current Sources:**
- ScrapeCreators (Truth Social, Facebook)
- NewsAPI (with Alpha Vantage as fallback)
- Manual scraping

**Comparison:**
| Feature | Alpha Vantage | Current Sources |
|--------|---------------|-----------------|
| News sentiment | ✅ Structured API | ⚠️ Multiple sources |
| Earnings transcripts | ✅ Available | ❌ Not collected |
| Insider transactions | ✅ Available | ❌ Not collected |
| Top gainers/losers | ✅ Available | ❌ Not collected |
| Sentiment scoring | ✅ Built-in | ⚠️ Custom processing |

**Verdict**: **CONSOLIDATION OPPORTUNITY** - Alpha Vantage can replace NewsAPI and add earnings/insider data. Keep ScrapeCreators for Truth Social (unique source).

---

### 4. **Fundamental Data**

**Alpha Vantage Provides:**
- Company Overview
- ETF Profile & Holdings
- Corporate Actions (Dividends, Splits)
- Income Statement, Balance Sheet, Cash Flow
- Shares Outstanding
- Earnings History & Estimates
- Listing & Delisting Status
- Earnings Calendar
- IPO Calendar

**Current Source:** ❌ **NOT COLLECTED** (except via Yahoo Finance basic info)

**Verdict**: **NEW CAPABILITY** - Fundamental data for publicly traded commodity companies (ADM, Bunge, Cargill subsidiaries) could provide supply chain signals.

---

### 5. **Forex (FX) Data**

**Alpha Vantage Provides:**
- Exchange Rates
- Intraday FX (premium)
- Daily, Weekly, Monthly FX

**Current Sources:**
- Yahoo Finance (USD/BRL, USD/CNY, USD/ARS, USD/MYR)
- Alpha Vantage (currently fallback only)

**Comparison:**
| Feature | Alpha Vantage | Yahoo Finance |
|--------|---------------|---------------|
| Currency pairs | ✅ 100+ pairs | ⚠️ Limited |
| Historical depth | ✅ 20+ years | ✅ 20+ years |
| Intraday FX | ✅ Premium tier | ⚠️ Limited |
| API reliability | ✅ Official API | ⚠️ Unofficial |

**Verdict**: **CONSOLIDATION OPPORTUNITY** - Alpha Vantage provides more currency pairs and better API reliability. Can replace Yahoo Finance for FX.

---

### 6. **Cryptocurrencies**

**Alpha Vantage Provides:**
- Crypto Exchange Rates
- Intraday Crypto (premium)
- Daily, Weekly, Monthly Crypto

**Current Source:** ❌ **NOT COLLECTED**

**Verdict**: **LOW PRIORITY** - Not directly relevant to soybean oil forecasting, but could be useful for macro correlation analysis.

---

### 7. **Commodities** ⭐ **HIGH VALUE**

**Alpha Vantage Provides:**
- Crude Oil (WTI) - Trending
- Crude Oil (Brent) - Trending
- Natural Gas
- Copper - Trending
- Aluminum
- Wheat
- Corn
- Cotton
- Sugar
- Coffee
- Global Commodities Index

**Current Sources:**
- Yahoo Finance (commodity futures: ZL, ZS, ZM, ZC, ZW, CL, NG, GC, CT)
- EIA (biofuel-specific)

**Comparison:**
| Commodity | Alpha Vantage | Current Source |
|-----------|---------------|----------------|
| Crude Oil (WTI) | ✅ Official API | Yahoo Finance (CL) |
| Crude Oil (Brent) | ✅ Available | ❌ Not collected |
| Natural Gas | ✅ Available | Yahoo Finance (NG) |
| Wheat | ✅ Available | Yahoo Finance (ZW) |
| Corn | ✅ Available | Yahoo Finance (ZC) |
| Cotton | ✅ Available | Yahoo Finance (CT) |
| Sugar | ✅ Available | ❌ Not collected |
| Coffee | ✅ Available | ❌ Not collected |
| Copper | ✅ Available | ❌ Not collected |
| Aluminum | ✅ Available | ❌ Not collected |

**Verdict**: **CONSOLIDATION + EXPANSION** - Alpha Vantage can:
1. Replace Yahoo Finance for commodity prices (better API reliability)
2. Add missing commodities (Brent, Sugar, Coffee, Copper, Aluminum)
3. Provide Global Commodities Index for macro signals

---

### 8. **Economic Indicators** ⭐ **HIGH VALUE**

**⚠️ IMPORTANT DISTINCTION**: Economic Indicators are **macroeconomic data series** (GDP, CPI, unemployment rates) - completely different from Technical Indicators (which are mathematical calculations on price data).

**Alpha Vantage Provides:**
- Real GDP - Trending
- Real GDP per Capita
- Treasury Yield - Trending
- Federal Funds (Interest) Rate
- CPI
- Inflation
- Retail Sales
- Durable Goods Orders
- Unemployment Rate
- Nonfarm Payroll

**Current Source:** FRED API (30+ economic series)

**Comparison:**
| Indicator | Alpha Vantage | FRED (Current) |
|----------|---------------|----------------|
| GDP | ✅ Available | ✅ Available |
| Treasury Yields | ✅ Available | ✅ Available (DGS10, DGS2, etc.) |
| Fed Funds Rate | ✅ Available | ✅ Available (DFF) |
| CPI | ✅ Available | ✅ Available (CPIAUCSL) |
| Unemployment | ✅ Available | ✅ Available (UNRATE) |
| Nonfarm Payroll | ✅ Available | ✅ Available (PAYEMS) |
| **Economic series count** | **~10 core indicators** | **30+ economic series** ✅ |
| Historical depth | 20+ years | 20+ years ✅ |
| API reliability | ✅ Official | ✅ Official |
| Rate limits | Premium: Higher | Free: 120 calls/min |

**Verdict**: **PARTIAL CONSOLIDATION** - Alpha Vantage covers core economic indicators but FRED has more depth (30+ economic series vs. ~10). Recommendation: **Keep FRED for comprehensive economic data coverage**, use Alpha Vantage as backup/verification.

---

### 9. **Technical Indicators** ⭐ **HIGH VALUE**

**⚠️ IMPORTANT DISTINCTION**: Technical Indicators are **mathematical calculations on price/volume data** (SMA, RSI, MACD, etc.) - completely different from Economic Indicators (which are macroeconomic data series like GDP, CPI).

**Alpha Vantage Provides:**
- **50+ Technical Indicators** including:
  - Moving Averages: SMA, EMA, WMA, DEMA, TEMA, TRIMA, KAMA, MAMA
  - Momentum: MACD, STOCH, RSI, MOM, ROC, CCI, ADX, AROON
  - Volatility: BBANDS, ATR, NATR
  - Volume: OBV, AD, ADOSC, VWAP (premium)
  - Advanced: HT_TRENDLINE, HT_SINE, HT_DCPERIOD, HT_PHASOR

**Current Source:** Custom calculations in `scripts/features/feature_calculations.py`

**Comparison:**
| Feature | Alpha Vantage | Current (Custom) |
|--------|---------------|------------------|
| **Technical indicator count** | ✅ **50+ technical indicators** | ⚠️ ~10-15 technical indicators |
| Calculation accuracy | ✅ Industry standard | ⚠️ Custom (may differ) |
| Maintenance | ✅ API handles | ⚠️ Manual code |
| New indicators | ✅ Easy to add | ⚠️ Requires coding |
| Performance | ✅ Optimized | ⚠️ Local computation |

**Note**: These are **technical indicators** (calculated from price data), NOT economic indicators (macroeconomic data series).

**Verdict**: **MAJOR UPGRADE OPPORTUNITY** - Alpha Vantage provides:
1. **3-4x more indicators** than currently calculated
2. **Standardized calculations** (matches TradingView, Bloomberg)
3. **Reduced maintenance** (no custom indicator code)
4. **Easy expansion** (add new indicators via API call)

**Current indicators calculated locally:**
- Moving Averages (6 types)
- RSI
- MACD
- Bollinger Bands
- Volume indicators

**Alpha Vantage adds:**
- ADX, AROON (trend strength)
- STOCH, STOCHRSI (momentum)
- HT_TRENDLINE, HT_SINE (Hilbert Transform)
- Plus 30+ more indicators

---

## Consolidation Analysis

### Data Sources That Could Be Replaced

| Current Source | Alpha Vantage Replacement | Savings |
|----------------|---------------------------|---------|
| Yahoo Finance (prices) | Core Stock APIs | ✅ Better API reliability |
| Yahoo Finance (FX) | Forex APIs | ✅ More currency pairs |
| NewsAPI | Alpha Intelligence News | ✅ Consolidate to one API |
| Custom technical indicators | Technical Indicators API | ✅ 50+ vs. 10-15 indicators |

### New Capabilities Added

1. **Options Data** - Volatility signals
2. **Earnings Transcripts** - Company-specific insights
3. **Insider Transactions** - Corporate activity signals
4. **Fundamental Data** - Company financials
5. **Brent Crude** - Additional energy benchmark
6. **Sugar, Coffee, Copper, Aluminum** - Additional commodities
7. **50+ Technical Indicators** - Expanded technical analysis

---

## Cost-Benefit Analysis

### Free Tier Limitations
- **25 API calls per day** ⚠️ **CRITICAL CONSTRAINT**
- Limited to basic endpoints
- Delayed data only (no real-time)

### Premium Tier Benefits (Subscription Required)
- Higher rate limits: Plan30 (30/min), Plan75 (75/min), Plan150 (150/min), Plan300 (300/min), Plan600 (600/min), Plan1200 (1,200/min)
- Real-time data access (15-minute delayed minimum due to regulations)
- Premium endpoints (VWAP, MACD Premium, etc.)
- Bulk quotes
- Extended historical data (same 20+ years, but faster collection)

### Current Usage Estimate

**⚠️ UPDATED REQUIREMENTS:**
- **11 symbols** (10 commodities + ES futures)
- **50+ technical indicators** per symbol **daily**
- **Daily updates** required

**Daily API Calls Needed:**
- Technical indicators: 11 symbols × 50 indicators = **550 calls/day** ❌
- Price data: 11 symbols × 1 call = 11 calls (or included in indicators)
- **Total: ~550 calls/day** ❌ **EXCEEDS FREE TIER BY 22x**

**Optimized Approach (Hybrid Strategy):**
- Daily core indicators: 11 symbols × 20 indicators = **220 calls/day**
- Weekly additional indicators: 11 symbols × 30 indicators = **330 calls/week**
- **Daily load: 220 calls/day** ⚠️ **REQUIRES PREMIUM TIER**

**Historical Collection (One-Time Backfill):**
- Daily data: 11 symbols × 1 call = 11 calls ✅ **Can do in 1 day**
- Technical indicators: 11 symbols × 50 indicators = 550 calls ⚠️ **Need premium for reasonable time**

**Free Tier:** 25 calls/day = 750 calls/month
- ❌ **Insufficient for daily updates** (need 220-550 calls/day)
- ❌ **Insufficient for historical collection** (would take weeks/months)
- ⚠️ **Not sufficient for intraday historical** (would take months)

**Premium Tier Required:**
- **Plan30 minimum** (30 requests/minute = sufficient for 220/day)
- **Plan75 recommended** (75 requests/minute = faster collection, more headroom)

**Why Premium is Required:**
- ✅ **Daily technical indicators** (220-550 calls/day needed)
- ✅ **ES futures support** (hidden page requirement)
- ✅ **All 50+ indicators** per symbol
- ✅ **Faster historical backfill** (hours vs. weeks)
- ✅ **Real-time data** (if needed)
- ✅ **Higher frequency updates** (if needed)

---

## Recommendation Matrix

### ✅ **HIGH PRIORITY - Subscribe**

1. **Technical Indicators API**
   - **Impact**: 3-4x more indicators, standardized calculations
   - **ROI**: Reduces custom code maintenance, improves accuracy
   - **Cost**: Premium tier likely needed for bulk operations

2. **Commodities API**
   - **Impact**: Better reliability than Yahoo Finance, adds missing commodities
   - **ROI**: Consolidates commodity data collection
   - **Cost**: Free tier may suffice for daily updates

### ⚠️ **MEDIUM PRIORITY - Evaluate**

3. **Alpha Intelligence (News & Sentiment)**
   - **Impact**: Consolidates NewsAPI, adds earnings/insider data
   - **ROI**: Reduces number of APIs to maintain
   - **Cost**: Free tier may suffice

4. **Forex API**
   - **Impact**: Better reliability, more currency pairs
   - **ROI**: Consolidates FX data collection
   - **Cost**: Free tier likely sufficient

### ❌ **LOW PRIORITY - Skip**

5. **Core Stock APIs** (if keeping Yahoo Finance)
   - **Reason**: Yahoo Finance works, no immediate need to change
   - **Exception**: If real-time data needed, consider Alpha Vantage premium

6. **Economic Indicators**
   - **Reason**: FRED provides more comprehensive coverage (30+ vs. 10 indicators)
   - **Keep**: FRED as primary, Alpha Vantage as backup

7. **Options, Crypto, Fundamental Data**
   - **Reason**: Not directly relevant to soybean oil forecasting
   - **Future**: Consider if expanding scope

---

## Implementation Plan (If Subscribing)

### Phase 1: Technical Indicators (Week 1)
1. Subscribe to Alpha Vantage premium
2. Replace custom indicator calculations with API calls
3. Add 20+ new indicators (ADX, AROON, HT_TRENDLINE, etc.)
4. Update feature engineering pipeline
5. Validate calculations match current results

### Phase 2: Commodities Consolidation (Week 2)
1. Replace Yahoo Finance commodity prices with Alpha Vantage
2. Add missing commodities (Brent, Sugar, Coffee, Copper, Aluminum)
3. Update ingestion scripts
4. Validate data quality

### Phase 3: News & Sentiment (Week 3)
1. Replace NewsAPI with Alpha Intelligence
2. Add earnings transcripts collection
3. Add insider transactions tracking
4. Update sentiment pipeline

### Phase 4: FX Consolidation (Week 4)
1. Replace Yahoo Finance FX with Alpha Vantage Forex API
2. Expand currency pairs
3. Update ingestion scripts

---

## Risk Assessment

### Risks
1. **API Dependency**: Single point of failure if Alpha Vantage goes down
   - **Mitigation**: Keep Yahoo Finance/FRED as fallbacks

2. **Rate Limits**: Premium tier may have limits
   - **Mitigation**: Implement caching, batch operations

3. **Data Quality**: Need to validate Alpha Vantage data matches current sources
   - **Mitigation**: Run parallel collection for 1 month, compare results

4. **Cost**: Premium subscription cost unknown
   - **Mitigation**: Start with free tier, upgrade if needed

### Benefits
1. **Consolidation**: Fewer APIs to maintain
2. **Reliability**: Official API vs. unofficial libraries
3. **Expansion**: Easy to add new indicators/data types
4. **Standardization**: Industry-standard calculations

---

## Final Recommendation

### ✅ **RECOMMEND SUBSCRIBING** with phased approach:

**Start with Free Tier:**
- Test Technical Indicators API
- Test Commodities API
- Validate data quality vs. current sources

**Upgrade to Premium If:**
- Need real-time data
- Need higher rate limits
- Need premium endpoints (VWAP, bulk quotes)
- Free tier insufficient for daily operations

**Priority Order:**
1. **Technical Indicators** (highest ROI - reduces code maintenance)
2. **Commodities** (consolidation + expansion)
3. **News & Sentiment** (consolidation)
4. **Forex** (consolidation)

**Keep Separate:**
- **FRED** (30+ **economic indicators** - macroeconomic data like GDP, CPI, unemployment - more comprehensive than Alpha Vantage's ~10 economic indicators)
- **EIA** (biofuel-specific data not available elsewhere)
- **CFTC** (COT data not available elsewhere)
- **USDA** (agricultural reports not available elsewhere)
- **NOAA** (weather data not available elsewhere)
- **ScrapeCreators** (Truth Social - unique source)

**Clarification**: 
- **FRED's 30+** = Economic Indicators (macroeconomic data series)
- **Alpha Vantage's 50+** = Technical Indicators (mathematical calculations on price data)
- These are **completely different categories** and both are valuable

---

## Next Steps

1. **Contact Alpha Vantage** for premium pricing
2. **Test free tier** with Technical Indicators API
3. **Validate data quality** vs. current sources
4. **Implement Phase 1** (Technical Indicators) if successful
5. **Evaluate premium tier** based on Phase 1 results

---

## References

- Alpha Vantage Documentation: https://www.alphavantage.co/documentation/
- Current Data Sources: `docs/plans/DATA_SOURCES_REFERENCE.md`
- Feature Calculations: `scripts/features/feature_calculations.py`
- Current Ingestion: `scripts/ingest/collect_*.py`

---

**Last Updated**: November 16, 2025  
**Status**: Ready for decision - Awaiting premium pricing information

