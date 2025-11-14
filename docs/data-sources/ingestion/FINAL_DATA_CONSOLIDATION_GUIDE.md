# 🚀 FINAL DATA CONSOLIDATION GUIDE
**Date:** November 6, 2025  
**Last Reviewed:** November 14, 2025  
**Purpose:** Achieve ZERO stale data and leverage ALL available resources

**Note**: BQML deprecated - all training now runs locally on Mac M4 via TensorFlow Metal. BQML SQL examples in this document are historical.

---

## ✅ WHAT WE DISCOVERED

### 1. **Vertex AI Export Data - THE GOLD MINE!**
```
Dataset: export_evaluated_data_items_cbi_v14_automl_pilot_1w_2025_10_28T10_08_35_327Z
Table: evaluated_data_items
```
- **200+ columns** of ALL features
- **112 rows** with predictions and confidence intervals
- **Perfect for:** Feature importance, gap filling, validation
- **KEEP FOREVER** - This is invaluable for optimization

### 2. **Massive Data Resources**
- **50+ tables** in forecasting_data_warehouse
- **300 features** available across all sources
- **5+ years** of historical data
- **56 heavy hitter features** (VIX, Tariffs, Biofuels)

### 3. **Current Problems**
| Issue | Impact | Solution |
|-------|--------|----------|
| Production data 57 days stale | Models using old data | Run ULTIMATE_DATA_CONSOLIDATION.sql |
| Sep 11-Oct 27 data gap | Missing 47 days | Fill with Vertex AI export |
| Feature importance unknown | Can't optimize | Extract from Vertex AI correlations |
| Scattered data sources | Confusion | Consolidate into production_training_data_* |

---

## 🎯 THE SOLUTION: ULTIMATE_DATA_CONSOLIDATION.sql

### What It Does:
1. **Extends dates** using Big 8 signals (current through Nov 6!)
2. **Fills gaps** with Vertex AI export data (Sep 11-Oct 27)
3. **Updates current data** from prices, VIX, palm (Oct 28-Nov 6)
4. **Forward-fills** sparse features (China imports, Argentina)
5. **Populates feature importance** from Vertex AI correlations
6. **Replicates** to all horizons (1w, 1m, 3m, 6m)

### How to Run:
```bash
# Easy method:
chmod +x scripts/run_ultimate_consolidation.sh
./scripts/run_ultimate_consolidation.sh

# Or direct:
bq query --use_legacy_sql=false < bigquery-sql/ULTIMATE_DATA_CONSOLIDATION.sql
```

---

## 📊 USING VERTEX AI DATA FOR OPTIMIZATION

### Extract Feature Importance:
```sql
-- Top features by correlation with target
SELECT 
  feature,
  importance_score,
  RANK() OVER (ORDER BY importance_score DESC) as rank
FROM `cbi-v14.predictions_uc1.model_feature_importance`
WHERE horizon = '1w'
ORDER BY importance_score DESC
LIMIT 20
```

### Create Focused Models:
```sql
-- Use only top 50 features for faster training
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_1w_focused`
OPTIONS(
  model_type='LINEAR_REG',
  input_label_cols=['target_1w'],
  max_iterations=100
) AS
SELECT 
  -- Only top 50 features from importance ranking
  china_soybean_imports_mt,
  vix_level,
  palm_price,
  feature_vix_stress,
  feature_tariff_threat,
  -- ... (45 more top features)
  target_1w
FROM `cbi-v14.models_v4.production_training_data_1w`
WHERE date >= '2024-01-01'
```

### Compare Models:
```sql
-- Full 300 features vs Focused 50 features
SELECT 
  'Full Model (300 features)' as model,
  mean_absolute_error,
  r2_score
FROM ML.EVALUATE(MODEL `cbi-v14.models_v4.bqml_1w`)

UNION ALL

SELECT 
  'Focused Model (50 features)',
  mean_absolute_error,
  r2_score  
FROM ML.EVALUATE(MODEL `cbi-v14.models_v4.bqml_1w_focused`)
```

---

## 🔥 WHY KEEP VERTEX AI DATA FOREVER

**Nov 2025 Decision - Documented for Future Reference:**

1. **Feature Importance Rankings** - Shows what Vertex AI considered important
2. **Historical Benchmark** - Oct 28, 2025 model performance baseline
3. **Confidence Intervals** - Has prediction bounds for uncertainty analysis
4. **Gap Filling** - Critical for Sep-Oct 2025 missing data
5. **Feature Discovery** - May contain features we missed
6. **Validation** - Export to Parquet and compare local Mac M4 vs Vertex AI predictions (BQML deprecated)
7. **Optimization** - Use for feature selection and focused models

**Storage Cost:** ~$0.02/month (negligible)
**Value:** Priceless for model optimization

---

## ✅ SUCCESS CHECKLIST

- [ ] Run ULTIMATE_DATA_CONSOLIDATION.sql
- [ ] Verify latest date is Nov 6, 2025
- [ ] Check all 300 features populated
- [ ] Feature importance table populated
- [ ] Archive old tables
- [ ] Set up daily refresh pipeline
- [ ] Create focused models with top features
- [ ] Document in execution plan

---

## 📝 FILES UPDATED

1. **CBI_V14_COMPLETE_EXECUTION_PLAN.md** - Added MASTER DATA CATALOG section
2. **ULTIMATE_DATA_CONSOLIDATION.sql** - The consolidation script
3. **ZERO_STALE_DATA_ACTION_PLAN.md** - Action plan
4. **DATA_CATALOG_SUMMARY.md** - Quick reference
5. **scripts/run_ultimate_consolidation.sh** - Easy execution

---

**REMEMBER:** The Vertex AI export data is GOLD - never delete it!






