-- Create shap_drivers table
-- Stores SHAP contributions for explainability
-- Includes feature values, changes, and business labels

CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.shap_drivers` (
  as_of_timestamp TIMESTAMP NOT NULL,
  future_day INT64 NOT NULL,  -- D+1 to D+30
  feature_name STRING NOT NULL,
  business_label STRING,  -- From shap_business_labels.json
  shap_value FLOAT64 NOT NULL,
  feature_current_value FLOAT64,
  feature_historical_value FLOAT64,
  feature_change_pct FLOAT64,  -- % change for tooltip
  interpretation STRING,
  dollar_impact FLOAT64,
  direction STRING,  -- 'bullish', 'bearish', 'neutral'
  category STRING,  -- 'FX', 'Demand', 'Processing', etc.
  model_version STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(as_of_timestamp)
CLUSTER BY (future_day, feature_name);

