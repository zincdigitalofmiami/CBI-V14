-- ============================================================================
-- PHASE 1: CRITICAL DATA FIXES
-- Date: November 15, 2025
-- Purpose: Remove duplicates, populate regimes, migrate tables
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1A. Verify and Remove Duplicate Tables
-- ----------------------------------------------------------------------------

-- First, verify parity between duplicate tables
WITH parity_check AS (
  SELECT 
    'prod_all_1m' AS table_variant,
    COUNT(*) AS row_count,
    MIN(date) AS min_date,
    MAX(date) AS max_date,
    COUNT(DISTINCT market_regime) AS unique_regimes,
    MIN(training_weight) AS min_weight,
    MAX(training_weight) AS max_weight
  FROM `cbi-v14.training.zl_training_prod_all_1m`
  
  UNION ALL
  
  SELECT 
    'prod_allhistory_1m' AS table_variant,
    COUNT(*) AS row_count,
    MIN(date) AS min_date,
    MAX(date) AS max_date,
    COUNT(DISTINCT market_regime) AS unique_regimes,
    MIN(training_weight) AS min_weight,
    MAX(training_weight) AS max_weight
  FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
)
SELECT 
  table_variant,
  row_count,
  min_date,
  max_date,
  unique_regimes,
  CONCAT(CAST(min_weight AS STRING), '-', CAST(max_weight AS STRING)) AS weight_range
FROM parity_check
ORDER BY table_variant;

-- Drop duplicate tables (the _all_ variants without "history")
DROP TABLE IF EXISTS `cbi-v14.training.zl_training_prod_all_1w`;
DROP TABLE IF EXISTS `cbi-v14.training.zl_training_prod_all_1m`;
DROP TABLE IF EXISTS `cbi-v14.training.zl_training_prod_all_3m`;
DROP TABLE IF EXISTS `cbi-v14.training.zl_training_prod_all_6m`;
DROP TABLE IF EXISTS `cbi-v14.training.zl_training_prod_all_12m`;

-- Verify duplicates removed
SELECT 
  'Duplicate Cleanup' AS task,
  COUNT(*) AS remaining_all_tables
FROM `cbi-v14.training`.INFORMATION_SCHEMA.TABLES
WHERE table_name LIKE 'zl_training_prod_all_%'
  AND table_name NOT LIKE '%allhistory%';

-- ----------------------------------------------------------------------------
-- 1B. Populate Regimes & Weights
-- ----------------------------------------------------------------------------

-- First test on one table to verify it works
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET market_regime = rc.regime
FROM `cbi-v14.training.regime_calendar` rc
WHERE DATE(t.date) = rc.date;

-- Check if update worked
SELECT 
  'Regime Update Test' AS test,
  COUNT(DISTINCT market_regime) AS unique_regimes,
  COUNT(*) AS total_rows
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`;

-- If successful, update weights
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET training_weight = CAST(rw.weight AS INT64)
FROM `cbi-v14.training.regime_weights` rw
WHERE t.market_regime = rw.regime
  AND DATE(t.date) BETWEEN rw.start_date AND rw.end_date;

-- Verify weights applied
SELECT 
  market_regime,
  MIN(training_weight) AS min_weight,
  MAX(training_weight) AS max_weight,
  COUNT(*) AS row_count
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
GROUP BY market_regime
ORDER BY market_regime;

-- ----------------------------------------------------------------------------
-- 1C. Apply to All Tables (if test successful)
-- ----------------------------------------------------------------------------

-- Update all 10 tables with regimes and weights
-- Using scripting for efficiency

DECLARE tables ARRAY<STRING> DEFAULT [
  'zl_training_prod_allhistory_1w',
  'zl_training_prod_allhistory_3m',
  'zl_training_prod_allhistory_6m',
  'zl_training_prod_allhistory_12m',
  'zl_training_full_allhistory_1w',
  'zl_training_full_allhistory_1m',
  'zl_training_full_allhistory_3m',
  'zl_training_full_allhistory_6m',
  'zl_training_full_allhistory_12m'
];

-- Loop through each table
FOR tbl IN UNNEST(tables) DO
  -- Update regime
  EXECUTE IMMEDIATE FORMAT("""
    UPDATE `cbi-v14.training.%s` t
    SET market_regime = rc.regime
    FROM `cbi-v14.training.regime_calendar` rc
    WHERE DATE(t.date) = rc.date
  """, tbl);
  
  -- Update weight
  EXECUTE IMMEDIATE FORMAT("""
    UPDATE `cbi-v14.training.%s` t
    SET training_weight = CAST(rw.weight AS INT64)
    FROM `cbi-v14.training.regime_weights` rw
    WHERE t.market_regime = rw.regime
      AND DATE(t.date) BETWEEN rw.start_date AND rw.end_date
  """, tbl);
END FOR;

-- ----------------------------------------------------------------------------
-- 1D. Migrate Soybean Oil to raw_intelligence
-- ----------------------------------------------------------------------------

-- Check if already exists
SELECT 
  'Soybean Oil Check' AS check_name,
  COUNT(*) AS existing_rows
FROM `cbi-v14.raw_intelligence`.INFORMATION_SCHEMA.TABLES
WHERE table_name = 'commodity_soybean_oil_prices';

-- Create if not exists
CREATE TABLE IF NOT EXISTS `cbi-v14.raw_intelligence.commodity_soybean_oil_prices`
PARTITION BY DATE(time)
CLUSTER BY symbol AS
SELECT 
  time,
  symbol,
  open,
  high,
  low,
  close,
  volume,
  'forecasting_data_warehouse.soybean_oil_prices' AS source_table,
  CURRENT_TIMESTAMP() AS migrated_at
FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`;

-- Verify migration
SELECT 
  'Soybean Oil Migration' AS task,
  COUNT(*) AS row_count,
  MIN(time) AS min_date,
  MAX(time) AS max_date
FROM `cbi-v14.raw_intelligence.commodity_soybean_oil_prices`;

-- ----------------------------------------------------------------------------
-- FINAL VERIFICATION
-- ----------------------------------------------------------------------------

-- Comprehensive check of all 10 training tables
SELECT 
  table_name,
  row_count,
  unique_regimes,
  CONCAT(CAST(min_weight AS STRING), '-', CAST(max_weight AS STRING)) AS weight_range,
  CASE 
    WHEN unique_regimes >= 7 AND min_weight >= 50 AND max_weight >= 1000 THEN '✅ PASS'
    ELSE '❌ FAIL'
  END AS status
FROM (
  SELECT 
    table_name,
    COUNT(*) AS row_count,
    COUNT(DISTINCT market_regime) AS unique_regimes,
    MIN(training_weight) AS min_weight,
    MAX(training_weight) AS max_weight
  FROM `cbi-v14.training.zl_training_prod_allhistory_1w`
  GROUP BY table_name
  
  UNION ALL
  
  SELECT 'zl_training_prod_allhistory_1m', COUNT(*), COUNT(DISTINCT market_regime), 
         MIN(training_weight), MAX(training_weight)
  FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
  
  UNION ALL
  
  SELECT 'zl_training_prod_allhistory_3m', COUNT(*), COUNT(DISTINCT market_regime),
         MIN(training_weight), MAX(training_weight)
  FROM `cbi-v14.training.zl_training_prod_allhistory_3m`
  
  -- Add remaining tables...
)
ORDER BY table_name;

-- Phase 1 Summary
SELECT 
  'Phase 1 Complete' AS phase,
  CURRENT_TIMESTAMP() AS completion_time,
  'Ready for Phase 2 - Exports' AS next_step;


