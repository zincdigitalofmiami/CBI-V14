-- Extend training_dataset_super_enriched forward from 2025-10-13 to today
-- Uses proper type handling: data_type directly from INFORMATION_SCHEMA
-- All columns NULL except explicitly populated ones

INSERT INTO `cbi-v14.models_v4.training_dataset_super_enriched`
WITH fresh_dates AS (
  SELECT DISTINCT DATE(time) AS date
  FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
  WHERE DATE(time) > '2025-10-13'
    AND DATE(time) <= CURRENT_DATE()
),
fresh_big8 AS (
  SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE date > '2025-10-13'
),
price_data AS (
  SELECT 
    DATE(time) AS date,
    close,
    volume
  FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
  WHERE symbol = 'ZL'
),
fx_data AS (
  SELECT * FROM `cbi-v14.models_v4.vw_fx_all`
)
SELECT 
  -- Explicitly populated columns
  d.date,
  CAST(NULL AS FLOAT64) AS target_1w,
  CAST(NULL AS FLOAT64) AS target_1m,
  CAST(NULL AS FLOAT64) AS target_3m,
  CAST(NULL AS FLOAT64) AS target_6m,
  p.close AS zl_price_current,
  LAG(p.close, 1) OVER (ORDER BY d.date) AS zl_price_lag1,
  LAG(p.close, 7) OVER (ORDER BY d.date) AS zl_price_lag7,
  LAG(p.close, 30) OVER (ORDER BY d.date) AS zl_price_lag30,
  (p.close - LAG(p.close, 1) OVER (ORDER BY d.date)) / NULLIF(LAG(p.close, 1) OVER (ORDER BY d.date), 0) AS return_1d,
  (p.close - LAG(p.close, 7) OVER (ORDER BY d.date)) / NULLIF(LAG(p.close, 7) OVER (ORDER BY d.date), 0) AS return_7d,
  AVG(p.close) OVER (ORDER BY d.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS ma_7d,
  AVG(p.close) OVER (ORDER BY d.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS ma_30d,
  STDDEV(p.close) OVER (ORDER BY d.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS volatility_30d,
  p.volume AS zl_volume,
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
  fx.fx_usd_ars_30d_z,
  fx.fx_usd_myr_30d_z,
  -- All other columns NULL (will be generated dynamically)

