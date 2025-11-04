-- ============================================
-- Technical Indicators for Soybean Futures
-- RSI, MACD, Bollinger Bands
-- ============================================

-- Add these columns to your training dataset
-- Run this as an ALTER TABLE or create as a view

WITH price_data AS (
  SELECT 
    date,
    zl_price_current,
    LAG(zl_price_current) OVER (ORDER BY date) AS prev_price
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE zl_price_current IS NOT NULL
),

rsi_calc AS (
  SELECT 
    date,
    zl_price_current,
    CASE 
      WHEN zl_price_current > prev_price THEN zl_price_current - prev_price
      ELSE 0 
    END AS gain,
    CASE 
      WHEN zl_price_current < prev_price THEN prev_price - zl_price_current
      ELSE 0 
    END AS loss
  FROM price_data
),

rsi_smoothed AS (
  SELECT 
    date,
    zl_price_current,
    AVG(gain) OVER (ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS avg_gain,
    AVG(loss) OVER (ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS avg_loss
  FROM rsi_calc
),

macd_data AS (
  SELECT 
    date,
    zl_price_current,
    -- EMA approximations (using moving averages)
    AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) AS ema_12,
    AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 25 PRECEDING AND CURRENT ROW) AS ema_26,
    AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 8 PRECEDING AND CURRENT ROW) AS ema_9
  FROM price_data
),

bollinger_data AS (
  SELECT 
    date,
    zl_price_current,
    AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS bb_middle,
    STDDEV(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS bb_stddev
  FROM price_data
)

SELECT 
  r.date,
  r.zl_price_current,
  -- RSI (14-day)
  CASE 
    WHEN r.avg_loss = 0 THEN 100
    ELSE 100 - (100 / (1 + (r.avg_gain / NULLIF(r.avg_loss, 0))))
  END AS rsi_14,
  
  -- MACD
  m.ema_12 - m.ema_26 AS macd_line,
  (m.ema_12 - m.ema_26) - m.ema_9 AS macd_signal,
  
  -- Bollinger Bands
  b.bb_middle AS bollinger_middle,
  b.bb_middle + (2 * b.bb_stddev) AS bollinger_upper,
  b.bb_middle - (2 * b.bb_stddev) AS bollinger_lower,
  (r.zl_price_current - b.bb_middle) / NULLIF(b.bb_stddev, 0) AS bollinger_percent
  
FROM rsi_smoothed r
JOIN macd_data m ON r.date = m.date
JOIN bollinger_data b ON r.date = b.date
ORDER BY date;

-- Usage: Join this with your training dataset to add technical indicators


