-- ============================================
-- BQML 1W MODEL - PRODUCTION
-- ============================================

-- Drop any existing model with this name to ensure fresh start
DROP MODEL IF EXISTS `cbi-v14.models_v4.bqml_1w`;

-- Create production model
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_1w`

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
    -- Exclude columns that are completely NULL (BQML cannot train with all NULLs)
    social_sentiment_volatility,  -- All NULLs
    bullish_ratio,  -- All NULLs
    bearish_ratio,  -- All NULLs
    social_sentiment_7d,  -- All NULLs
    social_volume_7d,  -- All NULLs
    trump_policy_7d,  -- All NULLs
    trump_events_7d,  -- All NULLs
    news_intelligence_7d,  -- All NULLs
    news_volume_7d  -- All NULLs
  )
  -- ✅ 276 NUMERIC FEATURES (excludes 8 completely NULL columns)
  
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_1w IS NOT NULL;


