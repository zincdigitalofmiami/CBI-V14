# VERTEX AI TRUMP ERA FORECASTING PLAN

-------

## 4 HORIZONS: 1M, 3M, 6M, 12M

-------

## EXECUTIVE SUMMARY

-------

**Objective:** Train 4 Vertex AI AutoML models (1M, 3M, 6M, 12M) using all available datasets, starting with a baseline of **~444 features** and expanding to **2,000+** with our new comprehensive data pull. The models will be regime-aware, incorporating best practices from GS Quant and JPMorgan DNA methodologies.

**Performance Targets (REALISTIC):**
- **1M:** MAPE 2-4%, R² 0.75-0.85 (beats 7.8% baseline)
- **3M:** MAPE 3-6%, R² 0.65-0.80 (beats 7.8% baseline)
- **6M:** MAPE 4-8%, R² 0.55-0.75 (competitive)
- **12M:** MAPE 6-12%, R² 0.40-0.65 (industry standard)

**Business Value Focus:**
- Actionable procurement signals (buy/wait/hedge)
- Risk management (confidence intervals)
- Explainable results (feature importance)
- Better decisions than gut feel or simple trends

**Reality Check:**
- **Baseline:** 7.8% MAPE (current performance)
- **Institutional Standard:** 3-8% MAPE for commodity forecasting
- **Goldman Sachs/JPMorgan:** Typically 3-5% MAPE for 1M horizons
- **Success Definition:** Beat baseline + provide actionable insights for procurement
- **Value Proposition:** Even 3-5% MAPE provides real business value for procurement decisions

**Status:** PLANNING ONLY - NO EXECUTION

---

## VERTEX AI NAMING CONVENTIONS (QUICK REFERENCE)

**WHAT THIS IS:** Complete naming convention for all Vertex AI resources. Use these exact names when creating datasets, models, endpoints, and training jobs.

**Datasets:**
- `CBI V14 Vertex – 1M Dataset`
- `CBI V14 Vertex – 3M Dataset`
- `CBI V14 Vertex – 6M Dataset`
- `CBI V14 Vertex – 12M Dataset`

**Models:**
- `CBI V14 Vertex – AutoML 1M`
- `CBI V14 Vertex – AutoML 3M`
- `CBI V14 Vertex – AutoML 6M`
- `CBI V14 Vertex – AutoML 12M`

**Endpoints:**
- `CBI V14 Vertex – 1M Endpoint`
- `CBI V14 Vertex – 3M Endpoint`
- `CBI V14 Vertex – 6M Endpoint`
- `CBI V14 Vertex – 12M Endpoint`

**Training Jobs:**
- `CBI V14 Vertex – Training 1M`
- `CBI V14 Vertex – Training 3M`
- `CBI V14 Vertex – Training 6M`
- `CBI V14 Vertex – Training 12M`

**Rules:** Use en dash (–), "CBI V14 Vertex" prefix, horizon format "1M/3M/6M/12M", NO date/version/test suffixes.

---

## WORKSPACE ORGANIZATION

---

**CRITICAL: All work must follow strict clean workspace principles.**
- **Key Principles:** Zero duplicates, zero test/backup files, strict naming conventions, immediate cleanup
- **Directory Structure:** All Vertex AI work in `vertex-ai/` with organized subdirectories (data/, training/, prediction/, evaluation/, deployment/, config/)
- **Naming:** No `_test`, `_backup`, `_fixed`, `_safe`, `_v2` suffixes - all files go directly to production locations
- **Reference:** See `vertex-ai/README.md` and `bigquery-sql/vertex-ai/README.md` for directory structure and naming conventions

---

-------

## PART 2: QUANT-GRADE DATA PIPELINE ARCHITECTURE

-------

To ensure the highest data quality and build a robust, maintainable system, we are adopting a professional-grade, iterative data pipeline architecture inspired by institutional quant workflows. We will perfect the 1-month horizon dataset first, which will then serve as the immutable "golden template" for all other horizons.

-------

### GUIDING PRINCIPLES

-------
- **Metadata First:** We define the schema and rich metadata *before* processing data. Our `feature_metadata_catalog` is the embodiment of this principle.
- **Idempotency:** Every script is designed to be runnable multiple times with the same, predictable outcome, preventing errors from partial runs.
- **Staging Area:** All transformations occur in a separate staging area. Production tables are never modified directly until the final, atomic swap, ensuring data integrity.
- **Factor-Based & Regime-Aware:** As discussed, features are organized into logical "Factors" (e.g., Volatility, Inflation, Substitution Effects) and the model is made aware of "Market Regimes" (e.g., Trade War, Supply Chain Shock) to understand critical context.

---

-------

### THE PIPELINE STAGES: STEP-BY-STEP DATA PROCESSING WORKFLOW

-------

**WHAT THIS IS:** This section outlines the 3-phase process for building our production training tables. We start with metadata (the "golden template"), then validate and clean data, then finalize and scale to all horizons. Each phase must complete before moving to the next.

-------

#### PHASE 1: METADATA FOUNDATION (THE "GOLDEN TEMPLATE")

-------

**WHAT THIS IS:** Before processing any data, we create a master catalog that defines every feature's schema, type, source, and metadata. This catalog becomes our immutable reference for all future work.

**Files in This Phase:**

1.  **`bigquery-sql/vertex-ai/01_CREATE_FEATURE_METADATA_CATALOG.sql`**: ✅ **(Completed)**
    - **Purpose:** Creates a master table (`feature_metadata_catalog`) that defines the schema and rich metadata for all 444+ features
    - **What It Does:** Defines `factor_group`, `feature_type`, `source_system`, `unit_of_measurement`, `lag_days`, `normalization_method`, `description` for every feature
    - **Status:** ✅ Completed - table exists in BigQuery

2.  **`bigquery-sql/vertex-ai/02_POPULATE_FEATURE_CATALOG.py`**: ✅ **(Exists)**
    - **Purpose:** Auto-populates the metadata catalog using rule-based categorization
    - **What It Does:** Uses regex patterns to automatically assign `factor_group` and `feature_type` to features based on their names (e.g., features with "vix" → VOLATILITY factor group)
    - **Status:** ✅ File exists - ready to run

-------

#### PHASE 2: VALIDATION & CLEANING (1-MONTH HORIZON FIRST)

-------

**WHAT THIS IS:** We audit the existing `vertex_ai_training_1m_base` table (or `production_training_data_1m` if migrating) for data quality issues (NULLs, duplicates, outliers), then create a clean staging table with all fixes applied. This becomes our "golden template" for the other horizons.

**Files in This Phase:**

3.  **`bigquery-sql/vertex-ai/validate_data_quality.sql`**: ✅ **(Exists)**
    - **Purpose:** Comprehensive validation script to audit training data tables
    - **What It Does:** Checks for NULLs, duplicates, outliers, schema mismatches, and other integrity issues
    - **Status:** ✅ File exists - ready to run

4.  **`bigquery-sql/vertex-ai/04_CREATE_CLEAN_1M_STAGING.sql`**: ❌ **(TO BE CREATED)**
    - **Purpose:** Creates a clean staging table (`stg_vertex_ai_training_1m`) with all data quality fixes applied
    - **What It Does:** Applies imputation for NULLs, removes duplicates, handles outliers, ensures schema consistency
    - **Status:** ❌ **MUST BE CREATED** before proceeding

-------

#### PHASE 3: FINALIZATION & TEMPLATING

-------

**WHAT THIS IS:** Once the 1-month staging table is perfected, we atomically swap it into production. Then we use this perfected pipeline as a strict template to build the 3m, 6m, and 12m datasets with identical schemas.

**Steps in This Phase:**

5.  **Atomic Overwrite Script** (TO BE CREATED)
    - **Purpose:** Atomically replace production table with validated staging table
    - **What It Does:** `CREATE OR REPLACE TABLE vertex_ai_training_1m_base AS SELECT * FROM stg_vertex_ai_training_1m`
    - **Why:** Ensures data integrity - production tables never modified directly until final swap
    - **Status:** ❌ **MUST BE CREATED**

6.  **Scale to Other Horizons** (TO BE CREATED)
    - **Purpose:** Use the perfected 1m pipeline as a template for 3m, 6m, 12m
    - **What It Does:** Applies the same validation, cleaning, and schema enforcement to create `vertex_ai_training_3m_base`, `6m_base`, `12m_base` with identical feature lists
    - **Why:** Ensures perfect consistency across all horizons (required for Vertex AI)
    - **Status:** ❌ **MUST BE CREATED**

---

-------

## PHASE 1: DATA AUDIT & CONSOLIDATION

-------

**WHAT THIS IS:** This phase identifies all available data sources, their locations, ingestion mechanisms, and how they will be consolidated into our training tables. This is the foundation for building our feature set.

-------

### 1.1 IDENTIFY ALL DATA SOURCES

-------

**WHAT THIS IS:** A comprehensive inventory of every data source we have, where it's stored, how it's ingested, and what data points it provides. This ensures we don't miss any valuable features.

**BigQuery Tables to Audit:**
- `vertex_ai_training_1m_base` (or `production_training_data_1m` if migrating, ~444 features)
- `vertex_ai_training_3m_base` (or `production_training_data_3m` if migrating, ~300 features)
- `vertex_ai_training_6m_base` (or `production_training_data_6m` if migrating, ~300 features)
- `yahoo_finance_comprehensive.all_drivers_224_universe` (IN PROGRESS - will form the basis for feature expansion)
- All tables in `forecasting_data_warehouse`, `neural`, and `staging` datasets.

**Validated Primary Data Sources:**

> For a complete and detailed breakdown of every ingestion pipeline, including specific APIs, cron schedules, and destination tables, see the authoritative audit report:
> **[./docs/vertex-ai/INGESTION_PIPELINE_AUDIT.md](./docs/vertex-ai/INGESTION_PIPELINE_AUDIT.md)**

| Source Category                | Data Provider / System      | Ingestion Mechanism / API Endpoint                               | Key Data Points                                                  | Ingestion Script(s)                                   |
| ------------------------------ | --------------------------- | ---------------------------------------------------------------- | ---------------------------------------------------------------- | ----------------------------------------------------- |
| **Internal (Vegas)**           | Glide (Kevin's System)      | `POST https://api.glideapp.io/api/function/queryTables`            | Fryer usage, oil consumption, restaurant data                      | `ingest_glide_vegas_data.py`                            |
| **Social & News Intelligence** | Scrape Creator API          | `GET /v1/{platform}/{endpoint}` (e.g., twitter, facebook)        | Real-time & historical posts from key entities (USDA, CME, Reuters) | `scrape_creators_full_blast.py`, `trump_truth_social_monitor.py` |
| **Market Prices**              | Yahoo Finance               | `yfinance` Python Library                                        | 210+ symbol OHLCV, technicals                                    | `pull_yahoo_complete_enterprise.py`                   |
| **Economic**                   | FRED                        | `GET https://api.stlouisfed.org/fred/series/observations`        | Fed Funds, CPI, GDP, Dollar Index                                | `fred_economic_deployment.py`                         |
| **Commodities**                | USDA FAS                    | Web Scrape of `apps.fas.usda.gov`                                | Weekly Export Sales, cancellations                               | `ingest_usda_export_sales_weekly.py`                  |
| **Biofuel**                    | EPA                         | Web Scrape of `www.epa.gov`                                      | RIN Prices (D4, D5, D6)                                          | `ingest_epa_rin_prices.py`                            |
| **Sentiment**                  | CFTC                        | Direct Download/Scrape from `www.cftc.gov`                       | Commitment of Traders (COT) reports                              | `ingest_cftc_positioning_REAL.py`                     |
| **Weather**                    | INMET (Brazil), IEM, etc.   | APIs & Direct Scrapes                                            | Station-level data for 19+ key locations                         | `unified_weather_scraper.py`, `ingest_brazil_weather_inmet.py` |
| **Logistics**                  | Web Sources                 | Web Scrape (e.g., for Baltic Dry Index)                          | Freight rates, port data                                         | `ingest_baltic_dry_index.py`, `ingest_port_congestion.py` |
| **Internal**                   | CBI-V14 Derived Features    | BigQuery SQL Calculation                                         | Neural Scores (Big Eight), calculated spreads                    | N/A (Generated within BigQuery)                       |

**Note on Scrape Creator API:** This is a highly flexible, on-demand data source. Custom data pulls for specific topics, entities (companies, people), or historical backfilling can be rapidly configured for Facebook, Twitter, and LinkedIn, allowing us to surgically target emerging narratives or fill specific data gaps.

-------

### 1.2 HISTORICAL DATA RANGE

-------

**WHAT THIS IS:** Defines the date ranges we'll use for training data. We want maximum historical context (50+ years) but will weight recent/Trump-era data more heavily.

**Target:** 50+ years of historical data
- **Start Date:** 1970-01-01 (or earliest available)
- **End Date:** 2025-11-06 (current)
- **Trump Era Filter:** 2023-01-01 to 2025-11-06 for regime-specific training

-------

### 1.3 FEATURE ENGINEERING STRATEGY (GS QUANT INSPIRED)

-------

**WHAT THIS IS:** Our approach to creating features inspired by Goldman Sachs Quant and JPMorgan DNA methodologies. We organize features into logical categories and create interaction terms, lags, and regime-aware features.

**GS Quant Principles:**
- **Signal Packaging:** Create reusable, versioned signals (like GS Quant's `gs_quant` library)
- **Cross-Asset Features:** Palm oil, crude oil, FX pairs, agricultural spreads
- **Regime Indicators:** VIX stress levels, market regime classification
- **Causal Features:** Not just correlations, but Granger causality-verified drivers

**Feature Categories (Target: 2,000+ features after initial processing):**
1.  **Price & Technical Features (~1,500+ from Yahoo Pull)**
   - Close, Open, High, Low, Volume
   - RSI, MACD, Bollinger Bands, ATR, ADX
   - Moving Averages (7, 14, 30, 60, 90, 180, 365 day)
   - Momentum indicators, volatility measures

2. **Cross-Asset Correlations (48 features)**
   - Palm oil, crude oil, corn, wheat, soybean meal
   - FX pairs (DXY, EUR/USD, BRL/USD, CNY/USD)
   - Correlation windows: 7d, 30d, 90d, 180d

3. **Economic Indicators (50+ features)**
   - Fed funds rate, employment, inflation expectations
   - Credit spreads, term spreads, yield curves
   - GDP, PMI, consumer confidence

4. **Commodity Fundamentals (100+ features)**
   - USDA WASDE: stocks, production, exports
   - China imports, Brazil/Argentina exports
   - Crush margins, processing capacity

5. **Geopolitical/Policy (200+ features)**
   - Trump sentiment scores, policy impact scores
   - Tariff rates, trade war intensity
   - China relations, cancellation flags

6. **Market Structure (50+ features)**
   - CFTC positioning, open interest
   - VIX levels, stress indicators
   - Social sentiment, news sentiment

7. **Weather/Logistics (50+ features)**
   - Brazil/Argentina precipitation, temperature
   - Harvest pace, export capacity
   - Freight rates, port logistics

8. **Biofuel Markets (30+ features)**
   - RIN prices (D4, D5, D6)
   - RFS mandates, biodiesel/ethanol prices
   - Blending economics

9. **Interaction Terms (500+ features)**
   - VIX × Trump sentiment
   - China imports × tariff rates
   - RIN prices × crush margins
   - Cross-feature multiplications

10. **Lagged Features (1,000+ features)**
    - Lag 1, 3, 7, 14, 30, 60, 90 days
    - Rolling statistics (mean, std, min, max)

-------

### 1.4 DATA CONSOLIDATION SQL

-------

**WHAT THIS IS:** The SQL script that will consolidate ALL data sources into a single master training table. This is where raw data from multiple sources gets joined, transformed, and feature-engineered into our final training dataset.

**Create Master Training Table:**
```sql
-- VERTEX_AI_MASTER_TRAINING_TABLE.sql
-- Consolidates ALL data sources into single table
-- 50+ years, 6k+ features
-- Regime filter: Trump era (2023-2025) for training
```

**Key Requirements:**
- Single table with ALL features
- Date range: 1970-01-01 to 2025-11-06
- Target columns: `target_1m`, `target_3m`, `target_6m`, `target_12m`
- All features COALESCED (no NULLs)
- Feature names: `f0001` through `f6000+` (standardized naming)

---

-------

## PHASE 2: VERTEX AI DATASET SETUP

-------

**WHAT THIS IS:** This phase prepares our BigQuery training tables for Vertex AI. We need to ensure the data format, schema, and structure meet Vertex AI's requirements before we can register datasets and start training.

-------

### 2.1 DATASET EXPORT STRATEGY

-------

**WHAT THIS IS:** Decides how we'll get our BigQuery data into Vertex AI - either direct BigQuery connection (recommended) or Cloud Storage export (backup option).

**Option A: BigQuery Direct Export (Recommended)**
- Vertex AI can read directly from BigQuery
- No intermediate CSV files needed
- Handles large datasets efficiently

**Option B: Cloud Storage Export**
- Export to GCS bucket as CSV/Parquet
- Use for backup or if BigQuery direct fails

-------

### 2.2 DATASET STRUCTURE REQUIREMENTS

-------

**WHAT THIS IS:** The exact requirements Vertex AI has for tabular regression datasets - size limits, column counts, target column specifications, and time column requirements. Our data must meet ALL of these before training.

**Vertex AI Tabular AutoML Requirements:**
- **Format:** BigQuery table or CSV in Cloud Storage
- **Size:** Up to 100 GB
- **Rows:** 1,000 to 100,000,000
- **Columns:** 3 to 1,000 (we'll use feature selection if >1,000)
- **Target Column:** Single numeric column per model
- **Time Column:** `date` column for time series splitting

**Dataset Naming (ESTABLISHED CONVENTIONS):**

**APPROVED NAMING CONVENTION (All follow `vertex_ai_training_*` pattern):**

**Stage 1: Staging Tables (Raw Consolidation)**
- `cbi-v14.models_v4.stg_vertex_ai_training_1m` - Raw features consolidated from sources
- `cbi-v14.models_v4.stg_vertex_ai_training_3m` - Raw features consolidated from sources
- `cbi-v14.models_v4.stg_vertex_ai_training_6m` - Raw features consolidated from sources
- `cbi-v14.models_v4.stg_vertex_ai_training_12m` - Raw features consolidated from sources
- **Purpose:** Intermediate staging area - raw data consolidation, feature engineering, schema alignment

**Stage 2: Base Tables (Cleaned, Filtered, Before Weights)**
- `cbi-v14.models_v4.vertex_ai_training_1m_base` - Cleaned, filtered, 1,000 features, targets calculated, NO weights
- `cbi-v14.models_v4.vertex_ai_training_3m_base` - Cleaned, filtered, 1,000 features, targets calculated, NO weights
- `cbi-v14.models_v4.vertex_ai_training_6m_base` - Cleaned, filtered, 1,000 features, targets calculated, NO weights
- `cbi-v14.models_v4.vertex_ai_training_12m_base` - Cleaned, filtered, 1,000 features, targets calculated, NO weights
- **Purpose:** Base tables with all features, targets, and data quality fixes. Used as foundation for final Vertex AI tables.
- **Migration Note:** These will replace existing `production_training_data_*` tables (renamed to follow new convention)

**Stage 3: Final Tables (WITH Regime Weights - Feeds Vertex AI)**
- `cbi-v14.models_v4.vertex_ai_training_1m` - Final 1-month table with `training_weight` and `market_regime` columns (feeds Vertex AI)
- `cbi-v14.models_v4.vertex_ai_training_3m` - Final 3-month table with regime weights (feeds Vertex AI)
- `cbi-v14.models_v4.vertex_ai_training_6m` - Final 6-month table with regime weights (feeds Vertex AI)
- `cbi-v14.models_v4.vertex_ai_training_12m` - Final 12-month table with regime weights (feeds Vertex AI)
- **Purpose:** Final tables ready for Vertex AI. Includes ALL features from base tables PLUS `training_weight` and `market_regime` columns for regime-based training.
- **Source:** Created from `vertex_ai_training_*_base` tables by adding regime weights via SQL transformation.

**Vertex AI Resource Naming (ESTABLISHED CONVENTIONS):**

**Vertex AI Datasets (Display Names):**
- `CBI V14 Vertex – 1M Dataset` - 1-month horizon training dataset
- `CBI V14 Vertex – 3M Dataset` - 3-month horizon training dataset
- `CBI V14 Vertex – 6M Dataset` - 6-month horizon training dataset
- `CBI V14 Vertex – 12M Dataset` - 12-month horizon training dataset

**Vertex AI AutoML Models (Display Names):**
- `CBI V14 Vertex – AutoML 1M` - 1-month horizon AutoML model
- `CBI V14 Vertex – AutoML 3M` - 3-month horizon AutoML model
- `CBI V14 Vertex – AutoML 6M` - 6-month horizon AutoML model
- `CBI V14 Vertex – AutoML 12M` - 12-month horizon AutoML model

**Vertex AI Endpoints (Display Names):**
- `CBI V14 Vertex – 1M Endpoint` - 1-month horizon prediction endpoint
- `CBI V14 Vertex – 3M Endpoint` - 3-month horizon prediction endpoint
- `CBI V14 Vertex – 6M Endpoint` - 6-month horizon prediction endpoint
- `CBI V14 Vertex – 12M Endpoint` - 12-month horizon prediction endpoint

**Vertex AI Training Jobs (Display Names):**
- `CBI V14 Vertex – Training 1M` - 1-month horizon training job
- `CBI V14 Vertex – Training 3M` - 3-month horizon training job
- `CBI V14 Vertex – Training 6M` - 6-month horizon training job
- `CBI V14 Vertex – Training 12M` - 12-month horizon training job

**Naming Convention Rules:**
- ✅ All resources use "CBI V14 Vertex" prefix
- ✅ Use en dash (–) not hyphen (-) for separation
- ✅ Horizon format: "1M", "3M", "6M", "12M" (not "1-month" or "1m")
- ✅ Resource type clearly stated: "Dataset", "AutoML", "Endpoint", "Training"
- ❌ NO date suffixes (`_20251107`)
- ❌ NO version suffixes (`_v1`, `_v2`, `_FINAL`)
- ❌ NO test/backup suffixes (`_test`, `_backup`)

**Raw Data Warehouse Tables:**
- `cbi-v14.forecasting_data_warehouse.*` - All raw ingested data
- `cbi-v14.yahoo_finance_comprehensive.*` - Yahoo Finance raw data

**Metadata & Schema Tables:**
- `cbi-v14.models_v4.feature_metadata_catalog` - Master feature metadata registry
- `cbi-v14.models_v4.training_schema_contract` - Schema contract table (if created)

-------

### 2.3 SCHEMA, METADATA, REGIME, AND TRANSFORMATION ARCHITECTURE

-------

**WHAT THIS IS:** This is the CORE architectural section that defines how we handle schema consistency, feature metadata, regime-based training, and data transformation. This section addresses the critical gap: raw data ingestion → production training tables.

**CRITICAL DISCOVERY:** All ingestion scripts write to raw warehouse tables (`forecasting_data_warehouse`, `yahoo_finance_comprehensive`). **NO transformation pipeline exists** to move data from raw tables to `models_v4.vertex_ai_training_*_base` tables. This is a fundamental architectural gap that must be addressed before any training can occur.

-------

#### 2.3.1 SCHEMA STANDARDIZATION & METADATA ARCHITECTURE

-------

**WHAT THIS IS:** Defines how we ensure all training tables have identical schemas (same columns, same data types, same order). Also covers the Feature Metadata Catalog - our master registry of every feature's definition, type, source, and metadata. This is the "golden template" that enforces consistency.

**Feature Metadata Catalog (The Golden Template):**
- **Table:** `cbi-v14.models_v4.feature_metadata_catalog`
- **Purpose:** Single source of truth for all feature definitions, types, sources, and metadata
- **Schema:** `column_name`, `ordinal_position`, `data_type`, `is_nullable`, `factor_group`, `feature_type`, `source_system`, `unit_of_measurement`, `lag_days`, `normalization_method`, `description`
- **Status:** Created via `bigquery-sql/vertex-ai/01_CREATE_FEATURE_METADATA_CATALOG.sql` ✅ (completed)
- **Population:** Auto-populated via `bigquery-sql/vertex-ai/02_POPULATE_FEATURE_CATALOG.py` ✅ using rule-based categorization

**Schema Contract Requirements:**
- **Identical Feature Count:** All 4 horizon tables (1m, 3m, 6m, 12m) must have EXACTLY the same feature list (same order, same count)
- **Fixed Feature Names:** No dynamic naming - all features must match `feature_metadata_catalog`
- **Data Type Consistency:** All features must have identical data types across all horizon tables
- **Date Column Standardization:** Single `date` column (DATE type, not INTEGER, not DATETIME) - no duplicates, no NULLs
- **Target Column Validation:** Each table has ONE unambiguous numeric target column (`target_1m`, `target_3m`, `target_6m`, `target_12m`) with zero NULLs

**Schema Validation Checklist (Pre-Training):**
1. ✅ **Feature Count Equality:** `SELECT COUNT(*) FROM vertex_ai_training_1m_base LIMIT 0` must equal all other horizons
2. ✅ **Date Column Validation:** `SELECT COUNT(*) AS total, COUNT(DISTINCT date) AS distinct_dates` - must be equal (no duplicates)
3. ✅ **Target Column NULL Check:** `SELECT COUNTIF(target_1m IS NULL)` - must be 0
4. ✅ **String Feature Audit:** Identify all STRING columns, drop those with >5000 unique values (AutoML limit)
5. ✅ **Boolean Conversion:** Convert all BOOLEAN columns to INT64 (1/0) - AutoML doesn't support BOOLEAN
6. ✅ **Reserved Name Check:** Rename any columns matching reserved names: `weight`, `class`, `id`, `prediction`, `target`, `time`, `split`, `fold`, `dataset`
7. ✅ **Null Cleansing:** Zero tolerance for NULLs - use `COALESCE` or imputation before training
8. ✅ **Frequency Normalization:** All data must be at daily granularity - expand weekly/monthly data via forward-fill

-------

#### 2.3.2 TRANSFORMATION PIPELINE ARCHITECTURE (CRITICAL - MISSING)

-------

**WHAT THIS IS:** The ETL pipeline that transforms raw data from warehouse tables into production training tables. Currently DOES NOT EXIST - this is the #1 blocker. Defines the 3-stage process: Raw Landing → Staging (transformations) → Atomic Overwrite to Production.

**Current State:**
- **Raw Data:** All ingestion scripts write to `forecasting_data_warehouse.*` and `yahoo_finance_comprehensive.*`
- **Base Tables:** `models_v4.vertex_ai_training_*_base` (or `production_training_data_*` if migrating) exist with 444 features (base tables, no regime weights)
- **Final Vertex AI Tables:** `models_v4.vertex_ai_training_*` should exist WITH regime weights (currently missing or incomplete)
- **Gap:** NO ETL pipeline connects raw data → base tables (`vertex_ai_training_*_base`) → final vertex_ai_training tables

**Required Transformation Pipeline:**

**Stage 1: Raw Data Landing (EXISTS)**
- Tables: `forecasting_data_warehouse.*`, `yahoo_finance_comprehensive.*`
- Purpose: Receive raw data from ingestion scripts
- Status: ✅ Working (but data not flowing to production)

**Stage 2: Staging Tables (MUST BUILD)**
- Tables: `models_v4.stg_vertex_ai_training_*` (e.g., `stg_vertex_ai_training_1m`)
- Purpose: Intermediate transformation area - apply all fixes, feature engineering, schema alignment, AND regime weights
- Requirements:
  - Read from raw warehouse tables OR from base `vertex_ai_training_*_base` tables
  - Map to production feature names (via `feature_metadata_catalog`)
  - Apply feature engineering (interactions, lags, derived features)
  - Handle NULLs, duplicates, outliers
  - Enforce schema contract (match production exactly)
  - Add regime weights (`training_weight` column) and regime labels (`market_regime` column)
  - Idempotent (can run multiple times safely)

**Stage 3: Atomic Overwrite (MUST BUILD)**
- Process: Replace final Vertex AI training table with validated staging table in single operation
- Purpose: Ensure data integrity - final `vertex_ai_training_*` tables never modified directly until final swap
- Implementation: `CREATE OR REPLACE TABLE vertex_ai_training_1m AS SELECT * FROM stg_vertex_ai_training_1m`
- Note: `vertex_ai_training_*` tables are the final tables WITH regime weights that feed Vertex AI

**Transformation Scripts Required (ALL TO BE CREATED):**
1. **`vertex-ai/data/TRANSFORM_YAHOO_TO_PRODUCTION.py`**: ❌ **(TO BE CREATED)** Transform Yahoo Finance raw data → production features
2. **`bigquery-sql/vertex-ai/TRANSFORM_WAREHOUSE_TO_PRODUCTION.sql`**: ❌ **(TO BE CREATED)** Transform all `forecasting_data_warehouse` tables → production features
3. **`bigquery-sql/vertex-ai/VALIDATE_STAGING_SCHEMA.sql`**: ❌ **(TO BE CREATED)** Validate staging tables match production schema contract
4. **`bigquery-sql/vertex-ai/ATOMIC_OVERWRITE_PRODUCTION.sql`**: ❌ **(TO BE CREATED)** Atomic swap of staging → production

**Existing Related Files:**
- ✅ `bigquery-sql/vertex-ai/schema_contract.sql` - Schema contract table creation
- ✅ `bigquery-sql/vertex-ai/validate_data_quality.sql` - Data quality validation
- ✅ `vertex-ai/data/validate_schema.py` - Python schema validation script

**Yahoo Finance Specific Issues:**
- **Date Column:** Currently INTEGER (WRONG) - must convert to DATE before transformation
- **Feature Mapping:** Raw Yahoo columns (e.g., `close`, `volume`, `rsi_14`) must map to production feature names (e.g., `zl_price_current`, `zl_volume`, `zl_rsi_14`)
- **Symbol Pivoting:** 224 symbols must be pivoted to wide format (224 symbols × 7 indicators = 1,568 potential columns)
- **Feature Selection:** Must select top 50-100 most correlated symbols to stay within Vertex AI 1,000 column limit

-------

#### 2.3.3 REGIME-BASED TRAINING STRATEGY (DATE-BASED + TOPIC-BASED)

-------

**WHAT THIS IS:** How we use Vertex AI's `weight` column to emphasize relevant data periods (Trump 2.0 era, Trade War era) while still using ALL 125 years of historical data. Combines date-based regimes (structural breaks) with topic-based regimes (tariffs, trade wars, inflation effects) for intelligent weighting.

**Vertex AI Weight Column Implementation:**
- **Column Name:** `training_weight` (numeric, 0-10,000)
- **Purpose:** Emphasize relevant data periods without discarding historical context
- **Advantage:** Use ALL 125 years of data (16,824 rows) with intelligent weighting vs. filtering to 700 rows

**Date-Based Regimes (Structural Breaks):**

| Regime | Date Range | Weight | Rationale |
|--------|-----------|--------|-----------|
| **Trump 2.0 Era** | 2023-01-01 to 2025-11-06 | **5,000** | Current regime - MAXIMUM emphasis |
| **Trade War Era** | 2017-01-01 to 2019-12-31 | **1,500** | Most similar to current - critical for learning tariff impacts |
| **Inflation Era** | 2021-01-01 to 2022-12-31 | **1,200** | Recent inflation dynamics - relevant for substitution effects |
| **COVID Crisis** | 2020-01-01 to 2020-12-31 | **800** | Supply chain disruption patterns |
| **Financial Crisis** | 2008-01-01 to 2009-12-31 | **500** | Extreme volatility learning |
| **Commodity Crash** | 2014-01-01 to 2016-12-31 | **400** | Dollar surge patterns |
| **QE/Supercycle** | 2010-01-01 to 2013-12-31 | **300** | Commodity boom dynamics |
| **Pre-Crisis** | 2000-01-01 to 2007-12-31 | **100** | Baseline patterns |
| **Historical** | Pre-2000 | **50** | Pattern learning only |

**Topic-Based Regimes (Factor-Specific Weighting):**

In addition to date-based regimes, we implement **topic-based regime indicators** that can overlap and provide factor-specific context:

| Topic Regime | Description | Key Features | Weight Multiplier |
|--------------|-------------|--------------|-------------------|
| **Tariffs** | Active tariff periods | `tariff_rate`, `china_tariff_threat`, `section_301_active` | ×1.5 |
| **Trade Wars** | Trade conflict periods | `china_relations_score`, `trade_war_intensity`, `export_cancellations` | ×1.3 |
| **Trade Developments** | New trade deals/agreements | `argentina_export_tax`, `new_trade_deals`, `export_credit_programs` | ×1.2 |
| **Inflation Effects** | High inflation periods | `cpi_yoy`, `soybean_oil_substitution`, `cheaper_alternatives_demand` | ×1.4 |
| **Trump Effects** | Trump policy actions | `trump_sentiment_score`, `executive_orders`, `truth_social_posts` | ×2.0 |

**Regime Weight Calculation:**
```sql
-- Base weight from date-based regime
base_weight = CASE 
  WHEN date >= '2023-01-01' THEN 5000
  WHEN date >= '2017-01-01' AND date < '2020-01-01' THEN 1500
  -- ... etc
END

-- Apply topic-based multipliers
final_weight = base_weight * 
  CASE 
    WHEN trump_sentiment_score > 0.7 THEN 2.0  -- Trump Effects
    WHEN tariff_rate > 0.25 THEN 1.5  -- Tariffs
    WHEN cpi_yoy > 0.05 THEN 1.4  -- Inflation Effects
    WHEN china_relations_score < -0.5 THEN 1.3  -- Trade Wars
    WHEN new_trade_deals = TRUE THEN 1.2  -- Trade Developments
    ELSE 1.0
  END
```

**Regime Label Column:**
- **Column Name:** `market_regime` (STRING)
- **Purpose:** Human-readable regime classification for analysis
- **Values:** `'Trump_2.0'`, `'Trade_War'`, `'Inflation_Era'`, `'COVID_Crisis'`, `'Financial_Crisis'`, `'Commodity_Crash'`, `'QE_Supercycle'`, `'Pre_Crisis'`, `'Historical'`

**Regime-Aware Feature Engineering:**
- **Regime-Specific Interaction Terms:** `trump_sentiment × tariff_rate` (only in Trump/Trade War regimes)
- **Crisis Amplifiers:** `vix_close × crush_margin_volatility` (only in crisis regimes)
- **Policy Uncertainty:** `trump_sentiment × policy_uncertainty_index` (only in Trump 2.0 regime)

-------

#### 2.3.4 FACTOR-BASED FEATURE ORGANIZATION

-------

**WHAT THIS IS:** How we organize features into logical "Factor Groups" (PRICE, VOLATILITY, MOMENTUM, MONETARY_POLICY, etc.) inspired by GS Quant and JPMorgan DNA methodologies. This makes features interpretable and enables regime-aware modeling (different factors matter in different regimes).

**Factor Groups (GS Quant / JPM DNA Style):**
Features are organized into logical "Factors" for interpretability and regime-aware modeling:

| Factor Group | Description | Example Features | Regime Relevance |
|-------------|-------------|------------------|------------------|
| **PRICE** | Absolute price levels | `zl_price_current`, `corn_price`, `palm_oil_price` | All regimes |
| **VOLATILITY** | Volatility indicators | `vix_close`, `atr_14`, `bb_width` | Crisis regimes (×1.5) |
| **MOMENTUM** | Momentum indicators | `rsi_14`, `macd`, `roc_10` | All regimes |
| **TREND** | Trend indicators | `ma_7d`, `ma_30d`, `ma_200d` | All regimes |
| **VOLUME** | Volume indicators | `zl_volume`, `volume_ratio` | All regimes |
| **MONETARY_POLICY** | Fed/central bank policy | `fed_funds_rate`, `dxy`, `yield_10y` | Inflation era (×1.4) |
| **POSITIONING** | Market positioning | `cftc_managed_money_net`, `open_interest` | All regimes |
| **SUBSTITUTION_EFFECT** | Substitution dynamics | `palm_oil_spread`, `rapeseed_oil_spread`, `cpi_yoy` | Inflation era (×1.4) |
| **NEURAL_FACTOR** | Proprietary neural scores | `dollar_neural_score`, `fed_neural_score`, `crush_neural_score` | All regimes |
| **GROWTH** | Economic growth | `gdp_growth`, `unemployment_rate` | All regimes |
| **INFLATION** | Inflation indicators | `cpi`, `ppi`, `inflation_expectations` | Inflation era (×1.4) |
| **TARGET** | Target variables | `target_1m`, `target_3m`, `target_6m`, `target_12m` | N/A (excluded from features) |

**Factor Group Population:**
- **Auto-Population:** `bigquery-sql/vertex-ai/02_POPULATE_FEATURE_CATALOG.py` ✅ uses regex rules to auto-categorize features
- **Manual Override:** Update `feature_metadata_catalog` table directly for edge cases
- **Validation:** Ensure all features have a `factor_group` before training

-------

#### 2.3.5 FEATURE SELECTION STRATEGY (JPMORGAN DNA INSPIRED)

-------

**WHAT THIS IS:** Our approach to selecting which features to include in training. We start with 6,000+ potential features, transform to 2,000+, then select top 1,000 for Vertex AI (its limit). Uses JPMorgan DNA principles: regime-aware, causal, stable, interpretable features.

**JPMorgan DNA Principles:**
- **Regime-Aware Features:** Different features matter in different market regimes
- **Causal Features:** Focus on features with economic causality, not just correlation
- **Stability:** Features should be stable across time periods
- **Interpretability:** Features should have clear economic meaning

**Feature Selection Approach:**
1. **Initial Filter:** Remove features with >90% NULL values
2. **Correlation Filter:** Remove highly correlated features (r > 0.95)
3. **Regime-Specific Selection:** Use different feature sets for different market regimes (via weighting, not exclusion)
4. **Causal Verification:** Use Granger causality tests to verify causal relationships
5. **Stability Check:** Features must be stable across training/validation splits
6. **Factor Balance:** Ensure representation from all factor groups (don't over-weight one factor)

**Target Feature Count:**
- **Initial:** 6,000+ features (all available from raw data)
- **After Transformation:** 2,000+ features (after pivoting Yahoo, adding interactions/lags)
- **After Selection:** 1,000 features (Vertex AI limit - top predictive features)
- **Vertex AI Feature Transform Engine:** Will automatically select best features from the 1,000 submitted

**Feature Selection Tiers:**
- **Tier 1 (MUST INCLUDE - ~200 columns):** Target variables, date, core derived features, VIX, DXY, Fed funds, ZL prices
- **Tier 2 (HIGH VALUE - ~400 columns):** Top 50 correlated Yahoo symbols, economic indicators (|correlation| > 0.3), weather, China imports, RIN prices
- **Tier 3 (INTERACTION/LAG - ~400 columns):** VIX × Trump sentiment, China imports × Tariffs, RIN × Crush margins, lag features (7d, 14d, 30d, 60d)

---

-------

## PHASE 3: VERTEX AI MODEL TRAINING

-------

**WHAT THIS IS:** This phase covers the actual training of our 4 Vertex AI AutoML models (1M, 3M, 6M, 12M horizons). Includes model configuration, training settings, regime weighting, and feature transform engine usage.

-------

### 3.1 MODEL CONFIGURATION (4 HORIZONS)

-------

**WHAT THIS IS:** Defines the 4 separate models we'll train, one for each forecasting horizon. Each model has its own dataset, target column, training budget, and optimization objective.

**Model 1: 1 Month Horizon**
- **Vertex AI Dataset:** `CBI V14 Vertex – 1M Dataset`
- **BigQuery Source:** `cbi-v14.models_v4.vertex_ai_training_1m` (WITH regime weights)
- **Model Display Name:** `CBI V14 Vertex – AutoML 1M`
- **Endpoint Display Name:** `CBI V14 Vertex – 1M Endpoint`
- **Target:** `target_1m` (22 trading days forward)
- **Weight Column:** `training_weight` (for regime-based training)
- **Training Budget:** $100 (20 hours)
- **Optimization Objective:** Minimize RMSE

**Model 2: 3 Month Horizon**
- **Vertex AI Dataset:** `CBI V14 Vertex – 3M Dataset`
- **BigQuery Source:** `cbi-v14.models_v4.vertex_ai_training_3m` (WITH regime weights)
- **Model Display Name:** `CBI V14 Vertex – AutoML 3M`
- **Endpoint Display Name:** `CBI V14 Vertex – 3M Endpoint`
- **Target:** `target_3m` (66 trading days forward)
- **Weight Column:** `training_weight` (for regime-based training)
- **Training Budget:** $100 (20 hours)
- **Optimization Objective:** Minimize RMSE

**Model 3: 6 Month Horizon**
- **Vertex AI Dataset:** `CBI V14 Vertex – 6M Dataset`
- **BigQuery Source:** `cbi-v14.models_v4.vertex_ai_training_6m` (WITH regime weights)
- **Model Display Name:** `CBI V14 Vertex – AutoML 6M`
- **Endpoint Display Name:** `CBI V14 Vertex – 6M Endpoint`
- **Target:** `target_6m` (132 trading days forward)
- **Weight Column:** `training_weight` (for regime-based training)
- **Training Budget:** $100 (20 hours)
- **Optimization Objective:** Minimize RMSE

**Model 4: 12 Month Horizon**
- **Vertex AI Dataset:** `CBI V14 Vertex – 12M Dataset`
- **BigQuery Source:** `cbi-v14.models_v4.vertex_ai_training_12m` (WITH regime weights)
- **Model Display Name:** `CBI V14 Vertex – AutoML 12M`
- **Endpoint Display Name:** `CBI V14 Vertex – 12M Endpoint`
- **Target:** `target_12m` (264 trading days forward)
- **Weight Column:** `training_weight` (for regime-based training)
- **Training Budget:** $100 (20 hours)
- **Optimization Objective:** Minimize RMSE

-------

### 3.2 TRAINING CONFIGURATION (GS QUANT + JPMORGAN DNA BEST PRACTICES)

-------

**WHAT THIS IS:** The exact Vertex AI AutoML configuration settings we'll use, including regime-based weighting, time series splitting, optimization objectives, and quantile predictions. This is the "recipe" for training our models.
```python
{
    "optimization_objective": "minimize-rmse",  # RMSE for balanced error handling
    "train_budget_milli_node_hours": 20000,  # 20 hours
    "disable_early_stopping": False,
    "weight_column_name": "training_weight",  # CRITICAL: Use regime-based weighting
    "optimization_objective_recall_value": None,
    "optimization_objective_precision_value": None,
    "data_split_method": "time_series",  # Sequential split for time series
    "data_split_eval_fraction": 0.2,  # 20% for validation
    "predefined_split_column_name": None,
    "timestamp_split_column_name": "date",  # Time-based split (must be DATE type, not INTEGER)
    "stratified_split_column_name": None,
    "cv_fold_column_name": None,
    "export_evaluated_data_items": True,  # Export predictions for analysis
    "export_evaluated_data_items_bigquery_prefix": "cbi-v14.models_v4.vertex_ai_evaluated_",
    "export_evaluated_data_items_override_destination": True,
    "quantiles": [0.1, 0.5, 0.9],  # P10, P50, P90 quantiles
    "validation_options": "validation_split",
    "budget_milli_node_hours": 20000
}
```

**Regime-Weighted Training (JPMorgan DNA Approach):**
- **Weight Column:** `training_weight` (0-10,000) - emphasizes relevant periods without discarding history
- **All Historical Data:** Use ALL 125 years (16,824 rows) with intelligent weighting
- **Trump 2.0 Emphasis:** Weight 5,000 (50-100x vs historical data)
- **Trade War Emphasis:** Weight 1,500 (most similar to current regime)
- **Topic-Based Multipliers:** Apply additional weight multipliers for tariffs (×1.5), Trump effects (×2.0), inflation (×1.4), trade wars (×1.3)
- **Regime Labels:** Include `market_regime` column for analysis and interpretability
- **Regime-Aware Features:** Include regime-specific interaction terms (e.g., `trump_sentiment × tariff_rate` only in Trump/Trade War regimes)

-------

### 3.3 FEATURE TRANSFORM ENGINE (VERTEX AI)

-------

**WHAT THIS IS:** Vertex AI's automated feature selection and transformation system. It will automatically rank features by importance, handle missing values, scaling, and encoding. We provide 1,000 features, it selects the best ones.
- Automatically handles feature selection
- Ranks features by importance
- Creates consistent feature transformations
- Handles missing values, scaling, encoding

**Manual Feature Engineering (Before Vertex AI):**
- Create all 6,000+ features in BigQuery
- Let Vertex AI Feature Transform Engine select top features
- Export feature importance rankings

---

-------

## PHASE 4: MODEL EVALUATION & VALIDATION

-------

**WHAT THIS IS:** After training, we evaluate model performance using multiple metrics (MAE, RMSE, MAPE, R²), validate on out-of-sample data, and analyze feature importance. This ensures models meet our performance targets before deployment.

-------

### 4.1 EVALUATION METRICS

-------

**WHAT THIS IS:** The specific metrics we'll use to measure model performance. Includes primary metrics (MAE, RMSE, MAPE, R²), realistic institutional targets, baseline comparisons, and business value metrics (directional accuracy, confidence intervals).

**Primary Metrics:**
- **MAE (Mean Absolute Error):** Primary optimization target
- **RMSE (Root Mean Squared Error):** Penalizes large errors
- **MAPE (Mean Absolute Percentage Error):** Percentage accuracy
- **R² (Coefficient of Determination):** Model fit quality

**Target Performance (REALISTIC INSTITUTIONAL-GRADE):**
- **1M Horizon:** MAPE 2-4%, R² 0.75-0.85 (Excellent)
- **3M Horizon:** MAPE 3-6%, R² 0.65-0.80 (Good)
- **6M Horizon:** MAPE 4-8%, R² 0.55-0.75 (Acceptable)
- **12M Horizon:** MAPE 6-12%, R² 0.40-0.65 (Industry Standard)

**Baseline Comparison:**
- Current baseline: 7.8% MAPE
- **Success Criteria:** Beat baseline (improve on 7.8% MAPE)
- **Institutional Benchmark:** 3-8% MAPE is typical for commodity forecasting
- **Goldman Sachs/JPMorgan:** Typically achieve 3-5% MAPE for 1M horizons

**Business Value Metrics:**
- **Directional Accuracy:** % of time correct direction (up/down) - target: 60-70%
- **Confidence Intervals:** P10/P50/P90 quantiles for risk management
- **Actionable Signals:** Clear buy/wait/hedge recommendations
- **Procurement ROI:** Cost savings from better timing decisions
- **Explainability:** Feature importance rankings (understand why prices move)
- **Consistency:** Reliable forecasts across different market regimes

**What Success Really Means:**
- ✅ **Better than baseline:** Improve on 7.8% MAPE (even 5-6% is a win)
- ✅ **Actionable for Chris:** Clear signals for procurement decisions
- ✅ **Explainable:** Understand which drivers matter most
- ✅ **Risk-aware:** Confidence intervals help manage uncertainty
- ✅ **Consistent:** Reliable across different market conditions

**The Real Value:**
The goal isn't perfect prediction (impossible in commodity markets). The goal is **consistently better decision-making** than gut feel or simple trend analysis. Even 3-5% MAPE provides institutional-grade insights that help Chris make better procurement timing decisions.

-------

### 4.2 VALIDATION STRATEGY

-------

**WHAT THIS IS:** How we'll validate our models to ensure they generalize well and don't overfit. Uses time series cross-validation (walk-forward, expanding window) and backtesting on out-of-sample data.
- **Walk-Forward Validation:** Train on 2023-2024, validate on 2025
- **Expanding Window:** Start with 1 year, expand to full dataset
- **Regime-Specific Validation:** Validate on different market regimes

**Backtesting:**
- Test on out-of-sample data (2025-01-01 to 2025-11-06)
- Compare to baseline models (ARIMA, naive forecasts)
- Validate on different market conditions (high VIX, low VIX, etc.)

-------

### 4.3 FEATURE IMPORTANCE ANALYSIS

-------

**WHAT THIS IS:** After training, Vertex AI provides feature importance rankings. We'll export and analyze these to understand which features drive predictions, compare across horizons, and identify regime-specific important features.
- Vertex AI provides feature importance rankings
- Compare across all 4 horizons
- Identify regime-specific important features
- Document top 100 features per horizon

---

-------

## PHASE 4.5: NEURAL FORECASTING PIPELINE (TENSORFLOW/KERAS)

-------

**WHAT THIS IS:** A modular TensorFlow/Keras pipeline that trains multi-horizon neural forecasts (1M/3M/6M/12M) with Monte Carlo uncertainty quantification, SHAP explainability, and "what-if" scenario analysis. This pipeline complements Vertex AI AutoML by providing deep neural architectures (LSTM/GRU/Feedforward), real-time scenario injection, and interactive explainability for Chris's strategy page. Models are trained on the M2 Max (GPU via tensorflow-metal) and deployed to Vertex AI as custom SavedModel artifacts.

**Key Capabilities:**
- **Monte Carlo Uncertainty:** P10/P50/P90 prediction intervals via dropout sampling (PRIMARY method)
- **SHAP Explainability:** DeepExplainer for feature attributions (global + local explanations)
- **What-If Scenarios:** Real-time feature override and re-prediction (<2 seconds)
- **Strategy Page Integration:** Interactive sliders for key drivers (tariffs, VIX, China imports, etc.)
- **Vertex AI Deployment:** SavedModel export for custom model serving

**Architecture:** Modular, versioned components (data/, models/, train/, evaluate/, interpret/, scenario/) with CLI orchestration. Same code for all horizons via parameterization.

**Status:** PLANNING ONLY - NO EXECUTION

---

### 4.5.1 FOLDER STRUCTURE & ORGANIZATION

-------

**WHAT THIS IS:** Complete directory structure for the neural forecasting pipeline. All code lives in `vertex-ai/neural-pipeline/` with clear separation of concerns.

```
vertex-ai/neural-pipeline/
├── data/
│   ├── loaders.py              # BigQuery → TensorFlow data loaders
│   ├── preprocessors.py        # Normalization, windowing, feature validation
│   └── schemas.py              # Feature schema validation (matches metadata catalog)
│
├── models/
│   ├── model.py                # Model factory (LSTM/GRU/Feedforward architectures)
│   ├── architectures.py       # Layer definitions (LSTM, GRU, Dense, Dropout)
│   └── configs/
│       ├── lstm_1m.yaml       # 1M horizon LSTM config
│       ├── gru_3m.yaml         # 3M horizon GRU config
│       └── feedforward_6m.yaml # 6M horizon Feedforward config
│
├── train/
│   ├── train.py                # Main training script (parameterized by horizon)
│   ├── callbacks.py            # EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
│   ├── hyperparameter_tuning.py # Keras Tuner integration (optional)
│   └── train_loop.py          # Reusable training loop abstraction
│
├── evaluate/
│   ├── evaluate.py             # Load model, compute metrics (MSE, directional accuracy)
│   ├── monte_carlo.py          # Monte Carlo dropout for P10/P50/P90 intervals
│   └── forecast_generator.py   # Generate point forecasts + intervals
│
├── interpret/
│   ├── compute_shap.py         # SHAP DeepExplainer for feature attributions
│   ├── global_importance.py    # Aggregate SHAP for global feature importance
│   ├── local_explanations.py   # Per-forecast waterfall/force plots
│   └── cache_shap.py           # Cache SHAP values for dashboard performance
│
├── scenario/
│   ├── run_scenario.py         # What-if scenario engine (feature override + re-predict)
│   ├── scenario_loader.py     # Load baseline + scenario definitions
│   ├── comparison.py           # Compare baseline vs scenario forecasts
│   └── api/
│       └── scenario_api.py     # FastAPI endpoint for dashboard what-if requests
│
├── utils/
│   ├── metrics.py               # Metric calculators (MAPE, RMSE, directional accuracy)
│   ├── logging.py              # TensorBoard, MLflow, Vertex logging utilities
│   └── versioning.py           # Model versioning (Git SHA, date tags)
│
├── deployment/
│   ├── export_savedmodel.py    # Export Keras model to SavedModel format
│   ├── vertex_upload.py        # Upload SavedModel to Vertex AI Model Registry
│   └── endpoint_deploy.py       # Deploy model to Vertex AI endpoint
│
└── main.py                     # CLI entry point (Click or argparse)
```

**CLI Commands:**
```bash
# Training
python main.py train --horizon=1m --config=configs/lstm_1m.yaml
python main.py train --horizon=3m --config=configs/gru_3m.yaml

# Evaluation
python main.py evaluate --horizon=1m --model-version=v20251107

# SHAP Analysis
python main.py compute-shap --horizon=1m --model-version=v20251107

# What-If Scenario
python main.py scenario --horizon=1m --feature=tariff_rate=0.10 --feature=vix=25

# Export for Vertex
python main.py export --horizon=1m --model-version=v20251107 --vertex-registry
```

---

### 4.5.2 DATA INGESTION & PREPROCESSING

-------

**WHAT THIS IS:** How we load data from BigQuery into TensorFlow, validate schemas, and prepare it for neural network training. Ensures strict compliance with feature metadata catalog.

**Data Source:**
- **BigQuery Tables:** `cbi-v14.models_v4.vertex_ai_training_{horizon}_base`
- **Schema Validation:** Matches `feature_metadata_catalog` (feature names, types, cardinalities)
- **Format:** TensorFlow `tf.data.Dataset` or NumPy arrays for Keras

**DataLoader Implementation (`data/loaders.py`):**
- Queries BigQuery for training data
- Validates schema against `feature_metadata_catalog`
- Converts to `tf.data.Dataset` with batching and prefetching
- Handles missing values (forward-fill, median imputation)

**Preprocessing (`data/preprocessors.py`):**
- **Normalization:** Min-max scaling or z-score (fit on training, apply to validation/test)
- **Time Windowing:** Sliding windows for LSTM/GRU (e.g., 30-day lookback window)
- **Feature Selection:** Filter to top 1,000 features (matches Vertex AI limit)
- **Missing Value Handling:** Forward-fill or median imputation (pre-aligned with BigQuery)

**Schema Validation (`data/schemas.py`):**
- Validates feature names match `feature_metadata_catalog`
- Ensures data types match (FLOAT64 → float32, INT64 → int32)
- Checks cardinality for categorical features
- Raises errors if schema drift detected

---

### 4.5.3 MODEL DESIGN & TRAINING (KERAS)

-------

**WHAT THIS IS:** Keras model factory that creates LSTM/GRU/Feedforward architectures from YAML configs. Training loop with callbacks (EarlyStopping, ModelCheckpoint) and optional hyperparameter tuning.

**Model Factory (`models/model.py`):**
- Creates models based on config parameters (LSTM, GRU, Feedforward)
- **CRITICAL:** Dropout layers enabled for Monte Carlo uncertainty quantification
- Configurable architectures via YAML files

**Training Script (`train/train.py`):**
- Loads data from BigQuery
- Creates model via factory
- Compiles with Adam optimizer, MSE loss
- **Callbacks:**
  - `EarlyStopping`: Monitors validation loss, patience=10, restores best weights
  - `ModelCheckpoint`: Saves best model weights to Cloud Storage
  - `ReduceLROnPlateau`: Decreases learning rate on plateau
  - `TensorBoard`: Logs to Vertex-managed TensorBoard
- Exports SavedModel format (required for Vertex AI)
- Logs metadata (config, feature list, hyperparameters, metrics)

**Hyperparameter Tuning (Optional):**
- Use Keras Tuner for automated hyperparameter search
- Grid search over: layer sizes, learning rates, dropout rates, batch sizes
- Log all trials to TensorBoard/MLflow for comparison
- Select best model via cross-validation

**Model Export:**
- **SavedModel Format:** `model.save()` creates TensorFlow SavedModel directory
- **Vertex AI Requirement:** SavedModel includes "serve" signature tag automatically
- **Location:** `gs://bucket/models/{horizon}/saved_model/`
- **Metadata:** Training config, feature list, hyperparameters stored alongside model

---

### 4.5.4 MONTE CARLO UNCERTAINTY QUANTIFICATION

-------

**WHAT THIS IS:** Monte Carlo dropout method for generating prediction intervals (P10/P50/P90). This is our PRIMARY uncertainty quantification method - more robust than quantile regression for neural networks. Runs model multiple times with dropout enabled at inference to capture epistemic uncertainty.

**Why Monte Carlo Dropout:**
- **Epistemic Uncertainty:** Captures model uncertainty (what the model doesn't know)
- **Non-Parametric:** No assumptions about error distribution
- **Neural-Network Native:** Works naturally with dropout layers
- **Robust:** Handles non-linear relationships better than quantile regression
- **Industry Standard:** Used by Goldman Sachs, JPMorgan for neural forecasting

**Implementation (`evaluate/monte_carlo.py`):**
```python
def monte_carlo_predict(
    model: tf.keras.Model,
    X: np.ndarray,
    n_samples: int = 1000,
    dropout_enabled: bool = True
) -> dict:
    """
    Generates P10/P50/P90 prediction intervals via Monte Carlo dropout.
    
    CRITICAL: Set training=True to enable dropout at inference.
    """
    predictions = []
    
    for _ in range(n_samples):
        # Run prediction with dropout enabled
        pred = model(X, training=True)  # training=True enables dropout
        predictions.append(pred.numpy())
    
    # Stack predictions: [n_samples, batch_size, 1]
    predictions = np.array(predictions)
    
    # Compute percentiles
    p10 = np.percentile(predictions, 10, axis=0)
    p50 = np.percentile(predictions, 50, axis=0)  # Median
    p90 = np.percentile(predictions, 90, axis=0)
    mean = np.mean(predictions, axis=0)
    std = np.std(predictions, axis=0)
    
    return {
        'p10': p10.flatten(),
        'p50': p50.flatten(),
        'mean': mean.flatten(),
        'p90': p90.flatten(),
        'std': std.flatten()
    }
```

**Usage in Evaluation (`evaluate/evaluate.py`):**
- Point prediction (single forward pass, dropout OFF)
- Monte Carlo intervals (1,000 forward passes, dropout ON)
- Combines results into DataFrame with `date`, `point_forecast`, `p10`, `p50`, `p90`, `uncertainty_std`
- Writes to BigQuery: `cbi-v14.models_v4.neural_forecasts_{horizon}`

**Performance Considerations:**
- **Sampling Count:** 1,000 samples provides robust intervals (diminishing returns beyond)
- **Inference Speed:** 1,000 forward passes takes ~2-5 seconds (acceptable for batch)
- **Caching:** Pre-compute intervals for dashboard (update daily)
- **Real-Time:** For what-if scenarios, use 100 samples (<0.5 seconds)

**Output Format:**
- **BigQuery Table:** `cbi-v14.models_v4.neural_forecasts_{horizon}`
- **Columns:** `date`, `point_forecast`, `p10`, `p50`, `p90`, `uncertainty_std`, `model_version`
- **Dashboard:** Overlay P10/P90 bands on price chart (confidence intervals)

---

### 4.5.5 SHAP EXPLAINABILITY (DEEP EXPLAINER)

-------

**WHAT THIS IS:** SHAP (SHapley Additive exPlanations) analysis using DeepExplainer for neural networks. Computes feature attributions per forecast, enabling global importance rankings and local explanations (waterfall/force plots) for individual predictions. SHAP values are cached for dashboard performance.

**Why SHAP:**
- **Game-Theoretic Foundation:** Shapley values provide mathematically principled feature attributions
- **Neural-Network Compatible:** DeepExplainer designed specifically for deep learning models
- **Interpretable:** Explains "why" the model made a prediction (not just "what")
- **Actionable:** Helps Chris understand which drivers are moving prices
- **Industry Standard:** Used by GS, JPMorgan for model interpretability

**Implementation (`interpret/compute_shap.py`):**
```python
import shap

def compute_shap_values(
    model: tf.keras.Model,
    background_data: np.ndarray,
    test_data: np.ndarray,
    horizon: str
) -> dict:
    """
    Computes SHAP values using DeepExplainer for neural networks.
    
    Args:
        model: Trained Keras model
        background_data: Representative sample for SHAP baseline (100-500 rows)
        test_data: Test data to explain (all forecasts)
        horizon: Forecast horizon (1m, 3m, 6m, 12m)
    
    Returns:
        {
            'shap_values': SHAP attributions per feature per sample,
            'feature_names': List of feature names,
            'global_importance': Mean |SHAP| per feature (global ranking)
        }
    """
    # Initialize DeepExplainer
    explainer = shap.DeepExplainer(model, background_data)
    
    # Compute SHAP values
    shap_values = explainer.shap_values(test_data)
    
    # Aggregate for global importance
    global_importance = np.mean(np.abs(shap_values), axis=0)
    
    # Get feature names from metadata catalog
    feature_names = get_feature_names(horizon)
    
    return {
        'shap_values': shap_values,
        'feature_names': feature_names,
        'global_importance': global_importance
    }
```

**Global Feature Importance (`interpret/global_importance.py`):**
- Creates global feature importance plot (mean |SHAP| per feature)
- Shows top 20 features that drive the model overall
- Saves to file or returns for dashboard

**Local Explanations (`interpret/local_explanations.py`):**
- Creates waterfall plot for a single forecast
- Shows how each feature contributed to the prediction
- Sorts features by |SHAP| value

**Caching for Performance (`interpret/cache_shap.py`):**
- Stores SHAP values in BigQuery: `cbi-v14.models_v4.shap_values_{horizon}`
- Flattens SHAP values (one row per forecast per feature)
- Enables fast dashboard queries

**Dashboard Integration:**
- **Global Importance:** Bar chart showing top 20 features (mean |SHAP|)
- **Local Explanations:** Waterfall plot for selected forecast date
- **Feature Contribution Table:** Sortable table of all feature contributions
- **Interactive:** Click on forecast date → see local explanation

---

### 4.5.6 WHAT-IF SCENARIO ENGINE

-------

**WHAT THIS IS:** Real-time scenario injection system that allows analysts to override feature values (e.g., "tariff_rate=0.10", "VIX=25") and re-run model predictions to see how forecasts change. This enables answering questions like "What if tariffs increase?" by comparing baseline vs scenario forecasts. Integrated with strategy page sliders for interactive exploration.

**Why What-If Scenarios:**
- **Strategic Planning:** Test different market conditions before they happen
- **Risk Assessment:** Understand sensitivity to key drivers (tariffs, VIX, China imports)
- **Procurement Decisions:** Evaluate "buy now" vs "wait" under different scenarios
- **Interactive Exploration:** Sliders on strategy page enable real-time scenario testing

**Implementation (`scenario/run_scenario.py`):**
- Takes baseline feature values (current market state)
- Overrides user-specified features (e.g., `{'tariff_rate': 0.10, 'vix': 25}`)
- Re-runs model prediction with Monte Carlo (100 samples for speed)
- Returns baseline vs scenario comparison (point + intervals, delta, delta_pct)

**Strategy Page Slider Integration (`scenario/api/scenario_api.py`):**
- **FastAPI Endpoint:** `POST /api/scenario/what-if`
- **Request:** `{horizon: '1m', feature_overrides: {'tariff_rate': 0.10, ...}}`
- **Response Time:** <2 seconds for single-feature override
- **Returns:** Baseline forecast, scenario forecast, delta ($ and %)

**Strategy Page UI Components:**
- **Feature Sliders:** Interactive sliders for key drivers:
  - Tariff Rate (0-50%, step 0.01)
  - VIX Index (10-50, step 1)
  - China Imports MT (0-1M, step 10K)
  - RIN D4 Price (0-2.0, step 0.05)
  - Fed Funds Rate (0-10%, step 0.25)
  - (More sliders as needed)
- **Real-Time Updates:** As user moves slider, API call updates forecast instantly (<2 seconds)
- **Comparison View:** Side-by-side baseline vs scenario forecast (point + P10/P90 bands)
- **Delta Display:** Shows price change ($ and %) for scenario
- **Multi-Scenario:** Save multiple scenarios, compare all at once
- **Export:** Download scenario results as CSV/PDF

**Performance Requirements:**
- **Response Time:** <2 seconds for single-feature override
- **Concurrent Requests:** Support 10+ simultaneous users
- **Caching:** Cache model loads (don't reload model for every request)
- **Batch Scenarios:** Support multiple feature overrides in one request

---

### 4.5.7 DEPLOYMENT TO VERTEX AI

-------

**WHAT THIS IS:** Export Keras models to TensorFlow SavedModel format and deploy to Vertex AI as custom models. This enables serving neural forecasts alongside AutoML models, with full integration into Vertex AI Model Registry and endpoints.

**SavedModel Export (`deployment/export_savedmodel.py`):**
- Exports Keras model to SavedModel format (required for Vertex AI)
- SavedModel includes 'serve' signature tag automatically
- Verifies export by loading and testing inference signature

**Vertex AI Upload (`deployment/vertex_upload.py`):**
- Uploads SavedModel to Vertex AI Model Registry
- Model display name: `CBI V14 Vertex – Neural {horizon}` (e.g., "CBI V14 Vertex – Neural 1M")
- Uses TensorFlow serving container image

**Endpoint Deployment (`deployment/endpoint_deploy.py`):**
- Deploys model to Vertex AI endpoint for online predictions
- Endpoint display name: `CBI V14 Vertex – Neural {horizon} Endpoint`
- Machine type: `n1-standard-4` (configurable)
- Min/max replicas: 1-3 (auto-scaling)

**Integration with AutoML:**
- **Hybrid Approach:** Use AutoML for baseline, neural models for explainability/scenarios
- **Ensemble Option:** Combine AutoML + Neural predictions (weighted average)
- **A/B Testing:** Compare AutoML vs Neural performance in production

---

### 4.5.8 VERSIONING & MONITORING

-------

**WHAT THIS IS:** Version control, metadata tracking, and monitoring for the neural forecasting pipeline. Ensures full reproducibility and enables model performance tracking over time.

**Versioning:**
- **Code:** All code in Git, tagged by date/git SHA
- **Models:** Vertex AI Model Registry stores model versions with metadata
- **Metadata:** Training config, feature list, hyperparameters, metrics logged per run
- **Artifacts:** SavedModel, SHAP values, forecasts stored in Cloud Storage with version tags

**Monitoring:**
- **Training Metrics:** Loss curves, validation metrics logged to TensorBoard (Vertex-managed)
- **Forecast Accuracy:** Track MAPE, RMSE, directional accuracy over time
- **Drift Detection:** Monitor feature distributions, prediction distributions for drift
- **Performance Alerts:** Alert if forecast accuracy degrades >20% from baseline

**Reproducibility:**
- **Data Hashes:** Log training data hash (ensures same data used for retraining)
- **Code Hashes:** Log Git commit SHA (ensures same code used)
- **Environment:** Log Python version, TensorFlow version, dependencies
- **ML Metadata:** Vertex AI ML Metadata tracks all artifacts, executions, lineage

---

## PHASE 5: DEPLOYMENT & MONITORING

-------

**WHAT THIS IS:** Once models are trained and validated, we deploy them to Vertex AI endpoints for production use. Includes prediction pipelines, dashboard integration, and ongoing monitoring for performance degradation.

-------

### 5.1 MODEL DEPLOYMENT

-------

**WHAT THIS IS:** Deploys each trained model to a Vertex AI endpoint so we can make predictions. Endpoints support both batch (historical) and online (real-time) predictions.
- Deploy each model to separate endpoint
- Use batch prediction for historical forecasts
- Use online prediction for real-time forecasts

**Endpoint Naming (Vertex AI Display Names):**
- `CBI V14 Vertex – 1M Endpoint`
- `CBI V14 Vertex – 3M Endpoint`
- `CBI V14 Vertex – 6M Endpoint`
- `CBI V14 Vertex – 12M Endpoint`

-------

### 5.2 PREDICTION PIPELINE

-------

**WHAT THIS IS:** The automated workflow that runs daily to generate fresh predictions. Updates feature data, calls all 4 model endpoints, stores predictions, and updates the dashboard.
1. Update feature data in BigQuery
2. Generate prediction frame (latest date)
3. Call Vertex AI endpoints for all 4 horizons
4. Store predictions in `vertex_ai_predictions` table
5. Update dashboard with new forecasts

-------

### 5.3 MONITORING STRATEGY

-------

**WHAT THIS IS:** Ongoing monitoring to track prediction accuracy over time, detect data drift (feature distributions changing), and alert on performance degradation. Triggers retraining when needed.
- Track prediction accuracy over time
- Monitor for data drift (feature distributions changing)
- Alert on performance degradation
- Retrain models quarterly or when performance drops

**Performance Tracking:**
- Daily MAPE calculation
- Weekly performance reports
- Monthly model retraining evaluation

---

-------

## PHASE 6: IMPLEMENTATION CHECKLIST

-------

**WHAT THIS IS:** A comprehensive checklist of all tasks that must be completed before training can begin. Organized by phase, with clear status indicators (✅ complete, ❌ to do).

-------

### 6.1 DATA PREPARATION

-------

**WHAT THIS IS:** All tasks related to preparing and validating training data. Includes building transformation pipelines, fixing schema issues, adding regime weights, and ensuring data quality.
- [ ] **CRITICAL:** Build transformation pipeline from raw warehouse → production tables
- [ ] Fix Yahoo Finance date column (INTEGER → DATE)
- [ ] Create staging tables (`stg_vertex_ai_training_*`)
- [ ] Build transformation scripts (Yahoo → production, warehouse → production)
- [ ] Populate feature metadata catalog (`bigquery-sql/vertex-ai/02_POPULATE_FEATURE_CATALOG.py`) ✅
- [ ] Audit all BigQuery tables for available features
- [ ] Create master consolidation SQL script
- [ ] Build base `vertex_ai_training_*_base` tables (1M, 3M, 6M, 12M) with identical schemas (or migrate from `production_training_data_*`)
- [ ] Add regime weights (`training_weight` column) to create `vertex_ai_training_*` tables
- [ ] Add topic-based regime multipliers (tariffs, trade wars, inflation, Trump effects)
- [ ] Add regime labels (`market_regime` column) to `vertex_ai_training_*` tables
- [ ] Create final `vertex_ai_training_1m`, `3m`, `6m`, `12m` tables (WITH regime weights, ready for Vertex AI)
- [ ] Validate schema contract (identical feature count, data types, date column)
- [ ] Validate data quality (no NULLs, correct date ranges, no duplicates)
- [ ] Convert BOOLEAN columns to INT64
- [ ] Remove/rename reserved column names
- [ ] Normalize frequencies (all daily granularity)

-------

### 6.2 VERTEX AI SETUP

-------

**WHAT THIS IS:** Tasks for setting up Vertex AI datasets, configuring AutoML settings, and preparing for training. Must complete before launching training jobs.
- [ ] Create Vertex AI dataset: `CBI V14 Vertex – 1M Dataset` (from `vertex_ai_training_1m` - WITH regime weights)
- [ ] Create Vertex AI dataset: `CBI V14 Vertex – 3M Dataset` (from `vertex_ai_training_3m` - WITH regime weights)
- [ ] Create Vertex AI dataset: `CBI V14 Vertex – 6M Dataset` (from `vertex_ai_training_6m` - WITH regime weights)
- [ ] Create Vertex AI dataset: `CBI V14 Vertex – 12M Dataset` (from `vertex_ai_training_12m` - WITH regime weights)
- [ ] Configure AutoML Tabular Regression settings
- [ ] Set training budgets ($100 each = $400 total)

-------

### 6.3 MODEL TRAINING

-------

**WHAT THIS IS:** The actual training of all 4 models. Each model takes ~20 hours and costs $100. Monitor progress and export evaluated data items for analysis.
- [ ] Train model: `CBI V14 Vertex – AutoML 1M` (20 hour budget, $100)
- [ ] Train model: `CBI V14 Vertex – AutoML 3M` (20 hour budget, $100)
- [ ] Train model: `CBI V14 Vertex – AutoML 6M` (20 hour budget, $100)
- [ ] Train model: `CBI V14 Vertex – AutoML 12M` (20 hour budget, $100)
- [ ] Monitor training progress
- [ ] Export evaluated data items for analysis

-------

### 6.4 EVALUATION

-------

**WHAT THIS IS:** After training completes, evaluate all models using the metrics defined in Phase 4. Compare to baseline, validate on out-of-sample data, and document performance.
- [ ] Evaluate all 4 models (MAE, RMSE, MAPE, R²)
- [ ] Export feature importance rankings
- [ ] Compare to baseline models
- [ ] Validate on out-of-sample data
- [ ] Document performance metrics

-------

### 6.5 DEPLOYMENT

-------

**WHAT THIS IS:** Deploy validated models to production endpoints, create prediction pipelines, test batch and online predictions, integrate with dashboard, and set up monitoring alerts.
- [ ] Deploy model `CBI V14 Vertex – AutoML 1M` to endpoint `CBI V14 Vertex – 1M Endpoint`
- [ ] Deploy model `CBI V14 Vertex – AutoML 3M` to endpoint `CBI V14 Vertex – 3M Endpoint`
- [ ] Deploy model `CBI V14 Vertex – AutoML 6M` to endpoint `CBI V14 Vertex – 6M Endpoint`
- [ ] Deploy model `CBI V14 Vertex – AutoML 12M` to endpoint `CBI V14 Vertex – 12M Endpoint`
- [ ] Create prediction pipeline script
- [ ] Test batch predictions
- [ ] Test online predictions
- [ ] Integrate with dashboard
- [ ] Set up monitoring alerts

-------

## PHASE 7: COST ESTIMATION

-------

**Training Costs:**
- 4 models × $100 each = $400 total training cost
- 20 hours per model × 4 = 80 total node-hours

**Prediction Costs:**
- Batch predictions: ~$0.10 per 1,000 predictions
- Online predictions: ~$0.50 per 1,000 predictions
- Estimated monthly: $50-100 for predictions

**Storage Costs:**
- BigQuery storage: ~$20/month for training tables
- Vertex AI model storage: Included in training cost

**Total Estimated Cost:**
- **One-time Training:** $400
- **Monthly Operations:** $70-120
- **Annual:** ~$1,200-1,800

-------

## PHASE 8: RISKS & MITIGATION

-------

### 8.1 DATA RISKS

-------
- **Risk:** Missing historical data (50+ years may have gaps)
- **Mitigation:** Use forward-fill, backward-fill, interpolation

- **Risk:** Feature count exceeds Vertex AI limit (1,000 columns)
- **Mitigation:** Use Vertex AI Feature Transform Engine for automatic selection

-------

### 8.2 TRAINING RISKS

-------

- **Risk:** Training fails due to data quality issues
- **Mitigation:** Pre-validate all data, handle NULLs, remove outliers

- **Risk:** Models overfit to Trump era data
- **Mitigation:** Use time series cross-validation, test on different regimes

-------

### 8.3 PERFORMANCE RISKS

-------

- **Risk:** Models don't meet unrealistic targets (0.35% MAPE)
- **Mitigation:** Use realistic targets (2-4% MAPE), focus on beating baseline (7.8%)
- **Reality:** Even 3-5% MAPE is institutional-grade and provides real business value
- **Success Metric:** Better than baseline + actionable for procurement decisions

-------

## PHASE 9: SUCCESS CRITERIA

-------

**Model Performance (REALISTIC TARGETS):**
- ✅ All 4 models trained successfully
- ✅ 1M model: MAPE 2-4%, R² 0.75-0.85 (beats 7.8% baseline)
- ✅ 3M model: MAPE 3-6%, R² 0.65-0.80 (beats 7.8% baseline)
- ✅ 6M model: MAPE 4-8%, R² 0.55-0.75 (competitive with baseline)
- ✅ 12M model: MAPE 6-12%, R² 0.40-0.65 (industry standard)

**Business Value Success Criteria:**
- ✅ **Actionable Signals:** Clear buy/wait/hedge recommendations for Chris
- ✅ **Explainability:** Understand why prices move (feature importance)
- ✅ **Risk Management:** Confidence intervals (P10/P50/P90) for decision-making
- ✅ **Procurement Value:** Better decisions than gut feel or simple trend analysis
- ✅ **Consistency:** Reliable forecasts across different market regimes

**Data Quality:**
- ✅ All primary data sources consolidated.
- ✅ **2,000+** high-quality features engineered for the `1m` golden template.
- ✅ Regime and Factor methodologies applied.
- ✅ Zero critical `NULL` values in final training tables.

**Deployment:**
- ✅ All 4 models deployed to Vertex AI endpoints
- ✅ Prediction pipeline operational
- ✅ Dashboard integration complete
- ✅ Monitoring alerts configured

-------

## DASHBOARD & VISUALIZATION REQUIREMENTS

-------

### PAGE 5: ADMIN PANEL (ON-DEMAND DATA REFRESH CONTROL)

-------

**WHAT THIS IS:** A secure, password-protected admin page that provides manual control over all data ingestion pipelines. This enables on-demand data refreshes in response to major market events, breaking news, or when we can't wait for the next scheduled cron run. This is a critical feature for maintaining data freshness during volatile market conditions.

-------

#### ADMIN PAGE ARCHITECTURE

-------

**Security & Access:**
- **Access Control:** Hidden page (not in main navigation) or password-protected route
- **Authentication:** Admin-only access (separate from main dashboard)
- **Route:** `/admin` or `/admin/data-refresh` (Next.js route)

**UI Components:**
- **Status Dashboard:** Real-time display of all ingestion job statuses
- **Button Grid:** Organized by data category (Financial, Trade/Policy, Economic, Commodity, Biofuel)
- **Job Status Indicators:** Visual feedback (Running, Completed, Error, Queued)
- **Last Run Timestamps:** Display when each script last executed successfully
- **Error Logs:** Click to view detailed error messages for failed jobs

-------

#### ON-DEMAND DATA PULL BUTTONS

-------

**WHAT THIS IS:** Each button triggers a specific ingestion script via a secure backend API endpoint. The UI provides real-time feedback on job status, and the backend executes the corresponding Python script asynchronously.

**Button Categories & Actions:**

**1. Financial Price Data Button**
- **Button Label:** `Refresh Financial Price Data`
- **Backend API Endpoint:** `POST /api/admin/refresh/financial-prices`
- **Script Executed:** `scripts/pull_yahoo_complete_enterprise.py`
- **Purpose:** Triggers a full, immediate refresh of all 210+ market price symbols from Yahoo Finance
- **Destination Table:** `cbi-v14.yahoo_finance_comprehensive.yahoo_finance_complete_enterprise`
- **Estimated Runtime:** 30-60 minutes (depends on symbol count and rate limiting)
- **Status Feedback:** Shows progress (e.g., "Pulling 50/210 symbols...", "Completed: 210 symbols updated")

**2. Trade & Policy Data Button**
- **Button Label:** `Refresh Trade & Policy Data`
- **Backend API Endpoint:** `POST /api/admin/refresh/trade-policy`
- **Scripts Executed:** 
  - `ingestion/trump_truth_social_monitor.py` (Trump Truth Social posts)
  - `ingestion/scrape_creators_full_blast.py` (Facebook, Twitter, LinkedIn intelligence)
- **Purpose:** Pulls the latest social media and news intelligence related to trade and geopolitical events
- **Destination Tables:** 
  - `cbi-v14.forecasting_data_warehouse.trump_policy_intelligence`
  - `cbi-v14.forecasting_data_warehouse.social_sentiment`
- **Estimated Runtime:** 5-15 minutes
- **Status Feedback:** Shows platform progress (e.g., "Facebook: Complete, Twitter: Running...")

**3. Economic Data Button**
- **Button Label:** `Refresh Economic Data`
- **Backend API Endpoint:** `POST /api/admin/refresh/economic`
- **Script Executed:** `ingestion/fred_economic_deployment.py` or `ingestion/economic_intelligence.py`
- **Purpose:** Fetches the latest releases for key economic indicators from the FRED API
- **Destination Table:** `cbi-v14.forecasting_data_warehouse.economic_indicators`
- **Estimated Runtime:** 2-5 minutes
- **Status Feedback:** Shows indicator count (e.g., "Fetched 25/30 indicators...")

**4. USDA/Commodity Data Button**
- **Button Label:** `Refresh USDA/Commodity Data`
- **Backend API Endpoint:** `POST /api/admin/refresh/usda-commodity`
- **Script Executed:** `ingestion/ingest_usda_export_sales_weekly.py`
- **Purpose:** Scrapes the latest weekly commodity export sales data, China imports, harvest progress
- **Destination Tables:** 
  - `cbi-v14.forecasting_data_warehouse.china_soybean_imports`
  - `cbi-v14.forecasting_data_warehouse.usda_harvest_progress`
- **Estimated Runtime:** 3-8 minutes
- **Status Feedback:** Shows data source progress (e.g., "Export Sales: Complete, Harvest Progress: Running...")

**5. Biofuel Data Button**
- **Button Label:** `Refresh Biofuel Data`
- **Backend API Endpoint:** `POST /api/admin/refresh/biofuel`
- **Script Executed:** `ingestion/ingest_epa_rin_prices.py`
- **Purpose:** Pulls the most recent RIN prices (D4, D5, D6) and other biofuel-related data from EPA
- **Destination Table:** `cbi-v14.forecasting_data_warehouse.biofuel_prices`
- **Estimated Runtime:** 2-5 minutes
- **Status Feedback:** Shows RIN type progress (e.g., "D4: Complete, D5: Running, D6: Pending...")

**6. CFTC Positioning Data Button** (Additional)
- **Button Label:** `Refresh CFTC Positioning Data`
- **Backend API Endpoint:** `POST /api/admin/refresh/cftc`
- **Script Executed:** `ingestion/ingest_cftc_positioning_REAL.py`
- **Purpose:** Fetches latest Commitment of Traders (COT) reports for money manager positioning
- **Destination Table:** `cbi-v14.forecasting_data_warehouse.cftc_cot`
- **Estimated Runtime:** 3-7 minutes
- **Status Feedback:** Shows commodity progress (e.g., "Soybean Oil: Complete, Corn: Running...")

**7. Weather Data Button** (Additional)
- **Button Label:** `Refresh Weather Data`
- **Backend API Endpoint:** `POST /api/admin/refresh/weather`
- **Script Executed:** `ingestion/unified_weather_scraper.py`
- **Purpose:** Pulls latest weather data for Brazil, Argentina, and US Midwest locations
- **Destination Table:** `cbi-v14.forecasting_data_warehouse.weather_daily`
- **Estimated Runtime:** 5-10 minutes
- **Status Feedback:** Shows location progress (e.g., "Brazil: 7/7 locations, Argentina: 4/4 locations...")

**8. All Data Refresh Button** (Master Button)
- **Button Label:** `Refresh All Data Sources`
- **Backend API Endpoint:** `POST /api/admin/refresh/all`
- **Purpose:** Triggers all data refresh buttons in sequence (with proper delays to avoid rate limiting)
- **Estimated Runtime:** 60-120 minutes (sequential execution)
- **Status Feedback:** Shows overall progress and individual script status

-------

#### BACKEND API IMPLEMENTATION

-------

**WHAT THIS IS:** Secure Next.js API routes that execute Python ingestion scripts asynchronously, track job status, and return real-time updates to the frontend.

**API Route Structure:**
```
/api/admin/refresh/
  ├── financial-prices    → POST (triggers pull_yahoo_complete_enterprise.py)
  ├── trade-policy        → POST (triggers trump_truth_social_monitor.py + scrape_creators_full_blast.py)
  ├── economic            → POST (triggers fred_economic_deployment.py)
  ├── usda-commodity      → POST (triggers ingest_usda_export_sales_weekly.py)
  ├── biofuel             → POST (triggers ingest_epa_rin_prices.py)
  ├── cftc                → POST (triggers ingest_cftc_positioning_REAL.py)
  ├── weather             → POST (triggers unified_weather_scraper.py)
  └── all                 → POST (triggers all scripts sequentially)
```

**API Response Format:**
```json
{
  "status": "running" | "completed" | "error" | "queued",
  "jobId": "uuid-string",
  "script": "pull_yahoo_complete_enterprise.py",
  "startedAt": "2025-11-07T14:30:00Z",
  "estimatedCompletion": "2025-11-07T15:00:00Z",
  "progress": {
    "current": 150,
    "total": 210,
    "percentage": 71.4,
    "message": "Pulling symbol 150/210: ZL=F"
  },
  "errors": []
}
```

**Job Status Tracking:**
- **In-Memory Store:** Track active jobs in Redis or in-memory Map
- **Database Log:** Store job history in `admin_job_logs` table for audit trail
- **WebSocket/SSE:** Optional real-time updates via WebSocket or Server-Sent Events

**Error Handling:**
- **Retry Logic:** Automatic retry for transient failures (network issues, rate limits)
- **Error Logging:** Detailed error messages stored in job log
- **Notification:** Email/Slack alert for critical failures
- **Rollback:** Ability to revert to previous data state if refresh fails catastrophically

-------

#### USE CASES & BENEFITS

-------

**Primary Use Cases:**
1. **Breaking News Events:** Trump announces new tariffs → Immediately refresh Trade & Policy data
2. **Market Volatility:** Major price movement → Refresh Financial Price Data to get latest prices
3. **Scheduled Report Releases:** USDA releases weekly export sales → Refresh USDA/Commodity Data
4. **Data Quality Issues:** Discover stale data → Refresh specific category to fix
5. **Pre-Training Refresh:** Before model training → Refresh All Data Sources to ensure latest data

**Benefits:**
- ✅ **Flexibility:** Don't wait for cron schedule when market-moving news breaks
- ✅ **Control:** Manual oversight of critical data refreshes
- ✅ **Transparency:** Real-time visibility into data ingestion status
- ✅ **Reliability:** Ability to retry failed jobs immediately
- ✅ **Audit Trail:** Complete history of all manual data refreshes

-------

#### IMPLEMENTATION CHECKLIST

-------

- [ ] Create `/admin` route in Next.js dashboard (password-protected)
- [ ] Design admin page UI with button grid and status dashboard
- [ ] Create backend API routes (`/api/admin/refresh/*`)
- [ ] Implement async job execution (Python script runner)
- [ ] Add job status tracking (Redis or in-memory store)
- [ ] Create `admin_job_logs` table in BigQuery for audit trail
- [ ] Implement real-time status updates (WebSocket or polling)
- [ ] Add error handling and retry logic
- [ ] Test each button with actual ingestion scripts
- [ ] Add authentication/authorization for admin access
- [ ] Document API endpoints and job execution flow

-------

## FILE & DOCUMENT STATUS

-------

### ✅ EXISTING FILES (VERIFIED)

-------

**SQL Scripts:**
- ✅ `bigquery-sql/vertex-ai/01_CREATE_FEATURE_METADATA_CATALOG.sql`
- ✅ `bigquery-sql/vertex-ai/01_create_master_time_spine.sql`
- ✅ `bigquery-sql/vertex-ai/02_join_derived_features.sql`
- ✅ `bigquery-sql/vertex-ai/03_add_regime_weights_to_production.sql`
- ✅ `bigquery-sql/vertex-ai/CREATE_12M_TRAINING_TABLE.sql`
- ✅ `bigquery-sql/vertex-ai/schema_contract.sql`
- ✅ `bigquery-sql/vertex-ai/validate_data_quality.sql`

**Python Scripts:**
- ✅ `bigquery-sql/vertex-ai/02_POPULATE_FEATURE_CATALOG.py`
- ✅ `vertex-ai/data/audit_data_sources.py`
- ✅ `vertex-ai/data/validate_schema.py`
- ✅ `vertex-ai/data/comprehensive_data_inventory.py`

**Documentation:**
- ✅ `docs/vertex-ai/INGESTION_PIPELINE_AUDIT.md` - [Link](./docs/vertex-ai/INGESTION_PIPELINE_AUDIT.md)
- ✅ `docs/vertex-ai/PROPER_VERTEX_AI_ARCHITECTURE.md` - [Link](./docs/vertex-ai/PROPER_VERTEX_AI_ARCHITECTURE.md)
- ✅ `docs/vertex-ai/REGIME_BASED_TRAINING_STRATEGY.md` - [Link](./docs/vertex-ai/REGIME_BASED_TRAINING_STRATEGY.md)
- ✅ `vertex-ai/README.md`
- ✅ `bigquery-sql/vertex-ai/README.md`

-------

### ❌ FILES TO BE CREATED

-------

**Transformation Pipeline:**
- ❌ `vertex-ai/data/TRANSFORM_YAHOO_TO_PRODUCTION.py`
- ❌ `bigquery-sql/vertex-ai/TRANSFORM_WAREHOUSE_TO_PRODUCTION.sql`
- ❌ `bigquery-sql/vertex-ai/VALIDATE_STAGING_SCHEMA.sql`
- ❌ `bigquery-sql/vertex-ai/ATOMIC_OVERWRITE_PRODUCTION.sql`
- ❌ `bigquery-sql/vertex-ai/04_CREATE_CLEAN_1M_STAGING.sql`

**Training Scripts:**
- ❌ `vertex-ai/training/train_1m_model.py`
- ❌ `vertex-ai/training/train_3m_model.py`
- ❌ `vertex-ai/training/train_6m_model.py`
- ❌ `vertex-ai/training/train_12m_model.py`

**Prediction Scripts:**
- ❌ `vertex-ai/prediction/predict_1m.py`
- ❌ `vertex-ai/prediction/predict_3m.py`
- ❌ `vertex-ai/prediction/predict_6m.py`
- ❌ `vertex-ai/prediction/predict_12m.py`

-------

## NEXT STEPS (AFTER PLAN APPROVAL)

-------

1. **Execute Phase 1:** Data audit and consolidation
2. **Build Transformation Pipeline:** Create all missing transformation scripts (CRITICAL)
3. **Execute Phase 2:** Vertex AI dataset setup
4. **Execute Phase 3:** Model training (sequential, one at a time)
5. **Execute Phase 4:** Evaluation and validation
6. **Execute Phase 5:** Deployment and monitoring

---

**STATUS: PLAN COMPLETE - AWAITING APPROVAL TO EXECUTE**

**CRITICAL BLOCKER:** Transformation pipeline must be built before any training can occur. All ingestion scripts write to raw warehouse tables, but no ETL exists to move data to production training tables.

