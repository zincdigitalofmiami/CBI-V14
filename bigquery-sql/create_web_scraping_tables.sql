-- ============================================
-- PHASE 0.2: WEB SCRAPING TABLES
-- ============================================
-- Create all 15 web scraping tables for CBI-V14

-- ============================================
-- PRICE & MARKET DATA TABLES
-- ============================================

CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.futures_prices_barchart` (
  symbol STRING,
  contract_month DATE,
  last FLOAT64,
  change FLOAT64,
  change_pct FLOAT64,
  volume INT64,
  open_interest INT64,
  high FLOAT64,
  low FLOAT64,
  scrape_timestamp TIMESTAMP,
  source_url STRING
);

CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.futures_prices_marketwatch` (
  symbol STRING,
  contract_month DATE,
  last FLOAT64,
  change FLOAT64,
  change_pct FLOAT64,
  volume INT64,
  open_interest INT64,
  high FLOAT64,
  low FLOAT64,
  scrape_timestamp TIMESTAMP,
  source_url STRING
);

CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.futures_prices_investing` (
  symbol STRING,
  contract_month DATE,
  last FLOAT64,
  change FLOAT64,
  change_pct FLOAT64,
  volume INT64,
  high FLOAT64,
  low FLOAT64,
  technical_indicator_rsi FLOAT64,
  technical_indicator_macd FLOAT64,
  scrape_timestamp TIMESTAMP,
  source_url STRING
);

CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.futures_sentiment_tradingview` (
  symbol STRING,
  bullish_pct FLOAT64,
  bearish_pct FLOAT64,
  price_target_high FLOAT64,
  price_target_low FLOAT64,
  scrape_timestamp TIMESTAMP,
  source_url STRING
);

-- ============================================
-- POLICY & LEGISLATION TABLES
-- ============================================

CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.policy_rfs_volumes` (
  policy_id STRING,
  announcement_date DATE,
  effective_start DATE,
  effective_end DATE,
  category STRING,  -- RFS, RIN, SRE, 45Z
  value_num FLOAT64,
  unit STRING,
  proposal_date DATE,
  comment_period_end DATE,
  finalization_date DATE,
  source_url STRING,
  raw_html_excerpt STRING,
  scrape_timestamp TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.legislative_bills` (
  bill_id STRING,
  congress INT64,
  introduced DATE,
  latest_action DATE,
  latest_action_text STRING,
  title STRING,
  sponsors ARRAY<STRING>,
  committees ARRAY<STRING>,
  subjects ARRAY<STRING>,
  text_excerpt STRING,
  url STRING,
  scrape_timestamp TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.policy_events_federalregister` (
  doc_id STRING,
  published_at TIMESTAMP,
  effective_date DATE,
  agency ARRAY<STRING>,
  doc_type STRING,
  title STRING,
  summary STRING,
  full_text_excerpt STRING,
  topics ARRAY<STRING>,
  url STRING,
  scrape_timestamp TIMESTAMP
);

-- ============================================
-- FUNDAMENTALS & REPORTS TABLES
-- ============================================

CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.ers_oilcrops_monthly` (
  report_date DATE,
  crush_margin_usd_per_bu FLOAT64,
  crush_forecast_mbu FLOAT64,
  soybean_oil_stocks_mlbs FLOAT64,
  meal_stocks_ktons FLOAT64,
  exports_mbu FLOAT64,
  price_forecast_low FLOAT64,
  price_forecast_high FLOAT64,
  notes STRING,
  source_url STRING,
  raw_pdf_text_excerpt STRING,
  scrape_timestamp TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.usda_wasde_soy` (
  report_date DATE,
  series STRING,
  region STRING,
  value FLOAT64,
  unit STRING,
  previous_value FLOAT64,
  change FLOAT64,
  forecast_value FLOAT64,
  source_url STRING,
  table_page_num INT64,
  scrape_timestamp TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.news_industry_brownfield` (
  news_id STRING,
  published_at TIMESTAMP,
  title STRING,
  author STRING,
  full_text STRING,
  categories ARRAY<STRING>,
  entities ARRAY<STRING>,
  url STRING,
  scrape_timestamp TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.news_market_farmprogress` (
  news_id STRING,
  published_at TIMESTAMP,
  title STRING,
  author STRING,
  full_text STRING,
  categories ARRAY<STRING>,
  entities ARRAY<STRING>,
  url STRING,
  scrape_timestamp TIMESTAMP
);

-- ============================================
-- WEATHER & CLIMATE TABLES
-- ============================================

CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.enso_climate_status` (
  as_of_date DATE,
  enso_phase STRING,
  probability FLOAT64,
  outlook_months INT64,
  strength STRING,
  forecast_phase_1mo STRING,
  forecast_phase_3mo STRING,
  notes STRING,
  source_url STRING,
  scrape_timestamp TIMESTAMP
);

-- ============================================
-- INDUSTRY INTELLIGENCE TABLES
-- ============================================

CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.industry_intelligence_asa` (
  article_id STRING,
  published_at TIMESTAMP,
  title STRING,
  full_text STRING,
  policy_position STRING,
  capacity_mention_mmbu FLOAT64,
  url STRING,
  scrape_timestamp TIMESTAMP
);

-- ============================================
-- MACRO & TRADE TABLES
-- ============================================

CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.news_reuters` (
  news_id STRING,
  published_at TIMESTAMP,
  title STRING,
  full_text STRING,
  categories ARRAY<STRING>,
  region STRING,
  entities ARRAY<STRING>,
  sentiment FLOAT64,
  url STRING,
  scrape_timestamp TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.futures_prices_cme_public` (
  symbol STRING,
  contract_month DATE,
  settlement_price FLOAT64,
  volume INT64,
  open_interest INT64,
  scrape_timestamp TIMESTAMP,
  source_url STRING
);

-- ============================================
-- CORRELATION & SUBSTITUTION TABLES
-- ============================================

CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.market_analysis_correlations` (
  article_id STRING,
  published_at TIMESTAMP,
  correlation_zl_palm FLOAT64,
  correlation_zl_canola FLOAT64,
  correlation_zl_crude FLOAT64,
  spread_zl_palm FLOAT64,
  substitution_trigger_price FLOAT64,
  analysis_text STRING,
  url STRING,
  scrape_timestamp TIMESTAMP
);




