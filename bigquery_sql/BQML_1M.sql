-- ============================================
-- BQML 1M MODEL - PRODUCTION
-- ============================================

-- Drop any existing model with this name to ensure fresh start
DROP MODEL IF EXISTS `cbi-v14.models_v4.bqml_1m`;

-- Create production model
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_1m`

OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1m'],
  max_iterations=100,
  learn_rate=0.1,
  early_stop=False
) AS

SELECT 
  target_1m,
  * EXCEPT(
    target_1w, 
    target_1m, 
    target_3m, 
    target_6m, 
    date,
    volatility_regime,  -- STRING type excluded
    -- Exclude columns that are completely NULL (BQML cannot train with all NULLs)
    -- Based on FULL_NULL_AUDIT_1M.sql audit
    social_sentiment_volatility,  -- 100% NULL (1347/1347)
    news_article_count,  -- 100% NULL (1347/1347)
    news_avg_score,  -- 100% NULL (1347/1347)
    news_sentiment_avg,  -- 100% NULL (1347/1347)
    china_news_count,  -- 100% NULL (1347/1347)
    biofuel_news_count,  -- 100% NULL (1347/1347)
    tariff_news_count,  -- 100% NULL (1347/1347)
    weather_news_count,  -- 100% NULL (1347/1347)
    news_intelligence_7d,  -- 100% NULL (1347/1347)
    news_volume_7d  -- 100% NULL (1347/1347)
    -- Note: bullish_ratio, bearish_ratio, social_sentiment_7d, social_volume_7d have data (only 5 NULLs each)
    -- Note: trump_policy_7d, trump_events_7d have partial data (110 rows)
  )
  -- ✅ 274 NUMERIC FEATURES (excludes 10 completely NULL columns)
  
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_1m IS NOT NULL;

