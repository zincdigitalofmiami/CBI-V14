# CBI-V14 Production Data Architecture
**Version**: 1.0  
**Date**: November 18, 2025  
**Status**: Production Specification  
**Purpose**: Complete data collection, schema, and processing architecture

---

## Executive Summary

This is a **production-grade institutional forecasting system** where:
- **Everything is critical** (no "supplementary" data)
- **DataBento is primary** for all available market data
- **Existing systems untouched** (FRED already working)
- **Drivers → Drivers of Drivers → Neural Feeds** all properly architected
- **Regimes locked down** for dates, topics, markets
- **Schema immutable** once deployed

---

## Part 1: Data Source Hierarchy (Validated)

### Tier 1: DataBento (Primary Price & Market Data)

**What DataBento Provides** (GLBX.MDP3 - CME Globex):
- **Futures**: ALL CME/CBOT/NYMEX/COMEX contracts
- **Schemas**: ohlcv-1m, ohlcv-1h, ohlcv-1d, trades, tbbo, mbp-1, mbp-10
- **Symbology**: Parent (.FUT) for continuous, specific contracts
- **Historical**: Back to 2010-06-06
- **Live**: Real-time and delayed feeds

**What DataBento DOES NOT Provide**:
- ❌ FRED economic data (interest rates, inflation, GDP, etc.)
- ❌ Weather data
- ❌ Agricultural reports (USDA)
- ❌ Positioning data (CFTC)
- ❌ Energy inventories (EIA)
- ❌ News sentiment
- ❌ Most forex pairs (futures-based FX only, not spot)

**Verdict**: Use DataBento for ALL futures. Keep FRED/NOAA/USDA/CFTC/EIA as-is.

### Tier 2: FRED (Macro Economic - DO NOT TOUCH)

**Status**: Already working, don't modify
**Coverage**: ~60 economic series
- Interest rates (DFF, DGS10, DGS2, DGS30, DGS5, DGS3MO, DGS1)
- Inflation (CPIAUCSL, CPILFESL, PCEPI)
- Dollar index (DTWEXBGS, DEXBZUS for USD/BRL)
- VIX (VIXCLS)
- Employment, GDP, manufacturing, etc.

**Collection**: Every 15 minutes (current setup)
**BigQuery**: `raw_intelligence.fred_economic` (existing table)

### Tier 3: Domain Data (All Critical)

**NOAA** (Weather - Daily):
- US Midwest (corn/soy belt) - specific stations by area code
- Brazil (soybean production regions) - by state code
- Argentina (soybean production regions) - by province code

**USDA** (Agricultural - Weekly/Monthly):
- Crop reports (weekly)
- Export sales (weekly)
- Harvest progress (weekly during season)
- Grain stocks (quarterly)

**CFTC** (Positioning - 8-hour pulls minimum):
- Commitments of Traders reports
- For: ZL, ZS, ZM, CL, NG, GC, ES, ZC, ZW

**EIA** (Energy - Weekly):
- Petroleum inventory
- Refinery operations  
- Biofuel production
- Natural gas storage

### Tier 4: News & Sentiment (Critical Layer)

**NewsAPI** (Every 1 hour for general, every 15 min for breaking):
- Commodity news
- Policy news
- Trade war news
- Bucketed by topic, regime, correlation

**Alpha Vantage** (Sentiment scoring only):
- News sentiment scores
- Daily aggregates
- **NOT for price data** (brittle, unreliable)

---

## Part 2: Collection Schedule (Production Grade)

### PRIMARY SYMBOLS (5-Minute Pulls)

**Symbols**: ZL, MES, ES
**Frequency**: Every 5 minutes during market hours
**Schema**: ohlcv-1m from DataBento
**Reason**: Most critical for forecasting model

```bash
# Cron: Every 5 minutes, market hours (6 PM - 4 PM CT)
*/5 * * * * python3 scripts/live/databento_live_poller.py --roots ZL,MES,ES --interval 0 --once
```

### SECONDARY SYMBOLS (1-Hour Pulls)

**Symbols**: ZS, ZM, CL, NG, ZC, ZW, RB, HO, GC, SI, HG
**Frequency**: Every 1 hour
**Schema**: ohlcv-1m from DataBento
**Reason**: Important context, less critical than primary

```bash
# Cron: Every hour
0 * * * * python3 scripts/live/databento_live_poller.py --roots ZS,ZM,CL,NG,ZC,ZW,RB,HO,GC,SI,HG --interval 0 --once
```

### FRED (15-Minute Pulls)

**Status**: Already working, don't modify
**Frequency**: Every 15 minutes
**Reason**: Macro indicators update infrequently, 15min is sufficient

```bash
# Existing cron (don't touch)
*/15 * * * * python3 scripts/ingest/collect_fred_comprehensive.py
```

### WEATHER (Daily)

**Frequency**: Daily at 6 AM
**Coverage**:
- **US**: Stations in IL, IN, IA, MN, NE, OH, SD (corn/soy belt)
- **Brazil**: States MG, GO, MT, PR, RS, MS (soybean regions)
- **Argentina**: Provinces Buenos Aires, Santa Fe, Córdoba, Entre Ríos

```bash
# Cron: Daily 6 AM
0 6 * * * python3 scripts/ingest/collect_weather_comprehensive.py --countries US,BR,AR --segment-by-area
```

### CFTC (8-Hour Pulls)

**Frequency**: Every 8 hours (3x daily)
**Reason**: Weekly data, but check for updates/revisions

```bash
# Cron: Every 8 hours
0 */8 * * * python3 scripts/ingest/collect_cftc_comprehensive.py --symbols ZL,ZS,ZM,CL,NG,GC,ES,ZC,ZW
```

### NEWS - GENERAL (1-Hour Pulls)

**Frequency**: Every 1 hour
**Sources**: NewsAPI, Alpha Vantage sentiment
**Topics**: All commodity topics, bucketed and regimed

```bash
# Cron: Every hour
0 * * * * python3 scripts/ingest/collect_news_comprehensive.py --bucket --regime --correlate
```

### NEWS - BREAKING (15-Minute Pulls for Critical Symbols)

**Frequency**: Every 15 minutes
**Symbols**: ZL, ES, CL (critical)
**Reason**: Breaking news needs fast ingestion

```bash
# Cron: Every 15 minutes
*/15 * * * * python3 scripts/ingest/collect_news_breaking.py --symbols ZL,ES,CL --priority critical
```

### USDA/EIA (Weekly)

**Frequency**: Weekly on release days
**USDA**: Thursday 12 PM (export sales), Friday (crop reports)
**EIA**: Wednesday 10:30 AM (petroleum), Thursday (natural gas)

```bash
# Cron: USDA Thursday
0 12 * * 4 python3 scripts/ingest/collect_usda_comprehensive.py

# Cron: EIA Wednesday
30 10 * * 3 python3 scripts/ingest/collect_eia_comprehensive.py
```

---

## Part 3: BigQuery Schema (Locked Down)

### Naming Convention

**Pattern**: `{dataset}.{source}_{datatype}_{frequency}`

**Datasets**:
- `market_data` - All price/market data
- `raw_intelligence` - Domain data (weather, ag, energy, positioning)
- `signals` - Derived signals and indicators
- `regimes` - Regime classifications
- `neural` - Neural network features and outputs
- `drivers` - Primary drivers
- `drivers_of_drivers` - Meta-drivers

### Table 1: `market_data.futures_ohlcv_1m`

**Purpose**: ALL futures 1-minute OHLCV from DataBento
**Partitioning**: `PARTITION BY DATE(ts_event)`
**Clustering**: `CLUSTER BY root, symbol`
**Expiration**: 365 days

```sql
CREATE TABLE market_data.futures_ohlcv_1m (
  ts_event TIMESTAMP NOT NULL,
  root STRING NOT NULL,           -- ZL, ES, CL, etc.
  symbol STRING NOT NULL,          -- ZLZ24, ESH25, etc.
  instrument_id INT64,
  open FLOAT64,
  high FLOAT64,
  low FLOAT64,
  close FLOAT64,
  volume INT64,
  publisher_id INT64,
  priority_tier INT64,             -- 1 (5min), 2 (1hr)
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  regime_id STRING,                -- Link to regime
  topic_id STRING                  -- Link to topic
)
PARTITION BY DATE(ts_event)
CLUSTER BY root, symbol, priority_tier
OPTIONS (
  partition_expiration_days=365,
  description='DataBento futures OHLCV - primary price source'
);
```

### Table 2: `raw_intelligence.fred_economic`

**Purpose**: FRED macro indicators (existing, don't modify schema)
**Partitioning**: `PARTITION BY DATE(date)`
**Clustering**: `CLUSTER BY series_id`

```sql
-- Existing table, keep as-is
-- DO NOT MODIFY
```

### Table 3: `raw_intelligence.weather_segmented`

**Purpose**: Weather data segmented by country and area code
**Partitioning**: `PARTITION BY date`
**Clustering**: `CLUSTER BY country, area_code`

```sql
CREATE TABLE raw_intelligence.weather_segmented (
  date DATE NOT NULL,
  country STRING NOT NULL,         -- US, BR, AR
  area_code STRING NOT NULL,       -- State/province code
  station_id STRING,
  latitude FLOAT64,
  longitude FLOAT64,
  temp_max_f FLOAT64,
  temp_min_f FLOAT64,
  temp_avg_f FLOAT64,
  precip_inches FLOAT64,
  gdd_base50 FLOAT64,              -- Growing degree days
  gdd_base60 FLOAT64,
  soil_moisture_pct FLOAT64,
  regime_id STRING,                -- Drought, flood, normal, etc.
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY country, area_code
OPTIONS (
  description='Weather data segmented by area for all three countries'
);
```

### Table 4: `raw_intelligence.cftc_positioning`

**Purpose**: CFTC Commitments of Traders
**Partitioning**: `PARTITION BY report_date`
**Clustering**: `CLUSTER BY commodity`

```sql
CREATE TABLE raw_intelligence.cftc_positioning (
  report_date DATE NOT NULL,
  commodity STRING NOT NULL,       -- ZL, ZS, CL, etc.
  managed_money_long INT64,
  managed_money_short INT64,
  commercial_long INT64,
  commercial_short INT64,
  nonreportable_long INT64,
  nonreportable_short INT64,
  open_interest INT64,
  net_managed_money INT64,
  net_commercial INT64,
  regime_id STRING,                -- Extreme long, extreme short, balanced
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY report_date
CLUSTER BY commodity
OPTIONS (
  description='CFTC positioning data with regime classification'
);
```

### Table 5: `raw_intelligence.news_bucketed`

**Purpose**: News articles bucketed by topic, regime, correlation
**Partitioning**: `PARTITION BY DATE(published_at)`
**Clustering**: `CLUSTER BY topic_bucket, regime, correlation_group`

```sql
CREATE TABLE raw_intelligence.news_bucketed (
  id STRING NOT NULL,
  published_at TIMESTAMP NOT NULL,
  headline STRING,
  content STRING,
  source STRING,
  topic_bucket STRING NOT NULL,    -- biofuel_policy, china_demand, weather, etc.
  regime STRING NOT NULL,          -- bull, bear, crisis, normal
  correlation_group STRING,        -- zl_soy_complex, crude_energy, macro
  sentiment_score FLOAT64,         -- -1 to 1
  sentiment_confidence FLOAT64,    -- 0 to 1
  impact_symbols ARRAY<STRING>,    -- [ZL, ZS, CL]
  priority STRING,                 -- breaking, normal, background
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(published_at)
CLUSTER BY topic_bucket, regime, correlation_group
OPTIONS (
  description='News bucketed and regimed with sentiment scoring'
);
```

### Table 6: `regimes.market_regimes`

**Purpose**: Regime classifications for all dates
**Partitioning**: `PARTITION BY date`
**Clustering**: `CLUSTER BY regime_type`

```sql
CREATE TABLE regimes.market_regimes (
  date DATE NOT NULL,
  regime_type STRING NOT NULL,     -- market, volatility, positioning, weather, policy
  regime_value STRING NOT NULL,    -- bull, bear, crisis, normal, etc.
  confidence FLOAT64,
  metadata JSON,
  valid_from DATE,
  valid_to DATE
)
PARTITION BY date
CLUSTER BY regime_type, regime_value
OPTIONS (
  description='All regime classifications by date and type'
);
```

### Table 7: `drivers.primary_drivers`

**Purpose**: Primary price drivers (direct factors)
**Partitioning**: `PARTITION BY date`
**Clustering**: `CLUSTER BY driver_type, target_symbol`

```sql
CREATE TABLE drivers.primary_drivers (
  date DATE NOT NULL,
  driver_type STRING NOT NULL,     -- substitution, supply, demand, policy, macro
  driver_name STRING NOT NULL,     -- palm_oil_price, brazil_production, china_demand, etc.
  value FLOAT64,
  target_symbol STRING,            -- ZL, CL, ES
  impact_direction STRING,         -- positive, negative, neutral
  impact_magnitude FLOAT64,        -- 0 to 1
  lag_days INT64,                  -- How many days until impact
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY driver_type, target_symbol
OPTIONS (
  description='Primary drivers with impact direction and magnitude'
);
```

### Table 8: `drivers_of_drivers.meta_drivers`

**Purpose**: Drivers of drivers (second-order factors)
**Partitioning**: `PARTITION BY date`
**Clustering**: `CLUSTER BY primary_driver, meta_driver_type`

```sql
CREATE TABLE drivers_of_drivers.meta_drivers (
  date DATE NOT NULL,
  primary_driver STRING NOT NULL,  -- What driver this affects
  meta_driver_type STRING NOT NULL, -- policy, geopolitical, technology, climate
  meta_driver_name STRING NOT NULL, -- trump_tariff, la_nina, renewable_mandate
  value FLOAT64,
  impact_chain STRING,             -- meta → driver → price
  lag_days INT64,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY primary_driver, meta_driver_type
OPTIONS (
  description='Drivers of drivers with impact chains'
);
```

### Table 9: `signals.calculated_signals`

**Purpose**: Calculated technical signals and indicators
**Partitioning**: `PARTITION BY date`
**Clustering**: `CLUSTER BY symbol, signal_type`

```sql
CREATE TABLE signals.calculated_signals (
  date DATE NOT NULL,
  symbol STRING NOT NULL,
  signal_type STRING NOT NULL,     -- sma, ema, rsi, macd, bollinger, atr, etc.
  signal_name STRING NOT NULL,     -- sma_50, rsi_14, macd_12_26_9
  value FLOAT64,
  parameters JSON,                 -- {period: 50, type: 'simple'}
  regime_adjusted BOOL,            -- Whether adjusted for regime
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY symbol, signal_type
OPTIONS (
  description='Calculated technical signals from OHLCV data'
);
```

### Table 10: `neural.feature_vectors`

**Purpose**: Feature vectors for neural network training
**Partitioning**: `PARTITION BY date`
**Clustering**: `CLUSTER BY symbol, horizon`

```sql
CREATE TABLE neural.feature_vectors (
  date DATE NOT NULL,
  symbol STRING NOT NULL,
  horizon STRING NOT NULL,         -- 1w, 1m, 3m, 6m, 12m
  features JSON NOT NULL,          -- All features as JSON
  regime_id STRING,
  target_value FLOAT64,            -- Actual price for training
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY symbol, horizon
OPTIONS (
  description='Feature vectors for neural network training'
);
```

---

## Part 4: Data Flow Architecture

### Layer 1: Raw Collection

**Input**: External APIs (DataBento, FRED, NOAA, etc.)
**Output**: Raw tables in `market_data` and `raw_intelligence`
**Frequency**: Per collection schedule above
**No processing**: Store as-is

### Layer 2: Regime Classification

**Input**: Raw tables
**Output**: `regimes.market_regimes`
**Frequency**: Hourly
**Processing**:
- Market regime (bull/bear/crisis/normal)
- Volatility regime (high/low)
- Positioning regime (extreme long/short/balanced)
- Weather regime (drought/flood/normal)
- Policy regime (restrictive/neutral/supportive)

```sql
-- Example: Classify market regime from price action
INSERT INTO regimes.market_regimes
SELECT 
  date,
  'market' as regime_type,
  CASE
    WHEN returns_20d > 0.10 THEN 'bull'
    WHEN returns_20d < -0.10 THEN 'bear'
    WHEN volatility_20d > 0.30 THEN 'crisis'
    ELSE 'normal'
  END as regime_value,
  confidence,
  metadata,
  date as valid_from,
  NULL as valid_to
FROM (
  SELECT 
    date,
    symbol,
    (close - LAG(close, 20) OVER (PARTITION BY symbol ORDER BY date)) / LAG(close, 20) OVER (PARTITION BY symbol ORDER BY date) as returns_20d,
    STDDEV(close) OVER (PARTITION BY symbol ORDER BY date ROWS BETWEEN 20 PRECEDING AND CURRENT ROW) / AVG(close) OVER (PARTITION BY symbol ORDER BY date ROWS BETWEEN 20 PRECEDING AND CURRENT ROW) as volatility_20d
  FROM market_data.futures_ohlcv_1d
  WHERE symbol = 'ZL'
)
```

### Layer 3: Driver Identification

**Input**: Raw tables + regimes
**Output**: `drivers.primary_drivers`
**Frequency**: Daily
**Processing**:
- Correlations to identify drivers
- Impact direction (positive/negative)
- Impact magnitude (0-1 scale)
- Lag analysis (how many days)

### Layer 4: Meta-Driver Identification

**Input**: Primary drivers + regimes
**Output**: `drivers_of_drivers.meta_drivers`
**Frequency**: Daily
**Processing**:
- Second-order correlations
- Policy impact chains
- Geopolitical impact chains

### Layer 5: Signal Calculation

**Input**: Raw OHLCV + regimes
**Output**: `signals.calculated_signals`
**Frequency**: Hourly (for 1m data), Daily (for 1d data)
**Processing**:
- Technical indicators (SMA, RSI, MACD, etc.)
- Regime-adjusted signals
- Cross-asset signals

### Layer 6: Feature Vector Assembly

**Input**: All layers above
**Output**: `neural.feature_vectors`
**Frequency**: Daily
**Processing**:
- Combine all features into vectors
- Normalize/scale features
- Add regime context
- Add targets for training

---

## Part 5: View Layer (For Dashboard & Training)

### View 1: `signals.vw_zl_comprehensive`

**Purpose**: All data for ZL in one view

```sql
CREATE VIEW signals.vw_zl_comprehensive AS
SELECT 
  p.date,
  p.close as zl_close,
  s.value as sma_50,
  r.regime_value as market_regime,
  d.value as palm_oil_substitute,
  dd.value as trump_tariff_impact,
  w.temp_avg_f as brazil_temp,
  c.net_managed_money as cftc_positioning,
  n.sentiment_score as news_sentiment
FROM market_data.futures_ohlcv_1d p
LEFT JOIN signals.calculated_signals s ON p.date = s.date AND s.symbol = 'ZL' AND s.signal_name = 'sma_50'
LEFT JOIN regimes.market_regimes r ON p.date = r.date AND r.regime_type = 'market'
LEFT JOIN drivers.primary_drivers d ON p.date = d.date AND d.driver_name = 'palm_oil_price'
LEFT JOIN drivers_of_drivers.meta_drivers dd ON p.date = dd.date AND dd.meta_driver_name = 'trump_tariff'
LEFT JOIN raw_intelligence.weather_segmented w ON p.date = w.date AND w.country = 'BR'
LEFT JOIN raw_intelligence.cftc_positioning c ON p.date = c.report_date AND c.commodity = 'ZL'
LEFT JOIN (
  SELECT DATE(published_at) as date, AVG(sentiment_score) as sentiment_score
  FROM raw_intelligence.news_bucketed
  WHERE 'ZL' IN UNNEST(impact_symbols)
  GROUP BY date
) n ON p.date = n.date
WHERE p.symbol = 'ZL';
```

---

## Part 6: Critical Implementation Notes

### DO NOT TOUCH

1. **FRED collection scripts** - Already working
2. **Existing BigQuery tables** - Migrate data, don't break

### MUST IMPLEMENT

1. **Regime classification** - Automated, daily
2. **News bucketing** - By topic, regime, correlation
3. **Weather segmentation** - By area code
4. **Driver identification** - Correlation analysis
5. **Meta-driver tracking** - Impact chains
6. **Signal calculation** - From OHLCV data
7. **Feature vector assembly** - For neural networks

### TRIPLE-CHECK BEFORE DEPLOYING

1. **DataBento symbols** - Verify all 13 available
2. **DataBento schemas** - Confirm GLBX.MDP3 access
3. **Collection frequencies** - Match requirements (5min primary, 1hr secondary)
4. **Schema partitioning** - All tables partitioned by date
5. **Regime classification** - Tested and validated
6. **News bucketing logic** - Properly segmented
7. **Weather area codes** - Correct mapping for all 3 countries

---

## Part 7: Cost Projection (Updated)

### Storage (Month 12)

| Table | Size | Cost |
|-------|------|------|
| futures_ohlcv_1m (primary 5min) | 50 MB | $0.001 |
| futures_ohlcv_1m (secondary 1hr) | 100 MB | $0.002 |
| fred_economic | 14 MB | $0.0003 |
| weather_segmented | 180 MB | $0.004 |
| cftc_positioning | 24 MB | $0.0005 |
| news_bucketed | 2.0 GB | $0.040 |
| market_regimes | 50 MB | $0.001 |
| primary_drivers | 100 MB | $0.002 |
| meta_drivers | 50 MB | $0.001 |
| calculated_signals | 500 MB | $0.010 |
| feature_vectors | 1.0 GB | $0.020 |
| **TOTAL** | **~4.0 GB** | **$0.08** |

**Still under 10 GB free tier** ✅

---

## Summary

**Primary Symbols** (ZL, MES, ES): 5-minute collection
**Secondary Symbols** (11 others): 1-hour collection
**FRED**: Keep as-is (already working)
**Weather**: Daily, all 3 countries, segmented by area
**CFTC**: 8-hour pulls minimum
**News**: 1-hour general, 15-min breaking for critical symbols
**Schema**: Locked down, regimed, correlated
**Layers**: Raw → Regimes → Drivers → Meta-Drivers → Signals → Features
**Cost**: $0.08/month (BigQuery storage only)

**Next**: Create implementation scripts for each layer


