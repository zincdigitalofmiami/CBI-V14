# 📊 HISTORICAL DATA LOCATIONS - Complete Inventory

**Date**: November 16, 2025  
**Status**: Current Data Inventory

---

## 🎯 SUMMARY

Historical data exists in **TWO locations**:

1. **BigQuery** (Legacy/Existing Data)
   - `yahoo_finance_comprehensive` dataset - Historical price data
   - `forecasting_data_warehouse` dataset - 108,487+ rows across 45+ tables
   - **Note**: This is LEGACY data. New training uses local drive only.

2. **External Drive** (Primary Source for New Training)
   - `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/`
   - **332 files** in `raw/` directory
   - **19 files** in `exports/` directory
   - **Status**: Partially populated, needs backfilling for 25-year coverage

---

## 📍 LOCATION 1: BIGQUERY (Legacy Data)

### Dataset: `yahoo_finance_comprehensive`
**Purpose**: Historical price data (20+ years)  
**Status**: ✅ Active, preserved  
**Location**: `cbi-v14.yahoo_finance_comprehensive.*`  
**Note**: Plan says "Keep yahoo_finance_comprehensive" - this is valuable historical data

**Tables Include**:
- Historical price data for all symbols
- 20+ years of market data
- **This is the main historical data source**

### Dataset: `forecasting_data_warehouse`
**Purpose**: Legacy training and intelligence data  
**Status**: ✅ Active (but not primary source for new training)  
**Location**: `cbi-v14.forecasting_data_warehouse.*`

**Historical Data Inventory** (from archive documents):
- **108,487 rows** across 45+ tables
- **Prices**: 16,655 rows (soybean oil, crude oil, grains, energy, financial, vegetable oils)
- **Intelligence**: 2,719 rows (social sentiment, Trump policy, news)
- **Market Data**: 65,211 rows (VIX, volatility, currency, USD index)
- **Fundamentals**: 9,944 rows (CFTC COT, USDA, economic indicators, biofuel)
- **Weather**: 13,958 rows (general weather, regional data)

**Key Tables**:
- `soybean_oil_prices`: 2,254 rows
- `crude_oil_prices`: 2,265 rows
- `social_sentiment`: 3,718 rows
- `weather_data`: 13,828 rows
- `vix_daily`: 508 rows
- `trump_policy_intelligence`: 215 rows
- And 40+ more tables

**Training Dataset**:
- `training_dataset_super_enriched`: 1,251 rows × 159 features
- Date range: 2020-2025 (one row per trading day)

---

## 📍 LOCATION 2: EXTERNAL DRIVE (Primary Source)

### Path: `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/`

### Current Status
- **Raw Directory**: 332 parquet files
- **Exports Directory**: 19 parquet files
- **Staging Directory**: Empty (needs data from raw)
- **Features Directory**: Empty (needs processing)
- **Labels Directory**: Empty (needs generation)

### Existing Files on External Drive

#### Raw Data (`TrainingData/raw/`)
**Found Files**:
- `models_v4/training_dataset_super_enriched.parquet` - 1,251 rows
- `models_v4/yahoo_finance_weekend_complete.parquet`
- `models_v4/yahoo_indicators_wide.parquet`
- `models_v4/baseline_1m_comprehensive_2yr.parquet`
- `models_v4/full_220_comprehensive_2yr.parquet`
- `models_v4/production_training_data_12m.parquet`
- `models_v4/production_training_data_1m.parquet`
- `models_v4/production_training_data_1w.parquet`
- `models_v4/production_training_data_3m.parquet`
- `models_v4/production_training_data_6m.parquet`
- `forecasting_data_warehouse/yahoo_finance_historical.parquet`
- `forecasting_data_warehouse/yahoo_finance_enhanced.parquet`
- And 320+ more files

#### Exports Data (`TrainingData/exports/`)
**Found Files**:
- `full_220_comprehensive_2yr.parquet`
- And 18+ more export files

### Data Gaps
**Missing for 25-Year Coverage**:
- ❌ 25-year historical data (currently have ~2-5 years)
- ❌ Full FRED economic data (2000-2025)
- ❌ Complete weather history (25 years)
- ❌ Full CFTC COT data (25 years)
- ❌ Complete USDA data (25 years)
- ❌ Full sentiment history (25 years)

**This is what Phase 1 will backfill.**

---

## 🔄 DATA MIGRATION STRATEGY

### From BigQuery → Local Drive (Phase 1)

**Strategy**: Export historical data from BigQuery to local drive for new training

**Key Data to Export**:
1. **yahoo_finance_comprehensive** - All historical price data
2. **forecasting_data_warehouse** - All existing intelligence data
3. **Training datasets** - Existing training data for reference

**Export Scripts Needed**:
- `scripts/migration/export_yahoo_finance.py` - Export yahoo_finance_comprehensive
- `scripts/migration/export_warehouse_data.py` - Export forecasting_data_warehouse tables
- `scripts/migration/load_from_external_drive.py` - Already exists

### Data Flow for New Training
```
BigQuery (Legacy) → Export → Local Drive raw/ → staging/ → features/ → exports/
```

---

## 📋 DATA AVAILABILITY BY SOURCE

### ✅ Available Now (BigQuery)
- **yahoo_finance_comprehensive**: 20+ years historical prices
- **forecasting_data_warehouse**: 108,487+ rows of intelligence data
- **Training datasets**: 1,251 rows (2020-2025)

### ⚠️ Partially Available (External Drive)
- **Raw data**: 332 files (mix of old and new)
- **Exports**: 19 files (limited coverage)
- **Staging**: Empty (needs processing)
- **Features**: Empty (needs engineering)
- **Labels**: Empty (needs generation)

### ❌ Missing (Needs Backfilling)
- **25-year FRED data**: Economic indicators (2000-2025)
- **25-year weather data**: Complete historical weather
- **25-year CFTC data**: Complete COT reports
- **25-year USDA data**: Complete WASDE, export sales, harvest progress
- **25-year sentiment**: Complete social/news sentiment history
- **25-year policy data**: Complete Trump/policy intelligence

---

## 🎯 PHASE 1 DATA COLLECTION PRIORITIES

### Tier 1 Critical Gaps (Must-Have)
1. **China Demand Composite** (8 sub-series)
   - Monthly China soy imports (FAS/USDA)
   - Weekly purchase pace
   - Dalian vs CBOT basis spread
   - State reserve actions
   - China crush margins
   - Hog herd size
   - ASF outbreak severity
   - Tariff/quota timeline

2. **Tariff Intelligence** (Dated Events)
   - Section 301 timelines
   - Exclusion lists
   - Retaliatory schedules
   - Trade deal milestones

3. **Biofuel Policy & Prices**
   - EIA biodiesel/renewable diesel production
   - RIN prices (D4, D5, D6)
   - LCFS credit prices
   - Mandate paths

4. **Substitute Oils** (Full History)
   - Palm oil (FCPO/MPOB)
   - Sunflower oil
   - Rapeseed/canola oil
   - Corn oil
   - FOB spreads

### Data Sources
- **FRED**: Economic indicators (2000-2025)
- **NOAA**: Weather data (25 years)
- **USDA**: WASDE, export sales, harvest progress
- **CFTC**: COT reports (25 years)
- **EIA**: Biofuel production data
- **Google Public Datasets**: Additional historical data

---

## 📊 DATA TIMELINE

### Current Coverage
- **BigQuery**: ~5 years (2020-2025) for most data, 20+ years for yahoo_finance
- **External Drive**: ~2-5 years (varies by data type)

### Target Coverage
- **25 years**: 2000-2025 (full historical range)
- **All data types**: Prices, weather, fundamentals, sentiment, policy

### Backfill Plan
- **Phase 1**: Collect Tier 1 critical gaps
- **Phase 1**: Export existing BigQuery data to local drive
- **Phase 1**: Backfill missing historical data from APIs
- **Result**: Complete 25-year dataset on local drive

---

## 🔍 HOW TO ACCESS DATA

### From BigQuery (Legacy)
```python
from google.cloud import bigquery
client = bigquery.Client(project='cbi-v14', location='us-central1')

# yahoo_finance_comprehensive
query = "SELECT * FROM `cbi-v14.yahoo_finance_comprehensive.*` LIMIT 100"

# forecasting_data_warehouse
query = "SELECT * FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`"
```

### From Local Drive (Primary)
```python
from pathlib import Path
import pandas as pd

drive = Path("/Volumes/Satechi Hub/Projects/CBI-V14")

# Raw data
df = pd.read_parquet(drive / "TrainingData/raw/data_name.parquet")

# Staging data (preferred)
df = pd.read_parquet(drive / "TrainingData/staging/data_name.parquet")

# Exports (final training data)
df = pd.read_parquet(drive / "TrainingData/exports/horizon_1w.parquet")
```

---

## ⚠️ IMPORTANT NOTES

1. **BigQuery is Legacy**: Existing data in BigQuery is valuable but we're moving to local drive for new training
2. **Export Needed**: Phase 1 will export BigQuery data to local drive
3. **Backfill Required**: Missing 25-year coverage needs to be collected
4. **yahoo_finance_comprehensive**: This is the main historical data source - preserve it
5. **Data Source Priority**: Local drive is primary, BigQuery is reference/legacy

---

## 📝 NEXT STEPS

1. **Export BigQuery Data**: Create scripts to export all historical data to local drive
2. **Backfill Missing Data**: Collect 25-year historical data from APIs
3. **Validate Coverage**: Ensure all data types have 25-year coverage
4. **Process to Staging**: Move raw data through staging → features → exports

---

**Last Updated**: November 16, 2025  
**Next Review**: After Phase 1 data collection
