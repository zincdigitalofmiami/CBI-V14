-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- STEP 5: EVALUATE ALL THREE MODELS
-- Target: MAPE < 0.35%, R² > 0.994
-- ============================================

-- EVALUATE P10 MODEL
SELECT 
  'P10 (10th percentile)' AS model_name,
  mean_absolute_error AS mae,
  mean_squared_error AS mse,
  root_mean_squared_error AS rmse,
  mean_absolute_percentage_error AS mape,
  r2_score AS r2
FROM ML.EVALUATE(
  MODEL `cbi-v14.models_v4.bqml_1m_p10`,
  (SELECT * FROM `cbi-v14.models_v4.training_data_1m_clean` WHERE date >= '2024-01-01')
);

-- EVALUATE P50 MODEL
SELECT 
  'P50 (50th percentile - median)' AS model_name,
  mean_absolute_error AS mae,
  mean_squared_error AS mse,
  root_mean_squared_error AS rmse,
  mean_absolute_percentage_error AS mape,
  r2_score AS r2
FROM ML.EVALUATE(
  MODEL `cbi-v14.models_v4.bqml_1m_p50`,
  (SELECT * FROM `cbi-v14.models_v4.training_data_1m_clean` WHERE date >= '2024-01-01')
);

-- EVALUATE P90 MODEL
SELECT 
  'P90 (90th percentile)' AS model_name,
  mean_absolute_error AS mae,
  mean_squared_error AS mse,
  root_mean_squared_error AS rmse,
  mean_absolute_percentage_error AS mape,
  r2_score AS r2
FROM ML.EVALUATE(
  MODEL `cbi-v14.models_v4.bqml_1m_p90`,
  (SELECT * FROM `cbi-v14.models_v4.training_data_1m_clean` WHERE date >= '2024-01-01')
);

-- FEATURE IMPORTANCE (P50 model - most important)
SELECT 
  feature,
  importance_weight,
  importance_gain
FROM ML.FEATURE_INFO(MODEL `cbi-v14.models_v4.bqml_1m_p50`)
ORDER BY importance_weight DESC
LIMIT 20;

