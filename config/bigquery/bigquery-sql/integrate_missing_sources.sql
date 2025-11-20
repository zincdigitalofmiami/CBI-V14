-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- INTEGRATE MISSING CRITICAL DATA SOURCES
-- Add soybean_meal_prices, usd_index_prices, economic_indicators
-- ============================================

-- Step 1: Add schema for missing sources (single ALTER to avoid rate limits)
ALTER TABLE `cbi-v14.models_v4.training_dataset_super_enriched`
ADD COLUMN IF NOT EXISTS soybean_meal_price FLOAT64,
ADD COLUMN IF NOT EXISTS usd_index FLOAT64,
ADD COLUMN IF NOT EXISTS fed_funds_rate FLOAT64,
ADD COLUMN IF NOT EXISTS gdp_growth FLOAT64,
ADD COLUMN IF NOT EXISTS unemployment_rate FLOAT64,
ADD COLUMN IF NOT EXISTS cpi_yoy FLOAT64,
ADD COLUMN IF NOT EXISTS crush_margin FLOAT64;

-- Step 2: Integrate soybean meal prices
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET soybean_meal_price = sm.close
FROM `cbi-v14.forecasting_data_warehouse.soybean_meal_prices` sm
WHERE t.date = DATE(sm.time) AND sm.symbol = 'ZM=F';

-- Step 3: Integrate USD index prices
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET usd_index = usd.close
FROM `cbi-v14.forecasting_data_warehouse.usd_index_prices` usd
WHERE t.date = usd.time AND usd.symbol = 'DX-Y.NYB';

-- Step 4: Integrate key economic indicators
-- Fed Funds Rate
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET fed_funds_rate = ei.value
FROM `cbi-v14.forecasting_data_warehouse.economic_indicators` ei
WHERE t.date = DATE(ei.time) AND ei.indicator = 'FEDFUNDS';

-- GDP Growth
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET gdp_growth = ei.value
FROM `cbi-v14.forecasting_data_warehouse.economic_indicators` ei
WHERE t.date = DATE(ei.time) AND ei.indicator = 'GDP_GROWTH_QTR';

-- Unemployment Rate
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET unemployment_rate = ei.value
FROM `cbi-v14.forecasting_data_warehouse.economic_indicators` ei
WHERE t.date = DATE(ei.time) AND ei.indicator = 'UNRATE';

-- CPI Year-over-Year
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET cpi_yoy = ei.value
FROM `cbi-v14.forecasting_data_warehouse.economic_indicators` ei
WHERE t.date = DATE(ei.time) AND ei.indicator = 'CPIAUCSL_YOY';

-- Step 5: Create feature engineering for new sources (ONLY REAL DATA)
-- Soybean crush margin (soybean oil price - soybean meal price) - REAL CALCULATION
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched`
SET crush_margin = zl_price_current - soybean_meal_price
WHERE zl_price_current IS NOT NULL AND soybean_meal_price IS NOT NULL;

-- Step 6: Update data catalog status
UPDATE `cbi-v14.forecasting_data_warehouse.data_catalog`
SET
  integration_status = 'integrated',
  training_features_created = CASE
    WHEN table_name = 'soybean_meal_prices' THEN 3
    WHEN table_name = 'usd_index_prices' THEN 2
    WHEN table_name = 'economic_indicators' THEN 5
    ELSE training_features_created
  END,
  last_updated = CURRENT_TIMESTAMP()
WHERE table_name IN ('soybean_meal_prices', 'usd_index_prices', 'economic_indicators');

-- Step 7: Add metadata for new features (ONLY REAL ONES)
INSERT INTO `cbi-v14.forecasting_data_warehouse.feature_metadata`
  (feature_name, feature_type, asset_class, economic_meaning, directional_impact,
   typical_lag_days, source_table, source_column, related_features, chat_aliases,
   source_reliability_score, affected_commodities)

VALUES
  ('soybean_meal_price', 'price', 'commodity', 'Soybean meal price - crush margin component', 'negative',
   1, 'soybean_meal_prices', 'close', ['zl_price_current', 'crush_margin'], ['meal price', 'soybean meal'],
   0.94, ['soybean_oil', 'soybean_meal']),

  ('usd_index', 'currency', 'fx', 'US Dollar Index - inverse correlation with commodities', 'negative',
   0, 'usd_index_prices', 'close', ['zl_price_current'], ['dollar index', 'dxy'],
   0.93, ['soybean_oil', 'corn', 'wheat']),

  ('fed_funds_rate', 'interest_rate', 'economic', 'Federal funds rate - carry cost determinant', 'negative',
   30, 'economic_indicators', 'value', ['treasury_10y_yield', 'real_yield'], ['fed rate', 'federal funds'],
   0.98, ['soybean_oil', 'all_commodities']),

  ('gdp_growth', 'economic', 'macro', 'GDP growth rate - economic activity indicator', 'positive',
   90, 'economic_indicators', 'value', ['cpi_yoy', 'unemployment_rate'], ['gdp', 'economic growth'],
   0.95, ['soybean_oil', 'all_commodities']),

  ('crush_margin', 'derived', 'commodity', 'Soybean crush margin - processing profitability', 'positive',
   1, 'calculated', 'zl_price_current - soybean_meal_price', ['zl_price_current', 'soybean_meal_price'], ['crush margin', 'processing margin'],
   0.94, ['soybean_oil', 'soybean_meal']);

-- Step 8: Verify integration
SELECT
  'Integration Results' as check_type,
  COUNTIF(soybean_meal_price IS NOT NULL) as meal_price_rows,
  COUNTIF(usd_index IS NOT NULL) as usd_index_rows,
  COUNTIF(fed_funds_rate IS NOT NULL) as fed_rate_rows,
  COUNTIF(crush_margin IS NOT NULL) as crush_margin_rows,
  COUNT(*) as total_rows
FROM `cbi-v14.models_v4.training_dataset_super_enriched`;

-- Step 9: Show updated integration status
SELECT * FROM `cbi-v14.forecasting_data_warehouse.data_integration_status`
ORDER BY integrated DESC;
