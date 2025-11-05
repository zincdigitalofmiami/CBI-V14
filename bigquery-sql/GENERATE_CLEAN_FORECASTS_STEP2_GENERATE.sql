-- ============================================
-- STEP 2: GENERATE CLEAN FORECASTS
-- ============================================
-- Run this after table is created

-- Get latest training data row
WITH latest_data AS (
  SELECT *
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE date = (SELECT MAX(date) FROM `cbi-v14.models_v4.training_dataset_super_enriched`)
),

-- Generate forecasts from all 4 models
forecast_1w AS (
  SELECT 
    GENERATE_UUID() as forecast_id,
    CURRENT_DATE() as forecast_date,
    '1W' as horizon,
    DATE_ADD((SELECT date FROM latest_data), INTERVAL 7 DAY) as target_date,
    predicted_target_1w as predicted_value,
    NULL as lower_bound_80,
    NULL as upper_bound_80,
    NULL as lower_bound_95,
    NULL as upper_bound_95,
    'bqml_1w' as model_name,
    75.0 as confidence,
    1.21 as mape_historical,
    NULL as market_regime,
    NULL as crisis_intensity_score,
    NULL as primary_signal_driver,
    NULL as composite_signal_score,
    NULL as palm_sub_risk,
    CURRENT_TIMESTAMP() as created_at
  FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_1w`, (SELECT * FROM latest_data))
),

forecast_1m AS (
  SELECT 
    GENERATE_UUID() as forecast_id,
    CURRENT_DATE() as forecast_date,
    '1M' as horizon,
    DATE_ADD((SELECT date FROM latest_data), INTERVAL 30 DAY) as target_date,
    predicted_target_1m as predicted_value,
    NULL as lower_bound_80,
    NULL as upper_bound_80,
    NULL as lower_bound_95,
    NULL as upper_bound_95,
    'bqml_1m' as model_name,
    70.0 as confidence,
    1.29 as mape_historical,
    NULL as market_regime,
    NULL as crisis_intensity_score,
    NULL as primary_signal_driver,
    NULL as composite_signal_score,
    NULL as palm_sub_risk,
    CURRENT_TIMESTAMP() as created_at
  FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_1m`, (SELECT * FROM latest_data))
),

forecast_3m AS (
  SELECT 
    GENERATE_UUID() as forecast_id,
    CURRENT_DATE() as forecast_date,
    '3M' as horizon,
    DATE_ADD((SELECT date FROM latest_data), INTERVAL 90 DAY) as target_date,
    predicted_target_3m as predicted_value,
    NULL as lower_bound_80,
    NULL as upper_bound_80,
    NULL as lower_bound_95,
    NULL as upper_bound_95,
    'bqml_3m' as model_name,
    65.0 as confidence,
    0.70 as mape_historical,
    NULL as market_regime,
    NULL as crisis_intensity_score,
    NULL as primary_signal_driver,
    NULL as composite_signal_score,
    NULL as palm_sub_risk,
    CURRENT_TIMESTAMP() as created_at
  FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_3m`, (SELECT * FROM latest_data))
),

forecast_6m AS (
  SELECT 
    GENERATE_UUID() as forecast_id,
    CURRENT_DATE() as forecast_date,
    '6M' as horizon,
    DATE_ADD((SELECT date FROM latest_data), INTERVAL 180 DAY) as target_date,
    predicted_target_6m as predicted_value,
    NULL as lower_bound_80,
    NULL as upper_bound_80,
    NULL as lower_bound_95,
    NULL as upper_bound_95,
    'bqml_6m' as model_name,
    60.0 as confidence,
    1.21 as mape_historical,
    NULL as market_regime,
    NULL as crisis_intensity_score,
    NULL as primary_signal_driver,
    NULL as composite_signal_score,
    NULL as palm_sub_risk,
    CURRENT_TIMESTAMP() as created_at
  FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_6m`, (SELECT * FROM latest_data))
),

-- Combine all forecasts
all_forecasts AS (
  SELECT * FROM forecast_1w
  UNION ALL
  SELECT * FROM forecast_1m
  UNION ALL
  SELECT * FROM forecast_3m
  UNION ALL
  SELECT * FROM forecast_6m
)

-- Insert forecasts (idempotent - delete existing first, then insert)
INSERT INTO `cbi-v14.predictions_uc1.production_forecasts`
SELECT * FROM all_forecasts;

