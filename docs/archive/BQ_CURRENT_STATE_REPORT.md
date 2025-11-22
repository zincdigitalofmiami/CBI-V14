---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# BigQuery Current State Report
**Date:** 2025-11-18 18:37:11
**Project:** cbi-v14

---

## Dataset Analysis

- **Expected:** 11 datasets
- **Current:** 43 datasets
- **Existing:** 8 datasets
- **Missing:** 3 datasets
- **Extra:** 35 datasets (legacy)

### Missing Datasets (Need Creation)

- ❌ `dim`
- ❌ `drivers`
- ❌ `ops`

### Extra Datasets (Legacy/Backup)

- ⚠️  `api`
- ⚠️  `archive`
- ⚠️  `archive_backup_20251115`
- ⚠️  `archive_consolidation_nov6`
- ⚠️  `bkp`
- ⚠️  `curated`
- ⚠️  `dashboard`
- ⚠️  `dashboard_backup_20251115_final`
- ⚠️  `dashboard_tmp`
- ⚠️  `deprecated`
- ⚠️  `export_evaluated_data_items_cbi_v14_automl_pilot_1w_2025_10_28T10_08_35_327Z`
- ⚠️  `features_backup_20251115`
- ⚠️  `features_backup_20251117`
- ⚠️  `forecasting_data_warehouse`
- ⚠️  `forecasting_data_warehouse_backup_20251117`
- ⚠️  `model_backups_oct27`
- ⚠️  `models`
- ⚠️  `models_v4`
- ⚠️  `models_v4_backup_20251117`
- ⚠️  `models_v5`
- ⚠️  `monitoring_backup_20251115`
- ⚠️  `performance`
- ⚠️  `predictions`
- ⚠️  `predictions_backup_20251115`
- ⚠️  `predictions_uc1`
- ⚠️  `raw`
- ⚠️  `raw_intelligence_backup_20251115`
- ⚠️  `raw_intelligence_backup_20251117`
- ⚠️  `staging`
- ⚠️  `staging_ml`
- ⚠️  `training_backup_20251115`
- ⚠️  `training_backup_20251117`
- ⚠️  `vegas_intelligence`
- ⚠️  `weather`
- ⚠️  `yahoo_finance_comprehensive`

## Table Analysis by Dataset

- **Expected Total:** 55 tables
- **Current Total:** 654 tables

### Dataset: `dim`

- Expected: 3 tables
- Existing: 0 tables
- Missing: 3 tables
- Extra: 0 tables

**Missing Tables:**

- ❌ `dim.crush_conversion_factors`
- ❌ `dim.instrument_metadata`
- ❌ `dim.production_weights`

### Dataset: `drivers`

- Expected: 2 tables
- Existing: 0 tables
- Missing: 2 tables
- Extra: 0 tables

**Missing Tables:**

- ❌ `drivers.meta_drivers`
- ❌ `drivers.primary_drivers`

### Dataset: `features`

- Expected: 1 tables
- Existing: 0 tables
- Missing: 1 tables
- Extra: 4 tables

**Missing Tables:**

- ❌ `features.master_features`

### Dataset: `market_data`

- Expected: 9 tables
- Existing: 0 tables
- Missing: 9 tables
- Extra: 4 tables

**Missing Tables:**

- ❌ `market_data.cme_indices_eod`
- ❌ `market_data.databento_futures_continuous_1d`
- ❌ `market_data.databento_futures_ohlcv_1d`
- ❌ `market_data.databento_futures_ohlcv_1m`
- ❌ `market_data.futures_curve_1d`
- ❌ `market_data.fx_daily`
- ❌ `market_data.orderflow_1m`
- ❌ `market_data.roll_calendar`
- ❌ `market_data.yahoo_zl_historical_2000_2010`

### Dataset: `monitoring`

- Expected: 1 tables
- Existing: 0 tables
- Missing: 1 tables
- Extra: 1 tables

**Missing Tables:**

- ❌ `monitoring.model_performance`

### Dataset: `neural`

- Expected: 1 tables
- Existing: 0 tables
- Missing: 1 tables
- Extra: 1 tables

**Missing Tables:**

- ❌ `neural.feature_vectors`

### Dataset: `ops`

- Expected: 2 tables
- Existing: 0 tables
- Missing: 2 tables
- Extra: 0 tables

**Missing Tables:**

- ❌ `ops.data_quality_events`
- ❌ `ops.ingestion_runs`

### Dataset: `raw_intelligence`

- Expected: 10 tables
- Existing: 0 tables
- Missing: 10 tables
- Extra: 7 tables

**Missing Tables:**

- ❌ `raw_intelligence.cftc_positioning`
- ❌ `raw_intelligence.eia_biofuels`
- ❌ `raw_intelligence.fred_economic`
- ❌ `raw_intelligence.news_bucketed`
- ❌ `raw_intelligence.news_intelligence`
- ❌ `raw_intelligence.policy_events`
- ❌ `raw_intelligence.usda_granular`
- ❌ `raw_intelligence.volatility_daily`
- ❌ `raw_intelligence.weather_segmented`
- ❌ `raw_intelligence.weather_weighted`

### Dataset: `regimes`

- Expected: 1 tables
- Existing: 0 tables
- Missing: 1 tables
- Extra: 0 tables

**Missing Tables:**

- ❌ `regimes.market_regimes`

### Dataset: `signals`

- Expected: 6 tables
- Existing: 0 tables
- Missing: 6 tables
- Extra: 34 tables

**Missing Tables:**

- ❌ `signals.big_eight_live`
- ❌ `signals.calculated_signals`
- ❌ `signals.calendar_spreads_1d`
- ❌ `signals.crush_oilshare_daily`
- ❌ `signals.energy_proxies_daily`
- ❌ `signals.hidden_relationship_signals`

### Dataset: `training`

- Expected: 19 tables
- Existing: 7 tables
- Missing: 12 tables
- Extra: 11 tables

**Missing Tables:**

- ❌ `training.mes_training_prod_allhistory_12m`
- ❌ `training.mes_training_prod_allhistory_15min`
- ❌ `training.mes_training_prod_allhistory_1d`
- ❌ `training.mes_training_prod_allhistory_1hr`
- ❌ `training.mes_training_prod_allhistory_1min`
- ❌ `training.mes_training_prod_allhistory_30d`
- ❌ `training.mes_training_prod_allhistory_30min`
- ❌ `training.mes_training_prod_allhistory_3m`
- ❌ `training.mes_training_prod_allhistory_4hr`
- ❌ `training.mes_training_prod_allhistory_5min`
- ❌ `training.mes_training_prod_allhistory_6m`
- ❌ `training.mes_training_prod_allhistory_7d`

**Existing Tables:**

- ✅ `training.regime_calendar`
- ✅ `training.regime_weights`
- ✅ `training.zl_training_prod_allhistory_12m`
- ✅ `training.zl_training_prod_allhistory_1m`
- ✅ `training.zl_training_prod_allhistory_1w`
- ✅ `training.zl_training_prod_allhistory_3m`
- ✅ `training.zl_training_prod_allhistory_6m`

## Recommendations

### 1. Create Missing Datasets

Run the deployment script to create missing datasets:
```bash
./scripts/deployment/deploy_bq_schema.sh
```

### 2. Create Missing Tables

The schema deployment will create all missing tables.

### 3. Handle Legacy Datasets

Consider archiving or removing legacy datasets after migration:
- `archive` (can be removed after verification)
- `archive_backup_20251115` (can be removed after verification)
- `archive_consolidation_nov6` (can be removed after verification)
- `dashboard_backup_20251115_final` (can be removed after verification)
- `features_backup_20251115` (can be removed after verification)
- `features_backup_20251117` (can be removed after verification)
- `forecasting_data_warehouse_backup_20251117` (can be removed after verification)
- `model_backups_oct27` (can be removed after verification)
- `models_v4_backup_20251117` (can be removed after verification)
- `monitoring_backup_20251115` (can be removed after verification)
- `predictions_backup_20251115` (can be removed after verification)
- `raw_intelligence_backup_20251115` (can be removed after verification)
- `raw_intelligence_backup_20251117` (can be removed after verification)
- `training_backup_20251115` (can be removed after verification)
- `training_backup_20251117` (can be removed after verification)

---

## Status

**Status:** ❌ NOT READY - Missing datasets and/or tables

**Next Steps:**
1. Run `./scripts/deployment/deploy_bq_schema.sh`
2. Re-run this scanner to verify