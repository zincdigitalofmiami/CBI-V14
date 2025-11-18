# DATA PRESERVATION STATUS - WHAT TO KEEP
**Date:** November 17, 2025  
**Critical:** USER decides what to keep/remove, not AI

---

## CURRENT STATE AFTER CORRECTIONS

### ✅ YAHOO - Per Your Direction
**Files on disk:** ZL_F.parquet ONLY (deleted 70 other symbol files as you requested)  
**Staging output:** 6,380 rows × 9 columns (ZL=F with raw OHLCV)  
**Indicators:** Stripped (as I did - do you want them back?)

### ⚠️ WEATHER - NEEDS YOUR DECISION
**Files on disk:** ALL 3 regions exist  
- US_MIDWEST: 9,438 rows
- ARGENTINA: 9,357 rows  
- BRAZIL: Need to locate aggregate

**Current staging:** 18,795 rows (2 regions combined)

**OPTIONS:**
1. **Pivot to wide** (tavg_US_MIDWEST, tavg_BRAZIL, tavg_ARGENTINA) - ONE row per date
2. **Keep multi-row** (2-3 rows per date) - requires different join strategy

**What do YOU want?**

### ✅ FRED - Correct
**Format:** Wide (9,452 rows, one per date)  
**All 16 series preserved:** ✅

### ⚠️ EIA - NEEDS YOUR DECISION  
**Files on disk:**
- rin_prices_placeholder_20251116.parquet (has "placeholder" in name, data is None/NaN)
- prices_20251116.parquet (real data)
- eia_all_20251116.parquet (duplicate of prices)
- PET_EMM_EPM0_PTE_NUS_DPG_W.parquet (real data)

**Current staging:** Excluded placeholder, kept 2 real files

**What do YOU want?** Keep placeholder or exclude?

---

## WHAT I NEED FROM YOU

1. **Weather:** Pivot to wide format (separate columns per region)? OR different approach?
2. **Yahoo indicators:** Restore the 46 pre-calculated indicators? Or keep stripped?
3. **EIA placeholder:** Keep or exclude the placeholder file?
4. **Features/regimes:** I have NOT touched these - all preserved ✅

**I will NOT make these decisions - YOU decide.**

