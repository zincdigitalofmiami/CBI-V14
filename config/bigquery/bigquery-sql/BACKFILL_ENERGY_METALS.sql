-- ============================================================================
-- BACKFILL ENERGY, METALS, AND MARKET INDICATORS
-- Handles correct data types for each table
-- ============================================================================

-- CRUDE OIL (CL=F) - Uses DATE for time column, INT64 for open/high/low
INSERT INTO `cbi-v14.forecasting_data_warehouse.crude_oil_prices`
(time, open, high, low, close, volume, symbol, source_name, confidence_score, ingest_timestamp_utc, provenance_uuid)
SELECT 
    date as time,
    CAST(open AS INT64) as open,
    CAST(high AS INT64) as high,
    CAST(low AS INT64) as low,
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

-- NATURAL GAS (NG=F) - Uses DATE for time column, INT64 for open/high/low
INSERT INTO `cbi-v14.forecasting_data_warehouse.natural_gas_prices`
(time, open, high, low, close, volume, symbol, source_name, confidence_score, ingest_timestamp_utc, provenance_uuid)
SELECT 
    date as time,
    CAST(open AS INT64) as open,
    CAST(high AS INT64) as high,
    CAST(low AS INT64) as low,
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

-- GOLD (GC=F) - Uses DATE for time column, INT64 for open/high/low
INSERT INTO `cbi-v14.forecasting_data_warehouse.gold_prices`
(time, open, high, low, close, volume, symbol, source_name, confidence_score, ingest_timestamp_utc, provenance_uuid)
SELECT 
    date as time,
    CAST(open AS INT64) as open,
    CAST(high AS INT64) as high,
    CAST(low AS INT64) as low,
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

-- USD INDEX (DX-Y.NYB) - Uses DATE for time column, INT64 for open/high/low
INSERT INTO `cbi-v14.forecasting_data_warehouse.usd_index_prices`
(time, open, high, low, close, volume, symbol, source_name, confidence_score, ingest_timestamp_utc, provenance_uuid)
SELECT 
    date as time,
    CAST(open AS INT64) as open,
    CAST(high AS INT64) as high,
    CAST(low AS INT64) as low,
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

-- S&P 500 (^GSPC) - Uses DATETIME for time column (backfill pre-2018)
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
  AND date < '2018-01-01'
ORDER BY date;

-- VIX (^VIX) - Uses DATE for date column (not time!), no source_name (backfill pre-2015)
INSERT INTO `cbi-v14.forecasting_data_warehouse.vix_daily`
(date, open, high, low, close, volume, symbol)
SELECT 
    date,
    open,
    high,
    low,
    close,
    volume,
    'VIX' as symbol
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol = '^VIX'
  AND date >= '2000-01-01'
  AND date < '2015-01-01'
ORDER BY date;

-- Create silver_prices table if it doesn't exist
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.silver_prices` (
    time DATE,
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

-- SILVER (SI=F)
INSERT INTO `cbi-v14.forecasting_data_warehouse.silver_prices`
(time, open, high, low, close, volume, symbol, source_name, confidence_score, ingest_timestamp_utc, provenance_uuid)
SELECT 
    date as time,
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

-- Create copper_prices table if it doesn't exist
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.copper_prices` (
    time DATE,
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

-- COPPER (HG=F)
INSERT INTO `cbi-v14.forecasting_data_warehouse.copper_prices`
(time, open, high, low, close, volume, symbol, source_name, confidence_score, ingest_timestamp_utc, provenance_uuid)
SELECT 
    date as time,
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
