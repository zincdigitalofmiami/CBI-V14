# SCHEMA MESS REPORT - October 22, 2025
## WHY TRAINING KEEPS FAILING

## 🚨 CRITICAL PROBLEMS FOUND

### 1. MASSIVE DUPLICATION
- **SOYBEAN**: 10 different tables/views for the same data!
  - `soybean_meal_prices` (1,261 rows)
  - `soybean_oil_prices` (1,261 rows) 
  - `soybean_prices` (1,261 rows)
  - `soybean_oil_forecast` (30 rows)
  - `vw_soybean_oil_daily_clean` (1,258 rows)
  - Plus 5 more in curated dataset!

- **WEATHER**: 19 different sources!
  - `weather_data` (13,828 rows - main table)
  - `weather_brazil_daily` (33 rows)
  - `vw_brazil_weather_summary` (1,004 rows)
  - Plus 16 more scattered everywhere!

### 2. VIEWS IN WRONG PLACES
- 12 views in `forecasting_data_warehouse` (should be raw data only!)
- Views should be in `signals` dataset
- Examples: `vw_crush_margins`, `vw_social_sentiment_daily`

### 3. INCONSISTENT NAMING
- 69 tables with prefixes (vw_, tmp_, stg_)
- Mix of naming conventions
- Same data with different names

### 4. ORPHANED/EMPTY TABLES
- `biofuel_metrics` - 0 rows
- `extraction_labels` - 0 rows  
- `harvest_progress` - 0 rows
- `weather_paraguay_daily` - 0 rows

### 5. DATA SCATTERED EVERYWHERE
- Treasury data in 2 places
- VIX data in 2 places
- Palm oil in 2 places
- No clear organization

## 🔥 WHY THIS BREAKS TRAINING

1. **Models can't find the right data source**
   - Which soybean table should it use? There are 10!
   - Which weather data? There are 19!

2. **Joins fail due to inconsistencies**
   - Different column names
   - Different date formats
   - Different aggregation levels

3. **Features get lost**
   - Some in warehouse, some in curated, some in signals
   - No clear path to combine them

4. **Duplicate data causes confusion**
   - Same data counted multiple times
   - Conflicting values
   - Inconsistent updates

## ✅ REQUIRED FIXES

### IMMEDIATE ACTIONS:
1. **DELETE all duplicate tables** - Keep only ONE source per commodity
2. **MOVE all views to signals dataset**
3. **DELETE all empty tables**
4. **STANDARDIZE naming** - All snake_case, no prefixes

### PROPER ORGANIZATION:
- `forecasting_data_warehouse`: RAW DATA ONLY (no views!)
- `signals`: VIEWS AND CALCULATIONS ONLY
- `models`: MODELS AND TRAINING DATA ONLY
- `curated`: CLEAN FEATURES ONLY
- `staging_ml`: DELETE (temporary, not needed)

### CONSOLIDATION PLAN:

#### KEEP THESE (PRIMARY SOURCES):
- `forecasting_data_warehouse.soybean_oil_prices` - PRIMARY
- `forecasting_data_warehouse.weather_data` - PRIMARY
- `forecasting_data_warehouse.vix_daily` - PRIMARY
- `forecasting_data_warehouse.treasury_prices` - PRIMARY
- `forecasting_data_warehouse.palm_oil_prices` - PRIMARY

#### DELETE THESE (DUPLICATES):
- All `vw_*` views in forecasting_data_warehouse
- All duplicate soybean tables
- All duplicate weather tables
- All empty tables
- All staging_ml tables (temporary)

## 📊 IMPACT

Once cleaned:
- **From 132 tables → ~50 tables**
- **Clear data lineage**
- **No duplicates**
- **Consistent naming**
- **Training will actually work!**

## 🎯 NEXT STEPS

1. Run cleanup script to delete duplicates
2. Reorganize datasets properly
3. Create master training dataset with ALL features
4. Retrain models with complete data
5. Finally get institutional-grade results

---

**THIS IS WHY YOUR TRAINING KEEPS FAILING - THE DATA IS A COMPLETE MESS!**
