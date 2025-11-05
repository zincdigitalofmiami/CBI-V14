# Comprehensive Connection Audit Report

**Date:** November 5, 2025  
**Status:** ✅ **COMPLETE**

---

## Executive Summary

**Critical Finding:** Both model name conventions exist in BigQuery:
- **Short names:** `bqml_1w`, `bqml_1m`, `bqml_3m`, `bqml_6m` ✅ **USED IN PRODUCTION**
- **Long names:** `bqml_1w_all_features`, `bqml_1m_all_features`, `bqml_3m_all_features`, `bqml_6m_all_features` ✅ **CREATED BY TRAINING FILES**

**Decision:** Production forecast generation uses **SHORT names** to match existing predictions.

---

## Audit Results

### 1. Model Existence Check

**✅ Both sets exist:**
- `bqml_1w` ✅ EXISTS
- `bqml_1m` ✅ EXISTS
- `bqml_3m` ✅ EXISTS
- `bqml_6m` ✅ EXISTS
- `bqml_1w_all_features` ✅ EXISTS
- `bqml_1m_all_features` ✅ EXISTS
- `bqml_3m_all_features` ✅ EXISTS
- `bqml_6m_all_features` ✅ EXISTS

### 2. Training Files Analysis

**Training files CREATE (with `_all_features`):**
- `BQML_1W_PRODUCTION.sql` → Creates `bqml_1w_all_features`
- `BQML_1M_PRODUCTION.sql` → Creates `bqml_1m_all_features`
- `BQML_3M_PRODUCTION.sql` → Creates `bqml_3m_all_features`
- `BQML_6M_PRODUCTION.sql` → Creates `bqml_6m_all_features`

### 3. Production Predictions Analysis

**Predictions table `model_name` field:**
```
bqml_1w  (1 row, latest: 2025-11-04)
bqml_1m  (1 row, latest: 2025-11-04)
bqml_3m  (1 row, latest: 2025-11-04)
bqml_6m  (1 row, latest: 2025-11-04)
```

**Conclusion:** Production uses **SHORT names** (`bqml_1w`, etc.)

### 4. Forecast Generation SQL

**Current state (CORRECTED):**
- `GENERATE_PRODUCTION_FORECASTS_V3.sql` now uses:
  - `ML.PREDICT(MODEL bqml_1w)` ✅
  - `model_name: 'bqml_1w'` ✅
  - Matches production predictions table ✅

---

## Connection Map

### Critical Data Flow Paths

**Path 1: Training → Models → Forecasts**
```
training_dataset_super_enriched (431 references)
  ↓
bqml_1w, bqml_1m, bqml_3m, bqml_6m (production models)
  ↓
production_forecasts (model_name: bqml_1w, etc.)
```

**Path 2: Big8 Signal → Forecasts**
```
api.vw_big8_composite_signal
  ↓
production_forecasts (regime, confidence, crisis flags)
```

### Dataset Inventory

**10 Datasets:**
- `cbi-v14.api` - API views
- `cbi-v14.forecasting_data_warehouse` - Source data
- `cbi-v14.models_v4` - Models and training data
- `cbi-v14.predictions_uc1` - Forecasts
- `cbi-v14.curated` - Curated views
- `cbi-v14.staging` - Staging tables
- `cbi-v14.signals` - Signal calculations
- `cbi-v14.market_data` - Market data
- `cbi-v14.neural` - Neural network models
- `cbi-v14.temp` - Temporary tables

### Reference Counts

**Top Referenced Tables:**
1. `training_dataset_super_enriched`: 431 references
2. `economic_indicators`: 38 references
3. `yahoo_finance_enhanced`: 38 references
4. `production_forecasts`: 36 references
5. `weather_data`: 18 references

**Models:**
- 29 models referenced across codebase
- Production models: `bqml_1w`, `bqml_1m`, `bqml_3m`, `bqml_6m`

**Views:**
- 23 views referenced
- Critical: `api.vw_big8_composite_signal`

---

## Files Analyzed

- **124 SQL files** scanned
- **66 Python scripts** scanned
- **208 tables** referenced
- **29 models** referenced
- **23 views** referenced

---

## Fixes Applied

### ✅ Fix 1: Model Name Correction

**Issue:** Forecast generation SQL referenced `bqml_1w_all_features` but production uses `bqml_1w`

**Fix:** Updated `GENERATE_PRODUCTION_FORECASTS_V3.sql` to use:
- `ML.PREDICT(MODEL bqml_1w)` (short name)
- `model_name: 'bqml_1w'` (matches predictions table)

**Status:** ✅ **FIXED**

---

## Recommendations

1. **Model Naming Standardization:**
   - Consider consolidating to one naming convention
   - Current: Both exist (short for production, long for training)

2. **Documentation:**
   - Document which models are production vs training
   - Update plan to reflect production model names

3. **Monitoring:**
   - Track which models are actually used in production
   - Verify model_name consistency across all predictions

---

**Full Report:** `docs/data-datasets/connection_audit_report.json`

**Last Updated:** November 5, 2025

