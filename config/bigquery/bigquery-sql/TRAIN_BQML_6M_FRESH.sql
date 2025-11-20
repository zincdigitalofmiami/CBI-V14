-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- TRAIN BQML 6M MODEL - FRESH START
-- Same setup as 1W model
-- ============================================

-- Drop any existing model with this name to ensure fresh start
DROP MODEL IF EXISTS `cbi-v14.models_v4.bqml_6m_all_features`;

-- Create fresh model
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_6m_all_features`

OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_6m'],
  max_iterations=100,
  learn_rate=0.1,
  early_stop=False
) AS

SELECT 
  target_6m,
  * EXCEPT(
    target_1w, 
    target_1m, 
    target_3m, 
    target_6m, 
    date,
    volatility_regime,  -- STRING type excluded
    -- EXACT SAME AS ALL MODELS: Exclude ALL columns that are 100% NULL across entire dataset
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
    -- News columns: 100% NULL for 6M (data only exists from 2025-10-04, 6M ends 2025-05-10)
    news_article_count,  -- 100% NULL for 6M
    news_avg_score,  -- 100% NULL for 6M
    news_sentiment_avg,  -- 100% NULL for 6M
    china_news_count,  -- 100% NULL for 6M
    biofuel_news_count,  -- 100% NULL for 6M
    tariff_news_count,  -- 100% NULL for 6M
    weather_news_count,  -- 100% NULL for 6M
    trump_soybean_sentiment_7d,  -- 100% NULL for 6M
    trump_agricultural_impact_30d,  -- 100% NULL for 6M
    trump_soybean_relevance_30d,  -- 100% NULL for 6M
    days_since_trump_policy,  -- 100% NULL for 6M
    trump_policy_intensity_14d,  -- 100% NULL for 6M
    trump_policy_events,  -- 100% NULL for 6M
    trump_policy_impact_avg,  -- 100% NULL for 6M
    trump_policy_impact_max,  -- 100% NULL for 6M
    trade_policy_events,  -- 100% NULL for 6M
    china_policy_events,  -- 100% NULL for 6M
    ag_policy_events  -- 100% NULL for 6M
  )
  -- ✅ 258 NUMERIC FEATURES (excludes 28 columns - 8 standard + 7 news + 11 trump columns)
  
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_6m IS NOT NULL;

