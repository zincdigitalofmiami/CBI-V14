# 🎯 PRODUCTION SYSTEM MANIFEST - OFFICIAL
**Date**: November 5, 2025  
**Status**: ✅ PRODUCTION MODELS READY

---

## ✅ PRODUCTION BQML MODELS (OFFICIAL - USE THESE)

```
cbi-v14.models_v4.bqml_1w_production  (274 features, Nov 4 trained)
cbi-v14.models_v4.bqml_1m_production  (274 features, Nov 4 trained)
cbi-v14.models_v4.bqml_3m_production  (268 features, Nov 4 trained)
cbi-v14.models_v4.bqml_6m_production  (258 features, Nov 4 trained)
```

**Performance**: MAE ~0.30, R² 0.987, MAPE <1%

---

## ✅ PRODUCTION TRAINING DATASETS (OFFICIAL - USE THESE)

```
cbi-v14.models_v4.production_training_data_1w  (290 cols, 1,448 rows)
cbi-v14.models_v4.production_training_data_1m  (290 cols, 1,347 rows)
cbi-v14.models_v4.production_training_data_3m  (290 cols, 1,329 rows)
cbi-v14.models_v4.production_training_data_6m  (290 cols, 1,198 rows)
```

**Source**: Restored from `training_dataset_pre_integration_backup` (Nov 3 data)

---

## 🔄 DATA FLOW

```
Ingestion Scripts
    ↓
production_training_data_1w/1m/3m/6m (290 features)
    ↓
bqml_1w/1m/3m/6m_production models
    ↓
ML.PREDICT() 
    ↓
Predictions
```

---

## 📋 INGESTION SCRIPTS (MUST UPDATE THESE TABLES)

ALL scripts must INSERT/UPDATE to production_training_data_*:

```bash
hourly_prices.py
daily_weather.py
ingest_social_intelligence_comprehensive.py
backfill_trump_intelligence.py
ingest_market_prices.py
ingest_cftc_positioning_REAL.py
ingest_usda_harvest_api.py
ingest_eia_biofuel_real.py
```

---

## 🚨 IMMEDIATE ACTIONS

1. ✅ Models copied to production names
2. ✅ Datasets created with 290 features
3. ⏳ Update datasets with Nov 4-5 data
4. ⏳ Connect ingestion scripts
5. ⏳ Update execution plan

---

## 🎯 FEATURES IN PRODUCTION MODELS (274)

**Critical Features** (from bqml_1m):
- argentina_export_tax, argentina_china_sales_mt
- china_soybean_sales, china_sentiment
- Big 8 signals (all 8)
- Correlations: ZL-palm, ZL-crude, ZL-VIX, ZL-DXY, ZL-corn, ZL-wheat
- Weather: Brazil, Argentina, US Midwest
- Economic: CPI, GDP, rates, DXY
- CFTC positioning
- News intelligence
- Trump policy events
- Crush margins, seasonal indices

---

**THIS IS THE OFFICIAL PRODUCTION SYSTEM**







