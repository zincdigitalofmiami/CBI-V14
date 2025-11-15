-- Migration Fix: Create missing raw_intelligence table
-- This script was missed during the main migration.

CREATE OR REPLACE TABLE `cbi-v14.raw_intelligence.commodity_soybean_oil_prices`
PARTITION BY
  DATE(time)
CLUSTER BY
  symbol
AS
SELECT *
FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`;
