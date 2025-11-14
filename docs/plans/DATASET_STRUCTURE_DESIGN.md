# BigQuery Dataset Structure Design

**Date**: November 13, 2025  
**Project**: CBI-V14 Soybean Oil Forecasting Platform  
**Version**: 1.0

## Overview

This document defines the purpose-driven dataset structure for the CBI-V14 BigQuery warehouse. The design replaces 24 ad-hoc datasets with 6 focused datasets, each with clear responsibilities and security policies.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    INGESTION LAYER                              │
│  src/ingestion/*.py scripts → raw_intelligence.*                │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FEATURE ENGINEERING                          │
│  ETL scripts → features.* (engineered datasets)                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TRAINING LAYER                                │
│  SQL transformations → training.* (model inputs)                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PREDICTION LAYER                             │
│  Vertex AI models → predictions.* (forecasts)                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CONSUMER LAYER                               │
│  Dashboard / API → monitoring.* (metrics & logs)               │
└─────────────────────────────────────────────────────────────────┘
```

## Dataset Specifications

### 1. `raw_intelligence`

**Purpose**: Landing zone for all ingestion scripts. Contains unprocessed raw data from external sources.

**Responsibilities**:
- Receive data from ingestion scripts in `src/ingestion/`
- Store raw, unprocessed data exactly as received
- Maintain data provenance and timestamps
- No data transformation or cleaning

**Write Access**: Ingestion scripts only  
**Read Access**: Feature engineering scripts, monitoring scripts, dashboard APIs (for Vegas Intel)

**Special Cases**:
- **Vegas Intel Tables**: These are part of a separate sales intelligence layer for US Oil Solutions restaurant customers. Data flows READ-ONLY from Glide API → BigQuery → Dashboard. These tables are NOT used in forecasting models but pull ZL price from the forecasting system for ROI calculations. See `docs/vegas-intel/` for details.
- **Weather Tables**: Preserve multi-location granularity (Argentina, Brazil, US, US_Midwest) - do not aggregate into single table

**Example Tables**:
- `raw_intelligence.commodities_agriculture_soybean_oil_raw_daily`
- `raw_intelligence.intelligence_weather_global_raw_daily` (multi-location: Argentina, Brazil, US, US_Midwest)
- `raw_intelligence.intelligence_policy_trump_raw_daily`
- `raw_intelligence.intelligence_news_general_raw_daily`
- `raw_intelligence.intelligence_sentiment_social_raw_daily`
- `raw_intelligence.intelligence_vegas_restaurants_raw_daily` (Vegas Intel - sales intelligence layer)
- `raw_intelligence.intelligence_vegas_fryers_raw_daily` (Vegas Intel - sales intelligence layer)
- `raw_intelligence.intelligence_vegas_casinos_raw_daily` (Vegas Intel - sales intelligence layer)
- `raw_intelligence.fx_dxy_raw_daily`
- `raw_intelligence.equities_vix_raw_daily`

**Schema Requirements**:
- All tables must include `ingest_timestamp TIMESTAMP NOT NULL`
- All tables must include `source STRING NOT NULL`
- Date/time columns should be `time TIMESTAMP` for raw data
- Include `data_quality_flag STRING` for anomaly tracking

**Partitioning**: Partition by date (DATE(time) or DATE(date))  
**Clustering**: Cluster by `source` for multi-source tables

### 2. `features`

**Purpose**: Engineered feature datasets used for model training and prediction.

**Responsibilities**:
- Transform raw data into model-ready features
- Consolidate duplicate columns and sources
- Maintain feature consistency across horizons
- Document feature definitions and transformations

**Write Access**: Feature engineering scripts (SQL/Python)  
**Read Access**: Training scripts, prediction scripts

**Example Tables**:
- `features.general_master_daily` – Master feature set (290+ features)
- `features.biofuel_rin_proxy_daily` – Biofuel RIN proxy features
- `features.commodities_general_yahoo_normalized_daily` – Normalized Yahoo Finance data
- `features.commodities_agriculture_cftc_filled_daily` – CFTC positioning with imputation
- `features.volatility_metrics_daily` – Volatility-derived features
- `features.macro_economic_indicators_monthly` – Macro indicators

**Schema Requirements**:
- Date columns should be `date DATE NOT NULL`
- All feature columns should be `FLOAT64` (nullable allowed)
- Include `training_weight INT64` for sample weighting
- Include `market_regime STRING` for regime-based training

**Partitioning**: Partition by `date`  
**Clustering**: Cluster by `market_regime` and `month` (extracted from date)

### 3. `training`

**Purpose**: Finalized training tables for each horizon and regime.

**Responsibilities**:
- Store training datasets with targets (target_1w, target_1m, etc.)
- Ensure identical schemas across horizons (290+ features)
- Include training weights and market regime assignments
- Support both production and archive environments

**Write Access**: Training preparation scripts  
**Read Access**: Mac M4 training pipeline (local TensorFlow Metal), prediction upload scripts

**Training Table Types**:
- **Full-Feature Tables**: `training.full_features_horizon_*` and `training.full_features_regime_*` contain all 1,948 columns for comprehensive local training
- **Production Tables**: `training.horizon_*_production` contain 290 columns for quick comparisons and production workflows
- **Regime Tables**: `training.regime_*` contain historical regime-specific training data

**Example Tables**:
- `training.horizon_1w_production` – 1-week horizon training data
- `training.horizon_1m_production` – 1-month horizon training data
- `training.horizon_3m_production` – 3-month horizon training data
- `training.horizon_6m_production` – 6-month horizon training data
- `training.horizon_12m_production` – 12-month horizon training data
- `training.regime_trump_2023_2025_production` – Trump era regime training
- `training.regime_pre_crisis_2000_2007_archive` – Pre-crisis historical regime
- `training.regime_recovery_2010_2016_archive` – Recovery era regime
- `training.regime_trade_war_2017_2019_archive` – Trade war era regime
- `training.regime_crisis_2008_archive` – Financial crisis regime

**Schema Requirements**:
- Must include `date DATE NOT NULL`
- Must include target columns: `target_1w`, `target_1m`, `target_3m`, `target_6m`, `target_12m` (FLOAT64)
- All feature columns must match `features.general_master_daily` schema
- Must include `training_weight INT64 NOT NULL`
- Must include `market_regime STRING NOT NULL`
- Identical column order across all horizon tables

**Partitioning**: Partition by `date`  
**Clustering**: Cluster by `market_regime`

### 4. `predictions`

**Purpose**: Model outputs and forecasts for production use.

**Responsibilities**:
- Store daily predictions from Vertex AI models
- Include quantiles (P10, P50, P90) and point forecasts
- Store BUY/WAIT/MONITOR signals
- Include feature attributions (SHAP values)

**Write Access**: Prediction serving scripts  
**Read Access**: Dashboard API, monitoring scripts

**Example Tables**:
- `predictions.horizon_1w_production` – 1-week horizon forecasts
- `predictions.horizon_1m_production` – 1-month horizon forecasts
- `predictions.horizon_3m_production` – 3-month horizon forecasts
- `predictions.horizon_6m_production` – 6-month horizon forecasts
- `predictions.horizon_12m_production` – 12-month horizon forecasts
- `predictions.signal_all_horizons_production` – Multi-horizon signals

**Schema Requirements**:
- Must include `date DATE NOT NULL`
- Must include `model_name STRING NOT NULL`
- Must include `p10 FLOAT64`, `p50 FLOAT64`, `p90 FLOAT64`
- Must include `point_prediction FLOAT64`
- Must include `buy_wait_monitor STRING`
- Must include `shap_top_factor STRING` and `shap_top_factor_contrib FLOAT64`
- Must include `ingest_timestamp TIMESTAMP NOT NULL`

**Partitioning**: Partition by `date`  
**Clustering**: Cluster by `model_name`

### 5. `monitoring`

**Purpose**: Metrics, logs, and health checks for data and models.

**Responsibilities**:
- Track data quality metrics (freshness, null rates, duplicates)
- Monitor model performance (MAPE, MAE, R²)
- Track feature drift and data anomalies
- Store alert logs and audit trails

**Write Access**: Monitoring scripts, validation scripts  
**Read Access**: Dashboard, alerting systems

**Example Tables**:
- `monitoring.data_quality_daily` – Daily data quality metrics
- `monitoring.model_performance_daily` – Daily model performance metrics
- `monitoring.feature_drift_daily` – Feature distribution drift tracking
- `monitoring.dedup_conflicts` – Deduplication conflict audit log
- `monitoring.ingestion_logs` – Ingestion job execution logs

**Schema Requirements**:
- Must include `date DATE NOT NULL` or `timestamp TIMESTAMP NOT NULL`
- Include table/column names for tracking
- Include metric values and thresholds
- Include alert flags and resolution status

**Partitioning**: Partition by `date` or `timestamp`  
**Clustering**: Cluster by table/column being monitored

### 6. `archive`

**Purpose**: Time-stamped snapshots of legacy tables and historical regimes.

**Responsibilities**:
- Store backups before migration
- Preserve historical regime training data
- Maintain legacy table snapshots for rollback
- Archive deprecated datasets

**Write Access**: Migration scripts, backup scripts  
**Read Access**: Read-only for historical analysis

**Example Tables**:
- `archive.legacy_nov12_2025_{original_table_name}` – Pre-migration snapshots
- `archive.regime_historical_{regime_name}_{date}` – Historical regime data
- `archive.backup_{table_name}_{timestamp}` – Point-in-time backups

**Schema Requirements**:
- Preserve original schema exactly
- Include archive metadata: `archived_date DATE`, `original_location STRING`
- No modifications to archived data

**Partitioning**: Preserve original partitioning  
**Clustering**: Preserve original clustering

## Dataset Creation Script

```sql
-- Create new datasets with proper IAM roles
CREATE SCHEMA IF NOT EXISTS `cbi-v14.raw_intelligence`
OPTIONS(
  description='Landing zone for ingestion scripts - raw unprocessed data',
  location='us-central1'
);

CREATE SCHEMA IF NOT EXISTS `cbi-v14.features`
OPTIONS(
  description='Engineered feature datasets for model training',
  location='us-central1'
);

CREATE SCHEMA IF NOT EXISTS `cbi-v14.training`
OPTIONS(
  description='Finalized training tables for each horizon and regime',
  location='us-central1'
);

CREATE SCHEMA IF NOT EXISTS `cbi-v14.predictions`
OPTIONS(
  description='Model outputs and forecasts for production',
  location='us-central1'
);

CREATE SCHEMA IF NOT EXISTS `cbi-v14.monitoring`
OPTIONS(
  description='Metrics, logs, and health checks for data and models',
  location='us-central1'
);

CREATE SCHEMA IF NOT EXISTS `cbi-v14.archive`
OPTIONS(
  description='Time-stamped snapshots of legacy tables and historical regimes',
  location='us-central1'
);
```

## IAM Roles and Permissions

### Service Accounts

- **Ingestion Service Account**: `cbi-v14-ingestion@cbi-v14.iam.gserviceaccount.com`
  - Write: `raw_intelligence.*`
  - Read: None (write-only for ingestion)

- **Feature Engineering Service Account**: `cbi-v14-features@cbi-v14.iam.gserviceaccount.com`
  - Read: `raw_intelligence.*`
  - Write: `features.*`

- **Training Service Account**: `cbi-v14-training@cbi-v14.iam.gserviceaccount.com`
  - Read: `features.*`
  - Write: `training.*`

- **Prediction Service Account**: `cbi-v14-predictions@cbi-v14.iam.gserviceaccount.com`
  - Read: `features.*`, `training.*`
  - Write: `predictions.*`

- **Monitoring Service Account**: `cbi-v14-monitoring@cbi-v14.iam.gserviceaccount.com`
  - Read: All datasets (read-only)
  - Write: `monitoring.*`

## Migration Strategy

1. **Create new datasets** (Phase 1)
2. **Migrate raw intelligence** (Phase 2)
3. **Build feature tables** (Phase 3)
4. **Build training tables** (Phase 4)
5. **Shadow run validation** (Phase 5)
6. **Cutover** (Phase 6)
7. **Archive legacy** (Phase 7)

See `MASTER_EXECUTION_PLAN.md` for detailed migration steps.

## References

- See `NAMING_CONVENTION_SPEC.md` for table naming rules
- See `DATA_LINEAGE_MAP.md` for data flow documentation
- See `ROLLBACK_PROCEDURE.md` for rollback instructions

