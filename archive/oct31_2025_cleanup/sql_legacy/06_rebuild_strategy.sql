-- Step 6: Rebuild strategy - Use backup as template, update with fresh data
-- CRITICAL: Match column names EXACTLY from contract (no dropping columns)

-- Strategy:
-- 1. Start with backup table structure (207 columns from 2025-10-13)
-- 2. Extend backup data forward to today using fresh sources
-- 3. Add 2 missing FX columns (fx_usd_ars_30d_z, fx_usd_myr_30d_z)
-- 4. Result: 209 columns, fresh to today

-- First, check what dates we need to fill
WITH backup_max AS (
  SELECT MAX(date) as max_date FROM `cbi-v14.models_v4.training_dataset_backup_20251028`
),
dates_needed AS (
  SELECT date
  FROM `cbi-v14.models_v4.vw_anchor`
  WHERE date > (SELECT max_date FROM backup_max)
)
SELECT 
  COUNT(*) as days_to_fill,
  MIN(date) as first_missing_date,
  MAX(date) as last_missing_date
FROM dates_needed;

-- For now, we'll rebuild by:
-- 1. Taking backup structure
-- 2. Adding rows from backup_max_date + 1 to today
-- 3. Computing features from fresh sources
-- 4. Adding 2 FX columns

-- This is complex - need to check if there's a simpler approach

