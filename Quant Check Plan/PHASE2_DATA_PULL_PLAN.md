# 🚀 Phase 2: Complete Data Pull Plan
**Date:** November 24, 2025  
**Goal:** Pull complete, fresh data from source APIs - NO splicing, NO partial data

---

## ✅ PRINCIPLE: PULL FRESH FROM SOURCE

**DO:**
- Pull complete history directly from APIs
- One clean pull per data source
- Load directly to BigQuery

**DO NOT:**
- Splice partial data from external drive
- Use Yahoo for anything
- Mix data sources for same instrument

---

## 📊 DATA SOURCES & SCRIPTS

### 1. DATABENTO (Market Data)

**Script Location:** `scripts/ingest/download_ALL_databento_historical.py`

**What it does (UPDATED):**
- Streams historical OHLCV from Databento GLBX.MDP3 for all configured symbols/timeframes
- Loads data **DIRECTLY into BigQuery** tables:
  - `market_data.databento_futures_ohlcv_1d` (daily)
  - `market_data.databento_futures_ohlcv_1h` (hourly)
  - `market_data.databento_futures_ohlcv_1m` (1-minute)
  - `market_data.databento_futures_ohlcv_1s` (1-second, MES only)
- No external-drive staging, no manual CSV downloads
- **Changed 2025-11-25:** This script is the canonical Databento loader. Do **not** revert to batch jobs + external drive; intraday schemas use scalar `spread_legs STRING` (not arrays) to match `market_data.databento_futures_ohlcv_*` exactly.

**Symbols Covered:**
| Tier | Symbols | Status |
|------|---------|--------|
| 1 Critical | ZL, ZS, ZM, ES | ZL ✅, others pending |
| 2 Energy | CL, HO, NG, RB | Pending |
| 3 Grains | ZC, ZW | Pending |
| 4 Indices | NQ, MNQ, RTY, M2K | Pending |
| 5 Metals | GC, SI, HG | Pending |
| 6 Additional | BZ, QM, PA, PL, ZR, ZO, LE, GF, HE | Pending |
| **Options** | **OZL.OPT, OZS.OPT, OZM.OPT, ES.OPT, MES.OPT** | **Pending** |

**Current State:**
- ZL: ✅ Ready (3,998 rows, 2010-2025)
- MES: ⚠️ **INCOMPLETE** (2,036 rows, 2019-2025 only - **need full history 2010-2025**)
- ZS, ZM, CL, HO: ❌ Need pull (ZL supporting symbols)
- ES, ZQ, ZT, ZN, ZB: ❌ Need pull (MES supporting symbols - after ZL complete)
- **Options:** Not yet submitted (OZL.OPT, OZS.OPT, OZM.OPT, ES.OPT, MES.OPT)

**Priority:** ZL engine first (pull ZS, ZM, CL, HO). MES full history pull after ZL stable.

**To Complete (Databento core):**
1. Ensure `DATABENTO_API_KEY` is set (environment or macOS Keychain).
2. From repo root, run:
   - `python3 scripts/ingest/download_ALL_databento_historical.py`
3. Verify BigQuery loads:
   - `bq query --use_legacy_sql=false "SELECT COUNT(*) FROM market_data.databento_futures_ohlcv_1d WHERE symbol = 'ZL'"` (and other roots)

**Options Data (still pending separate path):**
> The options flow (OZL.OPT, OZS.OPT, OZM.OPT, ES.OPT, MES.OPT) still uses the batch/portal workflow until the dedicated options ingestor is updated to write directly to BigQuery.

**Options Data (LEGACY FLOW - TO BE MODERNIZED):**
- **ZL Options:** OZL.OPT, OZS.OPT, OZM.OPT (for implied vol, GEX, vol surface, crush spread vol)
- **MES Options:** ES.OPT, MES.OPT (for MES GEX, vol surface, put/call ratios)
- **Schemas:** ohlcv-1d, ohlcv-1h, trades, quotes, statistics
- **Purpose:** IV30 calculation, gamma exposure, volatility surface, put/call ratios
- **CME Options Add-On:** ✅ ENABLED (confirmed in DATABENTO_PLAN_VALIDATION.md)

---

### 2. FRED (Economic Data)

**Script Location:** `/Volumes/Satechi Hub/Projects/CBI-V14/scripts/ingest/collect_fred_comprehensive.py`

**What it does:**
- Pulls 55-60 series from FRED API
- Full history (configurable start date)
- Rate-limited (1 req/sec)
- Saves to parquet

**Series Covered (60 total):**
| Category | Series | Key Ones |
|----------|--------|----------|
| Interest Rates | 9 | DFF, DGS10, DGS2 |
| Inflation | 4 | CPIAUCSL, PCEPI |
| PPI | 4 | PPIACO, PPIIDC |
| Employment | 6 | UNRATE, PAYEMS |
| GDP | 4 | GDP, GDPC1, INDPRO |
| Money Supply | 3 | M2SL, M1SL |
| Market | 3 | **VIXCLS**, DTWEXBGS |
| Credit Spreads | 4 | T10Y2Y, TEDRATE |
| Commodities | 1 | DCOILWTICO |
| FX | 7 | **DEXUSEU, DEXCHUS, DEXBZUS, DEXJPUS, DTWEXBGS, DTWEXAFEGS, DTWEXEMEGS** |
| Energy | 3 | DCOILBRENTEU, DHHNGSP |
| Consumer | 4 | UMCSENT, HOUST |
| Activity | 4 | CFNAI, STLFSI2 |

**Current State:**
- ✅ 41 series loaded to BigQuery (2010-2025)
- ✅ Critical series ready: DGS10, DGS2, VIXCLS, VXVCLS, DTWEXBGS, credit spreads
- ✅ **FX series loaded from FRED:** DEXUSEU (EUR/USD), DEXCHUS (USD/CNY), DEXBZUS (USD/BRL), DEXJPUS (USD/JPY), DTWEXBGS (Dollar Index)

**✅ All Critical Series Added:**
- ✅ T10YIE (10Y Breakeven Inflation) - Added
- ✅ NFCI (Financial Conditions Index) - Added
- ✅ DEXJPUS (USD/JPY) - Already had
- ✅ VXVCLS (3-Month VIX) - Added (replaces VIX3M)
- ✅ VXOCLS (Old VXO) - Added

**VIX Term Structure (No VX.FUT):**
- **Problem:** VX.FUT trades on CBOE CFE, not CME Globex. Not in subscription.
- **Solution:** ✅ Use FRED VIX substitutes (now available):
  - `VIXCLS` (spot VIX) - ✅ Loaded
  - `VXVCLS` (3-Month VIX) - ✅ Loaded (replaces VIX3M)
  - `VXOCLS` (Old VXO) - ✅ Loaded
  - Calculate: `vix_term_structure = VXVCLS / VIXCLS`
  - Calculate: `vix_term_slope = VXVCLS - VIXCLS`
  - Calculate: `vix_contango_flag = VXVCLS > VIXCLS`

**To Complete:**
1. Add 5 missing FRED series to `collect_fred_data.py`
2. Run fresh pull: `python scripts/collect_fred_data.py`
3. Load to BigQuery (already have infrastructure)

---

### 3. ADDITIONAL DATA SOURCES

**Available Scripts on External Drive:**

| Script | Data Source | Status |
|--------|-------------|--------|
| `collect_cftc_comprehensive.py` | CFTC COT data | Need to run |
| `collect_noaa_comprehensive.py` | Weather data | Need to run |
| `collect_usda_comprehensive.py` | USDA reports | Need to run |
| `collect_eia_comprehensive.py` | EIA energy | Need to run |
| `collect_google_public_datasets.py` | Google BQ public | Need to run |

---

## 🔧 EXECUTION PLAN

### Step 1: Check Databento Job Status
```bash
cd "/Volumes/Satechi Hub/Projects/CBI-V14"
python scripts/ingest/check_databento_jobs.py
```

### Step 2: Download Completed Databento Jobs
- Go to https://databento.com/portal/batch/jobs
- Download all completed jobs
- Extract to `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/databento_*/`

### Step 3: Pull Fresh FRED Data (2010-present)
```bash
# Modify START_DATE in script first!
cd "/Volumes/Satechi Hub/Projects/CBI-V14"
python scripts/ingest/collect_fred_comprehensive.py
```

### Step 4: Create BigQuery Loader
**Need to create:** `load_all_to_bigquery.py`
- Load Databento OHLCV to `market_data.databento_futures_ohlcv_1d`
- Load FRED to `raw_intelligence.fred_economic`
- Idempotent (MERGE, not INSERT)

### Step 5: Calculate Features
- Expand `ingest_zl_v2.py` to include:
  - Cross-asset features (ZS, ZM, CL correlations)
  - Crush margin
  - FRED macro features
  - FX features

### Step 6: Retrain with Full Features
- 50-100 features
- TimeSeriesSplit CV
- Proper hyperparameters

---

## 📋 IMMEDIATE NEXT ACTIONS (ZL Engine First)

### Phase 1: ZL Engine (Now)
1. **Pull ZL supporting symbols** - ZS, ZM, CL, HO from Databento
2. **Add 5 FRED series** - T10YIE, NFCI, DEXJPUS, VIX9D, VIX3M (for future MES)
3. **Build ZL engine tables** - Create engine-specific structure
4. **Build ZL features** - Crush margin, cross-asset, macro (50+ features)
5. **Retrain ZL model** - With expanded feature set

### Phase 2: MES Engine (After ZL Complete)
1. **Pull full MES history** - 2010-2025 (currently only 2019-2025)
2. **Pull MES supporting symbols** - ES, ZQ, ZT, ZN, ZB from Databento
3. **Build MES engine tables** - Create engine-specific structure
4. **Build MES features** - Microstructure, macro, VIX term structure (58+ features)
5. **Train MES models** - Special (intraday) + Main (daily) models

**See:** `ZL_EXECUTION_PLAN.md` for ZL details, `MES_MASTER_PLAN.md` for MES details

---

## 🎯 SUCCESS CRITERIA

### ZL Engine (Phase 1)
| Data Source | Target Rows | Date Range | Status |
|-------------|-------------|------------|--------|
| ZL (Databento) | ~3,800 | 2010-2025 | ✅ Ready |
| ZS (Databento) | ~3,800 | 2010-2025 | ❌ Need pull |
| ZM (Databento) | ~3,800 | 2010-2025 | ❌ Need pull |
| CL (Databento) | ~3,800 | 2010-2025 | ❌ Need pull |
| HO (Databento) | ~3,800 | 2010-2025 | ❌ Need pull |
| FRED VIX | ~3,800 | 2010-2025 | ✅ Ready |
| FRED Macro | ~3,800 | 2010-2025 | ✅ Ready |

### MES Engine (Phase 2 - After ZL)
| Data Source | Target Rows | Date Range | Status |
|-------------|-------------|------------|--------|
| MES (Databento) | ~3,800 | **2010-2025** | ⚠️ **Only 2019-2025** |
| ES (Databento) | ~3,800 | 2010-2025 | ❌ Need pull |
| ZQ (Databento) | ~3,800 | 2010-2025 | ❌ Need pull |
| ZT (Databento) | ~3,800 | 2010-2025 | ❌ Need pull |
| ZN (Databento) | ~3,800 | 2010-2025 | ❌ Need pull |
| ZB (Databento) | ~3,800 | 2010-2025 | ❌ Need pull |
| VX.FUT | N/A | N/A | ❌ **Not available** (use FRED VIX substitutes) |
| FRED VIX9D | ~3,800 | 2010-2025 | ❌ Need add |
| FRED VIX3M | ~3,800 | 2010-2025 | ❌ Need add |

**All data aligned to same date range, pulled fresh from source APIs.**
