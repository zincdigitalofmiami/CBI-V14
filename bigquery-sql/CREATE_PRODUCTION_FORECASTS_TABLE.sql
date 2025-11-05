-- ============================================
-- CREATE PRODUCTION FORECASTS TABLE
-- ============================================
-- Purpose: Create table to store production forecasts from BQML models
-- Dataset: cbi-v14.predictions_uc1
-- Table: production_forecasts
-- ============================================

CREATE TABLE IF NOT EXISTS `cbi-v14.predictions_uc1.production_forecasts`
(
  forecast_id STRING NOT NULL,  -- Unique forecast ID (UUID)
  forecast_date DATE NOT NULL,  -- Date forecast was generated
  horizon STRING NOT NULL,  -- '1W', '1M', '3M', '6M'
  target_date DATE NOT NULL,  -- Date being forecasted
  predicted_value FLOAT64 NOT NULL,  -- Forecasted price
  lower_bound_80 FLOAT64,  -- 10th percentile (80% confidence lower)
  upper_bound_80 FLOAT64,  -- 90th percentile (80% confidence upper)
  lower_bound_95 FLOAT64,  -- 2.5th percentile (95% confidence lower)
  upper_bound_95 FLOAT64,  -- 97.5th percentile (95% confidence upper)
  model_name STRING NOT NULL,  -- 'bqml_1w', 'bqml_1m', 'bqml_3m', 'bqml_6m'
  confidence FLOAT64,  -- Forecast confidence % (45-75% based on crisis intensity)
  mape_historical FLOAT64,  -- Historical MAPE for this model/horizon
  market_regime STRING,  -- Current market regime classification
  crisis_intensity_score FLOAT64,  -- Crisis intensity (0-100)
  primary_signal_driver STRING,  -- Which Big 8 signal is driving forecast
  composite_signal_score FLOAT64,  -- Big 8 composite score (0-1)
  palm_sub_risk FLOAT64,  -- Palm substitution risk indicator
  created_at TIMESTAMP NOT NULL  -- When forecast was generated
)
PARTITION BY forecast_date
CLUSTER BY horizon, model_name
OPTIONS(
  description="Production forecasts from BQML models with metadata for dashboard consumption"
);

-- Create indexes for common queries
-- Note: BigQuery doesn't support explicit indexes, but clustering helps

-- ============================================
-- VERIFICATION
-- ============================================
-- Check table was created
/*
SELECT 
  table_name,
  row_count,
  size_bytes,
  created
FROM `cbi-v14.predictions_uc1.INFORMATION_SCHEMA.TABLES`
WHERE table_name = 'production_forecasts';
*/


