---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# ✅ Model Organization - Simple & Clean

**Date**: November 6, 2025  
**Last Reviewed**: November 14, 2025

**Note**: BQML deprecated - all training now runs locally on Mac M4 via TensorFlow Metal. This document describes historical model organization.

---

## 📁 Simple Structure

Just **2 datasets** with **1 table each**:

```
cbi-v14/
├── models_trained/
│   └── all_models (27 models)
└── models_failed/
    └── all_models (11 models)
```

That's it. No empty folders. No confusing structure.

---

## 📊 Query Your Models

### Get Top Scoring Models
```sql
SELECT * FROM `cbi-v14.models_trained.all_models`
WHERE score_tier = 'Top Scoring'
ORDER BY r2_score DESC;
```

### Get Models by Month
```sql
SELECT * FROM `cbi-v14.models_trained.all_models`
WHERE month = '2025-11';
```

### Get Models by Type
```sql
-- Note: BQML deprecated - all training now local Mac M4
SELECT * FROM `cbi-v14.models_trained.all_models`
WHERE model_type = 'bqml';  -- Historical only
```

### Get Failed Models
```sql
SELECT * FROM `cbi-v14.models_failed.all_models`
ORDER BY created DESC;
```

---

## 📋 Table Schema

Each `all_models` table has:
- `model_name` - Name of the model
- `model_type` - 'bqml' (deprecated), 'Vertex', or 'Local' (Mac M4)
- `category` - 'Baselines', 'Predictions', or 'General Training'
- `month` - Creation month (YYYY-MM)
- `score_tier` - 'Top Scoring', 'Middle Scores', or 'Lowest Scores' (trained only)
- `mae` - Mean Absolute Error
- `r2_score` - R² score
- `source_location` - Where the actual model lives (models_v4.*, Vertex AI, or local Mac M4)
- `created` - Creation timestamp

**Note**: BQML models are deprecated. All new training uses local Mac M4 + TensorFlow Metal.

---

## ✅ Done

Simple. Clean. No mess. All 38 models organized in 2 tables.







