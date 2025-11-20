-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================================================
-- CBI-V14 COMPLETE CORRECTED BIGQUERY SCHEMA
-- Date: November 18, 2025
-- Purpose: COMPLETE schema aligned with Fresh Start + CME data + all gaps fixed
-- Validation: DataBento 29 symbols confirmed, palm NOT available
-- ============================================================================

-- ============================================================================
-- PART 1: DATASETS (8 total)
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS market_data
OPTIONS (location='us-central1', description='Market price data - DataBento futures, FX, competing oils');

CREATE SCHEMA IF NOT EXISTS raw_intelligence
OPTIONS (location='us-central1', description='Domain data with source prefixes');

CREATE SCHEMA IF NOT EXISTS regimes
OPTIONS (location='us-central1', description='Regime classifications per symbol and type');

CREATE SCHEMA IF NOT EXISTS drivers
OPTIONS (location='us-central1', description='Primary drivers and meta-drivers');

CREATE SCHEMA IF NOT EXISTS drivers_of_drivers
OPTIONS (location='us-central1', description='Second-order impact chains');

CREATE SCHEMA IF NOT EXISTS signals
OPTIONS (location='us-central1', description='Calculated signals, Big 8, technical indicators');

CREATE SCHEMA IF NOT EXISTS features
OPTIONS (location='us-central1', description='Canonical master_features mirror');

CREATE SCHEMA IF NOT EXISTS neural
OPTIONS (location='us-central1', description='Neural training features');

CREATE SCHEMA IF NOT EXISTS dim
OPTIONS (location='us-central1', description='Reference dimensions and metadata');

CREATE SCHEMA IF NOT EXISTS ops
OPTIONS (location='us-central1', description='Operations, quality, monitoring');

-- ============================================================================
-- PART 2: MARKET DATA - DATABENTO FUTURES (29 symbols)
-- ============================================================================

-- Table 1: DataBento 1-minute OHLCV
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
  open_interest INT64,
  publisher_id INT64,
  priority_tier INT64,              -- 1=5min (ZL,MES), 2=1hr (others)
  source_published_at TIMESTAMP,    -- PIT: when DataBento published
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(ts_event)
CLUSTER BY root, priority_tier
OPTIONS (
  partition_expiration_days=365,
  description='DataBento GLBX.MDP3 - 29 futures, 1-minute OHLCV'
);

-- Table 2: DataBento Daily OHLCV (aggregated or native)
CREATE OR REPLACE TABLE market_data.databento_futures_ohlcv_1d (
  date DATE NOT NULL,
  root STRING NOT NULL,
  symbol STRING NOT NULL,
  open FLOAT64,
  high FLOAT64,
  low FLOAT64,
  close FLOAT64,
  volume INT64,
  open_interest INT64,
  source_published_at TIMESTAMP,    -- PIT correctness
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY root, symbol
OPTIONS (
  description='DataBento daily OHLCV - aggregated from 1m or native 1d schema'
);

-- Table 3: Continuous Futures (back-adjusted, stitched)
CREATE OR REPLACE TABLE market_data.databento_futures_continuous_1d (
  date DATE NOT NULL,
  root STRING NOT NULL,
  cont_id STRING NOT NULL,          -- e.g., 'ZL_CONT_BACKADJ'
  close FLOAT64,
  open FLOAT64,
  high FLOAT64,
  low FLOAT64,
  volume INT64,
  open_interest INT64,
  back_adj FLOAT64,                 -- Cumulative back-adjustment
  roll_flag BOOL,                   -- TRUE on roll dates
  method STRING,                    -- 'volume', 'oi', 'hybrid'
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY root, cont_id
OPTIONS (
  description='Continuous futures series with back-adjustment and roll tracking'
);

-- Table 4: Roll Calendar (essential for stable training)
CREATE OR REPLACE TABLE market_data.roll_calendar (
  root STRING NOT NULL,
  contract STRING NOT NULL,
  first_notice_date DATE,
  last_trade_date DATE,
  volume_roll_date DATE,
  oi_roll_date DATE,
  roll_date DATE NOT NULL,          -- Actual roll used
  method STRING NOT NULL,           -- 'volume', 'oi', 'first_notice', 'hybrid'
  back_adjustment FLOAT64,          -- Cumulative back-adj applied
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY roll_date
CLUSTER BY root, method
OPTIONS (
  description='Futures roll calendar - volume/OI-based roll dates with back-adjustments'
);

-- ============================================================================
-- PART 3: CME GROUP DATA (Indices & Analytics)
-- ============================================================================

-- Table 5: CME Soybean Oilshare Index
CREATE OR REPLACE TABLE market_data.cme_soybean_oilshare_index (
  date DATE NOT NULL,
  contract_month STRING,            -- Dec 2025, Jan 2026, etc.
  oilshare_index FLOAT64,           -- Ratio of soy oil to soy meal price
  zl_price FLOAT64,                 -- Underlying ZL price
  zm_price FLOAT64,                 -- Underlying ZM price
  calculation_method STRING,
  source_published_at TIMESTAMP,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
OPTIONS (
  description='CME Soybean Oilshare Index - oil/meal price ratio (demand balance indicator)'
);

-- Table 6: CME Group Volatility Index (CVOL)
CREATE OR REPLACE TABLE market_data.cme_volatility_index (
  date DATE NOT NULL,
  commodity STRING NOT NULL,        -- SOYBEANS, CORN, WHEAT, etc.
  cvol_30d FLOAT64,                 -- 30-day implied volatility
  cvol_60d FLOAT64,                 -- 60-day (if available)
  cvol_90d FLOAT64,                 -- 90-day (if available)
  cvol_zscore FLOAT64,              -- Z-score vs historical
  regime STRING,                    -- high, low, crisis
  source_published_at TIMESTAMP,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY commodity
OPTIONS (
  description='CME Group Volatility Index (CVOL) - implied volatility for ag commodities'
);

-- ============================================================================
-- PART 4: COMPETING OILS & SUBSTITUTION (NOT on DataBento)
-- ============================================================================

-- Table 7: Vegetable Oils Daily (Palm, Rapeseed, Sunflower, Canola)
CREATE OR REPLACE TABLE market_data.vegoils_daily (
  date DATE NOT NULL,
  instrument STRING NOT NULL,       -- palm_fcpo, rapeseed_euronext, canola_ice, sunflower_wb
  source STRING NOT NULL,           -- barchart, ice, euronext, worldbank
  price_usd_per_mt FLOAT64,        -- Normalized: USD per metric ton
  px_native FLOAT64,                -- Original quote
  native_ccy STRING,                -- MYR, EUR, USD
  conversion_rate FLOAT64,          -- FX rate used for USD conversion
  vol_20d FLOAT64,
  source_published_at TIMESTAMP,    -- PIT: when source published
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY instrument, source
OPTIONS (
  description='Competing vegetable oils - palm (Barchart/ICE), rapeseed, canola, sunflower'
);

-- ============================================================================
-- PART 5: FX (Spot + Futures, Prefixed)
-- ============================================================================

-- Table 8: FX Daily (Spot + Futures)
CREATE OR REPLACE TABLE market_data.fx_daily (
  date DATE NOT NULL,
  pair STRING NOT NULL,             -- USD/BRL, USD/CNY, USD/ARS, USD/MYR, EUR/USD
  source STRING NOT NULL,           -- fred, yahoo, alpha, databento_fut
  px_close FLOAT64,
  px_open FLOAT64,
  px_high FLOAT64,
  px_low FLOAT64,
  source_published_at TIMESTAMP,    -- PIT
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY pair, source
OPTIONS (
  description='FX rates - spot (FRED/Yahoo) + futures (DataBento 6E/6B/6J/etc.)'
);

-- ============================================================================
-- PART 6: RAW INTELLIGENCE (Domain Data with Source Prefixes)
-- ============================================================================

-- Table 9: FRED Economic (EXISTING - DO NOT MODIFY SCHEMA)
-- Assume exists, keep as-is

-- Table 10: EIA Biofuels Granular (RINs, Biodiesel by PADD, Ethanol, SAF)
CREATE OR REPLACE TABLE raw_intelligence.eia_biofuels (
  date DATE NOT NULL,
  eia_biodiesel_prod_us FLOAT64,
  eia_biodiesel_prod_padd1 FLOAT64,
  eia_biodiesel_prod_padd2 FLOAT64,
  eia_biodiesel_prod_padd3 FLOAT64,
  eia_biodiesel_prod_padd4 FLOAT64,
  eia_biodiesel_prod_padd5 FLOAT64,
  eia_ethanol_prod_us FLOAT64,
  eia_renewable_diesel_prod_us FLOAT64,
  eia_saf_prod_us FLOAT64,          -- Sustainable Aviation Fuel
  eia_rin_price_d4 FLOAT64,
  eia_rin_price_d5 FLOAT64,
  eia_rin_price_d6 FLOAT64,
  source_published_at TIMESTAMP,    -- PIT: EIA release timestamp
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
OPTIONS (
  description='EIA biofuels granular - PADD-level biodiesel, RIN prices D4/D5/D6, renewable diesel, SAF'
);

-- Table 11: USDA Granular (WASDE, Exports by Destination, Yields by State)
CREATE OR REPLACE TABLE raw_intelligence.usda_granular (
  date DATE NOT NULL,
  -- WASDE World Soyoil
  usda_wasde_world_soyoil_prod FLOAT64,
  usda_wasde_world_soyoil_use FLOAT64,
  usda_wasde_world_soyoil_stocks FLOAT64,
  usda_wasde_us_soyoil_prod FLOAT64,
  usda_wasde_us_soyoil_use FLOAT64,
  usda_wasde_brazil_soybean_prod FLOAT64,
  usda_wasde_argentina_soybean_prod FLOAT64,
  -- Export Sales by Destination
  usda_exports_soybeans_net_sales_china FLOAT64,
  usda_exports_soybeans_net_sales_eu FLOAT64,
  usda_exports_soybeans_net_sales_total FLOAT64,
  usda_exports_soyoil_shipments_world FLOAT64,
  -- Crop Progress by State
  usda_cropprog_us_soy_harvest_complete_pct FLOAT64,
  usda_cropprog_il_soy_condition_good_excellent_pct FLOAT64,
  usda_cropprog_ia_soy_condition_good_excellent_pct FLOAT64,
  usda_cropprog_in_soy_condition_good_excellent_pct FLOAT64,
  -- Grain Stocks
  usda_stocks_soybeans_total FLOAT64,
  usda_stocks_soyoil_total FLOAT64,
  source_published_at TIMESTAMP,    -- PIT: USDA release timestamp
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
OPTIONS (
  description='USDA granular wide - WASDE by region, exports by destination, state yields'
);

-- Table 12: Weather Segmented (Raw by Area Code)
CREATE OR REPLACE TABLE raw_intelligence.weather_segmented (
  date DATE NOT NULL,
  country STRING NOT NULL,
  area_code STRING NOT NULL,
  station_id STRING,
  latitude FLOAT64,
  longitude FLOAT64,
  temp_max_f FLOAT64,
  temp_min_f FLOAT64,
  temp_avg_f FLOAT64,
  precip_inches FLOAT64,
  gdd_base50 FLOAT64,
  gdd_base60 FLOAT64,
  -- NOTE: soil_moisture removed (not reliable from station feeds)
  source_published_at TIMESTAMP,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY country, area_code
OPTIONS (
  description='Weather raw data by area code - US/BR/AR segmented'
);

-- Table 13: Weather Production-Weighted (Aggregated)
CREATE OR REPLACE TABLE raw_intelligence.weather_weighted (
  date DATE NOT NULL,
  weather_us_midwest_tavg_wgt FLOAT64,
  weather_us_midwest_prcp_wgt FLOAT64,
  weather_us_midwest_gdd_wgt FLOAT64,
  weather_br_soy_belt_tavg_wgt FLOAT64,
  weather_br_soy_belt_prcp_wgt FLOAT64,
  weather_br_soy_belt_gdd_wgt FLOAT64,
  weather_ar_soy_belt_tavg_wgt FLOAT64,
  weather_ar_soy_belt_prcp_wgt FLOAT64,
  weather_ar_soy_belt_gdd_wgt FLOAT64,
  source_published_at TIMESTAMP,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
OPTIONS (
  description='Production-weighted weather aggregates from weather_segmented + dim.production_weights'
);

-- Table 14: CFTC Positioning
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
  source_published_at TIMESTAMP,    -- PIT: CFTC release time
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY report_date
CLUSTER BY commodity
OPTIONS (
  description='CFTC Commitments of Traders - positioning data'
);

-- Table 15: News Bucketed (Topic, Regime, Correlation)
CREATE OR REPLACE TABLE raw_intelligence.news_bucketed (
  id STRING NOT NULL,
  published_at TIMESTAMP NOT NULL,
  headline STRING,
  content STRING,
  source STRING,
  bucket STRING,                    -- policy_*, trade_*, biofuel_*, logistics_*, macro_*
  topic_bucket STRING,              -- Detailed topic
  regime STRING,
  correlation_group STRING,
  sentiment_score FLOAT64,
  sentiment_confidence FLOAT64,
  impact_symbols ARRAY<STRING>,
  priority STRING,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(published_at)
CLUSTER BY bucket, topic_bucket
OPTIONS (
  description='News bucketed by topic, regime, correlation - NOT raw policy events'
);

-- Table 16: Policy Events (Structured Trump/Policy Intelligence)
CREATE OR REPLACE TABLE raw_intelligence.policy_events (
  id STRING NOT NULL,
  published_at TIMESTAMP NOT NULL,
  source STRING NOT NULL,           -- truth_social, white_house, ustr, epa, reuters
  bucket STRING NOT NULL,           -- policy_*, trade_*, biofuel_*, logistics_*, macro_*
  policy_trump_score FLOAT64,       -- 0..1 (probability/importance)
  policy_trump_score_signed FLOAT64, -- -1..1 (directional)
  sentiment_score FLOAT64,
  impact_symbols ARRAY<STRING>,
  expected_zl_move FLOAT64,         -- From zl_impact_predictor.py
  text STRING,
  source_published_at TIMESTAMP,    -- PIT
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(published_at)
CLUSTER BY bucket, source
OPTIONS (
  description='Structured policy events with Trump scores from trump_action_predictor.py'
);

-- Table 17: Alpha Vantage Insider Transactions
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
  related_commodity STRING,         -- soybean_oil, biofuel, ag_processing
  impact_signal STRING,             -- bullish, bearish, neutral
  source_published_at TIMESTAMP,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY symbol, related_commodity
OPTIONS (
  description='Alpha Vantage insider transactions - biofuel/ag companies (ADM, BG, REX, GEVO, etc.)'
);

-- Table 18: Alpha Vantage Analytics (Fixed + Sliding Windows)
CREATE OR REPLACE TABLE raw_intelligence.alpha_analytics (
  date DATE NOT NULL,
  symbol STRING NOT NULL,
  window_type STRING NOT NULL,      -- fixed, sliding
  window_size STRING NOT NULL,      -- 30d, 60d, 90d
  metric_name STRING NOT NULL,      -- volatility, correlation, sharpe, drawdown
  metric_value FLOAT64,
  reference_symbol STRING,          -- For correlations
  metadata JSON,
  source_published_at TIMESTAMP,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY symbol, metric_name
OPTIONS (
  description='Alpha Vantage pre-calculated analytics - fixed + sliding windows'
);

-- Table 19: Volatility Daily (VIX + Realized)
CREATE OR REPLACE TABLE raw_intelligence.volatility_daily (
  date DATE NOT NULL,
  vol_vix_level FLOAT64,
  vol_vix_zscore_30d FLOAT64,
  vol_zl_realized_20d FLOAT64,
  vol_es_realized_5d FLOAT64,
  vol_palm_realized_20d FLOAT64,
  vol_cl_realized_20d FLOAT64,
  vol_regime STRING,                -- high, low, crisis
  source_published_at TIMESTAMP,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
OPTIONS (
  description='Volatility layer - VIX + realized vols for ZL, ES, palm, crude'
);

-- ============================================================================
-- PART 7: REGIMES (Per Symbol + Global)
-- ============================================================================

-- Table 20: Market Regimes (Per Symbol + Global)
CREATE OR REPLACE TABLE regimes.market_regimes (
  date DATE NOT NULL,
  symbol STRING NOT NULL,           -- 'ZL', 'ES', 'ALL'
  regime_type STRING NOT NULL,      -- market, volatility, positioning, weather, policy
  regime_value STRING NOT NULL,     -- bull, bear, crisis, normal, high, low, etc.
  confidence FLOAT64,
  metadata JSON,
  valid_from DATE,
  valid_to DATE,
  calculation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY symbol, regime_type, regime_value
OPTIONS (
  description='Regime classifications per symbol and type - supports symbol=ALL for global regimes'
);

-- ============================================================================
-- PART 8: DRIVERS & META-DRIVERS
-- ============================================================================

-- Table 21: Primary Drivers
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
  source_published_at TIMESTAMP,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY driver_type, target_symbol
OPTIONS (
  description='Primary drivers with correlations and impact analysis'
);

-- Table 22: Meta-Drivers (Drivers of Drivers)
CREATE OR REPLACE TABLE drivers_of_drivers.meta_drivers (
  date DATE NOT NULL,
  primary_driver STRING NOT NULL,
  meta_driver_type STRING NOT NULL,
  meta_driver_name STRING NOT NULL,
  value FLOAT64,
  impact_chain STRING,              -- e.g., trump_tariff → USD/CNY → china_demand → ZL
  lag_days INT64,
  source_published_at TIMESTAMP,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY primary_driver, meta_driver_type
OPTIONS (
  description='Meta-drivers and second-order impact chains'
);

-- ============================================================================
-- PART 9: SIGNALS & BIG 8
-- ============================================================================

-- Table 23: Calculated Signals (Technical Indicators)
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
  description='Technical indicators from OHLCV - SMA, RSI, MACD, etc.'
);

-- Table 24: Big Eight Live (15-minute refresh)
CREATE OR REPLACE TABLE signals.big_eight_live (
  signal_timestamp TIMESTAMP NOT NULL,
  symbol STRING DEFAULT 'ZL',
  
  -- Big 8 Pillars (renamed from Big 7 per Fresh Start)
  big8_substitution_pressure FLOAT64,       -- Palm spread, competing oils
  big8_policy_shock FLOAT64,                -- Trump/policy signals
  big8_weather_supply_risk FLOAT64,         -- US/BR/AR weighted weather
  big8_china_demand FLOAT64,                -- China import flows, policy
  big8_vix_stress FLOAT64,                  -- VIX + realized vol regime
  big8_positioning_pressure FLOAT64,        -- CFTC managed money
  big8_biofuel_shock FLOAT64,               -- RINs, SAF mandates, production
  big8_fx_pressure FLOAT64,                 -- USD/BRL, USD/CNY, USD/ARS
  
  -- Composite
  big8_composite_score FLOAT64,
  big8_signal_direction STRING,
  big8_signal_strength FLOAT64,
  
  -- Context
  regime STRING,
  procurement_alert STRING,
  narrative STRING,
  
  as_of TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(signal_timestamp)
OPTIONS (
  partition_expiration_days=90,
  description='Big 8 signals - refreshed every 15 minutes for dashboard (replaces Big 7)'
);

-- ============================================================================
-- PART 10: CANONICAL FEATURES (Master Table)
-- ============================================================================

-- Table 25: Master Features 2000-2025 (Mirrors Parquet)
CREATE OR REPLACE TABLE features.master_features (
  date DATE NOT NULL,
  symbol STRING NOT NULL DEFAULT 'ZL',
  
  -- DataBento OHLCV (2010-present, prefixed)
  databento_zl_open FLOAT64,
  databento_zl_high FLOAT64,
  databento_zl_low FLOAT64,
  databento_zl_close FLOAT64,
  databento_zl_volume INT64,
  databento_zl_oi INT64,
  
  -- Yahoo OHLCV (2000-2010 historical bridge)
  yahoo_zl_open FLOAT64,
  yahoo_zl_high FLOAT64,
  yahoo_zl_low FLOAT64,
  yahoo_zl_close FLOAT64,
  yahoo_zl_volume INT64,
  
  -- Stitched (best available: Yahoo 2000-2010, DataBento 2010+)
  zl_open FLOAT64,
  zl_high FLOAT64,
  zl_low FLOAT64,
  zl_close FLOAT64,
  zl_volume INT64,
  
  -- CME Indices
  cme_soybean_oilshare_index FLOAT64,
  cme_soybean_cvol_30d FLOAT64,
  
  -- Palm Oil (Barchart/ICE - primary substitution driver)
  barchart_palm_close FLOAT64,
  barchart_palm_vol_20d FLOAT64,
  
  -- Competing Oils (World Bank)
  worldbank_rapeseed_price FLOAT64,
  worldbank_sunflower_price FLOAT64,
  worldbank_canola_price FLOAT64,
  
  -- FX (FRED for spot, DataBento for futures)
  fred_usd_brl FLOAT64,
  fred_usd_cny FLOAT64,
  fred_usd_ars FLOAT64,
  yahoo_usd_myr FLOAT64,
  databento_6e_close FLOAT64,       -- EUR/USD futures
  
  -- FRED Macro (~60 columns - abbreviated here)
  fred_dff FLOAT64,
  fred_dgs10 FLOAT64,
  fred_vixcls FLOAT64,
  fred_dtwexbgs FLOAT64,
  fred_cpiaucsl FLOAT64,
  -- ... (all 60 FRED series with fred_ prefix)
  
  -- EIA Biofuels (granular)
  eia_biodiesel_prod_us FLOAT64,
  eia_biodiesel_prod_padd2 FLOAT64,
  eia_rin_price_d4 FLOAT64,
  eia_rin_price_d6 FLOAT64,
  eia_saf_prod_us FLOAT64,
  
  -- USDA Granular
  usda_wasde_world_soyoil_prod FLOAT64,
  usda_wasde_world_soyoil_use FLOAT64,
  usda_exports_soybeans_net_sales_china FLOAT64,
  usda_exports_soybeans_net_sales_eu FLOAT64,
  usda_cropprog_il_soy_condition_good_excellent_pct FLOAT64,
  
  -- Weather (production-weighted)
  weather_us_midwest_tavg_wgt FLOAT64,
  weather_us_midwest_prcp_wgt FLOAT64,
  weather_br_soy_belt_tavg_wgt FLOAT64,
  weather_ar_soy_belt_tavg_wgt FLOAT64,
  
  -- CFTC
  cftc_zl_net_managed_money INT64,
  cftc_zl_net_commercial INT64,
  
  -- Volatility
  vol_vix_level FLOAT64,
  vol_vix_zscore_30d FLOAT64,
  vol_zl_realized_20d FLOAT64,
  vol_palm_realized_20d FLOAT64,
  vol_regime STRING,
  
  -- Policy/Trump (from trump_action_predictor.py)
  policy_trump_action_prob FLOAT64,
  policy_trump_expected_zl_move FLOAT64,
  policy_trump_procurement_alert STRING,
  policy_trump_score_signed FLOAT64,
  
  -- News Sentiment
  news_sentiment_zl_score FLOAT64,
  news_sentiment_zl_confidence FLOAT64,
  
  -- Calculated Signals
  signal_zl_sma_50 FLOAT64,
  signal_zl_rsi_14 FLOAT64,
  signal_zl_macd FLOAT64,
  signal_zl_atr_14 FLOAT64,
  
  -- Regime
  regime STRING,
  
  -- Targets (for training)
  target_1w FLOAT64,
  target_1m FLOAT64,
  target_3m FLOAT64,
  target_6m FLOAT64,
  target_12m FLOAT64,
  
  -- PIT tracking
  as_of TIMESTAMP NOT NULL,         -- Point-in-time as-of date
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY symbol
OPTIONS (
  description='Canonical master features 2000-2025 - mirrors master_features_2000_2025.parquet'
);

-- ============================================================================
-- PART 11: NEURAL TRAINING
-- ============================================================================

-- Table 26: Neural Feature Vectors
CREATE OR REPLACE TABLE neural.feature_vectors (
  date DATE NOT NULL,
  symbol STRING NOT NULL,
  horizon STRING NOT NULL,
  features JSON NOT NULL,
  regime_id STRING,
  target_value FLOAT64,
  as_of TIMESTAMP NOT NULL,         -- PIT
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY symbol, horizon
OPTIONS (
  description='Neural network training features'
);

-- ============================================================================
-- PART 12: DIMENSIONS & REFERENCE DATA
-- ============================================================================

-- Table 27: Instrument Metadata
CREATE OR REPLACE TABLE dim.instrument_metadata (
  root STRING NOT NULL,
  name STRING,
  tick_size FLOAT64,
  point_value FLOAT64,
  currency STRING,
  exchange STRING,                  -- CME, CBOT, NYMEX, COMEX
  session_tz STRING,
  session_hours STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- Table 28: Production Weights (for weather aggregation)
CREATE OR REPLACE TABLE dim.production_weights (
  region_id STRING NOT NULL,        -- us_midwest, br_soy_belt, ar_soy_belt
  area_code STRING NOT NULL,        -- Specific state/province
  commodity STRING NOT NULL,        -- soybeans, corn
  weight FLOAT64 NOT NULL,          -- Production weight (0-1, sums to 1 per region)
  source STRING,                    -- usda_nass, ibge, etc.
  valid_from DATE,
  valid_to DATE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY region_id, commodity;

-- ============================================================================
-- PART 13: OPERATIONS & QUALITY
-- ============================================================================

-- Table 29: Data Quality Events
CREATE OR REPLACE TABLE ops.data_quality_events (
  ts TIMESTAMP NOT NULL,
  source STRING NOT NULL,
  dataset STRING NOT NULL,
  table_name STRING,
  severity STRING NOT NULL,         -- INFO, WARN, ERROR
  check_type STRING,                -- schema, continuity, join_density, spike, null_rate
  message STRING NOT NULL,
  payload JSON,
  resolved BOOL DEFAULT FALSE,
  resolved_at TIMESTAMP
)
PARTITION BY DATE(ts)
CLUSTER BY source, severity
OPTIONS (
  description='Data quality monitoring and validation events'
);

-- ============================================================================
-- PART 14: VIEWS (Query Layer)
-- ============================================================================

-- View 1: ZL Comprehensive (All data joined)
CREATE OR REPLACE VIEW signals.vw_zl_comprehensive AS
WITH latest AS (
  SELECT 
    date,
    zl_close,
    barchart_palm_close,
    policy_trump_expected_zl_move,
    regime,
    vol_vix_level,
    cftc_zl_net_managed_money,
    weather_us_midwest_tavg_wgt,
    weather_br_soy_belt_tavg_wgt,
    eia_rin_price_d4,
    usda_exports_soybeans_net_sales_china
  FROM features.master_features
  WHERE symbol = 'ZL'
    AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
),
big8_latest AS (
  SELECT 
    DATE(signal_timestamp) as date,
    big8_composite_score,
    big8_signal_direction,
    big8_signal_strength,
    big8_substitution_pressure,
    big8_policy_shock,
    big8_biofuel_shock
  FROM signals.big_eight_live
  WHERE signal_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
  QUALIFY ROW_NUMBER() OVER (PARTITION BY DATE(signal_timestamp) ORDER BY signal_timestamp DESC) = 1
)
SELECT 
  l.*,
  b.big8_composite_score,
  b.big8_signal_direction,
  b.big8_signal_strength,
  b.big8_substitution_pressure,
  b.big8_policy_shock,
  b.big8_biofuel_shock
FROM latest l
LEFT JOIN big8_latest b ON l.date = b.date
ORDER BY l.date DESC;

-- View 2: Latest Big 8 (for dashboard)
CREATE OR REPLACE VIEW signals.vw_big_eight_latest AS
SELECT *
FROM signals.big_eight_live
WHERE signal_timestamp = (SELECT MAX(signal_timestamp) FROM signals.big_eight_live);

-- ============================================================================
-- PART 15: HISTORICAL BRIDGE (2000-2010)
-- ============================================================================

-- Table 30: Historical Yahoo ZL (2000-2010)
CREATE OR REPLACE TABLE market_data.yahoo_zl_historical_2000_2010 (
  date DATE NOT NULL,
  yahoo_zl_open FLOAT64,
  yahoo_zl_high FLOAT64,
  yahoo_zl_low FLOAT64,
  yahoo_zl_close FLOAT64,
  yahoo_zl_volume INT64,
  yahoo_zl_adj_close FLOAT64,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
OPTIONS (
  description='Yahoo Finance ZL historical 2000-2010 - bridges DataBento gap before 2010-06-06'
);

-- ============================================================================
-- VALIDATION QUERIES
-- ============================================================================

-- 1. Check all tables created
SELECT table_catalog, table_schema, table_name, table_type, creation_time
FROM `region-us-central1`.INFORMATION_SCHEMA.TABLES
WHERE table_catalog = 'cbi-v14'
  AND table_schema IN ('market_data', 'raw_intelligence', 'regimes', 'drivers', 
                       'drivers_of_drivers', 'signals', 'features', 'neural', 'dim', 'ops')
ORDER BY table_schema, table_name;

-- 2. Check partitioning
SELECT table_schema, table_name, is_partitioning_column, column_name
FROM `region-us-central1`.INFORMATION_SCHEMA.COLUMNS
WHERE table_catalog = 'cbi-v14'
  AND is_partitioning_column = 'YES'
ORDER BY table_schema, table_name;

-- 3. Check clustering
SELECT table_schema, table_name, clustering_ordinal_position, column_name
FROM `region-us-central1`.INFORMATION_SCHEMA.COLUMNS
WHERE table_catalog = 'cbi-v14'
  AND clustering_ordinal_position IS NOT NULL
ORDER BY table_schema, table_name, clustering_ordinal_position;

-- ============================================================================
-- END OF SCHEMA - 30 TABLES TOTAL
-- ============================================================================

