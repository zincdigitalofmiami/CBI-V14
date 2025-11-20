-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================================================
-- BACKFILL AGRICULTURAL COMMODITIES ONLY
-- These are the most critical for soybean oil forecasting
-- ============================================================================

-- SOYBEANS (ZS=F)
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

-- CORN (ZC=F)
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

-- WHEAT (ZW=F)
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

-- SOYBEAN MEAL (ZM=F) - Uses TIMESTAMP
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
