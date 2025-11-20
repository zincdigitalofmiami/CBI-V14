-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- STEP 4: CREATE PREDICTIONS WITH CONFIDENCE BANDS
-- Combines P10, P50, P90 predictions
-- ============================================

CREATE OR REPLACE TABLE `cbi-v14.models_v4.predictions_1m` AS
WITH 
p10_predictions AS (
  SELECT 
    input.date,
    input.f01_zl_close AS current_price,
    input.target_1m AS actual_change,
    predicted_target_1m AS predicted_change_p10,
    input.f01_zl_close + predicted_target_1m AS predicted_price_p10
  FROM ML.PREDICT(
    MODEL `cbi-v14.models_v4.bqml_1m_p10`,
    (SELECT * FROM `cbi-v14.models_v4.training_data_1m_clean` WHERE date >= '2024-01-01')
  ) AS input
),
p50_predictions AS (
  SELECT 
    input.date,
    predicted_target_1m AS predicted_change_p50,
    input.f01_zl_close + predicted_target_1m AS predicted_price_p50
  FROM ML.PREDICT(
    MODEL `cbi-v14.models_v4.bqml_1m_p50`,
    (SELECT * FROM `cbi-v14.models_v4.training_data_1m_clean` WHERE date >= '2024-01-01')
  ) AS input
),
p90_predictions AS (
  SELECT 
    input.date,
    predicted_target_1m AS predicted_change_p90,
    input.f01_zl_close + predicted_target_1m AS predicted_price_p90
  FROM ML.PREDICT(
    MODEL `cbi-v14.models_v4.bqml_1m_p90`,
    (SELECT * FROM `cbi-v14.models_v4.training_data_1m_clean` WHERE date >= '2024-01-01')
  ) AS input
)
SELECT 
  p10.date,
  p10.current_price,
  p10.actual_change,
  p10.predicted_change_p10,
  p50.predicted_change_p50,
  p90.predicted_change_p90,
  p10.predicted_price_p10,
  p50.predicted_price_p50,
  p90.predicted_price_p90,
  
  -- Uncertainty bands
  p90.predicted_price_p90 - p10.predicted_price_p10 AS uncertainty_range,
  (p90.predicted_price_p90 - p10.predicted_price_p10) / NULLIF(p50.predicted_price_p50, 0) * 100 AS uncertainty_pct,
  
  -- Risk classification
  CASE 
    WHEN (p90.predicted_price_p90 - p10.predicted_price_p10) / NULLIF(p50.predicted_price_p50, 0) > 0.10 THEN 'HIGH'
    WHEN (p90.predicted_price_p90 - p10.predicted_price_p10) / NULLIF(p50.predicted_price_p50, 0) > 0.05 THEN 'MEDIUM'
    ELSE 'LOW'
  END AS risk_level,
  
  -- Prediction error (if actual available)
  p50.predicted_price_p50 - (p10.current_price + p10.actual_change) AS prediction_error,
  ABS(p50.predicted_price_p50 - (p10.current_price + p10.actual_change)) / NULLIF(p10.current_price + p10.actual_change, 0) * 100 AS mape_pct
  
FROM p10_predictions p10
JOIN p50_predictions p50 ON p10.date = p50.date
JOIN p90_predictions p90 ON p10.date = p90.date
ORDER BY p10.date DESC;

-- Summary statistics
SELECT 
  COUNT(*) AS prediction_count,
  AVG(uncertainty_pct) AS avg_uncertainty_pct,
  AVG(mape_pct) AS avg_mape_pct,
  COUNT(CASE WHEN risk_level = 'HIGH' THEN 1 END) AS high_risk_count,
  COUNT(CASE WHEN risk_level = 'MEDIUM' THEN 1 END) AS medium_risk_count,
  COUNT(CASE WHEN risk_level = 'LOW' THEN 1 END) AS low_risk_count
FROM `cbi-v14.models_v4.predictions_1m`;

