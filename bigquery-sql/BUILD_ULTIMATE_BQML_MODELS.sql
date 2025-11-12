-- ============================================
-- BUILD ULTIMATE BQML PREDICTION MODELS
-- Based on ACTUAL data correlations from Vertex AI
-- Date: November 6, 2025
-- ============================================

-- FIRST: Ensure data is current
-- Run ULTIMATE_DATA_CONSOLIDATION.sql before this!

-- ============================================
-- MODEL 1: THE CRUSH KING (Top 20 High-Impact Features)
-- Correlation-driven feature selection
-- ============================================
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_ultimate_crush_1w`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1w'],
  max_iterations=150,
  subsample=0.85,
  learn_rate=0.1,
  max_tree_depth=8,
  min_tree_child_weight=10,
  booster_type='GBTREE',
  early_stop=TRUE,
  min_rel_progress=0.0001
) AS
SELECT 
  -- #1 DRIVER: CRUSH MARGIN (0.961 correlation!)
  COALESCE(crush_margin, 0) as crush_margin,
  COALESCE(crush_margin_30d_ma, 0) as crush_margin_30d_ma,
  COALESCE(crush_margin_7d_ma, 0) as crush_margin_7d_ma,
  
  -- #2 DRIVER: CHINA IMPORTS (-0.813!)
  COALESCE(china_soybean_imports_mt, 0) as china_soybean_imports_mt,
  COALESCE(china_imports_from_us_mt, 0) as china_imports_from_us_mt,
  COALESCE(china_weekly_cancellations_mt, 0) as china_weekly_cancellations_mt,
  
  -- #3 DRIVER: DOLLAR INDEX (-0.658)
  COALESCE(dollar_index, 0) as dollar_index,
  COALESCE(usd_cny_rate, 0) as usd_cny_rate,
  COALESCE(usd_brl_rate, 0) as usd_brl_rate,
  COALESCE(dollar_index_7d_change, 0) as dollar_index_7d_change,
  
  -- #4 DRIVER: FED POLICY (-0.656)
  COALESCE(fed_funds_rate, 0) as fed_funds_rate,
  COALESCE(real_yield, 0) as real_yield,
  COALESCE(treasury_10y_yield, 0) as treasury_10y_yield,
  COALESCE(yield_curve, 0) as yield_curve,
  
  -- #5 DRIVER: TRADE WAR/TARIFFS (0.647)
  COALESCE(trade_war_intensity, 0) as trade_war_intensity,
  COALESCE(feature_tariff_threat, 0) as feature_tariff_threat,
  COALESCE(china_tariff_rate, 0) as china_tariff_rate,
  COALESCE(trump_policy_events, 0) as trump_policy_events,
  
  -- #6 DRIVER: BIOFUELS (-0.601)
  COALESCE(feature_biofuel_cascade, 0) as feature_biofuel_cascade,
  COALESCE(feature_biofuel_ethanol, 0) as feature_biofuel_ethanol,
  
  -- #7 DRIVER: CRUDE OIL (0.584)
  COALESCE(crude_price, 0) as crude_price,
  COALESCE(wti_7d_change, 0) as wti_7d_change,
  
  -- Price mechanics (essential)
  zl_price_current,
  COALESCE(zl_price_lag1, zl_price_current) as zl_price_lag1,
  COALESCE(zl_price_lag7, zl_price_current) as zl_price_lag7,
  COALESCE(return_1d, 0) as return_1d,
  COALESCE(return_7d, 0) as return_7d,
  COALESCE(ma_7d, zl_price_current) as ma_7d,
  COALESCE(ma_30d, zl_price_current) as ma_30d,
  
  -- Target
  target_1w
FROM `cbi-v14.models_v4.production_training_data_1w`
WHERE target_1w IS NOT NULL
  AND date >= '2023-01-01'  -- Focus on recent market regime
  AND zl_price_current > 0;

-- ============================================
-- MODEL 2: BIG 8 SIGNALS FOCUSED
-- Leveraging your existing Big 8 infrastructure
-- ============================================
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_ultimate_big8_1w`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1w'],
  max_iterations=150,
  subsample=0.85,
  learn_rate=0.1,
  max_tree_depth=8
) AS
SELECT 
  -- Big 8 Signals
  feature_vix_stress,
  feature_harvest_pace,
  feature_china_relations,
  feature_tariff_threat,
  feature_geopolitical_volatility,
  feature_biofuel_cascade,
  feature_hidden_correlation,
  feature_biofuel_ethanol,
  big8_composite_score,
  
  -- Add the REAL heavy hitters
  COALESCE(crush_margin, 0) as crush_margin,
  COALESCE(china_soybean_imports_mt, 0) as china_soybean_imports_mt,
  COALESCE(dollar_index, 0) as dollar_index,
  COALESCE(fed_funds_rate, 0) as fed_funds_rate,
  
  -- Price context
  zl_price_current,
  COALESCE(zl_price_lag1, zl_price_current) as zl_price_lag1,
  COALESCE(ma_30d, zl_price_current) as ma_30d,
  
  target_1w
FROM `cbi-v14.models_v4.production_training_data_1w`
WHERE target_1w IS NOT NULL
  AND date >= '2023-01-01'
  AND big8_composite_score IS NOT NULL;

-- ============================================
-- MODEL 3: FULL KITCHEN SINK (All 300 Features)
-- For comparison and catching subtle patterns
-- ============================================
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_ultimate_full_1w`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1w'],
  max_iterations=100,  -- Lower iterations for 300 features
  subsample=0.7,
  learn_rate=0.05,     -- Slower learning for complexity
  max_tree_depth=6,
  early_stop=TRUE
) AS
SELECT 
  * EXCEPT(date, target_1m, target_3m, target_6m),
  target_1w
FROM `cbi-v14.models_v4.production_training_data_1w`
WHERE target_1w IS NOT NULL
  AND date >= '2022-01-01'  -- More data for complex model
  AND zl_price_current > 0;

-- ============================================
-- MODEL EVALUATION & COMPARISON
-- ============================================
CREATE OR REPLACE TABLE `cbi-v14.models_v4.ultimate_model_comparison` AS
WITH evaluation_data AS (
  SELECT * FROM `cbi-v14.models_v4.production_training_data_1w`
  WHERE date >= '2024-06-01'  -- Recent 5 months for evaluation
    AND target_1w IS NOT NULL
),
crush_eval AS (
  SELECT 
    'Crush King (Top 20)' as model_name,
    mean_absolute_error,
    mean_squared_error,
    r2_score
  FROM ML.EVALUATE(MODEL `cbi-v14.models_v4.bqml_ultimate_crush_1w`,
    (SELECT * FROM evaluation_data))
),
big8_eval AS (
  SELECT 
    'Big 8 Focused' as model_name,
    mean_absolute_error,
    mean_squared_error,
    r2_score
  FROM ML.EVALUATE(MODEL `cbi-v14.models_v4.bqml_ultimate_big8_1w`,
    (SELECT * FROM evaluation_data))
),
full_eval AS (
  SELECT 
    'Kitchen Sink (300)' as model_name,
    mean_absolute_error,
    mean_squared_error,
    r2_score
  FROM ML.EVALUATE(MODEL `cbi-v14.models_v4.bqml_ultimate_full_1w`,
    (SELECT * FROM evaluation_data))
),
original_eval AS (
  SELECT 
    'Original bqml_1w' as model_name,
    mean_absolute_error,
    mean_squared_error,
    r2_score
  FROM ML.EVALUATE(MODEL `cbi-v14.models_v4.bqml_1w`,
    (SELECT * FROM evaluation_data))
)
SELECT * FROM crush_eval
UNION ALL
SELECT * FROM big8_eval
UNION ALL
SELECT * FROM full_eval
UNION ALL
SELECT * FROM original_eval
ORDER BY mean_absolute_error;

-- ============================================
-- CREATE ENSEMBLE PREDICTIONS
-- ============================================
CREATE OR REPLACE VIEW `cbi-v14.models_v4.vw_ultimate_ensemble_1w` AS
WITH base_data AS (
  SELECT * FROM `cbi-v14.models_v4.predict_frame_209`
  WHERE date = (SELECT MAX(date) FROM `cbi-v14.models_v4.predict_frame_209`)
),
predictions AS (
  SELECT
    date,
    zl_price_current,
    
    -- Get predictions from each model
    (SELECT predicted_target_1w FROM ML.PREDICT(
      MODEL `cbi-v14.models_v4.bqml_ultimate_crush_1w`,
      (SELECT * FROM base_data))) as crush_prediction,
      
    (SELECT predicted_target_1w FROM ML.PREDICT(
      MODEL `cbi-v14.models_v4.bqml_ultimate_big8_1w`,
      (SELECT * FROM base_data))) as big8_prediction,
      
    (SELECT predicted_target_1w FROM ML.PREDICT(
      MODEL `cbi-v14.models_v4.bqml_ultimate_full_1w`,
      (SELECT * FROM base_data))) as full_prediction,
      
    (SELECT predicted_target_1w FROM ML.PREDICT(
      MODEL `cbi-v14.models_v4.bqml_1w`,
      (SELECT * FROM base_data))) as original_prediction
)
SELECT 
  date,
  zl_price_current as current_price,
  
  -- Individual predictions
  ROUND(crush_prediction, 2) as crush_model,
  ROUND(big8_prediction, 2) as big8_model,
  ROUND(full_prediction, 2) as full_model,
  ROUND(original_prediction, 2) as original_model,
  
  -- Weighted ensemble (favor best performer)
  ROUND(
    crush_prediction * 0.40 +    -- 40% weight on correlation-based
    big8_prediction * 0.25 +      -- 25% on Big 8
    full_prediction * 0.20 +      -- 20% on kitchen sink
    original_prediction * 0.15,   -- 15% on original
    2
  ) as ensemble_prediction,
  
  -- Price changes
  ROUND(crush_prediction - zl_price_current, 2) as crush_change,
  ROUND(((crush_prediction - zl_price_current) / zl_price_current) * 100, 2) as crush_pct_change,
  
  ROUND(
    ((crush_prediction * 0.40 + big8_prediction * 0.25 + full_prediction * 0.20 + original_prediction * 0.15) 
     - zl_price_current) / zl_price_current * 100, 
    2
  ) as ensemble_pct_change
  
FROM predictions;

-- ============================================
-- FEATURE IMPORTANCE EXTRACTION
-- ============================================
CREATE OR REPLACE TABLE `cbi-v14.models_v4.ultimate_feature_importance` AS
SELECT 
  'bqml_ultimate_crush_1w' as model_name,
  feature,
  importance_gain,
  importance_cover,
  importance_weight
FROM ML.FEATURE_IMPORTANCE(MODEL `cbi-v14.models_v4.bqml_ultimate_crush_1w`)

UNION ALL

SELECT 
  'bqml_ultimate_big8_1w',
  feature,
  importance_gain,
  importance_cover,
  importance_weight
FROM ML.FEATURE_IMPORTANCE(MODEL `cbi-v14.models_v4.bqml_ultimate_big8_1w`)

UNION ALL

SELECT 
  'bqml_ultimate_full_1w',
  feature,
  importance_gain,
  importance_cover,
  importance_weight
FROM ML.FEATURE_IMPORTANCE(MODEL `cbi-v14.models_v4.bqml_ultimate_full_1w`)
ORDER BY model_name, importance_gain DESC;

-- ============================================
-- FINAL VERIFICATION
-- ============================================
SELECT 
  '🚀 ULTIMATE MODELS CREATED!' as status,
  COUNT(DISTINCT model_name) as models_created,
  MIN(mean_absolute_error) as best_mae,
  MAX(r2_score) as best_r2,
  'CHECK vw_ultimate_ensemble_1w FOR PREDICTIONS' as next_step
FROM `cbi-v14.models_v4.ultimate_model_comparison`;






