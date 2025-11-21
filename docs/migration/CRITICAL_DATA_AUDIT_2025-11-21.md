# 🚨 CRITICAL DATA AUDIT - BEFORE ANY INGESTION
**Date:** November 21, 2025  
**Status:** 🔴 FULL STOP - AUDIT MODE  
**Purpose:** PREVENT DUPLICATES, ENSURE UNIFORM COVERAGE

---

## ✅ BIGQUERY STATE (VERIFIED)

**Source of Truth: BigQuery `market_data` dataset**

| Table | Rows | Status |
|-------|------|--------|
| `databento_futures_ohlcv_1d` | **0** | ❌ EMPTY |
| `databento_futures_ohlcv_1m` | **0** | ❌ EMPTY |
| `databento_futures_continuous_1d` | **0** | ❌ EMPTY |

**✅ CONFIRMED: NO DATABENTO DATA IN BIGQUERY YET**

---

## ✅ EXTERNAL DRIVE STATE (VERIFIED)

**Location:** `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/databento_*`

### Data That EXISTS (Downloaded from Databento):

| Symbol | Files | Size | Timeframe | Date Range |
|--------|-------|------|-----------|------------|
| **ZL** | 4,008 | 462 MB | 1-hour | 2010-06-06 → 2025-11-18 |
| **MES** | 209 | 748 MB | 1-hour | 2019-04-14 → 2025-11-18 |
| **FX (Forex)** | 16 | 3.6 MB | Daily | Various |
| **VIX** | 2 | 7.5 MB | Daily | Various |

**Total Downloaded:** 4,236 files, 1.2 GB

### Data That DOES NOT EXIST (Empty Directories):

| Symbol | Status | Reason |
|--------|--------|--------|
| ZL 1-minute | ❌ EMPTY | Not downloaded yet |
| ZL daily | ❌ EMPTY | Not downloaded yet |
| ZS (all) | ❌ EMPTY | Not downloaded yet |
| ZM (all) | ❌ EMPTY | Not downloaded yet |
| ES | ❌ EMPTY | Not downloaded yet |
| CL, HO, NG, RB | ❌ EMPTY | Not downloaded yet |
| ZC, ZW | ❌ EMPTY | Not downloaded yet |
| NQ, MNQ, RTY, M2K | ❌ EMPTY | Not downloaded yet |
| GC, SI, HG | ❌ EMPTY | Not downloaded yet |
| All others (14 more) | ❌ EMPTY | Not downloaded yet |

---

## ✅ STAGING FILES STATE (VERIFIED)

**Location:** `/Users/kirkmusick/Documents/GitHub/CBI-V14/TrainingData/staging/`

### What's in Staging:

| File | Rows | Source | Status |
|------|------|--------|--------|
| `yahoo_historical_prefixed.parquet` | 6,380 | Yahoo Finance | ⚠️ YAHOO (not Databento) |
| `zl_daily_aggregated.parquet` | 3,998 | ? | ⚠️ Unknown source |
| `mes_1hr_features.parquet` | 1 | ? | ❌ INSUFFICIENT |
| Various macro files | Various | FRED/USDA/EIA/etc | ✅ OK (non-price) |

**⚠️ WARNING:** Staging files are NOT from Databento and should NOT be used for canonical price data.

---

## 🎯 CRITICAL DECISION POINTS

### **1. DATA SOURCE HIERARCHY (FROZEN)**

**Per Codex directive:**
```
Databento = CANONICAL source for ALL futures price/volume data
Yahoo = ONLY for ZL 2000-2010 bridge (explicitly defined stitch)
```

**This means:**
- ❌ Do NOT use `yahoo_historical_prefixed.parquet` for 2010-2025
- ❌ Do NOT use `zl_daily_aggregated.parquet` (unknown source)
- ✅ ONLY use Databento data from external drive
- ✅ Yahoo ONLY for ZL 2000-2010 (with explicit stitch documentation)

### **2. WHAT DATA DO WE ACTUALLY HAVE FOR INGESTION?**

**For ZL:**
- ✅ 1-hour: 4,008 files (2010-2025) on external drive
- ❌ Daily: NONE (need to download from Databento)
- ❌ 1-minute: NONE (need to download from Databento)

**For MES:**
- ✅ 1-hour: 209 files (2019-2025) on external drive
- ❌ Daily: NONE
- ❌ 1-minute: NONE

**For All Other Symbols (ZS, ZM, ES, CL, etc.):**
- ❌ NONE

### **3. WORKFLOW CORRECTION**

**WRONG Workflow (What I Almost Did):**
1. Use staging parquet files → consolidate → load to BQ
2. Risk: Using non-Databento data, wrong source hierarchy

**CORRECT Workflow (What We MUST Do):**
1. Load existing Databento data (ZL 1h + MES 1h) from external drive → BigQuery raw tables
2. Download missing Databento data (ZL daily, ZL 1min, all other symbols)
3. Load new downloads → BigQuery raw tables
4. Build consolidated features FROM BigQuery raw tables (Databento-sourced)
5. Load features → `daily_ml_matrix`

---

## 🔴 CRITICAL GAPS ANALYSIS

### Gap 1: Missing Databento Downloads

**We have:**
- ZL 1-hour only
- MES 1-hour only

**We need (per MASTER_PLAN and Codex):**
- ZL: daily + 1-minute (for microstructure features)
- MES: daily + 5-min/15-min/30-min/4-hour (for all MES horizons)
- ZS, ZM: daily + 1-minute (for crush spread)
- ES: daily (for regime classification)
- All others: daily minimum

**Action:** Download from Databento Portal

### Gap 2: BigQuery is Empty

**Current state:** 0 rows in all Databento tables

**Action:** Load existing external drive data FIRST before any new downloads

### Gap 3: Staging Files Not Databento-Sourced

**Current state:** Staging parquet files are Yahoo/unknown sources

**Action:** Do NOT use for canonical price data, only for Yahoo 2000-2010 bridge

---

## ✅ SAFE EXECUTION PLAN (LOCKED)

### Phase 1: Load Existing Databento Data (SAFE - No Downloads Yet)

**What:** Load ZL 1-hour + MES 1-hour from external drive → BigQuery

**Steps:**
1. Create loader script: `scripts/ingestion/load_databento_raw_to_bq.py`
2. Read JSON files from external drive
3. Parse and load to `market_data.databento_futures_ohlcv_1h` (create if needed)
4. Verify row counts match file counts
5. Check for duplicates (should be 0)

**Safety:**
- Read-only from external drive
- No risk of duplicates (BQ tables are empty)
- No new downloads yet

**Expected Result:**
- ZL 1-hour: ~4,000 files → ~X rows in BQ
- MES 1-hour: ~209 files → ~Y rows in BQ

### Phase 2: Identify Missing Databento Downloads (SAFE - Planning Only)

**What:** Create precise download list from Databento Portal

**Steps:**
1. Review https://databento.com/portal/download-center
2. For each symbol, specify:
   - Exact date range (e.g., 2010-06-06 to 2025-11-21)
   - Exact schema (ohlcv-1d, ohlcv-1h, ohlcv-1m)
   - Exact symbols (no wildcards)
3. Document in `docs/data/DATABENTO_DOWNLOAD_SPEC_FINAL.md`
4. Review for uniformity (same date ranges where applicable)

**Safety:**
- No downloads yet, just planning
- Ensures uniform coverage
- Prevents partial/inconsistent data

### Phase 3: Execute Databento Downloads (AFTER REVIEW)

**What:** Download missing data from Databento

**Steps:**
1. Submit download jobs via Databento Portal
2. Wait for completion
3. Download to external drive (separate directories per symbol/timeframe)
4. Verify file counts and sizes

**Safety:**
- Downloads go to external drive (not BQ yet)
- Can review before loading
- No risk of BQ duplicates

### Phase 4: Load New Downloads to BigQuery (AFTER VERIFICATION)

**What:** Load new downloads → BigQuery raw tables

**Steps:**
1. Use same loader script from Phase 1
2. Load by symbol/timeframe batch
3. Verify no duplicates (check date ranges don't overlap with Phase 1)
4. Document row counts

**Safety:**
- Loader script already tested in Phase 1
- Can check for duplicates before committing
- Can delete and reload if issues

### Phase 5: Build Consolidated Features (AFTER ALL RAW DATA LOADED)

**What:** Create `daily_ml_matrix` from BigQuery raw Databento tables

**Steps:**
1. Create consolidation script that reads FROM BigQuery Databento tables
2. Calculate pivots, fibs, golden zone FROM Databento OHLCV
3. Join macro/policy data
4. Load to `features.daily_ml_matrix`

**Safety:**
- All source data is Databento (canonical)
- Can test on 10 rows first
- Integration test already passed

---

## 🚨 CRITICAL SAFETY CHECKS

### Before Any Data Movement:

- [ ] Confirm BigQuery Databento tables are empty (0 rows) ✅ DONE
- [ ] Confirm external drive has ZL + MES 1-hour data ✅ DONE
- [ ] Confirm NO other Databento data on external drive ✅ DONE
- [ ] Confirm staging parquet files will NOT be used for price data ✅ DONE

### Before Loading External Drive Data to BigQuery:

- [ ] Create `databento_futures_ohlcv_1h` table if doesn't exist
- [ ] Verify table is empty before loading
- [ ] Test loader script on 1 file first
- [ ] Check for date range overlaps

### Before New Databento Downloads:

- [ ] Review download spec with Kirk
- [ ] Ensure uniform date ranges
- [ ] Ensure no duplicate requests
- [ ] Verify external drive has space (~10 GB needed)

### Before Loading New Downloads to BigQuery:

- [ ] Verify no date range overlaps with existing data
- [ ] Test loader on 1 file first
- [ ] Check for duplicates in BQ after test load
- [ ] Document row counts before/after

---

## 📋 IMMEDIATE NEXT STEP (AWAITING APPROVAL)

**Recommended:** Phase 1 (Load Existing External Drive Data to BigQuery)

**Why Start Here:**
1. ✅ SAFE: No new downloads, no risk of duplicates
2. ✅ VERIFIABLE: Can check row counts immediately
3. ✅ FOUNDATION: Establishes BQ as source of truth
4. ✅ TESTABLE: Can validate before proceeding

**What I'll Do:**
1. Create `scripts/ingestion/load_databento_raw_to_bq.py`
2. Load ZL 1-hour JSON files → BigQuery
3. Load MES 1-hour JSON files → BigQuery
4. Verify and document row counts
5. Check for any duplicates (should be 0)

**What I WON'T Do:**
- ❌ Use staging parquet files
- ❌ Download new data yet
- ❌ Load to `daily_ml_matrix` yet
- ❌ Make any assumptions about date ranges

---

## ✅ KIRK'S APPROVAL REQUIRED

**Kirk, please confirm:**

1. **Approve Phase 1?** Load existing ZL + MES 1-hour from external drive → BigQuery?
2. **Databento Portal Review?** Should I draft download spec for missing data first?
3. **Date Range Uniformity?** What date range should ALL symbols use? (e.g., 2010-06-06 to 2025-11-21?)

**I will NOT proceed until you explicitly approve.**

---

**Status:** 🛑 AWAITING APPROVAL

