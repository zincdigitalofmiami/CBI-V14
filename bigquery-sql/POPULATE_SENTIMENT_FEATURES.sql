-- ============================================
-- POPULATE SENTIMENT FEATURES
-- Join sentiment tables for new dates
-- Date: November 6, 2025
-- ============================================

-- Step 1: Update social sentiment features
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
WHERE t.date = s.date
  AND t.date > '2025-09-10';

-- Step 2: Update news sentiment features
UPDATE `cbi-v14.models_v4.production_training_data_1m` t
SET 
  news_sentiment_avg = n.news_sentiment_avg,
  news_article_count = n.news_article_count,
  news_avg_score = n.news_avg_score,
  news_intelligence_7d = n.news_intelligence_7d,
  news_volume_7d = n.news_volume_7d
FROM `cbi-v14.models_v4.news_intelligence_daily` n
WHERE t.date = n.date
  AND t.date > '2025-09-10';

-- Step 3: Update Trump policy features
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
WHERE t.date = tp.date
  AND t.date > '2025-09-10';

-- Verification
SELECT 
  'Sentiment Features Updated' as status,
  COUNT(*) as total_rows,
  COUNT(CASE WHEN social_sentiment_avg IS NOT NULL THEN 1 END) as has_social_sentiment,
  COUNT(CASE WHEN news_sentiment_avg IS NOT NULL THEN 1 END) as has_news_sentiment,
  COUNT(CASE WHEN trump_policy_impact_max IS NOT NULL THEN 1 END) as has_trump_policy,
  MIN(date) as earliest,
  MAX(date) as latest
FROM `cbi-v14.models_v4.production_training_data_1m`
WHERE date > '2025-09-10';







