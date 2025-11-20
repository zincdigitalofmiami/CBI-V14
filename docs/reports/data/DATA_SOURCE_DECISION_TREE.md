---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Data Source Decision Tree
**Quick reference for "Where does this data come from?"**

---

## Question 1: Is it PRICE data for a FUTURES contract?

### YES → Use DataBento

```
Examples:
✅ ES (S&P 500 futures) → DataBento ES.FUT
✅ ZL (Soybean Oil futures) → DataBento ZL.FUT
✅ CL (WTI Crude futures) → DataBento CL.FUT
✅ GC (Gold futures) → DataBento GC.FUT

❌ NOT Yahoo Finance 'ZL=F'
❌ NOT Alpha Vantage TIME_SERIES_DAILY
❌ NOT any proxy ETF (USO, GLD, etc.)
```

**Why**: DataBento = actual futures, tick-accurate, no delays

---

## Question 2: Is it a TECHNICAL INDICATOR?

### Calculate it yourself from DataBento OHLCV

```
Examples:
✅ SMA/EMA → Calculate from DataBento bars
✅ RSI → Calculate from DataBento close prices
✅ MACD → Calculate from DataBento close prices
✅ Bollinger Bands → Calculate from DataBento close prices
✅ ATR → Calculate from DataBento high/low prices

Optional: Use Alpha Vantage for validation (weekly comparison)
❌ NOT primary feature source
```

**Why**: More accurate, no API delays, full control

---

## Question 3: Is it MACRO ECONOMIC data?

### YES → Use FRED

```
Examples:
✅ Interest rates → FRED (DFF, DGS10, etc.)
✅ Inflation → FRED (CPIAUCSL, CPILFESL)
✅ Dollar index → FRED (DTWEXBGS)
✅ USD/BRL exchange rate → FRED (DEXBZUS)
✅ VIX → FRED (VIXCLS)
✅ Employment → FRED (PAYEMS, UNRATE)
✅ GDP → FRED (GDP)

❌ NOT commodity prices (use DataBento)
```

**Why**: FRED = free, authoritative, updated daily

---

## Question 4: Is it WEATHER data?

### YES → Use NOAA

```
Examples:
✅ Temperature → NOAA API
✅ Precipitation → NOAA API
✅ GDD (Growing Degree Days) → Calculate from NOAA temps
✅ Brazil weather → INMET (Brazil weather service)
✅ Argentina weather → Argentina SMN

❌ NOT private weather services (unless free tier)
```

**Why**: NOAA = free, official, comprehensive

---

## Question 5: Is it AGRICULTURAL data?

### YES → Use USDA

```
Examples:
✅ Crop reports → USDA NASS API
✅ Export sales → USDA FAS API
✅ Harvest progress → USDA Crop Progress
✅ Stocks → USDA Grain Stocks

❌ NOT commodity prices (use DataBento)
```

**Why**: USDA = free, official, authoritative

---

## Question 6: Is it POSITIONING data (Commitments of Traders)?

### YES → Use CFTC

```
Examples:
✅ Managed money positions → CFTC API
✅ Commercial hedger positions → CFTC API
✅ Open interest → CFTC API

For: ZL, ZS, ZM, CL, NG, GC, ES
```

**Why**: CFTC = free, official, weekly updates

---

## Question 7: Is it ENERGY data?

### YES → Use EIA

```
Examples:
✅ Petroleum inventory → EIA API
✅ Refinery operations → EIA API
✅ Biofuel production → EIA API
✅ Natural gas storage → EIA API

❌ NOT energy prices (use DataBento CL, NG, RB, HO)
```

**Why**: EIA = free, official, weekly updates

---

## Question 8: Is it NEWS SENTIMENT?

### YES → Use NewsAPI / ScrapeCreators

```
Examples:
✅ Commodity news headlines → NewsAPI
✅ Social media sentiment → ScrapeCreators
✅ Policy news → NewsAPI
✅ Trade war news → NewsAPI
```

**Why**: Best coverage for sentiment analysis

---

## Summary Table

| Data Type | Source | Frequency | Cost |
|-----------|--------|-----------|------|
| **Futures OHLCV** | **DataBento** | **1-minute** | **$0 (included)** |
| Technical Indicators | Calculate from DataBento | As needed | $0 |
| Macro Economic | FRED | Daily | $0 |
| Weather | NOAA / INMET | Daily | $0 |
| Agricultural | USDA | Weekly | $0 |
| Positioning | CFTC | Weekly | $0 |
| Energy | EIA | Weekly | $0 |
| News Sentiment | NewsAPI | Hourly | $0-50 |
| Extended FX | FRED / Alpha | Daily | $0-75 |

---

## What NOT to Use

### ❌ Yahoo Finance for Futures
- Delayed data
- Gaps and errors
- Not tick-accurate
- Use DataBento instead

### ❌ Alpha Vantage for Primary Prices
- Not futures (uses ETF proxies)
- Delayed data
- Use DataBento instead

### ❌ Proxy ETFs
- USO ≠ CL (crude oil futures)
- GLD ≠ GC (gold futures)
- Use actual futures from DataBento

### ❌ Multiple Sources for Same Data
- Don't collect ZL from both Yahoo and DataBento
- Pick ONE authoritative source
- DataBento = authoritative for futures

---

## BigQuery Table Mapping

| Data Source | BigQuery Table | Update Method |
|-------------|----------------|---------------|
| DataBento | `market_data.futures_ohlcv_1m` | APPEND |
| FRED | `raw_intelligence.fred_economic` | MERGE |
| Alpha Vantage | `raw_intelligence.alpha_vantage` | MERGE |
| NOAA | `raw_intelligence.weather` | APPEND |
| USDA | `raw_intelligence.usda_agricultural` | MERGE |
| CFTC | `raw_intelligence.cftc_positioning` | MERGE |
| EIA | `raw_intelligence.eia_energy` | MERGE |
| NewsAPI | `raw_intelligence.news_sentiment` | APPEND + DEDUPE |

---

## Collection Priority

### Tier 1: Must Have (Run First)
1. **DataBento** (ES, ZL, CL) - Core price data
2. **FRED** (macro indicators) - Free, essential

### Tier 2: Important (Run Second)
3. **NOAA** (weather) - Free, for agricultural forecasting
4. **CFTC** (positioning) - Free, weekly

### Tier 3: Nice to Have
5. **Alpha Vantage** (validation, options) - Paid, supplementary
6. **USDA** (agricultural) - Free, weekly
7. **EIA** (energy) - Free, weekly
8. **NewsAPI** (sentiment) - Paid, supplementary

---

## Next Decision: What to Collect Now?

### Minimal Setup (Cost: $0/month)
- DataBento: ES, ZL, CL (Priority 1)
- FRED: All macro indicators
- NOAA: Weather
- CFTC: Weekly positioning

### Standard Setup (Cost: $75/month)
- Everything in Minimal
- Plus: Alpha Vantage (validation + options)
- Plus: All 13 DataBento symbols

### Full Setup (Cost: $125/month)
- Everything in Standard
- Plus: NewsAPI (sentiment)
- Plus: Extended data sources

**Recommendation**: Start with Standard Setup ($75/month = just DataBento plan)

