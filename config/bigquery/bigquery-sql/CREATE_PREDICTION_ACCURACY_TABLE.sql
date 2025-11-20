-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- CREATE PREDICTION ACCURACY TABLE
-- ============================================
-- Purpose: Track prediction accuracy by comparing forecasts vs actuals
-- Dataset: cbi-v14.predictions_uc1
-- Table: prediction_accuracy
-- ============================================

CREATE TABLE IF NOT EXISTS `cbi-v14.predictions_uc1.prediction_accuracy` (
  accuracy_id STRING NOT NULL,
  forecast_date DATE NOT NULL,
  target_date DATE NOT NULL,
  horizon STRING NOT NULL,
  predicted_value FLOAT64 NOT NULL,
  actual_value FLOAT64,
  absolute_error FLOAT64,
  absolute_percentage_error FLOAT64,
  prediction_error FLOAT64,
  within_80_ci BOOL,
  within_95_ci BOOL,
  model_name STRING NOT NULL,
  days_ahead INT64 NOT NULL,  -- Days between forecast_date and target_date
  computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY forecast_date
CLUSTER BY horizon, model_name
OPTIONS(
  description="Prediction accuracy tracking - compares forecasts vs actual prices for backtesting and model evaluation"
);

-- Create index-like structure using clustering
-- BigQuery automatically clusters by (horizon, model_name) for fast queries

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
WHERE table_name = 'prediction_accuracy';
*/

