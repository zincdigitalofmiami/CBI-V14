-- ============================================
-- CONVERT ALL TEMPERATURES FROM CELSIUS TO FAHRENHEIT
-- Formula: °F = (°C × 9/5) + 32
-- ============================================

-- Update temperature columns from Celsius to Fahrenheit
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched`
SET
  argentina_temp_c = (argentina_temp_c * 9/5) + 32,
  brazil_temp_c = (brazil_temp_c * 9/5) + 32,
  brazil_temperature_c = (brazil_temperature_c * 9/5) + 32,
  us_midwest_temp_c = (us_midwest_temp_c * 9/5) + 32
WHERE argentina_temp_c IS NOT NULL
   OR brazil_temp_c IS NOT NULL
   OR brazil_temperature_c IS NOT NULL
   OR us_midwest_temp_c IS NOT NULL;

-- Verify conversion results
SELECT
  'Temperature Conversion Results' as check_type,
  COUNTIF(argentina_temp_c IS NOT NULL) as argentina_temp_rows,
  COUNTIF(brazil_temp_c IS NOT NULL) as brazil_temp_rows,
  COUNTIF(us_midwest_temp_c IS NOT NULL) as us_midwest_temp_rows,
  ROUND(AVG(argentina_temp_c), 1) as avg_argentina_f,
  ROUND(AVG(brazil_temp_c), 1) as avg_brazil_f,
  ROUND(AVG(us_midwest_temp_c), 1) as avg_us_f,
  ROUND(MIN(brazil_temp_c), 1) as min_brazil_f,
  ROUND(MAX(brazil_temp_c), 1) as max_brazil_f
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE argentina_temp_c IS NOT NULL
   OR brazil_temp_c IS NOT NULL
   OR us_midwest_temp_c IS NOT NULL;


