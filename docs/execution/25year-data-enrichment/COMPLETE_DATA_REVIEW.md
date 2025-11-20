---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# 📊 COMPLETE DATA REVIEW & MAPPING
**Date**: November 16, 2025  
**Purpose**: Comprehensive review of all data sources, schemas, relationships, and pipeline destinations

---

## 🎯 CORE MISSION
**Predict Soybean Oil (ZL) futures prices** using 25 years of historical data across:
- Price/Technical (Yahoo Finance)
- Weather (NASA POWER, NOAA, INMET, SMN)
- Economic (FRED)
- Trade/Policy (USDA, CFTC, Tariffs)
- Biofuel (EIA, EPA, LCFS)
- Substitute Oils (World Bank Pink Sheet)

---

## 📁 DATA SOURCES - COMPLETE INVENTORY

### 1. YAHOO FINANCE (Price & Technical Data) ✅

#### **What It's For**
- Primary price data for ZL (Soybean Oil futures)
- Cross-asset correlations (crude oil, palm oil, VIX, dollar index)
- Technical indicators (RSI, MACD, Bollinger Bands, moving averages)
- Volume and volatility metrics

#### **Why It's Used**
- ZL price is the **target variable** we're predicting
- Cross-asset correlations reveal hidden relationships (e.g., ZL vs crude oil)
- Technical indicators capture market momentum and sentiment
- Volume indicates market participation and liquidity

#### **Schema**
```
Location: TrainingData/raw/yahoo_finance/prices/{category}/{symbol}.parquet

Columns:
- Date: datetime (timezone-naive)
- Symbol: string (e.g., 'ZL=F', '^GSPC')
- Open, High, Low, Close: float64 (prices)
- Volume: int64
- [Technical indicators]: float64 (RSI, MACD, etc.)

Categories:
- commodities/ (ZL=F, ZS=F, CL=F, GC=F, etc.)
- indices/ (^GSPC, ^VIX, ^TNX, etc.)
- currencies/ (DX-Y.NYB, EURUSD=X, etc.)
- etfs/ (TLT, XLE, DBA, etc.)
```

#### **Connected To**
- **ZL price** → Target variable (7d, 30d, 90d, 180d, 365d forward returns)
- **Crude oil (CL=F)** → Cross-asset correlation features
- **Palm oil** → Substitute oil spread features
- **VIX** → Volatility regime features
- **Dollar index** → Macro regime features
- **Treasury yields** → Macro regime features

#### **Where It Goes**
1. **Raw**: `TrainingData/raw/yahoo_finance/prices/`
2. **Staging**: `TrainingData/staging/` (after date standardization)
3. **Features**: `TrainingData/features/` (technical indicators calculated)
4. **Exports**: `TrainingData/exports/` (joined with labels for training)

#### **Features Created**
- `tech_ma_7d`, `tech_ma_30d`, `tech_ma_90d`, `tech_ma_200d`
- `tech_rsi_14d`, `tech_rsi_30d`
- `tech_macd_line`, `tech_macd_signal`, `tech_macd_histogram`
- `tech_bb_upper`, `tech_bb_lower`, `tech_bb_width`
- `tech_return_1d`, `tech_return_7d`, `tech_return_30d`
- `cross_corr_zl_crude_7d`, `cross_corr_zl_palm_7d`, `cross_corr_zl_vix_7d`
- `vol_realized_30d`, `vol_realized_90d`

---

### 2. WEATHER DATA ✅

#### **What It's For**
- Crop yield predictions (temperature, precipitation affect soybean production)
- Supply-side shocks (droughts, floods in Brazil/Argentina/US Midwest)
- Seasonal patterns (harvest timing, planting windows)
- Regional production weights (Brazil 40%, US 30%, Argentina 15%)

#### **Why It's Used**
- Weather directly impacts soybean supply → affects ZL prices
- Brazil/Argentina are major exporters → weather there is critical
- US Midwest is major producer → harvest weather matters
- Drought indicators predict supply shortages

#### **Schema**
```
Location: TrainingData/staging/weather_2000_2025.parquet

Columns:
- date: datetime64[ns]
- tavg_c, tmax_c, tmin_c: float64 (temperature in Celsius)
- prcp_mm: float64 (precipitation in mm)
- humidity_pct: float64
- wind_speed_ms: float64
- station_name: string
- latitude, longitude: float64
- region: string ('US_MIDWEST', 'BRAZIL', 'ARGENTINA')
- source: string ('NASA_POWER', 'NOAA_GHCND', 'INMET', 'SMN')
- reliability: float64 (0.85-0.98)
- production_weight: float64 (0.15-0.40)
```

#### **Connected To**
- **Brazil weather** → Brazil production estimates → Export capacity
- **Argentina weather** → Argentina production → Export competition
- **US Midwest weather** → US harvest progress → Supply glut indicators
- **Drought indicators** → Supply shock features → Price volatility

#### **Where It Goes**
1. **Raw**: `TrainingData/raw/weather/` (if collected from APIs)
2. **Staging**: `TrainingData/staging/weather_2000_2025.parquet` ✅ (already here)
3. **Features**: `TrainingData/features/` (aggregated by region, rolling windows)
4. **Exports**: `TrainingData/exports/` (joined on date)

#### **Features Created**
- `weather_brazil_temp`, `weather_brazil_precip`
- `weather_argentina_temp`, `weather_argentina_precip`
- `weather_us_temp`, `weather_us_precip`
- `weather_drought_index_30d`, `weather_drought_index_90d`
- `weather_growing_degree_days`
- `weather_precip_30d_rolling`, `weather_precip_90d_rolling`

---

### 3. FRED ECONOMIC DATA ✅

#### **What It's For**
- Macroeconomic regime classification (Fed policy, inflation, growth)
- Interest rate impacts on commodity prices
- Dollar strength effects on exports
- Economic cycle indicators

#### **Why It's Used**
- Fed policy affects commodity demand (rate hikes → lower demand)
- Dollar strength makes US exports more expensive → affects ZL exports
- Inflation affects real commodity prices
- Economic growth drives demand for vegetable oils

#### **Schema**
```
Location: TrainingData/raw/fred/combined/fred_all_series_{date}.parquet

Columns:
- date: datetime64[ns]
- series_id: string (e.g., 'DGS10', 'DFEDTARU', 'DEXUSEU')
- series_name: string
- value: float64
- realtime_start, realtime_end: datetime64[ns]

Key Series:
- DGS10: 10-Year Treasury Rate
- DFEDTARU/L: Fed Funds Rate (Upper/Lower)
- DEXUSEU: USD/EUR Exchange Rate
- DCOILWTICO: WTI Crude Oil Price
- CPIAUCSL: CPI All Urban
- UNRATE: Unemployment Rate
- T10Y2Y: 10Y-2Y Treasury Spread
```

#### **Connected To**
- **Fed Funds Rate** → Macro regime features → Fed policy impact
- **10Y-2Y Spread** → Yield curve regime → Recession indicators
- **Dollar Index** → USD strength features → Export competitiveness
- **CPI** → Inflation regime → Real price adjustments
- **Crude Oil** → Cross-asset correlation with ZL

#### **Where It Goes**
1. **Raw**: `TrainingData/raw/fred/processed/{series_id}.parquet`
2. **Staging**: `TrainingData/staging/` (after date standardization)
3. **Features**: `TrainingData/features/` (macro regime calculations)
4. **Exports**: `TrainingData/exports/` (joined on date)

#### **Features Created**
- `macro_fed_regime` (accommodative, neutral, restrictive)
- `macro_yield_curve_10y2y` (inverted, flat, normal, steep)
- `macro_inflation_regime` (deflation, low, moderate, high)
- `macro_usd_trend`, `macro_usd_percentile_1y`
- `macro_real_rate` (nominal - inflation)
- `macro_composite_regime` (combined macro score)

---

### 4. CFTC COT DATA ❌ (Needs Replacement)

#### **What It's For**
- Commitment of Traders positioning data
- Speculator vs commercial trader positions
- Market sentiment indicators (extreme positioning → reversals)
- Weekly positioning changes

#### **Why It's Used**
- Extreme speculator positions often precede price reversals
- Commercial trader positions reflect fundamental supply/demand
- COT data is a leading indicator of price movements
- Helps identify overbought/oversold conditions

#### **Schema** (Expected)
```
Location: TrainingData/raw/cftc/ (to be collected)

Columns:
- report_date: datetime64[ns]
- commodity: string ('SOYBEAN OIL')
- market: string ('CHICAGO BOARD OF TRADE')
- open_interest: int64
- noncommercial_long: int64
- noncommercial_short: int64
- commercial_long: int64
- commercial_short: int64
- nonreportable_long: int64
- nonreportable_short: int64
```

#### **Connected To**
- **ZL price** → Positioning extremes → Reversal signals
- **Speculator positions** → Sentiment features → Momentum indicators
- **Commercial positions** → Fundamental supply/demand → Trend confirmation

#### **Where It Goes**
1. **Raw**: `TrainingData/raw/cftc/` (to be collected)
2. **Staging**: `TrainingData/staging/cftc_cot.parquet`
3. **Features**: `TrainingData/features/` (positioning ratios, extremes)
4. **Exports**: `TrainingData/exports/` (joined on report_date)

#### **Features Created** (Planned)
- `cftc_spec_net_position`
- `cftc_spec_position_percentile`
- `cftc_commercial_net_position`
- `cftc_extreme_positioning_flag` (overbought/oversold)

---

### 5. USDA AGRICULTURAL DATA ❌ (Needs Replacement)

#### **What It's For**
- WASDE reports (supply/demand balance)
- Export sales (weekly China purchases)
- Crop progress (harvest timing)
- Acreage and yield estimates

#### **Why It's Used**
- WASDE reports are major price-moving events
- Export sales to China indicate demand strength
- Crop progress affects harvest timing → supply availability
- Acreage/yield estimates affect supply expectations

#### **Schema** (Expected)
```
Location: TrainingData/raw/usda/ (to be collected)

WASDE:
- report_date: datetime64[ns]
- commodity: string ('SOYBEANS', 'SOYBEAN OIL')
- category: string ('BEGINNING STOCKS', 'PRODUCTION', 'EXPORTS', etc.)
- value: float64
- unit: string ('MILLION BUSHELS', 'MILLION POUNDS')

Export Sales:
- week_ending: datetime64[ns]
- commodity: string
- destination: string ('CHINA')
- weekly_exports: float64 (MT)
- outstanding_sales: float64 (MT)
```

#### **Connected To**
- **WASDE reports** → Supply/demand balance → Price regime features
- **Export sales to China** → China demand proxy → Import pace features
- **Crop progress** → Harvest timing → Supply glut indicators
- **Acreage/yield** → Production estimates → Supply expectations

#### **Where It Goes**
1. **Raw**: `TrainingData/raw/usda/` (to be collected)
2. **Staging**: `TrainingData/staging/usda_{type}.parquet`
3. **Features**: `TrainingData/features/` (supply/demand ratios, export pace)
4. **Exports**: `TrainingData/exports/` (joined on date)

#### **Features Created** (Planned)
- `usda_supply_demand_ratio`
- `usda_ending_stocks_to_use_ratio`
- `usda_china_export_pace_4w`
- `usda_harvest_progress_pct`
- `usda_wasde_event_flag` (1 on report days)

---

### 6. EIA BIOFUEL DATA ⚠️ (Needs Verification)

#### **What It's For**
- Biodiesel production (demand for soybean oil)
- Renewable diesel production
- Biofuel stocks and inputs
- RIN prices (D4, D5, D6)

#### **Why It's Used**
- Biodiesel/renewable diesel are major ZL demand drivers
- Production levels indicate demand strength
- RIN prices reflect policy support for biofuels
- Biofuel mandates create structural demand

#### **Schema** (Current)
```
Location: TrainingData/raw/eia/combined/eia_all_{date}.parquet

Columns:
- date: datetime64[ns]
- series_id: string
- value: float64
- unit: string
```

#### **Connected To**
- **Biodiesel production** → Biofuel demand features → ZL demand proxy
- **RIN prices** → Policy support features → Mandate strength
- **Renewable diesel** → Growing demand segment → Long-term trend

#### **Where It Goes**
1. **Raw**: `TrainingData/raw/eia/`
2. **Staging**: `TrainingData/staging/eia_biofuels.parquet`
3. **Features**: `TrainingData/features/` (biofuel demand indices)
4. **Exports**: `TrainingData/exports/` (joined on date)

#### **Features Created** (Planned)
- `biofuel_production_4w_ma`
- `biofuel_production_yoy_change`
- `biofuel_demand_index`
- `rin_price_d4`, `rin_price_d5`, `rin_price_d6`
- `biofuel_policy_strength` (based on RIN prices)

---

### 7. WORLD BANK PINK SHEET 🆕 (To Be Collected)

#### **What It's For**
- Monthly FOB prices for all major vegetable oils
- Compute FOB spreads (soybean oil vs palm, sunflower, rapeseed)
- Long-history price anchors (1960s→present)
- Substitute oil competitiveness

#### **Why It's Used**
- FOB spreads indicate relative competitiveness
- Palm oil is a major substitute → spread affects demand
- Long history enables regime analysis
- Spreads predict demand shifts between oils

#### **Schema** (Expected)
```
Location: TrainingData/raw/wb_pinksheet/{commodity}_{date}.parquet

Columns:
- date: datetime64[ns]
- price_usd_per_mt: float64
- commodity: string ('Soybean Oil (Argentina)', 'Palm Oil (Malaysia)', etc.)
- source: string ('WORLD_BANK_PINK_SHEET')
```

#### **Connected To**
- **Palm oil price** → Palm-ZL spread → Substitute competitiveness
- **Sunflower oil** → Sunflower-ZL spread → Alternative demand
- **Rapeseed oil** → Rapeseed-ZL spread → European market competition

#### **Where It Goes**
1. **Raw**: `TrainingData/raw/wb_pinksheet/`
2. **Staging**: `TrainingData/staging/wb_vegoil_prices.parquet`
3. **Features**: `TrainingData/features/` (FOB spreads calculated)
4. **Exports**: `TrainingData/exports/` (joined on date)

#### **Features Created** (Planned)
- `spread_sbo_palm` (Soybean Oil - Palm Oil)
- `spread_sun_sbo` (Sunflower - Soybean Oil)
- `spread_rapeseed_sbo` (Rapeseed - Soybean Oil)
- `substitute_oil_competitiveness_index`

---

### 8. EPA RIN PRICES 🆕 (To Be Collected)

#### **What It's For**
- Weekly RIN price averages (D4, D5, D6)
- Policy support indicators
- Biofuel mandate strength

#### **Why It's Used**
- RIN prices reflect policy support for biofuels
- Higher RIN prices → stronger mandate → more ZL demand
- Weekly updates provide timely policy signals

#### **Schema** (Expected)
```
Location: TrainingData/raw/rins_epa/rin_prices_{date}.parquet

Columns:
- date: datetime64[ns] (week ending)
- rin_type: string ('D4', 'D5', 'D6')
- avg_price: float64 (USD)
- low_price, high_price: float64
- volume: int64
- source: string ('EPA_EMTS')
```

#### **Connected To**
- **RIN prices** → Biofuel policy features → Mandate strength
- **D4 RINs** → Biodiesel mandate → ZL demand
- **D5/D6 RINs** → Advanced biofuels → Long-term demand

#### **Where It Goes**
1. **Raw**: `TrainingData/raw/rins_epa/`
2. **Staging**: `TrainingData/staging/rin_prices.parquet`
3. **Features**: `TrainingData/features/` (policy strength indices)
4. **Exports**: `TrainingData/exports/` (joined on date)

---

### 9. USDA FAS ESR 🆕 (To Be Collected)

#### **What It's For**
- Weekly US export sales to China
- China purchase pace indicator
- Demand strength signal

#### **Why It's Used**
- China is the largest ZL importer
- Weekly purchase pace indicates demand strength
- Export sales are leading indicators of price movements

#### **Schema** (Expected)
```
Location: TrainingData/raw/usda_fas_esr/esr_china_purchases_{date}.parquet

Columns:
- week_ending: datetime64[ns]
- commodity: string ('soybeans', 'soybean_oil')
- destination: string ('CHINA')
- weekly_exports: float64 (MT)
- outstanding_sales: float64 (MT)
- unit: string ('MT')
- source: string ('USDA_FAS_ESR')
```

#### **Connected To**
- **China export sales** → China demand proxy → Import pace features
- **Outstanding sales** → Future demand pipeline → Forward demand

#### **Where It Goes**
1. **Raw**: `TrainingData/raw/usda_fas_esr/`
2. **Staging**: `TrainingData/staging/esr_china_weekly.parquet`
3. **Features**: `TrainingData/features/` (China demand indices)
4. **Exports**: `TrainingData/exports/` (joined on week_ending)

---

## 🔗 DATA RELATIONSHIPS & JOINS

### Primary Join Key: **DATE**

All data sources join on `date` (or `week_ending`, `report_date` aligned to date):

```
ZL Price (daily)
  ↓
Weather (daily) → JOIN on date
  ↓
FRED (daily/monthly) → JOIN on date (forward fill monthly)
  ↓
CFTC (weekly) → JOIN on report_date (forward fill to next report)
  ↓
USDA (weekly/monthly) → JOIN on week_ending/report_date
  ↓
EIA (monthly) → JOIN on date (forward fill)
  ↓
World Bank (monthly) → JOIN on date (forward fill)
  ↓
EPA RIN (weekly) → JOIN on week_ending
  ↓
USDA FAS ESR (weekly) → JOIN on week_ending
```

### Join Specification
Defined in: `registry/join_spec.yaml`

Key rules:
- **Forward fill** for lower-frequency data (monthly → daily)
- **Backward fill** for missing values (within 7 days)
- **Production weights** for regional weather (Brazil 40%, US 30%, Argentina 15%)

---

## 📊 FEATURE ENGINEERING PIPELINE

### Stage 1: Technical Indicators
**Input**: Yahoo Finance price data  
**Output**: `tech_*` features (RSI, MACD, moving averages, etc.)  
**Script**: `scripts/features/feature_calculations.py::calculate_technical_indicators()`

### Stage 2: Cross-Asset Features
**Input**: Multiple Yahoo Finance symbols  
**Output**: `cross_*` features (correlations, spreads)  
**Script**: `scripts/features/feature_calculations.py::calculate_cross_asset_features()`

### Stage 3: Volatility Features
**Input**: Price data  
**Output**: `vol_*` features (realized volatility, VIX regime)  
**Script**: `scripts/features/feature_calculations.py::calculate_volatility_features()`

### Stage 4: Seasonal Features
**Input**: Date column  
**Output**: `seas_*` features (day of week, month, harvest season)  
**Script**: `scripts/features/feature_calculations.py::calculate_seasonal_features()`

### Stage 5: Macro Regime Features
**Input**: FRED economic data  
**Output**: `macro_*` features (Fed regime, yield curve, inflation)  
**Script**: `scripts/features/feature_calculations.py::calculate_macro_regime_features()`

### Stage 6: Weather Aggregations
**Input**: Weather data (staging)  
**Output**: `weather_*` features (regional temp/precip, drought indices)  
**Script**: `scripts/features/feature_calculations.py::calculate_weather_aggregations()`

### Stage 7: Regime Assignments
**Input**: All features  
**Output**: `regime_*` columns (regime calendar, weights)  
**Script**: `scripts/features/feature_calculations.py::add_regime_columns()`

### Stage 8: Override Flags
**Input**: All features  
**Output**: `flag_*` columns (data quality, outliers)  
**Script**: `scripts/features/feature_calculations.py::add_override_flags()`

---

## 🎯 TARGET VARIABLES (Labels)

### Forward Returns (8 Horizons)
**Input**: ZL price data  
**Output**: `target_7d`, `target_30d`, `target_90d`, `target_180d`, `target_365d`  
**Script**: `scripts/labels/generate_labels.py`

**Calculation**:
```python
target_7d = (price_7d_future - price_current) / price_current
target_30d = (price_30d_future - price_current) / price_current
# ... etc
```

**Critical**: Uses **groupwise shifting** to prevent data leakage (shift by date, not by row)

---

## 📦 FINAL EXPORT STRUCTURE

### Training Dataset
**Location**: `TrainingData/exports/training_{horizon}.parquet`

**Columns**:
- `date`: datetime64[ns] (primary key)
- `target_{horizon}`: float64 (forward return)
- `tech_*`: Technical indicators (50+ features)
- `cross_*`: Cross-asset features (20+ features)
- `vol_*`: Volatility features (10+ features)
- `seas_*`: Seasonal features (15+ features)
- `macro_*`: Macro regime features (20+ features)
- `weather_*`: Weather features (15+ features)
- `regime_*`: Regime assignments (5+ features)
- `flag_*`: Quality flags (5+ features)

**Total**: ~150+ features per date

---

## ⚠️ DATA QUALITY GATES

### Quarantine Rules
**Location**: `TrainingData/quarantine/`

**Triggers**:
- Missing date column
- Invalid date ranges (future dates, pre-2000)
- Out-of-range values (negative prices, extreme temperatures)
- BigQuery contamination (dbdate types)
- Duplicate dates

### Validation Checks
**Script**: `scripts/qa/data_validation.py`

- **Range checks**: Prices > 0, temperatures -50 to 60°C
- **Missing data**: < 5% missing for critical columns
- **Date continuity**: No gaps > 30 days for daily data
- **Outlier detection**: Z-score > 4 flagged

---

## 🔄 UPDATE FREQUENCY

| Source | Frequency | Update Script | Schedule |
|-------|-----------|---------------|----------|
| Yahoo Finance | Daily | `daily_data_updates.py` | Daily 4:30pm ET |
| FRED | Daily/Monthly | `daily_data_updates.py` | Daily 6:00am ET |
| Weather | Daily | `collect_weather_production_v2.py` | Daily 6:00am ET |
| CFTC COT | Weekly (Fridays) | `collect_cftc_comprehensive.py` | Weekly Saturday |
| USDA Export Sales | Weekly (Thursdays) | `collect_usda_fas_esr.py` | Weekly Friday |
| EIA Biofuels | Monthly | `collect_eia_comprehensive.py` | Monthly 15th |
| EPA RIN | Weekly | `collect_epa_rin_prices.py` | Weekly Monday |
| World Bank | Monthly | `collect_worldbank_pinksheet.py` | Monthly 1st |

---

## 📝 NOTES

1. **UN Comtrade**: ❌ Cannot use (requires API registration)
   - **Alternative**: China Customs Statistics web scraping
   - **Alternative**: Use USDA FAS ESR for China import proxy

2. **DCE/CBOT Basis**: Requires licensed access or vendor feed
   - **Alternative**: Use World Bank monthly spreads for long-run analysis

3. **Historical Coverage**: Not all sources have full 25-year history
   - Document actual coverage in feature registry
   - Use monthly proxies where daily unavailable

4. **BigQuery**: NOT a data source (thin read layer only)
   - All data collected locally to external drive
   - BigQuery only for dashboard reads

---

## ✅ NEXT STEPS

1. ✅ Weather data: Collected and staged (37,808 records)
2. ✅ Yahoo Finance: Collected (74 symbols), updating daily
3. ✅ FRED: Collected (16 series), current
4. ⏳ CFTC: Needs replacement (BQ contamination)
5. ⏳ USDA: Needs replacement (BQ contamination)
6. ⏳ EIA: Needs verification
7. 🆕 World Bank Pink Sheet: Script ready, needs testing
8. 🆕 EPA RIN: Script ready, needs testing
9. 🆕 USDA FAS ESR: Script ready, needs testing
