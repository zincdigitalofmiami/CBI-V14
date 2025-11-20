-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- CORRELATION TRIMMING
-- Remove highly correlated features (ρ > 0.85) to prevent double-counting
-- Date: November 2025
-- ============================================

-- STEP 1: Calculate correlation matrix for regime-aware features
CREATE OR REPLACE TABLE `cbi-v14.models_v4.feature_correlation_matrix` AS
WITH feature_data AS (
  SELECT 
    date,
    -- Policy/Trade features (check for overlap)
    trump_policy_events,
    trump_policy_impact_avg,
    trade_war_intensity,
    china_policy_events,
    china_policy_impact,
    tariff_news_count,
    feature_tariff_threat,
    
    -- FX features
    dollar_index,
    usd_cny_rate,
    usd_brl_rate,
    fed_funds_rate,
    treasury_10y_yield,
    
    -- Argentina features
    argentina_export_tax,
    argentina_conditions_score,
    
    -- News features
    news_intelligence_7d,
    news_volume_7d,
    news_sentiment_avg
  FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
  WHERE date >= '2024-01-01'
    AND target_1m IS NOT NULL
),
correlations AS (
  SELECT 
    'trump_policy_events' as feature1,
    'trade_war_intensity' as feature2,
    CORR(trump_policy_events, trade_war_intensity) as correlation
  FROM feature_data
  
  UNION ALL
  
  SELECT 
    'trump_policy_events',
    'china_policy_events',
    CORR(trump_policy_events, china_policy_events)
  FROM feature_data
  
  UNION ALL
  
  SELECT 
    'trade_war_intensity',
    'china_policy_impact',
    CORR(trade_war_intensity, china_policy_impact)
  FROM feature_data
  
  UNION ALL
  
  SELECT 
    'tariff_news_count',
    'feature_tariff_threat',
    CORR(tariff_news_count, feature_tariff_threat)
  FROM feature_data
  
  UNION ALL
  
  SELECT 
    'china_policy_events',
    'china_policy_impact',
    CORR(china_policy_events, china_policy_impact)
  FROM feature_data
  
  -- Note: arg_crisis_score is the only Argentina crisis feature (from vw_arg_crisis_score)
  
  UNION ALL
  
  SELECT 
    'news_intelligence_7d',
    'news_volume_7d',
    CORR(news_intelligence_7d, news_volume_7d)
  FROM feature_data
)
SELECT 
  feature1,
  feature2,
  correlation,
  ABS(correlation) as abs_correlation,
  CASE 
    WHEN ABS(correlation) > 0.85 THEN 'DROP'
    WHEN ABS(correlation) > 0.70 THEN 'WARN'
    ELSE 'KEEP'
  END as action
FROM correlations
ORDER BY ABS(correlation) DESC;

-- STEP 2: Create feature exclusion list (high correlation pairs)
CREATE OR REPLACE TABLE `cbi-v14.models_v4.feature_exclusions` AS
WITH high_corr AS (
  SELECT 
    feature1,
    feature2,
    correlation
  FROM `cbi-v14.models_v4.feature_correlation_matrix`
  WHERE ABS(correlation) > 0.85
),
-- Keep the feature with higher importance, drop the other
feature_importance AS (
  SELECT 
    feature,
    combined_score
  FROM `cbi-v14.models_v4.rich_focused_feature_importance`
),
exclusions AS (
  SELECT 
    hc.feature2 as feature_to_drop,
    hc.feature1 as keep_instead,
    hc.correlation,
    fi1.combined_score as score_keep,
    fi2.combined_score as score_drop
  FROM high_corr hc
  LEFT JOIN feature_importance fi1 ON hc.feature1 = fi1.feature
  LEFT JOIN feature_importance fi2 ON hc.feature2 = fi2.feature
  WHERE COALESCE(fi1.combined_score, 0) >= COALESCE(fi2.combined_score, 0)
)
SELECT DISTINCT feature_to_drop as feature
FROM exclusions;

-- STEP 3: Summary
SELECT 
  'CORRELATION TRIMMING COMPLETE' as status,
  COUNT(*) as features_to_exclude,
  'Features with ρ > 0.85 will be excluded from training' as note
FROM `cbi-v14.models_v4.feature_exclusions`;

-- Show high correlation pairs
SELECT 
  feature1,
  feature2,
  ROUND(correlation, 3) as correlation,
  action
FROM `cbi-v14.models_v4.feature_correlation_matrix`
WHERE action IN ('DROP', 'WARN')
ORDER BY ABS(correlation) DESC;

