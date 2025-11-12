# Production Horizon-Specific Configuration
**Last Updated**: November 5, 2025

---

## 🚨 CRITICAL: MODEL NAMES (FIXED - DO NOT RENAME)

**These model names are FIXED and cannot be changed:**

```
cbi-v14.models_v4.bqml_1w
cbi-v14.models_v4.bqml_1m
cbi-v14.models_v4.bqml_3m
cbi-v14.models_v4.bqml_6m
```

**Why?** BigQuery ML does not support model renaming. These names are referenced in:
- Prediction scripts
- Dashboard queries
- Monitoring systems
- Documentation

---

## 📊 PRODUCTION TRAINING DATASETS (290 features each)

**ALL data ingestion MUST update these tables:**

```
cbi-v14.models_v4.production_training_data_1w
cbi-v14.models_v4.production_training_data_1m
cbi-v14.models_v4.production_training_data_3m
cbi-v14.models_v4.production_training_data_6m
```

**Each dataset**:
- Has 290 features (identical schema across all 4)
- Filtered by target availability (WHERE target_[horizon] IS NOT NULL)
- Contains all historical data (2020-present)
- Updated by ingestion scripts

---

## 🔄 DATA FLOW

```
Ingestion → forecasting_data_warehouse.* → Feature Engineering
    ↓
production_training_data_1w (1,448 rows, latest: Oct 13)
production_training_data_1m (1,347 rows, latest: Sept 10)
production_training_data_3m (1,329 rows, latest: June 13)
production_training_data_6m (1,198 rows, latest: Feb 4)
    ↓
bqml_1w/1m/3m/6m (ML.PREDICT)
    ↓
predictions_uc1.production_forecasts
```

---

## 📁 FILES IN THIS FOLDER

### Training SQL Files
- `TRAIN_BQML_1W_PRODUCTION.sql` → Creates bqml_1w
- `TRAIN_BQML_1M_PRODUCTION.sql` → Creates bqml_1m
- `TRAIN_BQML_3M_PRODUCTION.sql` → Creates bqml_3m
- `TRAIN_BQML_6M_PRODUCTION.sql` → Creates bqml_6m

### Prediction SQL Files
- `GENERATE_PREDICTIONS_PRODUCTION.sql` → Generates all 4 horizon predictions
- `GENERATE_PREDICTIONS_STANDARD.sql` → Alternative prediction script

### Validation SQL Files
- `DRY_RUN_VALIDATION.sql` → Pre-training validation checks

---

## ⚠️ DEPRECATED (DO NOT USE)

```
❌ training_dataset_super_enriched (11 columns - BROKEN)
❌ Any _all_features suffix models (legacy naming)
❌ Any _backup tables (except for restore)
❌ Any _ARCHIVED_ tables
```

---

## ✅ VERIFICATION

**Check models exist:**
```bash
bq ls models_v4 | grep "^  bqml_1[wm]\|^  bqml_[36]m"
```

**Check datasets exist:**
```bash
bq ls models_v4 | grep "production_training_data"
```

**Verify feature counts:**
```bash
bq query --nouse_legacy_sql "
SELECT table_name, COUNT(*) as features
FROM \`cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS\`
WHERE table_name LIKE 'production_training_data%'
GROUP BY table_name
"
```

---

**SEE ALSO**: `/PRODUCTION_NAMING_CONVENTIONS.md` for complete details
