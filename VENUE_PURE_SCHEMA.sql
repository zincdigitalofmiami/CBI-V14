-- ============================================================================
-- CBI-V14 VENUE-PURE BIGQUERY SCHEMA
-- Date: November 18, 2025
-- Constraint: CME/CBOT/NYMEX/COMEX ONLY + Free FRED/Yahoo + ScrapeCreator
-- Purpose: Complete ZL forecasting with NO external palm/ICE/BMD dependencies
-- Strategy: Use CME-native crush/oilshare/CVOL for substitution economics
-- ============================================================================

-- ============================================================================
-- DATASETS
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS market_data
OPTIONS (location='us-central1', description='CME/CBOT/NYMEX/COMEX market data only');

CREATE SCHEMA IF NOT EXISTS raw_intelligence  
OPTIONS (location='us-central1', description='Free APIs only - FRED, USDA, EIA, CFTC, NOAA');

CREATE SCHEMA IF NOT EXISTS signals
OPTIONS (location='us-central1', description='Derived signals - crush, spreads, microstructure, Big 8');

CREATE SCHEMA IF NOT EXISTS features
OPTIONS (location='us-central1', description='Canonical master_features table');

CREATE SCHEMA IF NOT EXISTS regimes
OPTIONS (location='us-central1', description='Regime classifications per symbol');

CREATE SCHEMA IF NOT EXISTS drivers
OPTIONS (location='us-central1', description='Drivers and meta-drivers');

CREATE SCHEMA IF NOT EXISTS neural
OPTIONS (location='us-central1', description='Neural training features');

CREATE SCHEMA IF NOT EXISTS dim
OPTIONS (location='us-central1', description='Reference data and metadata');

CREATE SCHEMA IF NOT EXISTS ops
OPTIONS (location='us-central1', description='Quality monitoring');

-- ============================================================================
-- PART 1: DATABENTO FUTURES (CME/CBOT/NYMEX/COMEX)
-- ============================================================================

-- Table 1: Futures OHLCV 1-minute (DataBento GLBX.MDP3)
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
  is_spread BOOL,                   -- TRUE if calendar spread (symbol contains '-')
  spread_legs ARRAY<STRING>,        -- e.g., ['ZLZ25', 'ZLH26'] for Dec25-Mar26
  publisher_id INT64,
  priority_tier INT64,              -- 1=5min (ZL,MES), 2=1hr
  source_published_at TIMESTAMP,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(ts_event)
CLUSTER BY root, is_spread, priority_tier
OPTIONS (
  partition_expiration_days=365,
  description='DataBento GLBX.MDP3 - 29 futures + calendar spreads, 1-minute'
);

-- Table 2: Futures OHLCV Daily (Aggregated from 1m OR native 1d schema)
CREATE OR REPLACE TABLE market_data.databento_futures_ohlcv_1d (
  date DATE NOT NULL,
  root STRING NOT NULL,
  symbol STRING NOT NULL,
  open FLOAT64,
  high FLOAT64,
  low FLOAT64,
  close FLOAT64,
  settle FLOAT64,                   -- Official settlement price
  volume INT64,
  open_interest INT64,
  is_spread BOOL,
  spread_legs ARRAY<STRING>,
  source_published_at TIMESTAMP,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY root, symbol, is_spread
OPTIONS (
  description='Daily OHLCV + settlement for all futures and calendar spreads'
);

-- Table 3: Continuous Futures (Back-Adjusted, Roll-Proof)
CREATE OR REPLACE TABLE market_data.databento_futures_continuous_1d (
  date DATE NOT NULL,
  root STRING NOT NULL,
  cont_id STRING NOT NULL,          -- e.g., 'ZL_CONT_VOL_BACKADJ'
  close FLOAT64,
  open FLOAT64,
  high FLOAT64,
  low FLOAT64,
  volume INT64,
  open_interest INT64,
  back_adj FLOAT64,
  roll_flag BOOL,
  active_contract STRING,           -- Which contract is front
  method STRING,                    -- volume, oi, first_notice, hybrid
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY root, cont_id
OPTIONS (
  description='Continuous futures with roll calendar and back-adjustments'
);

-- Table 4: Roll Calendar
CREATE OR REPLACE TABLE market_data.roll_calendar (
  root STRING NOT NULL,
  contract STRING NOT NULL,
  first_notice_date DATE,
  last_trade_date DATE,
  volume_roll_date DATE,
  oi_roll_date DATE,
  roll_date DATE NOT NULL,
  method STRING NOT NULL,
  back_adjustment FLOAT64,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY roll_date
CLUSTER BY root, method
OPTIONS (
  description='Futures roll calendar with volume/OI-based roll dates'
);

-- Table 5: Forward Curves (EOD Settlement by Contract Month)
CREATE OR REPLACE TABLE market_data.futures_curve_1d (
  date DATE NOT NULL,
  root STRING NOT NULL,
  contract STRING NOT NULL,         -- ZLZ25, ZLH26, ZLK26, etc.
  month_code STRING,                -- Z25, H26, K26
  months_to_expiry INT64,
  settle FLOAT64,
  volume INT64,
  open_interest INT64,
  source_published_at TIMESTAMP,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY root, contract
OPTIONS (
  description='Forward curves - EOD settlement for all contract months (6-12 months out)'
);

-- ============================================================================
-- PART 2: CME INDICES (COSI, CVOL) - Via ScrapeCreator EOD
-- ============================================================================

-- Table 6: CME Indices EOD (Oilshare + CVOL)
CREATE OR REPLACE TABLE market_data.cme_indices_eod (
  date DATE NOT NULL,
  index_type STRING NOT NULL,       -- COSI, CVOL
  product STRING NOT NULL,          -- COSI1, COSI2, ..., COSI9 OR ZS, ZL, ZC for CVOL
  tenor STRING,                     -- front, 2nd, 3rd (for CVOL by month)
  value FLOAT64 NOT NULL,
  source_url STRING,                -- CME page scraped
  source_published_at TIMESTAMP,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY index_type, product
OPTIONS (
  description='CME Soybean Oilshare Index (COSI1-9) + CVOL via ScrapeCreator'
);

-- ============================================================================
-- PART 3: CRUSH & OILSHARE ECONOMICS (CME-Native)
-- ============================================================================

-- Table 7: Calendar Spreads Daily (M1-M2, M1-M3)
CREATE OR REPLACE TABLE signals.calendar_spreads_1d (
  date DATE NOT NULL,
  root STRING NOT NULL,             -- ZL, ZS, ZM, CL, RB, HO
  spread_tenor STRING NOT NULL,     -- M1-M2, M1-M3
  spread_close FLOAT64,
  spread_settle FLOAT64,
  m1_contract STRING,
  m2_contract STRING,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY root, spread_tenor
OPTIONS (
  description='Calendar spreads - carry and stock-use signals'
);

-- Table 8: Crush & Oilshare Daily (Board vs Model)
CREATE OR REPLACE TABLE signals.crush_oilshare_daily (
  date DATE NOT NULL,
  
  -- Board Crush (facilitated spread from CME)
  board_crush_usd_per_bu FLOAT64,
  
  -- Theoretical Crush (from ZS/ZM/ZL + yield constants)
  theoretical_crush_usd_per_bu FLOAT64,
  theoretical_crush_pct_margin FLOAT64,
  
  -- Oilshare (oil/(oil+meal) ratio)
  oilshare_model FLOAT64,           -- ZL/(ZL+ZM) computed
  oilshare_cme_cosi_front FLOAT64,  -- From cme_indices_eod where product='COSI1'
  oilshare_divergence_bps FLOAT64,  -- (model - COSI) * 10000
  
  -- Context
  zs_settle FLOAT64,                -- Soybean price
  zl_settle FLOAT64,                -- Soy oil price
  zm_settle FLOAT64,                -- Soy meal price
  
  source_published_at TIMESTAMP,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
OPTIONS (
  description='Soybean crush and oilshare metrics - board vs model with divergence tracking'
);

-- ============================================================================
-- PART 4: ENERGY & BIOFUEL PROXIES (NYMEX-Native)
-- ============================================================================

-- Table 9: Energy Proxies Daily (Crack, Spreads, Ethanol)
CREATE OR REPLACE TABLE signals.energy_proxies_daily (
  date DATE NOT NULL,
  
  -- 3-2-1 Crack Spread (2*RB + 1*HO - 3*CL)
  crack_3_2_1_usd_per_bbl FLOAT64,
  
  -- Heating Oil Timespread (diesel/renewable diesel tightness)
  ho_timespread_m1_m2 FLOAT64,
  ho_timespread_m1_m3 FLOAT64,
  
  -- RBOB Timespread
  rb_timespread_m1_m2 FLOAT64,
  
  -- Ethanol Futures (NYMEX CU - Denatured Fuel Ethanol)
  ethanol_cu_settle FLOAT64,
  ethanol_cu_volume INT64,
  ethanol_cu_oi INT64,
  
  -- Brent-WTI Spread
  brent_wti_spread FLOAT64,         -- BZ - CL
  
  source_published_at TIMESTAMP,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
OPTIONS (
  description='Energy and biofuel proxies - crack spreads, timespreads, ethanol futures (NYMEX)'
);

-- ============================================================================
-- PART 5: FX (CME Futures First, FRED/Yahoo Fallback)
-- ============================================================================

-- Table 10: FX Daily (CME Futures + FRED/Yahoo Spot)
CREATE OR REPLACE TABLE market_data.fx_daily (
  date DATE NOT NULL,
  pair STRING NOT NULL,             -- USD/BRL, USD/CNH, EUR/USD, etc.
  source STRING NOT NULL,           -- cme_fut, fred, yahoo
  px_close FLOAT64,
  px_settle FLOAT64,                -- For futures
  volume INT64,                     -- For futures
  oi INT64,                         -- For futures
  source_published_at TIMESTAMP,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY pair, source
OPTIONS (
  description='FX - CME futures (6L BRL, CNH) first, FRED/Yahoo spot fallback for missing pairs'
);

-- ============================================================================
-- PART 6: MICROSTRUCTURE (DataBento Trades/TBBO/MBP)
-- ============================================================================

-- Table 11: Order Flow 1-Minute (Microstructure Features)
CREATE OR REPLACE TABLE market_data.orderflow_1m (
  ts_minute TIMESTAMP NOT NULL,
  root STRING NOT NULL,             -- ZL, ZS, ZM
  
  -- Spread & Depth
  spread_bps FLOAT64,               -- Bid-ask spread in basis points
  depth_bid_size INT64,             -- Best bid size
  depth_ask_size INT64,             -- Best ask size
  depth_imbalance FLOAT64,          -- (bid - ask) / (bid + ask)
  
  -- Trade Flow
  trade_volume INT64,
  trade_imbalance FLOAT64,          -- Buyer-initiated vs seller-initiated
  aggressor_buy_pct FLOAT64,
  
  -- Price Discovery
  microprice FLOAT64,               -- (bid*ask_size + ask*bid_size) / (bid_size + ask_size)
  microprice_dev_bps FLOAT64,       -- microprice - mid
  
  -- Volatility
  volatility_rv_1m FLOAT64,         -- 1-minute realized volatility
  
  source_published_at TIMESTAMP,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(ts_minute)
CLUSTER BY root
OPTIONS (
  partition_expiration_days=90,
  description='Microstructure features from DataBento trades/TBBO/MBP-10 schemas'
);

-- ============================================================================
-- PART 7: RAW INTELLIGENCE (Free APIs Only)
-- ============================================================================

-- Table 12: FRED Economic (EXISTING - Don't Modify)
-- Keep as-is

-- Table 13: EIA Biofuels Granular
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
  eia_saf_prod_us FLOAT64,
  eia_rin_price_d4 FLOAT64,
  eia_rin_price_d5 FLOAT64,
  eia_rin_price_d6 FLOAT64,
  source_published_at TIMESTAMP,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
OPTIONS (description='EIA biofuels - free API, granular PADD-level');

-- Table 14: USDA Granular
CREATE OR REPLACE TABLE raw_intelligence.usda_granular (
  date DATE NOT NULL,
  usda_wasde_world_soyoil_prod FLOAT64,
  usda_wasde_world_soyoil_use FLOAT64,
  usda_wasde_us_soyoil_prod FLOAT64,
  usda_wasde_us_soyoil_use FLOAT64,
  usda_wasde_brazil_soybean_prod FLOAT64,
  usda_wasde_argentina_soybean_prod FLOAT64,
  usda_exports_soybeans_net_sales_china FLOAT64,
  usda_exports_soybeans_net_sales_eu FLOAT64,
  usda_exports_soybeans_net_sales_total FLOAT64,
  usda_exports_soyoil_net_sales_total FLOAT64,
  usda_cropprog_il_soy_condition_good_excellent_pct FLOAT64,
  usda_cropprog_ia_soy_condition_good_excellent_pct FLOAT64,
  usda_cropprog_in_soy_condition_good_excellent_pct FLOAT64,
  usda_stocks_soybeans_total FLOAT64,
  usda_stocks_soyoil_total FLOAT64,
  source_published_at TIMESTAMP,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
OPTIONS (description='USDA granular - free API, by destination and state');

-- Table 15: Weather Segmented
CREATE OR REPLACE TABLE raw_intelligence.weather_segmented (
  date DATE NOT NULL,
  country STRING NOT NULL,
  area_code STRING NOT NULL,
  station_id STRING,
  temp_max_f FLOAT64,
  temp_min_f FLOAT64,
  temp_avg_f FLOAT64,
  precip_inches FLOAT64,
  gdd_base50 FLOAT64,
  gdd_base60 FLOAT64,
  source_published_at TIMESTAMP,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY country, area_code
OPTIONS (description='Weather raw - NOAA/INMET/SMN free APIs');

-- Table 16: Weather Production-Weighted
CREATE OR REPLACE TABLE raw_intelligence.weather_weighted (
  date DATE NOT NULL,
  weather_us_midwest_tavg_wgt FLOAT64,
  weather_us_midwest_prcp_wgt FLOAT64,
  weather_us_midwest_gdd_wgt FLOAT64,
  weather_br_soy_belt_tavg_wgt FLOAT64,
  weather_br_soy_belt_prcp_wgt FLOAT64,
  weather_ar_soy_belt_tavg_wgt FLOAT64,
  weather_ar_soy_belt_prcp_wgt FLOAT64,
  source_published_at TIMESTAMP,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
OPTIONS (description='Production-weighted weather from segmented + dim.production_weights');

-- Table 17: CFTC Positioning
CREATE OR REPLACE TABLE raw_intelligence.cftc_positioning (
  report_date DATE NOT NULL,
  commodity STRING NOT NULL,
  managed_money_long INT64,
  managed_money_short INT64,
  commercial_long INT64,
  commercial_short INT64,
  open_interest INT64,
  net_managed_money INT64,
  net_commercial INT64,
  source_published_at TIMESTAMP,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY report_date
CLUSTER BY commodity
OPTIONS (description='CFTC COT - free API');

-- Table 18: Policy Events (ScrapeCreator ONLY - No NewsAPI/Alpha)
CREATE OR REPLACE TABLE raw_intelligence.policy_events (
  id STRING NOT NULL,
  published_at TIMESTAMP NOT NULL,
  source STRING NOT NULL,           -- truth_social, white_house, ustr, epa, cme_insights
  bucket STRING NOT NULL,           -- policy_*, trade_*, biofuel_*, energy_*
  policy_trump_score FLOAT64,
  policy_trump_score_signed FLOAT64,
  sentiment_score FLOAT64,
  impact_symbols ARRAY<STRING>,
  expected_zl_move FLOAT64,         -- From zl_impact_predictor.py
  text STRING,
  source_published_at TIMESTAMP,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(published_at)
CLUSTER BY bucket, source
OPTIONS (
  description='Policy events - ScrapeCreator only (Truth Social, gov sites, CME) + trump_action_predictor.py'
);

-- Table 19: Volatility Daily (CVOL + Realized)
CREATE OR REPLACE TABLE raw_intelligence.volatility_daily (
  date DATE NOT NULL,
  
  -- FRED VIX
  vol_vix_level FLOAT64,
  vol_vix_zscore_30d FLOAT64,
  
  -- CME CVOL (from cme_indices_eod)
  vol_cme_cvol_soybeans_30d FLOAT64,
  vol_cme_cvol_zl_30d FLOAT64,      -- If available
  vol_cme_cvol_corn_30d FLOAT64,
  
  -- Realized Vol (from 1m DataBento bars)
  vol_zl_realized_5d FLOAT64,
  vol_zl_realized_10d FLOAT64,
  vol_zl_realized_20d FLOAT64,
  vol_zs_realized_20d FLOAT64,
  vol_cl_realized_20d FLOAT64,
  vol_es_realized_5d FLOAT64,
  
  -- Regime
  vol_regime STRING,                -- high, low, crisis
  
  source_published_at TIMESTAMP,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
OPTIONS (
  description='Volatility layer - CME CVOL + realized from DataBento + FRED VIX'
);

-- Table 20: Alpha Vantage News Sentiment (SANDBOXED OVERLAY - Feature Flagged)
-- ⚠️ WARNING: Equity-centric, NOT commodity-futures native
-- ⚠️ USE ONLY as event-gated overlay with strict keyword/source/temporal gates
-- ⚠️ NEVER let this override CME curves/spreads/CVOL or USDA/EIA/CFTC
-- ⚠️ Feature flagged for A/B testing - must prove OOS value before production use
CREATE OR REPLACE TABLE raw_intelligence.alpha_news_sentiment (
  id STRING NOT NULL,
  time_published TIMESTAMP NOT NULL,
  source STRING,
  title STRING,
  url STRING,
  summary STRING,
  
  -- Overall Sentiment (equity-centric, use with caution)
  overall_sentiment_score FLOAT64,  -- -1 to 1
  overall_sentiment_label STRING,   -- Bearish, Somewhat-Bearish, Neutral, Somewhat-Bullish, Bullish
  
  -- Per-Ticker Sentiment (equity proxies: ADM, BG, DAR, REX, GEVO, etc.)
  tickers ARRAY<STRUCT<
    ticker STRING,                   -- ADM, BG, DAR (ag processors), REX, GEVO (biofuel)
    relevance_score FLOAT64,         -- 0 to 1 (how relevant ticker is to article)
    ticker_sentiment_score FLOAT64,  -- -1 to 1
    ticker_sentiment_label STRING
  >>,
  
  -- Topics (generic, not commodity-specific)
  topics ARRAY<STRING>,              -- economy_monetary, energy_transportation, etc.
  
  -- STRICT GATES (computed in processing layer)
  keyword_gate_passed BOOL,         -- Requires ag/biofuel lexicon (soybean, crush, oilshare, biodiesel, CVOL, WASDE, export)
  source_gate_passed BOOL,          -- Whitelist: USDA, EIA, CFTC, CME, major wires only
  event_gate_passed BOOL,           -- Within ±60m of USDA/EIA release OR CME curve regime change
  temporal_relevance FLOAT64,       -- Decay score (fresher = higher)
  
  -- A/B Testing Control
  enabled_for_training BOOL DEFAULT FALSE,  -- Feature flag: default OFF until OOS validation passes
  ab_test_group STRING,             -- control, test_low_weight, test_full
  oos_performance_delta FLOAT64,    -- Track if adding this improves MAPE
  
  -- Low Prior Weight (if enabled)
  feature_weight FLOAT64 DEFAULT 0.05,  -- Start at 5% of other features, increase only if OOS proves value
  
  source_published_at TIMESTAMP,    -- PIT: when Alpha Vantage published
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(time_published)
CLUSTER BY overall_sentiment_label, keyword_gate_passed
OPTIONS (
  description='Alpha Vantage news sentiment - SANDBOXED, event-gated, feature-flagged overlay (NOT core driver)'
);

-- ============================================================================
-- PART 8: REGIMES (Per Symbol + Global)
-- ============================================================================

-- Table 20: Market Regimes (Per Symbol)
CREATE OR REPLACE TABLE regimes.market_regimes (
  date DATE NOT NULL,
  symbol STRING NOT NULL,           -- ZL, ES, ALL
  regime_type STRING NOT NULL,      -- market, volatility, positioning, energy, weather, policy, carry
  regime_value STRING NOT NULL,     -- bull, bear, crisis, tight_carry, loose_carry, etc.
  confidence FLOAT64,
  metadata JSON,
  valid_from DATE,
  valid_to DATE,
  calculation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY symbol, regime_type, regime_value
OPTIONS (
  description='Regime classifications per symbol and type - supports symbol=ALL for global'
);

-- ============================================================================
-- PART 9: DRIVERS
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
OPTIONS (description='Primary drivers with correlation analysis');

-- Table 22: Meta-Drivers (Drivers of Drivers)
CREATE OR REPLACE TABLE drivers.meta_drivers (
  date DATE NOT NULL,
  primary_driver STRING NOT NULL,
  meta_driver_type STRING NOT NULL,
  meta_driver_name STRING NOT NULL,
  value FLOAT64,
  impact_chain STRING,
  lag_days INT64,
  source_published_at TIMESTAMP,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY primary_driver, meta_driver_type
OPTIONS (description='Meta-drivers and impact chains');

-- ============================================================================
-- PART 10: SIGNALS
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
OPTIONS (description='Technical indicators from OHLCV');

-- Table 24: Big Eight Live (15-Minute Refresh)
CREATE OR REPLACE TABLE signals.big_eight_live (
  signal_timestamp TIMESTAMP NOT NULL,
  symbol STRING DEFAULT 'ZL',
  
  -- Big 8 Pillars (CME-Native Substitution)
  big8_crush_oilshare_pressure FLOAT64,    -- From crush_oilshare_daily (NOT external palm)
  big8_policy_shock FLOAT64,               -- From policy_events (trump_action_predictor.py)
  big8_weather_supply_risk FLOAT64,        -- From weather_weighted
  big8_china_demand FLOAT64,               -- From usda_granular exports to China
  big8_vix_cvol_stress FLOAT64,            -- From volatility_daily (VIX + CVOL)
  big8_positioning_pressure FLOAT64,       -- From cftc_positioning
  big8_energy_biofuel_shock FLOAT64,       -- From energy_proxies (crack, ethanol, spreads)
  big8_fx_pressure FLOAT64,                -- From fx_daily (6L, CNH, FRED fallback)
  
  -- Composite
  big8_composite_score FLOAT64,
  big8_signal_direction STRING,
  big8_signal_strength FLOAT64,
  
  -- Context
  regime STRING,
  procurement_alert STRING,
  narrative STRING,
  
  as_of TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(signal_timestamp)
OPTIONS (
  partition_expiration_days=90,
  description='Big 8 - CME-native crush/oilshare substitution, not external palm'
);

-- ============================================================================
-- PART 11: CANONICAL FEATURES (Master Table)
-- ============================================================================

-- Table 25: Master Features (Mirrors Parquet)
CREATE OR REPLACE TABLE features.master_features (
  date DATE NOT NULL,
  symbol STRING NOT NULL DEFAULT 'ZL',
  
  -- DataBento OHLCV (2010-present)
  databento_zl_open FLOAT64,
  databento_zl_high FLOAT64,
  databento_zl_low FLOAT64,
  databento_zl_close FLOAT64,
  databento_zl_volume INT64,
  databento_zl_oi INT64,
  
  -- Yahoo Historical (2000-2010 bridge)
  yahoo_zl_open FLOAT64,
  yahoo_zl_high FLOAT64,
  yahoo_zl_low FLOAT64,
  yahoo_zl_close FLOAT64,
  yahoo_zl_volume INT64,
  
  -- Stitched (best available)
  zl_open FLOAT64,
  zl_high FLOAT64,
  zl_low FLOAT64,
  zl_close FLOAT64,
  zl_volume INT64,
  
  -- CME Indices
  cme_soybean_oilshare_cosi1 FLOAT64,
  cme_soybean_cvol_30d FLOAT64,
  
  -- Crush & Oilshare (CME-native substitution)
  crush_theoretical_usd_per_bu FLOAT64,
  oilshare_model FLOAT64,
  oilshare_divergence_bps FLOAT64,  -- vs COSI
  
  -- Calendar Spreads (carry signals)
  zl_spread_m1_m2 FLOAT64,
  zs_spread_m1_m2 FLOAT64,
  cl_spread_m1_m2 FLOAT64,
  
  -- Energy Proxies
  crack_3_2_1 FLOAT64,
  ho_spread_m1_m2 FLOAT64,
  ethanol_cu_settle FLOAT64,
  
  -- FX (CME + FRED/Yahoo)
  cme_6l_brl_close FLOAT64,         -- CME BRL futures
  fred_usd_cny FLOAT64,             -- FRED spot (if no CME equivalent)
  fred_usd_ars FLOAT64,
  databento_6e_close FLOAT64,       -- EUR/USD futures
  
  -- FRED Macro (~60 columns, prefixed)
  fred_dff FLOAT64,
  fred_dgs10 FLOAT64,
  fred_vixcls FLOAT64,
  fred_dtwexbgs FLOAT64,
  fred_cpiaucsl FLOAT64,
  -- ... (all 60 FRED series)
  
  -- EIA Biofuels
  eia_biodiesel_prod_us FLOAT64,
  eia_rin_price_d4 FLOAT64,
  eia_rin_price_d6 FLOAT64,
  
  -- USDA Granular
  usda_wasde_world_soyoil_prod FLOAT64,
  usda_exports_soybeans_net_sales_china FLOAT64,
  usda_cropprog_il_soy_condition_good_excellent_pct FLOAT64,
  
  -- Weather
  weather_us_midwest_tavg_wgt FLOAT64,
  weather_br_soy_belt_tavg_wgt FLOAT64,
  weather_ar_soy_belt_tavg_wgt FLOAT64,
  
  -- CFTC
  cftc_zl_net_managed_money INT64,
  cftc_zl_net_commercial INT64,
  
  -- Volatility
  vol_vix_level FLOAT64,
  vol_cme_cvol_soybeans_30d FLOAT64,
  vol_zl_realized_20d FLOAT64,
  vol_regime STRING,
  
  -- Policy/Trump (from existing scripts)
  policy_trump_action_prob FLOAT64,
  policy_trump_expected_zl_move FLOAT64,
  policy_trump_score_signed FLOAT64,
  
  -- Microstructure (from orderflow_1m, daily aggregates)
  microstructure_zl_depth_imbalance_avg FLOAT64,
  microstructure_zl_trade_imbalance_avg FLOAT64,
  
  -- Calculated Signals
  signal_zl_sma_50 FLOAT64,
  signal_zl_rsi_14 FLOAT64,
  signal_zl_macd FLOAT64,
  
  -- Regime
  regime STRING,
  
  -- Targets
  target_1w FLOAT64,
  target_1m FLOAT64,
  target_3m FLOAT64,
  target_6m FLOAT64,
  target_12m FLOAT64,
  
  -- PIT
  as_of TIMESTAMP NOT NULL,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY symbol
OPTIONS (
  description='Canonical master_features - CME-native substitution via crush/oilshare, NO external palm'
);

-- ============================================================================
-- PART 12: NEURAL TRAINING
-- ============================================================================

-- Table 26: Neural Feature Vectors
CREATE OR REPLACE TABLE neural.feature_vectors (
  date DATE NOT NULL,
  symbol STRING NOT NULL,
  horizon STRING NOT NULL,
  features JSON NOT NULL,
  regime_id STRING,
  target_value FLOAT64,
  as_of TIMESTAMP NOT NULL,
  collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY symbol, horizon
OPTIONS (description='Neural training features');

-- ============================================================================
-- PART 13: DIMENSIONS & REFERENCE
-- ============================================================================

-- Table 27: Instrument Metadata
CREATE OR REPLACE TABLE dim.instrument_metadata (
  root STRING NOT NULL,
  name STRING,
  tick_size FLOAT64,
  point_value FLOAT64,
  currency STRING,
  exchange STRING,
  session_tz STRING,
  session_hours STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- Table 28: Production Weights (for Weather Aggregation)
CREATE OR REPLACE TABLE dim.production_weights (
  region_id STRING NOT NULL,
  area_code STRING NOT NULL,
  commodity STRING NOT NULL,
  weight FLOAT64 NOT NULL,
  source STRING,
  valid_from DATE,
  valid_to DATE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY region_id, commodity;

-- Table 29: Crush Conversion Factors (for Theoretical Crush)
CREATE OR REPLACE TABLE dim.crush_conversion_factors (
  effective_date DATE NOT NULL,
  oil_yield_lbs_per_bu FLOAT64 DEFAULT 11.0,
  meal_yield_lbs_per_bu FLOAT64 DEFAULT 44.0,
  processing_cost_usd_per_bu FLOAT64 DEFAULT 0.50,
  source STRING,
  notes STRING
);

-- ============================================================================
-- PART 14: OPERATIONS
-- ============================================================================

-- Table 30: Data Quality Events
CREATE OR REPLACE TABLE ops.data_quality_events (
  ts TIMESTAMP NOT NULL,
  source STRING NOT NULL,
  dataset STRING NOT NULL,
  table_name STRING,
  severity STRING NOT NULL,
  check_type STRING,
  message STRING NOT NULL,
  payload JSON,
  resolved BOOL DEFAULT FALSE,
  resolved_at TIMESTAMP
)
PARTITION BY DATE(ts)
CLUSTER BY source, severity
OPTIONS (description='Data quality monitoring');

-- ============================================================================
-- PART 15: HISTORICAL BRIDGE (2000-2010)
-- ============================================================================

-- Table 31: Yahoo ZL Historical 2000-2010
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
OPTIONS (description='Yahoo ZL 2000-2010 - bridges DataBento gap before 2010-06-06');

-- ============================================================================
-- VALIDATION QUERIES
-- ============================================================================

-- Check tables created
SELECT table_schema, table_name, table_type, creation_time
FROM `region-us-central1`.INFORMATION_SCHEMA.TABLES  
WHERE table_catalog = 'cbi-v14'
  AND table_schema IN ('market_data', 'raw_intelligence', 'signals', 'features', 
                       'regimes', 'drivers', 'drivers_of_drivers', 'neural', 'dim', 'ops')
ORDER BY table_schema, table_name;

-- ============================================================================
-- END - 31 TABLES TOTAL (Venue-Pure + Free APIs Only)
-- ============================================================================

