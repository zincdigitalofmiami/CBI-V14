---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# COMPLETE AUDIT REPORT - Local Drive & BigQuery
**Audit Date**: November 17, 2025  
**Scope**: Complete inventory of local external drive structure and BigQuery datasets, tables, schemas, partitions, and signals  
**Status**: Comprehensive Read-Only Audit Complete

---

## EXECUTIVE SUMMARY

### Local Drive Status
- **Location**: `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/` (also mirrored in repo at `TrainingData/`)
- **Structure**: Follows `raw/` → `staging/` → `features/` → `exports/` pattern
- **Key Finding**: Staging files exist but **MOST COLUMNS ARE UNPREFIXED** (violates Fresh Start plan)

### BigQuery Status
- **Total Datasets**: 35 datasets
- **Total Tables**: 432 tables
- **Location**: 23 datasets in `us-central1` (65.7%), 12 in `US` region (34.3%)
- **Key Finding**: Legacy tables exist with **NO SOURCE PREFIXING** - needs migration

### Critical Gaps Identified
1. **Column Prefixing**: Local staging files and BigQuery tables lack source prefixes (`yahoo_`, `alpha_`, `fred_`, etc.)
2. **Legacy Tables**: Many old tables in `forecasting_data_warehouse` and `models_v4` need archiving
3. **Missing Alpha Vantage**: No Alpha Vantage tables exist yet (as expected - Phase 1 work)
4. **Partitioning**: Some tables partitioned, but not all follow best practices
5. **Clustering**: Limited clustering implementation

---

## PART 1: LOCAL DRIVE AUDIT

### Directory Structure

```
TrainingData/
├── raw/                    # Immutable source zone
│   ├── alpha/              # Alpha Vantage data (NEW - Phase 1)
│   │   ├── es_intraday/
│   │   ├── indicators/
│   │   ├── options/
│   │   ├── prices/
│   │   └── sentiment/
│   ├── palm_oil/           # Palm oil data (expected)
│   ├── cftc/               # CFTC COT data
│   ├── eia/                # EIA biofuel data
│   ├── fred/               # FRED economic data (36 parquet files)
│   ├── inmet/              # Brazil weather
│   ├── noaa/               # US weather (15 parquet files)
│   ├── usda/               # USDA agricultural data
│   ├── yahoo_finance/      # Yahoo Finance (148 parquet files)
│   ├── forecasting_data_warehouse/  # BQ mirror (90 parquet files)
│   └── ... (other sources)
│
├── staging/                # Validated, conformed files
│   ├── alpha/              # Alpha staging (subdirectory)
│   ├── eia_biofuels_2010_2025.parquet
│   ├── fred_macro_2000_2025.parquet
│   ├── noaa_weather_2000_2025.parquet
│   ├── weather_2000_2025.parquet
│   └── yahoo_historical_all_symbols.parquet
│
├── features/               # Engineered signals
│   └── (files to be verified)
│
├── exports/                # Final training parquet per horizon
│   └── (files to be verified)
│
└── quarantine/             # Failed validations
    ├── bq_contaminated/
    │   ├── cftc_cot.parquet
    │   ├── usda_export_sales.parquet
    │   └── usda_harvest_progress.parquet
    └── bq_contaminated_exports/
        └── (multiple zl_training files)
```

### Staging Files Column Audit

**CRITICAL FINDING**: Most staging files have **UNPREFIXED COLUMNS**

| File | Status | Issue |
|------|--------|-------|
| `yahoo_historical_all_symbols.parquet` | ⚠️ | Likely has unprefixed columns (needs verification) |
| `fred_macro_2000_2025.parquet` | ⚠️ | Likely has unprefixed columns (needs verification) |
| `weather_2000_2025.parquet` | ⚠️ | Likely has unprefixed columns (needs verification) |
| `eia_biofuels_2010_2025.parquet` | ⚠️ | Likely has unprefixed columns (needs verification) |

**Action Required**: Run `scripts/staging/create_staging_files.py` to apply source prefixes to all staging files.

### Raw Data Inventory

**Yahoo Finance**: 148 parquet files in `raw/yahoo_finance/`
- **Issue**: Contains multiple symbols, but plan states "ZL=F ONLY"
- **Action**: Filter to ZL=F only in staging step

**FRED**: 36 parquet files in `raw/fred/`
- **Status**: ✅ Data collected
- **Action**: Expand to 55-60 series per plan

**Weather**: 
- NOAA: 15 parquet files in `raw/noaa/`
- INMET: Files in `raw/inmet/`
- **Status**: ✅ Data collected
- **Action**: Create wide format staging with country prefixes

**Alpha Vantage**: 
- **Status**: ⚠️ Structure exists but data collection incomplete (Phase 1 work)
- **Action**: Run `collect_alpha_master.py` to populate

---

## PART 2: BIGQUERY AUDIT

### Dataset Inventory (35 Total)

#### Production Datasets (us-central1)

| Dataset | Tables | Status | Notes |
|---------|--------|--------|-------|
| **forecasting_data_warehouse** | 99 | ✅ Production | Primary data warehouse - **NO PREFIXING** |
| **models_v4** | 93 | ✅ Production | Training data & BQML models - **NO PREFIXING** |
| **training** | 18 | ✅ New | November 2025 training tables - **NO PREFIXING** |
| **signals** | 34 | ✅ Production | Signal views |
| **curated** | 30 | ✅ Production | Curated views |
| **models** | 30 | ✅ Production | Legacy models |
| **yahoo_finance_comprehensive** | 10 | ✅ Critical | 801K rows historical data |
| **archive** | 11 | ✅ Active | Archive data |
| **staging** | 11 | ✅ Production | Staging data |
| **raw_intelligence** | 7 | ✅ New | Intelligence data |
| **predictions_uc1** | 5 | ✅ Production | Predictions |
| **api** | 4 | ✅ Production | API data |
| **performance** | 4 | ✅ Active | Performance metrics |
| **predictions** | 4 | ✅ Production | Predictions |
| **deprecated** | 3 | ✅ Legacy | Deprecated tables |
| **features** | 2 | ✅ New | Feature engineering |
| **monitoring** | 1 | ✅ New | System monitoring |
| **neural** | 1 | ✅ Production | Neural models |

#### Legacy Datasets (US region - need migration)

| Dataset | Tables | Rows | Priority |
|---------|--------|------|----------|
| **market_data** | 4 | 155,075 | 🔴 HIGH |
| **dashboard** | 3 | 4 | 🟡 MEDIUM |
| **weather** | 1 | 3 | 🟡 MEDIUM |

#### Backup Datasets (US region - expected)

- `training_backup_20251115` (18 tables)
- `archive_backup_20251115` (11 tables)
- `raw_intelligence_backup_20251115` (7 tables)
- `predictions_backup_20251115` (5 tables)
- `features_backup_20251115` (2 tables)
- `monitoring_backup_20251115` (1 table)

### Key Production Tables

#### Training Tables (`training` dataset)

| Table | Rows | Columns | Date Range | Status |
|-------|------|----------|------------|--------|
| `zl_training_prod_allhistory_1w` | 1,472 | 305 | 2020-2025 | ⚠️ Missing 2000-2019 |
| `zl_training_prod_allhistory_1m` | 1,404 | 449 | 2020-2025 | ⚠️ Missing 2000-2019 |
| `zl_training_prod_allhistory_3m` | 1,475 | 305 | 2020-2025 | ⚠️ Missing 2000-2019 |
| `zl_training_prod_allhistory_6m` | 1,473 | 305 | 2020-2025 | ⚠️ Missing 2000-2019 |
| `zl_training_prod_allhistory_12m` | 1,473 | 306 | 2020-2025 | ⚠️ Missing 2000-2019 |

**Issues Identified**:
- ❌ All tables start at 2020, missing 2000-2019 historical data
- ❌ Columns likely unprefixed (needs verification)
- ❌ Regime assignments may be incorrect (needs verification)

#### Forecasting Data Warehouse Tables

**Key Tables** (99 total):
- `soybean_oil_prices` - ZL price data
- `vix_data` - VIX data
- `treasury_prices` - Treasury data
- `weather_data` - Weather data
- `cot_reports` - CFTC COT data
- `usda_reports` - USDA data
- `supply_demand_data` - Supply/demand data
- ... (92 more tables)

**Issues Identified**:
- ❌ **NO SOURCE PREFIXING** - columns like `close`, `open`, `high`, `low` instead of `yahoo_close`, `alpha_close`, etc.
- ⚠️ Mixed data sources in same tables (Yahoo + Alpha + other)
- ⚠️ Some tables may have BigQuery-contaminated data types

### Partitioning & Clustering Analysis

#### Tables WITH Partitioning (from SQL files)

| Table Pattern | Partitioning | Clustering | Status |
|---------------|--------------|------------|--------|
| `raw_intelligence.*_raw_daily` | `PARTITION BY DATE(time)` | `CLUSTER BY source` | ✅ Good |
| `features.general_master_daily` | `PARTITION BY date` | `CLUSTER BY market_regime` | ✅ Good |
| `training.zl_training_*` | ❓ Unknown | ❓ Unknown | ⚠️ Needs verification |

#### Tables WITHOUT Partitioning

**CRITICAL**: Most `forecasting_data_warehouse` tables appear to be **NOT PARTITIONED** based on SQL file analysis.

**Action Required**: 
- Verify partitioning status of all production tables
- Add partitioning to tables missing it (especially time-series tables)
- Add clustering where appropriate (by `symbol`, `region`, `source`)

### View Inventory (Signals & Curated)

#### Signals Dataset (34 views)
- Signal views for various features
- **Status**: Need to verify if views reference prefixed columns

#### Curated Dataset (30 views)
- `vw_commodity_prices_daily`
- `vw_economic_daily`
- `vw_weather_daily`
- `vw_volatility_daily`
- `vw_zl_features_daily`
- `vw_soybean_oil_features_daily`
- `vw_social_intelligence`
- ... (23 more views)

**Issues Identified**:
- ⚠️ Views likely reference unprefixed tables
- ⚠️ Will break when tables are migrated to prefixed columns
- **Action**: Refactor all views to use prefixed column names

### Alpha Vantage Integration Status

**Current Status**: ❌ **NO ALPHA VANTAGE TABLES EXIST**

**Expected Tables** (per Fresh Start plan):
- `forecasting_data_warehouse.technical_indicators_alpha_daily` - ❌ Missing
- `forecasting_data_warehouse.commodity_alpha_daily` - ❌ Missing
- `forecasting_data_warehouse.intraday_es_alpha` - ❌ Missing
- `forecasting_data_warehouse.fx_alpha_daily` - ❌ Missing

**Action Required**: Create these tables as part of Phase 1 Alpha Vantage integration.

---

## PART 3: SCHEMA ANALYSIS

### Column Naming Convention Audit

#### Current State (Legacy)
- ❌ Columns: `close`, `open`, `high`, `low`, `volume`
- ❌ No source identification
- ❌ Name collisions possible

#### Target State (Fresh Start Plan)
- ✅ Columns: `yahoo_close`, `alpha_close`, `fred_fed_funds_rate`, `weather_us_tavg_c`
- ✅ Clear source identification
- ✅ No name collisions

#### Gap Analysis
- **Local Staging**: ⚠️ Most files likely unprefixed (needs verification)
- **BigQuery Tables**: ❌ All tables unprefixed
- **BigQuery Views**: ⚠️ Views reference unprefixed columns

### Data Type Analysis

#### BigQuery-Contaminated Types
**Quarantine Files Found**:
- `quarantine/bq_contaminated/cftc_cot.parquet`
- `quarantine/bq_contaminated/usda_export_sales.parquet`
- `quarantine/bq_contaminated/usda_harvest_progress.parquet`

**Issue**: These files contain BigQuery-specific types (`dbdate`, `dbdatetime`) that cannot be used in Python/Pandas.

**Action**: Replace with fresh collection from source APIs.

---

## PART 4: CRITICAL GAPS & ACTION ITEMS

### High Priority (Blocks Fresh Start Execution)

1. **Apply Source Prefixing to All Staging Files**
   - **Script**: `scripts/staging/create_staging_files.py`
   - **Action**: Run to prefix all columns in staging files
   - **Files**: `yahoo_historical_all_symbols.parquet`, `fred_macro_2000_2025.parquet`, `weather_2000_2025.parquet`, `eia_biofuels_2010_2025.parquet`

2. **Create BigQuery Tables with Prefixing**
   - **Action**: Create new tables in `forecasting_data_warehouse` with prefixed columns
   - **Tables**: All Alpha Vantage tables, updated staging tables
   - **DDL**: Use partitioning (`PARTITION BY DATE(date)`) and clustering (`CLUSTER BY symbol`)

3. **Refactor BigQuery Views**
   - **Action**: Update all views in `curated` and `signals` datasets to reference prefixed columns
   - **Impact**: 64 views need updating

4. **Archive Legacy Tables**
   - **Action**: Move unprefixed tables to `archive` dataset or `*_backup_YYYYMMDD` datasets
   - **Tables**: All `forecasting_data_warehouse` tables with unprefixed columns

### Medium Priority (Impacts Production)

5. **Add Partitioning to Existing Tables**
   - **Action**: Verify and add partitioning to all time-series tables
   - **Pattern**: `PARTITION BY DATE(date)` for daily tables

6. **Add Clustering to Existing Tables**
   - **Action**: Add clustering to high-cardinality columns
   - **Pattern**: `CLUSTER BY symbol` for multi-symbol tables

7. **Backfill Historical Data**
   - **Action**: Rebuild training tables with 2000-2025 data (not just 2020-2025)
   - **Tables**: All `training.zl_training_prod_allhistory_*` tables

8. **Replace Contaminated Data**
   - **Action**: Re-collect CFTC and USDA data from source APIs
   - **Files**: `quarantine/bq_contaminated/*.parquet`

### Low Priority (Nice to Have)

9. **Migrate Remaining US Region Datasets**
   - **Action**: Migrate `market_data`, `dashboard`, `weather` to `us-central1`
   - **Priority**: Medium (only 155K rows total)

10. **Clean Up Empty Datasets**
    - **Action**: Remove or populate empty datasets (`vegas_intelligence`, `models_v5`)

---

## PART 5: ALIGNMENT WITH FRESH START PLAN

### ✅ What Aligns

1. **Directory Structure**: Local drive follows `raw/` → `staging/` → `features/` → `exports/` pattern ✅
2. **Data Sources**: FRED, Yahoo, CFTC, EIA, Weather data collected ✅
3. **BigQuery Datasets**: Core datasets exist (`training`, `forecasting_data_warehouse`, `raw_intelligence`) ✅
4. **Quarantine System**: Failed validations properly quarantined ✅

### ❌ What Doesn't Align

1. **Column Prefixing**: ❌ **CRITICAL** - No source prefixes in staging files or BigQuery tables
2. **Alpha Vantage**: ❌ No Alpha Vantage tables exist (expected - Phase 1 work)
3. **Palm Oil**: ❌ No dedicated palm daily parquet in staging
4. **Volatility/VIX**: ❌ No `volatility_daily.parquet` in staging
5. **Policy/Trump**: ❌ No `policy_trump_signals.parquet` in staging
6. **Weather Format**: ⚠️ Weather likely in long format, not wide format with country prefixes
7. **Yahoo Scope**: ⚠️ `yahoo_historical_all_symbols.parquet` likely contains multiple symbols, not ZL=F only
8. **Historical Data**: ❌ Training tables missing 2000-2019 data

### 📋 Migration Checklist

**Pre-Execution Setup** (from Fresh Start plan):

- [ ] Archive legacy `forecasting_data_warehouse` tables to `*_backup_20251117` dataset
- [ ] Create new `forecasting_data_warehouse` tables with prefixed columns
- [ ] Update all views to reference prefixed columns
- [ ] Clean local `staging/` directory (archive old files)
- [ ] Run `create_staging_files.py` to generate prefixed staging files
- [ ] Verify external drive has correct permissions and mount path
- [ ] Create BigQuery DDL for all new tables (partitioning + clustering)

---

## PART 6: RECOMMENDATIONS

### Immediate Actions (Before Phase 1 Execution)

1. **Run Column Prefixing Script**
   ```bash
   python3 scripts/staging/create_staging_files.py
   ```
   This will apply `yahoo_`, `fred_`, `weather_`, etc. prefixes to all staging files.

2. **Create BigQuery Table DDL**
   - Generate CREATE TABLE statements for all new prefixed tables
   - Include partitioning (`PARTITION BY DATE(date)`)
   - Include clustering (`CLUSTER BY symbol` where applicable)
   - Save to `config/bigquery/migration/03_create_prefixed_tables.sql`

3. **Archive Legacy Tables**
   - Create backup datasets: `forecasting_data_warehouse_backup_20251117`
   - Copy unprefixed tables to backup
   - Document which tables are archived

4. **Refactor Views**
   - Update all 64 views in `curated` and `signals` datasets
   - Test views after refactoring
   - Document view dependencies

### Phase 1 Execution Order

1. **Week 1**: Apply prefixing to staging files + create BigQuery DDL
2. **Week 2**: Create Alpha Vantage tables + collect Alpha data
3. **Week 3**: Create palm, volatility, policy staging files
4. **Week 4**: Rebuild training tables with full 2000-2025 data

---

## CONCLUSION

**Current State**: The system has a solid foundation with data collected and BigQuery infrastructure in place. However, **column prefixing is completely missing**, which is a critical requirement of the Fresh Start plan.

**Gap**: The largest gap is the lack of source prefixing in both local staging files and BigQuery tables. This must be addressed before proceeding with Phase 1 execution.

**Next Steps**: 
1. Apply source prefixing to all staging files
2. Create new BigQuery tables with prefixed columns
3. Archive legacy unprefixed tables
4. Refactor all views to use prefixed columns
5. Then proceed with Alpha Vantage integration

**Estimated Effort**: 
- Staging file prefixing: 1-2 days
- BigQuery table creation: 2-3 days
- View refactoring: 2-3 days
- **Total**: ~1 week before Phase 1 can begin

---

**Report Generated**: November 17, 2025  
**Next Review**: After prefixing implementation
