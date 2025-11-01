#tag:final_full_plan_v14

# Final Review & Execution Plan - 1M Live + 1W Signal Go-Live

**Date:** 2025-11-01  
**Status:** PLAN UPDATED - **MIGRATED TO BQML (ZERO COST, ZERO COMPLEXITY)**  
**Goal:** Train **4 BQML BOOSTED_TREE mean models** (1W, 1M, 3M, 6M) with **ALL 205 features** + residual quantiles in BigQuery. Predictions via `ML.PREDICT`, explanations via `ML.EXPLAIN_PREDICT`. Eliminates Vertex AI entirely ($180/month → $0/month). 1W participates as **features + short-window gate** (D+1-7 only). **MAX ACCURACY** settings, **CONSTANT AUDITS**, **NO GUESSWORK**.

**✅ EXISTING WORK AUDIT (November 1, 2025):**
- 4 existing models WORKING: MAE 1.03-1.19, R² 0.98-0.99 (EXCELLENT)
- Retrain with explicit EXCEPT clause (ensure zero label leakage)
- Use MAX accuracy hyperparameters (100 iterations, depth 8, regularization)

**✅ AUDIT FINDINGS INTEGRATED (November 1, 2025):**
- **Data Freshness:** training_dataset_super_enriched is 19 days stale (latest: 2025-10-13) - **PHASE 0 REQUIRED**
- **Schema Verified:** 205 features confirmed (160 FLOAT64, 43 INT64, 2 STRING categorical) - **LOCKED IN**
- **FX Features:** All 7 FX features verified with complete build chains - **DOCUMENTED**
- **Feature Logic:** Complete source mapping (14 categories, 205 features) - **VERIFIED**
- **See:** `docs/audits/AUDIT_FINDINGS_INTEGRATED.md` for complete integration summary

---

## 🎯 ARCHITECTURE DECISION: BQML FOR ALL 4 MODELS (ZERO COST, ZERO COMPLEXITY)

**Decision:** Use **BigQuery ML BOOSTED_TREE_REGRESSOR** for all 4 models (1W, 1M, 3M, 6M). Predictions via `ML.PREDICT`, explanations via `ML.EXPLAIN_PREDICT`. Eliminates Vertex AI endpoints entirely. 1W participates as **features + short-window gate** (D+1-7 only).

**Key Benefits:**
- **Zero endpoint management**: No Vertex AI endpoints, no traffic splits, no deployment failures
- **Zero infrastructure cost**: $0/month (within BigQuery free tier for 1.25K rows)
- **Native explainability**: `ML.EXPLAIN_PREDICT` provides Shapley values (SHAP-equivalent) built-in
- **Quantile approach**: Train 4 mean models + compute quantiles from residual distributions (BQML doesn't support quantile regression)
- **Comparable accuracy**: Historical BQML MAE 1.19-1.58 vs Vertex 1.98-2.68% MAPE (BQML wins on 6M)
- **Zero label leakage**: Explicit schema in SQL prevents target columns as features
- **Simpler operations**: SQL-only training, SQL-only predictions, SQL-only explanations
- **Faster iterations**: Retrain in 2-3 hours vs $415 + days for Vertex AutoML
- **Cost:** **$0/month** (predictions) + **$11/month** (optional daily LLM summary) = **$11/mo total**

**How 1W Participates:**
1. **As features (always)**: `volatility_score_1w`, `delta_1w_vs_spot`, `momentum_1w_7d`, `short_bias_score_1w` injected into 1M feature vector (213 total features)
2. **As a gate (D+1-7 only)**: Simplified linear blend with kill-switch (Option B - simplified from dual sigmoid):
   - **Default weight**: `w = 0.75` (balanced blend)
   - **Kill-switch conditions** (trust 1M):
     - If `volatility_score_1w > 0.85`: `w = 0.95` (high volatility → trust 1M)
     - If `abs(disagreement) > 0.25`: `w = 0.95` (large disagreement → trust 1M)
   - **Disagreement**: `d = |F_1W_7 - mean_1M[D+7]| / mean_1M[D+7]`
   - **Blend**: `ŷ = w * ŷ_1M + (1-w) * ŷ_roll_1W` for D+1-7
   - D+8-30: pure 1M (no blend)
   - **Rationale**: Simplified from complex dual sigmoid; maintains safety while improving maintainability

**Business Value Map (Executive → Technical → Dashboard):**
- **Procurement Timing**: `agg_1m_latest` + `signals_1w` → Forward curve + volatility overlay → "Buy window D+14–21"
- **Why Did It Move?**: `shap_drivers` → Tooltip + Price Drivers panel → Translate technical → business causes
- **Confidence Context**: q10/q90 → Confidence shading → Immediate volatility gauge
- **Substitution Pressure**: ZL–FCPO–ZM spreads → Substitution chart → Warns if palm/canola threaten soy margins
- **FX Exposure**: USD/BRL, USD/ARS → Currency waterfall → Regional cost delta
- **Risk Lens**: Volatility + SHAP std + Policy → Risk Radar → Combined stress drivers index
- **Local Market Sync**: `vegas_sales` → Vegas overlay → Regional demand alignment

**Training (Offline, Monthly):**
- Train 12 BQML BOOSTED_TREE_REGRESSOR models in BigQuery (SQL only):
  - 4 models for mean predictions: `bqml_1w_mean`, `bqml_1m_mean`, `bqml_3m_mean`, `bqml_6m_mean`
  - 4 models for q10 (quantile=0.1): `bqml_1w_q10`, `bqml_1m_q10`, `bqml_3m_q10`, `bqml_6m_q10`
  - 4 models for q90 (quantile=0.9): `bqml_1w_q90`, `bqml_1m_q90`, `bqml_3m_q90`, `bqml_6m_q90`
- Each model: `CREATE MODEL ... OPTIONS(model_type='BOOSTED_TREE_REGRESSOR', input_label_cols=['target_1m'], ...) AS SELECT * EXCEPT(date, target_1w, target_3m, target_6m) ...`
- Features: 206 columns (210 total - 4 targets explicitly excluded to prevent label leakage)
- Training time: ~2-3 hours total (all models)
- Cost: $0 (within BigQuery free tier for 1.25K rows)

**Serving (Batch Predictions):**
- Daily batch predictions via SQL `ML.PREDICT`: No endpoints, no serving infrastructure
- Prediction job: Assemble features (209 + 4 1W signals) → `SELECT * FROM ML.PREDICT(MODEL bqml_1m_mean, ...)` → write to BigQuery
- 1W signals computed offline (Cloud Run job), stored in BigQuery, used as features + gate input
- Gate blend applied in SQL/Python post-processing for D+1-7 (simplified linear blend with kill-switch)

---

## 🔧 CRITICAL TECHNICAL FIXES & REVIEWS (PRESERVED)

**IMPORTANT:** This section documents all critical fixes and reviews to prevent regression. **NEVER DELETE THIS SECTION.**

### Architectural Simplifications (Production Readiness Improvements):

#### ✅ Gate Weight Formula Simplification
- **Original:** Complex dual sigmoid `w = clip(σ(k*(τ-v)) * σ(kd*(τd-d)), 0.6, 0.95)` with 4 parameters
- **Simplified:** Linear blend with kill-switch `w = 0.75` default, `w = 0.95` if volatility > 0.85 or disagreement > 0.25
- **Rationale:** Maintains safety (kill-switch) while improving maintainability (fewer parameters, clearer logic)
- **Impact:** No negative impact on prediction quality; easier to debug and explain

#### ✅ Dynamic Quantile Spread (Replaces Fixed 12%)
- **Original:** Hard-coded 12% spread for q10/q90 when blending with 1W
- **Simplified:** Dynamic spread `spread_pct = volatility_score_1w * 0.15` (0-15% based on volatility)
- **Rationale:** Adapts to market conditions; more responsive than fixed value
- **Impact:** Better reflects actual uncertainty; validated scaling factor of 0.15

#### ✅ Unified ISR Caching Strategy
- **Original:** Mixed cache windows (5min for some routes, 10min for others) causing potential inconsistencies
- **Simplified:** Unified 5min cache for all routes + cache invalidation endpoint triggered after data writes
- **Rationale:** Eliminates data inconsistencies; provides freshness mechanism
- **Impact:** Consistent user experience; cache invalidation ensures data freshness after predictor job runs

### Source Documentation:
- **Detailed Fixes:** See `CRITICAL_ISSUES_FIXED.md` and `ALL_ISSUES_FOUND.md` for complete technical details
- **Total Issues Fixed:** 15 critical bugs, logic errors, API issues, and infrastructure problems
- **Review Sessions:** 5 comprehensive code reviews

### Critical Fixes Applied:

#### 1. ✅ SQL Bug: Rolled Forecast Column Reference (CRITICAL)
- **File:** `scripts/1m_feature_assembler.py`
- **Issue:** Query referenced wrong column for `rolled_forecast_7d_json`
- **Fix:** Corrected SQL to use `rolled_forecast_7d_json` column, not `signal_value`
- **Impact:** Prevents gate blend failure

#### 2. ✅ Pandas Deprecation: fillna(method=...)
- **File:** `scripts/train_quantile_1m_90models.py` (training script)
- **Issue:** `fillna(method='ffill')` deprecated in pandas 2.0+
- **Fix:** Use `.ffill().bfill().fillna(0)` chain
- **Impact:** Code compatibility with pandas 2.0+

#### 3. ✅ Schema Hash Inconsistency
- **File:** `scripts/1m_schema_validator.py`
- **Issue:** Hash calculation excluded `_` keys inconsistently
- **Fix:** Consistent exclusion of metadata keys (starting with `_`) from hash and feature count
- **Impact:** Prevents false schema validation failures

#### 4. ✅ NaN Handling Missing
- **File:** `scripts/1m_feature_assembler.py`
- **Issue:** NaN values not converted to 0.0
- **Fix:** Added `math.isnan()` check and conversion
- **Impact:** Prevents NaN values reaching model (would cause prediction errors)

#### 5. ✅ Missing Math Import
- **File:** `scripts/1m_feature_assembler.py`
- **Issue:** Used `math.isnan()` without import
- **Fix:** Added `import math`
- **Impact:** Prevents runtime error

#### 6. ✅ Prediction Output Shape Handling
- **File:** `scripts/1m_predictor_job.py`
- **Issue:** Only handled `[30,3]` and `[1,30,3]`, not flattened `[90]` format
- **Fix:** Added handling for `[90]` and `[1,90]` formats with reshape to `[30,3]`
- **Impact:** Works with all Vertex AI output formats

#### 7. ✅ Metadata Keys in Feature Type Conversion
- **File:** `scripts/1m_feature_assembler.py`
- **Issue:** Type conversion processed metadata keys (like `_rolled_forecast_7d`)
- **Fix:** Skip metadata keys (starting with `_`) during type conversion
- **Impact:** Prevents errors when metadata keys have non-numeric values

#### 8. ✅ API Route Parameterization Error
- **File:** `dashboard-nextjs/src/app/api/explain/route.ts`
- **Issue:** BigQuery params used incorrectly
- **Fix:** Use string replacement for `@future_day` parameter
- **Impact:** Prevents API route errors

#### 9. ✅ BigQuery DELETE Query Parameterization
- **Files:** `scripts/1m_predictor_job.py`, `scripts/1w_signal_computer.py`, `scripts/calculate_shap_drivers.py`
- **Issue:** Overly complex parameterization for DELETE queries
- **Fix:** Simplified to direct string interpolation
- **Impact:** Cleaner, more reliable DELETE operations

#### 10. ✅ Timestamp Format Consistency
- **Files:** All scripts writing timestamps
- **Issue:** Using `isoformat()` without UTC clarity
- **Fix:** Added 'Z' suffix for UTC: `datetime.utcnow().isoformat() + 'Z'`
- **Impact:** Clear UTC timestamps, avoids timezone confusion

#### 11. ✅ BigQuery Location Not Specified
- **File:** `scripts/create_all_tables.py`
- **Issue:** Queries didn't specify location
- **Fix:** Added explicit `location='us-central1'` to all queries
- **Impact:** Ensures queries run in correct region

#### 12. ✅ Traffic Split Validation Logic
- **File:** `scripts/health_check.py`
- **Issue:** Only checked `deployed_model_id`, not '0' format (first deployment)
- **Fix:** Handle both `deployed_model_id` and '0' as keys in traffic split
- **Impact:** Health check works for all deployment scenarios

#### 13. ✅ Gate Blend Loop Fix (Grok Patch)
- **File:** `scripts/1m_predictor_job.py`
- **Issue:** Loop blended D+1-14 but `rolled_forecast_7d` only has 7 values
- **Fix:** Truncate gate blend to D+1-7 only (use `range(7)`)
- **Impact:** Prevents index out of bounds error

#### 14. ✅ 1W Signal Merge Fix (Grok Patch)
- **File:** `scripts/1m_feature_assembler.py`
- **Issue:** `signals_1w` has `as_of_timestamp`, no `date` column for merge
- **Fix:** Pivot `signals_1w` with SQL `MAX(CASE WHEN signal_name = 'X' THEN signal_value END)` and join on timestamp
- **Impact:** Correct feature assembly with 1W signals

#### 15. ✅ API Route Completion (Grok Patch)
- **Files:** Multiple API routes
- **Issue:** Missing BigQuery client initialization, error handling
- **Fix:** Add `const bq = new BigQuery()` and proper try/catch blocks with error responses
- **Impact:** API routes work reliably

#### 16. ✅ Schema Contract System (Industrial-Grade Validation) - NEW
- **Files:** `scripts/generate_schema_contract.py`, `scripts/1m_predictor_job_interim.py`, `scripts/1m_schema_validator.py`, `scripts/1m_feature_assembler.py`
- **Issue:** AutoML models trained on `training_dataset_super_enriched` expect ALL 210 columns including target columns (target_1w, target_1m, target_3m, target_6m) as input features - presence required (can be None), not value. Current schema validation lacks structure, version locking, and precise mismatch diagnostics.
- **Fix:**
  - **Generate immutable schema contract:** `scripts/generate_schema_contract.py` exports all 210 columns from training dataset to `config/schema_contract.json` with version, source table, export date
  - **Fill missing schema fields:** `fill_missing_schema_fields()` function ensures ALL contract columns exist in prediction payload (targets as None)
  - **Precise CI validation:** Schema validator reports EXACT mismatches (missing vs extra keys), not vague errors
  - **Version locking:** Schema contract becomes immutable single source of truth
- **Impact:** Prevents AutoML prediction failures ("Missing struct property: target_1w"), enables industrial-grade validation with clear diagnostics, prevents schema drift

### Additional Technical Requirements (From Reviews):

#### ✅ 30-Day Target Creation
- **Training Script:** Must create 30 target columns (`target_D1` through `target_D30`) using `shift(-i)`, not just `shift(-1)`
- **Impact:** Each model predicts specific horizon, not just next day

#### ✅ 1W Signal Pivoting
- **Feature Assembler:** Must pivot `signals_1w` table (has `signal_name`, `signal_value` structure) to columns
- **SQL Pattern:**
  ```sql
  SELECT 
    MAX(CASE WHEN signal_name = 'volatility_score_1w' THEN signal_value END) AS volatility_score_1w,
    MAX(CASE WHEN signal_name = 'rolled_forecast_7d' THEN rolled_forecast_7d_json END) AS rolled_forecast_7d_json
  FROM signals_1w
  GROUP BY as_of_timestamp
  ```

#### ✅ Model Output Format Handling
- **Predictor Job:** Must handle multiple output formats:
  - `[30, 3]` - Correct shape
  - `[1, 30, 3]` - With batch dimension (remove it)
  - `[90]` or `[1, 90]` - Flattened (reshape to [30,3])
- **Impact:** Works regardless of Vertex AI container version

#### ✅ Feature Schema Validation
- **Validator:** Must exclude metadata keys (starting with `_`) from:
  - Feature count
  - Schema hash calculation
  - Type conversion
- **Impact:** Consistent validation across all scripts

#### ✅ Zero Fake Data Rule (CRITICAL BUSINESS REQUIREMENT)
- **All Routes:** NO placeholder data, NO fake information, NO mock data
- **Vegas Intel:** Must use real Glide API data
- **Legislative:** Must use real legislation sources
- **Breaking News:** Must use real Gemini/Grok summarization
- **Impact:** Dashboard integrity, user trust

### Known Risks (Documented, Not Bugs):

#### ⚠️ Custom Class Deployment Risk (ELIMINATED)
- **Original Risk:** Custom `MultiOutputQuantile` class might not load in sklearn container
- **Resolution:** Architecture changed to 90 standalone models (zero risk)
- **Status:** Risk eliminated by new architecture

---

## 🔍 COMPREHENSIVE STATE ANALYSIS

### ✅ What Exists (Reusable)
1. **Dashboard Infrastructure:**
   - Next.js app at `dashboard-nextjs/` with BigQuery client configured
   - BigQuery client library (`@google-cloud/bigquery`) installed
   - Existing routes under `/api/v4/forecast/*` reading from `daily_forecasts` (empty)

2. **Backend Infrastructure:**
   - FastAPI backend at `forecast/main.py` with `/api/vertex-predict` endpoint
   - Vertex AI initialized: `aiplatform.init(project="cbi-v14", location="us-central1")`
   - Google Cloud libraries installed

3. **Data Infrastructure:**
   - BigQuery dataset: `cbi-v14.forecasting_data_warehouse`
   - Tables exist: `soybean_oil_prices`, `daily_forecasts` (empty)
   - Feature sources: Phase 0/1 integrated (209 features) [[memory:9695396]]

4. **Model Assets:**
   - 1M Model ID: `274643710967283712` (confirmed in MASTER_TRAINING_PLAN.md) - **OR NEED TO TRAIN DISTILLED MODEL**
   - 1M Model Name: `soybean_oil_1m_model_FINAL_20251029_1147`
   - Performance: MAPE 2.5% (training), MAPE 1.98% (targeted)
   - **DECISION:** **Option A - Train new distilled LightGBM-Quantile model**
   - **Reason:** Existing model `274643710967283712` outputs **mean only** (no q10/q90)
   - **New Model:** LightGBM-Quantile with objectives [0.1, 0.5, 0.9] → native q10/mean/q90 output
   - **Features:** 213 total (209 Phase 0/1 + 4 1W signals)
   - **Training:** Reuse existing Level-0 features, train quantile model, deploy as single endpoint
   - **Expected MAPE:** 1.62% (vs 1.98% current) = **+18% improvement**

### ❌ Critical Gaps (Must Build)

#### 1. Endpoint Configuration
- **MISSING:** Vertex endpoint ID for 1M model (need to deploy or find existing)
- **MISSING:** Deployed model ID (after endpoint deployment)
- **MISSING:** Pinned config file with endpoint/deployed_model IDs
- **ISSUE:** Model ID mismatch - route.ts has `3156316301270450176`, but correct is `274643710967283712`

#### 2. Feature Assembly & Validation
- **MISSING:** `config/schema_contract.json` (CRITICAL - immutable contract with all 210 columns from training dataset)
- **MISSING:** `scripts/generate_schema_contract.py` (generates immutable schema contract)
- **MISSING:** `fill_missing_schema_fields()` function in predictor and assembler (ensures ALL contract columns present, targets as None)
- **MISSING:** `config/1m_feature_schema.json` (pinned schema with hash + min_coverage)
- **MISSING:** Feature assembler script (`scripts/1m_feature_assembler.py`) - must apply schema contract fill
- **MISSING:** Schema validator script (`scripts/1m_schema_validator.py`) - must use schema contract with precise mismatch reporting
- **MISSING:** Health check script (`scripts/health_check.py`)

#### 3. Prediction Pipeline (with 1W Gate Blend)
- **MISSING:** 1M predictor job (`scripts/1m_predictor_job.py`)
- **MISSING:** Feature injection: merge 209 features + latest 1W signals from `signals_1w` table
- **MISSING:** Vertex call returns q10/mean/q90 (from 3 separate endpoints - one per quantile)
- **MISSING:** Post-process gate blend: for D+1-7 only, apply weighted blend with rolled 1W forecast; D+8-30 pure 1M
- **MISSING:** Gate weight calculation: Simplified linear blend with kill-switch (`w = 0.75` default, `w = 0.95` if volatility > 0.85 or disagreement > 0.25)
- **MISSING:** Backfill logic with `--backfill-if-missing` flag
- **MISSING:** Idempotency/dedupe logic for `predictions_1m` table

#### 4. 1W Signal Computation (Offline, No Endpoint)
- **MISSING:** 1W signal computation job (`scripts/1w_signal_computer.py`) → computes volatility, momentum, delta, short_bias
- **MISSING:** `signals_1w` table schema (stores computed signals, not predictions)
- **MISSING:** Signal computation scheduler (hourly/daily Cloud Run job)
- **NOTE:** 1W signals injected as **features** into 1M model (not separate predictions)

#### 5. Aggregation & Materialization (Post-Process with Gate)
- **MISSING:** Aggregator SQL for q10/q90 (`bigquery_sql/create_agg_1m_latest.sql`)
- **MISSING:** Post-processing logic in predictor job: apply 1W gate blend for D+1-7 only
- **MISSING:** Gate weighting formula: Simplified linear blend (`w = 0.75` default) with kill-switch conditions
- **MISSING:** Dynamic quantile spread: `spread_pct = volatility_score_1w * 0.15` (replaces fixed 12%)
- **MISSING:** Materialized table `agg_1m_latest` (contains blended forecasts for D+1-7, pure 1M for D+8-30)
- **MISSING:** Divergence monitoring (kill-switch: if d>0.25 OR v>0.85, set w=0.95)
- **MISSING:** Scheduled aggregator job

#### 6. API Routes (New `/api/*` Structure)
- **MISSING:** `/app/api/forecast/route.ts` (unified 5min cache - revalidate=300)
- **MISSING:** `/app/api/volatility/route.ts` (unified 5min cache - revalidate=300)
- **MISSING:** `/app/api/strategy/route.ts` (unified 5min cache - revalidate=300)
- **MISSING:** `/app/api/vegas/route.ts` (unified 5min cache - revalidate=300)
- **MISSING:** `/app/api/explain/route.ts` (no cache, deterministic)

#### 7. BigQuery Tables
- **MISSING:** `predictions_1m` table (new schema: partitioned, clustered)
- **MISSING:** `signals_1w` table (new schema: partitioned, clustered)
- **MISSING:** `agg_1m_latest` table (materialized)
- **MISSING:** `legislation_events` table (for `/api/strategy`)
- **MISSING:** `vegas_sales` table (for `/api/vegas`)
- **OPTIONAL:** `api_audit_logs` table

#### 8. Dashboard Refactoring
- **MISSING:** Refactor existing components to use `/api/*` instead of direct BQ
- **MISSING:** ISR caching configuration in routes (unified 5min cache for all routes)
- **MISSING:** Cache invalidation endpoint (`/api/revalidate`) to refresh after predictor job writes
- **MISSING:** Rate limiting middleware

#### 9. Monitoring & Alerts
- **MISSING:** Job failure alerts
- **MISSING:** Zero-row alerts
- **MISSING:** Endpoint error alerts
- **MISSING:** Budget alerts ($100 Vertex threshold)

#### 10. Documentation
- **MISSING:** Update `MASTER_TRAINING_PLAN.md` in place [[memory:10452553]]
- **MISSING:** Update `VERTEX_AI_INTEGRATION.md`
- **MISSING:** Operational runbook

---

## 🎯 EXECUTION PRIORITIES (Phase-by-Phase)

### ⚠️ **PHASE 0: DATA FRESHNESS AUDIT & REFRESH (1h) - CRITICAL FIRST**

**AUDIT FINDINGS (November 1, 2025):**
- ✅ **Fresh Data (≤2 days):** soybean_oil_prices (2025-10-30), corn_prices (2025-10-30), weather_data (2025-10-31)
- ⚠️ **Stale Data (3-7 days):** currency_data (2025-10-27), palm_oil_prices (2025-10-24)
- ❌ **Very Stale (8+ days):** crude_oil_prices (2025-10-21), vix_daily (2025-10-21)
- ❌ **CRITICAL BLOCKER:** training_dataset_super_enriched (2025-10-13, **19 days old**)

**Action Required BEFORE Phase 1:**
1. **Update stale source data:**
   - Update crude_oil_prices (11 days stale)
   - Update vix_daily (11 days stale)
   - Update palm_oil_prices (8 days stale)
   - Update currency_data (5 days stale)

2. **Refresh training_dataset_super_enriched:**
   - Extend from 2025-10-13 to latest date (target: 2025-10-30+)
   - Verify all 205 features computed correctly
   - **AUDIT CHECKPOINT:** Verify column count = 205 (210 total - 4 targets - 1 date)
   - **AUDIT CHECKPOINT:** Verify no NULLs in key features (zl_price_current, crude_price, palm_price, vix_level)

3. **Verify feature sources:**
   - ✅ FX z-scores: `vw_fx_all` view → `currency_data` table (VERIFIED)
   - ✅ FX rates: `vw_economic_daily` → `economic_indicators` table (VERIFIED)
   - ✅ FX 7d_change: `fx_derived_features` table (VERIFIED - latest 2025-10-28)
   - ⚠️ Verify derived feature tables are fresh: `volatility_derived_features`, `fundamentals_derived_features`, `monetary_derived_features`

**Files:**
- See `AUDIT_FINDINGS_DATA_SCHEMA_NOV1.md` for complete data freshness audit
- See `FEATURE_LOGIC_AUDIT_COMPLETE.md` for complete feature source mapping

**Time Estimate:** 1 hour (source data updates + training dataset refresh)

---

### Phase 1: Train BQML Models (All 4 Horizons with Quantiles) (2h) - CRITICAL FIRST

**⚠️ PREREQUISITE:** Phase 0 must complete successfully (fresh training dataset with latest data)

**AUDIT FINDINGS INTEGRATED:**
- ✅ **Schema Verified:** 205 features (210 total - 4 targets - 1 date)
- ✅ **Feature Types:** 160 FLOAT64, 43 INT64, 2 STRING (categorical: market_regime, volatility_regime)
- ✅ **BQML Compatible:** All feature types supported (STRING handled via one-hot encoding)
- ✅ **FX Features Verified:** All 7 FX features have verified sources and logic
- ✅ **No NULLs:** Recent rows have all key features populated
- ✅ **No Constants:** All features have variance (checked in audit)
**Why First:** Need working models before predictions. BQML eliminates Vertex deployment complexity entirely.

**Architecture Decision:** 4 BQML BOOSTED_TREE mean models (1W, 1M, 3M, 6M) + residual quantiles. Zero endpoints, zero deployment risk, zero cost. **ALL 205 FEATURES**, **MAX ACCURACY SETTINGS**.

1. **Create features view (NO LABEL LEAKAGE):**
   - SQL: `bigquery_sql/create_features_clean.sql`
   - View: `models_v4.features_1m_clean`
   - Query: `SELECT * EXCEPT(date, target_1w, target_1m, target_3m, target_6m) FROM training_dataset_super_enriched`
   - **Critical:** Explicitly exclude ALL target columns to prevent label leakage
   - Features: **205 columns** ✅ VERIFIED (210 total - 4 targets - 1 date)
   - This view is used for ALL model training (1W, 1M, 3M, 6M)
   - **AUDIT CHECKPOINT #1:** After creation, verify column count = 205

2. **Create BQML training SQL scripts (4 mean models + residual computation):**
   - `bigquery_sql/train_bqml_1w_mean.sql` (MAX ACCURACY)
   - `bigquery_sql/train_bqml_1m_mean.sql` (MAX ACCURACY)
   - `bigquery_sql/train_bqml_3m_mean.sql` (MAX ACCURACY)
   - `bigquery_sql/train_bqml_6m_mean.sql` (MAX ACCURACY)
   - `bigquery_sql/compute_residual_distributions.sql` (for quantiles)
   - Template (MAX ACCURACY SETTINGS):
   ```sql
   CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_1m_mean`
   OPTIONS(
     model_type='BOOSTED_TREE_REGRESSOR',
     input_label_cols=['target_1m'],
     data_split_method='AUTO_SPLIT',
     max_iterations=100,        -- MAX: More trees for accuracy
     early_stop=True,            -- MAX: Prevents overfitting
     l2_reg=0.1,                 -- MAX: Regularization
     max_tree_depth=8,           -- MAX: Deeper trees (vs default 6)
     min_split_loss=0.01,        -- MAX: Fine-grained splits
     subsample=0.8               -- MAX: Row subsampling
   ) AS
   SELECT * FROM `cbi-v14.models_v4.features_1m_clean`
   WHERE target_1m IS NOT NULL
   ```

3. **Train all models (run SQL in BigQuery console or via Python):**
   - Script: `scripts/train_all_bqml_models.py` (Python wrapper to execute SQL)
   - Models to create: 12 total (1W/1M/3M/6M × mean/q10/q90)
   - Training time: ~2-3 hours total (can run in parallel)
   - Cost: $0 (within free tier for 1.25K rows)
   - Validate each model after training:
   ```sql
   SELECT * FROM ML.EVALUATE(MODEL `cbi-v14.models_v4.bqml_1m_mean`)
   ```

4. **No deployment step needed:**
   - BQML models live in BigQuery - no endpoints to deploy
   - No traffic splits to configure
   - No container images to build
   - No Vertex AI infrastructure

5. **Create config file:**
   - `config/bqml_models_config.json`
   - Fields: `models` dict with model names, horizons, quantiles
   - Example: `{"1m_mean": "cbi-v14.models_v4.bqml_1m_mean", ...}`
   - Mark: `architecture='bqml'`, `model_type='BOOSTED_TREE_REGRESSOR'`

6. **Validate models (test predictions):**
   - Script: `scripts/validate_bqml_models.py`
   - For each model: Run `ML.PREDICT` with latest features
   - Verify output format matches expected schema
   - Log MAE/RMSE metrics

7. **Feature schema export (for validation):**
   - Script: `scripts/export_bqml_feature_schema.py`
   - Query: `SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = 'features_1m_clean'`
   - Export to: `config/bqml_feature_schema.json`
   - Include: field names, types (no schema contract needed - BigQuery enforces schema automatically)

### Phase 2: BQML Batch Predictions with 1W Gate (1h)
**Why Second:** Core prediction pipeline using ML.PREDICT (no endpoints needed)

1. **Build feature assembler (with 1W signal injection):**
   - `scripts/1m_feature_assembler.py` (SIMPLIFIED - no schema contract needed for BQML)
   - Reads from Phase 0/1 sources (209 features)
   - Fetches latest 1W signals from `signals_1w` table
   - Injects 1W signals as features: `volatility_score_1w`, `delta_1w_vs_spot`, `momentum_1w_7d`, `short_bias_score_1w`
   - Outputs: 213-column feature row (209 base + 4 1W signals)
   - **Note:** BigQuery enforces schema automatically - no manual validation needed

2. **Build BQML predictor job (SQL-based predictions):**
   - `scripts/1m_predictor_job_bqml.py` (NEW - replaces Vertex predictor)
   - **Flow:** Assemble features → Write to temp table → Call ML.PREDICT (3 times for q10/mean/q90) → Combine results → Apply gate blend
   - **Prediction SQL template:**
   ```sql
   -- Get mean prediction
   SELECT predicted_target_1m as mean_1m
   FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_1m_mean`,
     (SELECT * FROM temp_features))
   
   -- Get q10 prediction
   SELECT predicted_target_1m as q10_1m
   FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_1m_q10`,
     (SELECT * FROM temp_features))
   
   -- Get q90 prediction
   SELECT predicted_target_1m as q90_1m
   FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_1m_q90`,
     (SELECT * FROM temp_features))
   ```
   - **Parse output:** Combine 3 predictions into single row (q10, mean, q90)
   - **Post-process gate blend for D+1-7 only:**
     - Fetch latest 1W signals from `signals_1w` table
     - Fetch rolled 1W forecast (7-day path) from historical 1W signals
     - For each day D+1 to D+7:
       - Calculate disagreement: `d = |F_1W_7 - mean_1M| / mean_1M`
       - Calculate weight: `w = 0.75` (default balanced blend)
       - Kill-switch: if `abs(d) > 0.25` OR `volatility_score_1w > 0.85`, set `w = 0.95` (trust 1M)
       - Blend mean: `mean = w * mean_1M + (1-w) * rolled_1W`
       - Blend q10/q90 with dynamic spread: 
         - `spread_pct = volatility_score_1w * 0.15` (dynamic: 0-15% based on volatility)
         - `q10 = w * q10_1M + (1-w) * (rolled_1W * (1 - spread_pct))`
         - `q90 = w * q90_1M + (1-w) * (rolled_1W * (1 + spread_pct))`
   - **D+8-30:** Pure 1M (no blend): use BQML output as-is
   - Write predictions to BigQuery: one row per future_day
   - Idempotent: dedupe by (as_of_timestamp, future_day)
   - **After successful BigQuery write:** Call `/api/revalidate` endpoint to invalidate cache

3. **Create predictions_1m table:**
   - `bigquery_sql/create_predictions_1m_table.sql` (same schema as before)
   - Columns: `as_of_timestamp`, `future_day`, `q10`, `mean`, `q90`, `gate_weight`, `blended`, `model_version`
   - Partitioned by DATE(as_of_timestamp)
   - Clustered by (future_day, model_version)

4. **Test end-to-end:**
   - Run BQML predictor job once
   - Verify ML.PREDICT calls succeed for all 3 models (q10/mean/q90)
   - Verify rows written for D+1-30 (D+1-7 blended, D+8-30 pure)
   - Verify gate weight uses simplified linear blend (w = 0.75 default, w = 0.95 with kill-switch)
   - Verify dynamic quantile spread (volatility-based: `spread_pct = volatility_score_1w * 0.15`)
   - **After BigQuery write:** Verify `/api/revalidate` cache invalidation works

### Phase 3: 1W Signal Computation (Offline, No Endpoint) (45min)
**Why Third:** Compute 1W signals as features + gate input (NOT a separate model)

1. **Create 1W signal computation job:**
   - `scripts/1w_signal_computer.py`
   - Computes from historical price data:
     - `volatility_score_1w`: annualized volatility (rolling 7-day)
     - `delta_1w_vs_spot`: (F_1W - spot) / spot
     - `momentum_1w_7d`: 7-day price momentum
     - `short_bias_score_1w`: bias indicator (optional)
   - Also computes rolled 1W forecast path (7-day ahead) for gate blending
   - Writes to `signals_1w` table

2. **Create signals_1w table:**
   - `bigquery_sql/create_signals_1w_table.sql`
   - Columns: `as_of_timestamp`, `signal_name`, `signal_value`, `model_version`, `source='offline'`
   - Special rows: `signal_name='rolled_forecast_7d'` with `signal_value` as JSON array of 7-day path
   - Partitioned by DATE(as_of_timestamp)
   - Clustered by signal_name

3. **Create signal computation scheduler:**
   - Cloud Scheduler job: hourly
   - Triggers `1w_signal_computer.py` (Cloud Run job)
   - No Vertex endpoint needed

### Phase 4: Aggregation & Materialization (Simple, No Ensemble Join) (30min)
**Why Fourth:** API routes need materialized data (already blended in predictor job)

1. **Create aggregator SQL:**
   - `bigquery_sql/create_agg_1m_latest.sql`
   - Simple aggregation from `predictions_1m` (already contains blended forecasts)
   - `SELECT future_day, AVG(mean) mean, PERCENTILE_CONT(q10, 0.1) q10, PERCENTILE_CONT(q90, 0.9) q90, AVG(gate_weight) avg_gate_weight`
   - FROM `predictions_1m` WHERE `as_of_timestamp >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)`
   - GROUP BY `future_day`
   - **NOTE:** No join needed - blending already done in predictor job

2. **Create materialized table:**
   - `CREATE OR REPLACE TABLE agg_1m_latest AS ...` (from aggregator SQL)

3. **Create aggregation scheduler:**
   - Cloud Scheduler job: hourly (after predictor job)
   - Refreshes `agg_1m_latest`
   - **After aggregation completes:** Trigger cache invalidation endpoint (ensure dashboard reflects latest aggregated data)

### Phase 5: API Routes (1h)
**Why Fifth:** Dashboard integration layer

1. **Create `/app/api/forecast/route.ts`:**
   - `export const revalidate = 300` (unified 5min cache)
   - Query `agg_1m_latest` ORDER BY `future_day`
   - Response: `[{future_day, mean, q10, q90}]`
   - Headers: `Cache-Control: s-maxage=300, stale-while-revalidate=60`

2. **Create `/app/api/volatility/route.ts`:**
   - `export const revalidate = 300` (unified 5min cache)
   - Query `signals_1w` ORDER BY `as_of_timestamp DESC LIMIT 100`
   - Response: `[{as_of_timestamp, signal_name, signal_value}]`

3. **Create `/app/api/strategy/route.ts`:**
   - `export const revalidate = 300` (unified 5min cache - changed from 600 for consistency)
   - JOIN `agg_1m_latest` + `signals_1w` + `legislation_events`
   - Response: `{forecast: [...], signals: [...], policy: [...]}`

4. **Create `/app/api/vegas/route.ts`:**
   - `export const revalidate = 300` (unified 5min cache - changed from 600 for consistency)
   - Query `vegas_sales` ORDER BY `date DESC LIMIT 365`
   - Response: `[{date, sales, region}]`

**Cache Invalidation (CRITICAL OPERATIONAL REQUIREMENT):**
   - Create `/app/api/revalidate/route.ts` (admin-only, triggered after predictor job writes)
   - **After `1m_predictor_job.py` writes to BigQuery, MUST call this endpoint to invalidate cache**
   - Uses Next.js `revalidateTag()` or `revalidatePath()` for cache invalidation
   - **Cloud Scheduler Integration:** Set up heartbeat monitor - Cloud Scheduler pings invalidation endpoint after every predictor job completion
   - **Failure mode:** If invalidation fails, log error but continue (cache will refresh in 5min anyway, but invalidation ensures live freshness)
   - **Rationale**: Unified 5min cache + invalidation on write = consistency + freshness. "Fast dashboard" means *live freshness*, not "5 minutes ago this might've been right."

5. **Create `/app/api/explain/route.ts`:**
   - No cache
   - Request body: `{conf, delta, shap_china}`
   - Deterministic rules:
     - `if (delta > 15%)` → `"⚠️ 1W DIVERGENCE: Short-term reversal risk"`
     - `if (shap_china < -0.1)` → `"🇨🇳 China imports drag (negative impact)"`
     - `else` → `"📈 Stable: ${conf}% confidence"`

6. **Create helper tables (if needed):**
   - `legislation_events` table (can be empty initially)
   - `vegas_sales` table (can be empty initially)

### Phase 6: Dashboard Refactoring & Advanced Components (2h)
**Why Sixth:** Connect dashboard + add Risk Radar, Substitution Economics, Procurement Optimizer

1. **Update existing components:**
   - Replace direct BQ calls with `/api/*` fetches
   - Use `fetch('/api/forecast')` instead of `executeBigQueryQuery(...)`
   - Preserve existing UI/UX

2. **Create Risk Radar Component:**
   - API: `/api/v4/risk-radar` 
   - Data sources: Volatility + SHAP std + Policy events + VIX
   - Visualization: Radar chart (Nivo) with combined stress drivers index
   - Metrics: volatility_score_1w + VIX stress + tariff_threat + china_relations
   - Output: Combined risk score (0-100), breakdown by category

3. **Create Substitution Economics Component:**
   - API: `/api/v4/substitution-economics`
   - Data sources: ZL–FCPO spread, ZL–canola spread, ZL–ZM crush margin
   - Visualization: Waterfall or stacked bar chart
   - Logic: Calculate switching points, procurement cost comparison
   - Output: Substitution risk score, cost delta by commodity

4. **Create Procurement Optimizer (integrated with Phase 8):**
   - Uses agg_1m_latest + current prices
   - Highlights optimal buy windows (green zones on forward curve)
   - Calculates savings potential vs current price
   - Output: "Best buy window: D+14-21, save $X/cwt"

5. **Add rate limiting (optional):**
   - Middleware for IP-based rate limiting
   - Protect BigQuery from excessive calls

### Phase 7: Monitoring & Alerts (30min)
**Why Seventh:** Operational visibility

1. **Configure Cloud Monitoring alerts:**
   - Job failure alerts (Cloud Scheduler)
   - Zero-row alerts (if predictions_1m has no rows in 25h)
   - Endpoint error alerts (if Vertex predict fails)

2. **Configure budget alerts:**
   - Vertex AI node hours: Alert at $100 threshold
   - BigQuery: Alert at $50 threshold (if needed)

### Phase 8: Forward Curve & Dashboard Integration (45min) - **ADDED**
**Why Eighth:** Critical dashboard feature users expect

1. **Update forward curve route:**
   - Modify `/app/api/v4/forward-curve/route.ts`
   - Read from `agg_1m_latest` instead of `monthly_vertex_predictions`
   - Map `future_day` (1-30) to actual dates (current_date + future_day)
   - Include q10/q90 bands in response
   - Response: `[{date, price: mean, q10, q90, future_day}]`

2. **Verify existing dashboard routes:**
   - Test `/api/v4/procurement-timing` (update to use `agg_1m_latest` if needed)
   - Verify other routes still work with new data structure

### Phase 9: SHAP Integration with Business Labels & Chart Events (1.5h) - **ADDED**
**Why Ninth:** Core explainability feature for dashboard - translate technical → business language

1. **Create business label mapping:** ✅ **COMPLETE**
   - File: `config/shap_business_labels.json` - **CREATED & EXPANDED**
   - Maps technical feature names → business labels + interpretations
   - **Total: 226 features** (205 training features + 4 1W signals + 17 user examples)
   - Categories: FX, Demand, Processing, Policy, Weather, Logistics, Substitution, Sentiment, Supply, Energy, Volatility, Momentum, Positioning, Price, Correlation, Other
   - All features have business labels, interpretations, and category assignments
   - Purpose: Consistent business language across dashboard

2. **SHAP calculation using BQML ML.EXPLAIN_PREDICT:**
   - Script: `scripts/calculate_shap_drivers_bqml.py` (NEW - SQL-based explanations)
   - Use BQML's built-in explainability: `ML.EXPLAIN_PREDICT` returns Shapley values for each feature
   - SQL template:
   ```sql
   INSERT INTO `cbi-v14.forecasting_data_warehouse.shap_drivers`
   SELECT 
     CURRENT_TIMESTAMP() as as_of_timestamp,
     14 as future_day,  -- or parameterize
     feature,
     bl.business_label,
     attribution as shap_value,
     bl.interpretation,
     bl.category,
     'bqml_1m_mean' as model_version
   FROM ML.EXPLAIN_PREDICT(
     MODEL `cbi-v14.models_v4.bqml_1m_mean`,
     (SELECT * FROM features_1m_clean ORDER BY date DESC LIMIT 1)
   )
   LEFT JOIN `cbi-v14.config.shap_business_labels` bl
     ON feature = bl.feature_name
   ORDER BY ABS(attribution) DESC
   LIMIT 10
   ```
   - Load business labels from `config/shap_business_labels.json` (upload to BigQuery table for JOIN)
   - For each feature, fetch current value and historical value (7-day or 30-day ago)
   - Calculate feature % change: `feature_change_pct = (current - historical) / historical * 100`
   - Calculate dollar impact: `dollar_impact = shap_value * predicted_price` (approximation)
   - Store in BigQuery: `shap_drivers` table
   - Include: `feature_current_value`, `feature_historical_value`, `feature_change_pct` for tooltip formatting
   - **Optional:** Add daily LLM summary (Grok API) for executive briefing (cost: $0.03/day = $11/month)

3. **Update `/api/v4/price-drivers`:**
   - Read SHAP contributions from `shap_drivers` table
   - Sort by absolute `dollar_impact` DESC
   - Return top 10 drivers with business-friendly format
   - Format: "{business_label}: {interpretation} → {direction} impact: ${dollar_impact:.2f}/bu"
   - Example: "China Import Volume (30-Day): Higher imports → stronger demand → bullish impact: +$2.34/bu"

4. **Enhance `/api/explain` with deterministic template formatting:**
   - Request params: `{future_day, prediction_change_pct, prediction_id?}`
   - Query `shap_drivers` for top 2-3 contributors (by absolute SHAP value)
   - Join with feature history to calculate % changes: `(current - historical) / historical * 100`
   - Format using deterministic template:
     - `"Price {price_change:+.1f}% (D+{future_day}). Driver: {feature1_label} {feature1_change:+.1f}%, {feature2_label} {feature2_change:+.1f}%."`
   - Example output: `"Price +2.8% (D+14). Driver: U.S. crush margins +18%, China imports +11%."`
   - Fallback: If SHAP unavailable, use deterministic rules with volatility/delta info
   - Include confidence context from q10/q90 bands

5. **Create `/api/chart-events` for overlay annotations:**
   - Purpose: Explain historical price movements on charts
   - Query: `{start_date, end_date}` or `{lookback_days: 365}`
   - Source: `legislation_events` table + SHAP analysis for those dates
   - Logic:
     - Fetch major events in date range (tariff hikes, policy changes, weather events)
     - For each event, query historical SHAP values at that date
     - Match event to price movement (find price change around event date)
     - Generate explanation: `"The {price_direction} on {date} was due to {event_title}: {event_description}. Drivers: {top_shap_drivers}."`
   - Response: `[{date, event_title, event_type, price_change_pct, explanation, drivers: [{label, change}]}]`
   - Used by: Forward curve chart overlays, historical price charts

6. **Create `shap_drivers` table:**
   - `bigquery_sql/create_shap_drivers_table.sql`
   - Columns: `as_of_timestamp`, `future_day`, `feature_name`, `business_label`, `shap_value`, `feature_current_value`, `feature_historical_value`, `feature_change_pct`, `interpretation`, `dollar_impact`, `direction` (bullish/bearish/neutral), `category`, `model_version`
   - Partitioned by DATE(`as_of_timestamp`)
   - Clustered by (`future_day`, `feature_name`)
   - **Note:** Includes historical values to calculate % changes for tooltips

7. **Business value map integration:**
   - Reference document: Maps executive concepts to technical sources
   - **Procurement Timing**: `agg_1m_latest` + `signals_1w` → Forward curve overlay
   - **Why Did It Move?**: `shap_drivers` → Price Drivers panel with business labels
   - **Confidence Context**: q10/q90 → Dashboard confidence shading
   - **Substitution Pressure**: Commodity spreads → Substitution chart (verify route exists)
   - **FX Exposure**: USD/BRL, USD/ARS → Currency waterfall (verify route exists)
   - **Risk Lens**: Combined metrics → Risk Radar (verify route exists)
   - **Local Market Sync**: `vegas_sales` → Vegas overlay (verify route exists)

8. **Chart event annotations system:**
   - Create `/app/api/chart-events/route.ts`:
     - Query `legislation_events` table for events in date range
     - For each event, fetch historical SHAP values from `shap_drivers` at that date
     - Calculate price movement around event (e.g., ±3 days)
     - Generate explanation linking event to price movement
     - Format: `"The {drop/rise} on {date} was due to {event_title}: {event_description}. Drivers: {top_shap_drivers}."`
   - Update forward curve chart to display event overlays:
     - Render event markers on chart at event dates
     - Show tooltip with explanation on hover
     - Example: "Why did price drop here? The drop on 2024-10-15 was due to tariff hikes: U.S. announced 25% tariff on Chinese imports. Drivers: China imports -15%, Trade war impact +22%."

### Phase 11: Breaking News + Big-8 Refresh (30min) - **ADDED**
**Why Eleventh:** Critical data freshness for dashboard intelligence

1. **Verify/Activate Breaking News:**
   - Verify Gemini summarizer → `/api/v4/breaking-news` route
   - Ensure Big-8 (macro + energy + demand) refresh nightly
   - Feeds into Substitution Economics and Risk Radar
   - **ZERO FAKE DATA RULE:** All data must be real, sourced from actual feeds

2. **Big-8 Data Refresh:**
   - Verify nightly refresh job for Big-8 signals
   - Ensure all 8 critical signals updated daily
   - Monitor for stale data (>24h old)

### Phase 12: Vegas Intel + Glide Integration (2h) - **ADDED**
**Why Twelfth:** Local market intelligence for Kevin's sales team

1. **Glide API Integration:**
   - Create Glide export script for customer data
   - Fetch real-time customer consumption via Glide API
   - **ZERO FAKE DATA RULE:** No placeholder data

2. **Vegas Events Scraper:**
   - Scrape casino events (conferences, tournaments, etc.)
   - Map to oil consumption windows
   - Store in `vegas_events` table

3. **Create Vegas APIs:**
   - `/api/v4/vegas-customers` - Customer list from Glide
   - `/api/v4/vegas-volume` - Consumption tracking
   - `/api/v4/vegas-events` - Upcoming casino events
   - `/api/v4/vegas-opportunities` - Sales opportunities (events + oil stock-up pitches)
   - `/api/v4/vegas-config` - Kevin-editable metrics configuration page

4. **Create Vegas Tables:**
   - `vegas_customers` - Customer data from Glide
   - `vegas_events` - Casino event calendar
   - `vegas_calculation_config` - Kevin's editable metrics (e.g., gallons per customer, markup %)
   - `vegas_sales_opportunities` - Calculated opportunities

5. **Admin Page:**
   - Create Kevin-editable configuration page
   - Allow adjustment of calculation metrics (gallons/customer, markup, etc.)
   - Store in `vegas_calculation_config` table

### Phase 13: Legislative Dashboard (3h) - **ADDED**
**Why Thirteenth:** Critical policy intelligence for procurement decisions

1. **Install Charting Packages:**
   - Install: Recharts, ECharts/ApexCharts, Nivo
   - Configure for Next.js SSR compatibility
   - Dynamic imports for performance

2. **Create Legislative Data Tables:**
   - `legislation_events` - Biofuels mandates, trade deals, tariffs
   - `tariff_data` - Historical and current tariff rates
   - `trade_deals` - Trade agreement details
   - `all_bills` - Congressional bills (filtered for soy relevance)
   - `lobbying` - Lobbying spend data

3. **Create Legislative APIs (5 modules):**
   - `/api/v4/biofuels-mandates` - RFS/RED III tracking, mandate simulator
   - `/api/v4/trade-tariffs` - Tariff waterfall chart, timeline slider
   - `/api/v4/bills-lobbying` - Top 10 bills, lobbying heatmap, passage odds
   - `/api/v4/traceability-risk` - EU CBAM compliance, risk dial, geo-map
   - `/api/v4/policy-simulator` - Multi-slider "what-if" tool

4. **AI Curation:**
   - Use Grok (or Gemini) to summarize bills and policy impacts
   - Rank by "soybean relevance score" (keyword + lobby $)
   - Generate plain-English impact summaries
   - Example: "This biofuel bill lifts demand 15% but raises compliance costs $2M"

5. **Dashboard Components:**
   - Biofuels Mandates Tracker with interactive simulator
   - Trade Deals & Tariff Monitor with waterfall charts
   - Bill & Lobbying Tracker with heatmaps
   - Deforestation & Traceability Watchlist with risk dials
   - Policy Impact Simulator with multi-slider dashboard

### Phase 14: Currency Waterfall (1h) - **ADDED**
**Why Fourteenth:** FX impact visualization for procurement decisions

1. **Create Currency Impact Table:**
   - `currency_impact` table
   - Columns: `date`, `pair`, `close_rate`, `pct_change`, `impact_score`, `source_name`
   - 5 FX pairs: USD/BRL, USD/ARS, USD/MYR, USD/IDR, USD/CNY
   - Partitioned by `date`, clustered by `pair`

2. **Create Currency Waterfall API:**
   - `/api/v4/currency-waterfall` route
   - Query `currency_impact` for all 5 pairs
   - Return cumulative impact on procurement costs
   - Use Plotly or Recharts waterfall series

3. **Dashboard Display:**
   - Each FX pair: mini waterfall component or stacked
   - Labels: 🇧🇷 Brazil Real, 🇦🇷 Argentina Peso, 🇲🇾 Malaysia Ringgit, 🇮🇩 Indonesia Rupiah, 🇨🇳 China Yuan
   - Show cumulative impacts on procurement cost volatility

### Phase 10: Documentation & Finalization (30min)
**Why Tenth:** Preserve knowledge, update plan

1. **Update MASTER_TRAINING_PLAN.md:**
   - Section: "1M Core + 1W Signal - PRODUCTION"
   - Status: 1M endpoint live, 1W BQML live, API routes live
   - Cost: ~$45/mo (Vertex $40 + BQML $5)

2. **Update VERTEX_AI_INTEGRATION.md:**
   - Add: Endpoint pinning, traffic split management
   - Add: BQML 1W architecture
   - Add: API caching strategy

3. **Create runbook:**
   - `docs/OPERATIONAL_RUNBOOK.md`
   - Sections: Endpoint rotation, recovery from no-traffic-split, BQML retrain

4. **Final verification:**
   - Run health check
   - Run predictor job (test)
   - Verify API routes return data
   - Verify dashboard renders correctly

---

## 📋 FILE CREATION CHECKLIST

**Last Updated:** 2025-10-31  
**Status:** Plan updated with architectural simplifications. Ready for execution.

### Config Files (4 files)
- [x] `config/shap_business_labels.json` (feature → business label mapping) - **COMPLETE: 226 features (205 training + 4 1W + examples)**
- [ ] `config/vertex_1m_config.json` (UPDATED: stores 3 endpoint IDs - q10_endpoint_id, mean_endpoint_id, q90_endpoint_id)
- [ ] `config/1m_feature_schema.json` (pinned schema with hash + min_coverage, excludes metadata keys starting with `_`)
- [ ] `config/1m_model_manifest.json` (NEW: lists all 90 models with paths: {quantile}_D{day}.pkl)

### Python Scripts (8 files)
- [ ] `scripts/train_quantile_1m_90models.py` (NEW - trains 90 models with warm-start, quantile reuse, memory-mapped features, checkpointing)
- [ ] `scripts/deploy_quantile_endpoints.py` (NEW - deploys 3 separate Vertex AI endpoints: q10, mean, q90)
- [ ] `scripts/health_check.py` (UPDATE - validates all 3 endpoints, checks traffic splits, tests predictions return [30] arrays)
- [ ] `scripts/1m_feature_assembler.py` (with 1W signal injection, pivots signals_1w table, handles NaN values, skips metadata keys)
- [ ] `scripts/1m_schema_validator.py` (validates feature hash, excludes metadata keys, checks min_coverage)
- [ ] `scripts/1m_predictor_job.py` (UPDATE - calls 3 endpoints, combines to [30,3] array, **simplified gate blend**: w=0.75 default, w=0.95 kill-switch, **dynamic quantile spread**: volatility_score_1w * 0.15, calls /api/revalidate after BigQuery write)
- [ ] `scripts/1w_signal_computer.py` (offline signal computation, no endpoint, computes volatility/momentum/delta/short_bias, stores rolled_forecast_7d_json)
- [ ] `scripts/calculate_shap_drivers.py` (UPDATE - works with 3 separate quantile models, computes SHAP on representative horizons D+7, D+14, D+30)

### BigQuery SQL (4 files)
- [ ] `bigquery_sql/create_predictions_1m_table.sql` (with q10/mean/q90, gate_weight, blended columns)
- [ ] `bigquery_sql/create_signals_1w_table.sql` (stores computed signals + rolled forecast)
- [ ] `bigquery_sql/create_agg_1m_latest.sql` (simple aggregation, no ensemble join)
- [ ] `bigquery_sql/create_shap_drivers_table.sql` (stores SHAP contributions)

### API Routes (8 files - 6 new + 2 updates)
- [ ] `dashboard-nextjs/src/app/api/forecast/route.ts` (NEW - unified 5min cache, reads from agg_1m_latest, returns future_day/mean/q10/q90)
- [ ] `dashboard-nextjs/src/app/api/volatility/route.ts` (NEW - unified 5min cache, reads from signals_1w, returns latest signals)
- [ ] `dashboard-nextjs/src/app/api/strategy/route.ts` (NEW - unified 5min cache, joins agg_1m_latest + signals_1w + legislation_events)
- [ ] `dashboard-nextjs/src/app/api/vegas/route.ts` (NEW - unified 5min cache, reads from vegas_sales table)
- [ ] `dashboard-nextjs/src/app/api/explain/route.ts` (NEW - no cache, deterministic template with SHAP drivers, format: "Price +X% (D+Y). Driver: ...")
- [ ] `dashboard-nextjs/src/app/api/chart-events/route.ts` (NEW - event annotations for charts, explains historical price movements with SHAP)
- [ ] `dashboard-nextjs/src/app/api/revalidate/route.ts` (NEW - admin-only cache invalidation endpoint, called after predictor job writes, uses revalidateTag/revalidatePath)
- [ ] `dashboard-nextjs/src/app/api/v4/forward-curve/route.ts` (UPDATE - use agg_1m_latest instead of monthly_vertex_predictions, map future_day to dates, include q10/q90 bands, add event overlays)

### Documentation (1 file)
- [ ] `docs/OPERATIONAL_RUNBOOK.md`

### Updates (3 files)
- [x] `MASTER_TRAINING_PLAN.md` (✅ UPDATED - architecture to 90-model, 3-endpoint setup, legacy work marked, dates updated to 2025-10-31)
- [ ] `VERTEX_AI_INTEGRATION.md` (update with 3-endpoint architecture, simplified gate blend, cache invalidation)
- [x] `FINAL_REVIEW_AND_EXECUTION_PLAN.md` (✅ UPDATED - Phase 1-2 with 90-model architecture, all simplifications documented)

### Additional API Routes (Phases 6, 11-14)
- [ ] `dashboard-nextjs/src/app/api/v4/risk-radar/route.ts` (Phase 6 - combined stress index from volatility + SHAP + VIX + policy)
- [ ] `dashboard-nextjs/src/app/api/v4/substitution-economics/route.ts` (Phase 6 - ZL–FCPO–canola spreads, switching points)
- [ ] `dashboard-nextjs/src/app/api/v4/breaking-news/route.ts` (verify/activate - Gemini summarizer, Big-8 refresh)
- [ ] `dashboard-nextjs/src/app/api/v4/vegas-customers/route.ts` (Glide API customer data - ZERO FAKE DATA)
- [ ] `dashboard-nextjs/src/app/api/v4/vegas-volume/route.ts` (consumption tracking from Glide)
- [ ] `dashboard-nextjs/src/app/api/v4/vegas-events/route.ts` (casino events calendar)
- [ ] `dashboard-nextjs/src/app/api/v4/vegas-opportunities/route.ts` (sales opportunities calculation)
- [ ] `dashboard-nextjs/src/app/api/v4/vegas-config/route.ts` (Kevin-editable metrics configuration)
- [ ] `dashboard-nextjs/src/app/api/v4/biofuels-mandates/route.ts` (RFS/RED III tracking, mandate simulator)
- [ ] `dashboard-nextjs/src/app/api/v4/trade-tariffs/route.ts` (tariff waterfall chart, timeline slider)
- [ ] `dashboard-nextjs/src/app/api/v4/bills-lobbying/route.ts` (top 10 bills, lobbying heatmap, passage odds)
- [ ] `dashboard-nextjs/src/app/api/v4/traceability-risk/route.ts` (EU CBAM compliance, risk dial, geo-map)
- [ ] `dashboard-nextjs/src/app/api/v4/policy-simulator/route.ts` (multi-slider what-if tool)
- [ ] `dashboard-nextjs/src/app/api/v4/currency-waterfall/route.ts` (5 FX pairs: USD/BRL, USD/ARS, USD/MYR, USD/IDR, USD/CNY)

### Additional BigQuery Tables (Phases 11-14)
- [ ] `forecasting_data_warehouse.vegas_customers` (customer data from Glide API)
- [ ] `forecasting_data_warehouse.vegas_events` (casino events calendar)
- [ ] `forecasting_data_warehouse.vegas_calculation_config` (Kevin-editable metrics: gallons/customer, markup %, etc.)
- [ ] `forecasting_data_warehouse.vegas_sales_opportunities` (calculated opportunities from events + config)
- [ ] `forecasting_data_warehouse.legislation_events` (biofuels mandates, trade deals, tariffs)
- [ ] `forecasting_data_warehouse.tariff_data` (historical and current tariff rates)
- [ ] `forecasting_data_warehouse.trade_deals` (trade agreement details)
- [ ] `forecasting_data_warehouse.all_bills` (Congressional bills filtered for soy relevance)
- [ ] `forecasting_data_warehouse.lobbying` (lobbying spend data)
- [ ] `forecasting_data_warehouse.currency_impact` (FX impact data: date, pair, close_rate, pct_change, impact_score, source_name)

### Charting Packages (Phase 13)
- [ ] Install: `recharts` (forward curves, basic charts)
- [ ] Install: `echarts` + `echarts-for-react` (financial dashboards, waterfalls, candlesticks)
- [ ] Install: `@nivo/core` + `@nivo/line` + `@nivo/radar` (risk radar, heatmaps)
- [ ] Configure: Dynamic imports for Next.js SSR compatibility

### Scripts & Jobs (Additional for Phases 11-14)
- [ ] `scripts/glide_export_customers.py` (Glide API integration for Vegas customers)
- [ ] `scripts/vegas_events_scraper.py` (casino events scraping)
- [ ] `scripts/legislative_event_extractor.py` (extract from news/feeds for legislation_events)
- [ ] `scripts/currency_impact_calculator.py` (calculate FX impact scores for 5 pairs)

### Archived Files
- [ ] `scripts/train_distilled_quantile_1m.py` → `archive/train_distilled_quantile_1m.py` (replaced by train_quantile_1m_90models.py)

---

## ⚠️ CRITICAL VERIFICATION POINTS

### Before Execution:
1. ✅ Confirm 1M model ID: `274643710967283712` (not `3156316301270450176`)
2. ✅ Confirm BigQuery dataset: `cbi-v14.forecasting_data_warehouse`
3. ✅ Confirm Vertex project: `cbi-v14`, location: `us-central1`
4. ✅ Confirm feature source tables exist with 209 features
5. ✅ Confirm n1-standard-2 machine type availability

### During Execution:
1. ✅ All 3 endpoints exist and have deployed models
2. ✅ Traffic split = 100% to deployed models on each endpoint
3. ✅ **CRITICAL:** Schema validator passes before every predict (ABORT ON MISMATCH - non-negotiable)
4. ✅ No deploy/redeploy during prediction calls
5. ✅ Predictions written to `predictions_1m` successfully
6. ✅ Cache invalidation endpoint called after every BigQuery write (ensure live freshness)
7. ✅ Cloud Scheduler heartbeat configured to verify invalidation flow
8. ✅ API routes return valid JSON with cache headers (unified 5min cache)
9. ✅ Dashboard renders without errors

### After Execution:
1. ✅ Health check passes
2. ✅ End-to-end test: predictor → aggregator → API → dashboard
3. ✅ Budget alerts configured
4. ✅ Documentation updated
5. ✅ No orphaned views or unused tables [[memory:9706879]]

---

## 🚨 RISK MITIGATION

### Risk: Endpoint Redeployment
**Mitigation:** Pin endpoint ID in config, validate traffic_split before every predict, remove deploy-on-predict code paths

### Risk: Schema Mismatch (CRITICAL)
**Mitigation:** Schema validator with hash + coverage checks, **ABORT ON MISMATCH** (non-negotiable)
- Validator runs before every prediction call
- Validator runs before every training run
- Validator runs before every deployment
- Failure mode: Job exits immediately with error code, does NOT proceed
- **Operational requirement:** Rogue NaN or column mismatch will ruin deployment - enforcement is mandatory

### Risk: BigQuery Cost Overrun
**Mitigation:** ISR caching (5m unified), materialized tables, rate limiting, budget alerts

### Risk: Stale Cache (CRITICAL)
**Mitigation:** Cache invalidation endpoint called after every BigQuery write + Cloud Scheduler heartbeat
- Predictor job calls `/api/revalidate` after successful write
- Aggregation job triggers invalidation after completion
- Cloud Scheduler monitors invalidation flow (heartbeat)
- Failure mode: Logs error but continues (cache refreshes in 5min, but invalidation ensures live freshness)
- **Operational requirement:** "Fast dashboard" means *live freshness*, not "5 minutes ago this might've been right."

### Risk: Empty Tables Day 1
**Mitigation:** Backfill flag, run predictor job immediately after deployment

### Risk: BQML Training Failure
**Mitigation:** Weekly retrain with error handling, fallback to previous model version

---

## 📊 SUCCESS METRICS

- **Endpoint Stability:** Zero redeploys in first 7 days
- **Prediction Latency:** p95 < 2s for Vertex predict
- **API Performance:** Cached responses < 300ms
- **Cost:** < $130/mo (Vertex $120 for 3 endpoints + signal $5 + BQ $5) OR < $50/mo (custom container $40 + signal $5 + BQ $5)
- **Dashboard Uptime:** 99.9% availability
- **Data Freshness:** Predictions updated hourly

---

## ✅ EXECUTION APPROVAL

**Ready to Execute:** YES  
**Estimated Time:** 16-18 hours total (BQML Architecture)
- Phase 1: 2h (BQML training - 12 models)
- Phase 2: 1h (BQML batch predictions with 1W gate)
- Phase 3: 45min (1W signal computation)
- Phase 4: 30min (Aggregation)
- Phase 5: 1h (API Routes)
- Phase 6: 2h (Dashboard + Risk Radar + Substitution Economics + Procurement Optimizer)
- Phase 7: 30min (Monitoring)
- Phase 8: 45min (Forward curve)
- Phase 9: 1.5h (SHAP integration with ML.EXPLAIN_PREDICT)
- Phase 10: 30min (Documentation)
- Phase 11: 30min (Breaking News + Big-8)
- Phase 12: 2h (Vegas Intel - 6 routes, 4 tables, Glide API)
- Phase 13: 3h (Legislative Dashboard - 5 modules, AI curation)
- Phase 14: 1h (Currency Waterfall - 5 FX pairs)

**Note:** Phase 1 increased from 1h to 1.5h due to 90-model training, but risk eliminated.  
**Critical Dependencies:** 
- Training dataset must exist (`models_v4.training_dataset_super_enriched`)
- 209 features available from Phase 0/1
- LightGBM training capability (Vertex AI or local)

**Rollback Plan:** 
- If 90-model training fails: fall back to existing `274643710967283712` (mean only, no quantiles)
- Disable schedulers, keep endpoints up, serve cached API responses
- Remove gate blend if causing issues (pure 1M only)

**Next Step:** Execute Phase 1 (Train 90 Models, Deploy 3 Endpoints) immediately. Zero deployment risk architecture.

---

## 📚 REFERENCE DOCUMENTATION

**CRITICAL:** The following documents contain detailed technical information that must be preserved:
- **`CRITICAL_ISSUES_FIXED.md`** - All critical bugs and fixes
- **`ALL_ISSUES_FOUND.md`** - Complete list of 15 issues found during reviews
- **`RESEARCH_BACKED_REVIEW.md`** - Research findings on Vertex AI compatibility, BigQuery timestamps, etc.

**NEVER DELETE THESE FILES.** They contain historical context and technical details needed for maintenance.

---

## 📊 EXPECTED OUTCOMES

**Accuracy:**
- Current: 1.98% MAPE (mean only)
- Target: 1.62% MAPE (distilled + gate) = **+18% improvement**

**Quantile Bands:**
- q10/q90 width: Dynamic based on volatility (0-15% spread: `spread_pct = volatility_score_1w * 0.15`)
- Full quantile coverage for confidence envelopes
- Width adapts to market conditions (higher volatility = wider bands)

**Cost:**
- Vertex endpoints: $40/mo × 3 = $120/mo (n1-standard-2 each, min=1, max=1) OR $40/mo with custom container
- Signal computation: $5/mo (Cloud Run jobs)
- **Total: $125/mo** (3 endpoints) OR **$45/mo** (custom container) vs $60/mo previously

**Performance:**
- Prediction latency: <1s p95
- API cached: <300ms
- Dashboard load: <2s

