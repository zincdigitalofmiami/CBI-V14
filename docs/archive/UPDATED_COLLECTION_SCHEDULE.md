---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Updated Collection Schedule
**Date**: November 18, 2025  
**Status**: Revised based on user feedback

---

## Primary Symbols - DataBento

### ZL (Soybean Oil) - EVERY 5 MINUTES
**Reason**: Primary forecasting asset, needs highest resolution
```bash
*/5 * * * * python3 scripts/live/databento_collector.py --symbols ZL --tier primary
```

### MES (Micro E-mini S&P 500) - EVERY 5 MINUTES
**Reason**: Market sentiment indicator, high importance
```bash
*/5 * * * * python3 scripts/live/databento_collector.py --symbols MES --tier primary
```

### ES (S&P 500 E-mini) - EVERY HOUR
**Reason**: Modeling mostly, hourly sufficient
```bash
0 * * * * python3 scripts/live/databento_collector.py --symbols ES --tier secondary
```

---

## Secondary Symbols - DataBento (All Hourly)

**Symbols**: ZS, ZM, CL, NG, ZC, ZW, RB, HO, GC, SI, HG

```bash
# Every hour
0 * * * * python3 scripts/live/databento_collector.py --symbols ZS,ZM,CL,NG,ZC,ZW,RB,HO,GC,SI,HG --tier secondary
```

---

## FX Futures - DataBento (Hourly)

**Symbols**: 6E (EUR/USD), 6B (GBP/USD), 6J (JPY/USD)

```bash
# Every hour
0 * * * * python3 scripts/live/databento_collector.py --symbols 6E,6B,6J --tier fx
```

---

## Macro Economic - FRED (Every 4 Hours)

**Change**: Was 15 minutes → Now 4 hours
**Reason**: Data updates infrequently, 4-hour checks sufficient

```bash
# Every 4 hours
0 */4 * * * python3 scripts/ingest/collect_fred_comprehensive.py
```

**Update existing script**: Change from `*/15` to `0 */4`

---

## Weather - NOAA/INMET (Daily)

**Frequency**: Daily at 6 AM
**Coverage**: US (Midwest), Brazil (soybean regions), Argentina (soybean regions)
**Segmentation**: By area code (state/province)

```bash
# Daily 6 AM
0 6 * * * python3 scripts/ingest/collect_weather_comprehensive.py --countries US,BR,AR --segment-by-area
```

---

## Energy - EIA (Daily if Possible, Otherwise Weekly)

**Current**: Weekly (Wednesday 10:30 AM when report releases)
**Requested**: Daily if possible

**Research needed**: 
- Does EIA API provide daily updates?
- Or only weekly report releases?

**For now - Daily check with weekly actual data**:
```bash
# Daily check (will only find new data weekly)
0 11 * * * python3 scripts/ingest/collect_eia_comprehensive.py --check-daily
```

**EIA Release Schedule**:
- Petroleum Status Report: Wednesday 10:30 AM
- Natural Gas Storage: Thursday 10:30 AM
- Weekly data only, but check daily for revisions

---

## Alpha Vantage - Sentiment & Intelligence

### 1. News Sentiment (Hourly)

**Endpoint**: `NEWS_SENTIMENT`
**Frequency**: Every hour
**Topics**: Soybean, biofuel, energy, policy

```bash
# Every hour
0 * * * * python3 scripts/ingest/collect_alpha_sentiment.py --topics soybean,biofuel,energy,policy
```

### 2. Insider Transactions (Daily)

**Endpoint**: `INSIDER_TRANSACTIONS`
**Use Case**: Track insider activity in:
- Biofuel companies (renewable diesel producers)
- Agricultural companies (ADM, Bunge, Cargill public entities)
- Soybean processors
- Related ETFs

**Symbols to Track**:
- **Biofuel/Renewable**: REX (renewable fuels), GEVO (renewable fuels), REGI (Renewable Energy Group)
- **Ag Processors**: ADM (Archer Daniels Midland), BG (Bunge), MOO (VanEck Agribusiness ETF)
- **Oil Related**: CVX (Chevron - renewable diesel), PSX (Phillips 66 - renewable diesel)

```bash
# Daily at 7 AM
0 7 * * * python3 scripts/ingest/collect_alpha_insider.py --symbols ADM,BG,REX,GEVO,REGI,CVX,PSX,MOO
```

**Why useful**:
- Insider buying in biofuel stocks → bullish for renewable diesel demand → bullish for soybean oil
- Insider selling in ag processors → bearish signal for commodity processing
- Early indicator of corporate outlook

### 3. Analytics - Fixed Window (Daily)

**Endpoint**: `ANALYTICS_FIXED_WINDOW`
**Use Case**: Pre-calculated analytics over fixed time windows
- Volatility measures
- Correlation matrices
- Performance metrics

```bash
# Daily at 3 AM (after market close data available)
0 3 * * * python3 scripts/ingest/collect_alpha_analytics_fixed.py --symbols ZL,ADM,BG --window 30d
```

### 4. Analytics - Sliding Window (Daily)

**Endpoint**: `ANALYTICS_SLIDING_WINDOW`
**Use Case**: Rolling window analytics
- Moving correlations
- Dynamic volatility
- Trend strength

```bash
# Daily at 3:30 AM
30 3 * * * python3 scripts/ingest/collect_alpha_analytics_sliding.py --symbols ZL,ADM,BG --window 30d
```

---

## CFTC Positioning (Every 8 Hours)

**Frequency**: Every 8 hours (3x daily)
**Reason**: Check for updates/revisions

```bash
# Every 8 hours
0 */8 * * * python3 scripts/ingest/collect_cftc_comprehensive.py
```

---

## News - Breaking (Every 15 Minutes for Critical)

**Symbols**: ZL (critical)
**Sources**: NewsAPI, Alpha Vantage sentiment

```bash
# Every 15 minutes
*/15 * * * * python3 scripts/ingest/collect_news_breaking.py --symbols ZL --priority critical
```

---

## News - General (Every Hour)

**All Topics**: Commodity, policy, trade, weather

```bash
# Every hour
0 * * * * python3 scripts/ingest/collect_news_comprehensive.py --bucket --regime --correlate
```

---

## USDA (Weekly)

**Frequency**: Weekly on release days
**Thursday**: Export sales (12 PM)
**Friday**: Crop reports (varies)

```bash
# Thursday 12 PM
0 12 * * 4 python3 scripts/ingest/collect_usda_comprehensive.py

# Friday (check for crop reports)
0 8,12,16 * * 5 python3 scripts/ingest/collect_usda_crop_reports.py
```

---

## Complete Cron Schedule (Updated)

```bash
# ============================================================================
# CBI-V14 PRODUCTION COLLECTION SCHEDULE (Updated 2025-11-18)
# ============================================================================

# DataBento - Primary (5-minute)
*/5 * * * * cd /path/to/CBI-V14 && python3 scripts/live/databento_collector.py --symbols ZL,MES --tier primary >> Logs/databento_primary.log 2>&1

# DataBento - ES (hourly)
0 * * * * cd /path/to/CBI-V14 && python3 scripts/live/databento_collector.py --symbols ES --tier secondary >> Logs/databento_es.log 2>&1

# DataBento - Secondary symbols (hourly)
0 * * * * cd /path/to/CBI-V14 && python3 scripts/live/databento_collector.py --symbols ZS,ZM,CL,NG,ZC,ZW,RB,HO,GC,SI,HG --tier secondary >> Logs/databento_secondary.log 2>&1

# DataBento - FX futures (hourly)
0 * * * * cd /path/to/CBI-V14 && python3 scripts/live/databento_collector.py --symbols 6E,6B,6J --tier fx >> Logs/databento_fx.log 2>&1

# FRED - Economic indicators (every 4 hours)
0 */4 * * * cd /path/to/CBI-V14 && python3 scripts/ingest/collect_fred_comprehensive.py >> Logs/fred.log 2>&1

# Weather - Daily (all 3 countries, segmented)
0 6 * * * cd /path/to/CBI-V14 && python3 scripts/ingest/collect_weather_comprehensive.py --countries US,BR,AR --segment-by-area >> Logs/weather.log 2>&1

# EIA - Daily check (actual data weekly)
0 11 * * * cd /path/to/CBI-V14 && python3 scripts/ingest/collect_eia_comprehensive.py --check-daily >> Logs/eia.log 2>&1

# Alpha Vantage - News sentiment (hourly)
0 * * * * cd /path/to/CBI-V14 && python3 scripts/ingest/collect_alpha_sentiment.py --topics soybean,biofuel,energy,policy >> Logs/alpha_sentiment.log 2>&1

# Alpha Vantage - Insider transactions (daily)
0 7 * * * cd /path/to/CBI-V14 && python3 scripts/ingest/collect_alpha_insider.py --symbols ADM,BG,REX,GEVO,REGI,CVX,PSX,MOO >> Logs/alpha_insider.log 2>&1

# Alpha Vantage - Analytics fixed window (daily)
0 3 * * * cd /path/to/CBI-V14 && python3 scripts/ingest/collect_alpha_analytics_fixed.py --symbols ZL,ADM,BG --window 30d >> Logs/alpha_analytics_fixed.log 2>&1

# Alpha Vantage - Analytics sliding window (daily)
30 3 * * * cd /path/to/CBI-V14 && python3 scripts/ingest/collect_alpha_analytics_sliding.py --symbols ZL,ADM,BG --window 30d >> Logs/alpha_analytics_sliding.log 2>&1

# CFTC - Positioning (every 8 hours)
0 */8 * * * cd /path/to/CBI-V14 && python3 scripts/ingest/collect_cftc_comprehensive.py >> Logs/cftc.log 2>&1

# News - Breaking (every 15 minutes for ZL)
*/15 * * * * cd /path/to/CBI-V14 && python3 scripts/ingest/collect_news_breaking.py --symbols ZL --priority critical >> Logs/news_breaking.log 2>&1

# News - General (hourly)
0 * * * * cd /path/to/CBI-V14 && python3 scripts/ingest/collect_news_comprehensive.py --bucket --regime --correlate >> Logs/news_general.log 2>&1

# USDA - Weekly
0 12 * * 4 cd /path/to/CBI-V14 && python3 scripts/ingest/collect_usda_comprehensive.py >> Logs/usda.log 2>&1
0 8,12,16 * * 5 cd /path/to/CBI-V14 && python3 scripts/ingest/collect_usda_crop_reports.py >> Logs/usda_crops.log 2>&1
```

---

## Alpha Vantage Intelligence - Research Findings

### INSIDER_TRANSACTIONS

**What it provides**:
- Latest insider buying/selling activity
- Transaction amounts, dates, ownership changes
- For publicly traded companies

**Use for CBI-V14**:
- Track insider activity in biofuel producers (REX, GEVO, REGI)
- Track ag processors (ADM, Bunge)
- Early signal of corporate outlook → demand signals for soybean oil

**Example**:
- Heavy insider buying at REX (renewable fuel producer) → bullish signal for renewable diesel demand → bullish for soybean oil (feedstock)
- Insider selling at ADM (processor) → bearish signal for ag commodity demand

### ANALYTICS_FIXED_WINDOW

**What it provides**:
- Pre-calculated analytics over fixed time periods (30d, 60d, 90d, etc.)
- Metrics: volatility, Sharpe ratio, correlation, drawdown, etc.
- Saves compute time on common calculations

**Use for CBI-V14**:
- Volatility regime detection (high vs low volatility periods)
- Correlation tracking (ZL vs crude, ZL vs palm oil proxies)
- Risk metrics for position sizing

### ANALYTICS_SLIDING_WINDOW

**What it provides**:
- Rolling window analytics
- Dynamic correlations (how correlation changes over time)
- Trend strength measures

**Use for CBI-V14**:
- Detect regime changes (when correlations break down)
- Identify trend persistence
- Track changing relationships between ZL and drivers

---

## BigQuery Tables for Alpha Intelligence

### Table: `raw_intelligence.alpha_insider_transactions`

```sql
CREATE TABLE raw_intelligence.alpha_insider_transactions (
  date DATE NOT NULL,
  symbol STRING NOT NULL,
  insider_name STRING,
  transaction_type STRING,  -- buy, sell
  shares INT64,
  price FLOAT64,
  value FLOAT64,
  ownership_pct FLOAT64,
  filing_date DATE,
  related_commodity STRING,  -- soybean_oil, biofuel, ag_processing
  impact_signal STRING,      -- bullish, bearish, neutral
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY symbol, related_commodity
OPTIONS (
  description='Alpha Vantage insider transactions for biofuel/ag companies'
);
```

### Table: `raw_intelligence.alpha_analytics`

```sql
CREATE TABLE raw_intelligence.alpha_analytics (
  date DATE NOT NULL,
  symbol STRING NOT NULL,
  window_type STRING NOT NULL,    -- fixed, sliding
  window_size STRING NOT NULL,    -- 30d, 60d, 90d
  metric_name STRING NOT NULL,    -- volatility, correlation, sharpe, drawdown
  metric_value FLOAT64,
  reference_symbol STRING,        -- For correlations
  metadata JSON,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY symbol, metric_name
OPTIONS (
  description='Alpha Vantage pre-calculated analytics'
);
```

---

## Updated Monthly Data Volume

| Source | Frequency | Monthly Volume |
|--------|-----------|----------------|
| DataBento ZL,MES (5-min) | Every 5 min | 40 MB |
| DataBento ES (hourly) | Every hour | 10 MB |
| DataBento Secondary (hourly) | Every hour | 100 MB |
| DataBento FX (hourly) | Every hour | 30 MB |
| FRED (4-hour) | Every 4 hours | 0.3 MB |
| Weather (daily) | Daily | 60 MB |
| EIA (daily check) | Daily | 2 MB |
| Alpha Sentiment (hourly) | Every hour | 150 MB |
| Alpha Insider (daily) | Daily | 5 MB |
| Alpha Analytics (daily) | Daily | 10 MB |
| CFTC (8-hour) | Every 8 hours | 2 MB |
| News Breaking (15-min) | Every 15 min | 50 MB |
| News General (hourly) | Every hour | 100 MB |
| USDA (weekly) | Weekly | 4 MB |
| **TOTAL** | — | **~560 MB/month** |

**12-month storage**: ~6.7 GB
**Cost**: $0.13/month (13 pennies)

Still well under 10 GB free tier ✅

---

## Summary of Changes

### Original → Updated

| Item | Original | Updated | Reason |
|------|----------|---------|--------|
| ES collection | 5-minute | **Hourly** | Modeling mostly |
| FRED collection | 15-minute | **4-hour** | Data updates infrequently |
| Weather | Daily | **Daily** | No change |
| EIA | Weekly | **Daily check** | Catch revisions |
| Alpha Vantage | Sentiment only | **+ Insider + Analytics** | More signal layers |

### New Additions

1. **Insider Transactions** - Track biofuel/ag company insiders
2. **Analytics Fixed** - Pre-calculated metrics
3. **Analytics Sliding** - Rolling window analytics
4. **FX Futures** - 6E, 6B, 6J from DataBento

---

## Next: Create Collection Scripts

Ready to create:
1. Updated DataBento collector (handles all tiers)
2. Alpha Vantage intelligence collectors (insider + analytics)
3. Updated cron schedule script
4. BigQuery tables for new data

Say the word and I'll generate all collection scripts.






