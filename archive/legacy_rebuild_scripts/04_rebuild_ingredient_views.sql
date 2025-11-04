-- Step 4: Build all ingredient views for feature families

-- Anchor dates (all trading days)
CREATE OR REPLACE VIEW `cbi-v14.models_v4.vw_anchor` AS
SELECT DISTINCT DATE(time) AS date
FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
WHERE time IS NOT NULL AND DATE(time) <= CURRENT_DATE();

-- Price core
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

-- Big-8 (already in slim table)
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

-- FX (already created in step 2)
-- vw_fx_all exists with fx_usd_ars, fx_usd_myr, fx_usd_brl, fx_usd_cny + 30d z-scores

-- Correlations (from volatility_derived_features - use actual columns)
CREATE OR REPLACE VIEW `cbi-v14.models_v4.vw_correlations` AS
SELECT * FROM `cbi-v14.models_v4.volatility_derived_features`;

-- Fundamentals
CREATE OR REPLACE VIEW `cbi-v14.models_v4.vw_fundamentals` AS
SELECT 
  date,
  br_soybean_production_kt,
  br_soybean_yield_t_per_ha,
  cn_soybean_imports_mmt_month,
  cn_soybean_imports_mmt_ytd,
  supply_demand_ratio
FROM `cbi-v14.models_v4.fundamentals_derived_features`;

-- FX derived (from fx_derived_features table)
CREATE OR REPLACE VIEW `cbi-v14.models_v4.vw_fx_derived` AS
SELECT * FROM `cbi-v14.models_v4.fx_derived_features`;

-- Monetary
CREATE OR REPLACE VIEW `cbi-v14.models_v4.vw_monetary` AS
SELECT * FROM `cbi-v14.models_v4.monetary_derived_features`;

-- Note: Many other features (China, Argentina, News, etc.) need to be added
-- For now, these are the core ingredient views
-- We'll add more as we identify their sources

