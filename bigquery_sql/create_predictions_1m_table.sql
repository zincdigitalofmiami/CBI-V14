-- Create predictions_1m table
-- Stores 30-day ahead forecasts with q10/mean/q90 quantiles
-- Includes gate blend weights and blended flag

CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.predictions_1m` (
  as_of_timestamp TIMESTAMP NOT NULL,
  future_day INT64 NOT NULL,  -- D+1 to D+30
  q10 FLOAT64 NOT NULL,  -- 10th percentile
  mean FLOAT64 NOT NULL,  -- 50th percentile (median)
  q90 FLOAT64 NOT NULL,  -- 90th percentile
  gate_weight FLOAT64,  -- Blend weight (0.6-0.95 for D+1-7, 1.0 for D+8-30)
  blended BOOL,  -- True if blended with 1W (D+1-7 only)
  model_version STRING,
  created_at TIMESTAMP
)
PARTITION BY DATE(as_of_timestamp)
CLUSTER BY (future_day, model_version);

-- Create index for common queries
CREATE INDEX IF NOT EXISTS idx_predictions_1m_latest 
ON `cbi-v14.forecasting_data_warehouse.predictions_1m`(as_of_timestamp DESC, future_day);

