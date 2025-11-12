# Model Organization Structure

This folder contains the organized structure for all CBI-V14 training models.

## Structure Overview

```
models_organized/
├── Trained/                    # Successfully trained models
│   ├── Top Scoring/           # Top 1/3 by R² score
│   │   ├── Vertex/            # Vertex AI models
│   │   │   └── [YYYY-MM]/    # Organized by month
│   │   └── bqml/              # BigQuery ML models
│   │       └── [YYYY-MM]/
│   ├── Middle Scores/         # Middle 1/3 by R² score
│   │   ├── Vertex/
│   │   └── bqml/
│   ├── Lowest Scores/         # Bottom 1/3 by R² score
│   │   ├── Vertex/
│   │   └── bqml/
│   ├── Predictions/           # Prediction-specific models
│   │   └── [YYYY-MM]/
│   ├── Baselines/             # Baseline models
│   │   └── [YYYY-MM]/
│   └── General Training/      # General training models
│       └── [YYYY-MM]/
│
└── Failed/                     # Failed training attempts
    ├── Vertex/
    │   └── [YYYY-MM]/
    ├── bqml/
    │   └── [YYYY-MM]/
    ├── Predictions/
    │   └── [YYYY-MM]/
    ├── Baselines/
    │   └── [YYYY-MM]/
    └── General Training/
        └── [YYYY-MM]/
```

## Organization Rules

### Status Classification
- **Trained**: Models that completed training successfully (R² ≥ 0 or reasonable MAE)
- **Failed**: Models with negative R², very high MAE (>10), or training errors

### Score Tiers (Trained Models Only)
- **Top Scoring**: Top 1/3 of models by R² score
- **Middle Scores**: Middle 1/3 of models by R² score  
- **Lowest Scores**: Bottom 1/3 of models by R² score

### Model Types
- **Vertex**: Vertex AI AutoML models
- **bqml**: BigQuery ML models

### Categories
- **Predictions**: Models specifically for prediction tasks
- **Baselines**: Baseline/comparison models (ARIMA, simple baselines)
- **General Training**: Standard training models

### Month Organization
All models are organized by creation month (YYYY-MM format)

## Files

Each model has a JSON file containing:
- Model name/ID
- Type (Vertex/bqml)
- Status (Trained/Failed)
- Category (Baseline/Prediction/General)
- Performance metrics (MAE, R²)
- Creation date
- Location in BigQuery/Vertex AI

## Mapping

See `model_organization_mapping.json` for complete mapping of all models from their original locations to the new organized structure.

## Notes

- This is a **documentation/reference structure** for organizing model information
- Actual BigQuery models remain in their original datasets (`models_v4`, etc.)
- Vertex AI models remain in their original Vertex AI project
- This structure helps track model performance, organization, and history






