# CBI-V14 PROJECT RULES - READ FIRST

**PASTE THIS AT THE START OF EVERY NEW CLAUDE CONVERSATION**

---

## 🚨 BIGQUERY WHITELISTED TABLES (USE THESE ONLY)

```
✅ weather_data (regions: 'US', 'Argentina', 'Brazil')
✅ volatility_data
✅ news_intelligence
✅ social_sentiment
✅ economic_indicators
✅ ice_trump_intelligence
✅ currency_data
✅ soybean_oil_prices
✅ soybean_oil_forecast
✅ soybean_prices
✅ soybean_meal_prices
✅ treasury_prices
✅ corn_prices
✅ cotton_prices
✅ cocoa_prices
✅ fed_rates
✅ backtest_forecast
✅ intelligence_cycles

ARCHIVES (read-only):
✅ commodity_prices_archive
✅ milk_prices_archive
```

---

## ❌ BANNED TABLE PATTERNS (NEVER CREATE)

```
❌ ANY table ending in: _test, _staging, _backup, _tmp, _validation, _v2
❌ Duplicate "weather" tables (e.g., weather_data_validation)
❌ Generic labels like "data", "temp", "test"
❌ Tables not on whitelist above
```

**If you need a new table: STOP and ask user first**

---

## 📋 EXISTING WEATHER_DATA SCHEMA

**Table:** `weather_data`  
**Purpose:** All weather data from all regions  
**Schema:**
```sql
date        DATE       (required)
region      STRING     (required: 'US', 'Argentina', 'Brazil')
station_id  STRING     (required: 'GHCND:xxx' or 'INMET_xxx')
precip_mm   FLOAT64    (precipitation in millimeters)
temp_max    FLOAT64    (max temperature in °C)
temp_min    FLOAT64    (min temperature in °C)
```

**Current Data:**
- US: 2,672 rows (GHCND:USW00014933, GHCND:USW00094846)
- Argentina: 1,342 rows (GHCND:AR000875760, GHCND:AR000875850)
- Brazil: 0 rows (NEEDS INMET DATA)

**Station ID Prefixes:**
- `GHCND:` = NOAA stations (US, Argentina)
- `INMET_` = Brazilian meteorology stations

---

## 🇧🇷 BRAZIL WEATHER STATIONS (ALREADY DEFINED)

**DO NOT CREATE NEW STATION LISTS - USE THESE:**

```python
INMET_STATIONS = {
    "A901": {"name": "Sorriso", "state": "Mato Grosso", "lat": -12.5446, "lon": -55.7125},
    "A923": {"name": "Sinop", "state": "Mato Grosso", "lat": -11.8653, "lon": -55.5058},
    "A936": {"name": "Alta Floresta", "state": "Mato Grosso", "lat": -9.8709, "lon": -56.0862},
    "A702": {"name": "Campo Grande", "state": "MS", "lat": -20.4427, "lon": -54.6479},
    "A736": {"name": "Dourados", "state": "MS", "lat": -22.2192, "lon": -54.8055}
}
```

**Target:** Add Brazil rows to EXISTING `weather_data` table with `region='Brazil'`

---

## 📁 WHITELISTED FOLDERS ONLY

```
✅ cbi-v14-ingestion/  (data ingestion scripts)
✅ forecast/            (FastAPI service)
✅ bigquery_sql/        (SQL scripts)
✅ dashboard/           (React dashboard)
✅ terraform-deploy/    (infrastructure)

❌ BANNED: tmp/, temp/, backup/, test/, staging/
```

---

## 🔒 DATA SOURCES (APPROVED ONLY)

**✅ ALLOWED:**
- CSV files for historical prices (Barchart exports)
- INMET API/portal (Brazil weather, 2023-2025)
- NOAA GHCND (US/Argentina weather)
- FRED API (economic indicators)
- USDA APIs (agricultural data)
- Government sources only

**❌ BANNED:**
- Polygon.io (unreliable, failures)
- Yahoo Finance (inconsistent)
- Docker (we don't use containers)
- Milk/Dairy data (removed from scope)

---

## 🎯 CRITICAL RULES

### 1. APPEND, NEVER REPLACE
```python
# ✅ CORRECT
job_config = bigquery.LoadJobConfig(
    write_disposition="WRITE_APPEND"
)

# ❌ WRONG
job_config = bigquery.LoadJobConfig(
    write_disposition="WRITE_TRUNCATE"  # NEVER ON PRODUCTION TABLES
)
```

### 2. CHECK BEFORE CREATE
```bash
# Always check if table exists first
bq ls cbi-v14:forecasting_data_warehouse

# Check against whitelist
# If not on whitelist → STOP and ask user
```

### 3. NO MOCK DATA
```python
# ❌ WRONG
data = {"price": 50.0}  # Placeholder

# ✅ CORRECT
query = "SELECT * FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`"
data = client.query(query).to_dataframe()
```

### 4. PROTECT WORKING FORECAST
```
❌ DO NOT modify: soybean_oil_forecast
❌ DO NOT rename production tables
❌ DO NOT drop tables without explicit confirmation
```

---

## 📊 CURRENT PROJECT STATUS

**Working (Has Data):**
- ✅ ZL Prices: 519 rows (100% coverage)
- ✅ US Weather: 2,672 rows (89%)
- ⚠️ Argentina Weather: 1,342 rows (39% - needs backfill)
- ✅ Economic Indicators: 3,220 rows
- ⚠️ Treasury: 136 rows (26% - sparse)
- ⚠️ Volatility: 2 rows (0.2% - nearly empty)

**Empty (Needs Data):**
- ❌ Brazil Weather: 0 rows (CRITICAL - 50% of global soy production)
- ❌ Social Sentiment: 0 rows
- ❌ Shipping Alerts: 0 rows
- ❌ ICE/Trump Intel: 0 rows

**Phase:** Pre-training (data collection phase)

---

## 🎯 IMMEDIATE PRIORITIES

1. **Brazil Weather** - Add to existing `weather_data` table (no new tables)
2. **Argentina Backfill** - Add more rows to existing `weather_data` table
3. **Volatility Fix** - Add more rows to existing `volatility_data` table
4. **No Model Training** - Until all data pipelines operational

---

## 🚫 BANNED BEHAVIORS

```
❌ Creating _test, _staging, _validation, _tmp tables
❌ Proposing "clean" architectures with new tables
❌ Editing plan.md automatically
❌ Mock/fake/placeholder data
❌ Running DROP TABLE without confirmation
❌ Using Docker
❌ Adding milk/dairy data
```

---

## ✅ REQUIRED BEHAVIORS

```
✅ ls before create
✅ cat before overwrite
✅ bq ls before table operations
✅ Check whitelist before ANY new resource
✅ WRITE_APPEND to existing tables
✅ Real data or explicit "no data" states
✅ Ask when uncertain
```

---

## 📝 SCRIPT STATUS

**Current Scripts (cbi-v14-ingestion/):**
- `ingest_weather_noaa.py` - US/Argentina (working)
- `ingest_weather_inmet.py` - Brazil (ready to run, uses placeholder data until API implemented)
- `ingest_volatility.py` - VIX data (needs fixing)
- `economic_intelligence.py` - FRED/economic data (working)
- `multi_source_news.py` - News collection (test mode)
- `social_intelligence.py` - Social sentiment (not run yet)
- `shipping_intelligence.py` - Logistics (not run yet)
- `ice_trump_intelligence.py` - Policy intel (not run yet)

**All scripts use `safe_load_to_bigquery()` for batch loading**

---

## 🔑 KEY PRINCIPLE

**ONE TABLE PER DATA TYPE. MULTIPLE REGIONS IN SAME TABLE.**

```
✅ CORRECT: weather_data (regions: US, Argentina, Brazil)
❌ WRONG: weather_data_us, weather_data_brazil, weather_data_validation
```

---

**COMMIT THIS FILE. PASTE AT START OF EVERY CLAUDE CONVERSATION.**

