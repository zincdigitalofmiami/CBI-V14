# CBI-V14 Master Execution Plan
**Last Updated**: November 12, 2025  
**Status**: Active - 7-Day Institutional System Execution

---

## Current Mission

Train the most accurate ZL (soybean oil) forecasting models possible using local baselines on the Apple M4 Mac mini, then selectively deploy winners to Vertex AI for production predictions.

**Key Principle**: Train everything locally (free iterations), only push to Vertex AI when a model beats existing benchmarks.

---

## Project Architecture

### Two-Track Approach

**Track 1: Production BQML (Active)**
- **Models**: 5 BQML DART models (1w, 1m, 3m, 6m, 12m)
- **Performance**: MAPE 0.7–1.3%, R² > 0.95
- **Location**: `config/bigquery/bigquery-sql/PRODUCTION_HORIZON_SPECIFIC/`
- **Status**: Live, serving predictions
- **Cost**: ~$0.12 per training run

**Track 2: Local Neural Pipeline → Vertex AI (In Progress)**
- **Hardware**: Apple M4 Mac mini (16GB unified memory) + TensorFlow Metal
- **Environment**: `vertex-metal-312` (Python 3.12.6)
- **Models**: 60-70 models (sequential training, memory-managed)
- **Location**: `vertex-ai/` + `src/training/`
- **Status**: Environment ready, Day 1 execution starting
- **Cost**: Free locally, ~$10-15 optional cloud (FinBERT fine-tuning)
- **Constraints**: Sequential training only, FP16 mixed precision mandatory, external SSD for all artifacts

---

## Training Strategy

### Phase 1: Local Baselines (Current Focus)
Run comprehensive baselines locally on full dataset (125+ years):

**Statistical Baselines**:
- ARIMA/Prophet (naive time series)
- Exponential smoothing

**Tree-Based Baselines**:
- LightGBM with DART dropout
- XGBoost with regime weighting

**Neural Baselines**:
- Simple LSTM (1-2 layers)
- GRU with attention
- Feedforward dense networks

**Baseline Datasets**:
1. Full history (125 years) with regime weighting
2. Trump-era only (2023–2025)
3. Crisis periods (2008, 2020)
4. Trade war periods (2017–2019)

### Phase 2: Regime-Aware Training
- Train specialized models per regime
- Use weighting scheme from `MAC_TRAINING_EXPANDED_STRATEGY.md`:
  - Trump 2.0 (2023–2025): weight ×5000
  - Trade War (2017–2019): weight ×1500
  - Inflation (2021–2022): weight ×1200
  - Crisis (2008, 2020): weight ×500–800
  - Historical (<2000): weight ×50

### Phase 3: Horizon-Specific Optimization
For each horizon (1w, 1m, 3m, 6m, 12m):
- Compare all baselines on holdout data
- Select top performer
- Add horizon-specific features
- Fine-tune architecture

### Phase 4: Vertex AI Deployment
- Export winners as SavedModels
- Upload to Vertex AI Model Registry
- Deploy endpoints only for models beating BQML benchmarks

---

## Data Strategy

### Primary Datasets

**Trump-Era Training Table**:
- Table: `cbi-v14.models_v4.trump_rich_2023_2025`
- Features: 42 neural drivers
- Rows: 782 (2023–2025)
- Export: `TrainingData/exports/trump_rich_2023_2025.parquet`

**Extended Feature Catalog** (all 5 horizons):
- Tables: 
  - `cbi-v14.models_v4.production_training_data_1w`
  - `cbi-v14.models_v4.production_training_data_1m`
  - `cbi-v14.models_v4.production_training_data_3m`
  - `cbi-v14.models_v4.production_training_data_6m`
  - `cbi-v14.models_v4.production_training_data_12m`
- Features: 290+ production features
- Exports: `TrainingData/exports/production_training_data_{1w|1m|3m|6m|12m}.parquet`

**Full Historical Dataset** (for regime baselines):
- Tables: `cbi-v14.forecasting_data_warehouse.*`
- Features: All available drivers
- Timespan: 100–125 years
- Export: `TrainingData/raw/historical_full.parquet`

### Regime Segmentation
Create separate exports for:
- `trump_2.0_2023_2025.parquet` (weight ×5000)
- `trade_war_2017_2019.parquet` (weight ×1500)
- `inflation_2021_2022.parquet` (weight ×1200)
- `crisis_2008_2020.parquet` (weight ×500)
- `historical_pre2000.parquet` (weight ×50)

---

## Success Metrics

### Baseline Requirements (Realistic for M4 16GB)
| Metric | Target | Hardware Constraint | Notes |
|--------|--------|---------------------|-------|
| Ensemble MAPE | < 1.5% | Sequential training | Walk-forward validated, 60-70 models |
| Regime detection | > 95% accuracy | LightGBM CPU | Crisis/bull/bear/normal classifier |
| Volatility forecast | < 0.5% MAE | Small models | GARCH + 1 neural model |
| SHAP coverage | > 80% variance | Batch inference | Factor attribution |
| Model count | 60-70 | FP16 sequential | Trees first, nets second, meta last |
| NLP | Inference-only | Pre-trained FinBERT | Fine-tuning requires cloud |
| Memory management | Mandatory | 16GB unified | FP16, session cleanup, external SSD |
| Training strategy | Sequential | One GPU job at a time | Prevent thermal throttling |
| Batch sizes | Optimized | LSTM ≤32, TCN ≤32, Attention ≤16 | Memory-constrained |

### Promotion Criteria (Vertex AI)
A model qualifies for Vertex AI deployment if:
1. Beats BQML MAPE by ≥10% on holdout data
2. R² > 0.95 consistently across validation windows
3. SHAP explanations align with known market dynamics
4. No data leakage (verified via time-based splits)
5. Passes monotonic constraint validation
6. Passes walk-forward validation (60+ iterations)
7. Regime detection accuracy > 95%

---

## File Organization

### Training Scripts
- `src/training/baselines/` - Statistical/tree/simple neural baselines
- `src/training/regime_classifier.py` - Automatic regime detection
- `src/training/regime_models.py` - Crisis/bull/bear/normal specialists
- `src/training/walk_forward_validation.py` - True out-of-sample testing
- `vertex-ai/training/` - Advanced neural architectures

### Prediction & Monitoring
- `src/prediction/shap_explanations.py` - Factor attribution per prediction
- `src/prediction/ensemble_predictor.py` - Regime-aware ensemble
- `src/prediction/uncertainty_quantification.py` - Conformal prediction
- `src/prediction/news_impact_model.py` - FinBERT NLP integration
- `src/prediction/feature_drift_tracker.py` - Importance drift detection
- `scripts/daily_model_validation.py` - Predictions vs actuals
- `scripts/performance_alerts.py` - Email alerts on degradation
- `scripts/correlation_monitoring.py` - Correlation breakdown detection

### Analysis & Backtesting
- `src/analysis/backtesting_engine.py` - Strategy validation
- `src/api/explain.py` - SHAP explanations (dev tool)
- `src/api/backtest.py` - Strategy backtesting (dev tool)
- `src/api/validate.py` - Daily model validation (dev tool)
- `src/api/monitoring.py` - Performance tracking (dev tool)
- `src/deployment/ab_testing.py` - Shadow mode deployment

### Production Dashboard APIs
- `dashboard-nextjs/app/api/forecast/[horizon]/route.ts` - Production predictions
- `dashboard-nextjs/app/api/market/intelligence/route.ts` - Real-time signals
- `dashboard-nextjs/app/api/predictions/route.ts` - All horizons
- `dashboard-nextjs/app/api/regime/current/route.ts` - Regime detection

### Trained Models
- `Models/local/baselines/` - Local baseline artifacts
- `Models/local/{horizon}/` - Horizon-specific models
- `Models/vertex-ai/` - SavedModels for Vertex deployment
- `Models/mlflow/` - MLflow experiment tracking

### Training Data
- `TrainingData/raw/` - Raw exports from BigQuery
- `TrainingData/processed/` - Preprocessed/engineered features
- `TrainingData/exports/` - Ready-to-train Parquet files

### Documentation
- `active-plans/` - This file + related execution plans
- `docs/training/` - Training reports, analysis
- `docs/data/` - Data manifests, schemas

---

## Current Execution Plans (Reference)

1. **VERTEX_AI_TRUMP_ERA_PLAN.md** - Vertex AI AutoML + neural pipeline architecture
2. **TRUMP_ERA_EXECUTION_PLAN.md** - BQML DART production training
3. **MAC_TRAINING_SETUP_PLAN.md** - M4 Mac setup and environment
4. **MAC_TRAINING_EXPANDED_STRATEGY.md** - Multi-model ensemble strategy
5. **MASTER_EXECUTION_PLAN.md** - This file (overview)

---

## 7-Day Institutional Production System Execution Plan

**Timeline**: 65 hours over 7 days (9-10 hours/day)  
**Goal**: Complete institutional-grade forecasting system with zero deferrals

---

### Day 1: Foundation & Data Quality (6 hours)

**Morning (3h)**: Reorganization & Data Exports
- ✅ Commit repository reorganization (622 files)
- **Data quality validation BEFORE exports** - catch bad data early
- Export `trump_rich_2023_2025.parquet` (42 features, 782 rows)
- Export all 5 `production_training_data_{1w|1m|3m|6m|12m}.parquet` (290 features)
- Export full historical dataset (125 years) with regime labels
- Export 5 regime-specific datasets (trump_2.0, trade_war, inflation, crisis, historical)

**Afternoon (3h)**: Infrastructure Setup
- Configure MLflow tracking → `Models/mlflow/`
- **Set up Metal GPU acceleration** (enables all training)
- Create experiment structure (baselines_statistical, baselines_tree, baselines_neural, regime_models)
- Test GPU + logging with dummy run

**Scripts Created**:
- `scripts/data_quality_checks.py` - validate before training
- `scripts/export_training_data.py` - automated exports

**Deliverable**: Clean repo committed, all data exported, GPU + MLflow operational

---

### Day 2: Baselines + Volatility (7 hours)

**Setup (15min)**: GPU Optimization + Memory Management
- Enable Metal GPU with FP16 mixed precision (MANDATORY for 16GB RAM)
- Configure gradient checkpointing and memory cleanup
- Set batch sizes: Trees unlimited, LSTM ≤64, attention ≤16
- External SSD for all checkpoints/logs

**Track A (2h)**: Statistical Baselines (CPU, sequential)
- ARIMA/Prophet on 1w, 1m, 3m (Day 2)
- Complete 6m, 12m on Day 4 (stagger to avoid heat)
- Log to MLflow: MAPE, R², residuals
- Count: 10-12 statistical models

**Track B (2h)**: Tree-Based Baselines (CPU, 8-10 threads)
- LightGBM DART: 3-4 configs per horizon, 1w/1m/3m first
- XGBoost DART: 2 configs per horizon
- Complete 6m/12m on Day 4
- Count: 8-10 tree models (Day 2), 4-6 more (Day 4)

**Track C (1.5h)**: Simple Neural Baselines (GPU, sequential)
- 1-layer LSTM, 1-layer GRU, Feedforward Dense
- Train 1w, 1m only on Day 2 (test Metal performance)
- Complete 3m/6m/12m on Day 3-4
- Clear Keras session after each model (memory management)
- Count: 6 simple neural (Day 2), 9 more (Days 3-4)

**Track D (1h)**: Volatility Forecasting
- GARCH (statsmodels, fast)
- 1 neural volatility model (lightweight)
- Count: 2 volatility models

**Scripts Created**:
- `src/training/baselines/statistical.py` (with caching)
- `src/training/baselines/tree_models.py` (with memory limits)
- `src/training/baselines/neural_baseline.py` (FP16, session cleanup)
- `src/training/baselines/volatility_model.py`

**Deliverable**: 20 baseline models started (complete remainder Days 3-4), volatility forecasts available

**Memory Management**: Clear sessions, one GPU job at a time, monitor Activity Monitor

---

### Day 3: Advanced Models + Regime Detection + Backtesting (11 hours)

**Morning (5h)**: Advanced Neural Architectures (REALISTIC for 16GB)
- **Core architectures** (train 10-15 total, not 20-30):
  - 2-layer LSTM (2-3 variants, units 64-128)
  - 2-layer GRU (2-3 variants)
  - TCN (1-2 variants, kernel_size 3-5)
  - CNN-LSTM hybrid (1-2 variants)
  - Optional: 1-2 TINY attention (heads ≤4, d_model ≤256, seq_len ≤256)
- **Cut:** Heavy Transformers, multi-head attention >4, bidirectional LSTM
- **Strategy:** Train SEQUENTIALLY, clear Keras sessions, FP16 mixed precision
- **Batch sizes:** LSTM ≤32, TCN ≤32, attention ≤16
- **Focus:** 1w, 1m, 3m horizons (complete 6m/12m Day 4)
- Use Keras Tuner with RandomSearch (not Bayesian - too slow)
- Count: 10-12 advanced models

**Afternoon (6h)**: Critical Infrastructure
- **Regime classifier** (1h) - LightGBM, detect crisis/bull/bear/normal
- **Regime-specific models** (3h) - TOP 2-3 architectures per regime (not all)
  - Crisis regime: 2-layer LSTM + GRU (most important for risk)
  - Bull/Bear/Normal: 1 architecture each
  - Count: 8-10 regime models (not 20)
- **Walk-forward validation** (2h) - 60-iteration out-of-sample test
- **Backtesting engine** (2h) - procurement strategy validation
- Document winners

**Scripts Created**:
- `src/training/baselines/neural_advanced.py` (FP16, memory cleanup)
- `src/training/regime_classifier.py` - LightGBM classifier
- `src/training/regime_models.py` - selective regime specialists
- `src/training/walk_forward_validation.py`
- `src/analysis/backtesting_engine.py`

**Deliverable**: 20-25 models trained (realistic for 16GB), regime detection working, true MAPE known, strategies validated

**Overnight**: Let best models train overnight (2-layer LSTM for 6m/12m)

---

### Day 4: Production Monitoring & Decomposition (9 hours)

**Morning (4h)**: Daily Validation Framework
- `scripts/daily_model_validation.py` - predictions vs actuals
- **Performance decomposition** - MAPE by regime, by move size, by driver
- `scripts/performance_alerts.py` - email if MAPE > 3% or regime-specific failure
- Set up cron for daily runs

**Afternoon (5h)**: Explainability & Monitoring
- `src/prediction/shap_explanations.py` - factor attribution per prediction
- **Feature importance drift tracking** - detect when drivers change
- **Correlation breakdown monitoring** - alert on soy-palm/crude correlation failures
- Integrate with prediction API
- Dashboard endpoints: `/api/explain/{horizon}`, `/api/monitoring/performance`

**Scripts Created**:
- `scripts/daily_model_validation.py`
- `scripts/performance_alerts.py`
- `scripts/correlation_monitoring.py`
- `src/prediction/shap_explanations.py`
- `src/prediction/feature_drift_tracker.py`

**Deliverable**: Production monitoring operational, SHAP + drift tracking live, correlation alerts configured

---

### Day 5: Ensemble + Uncertainty + NLP (9 hours - REVISED)

**Morning (5h)**: Regime-Aware Ensemble
- `config/bigquery/bigquery-sql/ensemble_meta_learner.sql` - dynamic model blending
- **Regime-aware weighting** - crisis = weight 1W more, calm = weight 6M more
- Train LightGBM meta-learner on OOF predictions + regime context
- **Integrate regime classifier** - automatic model switching
- Count: 5 ensemble models (1 per horizon)

**Afternoon (4h)**: Uncertainty + NLP (INFERENCE-ONLY)
- **Uncertainty quantification** (2h) - MAPIE conformal prediction for 90% confidence bands
- **Volatility integration** (1h) - combine volatility forecasts with price forecasts
- **News impact NLP** (1h) - PRE-TRAINED FinBERT inference only (NOT fine-tuned)
  - Use ProsusAI/finbert out-of-box
  - Inference on 551 articles (batch 16, seq_len 128)
  - Generate sentiment features for predictions
  - **Skip:** Fine-tuning (too heavy for 16GB RAM)
  - **Optional:** Fine-tune on Colab Pro (2-hour session, $10)

**Scripts Created**:
- `src/prediction/ensemble_predictor.py` - LightGBM meta-learner
- `src/prediction/uncertainty_quantification.py` - MAPIE
- `src/prediction/news_impact_model.py` - FinBERT inference wrapper
- `config/bigquery/bigquery-sql/ensemble_meta_learner.sql`
- `scripts/correlation_monitoring.py`

**Deliverable**: Ensemble beating individuals, confidence intervals shown, NLP sentiment features (inference-only), correlation monitoring live

**Memory Management**: Keep FinBERT in inference mode only, batch size ≤16

---

### Day 6: Integration + A/B Testing + Backtesting Display (10 hours)

**Morning (5h)**: Complete Dashboard Integration
- Ensemble predictions → main forecast display
- SHAP explanations → "WHY prices moving" section with % contributions
- Confidence intervals → risk bands  
- Volatility forecasts → uncertainty display
- Regime detection → current regime + model selection display
- Daily validation → performance monitoring page
- **A/B testing framework** (30min) - shadow mode deployment for safe model swaps

**Afternoon (5h)**: Testing & Backtesting
- End-to-end testing: data refresh → prediction → explanation → alert
- **Backtest historical strategies** - show Chris what he would have saved
- **Load testing with A/B split** - verify shadow mode works
- Verify all 5 horizons operational
- Test correlation/regime alerts trigger correctly

**Scripts Created**:
- `src/deployment/ab_testing.py` - shadow mode deployment
- `dashboard-nextjs/app/api/monitoring/route.ts` - monitoring endpoints
- `dashboard-nextjs/app/api/backtesting/route.ts` - strategy validation display

**Deliverable**: Fully integrated dashboard, A/B testing ready, backtesting shows strategy ROI

---

### Day 7: Production Deployment & Documentation (6 hours)

**Morning (3h)**: Production Deployment
- Deploy ensemble to production endpoint (with shadow mode)
- Verify automatic retraining triggers work
- Test email alerts for all failure modes
- Verify regime switching operational
- Confirm correlation monitoring alerts

**Afternoon (3h)**: Documentation & Handoff
- Create `docs/training/PHASE_1_RESULTS.md` - metrics, model performance decomposition
- Create `docs/reference/PRODUCTION_PLAYBOOK.md` - operations guide
- Update this file with final results
- Handoff to Chris with capabilities overview

**Deliverable**: Production system live, documented, operational playbook complete

---

## Complete Feature Set (End of Day 7)

| Feature | Implementation | Hardware Realistic | Status |
|---------|---------------|-------------------|--------|
| **Baseline models** | 60-70 models (statistical, tree, neural, regime) | ✅ 16GB capable | ✅ |
| **Ensemble meta-learner** | LightGBM regime-aware blending | ✅ Lightweight | ✅ |
| **Regime detection** | LightGBM crisis/bull/bear/normal classifier | ✅ CPU-friendly | ✅ |
| **Daily validation** | Predictions vs actuals with decomposition | ✅ No GPU needed | ✅ |
| **Performance alerts** | Email if MAPE > 3% or regime failure | ✅ Scripts only | ✅ |
| **SHAP explainability** | Factor attribution per prediction | ✅ Batch inference | ✅ |
| **Feature drift tracking** | Detect importance changes over time | ✅ Lightweight | ✅ |
| **Volatility forecasting** | GARCH + 1 neural model | ✅ Small models | ✅ |
| **Uncertainty quantification** | MAPIE conformal prediction, 90% bands | ✅ Post-processing | ✅ |
| **Correlation monitoring** | Real-time soy-palm/crude breakdown alerts | ✅ Scripts only | ✅ |
| **News impact NLP** | FinBERT inference (pre-trained, NOT fine-tuned) | ✅ Inference-only | ✅ |
| **Backtesting engine** | Validate procurement strategies | ✅ Python only | ✅ |
| **A/B testing** | Shadow mode for safe model deployments | ✅ Logging only | ✅ |
| **Walk-forward validation** | 60-iteration out-of-sample testing | ✅ Sequential | ✅ |

**Optional (Cloud): FinBERT fine-tuning** - 2-hour Colab Pro session ($10), download weights for local inference

---

## API Architecture

### Production Dashboard (Chris-facing)
**Location**: `dashboard-nextjs/app/api/` (TypeScript, deployed on Vercel)

- `forecast/[horizon]/route.ts` - Production predictions from BigQuery
- `market/intelligence/route.ts` - Real-time signals
- `predictions/route.ts` - All horizons
- `regime/current/route.ts` - Regime detection display
- `monitoring/route.ts` - Performance tracking
- `backtesting/route.ts` - Strategy validation display

### Development Tools (Kirk-facing)
**Location**: `src/api/` (Python FastAPI, local server)

- `explain.py` - SHAP factor attribution (dev tool)
- `backtest.py` - Strategy backtesting (dev tool)
- `validate.py` - Daily model validation (dev tool)
- `monitoring.py` - Performance tracking (dev tool)
- `shadow.py` - A/B testing logs

**Communication**: Python scripts write results to BigQuery → Next.js reads them (no runtime dependency)

---

## Key Decisions Documented

**Baseline Approach**: Use full 125-year dataset with regime weighting, NOT just 2023–2025.

**Training Location**: Local M4 Mac mini for all development and baseline work.

**Cloud Usage**: Vertex AI for deployment only, after local validation.

**Model Selection**: Data-driven - promote models that beat benchmarks, not pre-selected architectures.

**Feature Strategy**: Start with 42 neural drivers, expand to 200–500 if baselines warrant it.

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Regime overfitting | Test on multiple regime holdouts |
| Data leakage | Strict time-based splits, no future data |
| Local compute limits | Start with simple models, scale complexity based on results |
| Vertex AI costs | Only deploy validated winners |
| Documentation drift | This file is source of truth, update after each phase |

---

## Project Health Indicators

**Green Flags**:
- ✅ Repository reorganized and clean
- ✅ External drive configured
- ✅ Environment ready (`vertex-metal-312`)
- ✅ BQML production models running
- ✅ Deployment scripts created

**Yellow Flags**:
- ⚠️ Training data exports pending
- ⚠️ Baseline scripts not yet created
- ⚠️ MLflow not configured
- ⚠️ No baseline results yet

**Red Flags** (Production Readiness Gaps - Being Addressed in 7-Day Plan):
- 🚨 No daily validation (predictions vs actuals) → **Day 4**
- 🚨 No performance degradation alerts → **Day 4**
- 🚨 No SHAP explainability for predictions → **Day 4**
- 🚨 No ensemble meta-learner (models don't communicate) → **Day 5**
- 🚨 No automatic retraining triggers → **Day 4**
- 🚨 No prediction uncertainty quantification → **Day 5**
- 🚨 No regime detection → **Day 3**
- 🚨 No volatility forecasting → **Day 2**
- 🚨 No correlation monitoring → **Day 4**
- 🚨 No news impact NLP → **Day 5**
- 🚨 No backtesting engine → **Day 3**
- 🚨 No A/B testing framework → **Day 6**

---

**Review Cadence**: Update this file weekly or after major milestones.

