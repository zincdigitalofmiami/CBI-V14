-- Create signals_1w table
-- Stores computed 1W signals (offline, no Vertex endpoint)
-- PATCH 3: JSON constraint for rolled_forecast_7d

CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.signals_1w` (
  as_of_timestamp TIMESTAMP NOT NULL,
  signal_name STRING NOT NULL,
  signal_value FLOAT64,
  rolled_forecast_7d_json STRING,  -- JSON array of 7-day forecast path
  model_version STRING,
  source STRING DEFAULT 'offline',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  
  -- PATCH 3: Constraint ensuring rolled_forecast_7d_json is valid JSON array with 7 elements
  CONSTRAINT valid_rolled_forecast CHECK (
    signal_name != 'rolled_forecast_7d' OR 
    (rolled_forecast_7d_json IS NOT NULL AND
     JSON_EXTRACT_ARRAY(rolled_forecast_7d_json) IS NOT NULL AND
     ARRAY_LENGTH(JSON_EXTRACT_ARRAY(rolled_forecast_7d_json)) = 7)
  )
)
PARTITION BY DATE(as_of_timestamp)
CLUSTER BY signal_name;

