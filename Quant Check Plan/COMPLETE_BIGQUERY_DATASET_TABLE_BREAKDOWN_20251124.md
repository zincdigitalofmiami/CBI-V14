# Complete BigQuery Dataset & Table Breakdown - First Time Setup
**Date**: November 24, 2025  
**Purpose**: Exhaustive list of ALL datasets, tables, views, and declarations needed for initial BigQuery construction  
**Source**: Dataform Structure + Maximum Quality Training + Comprehensive Data Pipeline Audit

---

## Dataset Structure Overview

```
cbi-v14 (Project)
├── raw                       # Raw source data (declarations)
├── staging                   # Cleaned, normalized data
├── features                  # Engineered features (STRUCTs + flat)
├── training                  # Training-ready tables & export views
├── forecasts                 # Model predictions (Mac → BQ)
├── api                       # Public API views
├── reference                 # Reference tables & mappings
├── ops                       # Operations & monitoring
├── neural                    # Neural signals (existing)
└── forecasting_data_warehouse  # Existing warehouse (legacy)
```

---

## LAYER 1: RAW DATASET (`raw`)

**Purpose**: Source data declarations (external sources, not created by Dataform)

### Declarations (Source Tables)

#### 1. Market Data
```sql
-- databento_daily_ohlcv
database: "cbi-v14"
schema: "raw"
name: "databento_daily_ohlcv"
description: "Daily OHLCV from Databento for ZL, FX, energies"
Source: Databento API
Symbols: ZL, ZS, ZM, ZC, CL, HO, RB, DXY, USDBRL, USDARS, USDCNY
```

```sql
-- databento_contract_ohlcv
database: "cbi-v14"
schema: "raw"
name: "databento_contract_ohlcv"
description: "Contract-specific OHLCV (F/H/K/N/U/Z months)"
Source: Databento API
Symbols: ZL contract months
```

```sql
-- databento_1m_bars
database: "cbi-v14"
schema: "raw"
name: "databento_1m_bars"
description: "1-minute bars for MES (Phase 2)"
Source: Databento API
```

#### 2. Macroeconomic Data
```sql
-- fred_macro
database: "cbi-v14"
schema: "raw"
name: "fred_macro"
description: "FRED indicators: VIXCLS, DFF, CPI, GDP, UNRATE, T10Y2Y"
Source: FRED API
Series: VIXCLS, DFF, CPIAUCSL, GDP, UNRATE, T10Y2Y
```

#### 3. CFTC Data
```sql
-- cftc_disagg
database: "cbi-v14"
schema: "raw"
name: "cftc_disagg"
description: "Commitment of Traders weekly data"
Source: CFTC API
Commodity: SOYBEAN OIL
```

#### 4. Weather Data
```sql
-- weather_daily
database: "cbi-v14"
schema: "raw"
name: "weather_daily"
description: "NOAA/GSOD/GHCN public weather data"
Source: NOAA/GSOD/GHCN
Regions: US Midwest, Brazil soy belt, Argentina
```

#### 5. News & Events
```sql
-- news_events
database: "cbi-v14"
schema: "raw"
name: "news_events"
description: "GDELT and Trends (news, tone, search intensity)"
Source: GDELT API
```

```sql
-- scrape_events
database: "cbi-v14"
schema: "raw"
name: "scrape_events"
description: "All regime-specific sensors: trump_zl_signal, macro_recession_headlines, tariffs_agriculture"
Source: ScrapeCreator API + custom scrapers
```

#### 6. USDA Data
```sql
-- usda_export_sales
database: "cbi-v14"
schema: "raw"
name: "usda_export_sales"
description: "USDA export sales data"
Source: USDA API
```

#### 7. Palm Oil Data
```sql
-- palm_oil_prices
database: "cbi-v14"
schema: "raw"
name: "palm_oil_prices"
description: "FCPO prices from Bursa Malaysia"
Source: Vendor API / yfinance
```

#### 8. Existing Warehouse Tables (Legacy)
```sql
-- trump_policy_intelligence (from forecasting_data_warehouse)
database: "cbi-v14"
schema: "forecasting_data_warehouse"
name: "trump_policy_intelligence"
description: "Truth Social posts, agricultural impact scores"
Source: ScrapeCreator API
```

```sql
-- social_sentiment (from forecasting_data_warehouse)
database: "cbi-v14"
schema: "forecasting_data_warehouse"
name: "social_sentiment"
description: "Social media sentiment data"
Source: ScrapeCreator API
```

```sql
-- news_intelligence (from forecasting_data_warehouse)
database: "cbi-v14"
schema: "forecasting_data_warehouse"
name: "news_intelligence"
description: "News intelligence data"
Source: GDELT / custom scrapers
```

```sql
-- biofuel_policy (from staging)
database: "cbi-v14"
schema: "staging"
name: "biofuel_policy"
description: "RFS mandates and policy data"
Source: EPA / custom scrapers
```

```sql
-- cftc_cot (from staging)
database: "cbi-v14"
schema: "staging"
name: "cftc_cot"
description: "CFTC COT positioning data"
Source: CFTC API
```

```sql
-- usda_export_sales (from staging)
database: "cbi-v14"
schema: "staging"
name: "usda_export_sales"
description: "USDA export sales"
Source: USDA API
```

---

## LAYER 2: STAGING DATASET (`staging`)

**Purpose**: Cleaned, normalized, forward-filled data

### Incremental Tables

#### 1. Market Data
```sql
-- market_daily
type: "incremental"
schema: "staging"
uniqueKey: ["date", "symbol"]
partitionBy: "DATE(date)"
clusterBy: ["symbol"]
tags: ["staging", "market"]

Columns:
- date (DATE)
- symbol (STRING)
- open, high, low, close, volume (FLOAT64)
- daily_range (FLOAT64)
- pct_change (FLOAT64)
- has_volume (BOOL)
- valid_range (BOOL)
- processed_at (TIMESTAMP)
```

#### 2. Macroeconomic Data
```sql
-- fred_macro_clean
type: "incremental"
schema: "staging"
uniqueKey: ["date", "indicator"]
partitionBy: "DATE(date)"
clusterBy: ["indicator"]
tags: ["staging", "macro"]

Columns:
- date (DATE)
- indicator (STRING) - VIXCLS, DFF, CPIAUCSL, GDP, UNRATE, T10Y2Y
- value (FLOAT64)
- value_filled (FLOAT64) - Forward-filled
- value_1d_ago (FLOAT64)
- value_1m_ago (FLOAT64)
- processed_at (TIMESTAMP)
```

```sql
-- vixcls_daily
type: "incremental"
schema: "staging"
uniqueKey: ["date"]
partitionBy: "DATE(date)"
tags: ["staging", "macro", "vix"]

Columns:
- date (DATE)
- vix_close (FLOAT64)
- vix_filled (FLOAT64)
- processed_at (TIMESTAMP)
```

#### 3. CFTC Data
```sql
-- cftc_positions
type: "incremental"
schema: "staging"
uniqueKey: ["report_date", "commodity"]
partitionBy: "DATE(report_date)"
clusterBy: ["commodity"]
tags: ["staging", "cftc"]

Columns:
- report_date (DATE)
- commodity (STRING)
- net_position_money_managers (INT64)
- net_position_commercial (INT64)
- open_interest (INT64)
- position_change_1w (INT64)
- processed_at (TIMESTAMP)
```

#### 4. Weather Data
```sql
-- weather_regions
type: "incremental"
schema: "staging"
uniqueKey: ["date", "region"]
partitionBy: "DATE(date)"
clusterBy: ["region"]
tags: ["staging", "weather"]

Columns:
- date (DATE)
- region (STRING) - US_MIDWEST, BRAZIL_SOY_BELT, ARGENTINA
- temperature_avg (FLOAT64)
- temperature_anomaly (FLOAT64)
- precipitation (FLOAT64)
- precipitation_anomaly (FLOAT64)
- soil_moisture (FLOAT64)
- processed_at (TIMESTAMP)
```

#### 5. News & Events
```sql
-- scrape_events_bucketed
type: "incremental"
schema: "staging"
uniqueKey: ["date", "slug", "bucket"]
partitionBy: "DATE(date)"
clusterBy: ["bucket"]
tags: ["staging", "events"]

Columns:
- date (DATE)
- slug (STRING) - scraper job name
- bucket (STRING) - from ref.scraper_to_bucket
- event_count (INT64)
- avg_sentiment (FLOAT64)
- processed_at (TIMESTAMP)
```

#### 6. FX Data
```sql
-- fx_daily_rates
type: "incremental"
schema: "staging"
uniqueKey: ["date", "currency_pair"]
partitionBy: "DATE(date)"
clusterBy: ["currency_pair"]
tags: ["staging", "fx"]

Columns:
- date (DATE)
- currency_pair (STRING) - USDBRL, USDARS, USDCNY
- rate (FLOAT64)
- rate_change_pct (FLOAT64)
- processed_at (TIMESTAMP)
```

#### 7. FinBERT News Processing (Mac writes here)
```sql
-- news_sentiment_finbert
type: "incremental"
schema: "staging"
uniqueKey: ["date", "topic"]
partitionBy: "DATE(date)"
clusterBy: ["topic"]
tags: ["staging", "news", "nlp"]

Columns:
- date (DATE)
- topic (STRING) - USDA, EPA, CHINA, TARIFFS, etc.
- avg_tone_finbert (FLOAT64)
- avg_uncertainty (FLOAT64)
- story_count (INT64)
- novelty_score (FLOAT64)
- processed_at (TIMESTAMP)
```

#### 8. Palm Oil
```sql
-- palm_oil_complete
type: "incremental"
schema: "staging"
uniqueKey: ["date"]
partitionBy: "DATE(date)"
tags: ["staging", "palm"]

Columns:
- date (DATE)
- fcpo_price (FLOAT64)
- fcpo_price_usd (FLOAT64) - Converted to USD
- fcpo_return (FLOAT64)
- processed_at (TIMESTAMP)
```

#### 9. USDA Data
```sql
-- usda_export_daily
type: "incremental"
schema: "staging"
uniqueKey: ["date", "commodity", "destination"]
partitionBy: "DATE(date)"
clusterBy: ["commodity"]
tags: ["staging", "usda"]

Columns:
- date (DATE)
- commodity (STRING)
- destination (STRING)
- export_sales_mt (FLOAT64)
- export_sales_cumulative_mt (FLOAT64)
- processed_at (TIMESTAMP)
```

#### 10. Biofuel Data
```sql
-- epa_rin_prices
type: "incremental"
schema: "staging"
uniqueKey: ["date"]
partitionBy: "DATE(date)"
tags: ["staging", "biofuel"]

Columns:
- date (DATE)
- rin_d4_price (FLOAT64)
- rin_d6_price (FLOAT64)
- rin_d5_price (FLOAT64)
- processed_at (TIMESTAMP)
```

```sql
-- rfs_mandates_daily
type: "incremental"
schema: "staging"
uniqueKey: ["date", "year"]
partitionBy: "DATE(date)"
tags: ["staging", "biofuel"]

Columns:
- date (DATE)
- year (INT64)
- biodiesel_volume_gal (FLOAT64)
- renewable_volume_gal (FLOAT64)
- advanced_volume_gal (FLOAT64)
- processed_at (TIMESTAMP)
```

---

## LAYER 3: FEATURES DATASET (`features`)

**Purpose**: Engineered features (STRUCTs for warehouse, flat views for Mac)

### Incremental Tables

#### 1. Technical Indicators
```sql
-- technical_indicators
type: "incremental"
schema: "features"
uniqueKey: ["date", "symbol"]
partitionBy: "DATE(date)"
clusterBy: ["symbol"]
tags: ["features", "technical"]

Columns:
- date (DATE)
- symbol (STRING)
- close (FLOAT64)
- ma_5, ma_21, ma_63, ma_252 (FLOAT64)
- rsi_14 (FLOAT64)
- volatility_21d (FLOAT64)
- momentum_21d (FLOAT64)
- processed_at (TIMESTAMP)
```

#### 2. Crush Margin
```sql
-- crush_margin_daily
type: "incremental"
schema: "features"
uniqueKey: ["date"]
partitionBy: "DATE(date)"
clusterBy: ["margin_regime"]
tags: ["features", "fundamentals", "big_eight"]

Columns:
- date (DATE)
- soybean_price (FLOAT64)
- soymeal_price (FLOAT64)
- soyoil_price (FLOAT64)
- gross_margin (FLOAT64)
- net_margin (FLOAT64)
- margin_percentile_all_time (FLOAT64)
- margin_percentile_30d (FLOAT64)
- margin_regime (STRING) - tight, normal, wide
- ma_21d (FLOAT64)
- stddev_21d (FLOAT64)
- processed_at (TIMESTAMP)
```

#### 3. Cross-Asset Correlations
```sql
-- cross_asset_correlations
type: "incremental"
schema: "features"
uniqueKey: ["date", "correlation_pair"]
partitionBy: "DATE(date)"
clusterBy: ["correlation_pair"]
tags: ["features", "cross_asset", "tft_ready"]

Columns:
- date (DATE)
- correlation_pair (STRING) - zl_fcpo, zl_ho, zl_cl, zl_dxy
- zl_fcpo_corr_60d (FLOAT64)
- zl_fcpo_corr_120d (FLOAT64)
- zl_fcpo_beta_60d (FLOAT64)
- zl_ho_corr_60d (FLOAT64)
- zl_ho_corr_120d (FLOAT64)
- zl_ho_beta_60d (FLOAT64)
- zl_cl_corr_60d (FLOAT64)
- zl_cl_corr_120d (FLOAT64)
- zl_cl_beta_60d (FLOAT64)
- zl_dxy_corr_60d (FLOAT64)
- zl_dxy_corr_120d (FLOAT64)
- zl_dxy_beta_60d (FLOAT64)
- processed_at (TIMESTAMP)
```

#### 4. Contract-Specific Features
```sql
-- zl_contracts_matrix
type: "incremental"
schema: "features"
uniqueKey: ["date", "contract_symbol"]
partitionBy: "DATE(date)"
clusterBy: ["contract_symbol", "days_to_expiry"]
tags: ["features", "contracts", "tft_ready"]

Columns:
- date (DATE)
- contract_symbol (STRING)
- contract_month (STRING)
- days_to_expiry (INT64)
- close (FLOAT64)
- volume (FLOAT64)
- open_interest (FLOAT64)
- log_return (FLOAT64)
- m1_m2_spread (FLOAT64)
- m1_m3_spread (FLOAT64)
- carry_signal (FLOAT64)
- processed_at (TIMESTAMP)
```

#### 5. Biodiesel Margin
```sql
-- biodiesel_margin_daily
type: "incremental"
schema: "features"
uniqueKey: ["date"]
partitionBy: "DATE(date)"
clusterBy: ["margin_regime"]
tags: ["features", "biofuel", "big_eight"]

Columns:
- date (DATE)
- zl_price (FLOAT64)
- ho_price (FLOAT64)
- cl_price (FLOAT64)
- rin_d4_price (FLOAT64)
- rin_d6_price (FLOAT64)
- biodiesel_margin (FLOAT64)
- biodiesel_margin_with_rin (FLOAT64)
- margin_regime (STRING) - tight, normal, wide
- processed_at (TIMESTAMP)
```

#### 6. Weather Anomalies
```sql
-- weather_anomalies
type: "incremental"
schema: "features"
uniqueKey: ["date", "region"]
partitionBy: "DATE(date)"
clusterBy: ["region"]
tags: ["features", "weather"]

Columns:
- date (DATE)
- region (STRING)
- precip_zscore (FLOAT64)
- temp_zscore (FLOAT64)
- soil_moisture_zscore (FLOAT64)
- processed_at (TIMESTAMP)
```

#### 7. News Bucket Aggregations
```sql
-- news_bucket_daily
type: "incremental"
schema: "features"
uniqueKey: ["date", "bucket"]
partitionBy: "DATE(date)"
clusterBy: ["bucket"]
tags: ["features", "news"]

Columns:
- date (DATE)
- bucket (STRING)
- event_count (INT64)
- avg_tone (FLOAT64)
- processed_at (TIMESTAMP)
```

#### 8. Master ML Matrix (Nested STRUCTs)
```sql
-- daily_ml_matrix
type: "incremental"
schema: "features"
uniqueKey: ["date", "symbol"]
partitionBy: "DATE(date)"
clusterBy: ["symbol"]
tags: ["features", "master", "structs"]

Columns:
- date (DATE)
- symbol (STRING)
- price (FLOAT64)
- volume (FLOAT64)
- return_1d (FLOAT64)
- market_data (STRUCT)
  - price (FLOAT64)
  - ma_5, ma_21, ma_63, ma_252 (FLOAT64)
  - rsi_14 (FLOAT64)
  - volatility_21d (FLOAT64)
  - momentum_21d (FLOAT64)
- pivots (STRUCT)
  - support_level (FLOAT64)
  - resistance_level (FLOAT64)
  - pivot_point (FLOAT64)
- policy (STRUCT)
  - tariff_events (INT64)
  - trump_sentiment (FLOAT64)
  - policy_score (FLOAT64)
- golden_zone (STRUCT)
  - crush_margin (FLOAT64)
  - china_imports (FLOAT64)
  - dollar_index (FLOAT64)
  - fed_policy (FLOAT64)
  - vix_regime (STRING)
- regime (STRUCT)
  - regime_name (STRING)
  - regime_weight (FLOAT64)
- processed_at (TIMESTAMP)
```

### Views (Flattened for Mac)

#### 1. Flattened ML Matrix
```sql
-- vw_daily_ml_flat
type: "view"
schema: "features"
tags: ["features", "flat", "mac_export"]

Columns: (All STRUCTs flattened)
- date, symbol, price, volume, return_1d
- md_price, md_ma_5, md_ma_21, md_rsi_14, md_vol_21d, md_mom_21d
- s_crush_margin, s_china_imports, s_dollar_index, s_fed_policy, s_vix_regime
- pol_tariff_events, pol_trump_sentiment
- regime_name, regime_weight
- processed_at
```

---

## LAYER 4: TRAINING DATASET (`training`)

**Purpose**: Training-ready tables with targets and export views

### Incremental Tables

#### 1. Training Tables (Per Horizon)
```sql
-- zl_training_prod_1d
type: "incremental"
schema: "training"
uniqueKey: ["date"]
partitionBy: "DATE(date)"
clusterBy: ["regime_name"]
tags: ["training", "1d_horizon"]

Columns:
- date (DATE)
- All features from vw_daily_ml_flat
- price_1d_fwd (FLOAT64)
- return_1d_fwd (FLOAT64)
- vol_1d_fwd (FLOAT64)
- direction_1d_fwd (INT64) - 0 or 1
- sample_weight (FLOAT64) - regime_weight
- split (STRING) - train, val, test
- processed_at (TIMESTAMP)
```

```sql
-- zl_training_prod_5d
type: "incremental"
schema: "training"
uniqueKey: ["date"]
partitionBy: "DATE(date)"
clusterBy: ["regime_name"]
tags: ["training", "5d_horizon"]

Columns: (Same as 1d, but 5d targets)
- return_5d_fwd (FLOAT64)
- vol_5d_fwd (FLOAT64)
- direction_5d_fwd (INT64)
```

```sql
-- zl_training_prod_20d
type: "incremental"
schema: "training"
uniqueKey: ["date"]
partitionBy: "DATE(date)"
clusterBy: ["regime_name"]
tags: ["training", "20d_horizon"]

Columns: (Same as 1d, but 20d targets)
- return_20d_fwd (FLOAT64)
- vol_20d_fwd (FLOAT64)
- direction_20d_fwd (INT64)
```

```sql
-- zl_training_prod_63d
type: "incremental"
schema: "training"
uniqueKey: ["date"]
partitionBy: "DATE(date)"
clusterBy: ["regime_name"]
tags: ["training", "63d_horizon"]

Columns: (Same as 1d, but 63d targets)
- return_63d_fwd (FLOAT64)
- vol_63d_fwd (FLOAT64)
- direction_63d_fwd (INT64)
```

### Views (Mac Export)

#### 1. TFT Training Export
```sql
-- vw_tft_training_export
type: "view"
schema: "training"
tags: ["training", "mac_export", "tft_ready"]

Columns:
- date (DATE)
- series_id (STRING) - CONCAT('ZL_', contract_month)
- static_contract_month (STRING)
- target (FLOAT64) - log_return
- dow, moy, dom (INT64)
- days_to_expiry (INT64)
- is_wasde_day, is_crop_progress_day, is_options_expiry (BOOL)
- md_price, md_ma_5, md_ma_21, md_rsi_14, md_vol_21d, md_mom_21d (FLOAT64)
- m1_m2_spread, m1_m3_spread, carry_signal (FLOAT64)
- s_crush_margin, s_china_imports, s_dollar_index, s_fed_policy, s_vix_regime (FLOAT64)
- zl_fcpo_corr_60d, zl_ho_corr_60d, zl_dxy_corr_60d, zl_fcpo_beta_60d (FLOAT64)
- pol_tariff_events, pol_trump_sentiment (FLOAT64)
- us_midwest_precip_zscore, brazil_precip_zscore, argentina_precip_zscore (FLOAT64)
- usda_tone_finbert, epa_tone_finbert, china_demand_story_count (FLOAT64)
- biodiesel_margin, biodiesel_margin_with_rin (FLOAT64)
- mm_net_length_zl, mm_net_length_pct_oi (FLOAT64)
- regime_name (STRING)
- regime_weight (FLOAT64)
```

---

## LAYER 5: FORECASTS DATASET (`forecasts`)

**Purpose**: Model predictions (Mac writes here)

### Tables (Schema for Mac Writes)

#### 1. ZL Forecasts
```sql
-- zl_forecasts_daily_schema
type: "table"
schema: "forecasts"
partitionBy: "DATE(forecast_date)"
clusterBy: ["horizon", "model_version"]
tags: ["forecasts", "schema"]

Columns:
- forecast_date (DATE)
- as_of_date (DATE)
- horizon (STRING) - 1d, 5d, 20d, 63d
- model_version (STRING)
- predicted_price (FLOAT64)
- predicted_return (FLOAT64)
- confidence_lower (FLOAT64) - P10
- confidence_upper (FLOAT64) - P90
- direction_prob (FLOAT64)
- predicted_volatility (FLOAT64)
- model_type (STRING) - TFT, LightGBM, DeepNN, Ensemble
- created_at (TIMESTAMP)
```

#### 2. ZL Explainers (SHAP)
```sql
-- zl_explainers_daily
type: "table"
schema: "forecasts"
partitionBy: "DATE(forecast_date)"
clusterBy: ["model_version"]
tags: ["forecasts", "shap"]

Columns:
- forecast_date (DATE)
- as_of_date (DATE)
- model_version (STRING)
- feature_name (STRING)
- shap_value (FLOAT64)
- feature_value (FLOAT64)
- created_at (TIMESTAMP)
```

#### 3. ZL Scenarios Grid
```sql
-- zl_scenarios_grid
type: "table"
schema: "forecasts"
partitionBy: "DATE(forecast_date)"
tags: ["forecasts", "scenarios"]

Columns:
- forecast_date (DATE)
- as_of_date (DATE)
- scenario_name (STRING)
- scenario_probability (FLOAT64)
- predicted_price (FLOAT64)
- created_at (TIMESTAMP)
```

#### 4. ZL Regimes
```sql
-- zl_regimes_daily
type: "table"
schema: "forecasts"
partitionBy: "DATE(date)"
tags: ["forecasts", "regimes"]

Columns:
- date (DATE)
- inferred_regime (STRING)
- canonical_regime (STRING)
- regime_confidence (FLOAT64)
- created_at (TIMESTAMP)
```

---

## LAYER 6: API DATASET (`api`)

**Purpose**: Public API views

### Views

#### 1. Latest Forecast
```sql
-- vw_latest_forecast
type: "view"
schema: "api"
tags: ["api", "public"]

Columns:
- forecast_date (DATE)
- as_of_date (DATE)
- horizon (STRING)
- predicted_price (FLOAT64)
- predicted_return (FLOAT64)
- confidence_lower (FLOAT64)
- confidence_upper (FLOAT64)
- direction_prob (FLOAT64)
- predicted_volatility (FLOAT64)
- current_price (FLOAT64)
- days_ahead (INT64)
```

---

## LAYER 7: REFERENCE DATASET (`reference`)

**Purpose**: Reference tables and mappings

### Tables

#### 1. Regime Calendar
```sql
-- regime_calendar
type: "table"
schema: "reference"
tags: ["reference", "regime"]

Columns:
- date (DATE)
- regime_name (STRING) - trump_anticipation_2024, trade_war_2017_2019, etc.
- start_date (DATE)
- end_date (DATE)
```

#### 2. Regime Weights
```sql
-- regime_weights
type: "table"
schema: "reference"
tags: ["reference", "regime"]

Columns:
- regime_name (STRING)
- training_weight (FLOAT64)
- gating_weight (FLOAT64)
```

#### 3. Scraper to Bucket Mapping
```sql
-- scraper_to_bucket
type: "table"
schema: "reference"
tags: ["reference", "mapping"]

Columns:
- slug (STRING) - scraper job name
- bucket (STRING) - bucket name
- regime (STRING) - associated regime
```

#### 4. News Bucket Taxonomy
```sql
-- news_bucket_taxonomy
type: "table"
schema: "reference"
tags: ["reference", "mapping"]

Columns:
- keyword (STRING)
- entity (STRING)
- bucket (STRING)
```

#### 5. Weather Region Mapping
```sql
-- weather_region_mapping
type: "table"
schema: "reference"
tags: ["reference", "mapping"]

Columns:
- station_id (STRING)
- region (STRING) - US_MIDWEST, BRAZIL_SOY_BELT, ARGENTINA
- latitude (FLOAT64)
- longitude (FLOAT64)
```

---

## LAYER 8: OPERATIONS DATASET (`ops`)

**Purpose**: Monitoring and operations

### Tables

#### 1. Data Quality Checks
```sql
-- data_quality_checks
type: "table"
schema: "ops"
tags: ["ops", "monitoring"]

Columns:
- check_timestamp (TIMESTAMP)
- table_name (STRING)
- row_count (INT64)
- distinct_dates (INT64)
- distinct_symbols (INT64)
- null_dates (INT64)
- null_symbols (INT64)
- latest_date (DATE)
- earliest_date (DATE)
```

#### 2. Dataform Run Metadata
```sql
-- dataform_run_metadata
type: "table"
schema: "ops"
tags: ["ops", "monitoring"]

Columns:
- run_timestamp (TIMESTAMP)
- config_vars (STRING)
- feature_row_count (INT64)
- latest_feature_date (DATE)
- distinct_dates (INT64)
- status (STRING)
```

---

## LAYER 9: ASSERTIONS (Data Quality Gates)

**Purpose**: Data quality checks (no tables, just assertions)

### Assertions

#### 1. Not Null Keys
```sql
-- assert_not_null_keys
type: "assertion"
schema: "reference"
tags: ["data_quality", "critical"]

Checks: market_daily.date IS NOT NULL AND market_daily.symbol IS NOT NULL
```

#### 2. Unique Market Key
```sql
-- assert_unique_market_key
type: "assertion"
schema: "reference"
tags: ["data_quality", "critical"]

Checks: No duplicate (date, symbol) in market_daily
```

#### 3. FRED Freshness
```sql
-- assert_fred_fresh
type: "assertion"
schema: "reference"
tags: ["data_quality", "freshness"]

Checks: MAX(date) in fred_macro_clean >= CURRENT_DATE() - 7 days
```

#### 4. Crush Margin Validity
```sql
-- assert_crush_margin_valid
type: "assertion"
schema: "reference"
tags: ["data_quality", "business_logic"]

Checks: 
- gross_margin BETWEEN -100 AND 1000
- net_margin IS NOT NULL
- margin_regime IN ('tight', 'normal', 'wide')
```

#### 5. Join Integrity
```sql
-- assert_join_integrity
type: "assertion"
schema: "reference"
tags: ["data_quality"]

Checks: All dates in daily_ml_matrix have corresponding market_daily rows
```

#### 6. Big Eight Complete
```sql
-- assert_big_eight_complete
type: "assertion"
schema: "reference"
tags: ["data_quality", "big_eight"]

Checks: All dates have Big 8 signals (crush_margin, china_imports, dollar_index, etc.)
```

---

## EXISTING DATASETS (Legacy - Keep for Now)

### `neural` Dataset
```sql
-- vw_big_eight_signals (existing view)
schema: "neural"
tags: ["neural", "big_eight"]

Columns:
- date (DATE)
- feature_vix_stress (FLOAT64)
- feature_harvest_pace (FLOAT64)
- feature_china_relations (FLOAT64)
- feature_tariff_threat (FLOAT64)
- feature_geopolitical_volatility (FLOAT64)
- feature_biofuel_cascade (FLOAT64)
- feature_hidden_correlation (FLOAT64)
- feature_biofuel_ethanol (FLOAT64)
- big8_composite_score (FLOAT64)
- market_regime (STRING)
```

### `forecasting_data_warehouse` Dataset
```sql
-- Keep existing tables for now, migrate gradually
Tables:
- trump_policy_intelligence
- social_sentiment
- news_intelligence
- biofuel_policy
- cftc_cot
- usda_export_sales
- weather_data_midwest_openmeteo
- vegas_customers
- vegas_events
- vegas_index
```

---

## SUMMARY: Complete Dataset & Table Count

### Datasets (9 total)
1. `raw` - 8 declarations
2. `staging` - 10 incremental tables
3. `features` - 8 incremental tables + 1 view
4. `training` - 4 incremental tables + 1 view
5. `forecasts` - 4 tables (Mac writes)
6. `api` - 1 view
7. `reference` - 5 tables
8. `ops` - 2 tables
9. `neural` - 1 view (existing)

### Total Objects
- **Declarations**: 8 (raw sources)
- **Incremental Tables**: 22
- **Regular Tables**: 11 (forecasts + reference + ops)
- **Views**: 3 (flattened exports + API)
- **Assertions**: 6 (data quality gates)

### Total: 50 objects

---

## CREATION ORDER (First Time Setup)

### Phase 1: Reference Tables (Day 1)
1. Create `reference` dataset
2. Create all reference tables (regime_calendar, regime_weights, scraper_to_bucket, etc.)
3. Populate reference data

### Phase 2: Raw Declarations (Day 1)
1. Create `raw` dataset
2. Declare all source tables (databento_daily_ohlcv, fred_macro, etc.)

### Phase 3: Staging Tables (Day 2)
1. Create `staging` dataset
2. Create all staging incremental tables
3. Run initial backfill

### Phase 4: Features Tables (Day 3-4)
1. Create `features` dataset
2. Create all feature incremental tables
3. Create daily_ml_matrix (with STRUCTs)
4. Create vw_daily_ml_flat (flattened view)

### Phase 5: Training Tables (Day 5)
1. Create `training` dataset
2. Create all training incremental tables
3. Create vw_tft_training_export view

### Phase 6: Forecasts Tables (Day 6)
1. Create `forecasts` dataset
2. Create all forecast schema tables (empty, Mac writes)

### Phase 7: API Views (Day 6)
1. Create `api` dataset
2. Create vw_latest_forecast view

### Phase 8: Operations Tables (Day 7)
1. Create `ops` dataset
2. Create monitoring tables

### Phase 9: Assertions (Day 7)
1. Create all assertions in `reference` dataset
2. Run initial data quality checks

---

## DATA SOURCES SUMMARY

### External APIs
- Databento (market data)
- FRED (macroeconomic)
- CFTC (positioning)
- NOAA/GSOD/GHCN (weather)
- GDELT (news)
- ScrapeCreator (social/Trump)
- USDA (exports)
- EPA (RFS/RIN)
- Bursa Malaysia (FCPO)

### Internal Sources
- forecasting_data_warehouse (legacy tables)
- neural.vw_big_eight_signals (existing view)

---

**STATUS**: Complete breakdown of all datasets, tables, views, and declarations needed for first-time BigQuery construction. Nothing left out.

