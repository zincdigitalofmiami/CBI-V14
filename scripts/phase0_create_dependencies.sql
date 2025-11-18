-- ============================================================================
-- PHASE 0: CREATE MISSING DEPENDENCIES
-- Date: November 15, 2025
-- Purpose: Create required objects that don't exist before any other work
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 0A. Create Historical Signal View (REQUIRED for Sharpe)
-- ----------------------------------------------------------------------------
-- This view is referenced by Sharpe but doesn't exist
-- Build from existing signals view with history

CREATE OR REPLACE VIEW `cbi-v14.api.vw_ultimate_adaptive_signal_historical` AS
WITH historical_signals AS (
  SELECT 
    date AS signal_date,
    date,
    zl_price AS zl_price_current,
    -- Temporary forecast until ML predictions integrated
    zl_price * (1 + COALESCE(zl_return_5d, 0)) AS nn_forecast_1week,
    zl_price * (1 + COALESCE(zl_return_20d, 0)) AS nn_forecast_1month, 
    zl_price * (1 + COALESCE(zl_return_60d, 0)) AS nn_forecast_3month,
    
    -- Map regime to standard classification
    COALESCE(regime, 'FUNDAMENTALS_REGIME') AS master_regime_classification,
    
    -- Use crisis intensity directly
    COALESCE(crisis_intensity, 0) AS crisis_intensity_score,
    
    -- Map primary driver
    COALESCE(primary_driver, 'FUNDAMENTAL') AS primary_signal_driver,
    
    -- Generate trading recommendation based on signals
    CASE 
      WHEN crisis_intensity > 75 AND primary_driver = 'HARVEST' THEN 'STRONG_BUY'
      WHEN crisis_intensity > 75 AND primary_driver IN ('VIX', 'TARIFF') THEN 'SELL'
      WHEN zl_return_5d > 0.03 AND zl_volatility < 0.02 THEN 'BUY'
      WHEN zl_return_5d > 0.03 THEN 'WEAK_BUY'
      WHEN zl_return_5d < -0.03 AND zl_volatility > 0.03 THEN 'SELL'
      WHEN zl_return_5d < -0.03 THEN 'WEAK_SELL'
      ELSE 'HOLD'
    END AS trading_recommendation,
    
    -- Additional fields that might be needed
    zl_return_5d,
    zl_return_20d,
    zl_return_60d,
    zl_volatility,
    corn_price,
    wheat_price,
    palm_price,
    crude_price
    
  FROM `cbi-v14.signals.vw_comprehensive_signal_universe`
  WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 YEAR)
    AND date <= CURRENT_DATE()
)
SELECT * FROM historical_signals
ORDER BY signal_date DESC;

-- ----------------------------------------------------------------------------
-- 0B. Create Risk-Free Rates Table
-- ----------------------------------------------------------------------------
-- Create and populate from treasury prices

CREATE OR REPLACE TABLE `cbi-v14.forecasting_data_warehouse.risk_free_rates` 
PARTITION BY rate_date
CLUSTER BY rate_type AS
SELECT DISTINCT
  DATE(time) AS rate_date,
  -- Convert annual percentage to daily decimal
  CASE 
    WHEN symbol = 'DGS3MO' THEN last / 100 / 365  -- 3-month treasury
    WHEN symbol = 'DGS10' THEN last / 100 / 365   -- 10-year treasury
    ELSE last / 100 / 365
  END AS daily_risk_free_rate,
  
  -- Keep annual rate for reference
  last / 100 AS annual_risk_free_rate,
  
  'FRED' AS source,
  
  -- Determine rate type
  CASE
    WHEN symbol = 'DGS3MO' OR symbol LIKE '%3M%' THEN '3M_TREASURY'
    WHEN symbol = 'DGS10' OR symbol LIKE '%10Y%' THEN '10Y_TREASURY'
    WHEN symbol = '^TNX' THEN '10Y_TREASURY'
    ELSE '3M_TREASURY'  -- Default
  END AS rate_type,
  
  CURRENT_TIMESTAMP() AS updated_at
  
FROM `cbi-v14.forecasting_data_warehouse.treasury_prices`
WHERE last IS NOT NULL
  AND last > 0
  AND last < 100  -- Sanity check - rates should be < 100%
ORDER BY rate_date DESC;

-- Verify risk-free rates populated
SELECT 
  rate_type,
  COUNT(*) as row_count,
  MIN(rate_date) as min_date,
  MAX(rate_date) as max_date,
  AVG(annual_risk_free_rate) as avg_annual_rate
FROM `cbi-v14.forecasting_data_warehouse.risk_free_rates`
GROUP BY rate_type;

-- ----------------------------------------------------------------------------
-- 0C. Backup Critical Tables
-- ----------------------------------------------------------------------------
-- Backup training tables before modifications

-- Backup 1m table (most critical, has column anomaly)
CREATE TABLE IF NOT EXISTS `cbi-v14.archive.backup_20251115__training__zl_training_prod_allhistory_1m` AS
SELECT *, 
  CURRENT_TIMESTAMP() AS backup_timestamp,
  'Pre-regime population and historical backfill' AS backup_reason
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`;

-- Backup 1w table 
CREATE TABLE IF NOT EXISTS `cbi-v14.archive.backup_20251115__training__zl_training_prod_allhistory_1w` AS
SELECT *, 
  CURRENT_TIMESTAMP() AS backup_timestamp,
  'Pre-regime population and historical backfill' AS backup_reason
FROM `cbi-v14.training.zl_training_prod_allhistory_1w`;

-- Backup regime calendar (critical for updates)
CREATE TABLE IF NOT EXISTS `cbi-v14.archive.backup_20251115__training__regime_calendar` AS
SELECT *, 
  CURRENT_TIMESTAMP() AS backup_timestamp,
  'Pre-regime updates' AS backup_reason
FROM `cbi-v14.training.regime_calendar`;

-- ----------------------------------------------------------------------------
-- 0D. Investigate Column Drift
-- ----------------------------------------------------------------------------
-- Get list of extra columns in 1m

WITH cols_1m AS (
  SELECT column_name, ordinal_position, data_type
  FROM `cbi-v14.training`.INFORMATION_SCHEMA.COLUMNS
  WHERE table_name = 'zl_training_prod_allhistory_1m'
),
cols_1w AS (
  SELECT column_name, data_type
  FROM `cbi-v14.training`.INFORMATION_SCHEMA.COLUMNS
  WHERE table_name = 'zl_training_prod_allhistory_1w'
),
extra_cols AS (
  SELECT 
    c1m.ordinal_position, 
    c1m.column_name AS extra_column_in_1m,
    c1m.data_type
  FROM cols_1m c1m
  WHERE c1m.column_name NOT IN (SELECT column_name FROM cols_1w)
  ORDER BY c1m.ordinal_position
)
SELECT 
  'Column Drift Analysis' AS analysis,
  COUNT(*) AS extra_columns_count,
  STRING_AGG(extra_column_in_1m, ', ' ORDER BY ordinal_position) AS extra_column_names
FROM extra_cols;

-- Get sample of extra column patterns
WITH cols_1m AS (
  SELECT column_name
  FROM `cbi-v14.training`.INFORMATION_SCHEMA.COLUMNS
  WHERE table_name = 'zl_training_prod_allhistory_1m'
),
cols_1w AS (
  SELECT column_name
  FROM `cbi-v14.training`.INFORMATION_SCHEMA.COLUMNS  
  WHERE table_name = 'zl_training_prod_allhistory_1w'
)
SELECT 
  c1m.column_name AS extra_column,
  CASE
    WHEN c1m.column_name LIKE '%_lag_%' THEN 'Lagged feature'
    WHEN c1m.column_name LIKE '%_ma_%' THEN 'Moving average'
    WHEN c1m.column_name LIKE '%_std_%' THEN 'Standard deviation'
    WHEN c1m.column_name LIKE '%_pct_%' THEN 'Percentage change'
    WHEN c1m.column_name LIKE '%_ratio_%' THEN 'Ratio feature'
    WHEN c1m.column_name LIKE '%_1m_%' THEN '1-month specific'
    ELSE 'Other'
  END AS likely_type
FROM cols_1m c1m
WHERE c1m.column_name NOT IN (SELECT column_name FROM cols_1w)
ORDER BY likely_type, c1m.column_name
LIMIT 20;

-- ----------------------------------------------------------------------------
-- VERIFICATION QUERIES
-- ----------------------------------------------------------------------------

-- Check if historical view created successfully
SELECT 
  'Historical Signal View' AS object_name,
  COUNT(*) AS row_count,
  MIN(signal_date) AS min_date,
  MAX(signal_date) AS max_date
FROM `cbi-v14.api.vw_ultimate_adaptive_signal_historical`;

-- Check if risk-free rates table created
SELECT 
  'Risk-Free Rates Table' AS object_name,
  COUNT(*) AS row_count,
  COUNT(DISTINCT rate_type) AS rate_types,
  MIN(rate_date) AS min_date,
  MAX(rate_date) AS max_date
FROM `cbi-v14.forecasting_data_warehouse.risk_free_rates`;

-- Check backups created
SELECT 
  table_name,
  row_count,
  DATE(creation_time) AS backup_date
FROM `cbi-v14.archive`.INFORMATION_SCHEMA.TABLE_STORAGE
WHERE table_name LIKE 'backup_20251115_%'
ORDER BY table_name;

-- Summary
SELECT 
  'Phase 0 Complete' AS status,
  CURRENT_TIMESTAMP() AS completion_time,
  'Ready for Phase 1' AS next_step;


