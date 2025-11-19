# CBI-V14: Table Mapping Matrix

**Last Updated**: November 15, 2025 (Updated with Verification Audit Findings)
**Status**: AUTO-GENERATED FROM BIGQUERY INVENTORY + VERIFICATION AUDIT
**Source**: Direct BigQuery query + external drive scan + comprehensive verification audit

This document is automatically generated from the actual BigQuery table inventory and external drive contents, updated with findings from the November 15, 2025 comprehensive data verification audit.

## Verification Audit Summary (November 15, 2025)

**Total Data Verified:** 1,877,182 rows across 453 tables in 29 datasets

**Key Findings:**
- ✅ **No 0.5 placeholder pattern** detected in production price data
- ⚠️ **Training tables missing pre-2020 data** (all start from 2020, not 2000)
- ⚠️ **Regime assignments incomplete** (only 1-3 regimes per table, expected 7+)
- ⚠️ **Some join tables missing** (commodity_soybean_oil_prices, vix_data)
- ✅ **Historical data verified real** (5,236 rows from models_v4, no placeholders)
- ✅ **Yahoo Finance data verified** (801K rows total, 6,227 ZL rows, no placeholders)

**Critical Issues Found:**
1. `training.zl_training_prod_allhistory_1m`: All 1,404 rows have regime='allhistory' and weight=1 (placeholder values)
2. All training tables: Missing pre-2020 data (should start from 2000-01-01)
3. Missing join tables: `raw_intelligence.commodity_soybean_oil_prices`, `forecasting_data_warehouse.vix_data`

**See:** `COMPREHENSIVE_DATA_VERIFICATION_REPORT.md` and `VERIFICATION_ISSUES_FOUND.md` for full details.

---

## Live Data Feed Mapping (2025 Forward-Only Stream)

| Source | Old Path | New Target Table / File | Notes |
|--------|----------|-------------------------|-------|
| DataBento GLBX.MDP3 `ohlcv-1m` | (none – new feed) | **Local Parquet:** `TrainingData/live/{root}/1m/date=YYYY-MM-DD/part-*.parquet` | Forward-only minute bars (roots: ES,ZL,CL in Phase 1). Spread-filter and tick-size validation enforced before write. |
| DataBento GLBX.MDP3 `ohlcv-1m` | (none – new feed) | **Local Continuous:** `TrainingData/live_continuous/{root}/1m/date=YYYY-MM-DD/part-*.parquet` | Front-by-volume continuous series; consumed by master_features stitcher. |
| DataBento GLBX.MDP3 `ohlcv-1m` | (optional) | **BigQuery:** `market_data.databento_futures_ohlcv_1m_live` (DATE partitioned, clustered by root,symbol) | Mirror only if dashboard/api needs BQ read surface; otherwise skip. |
| DataBento GLBX.MDP3 `ohlcv-1d` | (generated via aggregation) | **BigQuery:** `market_data.databento_futures_ohlcv_1d` | Populated via daily aggregation of the 1m Parquet (or direct DataBento 1d); used by downstream signals. |
| Continuous front | Legacy `market_data.futures_ohlcv_1d` | **BigQuery:** `market_data.databento_futures_continuous_1d` + `market_data.roll_calendar` | Compatibility views keep old table names alive during cutover. |

**Integration Flow:** local stitcher merges historical Yahoo/DataBento aggregates with the new live Parquet, writes refreshed `TrainingData/exports/zl_training_*` files, then BigQuery features tables are updated via standard load scripts. Vercel dashboards read the resulting BQ views (they do not hit DataBento directly).

---

## Current BigQuery Inventory

### Dataset Summary

| Dataset | Tables | Views | Total Objects | Total Rows | Total Size (MB) |
|---------|--------|-------|---------------|------------|----------------|
| `api` | 1 | 2 | 3 | 0 | 0.00 |
| `archive` | 11 | 0 | 11 | 13,937 | 19.46 |
| `archive_consolidation_nov6` | 4 | 0 | 4 | 5,322 | 9.33 |
| `bkp` | 8 | 0 | 8 | 17,871 | 2.11 |
| `curated` | 2 | 28 | 30 | 16 | 0.00 |
| `dashboard` | 3 | 0 | 3 | 4 | 0.00 |
| `deprecated` | 2 | 1 | 3 | 376 | 0.10 |
| `export_evaluated_data_items_cbi_v14_automl_pilot_1w_2025_10_28T10_08_35_327Z` | 1 | 0 | 1 | 112 | 0.15 |
| `features` | 2 | 0 | 2 | 2,894 | 0.13 |
| `forecasting_data_warehouse` | 87 | 12 | 99 | 422,772 | 65.32 |
| `market_data` | 4 | 0 | 4 | 155,075 | 34.73 |
| `models` | 22 | 8 | 30 | 27,191 | 14.11 |
| `models_v4` | 78 | 15 | 93 | 198,922 | 60.19 |
| `monitoring` | 1 | 0 | 1 | 615 | 0.03 |
| `neural` | 0 | 1 | 1 | 0 | 0.00 |
| `performance` | 2 | 2 | 4 | 0 | 0.00 |
| `predictions` | 5 | 0 | 5 | 4 | 0.00 |
| `predictions_uc1` | 4 | 1 | 5 | 5 | 0.00 |
| `raw_intelligence` | 7 | 0 | 7 | 87,666 | 9.49 |
| `signals` | 1 | 33 | 34 | 6 | 0.00 |
| `staging` | 11 | 0 | 11 | 79,885 | 35.76 |
| `training` | 18 | 0 | 18 | 34,206 | 30.96 |
| `weather` | 1 | 0 | 1 | 3 | 0.00 |
| `yahoo_finance_comprehensive` | 10 | 0 | 10 | 801,199 | 186.56 |

---

### Detailed Table Inventory

#### Dataset: `api`

| Table/View Name | Type | Rows | Size (MB) | Created | Partitioning | Clustering | Description |
|-----------------|------|------|-----------|---------|---------------|------------|-------------|
| `current_forecasts` | TABLE | 0 | 0.00 | 2025-10-29 | None | None |  |
| `vw_market_intelligence` | VIEW | 0 | 0.00 | 2025-10-20 | None | None |  |
| `vw_ultimate_adaptive_signal_historical` | VIEW | 0 | 0.00 | 2025-11-15 | None | None |  |

#### Dataset: `archive`

| Table/View Name | Type | Rows | Size (MB) | Created | Partitioning | Clustering | Description |
|-----------------|------|------|-----------|---------|---------------|------------|-------------|
| `backup_20251115_prod_1m` | TABLE | 1,404 | 4.11 | 2025-11-15 | None | None |  |
| `legacy_20251114__models_v4__crisis_2008_historical` | TABLE | 253 | 0.07 | 2025-11-14 | None | None |  |
| `legacy_20251114__models_v4__pre_crisis_2000_2007_historical` | TABLE | 1,737 | 0.49 | 2025-11-14 | None | None |  |
| `legacy_20251114__models_v4__production_training_data_12m` | TABLE | 1,473 | 2.31 | 2025-11-14 | None | None |  |
| `legacy_20251114__models_v4__production_training_data_1m` | TABLE | 1,404 | 4.07 | 2025-11-14 | None | None |  |
| `legacy_20251114__models_v4__production_training_data_1w` | TABLE | 1,472 | 2.59 | 2025-11-14 | None | None |  |
| `legacy_20251114__models_v4__production_training_data_3m` | TABLE | 1,475 | 2.45 | 2025-11-14 | None | None |  |
| `legacy_20251114__models_v4__production_training_data_6m` | TABLE | 1,473 | 2.30 | 2025-11-14 | None | None |  |
| `legacy_20251114__models_v4__recovery_2010_2016_historical` | TABLE | 1,760 | 0.50 | 2025-11-14 | None | None |  |
| `legacy_20251114__models_v4__trade_war_2017_2019_historical` | TABLE | 754 | 0.21 | 2025-11-14 | None | None |  |
| `legacy_20251114__models_v4__trump_rich_2023_2025` | TABLE | 732 | 0.36 | 2025-11-14 | None | None |  |

#### Dataset: `archive_consolidation_nov6`

| Table/View Name | Type | Rows | Size (MB) | Created | Partitioning | Clustering | Description |
|-----------------|------|------|-----------|---------|---------------|------------|-------------|
| `production_1m_backup_20251105` | TABLE | 1,347 | 2.42 | 2025-11-06 | None | None |  |
| `production_1w_backup_20251105` | TABLE | 1,448 | 2.49 | 2025-11-06 | None | None |  |
| `production_3m_backup_20251105` | TABLE | 1,329 | 2.31 | 2025-11-06 | None | None |  |
| `production_6m_backup_20251105` | TABLE | 1,198 | 2.11 | 2025-11-06 | None | None |  |

#### Dataset: `bkp`

| Table/View Name | Type | Rows | Size (MB) | Created | Partitioning | Clustering | Description |
|-----------------|------|------|-----------|---------|---------------|------------|-------------|
| `crude_oil_prices_SAFETY_20251021_180706` | TABLE | 2,265 | 0.29 | 2025-10-21 | None | None |  |
| `economic_indicators_SAFETY_20251021_180706` | TABLE | 7,523 | 0.72 | 2025-10-21 | None | None |  |
| `news_intelligence_20251010T231740Z` | TABLE | 333 | 0.17 | 2025-10-10 | None | None |  |
| `soybean_oil_prices_20251010T231754Z` | TABLE | 525 | 0.06 | 2025-10-10 | None | None |  |
| `soybean_oil_prices_SAFETY_20251021_180706` | TABLE | 1,935 | 0.23 | 2025-10-21 | None | None |  |
| `soybean_oil_prices_backup_20251021_152417` | TABLE | 2,255 | 0.27 | 2025-10-21 | None | None |  |
| `soybean_oil_prices_backup_20251021_152537` | TABLE | 2,255 | 0.27 | 2025-10-21 | None | None |  |
| `volatility_data_20251010T231720Z` | TABLE | 780 | 0.10 | 2025-10-10 | None | None |  |

#### Dataset: `curated`

| Table/View Name | Type | Rows | Size (MB) | Created | Partitioning | Clustering | Description |
|-----------------|------|------|-----------|---------|---------------|------------|-------------|
| `region_station_map` | TABLE | 10 | 0.00 | 2025-10-14 | None | None |  |
| `region_weight_map` | TABLE | 6 | 0.00 | 2025-10-14 | None | None |  |
| `vw_biofuel_policy_us_daily` | VIEW | 0 | 0.00 | 2025-10-14 | None | None |  |
| `vw_cftc_positions_oilseeds_weekly` | VIEW | 0 | 0.00 | 2025-10-20 | None | None |  |
| `vw_cftc_soybean_oil_weekly` | VIEW | 0 | 0.00 | 2025-10-20 | None | None |  |
| `vw_client_insights_daily` | VIEW | 0 | 0.00 | 2025-10-13 | None | None |  |
| `vw_client_multi_horizon_forecast` | VIEW | 0 | 0.00 | 2025-10-13 | None | None |  |
| `vw_commodity_prices_daily` | VIEW | 0 | 0.00 | 2025-10-27 | None | None |  |
| `vw_crush_margins_daily` | VIEW | 0 | 0.00 | 2025-10-13 | None | None |  |
| `vw_dashboard_commodity_prices` | VIEW | 0 | 0.00 | 2025-10-27 | None | None |  |
| `vw_dashboard_fundamentals` | VIEW | 0 | 0.00 | 2025-10-13 | None | None |  |
| `vw_dashboard_weather_intelligence` | VIEW | 0 | 0.00 | 2025-10-27 | None | None |  |
| `vw_economic_daily` | VIEW | 0 | 0.00 | 2025-10-10 | None | None |  |
| `vw_fed_rates_realtime` | VIEW | 0 | 0.00 | 2025-10-27 | None | None |  |
| `vw_multi_source_intelligence_summary` | VIEW | 0 | 0.00 | 2025-10-27 | None | None |  |
| `vw_news_commodity_daily` | VIEW | 0 | 0.00 | 2025-10-14 | None | None |  |
| `vw_news_intel_daily` | VIEW | 0 | 0.00 | 2025-10-27 | None | None |  |
| `vw_palm_soy_spread_daily` | VIEW | 0 | 0.00 | 2025-10-13 | None | None |  |
| `vw_priority_indicators_daily` | VIEW | 0 | 0.00 | 2025-10-27 | None | None |  |
| `vw_social_intelligence` | VIEW | 0 | 0.00 | 2025-10-10 | None | None |  |
| `vw_soybean_oil_features_daily` | VIEW | 0 | 0.00 | 2025-10-11 | None | None |  |
| `vw_soybean_oil_quote` | VIEW | 0 | 0.00 | 2025-10-11 | None | None |  |
| `vw_treasury_daily` | VIEW | 0 | 0.00 | 2025-10-27 | None | None |  |
| `vw_usda_export_sales_soy_weekly` | VIEW | 0 | 0.00 | 2025-10-14 | None | None |  |
| `vw_volatility_daily` | VIEW | 0 | 0.00 | 2025-10-10 | None | None |  |
| `vw_weather_ar_daily` | VIEW | 0 | 0.00 | 2025-10-14 | None | None |  |
| `vw_weather_br_daily` | VIEW | 0 | 0.00 | 2025-10-14 | None | None |  |
| `vw_weather_daily` | VIEW | 0 | 0.00 | 2025-10-27 | None | None |  |
| `vw_weather_global_daily` | VIEW | 0 | 0.00 | 2025-10-27 | None | None |  |
| `vw_weather_usmw_daily` | VIEW | 0 | 0.00 | 2025-10-20 | None | None |  |

#### Dataset: `dashboard`

| Table/View Name | Type | Rows | Size (MB) | Created | Partitioning | Clustering | Description |
|-----------------|------|------|-----------|---------|---------------|------------|-------------|
| `performance_metrics` | TABLE | 4 | 0.00 | 2025-10-27 | None | None |  |
| `prediction_history` | TABLE | 0 | 0.00 | 2025-10-27 | None | None |  |
| `regime_history` | TABLE | 0 | 0.00 | 2025-10-27 | None | None |  |

#### Dataset: `deprecated`

| Table/View Name | Type | Rows | Size (MB) | Created | Partitioning | Clustering | Description |
|-----------------|------|------|-----------|---------|---------------|------------|-------------|
| `fct_zl_price_volatility_daily_legacy_20251009T114922` | VIEW | 0 | 0.00 | 2025-10-09 | None | None |  |
| `ice_trump_intelligence` | TABLE | 186 | 0.05 | 2025-10-12 | PARTITION BY timestamp | category |  |
| `ice_trump_intelligence_legacy_20251013` | TABLE | 190 | 0.05 | 2025-10-13 | PARTITION BY timestamp | category |  |

#### Dataset: `export_evaluated_data_items_cbi_v14_automl_pilot_1w_2025_10_28T10_08_35_327Z`

| Table/View Name | Type | Rows | Size (MB) | Created | Partitioning | Clustering | Description |
|-----------------|------|------|-----------|---------|---------------|------------|-------------|
| `evaluated_data_items` | TABLE | 112 | 0.15 | 2025-10-28 | None | None |  |

#### Dataset: `features`

| Table/View Name | Type | Rows | Size (MB) | Created | Partitioning | Clustering | Description |
|-----------------|------|------|-----------|---------|---------------|------------|-------------|
| `feature_metadata` | TABLE | 52 | 0.02 | 2025-11-14 | None | None |  |
| `market_regimes` | TABLE | 2,842 | 0.11 | 2025-11-14 | None | None |  |

#### Dataset: `forecasting_data_warehouse`

| Table/View Name | Type | Rows | Size (MB) | Created | Partitioning | Clustering | Description |
|-----------------|------|------|-----------|---------|---------------|------------|-------------|
| `ai_metadata_summary` | VIEW | 0 | 0.00 | 2025-11-03 | None | None |  |
| `all_commodity_prices` | TABLE | 62,717 | 16.70 | 2025-11-15 | None | None |  |
| `argentina_crisis_tracker` | TABLE | 10 | 0.00 | 2025-10-28 | None | None |  |
| `baltic_dry_index` | TABLE | 0 | 0.00 | 2025-11-13 | PARTITION BY time | None | Baltic Dry Index - Daily shipping rates indicator ... |
| `biofuel_policy` | TABLE | 62 | 0.01 | 2025-10-22 | None | None |  |
| `biofuel_prices` | TABLE | 354 | 0.04 | 2025-10-22 | None | None |  |
| `breaking_news_hourly` | TABLE | 560 | 0.18 | 2025-10-30 | None | None |  |
| `canola_oil_prices` | TABLE | 770 | 0.10 | 2025-10-22 | None | None |  |
| `cftc_cot` | TABLE | 944 | 0.13 | 2025-10-21 | None | None |  |
| `china_soybean_imports` | TABLE | 22 | 0.00 | 2025-10-28 | None | None |  |
| `cocoa_prices` | TABLE | 21 | 0.00 | 2025-10-23 | None | None |  |
| `copper_prices` | TABLE | 4,800 | 0.67 | 2025-11-12 | None | None |  |
| `corn_prices` | TABLE | 15,623 | 2.14 | 2025-10-27 | None | None |  |
| `cotton_prices` | TABLE | 21 | 0.00 | 2025-10-23 | None | None |  |
| `crude_oil_prices` | TABLE | 10,859 | 1.45 | 2025-10-22 | None | None |  |
| `currency_data` | TABLE | 59,187 | 5.70 | 2025-10-22 | None | None |  |
| `data_catalog` | TABLE | 18 | 0.00 | 2025-11-03 | None | None |  |
| `data_integration_status` | VIEW | 0 | 0.00 | 2025-11-03 | None | None |  |
| `economic_indicators` | TABLE | 72,553 | 6.37 | 2025-10-27 | None | None |  |
| `enhanced_feature_metadata` | TABLE | 52 | 0.03 | 2025-11-03 | None | None |  |
| `enso_climate_status` | TABLE | 0 | 0.00 | 2025-11-02 | None | None |  |
| `ers_oilcrops_monthly` | TABLE | 0 | 0.00 | 2025-11-02 | None | None |  |
| `event_restaurant_impact` | VIEW | 0 | 0.00 | 2025-11-05 | None | None |  |
| `feature_metadata` | TABLE | 52 | 0.02 | 2025-10-08 | None | None |  |
| `freight_logistics` | TABLE | 0 | 0.00 | 2025-11-05 | PARTITION BY date | None | Freight and logistics data including Baltic Dry In... |
| `futures_prices_barchart` | TABLE | 0 | 0.00 | 2025-11-02 | None | None |  |
| `futures_prices_cme_public` | TABLE | 0 | 0.00 | 2025-11-02 | None | None |  |
| `futures_prices_investing` | TABLE | 0 | 0.00 | 2025-11-02 | None | None |  |
| `futures_prices_marketwatch` | TABLE | 0 | 0.00 | 2025-11-02 | None | None |  |
| `futures_sentiment_tradingview` | TABLE | 0 | 0.00 | 2025-11-02 | None | None |  |
| `gold_prices` | TABLE | 11,555 | 1.51 | 2025-10-22 | None | None |  |
| `hourly_prices` | TABLE | 27 | 0.00 | 2025-11-05 | None | None |  |
| `industrial_demand_indicators` | TABLE | 3 | 0.00 | 2025-10-28 | None | None |  |
| `industry_intelligence_asa` | TABLE | 0 | 0.00 | 2025-11-02 | None | None |  |
| `job_execution_tracking` | TABLE | 1 | 0.00 | 2025-11-05 | None | None |  |
| `legislative_bills` | TABLE | 0 | 0.00 | 2025-11-02 | None | None |  |
| `market_analysis_correlations` | TABLE | 0 | 0.00 | 2025-11-02 | None | None |  |
| `metadata_completeness_check` | VIEW | 0 | 0.00 | 2025-11-03 | None | None |  |
| `model_interpretability_metadata` | TABLE | 0 | 0.00 | 2025-11-03 | None | None |  |
| `natural_gas_prices` | TABLE | 11,567 | 1.52 | 2025-10-22 | None | None |  |
| `neural_network_architecture_metadata` | TABLE | 4 | 0.00 | 2025-11-03 | None | None |  |
| `news_advanced` | TABLE | 223 | 1.93 | 2025-10-22 | None | None |  |
| `news_industry_brownfield` | TABLE | 0 | 0.00 | 2025-11-02 | None | None |  |
| `news_intelligence` | TABLE | 2,830 | 1.51 | 2025-10-27 | None | None |  |
| `news_market_farmprogress` | TABLE | 0 | 0.00 | 2025-11-02 | None | None |  |
| `news_reuters` | TABLE | 0 | 0.00 | 2025-11-02 | None | None |  |
| `news_ultra_aggressive` | TABLE | 33 | 0.21 | 2025-10-22 | None | None |  |
| `palm_oil_prices` | TABLE | 1,340 | 0.15 | 2025-10-27 | None | None |  |
| `policy_events_federalregister` | TABLE | 0 | 0.00 | 2025-11-02 | None | None |  |
| `policy_rfs_volumes` | TABLE | 0 | 0.00 | 2025-11-02 | None | None |  |
| `predictions_1m` | TABLE | 0 | 0.00 | 2025-11-01 | PARTITION BY as_of_timestamp | None |  |
| `rapeseed_oil_prices` | TABLE | 146 | 0.02 | 2025-10-22 | None | None |  |
| `realtime_prices` | TABLE | 56 | 0.00 | 2025-10-23 | None | None |  |
| `risk_free_rates` | TABLE | 496 | 0.03 | 2025-11-15 | None | None |  |
| `shap_drivers` | TABLE | 0 | 0.00 | 2025-11-01 | PARTITION BY as_of_timestamp | None |  |
| `signals_1w` | TABLE | 0 | 0.00 | 2025-11-01 | PARTITION BY as_of_timestamp | signal_name |  |
| `silver_prices` | TABLE | 4,798 | 0.67 | 2025-11-12 | None | None |  |
| `social_intelligence_unified` | TABLE | 4,673 | 1.14 | 2025-11-03 | None | None |  |
| `social_sentiment` | TABLE | 677 | 0.22 | 2025-10-22 | None | None |  |
| `soybean_meal_prices` | TABLE | 10,775 | 1.47 | 2025-10-22 | None | None |  |
| `soybean_oil_prices` | TABLE | 6,057 | 0.81 | 2025-10-27 | None | None |  |
| `soybean_oil_prices_backup_20251112_165404` | TABLE | 1,301 | 0.15 | 2025-11-12 | None | None |  |
| `soybean_oil_prices_historical_view` | VIEW | 0 | 0.00 | 2025-11-12 | None | None |  |
| `soybean_prices` | TABLE | 15,708 | 2.16 | 2025-10-27 | None | None |  |
| `sp500_prices` | TABLE | 10,579 | 1.43 | 2025-10-21 | None | None |  |
| `treasury_prices` | TABLE | 1,961 | 0.24 | 2025-10-15 | None | None |  |
| `trump_policy_intelligence` | TABLE | 468 | 0.15 | 2025-10-22 | None | None |  |
| `usd_index_prices` | TABLE | 11,636 | 1.42 | 2025-10-22 | None | None |  |
| `usda_crop_progress` | TABLE | 2,814 | 0.43 | 2025-11-06 | None | None |  |
| `usda_export_sales` | TABLE | 12 | 0.00 | 2025-10-22 | None | None |  |
| `usda_harvest_progress` | TABLE | 1,950 | 0.11 | 2025-10-22 | None | None |  |
| `usda_wasde_soy` | TABLE | 0 | 0.00 | 2025-11-02 | None | None |  |
| `vegas_casinos` | TABLE | 31 | 0.01 | 2025-11-05 | None | None |  |
| `vegas_cuisine_multipliers` | TABLE | 142 | 0.02 | 2025-11-05 | None | None |  |
| `vegas_events` | TABLE | 5 | 0.00 | 2025-11-05 | None | None |  |
| `vegas_export_list` | TABLE | 3,176 | 0.54 | 2025-11-05 | None | None |  |
| `vegas_fryers` | TABLE | 0 | 0.00 | 2025-11-05 | PARTITION BY ingested_at | None |  |
| `vegas_opportunity_scores` | VIEW | 0 | 0.00 | 2025-11-05 | None | None |  |
| `vegas_restaurants` | TABLE | 151 | 0.04 | 2025-11-05 | None | None |  |
| `vegas_scheduled_reports` | TABLE | 28 | 0.01 | 2025-11-05 | None | None |  |
| `vegas_shift_casinos` | TABLE | 440 | 0.09 | 2025-11-05 | None | None |  |
| `vegas_shift_restaurants` | TABLE | 1,233 | 0.21 | 2025-11-05 | None | None |  |
| `vegas_shifts` | TABLE | 148 | 0.02 | 2025-11-05 | None | None |  |
| `vegas_top_opportunities` | VIEW | 0 | 0.00 | 2025-11-05 | None | None |  |
| `vix_daily` | TABLE | 6,271 | 0.32 | 2025-10-22 | None | None |  |
| `volatility_data` | TABLE | 1,985 | 0.16 | 2025-10-04 | None | None |  |
| `vw_scrapecreator_economic_proxy` | VIEW | 0 | 0.00 | 2025-11-03 | None | None |  |
| `vw_scrapecreator_policy_signals` | VIEW | 0 | 0.00 | 2025-11-03 | None | None |  |
| `vw_scrapecreator_price_proxy` | VIEW | 0 | 0.00 | 2025-11-03 | None | None |  |
| `vw_scrapecreator_weather_proxy` | VIEW | 0 | 0.00 | 2025-11-03 | None | None |  |
| `weather_argentina_daily` | TABLE | 0 | 0.00 | 2025-10-22 | None | None |  |
| `weather_brazil_clean` | TABLE | 33 | 0.01 | 2025-10-27 | None | None |  |
| `weather_brazil_daily` | TABLE | 0 | 0.00 | 2025-10-22 | None | None |  |
| `weather_data` | TABLE | 14,434 | 1.73 | 2025-10-27 | None | None |  |
| `weather_us_midwest_clean` | TABLE | 64 | 0.01 | 2025-10-27 | None | None |  |
| `weather_us_midwest_daily` | TABLE | 0 | 0.00 | 2025-10-22 | None | None |  |
| `wheat_prices` | TABLE | 15,631 | 2.15 | 2025-10-22 | None | None |  |
| `yahoo_finance_enhanced` | TABLE | 48,685 | 9.18 | 2025-11-03 | None | None |  |
| `yahoo_finance_historical` | VIEW | 0 | 0.00 | 2025-11-12 | None | None |  |

#### Dataset: `market_data`

| Table/View Name | Type | Rows | Size (MB) | Created | Partitioning | Clustering | Description |
|-----------------|------|------|-----------|---------|---------------|------------|-------------|
| `_ARCHIVED_yahoo_finance_enhanced_20251102` | TABLE | 48,685 | 9.18 | 2025-11-03 | None | None |  |
| `hourly_prices` | TABLE | 309 | 0.02 | 2025-10-29 | None | None |  |
| `yahoo_finance_20yr_STAGING` | TABLE | 57,397 | 16.35 | 2025-11-06 | None | None |  |
| `yahoo_finance_enhanced` | TABLE | 48,684 | 9.18 | 2025-11-03 | None | None |  |

#### Dataset: `models`

| Table/View Name | Type | Rows | Size (MB) | Created | Partitioning | Clustering | Description |
|-----------------|------|------|-----------|---------|---------------|------------|-------------|
| `FINAL_TRAINING_DATASET_COMPLETE` | TABLE | 1,263 | 1.49 | 2025-10-24 | None | None |  |
| `complete_signals_features` | TABLE | 1,263 | 0.38 | 2025-10-22 | None | None |  |
| `enhanced_market_regimes` | TABLE | 2,842 | 0.11 | 2025-10-22 | None | None |  |
| `enhanced_news_proxy` | TABLE | 653 | 0.07 | 2025-10-22 | None | None |  |
| `enhanced_policy_features` | TABLE | 653 | 0.05 | 2025-10-22 | None | None |  |
| `ensemble_predictions` | VIEW | 0 | 0.00 | 2025-10-22 | None | None |  |
| `news_features_materialized` | TABLE | 13 | 0.00 | 2025-10-22 | None | None |  |
| `price_features_precomputed` | TABLE | 1,261 | 0.14 | 2025-10-27 | None | None |  |
| `sentiment_features_materialized` | TABLE | 581 | 0.06 | 2025-10-22 | None | None |  |
| `sentiment_features_precomputed` | TABLE | 604 | 0.02 | 2025-10-27 | None | None |  |
| `signals_master` | TABLE | 2,830 | 0.33 | 2025-10-22 | None | None |  |
| `tariff_features_materialized` | TABLE | 46 | 0.00 | 2025-10-22 | None | None |  |
| `training_complete_enhanced` | TABLE | 1,263 | 2.12 | 2025-10-23 | None | None |  |
| `training_data_complete_all_intelligence` | TABLE | 1,263 | 1.48 | 2025-10-24 | None | None |  |
| `training_data_with_currencies_verified` | TABLE | 1,263 | 1.44 | 2025-10-24 | None | None |  |
| `training_dataset` | TABLE | 1,263 | 0.60 | 2025-10-23 | None | None |  |
| `training_dataset_backup_20251023` | TABLE | 1,263 | 0.60 | 2025-10-23 | None | None |  |
| `training_dataset_enhanced` | TABLE | 1,263 | 1.65 | 2025-10-22 | None | None |  |
| `training_dataset_enhanced_v5` | TABLE | 1,251 | 1.13 | 2025-10-24 | None | None |  |
| `training_dataset_enriched` | VIEW | 0 | 0.00 | 2025-10-23 | None | None |  |
| `training_dataset_master` | TABLE | 1,289 | 0.40 | 2025-10-23 | None | None |  |
| `training_enhanced_final` | TABLE | 1,323 | 1.72 | 2025-10-22 | None | None |  |
| `vix_features_materialized` | TABLE | 2,717 | 0.27 | 2025-10-22 | None | None |  |
| `vw_crush_margins` | VIEW | 0 | 0.00 | 2025-10-30 | None | None |  |
| `vw_daily_news_features` | VIEW | 0 | 0.00 | 2025-10-23 | None | None |  |
| `vw_daily_social_features` | VIEW | 0 | 0.00 | 2025-10-23 | None | None |  |
| `vw_ensemble_predictions` | VIEW | 0 | 0.00 | 2025-10-22 | None | None |  |
| `vw_event_driven_features` | VIEW | 0 | 0.00 | 2025-10-30 | None | None |  |
| `vw_seasonality_features` | VIEW | 0 | 0.00 | 2025-10-30 | None | None |  |
| `weather_features_precomputed` | TABLE | 1,024 | 0.05 | 2025-10-27 | None | None |  |

#### Dataset: `models_v4`

| Table/View Name | Type | Rows | Size (MB) | Created | Partitioning | Clustering | Description |
|-----------------|------|------|-----------|---------|---------------|------------|-------------|
| `_ARCHIVED_archive_training_dataset_20251027_pre_update` | TABLE | 1,251 | 1.80 | 2025-11-03 | None | None | DEPRECATED - DO NOT USE |
| `_ARCHIVED_archive_training_dataset_DUPLICATES_20251027` | TABLE | 1,263 | 1.82 | 2025-11-03 | None | None | DEPRECATED - DO NOT USE |
| `_ARCHIVED_archive_training_dataset_super_enriched_20251027_final` | TABLE | 1,251 | 1.80 | 2025-11-03 | None | None | DEPRECATED - DO NOT USE |
| `_ARCHIVED_training_dataset_backup_20251028` | TABLE | 1,251 | 1.85 | 2025-11-03 | None | None | DEPRECATED - DO NOT USE |
| `_ARCHIVED_training_dataset_baseline_clean` | TABLE | 1,251 | 1.75 | 2025-11-03 | None | None | DEPRECATED - DO NOT USE |
| `_ARCHIVED_training_dataset_baseline_complete` | TABLE | 1,251 | 1.75 | 2025-11-03 | None | None | DEPRECATED - DO NOT USE |
| `_ARCHIVED_training_dataset_clean` | TABLE | 1,251 | 1.82 | 2025-11-03 | None | None | DEPRECATED - DO NOT USE |
| `_ARCHIVED_training_dataset_snapshot_20251028_pre_update` | TABLE | 1,251 | 1.85 | 2025-11-03 | None | None | DEPRECATED - DO NOT USE |
| `_contract_207` | TABLE | 207 | 0.01 | 2025-10-30 | None | None |  |
| `_contract_209` | TABLE | 209 | 0.01 | 2025-10-30 | None | None |  |
| `_latest_date` | TABLE | 1 | 0.00 | 2025-11-05 | None | None |  |
| `_v_train_core` | VIEW | 0 | 0.00 | 2025-11-03 | None | None |  |
| `alternative_fx_rates` | TABLE | 2,043 | 0.03 | 2025-11-03 | None | None |  |
| `argentina_port_logistics_daily` | TABLE | 1,347 | 0.01 | 2025-11-06 | None | None |  |
| `backtesting_history` | TABLE | 508 | 0.02 | 2025-10-23 | None | None |  |
| `baseline_1m_comprehensive_2yr` | TABLE | 482 | 2.87 | 2025-11-07 | None | None |  |
| `baseline_1m_comprehensive_2yr_55_symbols_backup` | TABLE | 482 | 2.87 | 2025-11-07 | None | None |  |
| `batch_prediction_input` | TABLE | 1 | 0.00 | 2025-10-29 | None | None |  |
| `boost_weights_log` | TABLE | 172 | 0.02 | 2025-11-07 | PARTITION BY date_applied | category, feature |  |
| `cftc_daily_filled` | TABLE | 2,136 | 0.05 | 2025-11-10 | None | None |  |
| `cpi_yoy_daily` | TABLE | 0 | 0.00 | 2025-11-03 | None | None |  |
| `crisis_2008_historical` | TABLE | 253 | 0.06 | 2025-11-12 | None | None |  |
| `currency_complete` | TABLE | 6,287 | 0.23 | 2025-11-10 | None | None |  |
| `economic_indicators_daily_complete` | TABLE | 11,893 | 0.60 | 2025-11-03 | None | None |  |
| `enhanced_features_automl` | VIEW | 0 | 0.00 | 2025-10-28 | None | None |  |
| `errors_2025_10_29T13_14_07_060Z_043` | TABLE | 1 | 0.00 | 2025-10-29 | None | None |  |
| `eval_holdout_2024` | TABLE | 482 | 1.38 | 2025-11-06 | None | None |  |
| `feature_importance_vertex` | TABLE | 615 | 0.03 | 2025-11-02 | None | None |  |
| `feature_metadata_catalog` | TABLE | 444 | 0.02 | 2025-11-07 | None | None |  |
| `forecast_validation_alerts` | TABLE | 0 | 0.00 | 2025-10-28 | None | None |  |
| `forecast_validation_logs` | TABLE | 2 | 0.00 | 2025-10-28 | None | None |  |
| `forward_curve_v3` | TABLE | 181 | 0.01 | 2025-10-23 | None | None |  |
| `fred_economic_complete` | TABLE | 113 | 0.00 | 2025-11-03 | None | None |  |
| `freight_logistics_daily` | TABLE | 1,347 | 0.01 | 2025-11-06 | None | None |  |
| `full_220_comprehensive_2yr` | TABLE | 482 | 2.82 | 2025-11-07 | None | None |  |
| `fundamentals_derived_features` | TABLE | 16,824 | 0.13 | 2025-10-27 | None | None |  |
| `fx_derived_features` | TABLE | 16,824 | 0.20 | 2025-10-27 | None | None |  |
| `gdp_growth_daily` | TABLE | 0 | 0.00 | 2025-11-03 | None | None |  |
| `lag_alignment_audit` | TABLE | 1 | 0.00 | 2025-11-07 | None | None |  |
| `monetary_derived_features` | TABLE | 16,824 | 0.23 | 2025-10-27 | None | None |  |
| `news_intelligence_daily` | TABLE | 19 | 0.00 | 2025-11-10 | None | None |  |
| `palm_oil_complete` | TABLE | 1,842 | 0.07 | 2025-11-10 | None | None |  |
| `palm_price_daily_complete` | TABLE | 2,045 | 0.10 | 2025-11-03 | None | None |  |
| `pre_crisis_2000_2007_historical` | TABLE | 1,737 | 0.38 | 2025-11-12 | None | None |  |
| `predict_frame` | VIEW | 0 | 0.00 | 2025-10-31 | None | None |  |
| `predict_frame_209` | TABLE | 1 | 0.00 | 2025-11-05 | None | None |  |
| `predictions_comparison` | TABLE | 482 | 0.03 | 2025-11-06 | None | None |  |
| `production_training_data_12m` | TABLE | 1,473 | 2.22 | 2025-11-07 | None | None |  |
| `production_training_data_1m` | TABLE | 1,404 | 3.99 | 2025-11-06 | None | None |  |
| `production_training_data_1m_backup_20251112_165404` | TABLE | 1,404 | 3.99 | 2025-11-12 | None | None |  |
| `production_training_data_1w` | TABLE | 1,472 | 2.50 | 2025-11-06 | None | None |  |
| `production_training_data_1w_backup_20251112_165404` | TABLE | 1,472 | 2.50 | 2025-11-12 | None | None |  |
| `production_training_data_3m` | TABLE | 1,475 | 2.36 | 2025-11-06 | None | None |  |
| `production_training_data_6m` | TABLE | 1,473 | 2.22 | 2025-11-06 | None | None |  |
| `recovery_2010_2016_historical` | TABLE | 1,760 | 0.39 | 2025-11-12 | None | None |  |
| `residual_quantiles` | TABLE | 4 | 0.00 | 2025-11-02 | None | None |  |
| `rfs_mandates_daily` | TABLE | 1,347 | 0.01 | 2025-11-06 | None | None |  |
| `rich_focused_feature_availability` | TABLE | 148 | 0.00 | 2025-11-07 | None | None |  |
| `rich_focused_feature_importance` | TABLE | 281 | 0.02 | 2025-11-07 | None | None |  |
| `rich_focused_feature_list` | TABLE | 148 | 0.01 | 2025-11-07 | None | None |  |
| `rich_focused_feature_list_final` | TABLE | 137 | 0.00 | 2025-11-07 | None | None |  |
| `rin_prices_daily` | TABLE | 1,347 | 0.01 | 2025-11-06 | None | None |  |
| `social_sentiment_daily` | TABLE | 208 | 0.01 | 2025-11-10 | None | None |  |
| `trade_war_2017_2019_historical` | TABLE | 754 | 0.17 | 2025-11-12 | None | None |  |
| `train_1m` | VIEW | 0 | 0.00 | 2025-10-31 | None | None |  |
| `train_1w` | VIEW | 0 | 0.00 | 2025-10-31 | None | None |  |
| `train_3m` | VIEW | 0 | 0.00 | 2025-10-31 | None | None |  |
| `train_6m` | VIEW | 0 | 0.00 | 2025-10-31 | None | None |  |
| `training_data_1m_clean` | TABLE | 732 | 0.35 | 2025-11-07 | None | None |  |
| `training_dataset_1m_filtered` | VIEW | 0 | 0.00 | 2025-10-28 | None | None |  |
| `training_dataset_3m_filtered` | VIEW | 0 | 0.00 | 2025-10-28 | None | None |  |
| `training_dataset_6m_filtered` | VIEW | 0 | 0.00 | 2025-10-28 | None | None |  |
| `training_dataset_pre_coverage_fix_backup` | TABLE | 2,045 | 2.44 | 2025-11-03 | None | None |  |
| `training_dataset_pre_forwardfill_backup` | TABLE | 2,043 | 2.74 | 2025-11-04 | None | None |  |
| `training_dataset_pre_integration_backup` | TABLE | 2,136 | 0.18 | 2025-11-10 | None | None |  |
| `training_dataset_super_enriched` | TABLE | 2,136 | 0.18 | 2025-11-05 | None | None | ✅ PRODUCTION TRAINING DATASET - OFFICIAL SOURCE FO... |
| `training_dataset_super_enriched_backup` | TABLE | 2,045 | 2.42 | 2025-11-03 | None | None |  |
| `training_dataset_v4` | VIEW | 0 | 0.00 | 2025-10-23 | None | None |  |
| `treasury_10y_yahoo_complete` | TABLE | 2,043 | 0.08 | 2025-11-03 | None | None |  |
| `trump_policy_daily` | TABLE | 53 | 0.00 | 2025-11-10 | None | None |  |
| `trump_rich_2023_2025` | TABLE | 732 | 0.32 | 2025-11-07 | None | None |  |
| `us_midwest_weather_complete` | TABLE | 2,133 | 0.12 | 2025-11-03 | None | None |  |
| `us_midwest_weather_daily` | TABLE | 404 | 0.02 | 2025-11-03 | None | None |  |
| `usd_cny_daily_complete` | TABLE | 5,021 | 0.22 | 2025-11-03 | None | None |  |
| `usda_export_daily` | TABLE | 12 | 0.00 | 2025-11-10 | None | None |  |
| `vertex_core_features` | TABLE | 16,824 | 1.77 | 2025-11-07 | None | None |  |
| `vertex_master_time_spine` | TABLE | 16,824 | 1.29 | 2025-11-07 | None | None |  |
| `volatility_derived_features` | TABLE | 16,824 | 0.42 | 2025-10-27 | None | None |  |
| `vw_arg_crisis_score` | VIEW | 0 | 0.00 | 2025-11-07 | None | None |  |
| `vw_fx_all` | VIEW | 0 | 0.00 | 2025-10-30 | None | None |  |
| `vw_temporal_engineered` | VIEW | 0 | 0.00 | 2025-10-28 | None | None |  |
| `yahoo_finance_weekend_complete` | TABLE | 14,301 | 0.61 | 2025-11-03 | None | None |  |
| `yahoo_indicators_wide` | VIEW | 0 | 0.00 | 2025-11-03 | None | None |  |

#### Dataset: `monitoring`

| Table/View Name | Type | Rows | Size (MB) | Created | Partitioning | Clustering | Description |
|-----------------|------|------|-----------|---------|---------------|------------|-------------|
| `model_feature_importance` | TABLE | 615 | 0.03 | 2025-11-14 | None | None |  |

#### Dataset: `neural`

| Table/View Name | Type | Rows | Size (MB) | Created | Partitioning | Clustering | Description |
|-----------------|------|------|-----------|---------|---------------|------------|-------------|
| `vw_big_eight_signals` | VIEW | 0 | 0.00 | 2025-10-22 | None | None |  |

#### Dataset: `performance`

| Table/View Name | Type | Rows | Size (MB) | Created | Partitioning | Clustering | Description |
|-----------------|------|------|-----------|---------|---------------|------------|-------------|
| `mape_historical_tracking` | TABLE | 0 | 0.00 | 2025-11-15 | PARTITION BY tracking_date | tracking_date |  |
| `soybean_sharpe_historical_tracking` | TABLE | 0 | 0.00 | 2025-11-15 | PARTITION BY tracking_date | tracking_date |  |
| `vw_forecast_performance_tracking` | VIEW | 0 | 0.00 | 2025-11-15 | None | None |  |
| `vw_soybean_sharpe_metrics` | VIEW | 0 | 0.00 | 2025-11-15 | None | None |  |

#### Dataset: `predictions`

| Table/View Name | Type | Rows | Size (MB) | Created | Partitioning | Clustering | Description |
|-----------------|------|------|-----------|---------|---------------|------------|-------------|
| `daily_forecasts` | TABLE | 0 | 0.00 | 2025-10-30 | None | None |  |
| `errors_2025_10_29T15_00_41_432Z_235` | TABLE | 1 | 0.00 | 2025-10-29 | None | None |  |
| `errors_2025_10_29T15_27_01_724Z_285` | TABLE | 1 | 0.00 | 2025-10-29 | None | None |  |
| `monthly_vertex_predictions` | TABLE | 2 | 0.00 | 2025-10-30 | PARTITION BY prediction_date | None |  |
| `zl_predictions_prod_all_latest` | TABLE | 0 | 0.00 | 2025-11-14 | None | None |  |

#### Dataset: `predictions_uc1`

| Table/View Name | Type | Rows | Size (MB) | Created | Partitioning | Clustering | Description |
|-----------------|------|------|-----------|---------|---------------|------------|-------------|
| `daily_forecasts` | TABLE | 0 | 0.00 | 2025-10-31 | None | None |  |
| `model_feature_importance` | TABLE | 0 | 0.00 | 2025-10-31 | PARTITION BY prediction_date | horizon, feature |  |
| `monthly_vertex_predictions` | TABLE | 1 | 0.00 | 2025-10-31 | PARTITION BY prediction_date | None |  |
| `production_forecasts` | TABLE | 4 | 0.00 | 2025-11-04 | PARTITION BY forecast_date | horizon, model_name | Production forecasts from BQML models - clean base... |
| `vw_feature_importance_latest` | VIEW | 0 | 0.00 | 2025-10-31 | None | None |  |

#### Dataset: `raw_intelligence`

| Table/View Name | Type | Rows | Size (MB) | Created | Partitioning | Clustering | Description |
|-----------------|------|------|-----------|---------|---------------|------------|-------------|
| `commodity_crude_oil_prices` | TABLE | 10,859 | 1.45 | 2025-11-14 | None | None |  |
| `commodity_palm_oil_prices` | TABLE | 1,340 | 0.15 | 2025-11-14 | None | None |  |
| `macro_economic_indicators` | TABLE | 72,553 | 6.37 | 2025-11-14 | None | None |  |
| `news_sentiments` | TABLE | 2,830 | 1.51 | 2025-11-14 | None | None |  |
| `policy_biofuel` | TABLE | 62 | 0.01 | 2025-11-14 | None | None |  |
| `shipping_baltic_dry_index` | TABLE | 0 | 0.00 | 2025-11-14 | PARTITION BY time | None | Baltic Dry Index - Daily shipping rates indicator ... |
| `trade_china_soybean_imports` | TABLE | 22 | 0.00 | 2025-11-14 | None | None |  |

#### Dataset: `signals`

| Table/View Name | Type | Rows | Size (MB) | Created | Partitioning | Clustering | Description |
|-----------------|------|------|-----------|---------|---------------|------------|-------------|
| `daily_calculations` | TABLE | 6 | 0.00 | 2025-10-29 | None | None |  |
| `vw_bear_market_regime` | VIEW | 0 | 0.00 | 2025-10-30 | None | None |  |
| `vw_biofuel_cascade_signal` | VIEW | 0 | 0.00 | 2025-10-22 | None | None |  |
| `vw_biofuel_ethanol_signal` | VIEW | 0 | 0.00 | 2025-10-22 | None | None |  |
| `vw_biofuel_policy_intensity` | VIEW | 0 | 0.00 | 2025-10-30 | None | None |  |
| `vw_biofuel_substitution_aggregates_daily` | VIEW | 0 | 0.00 | 2025-10-14 | None | None |  |
| `vw_china_import_diversification_monthly` | VIEW | 0 | 0.00 | 2025-10-14 | None | None |  |
| `vw_china_import_diversification_nowcast_daily` | VIEW | 0 | 0.00 | 2025-10-14 | None | None |  |
| `vw_china_relations_big8` | VIEW | 0 | 0.00 | 2025-11-03 | None | None |  |
| `vw_china_relations_signal` | VIEW | 0 | 0.00 | 2025-10-22 | None | None |  |
| `vw_comprehensive_signal_universe` | VIEW | 0 | 0.00 | 2025-10-20 | None | None |  |
| `vw_fundamental_aggregates_comprehensive_daily` | VIEW | 0 | 0.00 | 2025-10-20 | None | None |  |
| `vw_geopolitical_aggregates_comprehensive_daily` | VIEW | 0 | 0.00 | 2025-10-20 | None | None |  |
| `vw_geopolitical_volatility_signal` | VIEW | 0 | 0.00 | 2025-10-22 | None | None |  |
| `vw_harvest_pace_big8` | VIEW | 0 | 0.00 | 2025-11-03 | None | None |  |
| `vw_harvest_pace_signal` | VIEW | 0 | 0.00 | 2025-10-22 | None | None |  |
| `vw_hidden_correlation_signal` | VIEW | 0 | 0.00 | 2025-10-27 | None | None |  |
| `vw_high_priority_social_intelligence` | VIEW | 0 | 0.00 | 2025-11-14 | None | None |  |
| `vw_master_signal_processor` | VIEW | 0 | 0.00 | 2025-10-16 | None | None |  |
| `vw_news_sentiment_scores_daily` | VIEW | 0 | 0.00 | 2025-10-14 | None | None |  |
| `vw_sentiment_price_correlation` | VIEW | 0 | 0.00 | 2025-10-20 | None | None |  |
| `vw_social_sentiment_aggregates_daily` | VIEW | 0 | 0.00 | 2025-11-14 | None | None |  |
| `vw_substitution_aggregates_comprehensive_daily` | VIEW | 0 | 0.00 | 2025-10-14 | None | None |  |
| `vw_supply_glut_indicator` | VIEW | 0 | 0.00 | 2025-10-30 | None | None |  |
| `vw_tariff_threat_big8` | VIEW | 0 | 0.00 | 2025-11-03 | None | None |  |
| `vw_tariff_threat_signal` | VIEW | 0 | 0.00 | 2025-10-22 | None | None |  |
| `vw_technical_aggregates_comprehensive_daily` | VIEW | 0 | 0.00 | 2025-10-14 | None | None |  |
| `vw_trade_war_impact` | VIEW | 0 | 0.00 | 2025-10-30 | None | None |  |
| `vw_vix_stress_big8` | VIEW | 0 | 0.00 | 2025-11-03 | None | None |  |
| `vw_vix_stress_daily` | VIEW | 0 | 0.00 | 2025-10-16 | None | None |  |
| `vw_vix_stress_signal` | VIEW | 0 | 0.00 | 2025-10-22 | None | None |  |
| `vw_weather_aggregates_daily` | VIEW | 0 | 0.00 | 2025-10-14 | None | None |  |
| `vw_weather_aggregates_daily_nowcast` | VIEW | 0 | 0.00 | 2025-10-14 | None | None |  |
| `vw_weather_availability_daily` | VIEW | 0 | 0.00 | 2025-10-14 | None | None |  |

#### Dataset: `staging`

| Table/View Name | Type | Rows | Size (MB) | Created | Partitioning | Clustering | Description |
|-----------------|------|------|-----------|---------|---------------|------------|-------------|
| `biofuel_policy` | TABLE | 30 | 0.01 | 2025-10-13 | PARTITION BY date | source_name |  |
| `biofuel_production` | TABLE | 24 | 0.00 | 2025-10-13 | PARTITION BY date | region |  |
| `cftc_cot` | TABLE | 78 | 0.01 | 2025-10-14 | PARTITION BY report_date | commodity, contract_code |  |
| `comprehensive_social_intelligence` | TABLE | 76,297 | 35.44 | 2025-10-14 | PARTITION BY collection_date | platform, handle |  |
| `ice_enforcement_intelligence` | TABLE | 4 | 0.00 | 2025-10-12 | PARTITION BY timestamp | source_name |  |
| `market_prices` | TABLE | 0 | 0.00 | 2025-10-10 | PARTITION BY date | symbol |  |
| `trade_policy_events` | TABLE | 0 | 0.00 | 2025-10-13 | PARTITION BY event_date | policy_type, country |  |
| `trump_policy_intelligence` | TABLE | 215 | 0.07 | 2025-10-12 | PARTITION BY timestamp | source_name |  |
| `usda_export_sales` | TABLE | 12 | 0.00 | 2025-10-13 | PARTITION BY report_date | commodity, destination_country |  |
| `usda_harvest_progress` | TABLE | 2,730 | 0.16 | 2025-10-20 | None | None |  |
| `weather_data_midwest_openmeteo` | TABLE | 495 | 0.07 | 2025-11-03 | None | None |  |

#### Dataset: `training`

| Table/View Name | Type | Rows | Size (MB) | Created | Partitioning | Clustering | Description |
|-----------------|------|------|-----------|---------|---------------|------------|-------------|
| `regime_calendar` | TABLE | 13,102 | 0.37 | 2025-11-14 | None | None | Maps dates to market regimes for regime-based trai... |
| `regime_weights` | TABLE | 11 | 0.00 | 2025-11-14 | None | None |  |
| `zl_training_full_all_1w` | TABLE | 1,263 | 1.48 | 2025-11-14 | None | None |  |
| `zl_training_full_allhistory_12m` | TABLE | 1,473 | 2.35 | 2025-11-14 | None | None |  |
| `zl_training_full_allhistory_1m` | TABLE | 1,404 | 4.10 | 2025-11-14 | None | None |  |
| `zl_training_full_allhistory_1w` | TABLE | 1,472 | 2.62 | 2025-11-14 | None | None |  |
| `zl_training_full_allhistory_3m` | TABLE | 1,475 | 2.49 | 2025-11-14 | None | None |  |
| `zl_training_full_allhistory_6m` | TABLE | 1,473 | 2.34 | 2025-11-14 | None | None |  |
| `zl_training_full_crisis_all` | TABLE | 253 | 0.06 | 2025-11-14 | None | None |  |
| `zl_training_full_precrisis_all` | TABLE | 1,737 | 0.38 | 2025-11-14 | None | None |  |
| `zl_training_full_recovery_all` | TABLE | 1,760 | 0.39 | 2025-11-14 | None | None |  |
| `zl_training_full_tradewar_all` | TABLE | 754 | 0.17 | 2025-11-14 | None | None |  |
| `zl_training_prod_allhistory_12m` | TABLE | 1,473 | 2.35 | 2025-11-14 | None | None |  |
| `zl_training_prod_allhistory_1m` | TABLE | 1,404 | 4.09 | 2025-11-14 | None | None |  |
| `zl_training_prod_allhistory_1w` | TABLE | 1,472 | 2.62 | 2025-11-14 | None | None |  |
| `zl_training_prod_allhistory_3m` | TABLE | 1,475 | 2.49 | 2025-11-14 | None | None |  |
| `zl_training_prod_allhistory_6m` | TABLE | 1,473 | 2.34 | 2025-11-14 | None | None |  |
| `zl_training_prod_trump_all` | TABLE | 732 | 0.32 | 2025-11-14 | None | None |  |

#### Dataset: `weather`

| Table/View Name | Type | Rows | Size (MB) | Created | Partitioning | Clustering | Description |
|-----------------|------|------|-----------|---------|---------------|------------|-------------|
| `daily_updates` | TABLE | 3 | 0.00 | 2025-10-29 | None | None |  |

#### Dataset: `yahoo_finance_comprehensive`

| Table/View Name | Type | Rows | Size (MB) | Created | Partitioning | Clustering | Description |
|-----------------|------|------|-----------|---------|---------------|------------|-------------|
| `all_symbols_20yr` | TABLE | 57,397 | 20.94 | 2025-11-06 | None | None |  |
| `biofuel_components_canonical` | TABLE | 6,475 | 0.92 | 2025-11-06 | None | None |  |
| `biofuel_components_raw` | TABLE | 42,367 | 5.19 | 2025-11-06 | None | None |  |
| `explosive_technicals` | TABLE | 28,101 | 5.54 | 2025-11-06 | None | None |  |
| `rin_proxy_features` | TABLE | 12,637 | 0.37 | 2025-11-06 | None | None |  |
| `rin_proxy_features_dedup` | TABLE | 6,348 | 0.18 | 2025-11-06 | None | None |  |
| `rin_proxy_features_final` | TABLE | 6,475 | 0.67 | 2025-11-06 | None | None |  |
| `rin_proxy_features_fixed` | TABLE | 12,637 | 0.37 | 2025-11-06 | None | None |  |
| `yahoo_finance_complete_enterprise` | TABLE | 314,381 | 81.46 | 2025-11-06 | None | None |  |
| `yahoo_normalized` | TABLE | 314,381 | 70.92 | 2025-11-06 | None | symbol, date |  |

---

## External Drive Inventory

**External Drive Found**: `/Volumes/Satechi Hub`

**Files Found**: 33 data files

### Sample Files

- `/Volumes/Satechi Hub/Projects/CBI-V14/archive/csv_backups_oct27/training_dataset_clean.parquet`
- `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/exports/recovery_2010_2016_historical.parquet`
- `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/exports/zl_training_full_allhistory_12m.parquet`
- `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/exports/zl_training_prod_allhistory_6m.parquet`
- `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/exports/trade_war_2017_2019_historical.parquet`
- `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/exports/zl_training_prod_allhistory_1m.parquet`
- `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/exports/crisis_2008_historical.parquet`
- `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/exports/zl_training_full_allhistory_1w.parquet`
- `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/exports/zl_training_full_allhistory_3m.parquet`
- `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/exports/inflation_2021_2022.parquet`
- `/Volumes/Satechi Hub/Projects/CBI-V14/GPT_Data/empty_minimal_tables.csv`
- `/Volumes/Satechi Hub/Projects/CBI-V14/GPT_Data/historical_data_sources.csv`
- `/Volumes/Satechi Hub/Projects/CBI-V14/GPT_Data/models_training_inventory.csv`
- `/Volumes/Satechi Hub/Projects/CBI-V14/GPT_Data/duplicate_table_names.csv`
- `/Volumes/Satechi Hub/Projects/CBI-V14/GPT_Data/dataset_summary.csv`
- `/Volumes/Satechi Hub/Projects/CBI-V14/GPT_Data/schema_all_columns.csv`
- `/Volumes/Satechi Hub/Projects/CBI-V14/GPT_Data/inventory_340_objects.csv`
- `/Volumes/Satechi Hub/Projects/CBI-V14/GPT_Data/column_name_frequency.csv`
- `/Volumes/Satechi Hub/Projects/CBI-V14/GPT_Data/production_tables_detail.csv`
- `/Volumes/Satechi Hub/Projects/CBI-V14/GPT_Data/production_features_290.csv`

*... and 13 more files*

---

## Migration Mapping

### New Dataset Architecture

| Dataset                | Purpose                                             |
| ---------------------- | --------------------------------------------------- |
| `raw_intelligence`     | Raw, unprocessed source data.                       |
| `features`             | Engineered features for modeling.                   |
| `training`             | Final, versioned training sets.                     |
| `predictions`          | Model outputs and generated signals.                |
| `monitoring`           | Performance metrics, data quality, model registry.  |
| `archive`              | Snapshots and retired legacy objects.               |
| `vegas_intelligence`   | Data for the "Vegas Intel" sales dashboard.         |

### Naming Convention

`asset_function_scope_regime_horizon`

-   **asset**: `zl` (Soybean Oil)
-   **function**: `features`, `training`, `predictions`, `monitoring`, `signals`
-   **scope**: `full` (research), `prod` (production), or model type
-   **regime**: `crisis`, `tradewar`, `all`, `precrisis`, `recovery`, `trump`
-   **horizon**: `1w`, `1m`, `3m`, `6m`, `12m`

---

### Migration Status

**Note**: This section should be manually maintained based on migration progress.

| Legacy Dataset                  | Legacy Table/View Name                          | Type  | New Dataset            | New Table/View Name                                   | Status      | Notes                                                              |
| ------------------------------- | ----------------------------------------------- | ----- | ---------------------- | ----------------------------------------------------- | ----------- | ------------------------------------------------------------------ |
| *See detailed inventory above for current state* | | | | | | |

---

### Action Plan

1.  **Review & Refine**: The project team will review this inventory and refine the mappings.
2.  **Script Development**: A script will be created to perform the `Migrate` and `Recreate` actions.
3.  **Execution**: The migration script will be run in a controlled environment.
4.  **Validation**: Post-migration, data and views will be validated against the old structure.
5.  **Decommission**: Once validated, legacy datasets will be backed up to the `archive` and then decommissioned.

---

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**BigQuery Project**: `{PROJECT_ID}`  
**Region**: `{BQ_REGION}`
