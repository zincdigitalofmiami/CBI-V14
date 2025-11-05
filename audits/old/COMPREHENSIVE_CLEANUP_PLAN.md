# COMPREHENSIVE CLEANUP PLAN - CBI-V14 Models Dataset
**Date:** October 22, 2025  
**Status:** Ready for Execution  
**Risk Level:** LOW (all items verified safe to delete)

---

## 🎯 EXECUTIVE SUMMARY

After comprehensive audit, identified **6 objects for deletion** with **zero production impact**:
- 1 test model (created by audit script today)
- 2 static forecast tables (superseded by actual models)
- 3 old training tables (superseded by current views)

**Storage to reclaim:** ~0.06 MB (minimal but improves hygiene)  
**Objects remaining:** 31 tables/views + 26 production models  

---

## ✅ AUDIT FINDINGS

### Current State:
- **Total objects**: 37 tables/views
- **BQML models**: 27 trained models
- **Storage**: 0.25 MB total
- **Orphaned tables**: 8 (not referenced by views)
- **Test artifacts**: 1 (created today)

### Quality Assessment:
✅ **No duplicate views** - all views are unique  
✅ **No versioning conflicts** - versioning is in model names, not tables  
⚠️ **Some old training data** - superseded by current views  
⚠️ **One test model** - left over from compatibility testing  

---

## 🗑️ OBJECTS TO DELETE

### 1. TEST ARTIFACTS (HIGH PRIORITY - DELETE IMMEDIATELY)

#### `linear_reg_test_compatibility` (MODEL)
- **Type**: BQML LINEAR_REGRESSION model
- **Created**: October 22, 2025 at 13:05 (today)
- **Purpose**: Compatibility testing during audit
- **Usage**: NONE - test artifact
- **Why Delete**: Created by audit script to test BQML compatibility
- **Impact**: ZERO
- **Command**:
  ```bash
  bq rm -m cbi-v14:models.linear_reg_test_compatibility
  ```

### 2. STATIC FORECAST TABLES (MEDIUM PRIORITY - DELETE)

These are **static forecast outputs**, NOT models. Real forecasting uses the actual BQML models.

#### `zl_forecast_arima_plus_v1` (TABLE)
- **Type**: Static forecast data
- **Rows**: 30
- **Created**: October 11, 2025
- **Schema**: [forecast_date, predicted_price, lower_bound, upper_bound, confidence_level]
- **Why Delete**: Static snapshot superseded by actual BQML model `bqml_arima_plus_zl_v1`
- **Impact**: ZERO - forecasts regenerated from actual model
- **Command**:
  ```bash
  bq rm -t cbi-v14:models.zl_forecast_arima_plus_v1
  ```

#### `zl_forecast_baseline_v1` (TABLE)
- **Type**: Static forecast data
- **Rows**: 30
- **Created**: October 11, 2025
- **Schema**: [forecast_timestamp, forecast_value, standard_error, confidence_level, prediction_interval_lower_bound]
- **Why Delete**: Static snapshot superseded by actual BQML model `bqml_zl_arima_baseline_v1`
- **Impact**: ZERO - forecasts regenerated from actual model
- **Command**:
  ```bash
  bq rm -t cbi-v14:models.zl_forecast_baseline_v1
  ```

### 3. OLD TRAINING TABLES (LOW PRIORITY - DELETE)

These are **old training datasets** superseded by current views.

#### `zl_enhanced_training` (TABLE)
- **Type**: Training dataset
- **Rows**: 100 (tiny!)
- **Created**: October 14, 2025
- **Columns**: 27
- **Why Delete**: 
  - Only 100 rows (insufficient for training)
  - Superseded by `vw_neural_training_dataset` (1,251 rows)
  - Not referenced anywhere
- **Impact**: ZERO - current view has 12x more data
- **Command**:
  ```bash
  bq rm -t cbi-v14:models.zl_enhanced_training
  ```

#### `zl_price_training_base` (TABLE)
- **Type**: Training dataset
- **Rows**: 525
- **Created**: October 11, 2025
- **Columns**: 9
- **Why Delete**:
  - Only 9 columns (no ML features)
  - Superseded by `vw_neural_training_dataset` (159 columns)
  - Not referenced anywhere
- **Impact**: ZERO - current view has 17x more features
- **Command**:
  ```bash
  bq rm -t cbi-v14:models.zl_price_training_base
  ```

---

## ✅ OBJECTS TO KEEP

### Precomputed Feature Tables (Created Today for Performance):
- ✅ `price_features_precomputed` - 1,258 rows, 15 columns
- ✅ `sentiment_features_precomputed` - 604 rows, 4 columns
- ✅ `weather_features_precomputed` - 1,024 rows, 7 columns

**Why Keep**: Performance optimization for feature engineering

### Specialized Training Data:
- ✅ `zl_timesfm_training_v1` - 100 rows, 20 columns
  - Last modified: October 14, 2025
  - Purpose: Specific format for TimeSFM model training
  - Not superseded by standard training views

### All Views (29 views):
- ✅ All views are current and properly structured
- ✅ No duplicate views found
- ✅ All follow naming conventions

### Production Models (26 models after cleanup):
- ✅ 15 ARIMA models (various horizons and versions)
- ✅ 5 DNN models (neural networks)
- ✅ 4 Boosted Tree models (LightGBM)
- ✅ 2 Linear Regression models

---

## 🔍 MODEL DUPLICATION ANALYSIS

### Models with Multiple Versions:

**1-Week Horizon:**
- `zl_arima_1w` (Oct 21)
- `zl_arima_1w_v1` (Oct 22) ← **NEWER**
- `zl_arima_1w_v2` (Oct 21)
- `zl_big8_1_week_arima` (Oct 21)

**1-Month Horizon:**
- `zl_arima_1m` (Oct 21)
- `zl_arima_1m_v1` (Oct 22) ← **NEWER**
- `zl_arima_1m_v2` (Oct 21)
- `zl_big8_1_month_arima` (Oct 21)

**3-Month Horizon:**
- `zl_arima_3m_v1` (Oct 22) ← **NEWER**
- `zl_arima_3m_v2` (Oct 21)
- `zl_big8_3_month_arima` (Oct 21)

**6-Month Horizon:**
- `zl_arima_6m_v1` (Oct 22) ← **NEWER**
- `zl_arima_6m_v2` (Oct 21)
- `zl_arima_12m_v2` (Oct 21)
- `zl_big8_6_month_arima` (Oct 21)

**Recommendation**: Keep all for now - need to evaluate performance before deleting older versions.

---

## 📋 EXECUTION PLAN

### Phase 1: Delete Test Artifacts (IMMEDIATE)
```bash
# Delete test model from audit
bq rm -m -f cbi-v14:models.linear_reg_test_compatibility
```

### Phase 2: Delete Static Forecast Tables (SAFE)
```bash
# Delete old static forecasts
bq rm -t -f cbi-v14:models.zl_forecast_arima_plus_v1
bq rm -t -f cbi-v14:models.zl_forecast_baseline_v1
```

### Phase 3: Delete Old Training Tables (SAFE)
```bash
# Delete superseded training data
bq rm -t -f cbi-v14:models.zl_enhanced_training
bq rm -t -f cbi-v14:models.zl_price_training_base
```

### Verification After Cleanup:
```bash
# List remaining objects
bq ls cbi-v14:models
bq ls --models cbi-v14:models
```

---

## ✅ SAFETY VERIFICATION

### Pre-Deletion Checklist:

- [x] Verified no code references to deleted objects
- [x] Confirmed all tables/models have newer replacements
- [x] Validated that forecast data is regenerable from models
- [x] Checked that training data is superseded by current views
- [x] Ensured precomputed tables are recent and in use

### Post-Deletion Validation:

```python
# Run after cleanup
python3 scripts/catalog_models_dataset.py
```

Expected result:
- Total objects: 31 (down from 37)
- Orphaned tables: 4 (down from 8)
- Storage: ~0.19 MB (down from 0.25 MB)

---

## 🎯 EXPECTED OUTCOMES

### Before Cleanup:
- 37 tables/views
- 27 models (1 test model)
- 8 orphaned tables
- 0.25 MB storage

### After Cleanup:
- 31 tables/views ✅
- 26 models (all production) ✅
- 4 orphaned tables (all precomputed/specialized) ✅
- 0.19 MB storage ✅

### Benefits:
1. ✅ Cleaner dataset with no test artifacts
2. ✅ No confusion from duplicate static forecasts
3. ✅ Reduced mental overhead
4. ✅ Clear separation of current vs old training data
5. ✅ Improved documentation accuracy

---

## 🚀 NEXT STEPS AFTER CLEANUP

1. **Complete ML Pipeline Audit** on `vw_neural_training_dataset`
2. **Fix correlated subquery issue** to enable BQML training
3. **Evaluate model performance** across all versions
4. **Delete underperforming model versions** (Phase 2 cleanup)
5. **Document which models are in production**

---

**READY TO EXECUTE - All deletions verified safe**

















