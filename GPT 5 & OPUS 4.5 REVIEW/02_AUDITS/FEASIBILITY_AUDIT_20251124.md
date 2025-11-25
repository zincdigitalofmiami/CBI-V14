# 🔍 FEASIBILITY AUDIT: BQ Setup & Baseline Training Plan
**Date:** November 24, 2025  
**Status:** 🟡 NEEDS REVISION - Multiple Gaps Identified  
**Purpose:** Reconcile BQ_SETUP_AND_BASELINE_TRAINING_PLAN.md against Dataform, TFT, and Maximum Quality documentation

---

## 📋 AUDIT SUMMARY

### Overall Assessment: **PARTIALLY FEASIBLE - NEEDS UPDATES**

| Category | Current Plan | Required by Docs | Gap | Severity |
|----------|--------------|------------------|-----|----------|
| **Dataset Structure** | Uses existing tables | Dataform requires new structure | 🔴 HIGH | Critical |
| **Table Names** | `training.regime_calendar` | Dataform uses `reference.regime_calendar` | 🟡 MEDIUM | Naming |
| **Feature Table** | `features.pivot_math_daily` | Dataform uses `features.daily_ml_matrix` with STRUCTs | 🔴 HIGH | Schema |
| **Training Tables** | `training.zl_training_prod_allhistory_*` | Matches Dataform | ✅ GOOD | Aligned |
| **Baseline Model** | LightGBM | TFT doc recommends LightGBM + XGBoost comparison | ✅ GOOD | Aligned |
| **Training Config** | Basic params | Maximum Quality doc has specific params | 🟡 MEDIUM | Tuning |

---

## 🔴 CRITICAL GAPS

### Gap 1: Dataset Structure Mismatch

**Current Plan Uses:**
- `training.regime_calendar`
- `training.regime_weights`
- `features.pivot_math_daily`
- `features.daily_ml_matrix`

**Dataform Structure Requires:**
- `reference.regime_calendar` (not `training`)
- `reference.regime_weights` (not `training`)
- `features.technical_indicators` (separate from pivots)
- `features.crush_margin_daily` (separate table)
- `features.cross_asset_correlations` (missing from plan)
- `features.daily_ml_matrix` (master table with STRUCTs)

**Impact:** 🔴 **HIGH** - Tables created in wrong datasets will break Dataform DAG

**Fix Required:**
```sql
-- CORRECT: Create in reference dataset
CREATE TABLE `cbi-v14.reference.regime_calendar` ...
CREATE TABLE `cbi-v14.reference.regime_weights` ...

-- NOT: training.regime_calendar
```

---

### Gap 2: Missing Dataform Infrastructure

**Current Plan Assumes:**
- Direct SQL execution
- Manual table creation
- No Dataform DAG

**Dataform Requires (per DATAFORM_STRUCTURE_REVISED_20251124.md):**
- `dataform.json` configuration
- `definitions/01_raw/` declarations
- `definitions/02_staging/` incremental tables
- `definitions/03_features/` feature tables
- `definitions/04_training/` training tables
- `includes/constants.js` and `includes/feature_helpers.sqlx`
- Assertions for data quality

**Impact:** 🔴 **HIGH** - Without Dataform, no incremental updates, no data quality checks

**Fix Required:**
1. Create Dataform project structure
2. Migrate SQL to `.sqlx` files
3. Add assertions

---

### Gap 3: STRUCT Schema Not Implemented

**Current Plan:**
```sql
-- Simple flat INSERT
INSERT INTO `cbi-v14.training.zl_training_prod_allhistory_1w`
SELECT
  market_data.close AS close,
  pivots.P,
  regime.name AS regime_name
...
```

**Dataform Requires (per COMPLETE_BIGQUERY_DATASET_TABLE_BREAKDOWN_20251124.md):**
```sql
-- daily_ml_matrix with nested STRUCTs
CREATE TABLE features.daily_ml_matrix (
  date DATE,
  symbol STRING,
  market_data STRUCT<open FLOAT64, high FLOAT64, low FLOAT64, close FLOAT64, ...>,
  pivots STRUCT<P FLOAT64, R1 FLOAT64, R2 FLOAT64, ...>,
  policy STRUCT<tariff_events INT64, trump_sentiment FLOAT64, ...>,
  golden_zone STRUCT<crush_margin FLOAT64, china_imports FLOAT64, ...>,
  regime STRUCT<name STRING, weight FLOAT64, ...>
)
```

**Impact:** 🔴 **HIGH** - Plan assumes STRUCTs exist but doesn't create them

**Fix Required:**
1. Create `daily_ml_matrix` with full STRUCT schema
2. Use `ingest_features_hybrid.py` to populate with correct STRUCTs

---

### Gap 4: Missing Feature Tables

**Current Plan Has:**
- `pivot_math_daily` (pivots only)
- `daily_ml_matrix` (assumed)

**Dataform Requires (per COMPLETE_BIGQUERY_DATASET_TABLE_BREAKDOWN_20251124.md):**

| Table | Purpose | In Plan? |
|-------|---------|----------|
| `features.technical_indicators` | RSI, MACD, MAs | ❌ MISSING |
| `features.crush_margin_daily` | Crush spread | ❌ MISSING |
| `features.cross_asset_correlations` | ZL-FCPO, ZL-HO correlations | ❌ MISSING |
| `features.zl_contracts_matrix` | Contract-specific data | ❌ MISSING |
| `features.biodiesel_margin_daily` | Biofuel margin | ❌ MISSING |
| `features.weather_anomalies` | Weather z-scores | ❌ MISSING |
| `features.news_bucket_daily` | News aggregations | ❌ MISSING |
| `features.daily_ml_matrix` | Master feature table | ✅ In plan |

**Impact:** 🔴 **HIGH** - Training will have minimal features (only pivots + regime)

**Fix Required:**
Add Phase 2.5: Create all feature tables before feature consolidation

---

### Gap 5: Scripts May Not Match Schema

**Current Plan Runs:**
```bash
python scripts/features/cloud_function_pivot_calculator.py
python scripts/ingestion/ingest_features_hybrid.py
```

**Potential Issues:**
1. `cloud_function_pivot_calculator.py` may write to different table than `features.pivot_math_daily`
2. `ingest_features_hybrid.py` may expect different STRUCT schema
3. Scripts may reference old dataset names (`raw_v2`, `staging_v2`, `features_v2`)

**Impact:** 🟡 **MEDIUM** - Scripts need verification before execution

**Fix Required:**
1. Review each script for table/dataset references
2. Update to match new naming convention (`raw`, `staging`, `features`)
3. Verify STRUCT schemas match

---

## 🟡 MEDIUM GAPS

### Gap 6: Training Split Strategy

**Current Plan:**
```sql
CASE
  WHEN data_date < '2023-01-01' THEN 'train'
  WHEN data_date < '2024-01-01' THEN 'val'
  ELSE 'test'
END AS split
```

**Maximum Quality Doc Recommends:**
```python
# Strict holdout (never touched during tuning)
HOLDOUT_START = '2023-07-01'  # Last 18-24 months
TEST_START = '2024-01-01'     # Final test set

# Validation folds: 2020-01-01 to 2023-06-30
# Training: 1900-01-01 to 2019-12-31
```

**Impact:** 🟡 **MEDIUM** - Plan uses 2023-01-01 cutoff, doc uses 2020-01-01 for train end

**Fix Required:**
Align split dates with Maximum Quality strategy

---

### Gap 7: LightGBM Parameters

**Current Plan:**
```python
params = {
    'num_leaves': 127,
    'learning_rate': 0.01,
    'max_depth': 15,
    'lambda_l1': 0.1,
    'lambda_l2': 0.1,
}
```

**Maximum Quality Doc:**
```python
params = {
    'num_leaves': 127,        # 63-127 range (not 255)
    'learning_rate': 0.02,    # 0.01-0.03 range
    'max_depth': 12,          # 10-15 range
    'lambda_l1': 0.1,         # Small L1
    'lambda_l2': 0.1,         # Small L2
    'min_data_in_leaf': 30,   # 20-50 range (MISSING FROM PLAN)
    'bagging_freq': 3,        # 1-5 (plan has 5)
}
```

**Impact:** 🟡 **MEDIUM** - Parameters are close but `min_data_in_leaf` is lower in plan (20 vs 30)

**Fix Required:**
Add `min_data_in_leaf: 30` for better generalization

---

### Gap 8: Missing Quantile Models

**Current Plan:**
- Single regression model (`objective: 'regression'`)

**TFT Integration Doc Recommends:**
```python
# Train separate models (better than single multi-output)
for quantile, name in [(0.1, 'p10'), (0.5, 'p50'), (0.9, 'p90')]:
    params['alpha'] = quantile
    params['objective'] = 'quantile'
    model = lgb.train(params, train_data, ...)
```

**Impact:** 🟡 **MEDIUM** - Plan produces point estimates only, not probabilistic forecasts

**Fix Required:**
Add quantile training after initial baseline

---

### Gap 9: Missing Data Quality Assertions

**Current Plan:**
- No assertions
- No freshness checks
- No null checks

**Dataform Requires:**
```sql
-- assert_not_null_keys.sqlx
SELECT 1 WHERE EXISTS (
  SELECT 1 FROM ${ref("market_daily")}
  WHERE date IS NULL OR symbol IS NULL
)

-- assert_fred_fresh.sqlx
SELECT 1 FROM ${ref("fred_macro_clean")}
QUALIFY MAX(date) OVER() < DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
```

**Impact:** 🟡 **MEDIUM** - No automated data quality checks

**Fix Required:**
Add assertion phase after each data load

---

## ✅ ALIGNED ELEMENTS

### What's Correct in Current Plan:

1. **Regime Names** ✅
   - Uses `trump_anticipation_2024` and `trump_second_term` (matches QUAD_CHECK_PLAN)
   - Weights are correct (400 and 600)

2. **Training Table Names** ✅
   - `zl_training_prod_allhistory_1w/1m/3m/6m/12m` matches Dataform structure

3. **LightGBM for Baseline** ✅
   - TFT doc recommends LightGBM for Mac training
   - CPU-based training is correct for M4 Pro

4. **Feature Importance Analysis** ✅
   - Plan includes SHAP-style feature importance
   - Matches Maximum Quality doc recommendations

5. **Export Strategy** ✅
   - Direct BigQuery to DataFrame matches Dataform export view pattern

---

## 🔧 RECOMMENDED REVISIONS

### Priority 1: Fix Dataset Structure (Before Phase 1)

**Add Phase 0: Create Dataset Structure**

```sql
-- Create missing datasets
CREATE SCHEMA IF NOT EXISTS `cbi-v14.raw`;
CREATE SCHEMA IF NOT EXISTS `cbi-v14.staging`;
CREATE SCHEMA IF NOT EXISTS `cbi-v14.features`;
CREATE SCHEMA IF NOT EXISTS `cbi-v14.training`;
CREATE SCHEMA IF NOT EXISTS `cbi-v14.reference`;
CREATE SCHEMA IF NOT EXISTS `cbi-v14.forecasts`;
CREATE SCHEMA IF NOT EXISTS `cbi-v14.api`;
CREATE SCHEMA IF NOT EXISTS `cbi-v14.ops`;
```

### Priority 2: Fix Table Locations (Phase 1 Revision)

**Change:**
```sql
-- OLD (wrong)
INSERT INTO `cbi-v14.training.regime_calendar` ...

-- NEW (correct)
INSERT INTO `cbi-v14.reference.regime_calendar` ...
```

### Priority 3: Add Missing Feature Tables (New Phase 2.5)

**Add Phase 2.5: Create Feature Infrastructure**

```sql
-- Create STRUCT-based daily_ml_matrix
CREATE TABLE `cbi-v14.features.daily_ml_matrix` (
  date DATE NOT NULL,
  symbol STRING NOT NULL,
  market_data STRUCT<
    open FLOAT64, high FLOAT64, low FLOAT64, close FLOAT64,
    volume INT64, vwap FLOAT64, realized_vol_1h FLOAT64
  >,
  pivots STRUCT<
    P FLOAT64, R1 FLOAT64, R2 FLOAT64, S1 FLOAT64, S2 FLOAT64,
    distance_to_P FLOAT64, distance_to_nearest FLOAT64,
    weekly_P_distance FLOAT64, is_above_P BOOL
  >,
  policy STRUCT<
    trump_action_prob FLOAT64, trump_score FLOAT64,
    trump_sentiment_7d FLOAT64, trump_tariff_intensity FLOAT64,
    is_shock_regime BOOL
  >,
  golden_zone STRUCT<
    crush_margin FLOAT64, china_imports FLOAT64,
    dollar_index FLOAT64, fed_policy FLOAT64,
    vix_regime STRING
  >,
  regime STRUCT<
    name STRING, weight INT64,
    vol_percentile FLOAT64, k_vol FLOAT64
  >,
  ingestion_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY symbol, regime.name;
```

### Priority 4: Verify Scripts Before Execution

**Add Pre-Execution Checklist:**
- [ ] Verify `cloud_function_pivot_calculator.py` writes to `features.pivot_math_daily`
- [ ] Verify `ingest_features_hybrid.py` creates correct STRUCTs
- [ ] Verify no `v2` suffixes in dataset references
- [ ] Verify BigQuery credentials work: `gcloud auth application-default login`

### Priority 5: Add Quantile Training (Phase 6 Extension)

**Add to Phase 6:**
```python
# After regression baseline, train quantile models
for quantile in [0.1, 0.5, 0.9]:
    params['objective'] = 'quantile'
    params['alpha'] = quantile
    model_q = lgb.train(params, train_data, ...)
    model_q.save_model(f'models/zl_1w_baseline_lgb_q{int(quantile*100)}.txt')
```

---

## 📊 REVISED EXECUTION PLAN

### Phase 0: Dataset Infrastructure (NEW - 30 min)
- [ ] Create all 8 datasets if missing
- [ ] Verify BigQuery credentials

### Phase 1: Reference Tables (REVISED - 30 min)
- [ ] Create `reference.regime_calendar` (not `training`)
- [ ] Create `reference.regime_weights` (not `training`)
- [ ] Verify no gaps in regime coverage

### Phase 2: Pivot Calculator (UNCHANGED - 15 min)
- [ ] Verify script writes to correct table
- [ ] Run pivot calculator
- [ ] Verify output

### Phase 2.5: Feature Infrastructure (NEW - 1 hour)
- [ ] Create `features.daily_ml_matrix` with STRUCT schema
- [ ] Create `features.technical_indicators`
- [ ] Create `features.crush_margin_daily`
- [ ] Create flattened view `features.vw_daily_ml_flat`

### Phase 3: Feature Consolidation (REVISED - 30 min)
- [ ] Verify `ingest_features_hybrid.py` matches STRUCT schema
- [ ] Run test batch (100 rows)
- [ ] Verify STRUCTs populated correctly
- [ ] Run full consolidation

### Phase 4: Training Tables (UNCHANGED - 20 min)
- [ ] Populate ZL training tables (5 horizons)
- [ ] Verify row counts and splits

### Phase 5: Export Data (UNCHANGED - 10 min)
- [ ] Export to Parquet
- [ ] Verify data integrity

### Phase 6: Baseline Training (EXTENDED - 4-6 hours)
- [ ] Train regression baseline
- [ ] Train quantile models (P10, P50, P90)
- [ ] Compare results
- [ ] Save all models

### Phase 7: Data Quality (NEW - 30 min)
- [ ] Run null checks
- [ ] Run freshness checks
- [ ] Document any issues

---

## 🎯 FEASIBILITY VERDICT

### Can We Execute Current Plan?

**NO** - Current plan will fail due to:
1. Wrong dataset locations (training vs reference)
2. Missing STRUCT schema for `daily_ml_matrix`
3. Missing feature tables (only pivots, no correlations/biofuel/weather)
4. Scripts may not match expected schema

### What's Needed to Make It Feasible?

1. **Phase 0 Addition**: Create dataset structure first
2. **Phase 1 Fix**: Use `reference` dataset for regime tables
3. **Phase 2.5 Addition**: Create STRUCT-based feature tables
4. **Script Verification**: Check all scripts before running
5. **Phase 6 Extension**: Add quantile training

### Estimated Additional Time

| Addition | Time |
|----------|------|
| Phase 0 (datasets) | +30 min |
| Phase 2.5 (feature tables) | +1 hour |
| Script verification | +30 min |
| Phase 6 extension (quantiles) | +1 hour |
| **Total Additional** | **+3 hours** |

### Revised Timeline

| Day | Original | Revised |
|-----|----------|---------|
| Day 1 | 2-3 hours | **4-5 hours** |
| Day 2 | 4-6 hours | **5-7 hours** |
| Day 3 | Iterate | Iterate |

---

## ✅ RECOMMENDATION

**Update the BQ_SETUP_AND_BASELINE_TRAINING_PLAN.md with:**

1. Add Phase 0 (dataset creation)
2. Fix Phase 1 (use `reference` dataset)
3. Add Phase 2.5 (feature infrastructure)
4. Add script verification checklist
5. Extend Phase 6 (quantile models)
6. Add Phase 7 (data quality)

**Then proceed with execution.**

---

**Status:** 🟡 PLAN NEEDS REVISION BEFORE EXECUTION
**Next Step:** Update plan with fixes, then execute






