-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================================================
-- BACKFILL HISTORICAL DATA FROM YAHOO_FINANCE_COMPREHENSIVE
-- Date: November 12, 2025
-- Purpose: Fill critical data gaps for 14 commodities (2000-2020)
-- Source: yahoo_finance_comprehensive.yahoo_normalized
-- ============================================================================

-- IMPORTANT: This will add ~75,000+ historical rows across 14 tables
-- Only backfills pre-2020 data to avoid duplicates with existing data
-- Run time: ~5-10 minutes total

-- ============================================================================
-- 1. AGRICULTURAL COMMODITIES (Core Trading Complex)
-- ============================================================================

-- SOYBEANS (ZS=F) - Critical for soy complex analysis
INSERT INTO `cbi-v14.forecasting_data_warehouse.soybean_prices`
(time, open, high, low, close, volume, symbol, source_name, confidence_score, ingest_timestamp_utc, provenance_uuid)
SELECT 
    DATETIME(date) as time,
    open,
    high,
    low,
    close,
    volume,
    'ZS' as symbol,
    'yahoo_finance_comprehensive_historical' as source_name,
    1.0 as confidence_score,
    CURRENT_TIMESTAMP() as ingest_timestamp_utc,
    GENERATE_UUID() as provenance_uuid
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol = 'ZS=F'
  AND date >= '2000-01-01'
  AND date < '2020-01-01'
ORDER BY date;
-- Expected: ~4,800 rows

-- CORN (ZC=F) - Acreage competition indicator
INSERT INTO `cbi-v14.forecasting_data_warehouse.corn_prices`
(time, open, high, low, close, volume, symbol, source_name, confidence_score, ingest_timestamp_utc, provenance_uuid)
SELECT 
    DATETIME(date) as time,
    open,
    high,
    low,
    close,
    volume,
    'ZC' as symbol,
    'yahoo_finance_comprehensive_historical' as source_name,
    1.0 as confidence_score,
    CURRENT_TIMESTAMP() as ingest_timestamp_utc,
    GENERATE_UUID() as provenance_uuid
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol = 'ZC=F'
  AND date >= '2000-01-01'
  AND date < '2020-01-01'
ORDER BY date;
-- Expected: ~4,800 rows

-- WHEAT (ZW=F) - Global grain benchmark
INSERT INTO `cbi-v14.forecasting_data_warehouse.wheat_prices`
(time, open, high, low, close, volume, symbol, source_name, confidence_score, ingest_timestamp_utc, provenance_uuid)
SELECT 
    DATETIME(date) as time,
    open,
    high,
    low,
    close,
    volume,
    'ZW' as symbol,
    'yahoo_finance_comprehensive_historical' as source_name,
    1.0 as confidence_score,
    CURRENT_TIMESTAMP() as ingest_timestamp_utc,
    GENERATE_UUID() as provenance_uuid
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol = 'ZW=F'
  AND date >= '2000-01-01'
  AND date < '2020-01-01'
ORDER BY date;
-- Expected: ~4,800 rows

-- SOYBEAN MEAL (ZM=F) - Protein market indicator
INSERT INTO `cbi-v14.forecasting_data_warehouse.soybean_meal_prices`
(time, open, high, low, close, volume, symbol, source_name, confidence_score, ingest_timestamp_utc, provenance_uuid)
SELECT 
    TIMESTAMP(date) as time,
    open,
    high,
    low,
    close,
    volume,
    'ZM' as symbol,
    'yahoo_finance_comprehensive_historical' as source_name,
    1.0 as confidence_score,
    CURRENT_TIMESTAMP() as ingest_timestamp_utc,
    GENERATE_UUID() as provenance_uuid
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol = 'ZM=F'
  AND date >= '2000-01-01'
  AND date < '2020-01-01'
ORDER BY date;
-- Expected: ~4,800 rows

-- ============================================================================
-- 2. ENERGY COMPLEX (Biofuel Correlation)
-- ============================================================================

-- CRUDE OIL WTI (CL=F) - Energy benchmark
-- Table already exists with DATE type for time column
INSERT INTO `cbi-v14.forecasting_data_warehouse.crude_oil_prices`
(time, open, high, low, close, volume, symbol, source_name, confidence_score, ingest_timestamp_utc, provenance_uuid)
SELECT 
    date as time,
    open,
    high,
    low,
    close,
    volume,
    'CL' as symbol,
    'yahoo_finance_comprehensive_historical' as source_name,
    1.0 as confidence_score,
    CURRENT_TIMESTAMP() as ingest_timestamp_utc,
    GENERATE_UUID() as provenance_uuid
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol = 'CL=F'
  AND date >= '2000-01-01'
  AND date < '2020-01-01'
ORDER BY date;
-- Expected: ~4,800 rows

-- NATURAL GAS (NG=F) - Energy alternative
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.natural_gas_prices` (
    time DATETIME,
    open FLOAT64,
    high FLOAT64,
    low FLOAT64,
    close FLOAT64,
    volume INT64,
    symbol STRING,
    source_name STRING,
    confidence_score FLOAT64,
    ingest_timestamp_utc TIMESTAMP,
    provenance_uuid STRING
);

INSERT INTO `cbi-v14.forecasting_data_warehouse.natural_gas_prices`
(time, open, high, low, close, volume, symbol, source_name, confidence_score, ingest_timestamp_utc, provenance_uuid)
SELECT 
    DATETIME(date) as time,
    open,
    high,
    low,
    close,
    volume,
    'NG' as symbol,
    'yahoo_finance_comprehensive_historical' as source_name,
    1.0 as confidence_score,
    CURRENT_TIMESTAMP() as ingest_timestamp_utc,
    GENERATE_UUID() as provenance_uuid
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol = 'NG=F'
  AND date >= '2000-01-01'
  AND date < '2020-01-01'
ORDER BY date;
-- Expected: ~4,800 rows

-- ============================================================================
-- 3. PRECIOUS METALS (Safe Haven Indicators)
-- ============================================================================

-- GOLD (GC=F) - Risk-off indicator
INSERT INTO `cbi-v14.forecasting_data_warehouse.gold_prices`
(time, open, high, low, close, volume, symbol, source_name, confidence_score, ingest_timestamp_utc, provenance_uuid)
SELECT 
    DATETIME(date) as time,
    open,
    high,
    low,
    close,
    volume,
    'GC' as symbol,
    'yahoo_finance_comprehensive_historical' as source_name,
    1.0 as confidence_score,
    CURRENT_TIMESTAMP() as ingest_timestamp_utc,
    GENERATE_UUID() as provenance_uuid
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol = 'GC=F'
  AND date >= '2000-01-01'
  AND date < '2020-01-01'
ORDER BY date;
-- Expected: ~4,800 rows

-- SILVER (SI=F) - Industrial/precious hybrid
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.silver_prices` (
    time DATETIME,
    open FLOAT64,
    high FLOAT64,
    low FLOAT64,
    close FLOAT64,
    volume INT64,
    symbol STRING,
    source_name STRING,
    confidence_score FLOAT64,
    ingest_timestamp_utc TIMESTAMP,
    provenance_uuid STRING
);

INSERT INTO `cbi-v14.forecasting_data_warehouse.silver_prices`
(time, open, high, low, close, volume, symbol, source_name, confidence_score, ingest_timestamp_utc, provenance_uuid)
SELECT 
    DATETIME(date) as time,
    open,
    high,
    low,
    close,
    volume,
    'SI' as symbol,
    'yahoo_finance_comprehensive_historical' as source_name,
    1.0 as confidence_score,
    CURRENT_TIMESTAMP() as ingest_timestamp_utc,
    GENERATE_UUID() as provenance_uuid
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol = 'SI=F'
  AND date >= '2000-01-01'
  AND date < '2020-01-01'
ORDER BY date;
-- Expected: ~4,800 rows

-- COPPER (HG=F) - Global growth indicator
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.copper_prices` (
    time DATETIME,
    open FLOAT64,
    high FLOAT64,
    low FLOAT64,
    close FLOAT64,
    volume INT64,
    symbol STRING,
    source_name STRING,
    confidence_score FLOAT64,
    ingest_timestamp_utc TIMESTAMP,
    provenance_uuid STRING
);

INSERT INTO `cbi-v14.forecasting_data_warehouse.copper_prices`
(time, open, high, low, close, volume, symbol, source_name, confidence_score, ingest_timestamp_utc, provenance_uuid)
SELECT 
    DATETIME(date) as time,
    open,
    high,
    low,
    close,
    volume,
    'HG' as symbol,
    'yahoo_finance_comprehensive_historical' as source_name,
    1.0 as confidence_score,
    CURRENT_TIMESTAMP() as ingest_timestamp_utc,
    GENERATE_UUID() as provenance_uuid
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol = 'HG=F'
  AND date >= '2000-01-01'
  AND date < '2020-01-01'
ORDER BY date;
-- Expected: ~4,800 rows

-- ============================================================================
-- 4. MARKET INDICATORS
-- ============================================================================

-- USD INDEX (DX-Y.NYB) - Dollar strength
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.usd_index_prices` (
    time DATETIME,
    open FLOAT64,
    high FLOAT64,
    low FLOAT64,
    close FLOAT64,
    volume INT64,
    symbol STRING,
    source_name STRING,
    confidence_score FLOAT64,
    ingest_timestamp_utc TIMESTAMP,
    provenance_uuid STRING
);

INSERT INTO `cbi-v14.forecasting_data_warehouse.usd_index_prices`
(time, open, high, low, close, volume, symbol, source_name, confidence_score, ingest_timestamp_utc, provenance_uuid)
SELECT 
    DATETIME(date) as time,
    open,
    high,
    low,
    close,
    volume,
    'DXY' as symbol,
    'yahoo_finance_comprehensive_historical' as source_name,
    1.0 as confidence_score,
    CURRENT_TIMESTAMP() as ingest_timestamp_utc,
    GENERATE_UUID() as provenance_uuid
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol = 'DX-Y.NYB'
  AND date >= '2000-01-01'
  AND date < '2020-01-01'
ORDER BY date;
-- Expected: ~4,800 rows

-- VIX VOLATILITY (^VIX) - Fear gauge (backfill pre-2015)
INSERT INTO `cbi-v14.forecasting_data_warehouse.vix_daily`
(date, open, high, low, close, volume, symbol, source_name)
SELECT 
    date,
    open,
    high,
    low,
    close,
    volume,
    'VIX' as symbol,
    'yahoo_finance_comprehensive_historical' as source_name
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol = '^VIX'
  AND date >= '2000-01-01'
  AND date < '2015-01-01'  -- Only backfill pre-2015
ORDER BY date;
-- Expected: ~3,500 rows

-- S&P 500 (^GSPC) - Market benchmark (backfill pre-2018)
INSERT INTO `cbi-v14.forecasting_data_warehouse.sp500_prices`
(time, open, high, low, close, volume, symbol, source_name, confidence_score, ingest_timestamp_utc, provenance_uuid)
SELECT 
    DATETIME(date) as time,
    open,
    high,
    low,
    close,
    volume,
    'SPX' as symbol,
    'yahoo_finance_comprehensive_historical' as source_name,
    1.0 as confidence_score,
    CURRENT_TIMESTAMP() as ingest_timestamp_utc,
    GENERATE_UUID() as provenance_uuid
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol = '^GSPC'
  AND date >= '2000-01-01'
  AND date < '2018-01-01'  -- Only backfill pre-2018
ORDER BY date;
-- Expected: ~4,300 rows

-- 10Y TREASURY YIELD (^TNX) - Interest rate benchmark
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.treasury_10y_yield` (
    time DATETIME,
    open FLOAT64,
    high FLOAT64,
    low FLOAT64,
    close FLOAT64,
    volume INT64,
    symbol STRING,
    source_name STRING,
    confidence_score FLOAT64,
    ingest_timestamp_utc TIMESTAMP,
    provenance_uuid STRING
);

INSERT INTO `cbi-v14.forecasting_data_warehouse.treasury_10y_yield`
(time, open, high, low, close, volume, symbol, source_name, confidence_score, ingest_timestamp_utc, provenance_uuid)
SELECT 
    DATETIME(date) as time,
    open,
    high,
    low,
    close,
    volume,
    'TNX' as symbol,
    'yahoo_finance_comprehensive_historical' as source_name,
    1.0 as confidence_score,
    CURRENT_TIMESTAMP() as ingest_timestamp_utc,
    GENERATE_UUID() as provenance_uuid
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol = '^TNX'
  AND date >= '2000-01-01'
  AND date < '2020-01-01'
ORDER BY date;
-- Expected: ~4,800 rows

-- ============================================================================
-- 5. VERIFICATION QUERIES
-- ============================================================================

-- Run these after backfill to verify success:

/*
-- Check row counts for all backfilled tables
SELECT 
    'soybean_prices' as table_name,
    COUNT(*) as total_rows,
    MIN(DATE(time)) as min_date,
    MAX(DATE(time)) as max_date,
    COUNTIF(source_name = 'yahoo_finance_comprehensive_historical') as yahoo_rows
FROM `cbi-v14.forecasting_data_warehouse.soybean_prices`

UNION ALL

SELECT 
    'corn_prices' as table_name,
    COUNT(*) as total_rows,
    MIN(DATE(time)) as min_date,
    MAX(DATE(time)) as max_date,
    COUNTIF(source_name = 'yahoo_finance_comprehensive_historical') as yahoo_rows
FROM `cbi-v14.forecasting_data_warehouse.corn_prices`

-- Add more verification queries as needed...

ORDER BY table_name;
*/

-- ============================================================================
-- SUMMARY
-- ============================================================================
-- This backfill will add approximately:
-- - 75,000+ historical rows across 14 tables
-- - Complete 2000-2020 coverage for major commodities
-- - Enable training on 25-year patterns
-- - Support regime-specific model training
-- - Fill critical gaps for 2008 crisis and trade war periods
-- ============================================================================
