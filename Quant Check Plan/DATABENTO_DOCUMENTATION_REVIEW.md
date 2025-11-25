# Databento Documentation Review - Critical Fixes Required

**Date:** November 24, 2025  
**Status:** ⚠️ **CRITICAL ISSUES FOUND** - Do NOT proceed until fixed

---

## 📚 Documentation Sources Reviewed

1. `/Volumes/Satechi Hub/Projects/CBI-V14/docs/features/DATABENTO_PLAN_VALIDATION.md`
2. `/Volumes/Satechi Hub/Projects/CBI-V14/docs/features/DATABENTO_CONNECTION_FIX.md`
3. `/Volumes/Satechi Hub/Projects/CBI-V14/docs/features/DATABENTO_LIVE_API_USAGE.md`
4. `/Volumes/Satechi Hub/Projects/CBI-V14/docs/reports/DATABENTO_DATA_STATUS_NOV20.md`
5. `/Volumes/Satechi Hub/Projects/CBI-V14/DATABENTO_DATA_INVENTORY.md`
6. `/Volumes/Satechi Hub/Projects/CBI-V14/config/databento_symbols.yaml`
7. `Quant Check Plan/DATABENTO_SYMBOL_FORMAT_REFERENCE.md`
8. `Quant Check Plan/DATABENTO_INVENTORY_2025-11-21.md`

---

## 🔴 CRITICAL ISSUES IN CURRENT SCRIPT

### Issue #1: WRONG START DATE ❌

**Current Code:**
```python
START_DATE = "2010-01-01"  # Full 15-year history
```

**Documentation Says:**
- From `DATABENTO_PLAN_VALIDATION.md` line 18: **"Historical Coverage: 15 years (June 6, 2010 - present)"**
- From `DATABENTO_LIVE_API_USAGE.md` line 18: **"Historical Coverage: 15 years (June 6, 2010 - present)"**
- From `DATABENTO_DATA_STATUS_NOV20.md` line 24: **"Coverage: 2010-06-06 to 2025-11-18"**

**FIX:**
```python
START_DATE = "2010-06-06"  # Actual available start date for GLBX.MDP3
```

**Why This Matters:**
- Using `2010-01-01` will cause `422 data_start_before_available_start` errors
- The dataset's actual available start date is `2010-06-06`, not `2010-01-01`

---

### Issue #2: INVALID OPTIONS SCHEMA ❌

**Current Code:**
```python
SCHEMAS_OPTIONS = [
    "ohlcv-1d",   # ✅ Valid
    "ohlcv-1h",   # ✅ Valid
    "trades",     # ✅ Valid
    "quotes",     # ❌ INVALID - not available for GLBX.MDP3 options
    "statistics", # ✅ Valid
]
```

**Documentation Says:**
- From `DATABENTO_PLAN_VALIDATION.md` line 47-49:
  - **"Options Schemas (Available with add-on): Options data (definitions, trades, OHLCV where supported) is accessible via GLBX.MDP3 using `stype_in='parent'`. Examples: `definition`, `ohlcv-1d`, `trades`, `mbo` (where supported by venue/schema)"**
- **NO MENTION OF `quotes` SCHEMA** for options

**FIX:**
```python
SCHEMAS_OPTIONS = [
    "ohlcv-1d",   # Daily options bars (for vol surface, GEX)
    "ohlcv-1h",   # Hourly options bars (for intraday GEX)
    "trades",     # Options trades (for put/call ratios, volume)
    "mbo",        # Market-by-order (for bid/ask, implied vol) - if supported
    "tbbo",       # Top-of-book (alternative to mbo if mbo not available)
    "statistics", # Options OI, settlement
]
```

**Why This Matters:**
- `quotes` schema is NOT valid for GLBX.MDP3 options
- Will cause `422 The schema was not a valid value of Schema` errors
- Use `mbo` or `tbbo` for bid/ask data instead

---

### Issue #3: PARAMETER NAMES (ALREADY FIXED ✅)

**Current Code:**
```python
split_duration="day",  # ✅ CORRECT
```

**Status:** This is already correct. The documentation confirms `split_duration` is the correct parameter name.

---

### Issue #4: SYMBOL FORMATS (ALREADY CORRECT ✅)

**Current Code:**
```python
HEAVY_SYMBOLS = ["ZL.FUT", "MES.FUT"]  # ✅ CORRECT
MES_OPTIONS_SYMBOLS = ["ES.OPT", "MES.OPT"]  # ✅ CORRECT
ZL_OPTIONS_SYMBOLS = ["OZL.OPT", "OZS.OPT", "OZM.OPT"]  # ✅ CORRECT
```

**Documentation Confirms:**
- From `DATABENTO_PLAN_VALIDATION.md` line 27-28:
  - **"ES.OPT, MES.OPT"** ✅
  - **"OZL.OPT (Soybean Oil), OZS.OPT (Soybeans), OZM.OPT (Soybean Meal)"** ✅
- From `DATABENTO_SYMBOL_FORMAT_REFERENCE.md` line 39-46:
  - **"ES.OPT - E-mini S&P 500 options ✅"**
  - **"MES.OPT - Micro E-mini S&P 500 options ✅"**
  - **"OZL.OPT - Soybean Oil options ✅ (note O prefix)"**

**Status:** Symbol formats are correct.

---

### Issue #5: STYPE_IN (ALREADY CORRECT ✅)

**Current Code:**
```python
stype_in="parent",  # ✅ CORRECT
```

**Documentation Confirms:**
- From `DATABENTO_PLAN_VALIDATION.md` line 48:
  - **"Options data (definitions, trades, OHLCV where supported) is accessible via GLBX.MDP3 using `stype_in='parent'`"**
- From `DATABENTO_SYMBOL_FORMAT_REFERENCE.md` line 49:
  - **"Uses: `stype_in='parent'` (same as futures, NOT `stype_in='option'`)"**

**Status:** `stype_in="parent"` is correct for both futures and options.

---

## ✅ WHAT'S ALREADY CORRECT

1. **Dataset:** `"GLBX.MDP3"` ✅
2. **Encoding:** `"csv"` ✅
3. **Compression:** `"none"` ✅ (for BigQuery compatibility)
4. **split_duration:** `"day"` ✅
5. **stype_in:** `"parent"` ✅
6. **stype_out:** `"instrument_id"` ✅
7. **map_symbols:** `True` ✅
8. **Symbol formats:** All correct ✅

---

## 🔧 REQUIRED FIXES

### Fix #1: Update START_DATE

**File:** `scripts/ingest/submit_granular_microstructure.py`

**Change:**
```python
# OLD (WRONG):
START_DATE = "2010-01-01"  # Full 15-year history

# NEW (CORRECT):
START_DATE = "2010-06-06"  # Actual available start date for GLBX.MDP3
```

---

### Fix #2: Remove Invalid Options Schema

**File:** `scripts/ingest/submit_granular_microstructure.py`

**Change:**
```python
# OLD (WRONG):
SCHEMAS_OPTIONS = [
    "ohlcv-1d",
    "ohlcv-1h",
    "trades",
    "quotes",     # ❌ INVALID
    "statistics",
]

# NEW (CORRECT):
SCHEMAS_OPTIONS = [
    "ohlcv-1d",   # Daily options bars (for vol surface, GEX)
    "ohlcv-1h",   # Hourly options bars (for intraday GEX)
    "trades",     # Options trades (for put/call ratios, volume)
    "mbo",        # Market-by-order (for bid/ask, implied vol) - if supported
    "tbbo",       # Top-of-book (alternative if mbo not available)
    "statistics", # Options OI, settlement
]
```

**Note:** Test `mbo` first. If it fails, use `tbbo` instead.

---

## 📋 VALIDATION CHECKLIST

Before running the script, verify:

- [ ] `START_DATE = "2010-06-06"` (NOT `2010-01-01`)
- [ ] `SCHEMAS_OPTIONS` does NOT include `"quotes"`
- [ ] `SCHEMAS_OPTIONS` includes `"mbo"` or `"tbbo"` for bid/ask data
- [ ] All symbol formats are correct (`.FUT` for futures, `.OPT` for options)
- [ ] `stype_in="parent"` for both futures and options
- [ ] `encoding="csv"` and `compression="none"` for BigQuery compatibility

---

## 🎯 NEXT STEPS

1. **Fix START_DATE** in `submit_granular_microstructure.py`
2. **Fix SCHEMAS_OPTIONS** in `submit_granular_microstructure.py`
3. **Test with small date range first** (e.g., `2024-01-01` to `2024-01-02`)
4. **Verify job submission succeeds** before submitting full 15-year range
5. **Monitor job status** at https://databento.com/portal/batch/jobs

---

## 📖 KEY DOCUMENTATION REFERENCES

### Historical Coverage
- **Start Date:** `2010-06-06` (NOT `2010-01-01`)
- **End Date:** Present
- **Cost:** $0 (included in CME MDP 3.0 plan)

### Options Access
- **CME Options Add-On:** ENABLED on this account ✅
- **Format:** `ES.OPT`, `MES.OPT` (equity indices), `OZL.OPT`, `OZS.OPT`, `OZM.OPT` (commodities)
- **stype_in:** `"parent"` (same as futures)
- **Valid Schemas:** `ohlcv-1d`, `ohlcv-1h`, `trades`, `mbo` (if supported), `statistics`
- **Invalid Schemas:** `quotes` ❌

### Symbol Formats
- **Futures:** `{ROOT}.FUT` (e.g., `ZL.FUT`, `MES.FUT`)
- **Options (Equity):** `{ROOT}.OPT` (e.g., `ES.OPT`, `MES.OPT`)
- **Options (Commodity):** `O{ROOT}.OPT` (e.g., `OZL.OPT`, `OZS.OPT`, `OZM.OPT`)

### API Parameters
- **split_duration:** `"day"` or `"month"` (NOT `split_method`)
- **encoding:** `"csv"` or `"json"`
- **compression:** `"none"` (for BigQuery compatibility)
- **stype_in:** `"parent"` (for both futures and options)
- **NO `price_type` parameter** ❌
- **NO `date_time_format` parameter** ❌

---

**Status:** ⚠️ **FIXES REQUIRED BEFORE PROCEEDING**

