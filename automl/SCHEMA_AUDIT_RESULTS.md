# 🔍 SCHEMA AUDIT RESULTS

## ❌ CRITICAL ISSUE FOUND

### Problem: Missing `date` Column in Batch Prediction Input

**Training Dataset (`models_v4.training_dataset_v4`):**
- ✅ Has `date` column (STRING type)
- ✅ 33 columns total
- ✅ Includes target columns (target_1w, target_1m, target_3m, target_6m)

**Batch Prediction Input (`models_v4.batch_prediction_input`):**
- ❌ NO `date` column
- ❌ 57 columns (different from training!)
- ❌ Excluded date when created with `SELECT * EXCEPT(date, ...)`

**Batch Prediction Error:**
```
Column prefix: . Error: Missing struct property: date.
```

---

## 📊 Schema Comparison

### Training Dataset (What Model Was Trained On):
| Column | Type | Present |
|--------|------|---------|
| date | STRING | ✅ YES |
| zl_price_current | FLOAT64 | ✅ |
| zl_price_lag1 | FLOAT64 | ✅ |
| ... | ... | ✅ |
| target_1w | FLOAT64 | ✅ (excluded for prediction) |
| target_1m | FLOAT64 | ✅ (excluded for prediction) |
| target_3m | FLOAT64 | ✅ (excluded for prediction) |
| target_6m | FLOAT64 | ✅ (excluded for prediction) |

**Total: 33 columns**

### Batch Prediction Input (What We're Using):
| Column | Type | Present |
|--------|------|---------|
| date | STRING | ❌ **MISSING** |
| zl_price_current | FLOAT64 | ✅ |
| zl_price_lag1 | FLOAT64 | ✅ |
| ... | ... | ✅ |
| news_* | Various | ✅ (28 extra columns!) |
| social_* | Various | ✅ (10 extra columns!) |

**Total: 57 columns (24 more than training dataset!)**

---

## 🚨 ROOT CAUSE

**My script did this:**
```python
query = """
SELECT * EXCEPT(date, target_1w, target_1m, target_3m, target_6m)
FROM `cbi-v14.models_v4.training_dataset_v4`
```

**Should have done:**
```python
query = """
SELECT * EXCEPT(target_1w, target_1m, target_3m, target_6m)
FROM `cbi-v14.models_v4.training_dataset_v4`
-- Keep the date column!
```

---

## ✅ FIX

Need to:
1. Include `date` column in batch prediction input
2. Match exact schema of training dataset (33 columns, not 57)
3. Exclude ONLY the target columns, keep everything else

---

## 📋 Action Items

1. **Update batch_prediction_input table** with correct schema
2. **Rerun batch predictions** with date column included
3. **Verify column count matches** training dataset (33 columns)

---

## 🎯 Correct Query

```sql
-- Get latest features for prediction (KEEP DATE!)
SELECT * EXCEPT(target_1w, target_1m, target_3m, target_6m)
FROM `cbi-v14.models_v4.training_dataset_v4`
ORDER BY date DESC
LIMIT 1
```

This will give us **29 columns** (33 - 4 targets = 29 features + date = 30 total for prediction input)

