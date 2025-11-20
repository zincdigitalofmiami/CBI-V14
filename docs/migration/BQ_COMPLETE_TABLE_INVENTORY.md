---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# BigQuery Complete Table Inventory - What Needs to Be Added
**Date:** November 19, 2025  
**Status:** COMPREHENSIVE LIST - All Tables/Views/Features Required  
**Based On:** Staging Files (19 files) + Join Spec + Schema Plans + News Integration

---

## 📊 EXECUTIVE SUMMARY

**Total Required:**
- **Datasets**: 12 core datasets
- **Tables**: 60+ tables (from staging + schema + news)
- **Views**: 10+ views (for dashboard/API)
- **Staging Files to Load**: 19 parquet files (523,291 rows)

---

## 1. STAGING FILES → BIGQUERY TABLES MAPPING

### Direct Staging File Loads (19 files)

| Staging File | Rows | Target Dataset | Target Table | Partition Key | Cluster Keys | Status |
|--------------|------|----------------|--------------|---------------|--------------|--------|
| `yahoo_historical_prefixed.parquet` | 6,380 | `market_data` | `yahoo_historical_prefixed` | `date` | `symbol` | ❌ Not loaded |
| `fred_macro_expanded.parquet` | 9,452 | `raw_intelligence` | `fred_macro_expanded` | `date` | None | ❌ Not loaded |
| `weather_granular.parquet` | 9,438 | `raw_intelligence` | `weather_granular` | `date` | `region` | ❌ Not loaded |
| `cftc_commitments.parquet` | 522 | `raw_intelligence` | `cftc_commitments` | `date` | `commodity` | ❌ Not loaded |
| `alpha_vantage_features.parquet` | 10,719 | `raw_intelligence` | `alpha_vantage_features` | `date` | `symbol` | ❌ Not loaded |
| `volatility_features.parquet` | 9,069 | `raw_intelligence` | `volatility_features` | `date` | None | ❌ Not loaded |
| `palm_oil_daily.parquet` | 1,269 | `raw_intelligence` | `palm_oil_daily` | `date` | None | ❌ Not loaded |
| `policy_trump_signals.parquet` | 25 | `raw_intelligence` | `policy_trump_signals` | `date` | None | ❌ Not loaded |
| `usda_reports_granular.parquet` | 6 | `raw_intelligence` | `usda_reports_granular` | `date` | None | ❌ Not loaded |
| `eia_energy_granular.parquet` | 828 | `raw_intelligence` | `eia_energy_granular` | `date` | None | ❌ Not loaded |
| `eia_biofuels_2010_2025.parquet` | 828 | `raw_intelligence` | `eia_biofuels` | `date` | None | ❌ Not loaded |
| `es_futures_daily.parquet` | 6,308 | `market_data` | `es_futures_daily` | `date` | `symbol` | ❌ Not loaded |
| `es_daily_aggregated.parquet` | 21 | `market_data` | `es_daily_aggregated` | `date` | None | ❌ Not loaded |
| `mes_futures_daily.parquet` | 2,036 | `market_data` | `mes_futures_daily` | `date` | `symbol` | ❌ Not loaded |
| `mes_daily_aggregated.parquet` | 2,036 | `market_data` | `mes_daily_aggregated` | `date` | None | ❌ Not loaded |
| `mes_15min.parquet` | 229,160 | `market_data` | `mes_15min` | `date` | `symbol` | ❌ Not loaded |
| `mes_15min_features.parquet` | 229,160 | `market_data` | `mes_15min_features` | `date` | `symbol` | ❌ Not loaded |
| `mes_confirmation_features.parquet` | 2,036 | `market_data` | `mes_confirmation_features` | `date` | None | ❌ Not loaded |
| `zl_daily_aggregated.parquet` | 3,998 | `market_data` | `zl_daily_aggregated` | `date` | None | ❌ Not loaded |

**Total Rows to Load**: 523,291

---

## 2. DATASET: `market_data` (Futures OHLCV Data)

### Tables Required (from PRODUCTION_READY_BQ_SCHEMA.sql)

| Table Name | Source | Rows (Expected) | Partition | Cluster | Status |
|------------|--------|-----------------|-----------|---------|--------|
| `databento_futures_ohlcv_1m` | DataBento live | Ongoing | `DATE(ts_event)` | `root, is_spread` | ❌ Not created |
| `databento_futures_ohlcv_1d` | DataBento daily | Ongoing | `date` | `root, symbol` | ❌ Not created |
| `databento_futures_continuous_1d` | Generated | Ongoing | `date` | `root, cont_id` | ❌ Not created |
| `roll_calendar` | Generated | ~500 | `roll_date` | `root, method` | ❌ Not created |
| `futures_curve_1d` | DataBento | Ongoing | `date` | `root, contract` | ❌ Not created |
| `cme_indices_eod` | ScrapeCreators | Daily | `date` | `index_type, product` | ❌ Not created |
| `fx_daily` | CME/FRED/Yahoo | Ongoing | `date` | `pair, source` | ❌ Not created |
| `orderflow_1m` | DataBento | Ongoing | `DATE(ts_minute)` | `root` | ❌ Not created |
| `yahoo_historical_prefixed` | Staging file | 6,380 | `date` | `symbol` | ❌ Not loaded |
| `es_futures_daily` | Staging file | 6,308 | `date` | `symbol` | ❌ Not loaded |
| `es_daily_aggregated` | Staging file | 21 | `date` | None | ❌ Not loaded |
| `mes_futures_daily` | Staging file | 2,036 | `date` | `symbol` | ❌ Not loaded |
| `mes_daily_aggregated` | Staging file | 2,036 | `date` | None | ❌ Not loaded |
| `mes_15min` | Staging file | 229,160 | `date` | `symbol` | ❌ Not loaded |
| `mes_15min_features` | Staging file | 229,160 | `date` | `symbol` | ❌ Not loaded |
| `mes_confirmation_features` | Staging file | 2,036 | `date` | None | ❌ Not loaded |
| `zl_daily_aggregated` | Staging file | 3,998 | `date` | None | ❌ Not loaded |

**Total**: 17 tables

---

## 3. DATASET: `raw_intelligence` (External API Data)

### Tables Required

| Table Name | Source | Rows (Expected) | Partition | Cluster | Status |
|------------|--------|-----------------|-----------|---------|--------|
| `fred_macro_expanded` | Staging file | 9,452 | `date` | None | ❌ Not loaded |
| `weather_granular` | Staging file | 9,438 | `date` | `region` | ❌ Not loaded |
| `cftc_commitments` | Staging file | 522 | `date` | `commodity` | ❌ Not loaded |
| `alpha_vantage_features` | Staging file | 10,719 | `date` | `symbol` | ❌ Not loaded |
| `volatility_features` | Staging file | 9,069 | `date` | None | ❌ Not loaded |
| `palm_oil_daily` | Staging file | 1,269 | `date` | None | ❌ Not loaded |
| `policy_trump_signals` | Staging file | 25 | `date` | None | ❌ Not loaded |
| `usda_reports_granular` | Staging file | 6 | `date` | None | ❌ Not loaded |
| `eia_energy_granular` | Staging file | 828 | `date` | None | ❌ Not loaded |
| `eia_biofuels` | Staging file | 828 | `date` | None | ❌ Not loaded |
| `intelligence_news_alpha_raw_daily` | Alpha Vantage API | Ongoing | `DATE(time_published)` | `source` | ❌ Not created |
| `intelligence_news_alpha_classified_daily` | GPT classification | Ongoing | `DATE(time_published)` | `primary_topic` | ❌ Not created |
| `news_scrapecreators_google_search` | ScrapeCreators API | Ongoing | `DATE(collection_date)` | `bucket` | ❌ Not created |
| `cme_cvol_indices` | ScrapeCreators | Daily | `date` | `index_type` | ❌ Not created |

**Total**: 14 tables

---

## 4. DATASET: `features` (Master Features Table)

### Tables Required

| Table Name | Source | Rows (Expected) | Partition | Cluster | Status |
|------------|--------|-----------------|-----------|---------|--------|
| `master_features` | Join executor output | 6,380+ | `date` | `symbol, market_regime` | ❌ Not created |
| `mes_volume_profile` | MES features | 2,036 | `date` | `symbol` | ❌ Not created |
| `mes_pivots` | MES features | 2,036 | `date` | `symbol` | ❌ Not created |
| `mes_fibonacci` | MES features | 2,036 | `date` | `symbol` | ❌ Not created |
| `mes_garch_vol` | MES volatility | 2,036 | `date` | `symbol` | ❌ Not created |
| `mes_ms_egarch_vol` | MES MS-EGARCH | 2,036 | `date` | `symbol` | ❌ Not created |

**Total**: 6 tables

**Key Table**: `master_features` - THE canonical table with 400+ columns from all joined sources

---

## 5. DATASET: `training` (Training Datasets)

### Tables Required

| Table Name | Source | Rows (Expected) | Partition | Cluster | Status |
|------------|--------|-----------------|-----------|---------|--------|
| `zl_training_prod_allhistory_1w` | From master_features | 1,472 | `date` | `regime` | ⚠️ Exists, empty |
| `zl_training_prod_allhistory_1m` | From master_features | 1,404 | `date` | `regime` | ⚠️ Exists, empty |
| `zl_training_prod_allhistory_3m` | From master_features | 1,475 | `date` | `regime` | ⚠️ Exists, empty |
| `zl_training_prod_allhistory_6m` | From master_features | 1,473 | `date` | `regime` | ⚠️ Exists, empty |
| `zl_training_prod_allhistory_12m` | From master_features | 1,473 | `date` | `regime` | ⚠️ Exists, empty |
| `mes_training_prod_allhistory_1min` | From MES features | TBD | `date` | `regime` | ⚠️ Exists, empty |
| `mes_training_prod_allhistory_5min` | From MES features | TBD | `date` | `regime` | ⚠️ Exists, empty |
| `mes_training_prod_allhistory_15min` | From MES features | TBD | `date` | `regime` | ⚠️ Exists, empty |
| `mes_training_prod_allhistory_30min` | From MES features | TBD | `date` | `regime` | ⚠️ Exists, empty |
| `mes_training_prod_allhistory_1hr` | From MES features | TBD | `date` | `regime` | ⚠️ Exists, empty |
| `mes_training_prod_allhistory_4hr` | From MES features | TBD | `date` | `regime` | ⚠️ Exists, empty |
| `mes_training_prod_allhistory_1d` | From MES features | TBD | `date` | `regime` | ⚠️ Exists, empty |
| `mes_training_prod_allhistory_7d` | From MES features | TBD | `date` | `regime` | ⚠️ Exists, empty |
| `mes_training_prod_allhistory_30d` | From MES features | TBD | `date` | `regime` | ⚠️ Exists, empty |
| `mes_training_prod_allhistory_3m` | From MES features | TBD | `date` | `regime` | ⚠️ Exists, empty |
| `mes_training_prod_allhistory_6m` | From MES features | TBD | `date` | `regime` | ⚠️ Exists, empty |
| `mes_training_prod_allhistory_12m` | From MES features | TBD | `date` | `regime` | ⚠️ Exists, empty |
| `regime_calendar` | Registry file | 13,102 | `date` | `regime` | ⚠️ Exists, empty |
| `regime_weights` | Registry file | 11 | None | None | ⚠️ Exists, empty |

**Total**: 19 tables (all exist but empty)

---

## 6. DATASET: `signals` (Derived Signals)

### Tables Required

| Table Name | Source | Rows (Expected) | Partition | Cluster | Status |
|------------|--------|-----------------|-----------|---------|--------|
| `hidden_relationship_signals` | News aggregation | Daily | `date` | None | ❌ Not created |
| `big_eight_live` | Calculated | Daily | `date` | None | ❌ Not created |
| `crush_oilshare_daily` | Calculated | Daily | `date` | None | ❌ Not created |
| `calendar_spreads_1d` | Calculated | Daily | `date` | `root` | ❌ Not created |
| `energy_proxies_daily` | Calculated | Daily | `date` | None | ❌ Not created |

**Total**: 5 tables

**Note**: `signals` dataset may not exist - needs to be created

---

## 7. DATASET: `regimes` (Regime Classifications)

### Tables Required

| Table Name | Source | Rows (Expected) | Partition | Cluster | Status |
|------------|--------|-----------------|-----------|---------|--------|
| `regime_calendar` | Registry file | 13,102 | `date` | `regime` | ⚠️ May be in training dataset |
| `regime_weights` | Registry file | 11 | None | None | ⚠️ May be in training dataset |

**Total**: 2 tables

**Note**: Currently in `training` dataset - may need to move to `regimes` dataset

---

## 8. DATASET: `predictions` (Model Outputs)

### Tables Required

| Table Name | Source | Rows (Expected) | Partition | Cluster | Status |
|------------|--------|-----------------|-----------|---------|--------|
| `zl_predictions_latest` | Model outputs | Daily | `prediction_date` | `horizon` | ❌ Not created |
| `mes_predictions_view_only` | Model outputs | Daily | `prediction_date` | `horizon` | ❌ Not created |
| `forecast_metadata` | Model metadata | Daily | `prediction_date` | `model_name` | ❌ Not created |

**Total**: 3 tables

---

## 9. DATASET: `monitoring` (Data Quality & Performance)

### Tables Required

| Table Name | Source | Rows (Expected) | Partition | Cluster | Status |
|------------|--------|-----------------|-----------|---------|--------|
| `data_quality_checks` | Validation scripts | Ongoing | `DATE(check_timestamp)` | `table_name` | ❌ Not created |
| `model_performance` | Model metrics | Ongoing | `tracking_date` | `model_name` | ⚠️ Exists, empty |
| `ingestion_health` | Ingestion logs | Ongoing | `DATE(run_timestamp)` | `source` | ❌ Not created |
| `alpha_news_cursor` | News ingestion | 1 | None | None | ❌ Not created |

**Total**: 4 tables

---

## 10. DATASET: `api` (Dashboard Views)

### Views Required

| View Name | Source Table | Purpose | Status |
|-----------|-------------|---------|--------|
| `vw_zl_dashboard` | `features.master_features` | Public ZL view | ❌ Not created |
| `vw_mes_private` | `features.master_features` | Private MES view | ❌ Not created |
| `vw_system_health` | `monitoring.*` | Monitoring view | ❌ Not created |
| `vw_zl_predictions_latest` | `predictions.zl_predictions_latest` | Latest predictions | ❌ Not created |

**Total**: 4 views

---

## 11. DATASET: `dim` (Reference Data)

### Tables Required

| Table Name | Source | Rows (Expected) | Status |
|------------|--------|-----------------|--------|
| `symbols` | Static | ~50 | ❌ Not created |
| `regions` | Static | ~20 | ❌ Not created |
| `data_sources` | Static | ~30 | ❌ Not created |
| `feature_metadata` | Static | ~400 | ❌ Not created |

**Total**: 4 tables

---

## 12. DATASET: `ops` (Operations & Logs)

### Tables Required

| Table Name | Source | Rows (Expected) | Partition | Cluster | Status |
|------------|--------|-----------------|-----------|---------|--------|
| `ingestion_runs` | Ingestion scripts | Ongoing | `DATE(started_at)` | `source, status` | ❌ Not created |
| `sync_logs` | Sync scripts | Ongoing | `DATE(sync_date)` | `table_name` | ❌ Not created |
| `error_logs` | All scripts | Ongoing | `DATE(error_timestamp)` | `script_name` | ❌ Not created |

**Total**: 3 tables

---

## 13. DATASET: `neural` (Neural Network Features)

### Tables/Views Required

| Name | Type | Source | Status |
|------|------|--------|--------|
| `neural_features` | TABLE | From master_features | ❌ Not created |
| `vw_big_eight_signals` | VIEW | From signals | ⚠️ May exist as view |

**Total**: 1-2 objects

---

## 📋 COMPLETE INVENTORY SUMMARY

### By Dataset

| Dataset | Tables | Views | Total | Status |
|---------|--------|-------|-------|--------|
| `market_data` | 17 | 0 | 17 | ❌ Most not created |
| `raw_intelligence` | 14 | 0 | 14 | ⚠️ Some exist, empty |
| `features` | 6 | 0 | 6 | ❌ Not created |
| `training` | 19 | 0 | 19 | ⚠️ All exist, empty |
| `signals` | 5 | 0 | 5 | ❌ Dataset may not exist |
| `regimes` | 2 | 0 | 2 | ⚠️ May be in training |
| `predictions` | 3 | 0 | 3 | ❌ Not created |
| `monitoring` | 4 | 0 | 4 | ⚠️ 1 exists, empty |
| `api` | 0 | 4 | 4 | ❌ Not created |
| `dim` | 4 | 0 | 4 | ❌ Not created |
| `ops` | 3 | 0 | 3 | ❌ Not created |
| `neural` | 1-2 | 0 | 1-2 | ❌ Not created |
| **TOTAL** | **82-83** | **4** | **86-87** | |

---

## 🔥 PRIORITY LOAD ORDER

### Phase 1: Core Staging Files (IMMEDIATE)

1. `yahoo_historical_prefixed.parquet` → `market_data.yahoo_historical_prefixed`
2. `fred_macro_expanded.parquet` → `raw_intelligence.fred_macro_expanded`
3. `weather_granular.parquet` → `raw_intelligence.weather_granular`
4. `cftc_commitments.parquet` → `raw_intelligence.cftc_commitments`
5. `alpha_vantage_features.parquet` → `raw_intelligence.alpha_vantage_features`

### Phase 2: Remaining Staging Files

6. `volatility_features.parquet` → `raw_intelligence.volatility_features`
7. `palm_oil_daily.parquet` → `raw_intelligence.palm_oil_daily`
8. `policy_trump_signals.parquet` → `raw_intelligence.policy_trump_signals`
9. `usda_reports_granular.parquet` → `raw_intelligence.usda_reports_granular`
10. `eia_energy_granular.parquet` → `raw_intelligence.eia_energy_granular`
11. `eia_biofuels_2010_2025.parquet` → `raw_intelligence.eia_biofuels`
12. All MES files → `market_data.*`
13. All ES files → `market_data.*`
14. `zl_daily_aggregated.parquet` → `market_data.zl_daily_aggregated`

### Phase 3: Build Derived Tables

15. Run join_executor → Create `features.master_features`
16. Populate training tables from `master_features`
17. Create signal tables from calculations
18. Create regime tables from registry files

### Phase 4: News & API Integration

19. Execute news DDL → Create news tables
20. Create API views for dashboard
21. Set up monitoring tables

---

## 📝 DDL FILES TO EXECUTE

1. `sql/schemas/PRODUCTION_READY_BQ_SCHEMA.sql` - Core schema (45+ tables)
2. `config/bigquery/bigquery-sql/create_alpha_news_tables.sql` - News tables (4 tables)
3. `config/bigquery/migration/01_create_datasets.sql` - Verify datasets
4. `config/bigquery/migration/02_create_core_tables.sql` - Core tables

---

## ✅ VALIDATION CHECKLIST

After loading, verify:
- [ ] All 19 staging files loaded (523,291 total rows)
- [ ] `features.master_features` has 400+ columns
- [ ] Training tables have proper date range (2000-2025)
- [ ] Training tables have 7+ regimes
- [ ] No placeholder data (regime='allhistory', weight=1)
- [ ] All datasets in `us-central1`
- [ ] All tables properly partitioned
- [ ] All tables properly clustered

---

**Total Objects to Create/Load**: 86-87 tables + 4 views = **90-91 objects**

**Total Rows to Load**: 523,291 (from staging) + ongoing (from APIs)

