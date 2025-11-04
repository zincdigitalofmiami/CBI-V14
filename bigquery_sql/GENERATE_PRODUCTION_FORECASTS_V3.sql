-- ============================================
-- GENERATE PRODUCTION FORECASTS - 7-STAGE PROTOCOL v3.0
-- ============================================
-- STAGE 1: Daily Model Inference
-- STAGE 2: Big 8 Signal Aggregation
-- STAGE 3: Regime-Aware Forecast Adjustment
-- STAGE 4: Crisis Override Engine
-- STAGE 5: Confidence & Accuracy Metrics
-- ============================================

-- STAGE 1: Get latest training data and generate base forecasts
WITH latest_data AS (
  SELECT *
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE date = (SELECT MAX(date) FROM `cbi-v14.models_v4.training_dataset_super_enriched`)
),

-- STAGE 2: Get Big 8 composite signal for metadata
big8_metadata AS (
  SELECT 
    composite_signal_score,
    crisis_intensity_score,
    market_regime,
    forecast_confidence_pct,
    primary_signal_driver,
    date as signal_date,
    vix_current
  FROM `cbi-v14.api.vw_big8_composite_signal`
  WHERE date = (SELECT MAX(date) FROM `cbi-v14.api.vw_big8_composite_signal`)
),

-- Get China cancellation signals (for crisis detection)
china_signals AS (
  SELECT 
    COUNT(*) as china_cancellation_count
  FROM `cbi-v14.forecasting_data_warehouse.china_soybean_imports`
  WHERE cancellation_flag = TRUE 
    AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
),

-- STAGE 1: Generate base forecasts from all 4 models
forecast_1w AS (
  SELECT 
    '1W' as horizon,
    DATE_ADD((SELECT date FROM latest_data), INTERVAL 7 DAY) as target_date,
    predicted_target_1w as predicted_value,
    'bqml_1w' as model_name,
    1.21 as mape_historical  -- From training results
  FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_1w`, (SELECT * FROM latest_data))
),

forecast_1m AS (
  SELECT 
    '1M' as horizon,
    DATE_ADD((SELECT date FROM latest_data), INTERVAL 30 DAY) as target_date,
    predicted_target_1m as predicted_value,
    'bqml_1m' as model_name,
    1.29 as mape_historical
  FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_1m`, (SELECT * FROM latest_data))
),

forecast_3m AS (
  SELECT 
    '3M' as horizon,
    DATE_ADD((SELECT date FROM latest_data), INTERVAL 90 DAY) as target_date,
    predicted_target_3m as predicted_value,
    'bqml_3m' as model_name,
    0.70 as mape_historical
  FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_3m`, (SELECT * FROM latest_data))
),

forecast_6m AS (
  SELECT 
    '6M' as horizon,
    DATE_ADD((SELECT date FROM latest_data), INTERVAL 180 DAY) as target_date,
    predicted_target_6m as predicted_value,
    'bqml_6m' as model_name,
    1.21 as mape_historical
  FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_6m`, (SELECT * FROM latest_data))
),

-- Combine all base forecasts
all_forecasts AS (
  SELECT * FROM forecast_1w
  UNION ALL SELECT * FROM forecast_1m
  UNION ALL SELECT * FROM forecast_3m
  UNION ALL SELECT * FROM forecast_6m
),

-- STAGE 4: Detect crisis conditions
crisis_detection AS (
  SELECT 
    CASE 
      WHEN b8.crisis_intensity_score > 70 THEN TRUE
      WHEN COALESCE(china.china_cancellation_count, 0) > 3 THEN TRUE
      WHEN b8.vix_current > 30 THEN TRUE
      ELSE FALSE
    END as crisis_flag,
    CASE 
      WHEN COALESCE(china.china_cancellation_count, 0) > 3 THEN 
        CONCAT('China canceled ', CAST(china.china_cancellation_count AS STRING), ' shipments → -4.2% ZL impact')
      WHEN b8.crisis_intensity_score > 70 THEN 
        CONCAT('Crisis intensity: ', CAST(b8.crisis_intensity_score AS STRING), '/100 → Widened bands')
      WHEN b8.vix_current > 30 THEN 
        CONCAT('VIX spike: ', CAST(b8.vix_current AS STRING), ' → Volatility risk')
      ELSE NULL
    END as crisis_message
  FROM big8_metadata b8
  CROSS JOIN china_signals china
),

-- STAGE 3: Apply regime-aware adjustments
regime_adjustments AS (
  SELECT 
    f.horizon,
    f.predicted_value as base_forecast,
    f.mape_historical,
    b8.market_regime,
    b8.crisis_intensity_score,
    b8.composite_signal_score,
    b8.forecast_confidence_pct as base_confidence,
    -- STAGE 3: Regime-specific adjustments
    CASE 
      WHEN b8.market_regime = 'FUNDAMENTALS_REGIME' THEN f.predicted_value  -- Base forecast
      WHEN b8.market_regime = 'VIX_CRISIS_REGIME' THEN f.predicted_value * 0.92  -- -8% bias
      WHEN b8.market_regime = 'CHINA_TENSION_REGIME' THEN f.predicted_value  -- Base + volatility band
      WHEN b8.market_regime = 'BIOFUEL_BOOM_REGIME' THEN f.predicted_value * 1.12  -- +12% upside
      ELSE f.predicted_value
    END as forecast_adjusted,
    -- Regime-specific confidence
    CASE 
      WHEN b8.market_regime = 'FUNDAMENTALS_REGIME' THEN 75.0
      WHEN b8.market_regime = 'VIX_CRISIS_REGIME' THEN 52.0
      WHEN b8.market_regime = 'CHINA_TENSION_REGIME' THEN 48.0
      WHEN b8.market_regime = 'BIOFUEL_BOOM_REGIME' THEN 70.0
      ELSE b8.forecast_confidence_pct
    END as confidence_pct,
    -- Regime badge for display
    CASE 
      WHEN b8.market_regime = 'FUNDAMENTALS_REGIME' THEN 'FUNDAMENTALS'
      WHEN b8.market_regime = 'VIX_CRISIS_REGIME' THEN 'VIX_CRISIS'
      WHEN b8.market_regime = 'CHINA_TENSION_REGIME' THEN 'CHINA_TENSION'
      WHEN b8.market_regime = 'BIOFUEL_BOOM_REGIME' THEN 'BIOFUEL_BOOM'
      ELSE 'UNKNOWN'
    END as regime_badge
  FROM all_forecasts f
  CROSS JOIN big8_metadata b8
  CROSS JOIN crisis_detection c
),

-- STAGE 4: Apply crisis overrides (widen bands if crisis)
final_forecasts AS (
  SELECT 
    r.horizon,
    r.target_date,
    r.forecast_adjusted as predicted_value,
    r.model_name,
    r.mape_historical,
    r.market_regime,
    r.regime_badge,
    r.crisis_intensity_score,
    r.composite_signal_score,
    r.confidence_pct,
    b8.primary_signal_driver,
    -- STAGE 4: Widen bands if crisis (use q05/q95 instead of q10/q90)
    CASE 
      WHEN c.crisis_flag THEN 
        r.forecast_adjusted * (1 - r.mape_historical / 100 * 1.96)  -- 95% CI lower
      ELSE 
        r.forecast_adjusted * (1 - r.mape_historical / 100 * 1.28)  -- 80% CI lower
    END as lower_bound_80,
    CASE 
      WHEN c.crisis_flag THEN 
        r.forecast_adjusted * (1 + r.mape_historical / 100 * 1.96)  -- 95% CI upper
      ELSE 
        r.forecast_adjusted * (1 + r.mape_historical / 100 * 1.28)  -- 80% CI upper
    END as upper_bound_80,
    -- Always calculate 95% bands
    r.forecast_adjusted * (1 - r.mape_historical / 100 * 1.96) as lower_bound_95,
    r.forecast_adjusted * (1 + r.mape_historical / 100 * 1.96) as upper_bound_95,
    c.crisis_flag,
    c.crisis_message,
    -- Calculate palm substitution risk
    CASE 
      WHEN (SELECT palm_spread FROM latest_data) > 145 THEN 
        ((SELECT palm_spread FROM latest_data) - 145) / 10.0
      ELSE 0.0
    END as palm_sub_risk
  FROM regime_adjustments r
  CROSS JOIN all_forecasts af ON r.horizon = af.horizon
  CROSS JOIN crisis_detection c
  CROSS JOIN big8_metadata b8
)

-- Insert into production_forecasts table
INSERT INTO `cbi-v14.predictions_uc1.production_forecasts`
(
  forecast_id,
  forecast_date,
  horizon,
  target_date,
  predicted_value,
  lower_bound_80,
  upper_bound_80,
  lower_bound_95,
  upper_bound_95,
  model_name,
  confidence,
  mape_historical,
  market_regime,
  crisis_intensity_score,
  primary_signal_driver,
  composite_signal_score,
  palm_sub_risk,
  created_at
)
SELECT 
  GENERATE_UUID() as forecast_id,
  CURRENT_DATE() as forecast_date,
  horizon,
  target_date,
  predicted_value,
  lower_bound_80,
  upper_bound_80,
  lower_bound_95,
  upper_bound_95,
  model_name,
  confidence_pct as confidence,
  mape_historical,
  market_regime,
  crisis_intensity_score,
  primary_signal_driver,
  composite_signal_score,
  palm_sub_risk,
  CURRENT_TIMESTAMP() as created_at
FROM final_forecasts;

-- ============================================
-- VERIFICATION QUERY
-- ============================================
-- Run this after the INSERT to verify forecasts were generated
/*
SELECT 
  horizon,
  target_date,
  predicted_value,
  lower_bound_80,
  upper_bound_80,
  confidence,
  market_regime,
  crisis_intensity_score,
  primary_signal_driver,
  model_name,
  forecast_date
FROM `cbi-v14.predictions_uc1.production_forecasts`
WHERE forecast_date = CURRENT_DATE()
ORDER BY 
  CASE horizon
    WHEN '1W' THEN 1
    WHEN '1M' THEN 2
    WHEN '3M' THEN 3
    WHEN '6M' THEN 4
  END;
*/

