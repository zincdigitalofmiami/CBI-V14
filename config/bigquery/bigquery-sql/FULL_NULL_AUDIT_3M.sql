-- ============================================
-- FULL NULL AUDIT FOR 3M TRAINING ROWS
-- Check all key columns for NULL status
-- ============================================

SELECT 
  'news_article_count' as column_name,
  COUNTIF(news_article_count IS NULL) as null_count,
  COUNT(*) as total_count,
  CASE WHEN COUNTIF(news_article_count IS NULL) = COUNT(*) THEN 'EXCLUDE' ELSE 'INCLUDE' END as action
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_3m IS NOT NULL

UNION ALL

SELECT 'news_avg_score', COUNTIF(news_avg_score IS NULL), COUNT(*), CASE WHEN COUNTIF(news_avg_score IS NULL) = COUNT(*) THEN 'EXCLUDE' ELSE 'INCLUDE' END
FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_3m IS NOT NULL

UNION ALL

SELECT 'news_sentiment_avg', COUNTIF(news_sentiment_avg IS NULL), COUNT(*), CASE WHEN COUNTIF(news_sentiment_avg IS NULL) = COUNT(*) THEN 'EXCLUDE' ELSE 'INCLUDE' END
FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_3m IS NOT NULL

UNION ALL

SELECT 'china_news_count', COUNTIF(china_news_count IS NULL), COUNT(*), CASE WHEN COUNTIF(china_news_count IS NULL) = COUNT(*) THEN 'EXCLUDE' ELSE 'INCLUDE' END
FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_3m IS NOT NULL

UNION ALL

SELECT 'biofuel_news_count', COUNTIF(biofuel_news_count IS NULL), COUNT(*), CASE WHEN COUNTIF(biofuel_news_count IS NULL) = COUNT(*) THEN 'EXCLUDE' ELSE 'INCLUDE' END
FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_3m IS NOT NULL

UNION ALL

SELECT 'tariff_news_count', COUNTIF(tariff_news_count IS NULL), COUNT(*), CASE WHEN COUNTIF(tariff_news_count IS NULL) = COUNT(*) THEN 'EXCLUDE' ELSE 'INCLUDE' END
FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_3m IS NOT NULL

UNION ALL

SELECT 'weather_news_count', COUNTIF(weather_news_count IS NULL), COUNT(*), CASE WHEN COUNTIF(weather_news_count IS NULL) = COUNT(*) THEN 'EXCLUDE' ELSE 'INCLUDE' END
FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_3m IS NOT NULL

UNION ALL

SELECT 'social_sentiment_volatility', COUNTIF(social_sentiment_volatility IS NULL), COUNT(*), CASE WHEN COUNTIF(social_sentiment_volatility IS NULL) = COUNT(*) THEN 'EXCLUDE' ELSE 'INCLUDE' END
FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_3m IS NOT NULL

UNION ALL

SELECT 'bullish_ratio', COUNTIF(bullish_ratio IS NULL), COUNT(*), CASE WHEN COUNTIF(bullish_ratio IS NULL) = COUNT(*) THEN 'EXCLUDE' ELSE 'INCLUDE' END
FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_3m IS NOT NULL

UNION ALL

SELECT 'bearish_ratio', COUNTIF(bearish_ratio IS NULL), COUNT(*), CASE WHEN COUNTIF(bearish_ratio IS NULL) = COUNT(*) THEN 'EXCLUDE' ELSE 'INCLUDE' END
FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_3m IS NOT NULL

UNION ALL

SELECT 'social_sentiment_7d', COUNTIF(social_sentiment_7d IS NULL), COUNT(*), CASE WHEN COUNTIF(social_sentiment_7d IS NULL) = COUNT(*) THEN 'EXCLUDE' ELSE 'INCLUDE' END
FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_3m IS NOT NULL

UNION ALL

SELECT 'social_volume_7d', COUNTIF(social_volume_7d IS NULL), COUNT(*), CASE WHEN COUNTIF(social_volume_7d IS NULL) = COUNT(*) THEN 'EXCLUDE' ELSE 'INCLUDE' END
FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_3m IS NOT NULL

UNION ALL

SELECT 'trump_policy_7d', COUNTIF(trump_policy_7d IS NULL), COUNT(*), CASE WHEN COUNTIF(trump_policy_7d IS NULL) = COUNT(*) THEN 'EXCLUDE' ELSE 'INCLUDE' END
FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_3m IS NOT NULL

UNION ALL

SELECT 'trump_events_7d', COUNTIF(trump_events_7d IS NULL), COUNT(*), CASE WHEN COUNTIF(trump_events_7d IS NULL) = COUNT(*) THEN 'EXCLUDE' ELSE 'INCLUDE' END
FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_3m IS NOT NULL

UNION ALL

SELECT 'news_intelligence_7d', COUNTIF(news_intelligence_7d IS NULL), COUNT(*), CASE WHEN COUNTIF(news_intelligence_7d IS NULL) = COUNT(*) THEN 'EXCLUDE' ELSE 'INCLUDE' END
FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_3m IS NOT NULL

UNION ALL

SELECT 'news_volume_7d', COUNTIF(news_volume_7d IS NULL), COUNT(*), CASE WHEN COUNTIF(news_volume_7d IS NULL) = COUNT(*) THEN 'EXCLUDE' ELSE 'INCLUDE' END
FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_3m IS NOT NULL

ORDER BY action DESC, column_name;



