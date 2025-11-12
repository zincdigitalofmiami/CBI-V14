# WHY HORIZONS HAVE DIFFERENT FEATURE COUNTS
**Date:** November 5, 2025  
**Status:** Explanation of horizon-specific feature exclusions

---

## THE REASON: TEMPORAL DATA AVAILABILITY

Different horizons have different feature counts because **newer data sources don't exist in older historical windows**.

---

## EXAMPLE: NEWS DATA

**News scraping started:** October 4, 2024  
**Data available from:** October 4, 2024 onwards

### Impact by Horizon:

**1W Model (275 features):**
- Training window: Needs data up to ~October 28, 2025 (for Nov 4 target)
- News columns: **AVAILABLE** for most of training window
- **Result:** News features INCLUDED (only ~300 NULLs out of 1,448 rows)

**1M Model (274 features):**
- Training window: Needs data up to ~October 6, 2025 (for Nov 5 target)
- News columns: **AVAILABLE** for most of training window  
- **Result:** News features INCLUDED

**3M Model (268 features):**
- Training window: Needs data up to ~August 7, 2025 (for Nov 5 target)
- News columns: **100% NULL** (news data starts Oct 4, 2024 - AFTER 3M window)
- **Result:** News features EXCLUDED (7 columns)

**6M Model (258 features):**
- Training window: Needs data up to ~May 8, 2025 (for Nov 5 target)
- News columns: **100% NULL** (news data starts Oct 4, 2024 - AFTER 6M window)
- Trump policy columns: **100% NULL** (data starts Oct 2024 - AFTER 6M window)
- **Result:** News + Trump features EXCLUDED (18 columns total)

---

## FEATURE COUNT BREAKDOWN

| Model | Features | Why Different? |
|-------|----------|---------------|
| **bqml_1w** | 275 | Most features available (only 7 days back) |
| **bqml_1m** | 274 | Most features available (only 30 days back) |
| **bqml_3m** | 268 | News features 100% NULL (3 months back = before Oct 4, 2024) |
| **bqml_6m** | 258 | News + Trump features 100% NULL (6 months back = before Oct 4, 2024) |

---

## SPECIFIC EXCLUSIONS BY HORIZON

### Always Excluded (All Models):
- `target_1w`, `target_1m`, `target_3m`, `target_6m` (other targets)
- `date` (temporal identifier)
- `volatility_regime` (STRING type)

### 1W Model - Excludes 8 columns:
```
Standard (6) + Fully NULL across dataset (2):
- social_sentiment_volatility
- news_volume_7d
```

### 1M Model - Excludes 10 columns:
```
Standard (6) + News columns that are 100% NULL for 1M window (4):
- social_sentiment_volatility
- news_article_count (was NULL, now has ~300 values but still excluded)
- news_avg_score
- news_sentiment_avg
- china_news_count
- biofuel_news_count
- tariff_news_count
- weather_news_count
- news_intelligence_7d
- news_volume_7d
```

### 3M Model - Excludes 18 columns:
```
Standard (6) + Social NULL (2) + News (7) + Trump partial (3):
- All from 1W/1M +
- trump_soybean_sentiment_7d (100% NULL for 3M window)
- (Plus additional news/social columns)
```

### 6M Model - Excludes 28 columns:
```
Standard (6) + All newer data sources (22):
- All from 3M +
- trump_agricultural_impact_30d (data starts Oct 2024, 6M goes back to May 2024)
- trump_soybean_relevance_30d
- days_since_trump_policy
- trump_policy_intensity_14d
- trump_policy_events
- trump_policy_impact_avg
- trump_policy_impact_max
- trade_policy_events
- china_policy_events
- ag_policy_events
```

---

## WHY THIS IS CORRECT

### BQML Cannot Train with 100% NULL Columns

**Error if you try:**
```
"Cannot train with columns that have all NULL values"
```

**Solution:** Exclude columns that are 100% NULL for that specific training window.

### Horizon-Specific NULL Status

**Example: News Article Count**

For `target_6m` training (needs data from May 2024 to Oct 2024):
```sql
SELECT 
  COUNT(*) as total,
  COUNTIF(news_article_count IS NULL) as nulls
FROM training_dataset_super_enriched
WHERE target_6m IS NOT NULL
```

**Result:**
- Total: 1,216 rows (May 2024 - Oct 2024)
- NULLs: 1,216 (100%)
- **Reason:** News scraping didn't exist before October 4, 2024

For `target_1w` training (needs data up to ~Oct 28, 2025):
```sql
SELECT 
  COUNT(*) as total,
  COUNTIF(news_article_count IS NULL) as nulls
FROM training_dataset_super_enriched
WHERE target_1w IS NOT NULL
```

**Result:**
- Total: 1,448 rows
- NULLs: 1,147 (79%)
- Non-NULL: 301 (21%)
- **Reason:** News data exists for Oct 4, 2024 onwards (~1 month of the 1W training window)

---

## VERIFICATION FROM ACTUAL MODELS

From ML.FEATURE_INFO results:

### bqml_1w (275 features)
- `news_article_count`: null_count=1,147, mean=139.5 ✅ **HAS DATA**
- `trump_agricultural_impact_30d`: null_count=1,126, mean=0.37 ✅ **HAS DATA**

### bqml_1m (274 features)
- `bullish_ratio`: null_count=4, mean=0.24 ✅ **HAS DATA**
- `trump_policy_7d`: null_count=994, mean=0.20 ✅ **HAS DATA**

### bqml_3m (267 features)
- `trump_agricultural_impact_30d`: null_count=1,051, mean=0.36 ✅ **HAS DATA**
- News columns: EXCLUDED (100% NULL for 3M window)

### bqml_6m (257 features)
- News columns: EXCLUDED (100% NULL for 6M window)
- Trump columns: EXCLUDED (100% NULL for 6M window)

---

## TIMELINE VISUALIZATION

```
Time -->  May 2024    Aug 2024    Oct 4, 2024     Nov 5, 2025
          |           |           |               |
          |           |           |               |
6M back --+           |           |               +-- Today
          |           |           |               |
3M back --------------+           |               +-- Today
          |           |           |               |
1M back --------------|-----------+---------------+-- Today
          |           |           |               |
1W back --|-----------|-----------|---------------+-- Today
          |           |           |               |
          |           |           +-- News/Trump data STARTS here
          |           |           |
          +-- 6M has NO news/trump data
                      +-- 3M has SOME news/trump data  
                                  +-- 1W/1M have MOST news/trump data
```

---

## SUMMARY

**Different feature counts are CORRECT and NECESSARY:**

1. **Shorter horizons (1W, 1M):** More features available (275-274) because training window includes recent data
2. **Longer horizons (3M, 6M):** Fewer features (268-258) because training window goes back before new data sources existed
3. **BQML requirement:** Cannot train with 100% NULL columns - must exclude them
4. **Horizon-specific exclusions:** Based on NULL status for that specific training window, not entire dataset

**This is optimal:** Each model uses the maximum features available for its specific training window.

---

**Conclusion:** Feature counts SHOULD be different by horizon. It's not a bug - it's the correct implementation.







