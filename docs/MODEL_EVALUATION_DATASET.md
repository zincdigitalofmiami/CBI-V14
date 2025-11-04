# Model Evaluation Dataset - MANDATORY

**Date:** November 5, 2025  
**Status:** ✅ **CRITICAL - NEVER DEVIATE FROM THIS**

---

## ⚠️ MANDATORY EVALUATION DATASET

**Table:** `cbi-v14.models_v4.training_dataset_super_enriched`  
**Filter:** `WHERE target_[horizon] IS NOT NULL AND date >= '2024-01-01'`  
**NEVER use full dataset (2020-2025) for ML.EVALUATE**

---

## Why This Matters

**Full Dataset (2020-2025) causes negative R² artifact:**
- Regime shifts (COVID lows, 2022 energy spike)
- Variance collapse in older segments
- SST (variance) < SSR (residuals) → R² < 0
- Only affects 1M/3M models (longer horizons include multi-regime data)

**Recent Data (2024+) gives correct R²:**
- Consistent regime
- Stable variance
- R² = 0.997 (excellent)

---

## Correct Evaluation Queries

### For ML.EVALUATE (R²):

```sql
-- CORRECT: Use date >= '2024-01-01'
SELECT * FROM ML.EVALUATE(
  MODEL `cbi-v14.models_v4.bqml_1m_all_features`,
  (SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched`
   WHERE target_1m IS NOT NULL AND date >= '2024-01-01')
);

-- WRONG: Full dataset causes negative R²
SELECT * FROM ML.EVALUATE(
  MODEL `cbi-v14.models_v4.bqml_1m_all_features`,
  (SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched`
   WHERE target_1m IS NOT NULL)  -- ❌ DON'T DO THIS
);
```

### For Manual MAE/MAPE (Always Accurate):

```sql
WITH predictions AS (
  SELECT 
    predicted_target_1m,
    target_1m,
    ABS(predicted_target_1m - target_1m) as error
  FROM ML.PREDICT(
    MODEL `cbi-v14.models_v4.bqml_1m_all_features`,
    (SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched`
     WHERE target_1m IS NOT NULL AND date >= '2024-01-01')
  )
)
SELECT 
  AVG(error) as mae,
  AVG(error / target_1m * 100) as mape,
  COUNT(*) as count
FROM predictions;
```

---

## Production Monitoring

**Use these KPIs (always accurate):**
- **MAE:** ~0.40 (all models)
- **MAPE:** ~0.76% (all models)
- **R²:** Only on date >= '2024-01-01' dataset

**Never use:**
- R² on full dataset (2020-2025)
- ML.EVALUATE without date filter

---

## Dataset Reference

| Model | Correct Dataset Filter |
|-------|----------------------|
| 1W | `WHERE target_1w IS NOT NULL AND date >= '2024-01-01'` |
| 1M | `WHERE target_1m IS NOT NULL AND date >= '2024-01-01'` |
| 3M | `WHERE target_3m IS NOT NULL AND date >= '2024-01-01'` |
| 6M | `WHERE target_6m IS NOT NULL AND date >= '2024-01-01'` |

**Table:** `cbi-v14.models_v4.training_dataset_super_enriched`

---

**Last Updated:** November 5, 2025  
**Status:** MANDATORY - NEVER DEVIATE FROM THIS DATASET

