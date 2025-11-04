-- Find all columns that are 100% NULL for 6M training rows
SELECT 
  'news_article_count' as col, COUNTIF(news_article_count IS NULL) as nulls, COUNT(*) as total FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_6m IS NOT NULL
UNION ALL SELECT 'news_avg_score', COUNTIF(news_avg_score IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_6m IS NOT NULL
UNION ALL SELECT 'news_sentiment_avg', COUNTIF(news_sentiment_avg IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_6m IS NOT NULL
UNION ALL SELECT 'china_news_count', COUNTIF(china_news_count IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_6m IS NOT NULL
UNION ALL SELECT 'biofuel_news_count', COUNTIF(biofuel_news_count IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_6m IS NOT NULL
UNION ALL SELECT 'tariff_news_count', COUNTIF(tariff_news_count IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_6m IS NOT NULL
UNION ALL SELECT 'weather_news_count', COUNTIF(weather_news_count IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_6m IS NOT NULL
UNION ALL SELECT 'trump_soybean_sentiment_7d', COUNTIF(trump_soybean_sentiment_7d IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_6m IS NOT NULL
UNION ALL SELECT 'trump_agricultural_impact_30d', COUNTIF(trump_agricultural_impact_30d IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_6m IS NOT NULL
UNION ALL SELECT 'trump_soybean_relevance_30d', COUNTIF(trump_soybean_relevance_30d IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_6m IS NOT NULL
UNION ALL SELECT 'days_since_trump_policy', COUNTIF(days_since_trump_policy IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_6m IS NOT NULL
UNION ALL SELECT 'trump_policy_intensity_14d', COUNTIF(trump_policy_intensity_14d IS NULL), COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_6m IS NOT NULL
ORDER BY col;


