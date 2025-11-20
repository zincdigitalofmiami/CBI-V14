---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# 📊 DATA SCHEMA MASTERY - Complete Understanding

**Date**: November 16, 2025  
**Purpose**: Master understanding of all data schemas, joins, and requirements before collection

---

## 🎯 CORE REQUIREMENT

All data must be **join-able on the `date` column** for feature engineering.

---

## 📋 REQUIRED SCHEMA FOR YAHOO FINANCE DATA

### Column Requirements

**Minimum Required Columns**:
```python
{
    'Date': 'datetime64[ns]',  # NO TIMEZONE, clean datetime
    'Symbol': 'object',         # Symbol identifier (e.g., 'ZL=F')
    'Open': 'float64',          # Opening price
    'High': 'float64',          # High price
    'Low': 'float64',           # Low price  
    'Close': 'float64',         # Closing price
    'Volume': 'float64',        # Trading volume
}
```

**Technical Indicators** (calculated, added later):
- SMA_5, SMA_10, SMA_20, SMA_50, SMA_100, SMA_200
- EMA_5, EMA_10, EMA_20, EMA_50, EMA_100, EMA_200
- RSI_14
- MACD, MACD_Signal, MACD_Hist
- BB_Upper_20, BB_Middle_20, BB_Lower_20, BB_Width_20
- BB_Upper_50, BB_Middle_50, BB_Lower_50, BB_Width_50
- Stoch_K, Stoch_D
- ATR_14
- ADX_14
- OBV
- CCI_20
- Williams_R
- ROC_10, ROC_20
- Momentum_10, Momentum_20
- Return_1d, Return_5d, Return_10d, Return_20d, Return_60d, Return_252d
- Volatility_5d, Volatility_10d, Volatility_20d, Volatility_60d, Volatility_252d

### Critical Schema Rules

1. **Date Column**:
   - Must be named `Date` (capital D)
   - Must be `datetime64[ns]` dtype
   - **NO TIMEZONE** - remove with `.dt.tz_localize(None)`
   - Must be a regular column (not index)
   - Must be sortable and join-able

2. **Symbol Column**:
   - Must be named `Symbol`
   - Must contain the original ticker (e.g., 'ZL=F', '^GSPC')
   - Used for filtering and identification

3. **OHLCV Columns**:
   - Standard capitalization: Open, High, Low, Close, Volume
   - All float64 dtype
   - No NaN in critical columns (Close especially)

4. **Columns to DROP**:
   - Dividends (not needed for commodities/indices)
   - Stock Splits (not needed)
   - Any unnamed columns
   - Any duplicate Date columns

---

## 🔗 JOIN SPECIFICATIONS (from join_spec.yaml)

### Base Data
- **Source**: `staging/yahoo_historical_all_symbols.parquet`
- **Expected**: 55+ symbols, 6000+ rows, date range 2000-2025
- **Key Column**: `date` (lowercase for joins)

### Join Sequence

1. **FRED Macro** → adds: `fed_funds_rate`, `vix`, `treasury_10y`, `usd_broad_index`
2. **NOAA Weather** → adds: `us_midwest_precip_30d`, `us_midwest_temp_avg`
3. **CFTC COT** → adds: positioning data (2006+)
4. **USDA NASS** → adds: crop data
5. **EIA Biofuels** → adds: biofuel production (2010+)
6. **Regime Calendar** → adds: `market_regime`, `training_weight`

### Join Key Rules
- All joins use `on: ["date"]`
- Left joins preserve all dates from base
- Null policies vary (some ffill, some default fill)

---

## 📊 FEATURE ENGINEERING EXPECTATIONS

### Feature Calculation Functions (from feature_calculations.py)

**Looks for these price columns** (in order):
1. `close` (lowercase)
2. `zl_price_current`
3. `price`

**Creates these feature prefixes**:
- `tech_` - Technical indicators
- `cross_` - Cross-asset correlations
- `vol_` - Volatility metrics
- `seas_` - Seasonal patterns
- `macro_` - Macroeconomic regimes
- `weather_` - Weather aggregations
- `flag_` - Override flags

### Final Feature Schema
- **Total columns**: 300+ features
- **Required for training**: 100+ columns minimum
- **Date range**: 2000-01-01 to 2025-12-31
- **Regime cardinality**: 7-11 distinct regimes
- **Weight range**: 50-500

---

## 🚨 CRITICAL ISSUES TO AVOID

### 1. Duplicate Date Column
**Problem**: Adding 'Date' when it already exists
**Solution**: 
```python
df = df.reset_index()  # This creates 'Date' from DatetimeIndex
# DO NOT add df['Date'] = ... after this
```

### 2. Timezone Issues
**Problem**: Yahoo Finance returns timezone-aware DatetimeIndex
**Solution**:
```python
df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
```

### 3. Column Name Inconsistency
**Problem**: Sometimes 'Date', sometimes 'date', sometimes index
**Solution**: Always use 'Date' for raw data, convert to 'date' before staging

### 4. Missing Required Columns
**Problem**: Some symbols may not have Volume data
**Solution**: Check for required columns, warn if missing

### 5. Data Type Mismatches
**Problem**: Numeric columns as strings, dates as objects
**Solution**: Explicit dtype conversion

---

## 📁 FILE ORGANIZATION REQUIREMENTS

### Directory Structure
```
TrainingData/raw/yahoo_finance/
├── prices/
│   ├── commodities/    # ZL=F.parquet, ZS=F.parquet, etc.
│   ├── indices/        # GSPC.parquet, VIX.parquet, etc.
│   ├── currencies/     # EURUSD_X.parquet, etc.
│   └── etfs/           # TLT.parquet, etc.
├── technical/          # Symbol_indicators.parquet files
├── fundamentals/       # Symbol_fundamentals.parquet files
└── master_index.parquet
```

### File Naming Convention
- Replace `=` with `_`
- Remove `^` prefix
- Replace `-` with `_`
- Examples:
  - `ZL=F` → `ZL_F.parquet`
  - `^GSPC` → `GSPC.parquet`
  - `DX-Y.NYB` → `DX_Y_NYB.parquet`

---

## 🔄 DATA PROCESSING PIPELINE

### Stage 1: Raw Collection (what we're doing now)
```
Yahoo Finance → raw/yahoo_finance/prices/
```

**Output Schema**:
```python
{
    'Date': datetime64[ns],      # NO timezone
    'Symbol': object,             # Original ticker
    'Open': float64,
    'High': float64,
    'Low': float64,
    'Close': float64,
    'Volume': float64,
    'SMA_20': float64,           # Plus all indicators...
    'RSI_14': float64,
    # ... 50+ indicator columns
}
```

### Stage 2: Conformance (future)
```
raw/yahoo_finance/ → staging/yahoo_historical_all_symbols.parquet
```

**Transforms**:
- Combine all symbols into single file
- Convert 'Date' → 'date' (lowercase for joins)
- Validate date ranges
- Check for gaps
- Apply quality checks

### Stage 3: Feature Engineering (future)
```
staging/ → features/master_features_2000_2025.parquet
```

**Adds**:
- Cross-asset correlations
- Regime assignments
- Seasonal patterns
- Macro features
- Weather features

### Stage 4: Label Generation (future)
```
features/ + labels/ → exports/horizon_1w.parquet, etc.
```

**Creates**: 10 training files (5 horizons × 2 types)

---

## ✅ VALIDATION CHECKLIST

Before saving any file, verify:

- [ ] Date column exists and is datetime64[ns]
- [ ] Date column has NO timezone
- [ ] No duplicate Date column
- [ ] Symbol column exists
- [ ] OHLCV columns all present
- [ ] OHLCV columns are float64
- [ ] No NaN in Date or Symbol
- [ ] Dividends/Stock Splits dropped
- [ ] Technical indicators calculated correctly
- [ ] File name follows convention
- [ ] Data sorted by Date ascending

---

## 🎯 CURRENT YAHOO FINANCE SCRIPT REQUIREMENTS

### What the script MUST do:

1. **Fetch data from yfinance**:
   ```python
   df = ticker.history(start='2000-01-01', end='2025-11-16', auto_adjust=True)
   ```

2. **Reset index to get Date column**:
   ```python
   df = df.reset_index()  # DatetimeIndex 'Date' becomes column 'Date'
   ```

3. **Remove timezone from Date**:
   ```python
   df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
   ```

4. **Add Symbol column**:
   ```python
   df['Symbol'] = symbol  # e.g., 'ZL=F'
   ```

5. **Drop unnecessary columns**:
   ```python
   df = df.drop(columns=['Dividends', 'Stock_Splits'], errors='ignore')
   ```

6. **Calculate technical indicators**:
   ```python
   df = calculate_technical_indicators(df)  # Adds 50+ columns
   ```

7. **Save to organized structure**:
   ```python
   price_file = YAHOO_DIR / "prices" / category / f"{clean_symbol}.parquet"
   df.to_parquet(price_file, index=False)  # index=False is CRITICAL
   ```

---

## 📊 EXPECTED OUTPUT

### Per Symbol File Structure

**Example**: `ZL_F.parquet`
```
Rows: ~6,000 (25 years of daily data)
Columns: ~60 (Date, Symbol, OHLCV, + 50+ indicators)

Sample:
Date         Symbol  Open   High   Low    Close  Volume  SMA_20  RSI_14  ...
2000-01-03   ZL=F    18.50  18.75  18.25  18.60  50000   18.45   55.2    ...
2000-01-04   ZL=F    18.60  18.80  18.50  18.70  52000   18.47   56.1    ...
...
```

### Master Index Structure

**File**: `master_index.parquet`
```
file                            symbol  rows  start_date  end_date
prices/commodities/ZL_F.parquet ZL=F    6234  2000-01-03  2025-11-16
prices/commodities/ZS_F.parquet ZS=F    6234  2000-01-03  2025-11-16
prices/indices/GSPC.parquet     ^GSPC   6450  2000-01-03  2025-11-16
...
```

---

## 🚀 EXECUTION CONFIDENCE

With this understanding, we can:
- ✅ Pull data with correct schema
- ✅ Save files in correct structure
- ✅ Ensure join compatibility
- ✅ Support feature engineering
- ✅ Enable training pipeline

**All potential schema issues identified and solutions documented.**

---

**Last Updated**: November 16, 2025  
**Status**: Ready for execution
