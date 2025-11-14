# CRITICAL: NULL STATUS UPDATE - November 5, 2025

**Last Reviewed:** November 14, 2025

## FINDING: NO COLUMNS ARE 100% NULL ANYMORE

**Date Discovered:** November 5, 2025  
**Status:** ⚠️ **DATA HAS BEEN BACKFILLED** - Previous NULL columns now have data

**Note**: BQML deprecated - all training now runs locally on Mac M4 via TensorFlow Metal. Production tables serve as data sources for local training.

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

### CURRENT TRAINING APPROACH:
- **Training**: Local Mac M4 + TensorFlow Metal (LSTM/GRU)
- **Data Source**: `production_training_data_*` tables exported to Parquet
- **Feature Counts**: 257-275 features per horizon (horizon-specific)
- **Status**: ✅ **LOCAL TRAINING PIPELINE OPERATIONAL**

### RECOMMENDED APPROACH:

**Local Mac M4 Training:**
- Export `production_training_data_*` tables to Parquet
- Train locally using TensorFlow Metal (LSTM/GRU models)
- Feature counts: 257-275 (horizon-specific, excludes minimal NULLs)
- Status: ✅ **READY FOR LOCAL TRAINING**

**Feature Selection:**
- Use ALL 275+ features where available (nothing excluded except targets/date/volatility_regime)
- Handle NULLs appropriately in local training pipeline
- Horizon-specific feature sets maintained

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

**USE LOCAL MAC M4 TRAINING - BQML DEPRECATED**

Data Sources (for local training):
- `cbi-v14.models_v4.production_training_data_1w` (275 features)
- `cbi-v14.models_v4.production_training_data_1m` (274 features)
- `cbi-v14.models_v4.production_training_data_3m` (268 features)
- `cbi-v14.models_v4.production_training_data_6m` (258 features)

**Action:** Export to Parquet and train locally on Mac M4

---

**Report Generated:** 2025-11-05  
**Last Reviewed:** November 14, 2025  
**Critical Decision:** Use horizon-specific feature counts for local Mac M4 training







