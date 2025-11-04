-- ============================================
-- BACKFILL ALL TECHNICAL INDICATORS
-- One-shot script to populate all missing features
-- ============================================

-- Step 1: Create temp table with all calculations
CREATE TEMP TABLE feature_calculations AS
WITH 
-- Base data with row numbers for window calcs
base AS (
  SELECT 
    date,
    zl_price_current,
    ROW_NUMBER() OVER (ORDER BY date) AS row_num
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE zl_price_current IS NOT NULL
),

-- Calculate 20-day rolling stats for Bollinger Bands
bb_stats AS (
  SELECT 
    date,
    AVG(zl_price_current) OVER w20 AS bb_middle,
    STDDEV(zl_price_current) OVER w20 AS bb_std
  FROM base
  WINDOW w20 AS (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)
),

-- Calculate 90-day MA
ma_90 AS (
  SELECT 
    date,
    AVG(zl_price_current) OVER w90 AS ma_90d
  FROM base
  WINDOW w90 AS (ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW)
),

-- Price changes for RSI
price_changes AS (
  SELECT 
    date,
    zl_price_current - LAG(zl_price_current, 1) OVER (ORDER BY date) AS price_change
  FROM base
),

-- Gains and losses
gains_losses AS (
  SELECT 
    date,
    CASE WHEN price_change > 0 THEN price_change ELSE 0 END AS gain,
    CASE WHEN price_change < 0 THEN ABS(price_change) ELSE 0 END AS loss
  FROM price_changes
),

-- RSI calculation
rsi_calc AS (
  SELECT 
    date,
    AVG(gain) OVER w14 AS avg_gain,
    AVG(loss) OVER w14 AS avg_loss
  FROM gains_losses
  WINDOW w14 AS (ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW)
),

-- EMA approximations for MACD
ema_12_26 AS (
  SELECT 
    date,
    zl_price_current,
    AVG(zl_price_current) OVER w12 AS ema_12,
    AVG(zl_price_current) OVER w26 AS ema_26
  FROM base
  WINDOW 
    w12 AS (ORDER BY date ROWS BETWEEN 11 PRECEDING AND CURRENT ROW),
    w26 AS (ORDER BY date ROWS BETWEEN 25 PRECEDING AND CURRENT ROW)
),

-- MACD line
macd_line_calc AS (
  SELECT 
    date,
    ema_12 - ema_26 AS macd_line
  FROM ema_12_26
),

-- MACD signal (9-day EMA of MACD line)
macd_signal_calc AS (
  SELECT 
    date,
    macd_line,
    AVG(macd_line) OVER w9 AS macd_signal
  FROM macd_line_calc
  WINDOW w9 AS (ORDER BY date ROWS BETWEEN 8 PRECEDING AND CURRENT ROW)
)

-- Combine all calculations
SELECT 
  b.date,
  
  -- Bollinger Bands
  bb.bb_middle,
  bb.bb_middle + (2 * bb.bb_std) AS bb_upper,
  bb.bb_middle - (2 * bb.bb_std) AS bb_lower,
  SAFE_DIVIDE(
    (b.zl_price_current - (bb.bb_middle - (2 * bb.bb_std))),
    ((bb.bb_middle + (2 * bb.bb_std)) - (bb.bb_middle - (2 * bb.bb_std)))
  ) AS bb_percent,
  
  -- MA 90d
  ma.ma_90d,
  
  -- RSI
  CASE 
    WHEN rsi.avg_loss = 0 THEN 100
    WHEN rsi.avg_gain IS NULL OR rsi.avg_loss IS NULL THEN NULL
    ELSE 100 - (100 / (1 + (rsi.avg_gain / rsi.avg_loss)))
  END AS rsi_14,
  
  -- MACD
  macd.macd_line,
  macd.macd_signal,
  macd.macd_line - macd.macd_signal AS macd_histogram

FROM base b
LEFT JOIN bb_stats bb ON b.date = bb.date
LEFT JOIN ma_90 ma ON b.date = ma.date
LEFT JOIN rsi_calc rsi ON b.date = rsi.date
LEFT JOIN macd_signal_calc macd ON b.date = macd.date;

-- Step 2: Update main table with calculated features
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET 
  bb_middle = c.bb_middle,
  bb_upper = c.bb_upper,
  bb_lower = c.bb_lower,
  bb_percent = c.bb_percent,
  ma_90d = c.ma_90d,
  rsi_14 = c.rsi_14,
  macd_line = c.macd_line,
  macd_signal = c.macd_signal,
  macd_histogram = c.macd_histogram
FROM feature_calculations c
WHERE t.date = c.date;

-- Step 3: Verify population
SELECT 
  'bb_middle' AS feature,
  COUNT(*) AS total,
  COUNTIF(bb_middle IS NOT NULL) AS populated,
  ROUND(COUNTIF(bb_middle IS NOT NULL) / COUNT(*) * 100, 2) AS pct
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE zl_price_current IS NOT NULL

UNION ALL

SELECT 'bb_upper', COUNT(*), COUNTIF(bb_upper IS NOT NULL), 
       ROUND(COUNTIF(bb_upper IS NOT NULL) / COUNT(*) * 100, 2)
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE zl_price_current IS NOT NULL

UNION ALL

SELECT 'rsi_14', COUNT(*), COUNTIF(rsi_14 IS NOT NULL), 
       ROUND(COUNTIF(rsi_14 IS NOT NULL) / COUNT(*) * 100, 2)
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE zl_price_current IS NOT NULL

UNION ALL

SELECT 'macd_line', COUNT(*), COUNTIF(macd_line IS NOT NULL), 
       ROUND(COUNTIF(macd_line IS NOT NULL) / COUNT(*) * 100, 2)
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE zl_price_current IS NOT NULL

UNION ALL

SELECT 'ma_90d', COUNT(*), COUNTIF(ma_90d IS NOT NULL), 
       ROUND(COUNTIF(ma_90d IS NOT NULL) / COUNT(*) * 100, 2)
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE zl_price_current IS NOT NULL

ORDER BY feature;

