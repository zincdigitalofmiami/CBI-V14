-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--


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
SELECT * EXCEPT(date, treasury_10y_yield, econ_gdp_growth, econ_unemployment_rate, us_midwest_temp_c, us_midwest_precip_mm),
  IF(date < '2024-12-01', 'TRAIN', 'EVAL') AS data_split
FROM `cbi-v14.models_v4.train_1w`
WHERE target_1w IS NOT NULL;
