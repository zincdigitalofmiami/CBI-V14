---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# CBI-V14 Data Source Strategy
**Date**: November 18, 2025  
**Purpose**: Define what data comes from where BEFORE setting up BigQuery

---

## Data Source Hierarchy

### Primary Rule: DataBento for ALL Futures Price Data

**DataBento** = Professional-grade futures OHLCV (Open/High/Low/Close/Volume)
- **Why**: Clean data, no proxy ETFs, actual futures contracts
- **What**: All futures symbols in `databento_universe.yaml`
- **How**: GLBX.MDP3 dataset, parent symbology, 1-minute bars

### Secondary Sources: Domain Data Only

**FRED** = Macro economic indicators (NOT prices)
**Alpha Vantage** = Technical indicators + validation (NOT prices)
**Other APIs** = Weather, policy, sentiment (NOT prices)

---

## Part 1: DataBento Coverage (Primary Price Source)

### Futures Symbols from DataBento (13 roots)

#### Priority 1 (Core - ALWAYS collect)
```yaml
ES   # S&P 500 E-mini futures (CME)
MES  # Micro E-mini S&P 500 (CME)
ZL   # Soybean Oil (CBOT) - PRIMARY ASSET
ZS   # Soybeans (CBOT)
ZM   # Soybean Meal (CBOT)
CL   # WTI Crude Oil (NYMEX)
NG   # Natural Gas (NYMEX)
```

#### Priority 2 (Important - collect if capacity)
```yaml
ZC   # Corn (CBOT)
ZW   # Wheat (CBOT)
RB   # RBOB Gasoline (NYMEX)
HO   # Heating Oil (NYMEX)
GC   # Gold (COMEX)
```

#### Priority 3 (Nice to have)
```yaml
SI   # Silver (COMEX)
HG   # Copper (COMEX)
```

### DataBento Data Characteristics

**Frequency**: 1-minute OHLCV bars
**Dataset**: GLBX.MDP3 (CME Globex Market Data Platform)
**Symbology**: Parent (e.g., `ES.FUT`)
**Schema**: `ohlcv-1m`
**Exclusions**: Calendar spreads (symbol contains '-')

**Daily Volume** (estimated):
- Trading hours: ~6.5 hours/day for ES (6:00 PM - 4:15 PM CT next day)
- Bars per symbol: ~390 bars/day (6.5 hours × 60 minutes)
- 13 symbols × 390 bars = **5,070 bars/day**
- **~150K bars/month** across all symbols

**Storage Size** (Parquet compressed):
- Per bar: ~80-100 bytes (OHLCV + metadata)
- Daily: 5,070 bars × 90 bytes = **456 KB/day**
- Monthly: **13.7 MB/month**
- Yearly: **165 MB/year**

---

## Part 2: Supplementary Data Sources (Non-Price)

### FRED (Federal Reserve Economic Data)

**Purpose**: Macro economic indicators
**Frequency**: Daily (some weekly/monthly)
**Volume**: ~60 series × daily = minimal

**Key Series**:
- Interest rates (DFF, DGS10, DGS2, DGS30, DGS5)
- Inflation (CPIAUCSL, CPILFESL, PCEPI)
- Dollar index (DTWEXBGS, DEXBZUS for USD/BRL)
- VIX (VIXCLS)
- Employment, GDP, manufacturing

**Storage**: ~10 KB/day = **300 KB/month**

**DO NOT collect from FRED**:
- ❌ Commodity prices (use DataBento)
- ❌ Stock prices (use DataBento for ES)
- ❌ Oil prices (use DataBento CL)

### NOAA (Weather)

**Purpose**: Weather data for agricultural commodities
**Frequency**: Daily
**Volume**: ~20-30 API calls/day

**Coverage**:
- US Midwest (corn/soy belt)
- Brazil (soybean production)
- Argentina (soybean production)

**Storage**: ~2 MB/day = **60 MB/month**

### USDA

**Purpose**: Agricultural data
**Frequency**: Weekly (some monthly)
**Volume**: ~10-20 API calls/week

**Coverage**:
- Crop reports
- Export sales
- Harvest progress

**Storage**: ~1 MB/week = **4 MB/month**

### CFTC

**Purpose**: Positioning data (Commitments of Traders)
**Frequency**: Weekly (Friday release)
**Volume**: ~5 API calls/week

**Coverage**:
- Managed money positions
- Commercial hedger positions
- For ZL, ZS, ZM, CL, NG, GC, ES

**Storage**: ~500 KB/week = **2 MB/month**

### EIA

**Purpose**: Energy data
**Frequency**: Weekly
**Volume**: ~10 API calls/week

**Coverage**:
- Petroleum inventory
- Refinery operations
- Biofuel production

**Storage**: ~500 KB/week = **2 MB/month**

### NewsAPI / ScrapeCreators

**Purpose**: Sentiment analysis
**Frequency**: Every 4-6 hours
**Volume**: ~100-200 articles/day

**Coverage**:
- Commodity news
- Policy news
- Trade war news
- Social media sentiment

**Storage**: ~5 MB/day = **150 MB/month**

---

## Part 3: Data Source Summary Table

| Source | Purpose | Frequency | Monthly Data | Cost |
|--------|---------|-----------|--------------|------|
| **DataBento** | **Futures OHLCV** | **1-minute** | **14 MB** | **$0 (included in plan)** |
| FRED | Macro indicators | Daily | 0.3 MB | $0 (free API) |
| Alpha Vantage | Technicals/validation | Daily | 150 MB | $75 (Plan75) |
| NOAA | Weather | Daily | 60 MB | $0 (free API) |
| USDA | Agricultural | Weekly | 4 MB | $0 (free API) |
| CFTC | Positioning | Weekly | 2 MB | $0 (free API) |
| EIA | Energy | Weekly | 2 MB | $0 (free API) |
| NewsAPI | Sentiment | 4-6 hours | 150 MB | $0-50/month |
| **TOTAL** | — | — | **~380 MB/month** | **$75-125/month** |

---

## Part 4: BigQuery Table Strategy

### Core Principle: Separate Tables by Source + Update Pattern

**Why**: Different update frequencies require different table structures

### Table 1: `market_data.futures_ohlcv_1m` (DataBento)

**Purpose**: ALL futures 1-minute OHLCV data
**Update**: Continuous (every 5-15 minutes during market hours)
**Partitioning**: `PARTITION BY DATE(ts_event)`
**Clustering**: `CLUSTER BY root, symbol`

**Schema**:
```sql
CREATE TABLE market_data.futures_ohlcv_1m (
  ts_event TIMESTAMP NOT NULL,
  root STRING NOT NULL,           -- ES, ZL, CL, etc.
  symbol STRING NOT NULL,          -- ESH5, ZLZ24, etc.
  instrument_id INT64,
  open FLOAT64,
  high FLOAT64,
  low FLOAT64,
  close FLOAT64,
  volume INT64,
  publisher_id INT64,
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(ts_event)
CLUSTER BY root, symbol
OPTIONS (
  partition_expiration_days=365,  -- Auto-delete after 1 year
  description='DataBento GLBX.MDP3 1-minute OHLCV for all futures'
);
```

**Update Strategy**: APPEND only (no duplicates due to state tracking)

**Storage Growth**:
- **New data**: 14 MB/month (only new bars)
- **After 1 year**: Auto-deleted (partition expiration)
- **Max storage**: ~170 MB (12 months × 14 MB)

**Cost**: $0.003/month (170 MB × $0.020/GB = $0.0034)

### Table 2: `raw_intelligence.fred_economic` (FRED)

**Purpose**: Macro economic indicators
**Update**: Daily (MERGE/UPSERT on date + series_id)
**Partitioning**: `PARTITION BY DATE(date)`

**Schema**:
```sql
CREATE TABLE raw_intelligence.fred_economic (
  date DATE NOT NULL,
  series_id STRING NOT NULL,
  series_name STRING,
  value FLOAT64,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY series_id
OPTIONS (
  partition_expiration_days=1825  -- 5 years
);
```

**Update Strategy**: MERGE (update existing dates)

**Storage Growth**:
- **Initial**: 10 MB (historical data 2020-2025)
- **Growth**: 0.3 MB/month (only new dates)
- **After 1 year**: 13.6 MB

**Cost**: $0.0003/month

### Table 3: `raw_intelligence.alpha_vantage` (Alpha Vantage)

**Purpose**: Technical indicators, options, extended FX
**Update**: Daily (MERGE on date + symbol + indicator)
**Partitioning**: `PARTITION BY DATE(date)`

**Schema**:
```sql
CREATE TABLE raw_intelligence.alpha_vantage (
  date DATE NOT NULL,
  symbol STRING NOT NULL,
  indicator_type STRING,  -- 'SMA', 'RSI', 'MACD', 'OPTIONS', 'FX'
  indicator_name STRING,
  value FLOAT64,
  metadata JSON,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY symbol, indicator_type;
```

**Update Strategy**: MERGE

**Storage Growth**: 150 MB/month → 1.8 GB/year

**Cost**: $0.03/month (1.8 GB × $0.020)

### Table 4: `raw_intelligence.weather` (NOAA)

**Purpose**: Weather data
**Update**: Daily (APPEND)
**Schema**: date, location, temp, precip, etc.
**Storage**: 60 MB/month → 720 MB/year
**Cost**: $0.014/month

### Table 5: `raw_intelligence.cftc_positioning` (CFTC)

**Purpose**: Positioning data
**Update**: Weekly (MERGE on report_date + commodity)
**Schema**: report_date, commodity, managed_money_long, managed_money_short, etc.
**Storage**: 2 MB/month → 24 MB/year
**Cost**: $0.0005/month

### Table 6: `raw_intelligence.news_sentiment` (NewsAPI)

**Purpose**: News sentiment
**Update**: Every 4-6 hours (APPEND with deduplication)
**Schema**: timestamp, headline, sentiment_score, source, etc.
**Storage**: 150 MB/month → 1.8 GB/year
**Cost**: $0.03/month

---

## Part 5: Total BigQuery Storage Projection

### Month 1 (After Initial Upload)

| Table | Size | Cost |
|-------|------|------|
| futures_ohlcv_1m | 14 MB | $0.0003 |
| fred_economic | 10 MB | $0.0002 |
| alpha_vantage | 150 MB | $0.003 |
| weather | 60 MB | $0.0012 |
| cftc_positioning | 2 MB | $0.00004 |
| news_sentiment | 150 MB | $0.003 |
| Existing data | 700 MB | $0.014 |
| **TOTAL** | **~1.1 GB** | **$0.022** |

### Month 12 (With Growth)

| Table | Size (12 months) | Cost |
|-------|------------------|------|
| futures_ohlcv_1m | 170 MB | $0.0034 |
| fred_economic | 13.6 MB | $0.0003 |
| alpha_vantage | 1.8 GB | $0.036 |
| weather | 720 MB | $0.014 |
| cftc_positioning | 24 MB | $0.0005 |
| news_sentiment | 1.8 GB | $0.036 |
| Existing data | 700 MB | $0.014 |
| **TOTAL** | **~5.2 GB** | **$0.10** |

**Still under 10 GB free tier** ✅

---

## Part 6: What NOT to Collect

### ❌ Don't Use Yahoo Finance for Futures

**Bad**: `yfinance.download('ZL=F')`
**Why**: Delayed data, gaps, not tick-accurate
**Use Instead**: DataBento ZL

### ❌ Don't Use Alpha Vantage for Primary Prices

**Bad**: Alpha Vantage TIME_SERIES_DAILY for ES
**Why**: Not futures, uses proxies (ETFs), delayed
**Use Instead**: DataBento ES

### ❌ Don't Calculate Technicals from Alpha Vantage

**Bad**: Use Alpha SMA/RSI as primary features
**Why**: We can calculate from DataBento OHLCV (more accurate)
**Use Instead**: Calculate SMA/RSI from DataBento bars, use Alpha for validation

### ❌ Don't Collect Duplicate Price Data

**Bad**: Collecting ZL from both Yahoo and DataBento
**Why**: Wasted storage, conflicting data
**Use Instead**: DataBento only for price data

---

## Part 7: Collection Schedule

### Continuous (During Market Hours)

**DataBento Live Poller**:
```bash
# Every 5 minutes during market hours
*/5 * * * * python3 scripts/live/databento_live_poller.py --roots ES,ZL,CL --once
```

### Every 15 Minutes

**Heavy Data Collection** (multiple sources):
```bash
*/15 * * * * python3 scripts/ingest/collect_fred_comprehensive.py
*/15 * * * * python3 scripts/ingest/collect_alpha_vantage_comprehensive.py
```

### Daily (Morning)

**Weather, USDA, EIA**:
```bash
0 6 * * * python3 scripts/ingest/collect_noaa_comprehensive.py
0 7 * * * python3 scripts/ingest/collect_eia_comprehensive.py
```

### Weekly (Friday)

**CFTC Positioning**:
```bash
0 17 * * 5 python3 scripts/ingest/collect_cftc_comprehensive.py
```

### Every 4-6 Hours

**News Sentiment**:
```bash
0 */6 * * * python3 scripts/ingest/collect_comprehensive_sentiment.py
```

---

## Part 8: Cost Summary (With DataBento Strategy)

### Monthly Data Collection

| Source | API Calls/Month | Data Volume | Cost |
|--------|-----------------|-------------|------|
| DataBento | Unlimited* | 14 MB | $0 (included) |
| FRED | ~1,800 | 0.3 MB | $0 (free) |
| Alpha Vantage | ~1,500 | 150 MB | $75 (Plan75) |
| NOAA | ~900 | 60 MB | $0 (free) |
| USDA | ~80 | 4 MB | $0 (free) |
| CFTC | ~20 | 2 MB | $0 (free) |
| EIA | ~40 | 2 MB | $0 (free) |
| NewsAPI | ~9,000 | 150 MB | $0-50 |
| **TOTAL** | **~13,340** | **~380 MB/month** | **$75-125** |

*DataBento Plan75 includes unlimited API calls for GLBX.MDP3

### BigQuery Costs

| Component | Month 1 | Month 12 |
|-----------|---------|----------|
| Storage | $0.022 (1.1 GB) | $0.10 (5.2 GB) |
| Ingestion | $0 (batch loads FREE) | $0 |
| Queries | $0 (under 1 TB) | $0 |
| **TOTAL** | **$0.02** | **$0.10** |

### GCP VM (e2-micro for DataBento poller)

| Component | Cost |
|-----------|------|
| Compute | $0 (free tier, us-central1) |
| Storage | $0 (< 30 GB) |
| Network | $0 (< 1 GB egress) |
| **TOTAL** | **$0** |

### Grand Total

| Component | Cost |
|-----------|------|
| APIs (DataBento + Alpha) | $75-125/month |
| BigQuery (storage + queries) | $0.02-0.10/month |
| GCP VM | $0/month |
| **TOTAL** | **$75-125/month** |

**BigQuery cost is negligible** (2-10 pennies/month)

---

## Part 9: Verification Checklist

Before uploading to BigQuery, verify:

### DataBento Data
- [ ] All 13 roots collecting successfully
- [ ] No calendar spreads in data (symbol !contains '-')
- [ ] Partitioned Parquet files created (date=YYYY-MM-DD)
- [ ] State tracking working (no duplicate bars)
- [ ] Volume estimate: ~5K bars/day across all symbols

### Domain Data
- [ ] FRED: ~60 series updating daily
- [ ] Alpha Vantage: NOT used for ES/ZL prices (DataBento only)
- [ ] NOAA: Weather data daily
- [ ] CFTC: Weekly positioning data (Friday)
- [ ] No duplicate price collection between sources

### BigQuery Schema
- [ ] Partitioning enabled (DATE column)
- [ ] Clustering configured (root, symbol)
- [ ] Auto-expiration set (365 days for 1m data)
- [ ] MERGE statements for FRED/Alpha/CFTC (not APPEND)
- [ ] APPEND only for DataBento futures

---

## Summary

### Primary Price Source: DataBento

**ALL futures OHLCV data from DataBento**:
- ES, MES, ZL, ZS, ZM, CL, NG, ZC, ZW, RB, HO, GC, SI, HG
- 1-minute bars, GLBX.MDP3 dataset
- ~14 MB/month, $0 cost (included in plan)

### Supplementary Sources

**FRED**: Macro indicators (NOT prices)
**Alpha Vantage**: Technicals for validation (NOT primary features)
**NOAA/USDA/CFTC/EIA**: Domain data
**NewsAPI**: Sentiment

### BigQuery Strategy

**Total storage**: 1.1 GB (Month 1) → 5.2 GB (Month 12)
**Total cost**: $0.02-0.10/month (2-10 pennies)
**Still under free tier**: Yes (< 10 GB)

### Next Steps

1. Review this strategy
2. Confirm DataBento symbols (13 roots OK?)
3. Create BigQuery tables with correct partitioning
4. Set up collection scripts (DataBento priority)
5. Configure MERGE statements for domain data
6. Test end-to-end flow

---

**Questions to Answer**:

1. Do you want all 13 DataBento symbols? Or just Priority 1 (7 symbols)?
2. Should we mirror DataBento to BigQuery? Or keep on external drive only?
3. Which supplementary sources are essential? (FRED, Alpha, Weather, etc.)
4. What's your DataBento plan? (Plan75 includes what?)

