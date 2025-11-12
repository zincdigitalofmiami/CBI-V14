# ✅ Model Organization - Simple & Clean

**Date**: November 6, 2025

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
SELECT * FROM `cbi-v14.models_trained.all_models`
WHERE model_type = 'bqml';
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
- `model_type` - 'bqml' or 'Vertex'
- `category` - 'Baselines', 'Predictions', or 'General Training'
- `month` - Creation month (YYYY-MM)
- `score_tier` - 'Top Scoring', 'Middle Scores', or 'Lowest Scores' (trained only)
- `mae` - Mean Absolute Error
- `r2_score` - R² score
- `source_location` - Where the actual model lives (models_v4.* or Vertex AI)
- `created` - Creation timestamp

---

## ✅ Done

Simple. Clean. No mess. All 38 models organized in 2 tables.






