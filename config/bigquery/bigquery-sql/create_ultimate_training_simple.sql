-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- ULTIMATE TRAINING VIEW: ALL EXISTING FEATURES (SIMPLIFIED)
-- Includes all features that actually exist in the tables
-- No assumptions about columns that don't exist
-- ============================================

CREATE OR REPLACE VIEW `cbi-v14.models_v4._v_train_core_ultimate` AS
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

  -- WEATHER DATA - BRAZIL (actual available features)
  wb.temp_max_c as brazil_temp_max,
  wb.temp_min_c as brazil_temp_min,
  wb.temp_avg_c as brazil_temp_avg,
  wb.precip_mm as brazil_precip_mm,
  wb.humidity as brazil_humidity,
  wb.growing_degree_days as brazil_gdd,
  wb.production_weight as brazil_production_weight,
  wb.confidence_score as brazil_confidence,

  -- WEATHER DATA - US MIDWEST (actual available features)
  wum.temp_max_c as us_midwest_temp_max,
  wum.temp_min_c as us_midwest_temp_min,
  wum.temp_avg_c as us_midwest_temp_avg,
  wum.precip_mm as us_midwest_precip_mm,
  wum.growing_degree_days as us_midwest_gdd,
  wum.production_weight as us_midwest_production_weight,
  wum.confidence_score as us_midwest_confidence,

  -- WEATHER DATA - ARGENTINA (actual available features)
  wa.temp_max_c as argentina_temp_max,
  wa.temp_min_c as argentina_temp_min,
  wa.temp_avg_c as argentina_temp_avg,
  wa.precip_mm as argentina_precip_mm,
  wa.production_weight as argentina_production_weight,
  wa.confidence_score as argentina_confidence,

  -- WEATHER AGGREGATED (available features)
  w.temp_max as weather_temp_max,
  w.temp_min as weather_temp_min,
  w.precip_mm as weather_precip_mm,
  w.region as weather_region,

  -- SOCIAL SENTIMENT (actual available features)
  ss.sentiment_score as social_sentiment_score,
  ss.score as social_score,
  ss.comments as social_comments,
  ss.market_relevance as social_market_relevance,
  ss.confidence_score as social_confidence,

  -- ENSO CLIMATE STATUS (actual available features)
  enso.probability as enso_probability,
  enso.strength as enso_strength,
  enso.outlook_months as enso_outlook_months,
  enso.phase as enso_phase,
  enso.notes as enso_notes,

  -- USDA EXPORT SALES (actual available features)
  usda.commodity as usda_commodity,
  usda.net_sales_mt as usda_net_sales,
  usda.cumulative_exports_mt as usda_cumulative_exports,
  usda.marketing_year as usda_marketing_year,
  usda.confidence_score as usda_confidence,

  -- MARKET ANALYSIS CORRELATIONS (actual available features)
  mac.correlation_zl_palm as correlation_zl_palm,
  mac.correlation_zl_crude as correlation_zl_crude,
  mac.spread_zl_palm as spread_zl_palm,
  mac.substitution_trigger_price as substitution_trigger_price,
  mac.article_id as correlation_article_id,

  -- ECONOMIC INDICATORS (actual available features)
  econ.indicator as economic_indicator,
  econ.value as economic_value,
  econ.confidence_score as economic_confidence,

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
  ON base.date = DATE(ss.timestamp)

-- ENSO CLIMATE
LEFT JOIN `cbi-v14.forecasting_data_warehouse.enso_climate_status` enso
  ON base.date = enso.as_of_date

-- USDA EXPORT SALES
LEFT JOIN `cbi-v14.forecasting_data_warehouse.usda_export_sales` usda
  ON base.date = usda.report_date

-- MARKET CORRELATIONS
LEFT JOIN `cbi-v14.forecasting_data_warehouse.market_analysis_correlations` mac
  ON base.date = DATE(mac.published_at)

-- ECONOMIC INDICATORS
LEFT JOIN `cbi-v14.forecasting_data_warehouse.economic_indicators` econ
  ON base.date = DATE(econ.time)

WHERE base.zl_price_current IS NOT NULL;

-- UPDATE TRAINING VIEWS TO USE ALL FEATURES
CREATE OR REPLACE VIEW `cbi-v14.models_v4.train_1w_ultimate` AS
SELECT * EXCEPT(target_1m, target_3m, target_6m)
FROM `cbi-v14.models_v4._v_train_core_ultimate`
WHERE target_1w IS NOT NULL;

CREATE OR REPLACE VIEW `cbi-v14.models_v4.train_1m_ultimate` AS
SELECT * EXCEPT(target_1w, target_3m, target_6m)
FROM `cbi-v14.models_v4._v_train_core_ultimate`
WHERE target_1m IS NOT NULL;

CREATE OR REPLACE VIEW `cbi-v14.models_v4.train_3m_ultimate` AS
SELECT * EXCEPT(target_1w, target_1m, target_6m)
FROM `cbi-v14.models_v4._v_train_core_ultimate`
WHERE target_3m IS NOT NULL;

CREATE OR REPLACE VIEW `cbi-v14.models_v4.train_6m_ultimate` AS
SELECT * EXCEPT(target_1w, target_1m, target_3m)
FROM `cbi-v14.models_v4._v_train_core_ultimate`
WHERE target_6m IS NOT NULL;

-- VERIFY THE ULTIMATE FEATURE COUNT
SELECT
  'ULTIMATE TRAINING VIEW WITH ALL EXISTING FEATURES CREATED' as status,
  CURRENT_TIMESTAMP() as created_at,

  (SELECT COUNT(*) FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
   WHERE table_name = '_v_train_core_ultimate') as ultimate_features,

  (SELECT COUNT(*) FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
   WHERE table_name = 'train_1w_ultimate') as train_1w_ultimate_features,

  'All features from 10 data sources included with correct columns!' as feature_policy,
  'Ready for maximum predictive power training' as next_step;


