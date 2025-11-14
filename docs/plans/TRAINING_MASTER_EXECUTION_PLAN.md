# CBI-V14 Master Execution Plan
**Last Updated**: November 14, 2025  
**Status**: ✅ Migration Complete - Ready for Training  
**Architecture**: Local-First (Mac M4), No Vertex AI, No BQML Training  
**Data Status**: ✅ **25+ YEARS INTEGRATED** (365% increase in training data)

---

## Current Mission

Train the most accurate ZL (soybean oil) forecasting models possible using **25 years of historical data** (2000-2025) with **regime-based weighting** on Apple M4 Mac mini. All training and inference is 100% local. BigQuery is used for storage only.

**Key Updates (November 2025)**:
- **Historical Data Integrated**: 6,057 rows of soybean oil prices (was 1,301)
- **11 Regime Tables Created**: From historical_pre2000 to trump_2023_2025
- **338K+ Pre-2020 Rows Available**: Full market cycle coverage
- **Migration Complete**: New naming convention (Option 3) implemented
- **Regime Weights Optimized**: Research-based, 50-5000 scale

---

## Project Architecture (November 2025)

### Local-First Training Architecture

**Storage Layer: BigQuery**
- **Purpose**: Data warehouse only (NO training, NO inference)
- **Datasets**: 8 canonical datasets (raw_intelligence, features, training, predictions, monitoring, vegas_intelligence, archive, yahoo_finance_comprehensive)
- **Tables**: 12 training tables using `{asset}_{function}_{scope}_{regime}_{horizon}` naming
- **Status**: ✅ Complete, all tables migrated

**Compute Layer: Mac M4**
- **Hardware**: Apple M4 Mac mini (16GB unified memory) + TensorFlow Metal GPU
- **Environment**: `vertex-metal-312` (Python 3.12.6)
- **Training**: 100% local (baselines, advanced, regime-specific, ensemble)
- **Inference**: 100% local prediction generation
- **Models**: 60-70 total (sequential training, memory-managed)
- **Cost**: $0 (no cloud compute)
- **Constraints**: Sequential training, FP16 mixed precision, external SSD

**Upload Layer: Python Scripts**
- **Export**: `scripts/export_training_data.py` (BigQuery → Parquet)
- **Upload**: `scripts/upload_predictions.py` (Local predictions → BigQuery)
- **Workflow**: Automated, no manual intervention

**UI Layer: Vercel Dashboard**
- **Purpose**: Read-only UI
- **Data Source**: BigQuery only (predictions.vw_zl_{h}_latest)
- **No Dependencies**: On local models or Vertex AI
- **Status**: Active

**NO Vertex AI. NO BQML Training. 100% Local Control.**

---

## Training Strategy

### Phase 1: Local Baselines (Current Focus - Enhanced with Historical Data)
Run comprehensive baselines locally on **expanded 25-year dataset** (2000-2025):

**Statistical Baselines**:
- ARIMA/Prophet (now with 25-year patterns)
- Exponential smoothing (validated on 2008 crisis)

**Tree-Based Baselines**:
- LightGBM with DART dropout (trained on all regimes)
- XGBoost with regime weighting (using new regime tables)

**Regime-Specific Models** (NEW):
- Crisis model (253 rows from 2008)
- Trade War model (754 rows from 2017-2019)
- Recovery model (1,760 rows from 2010-2016)
- Pre-Crisis baseline (1,737 rows from 2000-2007)

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

### Phase 4: Prediction Upload
- Generate predictions locally for all trained models
- Upload to BigQuery via `scripts/upload_predictions.py`
- Create/update `predictions.vw_zl_{horizon}_latest` views
- Dashboard reads from BigQuery (no Vertex AI endpoints)

---

## Data Strategy (November 2025 Update)

### New Naming Convention

**Pattern**: `{asset}_{function}_{scope}_{regime}_{horizon}`

**Components**:
- asset: `zl` (soybean oil)
- function: `training`, `feat`, `commodity`, etc.
- scope: `full` (1,948+ features) or `prod` (~290 features)
- regime: `allhistory`, `trump_2023_2025`, `tradewar_2017_2019`, etc.
- horizon: `1w`, `1m`, `3m`, `6m`, `12m`

### Primary Training Tables (NEW)

**Production Surface** (~290-450 features):
- Tables: `cbi-v14.training.zl_training_prod_allhistory_{1w|1m|3m|6m|12m}`
- Features: 275-449 features (varies by horizon)
- Rows: 1,404-1,475 per table
- Exports: `TrainingData/exports/zl_training_prod_allhistory_{horizon}.parquet`
- Status: ✅ All created and exported

**Full Surface** (1,948+ features):
- Tables: `cbi-v14.training.zl_training_full_allhistory_{1w|1m|3m|6m|12m}`
- Features: All available drivers
- Rows: Same as prod surface
- Status: ✅ Created (placeholders, rebuild pending)

### Regime Support Tables

**Regime Calendar**:
- Table: `cbi-v14.training.regime_calendar`
- Rows: 13,102 (maps every date 1990-2025 to regime)
- Regimes: 11 total (historical_pre2000 → trump_2023_2025)

**Regime Weights** (Research-Optimized):
- Table: `cbi-v14.training.regime_weights`
- Rows: 11 (one per regime)
- Scale: 50-5000 (100x differential)
- Trump era: 5000 (maximum recency bias)
- Historical: 50 (pattern learning only)
- Research: `scripts/migration/REGIME_WEIGHTS_RESEARCH.md`

### Legacy Tables (Archived, Read-Only)

**Archived to** `archive.legacy_20251114__models_v4__*`:
- `production_training_data_{1w|1m|3m|6m|12m}` (5 tables)
- `trump_rich_2023_2025`
- Crisis and regime tables (4 tables)

**Shim views** (temporary, 30-day grace period):
- `models_v4.production_training_data_{horizon}` → points to new tables

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

### Production Promotion Criteria (Dashboard Integration)
A model qualifies for dashboard production use if:
1. Beats reference BQML MAPE by ≥10% on holdout data (BQML: 0.7-1.3%)
2. R² > 0.95 consistently across validation windows
3. SHAP explanations align with known market dynamics
4. No data leakage (verified via time-based splits)
5. Passes monotonic constraint validation
6. Passes walk-forward validation (60+ iterations)
7. Regime detection accuracy > 95%
8. Predictions upload successfully to BigQuery
9. Dashboard can read from `predictions.vw_zl_{horizon}_latest`

**Note**: All models run locally. "Production" = uploaded to BigQuery for dashboard consumption.

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

## Migration Status (November 14, 2025)

### ✅ Completed: Naming Architecture Migration

**Achievement**: Migrated entire system to institutional naming convention (Option 3)

**Phases Complete**:
- Phase 1: Archive (10 tables preserved)
- Phase 2: Datasets (7/7 verified)
- Phase 3: Training Tables (12/12 created with new naming)
- Phase 4: Python Scripts (15/15 updated)
- Phase 6: Shim Views (5/5 backward compatibility)

**Key Deliverables**:
- ✅ New naming: `{asset}_{function}_{scope}_{regime}_{horizon}`
- ✅ Regime weights: 50-5000 (research-optimized)
- ✅ Upload pipeline: `scripts/upload_predictions.py`
- ✅ Documentation: 4 institutional framework documents
- ✅ Architecture: 100% local-first verified

**Documentation**: `docs/migrations/20251114_NAMING_ARCHITECTURE_MIGRATION.md`

### ✅ Completed: Institutional Quant Framework

**Achievement**: Established professional methodology for signal interpretation and forecasting

**Documents Created**:
1. `CONVICTION_VS_CONFIDENCE.md` - Separates directional certainty from forecast precision
2. `SIGNAL_TREATMENT_RULES.md` - 12 institutional guidelines for market signals
3. `CURSOR_MASTER_INSTRUCTION_SET.md` - Mandatory post-move audit protocol
4. `INSTITUTIONAL_FRAMEWORK_INDEX.md` - Central navigation

**Key Insights**:
- Crisis = high conviction (direction) + low confidence (precision)
- Signals must be paired, validated, contextualized
- Post-move audits mandatory (VIX >25, USD/BRL >3%, etc.)

**Documentation**: `docs/reference/` + `INSTITUTIONAL_FRAMEWORK_COMPLETE.md`

---

## 7-Day Institutional Production System Execution Plan

**Timeline**: 65 hours over 7 days (9-10 hours/day)  
**Goal**: Complete institutional-grade forecasting system with zero deferrals  
**Current Status**: Migration complete (Day 0), ready to start Day 1

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

**Scripts Created** (✅ COMPLETE - November 12, 2025):
- `src/training/baselines/train_statistical.py` (ARIMA/Prophet with caching)
- `src/training/baselines/train_tree.py` (LightGBM/XGBoost with memory limits)
- `src/training/baselines/train_simple_neural.py` (LSTM/GRU with FP16, Metal GPU, session cleanup)
- `scripts/build_features.py` (feature engineering pipeline)
- `src/prediction/generate_forecasts.py` (daily forecast generation)
- `src/prediction/shap_explanations.py` (SHAP feature importance)
- `src/analysis/backtesting_engine.py` (procurement strategy validation)
- `scripts/crontab_setup.sh` (updated with ML pipeline automation)

**Deliverable**: ✅ Day 2 baseline training infrastructure complete. Ready to execute 20 baseline models (complete remainder Days 3-4), volatility forecasts available

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

