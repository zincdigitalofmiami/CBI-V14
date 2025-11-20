-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- FORWARD-FILL SPARSE FEATURES
-- Maximize training data coverage for new features
-- ============================================

-- Create backup before forward-fill
CREATE OR REPLACE TABLE `cbi-v14.models_v4.training_dataset_pre_forwardfill_backup` AS
SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched`;

-- ============================================
-- FORWARD-FILL ALL SPARSE FEATURES
-- ============================================

CREATE OR REPLACE TABLE `cbi-v14.models_v4.training_dataset_super_enriched` AS
WITH 
-- Forward-fill social sentiment features
social_filled AS (
  SELECT 
    date,
    LAST_VALUE(social_sentiment_avg IGNORE NULLS) OVER (
      ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as social_sentiment_avg_filled,
    LAST_VALUE(social_sentiment_volatility IGNORE NULLS) OVER (
      ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as social_sentiment_volatility_filled,
    LAST_VALUE(social_post_count IGNORE NULLS) OVER (
      ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as social_post_count_filled,
    LAST_VALUE(bullish_ratio IGNORE NULLS) OVER (
      ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as bullish_ratio_filled,
    LAST_VALUE(bearish_ratio IGNORE NULLS) OVER (
      ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as bearish_ratio_filled,
    LAST_VALUE(social_sentiment_7d IGNORE NULLS) OVER (
      ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as social_sentiment_7d_filled,
    LAST_VALUE(social_volume_7d IGNORE NULLS) OVER (
      ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as social_volume_7d_filled
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
),

-- Forward-fill Trump policy features
trump_filled AS (
  SELECT 
    date,
    LAST_VALUE(trump_policy_events IGNORE NULLS) OVER (
      ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as trump_policy_events_filled,
    LAST_VALUE(trump_policy_impact_avg IGNORE NULLS) OVER (
      ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as trump_policy_impact_avg_filled,
    LAST_VALUE(trump_policy_impact_max IGNORE NULLS) OVER (
      ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as trump_policy_impact_max_filled,
    LAST_VALUE(trade_policy_events IGNORE NULLS) OVER (
      ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as trade_policy_events_filled,
    LAST_VALUE(china_policy_events IGNORE NULLS) OVER (
      ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as china_policy_events_filled,
    LAST_VALUE(ag_policy_events IGNORE NULLS) OVER (
      ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as ag_policy_events_filled,
    LAST_VALUE(trump_policy_7d IGNORE NULLS) OVER (
      ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as trump_policy_7d_filled,
    LAST_VALUE(trump_events_7d IGNORE NULLS) OVER (
      ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as trump_events_7d_filled
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
),

-- Forward-fill USDA export features
usda_filled AS (
  SELECT 
    date,
    LAST_VALUE(soybean_weekly_sales IGNORE NULLS) OVER (
      ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as soybean_weekly_sales_filled,
    LAST_VALUE(soybean_oil_weekly_sales IGNORE NULLS) OVER (
      ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as soybean_oil_weekly_sales_filled,
    LAST_VALUE(soybean_meal_weekly_sales IGNORE NULLS) OVER (
      ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as soybean_meal_weekly_sales_filled,
    LAST_VALUE(china_soybean_sales IGNORE NULLS) OVER (
      ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as china_soybean_sales_filled
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
),

-- Forward-fill news derived features
news_filled AS (
  SELECT 
    date,
    LAST_VALUE(china_news_count IGNORE NULLS) OVER (
      ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as china_news_count_filled,
    LAST_VALUE(biofuel_news_count IGNORE NULLS) OVER (
      ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as biofuel_news_count_filled,
    LAST_VALUE(tariff_news_count IGNORE NULLS) OVER (
      ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as tariff_news_count_filled,
    LAST_VALUE(weather_news_count IGNORE NULLS) OVER (
      ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as weather_news_count_filled,
    LAST_VALUE(news_intelligence_7d IGNORE NULLS) OVER (
      ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as news_intelligence_7d_filled,
    LAST_VALUE(news_volume_7d IGNORE NULLS) OVER (
      ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as news_volume_7d_filled,
    LAST_VALUE(news_sentiment_avg IGNORE NULLS) OVER (
      ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as news_sentiment_avg_filled
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
),

-- Forward-fill CFTC percentile features (if needed)
cftc_filled AS (
  SELECT 
    date,
    LAST_VALUE(cftc_commercial_extreme IGNORE NULLS) OVER (
      ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as cftc_commercial_extreme_filled,
    LAST_VALUE(cftc_spec_extreme IGNORE NULLS) OVER (
      ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as cftc_spec_extreme_filled
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
),

-- Combine all forward-filled data
all_filled AS (
  SELECT 
    -- Keep all columns from original table, but replace sparse ones with filled versions
    t.* REPLACE(
      -- Social sentiment (use filled if original is NULL)
      COALESCE(t.social_sentiment_avg, s.social_sentiment_avg_filled) as social_sentiment_avg,
      COALESCE(t.social_sentiment_volatility, s.social_sentiment_volatility_filled) as social_sentiment_volatility,
      COALESCE(t.social_post_count, s.social_post_count_filled) as social_post_count,
      COALESCE(t.bullish_ratio, s.bullish_ratio_filled) as bullish_ratio,
      COALESCE(t.bearish_ratio, s.bearish_ratio_filled) as bearish_ratio,
      COALESCE(t.social_sentiment_7d, s.social_sentiment_7d_filled) as social_sentiment_7d,
      COALESCE(t.social_volume_7d, s.social_volume_7d_filled) as social_volume_7d,
      
      -- Trump policy (use filled if original is NULL)
      COALESCE(t.trump_policy_events, tr.trump_policy_events_filled) as trump_policy_events,
      COALESCE(t.trump_policy_impact_avg, tr.trump_policy_impact_avg_filled) as trump_policy_impact_avg,
      COALESCE(t.trump_policy_impact_max, tr.trump_policy_impact_max_filled) as trump_policy_impact_max,
      COALESCE(t.trade_policy_events, tr.trade_policy_events_filled) as trade_policy_events,
      COALESCE(t.china_policy_events, tr.china_policy_events_filled) as china_policy_events,
      COALESCE(t.ag_policy_events, tr.ag_policy_events_filled) as ag_policy_events,
      COALESCE(t.trump_policy_7d, tr.trump_policy_7d_filled) as trump_policy_7d,
      COALESCE(t.trump_events_7d, tr.trump_events_7d_filled) as trump_events_7d,
      
      -- USDA export (use filled if original is NULL)
      COALESCE(t.soybean_weekly_sales, u.soybean_weekly_sales_filled) as soybean_weekly_sales,
      COALESCE(t.soybean_oil_weekly_sales, u.soybean_oil_weekly_sales_filled) as soybean_oil_weekly_sales,
      COALESCE(t.soybean_meal_weekly_sales, u.soybean_meal_weekly_sales_filled) as soybean_meal_weekly_sales,
      COALESCE(t.china_soybean_sales, u.china_soybean_sales_filled) as china_soybean_sales,
      
      -- News derived (use filled if original is NULL)
      COALESCE(t.china_news_count, n.china_news_count_filled) as china_news_count,
      COALESCE(t.biofuel_news_count, n.biofuel_news_count_filled) as biofuel_news_count,
      COALESCE(t.tariff_news_count, n.tariff_news_count_filled) as tariff_news_count,
      COALESCE(t.weather_news_count, n.weather_news_count_filled) as weather_news_count,
      COALESCE(t.news_intelligence_7d, n.news_intelligence_7d_filled) as news_intelligence_7d,
      COALESCE(t.news_volume_7d, n.news_volume_7d_filled) as news_volume_7d,
      COALESCE(t.news_sentiment_avg, n.news_sentiment_avg_filled) as news_sentiment_avg,
      
      -- CFTC percentiles (use filled if original is NULL)
      COALESCE(t.cftc_commercial_extreme, c.cftc_commercial_extreme_filled) as cftc_commercial_extreme,
      COALESCE(t.cftc_spec_extreme, c.cftc_spec_extreme_filled) as cftc_spec_extreme
    )
  FROM `cbi-v14.models_v4.training_dataset_super_enriched` t
  LEFT JOIN social_filled s ON t.date = s.date
  LEFT JOIN trump_filled tr ON t.date = tr.date
  LEFT JOIN usda_filled u ON t.date = u.date
  LEFT JOIN news_filled n ON t.date = n.date
  LEFT JOIN cftc_filled c ON t.date = c.date
)

SELECT * FROM all_filled;

-- ============================================
-- VERIFICATION: Check coverage improvement
-- ============================================

SELECT 
  'FORWARD-FILL RESULTS' as status,
  COUNT(*) as total_training_rows,
  
  -- Check coverage after forward-fill
  ROUND(COUNTIF(social_sentiment_avg IS NOT NULL) / COUNT(*) * 100, 1) as social_coverage_after,
  ROUND(COUNTIF(trump_policy_events IS NOT NULL) / COUNT(*) * 100, 1) as trump_coverage_after,
  ROUND(COUNTIF(soybean_weekly_sales IS NOT NULL) / COUNT(*) * 100, 1) as usda_coverage_after,
  ROUND(COUNTIF(china_news_count IS NOT NULL) / COUNT(*) * 100, 1) as news_coverage_after,
  ROUND(COUNTIF(cftc_commercial_extreme IS NOT NULL) / COUNT(*) * 100, 1) as cftc_coverage_after,
  
  -- Calculate improvement
  CONCAT(ROUND(COUNTIF(social_sentiment_avg IS NOT NULL) / COUNT(*) * 100, 1) - 6.0, '% improvement') as social_improvement,
  CONCAT(ROUND(COUNTIF(trump_policy_events IS NOT NULL) / COUNT(*) * 100, 1) - 3.0, '% improvement') as trump_improvement,
  CONCAT(ROUND(COUNTIF(china_news_count IS NOT NULL) / COUNT(*) * 100, 1) - 0.3, '% improvement') as news_improvement,
  
  -- Final assessment
  CASE 
    WHEN COUNTIF(social_sentiment_avg IS NOT NULL) / COUNT(*) >= 0.5 AND
         COUNTIF(trump_policy_events IS NOT NULL) / COUNT(*) >= 0.3
    THEN '🚀 MAJOR SUCCESS - Coverage significantly improved'
    WHEN COUNTIF(social_sentiment_avg IS NOT NULL) / COUNT(*) >= 0.3
    THEN '✅ SUCCESS - Good coverage improvement'
    ELSE '⚠️ PARTIAL - Some improvement but still limited'
  END as final_assessment
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_1w IS NOT NULL;

