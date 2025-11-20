-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================================================
-- INTEGRATE YAHOO FINANCE COMPREHENSIVE HISTORICAL DATA
-- ============================================================================
-- Purpose: Create views and backfill forecasting_data_warehouse with 25 years
--          of historical data from yahoo_finance_comprehensive dataset
-- Date: November 12, 2025
-- Impact: Adds ~338K pre-2020 rows to production system
-- ============================================================================

-- ============================================================================
-- STEP 1: CREATE VIEWS IN forecasting_data_warehouse
-- ============================================================================

-- View 1: Yahoo Finance Historical (All Symbols, Normalized)
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.yahoo_finance_historical` AS
SELECT 
    date,
    symbol,
    symbol_name,
    category,
    open,
    high,
    low,
    close,
    volume,
    ma_7d,
    ma_30d,
    ma_50d,
    ma_200d,
    'yahoo_finance_comprehensive' as data_source
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE date >= '2000-01-01'
ORDER BY date, symbol;

-- View 2: Soybean Oil Prices Historical (For Backfill)
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.soybean_oil_prices_historical_view` AS
SELECT 
    date as time,  -- Match existing schema
    close,
    open,
    high,
    low,
    volume,
    symbol,
    symbol_name,
    'ZL' as source_symbol,
    'yahoo_finance_comprehensive' as source_name,
    1.0 as confidence_score,
    CURRENT_TIMESTAMP() as ingest_timestamp_utc,
    GENERATE_UUID() as provenance_uuid
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol = 'ZL=F'  -- Yahoo Finance futures notation
AND date >= '2000-01-01';

-- View 3: Biofuel Components Historical
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.biofuel_components_historical_view` AS
SELECT 
    date,
    soybean_oil_price_cwt,
    soybean_price_cents_bu,
    soybean_meal_price_ton,
    corn_price_cents_bu,
    heating_oil_price_gal,
    gasoline_price_gal,
    natural_gas_price_mmbtu,
    sugar_price_cents_lb,
    crude_oil_price_bbl,
    'yahoo_finance_comprehensive' as data_source
FROM `cbi-v14.yahoo_finance_comprehensive.biofuel_components_canonical`
WHERE date >= '2000-01-01';

-- View 4: All Symbols 20-Year Historical
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.all_symbols_20yr_view` AS
SELECT 
    date,
    symbol,
    symbol_clean,
    name,
    Open,
    High,
    Low,
    Close,
    Volume,
    ma_7d,
    ma_30d,
    ma_50d,
    rsi_14d,
    'yahoo_finance_comprehensive' as data_source
FROM `cbi-v14.yahoo_finance_comprehensive.all_symbols_20yr`
WHERE date >= '2000-01-01';

-- ============================================================================
-- STEP 2: VERIFY VIEW CREATION
-- ============================================================================

-- Check yahoo_finance_historical view
SELECT 
    'yahoo_finance_historical' as view_name,
    COUNT(*) as total_rows,
    MIN(date) as earliest_date,
    MAX(date) as latest_date,
    COUNT(DISTINCT symbol) as unique_symbols,
    COUNTIF(date < '2020-01-01') as pre_2020_rows
FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_historical`;

-- Check soybean_oil_prices_historical_view
SELECT 
    'soybean_oil_prices_historical_view' as view_name,
    COUNT(*) as total_rows,
    MIN(time) as earliest_date,
    MAX(time) as latest_date,
    COUNTIF(DATE(time) < '2020-01-01') as pre_2020_rows
FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices_historical_view`;

-- ============================================================================
-- STEP 3: BACKFILL SOYBEAN OIL PRICES (CAREFUL - CHECK FIRST)
-- ============================================================================

-- DRY RUN: Check what would be inserted
SELECT 
    'DRY_RUN: Would insert' as status,
    COUNT(*) as rows_to_insert,
    MIN(DATE(time)) as earliest_date,
    MAX(DATE(time)) as latest_date
FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices_historical_view`
WHERE DATE(time) NOT IN (
    SELECT DISTINCT DATE(time) 
    FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
    WHERE time IS NOT NULL
)
AND DATE(time) >= '2000-01-01'
AND DATE(time) < '2020-01-01';

-- ACTUAL INSERT (UNCOMMENT AFTER VERIFICATION)
/*
INSERT INTO `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
(time, close, open, high, low, volume, symbol, source_name, confidence_score, ingest_timestamp_utc, provenance_uuid)
SELECT 
    TIMESTAMP(date) as time,
    close,
    open,
    high,
    low,
    volume,
    'ZL' as symbol,  -- Standardize to ZL for production
    'yahoo_finance_comprehensive_historical' as source_name,
    1.0 as confidence_score,
    CURRENT_TIMESTAMP() as ingest_timestamp_utc,
    GENERATE_UUID() as provenance_uuid
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol = 'ZL=F'  -- Yahoo Finance futures notation
  AND date >= '2000-01-01'
  AND date < '2020-01-01'  -- SAFE: Only backfill pre-2020 (avoid overlap)
ORDER BY date;

-- Expected to insert: ~4,756 rows (2000-11-13 to 2019-12-31)
*/

-- ============================================================================
-- STEP 4: CREATE HISTORICAL REGIME TABLES
-- ============================================================================

-- Regime 1: Trade War (2017-2019)  
CREATE OR REPLACE TABLE `cbi-v14.models_v4.trade_war_2017_2019_historical` AS
SELECT *
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol = 'ZL=F'  -- Yahoo Finance futures notation
  AND date >= '2017-01-01' AND date < '2020-01-01'
ORDER BY date;

-- Regime 2: 2008 Financial Crisis
CREATE OR REPLACE TABLE `cbi-v14.models_v4.crisis_2008_historical` AS
SELECT *
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol = 'ZL=F'  -- Yahoo Finance futures notation
  AND date >= '2008-01-01' AND date < '2009-01-01'
ORDER BY date;

-- Regime 3: Pre-2008 (Calm Period)
CREATE OR REPLACE TABLE `cbi-v14.models_v4.pre_crisis_2000_2007_historical` AS
SELECT *
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol = 'ZL=F'  -- Yahoo Finance futures notation
  AND date >= '2000-01-01' AND date < '2008-01-01'
ORDER BY date;

-- Regime 4: 2010-2016 (Recovery Period)
CREATE OR REPLACE TABLE `cbi-v14.models_v4.recovery_2010_2016_historical` AS
SELECT *
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol = 'ZL=F'  -- Yahoo Finance futures notation
  AND date >= '2010-01-01' AND date < '2017-01-01'
ORDER BY date;

-- ============================================================================
-- STEP 5: VERIFY REGIME TABLES
-- ============================================================================

SELECT 
    'trade_war_2017_2019' as regime,
    COUNT(*) as rows,
    MIN(date) as start_date,
    MAX(date) as end_date,
    COUNT(DISTINCT symbol) as symbols
FROM `cbi-v14.models_v4.trade_war_2017_2019_historical`

UNION ALL

SELECT 
    'crisis_2008' as regime,
    COUNT(*) as rows,
    MIN(date) as start_date,
    MAX(date) as end_date,
    COUNT(DISTINCT symbol) as symbols
FROM `cbi-v14.models_v4.crisis_2008_historical`

UNION ALL

SELECT 
    'pre_crisis_2000_2007' as regime,
    COUNT(*) as rows,
    MIN(date) as start_date,
    MAX(date) as end_date,
    COUNT(DISTINCT symbol) as symbols
FROM `cbi-v14.models_v4.pre_crisis_2000_2007_historical`

UNION ALL

SELECT 
    'recovery_2010_2016' as regime,
    COUNT(*) as rows,
    MIN(date) as start_date,
    MAX(date) as end_date,
    COUNT(DISTINCT symbol) as symbols
FROM `cbi-v14.models_v4.recovery_2010_2016_historical`

ORDER BY start_date;

-- ============================================================================
-- STEP 6: UPDATE DATASET DESCRIPTION
-- ============================================================================

-- Add description to yahoo_finance_comprehensive dataset (run via bq CLI)
/*
bq update --description "Historical market data from Yahoo Finance (2000-2025). 
Contains 25+ years of OHLCV data, technical indicators, and biofuel components. 
Primary source for pre-2020 historical backfill.
Tables: yahoo_normalized (314K rows), all_symbols_20yr (57K rows), biofuel_components_canonical (6K rows).
Integration: Used via views in forecasting_data_warehouse." \
cbi-v14:yahoo_finance_comprehensive
*/

-- ============================================================================
-- COMPLETION CHECKLIST
-- ============================================================================

-- [ ] Views created in forecasting_data_warehouse
-- [ ] Views verified with row counts
-- [ ] Dry run of soybean_oil_prices backfill successful
-- [ ] Actual backfill executed (if approved)
-- [ ] Historical regime tables created
-- [ ] Regime tables verified
-- [ ] Dataset description updated
-- [ ] Documentation updated (QUICK_REFERENCE.txt)
-- [ ] Integration validated

-- ============================================================================
-- END OF INTEGRATION SCRIPT
-- ============================================================================

