-- 📋 BEST PRACTICES: See `.cursorrules` and `docs/reference/BEST_PRACTICES_DRAFT.md` for mandatory best practices:
--    - No fake data, always check before creating, always audit after work
--    - us-central1 only, no costly resources without approval
--    - Research best practices, research quant finance modeling
--    - Always validate data quality, test queries, verify results

-- ============================================================================
-- VIEW: precomputed_features_daily
-- Technical indicators: RSI14, MACD 12/26/9, Bollinger 20/2, SMA50/200, daily vol proxy
-- ============================================================================

-- Create views dataset if it doesn't exist
CREATE SCHEMA IF NOT EXISTS views
OPTIONS (location='us-central1', description='Precomputed feature views');

CREATE OR REPLACE VIEW `cbi-v14.views.precomputed_features_daily` AS
WITH price_data AS (
  SELECT
    data_date,
    symbol,
    close,
    high,
    low,
    volume,
    -- Price change for RSI
    close - LAG(close) OVER (PARTITION BY symbol ORDER BY data_date) AS price_change
  FROM `cbi-v14.market_data.databento_futures_ohlcv_1d`
  WHERE close IS NOT NULL
),

-- RSI 14-day calculation (Wilder's method)
rsi_calc AS (
  SELECT
    data_date,
    symbol,
    close,
    -- Average gain over 14 days
    AVG(CASE WHEN price_change > 0 THEN price_change ELSE 0 END) 
      OVER (PARTITION BY symbol ORDER BY data_date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS avg_gain,
    -- Average loss over 14 days (absolute value)
    AVG(CASE WHEN price_change < 0 THEN ABS(price_change) ELSE 0 END) 
      OVER (PARTITION BY symbol ORDER BY data_date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS avg_loss
  FROM price_data
),

rsi_final AS (
  SELECT
    data_date,
    symbol,
    close,
    CASE
      WHEN avg_loss = 0 THEN 100
      ELSE 100 - (100 / (1 + (avg_gain / NULLIF(avg_loss, 0))))
    END AS rsi_14
  FROM rsi_calc
),

-- MACD 12-26-9 calculation
macd_data AS (
  SELECT
    data_date,
    symbol,
    close,
    -- EMA 12
    AVG(close) OVER (PARTITION BY symbol ORDER BY data_date ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) AS ema_12_approx,
    -- EMA 26
    AVG(close) OVER (PARTITION BY symbol ORDER BY data_date ROWS BETWEEN 25 PRECEDING AND CURRENT ROW) AS ema_26_approx
  FROM price_data
),

macd_calc AS (
  SELECT
    data_date,
    symbol,
    close,
    ema_12_approx,
    ema_26_approx,
    ema_12_approx - ema_26_approx AS macd_line,
    -- Signal line (9-day EMA of MACD line)
    AVG(ema_12_approx - ema_26_approx) 
      OVER (PARTITION BY symbol ORDER BY data_date ROWS BETWEEN 8 PRECEDING AND CURRENT ROW) AS macd_signal
  FROM macd_data
),

macd_final AS (
  SELECT
    data_date,
    symbol,
    macd_line,
    macd_signal,
    macd_line - macd_signal AS macd_histogram
  FROM macd_calc
),

-- Bollinger Bands (20-day, 2 standard deviations)
bb_calc AS (
  SELECT
    data_date,
    symbol,
    close,
    AVG(close) OVER (PARTITION BY symbol ORDER BY data_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS sma_20,
    STDDEV(close) OVER (PARTITION BY symbol ORDER BY data_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS std_20
  FROM price_data
),

bb_final AS (
  SELECT
    data_date,
    symbol,
    sma_20 AS bb_middle,
    sma_20 + (2 * std_20) AS bb_upper,
    sma_20 - (2 * std_20) AS bb_lower,
    SAFE_DIVIDE(
      (close - (sma_20 - (2 * std_20))),
      ((sma_20 + (2 * std_20)) - (sma_20 - (2 * std_20)))
    ) AS bb_percent
  FROM bb_calc
),

-- SMA 50 and 200
sma_calc AS (
  SELECT
    data_date,
    symbol,
    AVG(close) OVER (PARTITION BY symbol ORDER BY data_date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS sma_50,
    AVG(close) OVER (PARTITION BY symbol ORDER BY data_date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW) AS sma_200
  FROM price_data
),

-- Daily volatility proxy (using high-low range normalized by close)
vol_proxy AS (
  SELECT
    data_date,
    symbol,
    close,
    high,
    low,
    SAFE_DIVIDE(high - low, close) AS daily_vol_proxy
  FROM price_data
)

-- Final aggregation
SELECT
  p.data_date,
  p.symbol,
  p.close,
  p.high,
  p.low,
  p.volume,
  
  -- RSI 14
  r.rsi_14,
  
  -- MACD 12-26-9
  m.macd_line,
  m.macd_signal,
  m.macd_histogram,
  
  -- Bollinger Bands 20/2
  b.bb_middle,
  b.bb_upper,
  b.bb_lower,
  b.bb_percent,
  
  -- SMA 50/200
  s.sma_50,
  s.sma_200,
  
  -- Daily volatility proxy
  v.daily_vol_proxy
  
FROM price_data p
LEFT JOIN rsi_final r ON p.data_date = r.data_date AND p.symbol = r.symbol
LEFT JOIN macd_final m ON p.data_date = m.data_date AND p.symbol = m.symbol
LEFT JOIN bb_final b ON p.data_date = b.data_date AND p.symbol = b.symbol
LEFT JOIN sma_calc s ON p.data_date = s.data_date AND p.symbol = s.symbol
LEFT JOIN vol_proxy v ON p.data_date = v.data_date AND p.symbol = v.symbol
ORDER BY p.symbol, p.data_date;




