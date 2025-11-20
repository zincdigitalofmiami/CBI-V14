# FX Calculations: Before or After BigQuery?

**Date:** November 20, 2025  
**Question:** Should FX calculations happen before or after data goes through BigQuery?  
**Answer:** **AFTER BigQuery** (or hybrid: simple features before, complex features after)

---

## 🎯 EXECUTIVE SUMMARY

**Recommended Approach:**
1. **Raw FX data** → Load to BigQuery `market_data` dataset
2. **Simple technical indicators** → Can be done in Python (before BQ) OR BigQuery SQL
3. **Cross-currency correlations** → **MUST be in BigQuery** (needs all FX pairs)
4. **ZL-FX correlations** → **MUST be in BigQuery** (needs ZL + FX data together)

**Why After BigQuery:**
- ZL-FX correlations require ZL price data (already in BigQuery)
- Cross-currency correlations need all FX pairs (better in BigQuery)
- BigQuery is optimized for large joins and rolling calculations
- Architecture plan says "Curate in BQ"

---

## 📊 DATA FLOW ANALYSIS

### Current Flow (From Scripts):
```
Databento/FRED APIs
    ↓
Local Parquet files (raw)
    ↓
Python: build_forex_features.py
    ↓
Local Parquet files (staging/forex_features.parquet)
    ↓
BigQuery? (unclear)
```

### Recommended Flow (BigQuery-Centric):
```
Databento/FRED APIs
    ↓
BigQuery: market_data.databento_futures_ohlcv_1m
BigQuery: market_data.fred_economic_indicators
    ↓
BigQuery SQL: Calculate FX features
    ↓
BigQuery: features.forex_features
    ↓
BigQuery: features.master_features (join with ZL)
    ↓
Export to Parquet for training
```

---

## 🔍 DETAILED BREAKDOWN

### 1. Technical Indicators (Per Currency)

**Examples:**
- RSI (7, 14 periods)
- MACD (Line, Signal, Histogram)
- Moving Averages (SMA/EMA: 5, 10, 20, 50, 100)
- Bollinger Bands
- ATR (14 period)
- Returns (1d, 7d, 30d)
- Volatility (5, 10, 20, 30-day)

**When to Calculate:**
- ✅ **Can be done BEFORE BigQuery** (Python script)
- ✅ **Can be done IN BigQuery** (SQL window functions)
- ✅ **Recommendation:** Do in BigQuery SQL (consistent with architecture)

**Why:**
- Single currency, no dependencies
- Window functions work well in BigQuery
- Keeps raw data clean, features separate

---

### 2. Cross-Currency Correlations

**Examples:**
- 30-day rolling correlations between all FX pairs
- 90-day rolling correlations between all FX pairs
- Currency strength index (weighted average)

**When to Calculate:**
- ❌ **Cannot be done BEFORE BigQuery** (needs all currencies)
- ✅ **MUST be done IN BigQuery** (needs all FX pairs together)

**Why:**
- Requires joining multiple currency tables
- Rolling correlations across currencies
- Better performance in BigQuery for large joins

**SQL Example:**
```sql
-- Calculate 30-day rolling correlation between BRL and CNY
SELECT 
  date,
  CORR(fx_6l_return, fx_cnh_return) OVER (
    PARTITION BY date 
    ORDER BY date 
    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
  ) as fx_corr_6l_cnh_30d
FROM features.forex_features
```

---

### 3. ZL-FX Correlations (CRITICAL)

**Examples:**
- ZL-BRL correlation (30d, 90d rolling)
- ZL-CNY correlation (30d, 90d rolling)
- ZL-EUR correlation (30d, 90d rolling)
- ZL-USD Index correlation (30d, 90d rolling)

**When to Calculate:**
- ❌ **Cannot be done BEFORE BigQuery** (needs ZL data)
- ✅ **MUST be done IN BigQuery** (needs ZL + FX together)

**Why:**
- Requires ZL price data (already in BigQuery)
- Requires FX data (in BigQuery)
- Must join ZL and FX tables
- Critical for export competitiveness analysis

**Current Script Issue:**
```python
# From build_forex_features.py line 197:
if 'zl_close' not in df.columns:
    logger.warning("⚠️  ZL price data not found, skipping ZL-FX correlations")
```

**Solution:**
- Load ZL data to BigQuery
- Load FX data to BigQuery
- Calculate correlations in BigQuery SQL (join both tables)

---

### 4. FX Impact Features

**Examples:**
- `fx_brl_impact_score` = BRL return × ZL-BRL correlation
- `fx_cny_impact_score` = CNY return × ZL-CNY correlation
- USD strength index

**When to Calculate:**
- ❌ **Cannot be done BEFORE BigQuery** (needs correlations)
- ✅ **MUST be done IN BigQuery** (depends on ZL-FX correlations)

**Why:**
- Depends on ZL-FX correlations (calculated in BigQuery)
- Simple multiplication, but needs correlation data

---

### 5. Currency Spreads & Ratios

**Examples:**
- BRL-CNY spread: `fx_spread_brl_cny` = BRL - CNY
- EUR-USD spread: `fx_spread_eur_usd` = EUR - USD
- Currency ratios: `fx_ratio_{currency1}_{currency2}`

**When to Calculate:**
- ✅ **Can be done BEFORE BigQuery** (if all currencies in one file)
- ✅ **Can be done IN BigQuery** (join currencies, calculate)

**Why:**
- Simple arithmetic operations
- Works either way
- Recommendation: Do in BigQuery (consistent with architecture)

---

### 6. FX Regime Features

**Examples:**
- FX volatility regime (Low/Normal/High/Crisis)
- FX trend regime (Bullish/Bearish/Neutral)
- FX correlation regime

**When to Calculate:**
- ✅ **Can be done BEFORE BigQuery** (if all data available)
- ✅ **Can be done IN BigQuery** (better for historical analysis)

**Why:**
- Requires historical data analysis
- Better in BigQuery for time-series analysis
- Recommendation: Do in BigQuery

---

## 🏗️ RECOMMENDED ARCHITECTURE

### Phase 1: Load Raw Data to BigQuery

```python
# scripts/ingest/collect_databento_forex.py
# Collects FX data → Saves to local Parquet
# Then: Load to BigQuery

from google.cloud import bigquery

client = bigquery.Client(project='cbi-v14')
table_ref = client.dataset('market_data').table('databento_futures_ohlcv_1m')

# Load Parquet to BigQuery
job = client.load_table_from_dataframe(df, table_ref)
```

### Phase 2: Calculate Features in BigQuery

**Option A: BigQuery SQL (RECOMMENDED)**
```sql
-- features/forex_features.sql
CREATE OR REPLACE TABLE `cbi-v14.features.forex_features` AS
WITH fx_returns AS (
  SELECT 
    date,
    root,
    symbol,
    close,
    LAG(close) OVER (PARTITION BY symbol ORDER BY date) as prev_close,
    (close - LAG(close) OVER (PARTITION BY symbol ORDER BY date)) / 
      LAG(close) OVER (PARTITION BY symbol ORDER BY date) as return_1d
  FROM `cbi-v14.market_data.databento_futures_ohlcv_1m`
  WHERE root IN ('6L', '6E', '6J', '6C', '6B', '6A', 'CNH')
),
fx_indicators AS (
  SELECT 
    date,
    symbol,
    close,
    return_1d,
    -- RSI
    RSI(close, 14) OVER (PARTITION BY symbol ORDER BY date) as fx_rsi_14,
    -- Moving averages
    AVG(close) OVER (PARTITION BY symbol ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as fx_sma_20,
    -- Volatility
    STDDEV(return_1d) OVER (PARTITION BY symbol ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as fx_vol_30d
  FROM fx_returns
)
SELECT * FROM fx_indicators
```

**Option B: Python (if complex logic needed)**
```python
# scripts/features/build_forex_features_bq.py
# Export from BigQuery → Calculate → Load back
```

### Phase 3: ZL-FX Correlations in BigQuery

```sql
-- features/zl_fx_correlations.sql
CREATE OR REPLACE TABLE `cbi-v14.features.zl_fx_correlations` AS
WITH zl_returns AS (
  SELECT 
    date,
    close as zl_close,
    (close - LAG(close) OVER (ORDER BY date)) / LAG(close) OVER (ORDER BY date) as zl_return
  FROM `cbi-v14.market_data.databento_futures_ohlcv_1m`
  WHERE root = 'ZL' AND symbol = 'ZL=F'
),
fx_returns AS (
  SELECT 
    date,
    symbol,
    close,
    (close - LAG(close) OVER (PARTITION BY symbol ORDER BY date)) / 
      LAG(close) OVER (PARTITION BY symbol ORDER BY date) as fx_return
  FROM `cbi-v14.market_data.databento_futures_ohlcv_1m`
  WHERE root IN ('6L', '6E', 'CNH')
)
SELECT 
  z.date,
  z.zl_return,
  f.symbol,
  f.fx_return,
  CORR(z.zl_return, f.fx_return) OVER (
    PARTITION BY f.symbol 
    ORDER BY z.date 
    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
  ) as cross_corr_fx_30d
FROM zl_returns z
JOIN fx_returns f ON z.date = f.date
```

---

## ✅ FINAL RECOMMENDATION

### Do FX Calculations **AFTER BigQuery**:

1. **Load raw FX data to BigQuery** (`market_data` dataset)
2. **Calculate simple features in BigQuery SQL** (RSI, MACD, moving averages)
3. **Calculate cross-currency correlations in BigQuery** (needs all FX pairs)
4. **Calculate ZL-FX correlations in BigQuery** (needs ZL + FX together)
5. **Join with ZL data in BigQuery** (`features.master_features`)
6. **Export to Parquet for training**

### Why This Approach:

✅ **ZL-FX correlations require ZL data** (already in BigQuery)  
✅ **Cross-currency correlations need all FX pairs** (better in BigQuery)  
✅ **BigQuery optimized for large joins** (better performance)  
✅ **Consistent with architecture plan** ("Curate in BQ")  
✅ **Single source of truth** (all features in BigQuery)  
✅ **Easier to maintain** (SQL vs Python scripts)  

### Migration Path:

1. **Keep current Python scripts** for historical backfill
2. **Create BigQuery SQL equivalents** for live feeds
3. **Run both in parallel** during transition
4. **Switch to BigQuery-only** once validated

---

## 📋 ACTION ITEMS

1. ✅ Load raw FX data to BigQuery `market_data` dataset
2. 🚧 Create BigQuery SQL for simple FX features (RSI, MACD, etc.)
3. 🚧 Create BigQuery SQL for cross-currency correlations
4. 🚧 Create BigQuery SQL for ZL-FX correlations (join ZL + FX)
5. 🚧 Create `features.forex_features` table in BigQuery
6. 🚧 Update `features.master_features` to include FX features
7. 🚧 Update export scripts to pull from BigQuery

---

## 📄 RELATED FILES

- `docs/features/FX_CALCULATIONS_REQUIRED.md` - FX requirements
- `docs/plans/BIGQUERY_LIVE_FEEDS_ARCHITECTURE_PLAN.md` - Architecture
- `scripts/features/build_forex_features.py` - Current Python script
- `docs/plans/BIGQUERY_MIGRATION_PLAN.md` - Migration strategy

---

**Last Updated:** November 20, 2025

