---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# EMERGENCY COMPLETE DATA AUDIT - NOVEMBER 17, 2025
**Status:** READ ONLY - NO CHANGES MADE  
**Purpose:** Audit EVERYTHING that exists, find Brazil, identify what's actually needed

---

## CRITICAL FINDINGS

### YAHOO
**Location:** `raw/yahoo_finance/prices/commodities/`  
**Files:** 1 file (ZL_F.parquet) - other 70 deleted per user request  
**Staging:** 6,380 rows × 9 cols (ZL=F only, indicators stripped)  
**Status:** ✅ Per user direction

### FRED  
**Location:** `raw/fred/combined/`  
**Files:**
- `fred_all_series_20251116.parquet` (103,029 rows - LONG format)
- `fred_wide_format_20251116.parquet` (9,452 rows - WIDE format) ✅

**Staging:** 9,452 rows × 17 cols (using wide format, renamed columns)  
**Status:** ✅ Correct

### WEATHER - REGIONAL AGGREGATES
**Location:** `raw/noaa/regional/`  
**Files:**
- `us_midwest_aggregate.parquet` (9,438 rows, 1 row/date) ✅
- `argentina_aggregate.parquet` (9,357 rows, 1 row/date) ✅  
- `brazil_aggregate.parquet` ❌ **MISSING**

**Individual Stations:** `raw/noaa/processed/`
- 10 US stations ✅
- 2 AR stations ✅
- 0 BR stations ❌

**Current Staging:** 18,795 rows (US + AR combined, 2 rows/date)  
**BRAZIL DATA:** **MISSING** - need to find or regenerate from stations

### WEATHER - OTHER LOCATIONS (DUPLICATES?)
**Location:** `raw/forecasting_data_warehouse/`  
**Files (all EMPTY or ERROR):**
- `weather_brazil_daily.parquet` (0 rows)
- `weather_brazil_clean.parquet` (dbdate error)
- `weather_us_midwest_daily.parquet` (0 rows)
- `weather_argentina_daily.parquet` (0 rows)

**Status:** Empty/corrupted - regional aggregates are the real data

### EIA
**Location:** `raw/eia/`  
**Files:**
- `rin_prices_placeholder_20251116.parquet` (5,799 rows, all None/NaN) ❌
- `prices_20251116.parquet` (1,702 rows, REAL) ✅
- `eia_all_20251116.parquet` (1,702 rows, DUPLICATE) ⚠️
- `PET_EMM_EPM0_PTE_NUS_DPG_W.parquet` (1,702 rows, REAL) ✅

**Staging:** 828 rows (excluded placeholder, deduped)

### CFTC
**Location:** `raw/cftc/`  
**Files:** 0  
**Status:** No data collected yet

### USDA
**Location:** `raw/usda/`  
**Files:** 0  
**Status:** No data collected yet

### REGIME CALENDAR
**Location:** `registry/regime_calendar.parquet`  
**Status:** ✅ EXISTS  
**Shape:** 9,497 rows × 3 cols  
**Columns:** ['date', 'regime', 'training_weight']  
**Regimes:** 14 unique  
**Weight range:** 50-500

---

## CRITICAL ISSUES

### Issue #1: BRAZIL WEATHER MISSING
**What we have:**
- US_MIDWEST aggregate: ✅ 9,438 rows
- ARGENTINA aggregate: ✅ 9,357 rows
- BRAZIL aggregate: ❌ MISSING

**Options:**
1. Find Brazil aggregate file in another location
2. Generate from individual BR station files (but none exist in raw/noaa/processed/)
3. Check if Brazil data is in a different format/location
4. Re-collect Brazil weather data

**Need user direction on where Brazil data is or if it needs collection**

### Issue #2: Weather Join Strategy (2 regions = 2 rows/date)
**Current:** Combined file has 2 rows per date (US + AR)
**Problem:** Join on 'date' alone creates 2x cartesian product

**Options (KEEPING ALL DATA):**
1. **Pivot to wide:** tavg_US_MIDWEST, tavg_ARGENTINA, prcp_US_MIDWEST, prcp_ARGENTINA (1 row/date)
2. **Change join strategy:** More complex

**Need user direction on approach**

### Issue #3: Regime Calendar Column Name
**Actual:** 'regime' column  
**Expected by join_spec:** 'market_regime'  
**Options:**
1. Rename in regime_calendar.parquet file
2. Update join_spec.yaml to expect 'regime'
3. Rename after join in build_all_features.py

**Need user direction**

---

## WHAT EXISTS vs WHAT'S USED

### Currently in Staging (After My Fixes):
- Yahoo: 6,380 rows (ZL=F only) ✅
- FRED: 9,452 rows (wide format, renamed) ✅
- Weather: 18,795 rows (US + AR, 2 rows/date) ⚠️ Will cause cartesian product
- EIA: 828 rows (deduped) ✅

### Join_spec Expects:
- Yahoo: 1 symbol (ZL=F) ✅
- FRED: fed_funds_rate, vix, treasury_10y, usd_broad_index ✅
- Weather: us_midwest_precip_30d ⚠️ (only mentions US, not AR/BR)
- Regimes: market_regime, training_weight ⚠️ (actual has 'regime')

---

## IMMEDIATE QUESTIONS FOR USER

1. **Where is Brazil weather data?** Or does it need to be collected?
2. **Weather regions:** Pivot to wide (separate columns per region)? Or different approach?
3. **Regime column:** Rename 'regime' to 'market_regime'? Where?
4. **EIA placeholder:** Confirmed to exclude?
5. **Join_spec weather tests:** Only mention US_MIDWEST - should tests include AR/BR columns too?

**I WILL NOT PROCEED until you answer these questions.**





