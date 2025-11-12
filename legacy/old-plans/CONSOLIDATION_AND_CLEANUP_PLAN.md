# 🧹 CONSOLIDATION & CLEANUP PLAN
**Date:** November 5, 2025  
**Goal:** Merge ALL data into production tables, archive everything else

---

## ✅ OFFICIAL PRODUCTION SYSTEM (KEEP THESE ONLY)

### MODELS (DO NOT TOUCH):
- `cbi-v14.models_v4.bqml_1w`
- `cbi-v14.models_v4.bqml_1m`
- `cbi-v14.models_v4.bqml_3m`
- `cbi-v14.models_v4.bqml_6m`

### DATASETS (CONSOLIDATE EVERYTHING HERE):
- `cbi-v14.models_v4.production_training_data_1w` (300 features)
- `cbi-v14.models_v4.production_training_data_1m` (300 features)
- `cbi-v14.models_v4.production_training_data_3m` (300 features)
- `cbi-v14.models_v4.production_training_data_6m` (300 features)

---

## 📊 STEP 1: IDENTIFY ALL DATA SOURCES

### Core Data (YEARS of history):
- `forecasting_data_warehouse.soybean_oil_prices` → ZL prices
- `neural.vw_big_eight_signals` → Big 8 features (through Nov 6!)
- `models_v4.cftc_daily_filled` → CFTC positioning
- `forecasting_data_warehouse.palm_oil_prices` → Palm prices
- `forecasting_data_warehouse.commodity_prices` → Corn, wheat, etc.
- `forecasting_data_warehouse.vix_data` → VIX
- `forecasting_data_warehouse.dxy_data` → Dollar index
- `forecasting_data_warehouse.treasury_yields` → 10Y yield
- `forecasting_data_warehouse.fed_funds_rate` → Fed rates

### News & Sentiment:
- `forecasting_data_warehouse.news_intelligence`
- `forecasting_data_warehouse.social_sentiment`
- `forecasting_data_warehouse.trump_policy_intelligence`

### Economic Data:
- `forecasting_data_warehouse.cpi_data`
- `forecasting_data_warehouse.gdp_data`
- `forecasting_data_warehouse.economic_indicators`

### Weather:
- `forecasting_data_warehouse.weather_brazil`
- `forecasting_data_warehouse.weather_argentina`
- `forecasting_data_warehouse.weather_us_midwest`

### Trade Data:
- `forecasting_data_warehouse.china_soybean_imports`
- `forecasting_data_warehouse.argentina_crisis_tracker`
- `forecasting_data_warehouse.usda_export_sales`

### Daily Aggregations (Already processed):
- `models_v4.news_intelligence_daily`
- `models_v4.cftc_daily_filled`
- `models_v4.palm_oil_complete`
- `models_v4.social_sentiment_daily`
- `models_v4.trump_policy_daily`
- `models_v4.usda_export_daily`
- `models_v4.currency_complete`

---

## 🔄 STEP 2: MEGA-CONSOLIDATION QUERY

```sql
-- This will pull ALL available data into production tables
-- Using Big 8 signals dates as master (has data through Nov 6)
```

---

## 🗄️ STEP 3: ARCHIVE OLD TABLES

### Tables to Archive (prefix with _ARCHIVED_):
- training_dataset_super_enriched (broken, 11 cols)
- training_dataset_automl
- training_dataset_current
- enhanced_features_automl (broken view)
- Any other training_dataset_* variants

### Tables to Keep (for ingestion):
- All tables in forecasting_data_warehouse (source data)
- Daily aggregation tables in models_v4
- Production tables (obviously)

---

## 🎯 IMPLEMENTATION STEPS

1. **Run Mega-Consolidation** (Pull all data into production)
2. **Verify Data Coverage** (Check dates are current)
3. **Archive Old Tables** (Prefix with _ARCHIVED_)
4. **Update All Ingestion Scripts** (Point to production tables)
5. **Document Final Structure** (Single source of truth)

---

## ✅ EXPECTED RESULT

- **4 production tables** with ALL historical data (2020-2025)
- **Data through Nov 6, 2025** (current!)
- **No duplicate tables** (archived/hidden)
- **Clear ingestion path** (everything → production_training_data_*)
- **No confusion** about which table to use

---

## 🚫 WHAT NOT TO DO

- ❌ Don't create new tables
- ❌ Don't rename production tables
- ❌ Don't delete source data (forecasting_data_warehouse)
- ❌ Don't touch the models

---

Ready to execute? This will be the FINAL cleanup!






