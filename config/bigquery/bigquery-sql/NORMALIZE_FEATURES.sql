-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- NORMALIZE FEATURES [-1, 1] AFTER BOOSTING
-- Post-boost standardization to avoid scale dominance
-- Date: November 2025
-- ============================================

-- This creates normalized versions of boosted features
-- Formula: z_score = (feat - mean) / std
-- Then clip to [-1, 1] range

CREATE OR REPLACE TABLE `cbi-v14.models_v4.rich_focused_features_normalized` AS
WITH feature_stats AS (
  SELECT 
    -- Calculate mean and std for each feature
    AVG(trump_policy_events) as mean_trump_policy_events,
    STDDEV(trump_policy_events) as std_trump_policy_events,
    AVG(trade_war_intensity) as mean_trade_war_intensity,
    STDDEV(trade_war_intensity) as std_trade_war_intensity,
    AVG(dollar_index) as mean_dollar_index,
    STDDEV(dollar_index) as std_dollar_index,
    AVG(argentina_export_tax) as mean_argentina_export_tax,
    STDDEV(argentina_export_tax) as std_argentina_export_tax,
    AVG(news_intelligence_7d) as mean_news_intelligence_7d,
    STDDEV(news_intelligence_7d) as std_news_intelligence_7d
  FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
  WHERE date >= '2024-01-01'
    AND target_1m IS NOT NULL
),
normalized_data AS (
  SELECT 
    p.date,
    p.target_1m,
    
    -- Normalize boosted features (post-multiplier)
    -- Trump/Policy (1.4x boost applied, then normalize)
    LEAST(GREATEST(
      (p.trump_policy_events * 1.4 - fs.mean_trump_policy_events * 1.4) / 
      NULLIF(fs.std_trump_policy_events * 1.4, 0),
      -1.0
    ), 1.0) as trump_policy_events_norm,
    
    -- Trade War (1.3x boost applied, then normalize)
    LEAST(GREATEST(
      (p.trade_war_intensity * 1.3 - fs.mean_trade_war_intensity * 1.3) / 
      NULLIF(fs.std_trade_war_intensity * 1.3, 0),
      -1.0
    ), 1.0) as trade_war_intensity_norm,
    
    -- Dollar Index (1.3x boost applied, then normalize)
    LEAST(GREATEST(
      (p.dollar_index * 1.3 - fs.mean_dollar_index * 1.3) / 
      NULLIF(fs.std_dollar_index * 1.3, 0),
      -1.0
    ), 1.0) as dollar_index_norm,
    
    -- Argentina (1.3x boost applied, then normalize)
    LEAST(GREATEST(
      (p.argentina_export_tax * 1.3 - fs.mean_argentina_export_tax * 1.3) / 
      NULLIF(fs.std_argentina_export_tax * 1.3, 0),
      -1.0
    ), 1.0) as argentina_export_tax_norm,
    
    -- News (1.2x boost applied, then normalize)
    LEAST(GREATEST(
      (p.news_intelligence_7d * 1.2 - fs.mean_news_intelligence_7d * 1.2) / 
      NULLIF(fs.std_news_intelligence_7d * 1.2, 0),
      -1.0
    ), 1.0) as news_intelligence_7d_norm
    
  FROM `cbi-v14.training.zl_training_prod_allhistory_1m` p
  CROSS JOIN feature_stats fs
  WHERE p.date >= '2024-01-01'
    AND p.target_1m IS NOT NULL
)
SELECT * FROM normalized_data
LIMIT 100;  -- Sample for validation

-- Summary
SELECT 
  'NORMALIZATION COMPLETE' as status,
  'Features normalized to [-1, 1] after boosting' as note,
  COUNT(*) as rows_normalized
FROM normalized_data;







