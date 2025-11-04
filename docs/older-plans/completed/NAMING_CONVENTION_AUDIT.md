# Naming Convention Audit - Complete Execution Plan
**Date:** 2025-11-01  
**Purpose:** Surgical identification of ALL naming inconsistencies before plan finalization

## Audit Methodology

**STEP 1:** Examine current plan for naming patterns  
**STEP 2:** Compare against actual codebase conventions  
**STEP 3:** Compare against FINAL HYBRID PLAN standards  
**STEP 4:** Generate comprehensive change proposal  
**STEP 5:** Report all findings

---

## SECTION 1: MODEL NAMING CONVENTIONS

### Current Plan Usage:
- ❌ `bqml_soy_1w_mean` (found in corrections doc)
- ❌ Generic references like "bqml model" without specific names

### Actual Codebase Standard (MASTER_TRAINING_PLAN.md):
- ✅ `bqml_1w_mean`
- ✅ `bqml_1m_mean`
- ✅ `bqml_3m_mean`
- ✅ `bqml_6m_mean`

### FINAL HYBRID PLAN Standard:
- ✅ `cbi-v14.models_v4.bqml_1w_mean`
- ✅ `cbi-v14.models_v4.bqml_1m_mean`
- ✅ `cbi-v14.models_v4.bqml_3m_mean`
- ✅ `cbi-v14.models_v4.bqml_6m_mean`

### Changes Required:
1. **Remove "soy" prefix from ALL model references**
2. **Use full path format:** `cbi-v14.models_v4.bqml_{horizon}_mean`
3. **Horizon format:** `1w`, `1m`, `3m`, `6m` (lowercase, no space)

---

## SECTION 2: TABLE/VIEW NAMING CONVENTIONS

### Predictions Tables:

#### Current Plan References:
- ❓ `production_forecasts` (location unclear)
- ❓ `predictions_1m` (location unclear)

#### FINAL HYBRID PLAN Standard:
- ✅ `cbi-v14.predictions_uc1.production_forecasts` (primary predictions table)
- ✅ `cbi-v14.forecasting_data_warehouse.agg_1m_latest` (aggregation view)

#### Actual Codebase (EXECUTION_SUMMARY.md):
- ✅ `predictions_1m` (exists in SQL)
- ✅ `agg_1m_latest` (confirmed exists)

#### Decision Needed:
- **Option A:** Use `cbi-v14.predictions_uc1.production_forecasts` (from hybrid plan)
- **Option B:** Use `cbi-v14.forecasting_data_warehouse.predictions_1m` (existing)
- **RECOMMENDATION:** Follow hybrid plan → `production_forecasts` in `predictions_uc1`

### Residual/Quantile Tables:

#### Current Plan References:
- ❓ `residual_quantiles` (location unclear)
- ❓ `residual_distributions` (alternate name)

#### FINAL HYBRID PLAN Standard:
- ✅ `cbi-v14.models_v4.residual_quantiles`

#### Actual Codebase (MASTER_TRAINING_PLAN.md):
- ✅ `cbi-v14.models_v4.residual_distributions` (from training plan)

#### Decision Needed:
- **Option A:** `residual_quantiles` (hybrid plan)
- **Option B:** `residual_distributions` (training plan)
- **RECOMMENDATION:** Use `residual_quantiles` (matches hybrid plan, more concise)

### Training Tables:

#### Current Plan References:
- ✅ `cbi-v14.models_v4.training_dataset_super_enriched` (CORRECT)
- ❌ `training_features_master` (WRONG - not used)
- ❌ `training_features_1w`, `training_features_1m`, etc. (WRONG - these don't exist)

#### Actual Codebase:
- ✅ `cbi-v14.models_v4.training_dataset_super_enriched` (confirmed exists)

### Signal Tables:

#### Current Plan References:
- ❓ `signals_1w` (location unclear)

#### Actual Codebase (EXECUTION_SUMMARY.md):
- ✅ `signals_1w` table SQL exists

#### FINAL HYBRID PLAN Standard:
- ✅ `cbi-v14.forecasting_data_warehouse.signals_1w`

### Changes Required:
1. **Standardize predictions table:** `cbi-v14.predictions_uc1.production_forecasts`
2. **Standardize residual table:** `cbi-v14.models_v4.residual_quantiles`
3. **Remove references to non-existent tables:** `training_features_master`, etc.
4. **Use full paths for ALL table references**

---

## SECTION 3: FILE PATH CONVENTIONS

### Current Plan References:
- ✅ `cbi-v14-ingestion/web_scraper.py` (CORRECT)
- ✅ `bigquery_sql/create_*.sql` (CORRECT)
- ❓ `scripts/phase_0_data_refresh.py` (check if exists)
- ❓ Generic Python file references

### FINAL HYBRID PLAN Standard:
- ✅ `scripts/phase_0_data_refresh.py`
- ✅ `bigquery_sql/train_bqml_models.sql`
- ✅ `bigquery_sql/compute_residuals.sql`
- ✅ `dashboard-nextjs/src/app/api/forecast/route.ts`

### Actual Codebase Structure:
- ✅ `scripts/` directory exists
- ✅ `bigquery_sql/` directory exists
- ✅ `dashboard-nextjs/src/app/api/` structure exists
- ✅ `cbi-v14-ingestion/` directory exists

### Changes Required:
1. **Verify all file paths match actual directory structure**
2. **Use relative paths from repo root**
3. **Ensure all paths are consistent with existing structure**

---

## SECTION 4: PROJECT/DATASET CONVENTIONS

### Current Plan Usage:
- ✅ `cbi-v14` (CORRECT - used consistently)
- ✅ `forecasting_data_warehouse` (CORRECT)
- ✅ `models_v4` (CORRECT)
- ✅ `predictions_uc1` (CORRECT)

### Actual Codebase:
- ✅ `cbi-v14` confirmed
- ✅ All datasets confirmed

### Changes Required:
- ✅ **NO CHANGES** - Already correct

---

## SECTION 5: API ROUTE CONVENTIONS

### Current Plan References:
- ❓ Generic API route examples (may not match actual)

### FINAL HYBRID PLAN Standard:
- ✅ `dashboard-nextjs/src/app/api/forecast/route.ts`

### Actual Codebase (dashboard-nextjs):
- ✅ `src/app/api/forecast/route.ts` (exists)
- ✅ `src/app/api/v4/forward-curve/route.ts` (exists)
- ✅ `src/app/api/v4/feature-importance/[horizon]/route.ts` (exists)
- ✅ Multiple other v4 routes exist

### Changes Required:
1. **Verify all API route paths match actual Next.js structure**
2. **Include all existing routes in Phase 13**

---

## SECTION 6: COLUMN/SCHEMA NAMING

### Current Plan References:
- ✅ `target_1w`, `target_1m`, `target_3m`, `target_6m` (CORRECT)
- ❓ Generic feature names (need verification)

### Actual Codebase (MASTER_TRAINING_PLAN.md):
- ✅ `target_1w`, `target_1m`, `target_3m`, `target_6m` (confirmed)
- ✅ 205 features total (confirmed)

### FINAL HYBRID PLAN Standard:
- ✅ `target_1w`, `target_1m`, etc. (matches)

### Changes Required:
- ✅ **NO CHANGES** - Already correct

---

## SECTION 7: VERTEX AI REFERENCE DATA

### Current Plan References:
- ❌ **MISSING:** Vertex AI model IDs and performance metrics
- ❌ **MISSING:** Reference to residual quantiles from Vertex

### Required Addition:
- ✅ Add section: "Vertex AI Baseline Reference (for Validation)"
- ✅ Include model IDs:
  - Model 575258986094264320 (1W): MAE 1.008, MAPE 2.02%, R² 0.9836
  - Model 274643710967283712 (1M): Performance TBD
  - Model 3157158578716934144 (3M): MAE 1.340, MAPE 2.68%, R² 0.9727
  - Model 3788577320223113216 (6M): MAE 1.254, MAPE 2.51%, R² 0.9792
- ✅ Clarify: Residuals stored in Vertex AI Experiments (ephemeral, NOT in BigQuery)
- ✅ Clarify: Only predictions saved to `predictions.daily_forecasts` (or `predictions_uc1.daily_forecasts`?)
- ✅ Purpose: Use as reference/validation to inform BQML residual quantile calculations

---

## SECTION 8: TENSORFLOW REFERENCES

### Current Plan References:
- ❌ **NONE** (no TensorFlow mentioned)

### User Instruction:
- ✅ **HOLD OFF** on TensorFlow Remote Models (no complexity)
- ✅ **NO CHANGES NEEDED** - Not included

---

## COMPREHENSIVE CHANGE LIST

### Priority 1 (Critical - Model Names):

| Current (Wrong) | Correct | Location |
|----------------|---------|----------|
| `bqml_soy_1w_mean` | `bqml_1w_mean` | All SQL/model references |
| `bqml_soy_1m_mean` | `bqml_1m_mean` | All SQL/model references |
| `bqml_soy_3m_mean` | `bqml_3m_mean` | All SQL/model references |
| `bqml_soy_6m_mean` | `bqml_6m_mean` | All SQL/model references |
| Generic "BQML model" | Full path: `cbi-v14.models_v4.bqml_{horizon}_mean` | All references |

### Priority 2 (Critical - Table Names):

| Current (Wrong/Unclear) | Correct | Location |
|------------------------|---------|----------|
| `production_forecasts` (no path) | `cbi-v14.predictions_uc1.production_forecasts` | Phase 3, 8, 13 |
| `predictions_1m` (no path) | `cbi-v14.predictions_uc1.production_forecasts` OR confirm actual table name | Phase 3, 8 |
| `residual_quantiles` (no path) | `cbi-v14.models_v4.residual_quantiles` | Phase 2 |
| `residual_distributions` | `cbi-v14.models_v4.residual_quantiles` (standardize name) | Phase 2 |
| `training_features_master` | `cbi-v14.models_v4.training_dataset_super_enriched` | Phase 0, 1 |
| `training_features_1w` | Remove (doesn't exist) | Phase 0 |
| `training_features_1m` | Remove (doesn't exist) | Phase 0 |
| `signals_1w` (no path) | `cbi-v14.forecasting_data_warehouse.signals_1w` | Phase 3, 8 |
| `agg_1m_latest` (no path) | `cbi-v14.forecasting_data_warehouse.agg_1m_latest` | Phase 3, 8, 13 |

### Priority 3 (Important - Add Missing Sections):

| Missing Section | Location | Content |
|----------------|----------|---------|
| Vertex AI Baseline Reference | Phase 1 or Appendix A | Model IDs, performance metrics, residual quantile reference |
| TensorFlow Clarification | Appendix A | Note: Holding off, no complexity |

### Priority 4 (Important - File Paths):

| Current | Correct | Verification Needed |
|---------|---------|---------------------|
| `scripts/phase_0_data_refresh.py` | Verify exists | Check actual file |
| `bigquery_sql/train_bqml_models.sql` | Verify naming convention | Check if exists or create |
| `bigquery_sql/compute_residuals.sql` | Verify naming convention | Check if exists or create |

---

## VERIFICATION CHECKLIST

Before finalizing plan, verify:

- [ ] All model names use `bqml_{horizon}_mean` format (no "soy")
- [ ] All table references include full path: `cbi-v14.dataset.table`
- [ ] Predictions table confirmed: `cbi-v14.predictions_uc1.production_forecasts`
- [ ] Residual table confirmed: `cbi-v14.models_v4.residual_quantiles`
- [ ] No references to non-existent tables (`training_features_master`, etc.)
- [ ] Vertex AI reference section added with model IDs and metrics
- [ ] All file paths verified against actual directory structure
- [ ] API routes match actual Next.js structure
- [ ] All datasets/projects use `cbi-v14` consistently

---

## QUESTIONS FOR CLARIFICATION

1. **Predictions Table Name:**
   - Hybrid plan uses: `cbi-v14.predictions_uc1.production_forecasts`
   - Existing code uses: `predictions_1m` (location unclear)
   - **Question:** Which is correct? Should we migrate to `production_forecasts`?

2. **Residual Table Name:**
   - Hybrid plan uses: `residual_quantiles`
   - Training plan uses: `residual_distributions`
   - **Question:** Standardize to `residual_quantiles`?

3. **Vertex Predictions Location:**
   - User says: "Only predictions saved to `predictions.daily_forecasts`"
   - **Question:** Is this `cbi-v14.predictions_uc1.daily_forecasts` or `cbi-v14.predictions.daily_forecasts`?

---

## READY FOR SURGICAL UPDATES

Once clarifications provided:
1. Apply all Priority 1-2 changes (model/table names)
2. Add Priority 3 sections (Vertex AI reference)
3. Verify Priority 4 file paths
4. Complete full plan with all phases
5. Report completion

**STATUS:** Audit complete. Awaiting clarifications before surgical updates.



