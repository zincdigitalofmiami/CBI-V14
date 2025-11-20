---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# MES & Forex Features Status
**Date:** November 20, 2025  
**Status:** 🚧 In Progress - Scripts Created, Ready for Execution

---

## Overview

This document tracks the status of MES and Forex feature calculations needed for BigQuery tables.

---

## MES Features (All 12 Horizons)

### ✅ Completed
- **Horizon Building**: All 12 horizons created (`build_mes_all_horizons.py`)
  - Intraday: 1min, 5min, 15min, 30min, 1hr, 4hr
  - Daily+: 1d, 7d, 30d
  - Monthly: 3m, 6m, 12m

### 🚧 In Progress
- **Feature Calculation**: Script created (`build_mes_all_features.py`)
  - Calculates technical indicators for all horizons
  - Outputs: `mes_{horizon}_features.parquet` for each horizon

### Features Calculated Per Horizon:
- **RSI**: 7, 14, 21 periods
- **MACD**: Line, Signal, Histogram
- **Moving Averages**: SMA/EMA (5, 10, 20, 50, 100, 200)
- **Bollinger Bands**: Upper, Lower, Width, Position
- **ATR**: 7, 14 periods
- **Returns**: 1d, 7d, 30d
- **Volatility**: Realized vol (5, 10, 20, 30, 60-day)
- **Volume Features**: Volume SMA, ratio, trend
- **Price Position**: Distance from MAs

### Existing MES Feature Scripts:
- `mes_15min_features.py` - Specialized 15-minute micro features
- `add_mes_confirmation_features.py` - Correlations with VIX/USD/10Y

### BigQuery Requirements:
- Tables need: `mes_{horizon}_features` columns
- Master features view needs: All MES horizon features joined
- Training tables need: Features for each horizon

---

## Forex Features

### 🚧 Pending
- **Collection**: Script created (`collect_databento_forex.py`)
  - Collects: 6L (BRL), 6E (EUR), 6J (JPY), 6C (CAD), 6B (GBP), 6A (AUD), CNH (Yuan)
  - Outputs: `TrainingData/raw/databento_forex/{symbol}_daily_{start}_{end}.parquet`

- **Feature Calculation**: Script created (`build_forex_features.py`)
  - Calculates technical indicators for all forex symbols
  - Calculates cross-currency correlations
  - Outputs: `forex_features.parquet` (combined, prefixed)

### Features Calculated Per Currency:
- **RSI**: 7, 14 periods
- **MACD**: Line, Signal, Histogram
- **Moving Averages**: SMA/EMA (5, 10, 20, 50, 100)
- **Bollinger Bands**: Upper, Lower, Width, Position
- **ATR**: 14 period
- **Returns**: 1d, 7d, 30d
- **Volatility**: Realized vol (5, 10, 20, 30-day)

### Cross-Currency Features:
- **Correlations**: 30-day rolling correlations between all pairs
- **Currency Strength Index**: Weighted average of all currencies

### BigQuery Requirements:
- Master features table needs:
  - `databento_6e_close` (EUR/USD futures)
  - `cme_6l_brl_close` (BRL futures)
  - `fred_usd_cny` (CNY spot from FRED)
  - `fred_usd_ars` (ARS spot from FRED)
  - Plus all forex feature columns (`fx_*`)

---

## Execution Plan

### Step 1: MES Features (Immediate)
```bash
# Build features for all horizons
python3 scripts/features/build_mes_all_features.py
```

**Outputs:**
- `mes_1min_features.parquet`
- `mes_5min_features.parquet`
- `mes_15min_features.parquet`
- `mes_30min_features.parquet`
- `mes_1hr_features.parquet`
- `mes_4hr_features.parquet`
- `mes_1d_features.parquet`
- `mes_7d_features.parquet`
- `mes_30d_features.parquet`
- `mes_3m_features.parquet`
- `mes_6m_features.parquet`
- `mes_12m_features.parquet`

### Step 2: Forex Collection (Historical Backfill)
```bash
# Collect forex data (2010-present for full history)
python3 scripts/ingest/collect_databento_forex.py --start 2010-06-06 --end 2025-11-20
```

**Outputs:**
- `TrainingData/raw/databento_forex/6l_daily_2010-06-06_2025-11-20.parquet`
- `TrainingData/raw/databento_forex/6e_daily_2010-06-06_2025-11-20.parquet`
- `TrainingData/raw/databento_forex/6j_daily_2010-06-06_2025-11-20.parquet`
- `TrainingData/raw/databento_forex/6c_daily_2010-06-06_2025-11-20.parquet`
- `TrainingData/raw/databento_forex/6b_daily_2010-06-06_2025-11-20.parquet`
- `TrainingData/raw/databento_forex/6a_daily_2010-06-06_2025-11-20.parquet`
- `TrainingData/raw/databento_forex/cnh_daily_2010-06-06_2025-11-20.parquet`

### Step 3: Forex Features
```bash
# Build forex features
python3 scripts/features/build_forex_features.py
```

**Outputs:**
- `forex_features.parquet` (combined, all symbols, all features)

### Step 4: BigQuery Integration
- Update `join_spec.yaml` to include forex features
- Update staging file creation to include forex
- Load forex features to BigQuery
- Update master features view to include forex columns

---

## BigQuery Table Mapping

### MES Tables Needed:
- `features.mes_1min_features`
- `features.mes_5min_features`
- `features.mes_15min_features`
- `features.mes_30min_features`
- `features.mes_1hr_features`
- `features.mes_4hr_features`
- `features.mes_1d_features`
- `features.mes_7d_features`
- `features.mes_30d_features`
- `features.mes_3m_features`
- `features.mes_6m_features`
- `features.mes_12m_features`

### Forex Tables Needed:
- `features.forex_features` (combined table with all currencies)

### Master Features View:
- Must include all MES horizon features (joined on date)
- Must include all forex features (joined on date)
- Column naming: `mes_{horizon}_{feature}` and `fx_{symbol}_{feature}`

---

## Status Summary

| Component | Status | Script | Output |
|-----------|--------|--------|--------|
| MES Horizons | ✅ Complete | `build_mes_all_horizons.py` | 12 horizon files |
| MES Features | 🚧 Ready | `build_mes_all_features.py` | 12 feature files |
| Forex Collection | 🚧 Ready | `collect_databento_forex.py` | Raw forex files |
| Forex Features | 🚧 Ready | `build_forex_features.py` | Combined features |
| BigQuery Load | ⏳ Pending | TBD | BQ tables |

---

## Next Steps

1. ✅ Run `build_mes_all_features.py` to calculate all MES features
2. ⏳ Run `collect_databento_forex.py` for historical backfill
3. ⏳ Run `build_forex_features.py` to calculate forex features
4. ⏳ Update `join_spec.yaml` to include forex
5. ⏳ Update BigQuery schema to include MES/forex tables
6. ⏳ Load all features to BigQuery
7. ⏳ Update master features view

---

**Last Updated:** November 20, 2025





