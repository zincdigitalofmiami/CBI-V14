-- ============================================================================
-- PHASE 3: CREATE PERFORMANCE VIEWS (Sharpe & MAPE)
-- Date: November 15, 2025
-- Purpose: Create comprehensive performance tracking views for dashboard
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 3A. Create Soybean Sharpe Metrics View (Full Implementation)
-- ----------------------------------------------------------------------------

CREATE OR REPLACE VIEW `cbi-v14.performance.vw_soybean_sharpe_metrics` AS
WITH trading_signals AS (
  -- Get historical signals with recommendations
  SELECT 
    signal_date,
    trading_recommendation,
    nn_forecast_1week,
    zl_price_current,
    master_regime_classification,
    crisis_intensity_score,
    primary_signal_driver,
    labor_override_flag
  FROM `cbi-v14.api.vw_ultimate_adaptive_signal_historical`
  WHERE signal_date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY) AND CURRENT_DATE()
),
actual_prices AS (
  -- Get actual soybean oil prices
  SELECT 
    DATE(time) AS price_date,
    close,
    LAG(close) OVER (ORDER BY time) AS prev_close,
    (close - LAG(close) OVER (ORDER BY time)) / NULLIF(LAG(close) OVER (ORDER BY time), 0) AS daily_return
  FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
  WHERE symbol = 'ZL'
    AND time BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 370 DAY) AND CURRENT_DATE()
),
seasonal_volatility AS (
  -- Calculate seasonal volatility patterns
  SELECT 
    EXTRACT(MONTH FROM price_date) AS month,
    EXTRACT(DAY FROM price_date) <= 15 AS is_first_half,
    AVG(ABS(daily_return)) AS avg_absolute_return,
    STDDEV(daily_return) AS volatility
  FROM actual_prices
  GROUP BY 1, 2
),
seasonal_factors AS (
  -- Determine seasonal adjustment factors
  SELECT 
    month,
    is_first_half,
    volatility,
    volatility / NULLIF((SELECT AVG(volatility) FROM seasonal_volatility), 0) AS seasonal_factor,
    CASE 
      WHEN month = 6 AND is_first_half = FALSE THEN 'USDA_ACREAGE_REPORT'
      WHEN month = 8 AND is_first_half = FALSE THEN 'CROP_PRODUCTION'
      WHEN month = 10 AND is_first_half = TRUE THEN 'HARVEST_PRESSURE'
      WHEN month = 3 AND is_first_half = FALSE THEN 'PLANTING_INTENTIONS'
      ELSE 'NORMAL'
    END AS seasonal_event
  FROM seasonal_volatility
),
signal_returns AS (
  -- Calculate returns for each signal
  SELECT 
    t.signal_date,
    t.trading_recommendation,
    t.master_regime_classification,
    t.crisis_intensity_score,
    t.primary_signal_driver,
    t.labor_override_flag,
    
    -- Position direction based on recommendation
    CASE 
      WHEN t.trading_recommendation IN ('STRONG_BUY', 'BUY', 'WEAK_BUY') THEN 1.0
      WHEN t.trading_recommendation IN ('STRONG_SELL', 'SELL', 'WEAK_SELL') THEN -1.0
      ELSE 0.0
    END AS position_direction,
    
    -- Position sizing
    CASE 
      WHEN t.trading_recommendation = 'STRONG_BUY' THEN 1.0
      WHEN t.trading_recommendation = 'BUY' THEN 0.75
      WHEN t.trading_recommendation = 'WEAK_BUY' THEN 0.50
      WHEN t.trading_recommendation = 'HOLD' THEN 0.00
      WHEN t.trading_recommendation = 'WEAK_SELL' THEN 0.50
      WHEN t.trading_recommendation = 'SELL' THEN 0.75
      WHEN t.trading_recommendation = 'STRONG_SELL' THEN 1.0
    END * CASE 
      WHEN t.crisis_intensity_score > 75 THEN 1.0
      WHEN t.crisis_intensity_score > 50 THEN 0.8
      ELSE 0.6
    END AS position_size,
    
    sf.seasonal_factor,
    sf.seasonal_event,
    
    -- Calculate 1-week return
    (
      SELECT (a_end.close - t.zl_price_current) / NULLIF(t.zl_price_current, 0)
      FROM actual_prices a_end
      WHERE a_end.price_date = DATE_ADD(t.signal_date, INTERVAL 7 DAY)
    ) AS actual_return_1week,
    
    -- Strategy return (position-adjusted)
    CASE 
      WHEN t.trading_recommendation IN ('STRONG_BUY', 'BUY', 'WEAK_BUY') THEN 1.0
      WHEN t.trading_recommendation IN ('STRONG_SELL', 'SELL', 'WEAK_SELL') THEN -1.0
      ELSE 0.0
    END * (
      SELECT (a_end.close - t.zl_price_current) / NULLIF(t.zl_price_current, 0)
      FROM actual_prices a_end
      WHERE a_end.price_date = DATE_ADD(t.signal_date, INTERVAL 7 DAY)
    ) AS strategy_return_1week
    
  FROM trading_signals t
  LEFT JOIN seasonal_factors sf 
    ON EXTRACT(MONTH FROM t.signal_date) = sf.month
    AND (EXTRACT(DAY FROM t.signal_date) <= 15) = sf.is_first_half
),
risk_free AS (
  -- Get risk-free rate
  SELECT 
    AVG(daily_risk_free_rate) AS avg_rf,
    AVG(CASE 
      WHEN rate_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) 
      THEN daily_risk_free_rate 
    END) AS recent_rf
  FROM `cbi-v14.forecasting_data_warehouse.risk_free_rates`
  WHERE rate_type = '3M_TREASURY'
),
sharpe_calculations AS (
  -- Calculate various Sharpe ratios
  SELECT 
    -- Standard Sharpe (1-week horizon)
    (AVG(strategy_return_1week) - (SELECT avg_rf FROM risk_free)) / 
      NULLIF(STDDEV(strategy_return_1week), 0) * 
      SQRT(COUNT(strategy_return_1week)) AS standard_sharpe_1week,
    
    -- Seasonal-adjusted Sharpe
    (AVG(strategy_return_1week) - (SELECT avg_rf FROM risk_free)) / 
      NULLIF(STDDEV(strategy_return_1week) / NULLIF(AVG(NULLIF(seasonal_factor, 0)), 0), 0) * 
      SQRT(COUNT(strategy_return_1week)) AS seasonal_adjusted_sharpe_1week,
    
    -- Crisis regime Sharpe
    (AVG(CASE 
      WHEN master_regime_classification LIKE '%CRISIS%' THEN strategy_return_1week 
    END) - (SELECT avg_rf FROM risk_free)) / 
      NULLIF(STDDEV(CASE 
        WHEN master_regime_classification LIKE '%CRISIS%' THEN strategy_return_1week 
      END) * 0.85, 0) * 
      SQRT(COUNTIF(master_regime_classification LIKE '%CRISIS%')) AS crisis_sharpe_1week,
    
    -- Normal regime Sharpe
    (AVG(CASE 
      WHEN master_regime_classification = 'FUNDAMENTALS_REGIME' THEN strategy_return_1week 
    END) - (SELECT avg_rf FROM risk_free)) / 
      NULLIF(STDDEV(CASE 
        WHEN master_regime_classification = 'FUNDAMENTALS_REGIME' THEN strategy_return_1week 
      END), 0) * 
      SQRT(COUNTIF(master_regime_classification = 'FUNDAMENTALS_REGIME')) AS normal_sharpe_1week,
    
    -- Weather-driven Sharpe
    (AVG(CASE 
      WHEN primary_signal_driver LIKE '%harvest%' 
        OR primary_signal_driver LIKE '%weather%' 
        OR primary_signal_driver LIKE '%HARVEST%'
      THEN strategy_return_1week 
    END) - (SELECT avg_rf FROM risk_free)) / 
      NULLIF(STDDEV(CASE 
        WHEN primary_signal_driver LIKE '%harvest%' 
          OR primary_signal_driver LIKE '%weather%'
          OR primary_signal_driver LIKE '%HARVEST%'
        THEN strategy_return_1week 
      END), 0) * 
      SQRT(COUNTIF(primary_signal_driver LIKE '%harvest%' 
        OR primary_signal_driver LIKE '%weather%'
        OR primary_signal_driver LIKE '%HARVEST%')) AS weather_driven_sharpe_1week,

    -- Labor-driven Sharpe
    (AVG(CASE 
      WHEN labor_override_flag THEN strategy_return_1week
    END) - (SELECT avg_rf FROM risk_free)) /
      NULLIF(STDDEV(CASE
        WHEN labor_override_flag THEN strategy_return_1week
      END), 0) *
      SQRT(COUNTIF(labor_override_flag)) AS labor_sharpe_1week,
    
    -- Seasonal event Sharpe
    (AVG(CASE 
      WHEN seasonal_event <> 'NORMAL' THEN strategy_return_1week 
    END) - (SELECT avg_rf FROM risk_free)) / 
      NULLIF(STDDEV(CASE 
        WHEN seasonal_event <> 'NORMAL' THEN strategy_return_1week 
      END), 0) * 
      SQRT(COUNTIF(seasonal_event <> 'NORMAL')) AS seasonal_event_sharpe_1week,
    
    -- Recent Sharpe (last 30 days)
    (AVG(CASE 
      WHEN signal_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) THEN strategy_return_1week 
    END) - (SELECT recent_rf FROM risk_free)) / 
      NULLIF(STDDEV(CASE 
        WHEN signal_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) THEN strategy_return_1week 
      END), 0) * 
      SQRT(COUNTIF(signal_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY))) AS recent_sharpe_1week,
    
    -- Counts
    COUNT(strategy_return_1week) AS total_signals,
    COUNTIF(master_regime_classification LIKE '%CRISIS%') AS crisis_signals,
    COUNTIF(master_regime_classification = 'FUNDAMENTALS_REGIME') AS normal_signals
    
  FROM signal_returns
  WHERE strategy_return_1week IS NOT NULL
),
portfolio_metrics AS (
  -- Calculate portfolio-level metrics
  SELECT 
    -- Cumulative return
    EXP(SUM(LN(1 + COALESCE(strategy_return_1week, 0)))) - 1 AS cumulative_return,
    
    -- Max drawdown (simplified)
    MIN(strategy_return_1week) AS max_drawdown,
    
    -- Calmar ratio (simplified)
    (AVG(strategy_return_1week) * 52) / 
      NULLIF(ABS(MIN(strategy_return_1week)), 0) AS calmar_ratio,
    
    -- Win rate
    SAFE_DIVIDE(
      COUNTIF(strategy_return_1week > 0),
      COUNT(strategy_return_1week)
    ) AS win_rate,
    
    -- Profit factor
    SAFE_DIVIDE(
      SUM(CASE WHEN strategy_return_1week > 0 THEN strategy_return_1week ELSE 0 END),
      ABS(SUM(CASE WHEN strategy_return_1week < 0 THEN strategy_return_1week ELSE 0 END))
    ) AS profit_factor,
    
    -- Seasonal returns
    AVG(CASE 
      WHEN EXTRACT(MONTH FROM signal_date) IN (3, 4, 5) THEN strategy_return_1week 
    END) AS spring_avg_return,
    AVG(CASE 
      WHEN EXTRACT(MONTH FROM signal_date) IN (6, 7, 8) THEN strategy_return_1week 
    END) AS summer_avg_return,
    AVG(CASE 
      WHEN EXTRACT(MONTH FROM signal_date) IN (9, 10, 11) THEN strategy_return_1week 
    END) AS fall_avg_return,
    AVG(CASE 
      WHEN EXTRACT(MONTH FROM signal_date) IN (12, 1, 2) THEN strategy_return_1week 
    END) AS winter_avg_return
    
  FROM signal_returns
  WHERE strategy_return_1week IS NOT NULL
),
sharpe_trend AS (
  -- Calculate Sharpe trend
  SELECT 
    recent_sharpe_1week / NULLIF(standard_sharpe_1week, 0) AS sharpe_trend_ratio
  FROM sharpe_calculations
)
SELECT 
  -- Sharpe ratios
  s.standard_sharpe_1week,
  s.seasonal_adjusted_sharpe_1week,
  s.crisis_sharpe_1week,
  s.normal_sharpe_1week,
  s.weather_driven_sharpe_1week,
  s.labor_sharpe_1week,
  s.seasonal_event_sharpe_1week,
  s.recent_sharpe_1week,
  st.sharpe_trend_ratio,
  
  -- Portfolio metrics
  p.cumulative_return,
  p.max_drawdown,
  p.calmar_ratio,
  p.win_rate,
  p.profit_factor,
  
  -- Seasonal performance
  p.spring_avg_return,
  p.summer_avg_return,
  p.fall_avg_return,
  p.winter_avg_return,
  
  -- Best seasonal period
  CASE 
    WHEN GREATEST(p.spring_avg_return, p.summer_avg_return, p.fall_avg_return, p.winter_avg_return) = p.spring_avg_return THEN 'SPRING'
    WHEN GREATEST(p.spring_avg_return, p.summer_avg_return, p.fall_avg_return, p.winter_avg_return) = p.summer_avg_return THEN 'SUMMER'
    WHEN GREATEST(p.spring_avg_return, p.summer_avg_return, p.fall_avg_return, p.winter_avg_return) = p.fall_avg_return THEN 'FALL'
    ELSE 'WINTER'
  END AS best_seasonal_period,
  
  -- Performance rating
  CASE 
    WHEN s.seasonal_adjusted_sharpe_1week > 2.5 THEN 'EXCEPTIONAL'
    WHEN s.seasonal_adjusted_sharpe_1week > 1.8 THEN 'EXCELLENT'
    WHEN s.seasonal_adjusted_sharpe_1week > 1.2 THEN 'GOOD'
    WHEN s.seasonal_adjusted_sharpe_1week > 0.8 THEN 'FAIR'
    ELSE 'POOR'
  END AS soybean_performance_rating
  
FROM sharpe_calculations s
CROSS JOIN portfolio_metrics p
CROSS JOIN sharpe_trend st;

-- ----------------------------------------------------------------------------
-- 3B. Create MAPE Performance Tracking View
-- ----------------------------------------------------------------------------

CREATE OR REPLACE VIEW `cbi-v14.performance.vw_forecast_performance_tracking` AS
WITH forecast_history AS (
  -- Get historical forecasts
  SELECT 
    signal_date,
    master_regime_classification,
    crisis_intensity_score,
    zl_price_current,
    nn_forecast_1week,
    nn_forecast_1month,
    nn_forecast_3month
  FROM `cbi-v14.api.vw_ultimate_adaptive_signal_historical`
  WHERE signal_date <= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
),
actual_prices AS (
  -- Get actual prices
  SELECT 
    DATE(time) AS price_date,
    close AS actual_price
  FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
  WHERE symbol = 'ZL'
    AND time <= CURRENT_DATE()
),
forecast_vs_actual AS (
  -- Compare forecasts to actuals
  SELECT 
    f.signal_date AS forecast_date,
    f.master_regime_classification,
    f.crisis_intensity_score,
    f.zl_price_current AS price_at_forecast,
    
    -- 1-week forecast vs actual
    f.nn_forecast_1week,
    a1w.actual_price AS actual_1week_price,
    CASE 
      WHEN a1w.actual_price IS NOT NULL 
      THEN ABS(f.nn_forecast_1week - a1w.actual_price) / NULLIF(a1w.actual_price, 0) * 100
    END AS mape_1week,
    
    -- 1-month forecast vs actual
    f.nn_forecast_1month,
    a1m.actual_price AS actual_1month_price,
    CASE 
      WHEN a1m.actual_price IS NOT NULL 
      THEN ABS(f.nn_forecast_1month - a1m.actual_price) / NULLIF(a1m.actual_price, 0) * 100
    END AS mape_1month,
    
    -- 3-month forecast vs actual
    f.nn_forecast_3month,
    a3m.actual_price AS actual_3month_price,
    CASE 
      WHEN a3m.actual_price IS NOT NULL 
      THEN ABS(f.nn_forecast_3month - a3m.actual_price) / NULLIF(a3m.actual_price, 0) * 100
    END AS mape_3month
    
  FROM forecast_history f
  LEFT JOIN actual_prices a1w 
    ON DATE_ADD(f.signal_date, INTERVAL 7 DAY) = a1w.price_date
  LEFT JOIN actual_prices a1m 
    ON DATE_ADD(f.signal_date, INTERVAL 30 DAY) = a1m.price_date
  LEFT JOIN actual_prices a3m 
    ON DATE_ADD(f.signal_date, INTERVAL 90 DAY) = a3m.price_date
)
SELECT 
  -- Overall MAPE
  AVG(mape_1week) AS overall_mape_1week,
  AVG(mape_1month) AS overall_mape_1month,
  AVG(mape_3month) AS overall_mape_3month,
  
  -- Regime-specific MAPE
  AVG(CASE 
    WHEN master_regime_classification LIKE '%CRISIS%' THEN mape_1week 
  END) AS crisis_mape_1week,
  AVG(CASE 
    WHEN master_regime_classification = 'FUNDAMENTALS_REGIME' THEN mape_1week 
  END) AS normal_mape_1week,
  
  -- Recent MAPE (last 30 days)
  AVG(CASE 
    WHEN forecast_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) THEN mape_1week 
  END) AS recent_mape_1week,
  
  -- MAPE trend
  SAFE_DIVIDE(
    AVG(CASE 
      WHEN forecast_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) THEN mape_1week 
    END),
    AVG(CASE 
      WHEN forecast_date < DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) THEN mape_1week 
    END)
  ) AS mape_trend_ratio,
  
  -- Counts
  COUNT(mape_1week) AS total_1week_records,
  COUNT(mape_1month) AS total_1month_records,
  COUNT(mape_3month) AS total_3month_records
  
FROM forecast_vs_actual
WHERE mape_1week IS NOT NULL;

-- ----------------------------------------------------------------------------
-- 3C. Create Historical Tracking Tables
-- ----------------------------------------------------------------------------

-- MAPE historical tracking
CREATE TABLE IF NOT EXISTS `cbi-v14.performance.mape_historical_tracking`
(
  tracking_date DATE NOT NULL,
  overall_mape_1week FLOAT64,
  overall_mape_1month FLOAT64,
  overall_mape_3month FLOAT64,
  crisis_mape_1week FLOAT64,
  normal_mape_1week FLOAT64,
  recent_mape_1week FLOAT64,
  mape_trend_ratio FLOAT64,
  total_1week_records INT64,
  total_1month_records INT64,
  total_3month_records INT64,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY tracking_date
CLUSTER BY tracking_date;

-- Soybean Sharpe historical tracking
CREATE TABLE IF NOT EXISTS `cbi-v14.performance.soybean_sharpe_historical_tracking`
(
  tracking_date DATE NOT NULL,
  standard_sharpe_1week FLOAT64,
  seasonal_adjusted_sharpe_1week FLOAT64,
  crisis_sharpe_1week FLOAT64,
  normal_sharpe_1week FLOAT64,
  weather_driven_sharpe_1week FLOAT64,
  seasonal_event_sharpe_1week FLOAT64,
  recent_sharpe_1week FLOAT64,
  sharpe_trend_ratio FLOAT64,
  cumulative_return FLOAT64,
  max_drawdown FLOAT64,
  calmar_ratio FLOAT64,
  win_rate FLOAT64,
  profit_factor FLOAT64,
  spring_avg_return FLOAT64,
  summer_avg_return FLOAT64,
  fall_avg_return FLOAT64,
  winter_avg_return FLOAT64,
  best_seasonal_period STRING,
  soybean_performance_rating STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY tracking_date
CLUSTER BY tracking_date;

-- ----------------------------------------------------------------------------
-- 3D. Initial Population of Tracking Tables
-- ----------------------------------------------------------------------------

-- Populate MAPE tracking (idempotent)
MERGE `cbi-v14.performance.mape_historical_tracking` T
USING (
  SELECT 
    CURRENT_DATE() AS tracking_date,
    overall_mape_1week,
    overall_mape_1month,
    overall_mape_3month,
    crisis_mape_1week,
    normal_mape_1week,
    recent_mape_1week,
    mape_trend_ratio,
    total_1week_records,
    total_1month_records,
    total_3month_records
  FROM `cbi-v14.performance.vw_forecast_performance_tracking`
) S
ON T.tracking_date = S.tracking_date
WHEN MATCHED THEN UPDATE SET
  overall_mape_1week = S.overall_mape_1week,
  overall_mape_1month = S.overall_mape_1month,
  overall_mape_3month = S.overall_mape_3month,
  crisis_mape_1week = S.crisis_mape_1week,
  normal_mape_1week = S.normal_mape_1week,
  recent_mape_1week = S.recent_mape_1week,
  mape_trend_ratio = S.mape_trend_ratio,
  total_1week_records = S.total_1week_records,
  total_1month_records = S.total_1month_records,
  total_3month_records = S.total_3month_records
WHEN NOT MATCHED THEN INSERT ROW;

-- Populate Sharpe tracking (idempotent)
MERGE `cbi-v14.performance.soybean_sharpe_historical_tracking` T
USING (
  SELECT 
    CURRENT_DATE() AS tracking_date,
    standard_sharpe_1week,
    seasonal_adjusted_sharpe_1week,
    crisis_sharpe_1week,
    normal_sharpe_1week,
    weather_driven_sharpe_1week,
    seasonal_event_sharpe_1week,
    recent_sharpe_1week,
    sharpe_trend_ratio,
    cumulative_return,
    max_drawdown,
    calmar_ratio,
    win_rate,
    profit_factor,
    spring_avg_return,
    summer_avg_return,
    fall_avg_return,
    winter_avg_return,
    best_seasonal_period,
    soybean_performance_rating
  FROM `cbi-v14.performance.vw_soybean_sharpe_metrics`
) S
ON T.tracking_date = S.tracking_date
WHEN MATCHED THEN UPDATE SET
  standard_sharpe_1week = S.standard_sharpe_1week,
  seasonal_adjusted_sharpe_1week = S.seasonal_adjusted_sharpe_1week,
  crisis_sharpe_1week = S.crisis_sharpe_1week,
  normal_sharpe_1week = S.normal_sharpe_1week,
  weather_driven_sharpe_1week = S.weather_driven_sharpe_1week,
  seasonal_event_sharpe_1week = S.seasonal_event_sharpe_1week,
  recent_sharpe_1week = S.recent_sharpe_1week,
  sharpe_trend_ratio = S.sharpe_trend_ratio,
  cumulative_return = S.cumulative_return,
  max_drawdown = S.max_drawdown,
  calmar_ratio = S.calmar_ratio,
  win_rate = S.win_rate,
  profit_factor = S.profit_factor,
  spring_avg_return = S.spring_avg_return,
  summer_avg_return = S.summer_avg_return,
  fall_avg_return = S.fall_avg_return,
  winter_avg_return = S.winter_avg_return,
  best_seasonal_period = S.best_seasonal_period,
  soybean_performance_rating = S.soybean_performance_rating
WHEN NOT MATCHED THEN INSERT ROW;

-- ----------------------------------------------------------------------------
-- VERIFICATION
-- ----------------------------------------------------------------------------

-- Verify Sharpe metrics
SELECT 
  'Sharpe Metrics' AS metric_type,
  seasonal_adjusted_sharpe_1week,
  win_rate,
  profit_factor,
  soybean_performance_rating
FROM `cbi-v14.performance.vw_soybean_sharpe_metrics`;

-- Verify MAPE metrics
SELECT 
  'MAPE Metrics' AS metric_type,
  overall_mape_1week,
  recent_mape_1week,
  mape_trend_ratio
FROM `cbi-v14.performance.vw_forecast_performance_tracking`;

-- Phase 3 complete
SELECT 
  'Phase 3 Status' AS phase,
  'COMPLETE' AS status,
  CURRENT_TIMESTAMP() AS completion_time;
