-- ============================================================================
-- BigQuery Warehouse Rebuild - Phase 2: Create Core Tables
-- ============================================================================
-- Date: November 13, 2025
-- Project: CBI-V14 Soybean Oil Forecasting Platform
--
-- This script creates the core table schemas for the new warehouse structure.
-- Run after creating datasets (01_create_datasets.sql)
-- ============================================================================

-- Set project
SET @@project_id = 'cbi-v14';

-- ============================================================================
-- RAW INTELLIGENCE TABLES
-- ============================================================================

-- Soybean Oil Prices (Raw)
CREATE OR REPLACE TABLE `cbi-v14.raw_intelligence.commodities_agriculture_soybean_oil_raw_daily` (
  time TIMESTAMP NOT NULL,
  close_price FLOAT64 NOT NULL,
  open_price FLOAT64,
  high_price FLOAT64,
  low_price FLOAT64,
  volume INT64,
  source STRING NOT NULL,
  ingest_timestamp TIMESTAMP NOT NULL,
  data_quality_flag STRING
)
PARTITION BY DATE(time)
CLUSTER BY source
OPTIONS (
  description = 'Daily soybean oil prices from multiple sources (Yahoo, CME, Barchart)',
  require_partition_filter = TRUE
);

-- Weather Data (Raw)
CREATE OR REPLACE TABLE `cbi-v14.raw_intelligence.intelligence_weather_global_raw_daily` (
  time TIMESTAMP NOT NULL,
  region STRING NOT NULL,
  temperature_c FLOAT64,
  precipitation_mm FLOAT64,
  humidity_pct FLOAT64,
  source STRING NOT NULL,
  ingest_timestamp TIMESTAMP NOT NULL,
  data_quality_flag STRING
)
PARTITION BY DATE(time)
CLUSTER BY region, source
OPTIONS (
  description = 'Daily weather data from multiple sources (OpenMeteo, NOAA)',
  require_partition_filter = TRUE
);

-- Trump Policy Intelligence (Raw)
CREATE OR REPLACE TABLE `cbi-v14.raw_intelligence.intelligence_policy_trump_raw_daily` (
  time TIMESTAMP NOT NULL,
  source STRING NOT NULL,
  text STRING,
  category STRING,
  ingest_timestamp TIMESTAMP NOT NULL,
  data_quality_flag STRING
)
PARTITION BY DATE(time)
CLUSTER BY source, category
OPTIONS (
  description = 'Raw Trump policy intelligence from Truth Social and Federal Register',
  require_partition_filter = TRUE
);

-- News Intelligence (Raw)
CREATE OR REPLACE TABLE `cbi-v14.raw_intelligence.intelligence_news_general_raw_daily` (
  time TIMESTAMP NOT NULL,
  source STRING NOT NULL,
  headline STRING,
  text STRING,
  category STRING,
  ingest_timestamp TIMESTAMP NOT NULL,
  data_quality_flag STRING
)
PARTITION BY DATE(time)
CLUSTER BY source, category
OPTIONS (
  description = 'Raw news articles from Reuters and other news sources',
  require_partition_filter = TRUE
);

-- Social Sentiment (Raw)
CREATE OR REPLACE TABLE `cbi-v14.raw_intelligence.intelligence_sentiment_social_raw_daily` (
  time TIMESTAMP NOT NULL,
  source STRING NOT NULL,
  text STRING,
  platform STRING,
  ingest_timestamp TIMESTAMP NOT NULL,
  data_quality_flag STRING
)
PARTITION BY DATE(time)
CLUSTER BY source, platform
OPTIONS (
  description = 'Raw social media sentiment data from Reddit and other platforms',
  require_partition_filter = TRUE
);

-- ============================================================================
-- FEATURE TABLES
-- ============================================================================

-- General Master Features (Core feature set)
-- Note: This is a simplified schema - expand with all 290+ features
CREATE OR REPLACE TABLE `cbi-v14.features.general_master_daily` (
  date DATE NOT NULL,
  -- Price features
  zl_price_current FLOAT64,
  zl_volume INT64,
  -- Correlation features
  corr_zl_palm_30d FLOAT64,
  corr_zl_crude_30d FLOAT64,
  -- Volatility features
  vix_level FLOAT64,
  -- Macro features
  dxy_level FLOAT64,
  -- Policy features
  argentina_export_tax FLOAT64,
  brazil_market_share FLOAT64,
  -- Positioning features
  cftc_commercial_net FLOAT64,
  -- Technical features
  rsi_14 FLOAT64,
  ma_30d FLOAT64,
  -- Seasonal features
  seasonal_index FLOAT64,
  -- Event features
  event_impact_level INT64,
  -- Trade features
  china_tariff_rate FLOAT64,
  -- Add remaining 270+ features here
  -- Metadata
  training_weight INT64,
  market_regime STRING
)
PARTITION BY date
CLUSTER BY market_regime
OPTIONS (
  description = 'Master feature set for all horizons; columns aligned across horizons (290+ features)',
  require_partition_filter = TRUE
);

-- Biofuel RIN Proxy Features
CREATE OR REPLACE TABLE `cbi-v14.features.biofuel_rin_proxy_daily` (
  date DATE NOT NULL,
  rin_price_proxy FLOAT64,
  rfs_mandate_volume FLOAT64,
  ethanol_price FLOAT64,
  crude_oil_price FLOAT64,
  biofuel_demand_index FLOAT64,
  ingest_timestamp TIMESTAMP NOT NULL
)
PARTITION BY date
OPTIONS (
  description = 'Biofuel RIN proxy features derived from crude oil and ethanol prices',
  require_partition_filter = TRUE
);

-- CFTC Filled Features
CREATE OR REPLACE TABLE `cbi-v14.features.commodities_agriculture_cftc_filled_daily` (
  date DATE NOT NULL,
  commercial_long INT64,
  commercial_short INT64,
  commercial_net INT64,
  non_commercial_long INT64,
  non_commercial_short INT64,
  non_commercial_net INT64,
  total_long INT64,
  total_short INT64,
  open_interest INT64,
  ingest_timestamp TIMESTAMP NOT NULL
)
PARTITION BY date
OPTIONS (
  description = 'CFTC positioning data with missing values filled via interpolation',
  require_partition_filter = TRUE
);

-- ============================================================================
-- TRAINING TABLES
-- ============================================================================

-- Training Table - Horizon 1M (Example)
-- Note: Schema must match exactly across all horizons
CREATE OR REPLACE TABLE `cbi-v14.training.horizon_1m_production` (
  date DATE NOT NULL,
  -- Targets
  target_1w FLOAT64 NOT NULL,
  target_1m FLOAT64 NOT NULL,
  target_3m FLOAT64 NOT NULL,
  target_6m FLOAT64 NOT NULL,
  target_12m FLOAT64 NOT NULL,
  -- Features (copy from general_master_daily)
  zl_price_current FLOAT64,
  zl_volume INT64,
  corr_zl_palm_30d FLOAT64,
  corr_zl_crude_30d FLOAT64,
  vix_level FLOAT64,
  dxy_level FLOAT64,
  argentina_export_tax FLOAT64,
  brazil_market_share FLOAT64,
  cftc_commercial_net FLOAT64,
  rsi_14 FLOAT64,
  ma_30d FLOAT64,
  seasonal_index FLOAT64,
  event_impact_level INT64,
  china_tariff_rate FLOAT64,
  -- Add remaining 270+ features here (must match general_master_daily)
  -- Metadata
  training_weight INT64 NOT NULL,
  market_regime STRING NOT NULL
)
PARTITION BY date
CLUSTER BY market_regime
OPTIONS (
  description = '1-month horizon training data (290+ features) for ZL forecasting',
  require_partition_filter = TRUE
);

-- Training Table - Horizon 1W
CREATE OR REPLACE TABLE `cbi-v14.training.horizon_1w_production`
LIKE `cbi-v14.training.horizon_1m_production`
OPTIONS (
  description = '1-week horizon training data (290+ features) for ZL forecasting',
  require_partition_filter = TRUE
);

-- Training Table - Horizon 3M
CREATE OR REPLACE TABLE `cbi-v14.training.horizon_3m_production`
LIKE `cbi-v14.training.horizon_1m_production`
OPTIONS (
  description = '3-month horizon training data (290+ features) for ZL forecasting',
  require_partition_filter = TRUE
);

-- Training Table - Horizon 6M
CREATE OR REPLACE TABLE `cbi-v14.training.horizon_6m_production`
LIKE `cbi-v14.training.horizon_1m_production`
OPTIONS (
  description = '6-month horizon training data (290+ features) for ZL forecasting',
  require_partition_filter = TRUE
);

-- Training Table - Horizon 12M
CREATE OR REPLACE TABLE `cbi-v14.training.horizon_12m_production`
LIKE `cbi-v14.training.horizon_1m_production`
OPTIONS (
  description = '12-month horizon training data (290+ features) for ZL forecasting',
  require_partition_filter = TRUE
);

-- ============================================================================
-- PREDICTION TABLES
-- ============================================================================

-- Predictions - Horizon 1M
CREATE OR REPLACE TABLE `cbi-v14.predictions.horizon_1m_production` (
  date DATE NOT NULL,
  model_name STRING NOT NULL,
  p10 FLOAT64,
  p50 FLOAT64,
  p90 FLOAT64,
  point_prediction FLOAT64,
  buy_wait_monitor STRING,
  shap_top_factor STRING,
  shap_top_factor_contrib FLOAT64,
  ingest_timestamp TIMESTAMP NOT NULL
)
PARTITION BY date
CLUSTER BY model_name
OPTIONS (
  description = 'Daily 1-month horizon forecasts with quantiles and procurement signals',
  require_partition_filter = TRUE
);

-- ============================================================================
-- MONITORING TABLES
-- ============================================================================

-- Data Quality Daily
CREATE OR REPLACE TABLE `cbi-v14.monitoring.data_quality_daily` (
  date DATE NOT NULL,
  table_schema STRING NOT NULL,
  table_name STRING NOT NULL,
  freshness_days INT64,
  null_rate FLOAT64,
  duplicate_count INT64,
  row_count INT64,
  ingest_timestamp TIMESTAMP NOT NULL
)
PARTITION BY date
CLUSTER BY table_schema, table_name
OPTIONS (
  description = 'Daily data quality metrics for all tables',
  require_partition_filter = TRUE
);

-- Model Performance Daily
CREATE OR REPLACE TABLE `cbi-v14.monitoring.model_performance_daily` (
  date DATE NOT NULL,
  model_name STRING NOT NULL,
  table_source STRING NOT NULL,
  mape FLOAT64,
  mae FLOAT64,
  r2 FLOAT64,
  ingest_timestamp TIMESTAMP NOT NULL
)
PARTITION BY date
CLUSTER BY model_name
OPTIONS (
  description = 'Daily model performance metrics (MAPE, MAE, R²)',
  require_partition_filter = TRUE
);

-- Deduplication Conflicts
CREATE OR REPLACE TABLE `cbi-v14.monitoring.dedup_conflicts` (
  conflict_id STRING NOT NULL,
  table_name STRING NOT NULL,
  date DATE NOT NULL,
  column_name STRING NOT NULL,
  source_primary STRING NOT NULL,
  source_secondary STRING NOT NULL,
  value_primary FLOAT64,
  value_secondary FLOAT64,
  delta FLOAT64,
  pct_diff FLOAT64,
  resolution STRING,
  resolution_timestamp TIMESTAMP,
  review_required BOOL,
  reviewed_by STRING,
  review_notes STRING,
  created_timestamp TIMESTAMP NOT NULL
)
PARTITION BY date
CLUSTER BY table_name, column_name
OPTIONS (
  description = 'Audit log of deduplication conflicts and resolutions',
  require_partition_filter = TRUE
);

-- ============================================================================
-- Verification Query
-- ============================================================================
-- Run this to verify all tables were created successfully:
SELECT 
  table_schema,
  table_name,
  row_count,
  creation_time
FROM `cbi-v14.raw_intelligence.__TABLES__`
UNION ALL
SELECT 
  table_schema,
  table_name,
  row_count,
  creation_time
FROM `cbi-v14.features.__TABLES__`
UNION ALL
SELECT 
  table_schema,
  table_name,
  row_count,
  creation_time
FROM `cbi-v14.training.__TABLES__`
UNION ALL
SELECT 
  table_schema,
  table_name,
  row_count,
  creation_time
FROM `cbi-v14.predictions.__TABLES__`
UNION ALL
SELECT 
  table_schema,
  table_name,
  row_count,
  creation_time
FROM `cbi-v14.monitoring.__TABLES__`
ORDER BY table_schema, table_name;

