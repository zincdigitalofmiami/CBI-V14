-- ============================================
-- SCHEMA EXPANSION - ADD ALL MISSING COLUMNS
-- Based on continuity audit findings
-- ============================================

-- Add all missing columns to training dataset schema
ALTER TABLE `cbi-v14.models_v4.training_dataset_super_enriched`
ADD COLUMN IF NOT EXISTS social_sentiment_avg FLOAT64,
ADD COLUMN IF NOT EXISTS social_sentiment_volatility FLOAT64,
ADD COLUMN IF NOT EXISTS social_post_count INT64,
ADD COLUMN IF NOT EXISTS bullish_ratio FLOAT64,
ADD COLUMN IF NOT EXISTS bearish_ratio FLOAT64,
ADD COLUMN IF NOT EXISTS social_sentiment_7d FLOAT64,
ADD COLUMN IF NOT EXISTS social_volume_7d INT64,
ADD COLUMN IF NOT EXISTS trump_policy_events INT64,
ADD COLUMN IF NOT EXISTS trump_policy_impact_avg FLOAT64,
ADD COLUMN IF NOT EXISTS trump_policy_impact_max FLOAT64,
ADD COLUMN IF NOT EXISTS trade_policy_events INT64,
ADD COLUMN IF NOT EXISTS china_policy_events INT64,
ADD COLUMN IF NOT EXISTS ag_policy_events INT64,
ADD COLUMN IF NOT EXISTS trump_policy_7d FLOAT64,
ADD COLUMN IF NOT EXISTS trump_events_7d INT64,
ADD COLUMN IF NOT EXISTS soybean_weekly_sales FLOAT64,
ADD COLUMN IF NOT EXISTS soybean_oil_weekly_sales FLOAT64,
ADD COLUMN IF NOT EXISTS soybean_meal_weekly_sales FLOAT64,
ADD COLUMN IF NOT EXISTS china_soybean_sales FLOAT64,
ADD COLUMN IF NOT EXISTS china_news_count INT64,
ADD COLUMN IF NOT EXISTS biofuel_news_count INT64,
ADD COLUMN IF NOT EXISTS tariff_news_count INT64,
ADD COLUMN IF NOT EXISTS weather_news_count INT64,
ADD COLUMN IF NOT EXISTS news_intelligence_7d FLOAT64,
ADD COLUMN IF NOT EXISTS news_volume_7d INT64,
ADD COLUMN IF NOT EXISTS news_sentiment_avg FLOAT64,
ADD COLUMN IF NOT EXISTS cftc_commercial_extreme FLOAT64,
ADD COLUMN IF NOT EXISTS cftc_spec_extreme FLOAT64,
ADD COLUMN IF NOT EXISTS usd_ars_rate FLOAT64,
ADD COLUMN IF NOT EXISTS usd_myr_rate FLOAT64;

-- ============================================
-- COMPLETE MERGE ALL MISSING DATA
-- ============================================

MERGE `cbi-v14.models_v4.training_dataset_super_enriched` AS target
USING (
  WITH 
  -- Social sentiment data
  social AS (
    SELECT 
      date,
      social_sentiment_avg, social_sentiment_volatility, social_post_count,
      bullish_ratio, bearish_ratio, social_sentiment_7d, social_volume_7d
    FROM `cbi-v14.models_v4.social_sentiment_daily`
  ),
  
  -- Trump policy data
  trump AS (
    SELECT 
      date,
      trump_policy_events, trump_policy_impact_avg, trump_policy_impact_max,
      trade_policy_events, china_policy_events, ag_policy_events,
      trump_policy_7d, trump_events_7d
    FROM `cbi-v14.models_v4.trump_policy_daily`
  ),
  
  -- USDA export data
  usda AS (
    SELECT 
      date,
      soybean_weekly_sales, soybean_oil_weekly_sales, soybean_meal_weekly_sales,
      china_soybean_sales
    FROM `cbi-v14.models_v4.usda_export_daily`
  ),
  
  -- News intelligence derived data
  news_derived AS (
    SELECT 
      date,
      china_news_count, biofuel_news_count, tariff_news_count, weather_news_count,
      news_intelligence_7d, news_volume_7d, news_sentiment_avg
    FROM `cbi-v14.models_v4.news_intelligence_daily`
  ),
  
  -- CFTC percentile data (calculate on the fly since not in intermediate table)
  cftc_percentiles AS (
    WITH cftc_with_net AS (
      SELECT 
        date,
        cftc_commercial_long,
        cftc_commercial_short,
        cftc_managed_long,
        cftc_managed_short,
        (cftc_commercial_long - cftc_commercial_short) as commercial_net,
        (cftc_managed_long - cftc_managed_short) as managed_net
      FROM `cbi-v14.models_v4.cftc_daily_filled`
      WHERE cftc_commercial_long IS NOT NULL
    ),
    cftc_percentiles_calc AS (
      SELECT 
        date,
        commercial_net,
        managed_net,
        PERCENT_RANK() OVER (ORDER BY commercial_net) as commercial_net_percentile,
        PERCENT_RANK() OVER (ORDER BY managed_net) as spec_net_percentile
      FROM cftc_with_net
    )
    SELECT 
      date,
      commercial_net_percentile as cftc_commercial_extreme,
      spec_net_percentile as cftc_spec_extreme
    FROM cftc_percentiles_calc
  ),
  
  -- Currency data for missing pairs
  currency_missing AS (
    SELECT 
      date,
      usd_ars_rate, usd_myr_rate
    FROM `cbi-v14.models_v4.currency_complete`
  )
  
  -- Combine all missing data sources
  SELECT 
    COALESCE(s.date, t.date, u.date, n.date, c.date, cur.date) as date,
    
    -- Social sentiment features
    s.social_sentiment_avg, s.social_sentiment_volatility, s.social_post_count,
    s.bullish_ratio, s.bearish_ratio, s.social_sentiment_7d, s.social_volume_7d,
    
    -- Trump policy features
    t.trump_policy_events, t.trump_policy_impact_avg, t.trump_policy_impact_max,
    t.trade_policy_events, t.china_policy_events, t.ag_policy_events,
    t.trump_policy_7d, t.trump_events_7d,
    
    -- USDA features
    u.soybean_weekly_sales, u.soybean_oil_weekly_sales, u.soybean_meal_weekly_sales,
    u.china_soybean_sales,
    
    -- News derived features
    n.china_news_count, n.biofuel_news_count, n.tariff_news_count, n.weather_news_count,
    n.news_intelligence_7d, n.news_volume_7d, n.news_sentiment_avg,
    
    -- CFTC percentile features (calculated on the fly)
    c.cftc_commercial_extreme, c.cftc_spec_extreme,
    
    -- Missing currency features
    cur.usd_ars_rate, cur.usd_myr_rate
    
  FROM social s
  FULL OUTER JOIN trump t USING(date)
  FULL OUTER JOIN usda u USING(date)
  FULL OUTER JOIN news_derived n USING(date)
  FULL OUTER JOIN cftc_percentiles c USING(date)
  FULL OUTER JOIN currency_missing cur USING(date)
  WHERE COALESCE(s.date, t.date, u.date, n.date, c.date, cur.date) IS NOT NULL
  
) AS source ON target.date = source.date
WHEN MATCHED THEN UPDATE SET
  -- Social sentiment updates
  social_sentiment_avg = COALESCE(target.social_sentiment_avg, source.social_sentiment_avg),
  social_sentiment_volatility = COALESCE(target.social_sentiment_volatility, source.social_sentiment_volatility),
  social_post_count = COALESCE(target.social_post_count, source.social_post_count),
  bullish_ratio = COALESCE(target.bullish_ratio, source.bullish_ratio),
  bearish_ratio = COALESCE(target.bearish_ratio, source.bearish_ratio),
  social_sentiment_7d = COALESCE(target.social_sentiment_7d, source.social_sentiment_7d),
  social_volume_7d = COALESCE(target.social_volume_7d, source.social_volume_7d),
  
  -- Trump policy updates
  trump_policy_events = COALESCE(target.trump_policy_events, source.trump_policy_events),
  trump_policy_impact_avg = COALESCE(target.trump_policy_impact_avg, source.trump_policy_impact_avg),
  trump_policy_impact_max = COALESCE(target.trump_policy_impact_max, source.trump_policy_impact_max),
  trade_policy_events = COALESCE(target.trade_policy_events, source.trade_policy_events),
  china_policy_events = COALESCE(target.china_policy_events, source.china_policy_events),
  ag_policy_events = COALESCE(target.ag_policy_events, source.ag_policy_events),
  trump_policy_7d = COALESCE(target.trump_policy_7d, source.trump_policy_7d),
  trump_events_7d = COALESCE(target.trump_events_7d, source.trump_events_7d),
  
  -- USDA updates
  soybean_weekly_sales = COALESCE(target.soybean_weekly_sales, source.soybean_weekly_sales),
  soybean_oil_weekly_sales = COALESCE(target.soybean_oil_weekly_sales, source.soybean_oil_weekly_sales),
  soybean_meal_weekly_sales = COALESCE(target.soybean_meal_weekly_sales, source.soybean_meal_weekly_sales),
  china_soybean_sales = COALESCE(target.china_soybean_sales, source.china_soybean_sales),
  
  -- News derived updates
  china_news_count = COALESCE(target.china_news_count, source.china_news_count),
  biofuel_news_count = COALESCE(target.biofuel_news_count, source.biofuel_news_count),
  tariff_news_count = COALESCE(target.tariff_news_count, source.tariff_news_count),
  weather_news_count = COALESCE(target.weather_news_count, source.weather_news_count),
  news_intelligence_7d = COALESCE(target.news_intelligence_7d, source.news_intelligence_7d),
  news_volume_7d = COALESCE(target.news_volume_7d, source.news_volume_7d),
  news_sentiment_avg = COALESCE(target.news_sentiment_avg, source.news_sentiment_avg),
  
  -- CFTC percentile updates (calculated on the fly)
  cftc_commercial_extreme = COALESCE(target.cftc_commercial_extreme, source.cftc_commercial_extreme),
  cftc_spec_extreme = COALESCE(target.cftc_spec_extreme, source.cftc_spec_extreme),
  
  -- Currency updates
  usd_ars_rate = COALESCE(target.usd_ars_rate, source.usd_ars_rate),
  usd_myr_rate = COALESCE(target.usd_myr_rate, source.usd_myr_rate);

-- ============================================
-- FINAL VERIFICATION - ALL COLUMNS ADDED
-- ============================================

WITH final_coverage AS (
  SELECT 
    COUNT(*) as total_rows,
    COUNTIF(target_1w IS NOT NULL) as training_rows,
    
    -- Check all newly added columns
    COUNTIF(social_sentiment_avg IS NOT NULL) as social_filled,
    COUNTIF(trump_policy_events IS NOT NULL) as trump_filled,
    COUNTIF(soybean_weekly_sales IS NOT NULL) as usda_filled,
    COUNTIF(china_news_count IS NOT NULL) as news_derived_filled,
    COUNTIF(cftc_commercial_extreme IS NOT NULL) as cftc_percentile_filled,
    COUNTIF(usd_ars_rate IS NOT NULL) as ars_filled,
    COUNTIF(usd_myr_rate IS NOT NULL) as myr_filled,
    
    -- Calculate coverage percentages
    ROUND(COUNTIF(social_sentiment_avg IS NOT NULL) / NULLIF(COUNTIF(target_1w IS NOT NULL), 0) * 100, 1) as social_coverage,
    ROUND(COUNTIF(trump_policy_events IS NOT NULL) / NULLIF(COUNTIF(target_1w IS NOT NULL), 0) * 100, 1) as trump_coverage,
    ROUND(COUNTIF(soybean_weekly_sales IS NOT NULL) / NULLIF(COUNTIF(target_1w IS NOT NULL), 0) * 100, 1) as usda_coverage,
    ROUND(COUNTIF(china_news_count IS NOT NULL) / NULLIF(COUNTIF(target_1w IS NOT NULL), 0) * 100, 1) as news_coverage,
    ROUND(COUNTIF(cftc_commercial_extreme IS NOT NULL) / NULLIF(COUNTIF(target_1w IS NOT NULL), 0) * 100, 1) as cftc_percentile_coverage,
    ROUND(COUNTIF(usd_ars_rate IS NOT NULL) / NULLIF(COUNTIF(target_1w IS NOT NULL), 0) * 100, 1) as ars_coverage,
    ROUND(COUNTIF(usd_myr_rate IS NOT NULL) / NULLIF(COUNTIF(target_1w IS NOT NULL), 0) * 100, 1) as myr_coverage
    
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
)
SELECT 
  '🎉 SCHEMA EXPANSION COMPLETE' as status,
  training_rows as total_training_rows,
  
  -- Show all new feature coverage
  CONCAT('Social Sentiment: ', social_coverage, '% (', social_filled, ' rows)') as social_result,
  CONCAT('Trump Policy: ', trump_coverage, '% (', trump_filled, ' rows)') as trump_result,
  CONCAT('USDA Export: ', usda_coverage, '% (', usda_filled, ' rows)') as usda_result,
  CONCAT('News Derived: ', news_coverage, '% (', news_derived_filled, ' rows)') as news_result,
  CONCAT('CFTC Percentiles: ', cftc_percentile_coverage, '% (', cftc_percentile_filled, ' rows)') as cftc_result,
  CONCAT('USD/ARS: ', ars_coverage, '% (', ars_filled, ' rows)') as ars_result,
  CONCAT('USD/MYR: ', myr_coverage, '% (', myr_filled, ' rows)') as myr_result,
  
  -- Calculate total new features added
  (CASE WHEN social_coverage >= 5 THEN 7 ELSE 0 END +
   CASE WHEN trump_coverage >= 5 THEN 8 ELSE 0 END +
   CASE WHEN usda_coverage >= 5 THEN 4 ELSE 0 END +
   CASE WHEN news_coverage >= 5 THEN 7 ELSE 0 END +
   CASE WHEN cftc_percentile_coverage >= 5 THEN 2 ELSE 0 END +
   CASE WHEN ars_coverage >= 5 THEN 1 ELSE 0 END +
   CASE WHEN myr_coverage >= 5 THEN 1 ELSE 0 END) as new_features_added,
  
  -- Final assessment
  CASE 
    WHEN (social_coverage + trump_coverage + usda_coverage + news_coverage) / 4 >= 50
    THEN '🚀 MAJOR SUCCESS - SIGNIFICANT FEATURE EXPANSION'
    WHEN (social_coverage + trump_coverage + usda_coverage + news_coverage) / 4 >= 20
    THEN '✅ SUCCESS - GOOD FEATURE EXPANSION'
    ELSE '⚠️ PARTIAL - SCHEMA ADDED BUT LIMITED DATA'
  END as final_assessment
FROM final_coverage;


