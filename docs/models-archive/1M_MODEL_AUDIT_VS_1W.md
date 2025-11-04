# 1M MODEL AUDIT VS 1W - REVERSE ENGINEERING

**Date:** November 3, 2025  
**Status:** Comparing train_1m against train_1w baseline

---

## MODEL STATUS CHECK

**1W Model (`bqml_1w_mean`):**
- Status: NOT FOUND (not trained yet)
- Note: User said "recently passed and fully trained" but model doesn't exist in BigQuery

**1M Model (`bqml_1m_mean`):**
- Status: NOT FOUND (not trained yet)

---

## TRAINING DATA COMPARISON

### Row Counts:
| View | Total Rows | Target Available | Train Rows | Eval Rows | Train % |
|------|-----------|------------------|------------|-----------|---------|
| train_1w | 1,448 | 1,448 | 1,231 | 217 | 85% |
| train_1m | 1,347 | 1,347 | 1,153 | 194 | 86% |

**Difference:**
- 1m has 101 fewer rows than 1w (1,347 vs 1,448)
- This is expected: 1-month targets need more future data than 1-week targets
- Both have proper train/eval splits (~85%/15%)

---

## SQL FILE COMPARISON

### Differences Between 1w and 1m SQL Files:

```diff
< CREATE MODEL `cbi-v14.models_v4.bqml_1w_mean`
> CREATE MODEL `cbi-v14.models_v4.bqml_1m_mean`

< input_label_cols=['target_1w'],
> input_label_cols=['target_1m'],

< FROM `cbi-v14.models_v4.train_1w`
> FROM `cbi-v14.models_v4.train_1m`

< WHERE target_1w IS NOT NULL;
> WHERE target_1m IS NOT NULL;
```

**✅ IDENTICAL EXCEPT CLAUSE:**
- Both exclude same 11 all-NULL columns
- Both exclude same 11 temporal leakage features
- Both use same hyperparameter ranges
- Both use same train/eval split logic

---

## NULL CHECK FOR 1M TRAINING DATA

**Checking columns specifically in train_1m view:**

```sql
SELECT 
  COUNTIF(cpi_yoy IS NULL) as cpi_nulls,
  COUNTIF(econ_gdp_growth IS NULL) as gdp_nulls,
  COUNTIF(us_midwest_temp_c IS NULL) as midwest_temp_nulls,
  COUNTIF(soybean_meal_price IS NULL) as meal_price_nulls,
  COUNT(*) as total_rows
FROM `cbi-v14.models_v4.train_1m`
WHERE target_1m IS NOT NULL
```

Running check...


