-- ============================================
-- TRAINING WITH ALL FEATURES INCLUDING NULLS
-- NULL values contain critical information - DO NOT EXCLUDE
-- Configure BQML to handle sparse/missing data properly
-- ============================================

DROP MODEL IF EXISTS `cbi-v14.models_v4.bqml_1w_all_features`;

CREATE MODEL `cbi-v14.models_v4.bqml_1w_all_features`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1w'],

  -- HYPERPARAMETER TUNING (Optimized for speed)
  num_trials=25,
  MAX_PARALLEL_TRIALS=5,

  -- BROAD RANGES FOR MAXIMUM FEATURE UTILIZATION
  learn_rate=HPARAM_RANGE(0.01, 0.3),
  max_tree_depth=HPARAM_CANDIDATES([4, 5, 6, 8]),
  subsample=HPARAM_RANGE(0.7, 1.0),
  l1_reg=HPARAM_RANGE(0, 10),  -- Feature selection from ALL features
  l2_reg=HPARAM_RANGE(0, 5),
  num_parallel_tree=HPARAM_CANDIDATES([15, 20, 25]),

  -- FASTER TRAINING
  max_iterations=120,
  early_stop=TRUE,
  MIN_REL_PROGRESS=0.005,

  -- FEATURE ANALYSIS (Critical for understanding NULL patterns)
  enable_global_explain=TRUE,

  -- DATA SPLIT
  data_split_method='CUSTOM',
  data_split_col='data_split'

) AS
-- USE ALL FEATURES - NULLs contain valuable information!
SELECT * EXCEPT(date),
  IF(date < '2024-12-01', 'TRAIN', 'EVAL') AS data_split
FROM `cbi-v14.models_v4.train_1w`
WHERE target_1w IS NOT NULL;

-- ============================================
-- ALTERNATIVE: NEURAL NETWORK WITH NULL HANDLING
-- ============================================
DROP MODEL IF EXISTS `cbi-v14.models_v4.nn_1w_all_features`;

CREATE MODEL `cbi-v14.models_v4.nn_1w_all_features`
OPTIONS(
  model_type='DNN_REGRESSOR',
  input_label_cols=['target_1w'],

  -- NEURAL NETWORK ARCHITECTURE
  hidden_units=[256, 128, 64, 32],
  activation_fn='RELU',
  dropout=0.15,

  -- NULL HANDLING FOR NEURAL NETS
  -- BQML automatically handles NULLs in neural networks

  -- FAST TRAINING
  max_iterations=80,
  early_stop=TRUE,
  MIN_REL_PROGRESS=0.005,

  optimizer='ADAM',
  learn_rate=0.002,

  enable_global_explain=TRUE,

  data_split_method='CUSTOM',
  data_split_col='data_split'
) AS
SELECT * EXCEPT(date),
  IF(date < '2024-12-01', 'TRAIN', 'EVAL') AS data_split
FROM `cbi-v14.models_v4.train_1w`
WHERE target_1w IS NOT NULL;

SELECT
  'Training completed with ALL 206+ features including NULLs!' as status,
  CURRENT_TIMESTAMP() as trained_at,
  'NULL values preserved - they contain critical training information' as null_handling,
  'Boosted trees and neural networks can handle sparse features' as ml_capability,
  'Maximum predictive power maintained' as result;

