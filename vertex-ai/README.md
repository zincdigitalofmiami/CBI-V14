# Vertex AI Directory

⚠️ **LEGACY / REFERENCE ONLY** ⚠️

This directory contains Vertex AI-related implementation for neural forecasting models. **This is NOT used in the current architecture.**

## Current Architecture (November 2025)

**100% Local Training on M4 Mac** - No Vertex AI, No Cloud Compute
- All training happens locally on Mac M4
- BigQuery is used for **storage only** (training data, predictions)
- See `GPT5_READ_FIRST.md` for current architecture details

## Why This Directory Exists

This directory is kept for **reference only** in case you need to:
- Understand previous Vertex AI deployment approaches
- Reference old table naming conventions
- Review historical implementation patterns

**DO NOT USE** these scripts for current training. Use:
- `src/training/baselines/` - Local training scripts
- `scripts/export_training_data.py` - Export from BigQuery
- `scripts/upload_predictions.py` - Upload predictions to BigQuery

## Structure

```
vertex-ai/
├── data/              # Data validation and audit scripts (legacy)
├── deployment/        # Model deployment pipeline (legacy)
│   ├── train_local_deploy_vertex.py
│   ├── export_savedmodel.py
│   ├── upload_to_vertex.py
│   └── create_endpoint.py
├── evaluation/        # Model evaluation and explainability (legacy)
├── prediction/        # Prediction generation scripts (legacy)
└── training/          # Training configurations (empty - not used)
```

## Table Naming Convention

**Old (Legacy)**:
- `models_v4.production_training_data_*`
- `models_v4.vertex_ai_training_*_base`

**New (Current)**:
- `training.zl_training_prod_allhistory_*` (e.g., `zl_training_prod_allhistory_1m`)

Scripts in this directory may reference old table names. They are kept for reference only and are not actively maintained.

## Reference

- **Current Training**: See `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md`
- **M4 Optimization**: See `docs/training/M4_OPTIMIZATION_GUIDE.md`
- **Architecture**: See `GPT5_READ_FIRST.md`
