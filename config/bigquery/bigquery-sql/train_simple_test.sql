-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- TEST: Simple training with just core features
DROP MODEL IF EXISTS `cbi-v14.models_v4.test_simple`;

CREATE MODEL `cbi-v14.models_v4.test_simple`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1w'],
  num_trials=5,
  max_iterations=50,
  enable_global_explain=TRUE,
  data_split_method='CUSTOM',
  data_split_col='data_split'
) AS
SELECT
  -- Just core features to test if training works
  zl_price_current,
  zl_volume,
  feature_vix_stress,
  target_1w,
  IF(date < '2024-12-01', 'TRAIN', 'EVAL') AS data_split
FROM `cbi-v14.models_v4.train_1w`
WHERE target_1w IS NOT NULL
LIMIT 1000;  -- Small sample for quick test

SELECT 'Simple test training completed!' as status;


