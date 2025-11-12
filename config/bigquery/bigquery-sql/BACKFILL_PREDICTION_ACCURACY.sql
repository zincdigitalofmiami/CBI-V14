-- ============================================
-- BACKFILL PREDICTION ACCURACY
-- ============================================
-- Purpose: Compare historical predictions with actual prices
-- This script backfills accuracy data for all past predictions
-- ============================================

-- First, delete any existing accuracy records to avoid duplicates
DELETE FROM `cbi-v14.predictions_uc1.prediction_accuracy`
WHERE forecast_date < CURRENT_DATE();

-- Compare historical predictions with actual prices
WITH historical_forecasts AS (
  SELECT 
    forecast_id,
    forecast_date,
    target_date,
    horizon,
    predicted_value,
    lower_bound_80,
    upper_bound_80,
    lower_bound_95,
    upper_bound_95,
    model_name,
    DATE_DIFF(target_date, forecast_date, DAY) as days_ahead
  FROM `cbi-v14.predictions_uc1.production_forecasts`
  WHERE target_date <= CURRENT_DATE()  -- Only past predictions
    AND forecast_date < CURRENT_DATE()  -- Don't include today's forecasts
),
actual_prices AS (
  SELECT 
    DATE(time) as price_date,
    close as actual_price
  FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
),
matched_data AS (
  SELECT 
    hf.forecast_id,
    hf.forecast_date,
    hf.target_date,
    hf.horizon,
    hf.predicted_value,
    ap.actual_price,
    ABS(hf.predicted_value - ap.actual_price) as absolute_error,
    ABS((hf.predicted_value - ap.actual_price) / ap.actual_price) * 100 as absolute_percentage_error,
    hf.predicted_value - ap.actual_price as prediction_error,
    CASE 
      WHEN ap.actual_price BETWEEN hf.lower_bound_80 AND hf.upper_bound_80 THEN TRUE
      ELSE FALSE
    END as within_80_ci,
    CASE 
      WHEN hf.lower_bound_95 IS NOT NULL AND hf.upper_bound_95 IS NOT NULL THEN
        CASE 
          WHEN ap.actual_price BETWEEN hf.lower_bound_95 AND hf.upper_bound_95 THEN TRUE
          ELSE FALSE
        END
      ELSE FALSE
    END as within_95_ci,
    hf.model_name,
    hf.days_ahead
  FROM historical_forecasts hf
  LEFT JOIN actual_prices ap
    ON hf.target_date = ap.price_date
  WHERE ap.actual_price IS NOT NULL
)
INSERT INTO `cbi-v14.predictions_uc1.prediction_accuracy`
SELECT 
  GENERATE_UUID() as accuracy_id,
  forecast_date,
  target_date,
  horizon,
  predicted_value,
  actual_price as actual_value,
  absolute_error,
  absolute_percentage_error,
  prediction_error,
  within_80_ci,
  within_95_ci,
  model_name,
  days_ahead,
  CURRENT_TIMESTAMP() as computed_at
FROM matched_data;

-- ============================================
-- VERIFICATION QUERY
-- ============================================
-- Run this after backfill to verify accuracy data
/*
SELECT 
  horizon,
  model_name,
  COUNT(*) as total_predictions,
  AVG(absolute_percentage_error) as mean_ape,
  PERCENTILE_CONT(absolute_percentage_error, 0.5) OVER (PARTITION BY horizon) as median_ape,
  AVG(absolute_error) as mean_ae,
  SUM(CASE WHEN within_80_ci THEN 1 ELSE 0 END) / COUNT(*) * 100 as ci_coverage_80_pct,
  SUM(CASE WHEN within_95_ci THEN 1 ELSE 0 END) / COUNT(*) * 100 as ci_coverage_95_pct,
  MIN(forecast_date) as first_forecast,
  MAX(forecast_date) as last_forecast
FROM `cbi-v14.predictions_uc1.prediction_accuracy`
WHERE actual_value IS NOT NULL
GROUP BY horizon, model_name
ORDER BY horizon, mean_ape;
*/

