-- Create master features view for forecast service
-- Joins soybean prices + weather data + volatility metrics
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.soy_oil_features` AS
WITH price_data AS (
  SELECT 
    DATE(time) as date,
    close as oil_price,
    volume,
    -- Technical indicators
    AVG(close) OVER (ORDER BY time ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) as sma_5,
    AVG(close) OVER (ORDER BY time ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as sma_20,
    STDDEV(close) OVER (ORDER BY time ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as volatility_20d
  FROM `cbi-v14.forecasting_data_warehouse.soybean_prices`
  WHERE symbol = 'ZL'
),
weather_pivot AS (
  SELECT 
    date,
    AVG(CASE WHEN region = 'Argentina' THEN precip_mm END) as argentina_precip,
    AVG(CASE WHEN region = 'US' THEN precip_mm END) as us_precip,
    AVG(CASE WHEN region = 'Argentina' THEN temp_max END) as argentina_temp,
    AVG(CASE WHEN region = 'US' THEN temp_max END) as us_temp
  FROM `cbi-v14.forecasting_data_warehouse.weather_data`
  GROUP BY date
),
volatility_avg AS (
  SELECT
    AVG(implied_vol) as avg_implied_vol,
    AVG(iv_hv_ratio) as avg_iv_hv_ratio
  FROM `cbi-v14.forecasting_data_warehouse.volatility_data`
  WHERE symbol LIKE 'ZL%'
)
SELECT 
  p.date,
  p.oil_price as value,
  p.volume,
  p.sma_5,
  p.sma_20, 
  p.volatility_20d,
  -- Weather factors (35-45% variance)
  COALESCE(w.argentina_precip, 0) as argentina_precip,
  COALESCE(w.us_precip, 0) as us_precip,
  COALESCE(w.argentina_temp, 0) as argentina_temp,
  COALESCE(w.us_temp, 0) as us_temp,
  -- Volatility factors
  v.avg_implied_vol,
  v.avg_iv_hv_ratio
FROM price_data p
LEFT JOIN weather_pivot w ON p.date = w.date
CROSS JOIN volatility_avg v
WHERE p.date >= DATE_SUB(CURRENT_DATE(), INTERVAL 730 DAY)
ORDER BY p.date;
