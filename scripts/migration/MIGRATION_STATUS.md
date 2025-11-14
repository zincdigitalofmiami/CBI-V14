# Naming Architecture Migration Status

**Date**: 2025-11-14  
**Status**: Phase 1-6 Complete, Phase 4-5 In Progress

## ✅ Completed Phases

### Phase 1: Archive Legacy Tables ✅
- ✅ Archived 10 training tables to `archive.legacy_20251114__models_v4__*`
- All production_training_data_* tables safely archived
- All regime tables archived

### Phase 2: Verify Datasets ✅
- ✅ All 7 required datasets exist and verified

### Phase 3: Create New Training Tables ✅
- ✅ Created 10 new training tables:
  - `training.zl_training_prod_allhistory_{1w|1m|3m|6m|12m}` (5 tables)
  - `training.zl_training_full_allhistory_{1w|1m|3m|6m|12m}` (5 tables)
- ✅ Created regime tables:
  - `training.regime_calendar` (13,102 rows)
  - `training.regime_weights` (11 rows)

### Phase 6: Create Shim Views ✅
- ✅ Created 5 shim views in models_v4 for backward compatibility

### Phase 4: Update Python Scripts (Partial) ✅
- ✅ Created `scripts/export_training_data.py` with new naming
- ✅ Updated training scripts:
  - `src/training/baselines/train_tree.py` ✅
  - `src/training/baselines/train_simple_neural.py` ✅
  - `src/training/baselines/train_statistical.py` ✅
  - `src/training/advanced/*.py` (5 files) ✅
  - `src/training/ensemble/regime_ensemble.py` ✅
  - `src/training/regime/regime_classifier.py` ✅
  - `src/training/baselines/neural_baseline.py` ✅
  - `src/training/baselines/statistical.py` ✅
  - `src/training/baselines/tree_models.py` ✅

**Total Updated**: 11+ training scripts

## ⏳ Remaining Work

### Phase 4: Update Prediction Scripts
- [ ] `src/prediction/generate_local_predictions.py`
- [ ] `src/prediction/send_to_dashboard.py`

### Phase 5: Update SQL Files
- [ ] `config/bigquery/bigquery-sql/ULTIMATE_DATA_CONSOLIDATION.sql`
- [ ] Feature view builders
- [ ] Prediction queries

### Phase 7: Update Local File Paths
- [ ] Migrate existing models to new directory structure
- [ ] Update model save patterns in all training scripts (model artifacts)

## 📊 Progress

- **Tables Created**: 12/12 ✅
- **Shim Views**: 5/5 ✅
- **Training Scripts Updated**: 11/25 ✅
- **Prediction Scripts**: 0/2 ⏳
- **SQL Files**: 0/10+ ⏳

## 🎯 Next Steps

1. Update prediction scripts
2. Update SQL files (especially ULTIMATE_DATA_CONSOLIDATION.sql)
3. Update model save patterns to include version directories
4. Test end-to-end workflow
5. Update ingestion scripts to write to new table names

