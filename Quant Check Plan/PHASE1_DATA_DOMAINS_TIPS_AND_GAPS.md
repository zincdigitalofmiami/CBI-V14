# Phase 1 Data Domains: Tips, Gaps & Simplifications
**Date:** November 24, 2025 (Updated with Databento/Palm/VIX Intel)  
**Purpose:** Review spec against existing CBI-V14 infrastructure, identify gaps, and simplify where possible

---

## 🎯 EXECUTIVE SUMMARY

The spec is **solid** but can be simplified for Phase 1. Key points:

1. **Weather**: Use BigQuery Public Datasets (FREE) + ERA5-Land for gaps
2. **VIX/Vol**: **NO DIRECT VIX** - Use FRED proxies + Databento options implied vol
3. **Logistics**: BDI script exists but needs real API (not mock data)
4. **FX**: ✅ **Loaded from FRED** (DEXBZUS, DEXCHUS, DEXJPUS, DEXUSEU, DTWEXBGS) - calculate derived features
5. **Palm Oil**: Add CME CPO futures (USD cash-settled) + Indonesia/Malaysia policy signals
6. **Special Calcs**: Most already exist in scripts - just wire to BQ

### 🔴 CRITICAL UPDATE: NO VIX DATA AVAILABLE
We will **never have direct VIX data**. Must use:
- FRED volatility proxies (VXOCLS, BAMLH0A0HYM2)
- **Databento options data** → calculate implied volatility ourselves
- Realized volatility from ZL/ES futures

---

## 1. WEATHER & CLIMATE

### ✅ WHAT WE HAVE
- `scripts/fetch_weather_data.py` - NOAA CDO API framework (needs token)
- `ingestion/ingest_midwest_weather_openmeteo.py` - Alternative source
- NOAA API key: `rxoLrCxYOlQyWvVjbBGRlMMhIRElWKZi`
- Google Weather API: ✅ ENABLED

### ⚠️ SPEC SUGGESTIONS VS REALITY

| Spec Suggestion | Reality | Recommendation |
|-----------------|---------|----------------|
| **Weather Source (paid)** | $$$, requires contract | ❌ SKIP for Phase 1 |
| **NOAA Storm Events** | FREE in BQ Public Data | ✅ USE THIS |
| **Earth Engine Rasters** | Complex setup | ⏸️ Defer to Phase 2 |
| **NOAA GSOD/GHCN** | FREE in BQ Public Data | ✅ USE THIS |

### 🔧 SIMPLIFIED PHASE 1 WEATHER

**Use BigQuery Public Datasets (FREE):**

```sql
-- NOAA GSOD (Global Surface Summary of Day) - FREE
SELECT 
    DATE(year, mo, da) AS date,
    stn AS station_id,
    temp AS avg_temp_f,
    dewp AS dewpoint_f,
    prcp AS precipitation_in,
    max AS max_temp_f,
    min AS min_temp_f
FROM `bigquery-public-data.noaa_gsod.gsod*`
WHERE _TABLE_SUFFIX BETWEEN '2010' AND '2025'
  AND stn IN (
    -- US Midwest stations (Iowa, Illinois, Indiana, Nebraska, Minnesota)
    '725460', '725300', '724320', '725500', '726580'  -- Example station IDs
  )
```

```sql
-- NOAA Storm Events - FREE
SELECT 
    begin_date_time,
    state,
    event_type,
    damage_property,
    damage_crops
FROM `bigquery-public-data.noaa_historic_severe_storms.storms_*`
WHERE state IN ('IOWA', 'ILLINOIS', 'INDIANA', 'NEBRASKA', 'MINNESOTA')
  AND event_type IN ('Drought', 'Flood', 'Flash Flood', 'Hail', 'Tornado')
```

### 🎯 PHASE 1 WEATHER FEATURES (Keep Simple)

| Feature | Source | Calculation |
|---------|--------|-------------|
| `temp_anom_7d` | GSOD | `(avg_temp_7d - clim_mean) / clim_std` |
| `precip_anom_7d` | GSOD | Same z-score approach |
| `gdd_30d` | GSOD | `SUM(MAX(0, ((max+min)/2) - 50))` (F base) |
| `drought_events_30d` | Storm Events | `COUNT(*)` where event_type = 'Drought' |
| `flood_events_30d` | Storm Events | `COUNT(*)` where event_type IN ('Flood', 'Flash Flood') |

**Skip for Phase 1:**
- Earth Engine rasters
- Soil moisture (requires SMAP data)
- Brazil/Argentina weather (complex station mapping)

---

## 2. FX & RATES

### ✅ WHAT WE HAVE
- **FRED (Primary Source):** ✅ DEXUSEU (EUR/USD), DEXCHUS (USD/CNY), DEXBZUS (USD/BRL), DEXJPUS (USD/JPY), DTWEXBGS (Dollar Index) - All loaded (2010-2025)
- **FRED:** Fed Funds (DFF), 10Y Treasury (DGS10), CPI, GDP
- **Databento (Optional):** 6E, 6J, 6B futures (for additional granularity, not required)
- FRED API key: `dc195c8658c46ee1df83bcd4fd8a690b`
- `scripts/collect_fred_data.py` - Already implemented

### ⚠️ SPEC VS REALITY

| Spec Suggestion | What We Have | Gap? |
|-----------------|--------------|------|
| FX log returns | **FRED FX series** | ✅ Calculate from FRED close |
| Realized vol | **FRED FX series** | ✅ Calculate in BQ from FRED |
| Carry/basis | FRED rates | ✅ Approximate from DFF |
| BRL pressure index | **FRED DEXBZUS** | ✅ Can calculate from FRED |
| Curve slope | FRED DGS10, DFF | ✅ Already available |
| USD/JPY | **FRED DEXJPUS** | ✅ Loaded |
| EUR/USD | **FRED DEXUSEU** | ✅ Loaded |
| USD/CNY | **FRED DEXCHUS** | ✅ Loaded |
| Dollar Index | **FRED DTWEXBGS** | ✅ Loaded |

### 🔧 SIMPLIFIED PHASE 1 FX CALCULATIONS

```sql
-- FX Features from FRED (raw_intelligence.fred_economic)
WITH fx_base AS (
    SELECT 
        date,
        series_id,
        value AS close,
        LN(value / LAG(value) OVER (PARTITION BY series_id ORDER BY date)) AS fx_ret_1d
    FROM raw_intelligence.fred_economic
    WHERE series_id IN ('DEXBZUS', 'DEXCHUS', 'DEXJPUS', 'DEXUSEU', 'DTWEXBGS')
)
SELECT 
    date,
    symbol,
    fx_ret_1d,
    SQRT(252) * STDDEV(fx_ret_1d) OVER (
        PARTITION BY symbol ORDER BY date ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
    ) AS fx_realized_vol_10d,
    SQRT(252) * STDDEV(fx_ret_1d) OVER (
        PARTITION BY symbol ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) AS fx_realized_vol_20d
FROM fx_base
```

```sql
-- Soy FX Stress Index (composite)
WITH fx_zscores AS (
    SELECT 
        date,
        (usdbrl - AVG(usdbrl) OVER w60) / NULLIF(STDDEV(usdbrl) OVER w60, 0) AS z_usdbrl,
        (usdcny - AVG(usdcny) OVER w60) / NULLIF(STDDEV(usdcny) OVER w60, 0) AS z_usdcny,
        (dxy - AVG(dxy) OVER w60) / NULLIF(STDDEV(dxy) OVER w60, 0) AS z_dxy
    FROM staging.fx_daily_pivot
    WINDOW w60 AS (ORDER BY date ROWS BETWEEN 59 PRECEDING AND CURRENT ROW)
)
SELECT 
    date,
    0.5 * z_usdbrl + 0.5 * z_usdcny - 0.3 * z_dxy AS soy_fx_stress
FROM fx_zscores
```

### 🎯 PHASE 1 FX FEATURES

| Feature | Source | Priority |
|---------|--------|----------|
| `fx_ret_1d` | **FRED** | ✅ HIGH |
| `fx_realized_vol_10d` | Calculated | ✅ HIGH |
| `fx_realized_vol_20d` | Calculated | ✅ HIGH |
| `soy_fx_stress` | Composite | ✅ HIGH |
| `curve_slope` | FRED | ✅ HIGH |
| `curve_inversion_flag` | FRED | ✅ HIGH |
| `rate_level` | FRED | ✅ HIGH |

**Skip for Phase 1:**
- Carry/basis (need short rates for multiple countries)
- FX term structure (need futures curve data)

---

## 3. VOLATILITY: NO VIX - USE ALTERNATIVES

### 🔴 CRITICAL: WE WILL NEVER HAVE VIX DATA
Must build volatility signals from:
1. **FRED proxies** (credit spreads, bond vol)
2. **Databento options** → calculate implied vol ourselves
3. **Realized volatility** from futures prices

### ✅ WHAT WE CAN USE

| Source | Data | How to Get |
|--------|------|------------|
| **FRED** | BAMLH0A0HYM2 (High Yield Spread) | API - proxy for risk sentiment |
| **FRED** | TEDRATE (TED Spread) | API - credit stress proxy |
| **FRED** | T10Y2Y (Yield Curve) | API - recession/risk proxy |
| **Databento** | ZL Options (GLBX.MDP3) | Calculate IV from option prices |
| **Databento** | ES Options | Calculate IV for market vol proxy |
| **Calculated** | ZL Realized Vol | From ZL futures prices |

### 🔧 VOLATILITY ALTERNATIVES (Phase 1)

#### Option 1: FRED Risk Proxies (Easiest)
```sql
-- Risk/Volatility Proxies from FRED
SELECT 
    date,
    -- High Yield Spread (risk appetite proxy)
    MAX(CASE WHEN indicator = 'BAMLH0A0HYM2' THEN value END) AS hy_spread,
    -- TED Spread (credit stress)
    MAX(CASE WHEN indicator = 'TEDRATE' THEN value END) AS ted_spread,
    -- Yield Curve (recession signal)
    MAX(CASE WHEN indicator = 'T10Y2Y' THEN value END) AS yield_curve_slope
FROM staging.fred_macro_clean
WHERE indicator IN ('BAMLH0A0HYM2', 'TEDRATE', 'T10Y2Y')
GROUP BY date
```

```sql
-- Composite Risk Index (VIX alternative)
WITH risk_base AS (
    SELECT 
        date,
        hy_spread,
        ted_spread,
        yield_curve_slope
    FROM staging.fred_risk_proxies
)
SELECT 
    date,
    -- Z-score each component
    (hy_spread - AVG(hy_spread) OVER w60) / NULLIF(STDDEV(hy_spread) OVER w60, 0) AS z_hy_spread,
    (ted_spread - AVG(ted_spread) OVER w60) / NULLIF(STDDEV(ted_spread) OVER w60, 0) AS z_ted_spread,
    -- Composite (higher = more risk)
    0.5 * z_hy_spread + 0.3 * z_ted_spread + 0.2 * ABS(yield_curve_slope) AS risk_sentiment_index
FROM risk_base
WINDOW w60 AS (ORDER BY date ROWS BETWEEN 59 PRECEDING AND CURRENT ROW)
```

#### Option 2: Realized Volatility from Databento (Best)
```sql
-- ZL Realized Volatility (our best vol signal)
WITH zl_returns AS (
    SELECT 
        date,
        LN(close / LAG(close) OVER (ORDER BY date)) AS log_return
    FROM staging.market_daily
    WHERE symbol = 'ZL'
)
SELECT 
    date,
    -- Annualized realized vol
    SQRT(252) * STDDEV(log_return) OVER w10 AS zl_realized_vol_10d,
    SQRT(252) * STDDEV(log_return) OVER w21 AS zl_realized_vol_21d,
    SQRT(252) * STDDEV(log_return) OVER w63 AS zl_realized_vol_63d,
    -- Vol regime
    CASE 
        WHEN SQRT(252) * STDDEV(log_return) OVER w21 > 0.30 THEN 'HIGH'
        WHEN SQRT(252) * STDDEV(log_return) OVER w21 < 0.15 THEN 'LOW'
        ELSE 'NORMAL'
    END AS vol_regime
FROM zl_returns
WINDOW 
    w10 AS (ORDER BY date ROWS BETWEEN 9 PRECEDING AND CURRENT ROW),
    w21 AS (ORDER BY date ROWS BETWEEN 20 PRECEDING AND CURRENT ROW),
    w63 AS (ORDER BY date ROWS BETWEEN 62 PRECEDING AND CURRENT ROW)
```

#### Option 3: Implied Vol from Databento Options (Advanced)
```python
# Calculate IV from ZL options (Databento GLBX.MDP3)
# Options data available back to 2010 (legacy) and full MBO from 2017

def calculate_implied_vol(option_price, spot, strike, time_to_expiry, rate=0.05, option_type='call'):
    """
    Black-Scholes implied volatility via Newton-Raphson
    Use Databento options data: OZL (Soybean Oil Options)
    """
    from scipy.optimize import brentq
    from scipy.stats import norm
    import numpy as np
    
    def bs_price(vol):
        d1 = (np.log(spot/strike) + (rate + 0.5*vol**2)*time_to_expiry) / (vol*np.sqrt(time_to_expiry))
        d2 = d1 - vol*np.sqrt(time_to_expiry)
        if option_type == 'call':
            return spot*norm.cdf(d1) - strike*np.exp(-rate*time_to_expiry)*norm.cdf(d2)
        else:
            return strike*np.exp(-rate*time_to_expiry)*norm.cdf(-d2) - spot*norm.cdf(-d1)
    
    try:
        iv = brentq(lambda v: bs_price(v) - option_price, 0.001, 5.0)
        return iv
    except:
        return None

# Pull ATM options from Databento, calculate IV daily
# This gives us ZL-specific implied volatility
```

### 🎯 PHASE 1 VOLATILITY FEATURES (No VIX Required)

| Feature | Source | Priority |
|---------|--------|----------|
| `zl_realized_vol_21d` | Databento ZL | ✅ HIGH |
| `zl_realized_vol_63d` | Databento ZL | ✅ HIGH |
| `vol_regime` | Calculated | ✅ HIGH |
| `risk_sentiment_index` | FRED proxies | ✅ HIGH |
| `z_hy_spread` | FRED | ✅ MEDIUM |
| `yield_curve_slope` | FRED | ✅ MEDIUM |
| `zl_implied_vol_atm` | Databento options | 🟡 Phase 2 |

### 📊 FRED SERIES TO ADD (Volatility Proxies)

```python
# Add to FRED pull script
FRED_VOL_PROXIES = {
    'BAMLH0A0HYM2': 'hy_spread',           # High Yield OAS
    'BAMLC0A0CM': 'ig_spread',              # Investment Grade OAS
    'TEDRATE': 'ted_spread',                # TED Spread
    'T10Y2Y': 'yield_curve_slope',          # 10Y-2Y Spread
    'T10Y3M': 'yield_curve_3m',             # 10Y-3M Spread
    'DTWEXBGS': 'trade_weighted_usd',       # Trade-weighted USD
}
```

---

## 4. LOGISTICS & SHIPPING

### ✅ WHAT WE HAVE
- `ingestion/ingest_baltic_dry_index.py` - **EXISTS but uses MOCK DATA**
- `ingestion/ingest_argentina_port_logistics.py` - Scraper for Argentina ports
- `ingestion/ingest_port_congestion.py` - Port congestion scraper

### ⚠️ CRITICAL ISSUE: BDI SCRIPT USES MOCK DATA

The `ingest_baltic_dry_index.py` script has:
```python
# Mock data structure for now
mock_data = {
    'date': datetime.now().date(),
    'bdi_value': 1250 + (datetime.now().hour * 10),  # Mock BDI value
```

**This is FAKE DATA - needs real API!**

### 🔧 REAL BDI DATA OPTIONS

1. **FRED** - Has BDI historical: `https://fred.stlouisfed.org/series/BDILCY`
2. **Investing.com** - Free but requires scraping
3. **TradingEconomics** - API (may need subscription)

```python
# Add to FRED pull (FREE!)
FRED_SERIES = {
    'BDILCY': 'baltic_dry_index',  # Baltic Dry Index
    'DCOILWTICO': 'wti_crude',     # WTI Crude (for logistics cost proxy)
}
```

### 🎯 PHASE 1 LOGISTICS FEATURES (Simplified)

| Feature | Source | Priority |
|---------|--------|----------|
| `bdi_value` | FRED BDILCY | ✅ HIGH |
| `bdi_z_30d` | Calculated | ✅ HIGH |
| `bdi_change_pct` | Calculated | ✅ MEDIUM |

**Skip for Phase 1:**
- Storm-based disruption (complex geo matching)
- Port-specific events (requires scraping)
- Panama Canal data (no easy API)

**Composite Index (Simplified):**
```sql
-- Phase 1: Just use BDI z-score
SELECT 
    date,
    bdi_value,
    (bdi_value - AVG(bdi_value) OVER w30) / NULLIF(STDDEV(bdi_value) OVER w30, 0) AS logistics_pressure_global
FROM staging.baltic_dry_index
WINDOW w30 AS (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW)
```

---

## 5. PALM OIL INTELLIGENCE (Critical for ZL)

### 🔴 WHY PALM OIL MATTERS
- **Substitution channel**: ZL tracks FCPO tightly (buyers can switch)
- **Indonesia disruption risk**: 3.7M hectares seized by government task force
- **Malaysia futures pressure**: Weak exports, rising inventories
- **Direct ZL impact**: Palm supply shocks ripple into soybean oil demand

### ✅ WHAT WE CAN USE

| Source | Data | Access |
|--------|------|--------|
| **CME CPO Futures** | USD cash-settled Malaysian Crude Palm Oil | Databento GLBX.MDP3 |
| **Databento** | FCPO proxy via CME | Contract code: CPO |
| **News Signals** | Indonesia/Malaysia policy events | Crawlers (see Section 8) |

### 🔧 PALM OIL DATA FROM DATABENTO

```python
# CME Palm Oil Futures (USD cash-settled)
# Available in GLBX.MDP3 dataset

PALM_OIL_SYMBOLS = {
    'CPO': 'CME USD Palm Oil Futures',  # Cash-settled vs FCPO
}

# Pull from Databento
import databento as db
client = db.Historical()

# Daily OHLCV for palm oil
palm_data = client.timeseries.get_range(
    dataset='GLBX.MDP3',
    symbols=['CPO'],
    stype_in='parent',  # Continuous front-month
    schema='ohlcv-1d',
    start='2010-06-06',
    end='2025-11-24'
)
```

### 🎯 PALM OIL FEATURES

| Feature | Calculation | Priority |
|---------|-------------|----------|
| `cpo_close` | Databento CPO | ✅ HIGH |
| `cpo_return_1d` | LN(close/lag) | ✅ HIGH |
| `zl_cpo_spread` | ZL - CPO (normalized) | ✅ HIGH |
| `zl_cpo_corr_60d` | Rolling correlation | ✅ HIGH |
| `palm_substitution_pressure` | When CPO < ZL, buyers switch | ✅ HIGH |

```sql
-- Palm Oil Features
WITH palm_base AS (
    SELECT 
        date,
        MAX(CASE WHEN symbol = 'ZL' THEN close END) AS zl_close,
        MAX(CASE WHEN symbol = 'CPO' THEN close END) AS cpo_close
    FROM staging.market_daily
    WHERE symbol IN ('ZL', 'CPO')
    GROUP BY date
)
SELECT 
    date,
    zl_close,
    cpo_close,
    zl_close - cpo_close AS zl_cpo_spread,
    -- Substitution pressure: when CPO cheaper, buyers may switch away from ZL
    CASE 
        WHEN cpo_close < zl_close * 0.85 THEN 'HIGH_PALM_PRESSURE'
        WHEN cpo_close < zl_close * 0.95 THEN 'MODERATE_PALM_PRESSURE'
        ELSE 'LOW_PALM_PRESSURE'
    END AS palm_substitution_regime,
    -- Rolling correlation
    CORR(zl_close, cpo_close) OVER w60 AS zl_cpo_corr_60d
FROM palm_base
WINDOW w60 AS (ORDER BY date ROWS BETWEEN 59 PRECEDING AND CURRENT ROW)
```

### 📰 PALM OIL NEWS SIGNALS (Crawler Targets)

**Indonesia Disruption Events:**
- Government seizure of plantations (3.7M hectares)
- Agrinas Palma Nusantara (state-run) expansion
- Export bans/restrictions
- Deforestation policy changes

**Malaysia Supply Events:**
- MPOB production/inventory reports
- Export duty changes
- Labor shortages

**Crawler Pattern:**
```
(palm OR "palm oil" OR FCPO OR CPO OR "vegetable oil") 
AND (Indonesia OR Malaysia OR Riau OR "export ban" OR seizure OR "task force" OR mandate)
```

---

## 6. DATABENTO PLATFORM TIPS

### 📊 GLBX.MDP3 Dataset Specifics

| Attribute | Value |
|-----------|-------|
| **Venues** | CME, CBOT, NYMEX, COMEX |
| **History** | Back to **June 6, 2010** (extended from legacy FIX/FAST) |
| **Granularity** | Full MBO from May 2017; MBP-10 for pre-2017 |
| **Options** | Full options chain available (OZL for soybean oil) |
| **Palm Oil** | CPO (USD cash-settled Malaysian palm) |
| **Canola** | Use ICE for rapeseed/canola (separate venue) |

### ⚠️ CONNECTION LIMITS

| Limit | Value |
|-------|-------|
| **Historical API** | 100 concurrent connections, 100 req/sec per IP |
| **Live API** | 10 simultaneous sessions per dataset per team |
| **Gateway** | Max 5 incoming connections/sec from same IP |

**Implication:** Batch symbol requests, don't hammer API

### 💰 COST ESTIMATES

| Plan | Cost | Notes |
|------|------|-------|
| **Standard** | ~$179/month (CME MDP3) | April 2025 pricing |
| **Historical** | From $0.50/GB | Usage-based |
| **Full schema** | Higher | If you need full MBO depth |

### 🔧 OPTIMAL INGESTION PATTERN

```python
# Batch symbols to stay within limits
SYMBOL_BATCHES = [
    ['ZL', 'ZS', 'ZM', 'ZC'],  # Soy complex
    ['CL', 'HO', 'RB'],         # Energy
    ['ES', 'MES'],              # Equities
    ['6E', '6J', '6B', '6A'],   # FX
    ['CPO'],                    # Palm oil
]

# Rate-limit requests
import time
for batch in SYMBOL_BATCHES:
    data = client.timeseries.get_range(
        dataset='GLBX.MDP3',
        symbols=batch,
        schema='ohlcv-1d',
        start='2010-06-06'
    )
    time.sleep(1)  # Respect rate limits
```

### 📈 OPTIONS DATA FOR IMPLIED VOL

```python
# ZL Options (OZL) for implied volatility calculation
# Available in GLBX.MDP3

# Get ATM options for IV calculation
options_data = client.timeseries.get_range(
    dataset='GLBX.MDP3',
    symbols=['OZL'],  # Soybean Oil Options
    schema='ohlcv-1d',
    start='2017-05-21',  # Full MBO from this date
    end='2025-11-24'
)

# For pre-2017: MBP-10 granularity only
# Still useful for daily settlement prices
```

---

## 7. POLICY SENTIMENT TAXONOMY (Crawler Framework)

### 🎯 BUCKETS FOR VEG-OIL MARKET MOVERS

#### Bucket 1: AGG (Geopolitical/Supply/Ports)
```
Pattern: (soybean OR "veg oil" OR "soy oil" OR biodiesel OR canola OR palm) 
         AND (port OR strike OR blockade OR canal OR sanctions OR "export ban")
```
**Sources:** USDA FAS weekly export sales, Reuters, CME notices

#### Bucket 2: LABOR (Crusher/Trucker/Longshore)
```
Pattern: (crush* OR refiner* OR "oilseed plant" OR truck* OR longshore*) 
         AND (strike OR walkout OR stoppage) 
         AND (soybean OR canola OR palm)
```
**Sources:** CME delivery notices, industry press

#### Bucket 3: LEGISLATION (RFS/Biofuel Mandates)
```
Pattern: (RFS OR "renewable fuel standard" OR biodiesel OR "blend %" OR mandate) 
         AND (rule OR proposal OR waiver OR volume OR RVO)
```
**Sources:** EPA RFS pages, ABIOVE (Brazil biodiesel)

#### Bucket 4: TARIFFS/TRADE
```
Pattern: (tariff OR duty OR quota OR anti-dumping OR embargo) 
         AND (canola OR "soybean oil" OR rapeseed OR palm)
```
**Sources:** USTR, Canada trade news, Reuters

### 📊 SOURCE WEIGHTING

| Source Type | Weight | Examples |
|-------------|--------|----------|
| **Regulators/Exchanges** | 1.0 | EPA, USDA FAS, CME/CBOT |
| **National Agencies/Wires** | 0.8 | Reuters, AP |
| **Industry Orgs** | 0.7 | ABIOVE, S&P/DTN |
| **Social Media** | 0.3-0.5 | X/Truth Social (confirm with higher sources) |

### 🏷️ REGIME TAGS

| Event | Regime Tag | ZL Direction |
|-------|------------|--------------|
| Brazil B14→B15 mandate | `biofuel-policy-tightening` | Bullish |
| Brazil holds at B14 | `biofuel-policy-loosening` | Bearish vs path |
| EPA SRE waivers spike | `mandate-relief` | Bearish RINs |
| CME delivery notice | `delivery-mechanics-change` | Basis impact |
| USDA export sales surge | `export-flow-shift` | Bullish demand |
| Indonesia palm seizure | `supply-disruption-palm` | Bullish ZL (substitution) |

### 🔧 OUTPUT SCHEMA

```sql
-- events_raw
CREATE TABLE raw_intelligence.policy_events_raw (
    event_id STRING,
    timestamp TIMESTAMP,
    source STRING,
    source_weight FLOAT64,
    bucket STRING,  -- agg, labor, legislation, tariffs
    headline STRING,
    url STRING,
    country STRING,
    raw_text STRING
);

-- signals_policy (after de-dup + trust filter)
CREATE TABLE features.policy_signals_daily (
    date DATE,
    bucket STRING,
    regime_tag STRING,
    direction_zl INT64,  -- +1 bullish, -1 bearish, 0 neutral
    confidence FLOAT64,
    event_count INT64,
    supporting_urls ARRAY<STRING>
);

-- features_policy_daily (for model)
CREATE TABLE features.policy_features_daily (
    date DATE,
    agg_events_7d INT64,
    labor_events_7d INT64,
    legislation_events_7d INT64,
    tariff_events_7d INT64,
    policy_sentiment_7d FLOAT64,  -- weighted avg direction
    policy_sentiment_z_30d FLOAT64,  -- z-score
    is_mandate_change BOOL,
    is_trade_war_escalation BOOL
);
```

### 📅 KEY SOURCES TO POLL

| Source | URL | Frequency |
|--------|-----|-----------|
| USDA FAS Export Sales | fas.usda.gov/data/weekly-export-sales | Weekly |
| EPA RFS | epa.gov/renewable-fuel-standard | On change |
| CME Soy Oil Contract | cmegroup.com/rulebook/CBOT/II/12/12.pdf | On change |
| ABIOVE Biodiesel | abiove.org.br/biodiesel-main | Weekly |
| ICE Canola | ice.com/agriculture/canola | Daily |

---

## 8. WEATHER IMPROVEMENTS (ERA5-Land + SMAP)

### 🌧️ ENHANCED WEATHER STACK

The basic NOAA GSOD approach works, but for **Brazil/Argentina soy belt** we need:

| Source | Data | Why |
|--------|------|-----|
| **ERA5-Land** | Gridded reanalysis (hourly, 1950-present) | Fill station gaps, compute PET |
| **SMAP** | Satellite soil moisture | Drought proxy when stations sparse |
| **INMET** | Brazil automatic stations | High-density soy belt coverage |
| **SMN** | Argentina national weather | Pampas coverage |

### 🔧 IMPROVED WEATHER FEATURES

```sql
-- Enhanced Weather Features (per region)
CREATE TABLE features.weather_regional_daily (
    date DATE,
    region_id STRING,  -- BR_MT, BR_PR, AR_BA, US_MW
    
    -- Basic aggregates
    prcp_7d FLOAT64,
    tmean_7d FLOAT64,
    tmax_7d FLOAT64,
    tmin_7d FLOAT64,
    
    -- PET and moisture balance
    pet_7d FLOAT64,  -- Potential evapotranspiration (from ERA5-Land pev)
    p_minus_pet_7d FLOAT64,  -- Deficit < 0 = drying
    
    -- Soil moisture (SMAP)
    smap_surface_pct FLOAT64,  -- Surface soil moisture percentile
    smap_rootzone_pct FLOAT64,  -- Root zone percentile
    
    -- Anomalies (vs 10-year baseline)
    prcp_zscore_7d FLOAT64,
    tmean_zscore_7d FLOAT64,
    pet_zscore_7d FLOAT64,
    
    -- Lags (for delayed crop response)
    prcp_7d_lag7 FLOAT64,
    prcp_7d_lag14 FLOAT64,
    prcp_7d_lag21 FLOAT64,
    
    -- QA flags
    is_backfilled BOOL,
    qc_score FLOAT64,
    source STRING  -- station/era5/smap
);
```

### 🎯 REGION DEFINITIONS

| Region ID | Name | Key Stations/Grid |
|-----------|------|-------------------|
| `BR_MT` | Mato Grosso | INMET + ERA5 grid |
| `BR_PR` | Paraná | INMET + ERA5 grid |
| `BR_RS` | Rio Grande do Sul | INMET + ERA5 grid |
| `BR_GO` | Goiás | INMET + ERA5 grid |
| `AR_BA` | Buenos Aires | SMN + ERA5 grid |
| `AR_CB` | Córdoba | SMN + ERA5 grid |
| `AR_SF` | Santa Fe | SMN + ERA5 grid |
| `US_MW` | US Midwest (IA/IL/IN/NE/MN) | NOAA GSOD |

### 📊 PHASE 1 VS PHASE 2 WEATHER

| Feature | Phase 1 | Phase 2 |
|---------|---------|---------|
| US Midwest (GSOD) | ✅ | ✅ |
| Brazil (INMET) | ⏸️ | ✅ |
| Argentina (SMN) | ⏸️ | ✅ |
| ERA5-Land backfill | ⏸️ | ✅ |
| SMAP soil moisture | ⏸️ | ✅ |
| PET calculation | ⏸️ | ✅ |

**Phase 1:** Just US Midwest from BigQuery Public Data (GSOD)
**Phase 2:** Full Brazil/Argentina with ERA5-Land gap-fill and SMAP

---

## 9. SPECIAL CALCULATIONS

### ✅ WHAT WE HAVE (Scripts Located)

| Calculation | Script | Status |
|-------------|--------|--------|
| Pivot Points | `cloud_function_pivot_calculator.py` | ✅ READY |
| Fibonacci | `cloud_function_fibonacci_calculator.py` | ✅ READY |
| Trump/Policy | `trump_action_predictor.py` | ✅ READY |
| ZL Impact | `zl_impact_predictor.py` | ✅ READY |
| Cross-Asset | `build_all_features.py` | ✅ READY |
| RIN Proxies | `calculate_rin_proxies.py` | ✅ READY |
| FX Features | `build_forex_features.py` | ✅ READY |
| MES Features | `build_mes_all_features.py` | ✅ READY |

### 🔧 PHASE 1 SPECIAL FEATURES

| Feature | Source | Priority |
|---------|--------|----------|
| `zl_realized_vol_10d` | Databento | ✅ HIGH |
| `zl_realized_vol_30d` | Databento | ✅ HIGH |
| `crush_margin` | ZS, ZM, ZL | ✅ HIGH (Big 8) |
| `P, R1, R2, S1, S2` | Pivot calculator | ✅ HIGH |
| `trump_sentiment` | Trump predictor | ✅ HIGH |
| `soy_fx_stress` | FX composite | ✅ HIGH |
| `vix_z_60d` | FRED | ✅ HIGH |
| `bdi_z_30d` | FRED/BDI | ✅ MEDIUM |

---

## 6. IMPLEMENTATION ORDER (REVISED)

### Phase 1A: Core Data (Day 1-2)

1. **Confirm Databento data** (6,034 rows ZL + MES) ✅ DONE
2. **Pull FRED baseline:**
   - VIXCLS (VIX)
   - DFF (Fed Funds)
   - DGS10 (10Y Treasury)
   - BDILCY (Baltic Dry Index) ← **ADD THIS**
3. **Pull NOAA weather** (BigQuery Public Data - FREE)

### Phase 1B: Calculations (Day 3-4)

4. **Calculate FX features:**
   - `fx_ret_1d`, `fx_realized_vol_10d/20d`
   - `soy_fx_stress` composite
   - `curve_slope`, `curve_inversion_flag`

5. **Calculate VIX features:**
   - `vix_z_60d`, `vix_pctl_3y`

6. **Calculate weather features:**
   - `temp_anom_7d`, `precip_anom_7d`
   - `gdd_30d` (Growing Degree Days)

7. **Run pivot calculator:**
   - `P, R1, R2, S1, S2, distance_to_P`

### Phase 1C: Integration (Day 5)

8. **Build `features.daily_ml_matrix`:**
   - Join all features
   - Add regime from `reference.regime_calendar`
   - Export flat view for Mac

9. **Populate training tables:**
   - `training.zl_training_prod_1w/1m/3m/6m/12m`

---

## 7. MISSING ITEMS TO ADD

### 🔴 CRITICAL (Add to Phase 1)

| Item | Gap | Fix |
|------|-----|-----|
| **BDI from FRED** | Current script uses mock data | Add `BDILCY` to FRED pull |
| **Weather from BQ Public** | No SQL for GSOD/Storm Events | Write SQL queries |
| **Crush Margin** | Script exists but not wired | Wire `crush_margin_daily` table |

### 🟡 MEDIUM (Add to Phase 1 if time)

| Item | Gap | Fix |
|------|-----|-----|
| **OVX (Oil VIX)** | Not pulling | Add to FRED series |
| **MOVE Index** | Not pulling | Add to FRED series (bond vol) |
| **Brazil weather** | Complex station mapping | Use GSOD Brazil stations |

### 🟢 LOW (Defer to Phase 2)

| Item | Gap | Fix |
|------|-----|-----|
| **VIX term structure** | Need VIX futures | Add Databento VX contracts |
| **Implied vs realized** | Need ZL options | Complex - defer |
| **Earth Engine rasters** | Complex setup | Defer |
| **Port-specific logistics** | Requires scraping | Defer |

---

## 8. TABLES TO CREATE/UPDATE

### New Tables (Add to `COMPLETE_BIGQUERY_DATASET_TABLE_BREAKDOWN`)

```sql
-- raw.fred_macro (update to include)
Series to add:
- BDILCY (Baltic Dry Index)
- OVXCLS (Oil VIX) - optional
- BAMLH0A0HYM2 (High Yield Spread) - optional
```

```sql
-- raw.noaa_weather_gsod
type: "declaration"
database: "bigquery-public-data"
schema: "noaa_gsod"
name: "gsod*"
description: "NOAA Global Surface Summary of Day (FREE public dataset)"
```

```sql
-- raw.noaa_storm_events
type: "declaration"
database: "bigquery-public-data"
schema: "noaa_historic_severe_storms"
name: "storms_*"
description: "NOAA Storm Events (FREE public dataset)"
```

```sql
-- staging.weather_gsod_midwest
type: "incremental"
uniqueKey: ["date", "station_id"]
partitionBy: "DATE(date)"
clusterBy: ["station_id"]
tags: ["staging", "weather"]

Columns:
- date (DATE)
- station_id (STRING)
- avg_temp_f (FLOAT64)
- max_temp_f (FLOAT64)
- min_temp_f (FLOAT64)
- precipitation_in (FLOAT64)
- processed_at (TIMESTAMP)
```

```sql
-- staging.baltic_dry_index
type: "incremental"
uniqueKey: ["date"]
partitionBy: "DATE(date)"
tags: ["staging", "logistics"]

Columns:
- date (DATE)
- bdi_value (FLOAT64)
- bdi_change_pct (FLOAT64)
- source (STRING)
- processed_at (TIMESTAMP)
```

```sql
-- features.logistics_pressure_daily
type: "incremental"
uniqueKey: ["date"]
partitionBy: "DATE(date)"
tags: ["features", "logistics"]

Columns:
- date (DATE)
- bdi_value (FLOAT64)
- bdi_z_30d (FLOAT64)
- logistics_pressure_global (FLOAT64)
- processed_at (TIMESTAMP)
```

---

## 9. INTERACTION TERMS (Mac-Side)

**Let Mac discover these, don't pre-compute in BQ:**

```python
# In Mac training script, create interaction features:
interaction_features = {
    'fx_vol_x_temp_anom': df['fx_realized_vol_20d'] * df['temp_anom_30d'],
    'logistics_x_vix': df['logistics_pressure_global'] * df['vix_z_60d'],
    'drought_x_curve_inv': df['drought_events_90d'] * df['curve_inversion_flag'],
    'crush_x_brl_pressure': df['crush_margin'] * df['z_usdbrl'],
}
```

**Why Mac-side:**
- Cheaper (no BQ compute)
- Flexible (can add/remove easily)
- Model can learn non-linear interactions

---

## 10. SUMMARY: WHAT TO DO NOW

### ✅ IMMEDIATE ACTIONS (Phase 1)

1. **Fix BDI script** - Replace mock data with FRED `BDILCY`
2. **Write GSOD SQL** - Query BigQuery Public Data for Midwest weather
3. **Wire crush margin** - Ensure `crush_margin_daily` table is populated
4. **Add to FRED pull (volatility proxies):**
   - `BAMLH0A0HYM2` (High Yield Spread) - **VIX REPLACEMENT**
   - `TEDRATE` (TED Spread)
   - `T10Y2Y` (Yield Curve)
   - `BDILCY` (Baltic Dry Index)
5. **Add CPO (Palm Oil)** - Pull from Databento GLBX.MDP3
6. **Calculate realized vol** - ZL 10d/21d/63d from Databento prices
7. **Build risk_sentiment_index** - Composite from FRED proxies

### 🟡 PHASE 1.5 (After Baseline Validates)

- **Palm oil features** - ZL-CPO spread, correlation, substitution pressure
- **Policy sentiment crawler** - Start with EPA/USDA/CME sources
- **Indonesia/Malaysia news signals** - Palm disruption events

### ⏸️ DEFER TO PHASE 2

- Implied volatility from options (complex calculation)
- Brazil/Argentina weather (INMET/SMN/ERA5-Land)
- SMAP soil moisture
- Full policy sentiment taxonomy
- Canola from ICE (separate venue)

### ❌ SKIP ENTIRELY

- **VIX data** - We will NEVER have it, use alternatives above
- Weather Source (paid) - Use free GSOD instead
- Complex AIS shipping data - Use BDI proxy
- CVOL surfaces - Expensive, use realized vol instead

---

## 11. NEW TABLES SUMMARY

### Add to `COMPLETE_BIGQUERY_DATASET_TABLE_BREAKDOWN`

```sql
-- staging.fred_risk_proxies (VIX alternatives)
type: "incremental"
uniqueKey: ["date"]
Columns: date, hy_spread, ig_spread, ted_spread, yield_curve_slope, yield_curve_3m

-- staging.palm_oil_daily
type: "incremental"
uniqueKey: ["date"]
Columns: date, cpo_close, cpo_return_1d, cpo_volume

-- features.volatility_signals (NO VIX - use these)
type: "incremental"
uniqueKey: ["date"]
Columns: date, zl_realized_vol_10d, zl_realized_vol_21d, zl_realized_vol_63d,
         vol_regime, risk_sentiment_index, z_hy_spread, yield_curve_slope

-- features.palm_oil_features
type: "incremental"
uniqueKey: ["date"]
Columns: date, cpo_close, zl_cpo_spread, zl_cpo_corr_60d, palm_substitution_regime

-- raw_intelligence.policy_events_raw
type: "incremental"
uniqueKey: ["event_id"]
Columns: event_id, timestamp, source, source_weight, bucket, headline, url, country

-- features.policy_features_daily
type: "incremental"
uniqueKey: ["date"]
Columns: date, agg_events_7d, labor_events_7d, legislation_events_7d, tariff_events_7d,
         policy_sentiment_7d, policy_sentiment_z_30d, is_mandate_change
```

---

## 12. DATABENTO SYMBOL LIST (FINAL)

### Tier 1: Core (Load First)
```python
TIER_1_SYMBOLS = ['ZL', 'ZS', 'ZM', 'MES', 'ES']
```

### Tier 2: Energy + Palm
```python
TIER_2_SYMBOLS = ['CL', 'HO', 'RB', 'CPO']  # CPO = Palm Oil
```

### Tier 3: FX
```python
TIER_3_SYMBOLS = ['6E', '6J', '6B', '6A', '6C', '6N']  # Major FX futures
```

### Tier 4: Options (For Implied Vol - Phase 2)
```python
TIER_4_OPTIONS = ['OZL', 'OZS']  # Soybean Oil/Soybean Options
```

### NOT in Databento (Need ICE)
```python
# Canola/Rapeseed - ICE venue, not CME
# Must pull separately if needed
ICE_SYMBOLS = ['RS', 'RSX']  # ICE Canola
```

---

## 13. KEY INSIGHTS FROM INTEL

### 🔴 Indonesia Palm Disruption (Watch Closely)
- 3.7M hectares seized by government task force
- Agrinas Palma Nusantara = world's largest palm by land area
- Riau protests (2,800 protesters) signal social risk
- **Impact:** Supply constraint → higher palm prices → ZL substitution demand

### 🟡 Malaysia Futures Pressure
- Weak exports, rising inventories
- Rival edible oils (soy, sunflower) weighing on palm
- On track for second weekly gain despite pressure
- **Impact:** Mixed signals, watch for breakout

### 🟢 Brazil Biofuel Mandates
- B14→B15 approved for Aug 1, 2025
- Modestly bullish for soy oil demand
- **Impact:** Supportive for ZL

### 🟡 EPA Small Refinery Waivers
- 14 waivers approved Nov 2025
- Mild bearish pressure on biodiesel demand
- **Impact:** Watch RINs, spillover to ZL

---

## 14. FX/USD SHOCK REGIMES (Critical for Export Competitiveness)

### 🎯 WHY USD MATTERS FOR ZL

- **Rising USD** → suppresses U.S. export competitiveness
- **Tighter export flows** → domestic processing margins compress
- **6E (Euro FX)** encodes USD strength/weakness (inverse relationship)
- **USDX** monitors broad USD regime shifts

### 📊 6E CONTRACT SPECS (CME)

| Attribute | Value |
|-----------|-------|
| Contract Unit | EUR 125,000 |
| Tick Size | $0.00005 = $6.25/contract |
| Trading Hours | Sunday-Friday on Globex |
| Implied Vol | CME CVOL™ for EUR/USD |

### 🔧 USD SHOCK DETECTION

```sql
-- USD Regime Detection
WITH usd_base AS (
    SELECT 
        date,
        -- 6E is inverse USD (EUR/USD)
        MAX(CASE WHEN symbol = '6E' THEN close END) AS eur_usd,
        MAX(CASE WHEN symbol = 'DXY' THEN close END) AS dxy
    FROM staging.market_daily
    WHERE symbol IN ('6E', 'DXY')
    GROUP BY date
),
usd_vol AS (
    SELECT 
        date,
        eur_usd,
        dxy,
        -- DXY realized vol (proxy for USD stress)
        SQRT(252) * STDDEV(LN(dxy/LAG(dxy) OVER (ORDER BY date))) 
            OVER (ORDER BY date ROWS BETWEEN 20 PRECEDING AND CURRENT ROW) AS dxy_vol_21d,
        -- Z-score of DXY
        (dxy - AVG(dxy) OVER w60) / NULLIF(STDDEV(dxy) OVER w60, 0) AS dxy_z_60d
    FROM usd_base
    WINDOW w60 AS (ORDER BY date ROWS BETWEEN 59 PRECEDING AND CURRENT ROW)
)
SELECT 
    date,
    dxy,
    dxy_vol_21d,
    dxy_z_60d,
    -- USD Shock Regime
    CASE 
        WHEN dxy_z_60d > 1.5 AND dxy_vol_21d > 0.08 THEN 'USD_SURGE_HIGH_VOL'
        WHEN dxy_z_60d > 1.0 THEN 'USD_STRONG'
        WHEN dxy_z_60d < -1.0 THEN 'USD_WEAK'
        ELSE 'USD_NEUTRAL'
    END AS usd_regime,
    -- Export pressure flag
    CASE WHEN dxy_z_60d > 1.0 THEN TRUE ELSE FALSE END AS export_pressure_flag
FROM usd_vol
```

### 🎯 USD FEATURES FOR ZL MODEL

| Feature | Source | Impact on ZL |
|---------|--------|--------------|
| `dxy_z_60d` | Calculated | Negative (strong USD → weak exports) |
| `dxy_vol_21d` | Calculated | Uncertainty signal |
| `usd_regime` | Categorical | Regime gating |
| `export_pressure_flag` | Boolean | Margin compression signal |
| `eur_usd_change_5d` | 6E | Inverse USD momentum |

### 💡 IMPLEMENTATION IDEA

> "Use 6E implied vol or open interest build to flag heightened USD risk. 
> Trigger signal when USD futures/vol exceed threshold → adjust soybean-oil 
> exposure (reduce net long processing margin when USD threatens exports)."

---

## 15. CROSS-ASSET IMPLIED VOL SPILLOVER (ZL ↔ CL)

### 🎯 THE CRUDE → VEG OIL CHANNEL

- **Biofuel feedstock link**: Crude oil rallies → stronger veg oil demand
- **Vol spillover**: CL IV rises → ZL IV often follows (hedgers repositioning)
- **Skew signals**: Processors seeking upside protection = bullish ZL indicator

### 📊 CME CVOL™ INDICES (What We'd Want)

| Index | Asset | Notes |
|-------|-------|-------|
| CVOL ZL | Soybean Oil | Options-derived implied vol |
| CVOL CL | WTI Crude | Energy vol benchmark |
| CVOL 6E | EUR/USD | FX vol benchmark |

**Reality:** CVOL data requires CME license. **Alternative:** Calculate IV from Databento options.

### 🔧 CROSS-OILSEED HEDGING TRIGGER

```python
# Spillover Detection Logic
def detect_crude_to_vegoil_spillover(cl_vol, zl_vol, threshold_cl=0.30, lag_threshold=0.05):
    """
    Flag when CL vol rises but ZL vol hasn't caught up yet.
    This often precedes ZL price moves.
    
    Signal: CL_vol > threshold AND (CL_vol - ZL_vol) > lag_threshold
    """
    spillover_risk = (cl_vol > threshold_cl) and ((cl_vol - zl_vol) > lag_threshold)
    return {
        'spillover_risk': spillover_risk,
        'cl_vol': cl_vol,
        'zl_vol': zl_vol,
        'vol_gap': cl_vol - zl_vol
    }
```

```sql
-- Cross-Asset Vol Features
WITH vol_base AS (
    SELECT 
        date,
        zl_realized_vol_21d,
        cl_realized_vol_21d,
        -- Vol gap (CL leading ZL)
        cl_realized_vol_21d - zl_realized_vol_21d AS vol_gap_cl_zl,
        -- Vol ratio
        SAFE_DIVIDE(cl_realized_vol_21d, zl_realized_vol_21d) AS vol_ratio_cl_zl
    FROM features.volatility_signals
)
SELECT 
    date,
    vol_gap_cl_zl,
    vol_ratio_cl_zl,
    -- Spillover flag
    CASE 
        WHEN cl_realized_vol_21d > 0.30 AND vol_gap_cl_zl > 0.05 THEN 'SPILLOVER_RISK'
        WHEN vol_ratio_cl_zl > 1.5 THEN 'CL_LEADING'
        WHEN vol_ratio_cl_zl < 0.7 THEN 'ZL_LEADING'
        ELSE 'NORMAL'
    END AS vol_regime_cross_asset
FROM vol_base
```

### 🎯 CROSS-ASSET VOL FEATURES

| Feature | Calculation | Priority |
|---------|-------------|----------|
| `vol_gap_cl_zl` | CL_vol - ZL_vol | ✅ HIGH |
| `vol_ratio_cl_zl` | CL_vol / ZL_vol | ✅ HIGH |
| `vol_regime_cross_asset` | Categorical | ✅ HIGH |
| `zl_cl_vol_corr_30d` | Rolling correlation of vols | ✅ MEDIUM |

---

## 16. BIOFUEL DEMAND CHANNEL (Structural Driver)

### 🎯 THE BIG PICTURE

- **~40% of U.S. soybean oil** now goes to biofuels (up from ~0% two decades ago)
- **9 billion pounds growth** (2009/10 → 2021/22) almost ALL biofuel-driven
- **2023-24 forecast**: ~13 billion pounds for biofuel production
- **Policy drivers**: RFS, LCFS, 45Z credit

### 📊 USDA BIOFUEL METRICS TO TRACK

| Metric | Source | Frequency |
|--------|--------|-----------|
| Soybean oil biofuel use (billion lbs) | USDA ERS | Monthly/Quarterly |
| Soybean oil domestic disappearance | USDA WASDE | Monthly |
| Biofuel % of total soy oil use | Calculated | Monthly |
| Renewable diesel capacity (MMgal/yr) | EIA | Quarterly |

### 🔧 BIOFUEL DEMAND FEATURES

```sql
-- Biofuel Demand Channel Features
CREATE TABLE features.biofuel_demand_daily (
    date DATE,
    
    -- USDA metrics (interpolated to daily)
    soyoil_biofuel_use_blbs FLOAT64,  -- Billion pounds
    soyoil_total_disappearance_blbs FLOAT64,
    biofuel_share_pct FLOAT64,  -- biofuel / total
    
    -- YoY changes
    biofuel_use_yoy_pct FLOAT64,
    biofuel_share_yoy_change FLOAT64,
    
    -- Regime indicators
    biofuel_demand_regime STRING,  -- 'SURGE', 'GROWTH', 'STABLE', 'DECLINE'
    is_policy_change_window BOOL,  -- Near RFS/LCFS announcement
    
    -- Cross-asset sensitivity
    crude_vegoil_sensitivity FLOAT64  -- Rolling beta of ZL to CL
);
```

```sql
-- Biofuel Demand Regime Detection
SELECT 
    date,
    biofuel_share_pct,
    biofuel_use_yoy_pct,
    CASE 
        WHEN biofuel_use_yoy_pct > 15 THEN 'SURGE'
        WHEN biofuel_use_yoy_pct > 5 THEN 'GROWTH'
        WHEN biofuel_use_yoy_pct > -5 THEN 'STABLE'
        ELSE 'DECLINE'
    END AS biofuel_demand_regime,
    -- When biofuel demand surges, crude→ZL sensitivity increases
    CASE 
        WHEN biofuel_use_yoy_pct > 10 THEN 1.5  -- Amplified sensitivity
        WHEN biofuel_use_yoy_pct > 0 THEN 1.0  -- Normal
        ELSE 0.7  -- Dampened
    END AS crude_sensitivity_multiplier
FROM staging.usda_biofuel_metrics
```

### 🎯 BIOFUEL FEATURES FOR MODEL

| Feature | Source | Priority |
|---------|--------|----------|
| `biofuel_share_pct` | USDA | ✅ HIGH |
| `biofuel_use_yoy_pct` | USDA | ✅ HIGH |
| `biofuel_demand_regime` | Categorical | ✅ HIGH |
| `crude_sensitivity_multiplier` | Calculated | ✅ MEDIUM |
| `is_policy_change_window` | Calendar | ✅ MEDIUM |

### 💡 MODELING IMPLICATION

> "Include a 'biofuel demand shock' regime indicator (e.g., when USDA increases 
> forecast or key policy announced) and feed that into correlation shifts 
> (e.g., crude → veg oil sensitivity rises)."

---

## 17. VIX-BAND REGIME CLUSTERING (Dynamic Correlations)

### 🎯 THE INSIGHT

- **Static correlations fail** in choppy markets
- **Cluster by VIX percentile bands** → correlations "breathe" with stress
- **Lower MAPE** + cleaner SHAP attributions

### 📊 VIX BAND DEFINITIONS

| Band | VIX Percentile | Label | Market State |
|------|----------------|-------|--------------|
| VL | 0-20th | Very Low | Complacent |
| L | 20-40th | Low | Calm |
| N | 40-60th | Neutral | Normal |
| H | 60-80th | High | Elevated |
| VH | 80-100th | Very High | Stress/Crisis |

### 🔧 REGIME-AWARE CORRELATION FEATURES

```python
# Mac-side: VIX-Band Regime Clustering
import pandas as pd
import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster

# Symbols to correlate with ZL
CORR_SYMBOLS = ['FCPO', 'RS', 'ZC', 'ZS', 'ZM', 'CL', 'HO', 'DXY', 'USDBRL', 'USDCNY']

def compute_regime_correlations(df, window=126):
    """
    Compute rolling correlations by VIX band.
    
    Args:
        df: DataFrame with columns ['date', 'ZL', 'VIX'] + CORR_SYMBOLS
        window: Rolling window (126 = ~6 months)
    
    Returns:
        DataFrame with regime-aware correlation features
    """
    df = df.sort_values('date').set_index('date')
    
    # 1) VIX percentile bands
    q = df['VIX'].rank(pct=True)
    df['vix_band'] = pd.cut(q, [0, .2, .4, .6, .8, 1.0], 
                            labels=['VL', 'L', 'N', 'H', 'VH'])
    
    # 2) Rolling correlations per band
    results = []
    for band in ['VL', 'L', 'N', 'H', 'VH']:
        band_data = df[df['vix_band'] == band]
        if len(band_data) < window:
            continue
            
        for symbol in CORR_SYMBOLS:
            corr = band_data['ZL'].rolling(window).corr(band_data[symbol])
            results.append({
                'band': band,
                'symbol': symbol,
                'mean_corr': corr.mean(),
                'std_corr': corr.std()
            })
    
    return pd.DataFrame(results)

def generate_regime_features(df, current_vix_pctl):
    """
    Generate features for current regime.
    
    Returns dict of features like:
    - corr_ZL_CL_H (correlation in High VIX band)
    - w_ZL_CL_H (softmax weight)
    """
    band = get_band_from_percentile(current_vix_pctl)
    features = {}
    
    for symbol in CORR_SYMBOLS:
        corr_col = f'corr_ZL_{symbol}_{band}'
        weight_col = f'w_ZL_{symbol}_{band}'
        
        # Get band-specific correlation
        corr = compute_band_correlation(df, symbol, band)
        features[corr_col] = corr
        
        # Softmax weight (higher abs corr = higher weight)
        features[weight_col] = np.exp(abs(corr)) / sum_exp_all_symbols
    
    return features
```

### 📊 OUTPUT SCHEMA

```sql
-- Regime-Aware Correlation Features
CREATE TABLE features.regime_correlations_daily (
    date DATE,
    current_vix_band STRING,  -- VL, L, N, H, VH
    
    -- Per-symbol correlations in current band
    corr_ZL_FCPO_regime FLOAT64,
    corr_ZL_CL_regime FLOAT64,
    corr_ZL_HO_regime FLOAT64,
    corr_ZL_DXY_regime FLOAT64,
    corr_ZL_USDBRL_regime FLOAT64,
    
    -- Softmax weights (for feature re-weighting)
    w_ZL_FCPO_regime FLOAT64,
    w_ZL_CL_regime FLOAT64,
    w_ZL_HO_regime FLOAT64,
    w_ZL_DXY_regime FLOAT64,
    
    -- Sign flip alerts (vs Neutral band)
    sign_flip_FCPO BOOL,
    sign_flip_CL BOOL,
    sign_flip_DXY BOOL,
    
    -- Cluster membership (which group of drivers is active)
    cluster_id INT64
);
```

### 🎯 REGIME CORRELATION FEATURES

| Feature | Purpose | Priority |
|---------|---------|----------|
| `current_vix_band` | Route to correct model/weights | ✅ HIGH |
| `corr_ZL_*_regime` | Band-specific correlations | ✅ HIGH |
| `w_ZL_*_regime` | Dynamic feature weights | ✅ HIGH |
| `sign_flip_*` | Alert when correlation flips sign | ✅ MEDIUM |
| `cluster_id` | Which driver cluster is active | 🟡 Phase 2 |

### 💡 TRAINING APPROACHES

**Option A (Fast):** Single model with regime features (one-hot band + banded correlations)

**Option B (Clean):** One model per band + tiny gate that routes by current band

**Option C (Middle):** Single model; multiply each driver by its band weight (dynamic coefficients)

### ⚠️ GUARDRAILS

- **Stability:** Use 3-5 day hysteresis on band transitions (avoid whipsaw)
- **Leakage:** Compute correlations using only data up to `t-1`
- **Sign flips:** Log whenever `sign(corr)` differs from Neutral → alert in dashboard

---

## 18. DASHBOARD ENHANCEMENTS

### 🎯 NEW TILES FROM THIS INTEL

| Tile | Content | Use Case |
|------|---------|----------|
| **USD Regime** | Current DXY z-score, vol, regime label | Export pressure alert |
| **Vol Spillover** | CL vs ZL vol gap, spillover flag | Cross-asset positioning |
| **Biofuel Demand** | Current share %, YoY change, regime | Structural demand signal |
| **VIX Band** | Current band, top 3 boosted drivers, sign flips | Regime-aware attribution |
| **Palm Pressure** | ZL-CPO spread, substitution regime | Substitution risk |

### 📊 EXAMPLE: REGIME TILE

```
┌──────────────────────────────────────────────────┐
│              CURRENT REGIME: HIGH VOL            │
├──────────────────────────────────────────────────┤
│  VIX Band: H (72nd percentile)                   │
│                                                  │
│  Top Boosted Drivers (vs Neutral):               │
│    1. CL (Crude): +0.15 corr boost               │
│    2. DXY (USD): +0.08 corr boost                │
│    3. FCPO (Palm): -0.05 corr shift              │
│                                                  │
│  ⚠️ Sign Flip Alert: USDBRL flipped NEGATIVE    │
│     (was +0.32 in Neutral, now -0.18 in High)   │
│                                                  │
│  Interpretation: USD stress dominating;          │
│  export channel > substitution channel           │
└──────────────────────────────────────────────────┘
```

---

**Status:** 🟢 SPEC REVIEWED - COMPREHENSIVE TIPS ADDED  
**Key Changes:**
1. NO VIX - Use FRED proxies + realized vol
2. ADD Palm Oil (CPO) from Databento
3. ADD Policy Sentiment Taxonomy
4. Databento connection limits documented
5. Indonesia/Malaysia disruption signals added
6. **NEW: FX/USD shock regime detection**
7. **NEW: Cross-asset vol spillover (CL→ZL)**
8. **NEW: Biofuel demand channel metrics**
9. **NEW: VIX-band regime clustering for dynamic correlations**

**Next Steps:**
1. Update FRED pull script with volatility proxies
2. Add CPO to Databento symbol list
3. Fix BDI script (remove mock data)
4. Write GSOD SQL for weather
5. Build risk_sentiment_index calculation
6. **Implement USD regime detection**
7. **Build cross-asset vol spillover features**
8. **Add USDA biofuel metrics to pipeline**
9. **Implement VIX-band regime clustering (Mac-side)**


