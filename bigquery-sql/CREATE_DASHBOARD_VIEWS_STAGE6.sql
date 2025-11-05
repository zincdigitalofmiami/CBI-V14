-- ============================================
-- STAGE 6: DASHBOARD CONSUMPTION VIEWS
-- ============================================
-- Pre-Aggregated Views for Fast Dashboard Loading
-- ============================================

-- View 1: Latest Forecast + Signals (All Horizons)
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.vw_forecast_with_signals`
AS
SELECT 
  f.forecast_date,
  f.horizon,
  f.target_date,
  f.predicted_value,
  f.lower_bound_80,
  f.upper_bound_80,
  f.confidence,
  f.market_regime,
  f.crisis_intensity_score,
  f.primary_signal_driver,
  f.composite_signal_score,
  f.palm_sub_risk,
  f.model_name,
  f.mape_historical,
  -- Format for Vegas Intel display
  CONCAT(
    f.horizon, ' Forecast: $', CAST(ROUND(f.predicted_value, 2) AS STRING),
    ' | Confidence: ', CAST(CAST(f.confidence AS INT64) AS STRING), '%',
    ' | MAPE: ', CAST(ROUND(f.mape_historical, 1) AS STRING), '%',
    ' | Regime: ', f.market_regime
  ) as vegas_intel_display
FROM `cbi-v14.predictions_uc1.production_forecasts` f
WHERE f.forecast_date = (SELECT MAX(forecast_date) FROM `cbi-v14.predictions_uc1.production_forecasts`)
ORDER BY 
  CASE f.horizon
    WHEN '1W' THEN 1
    WHEN '1M' THEN 2
    WHEN '3M' THEN 3
    WHEN '6M' THEN 4
  END;

-- View 2: Vegas Intel Feed (Kevin's Live Page)
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.vw_vegas_intel_feed`
AS
SELECT 
  f.forecast_date,
  f.horizon,
  f.predicted_value as zl_cost,  -- Used in Kevin's ROI calculations
  f.confidence,
  f.market_regime,
  f.crisis_intensity_score,
  f.composite_signal_score,
  f.primary_signal_driver,
  -- Format for Vegas Intel display
  CONCAT(
    f.horizon, ' Forecast: $', CAST(ROUND(f.predicted_value, 2) AS STRING),
    ' (', CAST(CAST(f.confidence AS INT64) AS STRING), '% conf)'
  ) as forecast_display,
  CONCAT(
    'Signal Strength: Big 8 = ', CAST(ROUND(f.composite_signal_score * 100, 0) AS STRING),
    ' | Crisis: ', CAST(CAST(f.crisis_intensity_score AS INT64) AS STRING), '/100'
  ) as signal_display,
  f.created_at
FROM `cbi-v14.predictions_uc1.production_forecasts` f
WHERE f.forecast_date = (SELECT MAX(forecast_date) FROM `cbi-v14.predictions_uc1.production_forecasts`)
  AND f.horizon = '1W'  -- Vegas Intel uses 1W forecast for ZL cost
LIMIT 1;

-- View 3: China Intel Dashboard (Chris Priority #1)
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.vw_china_intel_dashboard`
AS
SELECT 
  f.forecast_date,
  f.horizon,
  f.predicted_value,
  f.confidence,
  f.market_regime,
  -- China-specific signals (if available)
  COALESCE(china.china_imports_from_us_mt, 0) as china_imports_mt,
  COALESCE(china.china_cancellation_signals, 0) as china_cancellations,
  COALESCE(china.china_sentiment, 0.5) as china_sentiment_score,
  -- Forecast impact from China
  CASE 
    WHEN COALESCE(china.china_cancellation_signals, 0) > 3 THEN 
      f.predicted_value * 0.958  -- -4.2% impact
    ELSE f.predicted_value
  END as forecast_adjusted_china
FROM `cbi-v14.predictions_uc1.production_forecasts` f
LEFT JOIN (
  SELECT 
    date,
    china_imports_from_us_mt,
    china_cancellation_signals,
    china_sentiment
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE date = (SELECT MAX(date) FROM `cbi-v14.models_v4.training_dataset_super_enriched`)
) china ON f.forecast_date = china.date
WHERE f.forecast_date = (SELECT MAX(forecast_date) FROM `cbi-v14.predictions_uc1.production_forecasts`)
ORDER BY 
  CASE f.horizon
    WHEN '1W' THEN 1
    WHEN '1M' THEN 2
    WHEN '3M' THEN 3
    WHEN '6M' THEN 4
  END;

-- View 4: Harvest Intel Dashboard (Chris Priority #2)
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.vw_harvest_intel_dashboard`
AS
SELECT 
  f.forecast_date,
  f.horizon,
  f.predicted_value,
  f.confidence,
  f.market_regime,
  -- Harvest signals (if available)
  COALESCE(harvest.feature_harvest_pace, 0) as harvest_pace_score,
  COALESCE(harvest.brazil_harvest_signals, 0) as brazil_harvest,
  COALESCE(harvest.argentina_harvest_signals, 0) as argentina_harvest,
  -- Weather impact
  COALESCE(harvest.brazil_temperature_c, NULL) as brazil_temp,
  COALESCE(harvest.argentina_precipitation_mm, NULL) as argentina_precip
FROM `cbi-v14.predictions_uc1.production_forecasts` f
LEFT JOIN (
  SELECT 
    date,
    feature_harvest_pace,
    brazil_harvest_signals,
    argentina_harvest_signals,
    brazil_temperature_c,
    argentina_precipitation_mm
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE date = (SELECT MAX(date) FROM `cbi-v14.models_v4.training_dataset_super_enriched`)
) harvest ON f.forecast_date = harvest.date
WHERE f.forecast_date = (SELECT MAX(forecast_date) FROM `cbi-v14.predictions_uc1.production_forecasts`)
ORDER BY 
  CASE f.horizon
    WHEN '1W' THEN 1
    WHEN '1M' THEN 2
    WHEN '3M' THEN 3
    WHEN '6M' THEN 4
  END;

-- View 5: Biofuel Intel Dashboard (Chris Priority #3)
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.vw_biofuel_intel_dashboard`
AS
SELECT 
  f.forecast_date,
  f.horizon,
  f.predicted_value,
  f.confidence,
  f.market_regime,
  -- Biofuel signals (if available)
  COALESCE(biofuel.feature_biofuel_cascade, 0) as biofuel_cascade_score,
  COALESCE(biofuel.biodiesel_demand_signals, 0) as biodiesel_demand,
  COALESCE(biofuel.rfs_volumes, 0) as rfs_volumes,
  -- Forecast impact from biofuel
  CASE 
    WHEN f.market_regime = 'BIOFUEL_BOOM_REGIME' THEN 
      f.predicted_value * 1.12  -- +12% upside
    ELSE f.predicted_value
  END as forecast_adjusted_biofuel
FROM `cbi-v14.predictions_uc1.production_forecasts` f
LEFT JOIN (
  SELECT 
    date,
    feature_biofuel_cascade,
    biodiesel_demand_signals,
    rfs_volumes
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE date = (SELECT MAX(date) FROM `cbi-v14.models_v4.training_dataset_super_enriched`)
) biofuel ON f.forecast_date = biofuel.date
WHERE f.forecast_date = (SELECT MAX(forecast_date) FROM `cbi-v14.predictions_uc1.production_forecasts`)
ORDER BY 
  CASE f.horizon
    WHEN '1W' THEN 1
    WHEN '1M' THEN 2
    WHEN '3M' THEN 3
    WHEN '6M' THEN 4
  END;

-- View 6: Forecast Timeline (Historical)
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.vw_forecast_timeline`
AS
SELECT 
  forecast_date,
  horizon,
  target_date,
  predicted_value,
  lower_bound_80,
  upper_bound_80,
  confidence,
  market_regime,
  crisis_intensity_score,
  primary_signal_driver,
  created_at
FROM `cbi-v14.predictions_uc1.production_forecasts`
ORDER BY forecast_date DESC, target_date ASC;


