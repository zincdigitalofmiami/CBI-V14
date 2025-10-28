# NEURAL SPECIALIST ARCHITECTURE - POST-BASELINE
**Date:** October 27, 2025  
**Status:** 📋 PLANNED - After Baseline Validation  
**Purpose:** Ensemble enhancement with LSTM/Transformer specialists

---

## BASELINE ESTABLISHED ✅

**Baseline Performance:**
- 1W: 2.38% MAPE
- 1M: 2.06% MAPE  
- 3M: 2.18% MAPE
- 6M: 2.15% MAPE

**Next:** Add neural specialists for pattern recognition beyond baseline capability.

---

## NEURAL SPECIALIST SPECIFICATIONS

### Specialist 1: LSTM Sequence Model
**Purpose:** Capture temporal patterns in price sequences

**Architecture:**
```python
Model Type: LSTM or DNN_REGRESSOR with sequence
Input Window: 30-60 days
Hidden Layers: [64, 32] (keep simple to avoid overfitting)
Dropout: 0.3
Features: Price sequences, Big 8 signal sequences
```

**Focus Areas:**
- Price momentum regimes
- Volatility clustering
- Seasonal pattern recognition

**BigQuery ML Implementation:**
```sql
CREATE MODEL `cbi-v14.models_v4.lstm_specialist_price_patterns`
OPTIONS(
    model_type='DNN_REGRESSOR',
    hidden_units=[64, 32],
    activation_fn='RELU',
    dropout=0.3,
    input_label_cols=['target_1m']
) AS
SELECT 
    target_1m,
    zl_price_lag1, zl_price_lag7, zl_price_lag30,
    return_1d, return_7d,
    volatility_30d,
    feature_vix_stress,
    feature_harvest_pace
FROM training_dataset_super_enriched
WHERE target_1m IS NOT NULL
```

---

### Specialist 2: Transformer Attention Model
**Purpose:** Learn which historical patterns best predict current conditions

**Architecture:**
```python
Model Type: Transformer (if available) or attention-based DNN
Context Window: 90 days
Attention Heads: 4-8
Features: Big 8 signals, correlations, regime indicators
```

**Focus Areas:**
- Regime-specific pattern matching
- Dynamic signal weighting by market condition
- Non-linear feature interactions

**Implementation:** Via external framework (PyTorch/TensorFlow) → BigQuery for inference

---

### Specialist 3: High-VIX Regime Model
**Purpose:** Specialized model for crisis/volatility periods

**Trigger:** VIX > 30 or feature_vix_stress > 0.7

**Architecture:**
```sql
CREATE MODEL `cbi-v14.models_v4.specialist_high_vix_regime`
OPTIONS(
    model_type='BOOSTED_TREE_REGRESSOR',
    max_iterations=50,
    learn_rate=0.15,  -- Slightly higher for volatile periods
    max_tree_depth=6   -- Simpler to avoid overfitting sparse regime data
) AS
SELECT * EXCEPT(date, target_1w, target_3m, target_6m)
FROM training_dataset_super_enriched
WHERE vix_level > 30  -- Train only on high-VIX periods
AND target_1m IS NOT NULL
```

**Features Emphasized:**
- VIX stress signal (highest weight)
- Geopolitical volatility
- Tariff threat
- Crude-soy correlations (flight to quality)

---

### Specialist 4: Substitution Dynamics Model
**Purpose:** Focus on palm-soy substitution effects

**Trigger:** Large palm-soy price divergence (>10% spread change)

**Features:**
- Palm price lags (1d, 2d, 3d)
- Palm-soy correlation (30d, 90d)
- Palm momentum
- Palm lead correlation
- Biofuel cascade signal
- Hidden correlation signal

**Implementation:**
```sql
CREATE MODEL `cbi-v14.models_v4.specialist_palm_substitution`
OPTIONS(
    model_type='BOOSTED_TREE_REGRESSOR',
    max_iterations=40
) AS
SELECT 
    target_1m,
    palm_price,
    palm_lag1, palm_lag2, palm_lag3,
    palm_momentum_3d,
    corr_zl_palm_30d,
    corr_zl_palm_90d,
    palm_lead2_correlation,
    feature_hidden_correlation,
    feature_biofuel_cascade,
    crude_price,
    corr_palm_crude_30d
FROM training_dataset_super_enriched
WHERE target_1m IS NOT NULL
AND palm_price IS NOT NULL
```

---

## ENSEMBLE ARCHITECTURE

### Layer 1: Baseline Models (Trained)
- 4 boosted tree models (1W, 1M, 3M, 6M)
- **Role:** Primary forecasts, stable predictions

### Layer 2: Specialist Models (Planned)
- LSTM sequence model
- High-VIX regime model
- Palm substitution model
- **Role:** Enhance predictions in specific conditions

### Layer 3: Meta-Learner (Planned)
**Purpose:** Weight and combine baseline + specialists

**Weighting Logic:**
```python
if vix_level > 30:
    weight_high_vix_specialist = 0.4
    weight_baseline = 0.6
elif abs(palm_momentum_3d) > 5:
    weight_palm_specialist = 0.3
    weight_baseline = 0.7
else:
    weight_baseline = 1.0
    
final_forecast = (baseline * weight_baseline + 
                  specialist * weight_specialist)
```

---

## IMPLEMENTATION TIMELINE

### Week 1 (Nov 1-7):
- Train LSTM specialist
- Train high-VIX specialist
- Validate on out-of-sample data

### Week 2 (Nov 8-14):
- Train palm substitution specialist
- Implement meta-learner weighting
- A/B test vs baseline

### Week 3 (Nov 15-21):
- Deploy ensemble to production
- Monitor blended forecasts
- Tune specialist weights

---

## SUCCESS CRITERIA

**Specialist Models:**
- MAPE < baseline (< 2% improvement expected)
- R² > baseline
- No catastrophic failures (no >10% errors)

**Ensemble:**
- Blended MAPE < 1.8% (10% improvement over 2% baseline)
- Improved directional accuracy (>65%)
- Better regime-specific performance

---

## RISK MITIGATION

### Risk: Overfitting on Specialists
**Mitigation:**
- Keep architectures simple (1-2 layers)
- Use dropout (0.3-0.4)
- Train only on regime-specific data
- Validate on held-out set

### Risk: Specialist Divergence
**Mitigation:**
- Cap specialist weight at 40%
- Require specialist agreement for high weights
- Fall back to baseline on extreme predictions

### Risk: Increased Complexity
**Mitigation:**
- Deploy baseline first (working now)
- Add specialists incrementally
- Keep baseline as fallback always

---

**Next Action:** Validate baseline forecasts, then implement specialists.

