# STANDARDIZED PRODUCTION CONFIGURATION
**Date:** November 5, 2025  
**Decision:** Use **258 features for ALL horizons** - identical configuration

---

## THE DECISION

**Standardized Configuration:**
- ✅ **258 features** for ALL 4 horizons (1W, 1M, 3M, 6M)
- ✅ **Identical exclusion list** across all models
- ✅ **Model names:** `bqml_{horizon}_all_features`
- ✅ **Training SQL:** `BQML_{HORIZON}_PRODUCTION.sql`

**Comment from SQL files:**
```
-- All models use identical configuration: 258 features, 100 iterations
-- EXACT SAME AS ALL OTHER MODELS: Exclude ALL columns that are 100% NULL across entire dataset
-- This ensures ALL 4 models use EXACTLY THE SAME features (258 features)
```

---

## STANDARDIZED EXCLUSION LIST (28 COLUMNS)

**All 4 models use this EXACT exclusion list:**

```sql
EXCEPT(
  target_1w, target_1m, target_3m, target_6m,  -- All targets except current
  date,                                       -- Temporal identifier
  volatility_regime,                          -- STRING type
  
  -- Standard NULL columns (8):
  social_sentiment_volatility,  -- 100% NULL
  bullish_ratio,               -- 100% NULL
  bearish_ratio,               -- 100% NULL
  social_sentiment_7d,         -- 100% NULL
  social_volume_7d,            -- 100% NULL
  trump_policy_7d,             -- 100% NULL
  trump_events_7d,             -- 100% NULL
  news_intelligence_7d,        -- 100% NULL
  news_volume_7d,              -- 100% NULL
  
  -- News columns (7):
  news_article_count,          -- 100% NULL
  news_avg_score,              -- 100% NULL
  news_sentiment_avg,          -- 100% NULL
  china_news_count,            -- 100% NULL
  biofuel_news_count,          -- 100% NULL
  tariff_news_count,           -- 100% NULL
  weather_news_count,          -- 100% NULL
  
  -- Trump columns (11):
  trump_soybean_sentiment_7d,  -- 100% NULL
  trump_agricultural_impact_30d,  -- 100% NULL
  trump_soybean_relevance_30d,    -- 100% NULL
  days_since_trump_policy,        -- 100% NULL
  trump_policy_intensity_14d,     -- 100% NULL
  trump_policy_events,             -- 100% NULL
  trump_policy_impact_avg,        -- 100% NULL
  trump_policy_impact_max,         -- 100% NULL
  trade_policy_events,             -- 100% NULL
  china_policy_events,             -- 100% NULL
  ag_policy_events                 -- 100% NULL
)
```

**Total Excluded:** 6 (targets + date + volatility_regime) + 28 (100% NULL columns) = **34 columns excluded**

**Result:** ✅ **258 numeric features** used for training

---

## PRODUCTION SQL FILES

**Standardized Training Files:**
- `bigquery-sql/BQML_1W_PRODUCTION.sql` → `bqml_1w_all_features`
- `bigquery-sql/BQML_1M_PRODUCTION.sql` → `bqml_1m_all_features`
- `bigquery-sql/BQML_3M_PRODUCTION.sql` → `bqml_3m_all_features`
- `bigquery-sql/BQML_6M_PRODUCTION.sql` → `bqml_6m_all_features`

**Alternative Files (same config):**
- `bigquery-sql/TRAIN_BQML_1W_PRODUCTION.sql`
- `bigquery-sql/TRAIN_BQML_1M_PRODUCTION.sql`
- `bigquery-sql/TRAIN_BQML_3M_PRODUCTION.sql`
- `bigquery-sql/TRAIN_BQML_6M_PRODUCTION.sql`

---

## COMPLETE STANDARDIZED TEMPLATE

```sql
-- ============================================
-- TRAIN BQML {HORIZON} MODEL - PRODUCTION
-- All models use identical configuration: 258 features, 100 iterations
-- ============================================

DROP MODEL IF EXISTS `cbi-v14.models_v4.bqml_{horizon}_all_features`;

CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_{horizon}_all_features`

OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_{horizon}'],
  max_iterations=100,
  learn_rate=0.1,
  early_stop=False
) AS

SELECT 
  target_{horizon},
  * EXCEPT(
    target_1w, target_1m, target_3m, target_6m,
    date,
    volatility_regime,
    social_sentiment_volatility,
    bullish_ratio,
    bearish_ratio,
    social_sentiment_7d,
    social_volume_7d,
    trump_policy_7d,
    trump_events_7d,
    news_intelligence_7d,
    news_volume_7d,
    news_article_count,
    news_avg_score,
    news_sentiment_avg,
    china_news_count,
    biofuel_news_count,
    tariff_news_count,
    weather_news_count,
    trump_soybean_sentiment_7d,
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
  -- ✅ 258 NUMERIC FEATURES (excludes 34 columns - EXACTLY THE SAME AS ALL OTHER MODELS)
  
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_{horizon} IS NOT NULL;
```

---

## KEY DIFFERENCES FROM HORIZON-SPECIFIC VERSIONS

**Old Horizon-Specific Versions:**
- `bqml_1w`: 275 features (8 excluded)
- `bqml_1m`: 274 features (10 excluded)
- `bqml_3m`: 268 features (18 excluded)
- `bqml_6m`: 258 features (28 excluded)

**New Standardized Version:**
- `bqml_1w_all_features`: **258 features** (34 excluded)
- `bqml_1m_all_features`: **258 features** (34 excluded)
- `bqml_3m_all_features`: **258 features** (34 excluded)
- `bqml_6m_all_features`: **258 features** (34 excluded)

**Rationale:**
- Consistency across all horizons
- Easier to compare model performance
- Same feature set ensures fair comparison
- Excludes ALL 100% NULL columns (not just horizon-specific ones)

---

## CURRENT STATUS

**Both Model Sets Exist:**
- ✅ `bqml_1w`, `bqml_1m`, `bqml_3m`, `bqml_6m` (horizon-specific features)
- ✅ `bqml_1w_all_features`, `bqml_1m_all_features`, `bqml_3m_all_features`, `bqml_6m_all_features` (standardized 258 features)

**Production Predictions:**
- Currently using: `bqml_1w`, `bqml_1m`, `bqml_3m`, `bqml_6m` (without suffix)
- Standardized version: `bqml_{horizon}_all_features` (258 features)

**Recommendation:**
- Use standardized `_all_features` models for consistency
- Update prediction SQL to use `bqml_{horizon}_all_features` instead of `bqml_{horizon}`

---

## SUMMARY

**Final Decision:** Use **258 features for ALL horizons** - identical configuration across all 4 models.

**Files:**
- `BQML_{HORIZON}_PRODUCTION.sql` (standardized version)
- Model names: `bqml_{horizon}_all_features`

**Exclusion:** 34 columns (6 standard + 28 100% NULL columns)

**Result:** ✅ **258 numeric features** - same for all horizons

---

**Document Generated:** 2025-11-05  
**Based On:** `BQML_{HORIZON}_PRODUCTION.sql` files with explicit comments about standardization







