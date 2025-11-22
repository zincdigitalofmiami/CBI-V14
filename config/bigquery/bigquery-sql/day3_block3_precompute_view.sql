-- 📋 BEST PRACTICES: See `.cursorrules` and `docs/reference/BEST_PRACTICES_DRAFT.md` for mandatory best practices:
--    - No fake data, always check before creating, always audit after work
--    - us-central1 only, no costly resources without approval
--    - Research best practices, research quant finance modeling
--    - Always validate data quality, test queries, verify results

-- 🔭 BLOCK 3: Daily Precompute View
-- Purpose: Offloads technical analysis (RSI, MACD, Bollinger, SMA) to BigQuery. Output: views.precomputed_features_daily

CREATE SCHEMA IF NOT EXISTS views
OPTIONS (location='us-central1', description='Precomputed feature views');

CREATE OR REPLACE VIEW `cbi-v14.views.precomputed_features_daily` AS
WITH src AS (
  SELECT
    date AS data_date,
    symbol,
    open, high, low, close, volume,
    settle,
    -- Calculate daily VWAP fallback if missing (using date since vwap column may not exist)
    SAFE_DIVIDE(SUM(volume * close) OVER (PARTITION BY symbol, date),
                NULLIF(SUM(volume) OVER (PARTITION BY symbol, date),0)) AS vwap,
    open_interest,
    CAST(NULL AS STRING) AS instrument_id,
    CAST(NULL AS STRING) AS exchange,
    CAST(NULL AS STRING) AS currency,
    CAST(NULL AS STRING) AS dataset
  FROM `cbi-v14.market_data.databento_futures_ohlcv_1d`
  WHERE close IS NOT NULL
),

diffs AS (
  SELECT
    *,
    close - LAG(close) OVER w AS diff_close,
    SAFE_DIVIDE(close - LAG(close) OVER w, NULLIF(LAG(close) OVER w,0)) AS return_1d,
    GREATEST(
      high - low,
      ABS(high - LAG(close) OVER w),
      ABS(low - LAG(close) OVER w)
    ) AS true_range
  FROM src
  WINDOW w AS (PARTITION BY symbol ORDER BY data_date)
),

agg AS (
  SELECT
    *,
    -- RSI 14
    SAFE_MULTIPLY(100,
      1 - 1 / (1 + SAFE_DIVIDE(
        SUM(IF(diff_close > 0, diff_close, 0)) OVER w14 / 14,
        NULLIF(SUM(IF(diff_close < 0, -diff_close, 0)) OVER w14 / 14, 0)
      ))) AS rsi_14,
    -- SMAs
    AVG(close) OVER w5  AS sma_5,
    AVG(close) OVER w10 AS sma_10,
    AVG(close) OVER w20 AS sma_20,
    AVG(close) OVER w50 AS sma_50,
    AVG(close) OVER w100 AS sma_100,
    AVG(close) OVER w200 AS sma_200,
    -- Bollinger 20,2
    AVG(close) OVER w20 AS boll_mid_20_2,
    AVG(close) OVER w20 + 2*STDDEV(close) OVER w20 AS boll_upper_20_2,
    AVG(close) OVER w20 - 2*STDDEV(close) OVER w20 AS boll_lower_20_2,
    SAFE_DIVIDE(
      (2*STDDEV(close) OVER w20)*2,
      NULLIF(AVG(close) OVER w20,0)
    ) AS boll_bandwidth_20_2,
    -- ATR 14
    AVG(true_range) OVER w14 AS atr_14,
    -- MACD via UDF (simplified - using window function approach)
    -- Note: For proper EMA-based MACD, we'll use window functions as approximation
    -- EMA 12 approximation
    AVG(close) OVER (PARTITION BY symbol ORDER BY data_date ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) AS ema_12_approx,
    -- EMA 26 approximation  
    AVG(close) OVER (PARTITION BY symbol ORDER BY data_date ROWS BETWEEN 25 PRECEDING AND CURRENT ROW) AS ema_26_approx,
    -- Daily Realized Vol Proxy (Until 1H data is live in Day 4)
    STDDEV(close) OVER w20 AS realized_vol_daily_proxy
  FROM diffs
  WINDOW
    w5   AS (PARTITION BY symbol ORDER BY data_date ROWS BETWEEN 4 PRECEDING  AND CURRENT ROW),
    w10  AS (PARTITION BY symbol ORDER BY data_date ROWS BETWEEN 9 PRECEDING  AND CURRENT ROW),
    w20  AS (PARTITION BY symbol ORDER BY data_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW),
    w50  AS (PARTITION BY symbol ORDER BY data_date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW),
    w100 AS (PARTITION BY symbol ORDER BY data_date ROWS BETWEEN 99 PRECEDING AND CURRENT ROW),
    w200 AS (PARTITION BY symbol ORDER BY data_date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW),
    w14  AS (PARTITION BY symbol ORDER BY data_date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW)
),

macd_final AS (
  SELECT
    *,
    -- MACD line = EMA12 - EMA26
    ema_12_approx - ema_26_approx AS macd_line_12_26_9,
    -- Signal line (9-period moving average of MACD line)
    AVG(ema_12_approx - ema_26_approx) OVER (PARTITION BY symbol ORDER BY data_date ROWS BETWEEN 8 PRECEDING AND CURRENT ROW) AS macd_signal_12_26_9
  FROM agg
)

SELECT
  data_date, symbol,
  open, high, low, close, volume, settle, vwap, open_interest,
  instrument_id, exchange, currency, dataset,
  return_1d,
  sma_5, sma_10, sma_20, sma_50, sma_100, sma_200,
  rsi_14,
  macd_line_12_26_9,
  macd_signal_12_26_9,
  macd_line_12_26_9 - macd_signal_12_26_9 AS macd_hist_12_26_9,
  boll_mid_20_2, boll_upper_20_2, boll_lower_20_2, boll_bandwidth_20_2,
  atr_14,
  realized_vol_daily_proxy
FROM macd_final;

