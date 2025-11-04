-- ============================================
-- TRAIN 1M MODEL - REVERSE ENGINEERED FROM SUCCESSFUL 1W
-- Uses minimal EXCEPT clause (only truly all-NULL columns)
-- ============================================

DROP MODEL IF EXISTS `cbi-v14.models_v4.bqml_1m_working`;

CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_1m_working`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1m'],
  max_iterations=50,
  learn_rate=0.1,
  early_stop=True
) AS

SELECT 
  target_1m,
  * EXCEPT(
    -- Target columns (exclude others)
    target_1w, 
    target_1m, 
    target_3m, 
    target_6m, 
    
    -- Non-numeric
    date,
    volatility_regime,
    
    -- ALL-NULL columns (verified in 1m dataset)
    social_sentiment_volatility,
    bullish_ratio,
    bearish_ratio,
    social_sentiment_7d,
    social_volume_7d,
    trump_policy_7d,
    trump_events_7d,
    news_intelligence_7d,
    news_volume_7d,
    news_article_count,
    news_avg_score,
    china_news_count,
    biofuel_news_count,
    tariff_news_count,
    weather_news_count,
    news_sentiment_avg
  )
  
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_1m IS NOT NULL;


