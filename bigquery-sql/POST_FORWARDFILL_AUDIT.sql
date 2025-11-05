-- ============================================
-- POST FORWARD-FILL AUDIT
-- Comprehensive verification after forward-fill
-- ============================================

-- 1. DATASET INTEGRITY CHECK
SELECT 
  'DATASET INTEGRITY' as check_type,
  COUNT(*) as total_rows,
  COUNTIF(target_1w IS NOT NULL) as training_rows,
  COUNT(DISTINCT date) as unique_dates,
  COUNT(*) - COUNT(DISTINCT date) as duplicate_dates,
  MIN(date) as earliest_date,
  MAX(date) as latest_date,
  CASE 
    WHEN COUNT(*) - COUNT(DISTINCT date) = 0 THEN '✅ NO DUPLICATES'
    ELSE '❌ DUPLICATE DATES FOUND'
  END as duplicate_status
FROM `cbi-v14.models_v4.training_dataset_super_enriched`;

-- 2. FORWARD-FILL COVERAGE VERIFICATION
WITH coverage_analysis AS (
  SELECT 
    'social_sentiment_avg' as feature_name,
    COUNTIF(social_sentiment_avg IS NOT NULL) as non_null_count,
    COUNT(*) as total_count,
    ROUND(COUNTIF(social_sentiment_avg IS NOT NULL) / COUNT(*) * 100, 1) as coverage_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
  
  UNION ALL
  
  SELECT 'trump_policy_events',
    COUNTIF(trump_policy_events IS NOT NULL),
    COUNT(*),
    ROUND(COUNTIF(trump_policy_events IS NOT NULL) / COUNT(*) * 100, 1)
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
  
  UNION ALL
  
  SELECT 'soybean_weekly_sales',
    COUNTIF(soybean_weekly_sales IS NOT NULL),
    COUNT(*),
    ROUND(COUNTIF(soybean_weekly_sales IS NOT NULL) / COUNT(*) * 100, 1)
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
  
  UNION ALL
  
  SELECT 'china_news_count',
    COUNTIF(china_news_count IS NOT NULL),
    COUNT(*),
    ROUND(COUNTIF(china_news_count IS NOT NULL) / COUNT(*) * 100, 1)
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
  
  UNION ALL
  
  SELECT 'cftc_commercial_extreme',
    COUNTIF(cftc_commercial_extreme IS NOT NULL),
    COUNT(*),
    ROUND(COUNTIF(cftc_commercial_extreme IS NOT NULL) / COUNT(*) * 100, 1)
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
  
  UNION ALL
  
  SELECT 'usd_ars_rate',
    COUNTIF(usd_ars_rate IS NOT NULL),
    COUNT(*),
    ROUND(COUNTIF(usd_ars_rate IS NOT NULL) / COUNT(*) * 100, 1)
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
)
SELECT 
  'FORWARD-FILL COVERAGE' as check_type,
  feature_name,
  non_null_count,
  total_count,
  coverage_pct,
  CASE 
    WHEN coverage_pct >= 80 THEN '✅ HIGH'
    WHEN coverage_pct >= 50 THEN '✅ MEDIUM'
    WHEN coverage_pct >= 20 THEN '⚠️ LOW'
    WHEN coverage_pct >= 5 THEN '⚠️ SPARSE'
    ELSE '❌ VERY SPARSE'
  END as status
FROM coverage_analysis
ORDER BY coverage_pct DESC;

-- 3. DATA QUALITY CHECKS
SELECT 
  'DATA QUALITY' as check_type,
  COUNTIF(target_1w IS NULL) as missing_target,
  COUNTIF(target_1w IS NOT NULL AND (target_1w < -100 OR target_1w > 100)) as extreme_target_values,
  COUNTIF(date IS NULL) as missing_dates,
  COUNTIF(usd_cny_rate IS NOT NULL AND usd_cny_rate <= 0) as invalid_usd_cny,
  COUNTIF(palm_price IS NOT NULL AND palm_price <= 0) as invalid_palm_price,
  CASE 
    WHEN COUNTIF(target_1w IS NULL) = 0 AND 
         COUNTIF(target_1w IS NOT NULL AND (target_1w < -100 OR target_1w > 100)) = 0 AND
         COUNTIF(date IS NULL) = 0
    THEN '✅ DATA QUALITY GOOD'
    ELSE '⚠️ DATA QUALITY ISSUES FOUND'
  END as quality_status
FROM `cbi-v14.models_v4.training_dataset_super_enriched`;

-- 4. FEATURE COUNT VERIFICATION
SELECT 
  'FEATURE COUNT' as check_type,
  COUNT(*) as total_numeric_features,
  COUNTIF(data_type = 'FLOAT64') as float_features,
  COUNTIF(data_type = 'INT64') as int_features,
  CASE 
    WHEN COUNT(*) >= 280 THEN '✅ SUFFICIENT FEATURES'
    ELSE '⚠️ FEATURE COUNT BELOW EXPECTED'
  END as feature_status
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'training_dataset_super_enriched'
  AND data_type IN ('FLOAT64', 'INT64')
  AND column_name NOT IN ('target_1w', 'target_1m', 'target_3m', 'target_6m');

-- 5. FORWARD-FILL LOGIC VERIFICATION
-- Check that forward-fill worked correctly by verifying temporal continuity
WITH temporal_check AS (
  SELECT 
    date,
    social_sentiment_avg,
    trump_policy_events,
    LAG(social_sentiment_avg) OVER (ORDER BY date) as prev_social,
    LAG(trump_policy_events) OVER (ORDER BY date) as prev_trump,
    CASE 
      WHEN social_sentiment_avg IS NOT NULL AND 
           LAG(social_sentiment_avg) OVER (ORDER BY date) IS NULL AND
           date > (SELECT MIN(date) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE social_sentiment_avg IS NOT NULL)
      THEN 1
      ELSE 0
    END as forward_fill_detected_social,
    CASE 
      WHEN trump_policy_events IS NOT NULL AND 
           LAG(trump_policy_events) OVER (ORDER BY date) IS NULL AND
           date > (SELECT MIN(date) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE trump_policy_events IS NOT NULL)
      THEN 1
      ELSE 0
    END as forward_fill_detected_trump
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
  ORDER BY date
  LIMIT 100
)
SELECT 
  'FORWARD-FILL LOGIC' as check_type,
  COUNT(*) as rows_checked,
  SUM(forward_fill_detected_social) as social_forward_fills_detected,
  SUM(forward_fill_detected_trump) as trump_forward_fills_detected,
  CASE 
    WHEN SUM(forward_fill_detected_social) > 0 OR SUM(forward_fill_detected_trump) > 0
    THEN '✅ FORWARD-FILL WORKING'
    ELSE '⚠️ CHECK FORWARD-FILL LOGIC'
  END as forward_fill_status
FROM temporal_check;

-- 6. TRAINING READINESS CHECK
SELECT 
  'TRAINING READINESS' as check_type,
  COUNTIF(target_1w IS NOT NULL) as training_rows,
  COUNT(*) as total_rows,
  ROUND(COUNTIF(target_1w IS NOT NULL) / COUNT(*) * 100, 1) as training_row_percentage,
  COUNTIF(social_sentiment_avg IS NOT NULL AND target_1w IS NOT NULL) as social_available_for_training,
  COUNTIF(trump_policy_events IS NOT NULL AND target_1w IS NOT NULL) as trump_available_for_training,
  COUNTIF(cftc_commercial_extreme IS NOT NULL AND target_1w IS NOT NULL) as cftc_available_for_training,
  CASE 
    WHEN COUNTIF(target_1w IS NOT NULL) >= 1000 AND
         COUNTIF(social_sentiment_avg IS NOT NULL AND target_1w IS NOT NULL) >= 500 AND
         COUNTIF(cftc_commercial_extreme IS NOT NULL AND target_1w IS NOT NULL) >= 200
    THEN '✅ READY FOR TRAINING'
    ELSE '⚠️ CHECK TRAINING READINESS'
  END as training_status
FROM `cbi-v14.models_v4.training_dataset_super_enriched`;

-- 7. COMPARE WITH PRE-FORWARD-FILL BASELINE
SELECT 
  'BEFORE/AFTER COMPARISON' as check_type,
  'BEFORE' as period,
  6.0 as social_coverage,
  3.0 as trump_coverage,
  0.5 as usda_coverage,
  0.3 as news_coverage,
  20.6 as cftc_coverage,
  100.0 as currency_coverage

UNION ALL

SELECT 
  'BEFORE/AFTER COMPARISON',
  'AFTER',
  ROUND(COUNTIF(social_sentiment_avg IS NOT NULL) / COUNTIF(target_1w IS NOT NULL) * 100, 1),
  ROUND(COUNTIF(trump_policy_events IS NOT NULL) / COUNTIF(target_1w IS NOT NULL) * 100, 1),
  ROUND(COUNTIF(soybean_weekly_sales IS NOT NULL) / COUNTIF(target_1w IS NOT NULL) * 100, 1),
  ROUND(COUNTIF(china_news_count IS NOT NULL) / COUNTIF(target_1w IS NOT NULL) * 100, 1),
  ROUND(COUNTIF(cftc_commercial_extreme IS NOT NULL) / COUNTIF(target_1w IS NOT NULL) * 100, 1),
  ROUND(COUNTIF(usd_ars_rate IS NOT NULL) / COUNTIF(target_1w IS NOT NULL) * 100, 1)
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_1w IS NOT NULL;



