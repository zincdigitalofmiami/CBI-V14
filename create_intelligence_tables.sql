-- Create Intelligence Collection Tables for CBI-V14
-- Run in BigQuery Console to prepare for intelligence deployment

-- 1. News Intelligence Table (multi_source_news.py)
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.news_intelligence` (
  headline STRING,
  source STRING,
  category STRING,
  url STRING,
  published STRING,
  content STRING,
  intelligence_score FLOAT64,
  processed_timestamp TIMESTAMP
)
PARTITION BY DATE(processed_timestamp)
CLUSTER BY category, source;

-- 2. ICE & Trump Intelligence Table (ice_trump_intelligence.py)  
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.ice_trump_intelligence` (
  source STRING,
  category STRING,
  text STRING,
  agricultural_impact FLOAT64,
  soybean_relevance FLOAT64,
  timestamp TIMESTAMP,
  priority INT64
)
PARTITION BY DATE(timestamp)
CLUSTER BY category;

-- 3. Social Intelligence Table (social_intelligence.py)
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.social_sentiment` (
  platform STRING,
  subreddit STRING,
  title STRING,
  score INT64,
  comments INT64,
  sentiment_score FLOAT64,
  timestamp TIMESTAMP,
  market_relevance STRING
)
PARTITION BY DATE(timestamp)
CLUSTER BY platform;

-- 4. Economic Intelligence Table (economic_intelligence.py)
-- Note: economic_indicators table exists but empty
-- Add currency data table
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.currency_data` (
  currency_pair STRING,
  rate FLOAT64,
  source STRING,
  timestamp TIMESTAMP,
  data_quality STRING
)
PARTITION BY DATE(timestamp)
CLUSTER BY currency_pair;

-- 5. Shipping Intelligence Table (shipping_intelligence.py)
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.shipping_alerts` (
  source STRING,
  alert_type STRING,
  location STRING,
  impact_level STRING,
  description STRING,
  timestamp TIMESTAMP
)
PARTITION BY DATE(timestamp)
CLUSTER BY location, alert_type;

-- 6. Intelligence Cycles Table (master_intelligence_controller.py)
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.intelligence_cycles` (
  cycle_timestamp TIMESTAMP,
  news_items INT64,
  economic_indicators INT64,
  shipping_alerts INT64,
  social_signals INT64,
  correlations_found INT64,
  new_sources INT64,
  intelligence_json STRING
)
PARTITION BY DATE(cycle_timestamp);
