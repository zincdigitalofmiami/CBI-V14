-- Step 6: Rebuild training_dataset_super_enriched
-- Strategy: Start from backup structure, update with fresh data, add 2 FX columns

-- Get all column names from backup (excluding targets for now)
-- We'll rebuild by selecting from backup and joining fresh sources

-- Phase 1: Create wide view that combines backup structure with fresh data
CREATE OR REPLACE VIEW `cbi-v14.models_v4.vw_training_rebuild` AS
WITH backup_data AS (
  SELECT * FROM `cbi-v14.models_v4.training_dataset_backup_20251028`
),
fx_fresh AS (
  SELECT * FROM `cbi-v14.models_v4.vw_fx_all`
),
big8_fresh AS (
  SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched`
)
SELECT 
  -- Use backup columns (207) plus add 2 FX z-scores
  b.*,
  fx.fx_usd_ars_30d_z,
  fx.fx_usd_myr_30d_z
FROM backup_data b
LEFT JOIN fx_fresh fx ON b.date = fx.date
LEFT JOIN big8_fresh big8 ON b.date = big8.date
-- Update Big-8 features from fresh source
WHERE b.date <= CURRENT_DATE()
ORDER BY b.date DESC;

-- Note: This approach preserves backup structure while adding fresh FX
-- We'll materialize this after verifying it has all 209 columns

