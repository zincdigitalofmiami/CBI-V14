# PREDICTIONS DATA AUDIT - October 30, 2025

## EXECUTIVE SUMMARY
**Status**: ⚠️ INCOMPLETE - Only 1W predictions exist  
**Missing Horizons**: 1M, 3MAMI, 6M  
**Action Required**: Generate predictions for missing horizons

---

## 1. CURRENT PREDICTIONS INVENTORY

### ✅ `predictions.monthly_vertex_predictions` Table

**Total Rows**: 2  
**Available Horizons**: 1W only  
**Latest Prediction Date**: 2025-10-29

| Horizon | Count | Latest Date | Target Date | Predicted Price | MAPE | Model Name |
|---------|-------|-------------|-------------|-----------------|------|------------|
| **1W** | 2 | 2025-10-29 | 2025-11-05 | $50.19 | 2.02% | cbi_v14_automl_pilot_1w |
| **1M** | 0 | ❌ MISSING | - | - | - | - |
| **3M** | 0 | ❌ MISSING | - | - | - | - |
| **6M** | 0 | ❌ MISSING | - | - | - | - |

### ❌ `predictions.daily_forecasts` Table

**Total Rows**: 0  
**Status**: EMPTY - No data  
**Action**: Populate with all horizons (1W, 1M, 3M, 6M)

---

## 2. TABLE SCHEMAS

### `predictions.monthly_vertex_predictions`
Columns:
- `horizon` (STRING) - Prediction horizon (1W, 1M, 3M, 6M)
- `prediction_date` (DATE) - Date prediction was made
- `target_date` (DATE) - Target date for prediction
- `predicted_price` (FLOAT) - Model prediction
- `confidence_lower` (FLOAT) - Lower confidence bound
- `confidence_upper` (FLOAT) - Upper confidence bound
- `mape` (FLOAT) - Mean Absolute Percentage Error
- `model_id` (STRING) - Vertex AI model ID
- `model_name` (STRING) - Model display name
- `created_at` (TIMESTAMP) - When row was created

### `predictions.daily_forecasts`
Schema matches `monthly_vertex_predictions` (same columns)

---

## 3. MODEL INFORMATION

Available Vertex AI Models:
- **1W**: Model ID `575258986094264320` ✅ EXISTS
- **1M**: Model ID `274643710967283712` ✅ EXISTS  
- **3M**: Model ID `3157158578716934144` ✅ EXISTS
- **6M**: Model ID `378857732 multicore3216` ✅ EXISTS

Endpoint Available:
- `soybean_oil_1w_working_endpoint` (ID: `7286867078038945792`) ✅ EXISTS

---

## 4. REQUIRED DATA (What User Needs)

### ✅ 1W Predictions
- **Status**: ✅ EXISTS (2 rows in monthly_vertex_predictions)
- **Latest**: 2025-10-29 → Target: 2025-11-05
- **Price**: $50.19
- **MAPE**: 2.02%

### ❌ 1M Predictions  
- **Status**: ❌ MISSING
- **Needed**: Prediction from today (2025-10-30) → Target: 2025-11-29
- **Model**: `274643710967283712`
- **MAPE**: ~2.5% (based on model info)

### ❌ 3M Predictions
- **Status**: ❌ MISSING  
- **Needed**: Prediction from today (2025-10-30) → Target: 2026-01-28
- **Model**: `3157158578716934144`
- **MAPE**: ~2.68% (based on model info)

### ❌ 6M Predictions
- **Status**: ❌ MISSING
- **Needed**: Prediction from today (2025-10-30) → Target: 2026-04-28
- **Model**: `3788577320223113216`
- **MAPE**: ~2.51% (based on model info)

---

## 5. ADDITIONAL REQUIREMENTS

User needs:
- ✅ All horizons (1W, 1M, 3M, 6M)
- ⚠️ ALL FEATURES - Need to verify features are included
- ⚠️ PREDICTIONS - Missing 3 horizons
- ⚠️ OVERLAYS - Need to check if overlay data exists
- ⚠️ AI ANALYSES - Need to verify AI analysis features
- ⚠️ WALK FORWARDS - Need to verify walk-forward backtesting data
- ⚠️ VIX OVERLAYS - Need to verify VIX overlay data

---

## 6. NEXT STEPS

1. **IMMEDIATE**: Generate predictions for 1M, 3M, 6M horizons
   - Use existing endpoint: `7286867078038945792`
   - Deploy models one at a time
   - Get predictions
   - Save to `predictions.monthly_vertex_predictions`

2. **VERIFY**: Check what features/overlays/AI data exists
   - Audit feature tables
   - Check VIX data availability
   - Verify walk-forward backtesting tables

3. **POPULATE**: Ensure all required data is available
   - Feature data for predictions
   - VIX overlay data
   - Walk-forward historical predictions

---

## 7. FILES TO FIX/RUN

1. `automl/get_remaining_predictions.py` - Needs fix (target columns don't exist)
2. Run fixed script to generate 1M, 3M, 6M predictions
3. Verify all overlays and features are available

---

**LAST UPDATED**: 2025-10-30

