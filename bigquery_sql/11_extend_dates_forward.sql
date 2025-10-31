-- Extend training_dataset_super_enriched forward from 2025-10-13 to today
-- Use fresh Big-8 data + price data + FX data
-- All other columns NULL (preserve structure, no fake data)

INSERT INTO `cbi-v14.models_v4.training_dataset_super_enriched`
SELECT 
  f.date,
  -- Target columns (NULL for future dates)
  CAST(NULL AS FLOAT64) AS target_1w,
  CAST(NULL AS FLOAT64) AS target_1m,
  CAST(NULL AS FLOAT64) AS target_3m,
  CAST(NULL AS FLOAT64) AS target_6m,
  -- Price columns (from soybean_oil_prices)
  p.close AS zl_price_current,
  LAG(p.close, 1) OVER (ORDER BY f.date) AS zl_price_lag1,
  LAG(p.close, 7) OVER (ORDER BY f.date) AS zl_price_lag7,
  LAG(p.close, 30) OVER (ORDER BY f.date) AS zl_price_lag30,
  -- Returns
  (p.close - LAG(p.close, 1) OVER (ORDER BY f.date)) / NULLIF(LAG(p.close, 1) OVER (ORDER BY f.date), 0) AS return_1d,
  (p.close - LAG(p.close, 7) OVER (ORDER BY f.date)) / NULLIF(LAG(p.close, 7) OVER (ORDER BY f.date), 0) AS return_7d,
  -- Moving averages
  AVG(p.close) OVER (ORDER BY f.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS ma_7d,
  AVG(p.close) OVER (ORDER BY f.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS ma_30d,
  -- Volatility
  STDDEV(p.close) OVER (ORDER BY f.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS volatility_30d,
  -- Volume
  p.volume AS zl_volume,
  -- Big-8 features (fresh from current table)
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
  -- All correlation columns NULL (need historical data to compute)
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
  -- Commodity prices NULL (would need to fetch)
  CAST(NULL AS FLOAT64) AS crude_price,
  CAST(NULL AS FLOAT64) AS palm_price,
  CAST(NULL AS FLOAT64) AS corn_price,
  CAST(NULL AS FLOAT64) AS wheat_price,
  CAST(NULL AS FLOAT64) AS vix_level,
  CAST(NULL AS FLOAT64) AS dxy_level,
  -- All other 150+ columns NULL (preserve structure)
  -- Note: This is incomplete - need all columns. Better approach: use template row

