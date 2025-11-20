-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- COMPREHENSIVE BQML TRAINING CONFIGURATION TEST
-- Verify EVERY part of the training process
-- ============================================

-- 1. CHECK TARGET VARIABLE DISTRIBUTION
SELECT 
  'TARGET VARIABLE CHECK' as check_type,
  COUNT(*) as total_rows,
  MIN(target_1w) as min_target,
  MAX(target_1w) as max_target,
  AVG(target_1w) as mean_target,
  STDDEV(target_1w) as stddev_target,
  COUNTIF(target_1w <= 0) as invalid_targets,
  COUNTIF(target_1w > 200) as extreme_targets,
  CASE 
    WHEN COUNTIF(target_1w <= 0) = 0 AND COUNT(*) >= 100 THEN 'PASS'
    ELSE 'FAIL'
  END as status
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_1w IS NOT NULL;

-- 2. CHECK FEATURE DATA TYPES
SELECT 
  'FEATURE DATA TYPE CHECK' as check_type,
  COUNT(*) as total_features,
  COUNTIF(data_type = 'FLOAT64') as float_features,
  COUNTIF(data_type = 'INT64') as int_features,
  COUNTIF(data_type = 'STRING') as string_features,
  COUNTIF(data_type = 'DATE') as date_features,
  COUNTIF(data_type = 'TIMESTAMP') as timestamp_features,
  COUNTIF(data_type = 'BOOL') as bool_features,
  CASE 
    WHEN COUNTIF(data_type IN ('STRING', 'DATE', 'TIMESTAMP', 'BOOL')) = 0 THEN 'PASS'
    ELSE 'FAIL - HAS NON-NUMERIC FEATURES'
  END as status
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'training_dataset_super_enriched'
  AND column_name NOT IN ('target_1w', 'target_1m', 'target_3m', 'target_6m', 'date', 'symbol');

-- 3. CHECK FOR INFINITE VALUES
SELECT 
  'INFINITE VALUES CHECK' as check_type,
  COUNTIF(IS_INF(zl_price_current)) as inf_zl,
  COUNTIF(IS_INF(soybean_meal_price)) as inf_meal,
  COUNTIF(IS_INF(treasury_10y_yield)) as inf_treasury,
  COUNTIF(IS_INF(target_1w)) as inf_target,
  CASE 
    WHEN COUNTIF(IS_INF(zl_price_current)) = 0 AND 
         COUNTIF(IS_INF(target_1w)) = 0 THEN 'PASS'
    ELSE 'FAIL'
  END as status
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_1w IS NOT NULL;

-- 4. CHECK FOR NaN VALUES
SELECT 
  'NaN VALUES CHECK' as check_type,
  COUNTIF(IS_NAN(zl_price_current)) as nan_zl,
  COUNTIF(IS_NAN(soybean_meal_price)) as nan_meal,
  COUNTIF(IS_NAN(target_1w)) as nan_target,
  CASE 
    WHEN COUNTIF(IS_NAN(zl_price_current)) = 0 AND 
         COUNTIF(IS_NAN(target_1w)) = 0 THEN 'PASS'
    ELSE 'FAIL'
  END as status
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_1w IS NOT NULL;

-- 5. CHECK FEATURE VALUE RANGES (for potential scaling issues)
SELECT 
  'FEATURE VALUE RANGE CHECK' as check_type,
  MIN(zl_price_current) as min_zl,
  MAX(zl_price_current) as max_zl,
  STDDEV(zl_price_current) as stddev_zl,
  MIN(treasury_10y_yield) as min_treasury,
  MAX(treasury_10y_yield) as max_treasury,
  STDDEV(treasury_10y_yield) as stddev_treasury,
  CASE 
    WHEN ABS(MAX(zl_price_current)) < 1e10 AND 
         ABS(MAX(treasury_10y_yield)) < 1e10 THEN 'PASS'
    ELSE 'FAIL - EXTREME VALUES'
  END as status
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_1w IS NOT NULL;

-- 6. CHECK COLUMN NAME COMPATIBILITY (no reserved keywords)
SELECT 
  'COLUMN NAME CHECK' as check_type,
  COUNT(*) as total_columns,
  COUNTIF(column_name IN ('date', 'timestamp', 'value', 'count', 'sum', 'avg', 'min', 'max', 'where', 'from', 'select', 'group', 'order', 'by')) as reserved_keywords,
  CASE 
    WHEN COUNTIF(column_name IN ('date', 'timestamp', 'value', 'count', 'sum', 'avg', 'min', 'max', 'where', 'from', 'select', 'group', 'order', 'by')) = 0 THEN 'PASS'
    ELSE 'FAIL - RESERVED KEYWORDS FOUND'
  END as status
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'training_dataset_super_enriched'
  AND column_name NOT IN ('target_1w', 'target_1m', 'target_3m', 'target_6m', 'date', 'symbol');

-- 7. CHECK TRAINING DATA SIZE
SELECT 
  'TRAINING DATA SIZE CHECK' as check_type,
  COUNT(*) as total_rows,
  CASE 
    WHEN COUNT(*) >= 100 AND COUNT(*) <= 10000000 THEN 'PASS'
    WHEN COUNT(*) < 100 THEN 'FAIL - TOO FEW ROWS'
    ELSE 'WARNING - VERY LARGE DATASET'
  END as status
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_1w IS NOT NULL;

-- 8. CHECK FOR CONSTANT FEATURES (zero variance)
WITH feature_stats AS (
  SELECT 
    'zl_price_current' as feature_name,
    STDDEV(zl_price_current) as stddev,
    COUNT(DISTINCT zl_price_current) as unique_values
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
  
  UNION ALL
  
  SELECT 
    'soybean_meal_price' as feature_name,
    STDDEV(soybean_meal_price) as stddev,
    COUNT(DISTINCT soybean_meal_price) as unique_values
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
  
  UNION ALL
  
  SELECT 
    'treasury_10y_yield' as feature_name,
    STDDEV(treasury_10y_yield) as stddev,
    COUNT(DISTINCT treasury_10y_yield) as unique_values
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
)
SELECT 
  'CONSTANT FEATURE CHECK' as check_type,
  COUNT(*) as features_checked,
  COUNTIF(stddev = 0 OR unique_values = 1) as constant_features,
  CASE 
    WHEN COUNTIF(stddev = 0 OR unique_values = 1) = 0 THEN 'PASS'
    ELSE 'WARNING - CONSTANT FEATURES FOUND'
  END as status
FROM feature_stats;

-- 9. VERIFY EXACT QUERY SYNTAX FOR BQML
SELECT 
  'BQML QUERY SYNTAX TEST' as check_type,
  COUNT(*) as test_row_count,
  COUNTIF(target_1w IS NOT NULL) as has_target,
  COUNTIF(zl_price_current IS NOT NULL) as has_features,
  CASE 
    WHEN COUNT(*) > 0 AND COUNTIF(target_1w IS NOT NULL) = COUNT(*) THEN 'PASS'
    ELSE 'FAIL'
  END as status
FROM (
  SELECT 
    target_1w,
    zl_price_current,
    soybean_meal_price,
    treasury_10y_yield
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
  LIMIT 100
);

-- 10. FINAL COMPREHENSIVE BQML READINESS
WITH all_checks AS (
  SELECT 'TARGET_VALID' as check_name,
    CASE WHEN COUNTIF(target_1w <= 0) = 0 THEN 'PASS' ELSE 'FAIL' END as status
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
  
  UNION ALL
  
  SELECT 'DATA_TYPES_VALID' as check_name,
    CASE WHEN COUNTIF(data_type NOT IN ('FLOAT64', 'INT64')) = 0 THEN 'PASS' ELSE 'FAIL' END as status
  FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
  WHERE table_name = 'training_dataset_super_enriched'
    AND column_name NOT IN ('target_1w', 'target_1m', 'target_3m', 'target_6m', 'date', 'symbol')
  
  UNION ALL
  
  SELECT 'NO_INF_VALUES' as check_name,
    CASE WHEN COUNTIF(IS_INF(target_1w)) = 0 THEN 'PASS' ELSE 'FAIL' END as status
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
  
  UNION ALL
  
  SELECT 'NO_NAN_VALUES' as check_name,
    CASE WHEN COUNTIF(IS_NAN(target_1w)) = 0 THEN 'PASS' ELSE 'FAIL' END as status
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
  
  UNION ALL
  
  SELECT 'SUFFICIENT_ROWS' as check_name,
    CASE WHEN COUNT(*) >= 100 THEN 'PASS' ELSE 'FAIL' END as status
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
)

SELECT 
  'FINAL BQML READINESS STATUS' as summary,
  COUNT(*) as total_checks,
  COUNTIF(status = 'PASS') as passing_checks,
  COUNTIF(status = 'FAIL') as failing_checks,
  CASE 
    WHEN COUNTIF(status = 'FAIL') = 0 THEN '✅ READY FOR BQML TRAINING'
    ELSE '❌ NOT READY - FIX FAILING CHECKS'
  END as final_status
FROM all_checks;



