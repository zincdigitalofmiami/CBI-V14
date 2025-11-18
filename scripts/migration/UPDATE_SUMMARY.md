# Migration Update Summary

## ✅ Completed

### Phase 1: Archive ✅
- Archived 10 training tables

### Phase 2: Datasets ✅
- All 7 datasets verified

### Phase 3: New Tables ✅
- Created 10 training tables (prod + full surfaces)
- Created regime_calendar and regime_weights tables

### Phase 6: Shim Views ✅
- Created 5 shim views for backward compatibility

### Phase 4: Scripts (Partial) ✅
- ✅ Created `scripts/export_training_data.py` with new naming
- ✅ Updated `src/training/baselines/train_tree.py`:
  - Data path: `zl_training_prod_allhistory_{horizon}.parquet`
  - Model path: `Models/local/horizon_{h}/prod/baselines/{model}_v001/`
  - Model artifacts: `model.bin`, `columns_used.txt`, `run_id.txt`, `feature_importance.csv`
- ✅ Updated `src/training/baselines/train_simple_neural.py`:
  - Data path updated
  - Model path updated

## ⏳ Remaining Updates Needed

### Training Scripts (17 files)
- [ ] `src/training/baselines/train_statistical.py`
- [ ] `src/training/advanced/*.py` (5 files)
- [ ] `src/training/ensemble/regime_ensemble.py`
- [ ] `src/training/regime/regime_classifier.py`
- [ ] `src/training/baselines/neural_baseline.py`
- [ ] `src/training/baselines/statistical.py`
- [ ] `src/training/baselines/tree_models.py`

### Prediction Scripts
- [ ] `src/prediction/generate_local_predictions.py`
- [ ] `src/prediction/send_to_dashboard.py`

### SQL Files
- [ ] `config/bigquery/bigquery-sql/ULTIMATE_DATA_CONSOLIDATION.sql`
- [ ] Feature view builders
- [ ] Prediction queries

## 📋 Next Steps

1. Update remaining training scripts (use train_tree.py as template)
2. Update prediction scripts
3. Update SQL files
4. Test end-to-end workflow



