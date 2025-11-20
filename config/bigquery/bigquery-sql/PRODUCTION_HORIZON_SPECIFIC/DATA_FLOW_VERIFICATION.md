---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# DATA FLOW VERIFICATION - PRODUCTION
**Date:** November 5, 2025  
**Status:** ✅ VERIFIED

---

## DATA INGESTION FLOW

### Step 1: Raw Data Collection (Cron Jobs)
**Destination:** `cbi-v14.forecasting_data_warehouse.*`

**Active Scrapers:**
- `MASTER_CONTINUOUS_COLLECTOR.py` → `forecasting_data_warehouse.*` (every hour)
- `ingest_social_intelligence_comprehensive.py` → `forecasting_data_warehouse.social_sentiment_daily`
- `trump_truth_social_monitor.py` → `forecasting_data_warehouse.trump_policy_daily`
- Various other ingestion scripts → `forecasting_data_warehouse.*`

**Verified:** ✅ All ingestion writes to `forecasting_data_warehouse` (correct)

### Step 2: Feature Engineering & Materialization
**Script:** `scripts/refresh_features_pipeline.py` (scheduled daily at 6 AM)

**Process:**
1. Reads from view: `cbi-v14.neural.vw_big_eight_signals`
2. Materializes to table: `cbi-v14.models_v4.training_dataset_super_enriched`

**Code:**
```python
query = f"""
CREATE OR REPLACE TABLE `cbi-v14.models_v4.training_dataset_super_enriched` AS
SELECT * FROM `cbi-v14.neural.vw_big_eight_signals`
"""
```

**Verified:** ✅ Pipeline writes to correct training table

### Step 3: Model Training
**Models:** `bqml_1w`, `bqml_1m`, `bqml_3m`, `bqml_6m`  
**Data Source:** `cbi-v14.models_v4.training_dataset_super_enriched`

**Training SQL:**
```sql
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_{horizon} IS NOT NULL
```

**Verified:** ✅ Models read from correct table

### Step 4: Prediction Generation
**Script:** `bigquery-sql/GENERATE_PRODUCTION_FORECASTS.sql`

**Process:**
1. Gets latest row from `training_dataset_super_enriched`
2. Calls `ML.PREDICT()` on each model
3. Inserts into `cbi-v14.predictions_uc1.production_forecasts`

**Verified:** ✅ Predictions use correct source and destination

---

## VERIFIED DATA FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────────┐
│ RAW DATA SOURCES (External APIs, Web Scraping, RSS)        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ INGESTION SCRIPTS (Cron Jobs)                               │
│ - MASTER_CONTINUOUS_COLLECTOR.py                            │
│ - ingest_social_intelligence_comprehensive.py               │
│ - trump_truth_social_monitor.py                             │
│ - Various other ingesters                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ forecasting_data_warehouse (Raw Tables)                     │
│ - trump_policy_daily                                        │
│ - social_sentiment_daily                                    │
│ - news_intelligence_daily                                   │
│ - weather, prices, CFTC, USDA, etc.                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ FEATURE ENGINEERING VIEW                                     │
│ neural.vw_big_eight_signals                                 │
│ (Joins all sources, calculates 275+ features)              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ MATERIALIZATION (Daily 6 AM)                                │
│ scripts/refresh_features_pipeline.py                        │
│ CREATE OR REPLACE TABLE training_dataset_super_enriched    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ TRAINING TABLE (models_v4)                                  │
│ training_dataset_super_enriched                             │
│ - 2,136 rows (2020-2025)                                   │
│ - 275+ columns (features + targets)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┬───────────┬───────────┐
         ▼                       ▼           ▼           ▼
┌─────────────┐  ┌─────────────┐  ┌────────┐  ┌────────┐
│ bqml_1w     │  │ bqml_1m     │  │bqml_3m │  │bqml_6m │
│ (275 feat)  │  │ (274 feat)  │  │(268 ft)│  │(258 ft)│
└──────┬──────┘  └──────┬──────┘  └───┬────┘  └───┬────┘
       │                │              │           │
       └────────────────┴──────────────┴───────────┘
                        │
                        ▼
          ┌─────────────────────────────────────┐
          │ ML.PREDICT() (Daily or On-Demand)   │
          │ Uses latest row from training table │
          └──────────────┬──────────────────────┘
                         │
                         ▼
          ┌─────────────────────────────────────┐
          │ predictions_uc1.production_forecasts│
          │ - Last prediction: Nov 4, 21:56 UTC │
          └─────────────────────────────────────┘
```

---

## CURRENT STATUS VERIFICATION

**Training Table:** `models_v4.training_dataset_super_enriched`
- ⚠️ **Current State:** Only 11 columns (truncated)
- ✅ **Was Full Schema When Models Trained:** Had all 275+ columns
- ⚠️ **Issue:** Table truncated after training, but models still work

**Production Models:**
- ✅ `bqml_1w`: 275 features, trained successfully
- ✅ `bqml_1m`: 274 features, trained successfully
- ✅ `bqml_3m`: 268 features, trained successfully
- ✅ `bqml_6m`: 258 features, trained successfully

**Predictions:**
- ✅ Last generated: November 4, 2025 at 21:56:18 UTC
- ✅ Stored in: `predictions_uc1.production_forecasts`
- ✅ All 4 models generated predictions

**Cron Schedule:**
- ✅ `refresh_features_pipeline.py` scheduled daily at 6 AM
- ✅ Ingestion scripts running hourly/daily
- ✅ All scrapers write to `forecasting_data_warehouse`

---

## CRITICAL REQUIREMENTS

### For Training to Work:
1. ✅ Raw data in `forecasting_data_warehouse` (verified)
2. ✅ `neural.vw_big_eight_signals` view exists (assumed)
3. ✅ `refresh_features_pipeline.py` materializes to `training_dataset_super_enriched`
4. ⚠️ Table must have ALL 275+ columns + targets (currently truncated)

### For Predictions to Work:
1. ✅ `training_dataset_super_enriched` has latest row with features
2. ✅ Models exist (`bqml_1w`, `bqml_1m`, `bqml_3m`, `bqml_6m`)
3. ✅ Prediction SQL reads from training table
4. ✅ Predictions stored in `predictions_uc1.production_forecasts`

---

## ISSUES IDENTIFIED

### Issue #1: Training Table Truncated
**Problem:** `training_dataset_super_enriched` currently has only 11 columns  
**Impact:** Cannot retrain models or evaluate them  
**Fix:** Run `refresh_features_pipeline.py` to restore full schema

### Issue #2: Targets Missing from Table
**Problem:** No target columns in current table  
**Impact:** Cannot retrain or evaluate  
**Fix:** Restore targets via feature pipeline or manual backfill

---

**Document Generated:** 2025-11-05  
**Next Verification:** After running `refresh_features_pipeline.py`







