# 📊 CALCULATION INVENTORY
**Date:** November 24, 2025  
**Purpose:** Every calculation, on what instrument, and where it's computed

---

## 🎯 CURRENT STATE: ONLY ZL

| Instrument | Rows | Date Range | Calculations Done |
|------------|------|------------|-------------------|
| **ZL (Soybean Oil)** | 3,936 | 2010-08-18 → 2025-11-14 | ✅ Full TA + Regime |
| MES (Micro E-mini) | 0 | - | ❌ Not calculated yet |
| Others | 0 | - | ❌ Not calculated yet |

---

## 📋 ZL CALCULATIONS (DONE)

### Layer 1: Raw Data (BigQuery Storage)
**Table:** `market_data.databento_futures_ohlcv_1d`  
**Source:** Databento  
**Computed:** N/A (raw ingestion)

| Column | Type | Description |
|--------|------|-------------|
| `date` | DATE | Trading date |
| `symbol` | STRING | 'ZL' |
| `open` | FLOAT64 | Open price |
| `high` | FLOAT64 | High price |
| `low` | FLOAT64 | Low price |
| `close` | FLOAT64 | Close price |
| `volume` | INT64 | Volume |

---

### Layer 2: Feature Calculations (Python → BigQuery)
**Table:** `features.zl_daily_v1`  
**Computed:** Python script (`ingest_zl_v1.py`) on **Mac**  
**Stored:** BigQuery

| Column | Type | Formula | Where Computed |
|--------|------|---------|----------------|
| `trade_date` | DATE | Renamed from `date` | Python |
| `symbol` | STRING | 'ZL' | Python |
| `open` | FLOAT64 | Pass-through | - |
| `high` | FLOAT64 | Pass-through | - |
| `low` | FLOAT64 | Pass-through | - |
| `close` | FLOAT64 | Pass-through | - |
| `volume` | INT64 | Pass-through | - |
| **`return_1d`** | FLOAT64 | `close.pct_change(1)` | **Python (Mac)** |
| **`return_5d`** | FLOAT64 | `close.pct_change(5)` | **Python (Mac)** |
| **`return_21d`** | FLOAT64 | `close.pct_change(21)` | **Python (Mac)** |
| **`ma_5`** | FLOAT64 | `close.rolling(5).mean()` | **Python (Mac)** |
| **`ma_21`** | FLOAT64 | `close.rolling(21).mean()` | **Python (Mac)** |
| **`ma_63`** | FLOAT64 | `close.rolling(63).mean()` | **Python (Mac)** |
| **`volatility_21d`** | FLOAT64 | `return_1d.rolling(21).std() * sqrt(252)` | **Python (Mac)** |
| **`rsi_14`** | FLOAT64 | RSI formula (14-period) | **Python (Mac)** |
| **`regime_name`** | STRING | Lookup from date ranges | **Python (Mac)** |
| **`regime_weight`** | INT64 | Lookup from regime table | **Python (Mac)** |
| `ingestion_ts` | TIMESTAMP | `datetime.utcnow()` | Python |

**RSI Formula Used:**
```python
delta = close.diff()
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / loss
rsi_14 = 100 - (100 / (1 + rs))
```

---

### Layer 3: Training View Calculations (BigQuery)
**View:** `training.vw_zl_1m_v1`  
**Computed:** BigQuery SQL  
**Stored:** View (computed on query)

| Column | Type | Formula | Where Computed |
|--------|------|---------|----------------|
| `trade_date` | DATE | Pass-through | - |
| `close` | FLOAT64 | Pass-through | - |
| `return_1d` | FLOAT64 | Pass-through | - |
| `return_5d` | FLOAT64 | Pass-through | - |
| `return_21d` | FLOAT64 | Pass-through | - |
| `ma_5` | FLOAT64 | Pass-through | - |
| `ma_21` | FLOAT64 | Pass-through | - |
| `ma_63` | FLOAT64 | Pass-through | - |
| `volatility_21d` | FLOAT64 | Pass-through | - |
| `rsi_14` | FLOAT64 | Pass-through | - |
| `regime_name` | STRING | Pass-through | - |
| **`sample_weight`** | INT64 | `regime_weight` (renamed) | **BigQuery** |
| **`target_1m`** | FLOAT64 | `(LEAD(close,21) - close) / close` | **BigQuery** |
| **`target_direction`** | INT64 | `IF(LEAD(close,21) > close, 1, 0)` | **BigQuery** |
| **`split`** | STRING | Date-based: train/val/test | **BigQuery** |

**Target Formula (BigQuery SQL):**
```sql
SAFE_DIVIDE(
    LEAD(close, 21) OVER (ORDER BY trade_date) - close,
    close
) AS target_1m
```

**Split Logic:**
```sql
CASE
    WHEN trade_date < DATE '2023-01-01' THEN 'train'
    WHEN trade_date < DATE '2024-01-01' THEN 'val'
    ELSE 'test'
END AS split
```

---

### Layer 4: Model Training (Mac Only)
**Script:** `train_baseline_v1.py`  
**Computed:** Mac (LightGBM)  
**Stored:** Mac (`models/zl_baseline_v1.txt`)

| What | Where |
|------|-------|
| Data pull from BQ | Mac |
| Feature selection | Mac |
| Train/val/test split | Mac (from BQ view) |
| LightGBM training | Mac |
| Model evaluation | Mac |
| Model save | Mac |

---

## 📊 SUMMARY: WHERE EACH CALCULATION HAPPENS

| Calculation Type | Location | Details |
|-----------------|----------|---------|
| **Raw OHLCV** | Databento → BQ | No calculation, just storage |
| **Returns (1d/5d/21d)** | Python (Mac) | `pct_change()` |
| **Moving Averages (5/21/63)** | Python (Mac) | `rolling().mean()` |
| **Volatility (21d)** | Python (Mac) | `rolling().std() * sqrt(252)` |
| **RSI (14)** | Python (Mac) | Standard RSI formula |
| **Regime Stamp** | Python (Mac) | Date range lookup |
| **Forward Targets** | BigQuery | `LEAD()` window function |
| **Train/Val/Test Split** | BigQuery | Date-based CASE |
| **Model Training** | Mac | LightGBM |

---

## ❌ WHAT'S NOT CALCULATED YET

### Missing Instruments:
- MES (Micro E-mini S&P) - raw data exists, no features
- ZS (Soybeans) - not ingested
- ZM (Soybean Meal) - not ingested
- CL (Crude Oil) - not ingested
- HO (Heating Oil) - not ingested
- FCPO (Palm Oil) - not ingested
- FX pairs - not ingested

### Missing Feature Types:
- **Cross-asset correlations** (ZL vs CL, ZL vs FCPO)
- **Crush margin** ((ZM * 11 + ZL * 11) - ZS)
- **FRED macro** (VIX, Fed Funds, CPI, GDP)
- **Weather anomalies** (temp, precip z-scores)
- **FX features** (DXY, USDBRL, USDCNY)
- **Sentiment/policy** (Trump, tariffs)
- **Pivot points** (P, R1-R4, S1-S4)
- **Volume profile** (VWAP, volume z-scores)
- **Seasonality** (day of week, month, harvest periods)

---

## 🔧 CALCULATION LOCATIONS RULE

```
┌─────────────────────────────────────────────────────────────┐
│                    CALCULATION RULES                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  PYTHON (Mac):                                               │
│  ├── Technical indicators (TA-Lib style)                    │
│  ├── Rolling calculations (returns, vol, MA)                │
│  ├── Regime stamping (date lookup)                          │
│  └── Any complex logic before BQ load                       │
│                                                              │
│  BIGQUERY:                                                   │
│  ├── Forward-looking targets (LEAD/LAG)                     │
│  ├── Train/val/test splits                                  │
│  ├── Window functions across full history                   │
│  ├── Cross-table joins (regime lookup)                      │
│  └── API views (aggregations for dashboard)                 │
│                                                              │
│  MAC (Training):                                             │
│  ├── All model training                                     │
│  ├── Hyperparameter tuning                                  │
│  ├── SHAP analysis                                          │
│  └── Prediction generation                                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📈 NEXT CALCULATIONS TO ADD

Priority order for ZL:

1. **Crush Margin** - Requires ZS, ZM data
2. **Cross-asset betas** - Requires CL, FCPO data
3. **FRED macro** - VIX proxy, Fed Funds, yields
4. **FX pressure** - DXY, USDBRL, USDCNY
5. **Weather anomalies** - NOAA GSOD data
6. **Seasonality** - Calendar features
7. **Pivot points** - P, R1-R4, S1-S4

