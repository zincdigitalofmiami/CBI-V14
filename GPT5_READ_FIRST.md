# GPT-5 / FUTURE AI: READ THIS FIRST
**Critical context for all assistants touching CBI-V14**

---

## 🎯 Current Architecture (November 17, 2025)
- Apple M4 Mac handles every training and inference task (TensorFlow Metal + PyTorch MPS + CPU tree libs).
- BigQuery = storage plus dashboard read layer only; no BigQuery ML, no AutoML jobs.
- Predictions generated locally, uploaded with `scripts/upload_predictions.py`, then read by the Vercel dashboard.
- The `vertex-ai/` directory is kept for reference. See `vertex-ai/LEGACY_MARKER.md`. Do **not** run anything in there.
- First-run models save to `Models/local/.../{model}` without version suffix. Pass an explicit `version` only when promoting a later retrain.
- **ZL = Soybean Oil Futures** (CBOT ticker) - NOT corn. Primary commodity for single-asset baseline.

### Architecture Pattern: Hybrid Python + BigQuery SQL
**Data Collection**: Python scripts → External drive (`/Volumes/Satechi Hub/`) + BigQuery  
**Feature Engineering**: HYBRID approach (already in use):
  - BigQuery SQL: Correlations (CORR() OVER window), moving averages, regimes (existing in `advanced_feature_engineering.sql`)
  - Python: Complex sentiment, NLP, policy extraction, interactions (existing in `feature_calculations.py`)
  - **Both are used** - this is the production pattern

### Data Sources (Formalized November 17, 2025)
1. **FRED**: 30+ economic series (interest rates, inflation, employment, GDP) via `collect_fred_comprehensive.py`
2. **Yahoo Finance**: 55 symbols OHLCV (ZL futures, commodities, indices) via `collect_yahoo_finance_comprehensive.py`
3. **Alpha Vantage** (NEW - November 2025): Technical indicators, options, FX pairs, commodities
   - Status: Integration in progress
   - Premium Plan75: 75 API calls/minute (API key in Keychain)
   - MCP Server configured for interactive testing
   - See `docs/plans/ALPHA_VANTAGE_EVALUATION.md` for complete strategy

### Primary Documents
- `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md` – Source of truth (updated Nov 15, 2025).
- `docs/plans/IMPLEMENTATION_PLAN_BIG8_UPDATE.md` – Active work on Big 8 labor pillar rollout.
- `COMPREHENSIVE_DATA_VERIFICATION_REPORT.md` & `COMPREHENSIVE_AUDIT_20251115_FRESH.md` – Latest data verification status.
- `README_CURRENT.md` – Repo map, workflows, and architecture recap.

### PyTorch Knowledge Base (November 2025)
- `Py Knowledge/` – Comprehensive PyTorch documentation tailored for CBI-V14
  - **01_pytorch_fundamentals.md** – Core concepts for commodity forecasting
  - **02_deep_dive_optimizations.md** – MPS backend, torch.compile, mixed precision
  - **03_extensions_custom_ops.md** – Custom operators for commodity-specific calculations
  - **04_neural_network_recipes.md** – Practical patterns and best practices
  - **05_torchcodec.md** – Video/multimedia (future enhancement potential)
  - **06_executorch_deployment.md** – On-device deployment strategies
  - **07_coreml_integration.md** – Apple Silicon optimization (optional, not primary)
  - **08_cbi_v14_implementation.md** – Complete implementation guide
  - **09_best_practices.md** – Do's and don'ts for commodity forecasting
  - **10_performance_benchmarks.md** – M4 Mac specific optimizations
  - **11_quantitative_finance_libraries.md** – QuantLib, TA-Lib, FinGPT integration
  - **12_research_insights.md** – Dual-stream LSTM, sentiment analysis research
  - **13_REFINED_ARCHITECTURE.md** – Production-ready architecture (CRITICAL)
  - **ZL_SOYBEAN_OIL_CLARIFICATION.md** – ZL = Soybean Oil Futures details

### Alpha Vantage Integration Documents (November 17, 2025)
- `docs/plans/ALPHA_VANTAGE_EVALUATION.md` – Complete API evaluation and integration strategy
- `docs/plans/FINAL_GPT_INTEGRATION_DIRECTIVE.md` – Architecture answers and implementation plan
- `docs/plans/ARCHITECTURE_REVIEW_REPORT.md` – Deep architecture audit findings
- `docs/plans/ALPHA_VANTAGE_MCP_CONFIG.md` – MCP server setup for interactive testing
- `docs/setup/KEYCHAIN_API_KEYS.md` – API key management (includes ALPHA_VANTAGE_API_KEY)

### Workflow Snapshot
1. Run `scripts/data_quality_checks.py` before exports or training.
2. Export Parquet datasets with `scripts/export_training_data.py` (us-central1 tables).
3. Train under `src/training/` (baselines, advanced, regime-aware). Use `training/utils/model_saver.py` for metadata.
4. Generate forecasts locally using `src/prediction/generate_forecasts.py`.
5. Upload predictions with `scripts/upload_predictions.py`.
6. Validate BigQuery views (COUNT, null, regime coverage, MAPE/Sharpe) prior to dashboard release.

---

## ✅ Active Code Paths
- `scripts/`: `data_quality_checks.py`, `export_training_data.py`, `upload_predictions.py`, `post_migration_audit.py`.
- `src/training/`: baselines, advanced, regime, utils (`model_saver` optional `version`).
- `src/prediction/`: forecasts, SHAP, ensemble, uncertainty, news impact.
- `src/analysis/backtesting_engine.py`, `scripts/daily_model_validation.py`, `scripts/performance_alerts.py`.
- `TrainingData/` + `Models/local/` – obey new directory naming with versionless first runs.

---

## ❌ Legacy / Ignore
- `archive/`, `legacy/`, `docs/plans/archive/`, `scripts/deprecated/`.
- Any doc or script pushing Vertex AI training, BQML, or AutoML.
- `vertex-ai/` (reference only, never execute).

---

## 🚨 Critical Rules
1. Keep `TRAINING_MASTER_EXECUTION_PLAN.md` synced with reality after every major change.
2. Use the naming convention `{asset}_{function}_{scope}_{regime}_{horizon}` everywhere (SQL, exports, directories).
3. Stay inside existing us-central1 datasets; do not create new datasets/tables without sign-off.
4. Run data quality checks plus BigQuery verification before training, uploading, or publishing results.
5. Save models with `version=None` on first run; create `_v002` style directories only when explicitly versioning a retrain.
6. **API Keys MUST be stored in macOS Keychain** - Use `src/utils/keychain_manager.py` to retrieve keys. Never hardcode keys or use environment variables. See Security section in `TRAINING_MASTER_EXECUTION_PLAN.md`.
7. **Alpha Vantage technicals are pre-calculated** - Don't recalculate SMA, EMA, RSI, MACD, etc. from API. Use Alpha Vantage for gap-filling and validation only.
8. **Follow existing collection patterns** - New collectors (like Alpha Vantage) should follow the same pattern as `collect_fred_comprehensive.py`: Python → External drive + BigQuery.
9. **PyTorch architecture decisions** - Follow `Py Knowledge/13_REFINED_ARCHITECTURE.md`: TCN vs LSTM bake-off, 30-60 curated features, single-asset (ZL) first, PyTorch → BigQuery inference path (NOT CoreML primary), focus on MAPE/Sharpe quality not throughput.
10. **ZL = Soybean Oil Futures** - NOT corn. Primary commodity for single-asset baseline. See `Py Knowledge/ZL_SOYBEAN_OIL_CLARIFICATION.md` for details.

---

## 📋 Quick Checklist
- [ ] File lives outside `archive/` and `legacy/`.
- [ ] No Vertex AI / BQML / AutoML assumptions.
- [ ] Dated on or after 12 Nov 2025 unless explicitly flagged as reference.
- [ ] Uses correct naming architecture and versionless first-run rule.
- [ ] Data quality + BigQuery verification documented before outputs ship.

---

## 📂 Safe References
- `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md`
- `docs/plans/IMPLEMENTATION_PLAN_BIG8_UPDATE.md`
- `COMPREHENSIVE_AUDIT_20251115_FRESH.md`, `FINAL_MIGRATION_COMPLETENESS_REPORT.md`, `MIGRATION_RECONCILIATION_FINAL.md`
- `COMPREHENSIVE_DATA_VERIFICATION_REPORT.md`
- `README_CURRENT.md`, `docs/reference/INSTITUTIONAL_FRAMEWORK_COMPLETE.md`
- `scripts/export_training_data.py`, `scripts/upload_predictions.py`, `scripts/data_quality_checks.py`
- `src/training/`, `src/prediction/`, `src/analysis/`
- `Py Knowledge/13_REFINED_ARCHITECTURE.md` – Production-ready PyTorch architecture (CRITICAL)
- `Py Knowledge/ZL_SOYBEAN_OIL_CLARIFICATION.md` – ZL commodity details

---

## ⚠️ Data & Verification Status (Nov 17, 2025)
- Training tables (`zl_training_*`) still missing pre-2020 history (20-year gap) – join fixes pending.
- Regime assignments incomplete (`allhistory` placeholders) – update joins and weight application.
- Missing joins: `raw_intelligence.commodity_soybean_oil_prices`, `forecasting_data_warehouse.vix_data`.
- ✅ No 0.5 placeholder patterns in production price data.
- ✅ Historical and Yahoo Finance datasets validated (see verification report).
- ⚠️ Alpha Vantage integration in progress - collection script and BQ tables to be created.
- ✅ MCP Server configured and tested for Alpha Vantage interactive API calls.

## 🆕 Alpha Vantage Integration Status (Nov 17, 2025)

### What Alpha Vantage Fills (Gaps in FRED/Yahoo)
1. **Technical Indicators** (50+ indicators) - FRED has none, manual calculations exist
2. **Options Data** (Full chains, Greeks, IV) - Not collected anywhere currently
3. **Extended FX Pairs** (USD/ARS, USD/INR, USD/MYR, etc.) - FRED has only 3 pairs
4. **Commodity Technicals** (Wheat, corn, metals with indicators) - Yahoo has prices only
5. **Market Analytics** (Correlation matrices, variance, MAX_DRAWDOWN) - Calculated manually in Python
6. **News Sentiment** (Enhanced layer) - Supplements existing NewsAPI collection
7. **Earnings Data** (Transcripts, estimates) - Not collected currently
8. **Insider Transactions** - Not collected currently

### Integration Strategy (Hybrid Approach)
**PRIMARY**: Keep our manual calculations (correlations, volatility in Python)
  - Reason: No data delay (Alpha has 2-3 day lag)
  - Reason: ZL futures not in Alpha Vantage (use Yahoo)
  
**VALIDATION**: Use Alpha Vantage for weekly validation
  - Compare our calculations vs Alpha Analytics API
  - Detect calculation drift
  
**GAP FILLING**: Use Alpha Vantage for data we don't have
  - Options data (put/call ratio, gamma exposure, IV skew)
  - Extended FX pairs with technicals
  - Commodity technicals (wheat, corn, copper, etc.)
  - Earnings surprises and transcripts
  - MAX_DRAWDOWN and AUTOCORRELATION metrics

### API Budget (Plan75)
- Daily collections: ~50-60 API calls (technicals, options, FX, commodities)
- Weekly validation: ~30 API calls (compare calculations)
- Within 75 calls/minute limit

### Phase Approach
**Phase 1** (Current): ZL Alpha Vantage integration complete
  - Create `collect_alpha_vantage_master.py`
  - Set up `raw_intelligence.alpha_vantage_*` tables
  - Integrate into daily pipeline
  - Weekly validation operational
  
**Phase 2** (Future): ES futures system
  - Reuses 90% of Phase 1 infrastructure (FRED, sentiment, regimes)
  - Adds ES intraday data (5min, 15min, 60min)
  - Private trading dashboard
  - Multi-timeframe forecasting

---

## 🧠 PyTorch Architecture Refinements (November 2025)

### Critical Architecture Decisions

**Model Family**: Run bake-off with 2-3 baselines:
- **TCN (Temporal Convolutional Network)** – Often best for commodity data, compiles cleaner on MPS
- **LSTM + Scaled Dot-Product Attention** – Solid baseline, proven architecture
- **N-BEATSx** (Optional) – Interpretable trend/seasonal blocks

**Feature Set**: **30-60 curated features** (NOT 15, NOT 290)
- Prices: ZL level/returns, limited technicals (RSI, MACD, ATR)
- Substitution & Macro: Palm oil spread (critical for ZL), WTI, USD/BRL, VIX
- Weather: Brazil/Argentina precip/GDD (primary for ZL), Midwest (secondary)
- Positioning: CFTC managed money flows, regime flags
- **Lock feature order** after SHAP/MI selection to avoid drift

**Commodity Strategy**: **Single-asset multi-horizon** (ZL = Soybean Oil Futures)
- Start with ZL only (soybean oil futures)
- Add palm oil, crude oil as **context inputs**, not separate targets
- Multi-commodity outputs only after single-asset proven

**Training Optimizations**:
- **MPS backend**: `torch.backends.mps.allow_tf32 = True`
- **Mixed precision**: `autocast(dtype=torch.float16)` with `GradScaler`
- **torch.compile**: Feature flag with fallback (1.2-2.0x speedup, not guaranteed 2.5x)
- **Gradient clipping**: `clip_grad_norm_(max_norm=1.0)` – mandatory for RNNs
- **Walk-forward CV**: Never shuffle across time, rolling origin validation

**Loss Function**: Huber loss (δ=1.0) with horizon weights + directionality penalty

**Inference Path**: **PyTorch on M4 → BigQuery** (NOT CoreML primary)
- Daily: Load parquet → PyTorch inference → Upload to BigQuery → Dashboard reads views
- CoreML optional for demos/on-device, not canonical serving path
- Focus on **MAPE/Sharpe parity**, not throughput (35k preds/s unnecessary for daily batch)

### BigQuery/Mac Integration Pattern

**Cloud Side (BigQuery)**:
- Data collection, feature engineering, scheduling, state management
- Export parquet bundles with manifest.json + `_SUCCESS` markers
- Store predictions, performance views, dashboard reads

**Mac Side (M4)**:
- Training with PyTorch MPS backend
- Inference using PyTorch (not CoreML primary)
- Upload predictions to BigQuery
- Quality gates: MAPE/Sharpe parity checks before deployment

**Pattern**: BigQuery owns clocks/state/backups; Mac owns training/compute

### Library Enhancements (Investigated, Not Yet Implemented)

**QuantLib**: Derivatives pricing, Monte Carlo simulations, risk metrics
**TA-Lib**: 150+ technical indicators, 60+ candlestick patterns
**FinGPT/FinBERT**: Financial sentiment analysis from news
**QuantRocket**: Professional data pipeline (free tier available)
**Finance-Python**: VaR, CVaR, Sharpe ratio calculations

All libraries are M4 Mac compatible and can enhance features WITHOUT disrupting existing structure.

### Research Integration

**Dual-Stream LSTM** (arXiv:2508.06497): Achieved 0.94 AUC by fusing price signals with news sentiment
- Architecture: Price stream + News stream → Cross-modal attention → Temporal attention
- Critical finding: Without news component, AUC drops to 0.46
- Implementation: Add after single-asset baseline proven

**Sentiment Analysis** (GitHub: dipakml/Sentiment-analysis-of-commodity-news-using-NLP)
- 10,000+ manually annotated commodity news headlines (2000-2021)
- Can enhance existing features with sentiment scores

**Supply Chain NLP** (MIT Thesis): Techniques for long-horizon forecasting improvements

---

## 📊 Architecture Audit Findings (Nov 17, 2025)

### Actual System Pattern
```
Data Collection: Python scripts (all sources)
    ↓
Storage: External drive (/Volumes/Satechi Hub/) + BigQuery
    ↓
Feature Engineering: HYBRID (already in use!)
    - BigQuery SQL: Correlations (CORR() OVER), regimes (CASE WHEN), moving averages
    - Python: Sentiment (NLP), policy extraction, complex interactions
    - Alpha Vantage: Pre-calculated technicals (NEW - store as-is, don't recalculate)
    ↓
Training: Local Mac M4 (TensorFlow Metal + PyTorch MPS)
    ↓
Predictions: Upload to BigQuery → Dashboard
```

### BigQuery Usage (Actual)
- **Storage**: 35 datasets, 432 tables (primary data warehouse)
- **Feature SQL**: Some correlations and technicals already in SQL (see `advanced_feature_engineering.sql`, `create_big8_signal_views.sql`)
- **Training Tables**: `training.zl_training_*` (305-449 features per table)
- **NOT for**: Primary feature engineering (mostly Python), ML training (local Mac)

### External Drive Usage (Actual)
- **Location**: `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/`
- **Size**: 620MB in raw/, 572KB in staging/
- **Purpose**: Backup, audit trail, intermediate storage
- **Pattern**: All collectors save here + upload to BQ

### No Cloud Run Jobs (Yet)
- All collection scripts run locally/cron
- Could migrate to Cloud Run in future (optional)
- Current pattern works reliably

---

**Last Updated**: November 2025  
**Action**: Update this file whenever architecture, guardrails, or verification status changes.  
**Recent Changes**: 
- Added PyTorch knowledge base documentation (`Py Knowledge/`)
- Added refined architecture recommendations (TCN vs LSTM, 30-60 features, single-asset strategy)
- Clarified ZL = Soybean Oil Futures (NOT corn)
- Added BigQuery/Mac integration pattern
- Added library enhancements investigation (QuantLib, TA-Lib, FinGPT)
- Added research insights integration (dual-stream LSTM, sentiment analysis)

