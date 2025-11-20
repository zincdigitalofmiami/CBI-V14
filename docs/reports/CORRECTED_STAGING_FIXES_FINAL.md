---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# CORRECTED STAGING FIXES - YAHOO ZL=F ONLY
**Date:** November 17, 2025  
**Critical Understanding:** Yahoo = ZL=F ONLY, Alpha = All Other Symbols + All Indicators

---

## CORRECTED DATA SOURCE RESPONSIBILITIES

### YAHOO FINANCE
**Role:** ZL=F price data ONLY (Alpha doesn't have ZL futures)  
**Provides:** Raw OHLCV for ZL=F (6,380 rows)  
**Does NOT provide:** Other commodities, FX, indices, indicators

### ALPHA VANTAGE  
**Role:** Everything except ZL prices  
**Provides:**
- All commodities (except ZL): CORN, WHEAT, ZS, ZM, ZC, ZW, CL, NG, etc.
- All FX pairs: USD/BRL, USD/CNY, EUR/USD, etc.
- All indices: SPY, VIX, DJI, etc.
- **ALL 50+ technical indicators for ALL symbols (including ZL!)**
- Options chains
- News & sentiment
- ES futures (all 11 timeframes)

---

## CORRECTED EXPECTED FLOW

### Phase 1 (ZL Only - Before Alpha Integration):

```
Step 1: Yahoo (ZL=F ONLY)
   6,380 rows × 8 cols (symbol, date, open, high, low, close, volume, dividends)

Step 2: + FRED (wide, 9,452 dates)
   6,380 → 6,380 rows ✅ (adds 16 macro columns)

Step 3: + Weather (US_MIDWEST, 9,452 dates)
   6,380 → 6,380 rows ✅ (adds 6 weather columns)

Step 4: + CFTC (optional)
   6,380 → 6,380 rows ✅ (NaN columns)

Step 5: + USDA (optional)
   6,380 → 6,380 rows ✅ (NaN columns)

Step 6: + EIA (deduped, ~1,700 dates)
   6,380 → 6,380 rows ✅ (adds ~3 biofuel columns)

Step 7: + Regimes (9,497 dates)
   6,380 → 6,380 rows ✅ (adds market_regime, training_weight)

Result: 6,380 rows × ~35 columns (ZL with macro/weather/regime context)
```

### Phase 2 (Add Alpha - Multi-Symbol Expansion):

```
Step 8: + Alpha (multi-symbol: ZL + 69 others with 50+ indicators each)
   File: staging/alpha/daily/alpha_complete_ready_for_join.parquet
   Structure: 70 symbols × ~6,000 dates × 55 cols (OHLCV + 50 indicators)
   
   Join on: ["date", "symbol"]
   
   ZL=F rows (6,380) get matched with Alpha's ZL indicators
   + Alpha adds 69 NEW symbols (CORN, WHEAT, etc.) with their data
   
   6,380 → ~420,000 rows ✅ (70 symbols total)
```

---

## CORRECTED FIX #1: YAHOO (ZL=F ONLY)

```python
def create_yahoo_staging():
    """
    CRITICAL: Yahoo = ZL=F ONLY
    Alpha provides all other 69 symbols
    """
    
    print("Creating Yahoo staging file (ZL=F ONLY)...")
    
    # Look for ZL_F.parquet in commodities folder
    yahoo_dir = DRIVE / "raw/yahoo_finance/prices"
    zl_file = yahoo_dir / "commodities/ZL_F.parquet"
    
    if not zl_file.exists():
        print(f"❌ ZL_F.parquet not found at {zl_file}")
        return None
    
    # Load ZL=F data ONLY
    df = pd.read_parquet(zl_file)
    
    print(f"  ✅ Loaded ZL=F: {len(df)} rows")
    
    # Strip pre-calculated indicators (Alpha will provide 50+ for ZL)
    raw_columns = ['Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 
                   'Volume', 'Dividends', 'Stock Splits']
    keep_cols = [c for c in raw_columns if c in df.columns]
    df = df[keep_cols]
    
    print(f"  ✅ Stripped {54 - len(keep_cols)} indicator columns")
    
    # Standardize date column
    if 'Date' in df.columns:
        df['date'] = pd.to_datetime(df['Date']).dt.date
        df = df.drop(columns=['Date'])
    elif 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date']).dt.date
    
    # Lowercase ALL columns (for Alpha join compatibility)
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    
    print(f"  ✅ Lowercase columns: {list(df.columns)}")
    print(f"  ✅ Final shape: {df.shape}")
    
    # Verify single symbol
    if 'symbol' in df.columns:
        unique_symbols = df['symbol'].unique()
        print(f"  ✅ Symbols: {unique_symbols} (should be ZL=F only)")
        if len(unique_symbols) > 1:
            print(f"  ❌ WARNING: Found {len(unique_symbols)} symbols, expected 1!")
    
    # Save
    staging_file = DRIVE / "staging/yahoo_historical_all_symbols.parquet"
    df.to_parquet(staging_file, index=False)
    print(f"✅ Created: {staging_file} (ZL=F ONLY: {len(df)} rows)")
    
    return df
```

---

## CORRECTED join_spec.yaml TESTS

```yaml
  - name: "base_prices"
    source: "staging/yahoo_historical_all_symbols.parquet"
    tests:
      - expect_date_range: ["2000-01-01", "2025-01-01"]
      - expect_symbols_count_gte: 1  # Changed from 55 - only ZL=F now
      - expect_zl_rows_gte: 6000     # Same - ZL should have 6K+ rows

# FINAL TESTS
final_tests:
  - expect_total_rows_gte: 6000  # ZL only (not 416K!)
  - expect_total_cols_gte: 35    # After all joins, before Alpha
```

---

## COMPLETE CORRECTED create_staging_files.py

```python
#!/usr/bin/env python3
"""
Create staging files from raw data for join pipeline.
CRITICAL: Yahoo = ZL=F ONLY, Alpha = Everything Else
"""

import pandas as pd
from pathlib import Path

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData")

def create_yahoo_staging():
    """Yahoo = ZL=F ONLY (Alpha doesn't have ZL futures)"""
    
    print("Creating Yahoo staging file (ZL=F ONLY)...")
    
    zl_file = DRIVE / "raw/yahoo_finance/prices/commodities/ZL_F.parquet"
    
    if not zl_file.exists():
        print(f"❌ ZL_F.parquet not found")
        return None
    
    df = pd.read_parquet(zl_file)
    
    # Keep raw OHLCV only (Alpha provides indicators)
    raw_cols = ['Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits']
    df = df[[c for c in raw_cols if c in df.columns]]
    
    # Standardize
    if 'Date' in df.columns:
        df['date'] = pd.to_datetime(df['Date']).dt.date
        df = df.drop(columns=['Date'])
    
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    
    staging_file = DRIVE / "staging/yahoo_historical_all_symbols.parquet"
    df.to_parquet(staging_file, index=False)
    print(f"✅ Created: {staging_file} (ZL=F: {len(df)} rows)")
    
    return df

def create_fred_staging():
    """FRED = Wide format with friendly column names"""
    
    print("Creating FRED staging file...")
    
    wide_file = DRIVE / "raw/fred/combined/fred_wide_format_20251116.parquet"
    
    if not wide_file.exists():
        print(f"⚠️  Wide format not found")
        return None
    
    df = pd.read_parquet(wide_file).reset_index()
    
    # Rename series codes to friendly names
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
    
    df['date'] = pd.to_datetime(df['date']).dt.date
    
    # Filter to 2000-2025
    df_temp = df.copy()
    df_temp['date'] = pd.to_datetime(df_temp['date'])
    df = df_temp[(df_temp['date'] >= '2000-01-01') & (df_temp['date'] <= '2025-12-31')]
    df['date'] = df['date'].dt.date
    
    staging_file = DRIVE / "staging/fred_macro_2000_2025.parquet"
    df.to_parquet(staging_file, index=False)
    print(f"✅ Created: {staging_file} ({len(df)} rows)")
    
    return df

def create_weather_staging():
    """Weather = US_MIDWEST region only"""
    
    print("Creating Weather staging file (US_MIDWEST ONLY)...")
    
    # Check if already exists and is correct
    staging_file = DRIVE / "staging/noaa_weather_2000_2025.parquet"
    
    # Load all weather data
    noaa_dir = DRIVE / "raw/noaa"
    if not noaa_dir.exists():
        # Try staging dir
        alt_file = DRIVE / "staging/weather_2000_2025.parquet"
        if alt_file.exists():
            df = pd.read_parquet(alt_file)
            
            # Filter to US_MIDWEST
            df['date'] = pd.to_datetime(df['date'])
            us_midwest = df[df['region'] == 'US_MIDWEST'].copy()
            
            # Rename columns
            us_midwest = us_midwest.rename(columns={
                'tavg_c': 'us_midwest_temp_avg',
                'tmax_c': 'us_midwest_temp_max',
                'tmin_c': 'us_midwest_temp_min',
                'prcp_mm': 'us_midwest_precip_30d',
                'humidity_pct': 'us_midwest_humidity_avg',
                'wind_speed_ms': 'us_midwest_wind_avg'
            })
            
            # Keep needed columns
            keep_cols = ['date', 'us_midwest_temp_avg', 'us_midwest_temp_max', 
                         'us_midwest_temp_min', 'us_midwest_precip_30d',
                         'us_midwest_humidity_avg', 'us_midwest_wind_avg']
            us_midwest = us_midwest[[c for c in keep_cols if c in us_midwest.columns]]
            us_midwest['date'] = us_midwest['date'].dt.date
            
            us_midwest.to_parquet(staging_file, index=False)
            print(f"✅ Created: {staging_file} (US_MIDWEST: {len(us_midwest)} rows)")
            return us_midwest
    
    print("⚠️  Weather data not found")
    return None

def create_eia_staging():
    """EIA = Real data only, deduplicated"""
    
    print("Creating EIA staging file...")
    
    eia_dir = DRIVE / "raw/eia"
    if not eia_dir.exists():
        return None
    
    real_files = []
    for parquet_file in eia_dir.rglob("*.parquet"):
        if 'placeholder' in parquet_file.name.lower():
            continue
        if parquet_file.name == 'eia_all_20251116.parquet':
            continue
        
        df = pd.read_parquet(parquet_file)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.date
            real_files.append(df)
    
    if not real_files:
        return None
    
    combined = pd.concat(real_files, ignore_index=True)
    combined['date'] = pd.to_datetime(combined['date'])
    combined = combined[(combined['date'] >= '2010-01-01') & (combined['date'] <= '2025-12-31')]
    
    # Dedup to one row per date
    deduped = combined.groupby(combined['date'].dt.date).first().reset_index()
    deduped['date'] = pd.to_datetime(deduped['date']).dt.date
    
    staging_file = DRIVE / "staging/eia_biofuels_2010_2025.parquet"
    deduped.to_parquet(staging_file, index=False)
    print(f"✅ Created: {staging_file} ({len(deduped)} rows)")
    
    return deduped

def create_cftc_staging():
    print("CFTC: No data yet (optional)")
    return None

def create_usda_staging():
    print("USDA: No data yet (optional)")
    return None

def main():
    print("="*80)
    print("CREATING STAGING FILES - CORRECTED")
    print("="*80)
    print("Yahoo = ZL=F ONLY, Alpha = Everything Else")
    print("="*80)
    
    staging_dir = DRIVE / "staging"
    staging_dir.mkdir(parents=True, exist_ok=True)
    
    create_yahoo_staging()    # ZL=F ONLY (not all 71 symbols!)
    create_fred_staging()     # Wide format + rename
    create_weather_staging()  # US_MIDWEST + rename
    create_cftc_staging()     # Optional
    create_usda_staging()     # Optional
    create_eia_staging()      # Real data + dedup
    
    print("\n" + "="*80)
    print("✅ STAGING FILES CREATED")
    print("="*80)

if __name__ == "__main__":
    main()
```

---

## CORRECTED EXPECTED RESULTS

### After Phase 1 rebuild:

```
Features: 6,380 rows × ~300 columns (ZL with all calculated features)
Exports:  10 files, each ~6,000-6,200 rows
  - zl_training_prod_allhistory_1w_price.parquet
  - zl_training_prod_allhistory_1w_return.parquet
  - ... (5 horizons × 2 label types)

Training surface: ZL ONLY (before Alpha multi-symbol expansion)
```

### After Phase 2 Alpha integration:

```
Features: ~420,000 rows × ~400 columns
  - 70 symbols (ZL + 69 from Alpha)
  - Each symbol has: OHLCV + 50+ indicators + macro + weather + regimes
  
Alpha adds:
  - CORN, WHEAT, ZS, ZM, ZC, ZW, CL, NG, CT, GC, SI (commodities)
  - USD/BRL, USD/CNY, EUR/USD, etc. (FX)
  - SPY, VIX, DJI, etc. (indices)
  - All with 50+ technical indicators
```

---

## KEY INSIGHT: WHY THIS CHANGES EVERYTHING

**WRONG Understanding:**
- Yahoo = all 71 symbols as base
- Alpha = just adds indicators to existing symbols

**CORRECT Understanding:**
- Yahoo = ZL=F ONLY (the one symbol Alpha can't provide)
- Alpha = ADDS 69 NEW symbols + provides indicators for ALL 70 (including ZL)

**Impact on joins:**
- Phase 1 joins work on ~6,380 rows (ZL only)
- Alpha join EXPANDS dataset to ~420,000 rows (adds 69 symbols)
- Much cleaner separation: Yahoo for unavailable asset, Alpha for everything else

---

## CORRECTED FINAL SUMMARY

**Yahoo role:** Price data for ZL=F ONLY (6,380 rows)  
**Alpha role:** All other symbols (69) + ALL indicators for ALL symbols (70 total)  
**Phase 1 target:** 6,000-6,500 rows (ZL training surface)  
**Phase 2 target:** 420,000 rows (full multi-symbol surface)

**This aligns perfectly with plan:** "Yahoo Finance: ZL=F ONLY"





