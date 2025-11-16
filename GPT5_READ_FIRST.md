# GPT-5 / FUTURE AI: READ THIS FIRST
**Critical context for all assistants touching CBI-V14**

---

## 🎯 Current Architecture (November 15, 2025)
- Apple M4 Mac handles every training and inference task (TensorFlow Metal + CPU tree libs).
- BigQuery = storage plus dashboard read layer only; no BigQuery ML, no AutoML jobs.
- Predictions generated locally, uploaded with `scripts/upload_predictions.py`, then read by the Vercel dashboard.
- The `vertex-ai/` directory is kept for reference. See `vertex-ai/LEGACY_MARKER.md`. Do **not** run anything in there.
- First-run models save to `Models/local/.../{model}` without version suffix. Pass an explicit `version` only when promoting a later retrain.

### Primary Documents
- `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md` – Source of truth (updated Nov 15, 2025).
- `docs/plans/IMPLEMENTATION_PLAN_BIG8_UPDATE.md` – Active work on Big 8 labor pillar rollout.
- `COMPREHENSIVE_DATA_VERIFICATION_REPORT.md` & `COMPREHENSIVE_AUDIT_20251115_FRESH.md` – Latest data verification status.
- `README_CURRENT.md` – Repo map, workflows, and architecture recap.

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

## ⚠️ Data & Verification Status (Nov 15, 2025)
- Training tables (`zl_training_*`) still missing pre-2020 history (20-year gap) – join fixes pending.
- Regime assignments incomplete (`allhistory` placeholders) – update joins and weight application.
- Missing joins: `raw_intelligence.commodity_soybean_oil_prices`, `forecasting_data_warehouse.vix_data`.
- ✅ No 0.5 placeholder patterns in production price data.
- ✅ Historical and Yahoo Finance datasets validated (see verification report).

---

**Last Updated**: November 15, 2025  
**Action**: Update this file whenever architecture, guardrails, or verification status changes.

