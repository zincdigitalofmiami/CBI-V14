CREATE OR REPLACE VIEW `cbi-v14.curated.vw_commodity_prices_daily`
OPTIONS(
  friendly_name="vw_commodity_prices_daily",
  description="Unified daily commodity prices from all price tables. Combines soybean oil, soybeans, soybean meal, corn, cotton, cocoa, palm oil, wheat, crude oil, natural gas, gold, USD index, canola oil, and sunflower oil prices."
)
AS
WITH all_commodity_prices AS (
  -- Core soybean complex (time column)
  SELECT 
    time,
    symbol,
    open,
    high,
    low,
    close,
    volume,
    source_name,
    confidence_score,
    ingest_timestamp_utc,
    provenance_uuid,
    'soybean_oil' as commodity_group
  FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
  WHERE symbol = 'ZL'
  
  UNION ALL
  
  SELECT 
    time,
    symbol,
    open,
    high,
    low,
    close,
    volume,
    source_name,
    confidence_score,
    ingest_timestamp_utc,
    provenance_uuid,
    'soybean_complex' as commodity_group
  FROM `cbi-v14.forecasting_data_warehouse.soybean_prices`
  WHERE symbol = 'ZS'
  
  UNION ALL
  
  SELECT 
    time,
    symbol,
    open,
    high,
    low,
    close,
    volume,
    source_name,
    confidence_score,
    ingest_timestamp_utc,
    provenance_uuid,
    'soybean_complex' as commodity_group
  FROM `cbi-v14.forecasting_data_warehouse.soybean_meal_prices`
  WHERE symbol = 'ZM'
  
  UNION ALL
  
  SELECT 
    time,
    symbol,
    open,
    high,
    low,
    close,
    volume,
    source_name,
    confidence_score,
    ingest_timestamp_utc,
    provenance_uuid,
    'grains' as commodity_group
  FROM `cbi-v14.forecasting_data_warehouse.corn_prices`
  WHERE symbol = 'ZC'
  
  UNION ALL
  
  SELECT 
    time,
    symbol,
    open,
    high,
    low,
    close,
    volume,
    source_name,
    confidence_score,
    ingest_timestamp_utc,
    provenance_uuid,
    'grains' as commodity_group
  FROM `cbi-v14.forecasting_data_warehouse.cotton_prices`
  WHERE symbol = 'CT'
  
  UNION ALL
  
  -- Soft commodities
  SELECT 
    time,
    symbol,
    open,
    high,
    low,
    close,
    volume,
    source_name,
    confidence_score,
    ingest_timestamp_utc,
    provenance_uuid,
    'soft_commodities' as commodity_group
  FROM `cbi-v14.forecasting_data_warehouse.cocoa_prices`
  WHERE symbol = 'CC'
  
  UNION ALL
  
  -- Vegetable oils (palm oil has only close price)
  SELECT 
    time,
    symbol,
    NULL as open,
    NULL as high,
    NULL as low,
    close,
    NULL as volume,
    source_name,
    confidence_score,
    ingest_timestamp_utc,
    provenance_uuid,
    'vegetable_oils' as commodity_group
  FROM `cbi-v14.forecasting_data_warehouse.palm_oil_prices`
  WHERE symbol = 'FCPO'
  
  UNION ALL
  
  -- New tables with date column and different field names
  SELECT 
    TIMESTAMP(date) as time,
    symbol,
    open_price as open,
    high_price as high,
    low_price as low,
    close_price as close,
    volume,
    source_name,
    confidence_score,
    ingest_timestamp_utc,
    provenance_uuid,
    'grains' as commodity_group
  FROM `cbi-v14.forecasting_data_warehouse.wheat_prices`
  WHERE symbol = 'ZW'
  
  UNION ALL
  
  SELECT 
    TIMESTAMP(date) as time,
    symbol,
    open_price as open,
    high_price as high,
    low_price as low,
    close_price as close,
    volume,
    source_name,
    confidence_score,
    ingest_timestamp_utc,
    provenance_uuid,
    'energy' as commodity_group
  FROM `cbi-v14.forecasting_data_warehouse.crude_oil_prices`
  WHERE symbol = 'CL'
  
  UNION ALL
  
  SELECT 
    TIMESTAMP(date) as time,
    symbol,
    open_price as open,
    high_price as high,
    low_price as low,
    close_price as close,
    volume,
    source_name,
    confidence_score,
    ingest_timestamp_utc,
    provenance_uuid,
    'energy' as commodity_group
  FROM `cbi-v14.forecasting_data_warehouse.natural_gas_prices`
  WHERE symbol = 'NG'
  
  UNION ALL
  
  SELECT 
    TIMESTAMP(date) as time,
    symbol,
    open_price as open,
    high_price as high,
    low_price as low,
    close_price as close,
    volume,
    source_name,
    confidence_score,
    ingest_timestamp_utc,
    provenance_uuid,
    'metals' as commodity_group
  FROM `cbi-v14.forecasting_data_warehouse.gold_prices`
  WHERE symbol = 'GC'
  
  UNION ALL
  
  SELECT 
    TIMESTAMP(date) as time,
    symbol,
    open_price as open,
    high_price as high,
    low_price as low,
    close_price as close,
    volume,
    source_name,
    confidence_score,
    ingest_timestamp_utc,
    provenance_uuid,
    'currency' as commodity_group
  FROM `cbi-v14.forecasting_data_warehouse.usd_index_prices`
  WHERE symbol = 'DX'
  
  UNION ALL
  
  SELECT 
    TIMESTAMP(date) as time,
    symbol,
    open_price as open,
    high_price as high,
    low_price as low,
    close_price as close,
    volume,
    source_name,
    confidence_score,
    ingest_timestamp_utc,
    provenance_uuid,
    'vegetable_oils' as commodity_group
  FROM `cbi-v14.forecasting_data_warehouse.canola_oil_prices`
  WHERE symbol = 'RS'
  
  UNION ALL
  
  SELECT 
    TIMESTAMP(date) as time,
    symbol,
    open_price as open,
    high_price as high,
    low_price as low,
    close_price as close,
    volume,
    source_name,
    confidence_score,
    ingest_timestamp_utc,
    provenance_uuid,
    'vegetable_oils' as commodity_group
  FROM `cbi-v14.forecasting_data_warehouse.sunflower_oil_prices`
  WHERE symbol = 'BO'
)
SELECT 
  time,
  symbol,
  open,
  high,
  low,
  close,
  volume,
  source_name,
  confidence_score,
  ingest_timestamp_utc,
  provenance_uuid,
  commodity_group,
  -- Add calculated fields
  CASE 
    WHEN LAG(close) OVER (PARTITION BY symbol ORDER BY time) IS NOT NULL 
    THEN close - LAG(close) OVER (PARTITION BY symbol ORDER BY time)
    ELSE NULL 
  END as price_change,
  CASE 
    WHEN LAG(close) OVER (PARTITION BY symbol ORDER BY time) IS NOT NULL 
    THEN ROUND((close - LAG(close) OVER (PARTITION BY symbol ORDER BY time)) / LAG(close) OVER (PARTITION BY symbol ORDER BY time) * 100, 4)
    ELSE NULL 
  END as price_change_pct
FROM all_commodity_prices
ORDER BY time DESC, commodity_group, symbol;
