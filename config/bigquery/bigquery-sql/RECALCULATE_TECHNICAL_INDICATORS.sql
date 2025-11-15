-- ============================================
-- RECALCULATE TECHNICAL INDICATORS
-- Fix RSI_14 and MACD (currently template values)
-- Date: November 6, 2025
-- ============================================

-- RSI (Relative Strength Index) calculation
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET rsi_14 = rsi_calc.rsi_14
FROM (
  WITH price_data AS (
    SELECT 
      date,
      zl_price_current,
      LAG(zl_price_current, 1) OVER (ORDER BY date) AS prev_price
    FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
    WHERE zl_price_current IS NOT NULL
  ),
  rsi_gains_losses AS (
    SELECT 
      date,
      CASE WHEN zl_price_current > prev_price THEN zl_price_current - prev_price ELSE 0 END AS gain,
      CASE WHEN zl_price_current < prev_price THEN prev_price - zl_price_current ELSE 0 END AS loss
    FROM price_data
  ),
  rsi_smoothed AS (
    SELECT 
      date,
      AVG(gain) OVER (ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS avg_gain,
      AVG(loss) OVER (ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS avg_loss
    FROM rsi_gains_losses
  )
  SELECT 
    date,
    CASE WHEN avg_loss = 0 THEN 100 ELSE 100 - (100 / (1 + (avg_gain / NULLIF(avg_loss, 0)))) END AS rsi_14
  FROM rsi_smoothed
) rsi_calc
WHERE t.date = rsi_calc.date AND t.date > '2025-09-10';

-- MACD (Moving Average Convergence Divergence) calculation
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  macd_line = macd_calc.macd_line,
  macd_signal = macd_calc.macd_signal,
  macd_histogram = macd_calc.macd_histogram
FROM (
  WITH price_data AS (
    SELECT 
      date,
      zl_price_current
    FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
    WHERE zl_price_current IS NOT NULL
  ),
  macd_ema AS (
    SELECT 
      date,
      AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) AS ema_12,
      AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 25 PRECEDING AND CURRENT ROW) AS ema_26
    FROM price_data
  ),
  macd_with_signal AS (
    SELECT 
      date,
      ema_12 - ema_26 AS macd_line,
      AVG(ema_12 - ema_26) OVER (ORDER BY date ROWS BETWEEN 8 PRECEDING AND CURRENT ROW) AS macd_signal
    FROM macd_ema
  )
  SELECT 
    date,
    macd_line,
    macd_signal,
    macd_line - macd_signal AS macd_histogram
  FROM macd_with_signal
) macd_calc
WHERE t.date = macd_calc.date AND t.date > '2025-09-10';

-- Verification
SELECT 
  'Technical Indicators Recalculated' as status,
  COUNT(*) as rows_updated,
  COUNT(CASE WHEN rsi_14 IS NOT NULL THEN 1 END) as has_rsi,
  COUNT(CASE WHEN macd_line IS NOT NULL THEN 1 END) as has_macd,
  AVG(rsi_14) as avg_rsi,
  AVG(macd_line) as avg_macd,
  MIN(date) as earliest,
  MAX(date) as latest
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
WHERE date > '2025-09-10';

