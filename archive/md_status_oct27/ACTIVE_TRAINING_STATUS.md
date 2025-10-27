# ACTIVE MODEL TRAINING STATUS
**Date:** October 22, 2025  
**Time:** 17:22 UTC

## 📊 CURRENT MODEL INVENTORY

### Total Models: 27

## ✅ SUCCESSFULLY TRAINED (Last Hour)

### V3 Production Models (8 models)
| Model | Type | MAE | R² | Status |
|-------|------|-----|-----|--------|
| `zl_boosted_tree_1w_v3` | Boosted Tree | 1.72 | 0.956 | 🌟 Excellent |
| `zl_boosted_tree_1m_v3` | Boosted Tree | 2.81 | 0.892 | ✓ Good |
| `zl_boosted_tree_3m_v3` | Boosted Tree | 3.69 | 0.796 | ✓ Good |
| `zl_boosted_tree_6m_v3` | Boosted Tree | 4.08 | 0.647 | ✓ Acceptable |
| `zl_linear_1w_v3` | Linear | 2.30 | 0.909 | ✓ Baseline |
| `zl_linear_1m_v3` | Linear | 5.02 | 0.645 | Baseline |
| `zl_linear_3m_v3` | Linear | 7.85 | 0.247 | Baseline |
| `zl_linear_6m_v3` | Linear | 8.32 | 0.173 | Baseline |

### Special/Optimized Models
- `zl_boosted_tree_1w_trending` - Regime-based model (11 min ago)
- `zl_boosted_tree_1w_simple` - Test model (44 min ago)

## ⏳ TRAINING STATUS

### Failed Training:
- ❌ `zl_boosted_tree_signals_v4` - FAILED (duplicate column issue)
- ❌ `zl_boosted_tree_1w_tuned` - Unknown status
- ❌ `zl_boosted_tree_1m_tuned` - Unknown status
- ❌ `zl_boosted_tree_1w_high_vol` - Unknown status

## 📈 PERFORMANCE SUMMARY

### Best Performers:
1. **1-Week**: `zl_boosted_tree_1w_v3` - MAE 1.72 🌟
2. **1-Month**: `zl_boosted_tree_1m_v3` - MAE 2.81 ✓
3. **3-Month**: `zl_boosted_tree_3m_v3` - MAE 3.69 ✓
4. **6-Month**: `zl_boosted_tree_6m_v3` - MAE 4.08 ✓

## 🔧 SIGNAL INTEGRATION STATUS

### Materialized Feature Tables Created:
- ✅ `vix_features_materialized` - 2,717 rows
- ✅ `sentiment_features_materialized` - 581 rows  
- ✅ `news_features_materialized` - 13 rows
- ✅ `tariff_features_materialized` - 46 rows
- ✅ `signals_master` - 2,830 rows (combined)

### Signal Coverage:
- VIX: 96% of days
- Sentiment: 21% of days
- Tariff: 1.6% of days
- News: 0.5% of days

## ❗ ISSUES TO RESOLVE

1. **Duplicate Column Error**: The `training_dataset_signals_v4` table has duplicate `tariff_mentions` column
2. **Window Function Errors**: Some queries still using window functions instead of materialized tables
3. **Data Type Mismatches**: INT64 vs STRING issues in some joins

## 🎯 RECOMMENDATIONS

### Immediate Actions:
1. **Fix duplicate columns** in signal dataset
2. **Retrain signals model** with corrected schema
3. **Evaluate trending model** once complete

### Performance Goals:
- Current Best MAE: 1.72 (1-week)
- Target MAE: < 1.0
- Path: Properly integrate signals without duplicates

## 📝 COMMANDS TO RUN

### Check Model Performance:
```sql
SELECT * FROM ML.EVALUATE(MODEL `cbi-v14.models.zl_boosted_tree_1w_v3`)
```

### Check Trending Model:
```sql
SELECT * FROM ML.EVALUATE(MODEL `cbi-v14.models.zl_boosted_tree_1w_trending`)
```

### Fix Signal Dataset:
```sql
CREATE OR REPLACE TABLE `cbi-v14.models.training_dataset_signals_v5` AS
SELECT * EXCEPT(tariff_mentions),
       tariff_mentions as signal_tariff_mentions
FROM `cbi-v14.models.training_dataset_signals_v4`
```

---

**Status**: 8 V3 models successfully trained and ready for production. Signal integration needs column name fixes.
