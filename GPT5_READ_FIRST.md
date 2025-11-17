# GPT-5 / FUTURE AI: READ THIS FIRST
**Critical context for all assistants touching CBI-V14**

---

## 🎯 Current Architecture (November 17, 2025)
- Apple M4 Mac handles every training and inference task (TensorFlow Metal + CPU tree libs).
- BigQuery = storage plus dashboard read layer only; no BigQuery ML, no AutoML jobs.
- Predictions generated locally, uploaded with `scripts/upload_predictions.py`, then read by the Vercel dashboard.
- The `vertex-ai/` directory is kept for reference. See `vertex-ai/LEGACY_MARKER.md`. Do **not** run anything in there.
- First-run models save to `Models/local/.../{model}` without version suffix. Pass an explicit `version` only when promoting a later retrain.

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
Training: Local Mac M4 (TensorFlow Metal)
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

**Last Updated**: November 17, 2025  
**Action**: Update this file whenever architecture, guardrails, or verification status changes.  
**Recent Changes**: Added Alpha Vantage integration status, hybrid architecture findings, Phase 1/2 approach, formalized data sources

