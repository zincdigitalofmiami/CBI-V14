-- ============================================
-- POPULATE TREASURY 10Y YIELD DATA
-- Join from treasury_prices table to training dataset
-- ============================================

UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET treasury_10y_yield = tp.close
FROM `cbi-v14.forecasting_data_warehouse.treasury_prices` tp
WHERE t.date = tp.date
  AND tp.symbol = '^TNX'
  AND t.treasury_10y_yield IS NULL;

SELECT 
  'Treasury 10y yield populated!' as status,
  COUNTIF(treasury_10y_yield IS NOT NULL) as populated_rows,
  COUNT(*) as total_rows
FROM `cbi-v14.models_v4.training_dataset_super_enriched`;

