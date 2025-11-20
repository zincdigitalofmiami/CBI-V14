---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# INDIVIDUAL DATA SOURCE REQUIREMENTS - EACH IS UNIQUE
**Date:** November 17, 2025  
**Analysis:** Per-source investigation based on actual usage in codebase  
**Mandate:** "Each area needs its own setup, nothing is uniform, all is unique"

---

## Source #1: YAHOO (Multi-Symbol OHLCV)

### What It Actually Is
- **70 individual parquet files** (one per symbol: ZL=F, ZS=F, etc.)
- **Already has pre-calculated indicators** (46 columns: SMA, EMA, RSI, MACD, etc.)
- **Format:** One file per symbol, with Date + Symbol + OHLCV + indicators

### Current Staging Output
```
Shape: 416,110 rows × 56 columns
Structure: Multi-symbol LONG format (panel data)
Columns: ['Symbol', 'Open', 'High', 'Low', 'Close', 'Volume', 'date', 
          'SMA_5', 'EMA_5', ...46 pre-calculated indicators...]
Symbol column: "Symbol" (capitalized)
Symbols: 71 unique
Dates: 6,750 unique
```

### What join_spec.yaml Expects
- `expect_symbols_count_gte: 55` ✅ (we have 71)
- `expect_zl_rows_gte: 6000` ✅
- Alpha join expects: `on: ["date", "symbol"]` (lowercase "symbol") ❌

### What feature_calculations.py Uses
- Looks for: `['vix', 'vix_close', 'vix_level']` - VIX from FRED, not Yahoo
- Doesn't reference Yahoo indicators directly
- Uses OHLCV for custom calculations

### UNIQUE REQUIREMENTS FOR YAHOO:

1. **Keep multi-symbol LONG format** ✅ (correct for panel data)
2. **Rename "Symbol" → "symbol"** (lowercase for Alpha join)
3. **Decision needed:** Keep or strip Yahoo's 46 pre-calculated indicators?
   - **Option A:** Keep them (rename to avoid conflict: `yahoo_RSI_14`)
   - **Option B:** Strip them (Alpha will provide clean set of 50+)
   - **Plan says:** "Alpha Vantage for ALL technical indicators"
   - **Recommendation:** **Strip Yahoo indicators**, keep only OHLCV + dividends + splits

### Required Columns (Final)
```
Columns: ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume', 'dividends', 'stock_splits']
Total: 9 columns (down from 56)
```

---

## Source #2: FRED (Economic Indicators)

### What It Actually Is
- **36 individual parquet files** (one per series: VIXCLS.parquet, DFF.parquet, etc.)
- **Pre-made wide format file** at `raw/fred/combined/fred_wide_format_20251116.parquet`
- **Collection script** creates both long AND wide formats

### Current Staging Output
```
Shape: 103,029 rows × 6 columns (WRONG - using long format)
Structure: LONG format (stacked series)
Columns: ['realtime_start', 'realtime_end', 'date', 'value', 'series_id', 'series_name']
```

### Available Pre-Made Wide Format
```
File: raw/fred/combined/fred_wide_format_20251116.parquet
Shape: 9,452 rows × 16 columns (one row per date) ✅
Index: 'date' (needs to be reset to column)
Columns: ['DCOILWTICO', 'DEXUSEU', 'DFEDTARL', 'DFEDTARU', 'DFF', 'DGS1', 
          'DGS10', 'DGS2', 'DGS30', 'DGS3MO', 'DGS5', 'DTWEXBGS', 
          'DTWEXEMEGS', 'T10Y2Y', 'T10Y3M', 'VIXCLS']
```

### What join_spec.yaml Expects
```
expect_columns_added: ["fed_funds_rate", "vix", "treasury_10y", "usd_broad_index"]
expect_null_rate_below: {"fed_funds_rate": 0.05, "vix": 0.05}
```

### What feature_calculations.py Uses
- `fed_funds_rate` - for macro regime features
- `vix` - for volatility features
- `treasury_10y`, `treasury_2y` - for yield curve
- `usd_broad_index` - for dollar strength

### Column Name Mapping (from collect_with_resilience.py)
```python
FRED_RENAME_MAP = {
    'DFF': 'fed_funds_rate',
    'VIXCLS': 'vix',
    'DGS10': 'treasury_10y',
    'DGS2': 'treasury_2y',
    'DGS30': 'treasury_30y',
    'DGS5': 'treasury_5y',
    'DGS1': 'treasury_1y',
    'DGS3MO': 'treasury_3mo',
    'DTWEXBGS': 'usd_broad_index',
    'DTWEXEMEGS': 'usd_emerging_index',
    'DCOILWTICO': 'crude_oil_wti',
    'DEXUSEU': 'usd_eur_rate',
    'DFEDTARU': 'fed_target_upper',
    'DFEDTARL': 'fed_target_lower',
    'T10Y2Y': 'yield_spread_10y2y',
    'T10Y3M': 'yield_spread_10y3m'
}
```

### UNIQUE REQUIREMENTS FOR FRED:

1. **Use wide format file** (already exists) ✅
2. **Reset index** to make 'date' a column
3. **Rename columns** from series IDs to friendly names
4. **Keep all 16 series** (join_spec only tests 4, but feature_calculations uses more)

### Required Format (Final)
```
Shape: 9,452 rows × 17 columns
Columns: ['date', 'fed_funds_rate', 'vix', 'treasury_10y', 'treasury_2y', 
          'treasury_30y', 'treasury_5y', 'treasury_1y', 'treasury_3mo',
          'usd_broad_index', 'usd_emerging_index', 'crude_oil_wti', 
          'usd_eur_rate', 'fed_target_upper', 'fed_target_lower',
          'yield_spread_10y2y', 'yield_spread_10y3m']
```

---

## Source #3: WEATHER (NOAA Multi-Region)

### What It Actually Is
- **4 weather stations across 3 regions:**
  - Argentina: Santa Fe (1 station)
  - Brazil: Mato Grosso + Paraná (2 stations)
  - US Midwest: Iowa (1 station)

### Current Staging Output
```
Shape: 37,808 rows × 13 columns
Structure: 4 rows per date (one per station)
Regions: ARGENTINA, BRAZIL (2 stations), US_MIDWEST

US_MIDWEST subset:
  9,452 rows (already one per date!)
  Station: Iowa, US
```

### What join_spec.yaml Expects
```
null_policy fill: {"us_midwest_precip_30d": 0.0, "us_midwest_temp_avg": 10.0}
expect_null_rate_below: {"us_midwest_precip_30d": 0.30}
```

### What feature_calculations.py Uses
```python
# Looks for columns with 'us_precip', 'midwest_precip', 'us_midwest_precip'
# Uses US Midwest weather for soybean growing region correlation
```

### Discovery: 4x Multiplication is from ALL REGIONS
- Join on 'date' alone matches all 4 stations per date
- **But we only need US_MIDWEST for ZL (soybean oil)**
- Brazil/Argentina data is for Brazilian/Argentine soybean regions (NOT currently used)

### UNIQUE REQUIREMENTS FOR WEATHER:

**Option A: Filter to US_MIDWEST Only (Simplest)**
```python
# Keep only US Midwest station
us_midwest = weather[weather['region'] == 'US_MIDWEST']
# Result: 9,452 rows (one per date) ✅
```

**Option B: Keep All Regions with Region Pivot**
```python
# Pivot so each region gets its own columns
pivot = weather.pivot_table(
    index='date',
    columns='region',
    values=['tavg_c', 'tmax_c', 'tmin_c', 'prcp_mm', 'humidity_pct'],
    aggfunc='mean'
)
# Result: columns like 'tavg_c_US_MIDWEST', 'tavg_c_BRAZIL', etc.
```

**Recommendation based on join_spec:** **Option A - US_MIDWEST only**
- join_spec expects `us_midwest_precip_30d` (not `brazil_precip`)
- Current model focuses on US Midwest growing region
- Can add other regions later if needed for expanded model

### Required Columns (Final)
```
Columns: ['date', 'us_midwest_temp_avg', 'us_midwest_temp_max', 'us_midwest_temp_min',
          'us_midwest_precip_30d', 'us_midwest_humidity_avg', 'us_midwest_wind_avg']
Shape: 9,452 rows × 7 columns
```

---

## Source #4: EIA (Biofuels)

### What It Actually Is
- **3 actual files + 1 placeholder:**
  1. `rin_prices_placeholder_20251116.parquet` (5,799 rows, placeholder data ❌)
  2. `prices_20251116.parquet` (1,702 rows, gasoline prices)
  3. `eia_all_20251116.parquet` (1,702 rows, duplicate of prices)
  4. `PET_EMM_EPM0_PTE_NUS_DPG_W.parquet` (1,702 rows, gasoline retail)

### Current Staging Output
```
Shape: 8,283 rows (combined all 4 files)
Issue: Includes PLACEHOLDER data with NaN/None values
Issue: Multiple series create 1.4 rows/date
```

### What join_spec.yaml Expects
```
No specific column tests
Just: expect_rows_preserved
```

### What feature_calculations.py Uses
- Not explicitly referenced in feature_calculations.py
- Likely used for biodiesel price proxies (D4, D5, D6 RIN prices)

### UNIQUE REQUIREMENTS FOR EIA:

1. **Exclude placeholder file** (has None/NaN data)
2. **Deduplicate** (prices and eia_all appear to be same data)
3. **Keep D4, D5, D6 prices** (biodiesel RIN credits)
4. **One row per date** after dedup

### Required Format (Final)
```
Use: rin_prices_placeholder file ONLY IF it has real data
OR: Use prices_20251116.parquet (1,702 rows)

Columns: ['date', 'biodiesel_d4_price', 'biodiesel_d5_price', 'biodiesel_d6_price']
Shape: ~1,700-5,800 rows (one per date)
```

**Note:** Name says "placeholder" - needs inspection to determine if data is real or fake

---

## Source #5: CFTC (Commitment of Traders)

### Current State
```
❌ NO FILES FOUND in raw/cftc
⚠️  Staging script skipped: "No CFTC files found"
```

### What join_spec.yaml Expects
```
expect_rows_preserved
expect_cftc_available_after: "2006-01-01"
null_policy: allow: true (OK if missing)
```

### UNIQUE REQUIREMENTS FOR CFTC:

**Status:** Optional - join allows nulls
**Action:** None required now (will add when CFTC data collected)
**Join behavior:** Left join preserves all Yahoo rows, CFTC columns will be NaN

---

## Source #6: USDA (Agricultural Reports)

### Current State
```
❌ NO FILES FOUND in raw/usda
⚠️  Staging script skipped: "No USDA files found"
```

### What join_spec.yaml Expects
```
expect_rows_preserved
null_policy: allow: true, fill_method: "ffill"
```

### UNIQUE REQUIREMENTS FOR USDA:

**Status:** Optional - join allows nulls with ffill
**Action:** None required now (will add when USDA data collected)
**Join behavior:** Left join preserves all Yahoo rows, USDA columns will be NaN then ffilled

---

## Source #7: REGIME CALENDAR

### What It Is
- Pre-defined regime assignments by date
- Expected location: `registry/regime_calendar.parquet`

### What join_spec.yaml Expects
```
expect_regime_cardinality_gte: 7
expect_columns_present: ["market_regime", "training_weight"]
null_policy:
  fill: {"market_regime": "allhistory", "training_weight": 1}
  fill_method: "ffill"
```

### Status
- **Needs verification:** Does `registry/regime_calendar.parquet` exist?
- **Critical for Phase 1:** This join assigns regimes and weights

---

## Source #8: ALPHA VANTAGE (Future)

### What join_spec.yaml Expects
```
on: ["date", "symbol"]  # Multi-key join!
expect_indicators_count_gte: 50
expect_columns_added: ["RSI_14", "MACD_line", "ATR_14", "BBANDS_upper_20"]
```

### UNIQUE REQUIREMENTS:
- **Must have "symbol" column** (lowercase) to join with Yahoo
- **Wide format:** 50+ indicator columns
- **Validated:** AlphaDataValidator checks before save

---

## COMPREHENSIVE FIX SPECIFICATION

### Fix #1: FRED Staging (UNIQUE TO FRED)
```python
def create_fred_staging():
    # Use pre-made wide format file
    wide_file = DRIVE / "raw/fred/combined/fred_wide_format_20251116.parquet"
    df = pd.read_parquet(wide_file)
    
    # Reset index (date is in index)
    df = df.reset_index()
    
    # Rename series IDs to friendly names (FRED-SPECIFIC mapping)
    df = df.rename(columns={
        'DFF': 'fed_funds_rate',
        'VIXCLS': 'vix',
        'DGS10': 'treasury_10y',
        'DGS2': 'treasury_2y',
        'DGS30': 'treasury_30y',
        'DGS5': 'treasury_5y',
        'DGS1': 'treasury_1y',
        'DGS3MO': 'treasury_3mo',
        'DTWEXBGS': 'usd_broad_index',
        'DTWEXEMEGS': 'usd_emerging_index',
        'DCOILWTICO': 'crude_oil_wti',
        'DEXUSEU': 'usd_eur_rate',
        'DFEDTARU': 'fed_target_upper',
        'DFEDTARL': 'fed_target_lower',
        'T10Y2Y': 'yield_spread_10y2y',
        'T10Y3M': 'yield_spread_10y3m'
    })
    
    # Ensure date is date type
    df['date'] = pd.to_datetime(df['date']).dt.date
    
    # Filter to 2000-2025
    df_temp = df.copy()
    df_temp['date'] = pd.to_datetime(df_temp['date'])
    df_temp = df_temp[(df_temp['date'] >= '2000-01-01') & (df_temp['date'] <= '2025-12-31')]
    df_temp['date'] = df_temp['date'].dt.date
    df = df_temp
    
    staging_file = DRIVE / "staging/fred_macro_2000_2025.parquet"
    df.to_parquet(staging_file, index=False)
    print(f"✅ Created: {staging_file} ({len(df)} rows × {len(df.columns)} cols)")
    
    return df
```

**Why This Is Right for FRED:**
- Wide format with series codes is how FRED API returns data
- Friendly column names match what feature_calculations.py expects
- One row per date is natural for economic indicators (published once per date)

---

### Fix #2: Weather Staging (UNIQUE TO WEATHER)
```python
def create_weather_staging():
    # ... existing loading code ...
    
    combined = pd.concat(all_weather, ignore_index=True)
    
    # Filter to 2000-2025
    combined['date'] = pd.to_datetime(combined['date'])
    combined = combined[(combined['date'] >= '2000-01-01') & (combined['date'] <= '2025-12-31')]
    
    # CRITICAL: Filter to US_MIDWEST region ONLY
    # Rationale: ZL (soybean oil) model focuses on US Midwest growing region
    # Other regions (Brazil, Argentina) are for future expansion
    us_midwest = combined[combined['region'] == 'US_MIDWEST'].copy()
    
    # Select and rename columns to match join_spec expectations
    us_midwest = us_midwest.rename(columns={
        'tavg_c': 'us_midwest_temp_avg',
        'tmax_c': 'us_midwest_temp_max',
        'tmin_c': 'us_midwest_temp_min',
        'prcp_mm': 'us_midwest_precip_30d',  # Note: May need 30-day rolling sum
        'humidity_pct': 'us_midwest_humidity_avg',
        'wind_speed_ms': 'us_midwest_wind_avg'
    })
    
    # Keep only needed columns
    keep_cols = ['date', 'us_midwest_temp_avg', 'us_midwest_temp_max', 
                 'us_midwest_temp_min', 'us_midwest_precip_30d',
                 'us_midwest_humidity_avg', 'us_midwest_wind_avg']
    us_midwest = us_midwest[[c for c in keep_cols if c in us_midwest.columns]]
    
    # Ensure date is date type
    us_midwest['date'] = us_midwest['date'].dt.date
    
    # Result: 9,452 rows (one per date) ✅
    
    staging_file = DRIVE / "staging/noaa_weather_2000_2025.parquet"
    us_midwest.to_parquet(staging_file, index=False)
    print(f"✅ Created: {staging_file} ({len(us_midwest)} rows)")
    
    return us_midwest
```

**Why This Is Right for Weather:**
- US Midwest is the relevant region for ZL (soybean oil) modeling
- Iowa station represents the key growing region
- One row per date matches time series join requirements
- Other regions (Brazil, Argentina) can be added later for international soybean modeling

---

### Fix #3: EIA Staging (UNIQUE TO EIA)
```python
def create_eia_staging():
    # ... existing loading code ...
    
    eia_dir = DRIVE / "raw/eia"
    
    # CRITICAL: Load only non-placeholder files
    # Exclude rin_prices_placeholder if it has None/NaN data
    real_files = []
    for parquet_file in eia_dir.rglob("*.parquet"):
        # Skip placeholder files
        if 'placeholder' in parquet_file.name.lower():
            print(f"  ⚠️  Skipping placeholder: {parquet_file.name}")
            continue
        
        df = pd.read_parquet(parquet_file)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.date
        real_files.append(df)
    
    if not real_files:
        print("⚠️  No non-placeholder EIA files found")
        return None
    
    # Combine real files
    combined = pd.concat(real_files, ignore_index=True)
    
    # Filter to 2010-2025
    combined['date'] = pd.to_datetime(combined['date'])
    combined = combined[(combined['date'] >= '2010-01-01') & (combined['date'] <= '2025-12-31')]
    
    # CRITICAL: Deduplicate - keep one row per date
    # If multiple series per date, pivot to wide
    if 'series_id' in combined.columns and combined['date'].dt.date.duplicated().any():
        # Pivot to wide format
        pivoted = combined.pivot_table(
            index=combined['date'].dt.date,
            columns='series_id',
            values='value',
            aggfunc='first'
        ).reset_index()
        pivoted.columns.name = None
    else:
        # If already one row per date, just keep D4/D5/D6 prices
        pivoted = combined.groupby(combined['date'].dt.date).agg({
            col: 'first' for col in combined.columns if col != 'date'
        }).reset_index()
    
    # Ensure date is date type
    pivoted['date'] = pd.to_datetime(pivoted['date']).dt.date
    
    staging_file = DRIVE / "staging/eia_biofuels_2010_2025.parquet"
    pivoted.to_parquet(staging_file, index=False)
    print(f"✅ Created: {staging_file} ({len(pivoted)} rows)")
    
    return pivoted
```

**Why This Is Right for EIA:**
- EIA publishes biofuel data weekly/monthly (irregular frequency)
- Multiple series (D4, D5, D6 RIN prices, gasoline prices)
- Placeholder data should be excluded
- One row per date prevents join explosions

---

### Fix #4: Yahoo Staging (UNIQUE TO YAHOO)
```python
def create_yahoo_staging():
    # ... existing loading code ...
    
    # Combine all symbols
    combined = pd.concat(all_symbols, ignore_index=True)
    
    # CRITICAL: Strip pre-calculated indicators (Yahoo has 46, Alpha will provide 50+)
    # Rationale: Plan states "Alpha Vantage for ALL technical indicators"
    raw_columns = ['Symbol', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume', 
                   'Dividends', 'Stock Splits', 'Capital Gains']
    
    # Keep only raw columns that exist
    keep_cols = [c for c in raw_columns if c in combined.columns]
    combined = combined[keep_cols]
    
    # Standardize column names to lowercase (for Alpha join compatibility)
    combined.columns = combined.columns.str.lower().str.replace(' ', '_')
    
    # Standardize date column
    if 'Date' in combined.columns or 'date' in combined.columns:
        date_col = 'Date' if 'Date' in combined.columns else 'date'
        combined['date'] = pd.to_datetime(combined[date_col]).dt.date
        if date_col != 'date':
            combined = combined.drop(columns=[date_col])
    
    print(f"  ✅ Stripped {56 - len(keep_cols)} pre-calculated indicator columns")
    print(f"  ✅ Kept only raw OHLCV data ({len(keep_cols)} columns)")
    print(f"  ✅ Standardized to lowercase column names")
    
    # Save
    staging_file = DRIVE / "staging/yahoo_historical_all_symbols.parquet"
    combined.to_parquet(staging_file, index=False)
    print(f"✅ Created: {staging_file} ({len(combined)} rows × {len(combined.columns)} cols)")
    
    return combined
```

**Why This Is Right for Yahoo:**
- Keeps multi-symbol panel data structure (correct for ML)
- Strips duplicate indicators (Alpha will provide clean, consistent set)
- Lowercase "symbol" enables Alpha multi-key join
- Raw OHLCV is source of truth (calculate features from this)

---

## Summary: Each Source's Unique Fix

| Source | Current Issue | Unique Fix | Rows |
|--------|---------------|------------|------|
| **FRED** | Long format + series codes | Use wide file + rename to friendly names | 103K → 9.5K ✅ |
| **Weather** | 4 regions × 9.5K dates | Filter to US_MIDWEST only | 37.8K → 9.5K ✅ |
| **EIA** | Placeholder + duplicates | Exclude placeholder, dedup | 8.3K → 1.7K ✅ |
| **Yahoo** | Capitalized + indicators | Lowercase + strip indicators | 416K (same) ✅ |
| **CFTC** | Missing | None (optional join) | N/A ✅ |
| **USDA** | Missing | None (optional join) | N/A ✅ |

**After fixes:**
```
Yahoo:     416,110 rows
+ FRED:    416,110 rows (wide format, one per date)
+ Weather: 416,110 rows (US_MIDWEST only, one per date)  
+ EIA:     416,110 rows (deduped, one per date)
+ Regimes: 416,110 rows (calendar join, one per date)
+ Alpha:   416,110 rows (multi-key join on date+symbol)

Final: 416,110 rows × ~120 columns ✅ NO EXPLOSIONS
```

**Each source requires its own unique transformation based on:**
1. Source data structure (wide vs long, single vs multi-entity)
2. Feature calculation requirements (what columns are actually used)
3. Join_spec expectations (what tests require)
4. Domain-specific logic (US Midwest weather, series code mapping, etc.)

**NOT uniform - each source handled according to its specific characteristics.**





