# MASTER WORK LIST - DO NOT DEVIATE

**Created:** October 24, 2025  
**Status:** IN PROGRESS  
**Critical:** Stay on track - complete in order

---

## PRIORITY TASKS (EXECUTE IN ORDER)

### ✅ TASK 1: Remove Bad Features (30 min)
**Status:** 🔄 IN PROGRESS  
**Goal:** Clean dataset by removing problematic features

**Sub-tasks:**
- [ ] 1.1: Remove features with <10% coverage (11 features)
  - `news_total_count_enhanced` (0.6%)
  - `brazil_article_count` (0.4%)
  - `weather_article_count` (0.4%)
  - `cftc_commercial_long` (5.7%)
  - `cftc_commercial_short` (5.7%)
  - `cftc_commercial_net` (5.7%)
  - `cftc_open_interest` (5.7%)
  - Any others with <10% coverage

- [ ] 1.2: Remove constant features (1 unique value)
  - `ice_mentions` (1 unique)
  - `ice_enforcement_count` (1 unique)
  - `reddit_sentiment` (1 unique)
  - Any others with 1 unique value

- [ ] 1.3: Remove features with >95% NaN
  - `sentiment_std` (99.8% NaN)
  - `tariff_sentiment` (99.6% NaN)
  - `trump_sentiment` (99.5% NaN)
  - `china_sentiment_policy` (98.8% NaN)
  - `tariff_mentions_lag7` (96.4% NaN)
  - `tariff_mentions_lag1` (96.0% NaN)
  - `china_mentions_lag1` (96.0% NaN)
  - `avg_ag_impact` (96.0% NaN)
  - Any others with >95% NaN

- [ ] 1.4: Save cleaned dataset as `CLEANED_TRAINING_DATA.csv`
- [ ] 1.5: Generate removal report showing what was removed and why
- [ ] 1.6: Verify final feature count and coverage stats

**Expected outcome:**
- Reduced from 190 features to ~150-160 features
- All remaining features have >10% coverage
- No constant features
- No features with >95% NaN

---

### ⏳ TASK 2: Feature Selection (20 min)
**Status:** ⏳ PENDING  
**Goal:** Reduce to optimal 100-120 features

**Sub-tasks:**
- [ ] 2.1: Calculate correlation matrix for all remaining features
- [ ] 2.2: Remove highly correlated pairs (correlation >0.95)
  - Keep the feature with higher target correlation
  - Document which pairs were removed
  
- [ ] 2.3: Calculate feature importance metrics:
  - Variance (remove near-zero variance)
  - Correlation with target
  - Mutual information with target
  
- [ ] 2.4: Rank features by combined importance score
- [ ] 2.5: Select top 100-120 features
- [ ] 2.6: Verify selected features include:
  - All price features
  - Key currency features
  - Important correlations
  - Weather data
  - Seasonal features
  - Top sentiment/intelligence features
  
- [ ] 2.7: Save feature selection report
- [ ] 2.8: Save final feature list to `SELECTED_FEATURES.txt`
- [ ] 2.9: Create dataset with selected features: `FINAL_FEATURES_DATASET.csv`

**Expected outcome:**
- 100-120 high-quality features
- Feature/sample ratio ~0.08-0.095 (good for ML)
- Documented selection rationale

---

### ⏳ TASK 3: Handle Duplicates (10 min)
**Status:** ⏳ PENDING  
**Goal:** Resolve 12 duplicate dates

**Sub-tasks:**
- [ ] 3.1: Identify which dates are duplicated
- [ ] 3.2: Investigate why duplicates exist (multiple joins?)
- [ ] 3.3: Check if duplicate rows have:
  - Same values (true duplicate - drop one)
  - Different values (conflicting data - investigate)
  - Complementary data (merge rows)
  
- [ ] 3.4: Decide resolution strategy per case
- [ ] 3.5: Apply resolution (drop, merge, or keep first)
- [ ] 3.6: Verify no duplicates remain
- [ ] 3.7: Document resolution decisions

**Expected outcome:**
- Zero duplicate dates
- 1,251-1,263 rows (depending on resolution)
- Clear documentation of what was done

---

### ⏳ TASK 4: Verify No Leakage (15 min)
**Status:** ⏳ PENDING  
**Goal:** Ensure no future data in features

**Sub-tasks:**
- [ ] 4.1: Audit all "lead" features:
  - `dxy_lead1_correlation` - CHECK THIS
  - Any other features with "lead" in name
  - Decision: Remove or verify calculation
  
- [ ] 4.2: Verify all lag features:
  - Confirm they use only past data
  - Check lag calculation logic
  - Ensure proper temporal ordering
  
- [ ] 4.3: Check derived features:
  - Moving averages: use only past data?
  - Returns: calculated from past prices?
  - Correlations: rolling windows look back only?
  
- [ ] 4.4: Verify target variable calculation:
  - `target_1w` = price[t+5] / price[t] - 1
  - Confirm no targets in feature set
  - Ensure future prices not leaked
  
- [ ] 4.5: Document all verified features
- [ ] 4.6: Create "NO LEAKAGE VERIFIED" stamp for dataset

**Expected outcome:**
- All features use only past data
- No look-ahead bias
- Documented verification

---

## TASKS TO DO AFTER 1-4 (DO NOT START YET)

### ⏸️ TASK 5: Set Up Scaling (5 min)
**Status:** ⏸️ NOT STARTED  
- Implement StandardScaler or RobustScaler
- Fit on training data only
- Transform train and test separately

### ⏸️ TASK 6: Create Proper Split (5 min)
**Status:** ⏸️ NOT STARTED  
- 80/20 chronological split
- 5-day purge gap
- Save train/test indices

### ⏸️ TASK 7: Train Baseline Model (30-60 min)
**Status:** ⏸️ NOT STARTED  
- PyTorch feed-forward network
- 100 epochs with early stopping
- Track all metrics

### ⏸️ TASK 8: Walk-Forward Validation (60-90 min)
**Status:** ⏸️ NOT STARTED  
- 10 windows minimum
- Track performance across time
- Save all predictions

### ⏸️ TASK 9: Analysis & Iteration (30-60 min)
**Status:** ⏸️ NOT STARTED  
- Review results
- Identify issues
- Adjust and retrain if needed

---

## RULES

### ✅ DO:
1. ✅ Complete tasks 1-4 in exact order
2. ✅ Save output at each step
3. ✅ Document all decisions
4. ✅ Verify results before moving on
5. ✅ Update this list as you progress

### ❌ DON'T:
1. ❌ Skip ahead to training
2. ❌ Start a task before previous is done
3. ❌ Deviate from the plan
4. ❌ Make undocumented changes
5. ❌ Zero-fill or fake any data

---

## PROGRESS TRACKER

**Started:** [TIMESTAMP]  
**Current Task:** TASK 1 - Remove Bad Features  
**Completed Tasks:** 0/4  
**Estimated Time Remaining:** 75 minutes  

---

## CHECKPOINT LOG

### Checkpoint 1: After Task 1
- [ ] Dataset cleaned
- [ ] Bad features removed
- [ ] Report generated
- [ ] File saved: `CLEANED_TRAINING_DATA.csv`

### Checkpoint 2: After Task 2
- [ ] Features selected
- [ ] ~100-120 features remaining
- [ ] Selection report generated
- [ ] File saved: `FINAL_FEATURES_DATASET.csv`

### Checkpoint 3: After Task 3
- [ ] Duplicates resolved
- [ ] Zero duplicate dates confirmed
- [ ] Resolution documented
- [ ] File updated

### Checkpoint 4: After Task 4
- [ ] Leakage audit complete
- [ ] All features verified
- [ ] "NO LEAKAGE" certification created
- [ ] Ready for training setup

---

## SUCCESS CRITERIA

**Tasks 1-4 Complete When:**
- ✅ Dataset has 100-120 high-quality features
- ✅ All features have >10% coverage
- ✅ No constant or near-constant features
- ✅ No duplicate dates
- ✅ No data leakage verified
- ✅ All steps documented
- ✅ Ready for scaling and training

**DO NOT PROCEED TO TASK 5+ UNTIL ALL CHECKPOINTS PASSED**

---

**THIS IS THE MASTER LIST - ALL WORK MUST FOLLOW THIS PLAN**

