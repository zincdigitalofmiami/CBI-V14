-- FINAL REBUILD: Copy backup + add 2 FX columns + extend forward
-- CRITICAL: Preserves ALL 207 columns from backup + adds 2 = 209 total
-- Matches contract EXACTLY - no dropping columns

-- Step 1: Create table with backup structure + 2 FX columns (historical data)
CREATE OR REPLACE TABLE `cbi-v14.models_v4.training_dataset_super_enriched` AS
SELECT 
  b.*,
  COALESCE(fx.fx_usd_ars_30d_z, CAST(NULL AS FLOAT64)) AS fx_usd_ars_30d_z,
  COALESCE(fx.fx_usd_myr_30d_z, CAST(NULL AS FLOAT64)) AS fx_usd_myr_30d_z
FROM `cbi-v14.models_v4.training_dataset_backup_20251028` b
LEFT JOIN `cbi-v14.models_v4.vw_fx_all` fx ON b.date = fx.date;

-- Step 2: Extend forward with fresh Big-8 data (for dates after backup_max_date)
-- All other columns NULL (preserve structure to match contract)
INSERT INTO `cbi-v14.models_v4.training_dataset_super_enriched`
SELECT 
  f.date,
  -- Target columns (NULL for prediction rows)
  CAST(NULL AS FLOAT64) AS target_1w,
  CAST(NULL AS FLOAT64) AS target_1m,
  CAST(NULL AS FLOAT64) AS target_3m,
  CAST(NULL AS FLOAT64) AS target_6m,
  -- Price columns (get from soybean_oil_prices)
  p.close AS zl_price_current,
  LAG(p.close, 1) OVER (ORDER BY f.date) AS zl_price_lag1,
  LAG(p.close, 7) OVER (ORDER BY f.date) AS zl_price_lag7,
  LAG(p.close, 30) OVER (ORDER BY f.date) AS zl_price_lag30,
  -- Returns (computed)
  (p.close - LAG(p.close, 1) OVER (ORDER BY f.date)) / LAG(p.close, 1) OVER (ORDER BY f.date) AS return_1d,
  (p.close - LAG(p.close, 7) OVER (ORDER BY f.date)) / LAG(p.close, 7) OVER (ORDER BY f.date) AS return_7d,
  -- MAs (computed)
  AVG(p.close) OVER (ORDER BY f.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS ma_7d,
  AVG(p.close) OVER (ORDER BY f.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS ma_30d,
  -- Volatility (computed)
  STDDEV(p.close) OVER (ORDER BY f.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS volatility_30d,
  -- Volume
  p.volume AS zl_volume,
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
  -- All correlation columns NULL (can't compute without historical data)
  CAST(NULL AS FLOAT64) AS corr_zl_crude_7d,
  CAST(NULL AS FLOAT64) AS corr_zl_palm_7d,
  CAST(NULL AS FLOAT64) AS corr_zl_vix_7d,
  CAST(NULL AS FLOAT64) AS corr_zl_dxy_7d,
  CAST(NULL AS FLOAT64) AS corr_zl_corn_7d,
  CAST(NULL AS FLOAT64) AS corr_zl_wheat_7d,
  CAST(NULL AS FLOAT64) AS corr_zl_crude_30d,
  CAST(NULL AS FLOAT64) AS corr_zl_palm_30d,
  CAST(NULL AS FLOAT64) AS corr_zl_vix_30d,
  CAST(NULL AS FLOAT64) AS corr_zl_dxy_30d,
  CAST(NULL AS FLOAT64) AS corr_zl_corn_30d,
  CAST(NULL AS FLOAT64) AS corr_zl_wheat_30d,
  CAST(NULL AS FLOAT64) AS corr_zl_crude_90d,
  CAST(NULL AS FLOAT64) AS corr_zl_palm_90d,
  CAST(NULL AS FLOAT64) AS corr_zl_vix_90d,
  CAST(NULL AS FLOAT64) AS corr_zl_dxy_90d,
  CAST(NULL AS FLOAT64) AS corr_zl_corn_90d,
  CAST(NULL AS FLOAT64) AS corr_zl_crude_180d,
  CAST(NULL AS FLOAT64) AS corr_zl_palm_180d,
  CAST(NULL AS FLOAT64) AS corr_zl_vix_180d,
  CAST(NULL AS FLOAT64) AS corr_zl_dxy_180d,
  CAST(NULL AS FLOAT64) AS corr_zl_crude_365d,
  CAST(NULL AS FLOAT64) AS corr_zl_palm_365d,
  CAST(NULL AS FLOAT64) AS corr_zl_vix_365d,
  CAST(NULL AS FLOAT64) AS corr_zl_dxy_365d,
  CAST(NULL AS FLOAT64) AS corr_zl_corn_365d,
  CAST(NULL AS FLOAT64) AS corr_palm_crude_30d,
  CAST(NULL AS FLOAT64) AS corr_corn_wheat_30d,
  -- Commodity prices (get from source tables)
  CAST(NULL AS FLOAT64) AS crude_price,
  CAST(NULL AS FLOAT64) AS palm_price,
  CAST(NULL AS FLOAT64) AS corn_price,
  CAST(NULL AS FLOAT64) AS wheat_price,
  CAST(NULL AS FLOAT64) AS vix_level,
  CAST(NULL AS FLOAT64) AS dxy_level,
  -- All other columns NULL (too many to list - use SELECT * with NULL overrides)
  -- Actually, better approach: Get structure from backup and NULL fill
  
  -- For now, let's use a simpler approach: Copy structure exactly using SELECT *
  -- but we need to handle the new dates
  
  -- Actually, the cleanest: Generate a template row with all NULLs, then override with fresh data
  
  -- Let me use a different approach: Get column list dynamically and build the INSERT



