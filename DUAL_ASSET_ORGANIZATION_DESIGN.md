# Dual-Asset Organization Design (ZL + MES)
**Date:** November 18, 2025  
**Status:** RESEARCH - NO EXECUTION  
**Questions:** How to organize for 2 primary targets, shared vs. separate data, intraday training, meta-learning

---

## 🎯 QUESTION 1: How to Organize for Two Primary Targets?

### Industry Pattern: SHARED + ASSET-SPECIFIC Architecture

```
/TrainingData/
│
├── 📁 shared/                           ← Data used by BOTH ZL and MES
│   ├── macro/
│   │   ├── fred_economic.parquet        ← Used by both
│   │   ├── vix_volatility.parquet       ← Used by both
│   │   └── fx_rates.parquet             ← Used by both
│   │
│   ├── market_regime/
│   │   ├── regime_calendar.parquet      ← Shared regime classification
│   │   ├── volatility_regime.parquet
│   │   └── policy_regime.parquet
│   │
│   ├── intelligence/
│   │   ├── news_sentiment.parquet       ← Macro news affects both
│   │   ├── policy_events.parquet        ← Trade/macro policy affects both
│   │   └── hidden_relationships.parquet
│   │
│   └── cross_asset/
│       ├── correlations.parquet         ← ZL-MES correlation tracking
│       └── regime_transitions.parquet
│
├── 📁 ZL/                               ← ZL-SPECIFIC (Soybean Oil)
│   ├── raw/
│   │   ├── databento_ZL/               ← ZL futures only
│   │   ├── yahoo_ZL_F/                 ← ZL historical only
│   │   └── continuous_contracts/
│   │
│   ├── features/
│   │   ├── zl_specific/
│   │   │   ├── crush_oilshare/         ← Only relevant for ZL
│   │   │   ├── soybean_complex/        ← ZS, ZM relationships
│   │   │   ├── palm_substitution/      ← Palm oil competition
│   │   │   ├── biofuel_demand/         ← Biodiesel, RINs
│   │   │   ├── usda_soy/               ← Soybean-specific USDA
│   │   │   ├── weather_soy_belt/       ← US/Brazil/Argentina soy weather
│   │   │   └── china_soy_demand/       ← China soy imports
│   │   │
│   │   └── master_features/
│   │       └── ZL_master_2000_2025.parquet  ← Shared + ZL-specific
│   │
│   ├── training/
│   │   └── by_horizon/
│   │       ├── 1w/ ... 1m/ ... 3m/ ... 6m/ ... 12m/
│   │
│   ├── models/
│   │   └── by_horizon/
│   │
│   └── predictions/
│       └── by_horizon/
│
└── 📁 MES/                              ← MES-SPECIFIC (Micro E-mini S&P 500)
    ├── raw/
    │   ├── databento_MES/              ← MES futures only
    │   │   ├── tick/                   ← Tick-by-tick
    │   │   ├── 1min/                   ← 1-minute bars
    │   │   ├── trades/                 ← Trade data
    │   │   ├── quotes_tbbo/            ← Top of book
    │   │   └── depth_mbp10/            ← Market by price (10 levels)
    │   │
    │   └── es_reference/               ← ES for comparison
    │
    ├── features/
    │   ├── mes_specific/
    │   │   ├── microstructure/         ← Only relevant for MES
    │   │   │   ├── order_imbalance/
    │   │   │   ├── microprice_deviation/
    │   │   │   ├── trade_aggressor/
    │   │   │   ├── quote_intensity/
    │   │   │   └── depth_metrics/
    │   │   ├── intraday_patterns/
    │   │   │   ├── opening_auction/
    │   │   │   ├── lunch_hour/
    │   │   │   └── close_patterns/
    │   │   ├── equity_specific/
    │   │   │   ├── earnings_proximity/
    │   │   │   ├── index_rebalancing/
    │   │   │   └── dividend_effects/
    │   │   └── risk_metrics/
    │   │       ├── vix_relationship/
    │   │       └── sector_rotation/
    │   │
    │   └── master_features/
    │       ├── by_timeframe/
    │       │   ├── MES_1min_features.parquet    ← Micro features
    │       │   ├── MES_5min_features.parquet
    │       │   ├── MES_15min_features.parquet
    │       │   ├── MES_30min_features.parquet
    │       │   ├── MES_1hr_features.parquet
    │       │   ├── MES_4hr_features.parquet
    │       │   └── MES_daily_features.parquet   ← Aggregated features
    │       └── MES_master_intraday_2010_2025.parquet
    │
    ├── training/
    │   └── by_horizon/
    │       ├── intraday_micro/          ← 1min, 5min, 15min, 30min
    │       ├── intraday_macro/          ← 1hr, 4hr
    │       ├── daily/                   ← 1d, 7d, 30d
    │       └── monthly/                 ← 3m, 6m, 12m
    │
    ├── models/
    │   ├── neural_intraday/             ← LSTM, TCN for micro timeframes
    │   ├── tree_daily/                  ← LightGBM for daily+
    │   └── meta_learner/                ← Meta-learning models
    │
    └── predictions/
        └── by_horizon/
            └── ... (12 horizons)
```

---

## 🎯 QUESTION 2: How to Share Datasets but Keep Separate?

### Solution: LAYERED COMPOSITION Pattern

**Layer 1: Shared Foundation** (Used by both ZL and MES)
```
shared/
├── macro/
│   ├── fred_rates.parquet              ← Affects both
│   ├── fed_policy.parquet              ← Affects both
│   └── dollar_index.parquet            ← Affects both
│
├── volatility/
│   ├── vix_daily.parquet               ← Risk-off affects both
│   └── volatility_regime.parquet       ← Shared regime
│
├── intelligence/
│   ├── macro_news.parquet              ← Fed, trade policy
│   └── geopolitical_events.parquet     ← War, elections
│
└── regimes/
    └── global_regime_calendar.parquet  ← Crisis, bull, bear, normal
```

**Layer 2: ZL-Specific** (ZL only, never MES)
```
ZL/
├── zl_specific_raw/
│   ├── crush_margins.parquet           ← ZL only
│   ├── palm_oil_prices.parquet         ← ZL substitution
│   ├── biodiesel_production.parquet    ← ZL demand
│   ├── soybean_complex.parquet         ← ZS, ZM
│   ├── china_soy_imports.parquet       ← ZL specific
│   └── brazil_argentina_weather.parquet ← ZL crop weather
│
└── zl_specific_regimes/
    └── biofuel_policy_regime.parquet   ← ZL-specific regime
```

**Layer 3: MES-Specific** (MES only, never ZL)
```
MES/
├── mes_specific_raw/
│   ├── es_futures.parquet              ← ES reference
│   ├── spx_index.parquet               ← Underlying index
│   ├── sector_etfs.parquet             ← XLF, XLE, etc.
│   ├── earnings_calendar.parquet       ← Equity-specific
│   └── microstructure/
│       ├── order_book_1min.parquet     ← Depth data
│       ├── trades_tick.parquet         ← Trade-by-trade
│       └── quotes_tbbo.parquet         ← Top of book
│
└── mes_specific_regimes/
    └── equity_market_regime.parquet    ← Bull/bear for equities
```

**Composition in Code:**
```python
# For ZL training
zl_features = (
    load_shared_macro()           # Shared layer
    + load_shared_volatility()    # Shared layer  
    + load_zl_specific_crush()    # ZL-only layer
    + load_zl_specific_weather()  # ZL-only layer
)

# For MES training
mes_features = (
    load_shared_macro()           # Shared layer (SAME DATA)
    + load_shared_volatility()    # Shared layer (SAME DATA)
    + load_mes_specific_micro()   # MES-only layer
    + load_mes_specific_equity()  # MES-only layer
)
```

**Benefit:** 
- Shared data stored once (FRED, VIX, etc.)
- Asset-specific data isolated
- Easy to maintain
- Clear what's shared vs. unique

---

## 🎯 QUESTION 3: Micro-Training on Hyper Sets for Lower Timeframes

### Pattern: TIMEFRAME-SPECIFIC FEATURE SETS

**Problem:** MES 1-minute model needs DIFFERENT features than MES 1-month model

**Solution:** Organize by timeframe granularity

```
MES/features/by_timeframe/
│
├── 📁 micro_1min/                       ← INTRADAY MICRO (1min)
│   ├── microstructure/
│   │   ├── order_imbalance_1min.parquet
│   │   ├── microprice_deviation_1min.parquet
│   │   ├── spread_1min.parquet
│   │   ├── depth_imbalance_1min.parquet
│   │   └── trade_flow_1min.parquet
│   │
│   ├── technical_micro/
│   │   ├── rsi_1min.parquet
│   │   ├── vwap_deviation_1min.parquet
│   │   └── volume_intensity_1min.parquet
│   │
│   └── master_features_1min.parquet     ← 150-200 micro features
│       Features: order_imbalance, microprice, spread, depth, flow,
│                 vwap, volume_intensity, NO macro, NO fundamentals
│
├── 📁 micro_5min/                       ← INTRADAY MICRO (5min)
│   └── master_features_5min.parquet     ← Aggregated from 1min
│
├── 📁 micro_15min/                      ← INTRADAY MICRO (15min)
│   └── master_features_15min.parquet
│
├── 📁 micro_30min/                      ← INTRADAY MICRO (30min)
│   └── master_features_30min.parquet
│
├── 📁 macro_1hr/                        ← INTRADAY MACRO (1hr)
│   ├── microstructure/                  ← Still has micro features
│   ├── macro_snapshots/                 ← START adding macro
│   │   ├── vix_hourly.parquet
│   │   └── fx_hourly.parquet
│   └── master_features_1hr.parquet      ← 180-220 features (micro + some macro)
│
├── 📁 macro_4hr/                        ← INTRADAY MACRO (4hr)
│   └── master_features_4hr.parquet      ← 200-250 features (more macro)
│
├── 📁 daily/                            ← MULTI-DAY (1d, 7d, 30d)
│   ├── microstructure_aggregated/       ← Daily aggregates of micro
│   ├── fundamentals/                    ← NOW add fundamentals
│   │   ├── earnings.parquet
│   │   └── economic_releases.parquet
│   └── master_features_daily.parquet    ← 250-300 features (micro agg + macro + fundamentals)
│
└── 📁 monthly/                          ← MULTI-MONTH (3m, 6m, 12m)
    └── master_features_monthly.parquet  ← 200-250 features (mostly macro + fundamentals, less micro)
```

**Feature Count by Timeframe:**
- **1min-30min (micro):** 150-200 features (90% microstructure, 10% technical)
- **1hr-4hr (transitional):** 180-250 features (60% microstructure, 30% macro, 10% technical)
- **1d-30d (daily):** 250-300 features (30% micro aggregates, 50% macro, 20% fundamentals)
- **3m-12m (monthly):** 200-250 features (10% micro, 40% macro, 50% fundamentals)

**Training Strategy:**
```python
# 1-minute model
train_1min_model(
    features=load_micro_features_1min(),  # 150-200 micro features
    architecture="LSTM",                  # Neural net for intraday
    batch_size=32,                        # Small batches
    sequence_length=60                    # Last 60 minutes
)

# 1-month model
train_1m_model(
    features=load_monthly_features(),     # 200-250 macro/fundamental
    architecture="LightGBM",              # Tree model for long horizon
    n_estimators=1000
)
```

---

## 🎯 QUESTION 4: Meta-Learning (Learn to Learn)

### Pattern: MAML-Style Meta-Learning for Time Series

**Concept:** Train a model that can QUICKLY ADAPT to new regimes with minimal data

**Organization for Meta-Learning:**
```
/TrainingData/meta_learning/
│
├── 📁 meta_training_tasks/              ← Each regime = one "task"
│   ├── task_001_trump_2023_2025/
│   │   ├── support_set.parquet          ← Small sample for adaptation
│   │   └── query_set.parquet            ← Test adaptation
│   │
│   ├── task_002_trade_war_2017_2019/
│   │   ├── support_set.parquet
│   │   └── query_set.parquet
│   │
│   ├── task_003_crisis_2008/
│   │   ├── support_set.parquet
│   │   └── query_set.parquet
│   │
│   └── ... (11 tasks = 11 regimes)
│
├── 📁 meta_model/
│   ├── base_model.keras                 ← Meta-learned initialization
│   ├── adaptation_parameters/
│   │   ├── learning_rate.yaml
│   │   └── adaptation_steps.yaml
│   └── performance/
│       └── few_shot_performance.csv     ← How well it adapts
│
└── 📁 regime_adaptation/
    ├── new_regime_detected/
    │   ├── regime_signature.parquet     ← New regime characteristics
    │   ├── adaptation_data.parquet      ← Last 30 days
    │   └── adapted_model.keras          ← Fine-tuned from meta-model
    │
    └── adaptation_history/
        └── all_adaptations.csv
```

**Meta-Learning Process:**
```python
# Step 1: Meta-Training (Train on 11 regimes)
for regime in all_regimes:
    support_data = load_regime_support_set(regime)   # Small sample
    query_data = load_regime_query_set(regime)       # Test sample
    
    # Inner loop: Adapt to regime
    adapted_model = meta_model.clone()
    adapted_model.fit(support_data, epochs=5)
    
    # Outer loop: Update meta-model to adapt faster
    loss = adapted_model.evaluate(query_data)
    meta_model.update_from_loss(loss)

# Step 2: When New Regime Detected
new_regime_data = load_last_30_days()  # Only 30 days!
adapted_model = meta_model.clone()
adapted_model.fit(new_regime_data, epochs=5)  # Quick adaptation
# Now adapted_model is tuned for new regime
```

**Key Files:**
1. `meta_training_tasks/` - One folder per regime (11 total)
2. `meta_model/base_model.keras` - The "learn to learn" model
3. `regime_adaptation/` - Quick fine-tuning when regime shifts

**Benefit:**
- NEW regime detected? Adapt in 5 epochs (not 100)
- Uses 30 days of data (not 5 years)
- Fast to production (hours, not weeks)

---

## 🎯 COMPLETE DUAL-ASSET ARCHITECTURE

```
/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/
│
├── 📁 SHARED/                           ← LAYER 0: Both assets use this
│   ├── macro/
│   │   ├── fred/
│   │   ├── vix/
│   │   └── fx/
│   ├── regimes/
│   │   ├── global_regime_calendar.parquet
│   │   ├── volatility_regime.parquet
│   │   └── policy_regime.parquet
│   └── intelligence/
│       ├── macro_news/
│       └── policy_events/
│
├── 📁 ZL/                               ← LAYER 1: Soybean Oil (Primary)
│   ├── raw/
│   │   ├── databento_ZL/
│   │   ├── yahoo_ZL_F/
│   │   ├── crush_margins/
│   │   ├── palm_oil/
│   │   ├── biodiesel/
│   │   ├── usda_soy/
│   │   ├── china_soy/
│   │   └── weather_soy/
│   │
│   ├── features/
│   │   ├── zl_specific/               ← Crush, palm, biodiesel, weather
│   │   └── master_features/
│   │       └── ZL_master_2000_2025.parquet  ← Shared + ZL features
│   │
│   ├── regimes/
│   │   └── biofuel_policy_regime.parquet    ← ZL-specific regime
│   │
│   ├── training/
│   │   ├── by_horizon/                ← 5 horizons (1w, 1m, 3m, 6m, 12m)
│   │   │   ├── 1w/
│   │   │   │   ├── train/
│   │   │   │   │   ├── all_regimes.parquet
│   │   │   │   │   └── by_regime/
│   │   │   │   │       ├── regime=trump_2023_2025/
│   │   │   │   │       └── ... (11 regimes)
│   │   │   │   ├── validation/
│   │   │   │   └── walk_forward_folds/
│   │   │   │       ├── fold_001/
│   │   │   │       └── ... (60 folds)
│   │   │   └── ... (1m, 3m, 6m, 12m)
│   │   │
│   │   └── by_regime/                 ← 11 regimes
│   │       └── ... (each regime × 5 horizons)
│   │
│   ├── models/
│   │   ├── baselines/                 ← ARIMA, Prophet, LightGBM, XGBoost
│   │   ├── advanced/                  ← TCN, LSTM, attention
│   │   ├── regime_specific/           ← Per-regime models
│   │   └── meta_learner/              ← Meta-learning model
│   │
│   ├── predictions/
│   │   ├── point/
│   │   └── quantiles/
│   │
│   └── performance/
│       ├── sharpe_tracking/
│       ├── shap_values/
│       └── monte_carlo/
│
└── 📁 MES/                              ← LAYER 2: Micro E-mini (Secondary/Hidden)
    ├── raw/
    │   ├── databento_MES/
    │   │   ├── tick/
    │   │   ├── 1min/
    │   │   ├── trades/
    │   │   ├── quotes/
    │   │   └── depth/
    │   │
    │   ├── equity_specific/
    │   │   ├── earnings/
    │   │   ├── sector_rotation/
    │   │   └── index_rebalancing/
    │   │
    │   └── microstructure_raw/
    │       ├── order_flow/
    │       └── liquidity/
    │
    ├── features/
    │   ├── by_timeframe/              ← CRITICAL: Different features per timeframe
    │   │   ├── 1min/
    │   │   │   └── micro_features_150.parquet    ← 150 micro features
    │   │   ├── 5min/
    │   │   ├── 15min/
    │   │   ├── 30min/
    │   │   ├── 1hr/
    │   │   ├── 4hr/
    │   │   ├── 1d/
    │   │   │   └── daily_features_250.parquet    ← 250 features (micro agg + macro)
    │   │   └── ... (12 timeframes)
    │   │
    │   └── master_features/
    │       └── MES_master_by_timeframe.parquet
    │
    ├── training/
    │   └── by_horizon/                ← 12 horizons organized by timeframe type
    │       ├── intraday_micro/        ← Neural nets (LSTM, TCN)
    │       │   ├── 1min/
    │       │   ├── 5min/
    │       │   ├── 15min/
    │       │   └── 30min/
    │       │
    │       ├── intraday_macro/        ← Neural nets
    │       │   ├── 1hr/
    │       │   └── 4hr/
    │       │
    │       ├── multiday/              ← Tree models (LightGBM)
    │       │   ├── 1d/
    │       │   ├── 7d/
    │       │   └── 30d/
    │       │
    │       └── multimonth/            ← Tree models
    │           ├── 3m/
    │           ├── 6m/
    │           └── 12m/
    │
    ├── models/
    │   ├── neural_intraday/           ← For 1min-4hr
    │   │   ├── lstm_1min/
    │   │   ├── tcn_5min/
    │   │   └── ...
    │   │
    │   ├── tree_daily/                ← For 1d-12m
    │   │   ├── lightgbm_1d/
    │   │   └── xgboost_30d/
    │   │
    │   └── meta_learner/              ← Transfer learning across timeframes
    │       ├── base_model.keras
    │       └── adapted_models/
    │           ├── adapted_1min.keras
    │           └── ...
    │
    └── performance/
        ├── by_timeframe/
        │   ├── intraday_metrics/      ← MAPE for 1min-4hr
        │   └── daily_metrics/         ← MAPE for 1d-12m
        └── meta_learning_performance/
```

**Training Data Volume by Timeframe:**

**Micro (1min-30min):**
- Data points: 390 bars/day × 252 days/year × 15 years = ~1.5M rows per timeframe
- Features: 150-200 (microstructure-heavy)
- Model type: Neural (LSTM, TCN)
- Batch size: 32
- Sequence length: 60 bars (1 hour of 1min bars)

**Macro (1hr-4hr):**
- Data points: ~98 bars/day × 252 × 15 = ~370K rows per timeframe
- Features: 180-250 (micro + macro blend)
- Model type: Neural (LSTM, TCN)
- Batch size: 32
- Sequence length: 24 bars (1 day of 1hr bars)

**Daily+ (1d-12m):**
- Data points: 252 days/year × 15 years = ~3.8K rows
- Features: 200-300 (macro + fundamentals heavy)
- Model type: Tree (LightGBM, XGBoost)
- No sequence needed (tabular)

---

## 🎯 META-LEARNING ORGANIZATION (Learn to Learn)

### Implementation Pattern:

```
/meta_learning/
│
├── 📁 meta_training_setup/
│   ├── task_definition/
│   │   ├── regime_tasks/              ← Each regime = one task
│   │   │   ├── trump_2023_2025/
│   │   │   │   ├── support_set_30days.parquet    ← Small sample
│   │   │   │   └── query_set_30days.parquet      ← Test sample
│   │   │   ├── crisis_2008/
│   │   │   └── ... (11 regime tasks)
│   │   │
│   │   └── timeframe_tasks/           ← Each timeframe = one task
│   │       ├── 1min_to_5min_transfer/
│   │       ├── 5min_to_15min_transfer/
│   │       └── ... (transfer between timeframes)
│   │
│   ├── base_models/
│   │   ├── zl_base_metalearner.keras  ← Meta-learned for ZL
│   │   └── mes_base_metalearner.keras ← Meta-learned for MES
│   │
│   └── adaptation_protocols/
│       ├── few_shot_5epoch.yaml
│       └── regime_shift_10epoch.yaml
│
├── 📁 transfer_learning/
│   ├── cross_timeframe/
│   │   ├── 1min_pretrained.keras      ← Pre-trained on 1min
│   │   ├── fine_tuned_for_5min.keras  ← Fine-tuned for 5min
│   │   └── fine_tuned_for_15min.keras
│   │
│   └── cross_regime/
│       ├── general_pretrained.keras    ← Trained on all regimes
│       ├── adapted_crisis.keras        ← Fine-tuned for crisis
│       └── adapted_trump.keras         ← Fine-tuned for Trump era
│
└── 📁 few_shot_learning/
    ├── new_regime_samples/
    │   └── last_30_days.parquet        ← When new regime detected
    │
    └── adapted_models/
        └── quick_adaptation_20251118.keras  ← Adapted in 5 epochs
```

**Meta-Learning Process:**
```python
# STEP 1: Meta-Training (One-time, expensive)
meta_model = build_base_architecture()

for regime_task in all_11_regimes:
    # Inner loop: Adapt quickly to regime
    support_set = load_regime_support(regime_task)  # 30 days only
    query_set = load_regime_query(regime_task)      # Test set
    
    # Clone and adapt
    adapted = meta_model.clone()
    adapted.fit(support_set, epochs=5)  # Just 5 epochs!
    
    # Measure adaptation quality
    loss = adapted.evaluate(query_set)
    
    # Outer loop: Update meta-model to adapt faster
    meta_model.meta_update(loss)

# Save meta-learned model
meta_model.save('zl_base_metalearner.keras')

# STEP 2: Fast Adaptation (When needed)
# New regime detected! (e.g., "Trump 2.0 Tariff War")
new_regime_data = load_last_30_days()  # Only 30 days!

# Clone meta-model
quick_model = load_meta_model('zl_base_metalearner.keras')

# Adapt in just 5 epochs (NOT 100 epochs!)
quick_model.fit(new_regime_data, epochs=5)

# Ready for production in MINUTES, not WEEKS
```

**Benefit:**
- Model "learns how to adapt" during meta-training
- When new regime appears, adapts with tiny data (30 days vs. 5 years)
- Fast to production (hours vs. weeks)
- Performs well even with limited new regime data

---

## 🎯 CROSS-ASSET KNOWLEDGE SHARING

### Pattern: Transfer Learning Between ZL and MES

```
/transfer_learning/
│
├── 📁 shared_representations/
│   ├── macro_encoder.keras            ← Learns macro patterns (used by both)
│   ├── volatility_encoder.keras       ← Learns vol patterns (used by both)
│   └── regime_encoder.keras           ← Learns regime patterns (used by both)
│
├── 📁 ZL_specific/
│   ├── zl_head.keras                  ← ZL-specific prediction head
│   └── zl_fine_tuned.keras            ← Full ZL model (shared encoder + ZL head)
│
└── 📁 MES_specific/
    ├── mes_head.keras                 ← MES-specific prediction head
    └── mes_fine_tuned.keras           ← Full MES model (shared encoder + MES head)
```

**Training Process:**
```python
# Step 1: Pre-train shared encoder on ALL data (ZL + MES)
shared_encoder = train_on_macro_features(
    data=load_shared_macro() + load_zl_data() + load_mes_data()
)

# Step 2: Fine-tune for ZL
zl_model = shared_encoder + ZL_prediction_head()
zl_model.fit(zl_specific_data)

# Step 3: Fine-tune for MES  
mes_model = shared_encoder + MES_prediction_head()
mes_model.fit(mes_specific_data)

# Benefit: Shared encoder learns general patterns, heads specialize
```

---

## 📊 STORAGE FOOTPRINT ESTIMATE

### For Full Dual-Asset Setup:

**ZL Data:**
- Raw: ~20 GB (2000-2025, daily)
- Features: ~5 GB
- Training (5 horizons × 11 regimes): ~10 GB
- Models (30-35 models): ~2 GB
- Predictions/SHAP/Sharpe: ~5 GB
- **Total: ~42 GB**

**MES Data:**
- Raw: ~500 GB (2010-2025, 1-minute tick)
- Features (12 timeframes): ~50 GB
- Training (12 horizons): ~30 GB
- Models (35-40 models): ~3 GB
- Predictions/SHAP/Sharpe: ~10 GB
- **Total: ~593 GB**

**Shared Data:**
- Macro (FRED): ~500 MB
- Regimes: ~100 MB
- Intelligence: ~2 GB
- **Total: ~2.6 GB**

**Meta-Learning:**
- Meta-training tasks: ~5 GB
- Meta-models: ~500 MB
- Adaptation history: ~2 GB
- **Total: ~7.5 GB**

**GRAND TOTAL: ~645 GB**

---

## ✅ ANSWERS TO YOUR QUESTIONS

### 1. How to organize for two primary targets?
**Answer:** SHARED folder for common data (macro, regimes, intelligence) + separate ZL/ and MES/ folders for asset-specific data

### 2. How to keep separate but share datasets?
**Answer:** Layered composition - shared data loaded once, combined with asset-specific data at feature engineering time

### 3. How to micro-train on hyper sets for lower timeframes?
**Answer:** Organize by timeframe granularity - 1min gets 150 micro features, 1d gets 250 macro+fundamental features, separate master_features per timeframe

### 4. How to train for it to learn to learn?
**Answer:** Meta-learning setup - train on all 11 regimes as "tasks," model learns to adapt quickly (5 epochs) to new regimes with minimal data

---

**STATUS:** Research complete  
**NEXT:** Design YOUR specific folder structure with all of this  
**WAITING:** Your approval to proceed with design

