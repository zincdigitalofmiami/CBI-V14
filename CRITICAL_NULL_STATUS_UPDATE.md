# CRITICAL: NULL STATUS UPDATE - November 5, 2025

## FINDING: NO COLUMNS ARE 100% NULL ANYMORE

**Date Discovered:** November 5, 2025  
**Status:** ⚠️ **DATA HAS BEEN BACKFILLED** - Previous NULL columns now have data

---

## NULL STATUS VERIFICATION RESULTS

**Checked:** All columns previously marked as "100% NULL"  
**Result:** **ZERO columns are 100% NULL**  
**Conclusion:** Data backfill has populated previously NULL columns

### Previously "NULL" Columns Now Have Data:

| Column | Non-NULL Values | Populated % |
|--------|----------------|-------------|
| `news_article_count` | 301 | 20.8% |
| `news_avg_score` | 301 | 20.8% |
| `news_sentiment_avg` | 303 | 20.9% |
| `china_news_count` | 303 | 20.9% |
| `biofuel_news_count` | 303 | 20.9% |
| `tariff_news_count` | 303 | 20.9% |
| `weather_news_count` | 303 | 20.9% |
| `trump_soybean_sentiment_7d` | 303 | 20.9% |
| `trump_agricultural_impact_30d` | ~300 | ~20% |
| `trump_soybean_relevance_30d` | ~300 | ~20% |
| `bullish_ratio` | 1,444 | 99.7% |
| `bearish_ratio` | 1,444 | 99.7% |
| `social_sentiment_7d` | 1,444 | 99.7% |
| `social_volume_7d` | 1,444 | 99.7% |
| `trump_policy_7d` | ~450 | ~31% |
| `trump_events_7d` | ~450 | ~31% |

---

## REVISED RECOMMENDATION

### CURRENT PRODUCTION MODELS (Working):
- `bqml_1w`: 275 features (excludes minimal NULLs)
- `bqml_1m`: 274 features
- `bqml_3m`: 267 features
- `bqml_6m`: 257 features

### RECOMMENDED APPROACH:

**Option 1: Use Current Working Models (SAFEST)**
- Models: `bqml_1w`, `bqml_1m`, `bqml_3m`, `bqml_6m` (without `_all_features` suffix)
- These are ALREADY trained and generating predictions
- Feature counts: 257-275 (horizon-specific)
- Status: ✅ **WORKING IN PRODUCTION**

**Option 2: Retrain with Maximum Features**
- Use ALL 275+ features (nothing excluded except targets/date/volatility_regime)
- Train new models: `bqml_{horizon}_max_features`
- Requires retraining

### DECISION NEEDED:

**Since current models are working with predictions generated Nov 4, 2025:**

✅ **RECOMMENDED: Keep current working models (`bqml_1w`, `bqml_1m`, `bqml_3m`, `bqml_6m`)**
- Already trained
- Already generating predictions
- Feature counts are appropriate for each horizon
- NO NEED to create new standardized models

---

## UPDATED EXCLUSION STRATEGY

### Only Exclude:
1. **Required exclusions:**
   - All target columns except current (`target_1w`, `target_1m`, `target_3m`, `target_6m`)
   - `date` (temporal identifier)
   - `volatility_regime` (STRING type)

2. **Horizon-specific exclusions:**
   - Columns with 100% NULL for that specific horizon only
   - Example: News columns for 6M (news data starts Oct 2024, 6M lookback goes to May 2024)

### Total Exclusions by Horizon:
- **1W:** 6-8 columns (minimal)
- **1M:** 6-10 columns  
- **3M:** 6-18 columns (news columns 100% NULL for 3M horizon)
- **6M:** 6-28 columns (news + trump columns 100% NULL for 6M horizon)

---

## PRODUCTION DECISION

**USE CURRENT WORKING MODELS - DO NOT CHANGE**

Models:
- `cbi-v14.models_v4.bqml_1w` (275 features)
- `cbi-v14.models_v4.bqml_1m` (274 features)
- `cbi-v14.models_v4.bqml_3m` (268 features)
- `cbi-v14.models_v4.bqml_6m` (258 features)

SQL Files (in `_ARCHIVED/HORIZON_SPECIFIC_OLD/`):
- `BQML_1W.sql`
- `BQML_1M.sql`
- `BQML_3M.sql`
- `BQML_6M.sql`

**Action:** MOVE THESE BACK TO PRODUCTION FOLDER

---

**Report Generated:** 2025-11-05  
**Critical Decision:** Use horizon-specific feature counts (current working models)







