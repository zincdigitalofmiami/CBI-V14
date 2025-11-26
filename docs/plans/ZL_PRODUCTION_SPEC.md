---
**Title:** ZL Production Specification (Baseline Engine)
**Scope:** ZL daily procurement forecasts only (price-level targets)
**Status:** DRAFT → to be treated as canonical once signed off
---

## 1. Purpose and Scope

This document defines the **non‑negotiable production contract** for the ZL baseline engine.  
It specifies:
- Data sources and tables used for production training.
- Target definitions per horizon (price levels only).
- Allowed feature families and column patterns.
- Train/validation/test windows and regime weighting rules.
- Approved model types and metrics.

Any model that drives client‑visible forecasts **must** comply with this spec. Experiments (returns, alternative splits, alternative models) are allowed only in clearly marked experimental code and may not be wired into production dashboards or training tables without an explicit update to this spec.

## 2. Data Sources (Authoritative)

**Source of truth:** BigQuery (project `cbi-v14`), us-central1 only.

ZL baseline models may read training data only from:
- `market_data.databento_futures_ohlcv_1d`  
  - Daily OHLCV for futures; `symbol = 'ZL'` for ZL close.  
  - Used as the canonical price history for targets and simple derived features.
- `features.master_features_all` (view or materialized table)  
  - Denormalized master feature matrix with source‑prefixed columns (e.g. `databento_*`, `fred_*`, `eia_*`, `usda_*`, `cftc_*`, `policy_trump_*`, etc.).  
  - Contains factor families A–H as defined in `MASTER_PLAN.md`.
- Optional: horizon‑specific training tables (once created)  
  - `training.zl_training_prod_allhistory_1w`  
  - `training.zl_training_prod_allhistory_1m`  
  - `training.zl_training_prod_allhistory_3m`  
  - `training.zl_training_prod_allhistory_6m`  
  - `training.zl_training_prod_allhistory_12m`  
  - These tables are simply sharded exports of `master_features_all` with horizon‑specific targets/metadata.

**External drive (`/Volumes/Satechi Hub/...`) is not authoritative.**  
Local Parquet files are treated as **caches/extracts**, and must always be reproducible from BigQuery by a documented query.

## 3. Horizons and Targets (Price Levels Only)

All production ZL models forecast **future ZL price levels**, not returns or log returns.

Let:
- `P_t` = ZL daily close on trading day `t`, from `market_data.databento_futures_ohlcv_1d` or `features.master_features_all` (`databento_zl_close`).

Define horizons in **trading days**:
- 1 week → 5 days
- 1 month → 20 days
- 3 months → 60 days
- 6 months → 120 days
- 12 months → 240 days

**Target definitions (conceptual):**
- `target_zl_1w`  = `P_{t+5}`
- `target_zl_1m`  = `P_{t+20}`
- `target_zl_3m`  = `P_{t+60}`
- `target_zl_6m`  = `P_{t+120}`
- `target_zl_12m` = `P_{t+240}`

On Mac (Python), the targets are implemented as forward shifts:
```python
df['target_zl_1w']  = df['databento_zl_close'].shift(-5)
df['target_zl_1m']  = df['databento_zl_close'].shift(-20)
df['target_zl_3m']  = df['databento_zl_close'].shift(-60)
df['target_zl_6m']  = df['databento_zl_close'].shift(-120)
df['target_zl_12m'] = df['databento_zl_close'].shift(-240)
```
Rows with `NaN` targets (end of series) are dropped from training.

**No production ZL model may use returns or log returns as the primary target.**  
Return‑based targets are allowed only for research/diagnostic scripts in the `experiments` area and must never be wired to production forecasts or dashboards without an explicit spec change.

## 4. Feature Set (Allowed Families)

All production ZL features must come from the denormalized master matrix (`features.master_features_all`) and follow the source‑prefix convention. Features are organized into the factor families defined in `MASTER_PLAN.md`:

- **A. Price & Technicals**  
  - ZL and related futures OHLCV, returns, simple MAs, basic momentum, range, etc.  
  - Prefixes: `databento_*` (e.g., `databento_zl_close`, `databento_zl_ret_1d`).

- **B. Fundamentals / Basis / Spreads**  
  - RINs, biodiesel margins, crush spreads, palm/ZL spreads, HOBO, crack spreads, basis where available.  
  - Prefixes: `eia_*`, `usda_*`, `palm_*`, etc.

- **C. Macro & Risk-On/Off**  
  - Rates, curves, indices, FX aggregates (e.g. DXY) where sourced from FRED/other macro feeds.  
  - Prefixes: `fred_*`, `macro_*`.

- **D. Volatility (Realized & Implied)**  
  - Realized vol for ZL/MES, VIX/VVIX, term‑structure slopes, vol regimes.  
  - Prefixes: `vol_*`, `vix_*`.

- **E. Positioning / Flow**  
  - CFTC COT, open interest, crowding metrics.  
  - Prefixes: `cftc_*`, `open_interest_*`.

- **F. Microstructure (ZL daily: limited use)**  
  - Daily‑aggregated microstructure summaries as needed; sub‑hour features remain on Mac only.  
  - Prefixes: `micro_*` where present.

- **G. Events & Policy**  
  - Tariffs, EPA/USTR actions, USDA prints, margin changes, policy shocks.  
  - Prefixes: `policy_*`, `tariff_*`, `event_*`.

- **H. Text‑Based Sentiment**  
  - Topic‑segmented sentiment scores from ScrapeCreators and related pipelines (true NLP outputs only).  
  - Prefixes: `sentiment_*`.

The exact list of columns may expand over time, but **all** must:
- Be source‑prefixed.
- Be present in `features.master_features_all`.
- Be documented in `CALCULATION_INVENTORY.md` (or successor) with calculation method and owner.

## 5. Train / Validation / Test Windows

To ensure robust evaluation and guard against regime drift, ZL production models use a fixed three‑way time split over the Databento era:

- **Training window:**  
  - `2010‑01‑01` → `2022‑12‑31`  
  - Used for fitting models and, where needed, light hyperparameter tuning.

- **Validation window:**  
  - `2023‑01‑01` → `2023‑12‑31`  
  - Used for model selection, early stopping, and hyperparameter tuning.  
  - Metrics on this window guide configuration changes but do not directly drive deployment decisions.

- **Test window (hold‑out):**  
  - `2024‑01‑01` → latest available date  
  - Used only for final evaluation and ongoing monitoring.  
  - No hyperparameters may be tuned against the test window, and no model version that has “seen” test data may be promoted to production.

For early baselines implemented via `scripts/train/train_zl_baselines.py` and `scripts/train/quick_zl_baseline.py`, a simpler 80/20 time‑based split is used internally. As the engine matures, those scripts and any new training harnesses must enforce the train/val/test scheme above and record the actual date boundaries in their backtest metadata.

## 6. Regime Weighting (High‑Level Rules)

Regime information comes from:
- `training.regime_calendar` (date → regime label).
- `training.regime_weights` (regime label → weight).

High‑level rules:
- Recent regimes (e.g., post‑2018, trade war, COVID, inflation, Trump‑anticipation, Trump‑second term) receive **higher weights** than early 2000s data.  
- Extreme crisis periods (e.g., 2008, Mar 2020) may be upweighted for risk‑aware models, but not so heavily that they dominate all training.  
- No single regime should account for more than a fixed fraction of total effective weight (to be tuned, e.g. ≤ 40%).

Exact numeric weights are defined in the YAML and Parquet regime files referenced by MASTER_PLAN and must be kept in sync with this spec.

## 7. Approved Model Classes (Baseline)

For ZL production baselines:

- **Primary model:** LightGBM regressor (GBDT), with conservative parameters:
  - `objective = 'regression'`
  - Metrics: `mae`, `rmse` (R² and MAPE derived)
  - Regularization: limited `num_leaves`, `feature_fraction`, `bagging_fraction`, `min_data_in_leaf`, `lambda_l1`, `lambda_l2`
  - Training: time‑ordered data, no shuffling, early stopping on validation loss.

- **Optional ensemble:**  
  - Second‑stage LightGBM meta‑learner combining baseline outputs and regime features.  
  - Only introduced once single‑stage baseline is fully validated.

Neural models, quantile models, and complex ensembles are considered **Phase 3+** and require a separate spec extension.

## 8. Metrics and Logging

Every production training run must log **at least**:
- Train / validation / test:
  - MAE, RMSE, R².
  - MAPE (where price > 0).
  - Directional accuracy (sign of `(target_t - current_price_t)` vs sign of `(prediction_t - current_price_t)`).
- Top features:
  - Top N features by gain and split counts.
  - Grouped attribution by factor family (A–H) where possible.
- Data ranges:
  - Train/val/test date ranges.
  - Number of rows used in each split.

These metrics and metadata must be written to JSON (alongside the saved model) on the Mac, in a predictable location (e.g., `TrainingData/models/zl_baselines/production/`).

## 9. Production vs Experimental Code

To prevent drift between design and implementation:

- **Production training scripts:**
  - `scripts/train/train_zl_baselines.py`  
  - May only use price‑level targets as defined here.  
  - Outputs to `TrainingData/models/zl_baselines/production/`.

- **Experimental scripts (research only):**
  - `scripts/train/quick_zl_baseline.py`  
  - May use return‑based targets and alternative horizons, **but**:
    - Must be clearly marked as experimental in their header.
    - Must output to an `experiments` subfolder, never read by production dashboards.

Any new training script must declare at the top whether it is **PRODUCTION ONLY** or **EXPERIMENTAL ONLY** and reference this spec.

## 10. Change Control

Changes to this spec must:
- Be made via pull request with a short rationale.
- Update this document’s “Change Log” below with:
  - Date
  - Author
  - Summary of change
  - Impact (e.g., “targets changed from returns to price levels”).

### Change Log

- 2025‑11‑26 – Initial draft created from MASTER_PLAN.md, Databento ingest plan, and current baseline training scripts.
