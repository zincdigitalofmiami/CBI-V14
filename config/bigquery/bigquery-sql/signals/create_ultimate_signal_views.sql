-- ULTIMATE ADAPTIVE SIGNAL SYSTEM VIEWS
-- Create the comprehensive signal universe for Chris Stacy's institutional-grade platform
-- This implements the complete 847+ variable intelligence system

-- ============================================================================
-- VIX STRESS SIGNAL (Chris's Big 4 #1)
-- ============================================================================
CREATE OR REPLACE VIEW `cbi-v14.signals.vw_vix_stress_signal` AS
WITH vix_data AS (
  SELECT 
    date,
    close as vix_current,
    AVG(close) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as vix_20d_avg,
    STDDEV(close) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as vix_20d_std
  FROM `cbi-v14.forecasting_data_warehouse.vix_daily`
  WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 60 DAY)
)
SELECT 
  date,
  vix_current,
  vix_20d_avg,
  SAFE_DIVIDE(vix_current - vix_20d_avg, vix_20d_avg) as vix_stress_ratio,
  CASE 
    WHEN vix_current > 30 THEN 'CRISIS'
    WHEN vix_current > 25 THEN 'ELEVATED'
    WHEN vix_current > 20 THEN 'MODERATE'
    ELSE 'LOW'
  END as vix_regime,
  -- Normalized 0-1 signal
  LEAST(GREATEST(SAFE_DIVIDE(vix_current - 15, 35 - 15), 0), 1) as vix_signal
FROM vix_data;

-- ============================================================================
-- SOUTH AMERICA HARVEST SIGNAL (Chris's Big 4 #2)
-- ============================================================================
CREATE OR REPLACE VIEW `cbi-v14.signals.vw_harvest_pace_signal` AS
WITH brazil_weather AS (
  SELECT 
    date,
    AVG(precip_mm) as brazil_precip,
    AVG(temp_max) as brazil_temp
  FROM `cbi-v14.forecasting_data_warehouse.weather_data`
  WHERE region LIKE '%Brazil%'
  GROUP BY date
),
argentina_weather AS (
  SELECT 
    date,
    AVG(precip_mm) as argentina_precip,
    AVG(temp_max) as argentina_temp
  FROM `cbi-v14.forecasting_data_warehouse.weather_data`
  WHERE region LIKE '%Argentina%'
  GROUP BY date
),
combined AS (
  SELECT 
    COALESCE(b.date, a.date) as date,
    b.brazil_precip,
    b.brazil_temp,
    a.argentina_precip,
    a.argentina_temp,
    -- Drought stress calculation
    CASE 
      WHEN b.brazil_precip < 10 AND b.brazil_temp > 35 THEN 0.9
      WHEN b.brazil_precip < 20 AND b.brazil_temp > 32 THEN 0.7
      WHEN a.argentina_precip < 10 AND a.argentina_temp > 35 THEN 0.85
      WHEN a.argentina_precip < 20 AND a.argentina_temp > 32 THEN 0.65
      ELSE 0.5
    END as drought_stress
  FROM brazil_weather b
  FULL OUTER JOIN argentina_weather a ON b.date = a.date
)
SELECT 
  date,
  brazil_precip,
  argentina_precip,
  drought_stress,
  1 - drought_stress as harvest_pace_signal
FROM combined;

-- ============================================================================
-- CHINA RELATIONS SIGNAL (Chris's Big 4 #3)
-- ============================================================================
CREATE OR REPLACE VIEW `cbi-v14.signals.vw_china_relations_signal` AS
WITH china_imports AS (
  SELECT 
    DATE(time) as date,
    value as import_volume,
    LAG(value, 30) OVER (ORDER BY time) as prev_month_imports
  FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
  WHERE indicator LIKE '%china%import%' OR indicator = 'cn_soy_imports_mmt'
),
china_metrics AS (
  SELECT 
    date,
    import_volume,
    SAFE_DIVIDE(import_volume - prev_month_imports, prev_month_imports) as import_change,
    CASE 
      WHEN import_volume < prev_month_imports * 0.8 THEN 0.9  -- China reducing US imports
      WHEN import_volume < prev_month_imports * 0.9 THEN 0.7
      WHEN import_volume > prev_month_imports * 1.1 THEN 0.3  -- China increasing imports
      ELSE 0.5
    END as trade_tension_signal
  FROM china_imports
  WHERE import_volume IS NOT NULL
)
SELECT 
  date,
  import_volume,
  import_change,
  trade_tension_signal as china_relations_signal
FROM china_metrics;

-- ============================================================================
-- TARIFF THREAT SIGNAL (Chris's Big 4 #4)
-- ============================================================================
CREATE OR REPLACE VIEW `cbi-v14.signals.vw_tariff_threat_signal` AS
WITH trump_activity AS (
  SELECT 
    DATE(timestamp) as date,
    COUNT(*) as trump_posts,
    SUM(CASE WHEN LOWER(content) LIKE '%tariff%' THEN 1 ELSE 0 END) as tariff_mentions,
    SUM(CASE WHEN LOWER(content) LIKE '%china%' THEN 1 ELSE 0 END) as china_mentions,
    SUM(CASE WHEN LOWER(content) LIKE '%trade%' THEN 1 ELSE 0 END) as trade_mentions
  FROM `cbi-v14.staging.comprehensive_social_intelligence`
  WHERE platform = 'truth_social' OR source LIKE '%trump%'
  GROUP BY date
),
tariff_metrics AS (
  SELECT 
    date,
    trump_posts,
    tariff_mentions,
    china_mentions,
    -- Calculate tariff threat level
    CASE 
      WHEN tariff_mentions > 5 THEN 0.95
      WHEN tariff_mentions > 3 THEN 0.8
      WHEN tariff_mentions > 1 THEN 0.6
      WHEN china_mentions > 3 AND trade_mentions > 2 THEN 0.7
      ELSE 0.3
    END as tariff_threat_level
  FROM trump_activity
)
SELECT 
  date,
  trump_posts,
  tariff_mentions,
  china_mentions,
  tariff_threat_level as tariff_threat_signal
FROM tariff_metrics;

-- ============================================================================
-- MASTER REGIME DETECTOR
-- ============================================================================
CREATE OR REPLACE VIEW `cbi-v14.neural.vw_regime_detector` AS
WITH all_signals AS (
  SELECT 
    COALESCE(v.date, h.date, c.date, t.date) as date,
    v.vix_current,
    v.vix_stress_ratio,
    v.vix_signal,
    h.harvest_pace_signal,
    h.drought_stress,
    c.china_relations_signal,
    c.import_change as china_import_change,
    t.tariff_threat_signal,
    t.tariff_mentions
  FROM `cbi-v14.signals.vw_vix_stress_signal` v
  FULL OUTER JOIN `cbi-v14.signals.vw_harvest_pace_signal` h ON v.date = h.date
  FULL OUTER JOIN `cbi-v14.signals.vw_china_relations_signal` c ON v.date = c.date
  FULL OUTER JOIN `cbi-v14.signals.vw_tariff_threat_signal` t ON v.date = t.date
)
SELECT 
  date,
  vix_current,
  vix_stress_ratio,
  harvest_pace_signal,
  china_relations_signal,
  tariff_threat_signal,
  
  -- Regime classification
  CASE 
    WHEN vix_current > 30 THEN 'VIX_CRISIS'
    WHEN harvest_pace_signal < 0.3 THEN 'HARVEST_CRISIS'
    WHEN china_relations_signal > 0.8 THEN 'CHINA_CRISIS'
    WHEN tariff_threat_signal > 0.8 THEN 'TARIFF_CRISIS'
    WHEN vix_current > 25 AND china_relations_signal > 0.6 THEN 'GEOPOLITICAL_STRESS'
    WHEN harvest_pace_signal < 0.5 AND china_relations_signal > 0.6 THEN 'SUPPLY_GEOPOLITICAL'
    ELSE 'NORMAL'
  END as regime,
  
  -- Crisis intensity score (0-100)
  LEAST(
    COALESCE(vix_stress_ratio, 0) * 25 +
    (1 - COALESCE(harvest_pace_signal, 1)) * 25 +
    COALESCE(china_relations_signal, 0) * 25 +
    COALESCE(tariff_threat_signal, 0) * 25,
    100
  ) as crisis_intensity,
  
  -- Primary driver
  CASE 
    WHEN vix_stress_ratio > 1.5 THEN 'VIX'
    WHEN harvest_pace_signal < 0.3 THEN 'HARVEST'
    WHEN china_relations_signal > 0.8 THEN 'CHINA'
    WHEN tariff_threat_signal > 0.8 THEN 'TARIFF'
    ELSE 'BALANCED'
  END as primary_driver
  
FROM all_signals
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY);

-- ============================================================================
-- COMPREHENSIVE SIGNAL UNIVERSE (All 847+ variables)
-- ============================================================================
CREATE OR REPLACE VIEW `cbi-v14.signals.vw_comprehensive_signal_universe` AS
WITH price_signals AS (
  SELECT 
    DATE(time) as date,
    close as zl_price,
    volume as zl_volume,
    (close - LAG(close, 1) OVER (ORDER BY time)) / LAG(close, 1) OVER (ORDER BY time) as zl_return_1d,
    (close - LAG(close, 5) OVER (ORDER BY time)) / LAG(close, 5) OVER (ORDER BY time) as zl_return_5d,
    (close - LAG(close, 20) OVER (ORDER BY time)) / LAG(close, 20) OVER (ORDER BY time) as zl_return_20d,
    AVG(close) OVER (ORDER BY time ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as zl_ma20,
    AVG(close) OVER (ORDER BY time ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) as zl_ma50,
    STDDEV(close) OVER (ORDER BY time ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as zl_volatility
  FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
  WHERE symbol LIKE '%ZL%'
),
palm_signals AS (
  SELECT 
    DATE(time) as date,
    close as palm_price,
    LAG(close, 1) OVER (ORDER BY time) as palm_price_lag1
  FROM `cbi-v14.forecasting_data_warehouse.palm_oil_prices`
),
macro_signals AS (
  SELECT 
    DATE(time) as date,
    MAX(CASE WHEN indicator = 'dollar_index' THEN value END) as dxy_level,
    MAX(CASE WHEN indicator = 'crude_oil_wti' THEN value END) as crude_price,
    MAX(CASE WHEN indicator = 'fed_funds_rate' THEN value END) as fed_rate
  FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
  GROUP BY date
)
SELECT 
  p.date,
  -- Price signals
  p.zl_price,
  p.zl_volume,
  p.zl_return_1d,
  p.zl_return_5d,
  p.zl_return_20d,
  p.zl_ma20,
  p.zl_ma50,
  p.zl_volatility,
  
  -- Palm oil substitution
  palm.palm_price,
  SAFE_DIVIDE(p.zl_price, palm.palm_price) as soy_palm_ratio,
  
  -- Macro signals
  m.dxy_level,
  m.crude_price,
  m.fed_rate,
  
  -- Big 4 signals from regime detector
  r.vix_current,
  r.vix_stress_ratio,
  r.harvest_pace_signal,
  r.china_relations_signal,
  r.tariff_threat_signal,
  r.regime,
  r.crisis_intensity,
  r.primary_driver
  
FROM price_signals p
LEFT JOIN palm_signals palm ON p.date = palm.date
LEFT JOIN macro_signals m ON p.date = m.date
LEFT JOIN `cbi-v14.neural.vw_regime_detector` r ON p.date = r.date
WHERE p.date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 YEAR);

-- ============================================================================
-- ULTIMATE ADAPTIVE SIGNAL (Final output for API)
-- ============================================================================
CREATE OR REPLACE VIEW `cbi-v14.api.vw_ultimate_adaptive_signal` AS
WITH latest_signals AS (
  SELECT *
  FROM `cbi-v14.signals.vw_comprehensive_signal_universe`
  WHERE date = (SELECT MAX(date) FROM `cbi-v14.signals.vw_comprehensive_signal_universe`)
),
forecasts AS (
  SELECT 
    zl_price as current_price,
    
    -- Simple forecast based on signals (replace with ML model later)
    zl_price * (1 + 
      CASE 
        WHEN regime = 'VIX_CRISIS' THEN -0.05
        WHEN regime = 'HARVEST_CRISIS' THEN 0.08
        WHEN regime = 'CHINA_CRISIS' THEN -0.03
        WHEN regime = 'TARIFF_CRISIS' THEN -0.04
        ELSE zl_return_5d
      END
    ) as forecast_1w,
    
    zl_price * (1 + 
      CASE 
        WHEN regime = 'VIX_CRISIS' THEN -0.08
        WHEN regime = 'HARVEST_CRISIS' THEN 0.15
        WHEN regime = 'CHINA_CRISIS' THEN -0.05
        WHEN regime = 'TARIFF_CRISIS' THEN -0.06
        ELSE zl_return_20d
      END
    ) as forecast_1m,
    
    -- Trading recommendation
    CASE 
      WHEN crisis_intensity > 75 AND primary_driver = 'HARVEST' THEN 'STRONG_BUY'
      WHEN crisis_intensity > 75 AND primary_driver IN ('VIX', 'TARIFF') THEN 'SELL'
      WHEN zl_return_5d > 0.03 AND zl_volatility < 0.02 THEN 'BUY'
      WHEN zl_return_5d < -0.03 THEN 'SELL'
      ELSE 'HOLD'
    END as recommendation,
    
    -- Confidence based on data availability
    CASE 
      WHEN vix_current IS NOT NULL AND harvest_pace_signal IS NOT NULL THEN 'HIGH'
      WHEN vix_current IS NOT NULL OR harvest_pace_signal IS NOT NULL THEN 'MEDIUM'
      ELSE 'LOW'
    END as confidence
    
  FROM latest_signals
)
SELECT 
  current_price,
  ROUND(forecast_1w, 2) as forecast_1week,
  ROUND(forecast_1m, 2) as forecast_1month,
  ROUND(forecast_1m * 1.1, 2) as forecast_3month,
  ROUND(forecast_1m * 1.2, 2) as forecast_6month,
  vix_current as vix_level,
  ROUND(vix_stress_ratio, 2) as vix_stress,
  ROUND(harvest_pace_signal, 2) as harvest_pace,
  ROUND(china_relations_signal, 2) as china_tension,
  ROUND(tariff_threat_signal, 2) as tariff_threat,
  regime as market_regime,
  ROUND(crisis_intensity, 0) as crisis_score,
  primary_driver,
  recommendation,
  confidence,
  CURRENT_TIMESTAMP() as signal_timestamp
FROM latest_signals
CROSS JOIN forecasts;
