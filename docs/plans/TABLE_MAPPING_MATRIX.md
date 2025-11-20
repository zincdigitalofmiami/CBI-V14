---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

**📋 BEST PRACTICES:** See `.cursorrules` and `docs/reference/BEST_PRACTICES_DRAFT.md` for mandatory best practices including: no fake data, always check before creating, always audit after work, us-central1 only, no costly resources without approval, research best practices, research quant finance modeling.

# CBI-V14: Table Mapping Matrix (Archived)
Note: This document is archived. For the active, consolidated reference, see `docs/plans/REFERENCE.md`.

**Last Updated**: November 19, 2025 (Updated with Fresh Audit Findings)  
**Status**: COMPREHENSIVE MAPPING - AUTO-GENERATED FROM AUDIT + VERIFICATION  
**Source**: Fresh Audit (Nov 19, 2025) + Join Spec + BigQuery Inventory + Staging File Scan

This document provides a comprehensive mapping between staging files, BigQuery tables, join specifications, and the complete data pipeline. Updated with findings from the November 19, 2025 fresh comprehensive audit.

---

## Executive Summary

### Current State (November 19, 2025)

- **Staging Files**: 19 parquet files, 523,291 total rows
- **BigQuery Tables**: 30 tables audited (all empty - expected for new datasets)
- **Pipeline Status**: ✅ PASSING (2,025 rows × 1,175 columns final output)
- **Date Range**: 2000-03-15 to 2025-11-14
- **Join Steps**: 15 joins in pipeline
- **News Collection**: Partial setup (ScrapeCreators ready, Alpha Vantage pending)

### Key Findings

✅ **Pipeline Validation**: All tests passing  
✅ **Staging Files**: 19 files, mostly healthy (1 file with duplicate dates)  
⚠️ **BigQuery Tables**: All empty (expected - new dataset structure)  
⚠️ **News Collection**: Alpha Vantage collector script missing  
✅ **Join Spec**: Fully aligned with staging files

---

## 1. STAGING FILES → BIGQUERY MAPPING

### Complete Staging File Inventory (November 19, 2025)

| Staging File | Rows | Columns | Date Range | Duplicates | Status | BigQuery Target | Dataset |
|--------------|------|---------|------------|------------|-------|-----------------|---------|
| `alpha_vantage_features.parquet` | 10,719 | 736 | 1986-01-02 to 2025-11-17 | 0 | ⏯ Archived | `alpha_vantage_features` | `raw_intelligence` (deprecated) |
| `cftc_commitments.parquet` | 522 | 195 | 2015-01-06 to 2024-12-31 | 0 | ✅ | `cftc_commitments` | `forecasting_data_warehouse` |
| `eia_biofuels_2010_2025.parquet` | 828 | 2 | 2010-01-04 to 2025-11-10 | 0 | ✅ | `eia_biofuels` | `raw_intelligence` |
| `eia_energy_granular.parquet` | 828 | 3 | 2010-01-04 to 2025-11-10 | 0 | ✅ | `eia_energy_granular` | `forecasting_data_warehouse` |
| `es_daily_aggregated.parquet` | 21 | 23 | 2025-10-20 to 2025-11-17 | 0 | ✅ | `es_daily_aggregated` | `forecasting_data_warehouse` |
| `es_futures_daily.parquet` | 6,308 | 58 | 2000-11-24 to 2025-11-17 | 0 | ✅ | `es_futures_daily` | `forecasting_data_warehouse` |
| `fred_macro_expanded.parquet` | 9,452 | 17 | 2000-01-01 to 2025-11-16 | 0 | ✅ | `fred_macro_expanded` | `forecasting_data_warehouse` |
| `mes_15min.parquet` | 229,160 | 6 | N/A | 0 | ✅ | `mes_15min` | `market_data` |
| `mes_15min_features.parquet` | 229,160 | 24 | N/A | 0 | ✅ | `mes_15min_features` | `market_data` |
| `mes_confirmation_features.parquet` | 2,036 | 15 | 2019-05-05 to 2025-11-16 | 0 | ✅ | `mes_confirmation_features` | `market_data` |
| `mes_daily_aggregated.parquet` | 2,036 | 34 | 2019-05-05 to 2025-11-16 | 0 | ✅ | `mes_daily_aggregated` | `market_data` |
| `mes_futures_daily.parquet` | 2,036 | 6 | 2019-05-05 to 2025-11-16 | 0 | ✅ | `mes_futures_daily` | `market_data` |
| `palm_oil_daily.parquet` | 1,269 | 9 | 2020-10-21 to 2025-11-17 | 0 | ✅ | `palm_oil_daily` | `forecasting_data_warehouse` |
| `policy_trump_signals.parquet` | 25 | 13 | 2025-11-17 to 2025-11-17 | 25 | ⚠️ | `policy_trump_signals` | `forecasting_data_warehouse` |
| `usda_reports_granular.parquet` | 6 | 16 | 2020-01-06 to 2025-01-06 | 0 | ✅ | `usda_reports_granular` | `forecasting_data_warehouse` |
| `volatility_features.parquet` | 9,069 | 21 | 1990-01-02 to 2025-11-17 | 0 | ✅ | `volatility_features` | `forecasting_data_warehouse` |
| `weather_granular.parquet` | 9,438 | 61 | 2000-01-01 to 2025-11-02 | 0 | ✅ | `weather_granular` | `forecasting_data_warehouse` |
| `yahoo_historical_prefixed.parquet` | 6,380 | 55 | 2000-03-15 to 2025-11-14 | 0 | ✅ | `yahoo_historical_prefixed` | `forecasting_data_warehouse` |
| `zl_daily_aggregated.parquet` | 3,998 | 14 | 2010-06-06 to 2025-11-14 | 0 | ✅ | `zl_daily_aggregated` | `market_data` |

**Total**: 19 files, 523,291 rows

### Issues Identified

⚠️ **policy_trump_signals.parquet**: All 25 rows have duplicate dates (same date: 2025-11-17). Investigation needed.

---

## 2. JOIN SPECIFICATION MAPPING

### Pipeline Join Steps (from `registry/join_spec.yaml`)

| Join Step | Left Input | Right Input (Staging File) | Join Key | How | Tests |
|-----------|------------|----------------------------|----------|-----|-------|
| `base_prices` | N/A (base) | `yahoo_historical_prefixed.parquet` | N/A | N/A | Date range, symbol count, ZL rows |
| `add_macro` | `<<base_prices>>` | `fred_macro_expanded.parquet` | `date` | left | Rows preserved, columns added, null rates |
| `add_weather` | `<<add_macro>>` | `weather_granular.parquet` | `date` | left | Rows preserved, null rates, columns added |
| `add_cftc` | `<<add_weather>>` | `cftc_commitments.parquet` | `date` | left | Rows preserved, CFTC available after 2015 |
| `add_usda` | `<<add_cftc>>` | `usda_reports_granular.parquet` | `date` | left | Rows preserved, columns prefixed |
| `add_eia` | `<<add_usda>>` | `eia_energy_granular.parquet` | `date` | left | Rows preserved, columns prefixed |
| `add_regimes` | `<<add_eia>>` | `registry/regime_calendar.parquet` | `date` | left | Rows preserved, regime columns added |
| `add_alpha_vantage` | `<<add_regimes>>` | `alpha_vantage_features.parquet` | `date` | left | Rows preserved, columns prefixed |
| `add_volatility` | `<<add_alpha_vantage>>` | `volatility_features.parquet` | `date` | left | Rows preserved, columns prefixed |
| `add_palm` | `<<add_volatility>>` | `palm_oil_daily.parquet` | `date` | left | Rows preserved, columns prefixed |
| `add_policy_trump` | `<<add_palm>>` | `policy_trump_signals.parquet` | `date` | left | Rows preserved, columns prefixed |
| `add_es_futures` | `<<add_policy_trump>>` | `es_futures_daily.parquet` | `date` | left | Rows preserved, columns prefixed |
| `add_es_intraday_features` | `<<add_es_futures>>` | `es_daily_aggregated.parquet` | `date` | left | Rows preserved, intraday features added |
| `add_mes_futures` | `<<add_es_intraday_features>>` | `mes_futures_daily.parquet` | `date` | left | Rows preserved, columns prefixed |
| `add_mes_intraday_features` | `<<add_mes_futures>>` | `mes_daily_aggregated.parquet` | `date` | left | Rows preserved, intraday features added |
| `add_mes_confirmation_features` | `<<add_mes_intraday_features>>` | `mes_confirmation_features.parquet` | `date` | left | Rows preserved, correlation features added |
| `add_zl_intraday_features` | `<<add_mes_confirmation_features>>` | `zl_daily_aggregated.parquet` | `date` | left | Rows preserved, ZL intraday features added |

**Total Join Steps**: 17 (1 base + 16 joins)

### Final Pipeline Output

- **Rows**: 2,025 (from join_executor validation)
- **Columns**: 1,175 (from join_executor validation)
- **Date Range**: 2000-03-15 to 2025-11-14
- **Status**: ✅ All tests passing

---

## 3. BIGQUERY DATASET MAPPING

### Current Dataset Structure (November 19, 2025)

| Dataset | Purpose | Tables | Status | Notes |
|---------|---------|--------|--------|-------|
| `forecasting_data_warehouse` | Primary raw data storage | 87 | ✅ Active | Main data warehouse |
| `raw_intelligence` | Intelligence data (news, policy, weather) | 10 | ⚠️ Empty | New structure, tables created but empty |
| `training` | Training datasets (ZL + MES) | 19 | ⚠️ Empty | New structure, tables created but empty |
| `signals` | Derived signals and features | 34 | ⚠️ Missing | Dataset not found in audit |
| `market_data` | Market data (futures, prices) | 4 | ✅ Active | Contains historical data |
| `models_v4` | Training data + BQML models | 93 | ✅ Active | Production training tables |
| `predictions` | Model predictions | 0 | ⚠️ Empty | No tables found |
| `monitoring` | Performance tracking | 1 | ⚠️ Empty | Table exists but empty |
| `yahoo_finance_comprehensive` | Historical Yahoo Finance data | 10 | ✅ Active | 801K rows total |

### Key Production Tables

#### Training Tables (Production)

| Table | Rows | Columns | Date Range | Status |
|-------|------|---------|------------|--------|
| `training.zl_training_prod_allhistory_1w` | 1,472 | 305 | 2020+ | ✅ Populated |
| `training.zl_training_prod_allhistory_1m` | 1,404 | 449 | 2020+ | ✅ Populated |
| `training.zl_training_prod_allhistory_3m` | 1,475 | 305 | 2020+ | ✅ Populated |
| `training.zl_training_prod_allhistory_6m` | 1,473 | 305 | 2020+ | ✅ Populated |
| `training.zl_training_prod_allhistory_12m` | 1,473 | 306 | 2020+ | ✅ Populated |

#### Models v4 Tables (Legacy Production)

| Table | Rows | Columns | Status |
|-------|------|---------|--------|
| `models_v4.production_training_data_1w` | 1,448 | 290 | ✅ Populated |
| `models_v4.production_training_data_1m` | 1,347 | 290 | ✅ Populated |
| `models_v4.production_training_data_3m` | 1,329 | 290 | ✅ Populated |
| `models_v4.production_training_data_6m` | 1,198 | 290 | ✅ Populated |

---

## 4. NEWS COLLECTION MAPPING

### News Collection Setup (November 19, 2025)

#### Collection Scripts

| Script | Status | Purpose | Target Table |
|--------|--------|---------|-------------|
| `collect_alpha_news_sentiment.py` | ❌ Missing | Alpha Vantage NEWS_SENTIMENT collection | `raw_intelligence.intelligence_news_alpha_raw_daily` |
| `collect_news_scrapecreators_bucketed.py` | ✅ Ready | ScrapeCreators Google Search collection | `raw_intelligence.news_scrapecreators_google_search` |
| `news_bucket_classifier.py` | ✅ Ready | Bucket classification for news articles | N/A (utility) |

#### BigQuery Tables (News)

| Table | Status | Rows | Purpose | Partitioning |
|-------|--------|------|---------|---------------|
| `raw_intelligence.intelligence_news_alpha_raw_daily` | ❌ Not created | 0 | Raw Alpha Vantage news | DATE(time_published) |
| `raw_intelligence.intelligence_news_alpha_classified_daily` | ❌ Not created | 0 | GPT-classified news | DATE(time_published) |
| `signals.hidden_relationship_signals` | ❌ Not created | 0 | Daily hidden driver scores | DATE(date) |

#### DDL Files

| File | Status | Purpose |
|------|--------|---------|
| `config/bigquery/bigquery-sql/create_alpha_news_tables.sql` | ✅ Ready | Creates news tables in BigQuery |

#### Documentation

| Document | Status | Purpose |
|----------|--------|---------|
| `docs/setup/NEWS_COLLECTION_REGIME_BUCKETS.md` | ✅ Ready | Bucket taxonomy (10 buckets) |
| `docs/audit/NEWS_COLLECTION_COMPARISON_ANALYSIS.md` | ✅ Ready | Alpha vs ScrapeCreators comparison |
| `docs/setup/ALPHA_NEWS_INTEGRATION_ALIGNED.md` | ✅ Ready | Alpha Vantage integration spec |
| `docs/audit/ALPHA_SCRAPECREATORS_WORKFLOW_ALIGNMENT.md` | ✅ Ready | Workflow alignment verification |

---

## 5. PREFIX-BY-PREFIX SOURCE MAPPING

### Source Prefix Analysis

| Prefix | Staging Files | BigQuery Tables | Status | Total Rows | Notes |
|--------|---------------|-----------------|--------|------------|-------|
| `alpha_` | 1 | 1 | ✅ Active | 10,719 | Alpha Vantage features populated |
| `cftc_` | 1 | 1 | ✅ Active | 522 | CFTC commitments (2020-2024) |
| `eia_` | 2 | 2 | ✅ Active | 1,656 | EIA biofuels + energy granular |
| `es_` | 2 | 2 | ✅ Active | 6,329 | ES futures + intraday aggregated |
| `fred_` | 1 | 1 | ✅ Active | 9,452 | FRED macro expanded |
| `mes_` | 5 | 5 | ✅ Active | 236,428 | MES futures, intraday, features |
| `palm_` / `barchart_palm_` | 1 | 1 | ✅ Active | 1,269 | Palm oil daily |
| `policy_trump_` | 1 | 1 | ⚠️ Issue | 25 | Duplicate dates issue |
| `usda_` | 1 | 1 | ✅ Active | 6 | USDA reports granular |
| `vol_` / `volatility_` | 1 | 1 | ✅ Active | 9,069 | Volatility features |
| `weather_` | 1 | 1 | ✅ Active | 9,438 | Weather granular |
| `yahoo_` | 1 | 1 | ✅ Active | 6,380 | Yahoo historical prefixed |
| `zl_` | 1 | 1 | ✅ Active | 3,998 | ZL intraday aggregated |

---

## 6. WORKFLOW MAPPING

### Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CBI-V14 DATA WORKFLOW (BQ → Mac → BQ → Dashboard)   │
└─────────────────────────────────────────────────────────────────────────┘

Step 1: DATA COLLECTION (Mac M4)
├── Cron jobs on Mac M4
├── Ingestion scripts (src/ingestion/*.py, scripts/ingest/*.py)
├── Collect from APIs: Yahoo, FRED, NOAA, CFTC, EPA, Alpha Vantage, etc.
└── Upload to BigQuery Cloud (forecasting_data_warehouse, raw_intelligence)

Step 2: FEATURE ENGINEERING (BigQuery Cloud)
├── Raw tables → Feature views (signals.vw_*)
├── SQL joins and aggregations
└── Training tables (training.zl_training_prod_allhistory_*)

Step 3: EXPORT FOR LOCAL TRAINING (BigQuery → Mac)
├── Run: scripts/export_training_data.py
├── Downloads from BigQuery → Parquet files
└── Saves to: TrainingData/exports/zl_training_prod_allhistory_{horizon}.parquet

Step 4: LOCAL TRAINING (Mac M4 - 100% Local)
├── Hardware: Apple M4 Mac mini + TensorFlow Metal
├── Scripts: src/training/baselines/*.py
├── Input: TrainingData/exports/*.parquet
└── Output: Models/local/horizon_{h}/prod/baselines/{model}_v001/

Step 5: PREDICTION GENERATION (Mac M4 - 100% Local)
├── Run: src/prediction/generate_local_predictions.py
├── Input: Local models + latest data
└── Output: predictions.parquet (in each model directory)

Step 6: UPLOAD PREDICTIONS (Mac → BigQuery)
├── Run: scripts/upload_predictions.py
├── Input: Local predictions.parquet files
└── Output: BigQuery predictions.vw_zl_{horizon}_latest views

Step 7: DASHBOARD (Vercel → BigQuery)
├── Dashboard reads from BigQuery only
├── Source: predictions.vw_zl_{horizon}_latest
└── NO dependencies on local models or Mac
```

### Staging File → Join Pipeline → Training Data Flow

```
Staging Files (TrainingData/staging/*.parquet)
    ↓
Join Executor (scripts/assemble/join_executor.py)
    ↓
Final Joined Dataset (6,380 rows × 1,175 columns)
    ↓
Feature Engineering (BigQuery SQL)
    ↓
Training Tables (training.zl_training_prod_allhistory_*)
    ↓
Export Script (scripts/export_training_data.py)
    ↓
Local Training (Mac M4)
```

---

## 7. NAMING CONVENTIONS

### Staging File Naming

- **Format**: `{source}_{type}_{granularity}.parquet`
- **Examples**:
  - `yahoo_historical_prefixed.parquet`
  - `fred_macro_expanded.parquet`
  - `weather_granular.parquet`
  - `cftc_commitments.parquet`

### BigQuery Table Naming

- **Raw Intelligence**: `intelligence_{category}_{source}_raw_daily`
- **Training Tables**: `{asset}_training_{scope}_{regime}_{horizon}`
- **Market Data**: `{source}_{type}_{granularity}`
- **Signals**: `{signal_name}` or `vw_{view_name}`

### Column Prefixing

- **Yahoo**: `yahoo_*`
- **FRED**: `fred_*`
- **CFTC**: `cftc_*`
- **USDA**: `usda_*`
- **EIA**: `eia_*`
- **Weather**: `weather_*`
- **Alpha Vantage**: `alpha_*`
- **Volatility**: `vol_*`
- **Palm Oil**: `barchart_palm_*`
- **Policy**: `policy_trump_*`
- **ES Futures**: `es_*`
- **MES Futures**: `mes_*`
- **ZL Intraday**: `zl_*`

---

## 8. MIGRATION STATUS

### Legacy → New Mapping

| Legacy Dataset | Legacy Table | New Dataset | New Table | Status |
|---------------|--------------|-------------|-----------|--------|
| `forecasting_data_warehouse` | Various | `forecasting_data_warehouse` | Same | ✅ Active |
| `models_v4` | `production_training_data_*` | `training` | `zl_training_prod_allhistory_*` | ✅ Migrated |
| N/A | N/A | `raw_intelligence` | `intelligence_*_raw_daily` | 🆕 New |
| N/A | N/A | `signals` | `hidden_relationship_signals` | 🆕 Planned |

### Migration Progress

- ✅ **Staging Files**: Standardized naming (19 files)
- ✅ **Join Spec**: Updated to match new file names
- ✅ **Training Tables**: New structure in `training` dataset
- ⚠️ **News Collection**: Tables defined, scripts pending
- ⚠️ **Signals Dataset**: Not found in audit (may need creation)

---

## 9. ACTION ITEMS

### High Priority

- [ ] **Fix policy_trump_signals.parquet**: Investigate duplicate dates (all 25 rows have same date)
- [ ] **Create Alpha Vantage news collector**: `scripts/ingest/collect_alpha_news_sentiment.py`
- [ ] **Run BigQuery DDL**: Execute `create_alpha_news_tables.sql` to create news tables
- [ ] **Verify signals dataset**: Check if `signals` dataset exists or needs creation
- [ ] **Load staging to BigQuery**: Run load scripts to populate empty tables

### Medium Priority

- [ ] **Standardize MES file naming**: Align `mes_*` files with naming conventions
- [ ] **Document missing datasets**: Clarify which datasets are expected vs. missing
- [ ] **Create staging → BQ load script**: Automate loading of all staging files
- [ ] **Validate join pipeline**: Ensure all 17 join steps are working correctly

### Low Priority

- [ ] **Archive old staging files**: Remove `.bak` files and redundant copies
- [ ] **Document column mappings**: Create detailed column-level mapping documentation
- [ ] **Create data lineage diagram**: Visual representation of data flow

---

## 10. VERIFICATION AUDIT SUMMARY

### November 19, 2025 Fresh Audit

**Staging Files**:
- ✅ 19 files found, 523,291 total rows
- ⚠️ 1 file with duplicate dates (policy_trump_signals.parquet)
- ✅ All other files healthy

**BigQuery Tables**:
- ⚠️ 30 tables audited, all empty (expected for new structure)
- ✅ Datasets exist: `raw_intelligence`, `training`, `predictions`, `monitoring`
- ❌ Dataset missing: `signals` (not found in audit)

**Pipeline Validation**:
- ✅ All tests passing
- ✅ Final output: 2,025 rows × 1,175 columns
- ✅ Date range: 2000-03-15 to 2025-11-14

**News Collection**:
- ✅ ScrapeCreators collector ready
- ✅ Bucket classifier ready
- ❌ Alpha Vantage collector missing
- ❌ BigQuery tables not created yet

---

## 11. REFERENCE DOCUMENTS

### Audit Reports

- `docs/audit/FRESH_AUDIT_20251119_191350.md` - Latest comprehensive audit
- `docs/audit/FORENSIC_AUDIT_20251118_SECOND_REVIEW.md` - Previous audit with corrections
- `docs/audit/ALPHA_SCRAPECREATORS_WORKFLOW_ALIGNMENT.md` - Workflow alignment verification

### Planning Documents

- `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md` - Training strategy
- `docs/plans/FRESH_START_MASTER_PLAN.md` - Overall project plan
- `registry/join_spec.yaml` - Join specification (source of truth)

### Setup Documents

- `docs/setup/NEWS_COLLECTION_REGIME_BUCKETS.md` - News bucket taxonomy
- `docs/setup/ALPHA_NEWS_INTEGRATION_ALIGNED.md` - Alpha Vantage integration
- `config/bigquery/bigquery-sql/create_alpha_news_tables.sql` - BigQuery DDL

---

**Generated**: November 19, 2025  
**BigQuery Project**: `cbi-v14`  
**Region**: `us-central1`  
**Last Audit**: November 19, 2025 19:14:23
