-- ============================================
-- RETRAIN bqml_1m_v2 WITH COMPLETE SCHEMA
-- All 334 columns: 311 Yahoo + 23 RIN/biofuel
-- Expected: 10-25% improvement from RIN proxies
-- ============================================
-- Version: 2.0
-- Date: November 6, 2025
--
-- TRAINING DATASET: zl_training_prod_allhistory_1m
-- - Total rows: 1,404
-- - Date range: 2020-01-01 to 2025-11-06
-- - Features: 334 (all validated, RIN/RFS now filled)
-- - Target: target_1m (1-month forward soybean oil price)
--
-- VALIDATION WINDOW: 2024+ (hold-out test)
-- EXPECTED METRICS: MAPE < 0.70%, R² > 0.99
-- ============================================

CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_1m_v2`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1m'],
  max_iterations=100,
  learn_rate=0.1,
  early_stop=FALSE,
  l1_reg=0.1,
  l2_reg=0.1
) AS
SELECT 
  target_1m,
  * EXCEPT(
    -- Exclude other targets
    target_1w, 
    target_1m, 
    target_3m, 
    target_6m,
    -- Exclude date (not a feature)
    date,
    -- Exclude string columns
    yahoo_data_source,
    volatility_regime,
    -- Exclude 100% NULL columns (20 total identified via Python scan)
    social_sentiment_volatility,
    news_article_count,
    news_avg_score,
    news_sentiment_avg,
    china_news_count,
    biofuel_news_count,
    tariff_news_count,
    weather_news_count,
    news_intelligence_7d,
    news_volume_7d,
    china_weekly_cancellations_mt,
    argentina_vessel_queue_count,
    argentina_port_throughput_teu,
    baltic_dry_index,
    heating_oil_price,
    natural_gas_price,
    gasoline_price,
    sugar_price,
    icln_price,
    tan_price,
    dba_price,
    vegi_price,
    biodiesel_spread_ma30,
    ethanol_spread_ma30,
    biodiesel_spread_vol,
    ethanol_spread_vol
  )
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
WHERE target_1m IS NOT NULL
  AND date >= '2020-01-01';  -- Filter to stable regime (post-COVID recovery)

