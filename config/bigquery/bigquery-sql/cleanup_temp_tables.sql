-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- CLEANUP TEMP TABLES CREATED DURING DEVELOPMENT
-- ============================================

-- Drop all temp tables created during Big8 signal work
DROP TABLE IF EXISTS `cbi-v14.models_v4.temp_vix_stress_historical`;
DROP TABLE IF EXISTS `cbi-v14.models_v4.temp_harvest_pace_historical`;
DROP TABLE IF EXISTS `cbi-v14.models_v4.temp_china_relations_historical`;
DROP TABLE IF EXISTS `cbi-v14.models_v4.temp_tariff_threat_historical`;
DROP TABLE IF EXISTS `cbi-v14.models_v4.temp_geopolitical_volatility_historical`;
DROP TABLE IF EXISTS `cbi-v14.models_v4.temp_biofuel_cascade_historical`;
DROP TABLE IF EXISTS `cbi-v14.models_v4.temp_hidden_correlation_historical`;
DROP TABLE IF EXISTS `cbi-v14.models_v4.temp_biofuel_ethanol_historical`;

-- Also drop the prediction temp table that was created
DROP TABLE IF EXISTS `cbi-v14.models_v4.temp_prediction_input_1w`;

-- Verify cleanup
SELECT
  'Cleanup Complete' as status,
  (SELECT COUNT(*) FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.TABLES`
   WHERE table_name LIKE 'temp_%') as remaining_temp_tables;


