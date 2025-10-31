-- Step 3: Capture schema contract from backup (207 columns)
CREATE OR REPLACE TABLE `cbi-v14.models_v4._contract_207` AS
SELECT 
  column_name, 
  data_type
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_schema = 'models_v4'
  AND table_name = 'training_dataset_backup_20251028'
  AND column_name NOT IN ('_PARTITIONDATE', '_PARTITIONTIME');

-- Add 2 FX columns to reach 209
CREATE OR REPLACE TABLE `cbi-v14.models_v4._contract_209` AS
SELECT * FROM `cbi-v14.models_v4._contract_207`
UNION ALL 
SELECT 'fx_usd_ars_30d_z' AS column_name, 'FLOAT64' AS data_type
UNION ALL 
SELECT 'fx_usd_myr_30d_z' AS column_name, 'FLOAT64' AS data_type;

-- Verify contract
SELECT COUNT(*) as contract_column_count FROM `cbi-v14.models_v4._contract_209`;

