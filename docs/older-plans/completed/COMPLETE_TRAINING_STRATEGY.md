# COMPLETE TRAINING STRATEGY
**Ensuring All New Data Gets Trained**

## CURRENT STATUS SUMMARY

### Feature Count
- **Total Numeric Features**: 284 features
- **Training Rows**: 1,448 rows
- **Current Training Query**: Includes ALL numeric features automatically

### Actual Coverage (Before Forward-Fill)

| Feature Category | Rows with Data | Coverage % | Status |
|-----------------|----------------|-------------|--------|
| Social Sentiment | 87/1,448 | 6.0% | ⚠️ Sparse |
| Trump Policy | 43/1,448 | 3.0% | ⚠️ Sparse |
| USDA Export | 7/1,448 | 0.5% | ⚠️ Very Sparse |
| News Derived | 4/1,448 | 0.3% | ⚠️ Very Sparse |
| CFTC Percentiles | 299/1,448 | 20.6% | ✅ Moderate |
| USD/ARS | 1,448/1,448 | 100% | ✅ Complete |
| USD/MYR | 1,448/1,448 | 100% | ✅ Complete |

---

## THE GOOD NEWS

### ✅ BQML Automatically Includes All Features

Your current training query uses:
```sql
SELECT target_1w, * EXCEPT(target_1w, target_1m, target_3m, target_6m, date, volatility_regime)
```

**This means ALL 284 numeric features are automatically included in training!**

### ✅ BQML Handles NULLs Intelligently

BQML's `BOOSTED_TREE_REGRESSOR`:
- Automatically skips NULL values during tree splits
- Features with sparse data may still be useful if they have strong signal
- Feature importance will naturally identify which sparse features matter

### ⚠️ BUT: Sparse Features May Be Less Useful

Features with <5% coverage:
- May add noise without signal
- May get zero feature importance
- May not improve model performance

---

## SOLUTION: FORWARD-FILL SPARSE FEATURES

### Why Forward-Fill?

1. **Increases Coverage**: 0.3-6% → 10-60%
2. **Maintains Temporal Relationships**: Uses last known value
3. **More Training Data**: Better model learning
4. **Standard Practice**: Common in time series forecasting

### Expected Coverage After Forward-Fill

| Feature Category | Before | After | Improvement |
|-----------------|--------|-------|-------------|
| Social Sentiment | 6% | 60-70% | 10x |
| Trump Policy | 3% | 30-40% | 10x |
| News Derived | 0.3% | 10-20% | 30x |
| USDA Export | 0.5% | 5-10% | 10x (weekly data) |
| CFTC Percentiles | 20.6% | 20.6% | Already good |

---

## ACTION PLAN

### Step 1: Forward-Fill Sparse Features ✅ READY

**Script**: `bigquery_sql/FORWARD_FILL_SPARSE_FEATURES.sql`

**What It Does**:
- Forward-fills all sparse features (social, trump, usda, news, cftc)
- Uses `LAST_VALUE() OVER (ORDER BY date)` to propagate last known value
- Preserves existing non-NULL values
- Creates backup before changes

**Run Command**:
```bash
bq query --use_legacy_sql=false < bigquery_sql/FORWARD_FILL_SPARSE_FEATURES.sql
```

**Expected Result**:
- Social Sentiment: 6% → 60%+ coverage
- Trump Policy: 3% → 30%+ coverage
- News Derived: 0.3% → 10%+ coverage
- All features now have usable coverage for training

### Step 2: Verify Training Query ✅ ALREADY DONE

**Current Status**: Training query already includes all features

**No changes needed** - The `* EXCEPT(...)` syntax automatically includes all 284 numeric features.

### Step 3: Train Model ✅ READY

**Script**: `bigquery_sql/FINAL_BQML_TRAINING_QUERY.sql`

**What It Does**:
- Trains with ALL 284 features
- BQML handles any remaining NULLs automatically
- Feature importance will identify which features matter most

**Expected Features**:
- 284 total numeric features
- ~200+ features with good coverage (>50%)
- ~50+ features with moderate coverage (10-50%)
- ~30+ features with sparse coverage (<10%)

---

## DECISION: Include or Exclude Sparse Features?

### Option A: Include All Features (RECOMMENDED)

**Pros**:
- BQML automatically handles NULLs
- Feature importance will identify useful sparse features
- No manual feature selection needed
- Forward-fill will improve coverage anyway

**Cons**:
- Some very sparse features may add noise
- Slightly longer training time

**Recommendation**: ✅ **Include All** - Forward-fill first, then train with all features.

### Option B: Exclude Features <10% Coverage

**Pros**:
- Cleaner training set
- Focus on features with sufficient data
- Potentially faster training

**Cons**:
- Manual feature selection required
- May exclude useful features with strong signal
- Need to maintain exclusion list

**Recommendation**: ⚠️ **Not Recommended** - BQML handles sparse features well, and forward-fill will improve coverage.

---

## FINAL RECOMMENDATION

### Immediate Action (TODAY)

1. ✅ **Run Forward-Fill Script**
   ```bash
   bq query --use_legacy_sql=false < bigquery_sql/FORWARD_FILL_SPARSE_FEATURES.sql
   ```

2. ✅ **Verify Coverage Improvement**
   - Check coverage increases from 0.3-6% to 10-60%
   - Verify all features now have usable data

3. ✅ **Train Model**
   ```bash
   bq query --use_legacy_sql=false < bigquery_sql/FINAL_BQML_TRAINING_QUERY.sql
   ```

### Expected Outcome

**After Forward-Fill + Training**:
- ✅ 284 features available for training
- ✅ 200+ features with >50% coverage
- ✅ 50+ features with 10-50% coverage
- ✅ All features included in training (BQML handles NULLs)
- ✅ Feature importance will identify most useful features

### Long-Term Improvement

**Historical Data Backfill** (1-2 weeks):
- CFTC: 2020-2024 → 20.6% → 80%+ coverage
- News: 2020-2025 → 0.3% → 80%+ coverage
- USDA: Historical weekly → 0.5% → 50%+ coverage
- Social: Historical data → 6% → 60%+ coverage

---

## CONCLUSION

### To Ensure All Data Gets Trained:

1. **Forward-Fill Sparse Features** (IMMEDIATE) ✅ Script ready
   - Increases coverage 10-30x
   - Makes sparse features usable

2. **Train with All Features** (IMMEDIATE) ✅ Query ready
   - BQML automatically includes all 284 features
   - Handles NULLs intelligently

3. **Historical Data Backfill** (LONG-TERM)
   - Improves coverage naturally
   - Better long-term model performance

### Current Status: ✅ READY TO TRAIN

**All systems go!** Forward-fill the sparse features, then train. The model will automatically use all 284 features, and BQML's feature importance will identify which ones matter most.


