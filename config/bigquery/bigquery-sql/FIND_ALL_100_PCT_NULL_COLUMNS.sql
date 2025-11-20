-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- FIND ALL 100% NULL COLUMNS ACROSS ENTIRE DATASET
-- ============================================
-- Purpose: Identify ALL columns that are 100% NULL so we can exclude them from ALL models
-- This ensures all 4 models use EXACTLY THE SAME features
-- ============================================

WITH column_stats AS (
  SELECT 
    column_name,
    COUNT(*) as total_rows,
    COUNTIF(value IS NULL) as null_count,
    ROUND(COUNTIF(value IS NULL) / COUNT(*) * 100, 2) as null_pct
  FROM 
    `cbi-v14.models_v4.training_dataset_super_enriched` t,
    UNNEST(REGEXP_EXTRACT_ALL(TO_JSON_STRING(t), r'"([^"]+)"\s*:\s*null')) as null_column
  GROUP BY column_name
  
  UNION ALL
  
  -- Check each column individually
  SELECT 
    'social_sentiment_volatility' as column_name,
    COUNT(*) as total_rows,
    COUNTIF(social_sentiment_volatility IS NULL) as null_count,
    ROUND(COUNTIF(social_sentiment_volatility IS NULL) / COUNT(*) * 100, 2) as null_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'bullish_ratio' as column_name,
    COUNT(*) as total_rows,
    COUNTIF(bullish_ratio IS NULL) as null_count,
    ROUND(COUNTIF(bullish_ratio IS NULL) / COUNT(*) * 100, 2) as null_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'bearish_ratio' as column_name,
    COUNT(*) as total_rows,
    COUNTIF(bearish_ratio IS NULL) as null_count,
    ROUND(COUNTIF(bearish_ratio IS NULL) / COUNT(*) * 100, 2) as null_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'social_sentiment_7d' as column_name,
    COUNT(*) as total_rows,
    COUNTIF(social_sentiment_7d IS NULL) as null_count,
    ROUND(COUNTIF(social_sentiment_7d IS NULL) / COUNT(*) * 100, 2) as null_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'social_volume_7d' as column_name,
    COUNT(*) as total_rows,
    COUNTIF(social_volume_7d IS NULL) as null_count,
    ROUND(COUNTIF(social_volume_7d IS NULL) / COUNT(*) * 100, 2) as null_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'trump_policy_7d' as column_name,
    COUNT(*) as total_rows,
    COUNTIF(trump_policy_7d IS NULL) as null_count,
    ROUND(COUNTIF(trump_policy_7d IS NULL) / COUNT(*) * 100, 2) as null_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'trump_events_7d' as column_name,
    COUNT(*) as total_rows,
    COUNTIF(trump_events_7d IS NULL) as null_count,
    ROUND(COUNTIF(trump_events_7d IS NULL) / COUNT(*) * 100, 2) as null_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'news_intelligence_7d' as column_name,
    COUNT(*) as total_rows,
    COUNTIF(news_intelligence_7d IS NULL) as null_count,
    ROUND(COUNTIF(news_intelligence_7d IS NULL) / COUNT(*) * 100, 2) as null_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'news_volume_7d' as column_name,
    COUNT(*) as total_rows,
    COUNTIF(news_volume_7d IS NULL) as null_count,
    ROUND(COUNTIF(news_volume_7d IS NULL) / COUNT(*) * 100, 2) as null_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'news_article_count' as column_name,
    COUNT(*) as total_rows,
    COUNTIF(news_article_count IS NULL) as null_count,
    ROUND(COUNTIF(news_article_count IS NULL) / COUNT(*) * 100, 2) as null_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'news_avg_score' as column_name,
    COUNT(*) as total_rows,
    COUNTIF(news_avg_score IS NULL) as null_count,
    ROUND(COUNTIF(news_avg_score IS NULL) / COUNT(*) * 100, 2) as null_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'news_sentiment_avg' as column_name,
    COUNT(*) as total_rows,
    COUNTIF(news_sentiment_avg IS NULL) as null_count,
    ROUND(COUNTIF(news_sentiment_avg IS NULL) / COUNT(*) * 100, 2) as null_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'china_news_count' as column_name,
    COUNT(*) as total_rows,
    COUNTIF(china_news_count IS NULL) as null_count,
    ROUND(COUNTIF(china_news_count IS NULL) / COUNT(*) * 100, 2) as null_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'biofuel_news_count' as column_name,
    COUNT(*) as total_rows,
    COUNTIF(biofuel_news_count IS NULL) as null_count,
    ROUND(COUNTIF(biofuel_news_count IS NULL) / COUNT(*) * 100, 2) as null_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'tariff_news_count' as column_name,
    COUNT(*) as total_rows,
    COUNTIF(tariff_news_count IS NULL) as null_count,
    ROUND(COUNTIF(tariff_news_count IS NULL) / COUNT(*) * 100, 2) as null_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'weather_news_count' as column_name,
    COUNT(*) as total_rows,
    COUNTIF(weather_news_count IS NULL) as null_count,
    ROUND(COUNTIF(weather_news_count IS NULL) / COUNT(*) * 100, 2) as null_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'trump_soybean_sentiment_7d' as column_name,
    COUNT(*) as total_rows,
    COUNTIF(trump_soybean_sentiment_7d IS NULL) as null_count,
    ROUND(COUNTIF(trump_soybean_sentiment_7d IS NULL) / COUNT(*) * 100, 2) as null_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'trump_agricultural_impact_30d' as column_name,
    COUNT(*) as total_rows,
    COUNTIF(trump_agricultural_impact_30d IS NULL) as null_count,
    ROUND(COUNTIF(trump_agricultural_impact_30d IS NULL) / COUNT(*) * 100, 2) as null_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'trump_soybean_relevance_30d' as column_name,
    COUNT(*) as total_rows,
    COUNTIF(trump_soybean_relevance_30d IS NULL) as null_count,
    ROUND(COUNTIF(trump_soybean_relevance_30d IS NULL) / COUNT(*) * 100, 2) as null_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'days_since_trump_policy' as column_name,
    COUNT(*) as total_rows,
    COUNTIF(days_since_trump_policy IS NULL) as null_count,
    ROUND(COUNTIF(days_since_trump_policy IS NULL) / COUNT(*) * 100, 2) as null_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'trump_policy_intensity_14d' as column_name,
    COUNT(*) as total_rows,
    COUNTIF(trump_policy_intensity_14d IS NULL) as null_count,
    ROUND(COUNTIF(trump_policy_intensity_14d IS NULL) / COUNT(*) * 100, 2) as null_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'trump_policy_events' as column_name,
    COUNT(*) as total_rows,
    COUNTIF(trump_policy_events IS NULL) as null_count,
    ROUND(COUNTIF(trump_policy_events IS NULL) / COUNT(*) * 100, 2) as null_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'trump_policy_impact_avg' as column_name,
    COUNT(*) as total_rows,
    COUNTIF(trump_policy_impact_avg IS NULL) as null_count,
    ROUND(COUNTIF(trump_policy_impact_avg IS NULL) / COUNT(*) * 100, 2) as null_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'trump_policy_impact_max' as column_name,
    COUNT(*) as total_rows,
    COUNTIF(trump_policy_impact_max IS NULL) as null_count,
    ROUND(COUNTIF(trump_policy_impact_max IS NULL) / COUNT(*) * 100, 2) as null_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'trade_policy_events' as column_name,
    COUNT(*) as total_rows,
    COUNTIF(trade_policy_events IS NULL) as null_count,
    ROUND(COUNTIF(trade_policy_events IS NULL) / COUNT(*) * 100, 2) as null_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'china_policy_events' as column_name,
    COUNT(*) as total_rows,
    COUNTIF(china_policy_events IS NULL) as null_count,
    ROUND(COUNTIF(china_policy_events IS NULL) / COUNT(*) * 100, 2) as null_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'ag_policy_events' as column_name,
    COUNT(*) as total_rows,
    COUNTIF(ag_policy_events IS NULL) as null_count,
    ROUND(COUNTIF(ag_policy_events IS NULL) / COUNT(*) * 100, 2) as null_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
)
SELECT 
  column_name,
  total_rows,
  null_count,
  null_pct,
  CASE 
    WHEN null_pct = 100.0 THEN '✅ EXCLUDE FROM ALL MODELS'
    WHEN null_pct >= 95.0 THEN '⚠️ WARNING: High NULL rate'
    ELSE '✅ KEEP'
  END as recommendation
FROM column_stats
WHERE null_pct = 100.0  -- Only show 100% NULL columns
ORDER BY column_name;

