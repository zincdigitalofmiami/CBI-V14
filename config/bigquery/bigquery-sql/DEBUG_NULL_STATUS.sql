-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- DEBUG: WHY ARE NULLS STILL THERE?
-- Check what happened with our MERGE operations
-- ============================================

-- 1. Verify our source data exists and has the right structure
SELECT 'yahoo_finance_enhanced' as table_name, 
       COUNT(*) as total_rows,
       COUNT(DISTINCT date) as unique_dates,
       COUNT(DISTINCT symbol) as unique_symbols,
       MIN(date) as earliest_date,
       MAX(date) as latest_date
FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
WHERE symbol IN ('ZL=F', 'ZM=F', '^VIX', 'DX-Y.NYB')

UNION ALL

SELECT 'economic_indicators' as table_name,
       COUNT(*) as total_rows,
       COUNT(DISTINCT CAST(time AS DATE)) as unique_dates,
       COUNT(DISTINCT indicator) as unique_indicators,
       MIN(CAST(time AS DATE)) as earliest_date,
       MAX(CAST(time AS DATE)) as latest_date
FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
WHERE indicator IN ('ten_year_treasury', 'unemployment_rate', 'fed_funds_rate');

-- 2. Check if our intermediate tables were created
SELECT 'yahoo_finance_weekend_complete' as table_name,
       COUNT(*) as row_count,
       'intermediate table exists' as status
FROM `cbi-v14.models_v4.yahoo_finance_weekend_complete`

UNION ALL

SELECT 'economic_indicators_daily_complete' as table_name,
       COUNT(*) as row_count,
       'intermediate table exists' as status  
FROM `cbi-v14.models_v4.economic_indicators_daily_complete`

-- 3. Check specific NULL counts in training dataset RIGHT NOW
WITH current_nulls AS (
  SELECT 
    COUNT(*) as total_rows,
    COUNTIF(zl_price_current IS NULL) as zl_price_nulls,
    COUNTIF(soybean_meal_price IS NULL) as meal_nulls,
    COUNTIF(unemployment_rate IS NULL) as unemployment_nulls,
    COUNTIF(treasury_10y_yield IS NULL) as treasury_nulls,
    COUNTIF(usd_cny_rate IS NULL) as usd_cny_nulls,
    
    -- Show percentage NULLs
    ROUND(COUNTIF(zl_price_current IS NULL) / COUNT(*) * 100, 1) as zl_price_null_pct,
    ROUND(COUNTIF(soybean_meal_price IS NULL) / COUNT(*) * 100, 1) as meal_null_pct,
    ROUND(COUNTIF(unemployment_rate IS NULL) / COUNT(*) * 100, 1) as unemployment_null_pct,
    ROUND(COUNTIF(treasury_10y_yield IS NULL) / COUNT(*) * 100, 1) as treasury_null_pct,
    ROUND(COUNTIF(usd_cny_rate IS NULL) / COUNT(*) * 100, 1) as usd_cny_null_pct
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
)

SELECT 
  'CURRENT NULL STATUS' as status,
  total_rows,
  CONCAT('ZL Price: ', zl_price_null_pct, '% NULL (', zl_price_nulls, ' rows)') as zl_status,
  CONCAT('Meal Price: ', meal_null_pct, '% NULL (', meal_nulls, ' rows)') as meal_status,
  CONCAT('Unemployment: ', unemployment_null_pct, '% NULL (', unemployment_nulls, ' rows)') as unemployment_status,
  CONCAT('Treasury: ', treasury_null_pct, '% NULL (', treasury_nulls, ' rows)') as treasury_status,
  CONCAT('USD/CNY: ', usd_cny_null_pct, '% NULL (', usd_cny_nulls, ' rows)') as usd_cny_status
FROM current_nulls;

-- 4. Check if we have backup tables (to verify MERGEs ran)
SELECT 'training_dataset_super_enriched_backup' as backup_table,
       COUNT(*) as row_count,
       'backup exists' as status
FROM `cbi-v14.models_v4.training_dataset_super_enriched_backup`

UNION ALL

SELECT 'training_dataset_pre_coverage_fix_backup' as backup_table,
       COUNT(*) as row_count,
       'backup exists' as status
FROM `cbi-v14.models_v4.training_dataset_pre_coverage_fix_backup`;

-- 5. Sample a few rows to see what data looks like
SELECT 
  date,
  zl_price_current,
  soybean_meal_price,
  unemployment_rate,
  treasury_10y_yield,
  usd_cny_rate,
  -- Check if these are NULL or have values
  CASE WHEN zl_price_current IS NULL THEN 'NULL' ELSE 'HAS_VALUE' END as zl_status,
  CASE WHEN soybean_meal_price IS NULL THEN 'NULL' ELSE 'HAS_VALUE' END as meal_status,
  CASE WHEN unemployment_rate IS NULL THEN 'NULL' ELSE 'HAS_VALUE' END as unemployment_status
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE date >= '2025-10-01'  -- Recent dates
ORDER BY date DESC
LIMIT 10;

-- 6. Check if source tables have data for recent dates
SELECT 'ZL prices in yahoo_finance' as check_type,
       COUNT(*) as records,
       MIN(date) as earliest,
       MAX(date) as latest
FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
WHERE symbol = 'ZL=F' AND Close IS NOT NULL
  AND date >= '2025-10-01'

UNION ALL

SELECT 'Meal prices in yahoo_finance' as check_type,
       COUNT(*) as records,
       MIN(date) as earliest,
       MAX(date) as latest
FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
WHERE symbol = 'ZM=F' AND Close IS NOT NULL
  AND date >= '2025-10-01'

UNION ALL

SELECT 'Unemployment in economic_indicators' as check_type,
       COUNT(*) as records,
       MIN(CAST(time AS DATE)) as earliest,
       MAX(CAST(time AS DATE)) as latest
FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
WHERE indicator = 'unemployment_rate' AND value IS NOT NULL
  AND CAST(time AS DATE) >= '2025-01-01';

-- 7. CRITICAL: Check if the MERGE actually updated anything
-- Compare backup vs current to see if changes were made
WITH backup_nulls AS (
  SELECT 
    COUNTIF(zl_price_current IS NULL) as zl_nulls_backup,
    COUNTIF(soybean_meal_price IS NULL) as meal_nulls_backup,
    COUNTIF(unemployment_rate IS NULL) as unemployment_nulls_backup
  FROM `cbi-v14.models_v4.training_dataset_super_enriched_backup`
),

current_nulls AS (
  SELECT 
    COUNTIF(zl_price_current IS NULL) as zl_nulls_current,
    COUNTIF(soybean_meal_price IS NULL) as meal_nulls_current,
    COUNTIF(unemployment_rate IS NULL) as unemployment_nulls_current
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
)

SELECT 
  'MERGE EFFECTIVENESS CHECK' as status,
  backup_nulls.zl_nulls_backup,
  current_nulls.zl_nulls_current,
  (backup_nulls.zl_nulls_backup - current_nulls.zl_nulls_current) as zl_nulls_fixed,
  
  backup_nulls.meal_nulls_backup,
  current_nulls.meal_nulls_current,
  (backup_nulls.meal_nulls_backup - current_nulls.meal_nulls_current) as meal_nulls_fixed,
  
  backup_nulls.unemployment_nulls_backup,
  current_nulls.unemployment_nulls_current,
  (backup_nulls.unemployment_nulls_backup - current_nulls.unemployment_nulls_current) as unemployment_nulls_fixed,
  
  CASE 
    WHEN (backup_nulls.zl_nulls_backup - current_nulls.zl_nulls_current) > 0 
    THEN 'MERGE WORKED'
    ELSE 'MERGE FAILED - NO CHANGES MADE'
  END as merge_status
  
FROM backup_nulls, current_nulls;

