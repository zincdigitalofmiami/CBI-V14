-- ============================================
-- COMPREHENSIVE NULL CHECK FOR 1M TRAINING
-- Find ALL columns that are 100% NULL
-- ============================================

WITH column_list AS (
  SELECT column_name
  FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
  WHERE table_name = 'training_dataset_super_enriched'
    AND data_type IN ('FLOAT64', 'INT64')
    AND column_name NOT IN ('target_1w', 'target_1m', 'target_3m', 'target_6m')
),
null_checks AS (
  SELECT 
    'news_article_count' as col, COUNTIF(news_article_count IS NULL) as nulls, COUNT(*) as total FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'news_avg_score', COUNTIF(news_avg_score IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'news_sentiment_avg', COUNTIF(news_sentiment_avg IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'china_news_count', COUNTIF(china_news_count IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'biofuel_news_count', COUNTIF(biofuel_news_count IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'tariff_news_count', COUNTIF(tariff_news_count IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'weather_news_count', COUNTIF(weather_news_count IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'news_intelligence_7d', COUNTIF(news_intelligence_7d IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'news_volume_7d', COUNTIF(news_volume_7d IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'social_sentiment_avg', COUNTIF(social_sentiment_avg IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'social_sentiment_volatility', COUNTIF(social_sentiment_volatility IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'social_post_count', COUNTIF(social_post_count IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'bullish_ratio', COUNTIF(bullish_ratio IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'bearish_ratio', COUNTIF(bearish_ratio IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'social_sentiment_7d', COUNTIF(social_sentiment_7d IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'social_volume_7d', COUNTIF(social_volume_7d IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'trump_policy_events', COUNTIF(trump_policy_events IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'trump_policy_impact_avg', COUNTIF(trump_policy_impact_avg IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'trump_policy_impact_max', COUNTIF(trump_policy_impact_max IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'trade_policy_events', COUNTIF(trade_policy_events IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'china_policy_events', COUNTIF(china_policy_events IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'ag_policy_events', COUNTIF(ag_policy_events IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'trump_policy_7d', COUNTIF(trump_policy_7d IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'trump_events_7d', COUNTIF(trump_events_7d IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'cftc_commercial_long', COUNTIF(cftc_commercial_long IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'cftc_commercial_short', COUNTIF(cftc_commercial_short IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'cftc_managed_long', COUNTIF(cftc_managed_long IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'cftc_managed_short', COUNTIF(cftc_managed_short IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'cftc_open_interest', COUNTIF(cftc_open_interest IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'cftc_commercial_net', COUNTIF(cftc_commercial_net IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'cftc_managed_net', COUNTIF(cftc_managed_net IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'cftc_commercial_extreme', COUNTIF(cftc_commercial_extreme IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'cftc_spec_extreme', COUNTIF(cftc_spec_extreme IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'soybean_weekly_sales', COUNTIF(soybean_weekly_sales IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'soybean_oil_weekly_sales', COUNTIF(soybean_oil_weekly_sales IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'soybean_meal_weekly_sales', COUNTIF(soybean_meal_weekly_sales IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
  UNION ALL SELECT 'china_soybean_sales', COUNTIF(china_soybean_sales IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL
)
SELECT 
  col as column_name,
  nulls,
  total,
  ROUND(nulls / total * 100, 1) as null_pct,
  CASE 
    WHEN nulls = total THEN '❌ EXCLUDE - 100% NULL'
    WHEN nulls / total > 0.95 THEN '⚠️ WARNING - >95% NULL'
    ELSE '✅ INCLUDE'
  END as status
FROM null_checks
WHERE nulls = total OR nulls / total > 0.95
ORDER BY null_pct DESC, col;



