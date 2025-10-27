# MODEL RETRAINING STATUS
**Date:** October 22, 2025  
**Time:** 16:22 UTC

## 🚀 RETRAINING IN PROGRESS

### Training Dataset Enhancement:
- **Original:** 159 features
- **Enhanced:** 172 features (+13 critical features)

### New Features Added:
- ✓ CFTC positioning data (commercial vs managed money)
- ✓ Treasury yields
- ✓ Economic indicators (GDP, inflation, unemployment)
- ✓ News intelligence scores

## 📊 MODELS BEING TRAINED

### Currently Training (10 models):
1. **Boosted Trees (4 models)** - Expected MAE < 1.0
   - zl_boosted_tree_1w_production_v2
   - zl_boosted_tree_1m_production_v2
   - zl_boosted_tree_3m_production_v2
   - zl_boosted_tree_6m_production_v2

2. **Deep Neural Networks (4 models)** - With proper normalization
   - zl_dnn_1w_production_v2
   - zl_dnn_1m_production_v2
   - zl_dnn_3m_production_v2 (not submitted yet)
   - zl_dnn_6m_production_v2 (not submitted yet)

3. **Linear Models (2 models)** - Baselines
   - zl_linear_production_1w_v2
   - zl_linear_production_1m_v2

### Completed (2 models):
- ✓ zl_arima_production_1w_v2
- ✓ zl_arima_production_1m_v2

## ⏱️ EXPECTED TRAINING TIMES

- **Boosted Trees:** 5-10 minutes
- **DNN:** 5-15 minutes  
- **Linear:** 1-2 minutes
- **ARIMA:** ✓ Already complete

**Total Expected Time:** 15-20 minutes from start

## 🎯 EXPECTED IMPROVEMENTS

With the addition of CFTC positioning, treasury yields, and economic indicators:

### Previous Performance (v1):
- Boosted Trees: MAE 1.19-1.58
- DNN: MAE ~3.0
- Linear: MAE 14-17

### Expected Performance (v2):
- **Boosted Trees: MAE < 1.0** 🌟
- DNN: MAE < 2.0
- Linear: MAE 10-12

The CFTC positioning data is particularly valuable for identifying turning points when commercial vs speculative positioning reaches extremes.

## 📈 KEY FEATURES DRIVING IMPROVEMENT

1. **CFTC Positioning** - Extremes signal reversals
2. **Treasury Yields** - Interest rate environment affects commodity financing
3. **Economic Indicators** - GDP/inflation drives demand
4. **News Intelligence** - Sentiment leads price moves
5. **Cross-asset correlations** - Substitution effects (palm oil)
6. **VIX regimes** - Volatility clustering

## ✅ TO MONITOR PROGRESS

Run this command to check training status:
```bash
python3 scripts/monitor_training.py
```

## 🔍 TO EVALUATE MODELS (After Training)

```sql
-- Check Boosted Tree performance
SELECT * FROM ML.EVALUATE(MODEL `cbi-v14.models.zl_boosted_tree_1w_production_v2`)

-- Compare to old version
SELECT 
    'v1' as version,
    mean_absolute_error as MAE,
    r2_score as R2
FROM ML.EVALUATE(MODEL `cbi-v14.models.zl_boosted_tree_1w_production`)
UNION ALL
SELECT 
    'v2' as version,
    mean_absolute_error as MAE,
    r2_score as R2
FROM ML.EVALUATE(MODEL `cbi-v14.models.zl_boosted_tree_1w_production_v2`)
```

---

**Status:** Models training with complete 172-feature dataset. Check back in 10-15 minutes for results.
