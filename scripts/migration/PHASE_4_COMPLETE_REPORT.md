# Phase 4: Update Python Scripts - COMPLETE ✅

**Date**: 2025-11-14  
**Status**: ✅ ALL FILES FIXED

## Summary

All baseline training scripts have been updated to use the new naming convention:
- **Data paths**: `zl_training_{surface}_allhistory_{horizon}.parquet`
- **Model paths**: `Models/local/horizon_{h}/{surface}/{family}/{model}_v{ver}/`

## Files Fixed

### ✅ Export Script
- `scripts/export_training_data.py` - Uses new naming, supports `--surface` parameter

### ✅ Training Scripts (All Fixed)

1. **`src/training/baselines/train_tree.py`** ✅
   - Data path: Updated to `zl_training_prod_allhistory_{horizon}.parquet`
   - Model path: Updated to `Models/local/horizon_{h}/{surface}/baselines/`
   - Model save: Uses version directories (`lightgbm_dart_v001/`, `xgboost_dart_v001/`)

2. **`src/training/baselines/train_simple_neural.py`** ✅
   - Data path: Updated
   - Model path: Updated

3. **`src/training/baselines/train_statistical.py`** ✅
   - Data path: Updated
   - Model path: Updated

4. **`src/training/baselines/tree_models.py`** ✅ FIXED
   - Line 30: Updated `load_training_data()` to use new naming
   - Added `surface` parameter support
   - Updated model save paths to use version directories
   - Fixed `MODELS_DIR` module-level issue (moved to function scope)

5. **`src/training/baselines/statistical.py`** ✅ FIXED
   - Line 34: Updated `load_training_data()` to use new naming
   - Added `surface` parameter support
   - Updated all training functions to accept `models_dir` parameter
   - Updated model save paths to use version directories
   - Fixed `MODELS_DIR` module-level issue

6. **`src/training/baselines/neural_baseline.py`** ✅ FIXED
   - Line 38: Updated `load_training_data()` to use new naming
   - Added `surface` parameter support
   - Updated `train_model()` to accept `models_dir` parameter
   - Updated model save paths to use version directories
   - Fixed `MODELS_DIR` module-level issue
   - Added missing `gc` import

### ✅ Advanced Training Scripts (Previously Updated)
- `src/training/advanced/attention_model.py` ✅
- `src/training/advanced/cnn_lstm_model.py` ✅
- `src/training/advanced/multi_layer_lstm.py` ✅
- `src/training/advanced/tcn_model.py` ✅
- `src/training/advanced/tiny_transformer.py` ✅

### ✅ Ensemble & Regime Scripts (Previously Updated)
- `src/training/ensemble/regime_ensemble.py` ✅
- `src/training/regime/regime_classifier.py` ✅

### ✅ Prediction Scripts (Previously Updated)
- `src/prediction/generate_local_predictions.py` ✅
- `src/prediction/send_to_dashboard.py` ✅

## Changes Made

### Data Path Pattern
**Old**: `production_training_data_{horizon}.parquet`  
**New**: `zl_training_{surface}_allhistory_{horizon}.parquet`

### Model Path Pattern
**Old**: `Models/local/baselines` (or `advanced`, `ensemble`, `regime`)  
**New**: `Models/local/horizon_{h}/{surface}/{family}/`

### Model Save Pattern
**Old**: `{model_name}_{horizon}.pkl` (or `.txt`, `.h5`)  
**New**: `{model_name}_v001/model.bin` (or `.h5` for neural)

### Function Signatures Updated
- `load_training_data(horizon, surface="prod")` - Added `surface` parameter
- Training functions now accept `models_dir` parameter instead of using module-level `MODELS_DIR`
- Model save functions create version directories automatically

## Verification

✅ All files checked for old naming patterns:
- ✅ `tree_models.py` - No old patterns found
- ✅ `statistical.py` - No old patterns found
- ✅ `neural_baseline.py` - No old patterns found
- ✅ `train_statistical.py` - No old patterns found

## Next Steps

Phase 4 is **COMPLETE**. Ready to proceed with:
- Phase 5: Update SQL Files
- Phase 7: Complete Model Save Patterns (add metadata files)
- Phase 8: Update Ingestion Scripts



