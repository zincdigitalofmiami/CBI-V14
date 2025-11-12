# Yahoo Finance Integration Plan - 245K Rows → Production

**Date**: November 6, 2025  
**Status**: Data pulled and staged, awaiting integration  
**Critical**: One dataset only - all ingestion goes to production_training_data_*

---

## Current Status

### ✅ Data Successfully Pulled & Staged

**Location**: `cbi-v14.yahoo_finance_comprehensive.all_symbols_20yr` (us-central1)

**Batch 1 - Commodities** (9 symbols, 57,397 rows):
| Symbol | Name | Rows | Date Range | ma_200d | RSI | Avg RSI |
|--------|------|------|------------|---------|-----|---------|
| ZL | Soybean Oil | 6,374 | 2000-03-15 to 2025-11-06 | 6,175 | 6,373 | 50.69 |
| ZS | Soybeans | 6,325 | 2000-09-15 to 2025-11-06 | 6,126 | 6,324 | 51.15 |
| ZM | Soybean Meal | 6,336 | 2000-05-15 to 2025-11-06 | 6,137 | 6,335 | 50.26 |
| ZC | Corn | 6,333 | 2000-07-17 to 2025-11-06 | 6,134 | 6,332 | 50.74 |
| ZW | Wheat | 6,345 | 2000-07-17 to 2025-11-06 | 6,146 | 6,344 | 49.94 |
| CL | Crude Oil | 6,330 | 2000-08-23 to 2025-11-06 | 6,131 | 6,329 | 51.20 |
| DX | Dollar Index | 6,531 | 2000-01-03 to 2025-11-06 | 6,332 | 6,530 | 50.02 |
| VIX | Volatility | 6,502 | 2000-01-03 to 2025-11-06 | 6,303 | 6,501 | 48.97 |
| GC | Gold | 6,321 | 2000-08-30 to 2025-11-06 | 6,122 | 6,320 | 52.94 |

**Batch 2 - Still in Cache** (32 symbols, 187,897 rows):
- 8 FX pairs (CNY, BRL, ARS, MYR, EUR, JPY, GBP, CAD)
- 3 Treasury yields (10Y, 2Y, 30Y)
- 5 Stock indices (S&P, Russell, Nasdaq, ES, ZQ)
- 3 Credit markets (HYG, LQD, TLT)
- 4 Additional commodities (HG, SI, NG, HO)
- 4 Ag sector ETFs (DBA, CORN, WEAT, SOYB)
- 5 Ag stocks (ADM, BG, DAR, INGR, MOS)

**Grand Total**: 245,294 rows when fully processed

---

## Production Tables (DO NOT RENAME)

### Models:
```
cbi-v14.models_v4.bqml_1w
cbi-v14.models_v4.bqml_1m
cbi-v14.models_v4.bqml_3m
cbi-v14.models_v4.bqml_6m
```

### Datasets (ALL INGESTION GOES HERE):
```
cbi-v14.models_v4.production_training_data_1w  (300 columns, 1,472 rows currently)
cbi-v14.models_v4.production_training_data_1m  (300 columns, 1,404 rows currently)
cbi-v14.models_v4.production_training_data_3m  (300 columns, 1,475 rows currently)
cbi-v14.models_v4.production_training_data_6m  (300 columns, 1,473 rows currently)
```

**Current baseline**: ~1,400 rows (2020-01-06 to 2025-11-06) = 5 years
**After integration**: ~6,400 rows (2000-01-03 to 2025-11-06) = 25 years = **5x more training data**

---

## Schema Analysis

### Production Table Has (300 columns):
- date, target_1w/1m/3m/6m
- zl_price_current, zl_volume
- Big 8 signals (9 columns)
- Correlations (30 columns)
- Weather (30+ columns)
- Economic indicators (20+ columns)
- China data (20+ columns)
- Argentina/Brazil data (30+ columns)
- CFTC positioning (10 columns)
- **Technical indicators** (25+ columns): ma_7d, ma_30d, ma_90d, rsi_14, macd_line, etc.
- Palm oil & crude (15+ columns)
- VIX & volatility (10+ columns)
- News & sentiment (20+ columns)
- Trump policy (15+ columns)
- USDA & export (10+ columns)
- Calendar & seasonal (20+ columns)
- Trade & geopolitics (10+ columns)
- Crush & processing (5+ columns)

### Yahoo Staging Has (40 columns):
- date, symbol, symbol_clean, name
- OHLCV (Open, High, Low, Close, Volume)
- **6 Moving Averages**: ma_7d, ma_30d, **ma_50d**, ma_90d, **ma_100d**, **ma_200d**
- **RSI & MACD** (proper EMA-based): rsi_14, macd_line, macd_signal, macd_histogram
- **Bollinger Bands** (5): bb_upper, bb_middle, bb_lower, bb_width, bb_percent
- **ATR**: atr_14
- **Returns** (3): return_1d, return_7d, return_30d
- **Volatility** (3): volatility_7d, volatility_30d, volatility_90d
- **Momentum** (5): price_momentum_7d/30d, price_vs_ma30/200, ma50_vs_ma200, is_golden_cross
- **Metadata**: pulled_at, data_source, calculation_method

---

## Integration Strategy

### NEW COLUMNS to Add to Production (from Yahoo):
1. **ma_50d** - 50-day MA (golden cross indicator)
2. **ma_100d** - 100-day MA
3. **ma_200d** - 200-day MA (major support/resistance)
4. **bb_upper/middle/lower** - Bollinger Bands
5. **bb_width** - Band width (volatility measure)
6. **bb_percent** - Price position within bands
7. **atr_14** - Average True Range
8. **volatility_90d** - 90-day realized volatility
9. **price_momentum_7d/30d** - Price momentum indicators
10. **price_vs_ma30/ma200** - Price relative to MAs
11. **ma50_vs_ma200** - Golden/Death cross indicator
12. **is_golden_cross** - Binary golden cross flag

**Total new columns**: 17 (from 300 → 317 columns)

### UPDATED COLUMNS (Replace with Proper Calculations):
1. **ma_7d** - Replace with Yahoo's properly calculated version
2. **ma_30d** - Replace with Yahoo's version
3. **ma_90d** - Replace with Yahoo's version  
4. **rsi_14** - Replace with proper Wilder's RSI (not my simplified SMA version)
5. **macd_line/signal/histogram** - Replace with proper EMA-based MACD

---

## Safe Integration Plan

### Step 1: Expand Production Schema (Add 17 new columns)
```sql
ALTER TABLE `cbi-v14.models_v4.production_training_data_1m`
ADD COLUMN IF NOT EXISTS ma_50d FLOAT64,
ADD COLUMN IF NOT EXISTS ma_100d FLOAT64,
ADD COLUMN IF NOT EXISTS ma_200d FLOAT64,
ADD COLUMN IF NOT EXISTS bb_upper FLOAT64,
ADD COLUMN IF NOT EXISTS bb_middle FLOAT64,
ADD COLUMN IF NOT EXISTS bb_lower FLOAT64,
ADD COLUMN IF NOT EXISTS bb_width FLOAT64,
ADD COLUMN IF NOT EXISTS bb_percent FLOAT64,
ADD COLUMN IF NOT EXISTS atr_14 FLOAT64,
ADD COLUMN IF NOT EXISTS volatility_90d FLOAT64,
ADD COLUMN IF NOT EXISTS price_momentum_7d FLOAT64,
ADD COLUMN IF NOT EXISTS price_momentum_30d FLOAT64,
ADD COLUMN IF NOT EXISTS price_vs_ma30 FLOAT64,
ADD COLUMN IF NOT EXISTS price_vs_ma200 FLOAT64,
ADD COLUMN IF NOT EXISTS ma50_vs_ma200 FLOAT64,
ADD COLUMN IF NOT EXISTS is_golden_cross INT64,
ADD COLUMN IF NOT EXISTS yahoo_data_source STRING;
```

### Step 2: Map Yahoo Symbols to Production Columns

**ZL (Soybean Oil)** → Updates:
- zl_price_current (from Close)
- zl_volume (from Volume)
- ma_7d, ma_30d, ma_50d, ma_90d, ma_100d, ma_200d
- rsi_14, macd_line, macd_signal, macd_histogram
- bb_*, atr_14, volatility_*, price_momentum_*
- oil_price_per_cwt (for crush margin)

**ZS (Soybeans)** → Updates:
- bean_price_per_bushel (for crush margin)
- Create soybean_price column (new)

**ZM (Soybean Meal)** → Updates:
- soybean_meal_price (existing column)
- meal_price_per_ton (for crush margin)

**ZC (Corn)** → Updates:
- corn_price (existing)

**ZW (Wheat)** → Updates:
- wheat_price (existing)

**CL (Crude Oil)** → Updates:
- crude_price (existing)

**VIX** → Updates:
- vix_level (existing)

**DX (Dollar Index)** → Updates:
- dollar_index (existing)

**GC (Gold)** → Updates:
- gold_price (existing)

### Step 3: Create Integration SQL

```sql
-- Update production_training_data_1m with Yahoo data
UPDATE `cbi-v14.models_v4.production_training_data_1m` prod
SET 
  -- ZL (Soybean Oil) - Primary target
  zl_price_current = COALESCE(yzl.Close, prod.zl_price_current),
  zl_volume = COALESCE(yzl.Volume, prod.zl_volume),
  
  -- Moving Averages (6) - REPLACE with proper calculations
  ma_7d = COALESCE(yzl.ma_7d, prod.ma_7d),
  ma_30d = COALESCE(yzl.ma_30d, prod.ma_30d),
  ma_50d = yzl.ma_50d,  -- NEW
  ma_90d = COALESCE(yzl.ma_90d, prod.ma_90d),
  ma_100d = yzl.ma_100d,  -- NEW
  ma_200d = yzl.ma_200d,  -- NEW
  
  -- Technical Indicators - REPLACE with proper EMA-based
  rsi_14 = COALESCE(yzl.rsi_14, prod.rsi_14),
  macd_line = COALESCE(yzl.macd_line, prod.macd_line),
  macd_signal = COALESCE(yzl.macd_signal, prod.macd_signal),
  macd_histogram = COALESCE(yzl.macd_histogram, prod.macd_histogram),
  
  -- Bollinger Bands - NEW
  bb_upper = yzl.bb_upper,
  bb_middle = yzl.bb_middle,
  bb_lower = yzl.bb_lower,
  bb_width = yzl.bb_width,
  bb_percent = yzl.bb_percent,
  
  -- ATR - NEW
  atr_14 = yzl.atr_14,
  
  -- Other commodities
  corn_price = COALESCE(yzc.Close, prod.corn_price),
  wheat_price = COALESCE(yzw.Close, prod.wheat_price),
  crude_price = COALESCE(ycl.Close, prod.crude_price),
  
  -- Macro indicators
  vix_level = COALESCE(yvix.Close, prod.vix_level),
  dollar_index = COALESCE(ydx.Close, prod.dollar_index),
  gold_price = COALESCE(ygc.Close, prod.gold_price),
  
  -- Crush margin components
  bean_price_per_bushel = COALESCE(yzs.Close / 100, prod.bean_price_per_bushel),
  meal_price_per_ton = COALESCE(yzm.Close, prod.meal_price_per_ton),
  oil_price_per_cwt = COALESCE(yzl.Close * 100, prod.oil_price_per_cwt),
  
  -- Metadata
  yahoo_data_source = 'Yahoo Finance 20yr pull - Nov 6, 2025'
  
FROM `cbi-v14.yahoo_finance_comprehensive.all_symbols_20yr` yzl
LEFT JOIN `cbi-v14.yahoo_finance_comprehensive.all_symbols_20yr` yzs ON prod.date = yzs.date AND yzs.symbol_clean = 'ZS'
LEFT JOIN `cbi-v14.yahoo_finance_comprehensive.all_symbols_20yr` yzm ON prod.date = yzm.date AND yzm.symbol_clean = 'ZM'
LEFT JOIN `cbi-v14.yahoo_finance_comprehensive.all_symbols_20yr` yzc ON prod.date = yzc.date AND yzc.symbol_clean = 'ZC'
LEFT JOIN `cbi-v14.yahoo_finance_comprehensive.all_symbols_20yr` yzw ON prod.date = yzw.date AND yzw.symbol_clean = 'ZW'
LEFT JOIN `cbi-v14.yahoo_finance_comprehensive.all_symbols_20yr` ycl ON prod.date = ycl.date AND ycl.symbol_clean = 'CL'
LEFT JOIN `cbi-v14.yahoo_finance_comprehensive.all_symbols_20yr` yvix ON prod.date = yvix.date AND yvix.symbol_clean = 'VIX'
LEFT JOIN `cbi-v14.yahoo_finance_comprehensive.all_symbols_20yr` ydx ON prod.date = ydx.date AND ydx.symbol_clean = 'DX'
LEFT JOIN `cbi-v14.yahoo_finance_comprehensive.all_symbols_20yr` ygc ON prod.date = ygc.date AND ygc.symbol_clean = 'GC'

WHERE prod.date = yzl.date AND yzl.symbol_clean = 'ZL';
```

---

## Critical Considerations

### 1. **Schema Expansion** (300 → 317 columns)
- Current: 300 columns
- Adding: 17 new columns (ma_50d, ma_100d, ma_200d, Bollinger Bands, ATR, etc.)
- New total: 317 columns
- **Risk**: BQML models trained on 300 columns - need retraining!

### 2. **Data Volume** (1,404 → 6,374 rows)
- Current: 1,404 rows (2020-2025) = 5 years
- After: 6,374 rows (2000-2025) = 25 years
- **Benefit**: 5x more training data for BQML models
- **Risk**: Need to retrain all 4 models (bqml_1w/1m/3m/6m)

### 3. **Metadata Requirements** (for neural network training)

**Already in Yahoo data**:
- ✅ `data_source`: "Yahoo Finance (yfinance library)"
- ✅ `calculation_method`: "EMA-based MACD, Wilders RSI, SMA moving averages"
- ✅ `pulled_at`: Timestamp of data pull

**Need to add to production**:
- `data_lineage`: Track which features came from which source
- `feature_quality_score`: Confidence in each feature (0-1)
- `calculation_timestamp`: When each feature was calculated
- `is_backfilled`: Flag for historical vs real-time data

### 4. **One Dataset Strategy**

**CRITICAL**: All data must flow into one place:
```
Raw Sources (Yahoo, FRED, USDA, etc.)
  ↓
Staging/Transformation Layer (yahoo_finance_comprehensive, etc.)
  ↓
ONE PRODUCTION DATASET: production_training_data_1w/1m/3m/6m
  ↓
BQML Models: bqml_1w/1m/3m/6m
```

**No parallel datasets**. No duplicate tables. One source of truth.

---

## Integration Execution Plan

### Phase 1: Schema Preparation
1. Backup production tables (ALREADY DONE ✅)
2. Add 17 new columns to production_training_data_1m
3. Verify schema expansion successful
4. Document new columns

### Phase 2: Data Integration (1M only first)
1. Test on 10 rows only
2. Verify values are correct
3. Check crush margin calculation works
4. Execute full integration for production_training_data_1m
5. Verify row count: should go from 1,404 → 6,374

### Phase 3: Replicate to Other Horizons
1. production_training_data_1w (same process)
2. production_training_data_3m (same process)
3. production_training_data_6m (same process)

### Phase 4: Model Retraining
1. Retrain bqml_1m with 317 columns, 6,374 rows
2. Verify performance (expect improvement with more data)
3. Retrain bqml_1w, bqml_3m, bqml_6m
4. Compare before/after MAPE

---

## Metadata Schema for Neural Training

### Add to Production Tables:
```sql
ALTER TABLE `cbi-v14.models_v4.production_training_data_1m`
ADD COLUMN IF NOT EXISTS data_lineage JSON,
ADD COLUMN IF NOT EXISTS feature_quality_scores JSON,
ADD COLUMN IF NOT EXISTS calculation_metadata JSON;
```

### Populate Metadata:
```sql
UPDATE `cbi-v14.models_v4.production_training_data_1m`
SET 
  data_lineage = JSON_OBJECT(
    'zl_price_source', 'Yahoo Finance ZL=F',
    'ma_calculation', 'Pandas rolling window',
    'rsi_method', 'Wilders EWM',
    'macd_method', 'EMA 12/26/9'
  ),
  feature_quality_scores = JSON_OBJECT(
    'zl_price', 1.0,
    'ma_200d', CASE WHEN ma_200d IS NOT NULL THEN 1.0 ELSE 0.0 END,
    'rsi_14', CASE WHEN rsi_14 BETWEEN 0 AND 100 THEN 1.0 ELSE 0.5 END
  )
WHERE date >= '2000-01-01';
```

---

## Questions Before Proceeding

1. **Schema expansion**: OK to add 17 new columns (300 → 317)?
2. **Historical data**: OK to go from 1,404 rows → 6,374 rows (5 years → 25 years)?
3. **Model retraining**: After integration, we MUST retrain all 4 BQML models. Ready for this?
4. **Batch 2 data**: Should I process the remaining 187K rows (FX, yields, stocks) or start with just commodities (57K rows)?

**My recommendation**: Start with commodities only (57K rows), integrate, retrain models, verify improvement, THEN add FX/yields/stocks.

**Ready to proceed with Step 1 (schema expansion)?**







