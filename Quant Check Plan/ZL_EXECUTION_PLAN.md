# ZL Engine Execution Plan (Priority #1)
**Date:** November 24, 2025  
**Status:** READY TO EXECUTE  
**Goal:** Build complete ZL engine with maximum features (50-100), then retrain baseline

---

## Executive Summary

**Priority:** ZL engine is the immediate focus. MES will be built after ZL is stable.

**Current State:**
- ✅ Baseline v1 trained successfully (3,900 rows, 9 features)
- ✅ Pipeline proven (BQ → Mac works)
- ✅ ZL.FUT data ready (3,998 rows, 2010-2025)
- ❌ Need supporting symbols (ZS, ZM, CL, HO)
- ❌ Need feature expansion (crush margin, cross-asset, macro)

**Target:** 50-100 features for ZL engine, MAE <5.0%, Direction Accuracy >54%

---

## Phase 1: Data Pull (Week 1)

### 1.1 Pull ZL Supporting Symbols from Databento

**Symbols to Pull:**
| Symbol | Purpose | Schemas | Priority |
|--------|---------|---------|----------|
| **ZS.FUT** | Soybeans (crush margin) | ohlcv-1h/1d, bbo-1m, statistics | 🔴 CRITICAL |
| **ZM.FUT** | Soybean Meal (crush margin) | ohlcv-1h/1d, bbo-1m, statistics | 🔴 CRITICAL |
| **CL.FUT** | Crude Oil (energy complex) | ohlcv-1d, statistics | 🟡 HIGH |
| **HO.FUT** | Heating Oil (biodiesel proxy) | ohlcv-1d, statistics | 🟡 HIGH |

**Date Range:** 2010-01-01 → 2025-11-24

**Action:**
```bash
# Update submit_granular_microstructure.py to include ZL supporting symbols
# Submit jobs for ZS, ZM, CL, HO with lean schemas
python scripts/ingest/submit_granular_microstructure.py
```

### 1.2 Add Missing FRED Series

**Series to Add:**
| Series | Purpose | Priority |
|--------|---------|----------|
| **T10YIE** | 10Y Breakeven Inflation | 🟡 For future MES (add now) |
| **NFCI** | Financial Conditions Index | 🟡 For future MES (add now) |
| **DEXJPUS** | USD/JPY | 🟢 For future MES (add now) |

**Action:**
```python
# Update collect_fred_data.py
SERIES_MAP = {
    # ... existing series ...
    "T10YIE": "breakeven_inflation_10y",
    "NFCI": "financial_conditions_index",
    "DEXJPUS": "usd_jpy",
}

# Run pull
python scripts/collect_fred_data.py
```

### 1.3 Load Data to BigQuery

**Action:**
- Use existing `load_databento_csv.py` for Databento data
- Load to generic tables first (`market_data.databento_futures_ohlcv_1d`)
- FRED data already loaded (just add 3 new series)

---

## Phase 2: Table Structure (Week 2)

### 2.1 Create ZL Engine Tables

**Prime Data Tables (11 tables):**
```sql
market_data.zl_ohlcv_1s
market_data.zl_ohlcv_1m
market_data.zl_ohlcv_1h
market_data.zl_ohlcv_1d
market_data.zl_bbo_1s
market_data.zl_bbo_1m
market_data.zl_tbbo
market_data.zl_mbp_1
market_data.zl_mbp_10
market_data.zl_mbo
market_data.zl_statistics
```

**Context Data Tables (3 tables):**
```sql
market_data.zl_context_ohlcv_1h  -- ZS, ZM, CL, HO combined
market_data.zl_context_ohlcv_1d  -- ZS, ZM, CL, HO combined
market_data.zl_context_statistics
```

**Action:** Create DDL script and run in BigQuery

### 2.2 Migrate Existing Data

**Action:**
- Migrate ZL data from generic tables to `zl_*` tables
- Load supporting symbols (ZS, ZM, CL, HO) to `zl_context_*` tables

---

## Phase 3: Feature Engineering (Week 3)

### 3.1 Crush Margin Features (Priority #1)

**Formula:**
```
Gross Crush = (ZM_price × 0.022) + (ZL_price × 0.11) - ZS_price
```

**Features to Create:**
- `crush_margin_gross`
- `crush_margin_21d_ma`
- `crush_margin_percentile_90d`
- `crush_margin_zscore_63d`
- `crush_margin_momentum_7d`
- `crush_margin_momentum_30d`

**Action:** Create `features.zl_crush_daily` view

### 3.2 Cross-Asset Features

**For each supporting symbol (ZS, ZM, CL, HO):**
- `{symbol}_return_1d`
- `{symbol}_return_21d`
- `{symbol}_volatility_21d`
- `zl_{symbol}_corr_63d` (rolling correlation)
- `zl_{symbol}_beta_63d` (rolling beta)

**Action:** Create `features.zl_cross_asset_daily` view

### 3.3 FRED Macro Features

**Features:**
- `vix_level`, `vix_21d_ma`, `vix_zscore`, `vix_percentile`
- `fed_funds_rate`
- `yield_curve_10y_2y` (spread)
- `usd_index`, `usd_return_21d` (from DTWEXBGS)
- `ig_spread`, `hy_spread`
- `ted_spread`

**FX Features (from FRED):**
- `usd_brl` (DEXBZUS) - Brazil FX
- `usd_cny` (DEXCHUS) - China FX
- `usd_jpy` (DEXJPUS) - Japan FX
- `eur_usd` (DEXUSEU) - Euro FX
- `dollar_index_broad` (DTWEXBGS) - Dollar Index

**Action:** Create `features.zl_macro_daily` view (includes FX from FRED)

### 3.4 Enhanced TA Features

**Add to ZL:**
- Bollinger Bands (upper, lower, %B)
- MACD (line, signal, histogram)
- ATR (14-day)
- Stochastic (K, D)
- Volume z-score
- Price momentum (ROC)

**Action:** Update `ingest_zl_v2.py` with enhanced TA

### 3.5 Calendar Features

- `day_of_week` (0-4)
- `month` (1-12)
- `is_month_end`
- `is_quarter_end`
- `days_to_first_notice` (futures-specific)

**Action:** Add to feature calculation script

### 3.6 Master Training View

**Action:** Create `features.zl_training_v1` joining:
- ZL TA features (existing)
- Crush margin features
- Cross-asset features
- Macro features
- Enhanced TA
- Calendar features
- Regime weights

**Target:** 50-100 features total

---

## Phase 4: Training (Week 4)

### 4.1 Export Training Data

**Action:**
```python
# Export from features.zl_training_v1
# Include all features + targets (return_1m_fwd, etc.)
# Export to CSV/Parquet for Mac
```

### 4.2 Retrain with Expanded Features

**Hyperparameters:**
```python
params = {
    'learning_rate': 0.01,      # Slower learning
    'num_leaves': 63,           # More complexity
    'max_depth': 8,             # Allow deeper trees
    'min_data_in_leaf': 50,     # Prevent overfitting
    'feature_fraction': 0.8,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'lambda_l1': 0.1,           # L1 regularization
    'lambda_l2': 0.1,           # L2 regularization
}
callbacks=[
    lgb.early_stopping(stopping_rounds=100),  # More patience
    lgb.log_evaluation(period=50)
]
num_boost_round = 3000  # More trees
```

**CV Strategy:**
```python
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5)
# Train on expanding window, validate on next chunk
```

### 4.3 Validation

**Metrics:**
- MAE < 5.0% (down from 6.16%)
- Direction Accuracy > 54% (up from 49.3%)
- Best Iteration > 500 (model actually learning)

---

## Feature Count Target

| Category | Features | Priority |
|----------|----------|----------|
| ZL TA (current) | 9 | ✅ Done |
| Crush Margin | 6 | 🔴 High |
| Cross-Asset Returns | 4 | 🔴 High |
| Cross-Asset Correlations | 4 | 🟡 Medium |
| Cross-Asset Betas | 4 | 🟡 Medium |
| FRED Macro | 10 | 🔴 High |
| Enhanced TA | 12 | 🟡 Medium |
| Calendar | 6 | 🟢 Low |
| **TOTAL** | **~55** | |

**Target:** 50-100 features (aim for 55+)

---

## Success Criteria

| Metric | v1 (Current) | v2 Target | Validation |
|--------|--------------|-----------|------------|
| Features | 9 | 50+ | Count in training view |
| MAE | 6.16% | <5.0% | Down from baseline |
| Direction Acc | 49.3% | >54% | Up from baseline |
| Best Iteration | 9 | 500+ | Model actually learning |
| Crush Margin | ❌ Missing | ✅ Calculated | Verify formula |
| Cross-Asset | ❌ Missing | ✅ Correlations | Verify 30d/90d rolling |

---

## Timeline

| Week | Task | Deliverable |
|------|------|-------------|
| 1 | Data Pull | ZS, ZM, CL, HO loaded to BQ |
| 2 | Table Structure | ZL engine tables created |
| 3 | Feature Engineering | 50+ features in training view |
| 4 | Training | v2 model trained and validated |

**Total:** 4 weeks for complete ZL engine

---

## Next Steps After ZL Complete

1. ✅ ZL engine stable and validated
2. Pull full MES history (2010-2025)
3. Pull MES supporting symbols (ES, ZQ, ZT, ZN, ZB)
4. Build MES engine (see MES_MASTER_PLAN.md)

---

**Status:** ✅ **READY TO EXECUTE - ZL FIRST, MES LATER**

