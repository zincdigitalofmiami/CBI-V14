-- EXECUTE REBUILD: Copy backup + add 2 FX columns = 209 columns
-- This preserves ALL column names exactly as trained
-- We'll extend dates forward in a separate step

CREATE OR REPLACE TABLE `cbi-v14.models_v4.training_dataset_super_enriched` AS
SELECT 
  b.*,
  COALESCE(fx.fx_usd_ars_30d_z, CAST(NULL AS FLOAT64)) AS fx_usd_ars_30d_z,
  COALESCE(fx.fx_usd_myr_30d_z, CAST(NULL AS FLOAT64)) AS fx_usd_myr_30d_z
FROM `cbi-v14.models_v4.training_dataset_backup_20251028` b
LEFT JOIN `cbi-v14.models_v4.vw_fx_all` fx ON b.date = fx.date;

-- Verify column count
SELECT 
  COUNT(*) as total_columns,
  COUNTIF(column_name LIKE 'target%') as target_columns,
  COUNTIF(column_name NOT LIKE 'target%') as feature_columns
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'training_dataset_super_enriched'
  AND table_schema = 'models_v4';



