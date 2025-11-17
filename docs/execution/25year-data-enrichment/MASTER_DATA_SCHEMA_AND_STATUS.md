# 📊 MASTER DATA SCHEMA & STATUS DOCUMENT
**Date**: November 17, 2025  
**Status**: Complete Repository Schema & Data Status  
**Purpose**: Single source of truth for all data schemas, folder structure, collection status, gaps, and problems

---

## 📁 FOLDER STRUCTURE (External Drive)

```
/Volumes/Satechi Hub/Projects/CBI-V14/
├── TrainingData/
│   ├── raw/                    # Immutable source zone (API downloads, never edited)
│   │   ├── yahoo_finance/      # Yahoo Finance data (73 symbols)
│   │   │   ├── prices/         # OHLCV + technical indicators
│   │   │   │   ├── commodities/ (21 files)
│   │   │   │   ├── currencies/ (18 files)
│   │   │   │   ├── indices/ (15 files)
│   │   │   │   ├── etfs/ (17 files)
│   │   │   │   └── volatility/ (2 files)
│   │   │   ├── technical/      # Technical indicators (separate files)
│   │   │   └── fundamentals/   # Fundamental data (if available)
│   │   ├── fred/               # FRED Economic Data (34 series)
│   │   │   ├── raw_responses/  # Raw JSON responses
│   │   │   ├── processed/      # Processed parquet files (one per series)
│   │   │   ├── combined/       # Combined datasets
│   │   │   └── metadata/       # Collection metadata
│   │   ├── weather/            # Weather data
│   │   │   ├── noaa/           # NOAA US/Argentina weather
│   │   │   ├── inmet/          # INMET Brazil weather
│   │   │   └── smn/            # SMN Argentina weather
│   │   ├── cftc/               # CFTC COT data (NEEDS REPLACEMENT - BQ contaminated)
│   │   ├── usda/               # USDA data (NEEDS REPLACEMENT - BQ contaminated)
│   │   ├── eia/                # EIA biofuel data (GASOLINE ONLY - needs biodiesel)
│   │   ├── epa/                # EPA RIN prices (if collected)
│   │   ├── worldbank/          # World Bank Pink Sheet (if collected)
│   │   └── .cache/             # Cache directory (outside raw/ to avoid pollution)
│   │       └── fred/           # FRED cache files
│   │
│   ├── staging/                # Validated, conformed (units/timezones/dtypes fixed)
│   │   ├── weather_2000_2025.parquet
│   │   ├── yahoo_historical_all_symbols.parquet (if combined)
│   │   ├── fred_macro_2000_2025.parquet
│   │   ├── cftc_cot_2006_2025.parquet (when replaced)
│   │   ├── usda_nass_2000_2025.parquet (when replaced)
│   │   └── eia_biofuels_2010_2025.parquet (when fixed)
│   │
│   ├── features/               # Engineered signals (Big 8, tech, macro, weather)
│   │   └── (Feature-engineered datasets)
│   │
│   ├── labels/                 # Forward targets by horizon (7d, 30d, 90d, etc.)
│   │   ├── target_1w.parquet
│   │   ├── target_1m.parquet
│   │   ├── target_3m.parquet
│   │   ├── target_6m.parquet
│   │   └── target_12m.parquet
│   │
│   ├── exports/                # Final training parquet per horizon
│   │   ├── zl_training_prod_allhistory_1w.parquet
│   │   ├── zl_training_prod_allhistory_1m.parquet
│   │   ├── zl_training_prod_allhistory_3m.parquet
│   │   ├── zl_training_prod_allhistory_6m.parquet
│   │   ├── zl_training_prod_allhistory_12m.parquet
│   │   ├── zl_training_last10y_1w.parquet (to be created)
│   │   ├── zl_training_last10y_1m.parquet (to be created)
│   │   ├── zl_training_last10y_3m.parquet (to be created)
│   │   ├── zl_training_last10y_6m.parquet (to be created)
│   │   └── zl_training_last10y_12m.parquet (to be created)
│   │
│   └── quarantine/            # Failed validations (human triage)
│       ├── bq_contaminated/    # BigQuery-contaminated files
│       │   ├── cftc_cot.parquet
│       │   ├── usda_export_sales.parquet
│       │   └── usda_harvest_progress.parquet
│       └── bq_contaminated_exports/  # Contaminated exports
│
├── registry/
│   ├── join_spec.yaml          # Declarative joins with tests
│   ├── data_sources.yaml       # Data source registry
│   ├── feature_registry.json   # Semantic metadata (reliability, impact)
│   └── regime_calendar.parquet # Static regime assignments
│
└── scripts/
    ├── ingest/                 # API pulls → raw/ (or quarantine/)
    ├── conform/                # raw/ → staging/ (validation)
    ├── features/               # staging/ → features/ (calculations)
    ├── labels/                 # Date offsets → labels/
    ├── assemble/               # features + labels → exports/
    └── qa/                     # Automated QA gates
```

---

## 📊 DATA SCHEMA SPECIFICATIONS

### 1. Yahoo Finance Data Schema

**Location**: `TrainingData/raw/yahoo_finance/prices/{category}/{symbol}.parquet`

**Required Columns**:
- `Date` (datetime64[ns]) - Trading date (no timezone)
- `Symbol` (string) - Symbol identifier (e.g., "ZL=F")
- `Open` (float64) - Opening price
- `High` (float64) - High price
- `Low` (float64) - Low price
- `Close` (float64) - Closing price
- `Volume` (int64) - Trading volume

**Technical Indicators** (calculated):
- `SMA_5`, `SMA_10`, `SMA_20`, `SMA_50`, `SMA_200` - Simple moving averages
- `EMA_12`, `EMA_26` - Exponential moving averages
- `RSI_14` - Relative Strength Index (0-100)
- `MACD_line`, `MACD_signal`, `MACD_histogram` - MACD indicators
- `BB_upper`, `BB_middle`, `BB_lower` - Bollinger Bands
- `Stoch_K`, `Stoch_D` - Stochastic oscillator
- `ATR_14` - Average True Range
- `ADX_14` - Average Directional Index
- `OBV` - On-Balance Volume
- `CCI_20` - Commodity Channel Index
- `Williams_%R` - Williams %R
- `ROC_10` - Rate of Change
- `Momentum_10` - Momentum
- `Return_1d`, `Return_7d`, `Return_30d` - Returns
- `Volatility_30d` - Rolling volatility

**Validation Rules**:
- ✅ No `High < Low` violations
- ✅ No negative prices (except treasury yields which can be negative)
- ✅ Date column sorted ascending
- ✅ No duplicate dates per symbol
- ✅ Technical indicators calculated from real price data (zero fake data)

**Status**: ✅ **73 symbols collected** (21 commodities, 18 currencies, 15 indices, 17 ETFs, 2 volatility)

---

### 2. FRED Economic Data Schema

**Location**: `TrainingData/raw/fred/processed/{series_id}.parquet`

**Required Columns**:
- `date` (datetime64[ns]) - Observation date
- `value` (float64) - Series value
- `series_id` (string) - FRED series identifier
- `series_name` (string) - Human-readable name

**Series Collected** (34/35):
- Interest Rates: DFF, DGS10, DGS2, DGS30, DGS5, DGS3MO, DGS1, DFEDTARU, DFEDTARL
- Inflation: CPIAUCSL, CPILFESL, PCEPI, DPCCRV1Q225SBEA
- Employment: UNRATE, PAYEMS, CIVPART, EMRATIO
- GDP & Production: GDP, GDPC1, INDPRO, DGORDER
- Money Supply: M2SL, M1SL, BOGMBASE
- Market Indicators: VIXCLS, DTWEXBGS, DTWEXEMEGS
- Credit Spreads: BAAFFM, T10Y2Y, T10Y3M
- Commodities: DCOILWTICO, GOLDPMGBD228NLBM
- Other: HOUST, UMCSENT, DEXUSEU

**Validation Rules**:
- ✅ Sorted by date before any calculations
- ✅ No hard-coded API keys (uses environment variable)
- ✅ Cache fallback works correctly (`fred_{series_id}.pkl`)
- ✅ Date range: 2000-01-01 to present

**Status**: ✅ **34/35 series collected** (103,029 records)

---

### 3. Weather Data Schema

**Location**: `TrainingData/staging/weather_2000_2025.parquet`

**Required Columns**:
- `date` (datetime64[ns]) - Observation date
- `region` (string) - Region identifier (US_MIDWEST, ARGENTINA, BRAZIL)
- `station_id` (string) - Weather station ID
- `tmax_f` (float64) - Maximum temperature (Fahrenheit)
- `tmin_f` (float64) - Minimum temperature (Fahrenheit)
- `prcp_inches` (float64) - Precipitation (inches)
- `temp_avg_f` (float64) - Average temperature (Fahrenheit)

**Sources**:
- **NOAA GHCN-D**: US Midwest weather (10 stations)
- **INMET**: Brazil weather (10 stations)
- **SMN**: Argentina weather (10 stations)

**Validation Rules**:
- ✅ Temperatures in Fahrenheit (as requested)
- ✅ Precipitation in inches
- ✅ Date range: 2000-01-01 to present
- ✅ No missing critical dates

**Status**: ✅ **37,808 records collected** (2000-2025)

---

### 4. CFTC COT Data Schema

**Location**: `TrainingData/staging/cftc_cot_2006_2025.parquet` (TO BE REPLACED)

**Required Columns**:
- `date` (datetime64[ns]) - Report date (Fridays)
- `symbol` (string) - Contract symbol (e.g., "ZL")
- `open_interest` (int64) - Total open interest
- `noncommercial_long` (int64) - Non-commercial long positions
- `noncommercial_short` (int64) - Non-commercial short positions
- `commercial_long` (int64) - Commercial long positions
- `commercial_short` (int64) - Commercial short positions
- `nonreportable_long` (int64) - Non-reportable long positions
- `nonreportable_short` (int64) - Non-reportable short positions

**Validation Rules**:
- ✅ Only available after 2006-01-01
- ✅ Weekly frequency (Fridays)
- ✅ No BigQuery contamination

**Status**: ❌ **NEEDS REPLACEMENT** (currently in quarantine - BQ contaminated)

---

### 5. USDA Data Schema

**Location**: `TrainingData/staging/usda_nass_2000_2025.parquet` (TO BE REPLACED)

**Required Columns**:
- `date` (datetime64[ns]) - Report date
- `report_type` (string) - Report type (WASDE, Crop Progress, etc.)
- `commodity` (string) - Commodity (Soybeans, Soybean Oil, etc.)
- `field` (string) - Data field (Production, Stocks, Exports, etc.)
- `value` (float64) - Value
- `unit` (string) - Unit (million bushels, thousand metric tons, etc.)

**Validation Rules**:
- ✅ Monthly/weekly frequency (varies by report)
- ✅ No BigQuery contamination
- ✅ Proper date formatting

**Status**: ❌ **NEEDS REPLACEMENT** (currently in quarantine - BQ contaminated)

---

### 6. EIA Biofuel Data Schema

**Location**: `TrainingData/raw/eia/combined/eia_all_20251116.parquet`

**Required Columns**:
- `date` (datetime64[ns]) - Observation date
- `series_id` (string) - EIA series identifier
- `value` (float64) - Value
- `unit` (string) - Unit

**Expected Series**:
- Biodiesel production (2001→present)
- Renewable diesel production (2013→present)
- Biodiesel stocks
- Renewable diesel stocks

**Validation Rules**:
- ✅ Monthly frequency
- ✅ Date range: 2001→present (biodiesel), 2013→present (renewable diesel)

**Status**: ⚠️ **GASOLINE ONLY** (1,702 records) - **NEEDS BIODIESEL DATA**

---

## ✅ DATA COLLECTION STATUS

### Collected & Clean ✅

| Source | Records | Date Range | Status | Location |
|--------|---------|------------|--------|----------|
| Yahoo Finance | 6,380+ | 2000-03-15 to 2025-11-14 | ✅ Complete | `raw/yahoo_finance/prices/` |
| FRED Economic | 103,029 | 2000-01-01 to 2025-11-16 | ✅ Complete | `raw/fred/processed/` |
| Weather (NOAA/INMET/SMN) | 37,808 | 2000-01-01 to 2025-11-16 | ✅ Complete | `staging/weather_2000_2025.parquet` |

### Needs Replacement ❌

| Source | Issue | Status | Action Required |
|--------|-------|--------|-----------------|
| CFTC COT | BigQuery contamination | ❌ Quarantined | Replace with fresh collection from CFTC |
| USDA Agricultural | BigQuery contamination | ❌ Quarantined | Replace with fresh collection from USDA |
| EIA Biofuels | Only gasoline data | ⚠️ Incomplete | Collect biodiesel/renewable diesel data |

### Not Yet Collected ⏳

| Source | Priority | Coverage | Script Status |
|--------|----------|----------|---------------|
| EPA RIN Prices | Medium | 2010→present | ✅ Script ready, needs testing |
| World Bank Pink Sheet | Medium | 1960s→present | ✅ Script ready, needs testing |
| USDA FAS ESR | High | 25+ years | ✅ Script ready, needs testing |
| UN Comtrade (China) | High | 2000→present | ⚠️ Needs API registration |
| DCE/CBOT Basis | High | ~2000→present | ⏳ Needs licensed access |
| MARA Hogs | Medium | 2010s→present | ⏳ Not started |
| ASF Severity | Medium | 2018→present | ⏳ Not started |
| Section 301 Tariffs | Medium | 2018→present | ⏳ Not started |

---

## 🚨 KNOWN PROBLEMS & ISSUES

### Critical Issues 🔴

1. **CFTC COT Data Contaminated**
   - **Problem**: Files contain BigQuery-specific data types (`dbdate`, `dbdatetime`)
   - **Location**: `quarantine/bq_contaminated/cftc_cot.parquet`
   - **Impact**: Cannot be used for training
   - **Solution**: Replace with fresh collection from CFTC legacy URLs
   - **Script**: `scripts/ingest/collect_cftc_comprehensive.py` (needs URL fix)

2. **USDA Data Contaminated**
   - **Problem**: Files contain BigQuery-specific data types
   - **Location**: `quarantine/bq_contaminated/usda_*.parquet`
   - **Impact**: Cannot be used for training
   - **Solution**: Replace with fresh collection from USDA APIs
   - **Script**: `scripts/ingest/collect_usda_comprehensive.py` (needs duplicate column fix)

3. **EIA Biofuel Data Incomplete**
   - **Problem**: Current file only contains gasoline data, missing biodiesel/renewable diesel
   - **Location**: `raw/eia/combined/eia_all_20251116.parquet`
   - **Impact**: Missing critical biofuel demand data
   - **Solution**: Collect biodiesel and renewable diesel series
   - **Script**: `scripts/ingest/collect_eia_comprehensive.py` (needs API endpoint fix)

### Medium Issues 🟡

4. **UN Comtrade API Registration**
   - **Problem**: API returns HTML instead of JSON (requires registration)
   - **Impact**: Cannot collect China soybean import data
   - **Solution**: Register for API access or use alternative endpoint
   - **Script**: `scripts/ingest/collect_un_comtrade.py`

5. **DCE/CBOT Data Access**
   - **Problem**: Requires licensed access or vendor feed
   - **Impact**: Missing China demand proxy (basis spread)
   - **Solution**: Use Nasdaq Data Link CHRIS or license CME
   - **Alternative**: Compute monthly spreads from World Bank Pink Sheet

6. **Export Count Mismatch**
   - **Problem**: Acceptance requires 10 exports, exporter only creates 5
   - **Impact**: QA gates will fail
   - **Solution**: Update exporter to create both `allhistory` and `last10y` variants
   - **Status**: Defined in QA gate, exporter needs update

### Minor Issues 🟢

7. **Labels Directory Not Materialized**
   - **Problem**: Labels created on-the-fly in exporter, but spec advertises `labels/` directory
   - **Impact**: Directory contract inconsistency
   - **Solution**: Either materialize labels/ directory OR update spec to match reality
   - **Status**: Pending decision

8. **Cache Directory Location**
   - **Problem**: Cache files should not be in `raw/` (immutable zone)
   - **Solution**: ✅ Fixed - cache moved to `.cache/` directory
   - **Status**: ✅ Resolved

---

## 📋 DATA GAPS ANALYSIS

### Critical Gaps (Block Training) 🔴

1. **CFTC COT Data**: Missing positioning data (2006→present)
   - **Impact**: Cannot calculate positioning features
   - **Priority**: P0 (Critical)
   - **Timeline**: Replace immediately

2. **USDA Agricultural Data**: Missing supply/demand fundamentals
   - **Impact**: Cannot calculate supply/demand features
   - **Priority**: P0 (Critical)
   - **Timeline**: Replace immediately

3. **EIA Biofuel Data**: Missing biodiesel/renewable diesel
   - **Impact**: Cannot calculate biofuel demand features
   - **Priority**: P0 (Critical)
   - **Timeline**: Fix immediately

### High Priority Gaps (Affect Model Quality) 🟠

4. **China Demand Proxy**: Missing DCE/CBOT basis, State Reserve actions
   - **Impact**: Cannot accurately model China demand
   - **Priority**: P1 (High)
   - **Timeline**: Implement within 1 week

5. **Tariff Intelligence**: Missing Section 301 tariffs, MOFCOM retaliation
   - **Impact**: Cannot model trade policy impacts
   - **Priority**: P1 (High)
   - **Timeline**: Implement within 1 week

### Medium Priority Gaps (Nice to Have) 🟡

6. **Substitute Oils**: Missing palm oil, rapeseed oil prices
   - **Impact**: Cannot model substitution effects
   - **Priority**: P2 (Medium)
   - **Timeline**: Implement within 2 weeks

7. **Biofuel Policy**: Missing CARB LCFS, Oregon CFP credits
   - **Impact**: Cannot model policy-driven demand
   - **Priority**: P2 (Medium)
   - **Timeline**: Implement within 2 weeks

---

## 🎯 NEXT STEPS (Priority Order)

### Immediate (This Week)
1. ✅ Fix CFTC COT collection script (URL fix)
2. ✅ Fix USDA collection script (duplicate column fix)
3. ✅ Fix EIA biofuel collection (API endpoint fix)
4. ✅ Replace contaminated data with fresh collection

### Short Term (Next 2 Weeks)
5. ⏳ Test EPA RIN, World Bank Pink Sheet, USDA FAS ESR scripts
6. ⏳ Implement China demand proxy (DCE/CBOT basis or alternative)
7. ⏳ Implement tariff intelligence collection
8. ⏳ Update exporter to create 10 exports (allhistory + last10y)

### Medium Term (Next Month)
9. ⏳ Resolve labels directory contract
10. ⏳ Implement substitute oils collection
11. ⏳ Implement biofuel policy collection
12. ⏳ Complete 25-year backfill for all sources

---

## 📝 SCHEMA VALIDATION CHECKLIST

### For Each Data Source:
- [x] Date column is `datetime64[ns]` (no timezone)
- [x] Date column sorted ascending
- [x] No duplicate dates (or duplicate date-symbol pairs)
- [x] Required columns present
- [x] Data types correct (float64 for prices, int64 for volumes)
- [x] No BigQuery contamination (`dbdate`, `dbdatetime` types)
- [x] No placeholder values (0, -1, 999, etc.)
- [x] No fake calculations (all indicators from real data)
- [x] Date range matches expected coverage
- [x] Join compatibility verified

---

## 🔗 JOIN SPECIFICATION

See `registry/join_spec.yaml` for complete declarative join specification.

**Key Joins**:
1. Base prices (Yahoo Finance) → Macro (FRED)
2. Base + Macro → Weather
3. Base + Macro + Weather → CFTC (2006+)
4. Base + Macro + Weather + CFTC → USDA
5. Base + Macro + Weather + CFTC + USDA → EIA Biofuels (2010+)
6. All → Regimes (every date must have regime)

**Join Tests**: All enforced by `scripts/assemble/join_executor.py`

---

**Last Updated**: November 17, 2025  
**Maintained By**: Data Engineering Team  
**Review Frequency**: Weekly

