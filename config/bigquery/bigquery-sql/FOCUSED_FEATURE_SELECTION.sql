-- ============================================
-- FOCUSED FEATURE SELECTION (50-100 Features)
-- Optimize training with top-performing features
-- Date: November 2025
-- ============================================

-- STEP 1: Extract feature importance from existing models
-- This gives us data-driven feature rankings
CREATE OR REPLACE TABLE `cbi-v14.models_v4.focused_feature_importance` AS
WITH importance_1w AS (
  SELECT 
    feature,
    importance_gain,
    importance_cover,
    importance_weight,
    '1w' as horizon
  FROM ML.FEATURE_IMPORTANCE(MODEL `cbi-v14.models_v4.bqml_1w`)
),
importance_1m AS (
  SELECT 
    feature,
    importance_gain,
    importance_cover,
    importance_weight,
    '1m' as horizon
  FROM ML.FEATURE_IMPORTANCE(MODEL `cbi-v14.models_v4.bqml_1m`)
),
importance_3m AS (
  SELECT 
    feature,
    importance_gain,
    importance_cover,
    importance_weight,
    '3m' as horizon
  FROM ML.FEATURE_IMPORTANCE(MODEL `cbi-v14.models_v4.bqml_3m`)
),
importance_6m AS (
  SELECT 
    feature,
    importance_gain,
    importance_cover,
    importance_weight,
    '6m' as horizon
  FROM ML.FEATURE_IMPORTANCE(MODEL `cbi-v14.models_v4.bqml_6m`)
),
all_importance AS (
  SELECT * FROM importance_1w
  UNION ALL SELECT * FROM importance_1m
  UNION ALL SELECT * FROM importance_3m
  UNION ALL SELECT * FROM importance_6m
),
aggregated_importance AS (
  SELECT 
    feature,
    AVG(importance_gain) as avg_importance_gain,
    AVG(importance_cover) as avg_importance_cover,
    AVG(importance_weight) as avg_importance_weight,
    COUNT(DISTINCT horizon) as horizons_appearing,
    -- Combined score (weighted average)
    (AVG(importance_gain) * 0.5 + 
     AVG(importance_cover) * 0.3 + 
     AVG(importance_weight) * 0.2) as combined_score
  FROM all_importance
  GROUP BY feature
)
SELECT 
  feature,
  avg_importance_gain,
  avg_importance_cover,
  avg_importance_weight,
  combined_score,
  horizons_appearing,
  ROW_NUMBER() OVER (ORDER BY combined_score DESC) as rank_by_importance
FROM aggregated_importance
ORDER BY combined_score DESC;

-- STEP 2: Create focused feature list (Top 75 features)
-- This balances performance with model complexity
CREATE OR REPLACE TABLE `cbi-v14.models_v4.focused_feature_list` AS
WITH top_features AS (
  SELECT feature
  FROM `cbi-v14.models_v4.focused_feature_importance`
  WHERE rank_by_importance <= 75
),
-- Always include these critical features (even if not in top 75)
-- PRIORITY: Rich regime-aware features for current market dynamics
critical_features AS (
  -- Price mechanics (essential)
  SELECT 'zl_price_current' as feature
  UNION ALL SELECT 'zl_price_lag1'
  UNION ALL SELECT 'zl_price_lag7'
  UNION ALL SELECT 'return_1d'
  UNION ALL SELECT 'return_7d'
  UNION ALL SELECT 'ma_7d'
  UNION ALL SELECT 'ma_30d'
  
  -- Core fundamentals
  UNION ALL SELECT 'crush_margin'
  UNION ALL SELECT 'china_soybean_imports_mt'
  UNION ALL SELECT 'crude_price'
  UNION ALL SELECT 'palm_price'
  UNION ALL SELECT 'vix_level'
  
  -- Big 8 signals
  UNION ALL SELECT 'feature_vix_stress'
  UNION ALL SELECT 'feature_tariff_threat'
  UNION ALL SELECT 'feature_biofuel_cascade'
  UNION ALL SELECT 'feature_china_relations'
  UNION ALL SELECT 'feature_harvest_pace'
  UNION ALL SELECT 'feature_geopolitical_volatility'
  UNION ALL SELECT 'big8_composite_score'
  
  -- FX/RATES (RICH - User Priority #1)
  UNION ALL SELECT 'dollar_index'
  UNION ALL SELECT 'usd_cny_rate'
  UNION ALL SELECT 'usd_brl_rate'
  UNION ALL SELECT 'usd_ars_rate'
  UNION ALL SELECT 'dollar_index_7d_change'
  UNION ALL SELECT 'fed_funds_rate'
  UNION ALL SELECT 'treasury_10y_yield'
  UNION ALL SELECT 'real_yield'
  UNION ALL SELECT 'yield_curve'
  
  -- TRUMP POLICY (RICH - User Priority #2)
  UNION ALL SELECT 'trump_policy_events'
  UNION ALL SELECT 'trump_policy_impact_avg'
  UNION ALL SELECT 'trump_policy_impact_max'
  UNION ALL SELECT 'trump_policy_7d'
  UNION ALL SELECT 'trump_events_7d'
  UNION ALL SELECT 'trump_policy_intensity_14d'
  UNION ALL SELECT 'trump_soybean_sentiment_7d'
  UNION ALL SELECT 'trump_agricultural_impact_30d'
  UNION ALL SELECT 'days_since_trump_policy'
  
  -- ICE/TRUMP INTELLIGENCE (RICH - User Priority #3)
  UNION ALL SELECT 'ice_trump_policy_score'
  UNION ALL SELECT 'ice_trump_agricultural_mentions'
  UNION ALL SELECT 'ice_trump_trade_mentions'
  UNION ALL SELECT 'ice_trump_executive_orders'
  UNION ALL SELECT 'ice_trump_company_deals'
  UNION ALL SELECT 'ice_trump_country_deals'
  
  -- TARIFFS/TRADE WAR (RICH - User Priority #4)
  UNION ALL SELECT 'trade_war_intensity'
  UNION ALL SELECT 'trade_war_impact_score'
  UNION ALL SELECT 'china_tariff_rate'
  UNION ALL SELECT 'tradewar_event_vol_mult'
  UNION ALL SELECT 'china_policy_events'
  UNION ALL SELECT 'china_policy_impact'
  
  -- ARGENTINA EVENTS (RICH - User Priority #5)
  UNION ALL SELECT 'argentina_export_tax'
  UNION ALL SELECT 'argentina_china_sales_mt'
  UNION ALL SELECT 'argentina_port_congestion'
  UNION ALL SELECT 'argentina_vessel_queue'
  UNION ALL SELECT 'argentina_crisis_score'
  
  -- RECENT EVENTS / REGIME AWARENESS (RICH - User Priority #6)
  UNION ALL SELECT 'news_intelligence_7d'
  UNION ALL SELECT 'news_volume_7d'
  UNION ALL SELECT 'news_sentiment_avg'
  UNION ALL SELECT 'china_news_count'
  UNION ALL SELECT 'tariff_news_count'
  UNION ALL SELECT 'biofuel_news_count'
  UNION ALL SELECT 'weather_news_count'
  
  -- Correlations (regime-aware)
  UNION ALL SELECT 'corr_zl_vix_7d'
  UNION ALL SELECT 'corr_zl_vix_30d'
  UNION ALL SELECT 'corr_zl_palm_7d'
  UNION ALL SELECT 'corr_zl_crude_7d'
  UNION ALL SELECT 'corr_zl_dxy_7d'
),
combined_features AS (
  SELECT DISTINCT feature FROM top_features
  UNION ALL
  SELECT DISTINCT feature FROM critical_features
)
SELECT 
  feature,
  ROW_NUMBER() OVER (ORDER BY feature) as feature_id
FROM combined_features
ORDER BY feature;

-- STEP 3: Verify feature availability in production tables
CREATE OR REPLACE TABLE `cbi-v14.models_v4.focused_feature_availability` AS
WITH feature_list AS (
  SELECT feature FROM `cbi-v14.models_v4.focused_feature_list`
),
schema_1w AS (
  SELECT column_name as feature
  FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
  WHERE table_name = 'zl_training_prod_allhistory_1w'
    AND column_name NOT IN ('date', 'target_1w', 'target_1m', 'target_3m', 'target_6m')
),
schema_1m AS (
  SELECT column_name as feature
  FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
  WHERE table_name = 'zl_training_prod_allhistory_1m'
    AND column_name NOT IN ('date', 'target_1w', 'target_1m', 'target_3m', 'target_6m')
),
schema_3m AS (
  SELECT column_name as feature
  FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
  WHERE table_name = 'zl_training_prod_allhistory_3m'
    AND column_name NOT IN ('date', 'target_1w', 'target_1m', 'target_3m', 'target_6m')
),
schema_6m AS (
  SELECT column_name as feature
  FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
  WHERE table_name = 'zl_training_prod_allhistory_6m'
    AND column_name NOT IN ('date', 'target_1w', 'target_1m', 'target_3m', 'target_6m')
)
SELECT 
  fl.feature,
  CASE WHEN s1w.feature IS NOT NULL THEN TRUE ELSE FALSE END as available_1w,
  CASE WHEN s1m.feature IS NOT NULL THEN TRUE ELSE FALSE END as available_1m,
  CASE WHEN s3m.feature IS NOT NULL THEN TRUE ELSE FALSE END as available_3m,
  CASE WHEN s6m.feature IS NOT NULL THEN TRUE ELSE FALSE END as available_6m
FROM feature_list fl
LEFT JOIN schema_1w s1w ON fl.feature = s1w.feature
LEFT JOIN schema_1m s1m ON fl.feature = s1m.feature
LEFT JOIN schema_3m s3m ON fl.feature = s3m.feature
LEFT JOIN schema_6m s6m ON fl.feature = s6m.feature;

-- STEP 4: Get final focused feature list (only available features)
CREATE OR REPLACE TABLE `cbi-v14.models_v4.focused_feature_list_final` AS
SELECT 
  feature,
  available_1w,
  available_1m,
  available_3m,
  available_6m
FROM `cbi-v14.models_v4.focused_feature_availability`
WHERE available_1w = TRUE  -- Start with 1w, then adapt for others
ORDER BY feature;

-- STEP 5: Summary report
SELECT 
  'FOCUSED FEATURE SELECTION COMPLETE' as status,
  COUNT(*) as total_features_selected,
  SUM(CASE WHEN available_1w THEN 1 ELSE 0 END) as available_1w,
  SUM(CASE WHEN available_1m THEN 1 ELSE 0 END) as available_1m,
  SUM(CASE WHEN available_3m THEN 1 ELSE 0 END) as available_3m,
  SUM(CASE WHEN available_6m THEN 1 ELSE 0 END) as available_6m
FROM `cbi-v14.models_v4.focused_feature_availability`;

