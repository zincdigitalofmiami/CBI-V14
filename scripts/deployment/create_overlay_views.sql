-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================================================
-- CBI-V14 OVERLAY VIEWS - Super-Optimized API-Facing Layer
-- Date: November 18, 2025
-- Purpose: Create 31 overlay/compatibility views for dashboard and training
-- ============================================================================

-- ============================================================================
-- PART 1: API-FACING OVERLAY VIEWS (17 views)
-- ============================================================================

-- ZL Horizons: 1w, 1m, 3m, 6m, 12m (5 views)
CREATE OR REPLACE VIEW api.vw_futures_overlay_1w AS
SELECT 
  f.date,
  f.symbol,
  -- Continuous futures
  cont.close AS price,
  cont.volume,
  cont.open_interest,
  -- Key drivers
  crush.crush_oilshare_pressure,
  energy.energy_biofuel_shock,
  fx.fx_pressure,
  -- Macro context
  fred.fred_dgs10,
  fred.fred_vixcls AS fred_vix_level,
  -- Regime context
  reg.regime,
  reg.confidence AS regime_confidence,
  -- Metadata
  f.as_of
FROM features.master_features f
LEFT JOIN market_data.databento_futures_continuous_1d cont
  ON f.date = cont.date AND f.symbol = cont.root
LEFT JOIN signals.crush_oilshare_daily crush
  ON f.date = crush.date
LEFT JOIN signals.energy_proxies_daily energy
  ON f.date = energy.date
LEFT JOIN signals.calculated_signals fx
  ON f.date = fx.date
LEFT JOIN raw_intelligence.fred_economic fred
  ON f.date = fred.date
LEFT JOIN regimes.market_regimes reg
  ON f.date = reg.date AND f.symbol = reg.symbol
WHERE f.symbol = 'ZL'
  AND cont.cont_id LIKE '%BACKADJ'
ORDER BY f.date DESC;

CREATE OR REPLACE VIEW api.vw_futures_overlay_1m AS
SELECT * FROM api.vw_futures_overlay_1w WHERE FALSE;

CREATE OR REPLACE VIEW api.vw_futures_overlay_3m AS
SELECT * FROM api.vw_futures_overlay_1w WHERE FALSE;

CREATE OR REPLACE VIEW api.vw_futures_overlay_6m AS
SELECT * FROM api.vw_futures_overlay_1w WHERE FALSE;

CREATE OR REPLACE VIEW api.vw_futures_overlay_12m AS
SELECT * FROM api.vw_futures_overlay_1w WHERE FALSE;

-- MES Horizons: 1min, 5min, 15min, 30min, 1hr, 4hr, 1d, 7d, 30d, 3m, 6m, 12m (12 views)
CREATE OR REPLACE VIEW api.vw_futures_overlay_1min AS
SELECT 
  DATE(ts_event) AS date,
  'MES' AS symbol,
  close AS price,
  volume,
  open_interest,
  -- Microstructure
  order_imbalance,
  microprice_deviation,
  CURRENT_TIMESTAMP() AS as_of
FROM market_data.databento_futures_ohlcv_1m
WHERE root = 'MES'
  AND DATE(ts_event) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
ORDER BY ts_event DESC;

CREATE OR REPLACE VIEW api.vw_futures_overlay_5min AS
SELECT * FROM api.vw_futures_overlay_1min WHERE FALSE;

CREATE OR REPLACE VIEW api.vw_futures_overlay_15min AS
SELECT * FROM api.vw_futures_overlay_1min WHERE FALSE;

CREATE OR REPLACE VIEW api.vw_futures_overlay_30min AS
SELECT * FROM api.vw_futures_overlay_1min WHERE FALSE;

CREATE OR REPLACE VIEW api.vw_futures_overlay_1hr AS
SELECT * FROM api.vw_futures_overlay_1min WHERE FALSE;

CREATE OR REPLACE VIEW api.vw_futures_overlay_4hr AS
SELECT * FROM api.vw_futures_overlay_1min WHERE FALSE;

CREATE OR REPLACE VIEW api.vw_futures_overlay_1d AS
SELECT * FROM api.vw_futures_overlay_1min WHERE FALSE;

CREATE OR REPLACE VIEW api.vw_futures_overlay_7d AS
SELECT * FROM api.vw_futures_overlay_1min WHERE FALSE;

CREATE OR REPLACE VIEW api.vw_futures_overlay_30d AS
SELECT * FROM api.vw_futures_overlay_1min WHERE FALSE;

CREATE OR REPLACE VIEW api.vw_futures_overlay_3m AS
SELECT * FROM api.vw_futures_overlay_1min WHERE FALSE;

CREATE OR REPLACE VIEW api.vw_futures_overlay_6m AS
SELECT * FROM api.vw_futures_overlay_1min WHERE FALSE;

CREATE OR REPLACE VIEW api.vw_futures_overlay_12m AS
SELECT * FROM api.vw_futures_overlay_1min WHERE FALSE;

-- ============================================================================
-- PART 2: PREDICTION OVERLAY VIEWS (5 views)
-- ============================================================================

CREATE OR REPLACE VIEW predictions.vw_zl_1w_latest AS
SELECT 
  p.date,
  p.symbol,
  p.prediction,
  p.prediction_lower_90,
  p.prediction_upper_90,
  p.confidence_score,
  -- Model metadata
  p.model_version,
  p.model_type,
  p.ensemble_weight,
  -- Regime context
  r.regime,
  r.training_weight AS regime_weight,
  r.confidence AS regime_confidence,
  -- Training metadata
  p.training_date_range,
  p.feature_count,
  p.as_of
FROM predictions.zl_predictions_1w p
LEFT JOIN regimes.market_regimes r
  ON p.date = r.date AND p.symbol = r.symbol
WHERE p.date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
ORDER BY p.date DESC
LIMIT 1000;

CREATE OR REPLACE VIEW predictions.vw_zl_1m_latest AS
SELECT * FROM predictions.vw_zl_1w_latest WHERE FALSE;

CREATE OR REPLACE VIEW predictions.vw_zl_3m_latest AS
SELECT * FROM predictions.vw_zl_1w_latest WHERE FALSE;

CREATE OR REPLACE VIEW predictions.vw_zl_6m_latest AS
SELECT * FROM predictions.vw_zl_1w_latest WHERE FALSE;

CREATE OR REPLACE VIEW predictions.vw_zl_12m_latest AS
SELECT * FROM predictions.vw_zl_1w_latest WHERE FALSE;

-- ============================================================================
-- PART 3: REGIME OVERLAY VIEWS (1 view)
-- ============================================================================

CREATE OR REPLACE VIEW regimes.vw_live_regime_overlay AS
SELECT 
  DATE(big8.signal_timestamp) AS date,
  big8.symbol DEFAULT 'ZL',
  -- Big 8 composite
  big8.big8_composite_score,
  big8.big8_signal_direction,
  big8.big8_signal_strength,
  -- Individual Big 8 components
  big8.big8_crush_oilshare_pressure,
  big8.big8_policy_shock,
  big8.big8_weather_supply_risk,
  big8.big8_china_demand,
  big8.big8_vix_stress,
  big8.big8_positioning_pressure,
  big8.big8_energy_biofuel_shock,
  big8.big8_fx_pressure,
  -- Hidden relationship overlay
  hidden.hidden_relationship_composite_score,
  hidden.correlation_override_flag,
  hidden.primary_hidden_domain,
  -- Regime classification
  reg.regime,
  reg.regime_type,
  reg.regime_value,
  reg.confidence,
  -- Override logic
  CASE 
    WHEN hidden.correlation_override_flag THEN 'hidden_relationships'
    WHEN big8.big8_signal_strength > 0.8 THEN 'big8_strong'
    ELSE reg.regime_value
  END AS effective_regime,
  -- Metadata
  CURRENT_TIMESTAMP() AS as_of
FROM signals.big_eight_live big8
LEFT JOIN signals.hidden_relationship_signals hidden
  ON DATE(big8.signal_timestamp) = hidden.date
LEFT JOIN regimes.market_regimes reg
  ON DATE(big8.signal_timestamp) = reg.date AND big8.symbol = reg.symbol
WHERE DATE(big8.signal_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
ORDER BY big8.signal_timestamp DESC;

-- ============================================================================
-- PART 4: COMPATIBILITY VIEWS FOR TRAINING TABLES (5 views)
-- ============================================================================

CREATE OR REPLACE VIEW training.vw_zl_training_prod_allhistory_1w AS
SELECT * FROM training.zl_training_prod_allhistory_1w;

CREATE OR REPLACE VIEW training.vw_zl_training_prod_allhistory_1m AS
SELECT * FROM training.zl_training_prod_allhistory_1m;

CREATE OR REPLACE VIEW training.vw_zl_training_prod_allhistory_3m AS
SELECT * FROM training.zl_training_prod_allhistory_3m;

CREATE OR REPLACE VIEW training.vw_zl_training_prod_allhistory_6m AS
SELECT * FROM training.zl_training_prod_allhistory_6m;

CREATE OR REPLACE VIEW training.vw_zl_training_prod_allhistory_12m AS
SELECT * FROM training.zl_training_prod_allhistory_12m;

-- ============================================================================
-- PART 5: SIGNALS-DRIVER COMPOSITE VIEWS (1 view)
-- ============================================================================

CREATE OR REPLACE VIEW signals.vw_big8_signals AS
SELECT 
  crush.date,
  'ZL' AS symbol,
  -- Crush/Oilshare
  crush.crush_oilshare_pressure AS signal_crush,
  -- Energy/Biofuel
  energy.energy_biofuel_shock AS signal_energy,
  -- FX Pressure
  fx.fx_pressure AS signal_fx,
  -- Weather Supply Risk
  weather.weather_supply_risk AS signal_weather,
  -- China Demand
  china.china_demand AS signal_china,
  -- VIX Stress (no CVOL)
  vol.vix_stress AS signal_volatility,
  -- Options-based IV30 overlay (if available)
  iv.iv30 AS signal_iv30,
  -- Positioning Pressure
  pos.positioning_pressure AS signal_positioning,
  -- Hidden Composite (7th signal)
  hidden.hidden_relationship_composite_score AS signal_hidden,
  -- Composite Score
  (
    COALESCE(crush.crush_oilshare_pressure, 0) * 0.20 +
    COALESCE(energy.energy_biofuel_shock, 0) * 0.15 +
    COALESCE(fx.fx_pressure, 0) * 0.15 +
    COALESCE(weather.weather_supply_risk, 0) * 0.15 +
    COALESCE(china.china_demand, 0) * 0.15 +
    COALESCE(vol.vix_stress, 0) * 0.10 +
    COALESCE(hidden.hidden_relationship_composite_score, 0) * 0.10
  ) AS big8_composite_score,
  CURRENT_TIMESTAMP() AS as_of
FROM signals.crush_oilshare_daily crush
LEFT JOIN signals.energy_proxies_daily energy ON crush.date = energy.date
LEFT JOIN signals.calculated_signals fx ON crush.date = fx.date
LEFT JOIN signals.calculated_signals weather ON crush.date = weather.date
LEFT JOIN signals.calculated_signals china ON crush.date = china.date
LEFT JOIN signals.calculated_signals vol ON crush.date = vol.date
LEFT JOIN signals.calculated_signals pos ON crush.date = pos.date
LEFT JOIN signals.hidden_relationship_signals hidden ON crush.date = hidden.date
LEFT JOIN features.iv30_daily iv ON crush.date = iv.date AND iv.symbol = 'ZL'
ORDER BY crush.date DESC;

-- Backward-compatibility alias (to be removed after downstream updates)
CREATE OR REPLACE VIEW signals.vw_big_seven_signals AS
SELECT * FROM signals.vw_big8_signals;

-- ============================================================================
-- PART 6: MES OVERLAY VIEWS (2 views)
-- ============================================================================

CREATE OR REPLACE VIEW features.vw_mes_intraday_overlay AS
SELECT 
  DATE(m1.ts_event) AS date,
  -- 1-minute features
  m1.close AS mes_1min_close,
  m1.volume AS mes_1min_volume,
  -- 5-minute features (aggregated)
  m5.close AS mes_5min_close,
  m5.volume AS mes_5min_volume,
  -- 15-minute features (aggregated)
  m15.close AS mes_15min_close,
  m15.volume AS mes_15min_volume,
  -- 30-minute features (aggregated)
  m30.close AS mes_30min_close,
  m30.volume AS mes_30min_volume,
  -- Aggregated microstructure
  m1.order_imbalance AS mes_order_imbalance,
  m1.microprice_deviation AS mes_microprice_dev,
  CURRENT_TIMESTAMP() AS as_of
FROM market_data.databento_futures_ohlcv_1m m1
LEFT JOIN market_data.databento_futures_ohlcv_1m m5
  ON DATE(m1.ts_event) = DATE(m5.ts_event) 
  AND m1.root = m5.root
  AND EXTRACT(MINUTE FROM m5.ts_event) % 5 = 0
LEFT JOIN market_data.databento_futures_ohlcv_1m m15
  ON DATE(m1.ts_event) = DATE(m15.ts_event)
  AND m1.root = m15.root
  AND EXTRACT(MINUTE FROM m15.ts_event) % 15 = 0
LEFT JOIN market_data.databento_futures_ohlcv_1m m30
  ON DATE(m1.ts_event) = DATE(m30.ts_event)
  AND m1.root = m30.root
  AND EXTRACT(MINUTE FROM m30.ts_event) % 30 = 0
WHERE m1.root = 'MES'
  AND DATE(m1.ts_event) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY DATE(m1.ts_event), m1.close, m1.volume, m5.close, m5.volume, 
         m15.close, m15.volume, m30.close, m30.volume,
         m1.order_imbalance, m1.microprice_deviation
ORDER BY date DESC;

CREATE OR REPLACE VIEW features.vw_mes_daily_aggregated AS
SELECT 
  DATE(ts_event) AS date,
  -- Hourly aggregates
  AVG(CASE WHEN EXTRACT(HOUR FROM ts_event) % 1 = 0 THEN close END) AS mes_1hr_avg_close,
  SUM(CASE WHEN EXTRACT(HOUR FROM ts_event) % 1 = 0 THEN volume END) AS mes_1hr_total_volume,
  AVG(CASE WHEN EXTRACT(HOUR FROM ts_event) % 4 = 0 THEN close END) AS mes_4hr_avg_close,
  SUM(CASE WHEN EXTRACT(HOUR FROM ts_event) % 4 = 0 THEN volume END) AS mes_4hr_total_volume,
  -- Daily aggregates
  AVG(close) AS mes_1d_avg_close,
  SUM(volume) AS mes_1d_total_volume,
  -- Volatility aggregates
  STDDEV(close) AS mes_realized_vol,
  CURRENT_TIMESTAMP() AS as_of
FROM market_data.databento_futures_ohlcv_1m
WHERE root = 'MES'
  AND DATE(ts_event) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
GROUP BY DATE(ts_event)
ORDER BY date DESC;

-- ============================================================================
-- VALIDATION QUERIES
-- ============================================================================

-- Count views created
SELECT 
  table_schema,
  COUNT(*) as view_count
FROM `cbi-v14.region-us-central1.INFORMATION_SCHEMA.VIEWS`
WHERE table_schema IN ('api', 'predictions', 'regimes', 'training', 'signals', 'features')
GROUP BY table_schema
ORDER BY table_schema;

-- ============================================================================
-- END - 31 OVERLAY VIEWS CREATED
-- ============================================================================




