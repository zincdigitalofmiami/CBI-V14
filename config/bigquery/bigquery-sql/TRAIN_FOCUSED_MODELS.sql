-- ============================================
-- TRAIN FOCUSED MODELS (50-100 Features)
-- Optimized training with selected features
-- Date: November 2025
-- ============================================

-- MODEL 1: Focused 1W Model
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_focused_1w`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1w'],
  max_iterations=150,
  subsample=0.85,
  learn_rate=0.1,
  max_tree_depth=8,
  min_tree_child_weight=10,
  early_stop=TRUE,
  min_rel_progress=0.0005,  -- Stop if improvement < 0.05% (prevents memorization)
  data_split_method='RANDOM',
  data_split_eval_fraction=0.2  -- 20% validation set for overfitting detection
) AS
SELECT 
  * EXCEPT(date, target_1m, target_3m, target_6m, volatility_regime),
  target_1w
FROM `cbi-v14.models_v4.focused_training_data_1w`
WHERE target_1w IS NOT NULL;

-- MODEL 2: Focused 1M Model
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_focused_1m`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1m'],
  max_iterations=150,
  subsample=0.85,
  learn_rate=0.1,
  max_tree_depth=8,
  min_tree_child_weight=10,
  early_stop=TRUE,
  min_rel_progress=0.0001
) AS
SELECT 
  * EXCEPT(date, target_1w, target_3m, target_6m, volatility_regime),
  target_1m
FROM `cbi-v14.models_v4.focused_training_data_1m`
WHERE target_1m IS NOT NULL;

-- MODEL 3: Focused 3M Model
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_focused_3m`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_3m'],
  max_iterations=150,
  subsample=0.85,
  learn_rate=0.1,
  max_tree_depth=8,
  min_tree_child_weight=10,
  early_stop=TRUE,
  min_rel_progress=0.0001
) AS
SELECT 
  * EXCEPT(date, target_1w, target_1m, target_6m, volatility_regime),
  target_3m
FROM `cbi-v14.models_v4.focused_training_data_3m`
WHERE target_3m IS NOT NULL;

-- MODEL 4: Focused 6M Model
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_focused_6m`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_6m'],
  max_iterations=150,
  subsample=0.85,
  learn_rate=0.1,
  max_tree_depth=8,
  min_tree_child_weight=10,
  early_stop=TRUE,
  min_rel_progress=0.0001
) AS
SELECT 
  * EXCEPT(date, target_1w, target_1m, target_3m, volatility_regime),
  target_6m
FROM `cbi-v14.models_v4.focused_training_data_6m`
WHERE target_6m IS NOT NULL;

-- ============================================
-- EVALUATE FOCUSED MODELS
-- ============================================
CREATE OR REPLACE TABLE `cbi-v14.models_v4.focused_model_evaluation` AS
WITH eval_1w AS (
  SELECT 
    'focused_1w' as model_name,
    mean_absolute_error,
    mean_squared_error,
    SQRT(mean_squared_error) as rmse,
    r2_score,
    mean_absolute_percentage_error
  FROM ML.EVALUATE(
    MODEL `cbi-v14.models_v4.bqml_focused_1w`,
    (SELECT * FROM `cbi-v14.models_v4.focused_training_data_1w`
     WHERE date >= '2024-01-01' AND target_1w IS NOT NULL)
  )
),
eval_1m AS (
  SELECT 
    'focused_1m' as model_name,
    mean_absolute_error,
    mean_squared_error,
    SQRT(mean_squared_error) as rmse,
    r2_score,
    mean_absolute_percentage_error
  FROM ML.EVALUATE(
    MODEL `cbi-v14.models_v4.bqml_focused_1m`,
    (SELECT * FROM `cbi-v14.models_v4.focused_training_data_1m`
     WHERE date >= '2024-01-01' AND target_1m IS NOT NULL)
  )
),
eval_3m AS (
  SELECT 
    'focused_3m' as model_name,
    mean_absolute_error,
    mean_squared_error,
    SQRT(mean_squared_error) as rmse,
    r2_score,
    mean_absolute_percentage_error
  FROM ML.EVALUATE(
    MODEL `cbi-v14.models_v4.bqml_focused_3m`,
    (SELECT * FROM `cbi-v14.models_v4.focused_training_data_3m`
     WHERE date >= '2024-01-01' AND target_3m IS NOT NULL)
  )
),
eval_6m AS (
  SELECT 
    'focused_6m' as model_name,
    mean_absolute_error,
    mean_squared_error,
    SQRT(mean_squared_error) as rmse,
    r2_score,
    mean_absolute_percentage_error
  FROM ML.EVALUATE(
    MODEL `cbi-v14.models_v4.bqml_focused_6m`,
    (SELECT * FROM `cbi-v14.models_v4.focused_training_data_6m`
     WHERE date >= '2024-01-01' AND target_6m IS NOT NULL)
  )
),
-- Compare with original models
original_1w AS (
  SELECT 
    'original_1w' as model_name,
    mean_absolute_error,
    mean_squared_error,
    SQRT(mean_squared_error) as rmse,
    r2_score,
    mean_absolute_percentage_error
  FROM ML.EVALUATE(
    MODEL `cbi-v14.models_v4.bqml_1w`,
    (SELECT * FROM `cbi-v14.training.zl_training_prod_allhistory_1w`
     WHERE date >= '2024-01-01' AND target_1w IS NOT NULL)
  )
),
original_1m AS (
  SELECT 
    'original_1m' as model_name,
    mean_absolute_error,
    mean_squared_error,
    SQRT(mean_squared_error) as rmse,
    r2_score,
    mean_absolute_percentage_error
  FROM ML.EVALUATE(
    MODEL `cbi-v14.models_v4.bqml_1m`,
    (SELECT * FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
     WHERE date >= '2024-01-01' AND target_1m IS NOT NULL)
  )
),
original_3m AS (
  SELECT 
    'original_3m' as model_name,
    mean_absolute_error,
    mean_squared_error,
    SQRT(mean_squared_error) as rmse,
    r2_score,
    mean_absolute_percentage_error
  FROM ML.EVALUATE(
    MODEL `cbi-v14.models_v4.bqml_3m`,
    (SELECT * FROM `cbi-v14.training.zl_training_prod_allhistory_3m`
     WHERE date >= '2024-01-01' AND target_3m IS NOT NULL)
  )
),
original_6m AS (
  SELECT 
    'original_6m' as model_name,
    mean_absolute_error,
    mean_squared_error,
    SQRT(mean_squared_error) as rmse,
    r2_score,
    mean_absolute_percentage_error
  FROM ML.EVALUATE(
    MODEL `cbi-v14.models_v4.bqml_6m`,
    (SELECT * FROM `cbi-v14.training.zl_training_prod_allhistory_6m`
     WHERE date >= '2024-01-01' AND target_6m IS NOT NULL)
  )
)
SELECT * FROM eval_1w
UNION ALL SELECT * FROM eval_1m
UNION ALL SELECT * FROM eval_3m
UNION ALL SELECT * FROM eval_6m
UNION ALL SELECT * FROM original_1w
UNION ALL SELECT * FROM original_1m
UNION ALL SELECT * FROM original_3m
UNION ALL SELECT * FROM original_6m
ORDER BY model_name;

-- Display results
SELECT 
  model_name,
  ROUND(mean_absolute_error, 4) as mae,
  ROUND(rmse, 4) as rmse,
  ROUND(r2_score, 4) as r2,
  ROUND(mean_absolute_percentage_error * 100, 2) as mape_pct,
  CASE 
    WHEN model_name LIKE 'focused%' THEN '✅ FOCUSED'
    ELSE '📊 ORIGINAL'
  END as model_type
FROM `cbi-v14.models_v4.focused_model_evaluation`
ORDER BY model_name;

