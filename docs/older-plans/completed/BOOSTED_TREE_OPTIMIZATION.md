# BOOSTED_TREE Optimization for 1W Model

**Date:** 2025-11-02  
**Decision:** Optimize BOOSTED_TREE to use more features (currently only using 57/188)

## Why BOOSTED_TREE is the Right Choice

Based on commodity forecasting research and soybean futures characteristics:

✅ **Captures Non-linearity**: Soybean prices have complex, non-linear relationships with weather, economics, supply/demand, sentiment  
✅ **Superior Accuracy**: Research shows boosted trees achieve significantly lower MAPE vs linear models  
✅ **Handles Diverse Data**: Effectively integrates price data, FX, sentiment, news, Fed data  
✅ **Robustness**: Ensemble methods are more robust to noise and less prone to overfitting  
✅ **Cost Effective**: $5/TB vs $250/TB for linear regression

## Current Problem

- Model only uses **57 out of 188 features** (70% excluded)
- Missing 131 potentially useful features
- Performance: **8% MAPE** (poor)

## Optimization Strategy

Modified hyperparameters to encourage using MORE features:

### Previous Configuration:
- `num_parallel_tree=10`
- `max_iterations=100`
- `learn_rate=0.05`
- `subsample=0.8`
- `max_tree_depth=8`
- `l2_reg=0.1` (high regularization = more feature dropping)

### New Configuration (Optimized):
- `num_parallel_tree=20` ⬆️ **Doubled** - More trees = more feature opportunities
- `max_iterations=200` ⬆️ **Doubled** - More iterations to discover useful features
- `learn_rate=0.03` ⬇️ **Lower** - More careful feature selection over time
- `subsample=0.9` ⬆️ **Higher** - More data per iteration (90% vs 80%)
- `max_tree_depth=10` ⬆️ **Deeper** - Can access more features in each tree
- `l2_reg=0.01` ⬇️ **Much lower** - Less aggressive regularization = less feature dropping

## Expected Impact

With these changes:
1. **More features should be utilized** (target: 100-150 features vs current 57)
2. **Better capture of non-linear relationships** with deeper trees
3. **More careful learning** with lower learning rate
4. **Less aggressive feature exclusion** with lower L2 regularization

## Trade-offs

⚠️ **Note**: BOOSTED_TREE will still perform automatic feature selection - it cannot be forced to use ALL 188 features like LINEAR_REGRESSOR can. However, these optimizations should make it use significantly more features while maintaining the advantages of boosted trees for commodity forecasting.

## Next Steps

1. ✅ Training SQL updated: `bigquery_sql/train_bqml_1w_mean.sql`
2. ⏳ Ready to train model with optimized hyperparameters
3. 📊 After training, verify:
   - How many features are actually used
   - Performance metrics (MAPE, R²)
   - Compare to baseline (57 features, 8% MAPE)

## Cost

- **BOOSTED_TREE**: $5/TB (cheaper)
- With ~1,251 rows × 206 columns ≈ very small dataset
- Estimated cost: < $0.01 per training run


