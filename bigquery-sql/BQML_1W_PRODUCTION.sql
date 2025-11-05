-- ============================================
-- TRAIN BQML 1W MODEL - PRODUCTION
-- All models use identical configuration: 258 features, 100 iterations
-- ============================================

-- Drop any existing model with this name to ensure fresh start
DROP MODEL IF EXISTS `cbi-v14.models_v4.bqml_1w_all_features`;

-- Create fresh model
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_1w_all_features`

OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1w'],
  max_iterations=100,
  learn_rate=0.1,
  early_stop=False
) AS

SELECT 
  target_1w,
  * EXCEPT(
    target_1w, 
    target_1m, 
    target_3m, 
    target_6m, 
    date,
    volatility_regime,  -- STRING type excluded
    -- EXACT SAME AS 6M MODEL: Exclude ALL columns that are 100% NULL across entire dataset
    -- This ensures ALL 4 models use EXACTLY THE SAME features (258 features)
    social_sentiment_volatility,  -- All NULLs
    bullish_ratio,  -- All NULLs
    bearish_ratio,  -- All NULLs
    social_sentiment_7d,  -- All NULLs
    social_volume_7d,  -- All NULLs
    trump_policy_7d,  -- All NULLs
    trump_events_7d,  -- All NULLs
    news_intelligence_7d,  -- All NULLs
    news_volume_7d,  -- All NULLs
    -- News columns: 100% NULL
    news_article_count,  -- 100% NULL
    news_avg_score,  -- 100% NULL
    news_sentiment_avg,  -- 100% NULL
    china_news_count,  -- 100% NULL
    biofuel_news_count,  -- 100% NULL
    tariff_news_count,  -- 100% NULL
    weather_news_count,  -- 100% NULL
    trump_soybean_sentiment_7d,  -- 100% NULL
    trump_agricultural_impact_30d,  -- 100% NULL
    trump_soybean_relevance_30d,  -- 100% NULL
    days_since_trump_policy,  -- 100% NULL
    trump_policy_intensity_14d,  -- 100% NULL
    trump_policy_events,  -- 100% NULL
    trump_policy_impact_avg,  -- 100% NULL
    trump_policy_impact_max,  -- 100% NULL
    trade_policy_events,  -- 100% NULL
    china_policy_events,  -- 100% NULL
    ag_policy_events  -- 100% NULL
  )
  -- ✅ 258 NUMERIC FEATURES (excludes 28 columns - EXACTLY THE SAME AS ALL OTHER MODELS)
  
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_1w IS NOT NULL;

