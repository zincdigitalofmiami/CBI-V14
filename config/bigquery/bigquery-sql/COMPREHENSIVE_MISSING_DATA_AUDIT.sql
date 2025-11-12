-- ============================================
-- COMPREHENSIVE MISSING DATA AUDIT
-- Find EVERY column with >5% NULLs
-- ============================================

WITH training_data AS (
  SELECT *
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
),

column_nulls AS (
  SELECT 
    'zl_price_current' as column_name,
    COUNTIF(zl_price_current IS NULL) / COUNT(*) * 100 as null_pct,
    COUNTIF(zl_price_current IS NULL) as null_count,
    COUNT(*) as total_rows
  FROM training_data
  
  UNION ALL
  
  SELECT 
    'weather_brazil_temp',
    COUNTIF(weather_brazil_temp IS NULL) / COUNT(*) * 100,
    COUNTIF(weather_brazil_temp IS NULL),
    COUNT(*)
  FROM training_data
  
  UNION ALL
  
  SELECT 
    'weather_argentina_temp',
    COUNTIF(weather_argentina_temp IS NULL) / COUNT(*) * 100,
    COUNTIF(weather_argentina_temp IS NULL),
    COUNT(*)
  FROM training_data
  
  UNION ALL
  
  SELECT 
    'cftc_commercial_long',
    COUNTIF(cftc_commercial_long IS NULL) / COUNT(*) * 100,
    COUNTIF(cftc_commercial_long IS NULL),
    COUNT(*)
  FROM training_data
  
  UNION ALL
  
  SELECT 
    'news_article_count',
    COUNTIF(news_article_count IS NULL) / COUNT(*) * 100,
    COUNTIF(news_article_count IS NULL),
    COUNT(*)
  FROM training_data
  
  UNION ALL
  
  SELECT 
    'cpi_yoy',
    COUNTIF(cpi_yoy IS NULL) / COUNT(*) * 100,
    COUNTIF(cpi_yoy IS NULL),
    COUNT(*)
  FROM training_data
  
  UNION ALL
  
  SELECT 
    'gdp_growth',
    COUNTIF(gdp_growth IS NULL) / COUNT(*) * 100,
    COUNTIF(gdp_growth IS NULL),
    COUNT(*)
  FROM training_data
  
  UNION ALL
  
  SELECT 
    'us_midwest_temp_c',
    COUNTIF(us_midwest_temp_c IS NULL) / COUNT(*) * 100,
    COUNTIF(us_midwest_temp_c IS NULL),
    COUNT(*)
  FROM training_data
)

SELECT 
  column_name,
  ROUND(null_pct, 1) as null_percentage,
  null_count,
  total_rows,
  CASE 
    WHEN null_pct = 0 THEN '✅ PERFECT'
    WHEN null_pct <= 5 THEN '✅ EXCELLENT'
    WHEN null_pct <= 20 THEN '⚠️ NEEDS ATTENTION'
    WHEN null_pct <= 50 THEN '❌ MAJOR GAPS'
    ELSE '❌ CRITICAL - MOSTLY NULL'
  END as status
FROM column_nulls
ORDER BY null_pct DESC;



