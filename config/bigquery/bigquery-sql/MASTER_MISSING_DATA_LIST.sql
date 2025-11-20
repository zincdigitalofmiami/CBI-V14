-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- MASTER LIST: ALL MISSING DATA SOURCES
-- Comprehensive audit of what's missing vs what exists
-- ============================================

-- 1. LIST ALL COLUMNS WITH >5% NULLS
WITH column_stats AS (
  SELECT 
    'fed_funds_rate' as column_name,
    COUNTIF(fed_funds_rate IS NULL) / COUNT(*) * 100 as null_pct,
    COUNTIF(fed_funds_rate IS NULL) as null_count
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
  
  UNION ALL
  
  SELECT 'feature_china_relations', COUNTIF(feature_china_relations IS NULL) / COUNT(*) * 100, COUNTIF(feature_china_relations IS NULL)
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
  
  UNION ALL
  
  SELECT 'feature_tariff_threat', COUNTIF(feature_tariff_threat IS NULL) / COUNT(*) * 100, COUNTIF(feature_tariff_threat IS NULL)
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
  
  UNION ALL
  
  SELECT 'weather_brazil_temp', COUNTIF(weather_brazil_temp IS NULL) / COUNT(*) * 100, COUNTIF(weather_brazil_temp IS NULL)
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
  
  UNION ALL
  
  SELECT 'weather_argentina_temp', COUNTIF(weather_argentina_temp IS NULL) / COUNT(*) * 100, COUNTIF(weather_argentina_temp IS NULL)
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
  
  UNION ALL
  
  SELECT 'cftc_commercial_long', COUNTIF(cftc_commercial_long IS NULL) / COUNT(*) * 100, COUNTIF(cftc_commercial_long IS NULL)
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
  
  UNION ALL
  
  SELECT 'news_article_count', COUNTIF(news_article_count IS NULL) / COUNT(*) * 100, COUNTIF(news_article_count IS NULL)
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
  
  UNION ALL
  
  SELECT 'cpi_yoy', COUNTIF(cpi_yoy IS NULL) / COUNT(*) * 100, COUNTIF(cpi_yoy IS NULL)
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
  
  UNION ALL
  
  SELECT 'gdp_growth', COUNTIF(gdp_growth IS NULL) / COUNT(*) * 100, COUNTIF(gdp_growth IS NULL)
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
)

SELECT 
  column_name,
  ROUND(null_pct, 1) as null_percentage,
  null_count,
  CASE 
    WHEN null_pct = 0 THEN 'PERFECT'
    WHEN null_pct <= 5 THEN 'EXCELLENT'
    WHEN null_pct <= 20 THEN 'NEEDS_ATTENTION'
    WHEN null_pct <= 50 THEN 'MAJOR_GAPS'
    ELSE 'CRITICAL_MISSING'
  END as status
FROM column_stats
ORDER BY null_pct DESC;

-- 2. CHECK SOURCE TABLE AVAILABILITY
SELECT 
  'SOURCE_TABLES' as check_type,
  'economic_indicators' as table_name,
  COUNT(*) as records,
  MIN(CAST(time AS DATE)) as earliest,
  MAX(CAST(time AS DATE)) as latest
FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
WHERE indicator IN ('fed_funds_rate', 'ten_year_treasury', 'unemployment_rate')

UNION ALL

SELECT 
  'SOURCE_TABLES',
  'weather_data',
  COUNT(*),
  MIN(date),
  MAX(date)
FROM `cbi-v14.forecasting_data_warehouse.weather_data`
WHERE region IN ('Brazil', 'Argentina', 'US_Midwest')

UNION ALL

SELECT 
  'SOURCE_TABLES',
  'cftc_cot',
  COUNT(*),
  MIN(report_date),
  MAX(report_date)
FROM `cbi-v14.forecasting_data_warehouse.cftc_cot`

UNION ALL

SELECT 
  'SOURCE_TABLES',
  'currency_data',
  COUNT(*),
  MIN(date),
  MAX(date)
FROM `cbi-v14.forecasting_data_warehouse.currency_data`

UNION ALL

SELECT 
  'SOURCE_TABLES',
  'news_intelligence',
  COUNT(*),
  MIN(SAFE.PARSE_DATE('%Y-%m-%d', published)),
  MAX(SAFE.PARSE_DATE('%Y-%m-%d', published))
FROM `cbi-v14.forecasting_data_warehouse.news_intelligence`
WHERE published IS NOT NULL

UNION ALL

SELECT 
  'SOURCE_TABLES',
  'signals.vw_china_relations_big8',
  COUNT(*),
  MIN(date),
  MAX(date)
FROM `cbi-v14.signals.vw_china_relations_big8`

UNION ALL

SELECT 
  'SOURCE_TABLES',
  'signals.vw_tariff_threat_big8',
  COUNT(*),
  MIN(date),
  MAX(date)
FROM `cbi-v14.signals.vw_tariff_threat_big8`;



