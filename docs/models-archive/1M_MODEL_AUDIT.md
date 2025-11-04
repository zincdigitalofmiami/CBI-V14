# 1M MODEL TRAINING AUDIT - REVERSE ENGINEERED FROM 1W

**Date:** November 3, 2025

---

## ✅ SUCCESSFUL 1W MODEL ANALYSIS

**Model:** `bqml_1w_all_features`  
**Status:** ✅ TRAINED SUCCESSFULLY  
**Training Date:** Nov 3, 18:35  
**Performance:**
- Training loss: 0.708
- Eval loss: 1.455
- Iterations: 50 (converged)

**Approach:**
- Used training_dataset_super_enriched directly (NOT train_1w view)
- Minimal EXCEPT clause: Only 9 all-NULL columns excluded
- Hyperparameters: Simple (learn_rate=0.1, max_iter=50)
- **Let BQML handle partial NULLs** (CFTC, economic, weather columns with 97-99% NULLs)

**Columns Excluded in 1W:**
1. target_1w, target_1m, target_3m, target_6m (labels)
2. date (non-feature)
3. volatility_regime (STRING type)
4. social_sentiment_volatility (all NULL)
5. bullish_ratio (all NULL)
6. bearish_ratio (all NULL)
7. social_sentiment_7d (all NULL)
8. social_volume_7d (all NULL)
9. trump_policy_7d (all NULL)
10. trump_events_7d (all NULL)
11. news_intelligence_7d (all NULL)
12. news_volume_7d (all NULL)

**Total excluded:** 12 columns  
**Features used:** ~276 features (including columns with 97% NULLs!)

---

## 🔍 1M MODEL AUDIT (REVERSE ENGINEERED)

**Training Data:**
- View: train_1m (1,347 rows)
- Train set: 1,153 rows (86%)
- Eval set: 194 rows (14%)
- Target: target_1m (65.93% filled)

**NULL Analysis:**
When using same EXCEPT as 1W, found **7 additional all-NULL columns** in 1M dataset:
1. news_article_count
2. news_avg_score
3. china_news_count
4. biofuel_news_count
5. tariff_news_count
6. weather_news_count
7. news_sentiment_avg

**Root Cause:** 
These news columns exist in 1w data but are all-NULL in 1m data (different date ranges)

---

## ✅ SOLUTION FOR 1M MODEL

**File:** `bigquery_sql/train_1m_model.sql`

**EXCEPT Clause (16 columns):**
- Same 9 as 1w
- Plus 7 additional all-NULL news columns

**Expected Performance:**
- Should train successfully like 1w
- Will use ~269 features
- Training time: ~10-15 minutes

---

## 📋 FINAL 1M MODEL READINESS

- [x] Training SQL created
- [x] All-NULL columns identified and excluded
- [x] Syntax validated (dry-run passed)
- [x] Sufficient data (1,153 training rows)
- [x] Proper train/eval split
- [x] Reverse engineered from successful 1w approach

**Status:** ✅ READY TO TRAIN

**Command:**
```bash
cd /Users/zincdigital/CBI-V14
bq query --use_legacy_sql=false < bigquery_sql/train_1m_model.sql
```


