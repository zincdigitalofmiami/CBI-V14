---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Regime Weights: Research & Rationale

**Date**: November 14, 2025  
**Purpose**: Document the research-based approach to regime weighting in training

---

## Research Summary

Based on machine learning research and best practices, optimal regime weighting follows these principles:

### 1. Recency Bias
**Principle**: More recent data is more representative of current market dynamics.

**Application**: Trump era (2023-2025) gets **100x** the weight of historical pre-2000 data.

**Citation**: Importance weighting and multiplicative weight update methods show that recent observations should dominate gradient updates in non-stationary environments.

### 2. Importance Weighting
**Principle**: Critical learning periods (crises, policy shifts) deserve higher weights regardless of recency.

**Application**: 
- Crisis periods (2008, 2020) get elevated weights for volatility learning
- Trade war era (2017-2019) gets high weight due to policy similarity to current regime

**Citation**: Metric-optimized example weights (ArXiv 1805.10582) demonstrate that weighting examples by relevance to test distribution improves generalization.

### 3. Sample Compensation
**Principle**: Smaller but more relevant regimes need higher per-sample weights to prevent being drowned out.

**Application**: Trump era has ~500-800 rows but gets weight 5000, giving it ~50% effective influence despite <5% of total rows.

**Citation**: Class imbalance techniques (SMOTE, inverse probability weighting) show that multiplicative factors can effectively balance uneven distributions.

### 4. Multiplicative Scale
**Principle**: Weights must be large enough to meaningfully affect gradient-based optimization.

**Application**: Scale 50-5000 (100x range) provides strong differentiation in loss functions.

**Citation**: Gradient-based optimization requires sufficient weight differences to impact convergence. Decimal scales (0.5-1.5) provide minimal differentiation.

---

## Final Regime Weights

| Regime | Weight | Rows (est) | Effective Weight | Rationale |
|--------|--------|------------|------------------|-----------|
| trump_2023_2025 | **5000** | ~600 | ~3,000,000 | Current regime - MAXIMUM recency + policy relevance |
| structural_events | **2000** | varies | varies | Extreme events - critical for tail risk learning |
| tradewar_2017_2019 | **1500** | ~750 | ~1,125,000 | High policy similarity to current environment |
| inflation_2021_2023 | **1200** | ~500 | ~600,000 | Recent macro dynamics |
| covid_2020_2021 | **800** | ~250 | ~200,000 | Supply chain disruption patterns |
| financial_crisis_2008_2009 | **500** | ~250 | ~125,000 | Volatility spike learning |
| commodity_crash_2014_2016 | **400** | ~600 | ~240,000 | Crash dynamics |
| qe_supercycle_2010_2014 | **300** | ~1,000 | ~300,000 | Commodity boom (less relevant) |
| precrisis_2000_2007 | **100** | ~1,750 | ~175,000 | Baseline patterns |
| historical_pre2000 | **50** | ~5,000 | ~250,000 | Pattern learning only |
| allhistory | **1000** | all | baseline | Default/fallback weight |

**Total Estimated Rows**: ~10,700  
**Effective Trump Influence**: ~40-50% despite ~6% of rows

---

## Weight Distribution Analysis

### By Era (chronological):
- Historical (pre-2000): 50 (oldest, least relevant)
- Pre-crisis (2000-2007): 100 (baseline patterns)
- QE/Commodity cycles (2010-2016): 300-400 (moderate)
- Modern era (2017-2023): 800-1500 (high relevance)
- Current regime (2023-2025): 5000 (maximum)

### By Purpose:
- **Recency**: Trump era gets 100x pre-2000 (5000 vs 50)
- **Volatility Learning**: Crises get 10x+ baseline (500-800)
- **Policy Learning**: Trade war era gets 15x baseline (1500)
- **Current Macro**: Inflation era gets 12x baseline (1200)

### Gradient Impact:
With these weights in loss functions:
- Trump era sample: loss × 5000 → dominates gradient updates
- Historical sample: loss × 50 → minimal gradient contribution
- Net effect: Model optimizes primarily for recent behavior while still learning patterns from history

---

## Implementation

### SQL Table: `training.regime_weights`
```sql
CREATE OR REPLACE TABLE `cbi-v14.training.regime_weights` AS
SELECT regime, weight, start_date, end_date, description
FROM UNNEST([
  STRUCT('trump_2023_2025' AS regime, 5000 AS weight, ...),
  STRUCT('tradewar_2017_2019' AS regime, 1500 AS weight, ...),
  ...
]);
```

### Usage in Training:
```python
# In model training
sample_weights = df['regime'].map(regime_weight_dict)
model.fit(X, y, sample_weight=sample_weights)

# Or in loss function
loss = mse_loss(y_pred, y_true) * sample_weights
```

---

## Validation Strategy

Monitor performance by regime:
1. **Holdout by regime**: Test on Trump-era holdout (most critical)
2. **Cross-regime validation**: Ensure crisis patterns transfer
3. **Temporal splits**: Walk-forward validation with regime awareness
4. **MAPE decomposition**: Track error by regime to detect overfitting

If Trump-era MAPE degrades, increase weight further (5000 → 7500).  
If historical patterns lost, slightly increase old weights (50 → 75).

---

## References

1. **Multiplicative Weight Update**: Wikipedia - Standard algorithm for online learning with expert weights
2. **Importance Weighting**: ArXiv 1805.10582 - Metric-optimized example weights
3. **Recency Bias**: Standard practice in time-series forecasting (exponential decay, window-based)
4. **Class Imbalance**: SMOTE, inverse probability weighting for unbalanced data
5. **Regime-Based Learning**: Financial ML literature on structural breaks and regime shifts

---

## Conclusion

The 50-5000 scale provides:
- ✅ Strong recency bias (100x differential)
- ✅ Importance weighting for critical periods
- ✅ Sample compensation for small but relevant regimes
- ✅ Meaningful gradient impact in optimization
- ✅ Flexibility for validation-based tuning

This approach is grounded in ML research and optimized for the non-stationary, policy-driven nature of commodity forecasting.

