-- ============================================================================
-- CBI-V14 COMPLETE BIGQUERY SCHEMA
-- Date: November 18, 2025
-- Purpose: Production-grade schema aligned with Fresh Start Master Plan
-- Status: Ready for deployment to us-central1
-- ============================================================================

-- ============================================================================
-- PART 1: DATASETS
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS market_data
OPTIONS (
  location='us-central1',
  description='Market price data from DataBento and other sources'
);

CREATE SCHEMA IF NOT EXISTS raw_intelligence
OPTIONS (
  location='us-central1',
  description='Domain data: weather, policy, agricultural, energy, positioning, news'
);

CREATE SCHEMA IF NOT EXISTS regimes
OPTIONS (
  location='us-central1',
  description='Regime classifications for all dates and types'
);

CREATE SCHEMA IF NOT EXISTS drivers
OPTIONS (
  location='us-central1',
  description='Primary price drivers and impact analysis'
);

CREATE SCHEMA IF NOT EXISTS drivers_of_drivers
OPTIONS (
  location='us-central1',
  description='Meta-drivers and second-order impacts'
);

CREATE SCHEMA IF NOT EXISTS signals
OPTIONS (
  location='us-central1',
  description='Calculated signals, indicators, and Big 8'
);

CREATE SCHEMA IF NOT EXISTS features
OPTIONS (
  location='us-central1',
  description='Canonical feature tables for training and dashboard'
);

CREATE SCHEMA IF NOT EXISTS neural
OPTIONS (
  location='us-central1',
  description='Neural network training features and predictions'
);

-- ============================================================================
-- PART 2: MARKET DATA TABLES (DataBento + Alternatives)
-- ============================================================================

-- Table 1: DataBento Futures OHLCV 1-minute
-- All 29 symbols from DataBento (14 core + 6 FX + 9 additional)
CREATE OR REPLACE TABLE market_data.databento_futures_ohlcv_1m (
  ts_event TIMESTAMP NOT NULL,
  root STRING NOT NULL,
  symbol STRING NOT NULL,
  instrument_id INT64,
  open FLOAT64,
  high FLOAT64,
  low FLOAT64,
  close FLOAT64,
  volume INT64,
  publisher_id INT64,
  priority_tier INT64,              -- 1=5min (ZL,MES), 2=1hr (ES+others)
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(ts_event)
CLUSTER BY root, priority_tier
OPTIONS (
  partition_expiration_days=365,
  description='DataBento GLBX.MDP3 futures - 29 symbols, 1-minute OHLCV'
);

-- Table 2: DataBento Futures OHLCV Daily (for efficiency)
CREATE OR REPLACE TABLE market_data.databento_futures_ohlcv_1d (
  date DATE NOT NULL,
  root STRING NOT NULL,
  symbol STRING NOT NULL,
  open FLOAT64,
  high FLOAT64,
  low FLOAT64,
  close FLOAT64,
  volume INT64,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY root
OPTIONS (
  partition_expiration_days=1825,  -- 5 years
  description='DataBento GLBX.MDP3 futures - daily aggregates'
);

-- Table 3: Palm Oil (Barchart/ICE) - NOT on DataBento
CREATE OR REPLACE TABLE market_data.palm_oil_daily (
  date DATE NOT NULL,
  barchart_palm_close FLOAT64,
  barchart_palm_open FLOAT64,
  barchart_palm_high FLOAT64,
  barchart_palm_low FLOAT64,
  barchart_palm_volume INT64,
  barchart_palm_vol_20d FLOAT64,
  source STRING,                    -- 'barchart', 'ice', 'yahoo'
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
OPTIONS (
  partition_expiration_days=1825,
  description='Palm oil prices from Barchart/ICE - primary substitution driver for ZL'
);

-- Table 4: Competing Vegetable Oils (World Bank Pink Sheet / Alpha)
CREATE OR REPLACE TABLE market_data.oils_competing_daily (
  date DATE NOT NULL,
  worldbank_rapeseed_price FLOAT64,
  worldbank_sunflower_price FLOAT64,
  worldbank_canola_price FLOAT64,
  worldbank_olive_price FLOAT64,
  source STRING,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
OPTIONS (
  description='Competing vegetable oils from World Bank Pink Sheet'
);

-- Table 5: Spot FX (FRED/Yahoo for non-futures pairs)
CREATE OR REPLACE TABLE market_data.fx_spot_daily (
  date DATE NOT NULL,
  fred_usd_brl FLOAT64,             -- Brazil Real (critical for soy)
  fred_usd_cny FLOAT64,             -- Chinese Yuan (critical for demand)
  fred_usd_ars FLOAT64,             -- Argentine Peso (critical for competition)
  yahoo_usd_myr FLOAT64,            -- Malaysian Ringgit (for palm)
  fred_usd_eur FLOAT64,             -- Euro
  fred_usd_jpy FLOAT64,             -- Yen
  fred_dxy FLOAT64,                 -- Dollar Index
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
OPTIONS (
  description='Spot FX from FRED/Yahoo for currencies not on CME'
);

-- ============================================================================
-- PART 3: RAW INTELLIGENCE TABLES (Domain Data)
-- ============================================================================

-- Table 6: FRED Economic (EXISTING - DO NOT MODIFY SCHEMA)
-- Keep as-is, already working

-- Table 7: EIA Biofuels (Granular)
CREATE OR REPLACE TABLE raw_intelligence.eia_biofuels_granular (
  date DATE NOT NULL,
  eia_biodiesel_prod_padd1 FLOAT64,
  eia_biodiesel_prod_padd2 FLOAT64,
  eia_biodiesel_prod_padd3 FLOAT64,
  eia_biodiesel_prod_padd4 FLOAT64,
  eia_biodiesel_prod_padd5 FLOAT64,
  eia_biodiesel_prod_total FLOAT64,
  eia_ethanol_prod_total FLOAT64,
  eia_rin_price_d4 FLOAT64,
  eia_rin_price_d5 FLOAT64,
  eia_rin_price_d6 FLOAT64,
  eia_renewable_diesel_prod FLOAT64,
  eia_saf_prod FLOAT64,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
OPTIONS (
  description='EIA biofuels granular - PADD-level biodiesel, RIN prices, SAF production'
);

-- Table 8: USDA Granular (Exports, Yields, WASDE)
CREATE OR REPLACE TABLE raw_intelligence.usda_granular (
  date DATE NOT NULL,
  -- WASDE World
  usda_wasde_world_soyoil_prod FLOAT64,
  usda_wasde_world_soyoil_cons FLOAT64,
  usda_wasde_us_soyoil_prod FLOAT64,
  usda_wasde_us_soyoil_cons FLOAT64,
  usda_wasde_brazil_soybean_prod FLOAT64,
  usda_wasde_argentina_soybean_prod FLOAT64,
  -- Export Sales by Destination
  usda_exports_soybeans_net_sales_china FLOAT64,
  usda_exports_soybeans_net_sales_eu FLOAT64,
  usda_exports_soybeans_net_sales_total FLOAT64,
  usda_exports_soyoil_net_sales_total FLOAT64,
  -- Crop Progress by State
  usda_cropprog_illinois_soybeans_condition_pct FLOAT64,
  usda_cropprog_iowa_soybeans_condition_pct FLOAT64,
  usda_cropprog_indiana_soybeans_condition_pct FLOAT64,
  -- Grain Stocks
  usda_stocks_soybeans_total FLOAT64,
  usda_stocks_soyoil_total FLOAT64,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
OPTIONS (
  description='USDA granular data - WASDE, exports by destination, state yields'
);

-- Table 9: Weather Segmented (Raw Layer)
CREATE OR REPLACE TABLE raw_intelligence.weather_segmented (
  date DATE NOT NULL,
  country STRING NOT NULL,          -- US, BR, AR
  area_code STRING NOT NULL,        -- State/province code
  station_id STRING,
  latitude FLOAT64,
  longitude FLOAT64,
  temp_max_f FLOAT64,
  temp_min_f FLOAT64,
  temp_avg_f FLOAT64,
  precip_inches FLOAT64,
  gdd_base50 FLOAT64,
  gdd_base60 FLOAT64,
  soil_moisture_pct FLOAT64,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY country, area_code
OPTIONS (
  description='Weather data segmented by area code for US/BR/AR'
);

-- Table 10: Weather Production-Weighted (Aggregated Layer)
CREATE OR REPLACE TABLE raw_intelligence.weather_aggregated (
  date DATE NOT NULL,
  weather_us_midwest_tavg_f FLOAT64,
  weather_us_midwest_precip_inches FLOAT64,
  weather_us_midwest_gdd FLOAT64,
  weather_br_soy_belt_tavg_f FLOAT64,
  weather_br_soy_belt_precip_inches FLOAT64,
  weather_br_soy_belt_gdd FLOAT64,
  weather_ar_soy_belt_tavg_f FLOAT64,
  weather_ar_soy_belt_precip_inches FLOAT64,
  weather_ar_soy_belt_gdd FLOAT64,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
OPTIONS (
  description='Production-weighted weather aggregates for key regions'
);

-- Table 11: CFTC Positioning
CREATE OR REPLACE TABLE raw_intelligence.cftc_positioning (
  report_date DATE NOT NULL,
  commodity STRING NOT NULL,
  managed_money_long INT64,
  managed_money_short INT64,
  commercial_long INT64,
  commercial_short INT64,
  nonreportable_long INT64,
  nonreportable_short INT64,
  open_interest INT64,
  net_managed_money INT64,
  net_commercial INT64,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY report_date
CLUSTER BY commodity
OPTIONS (
  description='CFTC Commitments of Traders positioning data'
);

-- Table 12: News Bucketed (Topic, Regime, Correlation)
CREATE OR REPLACE TABLE raw_intelligence.news_bucketed (
  id STRING NOT NULL,
  published_at TIMESTAMP NOT NULL,
  headline STRING,
  content STRING,
  source STRING,
  topic_bucket STRING NOT NULL,
  regime STRING NOT NULL,
  correlation_group STRING,
  sentiment_score FLOAT64,
  sentiment_confidence FLOAT64,
  impact_symbols ARRAY<STRING>,
  priority STRING,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(published_at)
CLUSTER BY topic_bucket, regime
OPTIONS (
  description='News bucketed by topic, regime, and correlation group'
);

-- Table 13: Policy/Trump Signals (EXISTING SCRIPTS!)
CREATE OR REPLACE TABLE raw_intelligence.policy_trump_signals (
  date DATE NOT NULL,
  policy_trump_action_prob FLOAT64,
  policy_trump_action_type STRING,
  policy_trump_expected_zl_move FLOAT64,
  policy_trump_confidence FLOAT64,
  policy_trump_time_to_impact_hours INT64,
  policy_trump_procurement_alert STRING,
  policy_trump_source STRING,       -- truth_social, white_house, ustr, etc.
  policy_trump_text STRING,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
OPTIONS (
  description='Trump policy signals from existing trump_action_predictor.py and zl_impact_predictor.py'
);

-- Table 14: Alpha Vantage Insider Transactions
CREATE OR REPLACE TABLE raw_intelligence.alpha_insider_transactions (
  date DATE NOT NULL,
  symbol STRING NOT NULL,
  insider_name STRING,
  transaction_type STRING,
  shares INT64,
  price FLOAT64,
  value FLOAT64,
  ownership_pct FLOAT64,
  filing_date DATE,
  related_commodity STRING,
  impact_signal STRING,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY symbol, related_commodity
OPTIONS (
  description='Alpha Vantage insider transactions for biofuel/ag companies'
);

-- Table 15: Alpha Vantage Analytics
CREATE OR REPLACE TABLE raw_intelligence.alpha_analytics (
  date DATE NOT NULL,
  symbol STRING NOT NULL,
  window_type STRING NOT NULL,
  window_size STRING NOT NULL,
  metric_name STRING NOT NULL,
  metric_value FLOAT64,
  reference_symbol STRING,
  metadata JSON,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY symbol, metric_name
OPTIONS (
  description='Alpha Vantage pre-calculated analytics (fixed + sliding windows)'
);

-- ============================================================================
-- PART 4: VOLATILITY LAYER
-- ============================================================================

-- Table 16: Volatility Daily
CREATE OR REPLACE TABLE raw_intelligence.volatility_daily (
  date DATE NOT NULL,
  vol_vix_level FLOAT64,
  vol_vix_zscore FLOAT64,
  vol_zl_realized_20d FLOAT64,
  vol_es_realized_20d FLOAT64,
  vol_palm_realized_20d FLOAT64,
  vol_cl_realized_20d FLOAT64,
  vol_regime STRING,                -- high, low, crisis
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
OPTIONS (
  description='Volatility metrics for VIX, ZL, palm, ES, crude - drives regime detection'
);

-- ============================================================================
-- PART 5: REGIME TABLES
-- ============================================================================

-- Table 17: Market Regimes (All Types)
CREATE OR REPLACE TABLE regimes.market_regimes (
  date DATE NOT NULL,
  regime_type STRING NOT NULL,      -- market, volatility, positioning, weather, policy
  regime_value STRING NOT NULL,     -- bull, bear, crisis, normal, etc.
  confidence FLOAT64,
  metadata JSON,
  valid_from DATE,
  valid_to DATE,
  calculation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY regime_type, regime_value
OPTIONS (
  description='All regime classifications by date and type'
);

-- ============================================================================
-- PART 6: DRIVER TABLES
-- ============================================================================

-- Table 18: Primary Drivers
CREATE OR REPLACE TABLE drivers.primary_drivers (
  date DATE NOT NULL,
  driver_type STRING NOT NULL,
  driver_name STRING NOT NULL,
  value FLOAT64,
  target_symbol STRING,
  impact_direction STRING,
  impact_magnitude FLOAT64,
  lag_days INT64,
  correlation_7d FLOAT64,
  correlation_30d FLOAT64,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY driver_type, target_symbol
OPTIONS (
  description='Primary drivers with impact direction, magnitude, and lags'
);

-- Table 19: Drivers of Drivers (Meta-Drivers)
CREATE OR REPLACE TABLE drivers_of_drivers.meta_drivers (
  date DATE NOT NULL,
  primary_driver STRING NOT NULL,
  meta_driver_type STRING NOT NULL,
  meta_driver_name STRING NOT NULL,
  value FLOAT64,
  impact_chain STRING,
  lag_days INT64,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY primary_driver, meta_driver_type
OPTIONS (
  description='Drivers of drivers with impact chains (trump tariff → USD/CNY → china demand → ZL)'
);

-- ============================================================================
-- PART 7: SIGNALS & INDICATORS
-- ============================================================================

-- Table 20: Calculated Signals (Technical Indicators)
CREATE OR REPLACE TABLE signals.calculated_signals (
  date DATE NOT NULL,
  symbol STRING NOT NULL,
  signal_type STRING NOT NULL,
  signal_name STRING NOT NULL,
  value FLOAT64,
  parameters JSON,
  regime_adjusted BOOL,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY symbol, signal_type
OPTIONS (
  description='Technical indicators calculated from OHLCV (SMA, RSI, MACD, etc.)'
);

-- Table 21: Big Eight Live (15-minute refresh)
CREATE OR REPLACE TABLE signals.big_eight_live (
  signal_timestamp TIMESTAMP NOT NULL,
  symbol STRING DEFAULT 'ZL',
  
  -- Big 8 Pillars (prefixed)
  big8_substitution_score FLOAT64,
  big8_policy_shock_score FLOAT64,
  big8_weather_shock_score FLOAT64,
  big8_china_demand_score FLOAT64,
  big8_vix_stress_score FLOAT64,
  big8_cftc_positioning_score FLOAT64,
  big8_correlation_stress_score FLOAT64,
  big8_news_sentiment_score FLOAT64,
  
  -- Composite
  big8_composite_score FLOAT64,
  big8_signal_direction STRING,     -- bullish, bearish, neutral
  big8_signal_strength FLOAT64,     -- 0-100
  
  -- Context
  regime STRING,
  procurement_alert STRING,
  
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(signal_timestamp)
OPTIONS (
  partition_expiration_days=90,
  description='Big 8 signals refreshed every 15 minutes for dashboard'
);

-- ============================================================================
-- PART 8: CANONICAL FEATURE TABLE (Master Features)
-- ============================================================================

-- Table 22: Master Features (Canonical, mirrors Parquet)
CREATE OR REPLACE TABLE features.master_features_2000_2025 (
  date DATE NOT NULL,
  symbol STRING DEFAULT 'ZL',
  
  -- DataBento OHLCV (prefixed)
  databento_zl_open FLOAT64,
  databento_zl_high FLOAT64,
  databento_zl_low FLOAT64,
  databento_zl_close FLOAT64,
  databento_zl_volume INT64,
  
  -- Yahoo OHLCV (historical 2000-2010)
  yahoo_zl_open FLOAT64,
  yahoo_zl_high FLOAT64,
  yahoo_zl_low FLOAT64,
  yahoo_zl_close FLOAT64,
  yahoo_zl_volume INT64,
  
  -- Stitched (best available)
  zl_open FLOAT64,                  -- DataBento if available, else Yahoo
  zl_high FLOAT64,
  zl_low FLOAT64,
  zl_close FLOAT64,
  zl_volume INT64,
  
  -- Palm (Barchart)
  barchart_palm_close FLOAT64,
  barchart_palm_vol_20d FLOAT64,
  
  -- FX (FRED/Yahoo)
  fred_usd_brl FLOAT64,
  fred_usd_cny FLOAT64,
  fred_usd_ars FLOAT64,
  
  -- FRED Macro (~60 columns)
  fred_dff FLOAT64,
  fred_dgs10 FLOAT64,
  fred_vixcls FLOAT64,
  fred_dtwexbgs FLOAT64,
  -- ... (all 60 FRED series)
  
  -- EIA Biofuels
  eia_biodiesel_prod_total FLOAT64,
  eia_rin_price_d4 FLOAT64,
  eia_rin_price_d6 FLOAT64,
  
  -- USDA
  usda_wasde_world_soyoil_prod FLOAT64,
  usda_exports_soybeans_net_sales_china FLOAT64,
  
  -- Weather (production-weighted)
  weather_us_midwest_tavg_f FLOAT64,
  weather_br_soy_belt_tavg_f FLOAT64,
  weather_ar_soy_belt_tavg_f FLOAT64,
  weather_us_midwest_precip_inches FLOAT64,
  weather_br_soy_belt_precip_inches FLOAT64,
  
  -- CFTC
  cftc_zl_net_managed_money INT64,
  cftc_zl_net_commercial INT64,
  
  -- Volatility
  vol_vix_level FLOAT64,
  vol_zl_realized_20d FLOAT64,
  vol_palm_realized_20d FLOAT64,
  vol_regime STRING,
  
  -- Policy/Trump
  policy_trump_action_prob FLOAT64,
  policy_trump_expected_zl_move FLOAT64,
  policy_trump_procurement_alert STRING,
  
  -- News Sentiment
  news_sentiment_zl_score FLOAT64,
  news_sentiment_zl_confidence FLOAT64,
  
  -- Calculated Signals
  signal_zl_sma_50 FLOAT64,
  signal_zl_rsi_14 FLOAT64,
  signal_zl_macd FLOAT64,
  
  -- Regime
  regime STRING,
  
  -- Targets (for training)
  target_1w FLOAT64,
  target_1m FLOAT64,
  target_3m FLOAT64,
  target_6m FLOAT64,
  target_12m FLOAT64,
  
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
OPTIONS (
  description='Canonical feature table mirroring master_features_2000_2025.parquet - single source of truth'
);

-- ============================================================================
-- PART 9: NEURAL NETWORK TABLES
-- ============================================================================

-- Table 23: Neural Feature Vectors (Training)
CREATE OR REPLACE TABLE neural.feature_vectors (
  date DATE NOT NULL,
  symbol STRING NOT NULL,
  horizon STRING NOT NULL,
  features JSON NOT NULL,
  regime_id STRING,
  target_value FLOAT64,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY symbol, horizon
OPTIONS (
  description='Feature vectors for neural network training'
);

-- ============================================================================
-- PART 10: VIEWS (Dashboard & Query Layer)
-- ============================================================================

-- View 1: ZL Comprehensive (All data in one view)
CREATE OR REPLACE VIEW signals.vw_zl_comprehensive AS
WITH latest AS (
  SELECT date, zl_close, regime
  FROM features.master_features_2000_2025
  WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
),
big8_latest AS (
  SELECT 
    DATE(signal_timestamp) as date,
    big8_composite_score,
    big8_signal_direction,
    big8_signal_strength
  FROM signals.big_eight_live
  WHERE signal_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
  QUALIFY ROW_NUMBER() OVER (PARTITION BY DATE(signal_timestamp) ORDER BY signal_timestamp DESC) = 1
)
SELECT 
  l.*,
  b.big8_composite_score,
  b.big8_signal_direction,
  b.big8_signal_strength
FROM latest l
LEFT JOIN big8_latest b ON l.date = b.date
ORDER BY l.date DESC;

-- ============================================================================
-- INDICES FOR PERFORMANCE
-- ============================================================================

-- Create indices on frequently queried columns
-- (BigQuery uses clustering instead of traditional indices)

-- ============================================================================
-- VALIDATION QUERIES
-- ============================================================================

-- After creation, run these to verify:

-- 1. Check all tables created
SELECT table_name, table_type, creation_time
FROM `cbi-v14.market_data.INFORMATION_SCHEMA.TABLES`
ORDER BY table_name;

-- 2. Check partitioning
SELECT table_name, column_name, partition_by
FROM `cbi-v14.market_data.INFORMATION_SCHEMA.COLUMNS`
WHERE is_partitioning_column = 'YES';

-- 3. Check clustering
SELECT table_name, clustering_ordinal_position, column_name
FROM `cbi-v14.market_data.INFORMATION_SCHEMA.COLUMNS`
WHERE clustering_ordinal_position IS NOT NULL
ORDER BY table_name, clustering_ordinal_position;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================

