---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# MES/ZL Pipeline Fix - Execution Summary

**Date:** 2025-11-18  
**Status:** ✅ COMPLETE

## Overview

Fixed systemic contract handling issues in all 4 Databento loaders that were mixing calendar spreads with outright contracts, causing dtype corruption and impossible prices.

## Files Modified

### 1. `scripts/ingest/aggregate_mes_intraday.py`
**Changes:**
- Flattened nested `hd.ts_event` in JSON success path
- Added strict symbol validation: `^MES[A-Z]\d+$` regex (fails if symbol missing)
- Volume-weighted contract selection in `aggregate_to_daily()` - groups by (date, symbol) first
- Per-symbol resampling to prevent mixing contracts during 1min→5/15/30/60/240min aggregation
- Numeric coercion with NaN cleanup

**Output:** `staging/mes_daily_aggregated.parquet` - 2,036 rows × 34 columns

### 2. `scripts/ingest/aggregate_zl_intraday.py`
**Changes:**
- Same fixes as MES aggregator
- Strict symbol validation: `^ZL[A-Z]\d+$` regex
- Volume-weighted selection in `aggregate_to_daily()`
- Per-symbol resampling

**Output:** `staging/zl_daily_aggregated.parquet` - 3,998 rows × 14 columns  
**Note:** ⚠️ Uses 1-hour data (no 1-minute files exist) - see ZL_1MIN_DATA_GAP.md

### 3. `scripts/staging/create_mes_futures_daily.py`
**Changes:**
- Flattened `hd.ts_event` in both JSON and NDJSON paths
- Preserved `symbol` column through loading
- Strict symbol validation
- Volume-weighted contract selection in `main()` - prevents splicing MESZ5 (6900) with spread prices (60)
- Numeric coercion

**Output:** `staging/mes_futures_daily.parquet` - 2,036 rows × 6 columns

### 4. `scripts/ingest/build_mes_15min_series.py`
**Changes:**
- Flattened `hd.ts_event`, preserved symbol
- Strict symbol validation
- **Contract calendar logic:** 7-day rolling volume window to select active contract per date
- Per-symbol resampling of 1-minute bars to 15-minute
- Prevents intraday oscillation during roll weeks

**Output:** `staging/mes_15min.parquet` - 229,160 rows × 6 columns  
(Started with 1,078,807 bars across all contracts, selected 229K from active contract chain)

### 5. `scripts/features/add_mes_confirmation_features.py` (no changes needed)
**Output:** `staging/mes_confirmation_features.parquet` - 2,036 rows × 15 columns

### 6. `scripts/features/mes_15min_features.py` (no changes needed)
**Output:** `staging/mes_15min_features.parquet` - 229,160 rows × features

### 7. `scripts/train/build_mes_15min_dataset.py` (no changes needed)
**Output:** `exports/mes_15min_training.parquet` - 229,159 rows × 30 columns

## Validation Results

### Dtype Check ✅
All OHLCV columns are now **float64** (previously object):
- `mes_futures_daily.parquet` ✅
- `mes_15min.parquet` ✅
- `mes_daily_aggregated.parquet` ✅
- `zl_daily_aggregated.parquet` ✅
- `es_futures_daily.parquet` ✅ (already clean - single symbol ES=F)

### Price Sanity Check ✅
- **MES:** 2,174 - 6,950 (includes historical data back to MES launch)
- **ZL:** 25.09 - 86.55 (soybean oil futures)
- **ES:** 676 - 6,925 (long history)

No more impossible prices (e.g., 60-handle values from spread contamination)

### Exports ✅
- `TrainingData/exports/mes_15min_training.parquet` created (229,159 rows × 30 columns)
- Includes MES 15-minute OHLCV + technical features (RSI, MACD, Bollinger, ATR, pivots)

## Key Fixes Applied

### 1. Spread Filtering
**Before:** Spread contracts like `MESZ5-MESH6` mixed with outrights  
**After:** Strict regex `^MES[A-Z]\d+$` enforces outright-only

### 2. JSON Flattening
**Before:** `KeyError: 'timestamp'` when Databento returns `{"data": [{"hd": {"ts_event": ...}}]}`  
**After:** Flattens nested `hd.ts_event` in both JSON and NDJSON paths

### 3. Contract Selection
**Before:** `groupby('date').agg(open='first')` took arbitrary first symbol → spliced different months  
**After:** Groups by `(date, symbol)` first, then selects highest-volume contract per date

### 4. Contract Calendar (15-min only)
**Before:** Resampled all symbols together → averaged MESZ5 + MESH6 when overlapping  
**After:** 
1. Resample per symbol separately
2. Build contract calendar using 7-day rolling volume window
3. Select single active contract per date to prevent intraday oscillation

### 5. Numeric Coercion
**Before:** Object dtypes for OHLCV due to string contamination  
**After:** `pd.to_numeric(..., errors='coerce')` + NaN cleanup

## Outstanding Issues

### ⚠️ ZL 1-Minute Data Gap (CRITICAL)
- Current: Only 1-hour files exist
- Impact: ZL microstructure features (`zl_60min_realized_vol`, `zl_60min_hl_vol`, `zl_60min_vwap`) computed from hourly bars → mathematically incorrect
- Action: Download 1-minute ZL data from Databento
- Documentation: `docs/setup/ZL_1MIN_DATA_GAP.md`

## Next Steps

1. ✅ All staging files generated with clean numeric dtypes
2. ✅ Exports directory populated with training dataset
3. ⏭️ Download ZL 1-minute data and rerun ZL aggregator
4. ⏭️ Run join harness to validate `registry/join_spec.yaml` requirements
5. ⏭️ Train MES 15-minute models (GBR, XGBoost, etc.)

## Testing Commands

```bash
# Verify all staging files exist and have correct dtypes
python3 - <<'PY'
import pandas as pd
from pathlib import Path
staging = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/staging")
for f in ["mes_futures_daily.parquet", "mes_15min.parquet", "mes_daily_aggregated.parquet", "zl_daily_aggregated.parquet"]:
    df = pd.read_parquet(staging / f)
    print(f"{f}: {df.shape}, dtypes OK: {all(df[c].dtype != 'object' for c in df.columns if 'close' in c)}")
PY

# Check exports
ls -lh /Volumes/Satechi\ Hub/Projects/CBI-V14/TrainingData/exports/

# Rerun full pipeline (if needed)
python3 scripts/ingest/aggregate_mes_intraday.py
python3 scripts/ingest/aggregate_zl_intraday.py
python3 scripts/staging/create_mes_futures_daily.py
python3 scripts/ingest/build_mes_15min_series.py
python3 scripts/features/add_mes_confirmation_features.py
python3 scripts/features/mes_15min_features.py
python3 scripts/train/build_mes_15min_dataset.py
```

## Success Criteria Met ✅

- [x] All 4 Databento loaders filter spreads and validate symbols
- [x] JSON paths flatten nested `hd.ts_event`
- [x] Volume-weighted contract selection prevents month-splicing
- [x] Contract calendar prevents intraday oscillation (15-min)
- [x] All OHLCV columns numeric (float64)
- [x] Price ranges reasonable (no 60-handle spread contamination)
- [x] Staging files generated: mes_daily_aggregated, zl_daily_aggregated, mes_futures_daily, mes_15min
- [x] Feature files generated: mes_confirmation_features, mes_15min_features
- [x] Training dataset created: exports/mes_15min_training.parquet
- [x] ES staging validated (already clean)
- [x] ZL 1-minute data gap documented

**Pipeline is now production-ready for MES. ZL requires 1-minute data download for accurate microstructure features.**

