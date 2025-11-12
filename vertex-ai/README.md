# Vertex AI Directory Structure

## Organization

All Vertex AI work is organized into clear subdirectories following strict naming conventions:

```
vertex-ai/
├── data/              # Data preparation and validation scripts
├── training/          # Model training scripts
├── prediction/        # Prediction generation scripts
├── evaluation/        # Model evaluation and explanation scripts
├── deployment/        # Deployment and monitoring scripts
└── config/            # Configuration files (YAML, JSON)
```

## Naming Conventions

**CRITICAL RULES:**
- ❌ NO `_test`, `_backup`, `_fixed`, `_safe`, `_v2` suffixes
- ❌ NO temporary files or test artifacts
- ✅ All files go directly to production locations
- ✅ Descriptive names following pattern: `{action}_{resource}_{purpose}.py`

## Current Files

### Prediction (`prediction/`)
- `predict_single_horizon.py` - Generate prediction for single horizon
- `predict_all_horizons.py` - Generate predictions for all 4 horizons
- `generate_predictions.py` - Batch prediction generator
- `get_remaining_predictions.py` - Get predictions using existing endpoint
- `run_predictions.sh` - Shell script for running predictions

### Evaluation (`evaluation/`)
- `explain_single_horizon.py` - Feature importance and model explanation

### Training (`training/`)
- (To be created for new Vertex AI training scripts)

### Data (`data/`)
- (To be created for data preparation scripts)

### Deployment (`deployment/`)
- (To be created for deployment scripts)

### Config (`config/`)
- (To be created for configuration files)

## Cleanup Rules

1. **Before Creating:** Check for existing files/resources
2. **During Work:** No temporary files - all work goes to final location
3. **After Work:** Remove any test artifacts, clean up unused imports
4. **Pre-Commit:** Verify no test/backup files in commit

## Reference

See `CLEAN_WORKSPACE_ORGANIZATION_PLAN.md` for complete workspace organization rules.

