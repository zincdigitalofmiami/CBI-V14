# Automated Hyperparameter Tuning Setup

**Date:** 2025-11-02  
**Model:** `bqml_1w_mean`  
**Approach:** BQML Automated Hyperparameter Tuning for Maximum Accuracy

## Changes Made

Replaced fixed hyperparameters with **automated hyperparameter tuning** using `NUM_TRIALS` and `HPARAM_RANGE`/`HPARAM_CANDIDATES`.

## Configuration

### Automated Tuning Enabled:
- **NUM_TRIALS: 30** - BQML will test 30 different hyperparameter combinations
- **Early Stop: TRUE** - Stops training if validation performance doesn't improve
- **Custom Data Split** - Uses `is_training` column (date < '2025-09-01')

### Hyperparameter Ranges:

| Parameter | Type | Values/Range | Purpose |
|-----------|------|--------------|---------|
| `learn_rate` | HPARAM_RANGE | 0.01 to 0.2 | Controls tree contribution |
| `max_tree_depth` | HPARAM_CANDIDATES | [3, 5, 7, 10, 12] | Tree complexity (deeper = more features) |
| `subsample` | HPARAM_RANGE | 0.7 to 1.0 | Fraction of data per tree |
| `l1_reg` | HPARAM_RANGE | 0 to 1 | L1 regularization |
| `l2_reg` | HPARAM_RANGE | 0 to 1 | L2 regularization (lower = less feature dropping) |
| `num_parallel_tree` | HPARAM_CANDIDATES | [10, 15, 20] | Ensemble size |

### Fixed Parameters:
- `max_iterations: 200` - Maximum iterations per trial
- `enable_global_explain: TRUE` - Feature importance for analysis
- `data_split_method: 'CUSTOM'` - Manual train/val split
- `data_split_col: 'is_training'` - Date-based split

## Expected Benefits

1. **Maximum Accuracy**: Automated tuning finds optimal hyperparameter combination for your specific dataset
2. **Feature Utilization**: Lower L2 regularization values in range should encourage using more features
3. **Non-linear Capture**: Deeper tree depths (up to 12) can capture more complex patterns
4. **Optimal Regularization**: Balance between overfitting (low reg) and generalization (high reg)
5. **Best Ensemble Size**: Tests different tree counts to find optimal ensemble

## Training Process

1. BQML will run 30 trials
2. Each trial tests a different combination of hyperparameters
3. Validates on custom split (data >= '2025-09-01')
4. Selects best performing configuration
5. Returns model with optimal hyperparameters

## Cost & Time

- **Cost**: Still $5/TB (BOOSTED_TREE pricing)
- **Time**: Will take longer (~30x normal training time) but ensures maximum accuracy
- **Worth it**: Automated tuning is the most reliable way to achieve optimal performance

## Expected Outcomes

### Feature Usage:
- Current: 57 features
- Target: 100-150 features (with lower L2 regularization values)
- Automated tuning will find the best balance

### Performance:
- Current: 8% MAPE
- Target: < 3% MAPE (based on research showing boosted trees outperform linear models)

## Monitoring

After training, check:
1. How many features are actually used (via ML.GLOBAL_EXPLAIN)
2. Final hyperparameter values selected (via ML.TRAINING_INFO)
3. Performance metrics (MAPE, R², MAE)
4. Compare to baseline (57 features, 8% MAPE)

## File Updated

- `bigquery_sql/train_bqml_1w_mean.sql` - Now uses automated hyperparameter tuning


