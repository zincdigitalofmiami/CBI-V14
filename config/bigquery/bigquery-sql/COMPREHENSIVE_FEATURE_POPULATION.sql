-- ============================================
-- COMPREHENSIVE FEATURE POPULATION
-- Master script to populate all complex features for new dates
-- Date: November 6, 2025
-- Target: Sep 11 - Nov 6, 2025 (57 rows)
-- ============================================

-- EXECUTION ORDER:
-- 1. Moving Averages (ma_7d, ma_30d, ma_90d)
-- 2. Crush Margin (crush_margin, crush_margin_7d_ma, crush_margin_30d_ma)
-- 3. Sentiment Features (social, news, trump policy)
-- 4. Technical Indicators (RSI, MACD)

SELECT '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' as separator;
SELECT '🚀 COMPREHENSIVE FEATURE POPULATION - START' as status;
SELECT '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' as separator;

-- ============================================
-- STEP 1: MOVING AVERAGES
-- ============================================
SELECT '' as blank;
SELECT '📊 STEP 1: Calculating Moving Averages...' as status;

UPDATE `cbi-v14.models_v4.production_training_data_1m` t
SET 
  ma_7d = ma_calc.ma_7d,
  ma_30d = ma_calc.ma_30d,
  ma_90d = ma_calc.ma_90d
FROM (
  SELECT 
    date,
    AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as ma_7d,
    AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as ma_30d,
    AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) as ma_90d
  FROM `cbi-v14.models_v4.production_training_data_1m`
  WHERE zl_price_current IS NOT NULL
) ma_calc
WHERE t.date = ma_calc.date AND t.date > '2025-09-10';

SELECT 
  '✅ Moving Averages' as step,
  COUNT(*) as rows_updated,
  COUNT(CASE WHEN ma_7d IS NOT NULL THEN 1 END) as has_ma_7d,
  COUNT(CASE WHEN ma_30d IS NOT NULL THEN 1 END) as has_ma_30d
FROM `cbi-v14.models_v4.production_training_data_1m`
WHERE date > '2025-09-10';

-- ============================================
-- STEP 2: CRUSH MARGIN
-- ============================================
SELECT '' as blank;
SELECT '💰 STEP 2: Calculating Crush Margin...' as status;

UPDATE `cbi-v14.models_v4.production_training_data_1m` t
SET crush_margin = crush_calc.crush_margin
FROM (
  SELECT 
    date,
    (oil_price_per_cwt * 0.11) + (meal_price_per_ton * 0.022) - bean_price_per_bushel as crush_margin
  FROM `cbi-v14.models_v4.production_training_data_1m`
  WHERE bean_price_per_bushel IS NOT NULL
    AND oil_price_per_cwt IS NOT NULL
    AND meal_price_per_ton IS NOT NULL
) crush_calc
WHERE t.date = crush_calc.date AND t.date > '2025-09-10';

UPDATE `cbi-v14.models_v4.production_training_data_1m` t
SET 
  crush_margin_7d_ma = crush_ma.crush_margin_7d_ma,
  crush_margin_30d_ma = crush_ma.crush_margin_30d_ma
FROM (
  SELECT 
    date,
    AVG(crush_margin) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as crush_margin_7d_ma,
    AVG(crush_margin) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as crush_margin_30d_ma
  FROM `cbi-v14.models_v4.production_training_data_1m`
  WHERE crush_margin IS NOT NULL
) crush_ma
WHERE t.date = crush_ma.date AND t.date > '2025-09-10';

SELECT 
  '✅ Crush Margin' as step,
  COUNT(*) as rows_updated,
  COUNT(CASE WHEN crush_margin IS NOT NULL THEN 1 END) as has_crush_margin,
  AVG(crush_margin) as avg_crush_margin
FROM `cbi-v14.models_v4.production_training_data_1m`
WHERE date > '2025-09-10';

-- ============================================
-- STEP 3: SENTIMENT FEATURES
-- ============================================
SELECT '' as blank;
SELECT '🗣️  STEP 3: Updating Sentiment Features...' as status;

UPDATE `cbi-v14.models_v4.production_training_data_1m` t
SET 
  social_sentiment_avg = s.social_sentiment_avg,
  social_sentiment_volatility = s.social_sentiment_volatility,
  social_post_count = s.social_post_count,
  bullish_ratio = s.bullish_ratio,
  bearish_ratio = s.bearish_ratio,
  social_sentiment_7d = s.social_sentiment_7d,
  social_volume_7d = s.social_volume_7d
FROM `cbi-v14.models_v4.social_sentiment_daily` s
WHERE t.date = s.date AND t.date > '2025-09-10';

UPDATE `cbi-v14.models_v4.production_training_data_1m` t
SET 
  news_sentiment_avg = n.news_sentiment_avg,
  news_article_count = n.news_article_count,
  news_avg_score = n.news_avg_score,
  news_intelligence_7d = n.news_intelligence_7d,
  news_volume_7d = n.news_volume_7d
FROM `cbi-v14.models_v4.news_intelligence_daily` n
WHERE t.date = n.date AND t.date > '2025-09-10';

UPDATE `cbi-v14.models_v4.production_training_data_1m` t
SET 
  trump_policy_events = tp.trump_policy_events,
  trump_policy_impact_avg = tp.trump_policy_impact_avg,
  trump_policy_impact_max = tp.trump_policy_impact_max,
  trade_policy_events = tp.trade_policy_events,
  china_policy_events = tp.china_policy_events,
  ag_policy_events = tp.ag_policy_events,
  trump_policy_7d = tp.trump_policy_7d,
  trump_events_7d = tp.trump_events_7d
FROM `cbi-v14.models_v4.trump_policy_daily` tp
WHERE t.date = tp.date AND t.date > '2025-09-10';

SELECT 
  '✅ Sentiment Features' as step,
  COUNT(*) as total_rows,
  COUNT(CASE WHEN social_sentiment_avg IS NOT NULL THEN 1 END) as has_social,
  COUNT(CASE WHEN news_sentiment_avg IS NOT NULL THEN 1 END) as has_news,
  COUNT(CASE WHEN trump_policy_impact_max IS NOT NULL THEN 1 END) as has_trump
FROM `cbi-v14.models_v4.production_training_data_1m`
WHERE date > '2025-09-10';

-- ============================================
-- STEP 4: TECHNICAL INDICATORS
-- ============================================
SELECT '' as blank;
SELECT '📈 STEP 4: Recalculating Technical Indicators...' as status;

WITH price_data AS (
  SELECT 
    date,
    zl_price_current,
    LAG(zl_price_current, 1) OVER (ORDER BY date) AS prev_price
  FROM `cbi-v14.models_v4.production_training_data_1m`
  WHERE zl_price_current IS NOT NULL
),
rsi_calc AS (
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
  FROM rsi_calc
),
rsi_final AS (
  SELECT 
    date,
    CASE WHEN avg_loss = 0 THEN 100 ELSE 100 - (100 / (1 + (avg_gain / NULLIF(avg_loss, 0)))) END AS rsi_14
  FROM rsi_smoothed
),
macd_calc AS (
  SELECT 
    date,
    AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) AS ema_12,
    AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 25 PRECEDING AND CURRENT ROW) AS ema_26
  FROM price_data
),
macd_final AS (
  SELECT 
    date,
    ema_12 - ema_26 AS macd_line,
    (ema_12 - ema_26) - AVG(ema_12 - ema_26) OVER (ORDER BY date ROWS BETWEEN 8 PRECEDING AND CURRENT ROW) AS macd_signal
  FROM macd_calc
)

UPDATE `cbi-v14.models_v4.production_training_data_1m` t
SET 
  rsi_14 = COALESCE(r.rsi_14, t.rsi_14),
  macd_line = COALESCE(m.macd_line, t.macd_line),
  macd_signal = COALESCE(m.macd_signal, t.macd_signal),
  macd_histogram = COALESCE(m.macd_line - m.macd_signal, t.macd_histogram)
FROM rsi_final r
FULL OUTER JOIN macd_final m ON r.date = m.date
WHERE t.date = COALESCE(r.date, m.date) AND t.date > '2025-09-10';

SELECT 
  '✅ Technical Indicators' as step,
  COUNT(*) as rows_updated,
  COUNT(CASE WHEN rsi_14 IS NOT NULL THEN 1 END) as has_rsi,
  AVG(rsi_14) as avg_rsi
FROM `cbi-v14.models_v4.production_training_data_1m`
WHERE date > '2025-09-10';

-- ============================================
-- FINAL VERIFICATION
-- ============================================
SELECT '' as blank;
SELECT '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' as separator;
SELECT '✅ COMPREHENSIVE FEATURE POPULATION - COMPLETE' as status;
SELECT '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' as separator;

SELECT 
  COUNT(*) as total_new_rows,
  COUNT(CASE WHEN ma_7d IS NOT NULL THEN 1 END) as has_ma_7d,
  COUNT(CASE WHEN crush_margin IS NOT NULL THEN 1 END) as has_crush_margin,
  COUNT(CASE WHEN social_sentiment_avg IS NOT NULL THEN 1 END) as has_social_sentiment,
  COUNT(CASE WHEN news_sentiment_avg IS NOT NULL THEN 1 END) as has_news_sentiment,
  COUNT(CASE WHEN rsi_14 IS NOT NULL THEN 1 END) as has_rsi,
  MIN(date) as earliest_date,
  MAX(date) as latest_date
FROM `cbi-v14.models_v4.production_training_data_1m`
WHERE date > '2025-09-10';







