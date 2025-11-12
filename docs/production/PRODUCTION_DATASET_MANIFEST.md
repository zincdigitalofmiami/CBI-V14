# 🎯 PRODUCTION DATASET MANIFEST - FINAL VERSION
**Last Updated**: November 5, 2025  
**Status**: ✅ PRODUCTION DATASETS RESTORED

---

## ⚠️ CRITICAL: ONLY USE THESE DATASETS

### ✅ PRODUCTION TRAINING DATASETS (THE ONLY ONES TO USE)

```
cbi-v14.models_v4.production_training_data_1w  (290 features, 1,448 rows)
cbi-v14.models_v4.production_training_data_1m  (290 features, 1,347 rows)
cbi-v14.models_v4.production_training_data_3m  (290 features, 1,329 rows)
cbi-v14.models_v4.production_training_data_6m  (290 features, 1,198 rows)
```

**Features**: 290 columns including:
- Price data (ZL, corn, wheat, palm, crude)
- Big 8 signals (all 8 features)
- Correlations (ZL-palm, ZL-crude, ZL-VIX, ZL-DXY, etc.)
- Weather (Brazil, Argentina, US Midwest)
- Economic (CPI, GDP, rates, yields, FX)
- China data (imports, sentiment, policy)
- Argentina data (export tax, sales, conditions)
- Industrial demand index
- CFTC positioning
- News sentiment
- Trump policy intelligence
- Social sentiment

**Purpose**: Official training data for BQML prediction models  
**Updated By**: ALL ingestion scripts MUST update these tables  

---

## ✅ PRODUCTION BQML MODELS (THE ONLY ONES TO USE)

1. `cbi-v14.models_v4.bqml_1w` - Uses `production_training_data_1w`
2. `cbi-v14.models_v4.bqml_1m` - Uses `production_training_data_1m`
3. `cbi-v14.models_v4.bqml_3m` - Uses `production_training_data_3m`
4. `cbi-v14.models_v4.bqml_6m` - Uses `production_training_data_6m`

**Each model trained on**: 258-274 features (290 total - NULL columns - targets)

---

## 🔄 DATA FLOW (PRODUCTION ONLY)

```
1. Data Ingestion Scripts (hourly/daily/weekly)
   ↓
2. forecasting_data_warehouse.* (raw tables)
   ↓
3. Feature Engineering Scripts
   ↓
4. production_training_data_1w/1m/3m/6m (MAIN DATASETS - 290 features)
   ↓
5. BQML Models (bqml_1w/1m/3m/6m)
   ↓
6. ML.PREDICT() queries
   ↓
7. Predictions output
```

---

## ❌ DEPRECATED DATASETS (DO NOT USE EVER!)

### Deprecated Tables
```
training_dataset_super_enriched (11 columns - BROKEN!)
training_dataset_super_enriched_backup
training_dataset_pre_integration_backup (source for restore)
training_dataset_pre_forwardfill_backup
training_dataset_pre_coverage_fix_backup
_ARCHIVED_* (all archived tables)
```

**Status**: All marked "DEPRECATED - DO NOT USE"

---

## 📋 INGESTION SCRIPTS - MUST UPDATE PRODUCTION DATASETS

### Current Cron Jobs (NEED TO BE UPDATED):
```
hourly_prices.py → MUST update production_training_data_*
daily_weather.py → MUST update production_training_data_*
ingest_social_intelligence_comprehensive.py → MUST update production_training_data_*
backfill_trump_intelligence.py → MUST update production_training_data_*
ingest_market_prices.py → MUST update production_training_data_*
ingest_cftc_positioning_REAL.py → MUST update production_training_data_*
ingest_usda_harvest_api.py → MUST update production_training_data_*
ingest_eia_biofuel_real.py → MUST update production_training_data_*
```

### Required Changes:
Each ingestion script must INSERT/UPDATE rows in ALL 4 production datasets:
- production_training_data_1w
- production_training_data_1m
- production_training_data_3m
- production_training_data_6m

---

## 🚨 CRITICAL FIXES NEEDED

### Issue #1: Data Staleness
- 1W latest: Oct 13 (23 days old)
- 1M latest: Sept 10 (56 days old)
- 3M latest: June 13 (145 days old)
- 6M latest: Feb 4 (275 days old)

### Issue #2: refresh_features_pipeline.py
- Currently overwrites with 11-column table
- MUST BE FIXED to update production_training_data_* tables

### Issue #3: No Ingestion Integration
- Cron jobs running but not updating production datasets
- Need to connect all ingestion to production_training_data_*

---

## ✅ Verification Commands

```bash
# Verify production datasets
bq query --nouse_legacy_sql "SELECT table_name, row_count FROM \`cbi-v14.models_v4.__TABLES__\` WHERE table_name LIKE 'production_training_data%'"

# Verify latest dates
bq query --nouse_legacy_sql "SELECT 'production_training_data_1w' as dataset, MAX(date) as latest FROM \`cbi-v14.models_v4.production_training_data_1w\`"

# Verify column counts
bq query --nouse_legacy_sql "SELECT table_name, COUNT(*) as cols FROM \`cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS\` WHERE table_name LIKE 'production_training_data%' GROUP BY table_name"
```

---

## 🚀 NEXT STEPS (IMMEDIATE)

1. ✅ Restore complete (4 datasets created)
2. ⏳ Fix refresh_features_pipeline.py to NOT overwrite
3. ⏳ Connect ALL ingestion scripts to production_training_data_*
4. ⏳ Backfill missing dates (Oct 13 → Nov 5)
5. ⏳ Update execution plan
6. ⏳ Retrain BQML models on fresh data

---

**REMEMBER**: If anyone mentions a different dataset, STOP and refer to this document!

**THE MAIN DATASETS**: `production_training_data_1w/1m/3m/6m` - 290 features - ALL INGESTION GOES HERE!
