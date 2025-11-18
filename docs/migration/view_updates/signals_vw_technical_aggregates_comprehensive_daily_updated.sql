-- Updated signals.vw_technical_aggregates_comprehensive_daily
-- Updated: 2025-11-17 17:57:50

WITH price_technical AS (
  SELECT
    DATE(time) as date,
    yahoo_close as zl_price_current,
    50.0 as zl_rsi_14,
    (yahoo_close - LAG(close, 20) OVER (ORDER BY time)) / NULLIF(LAG(close, 20) OVER (ORDER BY time), 0) as zl_momentum_20d,
    STDDEV(close) OVER (ORDER BY time ROWS 19 PRECEDING) * SQRT(252) as zl_volatility_20d_annualized
  FROM `cbi-v14.forecasting_data_warehouse.yahoo_historical_prefixed`
  WHERE symbol = "ZL"
),
cftc_data AS (
  SELECT
    report_date as date,
    managed_money_net_position,
    managed_money_percentile_rank
  FROM `cbi-v14.curated.vw_cftc_positions_oilseeds_weekly`
),
sentiment_data AS (
  SELECT
    date,
    AVG(avg_sentiment_score) as news_sentiment_7d
  FROM `cbi-v14.signals.vw_news_sentiment_scores_daily`
  WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
  GROUP BY date
)
SELECT
  p.date,
  p.zl_price_current,
  p.zl_rsi_14,
  p.zl_momentum_20d,
  p.zl_volatility_20d_annualized,
  COALESCE(c.managed_money_net_position, 0) as cftc_managed_money_net_position,
  COALESCE(c.managed_money_percentile_rank, 0.5) as cftc_managed_money_percentile_rank,
  COALESCE(s.news_sentiment_7d, 0.5) as news_sentiment_7d,
  0.50 as social_sentiment_7d,
  CASE
    WHEN p.zl_rsi_14 > 70 AND p.zl_momentum_20d > 0.05 THEN 0.80
    WHEN p.zl_rsi_14 < 30 AND p.zl_momentum_20d < -0.05 THEN 0.20
    ELSE 0.50
  END as technical_momentum_signal,
  CASE
    WHEN c.managed_money_percentile_rank > 0.80 THEN 0.25
    WHEN c.managed_money_percentile_rank < 0.20 THEN 0.75
    ELSE 0.50
  END as market_structure_signal
FROM price_technical p
LEFT JOIN cftc_data c ON p.date = c.date
LEFT JOIN sentiment_data s ON p.date = s.date
WHERE p.date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
ORDER BY p.date DESC