# CORRECTED DATA SOURCE SPLIT - YAHOO ZL ONLY
**Date:** November 17, 2025  
**Critical Correction:** Yahoo = ZL=F ONLY, Alpha = Everything Else

---

## THE CORRECT SPLIT

### YAHOO FINANCE: **ZL=F ONLY** (Soybean Oil Futures)

**Why Only ZL:**
- Alpha Vantage does NOT provide ZL=F futures contract
- ZL is the primary target asset for CBI-V14
- All other commodities/FX/indices available from Alpha

**Current staging has:** 71 symbols (416,110 rows)  
**Should have:** 1 symbol - ZL=F only (6,380 rows)

**Other 70 symbols to DELETE from Yahoo:**
- Commodities: ZS, ZM, ZC, ZW, CL, NG, CT, GC, SI, HG, etc. → **Alpha provides**
- FX: USD/BRL, USD/CNY, EUR/USD, etc. → **Alpha provides**
- Indices: ^GSPC, ^DJI, ^VIX, etc. → **Alpha provides**
- ETFs: DBA, SOYB, CORN, WEAT, etc. → **Alpha provides**

---

### ALPHA VANTAGE: **Everything Except ZL**

**Alpha provides:**
1. All commodities (except ZL): CORN, WHEAT, SOYBEANS (ZS), SOYBEAN MEAL (ZM), WTI, BRENT, etc.
2. All FX pairs: USD/BRL, USD/CNY, EUR/USD, etc.
3. All indices: SPY, DIA, QQQ, VIX, etc.
4. **ALL 50+ technical indicators for ALL symbols (including ZL!)**
5. Options chains
6. News & sentiment
7. ES futures (all timeframes)

---

## CORRECTED YAHOO STAGING FIX

```python
def create_yahoo_staging():
    """
    YAHOO-SPECIFIC: FILTER TO ZL=F ONLY
    Reason: Alpha Vantage provides all other symbols
    """
    
    print("Creating Yahoo staging file (ZL=F ONLY)...")
    
    yahoo_dir = DRIVE / "raw/yahoo_finance/prices"
    
    if not yahoo_dir.exists():
        print(f"⚠️  Yahoo directory not found: {yahoo_dir}")
        return None
    
    # Look for ZL=F file specifically
    zl_file = None
    for category in ['commodities', 'currencies', 'indices', 'etfs']:
        cat_dir = yahoo_dir / category
        if not cat_dir.exists():
            continue
        
        # Find ZL_F.parquet
        for parquet_file in cat_dir.glob("ZL_F.parquet"):
            zl_file = parquet_file
            break
        
        if zl_file:
            break
    
    if not zl_file:
        print("❌ ZL_F.parquet not found!")
        print("   Searched in: commodities, currencies, indices, etfs")
        return None
    
    # Load ZL=F ONLY
    df = pd.read_parquet(zl_file)
    
    print(f"  ✅ Found ZL=F: {len(df)} rows")
    
    # Keep ONLY raw OHLCV (strip 46 pre-calculated indicators)
    # Alpha will provide ALL technical indicators (for ZL and all other symbols)
    raw_columns = ['Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 
                   'Volume', 'Dividends', 'Stock Splits', 'Capital Gains']
    keep_cols = [c for c in raw_columns if c in df.columns]
    df = df[keep_cols]
    
    print(f"  ✅ Stripped indicators: {54 - len(keep_cols)} columns removed")
    print(f"  ✅ Kept only raw OHLCV: {len(keep_cols)} columns")
    
    # Standardize Date column
    if 'Date' in df.columns:
        df['date'] = pd.to_datetime(df['Date']).dt.date
        df = df.drop(columns=['Date'])
    
    # Lowercase ALL column names
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    
    # Verify we have ZL=F
    if 'symbol' in df.columns:
        assert df['symbol'].nunique() == 1, "Should only have one symbol (ZL=F)"
        assert 'ZL=F' in df['symbol'].values or 'ZL-F' in df['symbol'].values, "Symbol should be ZL=F"
    
    print(f"  ✅ Single symbol: {df['symbol'].iloc[0] if 'symbol' in df.columns else 'N/A'}")
    print(f"  ✅ Columns: {list(df.columns)}")
    
    # Save
    staging_file = DRIVE / "staging/yahoo_historical_all_symbols.parquet"  # Keep same name for join_spec compatibility
    df.to_parquet(staging_file, index=False)
    print(f"✅ Created: {staging_file} ({len(df)} rows × {len(df.columns)} cols - ZL=F ONLY)")
    
    return df
```

---

## IMPACT ON JOIN PIPELINE

### BEFORE (Current - WRONG):
```
Yahoo staging: 416,110 rows (71 symbols × ~6,000 days)
Contains: ZL + ZS + ZM + ZC + currencies + indices + VIX + SPY + etc.

Join sequence:
1. Yahoo (416K rows) - ALL symbols
2. + FRED → 6.2M rows ❌ (cartesian product)
```

### AFTER (Corrected):
```
Yahoo staging: 6,380 rows (1 symbol: ZL=F only × ~6,000 days)
Contains: ZL=F ONLY (raw OHLCV, no indicators)

Join sequence:
1. Yahoo (6.4K rows) - ZL=F ONLY
2. + FRED (9.5K dates) → 6.4K rows ✅ (preserves rows)
3. + Weather (9.5K dates) → 6.4K rows ✅
4. + CFTC → 6.4K rows ✅
5. + USDA → 6.4K rows ✅
6. + EIA → 6.4K rows ✅
7. + Regimes → 6.4K rows ✅
8. + Alpha (multi-symbol: ZL + 69 others with indicators) → expands rows ✅

FINAL: ~480K rows (70 symbols × ~6.8K dates) with all features
```

---

## WHAT ALPHA BRINGS TO THE TABLE

**For ZL=F (our primary asset):**
- ✅ 50+ technical indicators (RSI, MACD, SMA, EMA, BBANDS, ATR, etc.)
- ✅ Options chain data (if available for SOYB ETF as proxy)
- ✅ News & sentiment tagged with ZL/soybean/agriculture

**For other symbols (supporting features):**
- ✅ CORN, WHEAT, SOYBEANS (ZS), SOYBEAN MEAL (ZM) - prices + indicators
- ✅ WTI, BRENT, NATURAL_GAS - energy prices + indicators
- ✅ COTTON, SUGAR, COFFEE - soft commodities + indicators
- ✅ COPPER, ALUMINUM - metals + indicators
- ✅ FX pairs: USD/BRL, USD/CNY, USD/ARS, etc. - prices + indicators
- ✅ Indices: SPY, VIX (if not from FRED) - prices + indicators

---

## CORRECTED FINAL TESTS

### After all joins complete:

```yaml
final_tests:
  - expect_total_rows_gte: 6000  # ZL=F has ~6,380 rows (not 416K!)
  - expect_total_cols_gte: 100
  - expect_no_duplicate_dates
  - expect_date_range: ["2000-01-01", "2025-12-31"]
  - expect_regime_cardinality_gte: 7
  - expect_weight_range: [50, 1000]
```

**NOTE:** Row count expectation is ~6,000-6,500 (ZL only), NOT 416,000

---

## WHY THIS MAKES SENSE

1. **ZL is not in Alpha Vantage** - must use Yahoo
2. **Everything else IS in Alpha Vantage** - consolidation opportunity
3. **Alpha provides indicators for ALL symbols** - including ZL
4. **Simpler initial joins** - single symbol until Alpha adds multi-symbol data
5. **Plan explicitly states:** "Yahoo Finance: ZL=F ONLY"

---

## REVISED EXPECTATIONS

### Phase 1 (ZL Only):
- Yahoo: 6,380 rows (ZL=F)
- After all joins: 6,380 rows × ~40 columns (OHLCV + FRED + weather + regimes)
- After feature engineering: 6,380 rows × ~300 columns
- Exports: 5 horizons × 2 label types = 10 files, each ~6,000-6,200 rows ✅

### Phase 2 (Add Alpha):
- Alpha join adds: 69 more symbols × ~6,000 days = ~414,000 rows
- Plus: 50+ technical indicators for ALL 70 symbols
- Final: ~420,000 rows × ~400 columns (complete feature set)

---

## CORRECTED YAHOO STAGING FUNCTION

**Final version - ZL=F ONLY:**

```python
def create_yahoo_staging():
    """
    Yahoo = ZL=F ONLY (Alpha does not provide this futures contract)
    Alpha = Everything else (69 symbols + ALL indicators)
    """
    
    print("Creating Yahoo staging file (ZL=F ONLY)...")
    
    yahoo_dir = DRIVE / "raw/yahoo_finance/prices/commodities"
    
    # Find ZL_F.parquet specifically
    zl_file = yahoo_dir / "ZL_F.parquet"
    
    if not zl_file.exists():
        print(f"❌ ZL_F.parquet not found at {zl_file}")
        return None
    
    # Load ZL=F data
    df = pd.read_parquet(zl_file)
    
    # Keep ONLY raw OHLCV (strip 46 indicators - Alpha will provide 50+ for ZL)
    raw_columns = ['Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 
                   'Volume', 'Dividends', 'Stock Splits']
    keep_cols = [c for c in raw_columns if c in df.columns]
    df = df[keep_cols]
    
    # Standardize date
    df['date'] = pd.to_datetime(df['Date']).dt.date
    df = df.drop(columns=['Date'])
    
    # Lowercase columns
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    
    print(f"  ✅ ZL=F only: {len(df)} rows")
    print(f"  ✅ Stripped indicators: kept {len(df.columns)} raw columns")
    print(f"  ✅ Date range: {df['date'].min()} to {df['date'].max()}")
    
    # Save (same filename for join_spec compatibility)
    staging_file = DRIVE / "staging/yahoo_historical_all_symbols.parquet"
    df.to_parquet(staging_file, index=False)
    print(f"✅ Created: {staging_file} (ZL=F ONLY: {len(df)} rows × {len(df.columns)} cols)")
    
    return df
```

**Result:** 6,380 rows (not 416,110), ready for Phase 1 training surface rebuild

