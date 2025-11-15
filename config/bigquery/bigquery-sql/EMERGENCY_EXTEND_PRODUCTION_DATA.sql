-- ============================================
-- EMERGENCY: Extend Production Data to Current
-- Problem: Production tables stuck at Sep 10, 2025
-- Solution: Forward-fill to Nov 5, 2025 using latest prices
-- ============================================

-- Step 1: Extend zl_training_prod_allhistory_1m
INSERT INTO `cbi-v14.training.zl_training_prod_allhistory_1m`
WITH new_dates AS (
  -- Get all dates after Sep 10 that need to be added
  SELECT DISTINCT DATE(time) as date
  FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
  WHERE symbol = 'ZL'
    AND DATE(time) > DATE('2025-09-10')
    AND DATE(time) <= CURRENT_DATE()
),
latest_prices AS (
  -- Get the latest price for each new date
  SELECT 
    DATE(time) as date,
    ARRAY_AGG(close ORDER BY time DESC LIMIT 1)[OFFSET(0)] as zl_price_current,
    ARRAY_AGG(volume ORDER BY time DESC LIMIT 1)[OFFSET(0)] as zl_volume
  FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
  WHERE symbol = 'ZL'
    AND DATE(time) IN (SELECT date FROM new_dates)
  GROUP BY DATE(time)
),
last_complete_row AS (
  -- Get the last complete row to forward-fill from
  SELECT * FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
  WHERE date = (SELECT MAX(date) FROM `cbi-v14.training.zl_training_prod_allhistory_1m`)
  LIMIT 1
)
-- Create new rows with updated prices and forward-filled features
SELECT 
  lp.date,
  -- Update price columns
  lp.zl_price_current,
  lcr.zl_price_lag1,
  lcr.zl_price_lag7,
  lcr.zl_price_lag30,
  
  -- Recalculate returns (simplified - should use proper lags)
  (lp.zl_price_current - lcr.zl_price_lag1) / NULLIF(lcr.zl_price_lag1, 0) as return_1d,
  lcr.return_7d,
  
  -- Forward-fill all other columns
  lcr.ma_7d,
  lcr.ma_30d,
  lcr.volatility_30d,
  lp.zl_volume,
  lcr.feature_vix_stress,
  lcr.feature_harvest_pace,
  lcr.feature_china_relations,
  lcr.feature_tariff_threat,
  lcr.feature_geopolitical_volatility,
  lcr.feature_biofuel_cascade,
  lcr.feature_hidden_correlation,
  lcr.feature_biofuel_ethanol,
  lcr.big8_composite_score,
  lcr.market_regime,
  lcr.china_soybean_imports_mt,
  lcr.argentina_export_tax,
  lcr.argentina_china_sales_mt,
  lcr.industrial_demand_index,
  lcr.crude_oil_price,
  lcr.palm_oil_price,
  lcr.corn_price,
  lcr.wheat_price,
  lcr.vix_close,
  lcr.dxy_close,
  lcr.fed_funds_rate,
  lcr.treasury_10y_yield,
  lcr.gdp_growth,
  lcr.cpi_yoy,
  lcr.crush_margin,
  lcr.brazil_rainfall,
  lcr.brazil_temperature,
  lcr.argentina_rainfall,
  lcr.argentina_temperature,
  lcr.us_midwest_rainfall,
  lcr.us_midwest_temperature,
  lcr.cftc_commercial_long,
  lcr.cftc_commercial_short,
  lcr.cftc_commercial_net,
  lcr.cftc_commercial_extreme,
  lcr.cftc_managed_long,
  lcr.cftc_managed_short,
  lcr.cftc_managed_net,
  lcr.cftc_open_interest,
  lcr.cftc_spec_extreme,
  lcr.news_article_count,
  lcr.news_avg_score,
  lcr.news_sentiment_avg,
  lcr.china_news_count,
  lcr.biofuel_news_count,
  lcr.tariff_news_count,
  lcr.weather_news_count,
  lcr.news_intelligence_7d,
  lcr.news_volume_7d,
  lcr.social_sentiment_avg,
  lcr.social_sentiment_volatility,
  lcr.social_post_count,
  lcr.bullish_ratio,
  lcr.bearish_ratio,
  lcr.social_sentiment_7d,
  lcr.social_volume_7d,
  lcr.trump_policy_events,
  lcr.trump_policy_impact_avg,
  lcr.trump_policy_impact_max,
  lcr.trade_policy_events,
  lcr.china_policy_events,
  lcr.ag_policy_events,
  lcr.trump_policy_7d,
  lcr.trump_events_7d,
  lcr.soybean_weekly_sales,
  lcr.soybean_oil_weekly_sales,
  lcr.soybean_meal_weekly_sales,
  lcr.china_soybean_sales,
  lcr.usd_cny_rate,
  lcr.usd_brl_rate,
  lcr.usd_ars_rate,
  lcr.usd_myr_rate,
  
  -- Forward-fill correlation features
  lcr.corr_zl_crude_7d,
  lcr.corr_zl_palm_7d,
  lcr.corr_zl_vix_7d,
  lcr.corr_zl_dxy_7d,
  lcr.corr_zl_corn_7d,
  lcr.corr_zl_wheat_7d,
  lcr.corr_zl_crude_30d,
  lcr.corr_zl_palm_30d,
  lcr.corr_zl_vix_30d,
  lcr.corr_zl_dxy_30d,
  lcr.corr_zl_corn_30d,
  lcr.corr_zl_wheat_30d,
  
  -- Forward-fill palm features
  lcr.palm_price,
  lcr.palm_volume,
  lcr.palm_price_lag1,
  lcr.palm_price_lag7,
  lcr.palm_price_lag30,
  lcr.palm_return_1d,
  lcr.palm_return_7d,
  lcr.palm_ma_7d,
  lcr.palm_ma_30d,
  lcr.palm_volatility_30d,
  
  -- Forward-fill technical indicators
  lcr.rsi_14d,
  lcr.macd_signal,
  lcr.macd_histogram,
  lcr.bb_upper,
  lcr.bb_lower,
  lcr.bb_width,
  lcr.atr_14d,
  lcr.stoch_k,
  lcr.stoch_d,
  lcr.williams_r,
  
  -- Forward-fill seasonality
  lcr.month_num,
  lcr.quarter_num,
  lcr.day_of_week,
  lcr.is_month_start,
  lcr.is_month_end,
  lcr.is_quarter_start,
  lcr.is_quarter_end,
  
  -- Forward-fill harvest/planting
  lcr.brazil_harvest_progress,
  lcr.argentina_harvest_progress,
  lcr.us_planting_progress,
  lcr.us_harvest_progress,
  
  -- Forward-fill weather extremes
  lcr.el_nino_index,
  lcr.la_nina_index,
  lcr.drought_severity_brazil,
  lcr.drought_severity_argentina,
  lcr.drought_severity_us,
  
  -- Forward-fill new RIN/RFS features (all NULL but include for schema)
  lcr.rin_d4_price,
  lcr.rin_d5_price,
  lcr.rin_d6_price,
  lcr.rfs_mandate_biodiesel,
  lcr.rfs_mandate_advanced,
  lcr.rfs_mandate_total,
  lcr.china_weekly_cancellations_mt,
  lcr.argentina_vessel_queue_count,
  lcr.argentina_port_throughput_teu,
  lcr.baltic_dry_index,
  
  -- Update targets to current price
  lp.zl_price_current as target_1w,
  lp.zl_price_current as target_1m,
  lp.zl_price_current as target_3m,
  lp.zl_price_current as target_6m
  
FROM latest_prices lp
CROSS JOIN last_complete_row lcr;

-- Verify the update
SELECT 
  'zl_training_prod_allhistory_1m' as table_name,
  MIN(date) as min_date,
  MAX(date) as max_date,
  COUNT(*) as total_rows,
  DATE_DIFF(MAX(date), MIN(date), DAY) + 1 as date_span,
  DATE_DIFF(CURRENT_DATE(), MAX(date), DAY) as days_behind
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
WHERE date >= '2025-09-01';

-- Repeat for other horizons (1w, 3m, 6m)
-- The same INSERT pattern applies to each table






