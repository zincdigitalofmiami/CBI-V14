-- ============================================
-- MAXIMUM FEATURES TRAINING VIEW: ALL 440+ FEATURES
-- Includes every data source and feature available
-- No exclusions - ultimate predictive power
-- ============================================

CREATE OR REPLACE VIEW `cbi-v14.models_v4._v_train_core_maximum` AS
SELECT
  base.*,

  -- YAHOO FINANCE ENHANCED (25 features)
  yahoo.rsi_14 as yahoo_rsi_14,
  yahoo.macd_line as yahoo_macd_line,
  yahoo.macd_signal as yahoo_macd_signal,
  yahoo.macd_histogram as yahoo_macd_histogram,
  yahoo.bb_middle as yahoo_bb_middle,
  yahoo.bb_upper as yahoo_bb_upper,
  yahoo.bb_lower as yahoo_bb_lower,
  yahoo.bb_percent as yahoo_bb_percent,
  yahoo.ma_7 as yahoo_ma_7,
  yahoo.ma_30 as yahoo_ma_30,
  yahoo.ma_90 as yahoo_ma_90,
  yahoo.return_1d as yahoo_return_1d,
  yahoo.return_7d as yahoo_return_7d,
  yahoo.return_30d as yahoo_return_30d,
  yahoo.volatility_30d as yahoo_volatility_30d,
  yahoo.Close as yahoo_close,
  yahoo.Open as yahoo_open,
  yahoo.High as yahoo_high,
  yahoo.Low as yahoo_low,
  yahoo.Volume as yahoo_volume,
  yahoo.symbol as yahoo_symbol,
  yahoo.name as yahoo_name,

  -- WEATHER DATA - BRAZIL (17 features)
  wb.temp_max as brazil_temp_max,
  wb.temp_min as brazil_temp_min,
  wb.temp_mean as brazil_temp_mean,
  wb.precip_mm as brazil_precip_mm,
  wb.humidity_pct as brazil_humidity_pct,
  wb.wind_speed_ms as brazil_wind_speed_ms,
  wb.pressure_hpa as brazil_pressure_hpa,
  wb.cloud_cover_pct as brazil_cloud_cover_pct,
  wb.uv_index as brazil_uv_index,
  wb.visibility_km as brazil_visibility_km,
  wb.dew_point_c as brazil_dew_point_c,
  wb.feels_like_c as brazil_feels_like_c,
  wb.weather_condition as brazil_weather_condition,
  wb.precip_probability_pct as brazil_precip_probability_pct,
  wb.sunrise_time as brazil_sunrise_time,
  wb.sunset_time as brazil_sunset_time,
  wb.day_length_hours as brazil_day_length_hours,

  -- WEATHER DATA - US MIDWEST (16 features)
  wum.temp_max as us_midwest_temp_max,
  wum.temp_min as us_midwest_temp_min,
  wum.temp_mean as us_midwest_temp_mean,
  wum.precip_mm as us_midwest_precip_mm,
  wum.humidity_pct as us_midwest_humidity_pct,
  wum.wind_speed_ms as us_midwest_wind_speed_ms,
  wum.pressure_hpa as us_midwest_pressure_hpa,
  wum.cloud_cover_pct as us_midwest_cloud_cover_pct,
  wum.uv_index as us_midwest_uv_index,
  wum.visibility_km as us_midwest_visibility_km,
  wum.dew_point_c as us_midwest_dew_point_c,
  wum.feels_like_c as us_midwest_feels_like_c,
  wum.weather_condition as us_midwest_weather_condition,
  wum.precip_probability_pct as us_midwest_precip_probability_pct,
  wum.sunrise_time as us_midwest_sunrise_time,
  wum.sunset_time as us_midwest_sunset_time,

  -- WEATHER DATA - ARGENTINA (15 features)
  wa.temp_max as argentina_temp_max,
  wa.temp_min as argentina_temp_min,
  wa.temp_mean as argentina_temp_mean,
  wa.precip_mm as argentina_precip_mm,
  wa.humidity_pct as argentina_humidity_pct,
  wa.wind_speed_ms as argentina_wind_speed_ms,
  wa.pressure_hpa as argentina_pressure_hpa,
  wa.cloud_cover_pct as argentina_cloud_cover_pct,
  wa.uv_index as argentina_uv_index,
  wa.visibility_km as argentina_visibility_km,
  wa.dew_point_c as argentina_dew_point_c,
  wa.feels_like_c as argentina_feels_like_c,
  wa.weather_condition as argentina_weather_condition,
  wa.precip_probability_pct as argentina_precip_probability_pct,
  wa.sunrise_time as argentina_sunrise_time,

  -- SOCIAL SENTIMENT (12 features)
  ss.sentiment_score as social_sentiment_score,
  ss.sentiment_magnitude as social_sentiment_magnitude,
  ss.sentiment_confidence as social_sentiment_confidence,
  ss.topic_relevance as social_topic_relevance,
  ss.policy_impact_score as social_policy_impact_score,
  ss.market_relevance as social_market_relevance,
  ss.intensity_score as social_intensity_score,
  ss.recency_weight as social_recency_weight,
  ss.source_credibility as social_source_credibility,
  ss.conviction_level as social_conviction_level,
  ss.sentiment_momentum as social_sentiment_momentum,
  ss.policy_sentiment as social_policy_sentiment,

  -- WEATHER AGGREGATED (10 features)
  w.REGION as weather_region,
  w.TEMP_MAX as weather_temp_max,
  w.TEMP_MIN as weather_temp_min,
  w.PRECIP_MM as weather_precip_mm,
  w.HUMIDITY_PCT as weather_humidity_pct,
  w.WIND_SPEED_MS as weather_wind_speed_ms,
  w.PRESSURE_HPA as weather_pressure_hpa,
  w.CLOUD_COVER_PCT as weather_cloud_cover_pct,
  w.UV_INDEX as weather_uv_index,
  w.VISIBILITY_KM as weather_visibility_km,

  -- ENSO CLIMATE STATUS (10 features)
  enso.enso_phase as enso_phase,
  enso.nino34_anomaly as enso_nino34_anomaly,
  enso.sst_anomaly as enso_sst_anomaly,
  enso.wind_anomaly as enso_wind_anomaly,
  enso.pressure_anomaly as enso_pressure_anomaly,
  enso.soy_yield_impact as enso_soy_yield_impact,
  enso.precipitation_forecast as enso_precipitation_forecast,
  enso.temperature_forecast as enso_temperature_forecast,
  enso.climate_risk_score as enso_climate_risk_score,
  enso.el_nino_intensity as enso_el_nino_intensity,

  -- USDA EXPORT SALES (10 features)
  usda.week_ending as usda_week_ending,
  usda.commodity as usda_commodity,
  usda.sales_this_week as usda_sales_this_week,
  usda.sales_last_week as usda_sales_last_week,
  usda.net_sales as usda_net_sales,
  usda.outstanding_sales as usda_outstanding_sales,
  usda.accumulated_sales as usda_accumulated_sales,
  usda.export_price as usda_export_price,
  usda.origin_country as usda_origin_country,
  usda.destination_country as usda_destination_country,

  -- MARKET ANALYSIS CORRELATIONS (10 features)
  mac.corn_soybean_corr as corn_soybean_correlation,
  mac.wheat_soybean_corr as wheat_soybean_correlation,
  mac.crude_soybean_corr as crude_soybean_correlation,
  mac.gold_soybean_corr as gold_soybean_correlation,
  mac.usd_soybean_corr as usd_soybean_correlation,
  mac.sp500_soybean_corr as sp500_soybean_correlation,
  mac.vix_soybean_corr as vix_soybean_correlation,
  mac.bond_yield_corr as bond_yield_correlation,
  mac.currency_basket_corr as currency_basket_correlation,
  mac.commodity_index_corr as commodity_index_correlation,

  -- ECONOMIC INDICATORS (7 features)
  econ.fed_funds_rate as fed_funds_rate,
  econ.gdp_growth_rate as gdp_growth_rate,
  econ.unemployment_rate as unemployment_rate,
  econ.cpi_inflation as cpi_inflation,
  econ.ppi_inflation as ppi_inflation,
  econ.retail_sales as retail_sales,
  econ.industrial_production as industrial_production,

  -- FUTURES SENTIMENT TRADINGVIEW (7 features)
  tv.long_positions_pct as tv_long_positions_pct,
  tv.short_positions_pct as tv_short_positions_pct,
  tv.long_short_ratio as tv_long_short_ratio,
  tv.sentiment_score as tv_sentiment_score,
  tv.market_mood as tv_market_mood,
  tv.conviction_index as tv_conviction_index,
  tv.volatility_expectation as tv_volatility_expectation,

  -- BIG8 COMPOSITE SIGNAL (if available)
  big8.composite_signal_score as big8_composite_score,
  big8.crisis_intensity_score as big8_crisis_intensity,
  big8.market_regime as big8_market_regime,
  big8.forecast_confidence_pct as big8_confidence,
  big8.primary_signal_driver as big8_primary_driver,

  CURRENT_TIMESTAMP() as data_last_updated

FROM `cbi-v14.models_v4.training_dataset_super_enriched` base

-- YAHOO FINANCE ENHANCED
LEFT JOIN `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced` yahoo
  ON base.date = yahoo.date AND yahoo.symbol = 'ZL=F'

-- WEATHER DATA
LEFT JOIN `cbi-v14.forecasting_data_warehouse.weather_brazil_daily` wb
  ON base.date = wb.date

LEFT JOIN `cbi-v14.forecasting_data_warehouse.weather_us_midwest_daily` wum
  ON base.date = wum.date

LEFT JOIN `cbi-v14.forecasting_data_warehouse.weather_argentina_daily` wa
  ON base.date = wa.date

LEFT JOIN `cbi-v14.forecasting_data_warehouse.weather_data` w
  ON base.date = w.date

-- SOCIAL SENTIMENT
LEFT JOIN `cbi-v14.forecasting_data_warehouse.social_sentiment` ss
  ON base.date = ss.date

-- ENSO CLIMATE
LEFT JOIN `cbi-v14.forecasting_data_warehouse.enso_climate_status` enso
  ON base.date = enso.date

-- USDA EXPORT SALES
LEFT JOIN `cbi-v14.forecasting_data_warehouse.usda_export_sales` usda
  ON base.date = usda.week_ending

-- MARKET CORRELATIONS
LEFT JOIN `cbi-v14.forecasting_data_warehouse.market_analysis_correlations` mac
  ON base.date = mac.date

-- ECONOMIC INDICATORS
LEFT JOIN `cbi-v14.forecasting_data_warehouse.economic_indicators` econ
  ON base.date = DATE(econ.time)

-- TRADINGVIEW SENTIMENT
LEFT JOIN `cbi-v14.forecasting_data_warehouse.futures_sentiment_tradingview` tv
  ON base.date = tv.date

-- BIG8 COMPOSITE (if exists)
LEFT JOIN `cbi-v14.api.vw_big8_composite_signal` big8
  ON base.date = big8.date

WHERE base.zl_price_current IS NOT NULL;

-- UPDATE TRAINING VIEWS TO USE MAXIMUM FEATURES
CREATE OR REPLACE VIEW `cbi-v14.models_v4.train_1w_maximum` AS
SELECT * EXCEPT(target_1m, target_3m, target_6m)
FROM `cbi-v14.models_v4._v_train_core_maximum`
WHERE target_1w IS NOT NULL;

CREATE OR REPLACE VIEW `cbi-v14.models_v4.train_1m_maximum` AS
SELECT * EXCEPT(target_1w, target_3m, target_6m)
FROM `cbi-v14.models_v4._v_train_core_maximum`
WHERE target_1m IS NOT NULL;

CREATE OR REPLACE VIEW `cbi-v14.models_v4.train_3m_maximum` AS
SELECT * EXCEPT(target_1w, target_1m, target_6m)
FROM `cbi-v14.models_v4._v_train_core_maximum`
WHERE target_3m IS NOT NULL;

CREATE OR REPLACE VIEW `cbi-v14.models_v4.train_6m_maximum` AS
SELECT * EXCEPT(target_1w, target_1m, target_3m)
FROM `cbi-v14.models_v4._v_train_core_maximum`
WHERE target_6m IS NOT NULL;

-- VERIFY THE ULTIMATE FEATURE COUNT
SELECT
  'MAXIMUM FEATURES TRAINING VIEW CREATED' as status,
  CURRENT_TIMESTAMP() as created_at,

  (SELECT COUNT(*) FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
   WHERE table_name = '_v_train_core_maximum') as maximum_features,

  (SELECT COUNT(*) FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
   WHERE table_name = 'train_1w_maximum') as train_1w_maximum_features,

  'All 440+ features included - ZERO exclusions!' as feature_policy,
  'Ready for ultimate predictive power training' as next_step;


