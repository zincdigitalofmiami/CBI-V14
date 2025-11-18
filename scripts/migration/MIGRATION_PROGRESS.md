# Naming Architecture Migration Progress

**Date**: 2025-11-14  
**Status**: In Progress

## ✅ Completed Phases

### Phase 1: Archive Legacy Tables ✅
- ✅ Archived 10 training tables to `archive.legacy_20251114__models_v4__*`
- ✅ All production_training_data_* tables archived
- ✅ All regime tables archived

### Phase 2: Verify Datasets ✅
- ✅ All 7 required datasets exist:
  - archive
  - raw_intelligence
  - features
  - training
  - predictions
  - monitoring
  - vegas_intelligence

### Phase 3: Create New Training Tables ✅
- ✅ Created 10 new training tables:
  - `training.zl_training_prod_allhistory_{1w|1m|3m|6m|12m}` (5 tables)
  - `training.zl_training_full_allhistory_{1w|1m|3m|6m|12m}` (5 tables)
- ✅ Created regime tables:
  - `training.regime_calendar` (13,102 rows)
  - `training.regime_weights` (11 rows)

### Phase 6: Create Shim Views ✅
- ✅ Created 5 shim views in models_v4:
  - `models_v4.production_training_data_{1w|1m|3m|6m|12m}` → point to new tables

## ⏳ In Progress

### Phase 4: Update Python Scripts
- ⏳ Update training data export script
- ⏳ Update training scripts (baselines, advanced, ensemble, regime)
- ⏳ Update prediction scripts
- ⏳ Update ingestion scripts
- ⏳ Update feature calculation scripts

### Phase 5: Update SQL Files
- ⏳ Update ULTIMATE_DATA_CONSOLIDATION.sql
- ⏳ Update feature view builders
- ⏳ Update prediction queries

### Phase 7: Update Local File Paths
- ⏳ Migrate existing models to new directory structure
- ⏳ Update model save paths in training scripts

## 📋 Next Steps

1. Update `scripts/export_training_data.py` (or create if missing)
2. Update all training scripts in `src/training/`
3. Update prediction scripts
4. Update SQL files
5. Migrate local models to new structure

## 📊 Current Status

- **Tables Created**: 12/12 ✅
- **Shim Views**: 5/5 ✅
- **Scripts Updated**: 0/20+ ⏳
- **SQL Files Updated**: 0/10+ ⏳



