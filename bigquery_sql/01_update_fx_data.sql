-- Step 1: Update currency data to today (if needed)
-- Note: This assumes you have a script/process to pull latest FX data
-- For now, we'll check what's available and proceed with what exists

-- Check current FX data freshness
SELECT 
  from_currency,
  to_currency,
  MAX(date) as latest_date,
  COUNT(*) as row_count
FROM `cbi-v14.forecasting_data_warehouse.currency_data`
WHERE (from_currency, to_currency) IN (('USD','ARS'),('USD','MYR'),('USD','BRL'),('USD','CNY'))
GROUP BY from_currency, to_currency
ORDER BY from_currency, to_currency;

-- If data is stale, run your FX data pipeline here
-- For now, proceeding with existing data (will update if needed)

