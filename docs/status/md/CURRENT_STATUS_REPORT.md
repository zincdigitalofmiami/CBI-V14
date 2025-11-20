---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# CBI-V14 Current Status Report
**Date:** November 18, 2025  
**Status:** ⚠️ **PARTIAL DEPLOYMENT - DATA COLLECTION PRIORITY**  
**Primary Plan:** `docs/plans/FRESH_START_MASTER_PLAN.md`  
**Execution Plan:** `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md`

---

## 🎯 EXECUTIVE SUMMARY

**Current Phase:** Pre-Data Collection (Deployment Complete, Data Missing)  
**Primary Blocker:** No DataBento data collected (critical for ZL/MES training)  
**Architecture Status:** ✅ Schema deployed, ❌ Data empty, ❌ Views missing  
**Next Priority:** Data collection and organization (per user directive)

### Draft Proposals (to confirm)
See `docs/INDEX_DRAFT_IDEAS.md` for a curated list of newly drafted idea documents created during the last cycle, including deployment safety gates, labeling, schema audits, horizon strategy, dual-asset organization, and external drive organization. These are proposals pending confirmation and may evolve before promotion to active standards.

---

## 📦 ZL Procurement Signal Quality — Add Now

The following acquisitions expand ZL procurement signal quality and MES microstructure coverage. Scope them into Phase 0 collection so models and routers have the required surfaces.

- Grains complex breadth (daily OHLCV)
  - Futures: ZC (Corn), ZW (Chicago Wheat), KE (KC Wheat)
  - Rationale: crush/meal/oil substitution; feedstock competition for ZL.
  - Destination: `market_data.databento_futures_ohlcv_1d` (add roots ZC, ZW, KE)

- FX risk channels (daily OHLCV)
  - Futures: 6L (BRL), CNH (Offshore RMB)
  - Rationale: BRL → Brazil supply/policy; CNH → China demand/FX transmission.
  - Destination: `market_data.databento_futures_ohlcv_1d` (add roots 6L, CNH)

- Equity risk proxies (intraday/daily; MES routers)
  - Futures: NQ/MNQ (Nasdaq), RTY/M2K (Russell)
  - Rationale: cross‑asset risk/vol surfaces for intraday routing/calibration.
  - Destination: `market_data.databento_futures_ohlcv_1m` and `_1d` (add roots NQ, MNQ, RTY, M2K)

- Energy spreads (biofuel economics)
  - Futures: CL (Crude), HO (ULSD), RB (RBOB)
  - Rationale: diesel/gas proxies for biodiesel parity; ULSD (HO) is critical.
  - Destination: `market_data.databento_futures_ohlcv_1d` (add roots CL, HO, RB)

-- Implied volatility (CME CVOL indices)
-  Discontinued: CME CVOL indices (SOVL/SVL) are not used/collected.

- MES microstructure (required for 5m/15m/60m)
  - Subscriptions: MBP‑10 (market‑by‑price depth), trades, quotes/TBBO for MES and ES (reference)
  - Feed: GLBX.MDP3 supports all three; depth → stable imbalance metrics; quotes/TBBO → spread & microprice; trades → aggressor flow.
  - Destination: `market_data.orderflow_1m` (extend schema/loader for MBP‑10 fields) and `market_data.databento_futures_ohlcv_1m` (quotes/trades alignment)

Actioning
- Add roots (ZC, ZW, KE, 6L, CNH, NQ, MNQ, RTY, M2K, CL, HO, RB) to DataBento collection config.
- (Removed) Do not provision `raw_intelligence.cme_cvol_indices`.
- Extend orderflow pipeline to ingest MBP‑10 depth + TBBO; validate feature coverage for microprice/imbalance.

---

## 📋 PRIMARY PLAN WE'VE BEEN WORKING FROM

### **FRESH START MASTER PLAN** (`docs/plans/FRESH_START_MASTER_PLAN.md`)
**Date:** November 18, 2025  
**Status:** Complete Rebuild - Clean Architecture  
**Purpose:** Single source of truth for new architecture

**Key Principles:**
- Source prefixing (ALL columns: `yahoo_`, `databento_`, `fred_`, etc.)
- Mac M4: ALL training + feature engineering (local, deterministic)
- BigQuery: Storage + Scheduling + Dashboard (NOT training)
- External Drive: PRIMARY data storage + Backup
- Dual Storage: Parquet (external drive) + BigQuery (mirror)

### **TRAINING MASTER EXECUTION PLAN** (`docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md`)
**Date:** November 15, 2025  
**Status:** ⚠️ Data Verification Complete - Issues Found - Training Blocked  
**Architecture:** Local-First (Mac M4), No Vertex AI, No BQML Training

**Key Updates:**
- Historical Data Integrated: 6,057 rows of soybean oil prices
- 11 Regime Tables Created: From historical_pre2000 to trump_2023_2025
- 338K+ Pre-2020 Rows Available: Full market cycle coverage
- Migration Complete: New naming convention (Option 3) implemented

---

## 🏗️ CURRENT ARCHITECTURE

### **Storage Layer: BigQuery**
**Purpose:** Data warehouse, curated views, and dashboard serving

**Status:** ✅ **SCHEMA DEPLOYED** (Phase 1 Complete)

**Datasets (12/12):** ✅ All created in `us-central1`
- `market_data` - Futures OHLCV, continuous contracts, roll calendar
- `raw_intelligence` - FRED, EIA, USDA, CFTC, weather, news, policy
- `signals` - Big 8, calculated signals, hidden relationships
- `features` - Master features table (400+ columns)
- `training` - 17 training tables (5 ZL + 12 MES horizons)
- `regimes` - Market regime classifications
- `drivers` - Primary and meta drivers
- `neural` - Feature vectors for neural training
- `predictions` - Model predictions
- `monitoring` - Model performance tracking
- `dim` - Dimension tables (instrument metadata, etc.)
- `ops` - Operations tables (ingestion runs, data quality events)

**Tables (57/57):** ✅ All created with correct schemas
- 11 market_data tables
- 10 raw_intelligence tables
- 6 signals tables
- 1 features table (`master_features` - **57 columns, expected 400+**)
- 19 training tables (regime + 5 ZL + 12 MES)
- 1 regimes table
- 2 drivers tables
- 1 neural table
- 1 monitoring table
- 2 ops tables
- 3 dim tables

**Views (0/31):** ❌ **NOT CREATED**
- Missing `api` dataset (blocks overlay view creation)
- 17 API overlay views (`api.vw_futures_overlay_*`)
- 5 Prediction overlay views (`predictions.vw_zl_*_latest`)
- 1 Regime overlay view (`regimes.vw_live_regime_overlay`)
- 5 Compatibility views (`training.vw_zl_training_*`)
- 1 Signals composite view (`signals.vw_big_seven_signals`)
- 2 MES overlay views (`features.vw_mes_*`)

**Labels (48/48):** ✅ All applied
- `tier`: raw, derived, ml, production, ops
- `category`: market, intelligence, signals, etc.
- `purpose`: trading, training, serving, etc.
- `data_type`: ohlcv, calculated, predictions, etc.

**Data:** ❌ **ALL TABLES EMPTY** (0 rows)
- Expected: Historical data 2000-2025
- Current: No data loaded

**Data Authority Policy (Effective Now)**
- Futures OHLCV (intraday + daily): DataBento is authoritative (2010→present). Deprecate Alpha/Vendor daily bars where overlapping. Keep Yahoo ZL only as a 2000–2010 bridge.
- Macro/risk: FRED remains canonical (rates, VIXCLS, credit). No CME CVOL usage; rely on VIX and realized volatility.

---

### **Compute Layer: Mac M4**
**Hardware:** Apple M4 Mac mini (16GB unified memory) + TensorFlow Metal GPU  
**Environment:** `vertex-metal-312` (Python 3.12.6)  
**Training:** 100% local (baselines, advanced, regime-specific, ensemble)  
**Inference:** 100% local prediction generation  
**Models:** 60-70 total (sequential training, memory-managed)  
**Cost:** $0 (no cloud compute)  
**Constraints:** Sequential training, FP16 mixed precision, external SSD

**Status:** ✅ Ready (no training yet - waiting for data)

---

### **Data Storage: External Drive**
**Location:** `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/`

**Status:** ⚠️ **INCOMPLETE - CRITICAL GAPS**

**What We Have:**
- ✅ FRED Economic: 57 files, ~150,644 rows (EXCELLENT)
- ✅ NOAA Weather: 15 files, ~54,907 rows (EXCELLENT)
- ✅ EIA Energy: 4 files, ~10,905 rows (GOOD)
- ✅ CFTC Positioning: 28 files, ~10,440 rows (GOOD)
- ⚠️ USDA Reports: 5 files, ~4,689 rows (PARTIAL)
- ⚠️ Yahoo Finance: 148 files but sparse (~78 rows sample)
- ⚠️ Alpha Vantage: 49 files (needs verification - user decided to REMOVE)

**What's Missing (CRITICAL):**
- ❌ **DataBento ZL: 0 files, 0 rows** (PRIMARY ASSET - NOT COLLECTED)
- ❌ **DataBento MES: 0 files, 0 rows** (SECONDARY ASSET - NOT COLLECTED)
- ❌ **DataBento ES: 0 files, 0 rows** (REFERENCE ASSET - NOT COLLECTED)
- ❌ **Brazil Weather (INMET): Empty folder**
- ❌ **Palm Oil / Barchart: Minimal data (2 files)**

**Organization Status:** ❌ **NOT ORGANIZED**
- Folders are BARE
- No organization per regime/horizon/model/topic
- Need research-based organization (gsquant, JPM DNA patterns)

---

### **UI Layer: Vercel Dashboard**
**Purpose:** Read-only UI  
**Data Source:** BigQuery only (`predictions.vw_zl_{h}_latest`)  
**No Dependencies:** On local models or Vertex AI  
**Status:** ⚠️ Active but cannot function (missing views + data)

---

## 🚨 CRITICAL ISSUES

### **Issue #1: No DataBento Data (CRITICAL)**
**Severity:** CRITICAL  
**Impact:** Cannot train ZL or MES models without price data

**Details:**
- ZL: 0 files, 0 rows (PRIMARY ASSET)
- MES: 0 files, 0 rows (SECONDARY ASSET)
- ES: 0 files, 0 rows (REFERENCE ASSET)
- Collection script exists: `scripts/live/databento_live_poller.py` but NOT RUNNING

**Fix Required:**
```bash
# Download historical data from DataBento
python3 scripts/ingest/download_databento_historical.py \
  --symbols ZL,MES,ES,ZS,ZM,CL,NG \
  --start 2010-01-01 \
  --end 2025-11-18

# Then start live collection
python3 scripts/live/databento_live_poller.py \
  --roots ZL,MES,ES \
  --interval 300 \
  --lookback 1440
```

---

### **Issue #2: Missing Overlay Views (HIGH)**
**Severity:** HIGH  
**Impact:** Dashboard cannot function, training exports unavailable

**Details:**
- Missing `api` dataset (blocks view creation)
- 0 of 31 expected views exist
- Overlay views defined in `scripts/deployment/create_overlay_views.sql` but not executed

**Fix Required:**
```bash
# Create api dataset
bq mk --location=us-central1 --description="API-facing overlay views" cbi-v14:api

# Create overlay views
bq query --use_legacy_sql=false < scripts/deployment/create_overlay_views.sql
```

---

### **Issue #3: master_features Incomplete (MEDIUM)**
**Severity:** MEDIUM  
**Impact:** Feature table incomplete

**Details:**
- Table created with only 57 columns
- Expected: 400+ columns with all features
- Some columns missing source prefixes

**Root Cause:**
- Schema definition in `PRODUCTION_READY_BQ_SCHEMA.sql` may be truncated
- Only partial column list was parsed/executed

**Fix Required:**
- Audit `PRODUCTION_READY_BQ_SCHEMA.sql` for complete master_features definition
- Verify all 400+ columns are defined
- Recreate table if necessary

---

### **Issue #4: Training Tables Missing Pre-2020 Data (HIGH)**
**Severity:** HIGH  
**Impact:** Cannot train on full 25-year window (2000-2025)

**Details:**
- All training tables start from 2020, not 2000 (missing 20 years)
- Regime assignments incomplete: Only 1-3 unique regimes per table (expected 7+)
- Critical issue: `zl_training_prod_allhistory_1m` has 100% placeholder regimes ('allhistory', weight=1)

**Fix Required:**
- Historical backfill: Yahoo ZL 2000-2010 → `market_data.yahoo_zl_historical_2000_2010`
- DataBento 2010-present → `market_data.databento_futures_*` tables
- Regime assignment: Load 11 regimes → `training.regime_calendar`
- Feature assembly: Build continuous series from Yahoo + DataBento

---

### **Issue #5: External Drive Not Organized (HIGH)**
**Severity:** HIGH  
**Impact:** Cannot efficiently train or access data

**Details:**
- Folders are BARE
- No organization per regime/horizon/model/topic
- Need research-based organization (gsquant, JPM DNA patterns)

**Fix Required:**
- Research industry-standard organization patterns
- Design dual-asset structure (ZL + MES)
- Organize by timeframe granularity (intraday vs. daily+)
- Implement meta-learning folder structure

---

## 📊 DATA SOURCES AVAILABLE

### **✅ Active Data Sources**

**1. DataBento GLBX.MDP3** (PRIMARY - NOT COLLECTED)
- **Role:** Primary live futures provider (CME/CBOT/NYMEX/COMEX)
- **Coverage:** 2010-present (15 years available)
- **Schemas:** `ohlcv-1m`, `ohlcv-1h`, `ohlcv-1d`
- **Symbols:** 29 futures (ZL, MES, ES, ZS, ZM, CL, NG, RB, HO, GC, SI, HG, etc.)
- **API Key:** `db-cSwxrJxRGGbqSBX74iuh9gqPrF4xf` (stored in Keychain)
- **Status:** ❌ **NOT COLLECTING** (critical gap)
- **Script:** `scripts/live/databento_live_poller.py`

**2. Yahoo Finance** (HISTORICAL BRIDGE - SPARSE)
- **Role:** ZL Historical Bridge (2000-2010 ONLY)
- **Coverage:** 2000-2010 (10 years)
- **Provides:** ZL=F OHLCV + 46+ technical indicators
- **Prefix:** `yahoo_` on ALL columns
- **Status:** ⚠️ **SPARSE** (148 files but ~78 rows sample)
- **Script:** `scripts/ingest/collect_yahoo_finance_comprehensive.py`

**3. FRED Economic Data** (EXCELLENT)
- **Role:** Macroeconomic indicators
- **Coverage:** 55-60 series, full history
- **Provides:** Interest rates, FX, credit spreads, inflation, etc.
- **Prefix:** `fred_` on ALL columns
- **Status:** ✅ **EXCELLENT** (57 files, ~150,644 rows)
- **Script:** `scripts/ingest/collect_fred_comprehensive.py`

**4. NOAA Weather** (EXCELLENT)
- **Role:** US weather data
- **Coverage:** Historical complete
- **Provides:** Temperature, precipitation, GDDs by region
- **Prefix:** `noaa_` on ALL columns
- **Status:** ✅ **EXCELLENT** (15 files, ~54,907 rows)
- **Script:** `scripts/ingest/collect_noaa_comprehensive.py`

**5. EIA Energy** (GOOD)
- **Role:** Biofuel production, RIN prices
- **Coverage:** Historical + live
- **Provides:** Biodiesel/ethanol production, RIN prices (D4/D6)
- **Prefix:** `eia_` on ALL columns
- **Status:** ✅ **GOOD** (4 files, ~10,905 rows)
- **Script:** `scripts/ingest/collect_eia_comprehensive.py`

**6. CFTC Positioning** (GOOD)
- **Role:** Commitments of Traders reports
- **Coverage:** Historical weekly
- **Provides:** Long/short positions, net positioning
- **Prefix:** `cftc_` on ALL columns
- **Status:** ✅ **GOOD** (28 files, ~10,440 rows)
- **Script:** `scripts/ingest/collect_cftc_comprehensive.py`

**7. USDA Reports** (PARTIAL)
- **Role:** Agricultural reports (WASDE, exports, crop progress)
- **Coverage:** Partial historical
- **Provides:** Soybean production, exports, crop conditions
- **Prefix:** `usda_` on ALL columns
- **Status:** ⚠️ **PARTIAL** (5 files, ~4,689 rows)
- **Script:** `scripts/ingest/collect_usda_comprehensive.py`

---

### **❌ Missing/Inactive Data Sources**

**1. Brazil Weather (INMET)** (MISSING)
- **Role:** Brazil soy belt weather
- **Coverage:** Should be 2000-2025
- **Status:** ❌ **EMPTY FOLDER**
- **Script:** `scripts/ingest/collect_inmet_brazil.py` (NOT RUNNING)

**2. Palm Oil / Barchart** (MINIMAL)
- **Role:** Competing vegetable oil prices
- **Coverage:** Should be historical
- **Status:** ⚠️ **MINIMAL** (2 files)
- **Script:** `scripts/ingest/collect_palm_barchart.py` (NOT RUNNING)

**3. News / Sentiment** (NOT RUNNING)
- **Role:** News intelligence, sentiment scoring
- **Coverage:** Should be 24/7 collection
- **Status:** ❌ **NOT COLLECTING**
- **Scripts:** 
  - `scripts/ingest/collect_news_scrapecreators_bucketed.py`
  - `scripts/ingest/collect_policy_trump.py`

**4. Alpha Vantage** (REMOVED)
- **Role:** Previously used for sentiment/indicators
- **Status:** ❌ **REMOVED** (user decision)
- **Action:** Delete existing 49 files?

---

## 📈 DEPLOYMENT STATUS

### **Phase 1: Schema Deployment** ✅ **COMPLETE**
- ✅ All 12 datasets created
- ✅ All 57 tables created
- ✅ All 48 labels applied
- ✅ Location: `us-central1` (unified)

### **Phase 2: Folders** ❌ **PENDING**
- ❌ `/TrainingData/live/` not created
- ❌ `/TrainingData/live_continuous/` not created

### **Phase 3: Overlay Views** ❌ **PENDING**
- ❌ `api` dataset not created
- ❌ 0 of 31 views created

### **Phase 4: Data Migration** ❌ **PENDING**
- ❌ No data loaded to BigQuery
- ❌ External drive data not migrated

### **Phase 5: Final Validation** ⚠️ **PARTIAL**
- ✅ Schema validation passed
- ❌ View validation failed (views missing)
- ❌ Data validation failed (data missing)

**Overall Progress:** 40% (2/5 phases complete)

---

## 🎯 HORIZON TRAINING STRATEGY

### **ZL (Soybean Oil) - 5 Horizons (Daily-Based)**
All ZL horizons are daily-based - no intraday special training needed.

| Horizon | Type | Training Strategy | Model Type | MAPE Target |
|---------|------|------------------|------------|-------------|
| 1 week | Short-term | Main training | Tree + Neural | < 1.5% |
| 1 month | Short-term | Main training | Tree + Neural | < 1.5% |
| 3 months | Medium-term | Main training | Tree + Neural | < 1.5% |
| 6 months | Long-term | Main training | Tree + Neural | < 1.5% |
| 12 months | Long-term | Main training | Tree + Neural | < 1.5% |

### **MES (Micro E-mini S&P 500) - 12 Horizons**

**SPECIAL TRAINING (Intraday - 6 Horizons):**
- 1min, 5min, 15min, 30min, 1hr, 4hr
- Neural networks (LSTM, TCN)
- 150-200 micro features
- MAPE target: < 0.8%

**MAIN TRAINING (Multi-Day+ - 6 Horizons):**
- 1d, 7d, 30d, 3m, 6m, 12m
- Tree models (LightGBM, XGBoost)
- 200-300 macro/fundamental features
- MAPE target: < 1.2%

**Reference:** `HORIZON_TRAINING_STRATEGY.md`

---

## 🚀 IMMEDIATE PRIORITIES (Per User Directive)

### **Priority 1: Data Collection (CRITICAL)**
**User Directive:** "we need to fucking build out our data first like I asked so many times"

**Actions:**
1. **DataBento Historical Download** (CRITICAL)
   - ZL 2010-2025 (~15 years)
   - MES 2010-2025
   - ES 2010-2025
   - Secondary symbols (ZS, ZM, CL, etc.)

2. **Yahoo Historical Backfill** (CRITICAL FOR ZL)
   - ZL=F 2000-2010 bridge
   - All 79 symbols full history

3. **Weather Historical**
   - INMET Brazil 2000-2025
   - Verify NOAA coverage complete

4. **USDA Historical Expansion**
   - Export sales by destination
   - Crop progress by state
   - Full WASDE history

---

### **Priority 2: Data Organization (HIGH)**
**User Directive:** "nothing is organized per regime/horizon/model/topic/nothing"

**Actions:**
1. **Research Industry Patterns**
   - gsquant repo organization
   - JPM DNA repos organization
   - Quant forecasting setup patterns

2. **Design Dual-Asset Structure**
   - ZL (primary) vs. MES (secondary/hidden)
   - Shared vs. asset-specific data
   - Timeframe-specific organization

3. **Implement Organization**
   - Regime-based folders
   - Horizon-based folders
   - Model-based folders
   - Topic-based folders

**Reference:** `DUAL_ASSET_ORGANIZATION_DESIGN.md`, `EXTERNAL_DRIVE_ORGANIZATION_RESEARCH.md`

---

### **Priority 3: Complete BigQuery Deployment (MEDIUM)**
**Actions:**
1. Create `api` dataset
2. Create overlay views (31 views)
3. Audit `master_features` schema (expand to 400+ columns)
4. Load historical data to BigQuery

---

## 📋 KEY DOCUMENTS

### **Master Plans**
- `docs/plans/FRESH_START_MASTER_PLAN.md` - Primary architecture plan
- `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md` - Training execution plan

### **Status Reports**
- `BQ_CURRENT_STATE_REPORT.md` - BigQuery current state
- `DATA_COLLECTION_STATUS_NOW.md` - Data collection status
- `DEPLOYMENT_AUDIT_REPORT.md` - Deployment audit
- `CURRENT_STATUS_REPORT.md` - This document

### **Design Documents**
- `HORIZON_TRAINING_STRATEGY.md` - Horizon training strategy
- `DUAL_ASSET_ORGANIZATION_DESIGN.md` - Dual-asset organization
- `EXTERNAL_DRIVE_ORGANIZATION_RESEARCH.md` - Organization research
- `QUANT_BACKEND_ORGANIZATION_PATTERNS.md` - Industry patterns

### **Deployment Scripts**
- `PRODUCTION_READY_BQ_SCHEMA.sql` - Complete BigQuery schema
- `scripts/deployment/deploy_bq_schema.sh` - Schema deployment
- `scripts/deployment/create_overlay_views.sql` - Overlay views
- `scripts/validation/validate_bq_deployment.py` - Validation

---

## ✅ SUMMARY

**Current State:**
- ✅ BigQuery schema deployed (12 datasets, 57 tables)
- ❌ No data collected (critical blocker)
- ❌ External drive not organized
- ❌ Overlay views not created
- ⚠️ Training blocked (waiting for data)

**Primary Plan:** `FRESH_START_MASTER_PLAN.md`  
**Execution Plan:** `TRAINING_MASTER_EXECUTION_PLAN.md`

**Next Steps:**
1. **STOP DEPLOYING. START COLLECTING.**
2. Priority 1: DataBento historical download (ZL, MES, ES)
3. Priority 2: Organize external drive (research-based structure)
4. Priority 3: Complete BigQuery deployment (views, data load)

**Time to Full Data:** 1-2 days of continuous collection

---

**Last Updated:** November 18, 2025  
**Next Review:** After data collection begins
