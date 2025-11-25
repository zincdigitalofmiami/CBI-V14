---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# 🚨 PRODUCTION NAMING CONVENTIONS - NEVER DEVIATE
**Critical Document - Read Before ANY Changes**  
**Last Updated**: November 5, 2025

---

## ⚠️ CRITICAL WARNING

**THESE NAMES ARE FIXED AND MUST NEVER BE CHANGED**

Any deviation from these naming conventions will break the production system.

---

## PRODUCTION BQML MODELS (DO NOT RENAME)

**These model names are fixed and must never be changed:**

```
cbi-v14.models_v4.bqml_1w
cbi-v14.models_v4.bqml_1m
cbi-v14.models_v4.bqml_3m
cbi-v14.models_v4.bqml_6m
```

**Why Fixed?**
- BigQuery ML does not support model renaming
- Prediction scripts reference these exact names
- Dashboard API queries these exact names
- Historical accuracy tracking uses these names

**Trained**: November 4, 2025  
**Performance**: MAE 0.30, R² 0.987, MAPE <1%

---

## PRODUCTION TRAINING DATASETS (ALL INGESTION GOES HERE)

**These tables are the target for all data ingestion and feature materialization:**

```
cbi-v14.models_v4.production_training_data_1w  (290 features, for 1W predictions)
cbi-v14.models_v4.production_training_data_1m  (290 features, for 1M predictions)
cbi-v14.models_v4.production_training_data_3m  (290 features, for 3M predictions)
cbi-v14.models_v4.production_training_data_6m  (290 features, for 6M predictions)
```

**Features**: 290 columns each including:
- 4 target columns (target_1w, target_1m, target_3m, target_6m)
- 1 date column
- 285 feature columns (prices, Big 8, correlations, weather, economic, etc.)

**Row Counts** (as of Nov 5, 2025):
- 1W: 1,448 rows (latest: Oct 13, 2025)
- 1M: 1,347 rows (latest: Sept 10, 2025)
- 3M: 1,329 rows (latest: June 13, 2025)
- 6M: 1,198 rows (latest: Feb 4, 2025)

---

## DATA FLOW DIAGRAM

```
┌─────────────────────────────────────────┐
│   INGESTION SCRIPTS (Daily/Hourly)      │
│                                         │
│  • hourly_prices.py                     │
│  • daily_weather.py                     │
│  • ingest_social_intelligence.py        │
│  • ingest_market_prices.py              │
│  • ingest_cftc_positioning_REAL.py      │
│  • ingest_usda_harvest_api.py           │
│  • ingest_eia_biofuel_real.py           │
│  • backfill_trump_intelligence.py       │
│  • GDELT backfill (new)                 │
│  • FRED economic (new)                  │
│  • USDA FAS China (new)                 │
└───────────────┬─────────────────────────┘
                │
                ↓ ALL INGESTION MUST UPDATE THESE 4 TABLES
                │
┌─────────────────────────────────────────┐
│  RAW DATA WAREHOUSE (Intermediate)      │
│  forecasting_data_warehouse.*           │
└───────────────┬─────────────────────────┘
                │
                ↓ FEATURE ENGINEERING & AGGREGATION
                │
┌─────────────────────────────────────────┐
│  PRODUCTION TRAINING DATASETS           │
│  (290 features each)                    │
│                                         │
│  • production_training_data_1w          │
│  • production_training_data_1m          │
│  • production_training_data_3m          │
│  • production_training_data_6m          │
└───────────────┬─────────────────────────┘
                │
                ↓ ML.PREDICT()
                │
┌─────────────────────────────────────────┐
│     BQML PRODUCTION MODELS              │
│     (Trained Nov 4, 2025)               │
│                                         │
│  • bqml_1w (274 features used)          │
│  • bqml_1m (274 features used)          │
│  • bqml_3m (268 features used)          │
│  • bqml_6m (258 features used)          │
└───────────────┬─────────────────────────┘
                │
                ↓ PREDICTIONS
                │
┌─────────────────────────────────────────┐
│      PREDICTION OUTPUTS                 │
│                                         │
│  predictions_uc1.production_forecasts   │
│  or predictions.daily_forecasts         │
└─────────────────────────────────────────┘
```

---

## INGESTION SCRIPT REQUIREMENTS

**Every ingestion script MUST**:
1. Load data from source API
2. INSERT/UPDATE into `forecasting_data_warehouse.*` (existing)
3. **ALSO INSERT/UPDATE into ALL 4 production_training_data_* tables (NEW)**

**Example Pattern**:
```python
def save_to_production_datasets(date, feature_dict):
    """Update all 4 production training datasets"""
    client = bigquery.Client(project='cbi-v14')
    
    for horizon in ['1w', '1m', '3m', '6m']:
        table_id = f'cbi-v14.models_v4.production_training_data_{horizon}'
        
        # UPSERT logic (UPDATE if exists, INSERT if not)
        # ... your implementation ...
```

---

## DEPRECATED NAMES (DO NOT USE)

```
❌ training_dataset_super_enriched (11 columns - BROKEN)
❌ training_dataset_super_enriched_backup
❌ training_dataset_pre_integration_backup (used as source for restore only)
❌ training_dataset_pre_forwardfill_backup
❌ training_dataset_pre_coverage_fix_backup
❌ All _ARCHIVED_* tables
❌ Any variant of "training_dataset" except production_training_data_*
```

---

## PREDICTION QUERY PATTERN

**Each horizon MUST use its corresponding table:**

```sql
-- 1W PREDICTION
SELECT *
FROM ML.PREDICT(
  MODEL `cbi-v14.models_v4.bqml_1w`,
  (SELECT * EXCEPT(target_1w, target_1m, target_3m, target_6m, date, volatility_regime)
   FROM `cbi-v14.models_v4.production_training_data_1w`
   WHERE date = (SELECT MAX(date) FROM `cbi-v14.models_v4.production_training_data_1w`))
)

-- 1M PREDICTION
SELECT *
FROM ML.PREDICT(
  MODEL `cbi-v14.models_v4.bqml_1m`,
  (SELECT * EXCEPT(target_1w, target_1m, target_3m, target_6m, date, volatility_regime)
   FROM `cbi-v14.models_v4.production_training_data_1m`
   WHERE date = (SELECT MAX(date) FROM `cbi-v14.models_v4.production_training_data_1m`))
)

-- 3M PREDICTION
SELECT *
FROM ML.PREDICT(
  MODEL `cbi-v14.models_v4.bqml_3m`,
  (SELECT * EXCEPT(target_1w, target_1m, target_3m, target_6m, date, volatility_regime)
   FROM `cbi-v14.models_v4.production_training_data_3m`
   WHERE date = (SELECT MAX(date) FROM `cbi-v14.models_v4.production_training_data_3m`))
)

-- 6M PREDICTION
SELECT *
FROM ML.PREDICT(
  MODEL `cbi-v14.models_v4.bqml_6m`,
  (SELECT * EXCEPT(target_1w, target_1m, target_3m, target_6m, date, volatility_regime)
   FROM `cbi-v14.models_v4.production_training_data_6m`
   WHERE date = (SELECT MAX(date) FROM `cbi-v14.models_v4.production_training_data_6m`))
)
```

---

## VERIFICATION COMMANDS

**Check production datasets exist:**
```bash
bq ls models_v4 | grep "production_training_data"
```

**Check models exist:**
```bash
bq ls models_v4 | grep "^  bqml_1[wm]\|^  bqml_[36]m"
```

**Verify latest dates:**
```bash
for horizon in 1w 1m 3m 6m; do
  echo "=== production_training_data_$horizon ==="
  bq query --nouse_legacy_sql "SELECT MAX(date) as latest FROM \`cbi-v14.models_v4.production_training_data_$horizon\`"
done
```

**Verify feature count:**
```bash
bq query --nouse_legacy_sql "
SELECT 
  table_name, 
  COUNT(*) as feature_count
FROM \`cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS\`
WHERE table_name LIKE 'production_training_data%'
GROUP BY table_name
ORDER BY table_name
"
```

---

## FILE REFERENCES

**Training SQL Files** (should reference production_training_data_*):
- `bigquery-sql/BQML_1W_PRODUCTION.sql`
- `bigquery-sql/BQML_1M_PRODUCTION.sql`
- `bigquery-sql/BQML_3M_PRODUCTION.sql`
- `bigquery-sql/BQML_6M_PRODUCTION.sql`

**Prediction SQL Files**:
- `bigquery-sql/PRODUCTION_HORIZON_SPECIFIC/GENERATE_PREDICTIONS_PRODUCTION.sql`

**Documentation**:
- `CBI_V14_COMPLETE_EXECUTION_PLAN.md` (updated Nov 5)
- `OFFICIAL_PRODUCTION_SYSTEM.md`
- `QUICK_REFERENCE.txt`
- `WRITE_THIS_DOWN.md`

---

## CHANGE CONTROL

**IF YOU MUST RENAME (NEVER DO THIS)**:
1. ❌ STOP - Renaming breaks everything
2. ❌ Models cannot be renamed in BigQuery ML
3. ❌ Datasets should not be renamed (update references instead)

**IF SOMETHING IS WRONG**:
1. ✅ Create NEW tables/models with correct names
2. ✅ Update references in scripts
3. ✅ Archive old tables (don't delete)
4. ✅ Document changes in this file

---

## COMPLIANCE CHECKLIST

Before deploying ANY code change:
- [ ] Verify it uses `production_training_data_1w/1m/3m/6m`
- [ ] Verify it uses `bqml_1w/1m/3m/6m` (not `_production` suffix)
- [ ] Verify it does NOT reference `training_dataset_super_enriched`
- [ ] Verify it does NOT reference any `_backup` tables
- [ ] Verify it does NOT reference any `_ARCHIVED_` tables

---

**PRINT THIS PAGE AND KEEP IT VISIBLE AT ALL TIMES**

**Last Verified**: November 5, 2025  
**Next Review**: After any system changes








