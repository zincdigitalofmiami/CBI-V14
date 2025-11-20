---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Data Lineage Map

**Date**: November 13, 2025  
**Project**: CBI-V14 Soybean Oil Forecasting Platform  
**Version**: 1.0

## Overview

This document maps the complete data lineage from ingestion through feature engineering, training, prediction, and monitoring. Each table lists its upstream sources, transformations applied, and downstream consumers.

## Lineage Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│ INGESTION LAYER                                                      │
│ src/ingestion/*.py → raw_intelligence.*                              │
└──────────────┬───────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ FEATURE ENGINEERING LAYER                                           │
│ ETL Scripts → features.*                                            │
└──────────────┬───────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ TRAINING PREPARATION LAYER                                          │
│ SQL Transformations → training.*                                     │
└──────────────┬───────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ MODEL TRAINING LAYER                                                │
│ Mac M4 Pipeline → Vertex AI Models                                  │
└──────────────┬───────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PREDICTION & SERVING LAYER                                           │
│ Vertex AI Endpoints → predictions.*                                  │
└──────────────┬───────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ MONITORING LAYER                                                    │
│ Performance Scripts → monitoring.*                                   │
└─────────────────────────────────────────────────────────────────────┘
```

## Raw Intelligence Tables

### `raw_intelligence.commodities_agriculture_soybean_oil_raw_daily`

**Upstream Sources**:
- Yahoo Finance API (`src/ingestion/yahoo_finance_ingestion.py`)
- CME Group API (`src/ingestion/cme_ingestion.py`)
- Barchart API (`src/ingestion/barchart_ingestion.py`)

**Transformations**:
- None (raw data as received)
- Timestamp normalization to UTC
- Source attribution added

**Downstream Consumers**:
- `features.general_master_daily` (price features)
- `features.commodities_agriculture_cftc_filled_daily` (correlation features)

**Schema**:
- `time TIMESTAMP NOT NULL` – Price timestamp
- `close_price FLOAT64 NOT NULL` – Closing price
- `open_price FLOAT64` – Opening price
- `high_price FLOAT64` – High price
- `low_price FLOAT64` – Low price
- `volume INT64` – Trading volume
- `source STRING NOT NULL` – Data source (yahoo, cme, barchart)
- `ingest_timestamp TIMESTAMP NOT NULL` – When data was ingested
- `data_quality_flag STRING` – Quality flags (null, outlier, etc.)

### `raw_intelligence.intelligence_weather_global_raw_daily`

**Upstream Sources**:
- OpenMeteo API (`src/ingestion/weather_ingestion.py`)
- NOAA API (`src/ingestion/noaa_ingestion.py`)

**Transformations**:
- None (raw weather data)
- Location normalization (lat/lon to region codes)

**Downstream Consumers**:
- `features.weather_aggregates_daily` (weather-derived features)
- `features.general_master_daily` (seasonal features)

**Schema**:
- `time TIMESTAMP NOT NULL` – Weather observation time
- `region STRING NOT NULL` – Geographic region (us_midwest, brazil, argentina)
- `temperature_c FLOAT64` – Temperature in Celsius
- `precipitation_mm FLOAT64` – Precipitation in millimeters
- `humidity_pct FLOAT64` – Relative humidity percentage
- `source STRING NOT NULL` – Data source
- `ingest_timestamp TIMESTAMP NOT NULL`

### `raw_intelligence.intelligence_policy_trump_raw_daily`

**Upstream Sources**:
- Truth Social scraping (`src/ingestion/trump_policy_ingestion.py`)
- Federal Register API (`src/ingestion/federal_register_ingestion.py`)

**Transformations**:
- None (raw policy intelligence)
- Sentiment scoring applied in feature layer

**Downstream Consumers**:
- `features.policy_trump_daily` (policy-derived features)
- `features.general_master_daily` (geopolitical features)

**Schema**:
- `time TIMESTAMP NOT NULL` – Policy event time
- `source STRING NOT NULL` – Source (truth_social, federal_register)
- `text STRING` – Policy text or post content
- `category STRING` – Policy category (trade, agriculture, energy)
- `ingest_timestamp TIMESTAMP NOT NULL`

### `raw_intelligence.intelligence_news_general_raw_daily`

**Upstream Sources**:
- Reuters API (`src/ingestion/news_ingestion.py`)
- News scraping (`src/ingestion/news_scraper.py`)

**Transformations**:
- None (raw news articles)
- Sentiment analysis applied in feature layer

**Downstream Consumers**:
- `features.news_sentiment_daily` (news-derived features)
- `features.general_master_daily` (sentiment features)

### `raw_intelligence.intelligence_sentiment_social_raw_daily`

**Upstream Sources**:
- Social media APIs (`src/ingestion/social_sentiment_ingestion.py`)
- Reddit scraping (`src/ingestion/reddit_ingestion.py`)

**Transformations**:
- None (raw social posts)
- Sentiment scoring applied in feature layer

**Downstream Consumers**:
- `features.social_sentiment_daily` (social sentiment features)
- `features.general_master_daily` (sentiment aggregates)

### `raw_intelligence.fx_dxy_raw_daily`

**Upstream Sources**:
- Yahoo Finance API (`src/ingestion/yahoo_finance_ingestion.py`)
- FRED API (`src/ingestion/fred_ingestion.py`)

**Downstream Consumers**:
- `features.fx_derived_features_daily` (FX features)
- `features.general_master_daily` (macro features)

### `raw_intelligence.equities_vix_raw_daily`

**Upstream Sources**:
- Yahoo Finance API (`src/ingestion/yahoo_finance_ingestion.py`)

**Downstream Consumers**:
- `features.volatility_metrics_daily` (volatility features)
- `features.general_master_daily` (VIX stress features)

## Feature Tables

### `features.general_master_daily`

**Upstream Sources**:
- `raw_intelligence.commodities_agriculture_soybean_oil_raw_daily` (price features)
- `raw_intelligence.commodities_agriculture_corn_raw_daily` (corn prices)
- `raw_intelligence.commodities_agriculture_palm_oil_raw_daily` (palm oil prices)
- `raw_intelligence.commodities_energy_crude_oil_raw_daily` (crude oil prices)
- `raw_intelligence.equities_vix_raw_daily` (VIX levels)
- `raw_intelligence.fx_dxy_raw_daily` (USD index)
- `raw_intelligence.intelligence_weather_global_raw_daily` (weather aggregates)
- `raw_intelligence.intelligence_policy_trump_raw_daily` (policy signals)
- `raw_intelligence.intelligence_news_general_raw_daily` (news sentiment)
- `raw_intelligence.intelligence_sentiment_social_raw_daily` (social sentiment)
- `features.commodities_agriculture_cftc_filled_daily` (CFTC positioning)
- `features.biofuel_rin_proxy_daily` (RIN proxy features)

**Transformations**:
- Price features: returns, moving averages, RSI, momentum indicators
- Correlation features: 30-day rolling correlations (soybean oil vs palm, crude, etc.)
- Volatility features: VIX levels, volatility ratios
- Macro features: DXY levels, FX rates
- Weather features: aggregated weather scores by region
- Policy features: Trump policy impact scores, tariff threat levels
- Sentiment features: news sentiment scores, social sentiment aggregates
- Big-8 signals: composite scores from 8 major signals
- Seasonal features: monthly seasonality indices, harvest timing

**Downstream Consumers**:
- `training.horizon_1w_production`
- `training.horizon_1m_production`
- `training.horizon_3m_production`
- `training.horizon_6m_production`
- `training.horizon_12m_production`
- All regime training tables

**Schema**:
- `date DATE NOT NULL` – Feature date
- `zl_price_current FLOAT64` – Current soybean oil price
- `zl_volume INT64` – Trading volume
- `corr_zl_palm_30d FLOAT64` – 30-day correlation with palm oil
- `corr_zl_crude_30d FLOAT64` – 30-day correlation with crude oil
- `vix_level FLOAT64` – VIX index level
- `dxy_level FLOAT64` – USD index level
- `argentina_export_tax FLOAT64` – Argentina export tax rate
- `brazil_market_share FLOAT64` – Brazil market share
- `cftc_commercial_net FLOAT64` – CFTC commercial net positions
- `rsi_14 FLOAT64` – 14-day RSI
- `ma_30d FLOAT64` – 30-day moving average
- `seasonal_index FLOAT64` – Seasonal index
- `event_impact_level INT64` – Event impact level
- `china_tariff_rate FLOAT64` – China tariff rate
- ... (290+ total features)
- `training_weight INT64` – Sample weight for training
- `market_regime STRING` – Market regime classification

### `features.biofuel_rin_proxy_daily`

**Upstream Sources**:
- `raw_intelligence.commodities_energy_crude_oil_raw_daily` (crude prices)
- `yahoo_finance_comprehensive.rin_proxy_features_final` (legacy RIN data)

**Transformations**:
- RIN price proxy calculation from crude oil and ethanol prices
- Biofuel mandate calculations
- RFS volume requirements

**Downstream Consumers**:
- `features.general_master_daily` (biofuel features)

### `features.commodities_agriculture_cftc_filled_daily`

**Upstream Sources**:
- `raw_intelligence.commodities_agriculture_cftc_raw_weekly` (CFTC COT data)

**Transformations**:
- Weekly to daily interpolation
- Missing value imputation (forward fill, then backward fill)
- Net position calculations

**Downstream Consumers**:
- `features.general_master_daily` (positioning features)

## Training Tables

### `training.horizon_1m_production`

**Upstream Sources**:
- `features.general_master_daily` (all features)
- Target calculation: forward-looking 1-month price change

**Transformations**:
- Join features with target calculation: `target_1m = (price_1m_future - price_current) / price_current`
- Assign `training_weight` based on regime and data quality
- Assign `market_regime` based on date ranges:
  - `pre_crisis_2000_2007`: 2000-01-01 to 2007-12-31
  - `crisis_2008`: 2008-01-01 to 2009-12-31
  - `recovery_2010_2016`: 2010-01-01 to 2016-12-31
  - `trade_war_2017_2019`: 2017-01-01 to 2019-12-31
  - `trump_2023_2025`: 2023-01-01 to present

**Downstream Consumers**:
- Mac M4 training pipeline (`scripts/export_training_data.py`)
- BQML models (shadow mode during migration)

**Schema**:
- `date DATE NOT NULL`
- `target_1w FLOAT64` – 1-week forward return
- `target_1m FLOAT64` – 1-month forward return
- `target_3m FLOAT64` – 3-month forward return
- `target_6m FLOAT64` – 6-month forward return
- `target_12m FLOAT64` – 12-month forward return
- All feature columns from `features.general_master_daily` (290+ features)
- `training_weight INT64 NOT NULL`
- `market_regime STRING NOT NULL`

### `training.horizon_1w_production`

**Upstream Sources**: Same as `training.horizon_1m_production`  
**Transformations**: Target is 1-week forward return  
**Downstream Consumers**: Same as `training.horizon_1m_production`

### `training.horizon_3m_production`, `training.horizon_6m_production`, `training.horizon_12m_production`

**Upstream Sources**: Same as `training.horizon_1m_production`  
**Transformations**: Targets are 3-month, 6-month, 12-month forward returns  
**Downstream Consumers**: Same as `training.horizon_1m_production`

### `training.regime_trump_2023_2025_production`

**Upstream Sources**:
- `features.general_master_daily` (filtered to 2023-01-01 to present)

**Transformations**:
- Filter by date range
- Enhanced Trump policy features
- Higher weight on recent data

**Downstream Consumers**:
- Regime-specific model training

## Prediction Tables

### `predictions.horizon_1m_production`

**Upstream Sources**:
- Vertex AI model endpoints (deployed models)
- `features.general_master_daily` (latest features)

**Transformations**:
- Model inference on latest features
- Quantile calculation (P10, P50, P90)
- Signal generation (BUY/WAIT/MONITOR) based on prediction vs current price
- SHAP value extraction for feature attribution

**Downstream Consumers**:
- Dashboard API (`dashboard-nextjs/src/pages/api/v4/procurement-timing.tsx`)
- Monitoring scripts

**Schema**:
- `date DATE NOT NULL` – Prediction date
- `model_name STRING NOT NULL` – Model identifier
- `p10 FLOAT64` – 10th percentile forecast
- `p50 FLOAT64` – 50th percentile (median) forecast
- `p90 FLOAT64` – 90th percentile forecast
- `point_prediction FLOAT64` – Point forecast
- `buy_wait_monitor STRING` – Procurement signal
- `shap_top_factor STRING` – Top contributing feature
- `shap_top_factor_contrib FLOAT64` – Contribution value
- `ingest_timestamp TIMESTAMP NOT NULL`

## Monitoring Tables

### `monitoring.data_quality_daily`

**Upstream Sources**:
- All `raw_intelligence.*` tables
- All `features.*` tables

**Transformations**:
- Calculate freshness (days since last update)
- Calculate null rates per column
- Detect duplicates
- Flag anomalies

**Downstream Consumers**:
- Alerting system
- Dashboard

### `monitoring.model_performance_daily`

**Upstream Sources**:
- `predictions.horizon_1m_production` (predictions)
- `raw_intelligence.commodities_agriculture_soybean_oil_raw_daily` (actuals)

**Transformations**:
- Calculate MAPE, MAE, R²
- Compare predictions vs actuals
- Track performance over time

**Downstream Consumers**:
- Dashboard
- Model retraining triggers

### `monitoring.feature_drift_daily`

**Upstream Sources**:
- `features.general_master_daily` (current features)
- Historical feature distributions

**Transformations**:
- Calculate distribution drift (KL divergence, Wasserstein distance)
- Flag significant drift (>2 standard deviations)

**Downstream Consumers**:
- Alerting system
- Model retraining triggers

## Script Locations

### Ingestion Scripts
- `src/ingestion/yahoo_finance_ingestion.py` → `raw_intelligence.commodities_*_raw_daily`
- `src/ingestion/weather_ingestion.py` → `raw_intelligence.intelligence_weather_*_raw_daily`
- `src/ingestion/trump_policy_ingestion.py` → `raw_intelligence.intelligence_policy_trump_raw_daily`
- `src/ingestion/news_ingestion.py` → `raw_intelligence.intelligence_news_general_raw_daily`
- `src/ingestion/social_sentiment_ingestion.py` → `raw_intelligence.intelligence_sentiment_social_raw_daily`

### Feature Engineering Scripts
- `scripts/calculate_amplified_features.py` → `features.general_master_daily`
- `scripts/TRUMP_SENTIMENT_QUANT_ENGINE.py` → `features.policy_trump_daily`
- SQL transformations in `config/bigquery/features/` → `features.*`

### Training Scripts
- `scripts/export_training_data.py` → Exports `training.*` to Parquet for Mac M4
- SQL transformations in `config/bigquery/training/` → `training.*`

### Prediction Scripts
- `src/prediction/vertex_ai_predictor.py` → `predictions.*`
- `dashboard-nextjs/src/pages/api/v4/procurement-timing.tsx` → Reads `predictions.*`

### Monitoring Scripts
- `scripts/comprehensive_data_audit.py` → `monitoring.data_quality_daily`
- `docs/forecast/forecast_validator.py` → `monitoring.model_performance_daily`

## References

- See `NAMING_CONVENTION_SPEC.md` for table naming rules
- See `DATASET_STRUCTURE_DESIGN.md` for dataset organization
- See `DEDUPLICATION_RULES.md` for source precedence

