# Vertex AI Directory

This directory contains all Vertex AI-related implementation for neural forecasting models.

## Structure

```
vertex-ai/
├── data/              # Data validation and audit scripts
├── deployment/        # Model deployment pipeline
│   ├── train_local_deploy_vertex.py
│   ├── export_savedmodel.py
│   ├── upload_to_vertex.py
│   └── create_endpoint.py
├── evaluation/        # Model evaluation and explainability
├── prediction/        # Prediction generation scripts
└── training/          # Training configurations (future)
```

## Current Status

**Deployment Pipeline**: ✅ Complete
- Train locally on M4 Mac → Export SavedModel → Upload to Vertex → Deploy endpoint
- Scripts ready to use, documented in `active-plans/MAC_TRAINING_SETUP_PLAN.md`

**Data/Evaluation**: ✅ Audit scripts exist
- Validation and inventory tools in `data/`

**Training**: ⏳ Next phase
- Local training scripts to be created in `training/`

## Usage

### Complete Workflow
```bash
# Train a model locally and deploy to Vertex AI
python vertex-ai/deployment/train_local_deploy_vertex.py --horizon=1m
```

### Individual Steps
```bash
# Export a trained model
python vertex-ai/deployment/export_savedmodel.py --model_path=... --horizon=1m

# Upload to Vertex AI
python vertex-ai/deployment/upload_to_vertex.py --saved_model_path=... --horizon=1m

# Create/deploy endpoint
python vertex-ai/deployment/create_endpoint.py --model_resource_name=... --horizon=1m
```

## Reference

See `../active-plans/VERTEX_AI_TRUMP_ERA_PLAN.md` for complete Vertex AI strategy and naming conventions.
