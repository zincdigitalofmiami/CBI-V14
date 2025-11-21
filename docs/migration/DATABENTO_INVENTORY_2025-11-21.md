# 📚 DATABENTO DOCUMENTATION & SCRIPTS INVENTORY
**Date:** November 21, 2025  
**Purpose:** Read-only audit of all Databento-related documentation and scripts

---

## ✅ DATABENTO DOCUMENTATION FOUND

### **Key Documents (12 total):**

1. **`docs/reports/DATABENTO_DATA_STATUS_NOV20.md`** ⭐ **MOST CURRENT**
   - Date: November 20, 2025
   - Summary: Data already downloaded (MES, ZL hourly/daily, Forex, VIX)
   - Status: 35 new batch jobs submitted, 29 processing
   - Critical Gap: ZL 1-minute missing (but submitted)

2. **`docs/reports/data/COMPLETE_DATABENTO_DOWNLOAD_LIST.md`**
   - Complete universe: 26 symbols
   - Tiers: Critical (ZL/ZS/ZM/ES), Energy, Grains, Indices, Metals, Livestock
   - Date range: 2010-2025
   - Cost: $0 (included in plan)

3. **`docs/features/DATABENTO_PLAN_VALIDATION.md`**
   - Plan validation document

4. **`docs/migration/DATABENTO_VIX_DOWNLOAD_INSTRUCTIONS.md`**
   - VIX-specific download instructions

5. **`docs/archive/YAHOO_AND_DATABENTO_CLARIFICATION.md`** ⭐ **IMPORTANT**
   - Clarifies: Databento = canonical, Yahoo = ZL 2000-2010 bridge only

6. **Other Supporting Docs:**
   - `DATABENTO_DATA_INVENTORY.md` (multiple versions)
   - `DATABENTO_LIVE_API_USAGE.md`
   - `DATABENTO_CONNECTION_FIX.md`
   - `DATABENTO_COVERAGE_RESULTS.md`

---

## ✅ DATABENTO SCRIPTS FOUND

### **Download Scripts (5 total):**

1. **`scripts/ingest/download_ALL_databento_historical.py`** ⭐ **MAIN DOWNLOADER**
   - Downloads ALL 26 symbols from Databento Portal
   - Uses Databento Python API
   - Batch job submission
   - Date range: 2010-06-06 to present
   - Output: `/Volumes/Satechi Hub/.../databento_*/`
   - Status: **WORKING** (35 jobs submitted Nov 20)

2. **`scripts/ingest/download_zl_1min_databento.py`**
   - ZL 1-minute specific downloader
   - Fixes: API errors from previous attempts
   - Status: **WORKING** (job GLBX-20251120-CQRNQQM89S processing)

3. **`scripts/ingest/download_databento_vix.py`**
   - VIX OPRA data downloader
   - Status: **COMPLETE** (VIX data exists)

4. **`scripts/ingest/check_databento_jobs.py`**
   - Monitors batch job status
   - Checks https://databento.com/portal/batch/jobs

5. **`scripts/ingest/check_and_fetch_zl_1min.py`**
   - ZL 1-minute job checker/fetcher

### **Processing Scripts (3 total):**

1. **`scripts/ingest/process_databento_vix.py`**
   - Processes VIX OPRA data

2. **`scripts/ingest/aggregate_mes_intraday.py`**
   - Aggregates MES intraday bars

3. **`scripts/staging/create_mes_futures_daily.py`**
   - Creates MES daily staging files

### **❌ MISSING: BigQuery Load Scripts**

**NOT FOUND:**
- No `load_databento_to_bigquery.py`
- No `load_databento_to_bq.py`
- No Databento → BigQuery loader exists yet

---

## 📊 CURRENT DATABENTO DATA STATE

### **What Exists on External Drive:**

| Symbol/Asset | Timeframe | Files | Size | Date Range | Location |
|--------------|-----------|-------|------|------------|----------|
| **MES** | 1-min, 1-hour, daily | 209 JSON | 748 MB | 2019-04-14 → 2025-11-16 | `/Volumes/Satechi Hub/.../databento_mes/` |
| **ZL** | 1-hour, daily | 4,008 JSON | 462 MB | 2010-06-06 → 2025-11-18 | `/Volumes/Satechi Hub/.../databento_zl/` |
| **ZL 1-minute** | ❌ MISSING | 0 | 0 | - | Job GLBX-20251120-CQRNQQM89S processing |
| **Forex** | Daily | 16 Parquet | 3.6 MB | Various | `/Volumes/Satechi Hub/.../databento_forex/` |
| **VIX** | Daily (OPRA) | 2 Parquet | 7.5 MB | Various | `/Volumes/Satechi Hub/.../databento_vix/` |
| **All Others** | ❌ MISSING | 0 | 0 | - | 29 jobs processing (Nov 20) |

**Total Downloaded:** 4,236 files, 1.2 GB

### **What's in BigQuery:**

| Table | Rows | Status |
|-------|------|--------|
| `market_data.databento_futures_ohlcv_1d` | **0** | Empty |
| `market_data.databento_futures_ohlcv_1h` | **NOT CREATED** | Missing table |
| `market_data.databento_futures_ohlcv_1m` | **0** | Empty |
| `market_data.databento_futures_continuous_1d` | **0** | Empty |

**❌ CRITICAL:** All Databento BigQuery tables are EMPTY. No loader exists.

---

## 🔍 KEY INSIGHTS FROM DOCUMENTATION

### **1. Databento Download Method:**

From `download_ALL_databento_historical.py`:

```python
# Uses Databento Python API
import databento as db

client = db.Historical(api_key=DATABENTO_API_KEY)

# Submits batch jobs
job_id = client.batch.submit_job(
    dataset=DATASET,  # "GLBX.MDP3"
    symbols=[f"{root}.FUT"],  # e.g., "ZL.FUT"
    schema="ohlcv-1d",  # or "ohlcv-1h", "ohlcv-1m"
    start=START_DATE,
    end=END_DATE,
    stype_in="parent",  # Continuous front-month contracts
    split_duration="month"
)
```

**Output:** Batch jobs on Databento Portal → Manual download → Extract to external drive

### **2. Data Format:**

From file inspection:
- **Format:** JSON (NDJSON - newline delimited)
- **Schema:** OHLCV bars
- **Fields:** `ts_event, open, high, low, close, volume, symbol, ...`
- **Naming:** `glbx-mdp3-YYYYMMDD.ohlcv-1h.json` or `.ohlcv-1d.json`

### **3. Parent Symbology:**

From docs:
- `stype_in="parent"` = Continuous front-month contracts
- `.FUT` suffix for futures (e.g., `ZL.FUT`)
- Automatic roll handling by Databento
- No calendar spreads (excluded by design)

### **4. Critical Gap (Per Nov 20 Status):**

**Have:**
- MES: Complete (all timeframes, 2019-2025)
- ZL: 1-hour + daily (2010-2025)
- Forex: Daily (various pairs)
- VIX: Daily OPRA

**Missing:**
- ZL 1-minute (job processing)
- All other symbols: ZS, ZM, ES, CL, HO, NG, RB, ZC, ZW, NQ, MNQ, RTY, M2K, GC, SI, HG, BZ, QM, PA, PL, ZR, ZO, LE, GF, HE (29 jobs processing)

---

## 🎯 WHAT WE NEED TO BUILD

### **Priority 1: Databento → BigQuery Loader** ❌ **DOES NOT EXIST**

**Need:** `scripts/ingestion/load_databento_to_bq_idempotent.py`

**What it must do:**
1. Read JSON files from external drive (or download via API)
2. Parse NDJSON format
3. Map fields:
   - `ts_event` → `date` (for daily) or keep `ts_event` (for intraday)
   - Extract `root` from symbol (e.g., `ZLZ4` → `ZL`)
   - Handle `open, high, low, close, volume, settle, open_interest, is_spread`
4. Use MERGE (not INSERT) on `(symbol, date)` or `(symbol, ts_event)`
5. Track in `ops.databento_load_state`
6. Batch process (avoid memory issues)

**Inputs:**
- External drive: `/Volumes/Satechi Hub/.../databento_*/GLBX-*/glbx-mdp3-*.json`
- OR: Databento API download directly

**Outputs:**
- `market_data.databento_futures_ohlcv_1d` (daily bars)
- `market_data.databento_futures_ohlcv_1h` (hourly bars) - **need to create table**
- `market_data.databento_futures_ohlcv_1m` (1-min bars)
- `ops.databento_load_state` (tracking)

### **Priority 2: Feature Consolidation** (Already documented in DATA_FLOW_MAP)

**Need:** Read from BigQuery Databento tables (after Priority 1 complete)

---

## 🔴 CRITICAL FINDINGS

1. **External Drive Files = SCRATCH ONLY (Per Codex)**
   - Do NOT build loader that reads from external drive
   - Treat as temporary/scratch space
   - Canonical flow: Databento Portal → BigQuery (NOT external → BQ)

2. **No BigQuery Loader Exists**
   - All Databento scripts are for DOWNLOADING
   - Zero scripts for LOADING to BigQuery
   - This is the #1 missing piece

3. **Batch Jobs Still Processing**
   - 29 of 35 jobs still in queue (as of Nov 20)
   - Can't load what we don't have yet
   - May need to wait for downloads to complete

4. **Table Schema Mismatch**
   - Existing tables expect specific schema
   - Need to verify JSON format matches BQ schema
   - May need schema transformation

---

## 📋 RECOMMENDED APPROACH (Based on Codex Protocol)

### **Option A: Wait for Downloads, Then API → BQ Direct**

1. Wait for 29 batch jobs to complete
2. Use Databento Python API to download directly to Python
3. Transform and load to BigQuery immediately
4. No external drive dependency

**Pros:** Clean, canonical flow (Databento → BQ)  
**Cons:** Need to wait for jobs

### **Option B: One-Time Load from External Drive (Exception)**

1. Load existing ZL hourly + MES hourly from external drive (one-time only)
2. Future loads: API → BQ direct (no external drive)
3. Document this as bootstrap/migration only

**Pros:** Can start testing with real data now  
**Cons:** Violates "no external → BQ" rule, but documented exception

### **Option C: Skip External Files, Download Fresh via API**

1. Ignore existing external drive files completely
2. Re-download ZL + MES via Databento API
3. Load directly to BigQuery
4. Clean slate, no legacy file dependencies

**Pros:** Fully canonical  
**Cons:** Re-downloads data we already have

---

## ✅ NEXT STEPS (AWAITING DECISION)

**Kirk/Codex, please decide:**

1. **Which approach?** (A, B, or C above)
2. **Wait for jobs or proceed?** (29 jobs still processing)
3. **Build loader now or wait?**

**Once decided, I will:**
- Build `load_databento_to_bq_idempotent.py`
- Create `market_data.databento_futures_ohlcv_1h` table
- Test with ZL/MES data
- Document schema mappings

---

**Status:** 🛑 READ-ONLY COMPLETE, AWAITING DIRECTION

