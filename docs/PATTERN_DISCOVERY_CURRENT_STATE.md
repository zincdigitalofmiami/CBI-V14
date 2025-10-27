# PATTERN DISCOVERY SYSTEM - CURRENT STATE AUDIT
**Date:** October 22, 2025  
**Purpose:** Document existing infrastructure before adding automated learning loop

---

## ✅ WHAT ALREADY EXISTS (DO NOT RECREATE)

### 1. WORKING INFRASTRUCTURE (33 objects)

**Core Training Dataset:**
- ✅ `vw_neural_training_dataset` - 1,251 rows × 159 features (PRIMARY - WORKING)
- ✅ `vw_master_feature_set` - 1,259 rows (WORKING)

**Feature Engineering Views (ALL WORKING):**
- ✅ `vw_correlation_features` - 1,261 rows (35 correlation features)
- ✅ `vw_seasonality_features` - 1,258 rows (seasonal patterns)
- ✅ `vw_crush_margins` - 1,265 rows (crush spread signals)
- ✅ `vw_cross_asset_lead_lag` - 709 rows (28 lead/lag features)
- ✅ `vw_event_driven_features` - 1,258 rows (16 event features)
- ✅ `vw_china_import_tracker` - 683 rows (10 China signals)
- ✅ `vw_brazil_export_lineup` - 1,258 rows (9 Brazil signals)
- ✅ `vw_trump_xi_volatility` - 683 rows (13 tension features)
- ✅ `vw_price_anomalies` - 65 rows (outlier detection)

**Commodity Price Views (ALL WORKING):**
- ✅ `vw_soybean_oil_ordered` - 1,259 rows
- ✅ `vw_crude_oil_prices_daily` - 1,258 rows
- ✅ `vw_palm_oil_ordered` - 1,256 rows
- ... (9 total commodity price views)

**Trained Models (5 models in BigQuery ML):**
- ✅ `zl_forecast_baseline_v1` - ARIMA baseline
- ✅ `zl_forecast_arima_plus_v1` - Enhanced ARIMA
- ✅ `zl_price_training_base` - 525 rows historical
- ✅ `zl_enhanced_training` - 100 rows enhanced
- ✅ `zl_timesfm_training_v1` - 100 rows TimesFM

**Feature Registry:**
- ✅ `forecasting_data_warehouse.feature_metadata` - 29 features registered
  - Columns: feature_name, feature_type, asset_class, economic_meaning, directional_impact, typical_lag_days, source_table, related_features, chat_aliases, policy_impact_score, source_reliability_score, etc.

**Pattern Discovery Scripts (EXISTING):**
- ✅ `scripts/build_neural_obscure_connections.py` - Creates interaction features
- ✅ `scripts/create_biofuel_neural_features.py` - Biofuel pattern discovery
- ✅ `scripts/fix_neural_dataset_properly.py` - Dataset maintenance
- ✅ `scripts/create_comprehensive_neural_dataset.py` - Comprehensive features

---

## ❌ BROKEN INFRASTRUCTURE (4 objects - DO NOT USE)

1. **`vw_neural_interaction_features`** 
   - Error: References deleted view `vw_neural_training_dataset_v2_FIXED`
   - Status: Needs fixing to reference `vw_neural_training_dataset`
   - Purpose: Neural interaction features for obscure pattern discovery

2. **`vw_biofuel_bridge_features`**
   - Error: Column `biofuel_price_strength` not found
   - Status: Needs schema fix
   - Purpose: Biofuel policy linkages

3. **`vw_elasticity_features`**
   - Error: Column `china_relations_signal` not found
   - Status: Needs schema fix
   - Purpose: Price elasticity calculations

4. **`vw_regime_features`**
   - Error: Column `harvest_pace_signal` not found
   - Status: Needs schema fix
   - Purpose: Market regime detection

---

## 🔍 WHAT'S MISSING FOR AUTOMATED PATTERN DISCOVERY

### Currently No Infrastructure For:

1. **Model Explainability Tracking**
   - No table to store SHAP values from trained models
   - No feature importance logging
   - No tracking of which features matter most

2. **Pattern Discovery Log**
   - No table to record obscure correlations discovered
   - No confidence scores for new patterns
   - No trigger mechanism to flag interesting patterns

3. **Data Source API Registry**
   - Feature metadata exists BUT no API endpoints registered
   - No automated query templates
   - No similar-data-finder logic

4. **Feedback Loop Orchestrator**
   - No automated pipeline to:
     - Extract SHAP values after training
     - Identify high-importance obscure features
     - Query registry for similar data sources
     - Automatically ingest new related data
     - Retrain with expanded features

5. **Pattern Lifecycle Management**
   - No decay tracking for pattern relevance
   - No validation of pattern stability over time
   - No automated deactivation of stale patterns

---

## 📋 ARCHITECTURE FOR SELF-LEARNING LOOP

### Proposed Addition (WITHOUT BREAKING EXISTING):

```
CURRENT FLOW:
Raw Data → Feature Views → Training Dataset → BQML Training → Model

NEEDED ADDITION:
                    ↓
              [After Training]
                    ↓
         1. Extract SHAP Values
                    ↓
         2. Log to Pattern Discovery Table
                    ↓
         3. Query Feature Registry for Similar Data
                    ↓
         4. Trigger Data Acquisition Scripts
                    ↓
         5. Create New Feature Views
                    ↓
         6. Add to Training Dataset (expand columns)
                    ↓
         7. Retrain → Compare Performance → Keep if Better
```

### Required New Tables:

```sql
-- 1. Model Explainability Log
CREATE TABLE models.model_explainability (
    model_name STRING,
    training_date DATE,
    feature_name STRING,
    shap_value_mean FLOAT64,
    shap_value_std FLOAT64,
    feature_importance_rank INT64,
    is_obscure_pattern BOOL,  -- Not obvious from domain knowledge
    confidence_score FLOAT64
);

-- 2. Pattern Discovery Log
CREATE TABLE models.pattern_discoveries (
    discovery_id STRING,
    discovered_date TIMESTAMP,
    pattern_type STRING,  -- 'correlation', 'interaction', 'regime', 'anomaly'
    feature_combo ARRAY<STRING>,
    strength_score FLOAT64,
    validation_status STRING,  -- 'candidate', 'validated', 'rejected'
    similar_data_sources ARRAY<STRING>,  -- From registry lookup
    action_taken STRING,  -- 'data_acquired', 'feature_created', 'pending'
    performance_impact FLOAT64  -- MAPE improvement if retrained
);

-- 3. Data Source API Registry (extends feature_metadata)
ALTER TABLE forecasting_data_warehouse.feature_metadata
ADD COLUMN api_endpoint STRING,
ADD COLUMN query_template STRING,
ADD COLUMN similar_features ARRAY<STRING>,
ADD COLUMN auto_acquire_enabled BOOL;
```

### Required Scripts:

```python
# scripts/extract_model_explainability.py
- After BQML training, extract feature importance
- Log to model_explainability table
- Flag obscure high-importance features

# scripts/discover_patterns_from_shap.py  
- Query explainability log for surprising patterns
- Look for interaction effects
- Log to pattern_discoveries table

# scripts/find_similar_data_sources.py
- Query feature_registry for related features
- Use semantic similarity on economic_meaning
- Return list of potential data sources

# scripts/auto_acquire_data.py
- Given API endpoint from registry
- Fetch new data
- Load to staging table
- Trigger feature engineering

# scripts/orchestrate_learning_loop.py
- Master orchestrator
- Run after each training cycle
- Coordinate: extract → discover → find → acquire → retrain
```

---

## ⚠️ CRITICAL: WHAT NOT TO DO

1. ❌ DO NOT recreate `vw_neural_training_dataset` - IT WORKS (1,251 rows × 159 columns)
2. ❌ DO NOT modify working feature views - They feed into training dataset
3. ❌ DO NOT change schema of `feature_metadata` without migration script
4. ❌ DO NOT break existing model training scripts
5. ✅ ONLY ADD new tables/scripts that EXTEND existing system

---

## 🎯 NEXT STEPS (SAFE TO IMPLEMENT)

### Phase 1: Monitoring (Read-Only)
1. Fix 4 broken views to reference correct tables
2. Add explainability extraction script (reads BQML models, writes to new table)
3. Create pattern_discoveries table (new, doesn't affect existing)

### Phase 2: Discovery (Read-Only + Logging)
4. Build pattern discovery script (reads explainability, writes discoveries)
5. Enhance feature_metadata with API fields (additive columns only)
6. Build similar-data-finder (reads registry, returns suggestions)

### Phase 3: Automation (Writes New Data)
7. Build data acquisition scripts (writes to NEW staging tables)
8. Build feature engineering automation (creates NEW views)
9. Test expanded training dataset (NEW view, doesn't touch existing)
10. Compare performance (if better, promote; if worse, rollback)

---

## ✅ CURRENT SYSTEM STATUS

**Working Objects:** 33/37 (89%)  
**Training Dataset:** ✅ OPERATIONAL (1,251 × 159)  
**Trained Models:** ✅ 5 BQML models exist  
**Feature Registry:** ✅ 29 features documented  
**Pattern Discovery:** ⚠️ Infrastructure exists but broken  
**Automated Learning Loop:** ❌ NOT IMPLEMENTED YET  

**Recommendation:** Fix 4 broken views, then build Phase 1 monitoring WITHOUT touching working infrastructure.





