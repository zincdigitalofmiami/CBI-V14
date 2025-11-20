---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# MES Training Horizons Setup
**Date:** November 20, 2025  
**Status:** ✅ Complete - All 12 horizons operational

---

## Overview

MES (Micro E-mini S&P 500) training requires **12 distinct horizons** covering intraday, daily, and monthly timeframes. All horizons are built from 1-minute base data collected from DataBento.

---

## MES Training Horizons (Prod + AllHistory)

### Intraday Horizons (6)
Built from 1-minute resampling:
- **1min** - 1-minute bars
- **5min** - 5-minute bars  
- **15min** - 15-minute bars
- **30min** - 30-minute bars
- **1hr** - 60-minute bars
- **4hr** - 240-minute bars

### Daily+ Horizons (3)
Built from daily aggregation:
- **1d** - Daily bars
- **7d** - Weekly bars (7-day aggregation)
- **30d** - Monthly bars (30-day aggregation)

### Monthly Horizons (3)
Built from daily aggregation:
- **3m** - Quarterly bars (3-month aggregation)
- **6m** - Semi-annual bars (6-month aggregation)
- **12m** - Annual bars (12-month aggregation)

**Total: 12 horizons**

---

## Data Pipeline

### 1. Collection (1-Minute Base)
**Script:** `scripts/live/collect_mes_1m.py`
- Collects MES futures 1-minute OHLCV from DataBento
- Saves to: `TrainingData/live/MES/1m/date=YYYY-MM-DD/`
- Runs continuously (60-second interval) or one-time
- Tracks state to avoid duplicates

**Usage:**
```bash
# Run once
python3 scripts/live/collect_mes_1m.py --once

# Run continuously
python3 scripts/live/collect_mes_1m.py --interval 60

# Or use start script
./scripts/live/start_mes_1m_collection.sh
```

### 2. Horizon Building
**Script:** `scripts/ingest/build_mes_all_horizons.py`
- Reads all 1-minute data from `TrainingData/live/MES/1m/`
- Selects active contract chain (7-day rolling volume window)
- Resamples to all 12 horizons
- Saves each horizon to: `TrainingData/staging/mes_{horizon}.parquet`

**Usage:**
```bash
python3 scripts/ingest/build_mes_all_horizons.py
```

**Output Files:**
- `mes_1min.parquet`
- `mes_5min.parquet`
- `mes_15min.parquet`
- `mes_30min.parquet`
- `mes_1hr.parquet`
- `mes_4hr.parquet`
- `mes_1d.parquet`
- `mes_7d.parquet`
- `mes_30d.parquet`
- `mes_3m.parquet`
- `mes_6m.parquet`
- `mes_12m.parquet`

### 3. Technical Indicators
**Script:** `scripts/features/feature_calculations.py`
- Calculates technical indicators for all horizons
- Recognizes `mes_close` column (updated to support MES)
- Generates: RSI, MACD, Bollinger Bands, Moving Averages, etc.

**15-Minute Features:** `scripts/features/mes_15min_features.py`
- Specialized features for 15-minute horizon
- Includes: RSI(14), MACD(12,26,9), ATR(14), Bollinger Bands, daily pivots

---

## Contract Selection

The horizon builder uses **7-day rolling volume window** to select the active contract:
- Prevents intraday oscillation during roll weeks
- Selects highest-volume contract over rolling window
- Maps active contract back to all bars

This ensures smooth transitions during contract rolls (H, M, U, Z quarterly cycle).

---

## Integration with Training

### Training Surfaces
- **daily_only**: Uses daily+ and monthly horizons (1d, 7d, 30d, 3m, 6m, 12m)
- **daily_intra**: Adds intraday horizons (1min-4hr) for enhanced features

### Model Types
- **Intraday (1min-4hr)**: Neural models (LSTM/TCN/CNN-LSTM) - 150-200 features
- **Daily+ (1d-12m)**: Tree models (LightGBM/XGBoost) - 200+ features

---

## Status

✅ **1-Minute Collection**: Operational (`collect_mes_1m.py`)  
✅ **Horizon Building**: Complete (`build_mes_all_horizons.py`)  
✅ **All 12 Horizons**: Created and saved to staging  
✅ **Technical Indicators**: Supported (`feature_calculations.py`)  
✅ **Contract Selection**: 7-day rolling volume window implemented  

---

## Next Steps

1. **Historical Backfill**: Run 1-minute collection for full history (2010-present)
2. **Daily Updates**: Schedule horizon builder to run daily after market close
3. **Training Integration**: Update training scripts to use all 12 horizons
4. **Feature Engineering**: Add horizon-specific features as needed

---

**Last Updated:** November 20, 2025





