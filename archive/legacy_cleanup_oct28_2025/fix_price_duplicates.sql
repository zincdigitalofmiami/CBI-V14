-- FIX PRICE TABLE DUPLICATES
-- Date: October 27, 2025
-- Purpose: Remove 16 duplicate rows from 3 price tables

-- Fix soybean_oil_prices (1 duplicate on 2025-10-27)
CREATE OR REPLACE TABLE `cbi-v14.forecasting_data_warehouse.soybean_oil_prices` AS
SELECT * EXCEPT(row_num)
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY DATE(time) ORDER BY time) as row_num
  FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
)
WHERE row_num = 1;

-- Fix corn_prices (1 duplicate on 2025-10-27)
CREATE OR REPLACE TABLE `cbi-v14.forecasting_data_warehouse.corn_prices` AS
SELECT * EXCEPT(row_num)
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY DATE(time) ORDER BY time) as row_num
  FROM `cbi-v14.forecasting_data_warehouse.corn_prices`
)
WHERE row_num = 1;

-- Fix soybean_prices (12 duplicates on Oct 22-24, 27)
CREATE OR REPLACE TABLE `cbi-v14.forecasting_data_warehouse.soybean_prices` AS
SELECT * EXCEPT(row_num)
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY DATE(time) ORDER BY time) as row_num
  FROM `cbi-v14.forecasting_data_warehouse.soybean_prices`
)
WHERE row_num = 1;

-- Verify fixes
SELECT 
  'soybean_oil_prices' as table_name,
  COUNT(*) as total_rows,
  COUNT(DISTINCT DATE(time)) as unique_dates,
  COUNT(*) - COUNT(DISTINCT DATE(time)) as remaining_duplicates
FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`

UNION ALL

SELECT 
  'corn_prices',
  COUNT(*),
  COUNT(DISTINCT DATE(time)),
  COUNT(*) - COUNT(DISTINCT DATE(time))
FROM `cbi-v14.forecasting_data_warehouse.corn_prices`

UNION ALL

SELECT 
  'soybean_prices',
  COUNT(*),
  COUNT(DISTINCT DATE(time)),
  COUNT(*) - COUNT(DISTINCT DATE(time))
FROM `cbi-v14.forecasting_data_warehouse.soybean_prices`;




