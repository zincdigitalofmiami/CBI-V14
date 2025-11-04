-- ============================================
-- COMPREHENSIVE TRAINING READINESS VERIFICATION
-- NO "SHOULD BE OK" - DEFINITIVE ANSWERS ONLY
-- ============================================

-- 1. VERIFY TABLE EXISTS AND HAS DATA
SELECT 
  'TABLE VERIFICATION' as check_type,
  COUNT(*) as total_rows,
  COUNT(DISTINCT date) as unique_dates,
  MIN(date) as earliest_date,
  MAX(date) as latest_date,
  COUNTIF(target_1w IS NOT NULL) as rows_with_target,
  CASE 
    WHEN COUNT(*) > 0 AND COUNTIF(target_1w IS NOT NULL) > 0 THEN 'PASS'
    ELSE 'FAIL'
  END as status
FROM `cbi-v14.models_v4.training_dataset_super_enriched`;

-- 2. VERIFY ALL CRITICAL COLUMNS EXIST
SELECT 
  'COLUMN EXISTENCE CHECK' as check_type,
  COUNTIF(column_name = 'target_1w') as has_target,
  COUNTIF(column_name = 'zl_price_current') as has_zl_price,
  COUNTIF(column_name = 'soybean_meal_price') as has_meal_price,
  COUNTIF(column_name = 'treasury_10y_yield') as has_treasury,
  COUNTIF(column_name = 'usd_cny_rate') as has_usd_cny,
  COUNTIF(column_name = 'unemployment_rate') as has_unemployment,
  COUNTIF(column_name = 'cpi_yoy') as has_cpi,
  COUNTIF(column_name = 'gdp_growth') as has_gdp,
  COUNTIF(column_name = 'us_midwest_temp_c') as has_temp,
  CASE 
    WHEN COUNTIF(column_name = 'target_1w') = 1 AND
         COUNTIF(column_name = 'zl_price_current') = 1 AND
         COUNTIF(column_name = 'soybean_meal_price') = 1 THEN 'PASS'
    ELSE 'FAIL'
  END as status
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'training_dataset_super_enriched';

-- 3. VERIFY DATA TYPES ARE CORRECT
SELECT 
  'DATA TYPE CHECK' as check_type,
  MAX(CASE WHEN column_name = 'target_1w' THEN data_type END) as target_type,
  MAX(CASE WHEN column_name = 'zl_price_current' THEN data_type END) as zl_price_type,
  MAX(CASE WHEN column_name = 'soybean_meal_price' THEN data_type END) as meal_type,
  MAX(CASE WHEN column_name = 'treasury_10y_yield' THEN data_type END) as treasury_type,
  MAX(CASE WHEN column_name = 'usd_cny_rate' THEN data_type END) as usd_cny_type,
  CASE 
    WHEN MAX(CASE WHEN column_name = 'target_1w' THEN data_type END) = 'FLOAT64' AND
         MAX(CASE WHEN column_name = 'zl_price_current' THEN data_type END) = 'FLOAT64' THEN 'PASS'
    ELSE 'FAIL'
  END as status
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'training_dataset_super_enriched'
  AND column_name IN ('target_1w', 'zl_price_current', 'soybean_meal_price', 'treasury_10y_yield', 'usd_cny_rate');

-- 4. VERIFY DATA COVERAGE IN TRAINING SET
SELECT 
  'DATA COVERAGE IN TRAINING SET' as check_type,
  COUNT(*) as total_training_rows,
  ROUND(COUNTIF(zl_price_current IS NOT NULL) / COUNT(*) * 100, 1) as zl_coverage_pct,
  ROUND(COUNTIF(soybean_meal_price IS NOT NULL) / COUNT(*) * 100, 1) as meal_coverage_pct,
  ROUND(COUNTIF(treasury_10y_yield IS NOT NULL) / COUNT(*) * 100, 1) as treasury_coverage_pct,
  ROUND(COUNTIF(usd_cny_rate IS NOT NULL) / COUNT(*) * 100, 1) as usd_cny_coverage_pct,
  ROUND(COUNTIF(unemployment_rate IS NOT NULL) / COUNT(*) * 100, 1) as unemp_coverage_pct,
  ROUND(COUNTIF(cpi_yoy IS NOT NULL) / COUNT(*) * 100, 1) as cpi_coverage_pct,
  ROUND(COUNTIF(gdp_growth IS NOT NULL) / COUNT(*) * 100, 1) as gdp_coverage_pct,
  ROUND(COUNTIF(us_midwest_temp_c IS NOT NULL) / COUNT(*) * 100, 1) as temp_coverage_pct,
  CASE 
    WHEN COUNTIF(zl_price_current IS NOT NULL) / COUNT(*) >= 0.95 AND
         COUNTIF(soybean_meal_price IS NOT NULL) / COUNT(*) >= 0.95 AND
         COUNTIF(treasury_10y_yield IS NOT NULL) / COUNT(*) >= 0.95 THEN 'PASS'
    ELSE 'FAIL'
  END as status
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_1w IS NOT NULL;

-- 5. TEST EXACT TRAINING QUERY SYNTAX
SELECT 
  'TRAINING QUERY SYNTAX TEST' as check_type,
  COUNT(*) as test_row_count,
  COUNTIF(target_1w IS NOT NULL) as has_target,
  COUNTIF(zl_price_current IS NOT NULL) as has_zl,
  COUNTIF(soybean_meal_price IS NOT NULL) as has_meal,
  CASE 
    WHEN COUNT(*) > 0 AND COUNTIF(target_1w IS NOT NULL) = COUNT(*) THEN 'PASS'
    ELSE 'FAIL'
  END as status
FROM (
  SELECT 
    target_1w,
    zl_price_current,
    soybean_meal_price,
    treasury_10y_yield,
    usd_cny_rate,
    unemployment_rate,
    cpi_yoy,
    gdp_growth,
    us_midwest_temp_c
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
  LIMIT 100
);

-- 6. VERIFY NO DUPLICATE DATES IN TRAINING SET
SELECT 
  'DUPLICATE DATE CHECK' as check_type,
  COUNT(*) as total_rows,
  COUNT(DISTINCT date) as unique_dates,
  COUNT(*) - COUNT(DISTINCT date) as duplicate_count,
  CASE 
    WHEN COUNT(*) = COUNT(DISTINCT date) THEN 'PASS'
    ELSE 'FAIL'
  END as status
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_1w IS NOT NULL;

-- 7. VERIFY NO INVALID VALUES
SELECT 
  'DATA VALIDITY CHECK' as check_type,
  COUNTIF(target_1w IS NOT NULL AND target_1w <= 0) as invalid_targets,
  COUNTIF(zl_price_current IS NOT NULL AND (zl_price_current <= 0 OR zl_price_current > 1000)) as invalid_zl_prices,
  COUNTIF(treasury_10y_yield IS NOT NULL AND (treasury_10y_yield < 0 OR treasury_10y_yield > 20)) as invalid_treasury,
  COUNTIF(usd_cny_rate IS NOT NULL AND (usd_cny_rate <= 0 OR usd_cny_rate > 20)) as invalid_usd_cny,
  CASE 
    WHEN COUNTIF(target_1w IS NOT NULL AND target_1w <= 0) = 0 AND
         COUNTIF(zl_price_current IS NOT NULL AND zl_price_current <= 0) = 0 THEN 'PASS'
    ELSE 'FAIL'
  END as status
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_1w IS NOT NULL;

-- 8. FINAL COMPREHENSIVE STATUS
WITH all_checks AS (
  SELECT 'TABLE_EXISTS' as check_name, 
    CASE WHEN COUNT(*) > 0 THEN 'PASS' ELSE 'FAIL' END as status
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 'HAS_TARGET' as check_name,
    CASE WHEN COUNTIF(target_1w IS NOT NULL) > 0 THEN 'PASS' ELSE 'FAIL' END as status
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 'NO_DUPLICATES' as check_name,
    CASE WHEN COUNT(*) = COUNT(DISTINCT date) THEN 'PASS' ELSE 'FAIL' END as status
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
  
  UNION ALL
  
  SELECT 'ZL_COVERAGE' as check_name,
    CASE WHEN COUNTIF(zl_price_current IS NOT NULL) / COUNT(*) >= 0.95 THEN 'PASS' ELSE 'FAIL' END as status
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
  
  UNION ALL
  
  SELECT 'MEAL_COVERAGE' as check_name,
    CASE WHEN COUNTIF(soybean_meal_price IS NOT NULL) / COUNT(*) >= 0.95 THEN 'PASS' ELSE 'FAIL' END as status
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
  
  UNION ALL
  
  SELECT 'TREASURY_COVERAGE' as check_name,
    CASE WHEN COUNTIF(treasury_10y_yield IS NOT NULL) / COUNT(*) >= 0.95 THEN 'PASS' ELSE 'FAIL' END as status
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE target_1w IS NOT NULL
)

SELECT 
  'FINAL TRAINING READINESS STATUS' as summary,
  COUNT(*) as total_checks,
  COUNTIF(status = 'PASS') as passing_checks,
  COUNTIF(status = 'FAIL') as failing_checks,
  CASE 
    WHEN COUNTIF(status = 'FAIL') = 0 THEN '✅ READY TO TRAIN - ALL CHECKS PASS'
    ELSE '❌ NOT READY - FIX FAILING CHECKS'
  END as final_status
FROM all_checks;


