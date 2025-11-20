-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- DATA CONTINUITY VERIFICATION QUERIES
-- Reverse engineer all areas for continuity verification
-- ============================================

-- 1. SOURCE DATA AVAILABILITY CHECK
SELECT 
  'SOURCE DATA AVAILABILITY' as check_type,
  'news_intelligence' as source_table,
  COUNT(*) as total_records,
  COUNT(DISTINCT DATE(published)) as unique_dates,
  MIN(DATE(published)) as earliest_date,
  MAX(DATE(published)) as latest_date,
  COUNTIF(intelligence_score IS NOT NULL) as records_with_score
FROM `cbi-v14.forecasting_data_warehouse.news_intelligence`
WHERE published IS NOT NULL

UNION ALL

SELECT 
  'SOURCE DATA AVAILABILITY',
  'cftc_cot',
  COUNT(*),
  COUNT(DISTINCT report_date),
  MIN(report_date),
  MAX(report_date),
  COUNTIF(commercial_long IS NOT NULL)
FROM `cbi-v14.forecasting_data_warehouse.cftc_cot`
WHERE commercial_long IS NOT NULL

UNION ALL

SELECT 
  'SOURCE DATA AVAILABILITY',
  'social_sentiment',
  COUNT(*),
  COUNT(DISTINCT DATE(timestamp)),
  MIN(DATE(timestamp)),
  MAX(DATE(timestamp)),
  COUNTIF(sentiment_score IS NOT NULL)
FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
WHERE timestamp IS NOT NULL

UNION ALL

SELECT 
  'SOURCE DATA AVAILABILITY',
  'trump_policy_intelligence',
  COUNT(*),
  COUNT(DISTINCT DATE(timestamp)),
  MIN(DATE(timestamp)),
  MAX(DATE(timestamp)),
  COUNTIF(agricultural_impact IS NOT NULL OR soybean_relevance IS NOT NULL)
FROM `cbi-v14.forecasting_data_warehouse.trump_policy_intelligence`
WHERE timestamp IS NOT NULL

UNION ALL

SELECT 
  'SOURCE DATA AVAILABILITY',
  'currency_data',
  COUNT(*),
  COUNT(DISTINCT date),
  MIN(date),
  MAX(date),
  COUNTIF(rate IS NOT NULL)
FROM `cbi-v14.forecasting_data_warehouse.currency_data`
WHERE date IS NOT NULL

UNION ALL

SELECT 
  'SOURCE DATA AVAILABILITY',
  'palm_oil_prices',
  COUNT(*),
  COUNT(DISTINCT DATE(time)),
  MIN(DATE(time)),
  MAX(DATE(time)),
  COUNTIF(close IS NOT NULL)
FROM `cbi-v14.forecasting_data_warehouse.palm_oil_prices`
WHERE time IS NOT NULL;

-- ============================================
-- 2. INTERMEDIATE TABLE VERIFICATION
-- ============================================

SELECT 
  'INTERMEDIATE TABLE STATUS' as check_type,
  table_name,
  COUNT(*) as total_records,
  MIN(date) as earliest_date,
  MAX(date) as latest_date,
  COUNT(DISTINCT date) as unique_dates
FROM (
  SELECT 'news_intelligence_daily' as table_name, date FROM `cbi-v14.models_v4.news_intelligence_daily`
  UNION ALL
  SELECT 'cftc_daily_filled', date FROM `cbi-v14.models_v4.cftc_daily_filled`
  UNION ALL
  SELECT 'palm_oil_complete', date FROM `cbi-v14.models_v4.palm_oil_complete`
  UNION ALL
  SELECT 'social_sentiment_daily', date FROM `cbi-v14.models_v4.social_sentiment_daily`
  UNION ALL
  SELECT 'trump_policy_daily', date FROM `cbi-v14.models_v4.trump_policy_daily`
  UNION ALL
  SELECT 'currency_complete', date FROM `cbi-v14.models_v4.currency_complete`
  UNION ALL
  SELECT 'usda_export_daily', date FROM `cbi-v14.models_v4.usda_export_daily`
)
GROUP BY table_name
ORDER BY table_name;

-- ============================================
-- 3. TRAINING DATASET COVERAGE ANALYSIS
-- ============================================

SELECT 
  'TRAINING DATASET COVERAGE' as check_type,
  COUNT(*) as total_rows,
  COUNTIF(target_1w IS NOT NULL) as rows_with_target,
  COUNTIF(news_article_count IS NOT NULL) as news_filled,
  COUNTIF(cftc_commercial_long IS NOT NULL) as cftc_filled,
  COUNTIF(palm_price IS NOT NULL) as palm_filled,
  COUNTIF(usd_cny_rate IS NOT NULL) as currency_filled,
  ROUND(COUNTIF(news_article_count IS NOT NULL) / COUNTIF(target_1w IS NOT NULL) * 100, 1) as news_coverage_pct,
  ROUND(COUNTIF(cftc_commercial_long IS NOT NULL) / COUNTIF(target_1w IS NOT NULL) * 100, 1) as cftc_coverage_pct,
  ROUND(COUNTIF(palm_price IS NOT NULL) / COUNTIF(target_1w IS NOT NULL) * 100, 1) as palm_coverage_pct,
  ROUND(COUNTIF(usd_cny_rate IS NOT NULL) / COUNTIF(target_1w IS NOT NULL) * 100, 1) as currency_coverage_pct
FROM `cbi-v14.models_v4.training_dataset_super_enriched`;

-- ============================================
-- 4. DATE RANGE OVERLAP ANALYSIS
-- ============================================

WITH training_dates AS (
  SELECT DISTINCT date 
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
),
source_overlaps AS (
  SELECT 
    'news_intelligence' as source,
    COUNT(DISTINCT t.date) as training_dates,
    COUNT(DISTINCT DATE(n.published)) as source_dates,
    COUNT(DISTINCT t.date) - COUNT(DISTINCT DATE(n.published)) as dates_only_in_training,
    COUNT(DISTINCT DATE(n.published)) - COUNT(DISTINCT t.date) as dates_only_in_source,
    COUNT(DISTINCT CASE WHEN t.date = DATE(n.published) THEN t.date END) as overlap_dates
  FROM training_dates t
  CROSS JOIN `cbi-v14.forecasting_data_warehouse.news_intelligence` n
  WHERE n.published IS NOT NULL
  
  UNION ALL
  
  SELECT 
    'cftc_cot',
    COUNT(DISTINCT t.date),
    COUNT(DISTINCT c.report_date),
    COUNT(DISTINCT t.date) - COUNT(DISTINCT c.report_date),
    COUNT(DISTINCT c.report_date) - COUNT(DISTINCT t.date),
    COUNT(DISTINCT CASE WHEN t.date = c.report_date THEN t.date END)
  FROM training_dates t
  CROSS JOIN `cbi-v14.forecasting_data_warehouse.cftc_cot` c
  WHERE c.commercial_long IS NOT NULL
)
SELECT 
  'DATE RANGE OVERLAP' as check_type,
  source,
  training_dates,
  source_dates,
  overlap_dates,
  ROUND(overlap_dates / training_dates * 100, 1) as overlap_percentage
FROM source_overlaps;

-- ============================================
-- 5. DATA PIPELINE INTEGRITY CHECK
-- ============================================

SELECT 
  'PIPELINE INTEGRITY' as check_type,
  'Source → Intermediate' as pipeline_stage,
  CASE 
    WHEN EXISTS (SELECT 1 FROM `cbi-v14.models_v4.news_intelligence_daily`) THEN '✅ news_intelligence_daily created'
    ELSE '❌ news_intelligence_daily missing'
  END as news_status,
  CASE 
    WHEN EXISTS (SELECT 1 FROM `cbi-v14.models_v4.cftc_daily_filled`) THEN '✅ cftc_daily_filled created'
    ELSE '❌ cftc_daily_filled missing'
  END as cftc_status,
  CASE 
    WHEN EXISTS (SELECT 1 FROM `cbi-v14.models_v4.palm_oil_complete`) THEN '✅ palm_oil_complete created'
    ELSE '❌ palm_oil_complete missing'
  END as palm_status,
  CASE 
    WHEN EXISTS (SELECT 1 FROM `cbi-v14.models_v4.currency_complete`) THEN '✅ currency_complete created'
    ELSE '❌ currency_complete missing'
  END as currency_status

UNION ALL

SELECT 
  'PIPELINE INTEGRITY',
  'Intermediate → Training',
  CASE 
    WHEN COUNTIF(news_article_count IS NOT NULL) > 0 THEN CONCAT('✅ News merged: ', COUNTIF(news_article_count IS NOT NULL), ' rows')
    ELSE '❌ News not merged'
  END,
  CASE 
    WHEN COUNTIF(cftc_commercial_long IS NOT NULL) > 0 THEN CONCAT('✅ CFTC merged: ', COUNTIF(cftc_commercial_long IS NOT NULL), ' rows')
    ELSE '❌ CFTC not merged'
  END,
  CASE 
    WHEN COUNTIF(palm_price IS NOT NULL) > 0 THEN CONCAT('✅ Palm merged: ', COUNTIF(palm_price IS NOT NULL), ' rows')
    ELSE '❌ Palm not merged'
  END,
  CASE 
    WHEN COUNTIF(usd_cny_rate IS NOT NULL) > 0 THEN CONCAT('✅ Currency merged: ', COUNTIF(usd_cny_rate IS NOT NULL), ' rows')
    ELSE '❌ Currency not merged'
  END
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_1w IS NOT NULL;

-- ============================================
-- 6. CONTINUITY GAPS IDENTIFICATION
-- ============================================

WITH date_analysis AS (
  SELECT 
    date,
    CASE WHEN news_article_count IS NOT NULL THEN 1 ELSE 0 END as has_news,
    CASE WHEN cftc_commercial_long IS NOT NULL THEN 1 ELSE 0 END as has_cftc,
    CASE WHEN palm_price IS NOT NULL THEN 1 ELSE 0 END as has_palm,
    CASE WHEN usd_cny_rate IS NOT NULL THEN 1 ELSE 0 END as has_currency
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
),
gap_summary AS (
  SELECT 
    CASE 
      WHEN has_news + has_cftc + has_palm + has_currency = 4 THEN 'COMPLETE'
      WHEN has_news + has_cftc + has_palm + has_currency >= 2 THEN 'PARTIAL'
      WHEN has_news + has_cftc + has_palm + has_currency = 1 THEN 'MOSTLY_MISSING'
      ELSE 'ALL_MISSING'
    END as data_status,
    COUNT(*) as date_count,
    MIN(date) as earliest_date,
    MAX(date) as latest_date
  FROM date_analysis
  GROUP BY data_status
)
SELECT 
  'CONTINUITY GAPS' as check_type,
  data_status,
  date_count,
  ROUND(date_count / SUM(date_count) OVER () * 100, 1) as percentage,
  earliest_date,
  latest_date
FROM gap_summary
ORDER BY 
  CASE data_status
    WHEN 'COMPLETE' THEN 1
    WHEN 'PARTIAL' THEN 2
    WHEN 'MOSTLY_MISSING' THEN 3
    ELSE 4
  END;

-- ============================================
-- 7. FORWARD-FILL VERIFICATION (CFTC)
-- ============================================

SELECT 
  'FORWARD-FILL VERIFICATION' as check_type,
  'CFTC Data' as dataset,
  date,
  cftc_commercial_long,
  LAG(cftc_commercial_long) OVER (ORDER BY date) as prev_value,
  CASE 
    WHEN cftc_commercial_long IS NOT NULL AND LAG(cftc_commercial_long) OVER (ORDER BY date) IS NULL THEN 'NEW_DATA'
    WHEN cftc_commercial_long IS NOT NULL AND LAG(cftc_commercial_long) OVER (ORDER BY date) = cftc_commercial_long THEN 'FORWARD_FILLED'
    WHEN cftc_commercial_long IS NOT NULL AND LAG(cftc_commercial_long) OVER (ORDER BY date) != cftc_commercial_long THEN 'UPDATED'
    ELSE 'NULL'
  END as fill_status
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_1w IS NOT NULL
  AND date >= '2024-08-06' 
  AND date <= '2024-08-20'
ORDER BY date
LIMIT 15;



