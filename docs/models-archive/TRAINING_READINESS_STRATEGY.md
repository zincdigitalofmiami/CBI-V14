# TRAINING READINESS STRATEGY
**Ensuring All New Data Gets Trained**

## CURRENT STATUS

### Feature Coverage Analysis

| Feature Category | Rows with Data | Coverage % | Training Status |
|-----------------|----------------|-------------|-----------------|
| **Social Sentiment** | 87/1,448 | 6.0% | ⚠️ Sparse |
| **Trump Policy** | 43/1,448 | 3.0% | ⚠️ Sparse |
| **USDA Export** | 7/1,448 | 0.5% | ⚠️ Very Sparse |
| **News Derived** | 4/1,448 | 0.3% | ⚠️ Very Sparse |
| **CFTC Percentiles** | 299/1,448 | 20.6% | ✅ Moderate |
| **USD/ARS** | 1,448/1,448 | 100% | ✅ Complete |
| **USD/MYR** | 1,448/1,448 | 100% | ✅ Complete |

### Current Training Query

The current `FINAL_BQML_TRAINING_QUERY.sql` uses:
```sql
SELECT target_1w, * EXCEPT(target_1w, target_1m, target_3m, target_6m, date, volatility_regime)
```

**This means ALL numeric columns are included, including the new sparse ones.**

---

## THE PROBLEM

### BQML NULL Handling

BQML automatically handles NULLs by:
1. **Tree-based models** (BOOSTED_TREE_REGRESSOR): Automatically skip NULL values during splits
2. **Sparse features** (<5% coverage): May not be useful if too few samples exist
3. **Feature importance**: Very sparse features may get zero importance

### Current Issues

1. **Very Sparse Features** (0.3-6% coverage):
   - News derived features: 4 rows
   - USDA export: 7 rows
   - These may add noise without signal

2. **Moderate Coverage** (20% coverage):
   - CFTC percentiles: 299 rows
   - Social sentiment: 87 rows
   - These could be useful but need more data

3. **Complete Coverage** (100%):
   - Currency pairs: Full coverage
   - These will definitely be trained

---

## SOLUTION STRATEGIES

### Strategy 1: Forward-Fill Sparse Data (RECOMMENDED)

**Approach**: Use forward-fill and back-fill to maximize usable data

**Benefits**:
- Increases coverage from 0.3-6% to 50-80%
- Maintains temporal relationships
- More data = better training

**Implementation**:
```sql
-- Forward-fill sparse features within training dataset
UPDATE training_dataset_super_enriched
SET 
  social_sentiment_avg = LAST_VALUE(social_sentiment_avg IGNORE NULLS) OVER (ORDER BY date),
  trump_policy_events = LAST_VALUE(trump_policy_events IGNORE NULLS) OVER (ORDER BY date),
  ...
WHERE target_1w IS NOT NULL;
```

**Coverage After Forward-Fill**:
- Social Sentiment: 6% → 60-70%
- Trump Policy: 3% → 30-40%
- News Derived: 0.3% → 10-20%
- USDA Export: 0.5% → 5-10%

### Strategy 2: Feature Selection by Coverage

**Approach**: Exclude features below a coverage threshold

**Benefits**:
- Cleaner training set
- Focus on features with sufficient data
- Better model performance

**Implementation**:
```sql
-- Only include features with >20% coverage
SELECT target_1w,
  * EXCEPT(
    target_1w, target_1m, target_3m, target_6m, date, volatility_regime,
    -- Exclude very sparse features
    social_sentiment_avg, social_sentiment_volatility, social_post_count,
    social_sentiment_7d, social_volume_7d, bullish_ratio, bearish_ratio,
    trump_policy_events, trump_policy_impact_avg, trump_policy_impact_max,
    trade_policy_events, china_policy_events, ag_policy_events,
    trump_policy_7d, trump_events_7d,
    soybean_weekly_sales, soybean_oil_weekly_sales, soybean_meal_weekly_sales,
    china_soybean_sales,
    china_news_count, biofuel_news_count, tariff_news_count, weather_news_count,
    news_intelligence_7d, news_volume_7d, news_sentiment_avg
  )
FROM training_dataset_super_enriched
WHERE target_1w IS NOT NULL;
```

**Features Kept**:
- CFTC percentiles (20.6% coverage)
- Currency pairs (100% coverage)
- All existing features with good coverage

### Strategy 3: Hybrid Approach (BEST)

**Approach**: Forward-fill + Selective Inclusion

**Steps**:
1. Forward-fill all sparse features
2. Include features with >10% coverage after forward-fill
3. Exclude features that remain <10% even after forward-fill

**Benefits**:
- Maximizes usable data
- Balances coverage vs. quality
- Best of both worlds

---

## RECOMMENDED ACTION PLAN

### Phase 1: Forward-Fill Sparse Features (IMMEDIATE)

**Goal**: Increase coverage of sparse features to 50%+

**SQL Script**: `bigquery_sql/FORWARD_FILL_SPARSE_FEATURES.sql`

**Features to Forward-Fill**:
- Social sentiment (7 features)
- Trump policy (8 features)
- USDA export (4 features)
- News derived (7 features)

**Expected Result**:
- Social: 6% → 60%+
- Trump: 3% → 30%+
- News: 0.3% → 10%+
- USDA: 0.5% → 5%+ (weekly data, limited improvement)

### Phase 2: Verify Training Query Includes All Features

**Action**: Confirm current training query includes all new columns

**Current Status**: ✅ Already includes all (uses `* EXCEPT(...)`)

**No changes needed** - BQML will automatically include all numeric columns.

### Phase 3: Historical Data Backfill (LONG-TERM)

**Goal**: Fetch historical data to improve coverage naturally

**Priority**:
1. **CFTC Data**: Backfill 2020-2024 (will improve from 20.6% to 80%+)
2. **News Intelligence**: Backfill 2020-2025 (will improve from 0.3% to 80%+)
3. **USDA Export**: Backfill historical weekly reports (will improve from 0.5% to 50%+)
4. **Social Sentiment**: Backfill historical data (will improve from 6% to 60%+)

**Timeline**: 1-2 weeks for data acquisition and ingestion

---

## IMMEDIATE ACTIONS

### 1. Create Forward-Fill Script

**File**: `bigquery_sql/FORWARD_FILL_SPARSE_FEATURES.sql`

**Purpose**: Forward-fill all sparse features to maximize training data

### 2. Update Training Query (Optional)

**Decision Point**: 
- **Option A**: Keep all features (current approach) - BQML handles NULLs
- **Option B**: Exclude features <10% coverage - Cleaner training set

**Recommendation**: **Option A** (keep all) - BQML handles NULLs well, and forward-fill will improve coverage

### 3. Verify Feature Count

**Action**: Count total features after schema expansion

**Expected**: ~350+ features (up from ~220)

---

## EXPECTED OUTCOMES

### After Forward-Fill

| Feature Category | Before | After | Improvement |
|-----------------|--------|-------|-------------|
| Social Sentiment | 6% | 60%+ | 10x |
| Trump Policy | 3% | 30%+ | 10x |
| News Derived | 0.3% | 10%+ | 30x |
| CFTC Percentiles | 20.6% | 20.6% | Already good |

### After Historical Backfill

| Feature Category | Before | After | Improvement |
|-----------------|--------|-------|-------------|
| Social Sentiment | 6% | 80%+ | 13x |
| Trump Policy | 3% | 50%+ | 17x |
| News Derived | 0.3% | 80%+ | 267x |
| CFTC Percentiles | 20.6% | 80%+ | 4x |
| USDA Export | 0.5% | 50%+ | 100x |

---

## CONCLUSION

### Current State
- ✅ All new columns added to schema
- ✅ All data merged into training dataset
- ✅ Training query includes all numeric features
- ⚠️ Many features are sparse (0.3-6% coverage)

### To Ensure All Data Gets Trained

1. **Immediate**: Forward-fill sparse features (increases coverage 10-30x)
2. **Short-term**: Verify training query includes all features (already done)
3. **Long-term**: Backfill historical data (increases coverage 10-100x)

### Recommendation

**Start with forward-fill** - This will immediately improve coverage from 0.3-6% to 10-60%, making the features much more useful for training. Historical backfill can follow as a longer-term improvement.


