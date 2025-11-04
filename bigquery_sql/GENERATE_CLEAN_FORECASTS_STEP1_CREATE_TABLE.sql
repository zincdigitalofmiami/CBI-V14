-- ============================================
-- STEP 1: CREATE PRODUCTION FORECASTS TABLE
-- ============================================
-- Run this first to create the table

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

