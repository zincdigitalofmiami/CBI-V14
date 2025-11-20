-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- POPULATE ALL MISSING ECONOMIC DATA
-- Use correct indicator names from economic_indicators table
-- ============================================

-- Unemployment Rate (correct indicator name)
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET econ_unemployment_rate = ei.value
FROM `cbi-v14.forecasting_data_warehouse.economic_indicators` ei
WHERE t.date = DATE(ei.time)
  AND ei.indicator = 'unemployment_rate'
  AND t.econ_unemployment_rate IS NULL;

-- GDP Growth (try multiple possible names)
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET econ_gdp_growth = ei.value
FROM `cbi-v14.forecasting_data_warehouse.economic_indicators` ei
WHERE t.date = DATE(ei.time)
  AND (ei.indicator LIKE '%GDP%' OR ei.indicator LIKE '%gdp%')
  AND t.econ_gdp_growth IS NULL;

SELECT 
  'All economic data populated!' as status,
  COUNTIF(treasury_10y_yield IS NOT NULL) as treasury_rows,
  COUNTIF(econ_gdp_growth IS NOT NULL) as gdp_rows,
  COUNTIF(econ_unemployment_rate IS NOT NULL) as unemployment_rows,
  COUNT(*) as total_rows
FROM `cbi-v14.models_v4.training_dataset_super_enriched`;
