-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- CLEAN TRAINING: ALL 4 HORIZONS
-- Identical configurations across all models
-- Uses 200+ features (excludes only 6 entirely NULL columns)
-- ============================================

-- 1-WEEK MODEL
DROP MODEL IF EXISTS `cbi-v14.models_v4.bqml_1w_mean`;

CREATE MODEL `cbi-v14.models_v4.bqml_1w_mean`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1w'],
  num_trials=25,
  MAX_PARALLEL_TRIALS=5,
  learn_rate=HPARAM_RANGE(0.01, 0.3),
  max_tree_depth=HPARAM_CANDIDATES([4, 5, 6, 8]),
  subsample=HPARAM_RANGE(0.7, 1.0),
  l1_reg=HPARAM_RANGE(0, 10),
  l2_reg=HPARAM_RANGE(0, 5),
  num_parallel_tree=HPARAM_CANDIDATES([15, 20, 25]),
  max_iterations=120,
  early_stop=TRUE,
  MIN_REL_PROGRESS=0.005,
  enable_global_explain=TRUE,
  data_split_method='CUSTOM',
  data_split_col='data_split'
) AS
SELECT * EXCEPT(date, treasury_10y_yield, econ_gdp_growth, econ_unemployment_rate, us_midwest_temp_c, us_midwest_precip_mm, news_article_count),
  IF(date < '2024-12-01', 'TRAIN', 'EVAL') AS data_split
FROM `cbi-v14.models_v4.train_1w`
WHERE target_1w IS NOT NULL;

-- 1-MONTH MODEL
DROP MODEL IF EXISTS `cbi-v14.models_v4.bqml_1m_mean`;

CREATE MODEL `cbi-v14.models_v4.bqml_1m_mean`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1m'],
  num_trials=25,
  MAX_PARALLEL_TRIALS=5,
  learn_rate=HPARAM_RANGE(0.01, 0.3),
  max_tree_depth=HPARAM_CANDIDATES([4, 5, 6, 8]),
  subsample=HPARAM_RANGE(0.7, 1.0),
  l1_reg=HPARAM_RANGE(0, 10),
  l2_reg=HPARAM_RANGE(0, 5),
  num_parallel_tree=HPARAM_CANDIDATES([15, 20, 25]),
  max_iterations=120,
  early_stop=TRUE,
  MIN_REL_PROGRESS=0.005,
  enable_global_explain=TRUE,
  data_split_method='CUSTOM',
  data_split_col='data_split'
) AS
SELECT * EXCEPT(date, treasury_10y_yield, econ_gdp_growth, econ_unemployment_rate, us_midwest_temp_c, us_midwest_precip_mm, news_article_count),
  IF(date < '2024-12-01', 'TRAIN', 'EVAL') AS data_split
FROM `cbi-v14.models_v4.train_1m`
WHERE target_1m IS NOT NULL;

-- 3-MONTH MODEL
DROP MODEL IF EXISTS `cbi-v14.models_v4.bqml_3m_mean`;

CREATE MODEL `cbi-v14.models_v4.bqml_3m_mean`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_3m'],
  num_trials=25,
  MAX_PARALLEL_TRIALS=5,
  learn_rate=HPARAM_RANGE(0.01, 0.3),
  max_tree_depth=HPARAM_CANDIDATES([4, 5, 6, 8]),
  subsample=HPARAM_RANGE(0.7, 1.0),
  l1_reg=HPARAM_RANGE(0, 10),
  l2_reg=HPARAM_RANGE(0, 5),
  num_parallel_tree=HPARAM_CANDIDATES([15, 20, 25]),
  max_iterations=120,
  early_stop=TRUE,
  MIN_REL_PROGRESS=0.005,
  enable_global_explain=TRUE,
  data_split_method='CUSTOM',
  data_split_col='data_split'
) AS
SELECT * EXCEPT(date, treasury_10y_yield, econ_gdp_growth, econ_unemployment_rate, us_midwest_temp_c, us_midwest_precip_mm, news_article_count),
  IF(date < '2024-12-01', 'TRAIN', 'EVAL') AS data_split
FROM `cbi-v14.models_v4.train_3m`
WHERE target_3m IS NOT NULL;

-- 6-MONTH MODEL
DROP MODEL IF EXISTS `cbi-v14.models_v4.bqml_6m_mean`;

CREATE MODEL `cbi-v14.models_v4.bqml_6m_mean`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_6m'],
  num_trials=25,
  MAX_PARALLEL_TRIALS=5,
  learn_rate=HPARAM_RANGE(0.01, 0.3),
  max_tree_depth=HPARAM_CANDIDATES([4, 5, 6, 8]),
  subsample=HPARAM_RANGE(0.7, 1.0),
  l1_reg=HPARAM_RANGE(0, 10),
  l2_reg=HPARAM_RANGE(0, 5),
  num_parallel_tree=HPARAM_CANDIDATES([15, 20, 25]),
  max_iterations=120,
  early_stop=TRUE,
  MIN_REL_PROGRESS=0.005,
  enable_global_explain=TRUE,
  data_split_method='CUSTOM',
  data_split_col='data_split'
) AS
SELECT * EXCEPT(date, treasury_10y_yield, econ_gdp_growth, econ_unemployment_rate, us_midwest_temp_c, us_midwest_precip_mm, news_article_count),
  IF(date < '2024-12-01', 'TRAIN', 'EVAL') AS data_split
FROM `cbi-v14.models_v4.train_6m`
WHERE target_6m IS NOT NULL;

SELECT 
  'All 4 models training with identical configurations!' as status,
  CURRENT_TIMESTAMP() as started_at,
  '200+ features per model (206 - 6 entirely NULL)' as feature_count,
  '25 hyperparameter trials × 5 parallel' as tuning,
  'Optimized for speed while maintaining accuracy' as optimization;


