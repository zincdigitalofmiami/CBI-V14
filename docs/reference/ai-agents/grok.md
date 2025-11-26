# CBI-V14 – Project Manual for Grok AI Assistant

This file tells Grok how to work in this repo without breaking the architecture or multiplying plans. Treat it as the project manual.

---

## 1. Where to Start (Canonical Docs)

Always get context from these, in this order:

1. `docs/plans/MASTER_PLAN.md`  
   - High‑level architecture, data sources, rules (BigQuery vs Mac, Big 8, etc.).
2. `docs/plans/ZL_PRODUCTION_SPEC.md`  
   - Non‑negotiable contract for ZL baselines (targets, horizons, features, splits, metrics).
3. `docs/reference/ACTIVE_EXECUTION_DOCS.md`  
   - Short index of "live" execution docs (data pull plans, schema breakdown, FX clarification, etc.).

If a document is **not** in `ACTIVE_EXECUTION_DOCS.md` or starts with an `⚠️ ARCHIVE` banner, treat it as reference only, not an instruction source.

**Never treat anything under `archive/` or `docs/archive/` as live.**
- `archive/` and its subfolders exist only for historical reference and must not drive new code, schemas, or data sources.
- `docs/archive/` and `docs/audits/` are frozen snapshots; do not resurrect design choices from there into current specs or implementations.

---

## 2. Hard Architecture Rules

- **BigQuery is the system of record.**
  - All authoritative data lives in BigQuery (project `cbi-v14`, us‑central1).
  - The external drive (`/Volumes/Satechi Hub/...`) is a cache/backup of exports, never a source of truth.

- **Mac M‑series handles all training and heavy feature engineering.**
  - No BigQuery ML, no Vertex AI, no cloud training jobs.
  - Models are trained via Python scripts (LightGBM + small neural nets later) on the Mac, using data pulled from BigQuery.

- **Targets are future price levels.**
  - ZL production targets are future price **levels**, not returns.
  - Horizons: 1w (5d), 1m (20d), 3m (60d), 6m (120d), 12m (240d); see `ZL_PRODUCTION_SPEC.md`.

- **Factor families (A–H + Big 8).**
  - All features must belong to one of the documented factor families:
    - A: Price & technicals,
    - B: Fundamentals / basis / spreads (includes crush, biofuels, palm),
    - C: Macro & risk‑on/off,
    - D: Volatility,
    - E: Positioning / flow,
    - F: Microstructure,
    - G: Events & policy,
    - H: Text sentiment.
  - The core signal set is the "Big 8" drivers for ZL (crush, China, dollar, Fed, tariffs, biofuels, energy complex, palm).

- **No fake or synthetic data.**
  - Never generate placeholder rows or synthetic series to "make something work".
  - All data must come from authenticated APIs or official sources (Databento, FRED, EIA, USDA, CFTC, ScrapeCreators, etc.).

---

## 3. Code & Repo Map

Use this as your mental model of the project:

- `cbi_v14/` – Core Python package (use this for reusable logic)
  - `api/`
    - `databento/` – Databento→BigQuery ingestion interfaces.
    - `fred/` – FRED→BigQuery ingestion interfaces.
    - `scrapecreators/` – News buckets + Trump feed ingestion interfaces.
  - `backtest/`
    - `specs.py` – `DatasetSpec`, `ModelSpec`, `BacktestRun` dataclasses for logging experiments and baselines.
  - `features/`
    - `palm.py` – Palm oil feature engineering (palm_* fields) for ZL horizons.
    - (Future) other feature builders should live here, not in ad‑hoc scripts.
  - `markets/`
    - `zl.py` – Canonical ZL engine config (roots, supporting symbols, horizon day counts).
  - `training/`
    - Place for shared training utilities; scripts under `scripts/train/` should import from here as it grows.
  - `models/`
    - (Future) wrappers around LightGBM/XGBoost/neural models and ensembles.

- `scripts/`
  - `ingest/` – Ingestion scripts (Databento, FRED, EIA, USDA, etc.). Over time, they should call into `cbi_v14.api.*` instead of duplicating logic.
  - `train/`
    - `train_zl_baselines.py` – **PRODUCTION ONLY** ZL baseline trainer (price‑level targets). Writes models + backtest JSONs.
    - `quick_zl_baseline.py` – **EXPERIMENTAL ONLY** directional/return experiments; never wired to dashboards.
    - `train_mes_*` – MES training scripts (future work; follow ZL spec when updated).

- `docs/plans/`
  - `MASTER_PLAN.md` – Canonical architecture and philosophy.
  - `ZL_PRODUCTION_SPEC.md` – ZL baseline production contract.
  - `TRAINING_PLAN.md` – High‑level modeling/training phases.

- `Quant Check Plan/`
  - Execution/audit/planning docs:
    - `CALCULATION_INVENTORY.md`,
    - `PHASE2_DATA_PULL_PLAN.md`,
    - `ZL_EXECUTION_PLAN.md`,
    - `EXECUTION_START_20251124.md`,
    - `FX_DATA_SOURCE_CLARIFICATION.md`, etc.
  - Some older plans are marked `⚠️ ARCHIVE` – do not use them for new work.

- `bigquery-sql/`
  - `FINAL_COMPLETE_BQ_SCHEMA.sql` – Canonical BigQuery schema for `features.master_features_all` and related tables.

- `dashboard-nextjs/`
  - Next.js dashboard; future work will connect it to the new BigQuery views and production forecasts.

---

## 4. Modeling Rules (ZL Baselines)

- **Targets:** future ZL close at T+N trading days (price levels), as defined in `ZL_PRODUCTION_SPEC.md`.
- **Horizons:** 1w, 1m, 3m, 6m, 12m; each has its own model.
- **Train/Val/Test (institutional split):**
  - Train: `2010‑01‑01` → `2022‑12‑31`.
  - Val: `2023‑01‑01` → `2023‑12‑31`.
  - Test (hold‑out): `2024‑01‑01` → latest date (no tuning against this window).
- **Baseline model class:** LightGBM regression per horizon (no BQML, no Vertex).
- **Backtest logging:** all serious training runs should produce a `BacktestRun` JSON (via `cbi_v14.backtest.specs`) alongside saved models.
- **Palm horizon rule:**
  - For **all production horizons** (1w, 1m, 3m, 6m, 12m), palm features (`palm_*`) must be present and populated in the training surface and live feature feed.
  - Experimental scripts may try variants without palm, but no model may be promoted to client‑facing production unless the full palm feature family is wired and available.

---

## 5. Behavior & "Do Not" Rules for AI

**1. No new plan documents by default.**
- Do **not** create new "master" plan files.
- If a change is architectural:
  - Update `MASTER_PLAN.md` or `ZL_PRODUCTION_SPEC.md`.
  - If necessary, update or add a short supporting note in `Quant Check Plan/`, but prefer editing existing docs listed in `ACTIVE_EXECUTION_DOCS.md`.

**2. No new SQL/DDL before checking existing.**
- Before adding any new `.sql`:
  - Search `bigquery-sql/` and `FINAL_COMPLETE_BQ_SCHEMA.sql` for related tables/columns.
  - Prefer updating the canonical schema or views instead of creating parallel ones.
- Do **not** add new datasets or regions; stay within the existing datasets and `us-central1`.

**3. No new BigQuery tables/views for training unless explicitly required by the spec.**
- Training views should be simple `SELECT ... FROM features.*` with no joins.
- All joins happen in feature build pipelines, not in training queries.

**4. No pandas-gbq.**
- Use `google-cloud-bigquery` clients (`load_table_from_dataframe`, `to_dataframe`) only.
- Do not introduce `pandas_gbq` or `DataFrame.to_gbq()` in this codebase.

**5. No Vertex AI, no BQML, no extra cloud services.**
- Ignore the `vertex-ai/` directory (legacy marker).
- Do not wire in Vertex endpoints, BQML models, Dataflow, Pub/Sub, etc., unless the user explicitly changes the spec.

**6. Keep changes surgical and spec‑aligned.**
- Respect the existing package layout (`cbi_v14.*`) and specs.
- When refactoring scripts, move reusable logic into `cbi_v14` modules, then make scripts thin wrappers.
- Do not rename tables, datasets, or core files unless the spec is updated first.

**7. For new features: document → implement → wire.**
If you add a new feature family or field:
1. Add it to `CALCULATION_INVENTORY.md` (formula, type, where computed).  
2. Add it to `FINAL_COMPLETE_BQ_SCHEMA.sql` (under the correct factor section).  
3. Implement it in an appropriate `cbi_v14/features/*.py` module.  
4. Wire it into the master feature assembly and ensure training exports include it.

---

## 6. Ingestion & Freshness (Before Training)

Before running any important baseline training:

- Ensure **Databento daily tables** are up to date for the ZL engine roots (ZL, ZS, ZM, CL, HO; and FX roots when in use) in `market_data.databento_futures_ohlcv_1d`.
- Ensure macro/FRED tables, domain tables (EIA, USDA, CFTC, weather, policy), and palm series (once wired) have recent `MAX(date)` in BigQuery.
- If data is stale or missing, fix ingestion **first**; do not train on half‑fresh data.

(In the future, Cloud Scheduler/Dataform may automate this, but until then, use a manual pre‑training checklist.)

---

## 7. Experiments vs Production

- **Production:**
  - ZL baselines that conform to `ZL_PRODUCTION_SPEC.md` and use the defined train/val/test windows.
  - Scripts: primarily `scripts/train/train_zl_baselines.py`.
  - Outputs: models under `TrainingData/models/zl_baselines/production/` with `BacktestRun` JSONs.

- **Experimental:**
  - Anything that uses return targets, different horizons, or different model classes.
  - Scripts: `scripts/train/quick_zl_baseline.py` and similar.
  - Outputs: must go under `TrainingData/models/zl_baselines/experiments/` (or equivalent), never read directly by dashboards or production upload code.

Always be explicit in script headers and comments about whether something is PRODUCTION ONLY or EXPERIMENTAL ONLY.

---

## 8. Critical Best Practices

### Data Quality
- **NO FAKE DATA** - NEVER use placeholders, synthetic data, or fake values. ONLY use real, verified data from authenticated APIs or official sources.
- **ALWAYS CHECK BEFORE CREATING** - Before creating ANY table/schema/dataset/folder/file, check if it already exists. Verify naming conventions, check for duplicates, validate schema compatibility.
- **ALWAYS AUDIT AFTER WORK** - After ANY data modification, run data quality checks. Audit for errors, nulls, duplicates, gaps. Verify row counts, date ranges, value ranges.

### Cost & Resource Management
- **us-central1 ONLY** - ALL BigQuery datasets, GCS buckets, and GCP resources MUST be in us-central1. NEVER create resources in US multi-region or other regions.
- **NO COSTLY RESOURCES WITHOUT APPROVAL** - Do NOT create Cloud SQL, Cloud Workstations, Compute Engine, Vertex AI endpoints, or any paid GCP resources without explicit user approval. Estimate costs if > $5/month and ask for approval.

### Research & Validation
- **RESEARCH BEST PRACTICES** - ALWAYS research online for best practices before implementing. Verify current practices (not outdated), cite sources, compare approaches, validate against industry standards.
- **RESEARCH QUANT FINANCE** - For modeling features, research quant finance best practices. Study academic papers, industry standards, proven methodologies. Validate formulas against authoritative sources.

---

## 9. Communication Style

### Be Direct, Not Diplomatic
- Challenge assumptions when they seem wrong
- Ask "Why?" or "Have you considered...?" when something seems questionable
- Quantify claims with evidence (correlations, SHAP values, etc.)

### Domain Knowledge
**ZL (Soybean Oil) Drivers (By Actual Correlation):**
1. **Crush Margin** (#1, 0.961) - Processing economics dominate
2. **China Imports** (#2, -0.813) - Less buying = higher prices (inverse!)
3. **Dollar Index** (#3, -0.658) - Strong dollar = weak commodities
4. **Fed Policy** (#4, -0.656) - Rates kill commodity speculation
5. **Tariffs** (#5, 0.647) - Trade war creates volatility
6. **Biofuels** (#6, -0.601) - RIN prices, RFS mandates
7. **Crude Oil** (#7, 0.584) - Energy complex linkage
8. **VIX** (#8, 0.398) - MUCH lower than most assume!

**MES (Micro E-mini) Drivers:**
1. Fed Policy (40-50% of variance)
2. Treasury Yields / Curve (25-30%)
3. Volatility Complex (15-20%)
4. Dollar/FX (10-15%)
5. Credit Spreads (5-10%)

---

## 10. Quick Reference

### Cost Lessons
- Always use us-central1, never US multi-region
- Get approval for any resource > $5/month

### Data Quality
- No placeholders (0.5, 1.0, all-same values)
- Quarantine suspicious data, never delete
- Validate at raw → curated → training stages

### BigQuery Best Practices
- Partition on date columns
- Cluster on frequently filtered columns
- Limit query date ranges
- Monitor query costs (stay under 1 TB/month)

### Model Training
- Run 24-audit suite before training
- Use local M4 Mac only
- Validate training data quality
- Save models with proper metadata

---

## RELATED DOCUMENTATION
- `docs/plans/MASTER_PLAN.md` - Source of truth
- `docs/plans/TRAINING_PLAN.md` - Training strategy
- `docs/reference/BEST_PRACTICES_DRAFT.md` - Detailed best practices
- `docs/reports/costs/AI_MIGRATION_NIGHTMARE.md` - Cost lessons learned

---

**Last Updated:** November 26, 2025

