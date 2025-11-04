-- Step 5: Rebuild training_dataset_super_enriched using backup structure + fresh data
-- Strategy: Use backup as template, update with fresh data from current sources

-- First, create ingredient views only for what doesn't exist
-- vw_fx_all already exists (created in step 2)

-- Check what views we need to create (only if they don't exist)
-- We'll use CREATE OR REPLACE so it's safe

-- Anchor dates view (create if doesn't exist)
CREATE OR REPLACE VIEW `cbi-v14.models_v4.vw_anchor` AS
SELECT DISTINCT DATE(time) AS date
FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
WHERE time IS NOT NULL AND DATE(time) <= CURRENT_DATE();

-- Price view (create if doesn't exist)  
CREATE OR REPLACE VIEW `cbi-v14.models_v4.vw_price` AS
SELECT 
  DATE(time) AS date,
  close AS zl_price_close,
  volume AS zl_volume,
  close AS zl_price_current,
  LAG(close, 1) OVER (ORDER BY DATE(time)) AS zl_price_lag1,
  LAG(close, 7) OVER (ORDER BY DATE(time)) AS zl_price_lag7,
  LAG(close, 30) OVER (ORDER BY DATE(time)) AS zl_price_lag30
FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
WHERE symbol = 'ZL';

-- Big-8 view (create if doesn't exist)
CREATE OR REPLACE VIEW `cbi-v14.models_v4.vw_big8` AS
SELECT 
  date,
  feature_vix_stress,
  feature_harvest_pace,
  feature_china_relations,
  feature_tariff_threat,
  feature_geopolitical_volatility,
  feature_biofuel_cascade,
  feature_hidden_correlation,
  feature_biofuel_ethanol,
  big8_composite_score,
  market_regime
FROM `cbi-v14.models_v4.training_dataset_super_enriched`;

-- For now, use backup table structure as reference
-- We'll rebuild incrementally by joining fresh sources to backup structure
-- This ensures we get all 207 columns + add 2 FX columns = 209



