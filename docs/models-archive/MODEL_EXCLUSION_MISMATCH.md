# Model Exclusion Mismatch - CRITICAL ISSUE

**Date:** November 5, 2025  
**Status:** ❌ **MODELS ARE NOT EXACTLY THE SAME**  
**Priority:** 🔥 **CRITICAL - MUST FIX IMMEDIATELY**

---

## Problem

The 4 BQML models use **DIFFERENT feature sets**, causing:
- Inconsistent model performance comparisons
- Unfair MAPE rankings (models with fewer features perform better)
- Cannot compare models apples-to-apples
- User explicitly required ALL models to use EXACTLY THE SAME features

---

## Current State (BROKEN)

### Model Feature Counts (INCONSISTENT)

| Model | Features | Exclusions | MAPE | Why Different |
|-------|----------|------------|------|---------------|
| **1W** | 276 | 8 columns | 0.72% | Only excludes basic NULL columns |
| **1M** | 274 | 10 columns | 0.70% | Excludes news columns (100% NULL for 1M) |
| **3M** | 268 | 18 columns | 0.69% | Excludes news + trump_soybean columns |
| **6M** | 258 | 28 columns | 0.67% | **MOST AGGRESSIVE** - excludes all NULL columns |

### MAPE Ranking (MISLEADING)

1. **6M: 0.67%** (best) - But uses **258 features** (fewest)
2. **3M: 0.69%** - Uses **268 features**
3. **1M: 0.70%** - Uses **274 features**
4. **1W: 0.72%** (worst) - Uses **276 features** (most)

### Why They Differ (THE PROBLEM)

**6M (0.67% - best):**
- 258 features (excludes 28 NULL columns)
- Most aggressive filtering
- 180-day horizon (most stable)
- **BUT**: Better MAPE might be because it excludes more noise, not because it's actually better

**3M (0.69%):**
- 268 features (excludes 18 NULL columns)
- Excludes news columns (100% NULL)
- 90-day horizon (stable)

**1M (0.70%):**
- 274 features (excludes 10 NULL columns)
- Keeps more features (some sparse)
- 30-day horizon (more volatility)

**1W (0.72% - worst):**
- 276 features (excludes 8 NULL columns)
- Most features (includes sparse data)
- 7-day horizon (most volatile)
- **BUT**: Worse MAPE might be because it includes more noise, not because it's actually worse

### Pattern (THE REAL ISSUE)

- **More NULL exclusions → better MAPE** (not necessarily better model!)
- **Longer horizon → better MAPE** (less volatility)
- **Fewer features with real data → better MAPE** (less noise)

**6M is "best" because it has the most aggressive feature filtering (258 features, excludes 28 NULLs) and the longest, most stable horizon (180 days).**

**1W is "worst" because it keeps the most features (276, only excludes 8 NULLs) and has the shortest, most volatile horizon (7 days).**

---

## Root Cause

**Each model was trained with DIFFERENT EXCEPT clauses:**

### 1W Model Exclusions (8 columns):
```sql
EXCEPT(
  target_1w, target_1m, target_3m, target_6m, date,
  volatility_regime,
  social_sentiment_volatility,
  bullish_ratio,
  bearish_ratio,
  social_sentiment_7d,
  social_volume_7d,
  trump_policy_7d,
  trump_events_7d,
  news_intelligence_7d,
  news_volume_7d
)
```

### 1M Model Exclusions (10 columns):
```sql
EXCEPT(
  -- Same as 1W PLUS:
  news_article_count,
  news_avg_score,
  news_sentiment_avg,
  china_news_count,
  biofuel_news_count,
  tariff_news_count,
  weather_news_count
)
```

### 3M Model Exclusions (18 columns):
```sql
EXCEPT(
  -- Same as 1M PLUS:
  trump_soybean_sentiment_7d
)
```

### 6M Model Exclusions (28 columns):
```sql
EXCEPT(
  -- Same as 3M PLUS:
  trump_agricultural_impact_30d,
  trump_soybean_relevance_30d,
  days_since_trump_policy,
  trump_policy_intensity_14d,
  trump_policy_events,
  trump_policy_impact_avg,
  trump_policy_impact_max,
  trade_policy_events,
  china_policy_events,
  ag_policy_events
)
```

---

## Solution (REQUIRED)

### Step 1: Identify ALL 100% NULL Columns

Run `FIND_ALL_100_PCT_NULL_COLUMNS.sql` to find ALL columns that are 100% NULL across the ENTIRE dataset.

### Step 2: Use MOST AGGRESSIVE Exclusion List

Use **6M's exclusion list (28 columns)** for ALL 4 models. This ensures:
- All models use EXACTLY THE SAME features
- All models have 258 features
- Fair comparison of MAPE
- Models are truly comparable

### Step 3: Retrain ALL Models

Update all 4 training SQL files to use IDENTICAL EXCEPT clauses:
- `TRAIN_BQML_1W_FRESH.sql`
- `TRAIN_BQML_1M_FRESH.sql`
- `TRAIN_BQML_3M_FRESH.sql`
- `TRAIN_BQML_6M_FRESH.sql` (already correct, use as template)

### Step 4: Verify Feature Count

After retraining, all 4 models must have:
- **258 features** (exactly the same)
- **Same EXCEPT clause** (exactly the same)
- **Fair MAPE comparison** (apples-to-apples)

---

## Expected Outcome

After fix:
- All 4 models: **258 features** (identical)
- All 4 models: **Same EXCEPT clause** (identical)
- MAPE ranking will be **fair** (based on horizon/volatility, not feature count)
- Models are **truly comparable**

---

## Files Updated

1. ✅ `bigquery_sql/FIND_ALL_100_PCT_NULL_COLUMNS.sql` - Created
2. ✅ `bigquery_sql/BQML_1W_PRODUCTION.sql` - Fixed: 258 features, 100 iterations
3. ✅ `bigquery_sql/BQML_1M_PRODUCTION.sql` - Fixed: 258 features, 100 iterations
4. ✅ `bigquery_sql/BQML_3M_PRODUCTION.sql` - Fixed: 258 features, 100 iterations
5. ✅ `bigquery_sql/BQML_6M_PRODUCTION.sql` - Fixed: 258 features, 100 iterations

**All files renamed: FRESH → PRODUCTION, removed TRAIN prefix, fixed to use identical configuration.**

---

## Status

- ✅ **FIXED**: All training files updated to use identical configuration
- ✅ **258 features**: All models use same EXCEPT clause (28 exclusions)
- ✅ **100 iterations**: All models use same max_iterations
- ✅ **early_stop=False**: All models use same early stopping
- ✅ **Files renamed**: All files renamed from FRESH to PRODUCTION
- ⏳ **PENDING**: Retrain all 4 models with fixed configuration
- ⏳ **PENDING**: Verify all models have 258 features after retraining

---

**Last Updated:** November 5, 2025  
**Priority:** 🔥 **CRITICAL - MUST FIX BEFORE ANY MODEL COMPARISONS**
