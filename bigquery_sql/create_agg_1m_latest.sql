-- Create agg_1m_latest table (materialized aggregation)
-- Aggregates predictions_1m to provide latest forecasts per future_day
-- FIXED: Uses AVG(q10), AVG(mean), AVG(q90) - NOT PERCENTILE_CONT

CREATE OR REPLACE TABLE `cbi-v14.forecasting_data_warehouse.agg_1m_latest` AS
SELECT 
  future_day,
  AVG(mean) AS mean,  -- FIXED: AVG not PERCENTILE_CONT
  AVG(q10) AS q10,  -- FIXED: AVG not PERCENTILE_CONT(0.1)
  AVG(q90) AS q90,  -- FIXED: AVG not PERCENTILE_CONT(0.9)
  AVG(gate_weight) AS avg_gate_weight,
  COUNT(*) AS prediction_count,
  MAX(as_of_timestamp) AS latest_prediction_time
FROM `cbi-v14.forecasting_data_warehouse.predictions_1m`
WHERE as_of_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY future_day
ORDER BY future_day;

