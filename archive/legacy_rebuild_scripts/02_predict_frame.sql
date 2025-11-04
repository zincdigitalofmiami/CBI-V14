-- 02_predict_frame.sql
-- Build predict_frame_209: single row with all 209 columns, no NULLs for target_*

CREATE OR REPLACE TABLE `cbi-v14.models_v4.predict_frame_209` AS
WITH d AS (
  SELECT latest_date FROM `cbi-v14.models_v4._latest_date`
),
price_data AS (
  SELECT 
    DATE(time) AS date,
    close,
    volume,
    LAG(close, 1)  OVER (ORDER BY time) AS lag1,
    LAG(close, 7)  OVER (ORDER BY time) AS lag7,
    LAG(close, 30) OVER (ORDER BY time) AS lag30
  FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
  WHERE symbol = 'ZL'
),
training_row AS (
  SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE date = (SELECT latest_date FROM d)
)
SELECT
  -- REQUIRED KEYS
  d.latest_date AS date,
  
  -- PRICE CORE (recomputed from fresh price data)
  p.close AS zl_price_current,
  p.lag1 AS zl_price_lag1,
  p.lag7 AS zl_price_lag7,
  p.lag30 AS zl_price_lag30,
  (p.close - p.lag1) / NULLIF(p.lag1, 0) AS return_1d,
  (p.close - p.lag7) / NULLIF(p.lag7, 0) AS return_7d,
  AVG(p.close) OVER (ORDER BY p.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS ma_7d,
  AVG(p.close) OVER (ORDER BY p.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS ma_30d,
  STDDEV_POP(p.close) OVER (ORDER BY p.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS volatility_30d,
  p.volume AS zl_volume,
  
  -- ALL OTHER COLUMNS FROM TRAINING ROW (except date, price columns, targets)
  -- Use SELECT * EXCEPT to bring everything else
  t.* EXCEPT(date, zl_price_current, zl_price_lag1, zl_price_lag7, zl_price_lag30,
             return_1d, return_7d, ma_7d, ma_30d, volatility_30d, zl_volume,
             target_1w, target_1m, target_3m, target_6m),
  
  -- TARGET COLUMNS (REQUIRED BY MODEL SCHEMA; NO NULLS!)
  -- Set to current price to satisfy "no NULL in transformations"
  CAST(p.close AS FLOAT64) AS target_1w,
  CAST(p.close AS FLOAT64) AS target_1m,
  CAST(p.close AS FLOAT64) AS target_3m,
  CAST(p.close AS FLOAT64) AS target_6m

FROM d
JOIN price_data p ON p.date = d.latest_date
JOIN training_row t ON TRUE  -- Single row join



