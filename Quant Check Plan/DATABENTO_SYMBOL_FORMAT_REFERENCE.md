# 📚 Databento Symbol Format Reference
**Date:** November 24, 2025  
**Purpose:** Consolidated reference for Databento symbol formats and symbology conventions

---

## ✅ CONFIRMED FORMATS (From Documentation)

### Futures Symbols
- **Format:** `{ROOT}.FUT`
- **Examples:**
  - `ZL.FUT` - Soybean Oil continuous front-month
  - `ES.FUT` - E-mini S&P 500 continuous front-month
  - `MES.FUT` - Micro E-mini S&P 500 continuous front-month
  - `ZS.FUT` - Soybeans
  - `ZM.FUT` - Soybean Meal
  - `CL.FUT` - Crude Oil
  - `HO.FUT` - Heating Oil

- **Source:** `DATABENTO_INVENTORY_2025-11-21.md` line 131, 154
- **Usage:** `stype_in="parent"` for continuous contracts

### Continuous Contract Symbology
- **Format:** `{ROOT}.{ROLL_RULE}.{RANK}`
- **Examples:**
  - `NG.c.0` - Front-month natural gas (calendar roll)
  - `ZL.c.0` - Front-month soybean oil (calendar roll)
- **Roll Rules:**
  - `c` = calendar (roll on calendar date)
  - `n` = open interest (roll based on OI)
  - `v` = volume (roll based on volume)
- **Rank:** Zero-indexed integer (0 = front month, 1 = second month, etc.)

---

## ✅ CONFIRMED: Options Symbols

### Format (CONFIRMED from DATABENTO_PLAN_VALIDATION.md)
- **Format:** `{ROOT}.OPT` (for equity indices) or `O{ROOT}.OPT` (for commodities)
- **Examples (confirmed):**
  - `ES.OPT` - E-mini S&P 500 options ✅
  - `MES.OPT` - Micro E-mini S&P 500 options ✅
  - `NQ.OPT` - E-mini Nasdaq options (likely)
  - `OZL.OPT` - Soybean Oil options ✅ (note `O` prefix)
  - `OZS.OPT` - Soybeans options ✅
  - `OZM.OPT` - Soybean Meal options ✅

### Key Details
- **Uses:** `stype_in='parent'` (same as futures, NOT `stype_in='option'`)
- **CME Options Add-On:** ENABLED on this account
- **Reference:** `/Volumes/Satechi Hub/Projects/CBI-V14/docs/features/DATABENTO_PLAN_VALIDATION.md`

### Databento Documentation References
- **Symbology Docs:** https://databento.com/docs/standards-and-conventions/symbology
- **Common Fields:** https://databento.com/docs/standards-and-conventions/common-fields-enums-types

---

## 📋 DATASET INFORMATION

### GLBX.MDP3 (CME Globex MDP 3.0)
- **Includes:** Futures + Options on Futures
- **History:** 15 years available
- **Options Available:** Confirmed (ES, MES, NQ, etc.)
- **Symbol Count:** 650,000+ symbols available

### Confirmed Capabilities
- ✅ Futures OHLCV (all timeframes)
- ✅ Futures microstructure (BBO, MBP, MBO, TBBO)
- ✅ Options on futures (format TBD)
- ✅ Statistics feed (OI, settlement, volume)

---

## 🔧 CURRENT SCRIPT STATUS

### `submit_granular_microstructure.py`
- **Futures:** ✅ Using `ZL.FUT`, `MES.FUT`, etc. (confirmed format)
- **Options:** ⚠️ Using `ES.OPT`, `MES.OPT` (needs verification)
- **Note:** Script includes verification warnings and alternative format comments

### `validate_databento_options.py`
- **Purpose:** Test options symbol formats
- **Status:** Ready to run once API key is set
- **Tests:** Multiple symbol format variations

---

## 🎯 VERIFICATION PLAN

### Step 1: Check Databento Metadata API
```python
import databento as db
client = db.Historical(api_key=API_KEY)

# List available symbols for options
# Check metadata for ES/MES options
```

### Step 2: Test Small Date Range
```python
# Test each format with small date range
test_symbols = ["ES.OPT", "ES.OP", "ES"]
for symbol in test_symbols:
    try:
        data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols=[symbol],
            schema="ohlcv-1d",
            start="2024-01-01",
            end="2024-01-02",
            stype_in="parent"  # or "option"?
        )
        print(f"✅ {symbol} works!")
    except Exception as e:
        print(f"❌ {symbol} failed: {e}")
```

### Step 3: Check Databento Portal
- Go to https://databento.com/portal
- Check symbol search/explorer
- Look for options examples in UI

---

## 📝 REFERENCES

### Internal Documentation
- `DATABENTO_INVENTORY_2025-11-21.md` - Main inventory document
- `PHASE2_DATA_PULL_PLAN.md` - Data pull strategy
- `submit_granular_microstructure.py` - Main submission script

### External Documentation
- Databento Symbology: https://databento.com/docs/standards-and-conventions/symbology
- Databento Common Fields: https://databento.com/docs/standards-and-conventions/common-fields-enums-types
- Databento Python Client: https://github.com/databento/databento-python

---

## ✅ NEXT ACTIONS

1. **Locate Databento Options Documentation** (user mentioned many MDs exist)
2. **Run Validation Script** (`validate_databento_options.py`)
3. **Test Symbol Formats** with small date range
4. **Update Scripts** once format is confirmed
5. **Document Confirmed Format** in this reference

---

**Status:** ⚠️ Options format needs verification from Databento docs or testing

