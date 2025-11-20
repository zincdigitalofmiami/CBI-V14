-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- CREATE ACCURACY DASHBOARD VIEW
-- ============================================
-- Purpose: Aggregate accuracy metrics for dashboard display
-- Dataset: cbi-v14.api
-- View: vw_prediction_accuracy
-- ============================================

CREATE OR REPLACE VIEW `cbi-v14.api.vw_prediction_accuracy` AS
SELECT 
  horizon,
  model_name,
  COUNT(*) as total_predictions,
  AVG(absolute_percentage_error) as mean_ape,
  APPROX_QUANTILES(absolute_percentage_error, 100)[OFFSET(50)] as median_ape,
  APPROX_QUANTILES(absolute_percentage_error, 100)[OFFSET(25)] as p25_ape,
  APPROX_QUANTILES(absolute_percentage_error, 100)[OFFSET(75)] as p75_ape,
  AVG(absolute_error) as mean_ae,
  STDDEV(absolute_percentage_error) as stddev_ape,
  SUM(CASE WHEN within_80_ci THEN 1 ELSE 0 END) / COUNT(*) * 100 as ci_coverage_80_pct,
  SUM(CASE WHEN within_95_ci THEN 1 ELSE 0 END) / COUNT(*) * 100 as ci_coverage_95_pct,
  MIN(forecast_date) as first_forecast,
  MAX(forecast_date) as last_forecast,
  COUNT(DISTINCT forecast_date) as unique_forecast_dates
FROM `cbi-v14.predictions_uc1.prediction_accuracy`
WHERE actual_value IS NOT NULL
GROUP BY horizon, model_name;

-- ============================================
-- VERIFICATION
-- ============================================
-- Check view returns data
/*
SELECT * FROM `cbi-v14.api.vw_prediction_accuracy`
ORDER BY horizon, mean_ape;
*/

