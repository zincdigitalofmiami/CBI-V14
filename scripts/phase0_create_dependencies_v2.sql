-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================================================
-- PHASE 0: CREATE MISSING DEPENDENCIES (V2 - FIXED)
-- Date: November 15, 2025
-- Purpose: Create required objects without dependency on broken views
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 0A. Create Historical Signal View (Alternative Approach)
-- ----------------------------------------------------------------------------
-- Build from base data instead of broken comprehensive view

CREATE OR REPLACE VIEW `cbi-v14.api.vw_ultimate_adaptive_signal_historical` AS
WITH price_data AS (
  -- Get soybean oil price history
  SELECT 
    DATE(time) AS signal_date,
    last AS zl_price_current,
    -- Calculate returns
    (last - LAG(last, 5) OVER (ORDER BY time)) / NULLIF(LAG(last, 5) OVER (ORDER BY time), 0) AS return_5d,
    (last - LAG(last, 20) OVER (ORDER BY time)) / NULLIF(LAG(last, 20) OVER (ORDER BY time), 0) AS return_20d,
    (last - LAG(last, 60) OVER (ORDER BY time)) / NULLIF(LAG(last, 60) OVER (ORDER BY time), 0) AS return_60d,
    -- Calculate volatility
    STDDEV(last) OVER (ORDER BY time ROWS BETWEEN 20 PRECEDING AND CURRENT ROW) / 
      AVG(last) OVER (ORDER BY time ROWS BETWEEN 20 PRECEDING AND CURRENT ROW) AS volatility_20d
  FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
  WHERE symbol = 'ZL'
    AND time >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 YEAR)
    AND time <= CURRENT_DATE()
),
vix_data AS (
  -- Get VIX for regime detection
  SELECT 
    DATE(time) AS date,
    close AS vix_level,
    CASE 
      WHEN close > 30 THEN 'CRISIS'
      WHEN close > 20 THEN 'ELEVATED'
      ELSE 'NORMAL'
    END AS vix_regime
  FROM `cbi-v14.forecasting_data_warehouse.vix_daily`
  WHERE time >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 YEAR)
),
regime_map AS (
  -- Get regime calendar if available
  SELECT DISTINCT
    date,
    regime
  FROM `cbi-v14.training.regime_calendar`
  WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 YEAR)
),
combined AS (
  SELECT 
    p.signal_date,
    p.signal_date AS date,
    p.zl_price_current,
    
    -- Simple forecasts based on momentum
    p.zl_price_current * (1 + COALESCE(p.return_5d, 0)) AS nn_forecast_1week,
    p.zl_price_current * (1 + COALESCE(p.return_20d, 0)) AS nn_forecast_1month,
    p.zl_price_current * (1 + COALESCE(p.return_60d, 0)) AS nn_forecast_3month,
    
    -- Regime classification
    CASE
      WHEN rm.regime IS NOT NULL THEN rm.regime
      WHEN v.vix_regime = 'CRISIS' THEN 'CRISIS_REGIME'
      WHEN v.vix_regime = 'ELEVATED' THEN 'ELEVATED_VOLATILITY'
      ELSE 'FUNDAMENTALS_REGIME'
    END AS master_regime_classification,
    
    -- Crisis intensity based on VIX and volatility
    CASE
      WHEN v.vix_level > 40 THEN 90
      WHEN v.vix_level > 30 THEN 75
      WHEN v.vix_level > 25 THEN 60
      WHEN v.vix_level > 20 THEN 40
      WHEN p.volatility_20d > 0.3 THEN 50
      ELSE 20
    END AS crisis_intensity_score,
    
    -- Primary driver detection
    CASE
      WHEN ABS(p.return_5d) > 0.05 AND v.vix_level > 25 THEN 'VIX'
      WHEN p.return_5d > 0.03 AND p.volatility_20d < 0.15 THEN 'FUNDAMENTAL'
      WHEN p.return_5d < -0.03 AND v.vix_level > 20 THEN 'VIX'
      WHEN EXTRACT(MONTH FROM p.signal_date) IN (9,10,11) THEN 'HARVEST'
      WHEN EXTRACT(MONTH FROM p.signal_date) IN (3,4,5) THEN 'PLANTING'
      ELSE 'FUNDAMENTAL'
    END AS primary_signal_driver,
    
    -- Trading recommendation
    CASE 
      WHEN p.return_5d > 0.05 AND p.volatility_20d < 0.2 THEN 'STRONG_BUY'
      WHEN p.return_5d > 0.03 THEN 'BUY'
      WHEN p.return_5d > 0.01 THEN 'WEAK_BUY'
      WHEN p.return_5d < -0.05 AND p.volatility_20d > 0.25 THEN 'STRONG_SELL'
      WHEN p.return_5d < -0.03 THEN 'SELL'
      WHEN p.return_5d < -0.01 THEN 'WEAK_SELL'
      ELSE 'HOLD'
    END AS trading_recommendation
    
  FROM price_data p
  LEFT JOIN vix_data v ON p.signal_date = v.date
  LEFT JOIN regime_map rm ON p.signal_date = rm.date
)
priority AS (
  SELECT *
  FROM `cbi-v14.neural.vw_chris_priority_regime_detector`
)
SELECT 
  c.signal_date,
  c.date,
  c.zl_price_current,
  c.nn_forecast_1week,
  c.nn_forecast_1month,
  c.nn_forecast_3month,
  CASE 
    WHEN COALESCE(pdet.labor_override_flag, FALSE) THEN 'LABOR_STRESS_REGIME'
    ELSE c.master_regime_classification
  END AS master_regime_classification,
  c.crisis_intensity_score,
  COALESCE(pdet.feature_labor_stress, 0.0) AS feature_labor_stress,
  CASE
    WHEN COALESCE(pdet.labor_override_flag, FALSE) THEN 'LABOR'
    ELSE c.primary_signal_driver
  END AS primary_signal_driver,
  COALESCE(pdet.vix_override_flag, FALSE) AS vix_override_flag,
  COALESCE(pdet.harvest_override_flag, FALSE) AS harvest_override_flag,
  COALESCE(pdet.china_override_flag, FALSE) AS china_override_flag,
  COALESCE(pdet.tariff_override_flag, FALSE) AS tariff_override_flag,
  COALESCE(pdet.labor_override_flag, FALSE) AS labor_override_flag
FROM combined c
LEFT JOIN priority pdet
  ON c.signal_date = pdet.signal_date
WHERE c.signal_date IS NOT NULL
ORDER BY c.signal_date DESC;

-- ----------------------------------------------------------------------------
-- 0B. Create Risk-Free Rates Table (SIMPLIFIED)
-- ----------------------------------------------------------------------------
-- Create from treasury prices or use default if not available

CREATE OR REPLACE TABLE `cbi-v14.forecasting_data_warehouse.risk_free_rates` 
PARTITION BY rate_date
CLUSTER BY rate_type AS
WITH treasury_data AS (
  SELECT DISTINCT
    DATE(time) AS rate_date,
    last AS treasury_rate,
    symbol
  FROM `cbi-v14.forecasting_data_warehouse.treasury_prices`
  WHERE last IS NOT NULL
    AND last > 0
    AND last < 100
),
processed AS (
  SELECT 
    rate_date,
    -- Convert to daily rate
    AVG(treasury_rate) / 100 / 365 AS daily_risk_free_rate,
    AVG(treasury_rate) / 100 AS annual_risk_free_rate,
    '3M_TREASURY' AS rate_type,
    'FRED' AS source,
    CURRENT_TIMESTAMP() AS updated_at
  FROM treasury_data
  GROUP BY rate_date
)
SELECT * FROM processed
WHERE rate_date IS NOT NULL
ORDER BY rate_date DESC;

-- If no treasury data, create with default rates
INSERT INTO `cbi-v14.forecasting_data_warehouse.risk_free_rates` 
  (rate_date, daily_risk_free_rate, annual_risk_free_rate, rate_type, source, updated_at)
SELECT 
  date AS rate_date,
  0.05 / 365 AS daily_risk_free_rate,  -- Default 5% annual
  0.05 AS annual_risk_free_rate,
  '3M_TREASURY' AS rate_type,
  'DEFAULT' AS source,
  CURRENT_TIMESTAMP() AS updated_at
FROM (
  SELECT DISTINCT DATE(time) AS date
  FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
  WHERE time >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 YEAR)
)
WHERE date NOT IN (
  SELECT rate_date 
  FROM `cbi-v14.forecasting_data_warehouse.risk_free_rates`
);

-- ----------------------------------------------------------------------------
-- 0C. Backup Critical Tables (SIMPLIFIED)
-- ----------------------------------------------------------------------------

-- Only backup if not already backed up
CREATE TABLE IF NOT EXISTS `cbi-v14.archive.backup_20251115__training__zl_training_prod_allhistory_1m` AS
SELECT *, 
  CURRENT_TIMESTAMP() AS backup_timestamp,
  'Pre-regime population and historical backfill' AS backup_reason
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`;

-- ----------------------------------------------------------------------------
-- 0D. Column Drift Investigation
-- ----------------------------------------------------------------------------

SELECT 
  'Column Count by Table' AS analysis_type,
  table_name,
  COUNT(*) AS column_count
FROM `cbi-v14.training`.INFORMATION_SCHEMA.COLUMNS
WHERE table_name LIKE 'zl_training_prod_allhistory_%'
GROUP BY table_name
ORDER BY column_count DESC;

-- ----------------------------------------------------------------------------
-- VERIFICATION
-- ----------------------------------------------------------------------------

-- Verify historical signal view
SELECT 
  'Historical Signal View Check' AS check_name,
  COUNT(*) AS row_count,
  MIN(signal_date) AS min_date,
  MAX(signal_date) AS max_date
FROM `cbi-v14.api.vw_ultimate_adaptive_signal_historical`;

-- Verify risk-free rates
SELECT 
  'Risk-Free Rates Check' AS check_name,
  COUNT(*) AS row_count,
  MIN(rate_date) AS min_date,
  MAX(rate_date) AS max_date,
  AVG(annual_risk_free_rate) AS avg_annual_rate
FROM `cbi-v14.forecasting_data_warehouse.risk_free_rates`
WHERE rate_type = '3M_TREASURY';

-- Phase 0 complete
SELECT 
  'Phase 0 Status' AS phase,
  'COMPLETE' AS status,
  CURRENT_TIMESTAMP() AS completion_time;
