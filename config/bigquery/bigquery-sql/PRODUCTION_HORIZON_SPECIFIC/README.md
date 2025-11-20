---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Production Horizon-Specific Folder
**Purpose**: Production-ready BQML training and prediction scripts

---

## 🚨 CRITICAL WARNING: MODEL NAMES

**THESE MODEL NAMES ARE FIXED AND MUST NEVER BE CHANGED:**

```
cbi-v14.models_v4.bqml_1w
cbi-v14.models_v4.bqml_1m
cbi-v14.models_v4.bqml_3m
cbi-v14.models_v4.bqml_6m
```

**DO NOT**:
- ❌ Add `_production` suffix
- ❌ Add `_all_features` suffix
- ❌ Rename to any other format
- ❌ Create duplicate models with different names

**WHY**: BigQuery ML does not support renaming. All production code references these exact names.

---

## 📊 PRODUCTION TRAINING DATASETS

**Data Source for Training (290 features each):**

```
cbi-v14.models_v4.production_training_data_1w
cbi-v14.models_v4.production_training_data_1m
cbi-v14.models_v4.production_training_data_3m
cbi-v14.models_v4.production_training_data_6m
```

**Each training script MUST use its corresponding dataset:**
- TRAIN_BQML_1W_PRODUCTION.sql → production_training_data_1w
- TRAIN_BQML_1M_PRODUCTION.sql → production_training_data_1m
- TRAIN_BQML_3M_PRODUCTION.sql → production_training_data_3m
- TRAIN_BQML_6M_PRODUCTION.sql → production_training_data_6m

---

## 📁 FILES

### Training Scripts
1. `TRAIN_BQML_1W_PRODUCTION.sql` - Train 1-week model
2. `TRAIN_BQML_1M_PRODUCTION.sql` - Train 1-month model
3. `TRAIN_BQML_3M_PRODUCTION.sql` - Train 3-month model
4. `TRAIN_BQML_6M_PRODUCTION.sql` - Train 6-month model

### Prediction Scripts
5. `GENERATE_PREDICTIONS_PRODUCTION.sql` - Generate all predictions
6. `GENERATE_PREDICTIONS_STANDARD.sql` - Alternative prediction format

### Validation Scripts
7. `DRY_RUN_VALIDATION.sql` - Pre-training validation

### Documentation
8. `README.md` (this file)
9. `PRODUCTION_SUMMARY.md` - Complete production documentation

---

## 🔄 DATA FLOW

**Training**:
```
production_training_data_1w → TRAIN_BQML_1W_PRODUCTION.sql → bqml_1w
production_training_data_1m → TRAIN_BQML_1M_PRODUCTION.sql → bqml_1m
production_training_data_3m → TRAIN_BQML_3M_PRODUCTION.sql → bqml_3m
production_training_data_6m → TRAIN_BQML_6M_PRODUCTION.sql → bqml_6m
```

**Prediction**:
```
Latest row from production_training_data_* → ML.PREDICT(bqml_*) → Predictions
```

---

## ✅ USAGE

**To train a model:**
```bash
bq query --use_legacy_sql=false < TRAIN_BQML_1M_PRODUCTION.sql
```

**To generate predictions:**
```bash
bq query --use_legacy_sql=false < GENERATE_PREDICTIONS_PRODUCTION.sql
```

**To validate before training:**
```bash
bq query --use_legacy_sql=false < DRY_RUN_VALIDATION.sql
```

---

**SEE ALSO**: 
- `/PRODUCTION_NAMING_CONVENTIONS.md`
- `/OFFICIAL_PRODUCTION_SYSTEM.md`
- `/CBI_V14_COMPLETE_EXECUTION_PLAN.md`
