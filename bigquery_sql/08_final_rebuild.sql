-- FINAL REBUILD: Copy backup + add 2 FX columns + extend forward
-- CRITICAL: This preserves ALL 207 columns from backup + adds 2 = 209 total

-- Step 1: Create table with backup structure + 2 FX columns
CREATE OR REPLACE TABLE `cbi-v14.models_v4.training_dataset_super_enriched` AS
SELECT 
  b.*,
  COALESCE(fx.fx_usd_ars_30d_z, CAST(NULL AS FLOAT64)) AS fx_usd_ars_30d_z,
  COALESCE(fx.fx_usd_myr_30d_z, CAST(NULL AS FLOAT64)) AS fx_usd_myr_30d_z
FROM `cbi-v14.models_v4.training_dataset_backup_20251028` b
LEFT JOIN `cbi-v14.models_v4.vw_fx_all` fx ON b.date = fx.date;

-- Step 2: Extend forward with fresh Big-8 data (for dates after backup)
-- Note: Other columns will be NULL but structure preserved
INSERT INTO `cbi-v14.models_v4.training_dataset_super_enriched`
SELECT 
  f.date,
  -- Big-8 features (fresh)
  f.feature_vix_stress,
  f.feature_harvest_pace,
  f.feature_china_relations,
  f.feature_tariff_threat,
  f.feature_geopolitical_volatility,
  f.feature_biofuel_cascade,
  f.feature_hidden_correlation,
  f.feature_biofuel_ethanol,
  f.big8_composite_score,
  f.market_regime,
  -- All other columns NULL (preserve structure)
  -- We need to list ALL 207 columns here...
  -- This is complex - let me use a different approach

-- Better: Copy structure from backup, then UNION ALL fresh rows with NULLs for missing features

