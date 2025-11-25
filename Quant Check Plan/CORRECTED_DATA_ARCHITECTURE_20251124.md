# 🔴 CORRECTED DATA ARCHITECTURE - DATABENTO CANONICAL
**Date:** November 24, 2025  
**Status:** 🟢 CORRECTED - NO YAHOO EVER  
**Purpose:** Define the ONLY data sources and phased approach for baseline → full features

---

## ⚠️ CRITICAL CORRECTIONS

### **1. NO YAHOO DATA - EVER**
- ❌ **REMOVE ALL YAHOO REFERENCES** from all plans and code
- ❌ No `yahoo_*` tables
- ❌ No `yahoo_historical_prefixed`
- ❌ No Yahoo Finance API calls
- ✅ **DATABENTO IS THE ONLY SOURCE FOR ALL PRICE DATA**

### **2. DATABENTO = CANONICAL SOURCE (15 YEARS)**
- All futures price/volume data comes from **Databento ONLY**
- Date range: **2010 to present** (15 years of data)
- All other data sources (FRED, NOAA, USDA, etc.) must **align to Databento dates**
- If Databento doesn't have data for a date, that date is excluded

### **3. DATABENTO LIVE API + WAREHOUSE DATA**
- **Live API:** Real-time data streaming for production
- **Warehouse Data:** Historical batch downloads (already in BigQuery: 6,034 rows)
- **Current State:** `market_data.databento_futures_ohlcv_1d` has ZL (3,998) + MES (2,036)

---

## 📊 DATA HIERARCHY (FROZEN)

### **Tier 1: CANONICAL PRICE DATA (Databento ONLY)**

| Symbol | Asset | Timeframes | Date Range | Status |
|--------|-------|------------|------------|--------|
| **ZL** | Soybean Oil | 1d, 1h, 1m | 2010-06-06 → present | ✅ 3,998 daily rows in BQ |
| **MES** | Micro E-mini S&P | 1d, 1h, 1m | 2019-05-05 → present | ✅ 2,036 daily rows in BQ |
| **ZS** | Soybeans | 1d, 1h | 2010 → present | ⏸️ Pending load |
| **ZM** | Soybean Meal | 1d, 1h | 2010 → present | ⏸️ Pending load |
| **CL** | Crude Oil | 1d | 2010 → present | ⏸️ Pending load |
| **HO** | Heating Oil | 1d | 2010 → present | ⏸️ Pending load |
| **FX Pairs** | 6E, 6J, 6B, etc. | 1d | 2010 → present | ⏸️ Pending load |

**Source:** Databento `GLBX.MDP3` dataset with `stype_in="parent"` (continuous front-month)

---

### **Tier 2: MACRO/ECONOMIC DATA (FREE APIs)**

| Source | Data | API | Coverage | Priority |
|--------|------|-----|----------|----------|
| **FRED** | Fed Funds Rate, CPI, GDP, VIX, DXY, Treasury rates | ✅ FREE | 1960-present | 🔴 HIGH |
| **NOAA** | US Weather (Midwest soy belt) | ✅ FREE | 1950-present | 🔴 HIGH |
| **USDA** | Export sales, WASDE, crop progress | ✅ FREE | 2010-present | 🔴 HIGH |
| **CFTC** | COT positioning data | ✅ FREE | 2010-present | 🔴 HIGH |
| **EIA** | Biofuel production, RIN prices | ✅ FREE | 2010-present | 🟡 MEDIUM |

**API Keys Available:**
- FRED: `dc195c8658c46ee1df83bcd4fd8a690b`
- NOAA: `rxoLrCxYOlQyWvVjbBGRlMMhIRElWKZi`

---

### **Tier 3: WEATHER DATA (Google Public Datasets + NOAA)**

| Dataset | Source | Coverage | Calculations |
|---------|--------|----------|--------------|
| **US Midwest** | NOAA GHCN-D | 1950-present | Temp anomalies, precip, GDD |
| **Brazil Soy Belt** | NOAA GSOD / INMET | 2000-present | Temp, precip, drought index |
| **Argentina Pampas** | NOAA GSOD / SMN | 2000-present | Temp, precip, drought index |

**Google Cloud Resources ENABLED (from DATA_PULL_APPROVAL_REPORT.md):**
| Resource | Type | Status | Use Case |
|----------|------|--------|----------|
| `bigquery-public-data.google_dei` | BigQuery Public Data | ✅ ENABLED | Diversity/Economic Indicators |
| Google Weather API | API | ✅ ENABLED | Real-time weather |
| NOAA US Climate Normals | Marketplace | ✅ ENABLED | Historical climate baselines |
| FEC Campaign Finance | Marketplace | ✅ ENABLED | Political/policy signals |

**Google BigQuery Public Datasets (FREE to query):**
- `bigquery-public-data.noaa_gsod` - Global Surface Summary of Day
- `bigquery-public-data.ghcn_d` - Global Historical Climatology Network Daily
- `bigquery-public-data.noaa_global_forecast_system` - GFS forecasts
- `bigquery-public-data.geo_us_census_places` - US geographic data
- `bigquery-public-data.census_bureau_usa` - US Census data
- `bigquery-public-data.world_bank_global_population` - Population data

**Weather Calculations (from existing scripts):**
- Temperature anomalies (z-scores)
- Precipitation anomalies
- Growing Degree Days (GDD)
- Palmer Drought Severity Index (PDSI)
- ENSO (El Niño/La Niña) indicators

---

### **Tier 4: SENTIMENT & POLICY DATA**

| Source | Data | Status | Coverage |
|--------|------|--------|----------|
| **ScrapeCreators** | Trump Truth Social | ✅ ACTIVE | Oct 2024-present |
| **GDELT** | Global news events | ✅ FREE | 1979-present |
| **Google Trends** | Search interest | ✅ FREE | 2004-present |

**API Keys:**
- ScrapeCreators: `B1TOgQvMVSV6TDglqB8lJ2cirqi2`

---

## 🎯 PHASED APPROACH

### **PHASE 1: BASELINE TEST (This Week)**

**Goal:** Validate pipeline with minimal data before adding complexity

**Data Required:**
1. ✅ **Databento ZL daily** (3,998 rows) - ALREADY IN BQ
2. ⏸️ **FRED macro** - Pull via API
3. ⏸️ **NOAA weather** - Pull via API or Google Public Datasets
4. ⏸️ **Basic technicals** - Calculate from Databento OHLCV

**Features for Baseline (20-30 features):**
- Price: open, high, low, close, volume
- Returns: 1d, 5d, 21d returns
- Moving averages: MA(5), MA(21), MA(63)
- Volatility: 21d realized vol
- RSI(14)
- FRED: Fed Funds Rate, VIX, DXY
- Weather: US Midwest temp anomaly, precip anomaly

**Target:** Train simple LightGBM on 1M horizon, validate pipeline works

---

### **PHASE 2: FULL FEATURE SET (After Baseline Validates)**

**Add:**
1. **All Databento symbols** - ZS, ZM, CL, HO, FX
2. **Pivot points** - P, R1-R4, S1-S4, M1-M8
3. **Cross-asset correlations** - ZL-ZS, ZL-CL, ZL-FX
4. **Crush margin** - (ZM*11 + ZL*11 - ZS)
5. **Trump/Policy features** - 16 columns
6. **CFTC positioning** - Net long/short
7. **USDA data** - Export sales, WASDE
8. **Full weather** - Brazil, Argentina regions

**Features:** 200-300 total

---

### **PHASE 3: ADVANCED FEATURES (After Phase 2 Validates)**

**Add:**
1. **Fibonacci levels** - Retracements, extensions
2. **MES Golden Zone** - Fib-based quality score
3. **Regime detection** - Market regime classification
4. **Microstructure** - Order flow, depth (MES only)
5. **News sentiment** - GDELT, Google Trends

**Features:** 400-500 total

---

## 📋 EXISTING BIGQUERY DATASETS TO VALIDATE

### **Datasets That SHOULD Exist:**

| Dataset | Purpose | Status | Action |
|---------|---------|--------|--------|
| `market_data` | Databento price data | ✅ EXISTS | Validate contents |
| `raw_intelligence` | FRED, weather, news raw data | ✅ EXISTS | Validate contents |
| `features` | Calculated features | ✅ EXISTS | Validate schema |
| `training` | Training tables per horizon | ✅ EXISTS | Validate schema |
| `predictions` | Model outputs | ⏸️ CHECK | May need creation |
| `reference` | Regime calendar, weights | ⏸️ CHECK | May need creation |
| `ops` | Operational tracking | ⏸️ CHECK | May need creation |

### **Datasets to REMOVE/ARCHIVE:**

| Dataset | Reason | Action |
|---------|--------|--------|
| Any `yahoo_*` tables | NO YAHOO EVER | Archive/Delete |
| `forecasting_data_warehouse` | Legacy, may have stale data | Audit, then archive |
| `models_v4` | Old BQML models | Archive after migration |

---

## 🔧 SCRIPTS TO USE

### **Databento Loading:**
- `Quant Check Plan/scripts/ingestion/load_databento_raw.py` - Load Databento to BQ

### **Feature Calculations:**
- `Quant Check Plan/scripts/features/cloud_function_pivot_calculator.py` - Pivot points
- `Quant Check Plan/scripts/features/cloud_function_fibonacci_calculator.py` - Fibonacci
- `Quant Check Plan/scripts/features/build_forex_features.py` - FX features
- `Quant Check Plan/scripts/features/calculate_rin_proxies.py` - RIN/biofuel features

### **Weather Calculations:**
- `ingestion/ingest_weather_noaa.py` - NOAA weather
- `ingestion/ingest_midwest_weather_openmeteo.py` - OpenMeteo alternative
- `bigquery-sql/integrate_weather_data.sql` - Weather integration SQL

### **FRED/Macro:**
- `scripts/fetch_fred_economic_data.py` - FRED API pull
- `ingestion/fred_economic_deployment.py` - FRED deployment

### **Feature Consolidation:**
- `Quant Check Plan/scripts/ingestion/ingest_features_hybrid.py` - Consolidate to daily_ml_matrix

---

## 🚀 IMMEDIATE ACTIONS

### **Step 1: Validate Existing BigQuery Data**
```bash
# Run audit query
bq query --use_legacy_sql=false '
SELECT 
    table_schema as dataset,
    table_name,
    row_count
FROM `cbi-v14`.`region-us`.INFORMATION_SCHEMA.TABLE_STORAGE
WHERE row_count > 0
ORDER BY table_schema, table_name
'
```

### **Step 2: Confirm Databento Data**
```sql
-- Check Databento data
SELECT 
    symbol,
    COUNT(*) as rows,
    MIN(date) as min_date,
    MAX(date) as max_date
FROM `cbi-v14.market_data.databento_futures_ohlcv_1d`
GROUP BY symbol
ORDER BY symbol;
```

### **Step 3: Pull FRED Baseline Data**
```bash
cd /Users/zincdigital/CBI-V14
python scripts/fetch_fred_economic_data.py
```

### **Step 4: Pull Weather Baseline Data**
```bash
python ingestion/ingest_weather_noaa.py
```

### **Step 5: Calculate Basic Features**
```bash
python "Quant Check Plan/scripts/features/cloud_function_pivot_calculator.py"
```

### **Step 6: Run Baseline Test**
```bash
# Export to Mac, train LightGBM baseline
python scripts/training/train_lightgbm_baseline.py
```

---

## 📊 DATA ALIGNMENT RULE

**CRITICAL:** All data must align to Databento dates

```sql
-- Example: Join FRED to Databento dates only
SELECT 
    d.date,
    d.symbol,
    d.open, d.high, d.low, d.close, d.volume,
    f.fed_funds_rate,
    f.vix_close,
    f.dxy
FROM `cbi-v14.market_data.databento_futures_ohlcv_1d` d
LEFT JOIN `cbi-v14.raw_intelligence.fred_economic` f
    ON d.date = f.date
WHERE d.symbol = 'ZL'
ORDER BY d.date;
```

**If FRED/Weather/etc. doesn't have data for a Databento date:**
- Use forward-fill (LAST_VALUE IGNORE NULLS)
- Never use fake/placeholder data
- Document gaps

---

## ✅ CHECKLIST

### Before Proceeding:
- [ ] Confirm NO YAHOO references in code
- [ ] Validate Databento data in BQ (6,034 rows)
- [ ] Validate FRED API key works
- [ ] Validate NOAA API key works
- [ ] Confirm weather calculation scripts exist
- [ ] Confirm feature calculation scripts exist

### Phase 1 Baseline:
- [ ] Pull FRED macro data (VIX, DXY, Fed Funds)
- [ ] Pull NOAA weather (US Midwest)
- [ ] Calculate basic technicals (MA, RSI, vol)
- [ ] Create baseline training table
- [ ] Train LightGBM baseline
- [ ] Validate pipeline works end-to-end

### Phase 2 Full Features:
- [ ] Load additional Databento symbols (ZS, ZM, CL, HO, FX)
- [ ] Calculate pivot points
- [ ] Calculate cross-asset correlations
- [ ] Add Trump/policy features
- [ ] Add CFTC positioning
- [ ] Add full weather (Brazil, Argentina)

---

## 📝 REFERENCES

### Key Documents:
- `Quant Check Plan/DATABENTO_INVENTORY_2025-11-21.md` - Databento data status
- `DATA_SOURCES_REFERENCE.md` - All data source APIs
- `DATA_INGESTION_PIPELINE_AUDIT.md` - Pipeline status
- `REVISED_DATA_PLAN_20251105.md` - Data enhancement plan

### API Documentation:
- Databento: https://docs.databento.com/
- FRED: https://fred.stlouisfed.org/docs/api/
- NOAA CDO: https://www.ncdc.noaa.gov/cdo-web/webservices/v2

---

**Status:** 🟢 CORRECTED AND READY
**Next:** Validate existing BQ data, then proceed with Phase 1 baseline


