# How Quant Firms Organize Backend Data Infrastructure
**Date:** November 18, 2025  
**Research:** Industry patterns from hedge funds, banks, systematic traders  
**Status:** RESEARCH - NO EXECUTION

---

## 🏦 INDUSTRY BACKEND PATTERNS (From Research)

### Pattern #1: THREE-TIER SEPARATION (Universal)

**Tier 1: RAW DATA (Immutable)**
```
/data/raw/
├── market/
│   ├── equities/
│   │   ├── tick/              ← Tick-by-tick (kdb+/TimeScaleDB)
│   │   ├── 1min/              ← 1-minute bars (Parquet partitioned by date)
│   │   ├── daily/             ← Daily bars (Parquet partitioned by year/month)
│   │   └── metadata/          ← Corporate actions, splits, dividends
│   ├── futures/
│   │   ├── by_exchange/       ← CME, ICE, Eurex, etc.
│   │   │   ├── CME/
│   │   │   │   ├── ZL/        ← By symbol
│   │   │   │   │   ├── tick/
│   │   │   │   │   ├── 1min/
│   │   │   │   │   └── daily/
│   │   │   │   └── ...
│   │   │   └── ...
│   │   └── continuous/        ← Continuous contracts (back-adjusted)
│   ├── fx/
│   └── crypto/
│
├── fundamentals/
│   ├── economic/
│   │   ├── fred/              ← By provider
│   │   ├── bloomberg/
│   │   └── refinitiv/
│   ├── corporate/
│   │   ├── earnings/
│   │   ├── filings/
│   │   └── estimates/
│   └── commodities/
│       ├── usda/
│       ├── eia/
│       └── cftc/
│
└── alternative/
    ├── sentiment/
    │   ├── news/
    │   ├── social/
    │   └── analyst_ratings/
    ├── satellite/
    └── web_scraping/
```

**Key Principles:**
- NEVER modify raw data
- Append-only writes
- Partitioned by date (year=YYYY/month=MM/day=DD)
- Immutable once written
- Versioned if source changes schema

**Tier 2: FEATURE STORE (Computed)**
```
/data/features/
├── market_features/
│   ├── technical/
│   │   ├── by_asset/
│   │   │   ├── ZL/
│   │   │   │   ├── daily_indicators.parquet    ← RSI, MACD, etc.
│   │   │   │   ├── volatility.parquet
│   │   │   │   └── microstructure.parquet
│   │   │   └── ...
│   │   └── cross_sectional/
│   │       ├── correlations.parquet
│   │       └── relative_strength.parquet
│   │
│   ├── fundamental_features/
│   │   ├── macro/
│   │   ├── commodity_specific/
│   │   └── sentiment/
│   │
│   └── derived/
│       ├── regime_indicators/
│       ├── signals/
│       └── composite_scores/
│
└── master_features/
    ├── by_asset/
    │   ├── ZL_master_2000_2025.parquet         ← THE canonical table
    │   └── MES_master_2010_2025.parquet
    └── by_horizon/
        ├── daily_features.parquet
        └── intraday_features.parquet
```

**Key Principles:**
- Features computed from raw data
- Versioned (v1, v2, etc.)
- Point-in-time correct (no look-ahead bias)
- Documented in feature registry
- Can be regenerated from raw

**Tier 3: MODEL-READY DATA (Training/Inference)**
```
/data/training/
├── by_asset/
│   ├── ZL/
│   │   ├── by_horizon/
│   │   │   ├── 1w/
│   │   │   │   ├── train/
│   │   │   │   │   ├── by_regime/
│   │   │   │   │   │   ├── trump_2023_2025.parquet
│   │   │   │   │   │   ├── crisis.parquet
│   │   │   │   │   │   └── all_regimes.parquet
│   │   │   │   │   └── by_fold/             ← Walk-forward validation
│   │   │   │   │       ├── fold_001.parquet
│   │   │   │   │       ├── fold_002.parquet
│   │   │   │   │       └── ... (60 folds)
│   │   │   │   ├── validation/
│   │   │   │   └── holdout/
│   │   │   └── ... (5 horizons for ZL)
│   │   │
│   │   └── by_regime/
│   │       ├── trump_2023_2025/
│   │       │   ├── all_horizons.parquet
│   │       │   └── by_horizon/
│   │       └── ... (11 regimes)
│   │
│   └── MES/
│       └── by_horizon/
│           ├── 1min/, 5min/, ... (12 horizons)
│
└── metadata/
    ├── regime_calendar.parquet
    ├── regime_weights.parquet
    └── feature_manifest.yaml
```

**Key Principles:**
- One dataset per training job
- Train/validation/holdout splits preserved
- Regime-specific datasets
- Horizon-specific datasets
- Labels (targets) included
- Training weights included

---

## 🎯 REGIME-BASED ORGANIZATION (Critical for Your Setup)

### How Pros Handle Regime Switching:

**Storage Pattern:**
```
/data/regimes/
├── detection/
│   ├── regime_calendar.parquet          ← Date → Regime mapping
│   ├── regime_probabilities.parquet     ← Soft regime assignments
│   └── transition_matrix.parquet        ← Regime transition probs
│
├── parameters/
│   ├── by_regime/
│   │   ├── bull/
│   │   │   ├── mean_returns.yaml
│   │   │   ├── covariance.parquet
│   │   │   └── feature_distributions.parquet
│   │   └── ... (per regime)
│   └── weights/
│       └── training_weights.yaml        ← 50-5000 scale
│
└── models/
    ├── regime_classifier/
    │   ├── model.pkl
    │   ├── features_used.yaml
    │   └── performance.csv
    └── regime_specific_models/
        ├── bull_regime_model.pkl
        ├── bear_regime_model.pkl
        └── ...
```

**What This Enables:**
- Regime detection runs first
- Routes to regime-specific model
- Each regime has own training data
- Regime transitions tracked
- Performance decomposed by regime

---

## 🎯 HORIZON-BASED ORGANIZATION (Critical for Your Setup)

### How Pros Handle Multi-Horizon:

**Storage Pattern:**
```
/data/horizons/
├── 1w/
│   ├── features/
│   │   └── daily_aggregated.parquet     ← Features relevant for 1w forecast
│   ├── targets/
│   │   └── forward_returns_1w.parquet
│   ├── predictions/
│   │   ├── point/
│   │   └── quantiles/
│   │       ├── p10.parquet
│   │       ├── p50.parquet
│   │       └── p90.parquet
│   └── validation/
│       ├── walk_forward_folds/
│       ├── mape_by_date.csv
│       └── sharpe_tracking.csv
│
├── 1m/ ... (same structure)
├── 3m/ ... (same structure)
└── ... (17 horizons total)
```

**What This Enables:**
- Horizon-specific feature engineering
- Horizon-specific models
- Horizon-specific validation
- Clean separation of concerns

---

## 🎯 MONTE CARLO / BACKTESTING ORGANIZATION

### Industry Pattern:

```
/backtesting/
├── strategies/
│   ├── strategy_001_long_only/
│   │   ├── definition.yaml
│   │   ├── parameters.yaml
│   │   └── rules.py
│   └── ...
│
├── monte_carlo/
│   ├── scenarios/
│   │   ├── base_case/
│   │   │   ├── market_params.yaml
│   │   │   ├── correlation_matrix.parquet
│   │   │   └── volatility_surface.parquet
│   │   ├── bull_regime/
│   │   ├── bear_regime/
│   │   ├── crisis_regime/
│   │   └── custom/
│   │
│   ├── simulations/
│   │   ├── run_20251118_001/
│   │   │   ├── inputs/
│   │   │   ├── paths/              ← 10,000 price paths
│   │   │   │   ├── path_0001.parquet
│   │   │   │   ├── path_0002.parquet
│   │   │   │   └── ...
│   │   │   └── results/
│   │   │       ├── summary_statistics.csv
│   │   │       ├── sharpe_distribution.parquet
│   │   │       └── var_cvar.csv
│   │   └── ...
│   │
│   └── aggregated/
│       ├── strategy_comparison.csv
│       └── regime_performance.csv
│
└── walk_forward/
    ├── folds/
    │   ├── fold_001/
    │   │   ├── train.parquet
    │   │   ├── validation.parquet
    │   │   ├── predictions.parquet
    │   │   └── metrics.csv
    │   └── ... (60 folds)
    │
    └── aggregated/
        ├── out_of_sample_mape.csv
        └── regime_breakdown.csv
```

---

## 🎯 SHAP / EXPLAINABILITY ORGANIZATION

### Industry Pattern:

```
/explainability/
├── shap_values/
│   ├── by_model/
│   │   ├── tcn_1w/
│   │   │   ├── daily/
│   │   │   │   ├── 2025/11/
│   │   │   │   │   ├── shap_2025-11-18.parquet  ← 400 features × SHAP value
│   │   │   │   │   └── ...
│   │   │   │   └── ...
│   │   │   ├── aggregated/
│   │   │   │   ├── feature_importance_monthly.csv
│   │   │   │   ├── feature_importance_by_regime.csv
│   │   │   │   └── top_20_features.csv
│   │   │   └── drift_detection/
│   │   │       └── importance_changes.csv
│   │   └── ...
│   │
│   └── by_horizon/
│       ├── 1w_all_models_shap/
│       └── ...
│
├── feature_importance/
│   ├── historical/
│   │   ├── 2024/
│   │   └── 2025/
│   └── by_regime/
│       ├── trump_2023_2025/
│       └── ...
│
└── interaction_effects/
    ├── pairwise_interactions.parquet
    └── regime_interactions.parquet
```

**What This Tracks:**
- SHAP value for EVERY prediction
- Feature importance over time (drift detection)
- Regime-specific importance
- Interaction effects
- Model behavior explanation

---

## 🎯 SHARPE / PERFORMANCE ORGANIZATION

### Industry Pattern:

```
/performance/
├── sharpe_ratios/
│   ├── by_model/
│   │   ├── tcn_1w_sharpe_history.csv
│   │   ├── lightgbm_1m_sharpe_history.csv
│   │   └── ...
│   │
│   ├── by_horizon/
│   │   ├── 1w/
│   │   │   ├── all_models_comparison.csv
│   │   │   ├── sharpe_over_time.csv
│   │   │   └── regime_decomposition.csv
│   │   └── ...
│   │
│   └── by_regime/
│       ├── trump_2023_2025/
│       │   ├── all_models_sharpe.csv
│       │   └── best_performers.csv
│       └── ...
│
├── mape/
│   ├── by_model/
│   ├── by_horizon/
│   └── by_regime/
│
├── decomposition/
│   ├── sharpe_by_feature_group/
│   ├── sharpe_by_signal/              ← Big 8 signal contribution
│   └── sharpe_by_regime_transition/
│
└── optimization/
    ├── optimal_weights/
    │   ├── by_horizon.csv
    │   └── by_regime.csv
    └── risk_budgets/
```

**What This Tracks:**
- Daily Sharpe by model
- Regime-specific Sharpe
- Feature group contribution to Sharpe
- Signal contribution to Sharpe
- Optimal model weights

---

## 🎯 QUINTILE / QUANTILE ORGANIZATION

### Industry Pattern:

```
/predictions/
├── point_forecasts/
│   ├── by_model/
│   └── by_horizon/
│
├── quantiles/                           ← Probabilistic forecasts
│   ├── by_horizon/
│   │   ├── 1w/
│   │   │   ├── quantile_forecasts/
│   │   │   │   ├── 2025-11-18/
│   │   │   │   │   ├── p05.parquet
│   │   │   │   │   ├── p10.parquet
│   │   │   │   │   ├── p25.parquet
│   │   │   │   │   ├── p50.parquet
│   │   │   │   │   ├── p75.parquet
│   │   │   │   │   ├── p90.parquet
│   │   │   │   │   └── p95.parquet
│   │   │   │   └── ...
│   │   │   └── calibration/
│   │   │       ├── coverage_tests.csv         ← Is 90% interval actually 90%?
│   │   │       └── quantile_loss.csv
│   │   └── ...
│   │
│   └── by_regime/
│       ├── crisis/
│       │   ├── wider_intervals.parquet        ← Crisis = more uncertainty
│       │   └── ...
│       └── ...
│
└── ensemble_quantiles/                  ← Combined from multiple models
    └── final_quantiles/
```

**What This Tracks:**
- 7 quantiles per prediction (P05, P10, P25, P50, P75, P90, P95)
- Calibration (are intervals correct?)
- Regime-specific uncertainty
- Confidence intervals for risk management

---

## 🎯 METADATA / REGISTRY ORGANIZATION (Critical)

### Industry Pattern:

```
/metadata/
├── registries/
│   ├── feature_registry/
│   │   ├── feature_catalog.csv          ← ALL features documented
│   │   │   Columns: feature_name, feature_group, source, calculation,
│   │   │            used_in_models, importance_rank, status, owner
│   │   ├── feature_lineage.yaml         ← raw → processed → feature DAG
│   │   └── deprecated_features.csv
│   │
│   ├── model_registry/
│   │   ├── model_catalog.yaml           ← ALL models documented
│   │   │   - model_id, architecture, hyperparameters, horizon,
│   │   │     regime, training_date, performance, status
│   │   ├── hyperparameters/
│   │   │   ├── tcn_1w_v001.yaml
│   │   │   └── ...
│   │   └── model_lineage.yaml           ← Model evolution tracking
│   │
│   ├── data_registry/
│   │   ├── dataset_catalog.csv
│   │   ├── data_quality_scores.csv
│   │   └── collection_status.yaml
│   │
│   └── experiment_registry/
│       ├── mlflow/                      ← MLflow tracking
│       └── experiments.db
│
├── schemas/
│   ├── raw_data_schemas/
│   ├── feature_schemas/
│   └── training_data_schemas/
│
└── documentation/
    ├── data_dictionaries/
    ├── calculation_specs/
    └── validation_rules/
```

---

## 🎯 PARTITIONING STRATEGY (Performance Critical)

### Time-Based Partitioning (Universal in Quant):

```
# Parquet files partitioned by date
/data/raw/futures/CME/ZL/1min/
├── year=2024/
│   ├── month=11/
│   │   ├── day=01/
│   │   │   └── data.parquet
│   │   ├── day=02/
│   │   └── ...
│   ├── month=10/
│   └── ...
└── year=2025/
```

**Why:**
- Fast date range queries
- Easy to archive old data
- Parallel processing
- Incremental updates

### Regime Partitioning (Your Use Case):

```
/data/training/ZL/by_horizon/1w/
├── regime=trump_2023_2025/
│   └── data.parquet
├── regime=trade_war_2017_2019/
│   └── data.parquet
└── ...
```

**Why:**
- Load only relevant regime data
- Regime-specific model training
- Easy to apply different weights
- Clear performance attribution

---

## 🎯 COMPREHENSIVE BACKEND STRUCTURE (Synthesized)

```
/Volumes/Satechi Hub/Projects/CBI-V14/
│
├── TrainingData/
│   │
│   ├── 📁 raw/                          [TIER 1: Immutable source]
│   │   ├── databento/
│   │   │   ├── historical/
│   │   │   │   └── year=YYYY/month=MM/day=DD/
│   │   │   └── live/
│   │   │       └── year=YYYY/month=MM/day=DD/
│   │   ├── yahoo/
│   │   ├── fred/
│   │   ├── usda/
│   │   ├── eia/
│   │   ├── cftc/
│   │   ├── weather/
│   │   ├── news/
│   │   └── intelligence/
│   │
│   ├── 📁 processed/                    [TIER 2: Cleaned, unified]
│   │   ├── market/
│   │   ├── fundamentals/
│   │   ├── macro/
│   │   ├── intelligence/
│   │   └── weather/
│   │
│   ├── 📁 features/                     [TIER 3: Feature store]
│   │   ├── ZL/
│   │   │   ├── master_features_2000_2025.parquet
│   │   │   ├── technical/
│   │   │   ├── fundamental/
│   │   │   └── intelligence/
│   │   └── MES/
│   │       └── master_features_intraday_2010_2025.parquet
│   │
│   ├── 📁 regimes/                      [Regime infrastructure]
│   │   ├── detection/
│   │   ├── parameters/
│   │   ├── models/
│   │   └── by_regime/
│   │       ├── trump_2023_2025/
│   │       ├── trade_war_2017_2019/
│   │       └── ... (11 regime folders)
│   │
│   ├── 📁 training/                     [TIER 4: Training data]
│   │   ├── ZL/
│   │   │   ├── by_horizon/
│   │   │   │   ├── 1w/
│   │   │   │   │   ├── train/
│   │   │   │   │   │   ├── all_regimes.parquet
│   │   │   │   │   │   └── by_regime/
│   │   │   │   │   │       ├── regime=trump_2023_2025/
│   │   │   │   │   │       └── ...
│   │   │   │   │   ├── validation/
│   │   │   │   │   ├── holdout/
│   │   │   │   │   └── walk_forward_folds/
│   │   │   │   │       ├── fold_001/
│   │   │   │   │       └── ... (60 folds)
│   │   │   │   └── ... (5 horizons)
│   │   │   └── by_regime/
│   │   │       └── ... (11 regimes)
│   │   └── MES/
│   │       └── by_horizon/
│   │           └── ... (12 horizons)
│   │
│   ├── 📁 models/                       [Trained models]
│   │   ├── ZL/
│   │   │   ├── baselines/
│   │   │   ├── advanced/
│   │   │   ├── regime_specific/
│   │   │   └── ensemble/
│   │   └── MES/
│   │
│   ├── 📁 predictions/                  [Model outputs]
│   │   ├── ZL/
│   │   │   ├── point_forecasts/
│   │   │   ├── quantiles/               ← Quintile/quantile predictions
│   │   │   └── by_horizon/
│   │   └── MES/
│   │
│   ├── 📁 backtesting/                  [Simulations & validation]
│   │   ├── monte_carlo/
│   │   │   ├── scenarios/
│   │   │   ├── simulations/
│   │   │   └── results/
│   │   ├── walk_forward/
│   │   └── strategies/
│   │
│   ├── 📁 performance/                  [Metrics tracking]
│   │   ├── sharpe_tracking/             ← Sharpe ratios
│   │   ├── mape_tracking/
│   │   ├── decomposition/
│   │   └── optimization/
│   │
│   ├── 📁 explainability/               [Model interpretation]
│   │   ├── shap_values/                 ← SHAP analysis
│   │   ├── feature_importance/
│   │   ├── drift_detection/
│   │   └── interaction_effects/
│   │
│   └── 📁 metadata/                     [Registries & catalogs]
│       ├── feature_catalog.csv
│       ├── model_registry.yaml
│       ├── experiment_tracking/
│       ├── regime_definitions.yaml
│       └── data_lineage.yaml
```

---

## 🔥 WHAT THIS MEANS FOR YOUR SETUP

**You need to organize for:**

1. **11 Regimes** - Each needs own folder + parameters
2. **17 Horizons** - Each needs own training/validation/prediction data
3. **60-75 Models** - Each needs SHAP values, Sharpe tracking, quantile outputs
4. **60 Walk-Forward Folds** - Per horizon (for validation)
5. **10,000+ Monte Carlo Paths** - Per strategy/scenario
6. **400+ Features** - All documented in feature catalog
7. **Big 8 Signals** - Each signal needs source data organized
8. **Daily Predictions** - Point + 7 quantiles × 17 horizons = 119 files per day

**Current Organization:** ZERO folders for this  
**Required Folders:** ~500+ folders  
**Required Files:** ~100,000+ files when complete

**THIS IS WHY YOUR EXTERNAL DRIVE IS BARE - IT'S NOT SET UP FOR SOPHISTICATED QUANT FORECASTING**

---

**STATUS:** Researched industry patterns  
**NEXT:** Design YOUR specific folder structure incorporating all of this  
**WAITING:** Your approval before designing

