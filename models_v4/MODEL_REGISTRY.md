# V4 Model Registry - CBI-V14

**Created:** October 23, 2025  
**Location:** us-central1  
**Training Data:** `cbi-v14.models_v4.training_dataset_v4` (1,263 rows, 28 features)

## Production V3 Models (PROTECTED - DO NOT MODIFY)

| Model | Horizon | MAE | R² | MAPE | Status |
|-------|---------|-----|----|----|--------|
| zl_boosted_tree_1w_v3 | 1 week | 1.72 | 0.956 | 3.4% | ✅ PRODUCTION |
| zl_boosted_tree_1m_v3 | 1 month | 2.81 | 0.892 | 5.6% | ✅ PRODUCTION |
| zl_boosted_tree_3m_v3 | 3 months | 3.69 | 0.796 | 7.4% | ✅ PRODUCTION |
| zl_boosted_tree_6m_v3 | 6 months | 4.08 | 0.647 | 8.2% | ✅ PRODUCTION |

## V4 Models (In Development)

### AutoML Models
| Model | Horizon | Target | Budget Hours | Status | MAE | MAPE | Notes |
|-------|---------|--------|--------------|--------|-----|------|-------|
| zl_automl_1w_v4 | 1 week | target_1w | 1.0 | 🔄 PENDING | - | - | Goal: MAPE < 2.0% |
| zl_automl_1m_v4 | 1 month | target_1m | 1.0 | 🔄 PENDING | - | - | Goal: MAPE < 2.0% |
| zl_automl_3m_v4 | 3 months | target_3m | 1.5 | 🔄 PENDING | - | - | Goal: MAPE < 2.0% |
| zl_automl_6m_v4 | 6 months | target_6m | 1.5 | 🔄 PENDING | - | - | Goal: MAPE < 2.0% |

### Fixed DNN Models (with TRANSFORM normalization)
| Model | Horizon | Target | Hidden Units | Status | MAE | MAPE | Notes |
|-------|---------|--------|--------------|--------|-----|------|-------|
| zl_dnn_1w_v4 | 1 week | target_1w | [256,128,64,32] | 🔄 PENDING | - | - | Fixes broken V3 DNN |
| zl_dnn_1m_v4 | 1 month | target_1m | [256,128,64,32] | 🔄 PENDING | - | - | Fixes broken V3 DNN |

### ARIMA+ Models (validated)
| Model | Horizon | Target | Auto-ARIMA | Status | Directional Accuracy | Notes |
|-------|---------|--------|------------|--------|---------------------|-------|
| zl_arima_1w_v4 | 1 week | target_1w | TRUE | 🔄 PENDING | - | Baseline for ensemble |
| zl_arima_1m_v4 | 1 month | target_1m | TRUE | 🔄 PENDING | - | Baseline for ensemble |
| zl_arima_3m_v4 | 3 months | target_3m | TRUE | 🔄 PENDING | - | Baseline for ensemble |
| zl_arima_6m_v4 | 6 months | target_6m | TRUE | 🔄 PENDING | - | Baseline for ensemble |

### Ensemble Models (weighted blend)
| Model | Horizon | Composition | Status | MAE | MAPE | Notes |
|-------|---------|-------------|--------|-----|------|-------|
| zl_ensemble_1w_v4 | 1 week | 40% Boosted + 30% AutoML + 20% DNN + 10% ARIMA | 🔄 PENDING | - | - | Target: < V3 MAE |
| zl_ensemble_1m_v4 | 1 month | 40% Boosted + 30% AutoML + 20% DNN + 10% ARIMA | 🔄 PENDING | - | - | Target: < V3 MAE |
| zl_ensemble_3m_v4 | 3 months | 40% Boosted + 30% AutoML + 20% DNN + 10% ARIMA | 🔄 PENDING | - | - | Target: < V3 MAE |
| zl_ensemble_6m_v4 | 6 months | 40% Boosted + 30% AutoML + 20% DNN + 10% ARIMA | 🔄 PENDING | - | - | Target: < V3 MAE |

## Performance Targets

**Strict Requirements:**
- 1W Forecast: MAPE < 2.0% (MAE < 1.0)
- 1M Forecast: MAPE < 2.0% (MAE < 1.0)
- 3M Forecast: MAPE < 2.0% (MAE < 1.0)
- 6M Forecast: MAPE < 2.0% (MAE < 1.0)

**Current V3 Baseline:**
- V3 models achieve 3.4-8.2% MAPE
- V4 must improve by 40-75% to meet 2% target

## Safety Protocol

1. **NEVER modify production V3 models**
2. **NEVER modify `cbi-v14.models.training_dataset`**
3. **NEVER create models in `cbi-v14.models` dataset**
4. **ALWAYS use `cbi-v14.models_v4` for new work**
5. **ALWAYS verify V3 API operational before/after changes**

## Training Log

### Phase 1: Infrastructure Setup (October 23, 2025)
- ✅ Created `cbi-v14.models_v4` dataset (us-central1)
- ✅ Created `training_dataset_v4` view (1,263 rows)
- ✅ Verified V3 API operational (MAE: 1.72, R²: 0.956)
- ✅ Created MODEL_REGISTRY.md

### Phase 2: Model Training (In Progress)
- 🔄 AutoML models: PENDING
- 🔄 Fixed DNN models: PENDING
- 🔄 ARIMA+ models: PENDING
- 🔄 Ensemble models: PENDING

---

**Last Updated:** October 23, 2025 - 13:52 UTC  
**Status:** Phase 1 Complete, Phase 2 Starting

