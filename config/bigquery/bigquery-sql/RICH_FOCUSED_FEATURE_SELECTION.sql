-- ============================================
-- RICH FOCUSED FEATURE SELECTION
-- Maximum impact with regime-aware features
-- Prioritizes: FX, Trump policy, ICE, Argentina, tariffs, recent events
-- Date: November 2025
-- ============================================

-- STEP 1: Extract feature importance from existing models
CREATE OR REPLACE TABLE `cbi-v14.models_v4.rich_focused_feature_importance` AS
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
),
-- Boost features that match user priorities (regime-aware)
priority_boost AS (
  SELECT 
    ai.feature,
    ai.avg_importance_gain,
    ai.avg_importance_cover,
    ai.avg_importance_weight,
    ai.combined_score,
    ai.horizons_appearing,
    -- Boost regime-aware features
    CASE 
      -- FX features (high priority) - add 2Y diff if needed
      WHEN ai.feature LIKE '%usd_%' OR ai.feature LIKE '%dollar%' OR ai.feature LIKE '%fx%' 
           OR ai.feature LIKE '%rate%' OR ai.feature LIKE '%yield%' 
           OR ai.feature LIKE '%usdeur2y%'  -- 2Y differential
      THEN ai.combined_score * 1.3
      
      -- Trump policy features (high priority)
      WHEN ai.feature LIKE '%trump%' OR ai.feature LIKE '%executive%' OR ai.feature LIKE '%policy%'
           OR ai.feature LIKE '%ice_trump%' OR ai.feature LIKE '%rin_%' OR ai.feature LIKE '%rfs_%'
      THEN ai.combined_score * 1.4
      
      -- Tariff/trade features (high priority)
      WHEN ai.feature LIKE '%tariff%' OR ai.feature LIKE '%trade_war%' OR ai.feature LIKE '%china_tariff%'
      THEN ai.combined_score * 1.3
      
      -- Argentina features (high priority)
      WHEN ai.feature LIKE '%argentina%' OR ai.feature LIKE '%arg_%'
      THEN ai.combined_score * 1.3
      
      -- Recent events / news (high priority)
      WHEN ai.feature LIKE '%news%' OR ai.feature LIKE '%intelligence%' OR ai.feature LIKE '%sentiment%'
      THEN ai.combined_score * 1.2
      
      -- ICE/labor features
      WHEN ai.feature LIKE '%ice%' OR ai.feature LIKE '%labor%'
      THEN ai.combined_score * 1.3
      
      ELSE ai.combined_score
    END as boosted_score
  FROM aggregated_importance ai
)
SELECT 
  feature,
  avg_importance_gain,
  avg_importance_cover,
  avg_importance_weight,
  combined_score,
  boosted_score,
  horizons_appearing,
  ROW_NUMBER() OVER (ORDER BY boosted_score DESC) as rank_by_importance
FROM priority_boost
ORDER BY boosted_score DESC;

-- STEP 2: Create rich focused feature list (Top 75 by boosted score + critical features)
CREATE OR REPLACE TABLE `cbi-v14.models_v4.rich_focused_feature_list` AS
WITH top_features AS (
  SELECT feature
  FROM `cbi-v14.models_v4.rich_focused_feature_importance`
  WHERE rank_by_importance <= 75
),
-- ALWAYS include these rich regime-aware features (even if not in top 75)
rich_critical_features AS (
  -- Price mechanics (essential)
  SELECT 'zl_price_current' as feature, 'price' as category
  UNION ALL SELECT 'zl_price_lag1', 'price'
  UNION ALL SELECT 'zl_price_lag7', 'price'
  UNION ALL SELECT 'return_1d', 'price'
  UNION ALL SELECT 'return_7d', 'price'
  UNION ALL SELECT 'ma_7d', 'price'
  UNION ALL SELECT 'ma_30d', 'price'
  
  -- Core fundamentals
  UNION ALL SELECT 'crush_margin', 'fundamental'
  UNION ALL SELECT 'china_soybean_imports_mt', 'fundamental'
  UNION ALL SELECT 'crude_price', 'fundamental'
  UNION ALL SELECT 'palm_price', 'fundamental'
  UNION ALL SELECT 'vix_level', 'volatility'
  
  -- Big 8 signals
  UNION ALL SELECT 'feature_vix_stress', 'big8'
  UNION ALL SELECT 'feature_tariff_threat', 'big8'
  UNION ALL SELECT 'feature_biofuel_cascade', 'big8'
  UNION ALL SELECT 'feature_china_relations', 'big8'
  UNION ALL SELECT 'feature_harvest_pace', 'big8'
  UNION ALL SELECT 'feature_geopolitical_volatility', 'big8'
  UNION ALL SELECT 'big8_composite_score', 'big8'
  
  -- FX/RATES (RICH - User Priority #1)
  UNION ALL SELECT 'dollar_index', 'fx'
  UNION ALL SELECT 'usd_cny_rate', 'fx'
  UNION ALL SELECT 'usd_brl_rate', 'fx'
  UNION ALL SELECT 'usd_ars_rate', 'fx'
  UNION ALL SELECT 'dollar_index_7d_change', 'fx'
  UNION ALL SELECT 'fed_funds_rate', 'fx'
  UNION ALL SELECT 'treasury_10y_yield', 'fx'
  UNION ALL SELECT 'real_yield', 'fx'
  UNION ALL SELECT 'yield_curve', 'fx'
  
  -- TRUMP POLICY + RINs/RFS (RICH - User Priority #2)
  UNION ALL SELECT 'trump_policy_events', 'trump'
  UNION ALL SELECT 'trump_policy_impact_avg', 'trump'
  UNION ALL SELECT 'trump_policy_impact_max', 'trump'
  UNION ALL SELECT 'trump_policy_7d', 'trump'
  UNION ALL SELECT 'trump_events_7d', 'trump'
  UNION ALL SELECT 'trump_policy_intensity_14d', 'trump'
  UNION ALL SELECT 'trump_soybean_sentiment_7d', 'trump'
  UNION ALL SELECT 'trump_agricultural_impact_30d', 'trump'
  UNION ALL SELECT 'days_since_trump_policy', 'trump'
  -- RINs/RFS (folded into Policy bucket - 1.4x boost)
  UNION ALL SELECT 'rin_d4_price', 'trump'
  UNION ALL SELECT 'rin_d5_price', 'trump'
  UNION ALL SELECT 'rin_d6_price', 'trump'
  UNION ALL SELECT 'rfs_mandate_biodiesel', 'trump'
  UNION ALL SELECT 'rfs_mandate_advanced', 'trump'
  UNION ALL SELECT 'rfs_mandate_total', 'trump'
  
  -- ICE/TRUMP INTELLIGENCE (RICH - User Priority #3)
  UNION ALL SELECT 'ice_trump_policy_score', 'ice'
  UNION ALL SELECT 'ice_trump_agricultural_mentions', 'ice'
  UNION ALL SELECT 'ice_trump_trade_mentions', 'ice'
  UNION ALL SELECT 'ice_trump_executive_orders', 'ice'
  UNION ALL SELECT 'ice_trump_company_deals', 'ice'
  UNION ALL SELECT 'ice_trump_country_deals', 'ice'
  
  -- TARIFFS/TRADE WAR (RICH - User Priority #4)
  UNION ALL SELECT 'trade_war_intensity', 'tariff'
  UNION ALL SELECT 'trade_war_impact_score', 'tariff'
  UNION ALL SELECT 'china_tariff_rate', 'tariff'
  UNION ALL SELECT 'tradewar_event_vol_mult', 'tariff'
  UNION ALL SELECT 'china_policy_events', 'tariff'
  UNION ALL SELECT 'china_policy_impact', 'tariff'
  
  -- ARGENTINA EVENTS (RICH - User Priority #5)
  UNION ALL SELECT 'argentina_export_tax', 'argentina'
  UNION ALL SELECT 'argentina_china_sales_mt', 'argentina'
  UNION ALL SELECT 'argentina_port_congestion', 'argentina'
  UNION ALL SELECT 'argentina_vessel_queue', 'argentina'
  UNION ALL SELECT 'argentina_crisis_score', 'argentina'
  UNION ALL SELECT 'arg_crisis_score', 'argentina'  -- Enhanced: (ARSUSD_vol_30d + (debt_gdp / 100)) / 2 [0,1]
  
  -- RECENT EVENTS / REGIME AWARENESS (RICH - User Priority #6)
  UNION ALL SELECT 'news_intelligence_7d', 'news'
  UNION ALL SELECT 'news_volume_7d', 'news'
  UNION ALL SELECT 'news_sentiment_avg', 'news'
  UNION ALL SELECT 'china_news_count', 'news'
  UNION ALL SELECT 'tariff_news_count', 'news'
  UNION ALL SELECT 'biofuel_news_count', 'news'
  UNION ALL SELECT 'weather_news_count', 'news'
  
  -- Correlations (regime-aware)
  UNION ALL SELECT 'corr_zl_vix_7d', 'correlation'
  UNION ALL SELECT 'corr_zl_vix_30d', 'correlation'
  UNION ALL SELECT 'corr_zl_palm_7d', 'correlation'
  UNION ALL SELECT 'corr_zl_crude_7d', 'correlation'
  UNION ALL SELECT 'corr_zl_dxy_7d', 'correlation'
),
combined_features AS (
  SELECT DISTINCT feature FROM top_features
  UNION ALL
  SELECT DISTINCT feature FROM rich_critical_features
)
SELECT 
  feature,
  COALESCE(rcf.category, 'top_ranked') as category,
  ROW_NUMBER() OVER (ORDER BY 
    CASE 
      WHEN feature IN (SELECT feature FROM rich_critical_features) THEN 0
      ELSE 1
    END,
    feature
  ) as feature_id
FROM combined_features
LEFT JOIN rich_critical_features rcf USING (feature)
ORDER BY feature_id;

-- STEP 3: Verify feature availability in production tables
CREATE OR REPLACE TABLE `cbi-v14.models_v4.rich_focused_feature_availability` AS
WITH feature_list AS (
  SELECT feature, category FROM `cbi-v14.models_v4.rich_focused_feature_list`
),
schema_1w AS (
  SELECT column_name as feature
  FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
  WHERE table_name = 'production_training_data_1w'
    AND column_name NOT IN ('date', 'target_1w', 'target_1m', 'target_3m', 'target_6m')
),
schema_1m AS (
  SELECT column_name as feature
  FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
  WHERE table_name = 'production_training_data_1m'
    AND column_name NOT IN ('date', 'target_1w', 'target_1m', 'target_3m', 'target_6m')
),
schema_3m AS (
  SELECT column_name as feature
  FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
  WHERE table_name = 'production_training_data_3m'
    AND column_name NOT IN ('date', 'target_1w', 'target_1m', 'target_3m', 'target_6m')
),
schema_6m AS (
  SELECT column_name as feature
  FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
  WHERE table_name = 'production_training_data_6m'
    AND column_name NOT IN ('date', 'target_1w', 'target_1m', 'target_3m', 'target_6m')
)
SELECT 
  fl.feature,
  fl.category,
  CASE WHEN s1w.feature IS NOT NULL THEN TRUE ELSE FALSE END as available_1w,
  CASE WHEN s1m.feature IS NOT NULL THEN TRUE ELSE FALSE END as available_1m,
  CASE WHEN s3m.feature IS NOT NULL THEN TRUE ELSE FALSE END as available_3m,
  CASE WHEN s6m.feature IS NOT NULL THEN TRUE ELSE FALSE END as available_6m
FROM feature_list fl
LEFT JOIN schema_1w s1w ON fl.feature = s1w.feature
LEFT JOIN schema_1m s1m ON fl.feature = s1m.feature
LEFT JOIN schema_3m s3m ON fl.feature = s3m.feature
LEFT JOIN schema_6m s6m ON fl.feature = s6m.feature;

-- STEP 4: Get final rich focused feature list (only available features)
CREATE OR REPLACE TABLE `cbi-v14.models_v4.rich_focused_feature_list_final` AS
SELECT 
  feature,
  category,
  available_1w,
  available_1m,
  available_3m,
  available_6m
FROM `cbi-v14.models_v4.rich_focused_feature_availability`
WHERE available_1w = TRUE  -- Start with 1w, then adapt for others
ORDER BY 
  CASE category
    WHEN 'price' THEN 1
    WHEN 'fundamental' THEN 2
    WHEN 'fx' THEN 3
    WHEN 'trump' THEN 4
    WHEN 'ice' THEN 5
    WHEN 'tariff' THEN 6
    WHEN 'argentina' THEN 7
    WHEN 'news' THEN 8
    WHEN 'big8' THEN 9
    WHEN 'correlation' THEN 10
    ELSE 11
  END,
  feature;

-- STEP 5: Summary report with category breakdown
SELECT 
  'RICH FOCUSED FEATURE SELECTION COMPLETE' as status,
  COUNT(*) as total_features_selected,
  SUM(CASE WHEN available_1w THEN 1 ELSE 0 END) as available_1w,
  SUM(CASE WHEN available_1m THEN 1 ELSE 0 END) as available_1m,
  SUM(CASE WHEN available_3m THEN 1 ELSE 0 END) as available_3m,
  SUM(CASE WHEN available_6m THEN 1 ELSE 0 END) as available_6m,
  COUNT(DISTINCT category) as categories_represented
FROM `cbi-v14.models_v4.rich_focused_feature_availability`;

-- Category breakdown
SELECT 
  category,
  COUNT(*) as feature_count,
  SUM(CASE WHEN available_1w THEN 1 ELSE 0 END) as available_1w
FROM `cbi-v14.models_v4.rich_focused_feature_availability`
GROUP BY category
ORDER BY 
  CASE category
    WHEN 'fx' THEN 1
    WHEN 'trump' THEN 2
    WHEN 'ice' THEN 3
    WHEN 'tariff' THEN 4
    WHEN 'argentina' THEN 5
    WHEN 'news' THEN 6
    WHEN 'price' THEN 7
    WHEN 'fundamental' THEN 8
    WHEN 'big8' THEN 9
    WHEN 'correlation' THEN 10
    ELSE 11
  END;

