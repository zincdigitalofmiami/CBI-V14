-- ============================================
-- PRE-TRAINING AUDIT - 1M MODEL
-- Reverse engineer audit before training
-- ============================================

-- 1. TARGET VARIABLE CHECK
SELECT 
  'TARGET VARIABLE CHECK' as check_type,
  COUNT(*) as total_rows,
  COUNTIF(target_1m IS NOT NULL) as training_rows,
  ROUND(COUNTIF(target_1m IS NOT NULL) / COUNT(*) * 100, 1) as coverage_pct,
  MIN(target_1m) as min_target,
  MAX(target_1m) as max_target,
  ROUND(AVG(target_1m), 2) as mean_target,
  ROUND(STDDEV(target_1m), 2) as stddev_target,
  COUNTIF(target_1m < 0 OR target_1m > 100) as extreme_values,
  CASE 
    WHEN COUNTIF(target_1m IS NOT NULL) >= 1000 AND
         COUNTIF(target_1m < 0 OR target_1m > 100) = 0
    THEN '✅ READY FOR TRAINING'
    ELSE '⚠️ CHECK REQUIRED'
  END as status
FROM `cbi-v14.models_v4.training_dataset_super_enriched`;

-- 2. DATASET INTEGRITY CHECK
SELECT 
  'DATASET INTEGRITY' as check_type,
  COUNT(*) as total_rows,
  COUNTIF(target_1m IS NOT NULL) as training_rows,
  COUNT(DISTINCT date) as unique_dates,
  COUNT(*) - COUNT(DISTINCT date) as duplicate_dates,
  MIN(date) as earliest_date,
  MAX(date) as latest_date,
  CASE 
    WHEN COUNT(*) - COUNT(DISTINCT date) = 0 THEN '✅ NO DUPLICATES'
    ELSE '❌ DUPLICATE DATES FOUND'
  END as duplicate_status
FROM `cbi-v14.models_v4.training_dataset_super_enriched`;

-- 3. FEATURE COUNT VERIFICATION
SELECT 
  'FEATURE COUNT' as check_type,
  COUNT(*) as total_numeric_features,
  COUNTIF(data_type = 'FLOAT64') as float_features,
  COUNTIF(data_type = 'INT64') as int_features,
  CASE 
    WHEN COUNT(*) >= 270 THEN '✅ SUFFICIENT FEATURES'
    ELSE '⚠️ FEATURE COUNT BELOW EXPECTED'
  END as feature_status
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'training_dataset_super_enriched'
  AND data_type IN ('FLOAT64', 'INT64')
  AND column_name NOT IN ('target_1w', 'target_1m', 'target_3m', 'target_6m');

-- 4. FORWARD-FILL COVERAGE CHECK
SELECT 
  'FORWARD-FILL COVERAGE' as check_type,
  COUNTIF(social_sentiment_avg IS NOT NULL) / COUNTIF(target_1m IS NOT NULL) * 100 as social_coverage,
  COUNTIF(trump_policy_events IS NOT NULL) / COUNTIF(target_1m IS NOT NULL) * 100 as trump_coverage,
  COUNTIF(cftc_commercial_extreme IS NOT NULL) / COUNTIF(target_1m IS NOT NULL) * 100 as cftc_coverage,
  COUNTIF(usd_ars_rate IS NOT NULL) / COUNTIF(target_1m IS NOT NULL) * 100 as currency_coverage,
  CASE 
    WHEN COUNTIF(social_sentiment_avg IS NOT NULL) / COUNTIF(target_1m IS NOT NULL) >= 0.9
    THEN '✅ FORWARD-FILL WORKING'
    ELSE '⚠️ CHECK FORWARD-FILL'
  END as forward_fill_status
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_1m IS NOT NULL;

-- 5. DATA QUALITY CHECK
SELECT 
  'DATA QUALITY' as check_type,
  COUNTIF(target_1m IS NULL) as missing_target,
  COUNTIF(target_1m IS NOT NULL AND (target_1m < -100 OR target_1m > 100)) as extreme_target_values,
  COUNTIF(date IS NULL) as missing_dates,
  COUNTIF(usd_cny_rate IS NOT NULL AND usd_cny_rate <= 0) as invalid_usd_cny,
  COUNTIF(palm_price IS NOT NULL AND palm_price <= 0) as invalid_palm_price,
  CASE 
    WHEN COUNTIF(target_1m IS NOT NULL AND (target_1m < -100 OR target_1m > 100)) = 0 AND
         COUNTIF(date IS NULL) = 0
    THEN '✅ DATA QUALITY GOOD'
    ELSE '⚠️ DATA QUALITY ISSUES FOUND'
  END as quality_status
FROM `cbi-v14.models_v4.training_dataset_super_enriched`;

-- 6. TRAINING READINESS FINAL CHECK
SELECT 
  'TRAINING READINESS' as check_type,
  COUNTIF(target_1m IS NOT NULL) as training_rows,
  COUNT(*) as total_rows,
  ROUND(COUNTIF(target_1m IS NOT NULL) / COUNT(*) * 100, 1) as training_row_percentage,
  (SELECT COUNT(*) FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS` WHERE table_name = 'training_dataset_super_enriched' AND data_type IN ('FLOAT64', 'INT64') AND column_name NOT IN ('target_1w', 'target_1m', 'target_3m', 'target_6m')) as available_features,
  CASE 
    WHEN COUNTIF(target_1m IS NOT NULL) >= 1000
    THEN '✅ READY FOR TRAINING'
    ELSE '⚠️ CHECK TRAINING READINESS'
  END as training_status
FROM `cbi-v14.models_v4.training_dataset_super_enriched`;



