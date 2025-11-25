# 🚀 Phase 2: Feature Expansion Plan
**Date:** November 24, 2025  
**Goal:** Expand from 9 features to 50-100 features

---

## ✅ Phase 1 Complete

- Pipeline working: BQ → Mac
- 3,900 rows, 15 years history
- 9 features, baseline trained
- **Ready for expansion**

---

## 📊 Current Data Inventory

### Databento (POPULATED)
| Symbol | Rows | Date Range | Status |
|--------|------|------------|--------|
| ZL | 3,998 | 2010-06-06 → 2025-11-14 | ✅ Ready |
| MES | 2,036 | 2019-05-05 → 2025-11-16 | ✅ Ready |
| ZS | 0 | - | ❌ Need to pull |
| ZM | 0 | - | ❌ Need to pull |
| CL | 0 | - | ❌ Need to pull |
| HO | 0 | - | ❌ Need to pull |

### raw_intelligence (EMPTY - Schema only)
| Table | Rows | Status |
|-------|------|--------|
| fred_economic | 0 | ❌ Empty |
| volatility_daily | 0 | ❌ Empty |
| palm_oil_daily | 0 | ❌ Empty |
| cftc_positioning | 0 | ❌ Empty |
| weather_segmented | 0 | ❌ Empty |
| news_intelligence | ? | Need to check |
| policy_events | ? | Need to check |

**⚠️ Most raw_intelligence tables are EMPTY. Need to populate.**

---

## 📋 Phase 2 Tasks

### 1. Additional Instruments from Databento

**Need to pull (Futures):**
| Symbol | Name | Why |
|--------|------|-----|
| ZS | Soybeans | Crush margin input |
| ZM | Soybean Meal | Crush margin input |
| CL | Crude Oil | Biofuel/energy link |
| HO | Heating Oil | Biodiesel proxy |
| DX | Dollar Index | FX pressure |

**Need to pull (Options):**
| Symbol | Name | Why |
|--------|------|-----|
| OZL.OPT | Soybean Oil Options | Implied vol, GEX, vol surface |
| OZS.OPT | Soybeans Options | Crush spread vol analysis |
| OZM.OPT | Soybean Meal Options | Crush spread vol analysis |
| ES.OPT | E-mini S&P Options | MES vol context, GEX |
| MES.OPT | Micro E-mini Options | MES GEX, vol surface |

**Check what's already in BQ:**
```sql
SELECT DISTINCT symbol, COUNT(*) as rows, MIN(date) as min_date, MAX(date) as max_date
FROM `cbi-v14.market_data.databento_futures_ohlcv_1d`
GROUP BY symbol
```

### 2. Crush Margin Calculation

**Formula:**
```
Gross Crush = (ZM_price × 11) + (ZL_price × 11) - ZS_price
```
- ZM: Soybean Meal ($/short ton) → convert to $/bushel
- ZL: Soybean Oil (cents/lb) → convert to $/bushel  
- ZS: Soybeans (cents/bushel)

**Features to create:**
- `crush_margin_gross`
- `crush_margin_21d_ma`
- `crush_margin_percentile_90d`
- `crush_margin_zscore_63d`

### 3. FRED Macro Data

**Series to pull:**
| Series ID | Name | Frequency |
|-----------|------|-----------|
| VIXCLS | VIX Close | Daily |
| DFF | Fed Funds Rate | Daily |
| DGS10 | 10-Year Treasury | Daily |
| DGS2 | 2-Year Treasury | Daily |
| DTWEXBGS | Trade-Weighted USD | Daily |
| CPIAUCSL | CPI | Monthly |

**Features to create:**
- `vix_level`, `vix_21d_ma`, `vix_zscore`
- `fed_funds_rate`
- `yield_curve_10y_2y` (spread)
- `usd_index`, `usd_return_21d`

### 4. Cross-Asset Features

**For each related instrument (ZS, ZM, CL, HO):**
- `{symbol}_return_1d`
- `{symbol}_return_21d`
- `{symbol}_volatility_21d`
- `zl_{symbol}_corr_63d` (rolling correlation)
- `zl_{symbol}_beta_63d` (rolling beta)

### 4b. Options-Based Features (NEW)

**From OZL.OPT, OZS.OPT, OZM.OPT:**
- `zl_implied_vol_30d` (IV30 from options chain)
- `zl_vol_surface_slope` (short-term vs long-term IV)
- `zl_put_call_ratio` (sentiment indicator)
- `zl_gamma_exposure` (GEX - dealer positioning)
- `zl_skew` (put/call skew - tail risk)
- `crush_implied_vol` (from OZS/OZM/OZL options)

**From ES.OPT, MES.OPT (for MES model):**
- `mes_implied_vol_30d`
- `mes_gamma_exposure`
- `mes_put_call_ratio`

### 5. Enhanced TA Features

**Add to ZL:**
- Bollinger Bands (upper, lower, %B)
- MACD (line, signal, histogram)
- ATR (14-day)
- Stochastic (K, D)
- Volume z-score
- Price momentum (ROC)

### 6. Calendar Features

- `day_of_week` (0-4)
- `month` (1-12)
- `is_month_end`
- `is_quarter_end`
- `days_to_first_notice` (futures-specific)

---

## 📊 Target Feature Count

| Category | Features | Priority |
|----------|----------|----------|
| ZL TA (current) | 9 | ✅ Done |
| Crush Margin | 5 | 🔴 High |
| Cross-Asset Returns | 8 | 🔴 High |
| Cross-Asset Correlations | 8 | 🟡 Medium |
| FRED Macro | 10 | 🔴 High |
| Enhanced TA | 12 | 🟡 Medium |
| Calendar | 6 | 🟢 Low |
| **Options-Based** | **6** | **🟡 Medium** |
| **TOTAL** | **~64** | |

---

## 🔧 Implementation Order

### Step 1: Check Databento Coverage (Now)
```bash
bq query 'SELECT DISTINCT symbol FROM market_data.databento_futures_ohlcv_1d'
```

### Step 2: Pull FRED Data (If not in BQ)
- Use FRED API or existing ingestion scripts
- Load to `raw_intelligence.fred_economic`

### Step 3: Expand Ingestion Script
- Add ZS, ZM, CL, HO processing
- Calculate crush margin
- Calculate cross-asset features

### Step 4: Update Feature Table
- Create `features.zl_daily_v2` with expanded schema
- Or add columns to existing table

### Step 5: Retrain with Expanded Features
- Use TimeSeriesSplit (5 folds)
- LR=0.01, trees=3000, patience=100

---

## 📁 Files to Create/Modify

```
Quant Check Plan/scripts/
├── ingest_zl_v1.py          # Current (9 features)
├── ingest_zl_v2.py          # NEW: Expanded features
├── pull_fred_macro.py       # NEW: FRED data pull
├── train_baseline_v2.py     # NEW: With TimeSeriesSplit
└── calculate_crush_margin.py # NEW: Crush calculation
```

---

## ⏱️ Timeline

| Task | Time | Status |
|------|------|--------|
| Check Databento coverage | 5 min | Pending |
| Pull FRED data | 30 min | Pending |
| Expand ingestion script | 1 hr | Pending |
| Update feature table | 30 min | Pending |
| Retrain v2 | 30 min | Pending |
| **Total** | **~3 hrs** | |

---

## 🎯 Success Criteria

| Metric | v1 (Current) | v2 Target |
|--------|--------------|-----------|
| Features | 9 | 50+ |
| MAE | 6.16% | <5.0% |
| Direction Acc | 49.3% | >54% |
| Best Iteration | 9 | 500+ |

**Ready to start?**

