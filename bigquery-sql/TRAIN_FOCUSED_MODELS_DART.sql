-- ============================================
-- TRAIN FOCUSED MODELS WITH DART (Alternative Approach)
-- Uses DART booster for better regularization with 50-100 features
-- Date: November 2025
-- ============================================

-- MODEL 1: Focused 1W Model (DART)
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_focused_dart_1w`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1w'],
  booster_type='DART',  -- Dropout for regularization
  dart_normalized_type='FOREST',
  max_iterations=200,
  learn_rate=0.05,  -- Slower learning with DART
  early_stop=TRUE,
  min_rel_progress=0.0005,  -- Stop if improvement < 0.05%
  l1_reg=2.0,  -- L1 regularization (feature selection)
  l2_reg=1.0,  -- L2 regularization (prevent overfitting)
  subsample=0.7,
  colsample_bytree=0.5,  -- Each tree sees 50% of features (50-100 features)
  max_tree_depth=10,
  min_tree_child_weight=10,
  data_split_method='RANDOM',
  data_split_eval_fraction=0.2  -- 20% validation set
) AS
SELECT 
  * EXCEPT(date, target_1m, target_3m, target_6m, volatility_regime),
  target_1w
FROM `cbi-v14.models_v4.focused_training_data_1w`
WHERE target_1w IS NOT NULL;

-- MODEL 2: Focused 1M Model (DART)
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_focused_dart_1m`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1m'],
  booster_type='DART',
  dart_normalized_type='FOREST',
  max_iterations=200,
  learn_rate=0.05,
  early_stop=TRUE,
  min_rel_progress=0.0005,
  l1_reg=2.0,
  l2_reg=1.0,
  subsample=0.7,
  colsample_bytree=0.5,
  max_tree_depth=10,
  min_tree_child_weight=10,
  data_split_method='RANDOM',
  data_split_eval_fraction=0.2
) AS
SELECT 
  * EXCEPT(date, target_1w, target_3m, target_6m, volatility_regime),
  target_1m
FROM `cbi-v14.models_v4.focused_training_data_1m`
WHERE target_1m IS NOT NULL;

-- MODEL 3: Focused 3M Model (DART)
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_focused_dart_3m`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_3m'],
  booster_type='DART',
  dart_normalized_type='FOREST',
  max_iterations=200,
  learn_rate=0.05,
  early_stop=TRUE,
  min_rel_progress=0.0005,
  l1_reg=2.0,
  l2_reg=1.0,
  subsample=0.7,
  colsample_bytree=0.5,
  max_tree_depth=10,
  min_tree_child_weight=10,
  data_split_method='RANDOM',
  data_split_eval_fraction=0.2
) AS
SELECT 
  * EXCEPT(date, target_1w, target_1m, target_6m, volatility_regime),
  target_3m
FROM `cbi-v14.models_v4.focused_training_data_3m`
WHERE target_3m IS NOT NULL;

-- MODEL 4: Focused 6M Model (DART)
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_focused_dart_6m`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_6m'],
  booster_type='DART',
  dart_normalized_type='FOREST',
  max_iterations=200,
  learn_rate=0.05,
  early_stop=TRUE,
  min_rel_progress=0.0005,
  l1_reg=2.0,
  l2_reg=1.0,
  subsample=0.7,
  colsample_bytree=0.5,
  max_tree_depth=10,
  min_tree_child_weight=10,
  data_split_method='RANDOM',
  data_split_eval_fraction=0.2
) AS
SELECT 
  * EXCEPT(date, target_1w, target_1m, target_3m, volatility_regime),
  target_6m
FROM `cbi-v14.models_v4.focused_training_data_6m`
WHERE target_6m IS NOT NULL;

-- Compare DART vs Standard Focused Models
SELECT 
  '✅ DART MODELS TRAINED' as status,
  'Compare bqml_focused_dart_* vs bqml_focused_* for best performance' as next_step;






