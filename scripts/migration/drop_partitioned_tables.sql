-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- Drop all tables with daily partitioning that exceed the 4,000 partition limit

DROP TABLE IF EXISTS `cbi-v14.forecasting_data_warehouse.yahoo_historical_prefixed`;
DROP TABLE IF EXISTS `cbi-v14.forecasting_data_warehouse.fred_macro_expanded`;
DROP TABLE IF EXISTS `cbi-v14.forecasting_data_warehouse.weather_granular`;
DROP TABLE IF EXISTS `cbi-v14.forecasting_data_warehouse.eia_energy_granular`;
DROP TABLE IF EXISTS `cbi-v14.forecasting_data_warehouse.cftc_commitments`;
DROP TABLE IF EXISTS `cbi-v14.forecasting_data_warehouse.usda_reports_granular`;
DROP TABLE IF EXISTS `cbi-v14.forecasting_data_warehouse.alpha_es_intraday`;
DROP TABLE IF EXISTS `cbi-v14.forecasting_data_warehouse.alpha_commodities_daily`;
DROP TABLE IF EXISTS `cbi-v14.forecasting_data_warehouse.alpha_fx_daily`;
DROP TABLE IF EXISTS `cbi-v14.forecasting_data_warehouse.alpha_indicators_daily`;
DROP TABLE IF EXISTS `cbi-v14.forecasting_data_warehouse.alpha_news_sentiment`;
DROP TABLE IF EXISTS `cbi-v14.forecasting_data_warehouse.alpha_options_snapshot`;
DROP TABLE IF EXISTS `cbi-v14.features.master_features_canonical`;

