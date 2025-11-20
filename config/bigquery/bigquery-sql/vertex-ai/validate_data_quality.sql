-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- =======================================================================================
-- ⚠️ LEGACY SCRIPT - REFERENCE ONLY ⚠️
-- 
-- This script is NOT used in the current architecture (100% local M4 training).
-- Kept for reference only.
--
-- Current architecture: 100% local training, no Vertex AI deployment.
-- Current table naming: training.zl_training_prod_allhistory_{horizon}
-- Legacy tables referenced: models_v4.vertex_ai_training_{horizon}_base
--
-- =======================================================================================
-- validate_data_quality.sql
-- Comprehensive data quality validation for Vertex AI training readiness
-- Run this before creating training datasets
-- =======================================================================================

-- 1. Check target columns (must be non-null and numeric)
SELECT 
    'Target Column Validation' as check_type,
    COUNTIF(target_1m IS NULL) as null_1m,
    COUNTIF(target_3m IS NULL) as null_3m,
    COUNTIF(target_6m IS NULL) as null_6m,
    COUNTIF(target_1w IS NULL) as null_1w,
    COUNT(*) as total_rows
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`;  -- Current: training.zl_training_prod_allhistory_1m

-- 2. Check date column (no duplicates, proper time series)
SELECT 
    'Date Column Validation' as check_type,
    COUNT(*) as total_rows,
    COUNT(DISTINCT date) as distinct_dates,
    MIN(date) as min_date,
    MAX(date) as max_date,
    CASE 
        WHEN COUNT(*) = COUNT(DISTINCT date) THEN 'PASS'
        ELSE 'FAIL - Duplicate dates found'
    END as status
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`;  -- Current: training.zl_training_prod_allhistory_1m

-- 3. Check string columns (must have <5000 unique values for AutoML)
SELECT 
    'String Column Validation' as check_type,
    column_name,
    COUNT(DISTINCT volatility_regime) as unique_volatility_regime,
    COUNT(DISTINCT yahoo_data_source) as unique_yahoo_source
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
GROUP BY column_name;

-- 4. Check for columns with >90% NULL values (will be dropped)
WITH null_check AS (
    SELECT 
        column_name,
        COUNT(*) as total_rows,
        COUNTIF(value IS NULL) as null_count
    FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
    UNPIVOT (value FOR column_name IN (
        -- Dynamic column list would go here
        -- For now, check specific high-risk columns
        SELECT column_name 
        FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = 'zl_training_prod_allhistory_1m'  -- Current: training.zl_training_prod_allhistory_1m
          AND data_type IN ('FLOAT64', 'INT64')
          AND column_name NOT IN ('date', 'target_1m', 'target_3m', 'target_6m', 'target_1w')
    ))
    GROUP BY column_name
)
SELECT 
    'High NULL Percentage Check' as check_type,
    column_name,
    ROUND(100.0 * null_count / total_rows, 2) as null_pct
FROM null_check
WHERE null_pct > 90
ORDER BY null_pct DESC;

-- 5. Check feature count consistency across horizons
SELECT 
    'Feature Count Consistency' as check_type,
    table_name,
    COUNT(*) as column_count
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name LIKE 'zl_training_prod_allhistory%'  -- Current: training.zl_training_prod_allhistory_{horizon}
  AND column_name NOT IN ('date', 'target_1m', 'target_3m', 'target_6m', 'target_1w', 
                          'volatility_regime', 'yahoo_data_source')
GROUP BY table_name
ORDER BY table_name;

-- 6. Check boolean columns (must be converted to INT64)
SELECT 
    'Boolean Column Check' as check_type,
    column_name,
    data_type
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'zl_training_prod_allhistory_1m'
  AND data_type = 'BOOL';

-- 7. Check reserved column names (AutoML doesn't allow: weight, class, id, prediction, target, time, split, fold, dataset)
SELECT 
    'Reserved Name Check' as check_type,
    column_name
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'zl_training_prod_allhistory_1m'
  AND LOWER(column_name) IN ('weight', 'class', 'id', 'prediction', 'target', 'time', 'split', 'fold', 'dataset');

