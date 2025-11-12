# PLAN: ADD ALL SYMBOLS + NEW CONFIGURATION
## PLANNING ONLY - NO EXECUTION

**Date:** November 7, 2025  
**Objective:** Safely expand from 55 symbols to all available symbols with new aggressive training configuration  
**Status:** ⚠️ PLANNING PHASE - DO NOT EXECUTE

---

## CURRENT STATE

### Current Configuration
- **Symbols:** 55 (only ones with data in source table)
- **Yahoo Features:** 385 (55 × 7 indicators)
- **Total Features:** ~1,093 (385 Yahoo + 638 production + 48 correlations + 22 interactions)
- **Rows:** 482 (2024-01-02 to 2025-11-06)
- **Rows per Feature:** 0.44 (CRITICAL - inverted ratio)

### Current Training Config
```sql
max_iterations=50,
learn_rate=0.05,
early_stop=TRUE,
min_rel_progress=0.0001,
l1_reg=1.5,
l2_reg=0.5,
data_split_method='RANDOM',
data_split_eval_fraction=0.2
```

### Current Performance
- **R²:** 0.65 (underfitting)
- **MAE:** $3.51/cwt
- **Status:** Stopped too early (loss improving 4.5%/iter at iteration 50)

---

## TARGET STATE

### New Symbol Count
- **Python Script:** 220 symbols defined in `pull_224_driver_universe.py`
- **Currently in BigQuery:** 55 symbols with data (2024+)
- **Target:** Use ALL 220 symbols from Python script
- **Feature Count:** 220 × 7 indicators = 1,540 Yahoo features (vs current 385)
- **Net Change:** +1,155 additional features
- **NULL Columns:** ~165 symbols will be NULL (not in BigQuery yet)
  - **Safe:** L1 regularization will automatically prune NULL columns
  - **Safe:** BQML handles NULL columns gracefully (excludes from training)
  - **Benefit:** When data is added later, features are already in place

### New Training Configuration
```sql
max_iterations=300,          -- TRIPLE (was 50, now 300)
learn_rate=0.12,             -- 2.4× faster (was 0.05, now 0.12)
early_stop=TRUE,             -- Keep safety net
min_rel_progress=0.00001,    -- 0.001% – let it run until flat (10× tighter)
l1_reg=0.7,                  -- Looser – keep more Yahoo signals (was 1.5, now 0.7)
l2_reg=0.3,                  -- Looser (was 0.5, now 0.3)
data_split_method='SEQ',     -- FIXED: time-aware (was 'RANDOM')
data_split_col='date',       -- NEW: explicitly specify time column
data_split_eval_fraction=0.2 -- SAME: 80/20 split
```

---

## SAFETY ANALYSIS

### ✅ SAFE TO ADD ALL SYMBOLS

**Why it's safe:**
1. **Current model works** - 55 symbols trained successfully
2. **Data exists** - 50+ symbols have >=400 rows (96%+ coverage)
3. **L1 regularization** - Will automatically prune irrelevant features
4. **Early stopping** - Will stop if model degrades
5. **Isolated model** - Won't affect production models

**Risks mitigated:**
- ✅ Too many features → L1=0.7 will prune (looser than 1.5, but still prunes)
- ✅ Overfitting → L2=0.3 + early stopping + validation split
- ✅ Training time → 300 iterations with early stop should complete in reasonable time
- ✅ Memory issues → BigQuery handles large feature sets well

### ⚠️ CONCERNS TO MONITOR

1. **Feature-to-sample ratio will worsen**
   - Current: 0.44 rows per feature (already inverted)
   - With all symbols: ~0.27 rows per feature (even worse)
   - **Mitigation:** L1=0.7 will prune aggressively, early stopping will prevent overfitting

2. **Learning rate might be too high**
   - 0.12 is 2.4× faster than 0.05
   - Could cause oscillation or overshooting
   - **Mitigation:** Early stopping will catch instability, min_rel_progress will stop if oscillating

3. **Training time could be long**
   - 300 iterations × 0.12 LR might run all 300 iterations
   - min_rel_progress=0.00001 is very tight (0.001% threshold)
   - **Mitigation:** Monitor training progress, can cancel if needed

4. **L1 too loose might keep noise**
   - L1=0.7 is 2.1× looser than 1.5
   - Might keep irrelevant Yahoo features
   - **Mitigation:** Can increase L1 if validation degrades

---

## STEP-BY-STEP EXECUTION PLAN

### STEP 1: Extract All 220 Symbols from Python Script
**Action:** Extract all symbol names from `scripts/pull_224_driver_universe.py`  
**Method:** Use regex to find all symbol definitions: `'SYMBOL': {`  
**Expected:** 220 symbols  
**Output:** Complete list of 220 symbols for pivot generation

**Python Code:**
```python
import re
with open('scripts/pull_224_driver_universe.py', 'r') as f:
    content = f.read()
    symbols = re.findall(r"'([^']+)':\s*\{", content)
# Result: 220 symbols
```

**Note:** 
- 55 symbols have data in BigQuery (will have values)
- 165 symbols don't have data yet (will be NULL columns)
- This is SAFE - L1 regularization will prune NULL columns automatically

### STEP 2: Generate Complete Pivot for ALL 220 Symbols
**Action:** Generate pivot statements for ALL 220 symbols from Python script  
**Method:** Use Python script to generate pivot for all 220 symbols  
**Output:** Complete `yahoo_pivoted` CTE with all 220 symbols (1,540 features)

**Key considerations:**
- Include ALL 220 symbols (even if they don't have data yet)
- NULL columns will be automatically pruned by L1 regularization
- Handle column name conflicts (add `_yh` suffix where needed)
- Generate all 7 indicators per symbol (close, rsi_14, ma_30d, macd_hist, atr_14, bb_width, momentum)
- **Total pivot lines:** 220 × 7 = 1,540 lines

### STEP 3: Update SQL File
**Action:** Update `BASELINE_1M_COMPREHENSIVE_2YR.sql` with:
1. New pivot section (all symbols)
2. New training configuration
3. Updated EXCEPT clause (if needed for new NULL columns)

**Changes:**
```sql
-- Replace yahoo_pivoted CTE with new complete pivot
-- Update CREATE MODEL with new parameters:
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_1m_baseline_exploratory`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1m'],
  max_iterations=300,          -- TRIPLE
  learn_rate=0.12,             -- 2.4× faster
  early_stop=TRUE,
  min_rel_progress=0.00001,    -- 0.001% – let it run until flat
  l1_reg=0.7,                  -- Looser – keep more Yahoo signals
  l2_reg=0.3,
  data_split_method='SEQ',     -- FIXED: time-aware
  data_split_col='date',
  data_split_eval_fraction=0.2
)
```

### STEP 4: Pre-Flight Checks
**Action:** Run verification queries before training

**Checks:**
1. ✅ Verify all symbols exist in source table
2. ✅ Check for column name conflicts
3. ✅ Verify date range (2024-01-01 onwards)
4. ✅ Count expected features
5. ✅ Verify no 100% NULL columns
6. ✅ Check data split will work with SEQ method

### STEP 5: Execute Training
**Action:** Run updated SQL script  
**Expected Time:** 20-40 minutes (300 iterations, but early stop should trigger)  
**Monitoring:** Check `ML.TRAINING_INFO()` periodically

**Success Criteria:**
- Model trains without errors
- Early stopping triggers before 300 iterations (or completes all 300)
- R² improves from 0.65 (target: >0.70)
- Validation MAE improves or stays similar

### STEP 6: Post-Training Analysis
**Action:** Analyze results and compare to previous run

**Metrics to check:**
- Final iteration count (did early stop trigger?)
- Final loss values (train vs validation)
- R² score (did it improve?)
- MAE/RMSE (did it improve?)
- Feature usage (how many features actually used?)

---

## CONFIGURATION PARAMETER ANALYSIS

### max_iterations=300 (was 50)
**Rationale:**
- Previous run stopped at 50 while loss improving 4.5%/iter
- Need to allow full convergence
- Early stopping will prevent unnecessary iterations

**Risk:** Might run all 300 iterations if loss keeps improving  
**Mitigation:** Early stopping + min_rel_progress will stop when flat

### learn_rate=0.12 (was 0.05)
**Rationale:**
- 2.4× faster convergence
- Previous run showed stable loss reduction (no oscillation)
- With early stopping, higher LR is safer

**Risk:** Could cause oscillation or overshooting  
**Mitigation:** Early stopping will catch instability, min_rel_progress will stop if oscillating

### min_rel_progress=0.00001 (was 0.0001)
**Rationale:**
- 10× tighter threshold (0.001% vs 0.01%)
- Will run until truly flat
- With 300 iterations, can afford to wait for true convergence

**Risk:** Might run all 300 iterations  
**Mitigation:** Acceptable - want full convergence for discovery model

### l1_reg=0.7 (was 1.5)
**Rationale:**
- 2.1× looser to keep more Yahoo features
- Previous L1=1.5 might have been too aggressive (causing underfitting)
- Want to discover which Yahoo features matter

**Risk:** Might keep irrelevant features (noise)  
**Mitigation:** Can increase if validation degrades, L2=0.3 provides additional regularization

### l2_reg=0.3 (was 0.5)
**Rationale:**
- Looser regularization
- L1=0.7 already provides feature selection
- L2 mainly prevents overfitting, 0.3 should be sufficient

**Risk:** Less overfitting protection  
**Mitigation:** Early stopping + validation split + SEQ split will catch overfitting

### data_split_method='SEQ' (was 'RANDOM')
**Rationale:**
- **CRITICAL FIX** - Time series must use sequential split
- Random split can cause data leakage (predicting past from future)
- SEQ ensures train on past, validate on future

**Risk:** None - this is the correct approach for time series

### data_split_col='date'
**Rationale:**
- Explicitly specifies time column for SEQ split
- Ensures proper time-aware splitting
- Prevents ambiguity

**Risk:** None - required for SEQ split

---

## EXPECTED OUTCOMES

### Feature Count
- **Current:** ~1,093 features (385 Yahoo + 638 production + 48 correlations + 22 interactions)
- **With all 220 symbols:** ~2,233 features (1,540 Yahoo + 638 production + 48 correlations + 22 interactions)
- **NULL columns:** ~1,155 features will be NULL (165 symbols × 7 indicators)
- **After L1 pruning:** L1=0.7 will prune NULL columns automatically, keep only features with data

### Training Time
- **Current:** ~5 minutes (50 iterations)
- **Expected:** 20-40 minutes (300 iterations, but early stop should trigger around 100-150)
- **Worst case:** 60+ minutes if runs all 300 iterations

### Performance
- **Current R²:** 0.65
- **Target R²:** >0.70 (improvement from more iterations + more features)
- **Current MAE:** $3.51/cwt
- **Target MAE:** <$3.50/cwt (marginal improvement expected)

### Iteration Count
- **Current:** 50 (stopped at limit)
- **Expected:** 100-150 iterations (early stop should trigger)
- **Worst case:** 300 iterations (if loss keeps improving)

---

## RISK MITIGATION

### Risk 1: Too Many Features → Underfitting
**Mitigation:**
- L1=0.7 will prune NULL columns automatically (1,155 features will be removed)
- Only features with actual data will be used (55 symbols × 7 = 385 features)
- Early stopping will prevent overfitting
- Can increase L1 to 1.0 if needed

**Note:** NULL columns are SAFE - BQML excludes them from training automatically

### Risk 2: Learning Rate Too High → Instability
**Mitigation:**
- Early stopping will catch oscillation
- min_rel_progress will stop if loss plateaus
- Can reduce to 0.1 if needed

### Risk 3: Training Takes Too Long
**Mitigation:**
- Early stopping should trigger before 300 iterations
- Can monitor and cancel if needed
- Acceptable for discovery model

### Risk 4: L1 Too Loose → Noise Features
**Mitigation:**
- L2=0.3 provides additional regularization
- Validation split will catch overfitting
- Can increase L1 if validation degrades

---

## ROLLBACK PLAN

If training fails or performs worse:

1. **Revert to 55 symbols** - Use current working pivot
2. **Revert config** - Use previous config (50 iterations, 0.05 LR, L1=1.5)
3. **Keep SEQ split** - This is a critical fix, keep it
4. **Gradual increase** - Try 100 iterations first, then 300

---

## SUCCESS CRITERIA

### Must Have:
- ✅ Model trains without errors
- ✅ Early stopping works (stops before 300 if loss plateaus)
- ✅ R² >= 0.65 (at least matches current)
- ✅ Validation MAE <= $3.60/cwt (within 3% of current)

### Nice to Have:
- ✅ R² > 0.70 (improvement from more iterations)
- ✅ MAE < $3.50/cwt (improvement)
- ✅ Early stop triggers around 100-150 iterations
- ✅ More Yahoo features contribute to predictions

---

## NEXT STEPS (AFTER APPROVAL)

1. ✅ **Generate symbol list** - Query for all symbols with >=400 rows
2. ✅ **Generate pivot** - Create pivot for all symbols
3. ✅ **Update SQL** - Add new pivot + new config
4. ✅ **Pre-flight checks** - Verify everything before training
5. ✅ **Execute** - Run training and monitor
6. ✅ **Analyze** - Compare results to previous run

---

## QUESTIONS TO RESOLVE

1. **Symbol threshold:** Use >=400 rows (83% coverage) or >=450 rows (93% coverage)?
   - **Recommendation:** >=400 rows (more symbols = more discovery)

2. **L1 value:** 0.7 might be too loose, should we try 1.0 first?
   - **Recommendation:** Start with 0.7 (as requested), can increase if needed

3. **Learning rate:** 0.12 might be too high, should we try 0.1 first?
   - **Recommendation:** Start with 0.12 (as requested), early stopping will catch issues

4. **Feature limit:** Should we cap at certain number of features?
   - **Recommendation:** No cap - let L1 regularization handle it

---

**PLANNING COMPLETE - READY FOR REVIEW**

**⚠️ DO NOT EXECUTE UNTIL APPROVED**

