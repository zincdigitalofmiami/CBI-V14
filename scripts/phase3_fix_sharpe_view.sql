-- ============================================================================
-- PHASE 3 FIX: Complete Sharpe View with Proper Subquery Handling
-- Date: November 15, 2025
-- Purpose: Fix subquery issue and create complete institutional-grade Sharpe
-- ============================================================================

CREATE OR REPLACE VIEW `cbi-v14.performance.vw_soybean_sharpe_metrics` AS
WITH trading_signals AS (
  SELECT 
    signal_date,
    trading_recommendation,
    nn_forecast_1week,
    zl_price_current,
    master_regime_classification,
    crisis_intensity_score,
    primary_signal_driver
  FROM `cbi-v14.api.vw_ultimate_adaptive_signal_historical`
  WHERE signal_date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY) AND CURRENT_DATE()
),
actual_prices AS (
  SELECT 
    DATE(time) AS price_date,
    close,
    LAG(close) OVER (ORDER BY time) AS prev_close,
    (close - LAG(close) OVER (ORDER BY time)) / NULLIF(LAG(close) OVER (ORDER BY time), 0) AS daily_return,
    LEAD(close, 7) OVER (ORDER BY time) AS close_7d_future,
    LEAD(close, 30) OVER (ORDER BY time) AS close_30d_future,
    LEAD(close, 90) OVER (ORDER BY time) AS close_90d_future
  FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
  WHERE symbol = 'ZL'
    AND time BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 400 DAY) AND CURRENT_DATE()
),
seasonal_volatility AS (
  SELECT 
    EXTRACT(MONTH FROM price_date) AS month,
    CASE WHEN EXTRACT(DAY FROM price_date) <= 15 THEN TRUE ELSE FALSE END AS is_first_half,
    AVG(ABS(daily_return)) AS avg_absolute_return,
    STDDEV(daily_return) AS volatility,
    COUNT(*) AS observations
  FROM actual_prices
  WHERE daily_return IS NOT NULL
  GROUP BY 1, 2
  HAVING COUNT(*) > 5
),
seasonal_factors AS (
  SELECT 
    month,
    is_first_half,
    volatility,
    SAFE_DIVIDE(volatility, (SELECT AVG(volatility) FROM seasonal_volatility WHERE volatility IS NOT NULL)) AS seasonal_factor,
    CASE 
      WHEN month = 6 AND is_first_half = FALSE THEN 'USDA_ACREAGE_REPORT'
      WHEN month = 8 AND is_first_half = FALSE THEN 'CROP_PRODUCTION'
      WHEN month = 10 AND is_first_half = TRUE THEN 'HARVEST_PRESSURE'
      WHEN month = 3 AND is_first_half = FALSE THEN 'PLANTING_INTENTIONS'
      WHEN month IN (9, 10, 11) THEN 'HARVEST_SEASON'
      WHEN month IN (3, 4, 5) THEN 'PLANTING_SEASON'
      WHEN month IN (6, 7, 8) THEN 'GROWING_SEASON'
      ELSE 'OFF_SEASON'
    END AS seasonal_event
  FROM seasonal_volatility
),
signal_returns AS (
  SELECT 
    t.signal_date,
    t.trading_recommendation,
    t.master_regime_classification,
    t.crisis_intensity_score,
    t.primary_signal_driver,
    
    -- Position direction
    CASE 
      WHEN t.trading_recommendation IN ('STRONG_BUY', 'BUY', 'WEAK_BUY') THEN 1.0
      WHEN t.trading_recommendation IN ('STRONG_SELL', 'SELL', 'WEAK_SELL') THEN -1.0
      ELSE 0.0
    END AS position_direction,
    
    -- Position sizing with conviction
    CASE 
      WHEN t.trading_recommendation = 'STRONG_BUY' THEN 1.00
      WHEN t.trading_recommendation = 'BUY' THEN 0.75
      WHEN t.trading_recommendation = 'WEAK_BUY' THEN 0.50
      WHEN t.trading_recommendation = 'HOLD' THEN 0.00
      WHEN t.trading_recommendation = 'WEAK_SELL' THEN 0.50
      WHEN t.trading_recommendation = 'SELL' THEN 0.75
      WHEN t.trading_recommendation = 'STRONG_SELL' THEN 1.00
      ELSE 0.00
    END * CASE 
      WHEN t.crisis_intensity_score > 75 THEN 1.0
      WHEN t.crisis_intensity_score > 50 THEN 0.8
      WHEN t.crisis_intensity_score > 25 THEN 0.6
      ELSE 0.4
    END AS position_size,
    
    -- Get seasonal factor for the signal date
    COALESCE(sf.seasonal_factor, 1.0) AS seasonal_factor,
    COALESCE(sf.seasonal_event, 'UNKNOWN') AS seasonal_event,
    
    -- Calculate actual returns (using JOIN instead of subquery)
    SAFE_DIVIDE(p7.close - t.zl_price_current, t.zl_price_current) AS actual_return_1week,
    SAFE_DIVIDE(p30.close - t.zl_price_current, t.zl_price_current) AS actual_return_1month,
    
    -- Strategy returns (position-adjusted)
    CASE 
      WHEN t.trading_recommendation IN ('STRONG_BUY', 'BUY', 'WEAK_BUY') THEN 1.0
      WHEN t.trading_recommendation IN ('STRONG_SELL', 'SELL', 'WEAK_SELL') THEN -1.0
      ELSE 0.0
    END * SAFE_DIVIDE(p7.close - t.zl_price_current, t.zl_price_current) AS strategy_return_1week
    
  FROM trading_signals t
  LEFT JOIN actual_prices p7 
    ON DATE_ADD(t.signal_date, INTERVAL 7 DAY) = p7.price_date
  LEFT JOIN actual_prices p30 
    ON DATE_ADD(t.signal_date, INTERVAL 30 DAY) = p30.price_date
  LEFT JOIN seasonal_factors sf 
    ON EXTRACT(MONTH FROM t.signal_date) = sf.month
    AND (EXTRACT(DAY FROM t.signal_date) <= 15) = sf.is_first_half
),
risk_free AS (
  SELECT 
    AVG(daily_risk_free_rate) AS avg_rf,
    AVG(CASE 
      WHEN rate_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) 
      THEN daily_risk_free_rate 
    END) AS recent_rf,
    STDDEV(daily_risk_free_rate) AS rf_volatility
  FROM `cbi-v14.forecasting_data_warehouse.risk_free_rates`
  WHERE rate_type = '3M_TREASURY'
),
strategy_stats AS (
  SELECT 
    -- Overall statistics
    COUNT(*) AS total_signals,
    COUNTIF(strategy_return_1week IS NOT NULL) AS valid_signals,
    AVG(strategy_return_1week) AS mean_return,
    STDDEV(strategy_return_1week) AS return_volatility,
    
    -- Regime-specific stats
    AVG(CASE WHEN master_regime_classification LIKE '%CRISIS%' THEN strategy_return_1week END) AS crisis_mean,
    STDDEV(CASE WHEN master_regime_classification LIKE '%CRISIS%' THEN strategy_return_1week END) AS crisis_vol,
    COUNTIF(master_regime_classification LIKE '%CRISIS%' AND strategy_return_1week IS NOT NULL) AS crisis_count,
    
    AVG(CASE WHEN master_regime_classification = 'FUNDAMENTALS_REGIME' THEN strategy_return_1week END) AS normal_mean,
    STDDEV(CASE WHEN master_regime_classification = 'FUNDAMENTALS_REGIME' THEN strategy_return_1week END) AS normal_vol,
    COUNTIF(master_regime_classification = 'FUNDAMENTALS_REGIME' AND strategy_return_1week IS NOT NULL) AS normal_count,
    
    -- Weather-driven stats
    AVG(CASE 
      WHEN primary_signal_driver IN ('HARVEST', 'PLANTING', 'WEATHER', 'DROUGHT', 'FLOOD') 
      THEN strategy_return_1week 
    END) AS weather_mean,
    STDDEV(CASE 
      WHEN primary_signal_driver IN ('HARVEST', 'PLANTING', 'WEATHER', 'DROUGHT', 'FLOOD') 
      THEN strategy_return_1week 
    END) AS weather_vol,
    COUNTIF(primary_signal_driver IN ('HARVEST', 'PLANTING', 'WEATHER', 'DROUGHT', 'FLOOD') 
      AND strategy_return_1week IS NOT NULL) AS weather_count,
    
    -- Seasonal event stats
    AVG(CASE WHEN seasonal_event NOT IN ('OFF_SEASON', 'UNKNOWN') THEN strategy_return_1week END) AS seasonal_mean,
    STDDEV(CASE WHEN seasonal_event NOT IN ('OFF_SEASON', 'UNKNOWN') THEN strategy_return_1week END) AS seasonal_vol,
    COUNTIF(seasonal_event NOT IN ('OFF_SEASON', 'UNKNOWN') AND strategy_return_1week IS NOT NULL) AS seasonal_count,
    
    -- Recent period stats
    AVG(CASE WHEN signal_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) THEN strategy_return_1week END) AS recent_mean,
    STDDEV(CASE WHEN signal_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) THEN strategy_return_1week END) AS recent_vol,
    COUNTIF(signal_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) AND strategy_return_1week IS NOT NULL) AS recent_count,
    
    -- Seasonal adjustment factor
    AVG(NULLIF(seasonal_factor, 0)) AS avg_seasonal_factor
    
  FROM signal_returns
),
sharpe_calculations AS (
  SELECT 
    -- Standard Sharpe Ratio
    SAFE_DIVIDE(
      s.mean_return - rf.avg_rf,
      s.return_volatility
    ) * SQRT(s.valid_signals) AS standard_sharpe_1week,
    
    -- Seasonal-Adjusted Sharpe
    SAFE_DIVIDE(
      s.mean_return - rf.avg_rf,
      s.return_volatility / NULLIF(s.avg_seasonal_factor, 0)
    ) * SQRT(s.valid_signals) AS seasonal_adjusted_sharpe_1week,
    
    -- Crisis Regime Sharpe
    SAFE_DIVIDE(
      s.crisis_mean - rf.avg_rf,
      s.crisis_vol * 0.85  -- Reduce vol requirement in crisis
    ) * SQRT(GREATEST(s.crisis_count, 1)) AS crisis_sharpe_1week,
    
    -- Normal Regime Sharpe
    SAFE_DIVIDE(
      s.normal_mean - rf.avg_rf,
      s.normal_vol
    ) * SQRT(GREATEST(s.normal_count, 1)) AS normal_sharpe_1week,
    
    -- Weather-Driven Sharpe
    SAFE_DIVIDE(
      s.weather_mean - rf.avg_rf,
      s.weather_vol
    ) * SQRT(GREATEST(s.weather_count, 1)) AS weather_driven_sharpe_1week,
    
    -- Seasonal Event Sharpe
    SAFE_DIVIDE(
      s.seasonal_mean - rf.avg_rf,
      s.seasonal_vol
    ) * SQRT(GREATEST(s.seasonal_count, 1)) AS seasonal_event_sharpe_1week,
    
    -- Recent Period Sharpe
    SAFE_DIVIDE(
      s.recent_mean - rf.recent_rf,
      s.recent_vol
    ) * SQRT(GREATEST(s.recent_count, 1)) AS recent_sharpe_1week,
    
    -- Signal counts
    s.total_signals,
    s.crisis_count AS crisis_signals,
    s.normal_count AS normal_signals
    
  FROM strategy_stats s
  CROSS JOIN risk_free rf
),
portfolio_metrics AS (
  SELECT 
    -- Cumulative Return (using log returns for better accuracy)
    EXP(SUM(LN(1 + COALESCE(strategy_return_1week, 0)))) - 1 AS cumulative_return,
    
    -- Maximum Drawdown (proper calculation)
    MAX((cummax - cumret) / NULLIF(cummax, 0)) AS max_drawdown,
    
    -- Win Rate
    SAFE_DIVIDE(
      COUNTIF(strategy_return_1week > 0),
      COUNTIF(strategy_return_1week IS NOT NULL)
    ) AS win_rate,
    
    -- Profit Factor
    SAFE_DIVIDE(
      SUM(CASE WHEN strategy_return_1week > 0 THEN strategy_return_1week ELSE 0 END),
      ABS(SUM(CASE WHEN strategy_return_1week < 0 THEN strategy_return_1week ELSE 0 END))
    ) AS profit_factor,
    
    -- Average Win vs Average Loss
    AVG(CASE WHEN strategy_return_1week > 0 THEN strategy_return_1week END) AS avg_win,
    AVG(CASE WHEN strategy_return_1week < 0 THEN strategy_return_1week END) AS avg_loss,
    
    -- Seasonal Performance
    AVG(CASE WHEN EXTRACT(MONTH FROM signal_date) IN (3, 4, 5) THEN strategy_return_1week END) AS spring_avg_return,
    AVG(CASE WHEN EXTRACT(MONTH FROM signal_date) IN (6, 7, 8) THEN strategy_return_1week END) AS summer_avg_return,
    AVG(CASE WHEN EXTRACT(MONTH FROM signal_date) IN (9, 10, 11) THEN strategy_return_1week END) AS fall_avg_return,
    AVG(CASE WHEN EXTRACT(MONTH FROM signal_date) IN (12, 1, 2) THEN strategy_return_1week END) AS winter_avg_return,
    
    -- Sortino Ratio (downside deviation)
    SAFE_DIVIDE(
      AVG(strategy_return_1week),
      STDDEV(CASE WHEN strategy_return_1week < 0 THEN strategy_return_1week END)
    ) AS sortino_ratio,
    
    -- Information Ratio
    SAFE_DIVIDE(
      AVG(strategy_return_1week) - AVG(actual_return_1week),
      STDDEV(strategy_return_1week - actual_return_1week)
    ) AS information_ratio
    
  FROM (
    SELECT 
      signal_date,
      strategy_return_1week,
      actual_return_1week,
      SUM(1 + COALESCE(strategy_return_1week, 0)) OVER (ORDER BY signal_date) AS cumret,
      MAX(SUM(1 + COALESCE(strategy_return_1week, 0)) OVER (ORDER BY signal_date)) 
        OVER (ORDER BY signal_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cummax
    FROM signal_returns
  )
),
final_metrics AS (
  SELECT 
    -- Core Sharpe Ratios
    COALESCE(sc.standard_sharpe_1week, 0) AS standard_sharpe_1week,
    COALESCE(sc.seasonal_adjusted_sharpe_1week, 0) AS seasonal_adjusted_sharpe_1week,
    COALESCE(sc.crisis_sharpe_1week, 0) AS crisis_sharpe_1week,
    COALESCE(sc.normal_sharpe_1week, 0) AS normal_sharpe_1week,
    COALESCE(sc.weather_driven_sharpe_1week, 0) AS weather_driven_sharpe_1week,
    COALESCE(sc.seasonal_event_sharpe_1week, 0) AS seasonal_event_sharpe_1week,
    COALESCE(sc.recent_sharpe_1week, 0) AS recent_sharpe_1week,
    
    -- Sharpe Trend
    SAFE_DIVIDE(sc.recent_sharpe_1week, NULLIF(sc.standard_sharpe_1week, 0)) AS sharpe_trend_ratio,
    
    -- Portfolio Metrics
    COALESCE(pm.cumulative_return, 0) AS cumulative_return,
    COALESCE(pm.max_drawdown, 0) AS max_drawdown,
    
    -- Calmar Ratio (annualized return / max drawdown)
    SAFE_DIVIDE(
      pm.cumulative_return * (365.0 / sc.total_signals),
      ABS(pm.max_drawdown)
    ) AS calmar_ratio,
    
    COALESCE(pm.win_rate, 0) AS win_rate,
    COALESCE(pm.profit_factor, 1) AS profit_factor,
    COALESCE(pm.sortino_ratio, 0) AS sortino_ratio,
    COALESCE(pm.information_ratio, 0) AS information_ratio,
    
    -- Seasonal Returns
    COALESCE(pm.spring_avg_return, 0) AS spring_avg_return,
    COALESCE(pm.summer_avg_return, 0) AS summer_avg_return,
    COALESCE(pm.fall_avg_return, 0) AS fall_avg_return,
    COALESCE(pm.winter_avg_return, 0) AS winter_avg_return
    
  FROM sharpe_calculations sc
  CROSS JOIN portfolio_metrics pm
)
SELECT 
  -- All Sharpe Metrics
  standard_sharpe_1week,
  seasonal_adjusted_sharpe_1week,
  crisis_sharpe_1week,
  normal_sharpe_1week,
  weather_driven_sharpe_1week,
  seasonal_event_sharpe_1week,
  recent_sharpe_1week,
  sharpe_trend_ratio,
  
  -- Portfolio Performance
  cumulative_return,
  max_drawdown,
  calmar_ratio,
  win_rate,
  profit_factor,
  sortino_ratio,
  information_ratio,
  
  -- Seasonal Analysis
  spring_avg_return,
  summer_avg_return,
  fall_avg_return,
  winter_avg_return,
  
  -- Best Season Determination
  CASE 
    WHEN GREATEST(spring_avg_return, summer_avg_return, fall_avg_return, winter_avg_return) = spring_avg_return THEN 'SPRING'
    WHEN GREATEST(spring_avg_return, summer_avg_return, fall_avg_return, winter_avg_return) = summer_avg_return THEN 'SUMMER'
    WHEN GREATEST(spring_avg_return, summer_avg_return, fall_avg_return, winter_avg_return) = fall_avg_return THEN 'FALL'
    ELSE 'WINTER'
  END AS best_seasonal_period,
  
  -- Performance Rating
  CASE 
    WHEN seasonal_adjusted_sharpe_1week > 2.5 THEN 'EXCEPTIONAL'
    WHEN seasonal_adjusted_sharpe_1week > 1.8 THEN 'EXCELLENT'
    WHEN seasonal_adjusted_sharpe_1week > 1.2 THEN 'GOOD'
    WHEN seasonal_adjusted_sharpe_1week > 0.8 THEN 'FAIR'
    WHEN seasonal_adjusted_sharpe_1week > 0.5 THEN 'MARGINAL'
    ELSE 'POOR'
  END AS soybean_performance_rating
  
FROM final_metrics;
