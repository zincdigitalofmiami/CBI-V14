-- PHASE 2: BIGQUERY STORAGE STRUCTURE
-- Run this ONCE to create all required tables

-- 1. Current Forecasts (Monthly Vertex AI predictions)
CREATE TABLE IF NOT EXISTS `cbi-v14.api.current_forecasts` (
  prediction_date DATE,
  run_timestamp TIMESTAMP,
  current_price FLOAT64,
  forecast_1w FLOAT64,
  forecast_1m FLOAT64,
  forecast_3m FLOAT64,
  forecast_6m FLOAT64,
  confidence_1w FLOAT64,
  confidence_1m FLOAT64,
  confidence_3m FLOAT64,
  confidence_6m FLOAT64,
  signal_1w STRING,
  signal_1m STRING,
  signal_3m STRING,
  signal_6m STRING,
  model_1w_id STRING,
  model_1m_id STRING,
  model_3m_id STRING,
  model_6m_id STRING,
  deployment_minutes FLOAT64,
  total_cost_usd FLOAT64
);

-- 2. Hourly Prices (Yahoo Finance + Alpha Vantage)
CREATE TABLE IF NOT EXISTS `cbi-v14.market_data.hourly_prices` (
  timestamp TIMESTAMP,
  symbol STRING,
  price FLOAT64,
  volume INT64,
  source STRING,
  ingest_timestamp TIMESTAMP
);

-- 3. Daily Weather Updates
CREATE TABLE IF NOT EXISTS `cbi-v14.weather.daily_updates` (
  date DATE,
  region STRING,
  temp_max_c FLOAT64,
  temp_min_c FLOAT64,
  precipitation_mm FLOAT64,
  humidity_pct FLOAT64,
  source STRING,
  ingest_timestamp TIMESTAMP
);

-- 4. Daily Signal Calculations
CREATE TABLE IF NOT EXISTS `cbi-v14.signals.daily_calculations` (
  date DATE,
  vix_stress_score FLOAT64,
  harvest_pace_score FLOAT64,
  china_relations_score FLOAT64,
  tariff_threat_score FLOAT64,
  calculated_timestamp TIMESTAMP
);

