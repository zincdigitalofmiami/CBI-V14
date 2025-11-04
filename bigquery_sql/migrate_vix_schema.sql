-- ============================================
-- MIGRATE VIX SCHEMA TO PROPERLY CLASSIFY AS INDEX
-- Add asset_type field and clarify VIX is a volatility index, not a price
-- ============================================

-- Add asset_type column to hourly_prices table
ALTER TABLE `cbi-v14.market_data.hourly_prices`
ADD COLUMN IF NOT EXISTS asset_type STRING;

-- Update existing data to classify asset types
UPDATE `cbi-v14.market_data.hourly_prices`
SET asset_type = CASE
  WHEN symbol IN ('^VIX', 'VIX') THEN 'volatility_index'
  WHEN symbol LIKE '%=F' THEN 'commodity_future'
  ELSE 'unknown'
END
WHERE asset_type IS NULL;

-- Add comments to clarify the schema
-- Note: VIX represents the CBOE Volatility Index, which measures
-- expected market volatility over the next 30 days, not a tradable asset price

-- Verify the migration
SELECT
  'VIX Schema Migration Results' as check_type,
  asset_type,
  COUNT(*) as record_count,
  COUNT(DISTINCT symbol) as unique_symbols,
  ROUND(AVG(CASE WHEN asset_type = 'volatility_index' THEN price END), 2) as avg_vix_value,
  ROUND(AVG(CASE WHEN asset_type = 'commodity_future' THEN price END), 2) as avg_commodity_price
FROM `cbi-v14.market_data.hourly_prices`
WHERE asset_type IS NOT NULL
GROUP BY asset_type
ORDER BY asset_type;

-- Show VIX data specifically
SELECT
  'VIX Data Verification' as check_type,
  symbol,
  asset_type,
  COUNT(*) as records,
  ROUND(MIN(price), 2) as min_value,
  ROUND(MAX(price), 2) as max_value,
  ROUND(AVG(price), 2) as avg_value,
  MAX(timestamp) as latest_timestamp
FROM `cbi-v14.market_data.hourly_prices`
WHERE symbol IN ('^VIX', 'VIX')
GROUP BY symbol, asset_type;

