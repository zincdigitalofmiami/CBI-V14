# SELF-LEARNING PATTERN DISCOVERY SYSTEM
**Date:** October 22, 2025  
**Status:** ARCHITECTURE DEFINED - READY TO IMPLEMENT  
**Question:** "When the neural net finds obscure connections, how will this system record this information and observation and automatically go after more data like it in efforts to 'do deeper'?"

---

## 🎯 ANSWER: THE SELF-LEARNING LOOP

### Current Infrastructure (Clean, Post-Naming-Standardization)

**✅ CANONICAL TRAINING DATASET:**
- `models.vw_neural_training_dataset` - 1,251 rows × 159 features
- Date range: 2020-10-21 to 2025-10-13
- Targets: 1w, 1m, 3m, 6m horizons
- **This is the ONLY neural training dataset - all v2/v3 variants removed**

**✅ FEATURE REGISTRY:**
- `forecasting_data_warehouse.feature_metadata` - 29 features documented
- Tracks: feature_name, feature_type, asset_class, economic_meaning, source_table, related_features

**✅ WORKING PATTERN DETECTION:**
- `vw_price_anomalies` - 65 anomaly records (WORKING)

**❌ BROKEN PATTERN VIEWS (need fixing):**
- `vw_neural_interaction_features` - References deleted dataset
- `vw_biofuel_bridge_features` - Missing columns
- `vw_elasticity_features` - Missing columns  
- `vw_regime_features` - Missing columns

**✅ PATTERN DISCOVERY SCRIPTS (exist but reference old names):**
- `scripts/build_neural_obscure_connections.py`
- `scripts/create_biofuel_neural_features.py`

---

## 🔄 THE SELF-LEARNING LOOP ARCHITECTURE

### Phase 1: Training & Explainability Extraction

```
┌─────────────────────────────────────────────────────────────┐
│ 1. MODEL TRAINING (BigQuery ML)                            │
│    • Train on vw_neural_training_dataset (159 features)    │
│    • Algorithms: DNN, LightGBM, ARIMA, AutoML              │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. EXTRACT MODEL EXPLAINABILITY                             │
│    • Use ML.EXPLAIN_PREDICT() to get SHAP values           │
│    • Use ML.FEATURE_IMPORTANCE() to rank features          │
│    • Log to NEW TABLE: models.model_explainability_log     │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ TABLE: models.model_explainability_log                      │
│ ┌───────────────────────────────────────────────────────┐  │
│ │ • model_name: "zl_dnn_6m_v1"                          │  │
│ │ • training_date: 2025-10-22                           │  │
│ │ • feature_name: "feature_biofuel_cascade"             │  │
│ │ • shap_value_mean: 2.47  ← HIGH IMPORTANCE!           │  │
│ │ • feature_importance_rank: 3                          │  │
│ │ • is_obscure_pattern: TRUE  ← Not obvious from theory │  │
│ │ • confidence_score: 0.89                              │  │
│ └───────────────────────────────────────────────────────┘  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼ (Automated trigger when is_obscure_pattern=TRUE 
                     AND importance_rank < 10)
```

### Phase 2: Pattern Discovery & Hypothesis Generation

```
┌─────────────────────────────────────────────────────────────┐
│ 3. PATTERN DISCOVERY ANALYZER                               │
│    • Script: discover_obscure_patterns.py (NEW)            │
│    • Query: SELECT * FROM model_explainability_log         │
│             WHERE is_obscure_pattern = TRUE                 │
│             AND shap_value_mean > threshold                 │
│    • Identify: Interaction effects, non-linear patterns    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. HYPOTHESIS GENERATION                                    │
│    • Found: "biofuel_cascade" has high importance          │
│    • Hypothesis: EPA policy + crush margins + palm price   │
│                  = Strong soy oil price predictor          │
│    • Log to: models.pattern_discoveries                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ TABLE: models.pattern_discoveries                           │
│ ┌───────────────────────────────────────────────────────┐  │
│ │ • discovery_id: "disc_20251022_001"                   │  │
│ │ • discovered_date: 2025-10-22 18:30:00                │  │
│ │ • pattern_type: "interaction"                         │  │
│ │ • feature_combo: ["biofuel_policy", "crush_margin",   │  │
│ │                   "palm_oil_price"]                    │  │
│ │ • strength_score: 0.89                                │  │
│ │ • hypothesis: "EPA RFS mandates drive soy demand..."  │  │
│ │ • similar_data_sources: NULL ← TO BE FILLED           │  │
│ │ • action_status: "pending_data_discovery"             │  │
│ └───────────────────────────────────────────────────────┘  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
```

### Phase 3: Intelligent Data Source Discovery

```
┌─────────────────────────────────────────────────────────────┐
│ 5. QUERY FEATURE REGISTRY FOR SIMILAR DATA                  │
│    • Script: find_similar_data_sources.py (NEW)            │
│    • Input: pattern_discoveries.feature_combo              │
│    • Query: forecasting_data_warehouse.feature_metadata    │
│             WHERE economic_meaning SIMILAR TO pattern      │
│    • Use semantic matching on:                             │
│        - economic_meaning                                  │
│        - related_features                                  │
│        - asset_class                                       │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ EXAMPLE DISCOVERY:                                          │
│ Pattern: "biofuel_cascade" is important                     │
│ Registry Search: "biofuel" OR "renewable" OR "RIN"          │
│ Results Found:                                              │
│   1. EPA RIN prices (already have ✅)                       │
│   2. California LCFS credits (MISSING ❌)                   │
│   3. EU biodiesel mandates (MISSING ❌)                     │
│   4. Brazilian RenovaBio credits (MISSING ❌)               │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. EXPAND FEATURE REGISTRY WITH NEW SOURCES                 │
│    • Add to feature_metadata:                              │
│      - feature_name: "california_lcfs_credit_price"        │
│      - api_endpoint: "https://ww2.arb.ca.gov/lcfs"         │
│      - query_template: "fetch_lcfs_prices(date_range)"     │
│      - auto_acquire_enabled: TRUE                          │
│      - related_features: ["biofuel_policy", "RIN_price"]   │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
```

### Phase 4: Automated Data Acquisition

```
┌─────────────────────────────────────────────────────────────┐
│ 7. AUTOMATED DATA INGESTION                                 │
│    • Script: auto_acquire_similar_data.py (NEW)            │
│    • For each new source in registry:                      │
│        - Execute api_endpoint + query_template             │
│        - Load to staging.auto_discovered_features          │
│        - Run validation checks                             │
│        - Promote to forecasting_data_warehouse             │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. FEATURE ENGINEERING ON NEW DATA                          │
│    • Script: create_discovered_features.py (NEW)           │
│    • Create NEW VIEW: vw_discovered_biofuel_features       │
│    • Calculate: LCFS/RIN spread, policy intensity, etc.    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
```

### Phase 5: Expanded Training & Performance Validation

```
┌─────────────────────────────────────────────────────────────┐
│ 9. EXPAND TRAINING DATASET                                  │
│    • Create: vw_neural_training_dataset_expanded           │
│    • Add columns from: vw_discovered_biofuel_features      │
│    • Now: 159 → 168 features (9 new biofuel features)      │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 10. A/B RETRAIN & COMPARE                                   │
│    • Train model A: Original 159 features                  │
│    • Train model B: Expanded 168 features                  │
│    • Compare: MAPE, RMSE, directional accuracy             │
│    • If Model B wins: Promote to production                │
│    • If Model A wins: Reject expansion, log failure        │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 11. UPDATE PATTERN DISCOVERY LOG                            │
│    • UPDATE models.pattern_discoveries                     │
│      SET validation_status = 'validated',                  │
│          performance_impact = +0.03  (3% MAPE improvement) │
│          action_status = 'deployed'                        │
│    • This pattern is now PROVEN ALPHA                      │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
                LOOP CONTINUES ∞
```

---

## 📊 NEW INFRASTRUCTURE REQUIRED

### 1. New BigQuery Tables

```sql
-- Explainability Log
CREATE TABLE `cbi-v14.models.model_explainability_log` (
    model_name STRING,
    training_date DATE,
    feature_name STRING,
    shap_value_mean FLOAT64,
    shap_value_std FLOAT64,
    feature_importance_rank INT64,
    is_obscure_pattern BOOL,
    confidence_score FLOAT64,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- Pattern Discoveries
CREATE TABLE `cbi-v14.models.pattern_discoveries` (
    discovery_id STRING,
    discovered_date TIMESTAMP,
    pattern_type STRING,  -- 'correlation', 'interaction', 'regime', 'anomaly'
    feature_combo ARRAY<STRING>,
    strength_score FLOAT64,
    hypothesis STRING,
    similar_data_sources ARRAY<STRING>,
    action_status STRING,  -- 'pending', 'data_acquired', 'deployed', 'rejected'
    validation_status STRING,  -- 'candidate', 'validated', 'rejected'
    performance_impact FLOAT64,  -- MAPE improvement or NULL if not deployed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP
);

-- Auto-Discovered Features (Staging)
CREATE TABLE `cbi-v14.staging.auto_discovered_features` (
    source_name STRING,
    feature_name STRING,
    date DATE,
    value FLOAT64,
    metadata JSON,
    discovered_from_pattern_id STRING,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
```

### 2. Extend Feature Metadata (Additive Only)

```sql
-- Add columns to EXISTING table
ALTER TABLE `cbi-v14.forecasting_data_warehouse.feature_metadata`
ADD COLUMN IF NOT EXISTS api_endpoint STRING,
ADD COLUMN IF NOT EXISTS query_template STRING,
ADD COLUMN IF NOT EXISTS similar_features ARRAY<STRING>,
ADD COLUMN IF NOT EXISTS auto_acquire_enabled BOOL DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS discovery_priority INT64;  -- 1=high, 5=low
```

### 3. New Python Scripts

```
scripts/
├── extract_model_explainability.py      (NEW) - Extract SHAP after training
├── discover_obscure_patterns.py         (NEW) - Analyze explainability log
├── find_similar_data_sources.py         (NEW) - Query registry for similar
├── auto_acquire_similar_data.py         (NEW) - Fetch data from APIs
├── create_discovered_features.py        (NEW) - Engineer features from new data
├── expand_training_dataset.py           (NEW) - Add new features to training
├── compare_model_performance.py         (NEW) - A/B test old vs new
└── orchestrate_learning_loop.py         (NEW) - Master coordinator
```

### 4. Update Existing Scripts (Fix Broken References)

```
BROKEN VIEWS TO FIX:
- vw_neural_interaction_features → Update to reference vw_neural_training_dataset (not v2)
- vw_biofuel_bridge_features → Fix missing column references
- vw_elasticity_features → Fix missing column references
- vw_regime_features → Fix missing column references

SCRIPTS TO UPDATE:
- build_neural_obscure_connections.py → Update dataset references
- create_biofuel_neural_features.py → Update dataset references
```

---

## 🔥 EXAMPLE: FULL LOOP IN ACTION

### Iteration 1: Discovering Biofuel Pattern

```
1. Train zl_dnn_6m_v1 on 159 features
   ↓
2. Extract SHAP values
   ↓ Find: "feature_biofuel_cascade" ranks #3 (unexpected!)
   ↓
3. Log to model_explainability_log
   ↓ is_obscure_pattern=TRUE (not obvious from commodity fundamentals)
   ↓
4. Pattern discovery script triggers
   ↓ Hypothesis: "Biofuel policy mandates drive soy oil demand"
   ↓
5. Query feature_metadata for similar data
   ↓ Find: EPA RIN prices (have ✅), CA LCFS (missing ❌), EU mandates (missing ❌)
   ↓
6. Auto-acquire script pulls CA LCFS credit prices
   ↓ Load to staging.auto_discovered_features
   ↓
7. Create vw_discovered_lcfs_features (new view)
   ↓ Features: lcfs_price, lcfs_rin_spread, policy_intensity
   ↓
8. Expand training dataset: 159 → 162 features
   ↓
9. Retrain: Model A (159) vs Model B (162)
   ↓ Model B MAPE: 4.2% | Model A MAPE: 4.5%
   ↓ Model B WINS by 0.3% (7% relative improvement)
   ↓
10. Deploy Model B, update pattern_discoveries
    ↓ validation_status='validated', performance_impact=+0.003
    ↓
LOOP COMPLETE - New features permanently added
```

### Iteration 2: System Goes Deeper

```
Now the system looks for patterns in the NEW features:
- Does LCFS price interact with crush margins?
- Does LCFS/RIN spread predict volatility regimes?
- Should we get state-level biodiesel mandates?

The loop NEVER STOPS discovering and improving.
```

---

## ⚠️ CRITICAL SAFEGUARDS

### 1. Cost Control
- Set `auto_acquire_enabled=FALSE` by default
- Require human approval for new API endpoints
- Budget cap: $50/month for experimental data

### 2. Performance Validation
- NEVER deploy expanded model if performance degrades
- Require minimum 2% relative MAPE improvement
- Backtest on held-out data before production

### 3. Pattern Decay Tracking
- Monitor pattern strength over rolling windows
- Auto-disable features if importance drops below threshold
- Re-validate patterns quarterly

### 4. Data Quality Gates
- Validate new data for completeness, freshness, outliers
- Reject sources with >10% missing data
- Require manual review for non-numeric data

---

## 📈 EXPECTED OUTCOMES

### Short Term (1-2 weeks)
- 4 broken views fixed
- Explainability extraction working
- Pattern discovery logging operational

### Medium Term (1 month)
- First automated data source added
- Training dataset expanded by 5-10 features
- Measurable MAPE improvement from discovered patterns

### Long Term (3-6 months)
- 20+ new features discovered and validated
- Self-learning loop runs weekly without human intervention
- System discovers non-obvious interactions (e.g., freight costs × weather × biofuel policy)
- Platform becomes "smarter" with every training cycle

---

## ✅ NEXT STEPS TO IMPLEMENT

### Phase 1: Fix & Monitor (This Week)
1. ✅ Document current state (DONE - this file)
2. Fix 4 broken pattern views
3. Create explainability extraction script
4. Test SHAP value extraction on existing models

### Phase 2: Discovery Infrastructure (Week 2)
5. Create pattern_discoveries table
6. Build pattern discovery analyzer
7. Enhance feature_metadata with API fields
8. Test similar-data-finder on existing registry

### Phase 3: Automation (Week 3-4)
9. Build data acquisition framework
10. Create feature engineering automation
11. Implement A/B testing framework
12. Deploy orchestrator for full loop

**THIS IS HOW THE SYSTEM GETS SMARTER AUTOMATICALLY.**












