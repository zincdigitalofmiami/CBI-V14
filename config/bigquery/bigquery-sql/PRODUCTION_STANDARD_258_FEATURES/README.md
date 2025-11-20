---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# PRODUCTION STANDARD: 258 FEATURES - ALL HORIZONS
**Status:** ✅ PRODUCTION - USE THESE FILES ONLY  
**Date Established:** November 5, 2025  
**Last Verified:** November 5, 2025

---

## ⚠️ CRITICAL: THIS IS THE ONLY PRODUCTION CONFIGURATION

**All 4 models use IDENTICAL 258 features.**  
**DO NOT use files outside this folder for production training.**

---

## FOLDER METADATA

```json
{
  "folder_name": "PRODUCTION_STANDARD_258_FEATURES",
  "purpose": "Standardized BQML training configuration - 258 features for all horizons",
  "status": "PRODUCTION",
  "feature_count": 258,
  "excluded_columns": 34,
  "models": ["bqml_1w_all_features", "bqml_1m_all_features", "bqml_3m_all_features", "bqml_6m_all_features"],
  "data_source": "cbi-v14.models_v4.training_dataset_super_enriched",
  "last_updated": "2025-11-05",
  "maintainer": "CBI-V14 Production Team"
}
```

---

## FILES IN THIS FOLDER

### Training SQL Files (USE THESE)
1. **TRAIN_BQML_1W_STANDARD.sql** - 1 Week model (258 features)
2. **TRAIN_BQML_1M_STANDARD.sql** - 1 Month model (258 features)
3. **TRAIN_BQML_3M_STANDARD.sql** - 3 Month model (258 features)
4. **TRAIN_BQML_6M_STANDARD.sql** - 6 Month model (258 features)

### Prediction SQL Files
5. **GENERATE_PREDICTIONS_STANDARD.sql** - Generate predictions from all 4 standardized models

### Documentation
6. **EXCLUSION_LIST_STANDARD.txt** - Complete list of 34 excluded columns
7. **FEATURE_LIST_258.txt** - Complete list of 258 features used
8. **README.md** - This file

---

## STANDARDIZED CONFIGURATION

### Models Created
- `cbi-v14.models_v4.bqml_1w_all_features`
- `cbi-v14.models_v4.bqml_1m_all_features`
- `cbi-v14.models_v4.bqml_3m_all_features`
- `cbi-v14.models_v4.bqml_6m_all_features`

### Data Source
- **Table:** `cbi-v14.models_v4.training_dataset_super_enriched`
- **Filter:** `WHERE target_{horizon} IS NOT NULL`

### Features
- **Total Features:** 258 (identical across all horizons)
- **Excluded Columns:** 34
  - 6 standard (targets, date, volatility_regime)
  - 28 columns that are 100% NULL across entire dataset

### Training Parameters
```sql
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_{horizon}'],
  max_iterations=100,
  learn_rate=0.1,
  early_stop=False
)
```

---

## EXCLUSION LIST (IDENTICAL FOR ALL MODELS)

### Standard Exclusions (6)
- `target_1w`, `target_1m`, `target_3m`, `target_6m` (all except current)
- `date`
- `volatility_regime`

### 100% NULL Columns - Social/News Basic (8)
- `social_sentiment_volatility`
- `bullish_ratio`
- `bearish_ratio`
- `social_sentiment_7d`
- `social_volume_7d`
- `trump_policy_7d`
- `trump_events_7d`
- `news_intelligence_7d`
- `news_volume_7d`

### 100% NULL Columns - News (7)
- `news_article_count`
- `news_avg_score`
- `news_sentiment_avg`
- `china_news_count`
- `biofuel_news_count`
- `tariff_news_count`
- `weather_news_count`

### 100% NULL Columns - Trump/Policy (11)
- `trump_soybean_sentiment_7d`
- `trump_agricultural_impact_30d`
- `trump_soybean_relevance_30d`
- `days_since_trump_policy`
- `trump_policy_intensity_14d`
- `trump_policy_events`
- `trump_policy_impact_avg`
- `trump_policy_impact_max`
- `trade_policy_events`
- `china_policy_events`
- `ag_policy_events`

**Total:** 34 excluded columns

---

## USAGE INSTRUCTIONS

### To Train Models
```bash
# Run each training file in BigQuery:
# 1. TRAIN_BQML_1W_STANDARD.sql
# 2. TRAIN_BQML_1M_STANDARD.sql
# 3. TRAIN_BQML_3M_STANDARD.sql
# 4. TRAIN_BQML_6M_STANDARD.sql
```

### To Generate Predictions
```bash
# Run prediction file:
# GENERATE_PREDICTIONS_STANDARD.sql
```

### Verification
```sql
-- Verify all models exist:
SELECT training_run, iteration, loss, eval_loss
FROM ML.TRAINING_INFO(MODEL `cbi-v14.models_v4.bqml_1w_all_features`)
ORDER BY iteration DESC LIMIT 5;

-- Repeat for 1m, 3m, 6m
```

---

## DATA INGESTION REQUIREMENTS

### Training Data Table
**Table:** `cbi-v14.models_v4.training_dataset_super_enriched`

**Required Columns:**
- All 258 feature columns
- Target columns: `target_1w`, `target_1m`, `target_3m`, `target_6m`
- `date` column (for filtering)
- `volatility_regime` (STRING, excluded from training)

**Data Ingestion:**
- All scrapers and data pipelines MUST write to this table
- Table must be kept up-to-date with latest dates
- Targets must be backfilled for historical evaluation

---

## MIGRATION FROM OLD FILES

### Old Files (DO NOT USE)
- `BQML_1W.sql` (275 features)
- `BQML_1M.sql` (274 features)
- `BQML_3M.sql` (268 features)
- `BQML_6M.sql` (258 features - horizon-specific)

### New Files (USE THESE)
- `TRAIN_BQML_1W_STANDARD.sql` (258 features - standardized)
- `TRAIN_BQML_1M_STANDARD.sql` (258 features - standardized)
- `TRAIN_BQML_3M_STANDARD.sql` (258 features - standardized)
- `TRAIN_BQML_6M_STANDARD.sql` (258 features - standardized)

### Migration Notes
- Old models (`bqml_1w`, etc.) still exist but use different feature counts
- New standardized models use `_all_features` suffix
- Update prediction SQL to use `bqml_{horizon}_all_features` models

---

## SAFEGUARDS

✅ All files in this folder use identical exclusion lists  
✅ All models train on same 258 features  
✅ Feature consistency verified across all horizons  
✅ Data source verified: `training_dataset_super_enriched`  
✅ Prediction SQL updated to use standardized models  

---

## CONTACT & SUPPORT

**Questions?** Refer to:
- `/CBI-V14/STANDARDIZED_PRODUCTION_CONFIG.md`
- `/CBI-V14/PRODUCTION_WORKING_CONFIGURATION.md`
- `/CBI-V14/CBI_V14_COMPLETE_EXECUTION_PLAN.md`

**Last Audit:** November 5, 2025  
**Next Review:** When retraining models or updating features

---

**DO NOT MODIFY FILES IN THIS FOLDER WITHOUT UPDATING THIS README**







