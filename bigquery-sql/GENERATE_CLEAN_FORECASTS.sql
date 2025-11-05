-- ============================================
-- GENERATE CLEAN, SAFE FORECASTS - BASE ONLY
-- ============================================
-- Purpose: Generate base forecasts from all 4 models
-- Approach: Clean, minimal, reliable
-- No enhancements yet - just core forecasting
-- ============================================

-- Step 1: Create production_forecasts table if it doesn't exist
CREATE TABLE IF NOT EXISTS `cbi-v14.predictions_uc1.production_forecasts`
(
  forecast_id STRING NOT NULL,
  forecast_date DATE NOT NULL,
  horizon STRING NOT NULL,  -- '1W', '1M', '3M', '6M'
  target_date DATE NOT NULL,
  predicted_value FLOAT64 NOT NULL,
  lower_bound_80 FLOAT64,
  upper_bound_80 FLOAT64,
  lower_bound_95 FLOAT64,
  upper_bound_95 FLOAT64,
  model_name STRING NOT NULL,
  confidence FLOAT64,
  mape_historical FLOAT64,
  market_regime STRING,
  crisis_intensity_score FLOAT64,
  primary_signal_driver STRING,
  composite_signal_score FLOAT64,
  palm_sub_risk FLOAT64,
  created_at TIMESTAMP NOT NULL
)
PARTITION BY forecast_date
CLUSTER BY horizon, model_name
OPTIONS(
  description="Production forecasts from BQML models - clean base forecasts"
);

-- Step 2: Get latest training data row
WITH latest_data AS (
  SELECT *
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE date = (SELECT MAX(date) FROM `cbi-v14.models_v4.training_dataset_super_enriched`)
),

-- Step 3: Generate forecasts from all 4 models
forecast_1w AS (
  SELECT 
    GENERATE_UUID() as forecast_id,
    CURRENT_DATE() as forecast_date,
    '1W' as horizon,
    DATE_ADD((SELECT date FROM latest_data), INTERVAL 7 DAY) as target_date,
    predicted_target_1w as predicted_value,
    NULL as lower_bound_80,  -- Will calculate from MAPE if needed
    NULL as upper_bound_80,  -- Will calculate from MAPE if needed
    NULL as lower_bound_95,  -- Will calculate if needed
    NULL as upper_bound_95,
    'bqml_1w' as model_name,
    75.0 as confidence,  -- Default confidence
    1.21 as mape_historical,  -- From training results
    NULL as market_regime,  -- Will add later
    NULL as crisis_intensity_score,  -- Will add later
    NULL as primary_signal_driver,  -- Will add later
    NULL as composite_signal_score,  -- Will add later
    NULL as palm_sub_risk,  -- Will add later
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
    0.70 as mape_historical,  -- Best performance
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

-- Step 4: Combine all forecasts
all_forecasts AS (
  SELECT * FROM forecast_1w
  UNION ALL
  SELECT * FROM forecast_1m
  UNION ALL
  SELECT * FROM forecast_3m
  UNION ALL
  SELECT * FROM forecast_6m
)

-- Step 5: Insert forecasts (idempotent - use MERGE to handle duplicates)
MERGE `cbi-v14.predictions_uc1.production_forecasts` AS target
USING all_forecasts AS source
ON target.forecast_date = source.forecast_date 
   AND target.horizon = source.horizon
WHEN MATCHED THEN
  UPDATE SET
    predicted_value = source.predicted_value,
    lower_bound_80 = source.lower_bound_80,
    upper_bound_80 = source.upper_bound_80,
    lower_bound_95 = source.lower_bound_95,
    upper_bound_95 = source.upper_bound_95,
    model_name = source.model_name,
    confidence = source.confidence,
    mape_historical = source.mape_historical,
    market_regime = source.market_regime,
    crisis_intensity_score = source.crisis_intensity_score,
    primary_signal_driver = source.primary_signal_driver,
    composite_signal_score = source.composite_signal_score,
    palm_sub_risk = source.palm_sub_risk,
    created_at = source.created_at
WHEN NOT MATCHED THEN
  INSERT (
    forecast_id, forecast_date, horizon, target_date, predicted_value,
    lower_bound_80, upper_bound_80, lower_bound_95, upper_bound_95,
    model_name, confidence, mape_historical, market_regime,
    crisis_intensity_score, primary_signal_driver, composite_signal_score,
    palm_sub_risk, created_at
  )
  VALUES (
    source.forecast_id, source.forecast_date, source.horizon, source.target_date, source.predicted_value,
    source.lower_bound_80, source.upper_bound_80, source.lower_bound_95, source.upper_bound_95,
    source.model_name, source.confidence, source.mape_historical, source.market_regime,
    source.crisis_intensity_score, source.primary_signal_driver, source.composite_signal_score,
    source.palm_sub_risk, source.created_at
  );

-- Step 6: Verification query
SELECT 
  horizon,
  target_date,
  predicted_value,
  lower_bound_80,
  upper_bound_80,
  model_name,
  confidence,
  mape_historical,
  created_at
FROM `cbi-v14.predictions_uc1.production_forecasts`
WHERE forecast_date = CURRENT_DATE()
ORDER BY 
  CASE horizon
    WHEN '1W' THEN 1
    WHEN '1M' THEN 2
    WHEN '3M' THEN 3
    WHEN '6M' THEN 4
  END;

