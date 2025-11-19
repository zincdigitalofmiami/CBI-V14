# Horizon Training Strategy: Special vs. Main Training
**Date:** November 18, 2025  
**Status:** COMPLETE REFERENCE  
**Purpose:** Explain all horizons, special training (intraday), main training (daily+), and how they combine

---

## 🎯 HORIZON OVERVIEW

### ZL (Soybean Oil) - 5 Horizons (Daily-Based)
**All ZL horizons are daily-based** - no intraday special training needed.

| Horizon | Type | Training Strategy | Model Type | Features | MAPE Target |
|---------|------|------------------|------------|----------|-------------|
| **1 week** | Short-term | Main training | Tree + Neural | Daily fundamentals | < 1.5% |
| **1 month** | Short-term | Main training | Tree + Neural | Daily fundamentals | < 1.5% |
| **3 months** | Medium-term | Main training | Tree + Neural | Daily fundamentals | < 1.5% |
| **6 months** | Long-term | Main training | Tree + Neural | Daily fundamentals | < 1.5% |
| **12 months** | Long-term | Main training | Tree + Neural | Daily fundamentals | < 1.5% |

**Key Point:** ZL uses **daily data only** - no microstructure, no intraday patterns. All 5 horizons trained with same daily feature set, just different target labels.

---

### MES (Micro E-mini S&P 500) - 12 Horizons (Intraday + Daily)

**CRITICAL SPLIT:** MES has TWO distinct training strategies based on timeframe granularity.

#### **SPECIAL TRAINING (Intraday - 6 Horizons)**
**These need neural networks + microstructure features**

| Horizon | Type | Training Strategy | Model Type | Features | MAPE Target | Data Volume |
|---------|------|------------------|------------|----------|-------------|-------------|
| **1 min** | Micro | **SPECIAL** | Neural (LSTM, TCN) | 150 micro features | < 0.8% | ~1.5M rows |
| **5 min** | Micro | **SPECIAL** | Neural (LSTM, TCN) | 150 micro features | < 0.8% | ~300K rows |
| **15 min** | Micro | **SPECIAL** | Neural (LSTM, TCN) | 150 micro features | < 0.8% | ~100K rows |
| **30 min** | Micro | **SPECIAL** | Neural (LSTM, TCN) | 150 micro features | < 0.8% | ~50K rows |
| **1 hour** | Transitional | **SPECIAL** | Neural (LSTM, TCN) | 180 features (micro + macro) | < 0.8% | ~25K rows |
| **4 hours** | Transitional | **SPECIAL** | Neural (LSTM, TCN) | 200 features (micro + macro) | < 0.8% | ~6K rows |

**Special Training Characteristics:**
- **Model Type:** Neural networks (LSTM, TCN, CNN-LSTM)
- **Hardware:** FP16 mixed precision (Metal GPU)
- **Features:** Microstructure-heavy (order imbalance, microprice, depth, trade flow)
- **Batch Size:** ≤32 (memory-constrained)
- **Sequence Length:** 60 bars (1 hour of 1min bars)
- **Training Time:** Longer (neural nets are slower)
- **Data:** High-frequency (1min-4hr bars)

#### **MAIN TRAINING (Multi-Day+ - 6 Horizons)**
**These use tree models + macro/fundamental features**

| Horizon | Type | Training Strategy | Model Type | Features | MAPE Target | Data Volume |
|---------|------|------------------|------------|----------|-------------|-------------|
| **1 day** | Multi-day | **MAIN** | Tree (LightGBM, XGBoost) | 250 features (micro agg + macro) | < 1.2% | ~3.8K rows |
| **7 days** | Multi-day | **MAIN** | Tree (LightGBM, XGBoost) | 250 features (micro agg + macro) | < 1.2% | ~3.8K rows |
| **30 days** | Multi-day | **MAIN** | Tree (LightGBM, XGBoost) | 250 features (micro agg + macro) | < 1.2% | ~3.8K rows |
| **3 months** | Multi-month | **MAIN** | Tree (LightGBM, XGBoost) | 200 features (mostly macro/fundamental) | < 1.2% | ~3.8K rows |
| **6 months** | Multi-month | **MAIN** | Tree (LightGBM, XGBoost) | 200 features (mostly macro/fundamental) | < 1.2% | ~3.8K rows |
| **12 months** | Multi-month | **MAIN** | Tree (LightGBM, XGBoost) | 200 features (mostly macro/fundamental) | < 1.2% | ~3.8K rows |

**Main Training Characteristics:**
- **Model Type:** Tree models (LightGBM, XGBoost, CatBoost)
- **Hardware:** CPU (no GPU needed)
- **Features:** Macro/fundamental-heavy (VIX, FX, earnings, economic releases)
- **Batch Size:** Unlimited (tree models are fast)
- **Sequence Length:** None (tabular data)
- **Training Time:** Fast (tree models train quickly)
- **Data:** Daily aggregates (1d-12m horizons)

---

## 🔄 HOW THEY COMBINE

### 1. **Feature Engineering Pipeline**

```
MES Raw Data (DataBento 1-minute)
    ↓
┌─────────────────────────────────────────┐
│  INTRADAY FEATURES (1min-4hr)          │
│  - Order imbalance                      │
│  - Microprice deviation                 │
│  - Trade aggressor imbalance            │
│  - Depth metrics                        │
│  - Volume intensity                     │
│  - VWAP deviation                       │
│  → 150-200 micro features               │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  DAILY AGGREGATION (1d-12m)            │
│  - Aggregate micro features to daily    │
│  - Add macro features (VIX, FX, etc.)  │
│  - Add fundamental features (earnings)  │
│  → 200-300 macro/fundamental features   │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  TRAINING EXPORTS                      │
│  - 1min-4hr: Neural net features       │
│  - 1d-12m: Tree model features        │
└─────────────────────────────────────────┘
```

### 2. **Model Architecture Selection**

**Intraday (1min-4hr):**
- **Why Neural?** Microstructure patterns are sequential (order flow, depth changes)
- **Architecture:** LSTM, TCN, CNN-LSTM (capture temporal patterns)
- **Input:** Sequence of 60 bars (last hour of 1min bars)
- **Output:** Next bar prediction

**Multi-Day+ (1d-12m):**
- **Why Tree?** Daily aggregates are tabular (no sequential patterns)
- **Architecture:** LightGBM, XGBoost (fast, interpretable)
- **Input:** Single row (today's features)
- **Output:** Future price (1d, 7d, 30d, 3m, 6m, 12m ahead)

### 3. **Training Workflow**

```
PHASE 1: Special Training (Intraday)
├── Train 1min model (LSTM, 150 micro features)
├── Train 5min model (LSTM, 150 micro features)
├── Train 15min model (LSTM, 150 micro features)
├── Train 30min model (LSTM, 150 micro features)
├── Train 1hr model (LSTM, 180 features)
└── Train 4hr model (LSTM, 200 features)
    ↓
PHASE 2: Main Training (Multi-Day+)
├── Train 1d model (LightGBM, 250 features)
├── Train 7d model (LightGBM, 250 features)
├── Train 30d model (LightGBM, 250 features)
├── Train 3m model (LightGBM, 200 features)
├── Train 6m model (LightGBM, 200 features)
└── Train 12m model (LightGBM, 200 features)
    ↓
PHASE 3: Ensemble
├── Combine intraday predictions (neural ensemble)
├── Combine multi-day predictions (tree ensemble)
└── Meta-learner chooses best model per regime
```

### 4. **Shared vs. Separate Data**

**Shared Data (Both ZL and MES use):**
- Macro indicators (FRED rates, VIX, FX)
- Regime calendar (crisis, bull, bear, normal)
- Policy events (Trump, trade war, biofuel)
- Global intelligence (news sentiment, hidden relationships)

**ZL-Specific Data:**
- Crush margins, palm oil prices, biodiesel production
- USDA soy reports, China soy imports
- Brazil/Argentina weather (soy belt)

**MES-Specific Data:**
- Microstructure (order flow, depth, trades)
- Equity-specific (earnings, sector rotation, index rebalancing)
- Intraday patterns (opening auction, lunch hour, close)

**Combination in Training:**
```python
# ZL training
zl_features = (
    load_shared_macro() +           # Shared
    load_zl_crush() +               # ZL-specific
    load_zl_weather()               # ZL-specific
)

# MES intraday training (1min-4hr)
mes_intraday_features = (
    load_shared_macro() +           # Shared
    load_mes_microstructure() +     # MES-specific
    load_mes_orderflow()            # MES-specific
)

# MES multi-day training (1d-12m)
mes_daily_features = (
    load_shared_macro() +           # Shared
    load_mes_micro_aggregated() +   # MES-specific (aggregated from intraday)
    load_mes_fundamentals()         # MES-specific (earnings, etc.)
)
```

---

## 📊 FEATURE COUNT BY TIMEFRAME

### MES Intraday (1min-4hr) - Special Training
**150-200 features (90% microstructure, 10% technical)**

**Microstructure Features (135-180):**
- Order imbalance (bid/ask volume ratio)
- Microprice deviation (midpoint vs. last trade)
- Trade aggressor imbalance (buyer-initiated vs. seller-initiated)
- Depth metrics (bid/ask depth, depth imbalance)
- Quote intensity (quote updates per second)
- Spread metrics (bid-ask spread, spread volatility)
- Trade flow (volume, trade count, average trade size)
- VWAP deviation (price vs. VWAP)

**Technical Features (15-20):**
- RSI (14-period)
- MACD
- Bollinger Bands
- ATR (Average True Range)
- Volume intensity

**NO Macro/Fundamental Features** (too noisy for 1min-4hr)

---

### MES Multi-Day+ (1d-12m) - Main Training
**200-300 features (30% micro aggregates, 50% macro, 20% fundamentals)**

**Microstructure Aggregates (60-90):**
- Daily order imbalance (average, std dev)
- Daily microprice deviation (average, max)
- Daily trade aggressor ratio
- Daily depth metrics (average, min, max)
- Daily spread metrics (average, volatility)
- Daily volume intensity

**Macro Features (100-150):**
- VIX level, VIX z-score
- FX rates (USD/BRL, USD/CNY, etc.)
- Interest rates (10Y, 2Y, spread)
- Dollar index
- Commodity indices
- Economic releases (NFP, CPI, etc.)

**Fundamental Features (40-60):**
- Earnings proximity (days to next earnings)
- Sector rotation signals
- Index rebalancing dates
- Dividend effects
- Equity-specific events

---

## 🎯 TRAINING PRIORITY

### Priority 1: Special Training (Intraday)
**Why First?** These are the hardest (high-frequency, microstructure patterns)

1. **1min model** (most challenging)
2. **5min model**
3. **15min model**
4. **30min model**
5. **1hr model**
6. **4hr model**

**Training Time:** ~2-3 days per model (neural nets are slow)
**Total Time:** ~12-18 days for all 6 intraday models

---

### Priority 2: Main Training (Multi-Day+)
**Why Second?** These are easier (daily aggregates, tree models)

1. **1d model** (fastest to train)
2. **7d model**
3. **30d model**
4. **3m model**
5. **6m model**
6. **12m model**

**Training Time:** ~2-4 hours per model (tree models are fast)
**Total Time:** ~12-24 hours for all 6 multi-day models

---

### Priority 3: ZL Training (All Horizons)
**Why Third?** ZL is primary target, but simpler (daily-only)

1. **1w model**
2. **1m model**
3. **3m model**
4. **6m model**
5. **12m model**

**Training Time:** ~4-8 hours per model (mix of tree + neural)
**Total Time:** ~20-40 hours for all 5 ZL models

---

## 🔗 ENSEMBLE STRATEGY

### Intraday Ensemble (1min-4hr)
**Combine 6 neural models:**
```python
intraday_ensemble = MetaLearner(
    models=[
        model_1min,   # LSTM
        model_5min,   # LSTM
        model_15min,  # TCN
        model_30min,  # TCN
        model_1hr,    # CNN-LSTM
        model_4hr     # CNN-LSTM
    ],
    weighting='regime_aware'  # Crisis = weight 1min more, calm = weight 4hr more
)
```

### Multi-Day Ensemble (1d-12m)
**Combine 6 tree models:**
```python
daily_ensemble = MetaLearner(
    models=[
        model_1d,    # LightGBM
        model_7d,    # LightGBM
        model_30d,   # XGBoost
        model_3m,    # LightGBM
        model_6m,    # XGBoost
        model_12m    # LightGBM
    ],
    weighting='regime_aware'  # Crisis = weight 1d more, calm = weight 12m more
)
```

### Cross-Horizon Meta-Learner
**Choose best horizon per regime:**
```python
meta_learner = RegimeRouter(
    regimes={
        'crisis': '1min_model',      # Use 1min in crisis (fast reactions)
        'bull': '1hr_model',         # Use 1hr in bull (momentum)
        'bear': '4hr_model',         # Use 4hr in bear (defensive)
        'normal': '1d_model'          # Use 1d in normal (balanced)
    }
)
```

---

## 📈 DATA VOLUME ESTIMATES

### MES Intraday (Special Training)
- **1min:** ~1.5M rows (390 bars/day × 252 days/year × 15 years)
- **5min:** ~300K rows (78 bars/day × 252 × 15)
- **15min:** ~100K rows (26 bars/day × 252 × 15)
- **30min:** ~50K rows (13 bars/day × 252 × 15)
- **1hr:** ~25K rows (6.5 bars/day × 252 × 15)
- **4hr:** ~6K rows (1.6 bars/day × 252 × 15)

**Total Intraday Data:** ~2M rows

### MES Multi-Day+ (Main Training)
- **1d, 7d, 30d, 3m, 6m, 12m:** ~3.8K rows each (252 days/year × 15 years)

**Total Multi-Day Data:** ~23K rows

### ZL (All Horizons)
- **1w, 1m, 3m, 6m, 12m:** ~3.8K rows each (252 days/year × 15 years)

**Total ZL Data:** ~19K rows

---

## ✅ SUMMARY

### Special Training (Intraday - 6 MES Horizons)
- **What:** 1min, 5min, 15min, 30min, 1hr, 4hr
- **Why Special:** High-frequency microstructure patterns
- **How:** Neural networks (LSTM, TCN)
- **Features:** 150-200 micro features
- **Hardware:** FP16 mixed precision (Metal GPU)
- **Time:** ~12-18 days total

### Main Training (Multi-Day+ - 6 MES + 5 ZL Horizons)
- **What:** MES (1d, 7d, 30d, 3m, 6m, 12m) + ZL (1w, 1m, 3m, 6m, 12m)
- **Why Main:** Daily aggregates, macro/fundamental drivers
- **How:** Tree models (LightGBM, XGBoost)
- **Features:** 200-300 macro/fundamental features
- **Hardware:** CPU (no GPU needed)
- **Time:** ~32-64 hours total

### How They Combine
1. **Feature Engineering:** Intraday → daily aggregation → multi-day
2. **Model Selection:** Neural for intraday, tree for multi-day
3. **Ensemble:** Meta-learner routes by regime
4. **Shared Data:** Macro, regimes, policy (both ZL and MES use)
5. **Separate Data:** ZL-specific (crush, palm) vs. MES-specific (microstructure, equity)

---

**STATUS:** Complete reference document  
**NEXT:** Begin special training (intraday) first, then main training (multi-day+)

