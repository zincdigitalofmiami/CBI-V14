-- ============================================
-- POPULATE ECONOMIC INDICATORS FROM ECONOMIC_INDICATORS TABLE
-- Join GDP, unemployment, and other economic data
-- ============================================

-- GDP Growth
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET econ_gdp_growth = ei.value
FROM `cbi-v14.forecasting_data_warehouse.economic_indicators` ei
WHERE t.date = DATE(ei.time)
  AND ei.indicator = 'GDP'
  AND t.econ_gdp_growth IS NULL;

-- Unemployment Rate
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET econ_unemployment_rate = ei.value
FROM `cbi-v14.forecasting_data_warehouse.economic_indicators` ei
WHERE t.date = DATE(ei.time)
  AND ei.indicator = 'UNRATE'
  AND t.econ_unemployment_rate IS NULL;

SELECT 
  'Economic indicators populated!' as status,
  COUNTIF(econ_gdp_growth IS NOT NULL) as gdp_rows,
  COUNTIF(econ_unemployment_rate IS NOT NULL) as unemployment_rows,
  COUNT(*) as total_rows
FROM `cbi-v14.models_v4.training_dataset_super_enriched`;


