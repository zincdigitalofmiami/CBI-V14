CREATE OR REPLACE VIEW `cbi-v14.api.vw_ultimate_adaptive_signal` AS
WITH current_comprehensive_data AS (
  -- Your existing base selection of signals + prices + regimes for "today"
  SELECT *
  FROM `cbi-v14.signals.vw_comprehensive_signal_universe`
  WHERE signal_date = CURRENT_DATE()
),

big8 AS (
  SELECT d.*
  FROM `cbi-v14.neural.vw_chris_priority_regime_detector` d
),

neural_predictions AS (
  -- Your existing prediction join (local models; forecasts already uploaded to BQ)
  SELECT c.*, b.*
  FROM current_comprehensive_data c
  LEFT JOIN big8 b ON b.date = c.signal_date
),

final_forecasts AS (
  -- Your existing horizon assembly (1w/1m/3m/6m/12m prices)
  SELECT *
  FROM neural_predictions
),

-- Performance sources (single-row views)
mape_metrics AS (
  SELECT
    overall_mape_1week,
    crisis_mape_1week,
    normal_mape_1week,
    mape_trend_ratio
  FROM `cbi-v14.performance.vw_forecast_performance_tracking`
),

soybean_sharpe AS (
  SELECT
    seasonal_adjusted_sharpe_1week,
    CASE WHEN master_regime_classification LIKE '%CRISIS%' THEN crisis_sharpe_1week
         ELSE normal_sharpe_1week END AS regime_sharpe_1week,
    weather_driven_sharpe_1week,
    best_seasonal_period,
    cumulative_return,
    max_drawdown,
    calmar_ratio,
    win_rate,
    profit_factor,
    soybean_performance_rating
  FROM `cbi-v14.performance.vw_soybean_sharpe_metrics`
)

SELECT
  f.*,

  -- Labor/ICE additions
  f.feature_labor_stress,
  f.labor_override_flag,
  f.primary_signal_driver_labor_aware AS primary_signal_driver,

  -- MAPE (regime-aware) + trend
  ROUND(m.overall_mape_1week, 1) AS overall_mape_1week,
  ROUND(CASE WHEN f.master_regime_classification LIKE '%CRISIS%'
       THEN m.crisis_mape_1week ELSE m.normal_mape_1week END, 1) AS relevant_regime_mape,
  CASE
    WHEN m.mape_trend_ratio < 0.9 THEN 'IMPROVING'
    WHEN m.mape_trend_ratio > 1.1 THEN 'DEGRADING'
    ELSE 'STABLE'
  END AS forecast_quality_trend,

  -- Soybean-specific Sharpe & portfolio metrics
  ROUND(s.seasonal_adjusted_sharpe_1week, 2) AS soybean_adjusted_sharpe,
  ROUND(s.regime_sharpe_1week, 2) AS soybean_regime_sharpe,
  ROUND(s.weather_driven_sharpe_1week, 2) AS weather_driven_sharpe,
  ROUND(s.cumulative_return * 100, 1) AS soybean_strategy_return_pct,
  ROUND(s.max_drawdown * 100, 1) AS max_drawdown_pct,
  ROUND(s.calmar_ratio, 2) AS calmar_ratio,
  ROUND(s.win_rate * 100, 1) AS win_rate_pct,
  ROUND(s.profit_factor, 2) AS soybean_profit_factor,
  s.soybean_performance_rating,
  s.best_seasonal_period

FROM final_forecasts f
CROSS JOIN mape_metrics m
CROSS JOIN soybean_sharpe s;

