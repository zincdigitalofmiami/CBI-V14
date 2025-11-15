-- ============================================
-- BACKFILL PRODUCTION_TRAINING_DATA_1M
-- Expand from 1,404 rows (2020-2025) to ~6,300 rows (2000-2025)
-- ============================================
-- Strategy: Use existing yahoo_finance_complete_enterprise data
-- Only backfill dates that don't exist in production yet

-- Step 1: Create staging table with full 25-year history
CREATE OR REPLACE TABLE `cbi-v14.training.zl_training_prod_allhistory_1m_staging_25yr` AS

WITH 
-- Get all dates from Yahoo ZL data (2000-2025)
all_yahoo_dates AS (
  SELECT DISTINCT
    DATE(TIMESTAMP_MICROS(CAST(date AS INT64))) as date
  FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_finance_complete_enterprise`
  WHERE symbol = 'ZL=F'
    AND date IS NOT NULL
  ORDER BY date
),

-- Get existing production data (2020-2025)
existing_prod AS (
  SELECT *
  FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
),

-- Get historical ZL data from Yahoo (2000-2020, before production starts)
historical_zl AS (
  SELECT 
    DATE(TIMESTAMP_MICROS(CAST(date AS INT64))) as date,
    close as zl_price_current,
    volume as zl_volume,
    ma_7d,
    ma_30d,
    ma_50d,
    ma_90d,
    ma_100d,
    ma_200d,
    rsi_14,
    macd_line,
    macd_signal,
    macd_histogram,
    bb_upper,
    bb_middle,
    bb_lower,
    atr_14
  FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_finance_complete_enterprise`
  WHERE symbol = 'ZL=F'
    AND DATE(TIMESTAMP_MICROS(CAST(date AS INT64))) < '2020-01-06'  -- Before production starts
),

-- Create scaffold for historical dates (2000-2020)
historical_scaffold AS (
  SELECT 
    h.date,
    h.zl_price_current,
    h.zl_volume,
    h.ma_7d,
    h.ma_30d,
    h.ma_50d,
    h.ma_90d,
    h.ma_100d,
    h.ma_200d,
    h.rsi_14,
    h.macd_line,
    h.macd_signal,
    h.macd_histogram,
    h.bb_upper,
    h.bb_middle,
    h.bb_lower,
    h.atr_14,
    -- Add NULL for columns that don't exist in historical data
    CAST(NULL AS FLOAT64) as target_1m,
    CAST(NULL AS FLOAT64) as target_1w,
    CAST(NULL AS FLOAT64) as target_3m,
    CAST(NULL AS FLOAT64) as target_6m
  FROM historical_zl h
)

-- Combine existing production (2020-2025) + historical backfill (2000-2020)
SELECT * FROM existing_prod
WHERE date >= '2020-01-06'

UNION ALL

SELECT 
  date,
  target_1w,
  target_1m,
  target_3m,
  target_6m,
  zl_price_current,
  zl_volume,
  e.* EXCEPT(date, target_1w, target_1m, target_3m, target_6m, zl_price_current, zl_volume)
FROM historical_scaffold h
LEFT JOIN existing_prod e ON 1=0  -- Template row for schema
LIMIT 1;

-- Verify backfill
SELECT 
  'Staging Table Created' as status,
  COUNT(*) as total_rows,
  MIN(date) as earliest_date,
  MAX(date) as latest_date,
  COUNT(CASE WHEN date < '2020-01-06' THEN 1 END) as historical_rows,
  COUNT(CASE WHEN date >= '2020-01-06' THEN 1 END) as current_rows
FROM `cbi-v14.training.zl_training_prod_allhistory_1m_staging_25yr`;






