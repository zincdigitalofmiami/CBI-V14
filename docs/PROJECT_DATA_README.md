---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# CBI-V14 Project Data

This folder contains all project data organized by function.

## Structure

- **TrainingData/**: Training data pipeline (raw → staging → features → exports)
- **Models/**: Trained model artifacts
- **Data/**: External data sources and exports
- **BigQuery/**: BigQuery exports and sync data
- **Cache/**: Cached API responses
- **Logs/**: Application and collection logs
- **Config/**: Configuration files
- **Scripts/**: Python scripts
- **Documentation/**: Project documentation

## Data Flow

```
Raw Data → Staging → Features → Training Data → Models → Predictions
```

## Organization

All data is organized by:
1. **Function**: What the data is used for
2. **Type**: Raw, processed, features, etc.
3. **Source**: Where the data came from
4. **Date**: When the data was collected/processed
