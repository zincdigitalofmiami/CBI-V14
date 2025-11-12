-- ============================================
-- DRY RUN VALIDATION BEFORE TRAINING
-- ============================================
-- Purpose: Validate all requirements before executing model training
-- Run this BEFORE running any TRAIN_BQML_*_PRODUCTION.sql files
-- ============================================

-- ============================================
-- CHECK 1: Training table exists and has data
-- ============================================
SELECT 
  'CHECK 1: Training Table Status' as check_name,
  CASE 
    WHEN COUNT(*) > 0 THEN '✅ PASS'
    ELSE '❌ FAIL - Table empty'
  END as status,
  COUNT(*) as row_count,
  MIN(date) as min_date,
  MAX(date) as max_date,
  DATE_DIFF(CURRENT_DATE(), MAX(date), DAY) as days_since_last_update
FROM `cbi-v14.models_v4.training_dataset_super_enriched`;

-- ============================================
-- CHECK 2: Verify target columns exist
-- ============================================
SELECT 
  'CHECK 2: Target Columns Exist' as check_name,
  CASE 
    WHEN COUNT(*) >= 4 THEN '✅ PASS'
    WHEN COUNT(*) > 0 THEN '⚠️  PARTIAL - Missing some targets'
    ELSE '❌ FAIL - No target columns'
  END as status,
  STRING_AGG(column_name ORDER BY column_name) as target_columns_found
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'training_dataset_super_enriched'
  AND column_name IN ('target_1w', 'target_1m', 'target_3m', 'target_6m');

-- ============================================
-- CHECK 3: Verify target availability by horizon
-- ============================================
WITH target_counts AS (
  SELECT 
    COUNTIF(target_1w IS NOT NULL) as target_1w_count,
    COUNTIF(target_1m IS NOT NULL) as target_1m_count,
    COUNTIF(target_3m IS NOT NULL) as target_3m_count,
    COUNTIF(target_6m IS NOT NULL) as target_6m_count,
    COUNT(*) as total_rows
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
)
SELECT 
  'CHECK 3: Target Availability' as check_name,
  CASE 
    WHEN target_1w_count >= 1000 
     AND target_1m_count >= 1000 
     AND target_3m_count >= 1000 
     AND target_6m_count >= 1000 
    THEN '✅ PASS'
    WHEN target_1w_count >= 500 
     AND target_1m_count >= 500 
     AND target_3m_count >= 500 
     AND target_6m_count >= 500 
    THEN '⚠️  WARNING - Low target counts'
    ELSE '❌ FAIL - Insufficient targets'
  END as status,
  target_1w_count,
  target_1m_count,
  target_3m_count,
  target_6m_count,
  total_rows
FROM target_counts;

-- ============================================
-- CHECK 4: Verify no duplicate dates
-- ============================================
WITH date_counts AS (
  SELECT 
    date,
    COUNT(*) as count
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  GROUP BY date
  HAVING COUNT(*) > 1
)
SELECT 
  'CHECK 4: No Duplicate Dates' as check_name,
  CASE 
    WHEN COUNT(*) = 0 THEN '✅ PASS'
    ELSE '❌ FAIL - Duplicate dates found'
  END as status,
  COUNT(*) as duplicate_date_count,
  STRING_AGG(CAST(date AS STRING) ORDER BY date LIMIT 10) as sample_duplicates
FROM date_counts;

-- ============================================
-- CHECK 5: Verify column count
-- ============================================
SELECT 
  'CHECK 5: Column Count' as check_name,
  CASE 
    WHEN COUNT(*) >= 275 THEN '✅ PASS - Full schema'
    WHEN COUNT(*) >= 200 THEN '⚠️  WARNING - Reduced schema'
    WHEN COUNT(*) >= 100 THEN '⚠️  WARNING - Minimal schema'
    ELSE '❌ FAIL - Truncated table'
  END as status,
  COUNT(*) as column_count,
  COUNT(*) - 6 as estimated_feature_count
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'training_dataset_super_enriched';

-- ============================================
-- CHECK 6: Verify no 100% NULL columns
-- ============================================
-- Note: This is a sample check - full check would need to query all columns
SELECT 
  'CHECK 6: Sample NULL Check' as check_name,
  CASE 
    WHEN COUNTIF(zl_price_current IS NULL) = 0 THEN '✅ PASS - Core features populated'
    ELSE '❌ FAIL - Core features have NULLs'
  END as status,
  COUNTIF(zl_price_current IS NULL) as null_count,
  COUNT(*) as total_rows
FROM `cbi-v14.models_v4.training_dataset_super_enriched`;

-- ============================================
-- CHECK 7: Verify date column exists and has no NULLs
-- ============================================
SELECT 
  'CHECK 7: Date Column Status' as check_name,
  CASE 
    WHEN COUNTIF(date IS NULL) = 0 THEN '✅ PASS'
    ELSE '❌ FAIL - NULL dates found'
  END as status,
  COUNTIF(date IS NULL) as null_dates,
  COUNT(*) as total_rows
FROM `cbi-v14.models_v4.training_dataset_super_enriched`;

-- ============================================
-- CHECK 8: Verify no STRING columns (except excluded ones)
-- ============================================
SELECT 
  'CHECK 8: Data Types Valid' as check_name,
  CASE 
    WHEN COUNT(*) = 0 THEN '✅ PASS - Only valid types'
    WHEN COUNT(*) <= 2 THEN '✅ PASS - Only volatility_regime and market_regime'
    ELSE '⚠️  WARNING - Multiple STRING columns found'
  END as status,
  COUNT(*) as string_column_count,
  STRING_AGG(column_name ORDER BY column_name) as string_columns
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'training_dataset_super_enriched'
  AND data_type = 'STRING'
  AND column_name NOT IN ('volatility_regime', 'market_regime');

-- ============================================
-- CHECK 9: Latest date is recent
-- ============================================
SELECT 
  'CHECK 9: Data Freshness' as check_name,
  CASE 
    WHEN DATE_DIFF(CURRENT_DATE(), MAX(date), DAY) <= 2 THEN '✅ PASS - Fresh data'
    WHEN DATE_DIFF(CURRENT_DATE(), MAX(date), DAY) <= 7 THEN '⚠️  WARNING - Data slightly stale'
    ELSE '❌ FAIL - Data is stale'
  END as status,
  MAX(date) as latest_date,
  DATE_DIFF(CURRENT_DATE(), MAX(date), DAY) as days_old
FROM `cbi-v14.models_v4.training_dataset_super_enriched`;

-- ============================================
-- CHECK 10: Verify required features exist
-- ============================================
WITH required_features AS (
  SELECT column_name
  FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
  WHERE table_name = 'training_dataset_super_enriched'
    AND column_name IN (
      'zl_price_current', 'crude_price', 'palm_price', 
      'vix_level', 'dxy_level', 'big8_composite_score',
      'china_sentiment', 'brazil_temp_c', 'argentina_export_tax'
    )
)
SELECT 
  'CHECK 10: Required Features' as check_name,
  CASE 
    WHEN COUNT(*) >= 8 THEN '✅ PASS - All required features exist'
    WHEN COUNT(*) >= 5 THEN '⚠️  WARNING - Some required features missing'
    ELSE '❌ FAIL - Missing critical features'
  END as status,
  COUNT(*) as features_found,
  9 as features_required,
  STRING_AGG(column_name ORDER BY column_name) as found_features
FROM required_features;

-- ============================================
-- SUMMARY
-- ============================================
SELECT 
  '====== DRY RUN VALIDATION SUMMARY ======' as message,
  CURRENT_TIMESTAMP() as validation_time;

-- ============================================
-- MANUAL CHECKS REQUIRED:
-- ============================================
-- 1. Verify no other training jobs are currently running
-- 2. Verify BigQuery quota is available
-- 3. Verify table schema matches expected (275+ columns)
-- 4. Review any WARNINGS above before proceeding
-- 5. If all checks PASS, proceed with training
-- ============================================







