-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- BQML 3M MODEL - PRODUCTION
-- ============================================

-- Drop any existing model with this name to ensure fresh start
DROP MODEL IF EXISTS `cbi-v14.models_v4.bqml_3m`;

-- Create production model
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_3m`

OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_3m'],
  max_iterations=100,
  learn_rate=0.1,
  early_stop=False
) AS

SELECT 
  target_3m,
  * EXCEPT(
    target_1w, 
    target_1m, 
    target_3m, 
    target_6m, 
    date,
    volatility_regime,  -- STRING type excluded
    -- EXACT SAME AS 1W MODEL: Exclude only columns that are completely NULL
    social_sentiment_volatility,  -- All NULLs
    bullish_ratio,  -- All NULLs
    bearish_ratio,  -- All NULLs
    social_sentiment_7d,  -- All NULLs
    social_volume_7d,  -- All NULLs
    trump_policy_7d,  -- All NULLs
    trump_events_7d,  -- All NULLs
    news_intelligence_7d,  -- All NULLs
    news_volume_7d,  -- All NULLs
    -- News columns: 100% NULL for 3M (data only exists from 2025-10-04, 3M ends 2025-08-13)
    news_article_count,  -- 100% NULL for 3M
    news_avg_score,  -- 100% NULL for 3M
    news_sentiment_avg,  -- 100% NULL for 3M
    china_news_count,  -- 100% NULL for 3M
    biofuel_news_count,  -- 100% NULL for 3M
    tariff_news_count,  -- 100% NULL for 3M
    weather_news_count,  -- 100% NULL for 3M
    trump_soybean_sentiment_7d  -- 100% NULL for 3M
  )
  -- ✅ 268 NUMERIC FEATURES (excludes 18 columns - 8 standard + 7 news + 1 trump_soybean)
  
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_3m IS NOT NULL;


