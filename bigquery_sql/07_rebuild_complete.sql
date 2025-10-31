-- Step 7: Rebuild training_dataset_super_enriched 
-- Strategy: Copy backup structure (207 cols) + add 2 FX cols = 209 cols
-- Extend dates forward using available sources
-- CRITICAL: Match column names EXACTLY - no dropping columns

-- First, create anchor view
CREATE OR REPLACE VIEW `cbi-v14.models_v4.vw_anchor` AS
SELECT DISTINCT DATE(time) AS date
FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
WHERE time IS NOT NULL AND DATE(time) <= CURRENT_DATE();

-- Rebuild: Copy backup structure + add 2 FX columns + extend forward
-- For columns we can't compute, use NULL (but keep the column to match contract)

CREATE OR REPLACE TABLE `cbi-v14.models_v4.training_dataset_super_enriched` AS
WITH backup_data AS (
  -- Get all 207 columns from backup
  SELECT * FROM `cbi-v14.models_v4.training_dataset_backup_20251028`
),
backup_max_date AS (
  SELECT MAX(date) as max_date FROM backup_data
),
fx_data AS (
  SELECT * FROM `cbi-v14.models_v4.vw_fx_all`
),
fresh_big8 AS (
  SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE date > (SELECT max_date FROM backup_max_date)
),
all_dates AS (
  SELECT date FROM `cbi-v14.models_v4.vw_anchor`
)
SELECT 
  -- All columns from backup (matching contract exactly)
  b.*,
  -- Add 2 missing FX columns
  COALESCE(fx.fx_usd_ars_30d_z, NULL) AS fx_usd_ars_30d_z,
  COALESCE(fx.fx_usd_myr_30d_z, NULL) AS fx_usd_myr_30d_z
FROM all_dates d
LEFT JOIN backup_data b ON d.date = b.date
LEFT JOIN fx_data fx ON d.date = fx.date
WHERE d.date <= (SELECT max_date FROM backup_max_date)

UNION ALL

-- Add fresh rows (from backup_max_date + 1 to today)
SELECT 
  -- Use fresh Big-8 where available, NULL for other columns we can't compute
  f.date,
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
  -- All other columns NULL (we'll populate incrementally)
  CAST(NULL AS FLOAT64) AS zl_price_current,
  -- ... need to add all other columns as NULL
  -- Then add 2 FX columns
  COALESCE(fx.fx_usd_ars_30d_z, NULL) AS fx_usd_ars_30d_z,
  COALESCE(fx.fx_usd_myr_30d_z, NULL) AS fx_usd_myr_30d_z
FROM all_dates d
LEFT JOIN fresh_big8 f ON d.date = f.date
LEFT JOIN fx_data fx ON d.date = fx.date
WHERE d.date > (SELECT max_date FROM backup_max_date)
  AND f.date IS NOT NULL;

-- This approach is incomplete - need to list ALL 207 columns explicitly
-- Better approach: Use backup as-is, then UNION with fresh Big-8 rows

