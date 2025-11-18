# Data Quality Status
**Last Updated**: November 14, 2025  
**Purpose**: Consolidated status of data quality and model organization

**Note**: BQML deprecated - all training now runs locally on Mac M4 via TensorFlow Metal. Production tables serve as data sources for local training.

---

## NULL Status Update (November 5, 2025)

### Finding: NO COLUMNS ARE 100% NULL ANYMORE

**Date Discovered**: November 5, 2025  
**Status**: ⚠️ **DATA HAS BEEN BACKFILLED** - Previous NULL columns now have data

### Previously "NULL" Columns Now Have Data

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

## Current Training Approach

### Local Mac M4 Training
- **Training**: Local Mac M4 + TensorFlow Metal (LSTM/GRU)
- **Data Source**: `production_training_data_*` tables exported to Parquet
- **Feature Counts**: 257-275 features per horizon (horizon-specific)
- **Status**: ✅ **LOCAL TRAINING PIPELINE OPERATIONAL**

### Feature Selection
- Use ALL 275+ features where available (nothing excluded except targets/date/volatility_regime)
- Handle NULLs appropriately in local training pipeline
- Horizon-specific feature sets maintained

### Data Sources (for local training)
- `cbi-v14.models_v4.production_training_data_1w` (275 features)
- `cbi-v14.models_v4.production_training_data_1m` (274 features)
- `cbi-v14.models_v4.production_training_data_3m` (268 features)
- `cbi-v14.models_v4.production_training_data_6m` (258 features)

**Action**: Export to Parquet and train locally on Mac M4

---

## Exclusion Strategy

### Only Exclude
1. **Required exclusions**:
   - All target columns except current (`target_1w`, `target_1m`, `target_3m`, `target_6m`)
   - `date` (temporal identifier)
   - `volatility_regime` (STRING type)

2. **Horizon-specific exclusions**:
   - Columns with 100% NULL for that specific horizon only
   - Example: News columns for 6M (news data starts Oct 2024, 6M lookback goes to May 2024)

### Total Exclusions by Horizon
- **1W**: 6-8 columns (minimal)
- **1M**: 6-10 columns
- **3M**: 6-18 columns (news columns 100% NULL for 3M horizon)
- **6M**: 6-28 columns (news + trump columns 100% NULL for 6M horizon)

---

## Model Organization (Historical)

**Note**: BQML deprecated - this section describes historical model organization.

### Simple Structure

Just **2 datasets** with **1 table each**:

```
cbi-v14/
├── models_trained/
│   └── all_models (27 models)
└── models_failed/
    └── all_models (11 models)
```

### Table Schema

Each `all_models` table has:
- `model_name` - Name of the model
- `model_type` - 'bqml' (deprecated), 'Vertex', or 'Local' (Mac M4)
- `category` - 'Baselines', 'Predictions', or 'General Training'
- `month` - Creation month (YYYY-MM)
- `score_tier` - 'Top Scoring', 'Middle Scores', or 'Lowest Scores' (trained only)
- `mae` - Mean Absolute Error
- `r2_score` - R² score
- `source_location` - Where the actual model lives (models_v4.*, Vertex AI, or local Mac M4)
- `created` - Creation timestamp

**Note**: BQML models are deprecated. All new training uses local Mac M4 + TensorFlow Metal.

---

## Summary

### Data Quality
- ✅ No columns are 100% NULL anymore
- ✅ Data backfill completed successfully
- ✅ Feature coverage: 20-99.7% depending on feature type

### Training Status
- ✅ Local Mac M4 training pipeline operational
- ✅ Production tables ready for Parquet export
- ✅ Horizon-specific feature sets maintained
- ✅ BQML deprecated (all training now local)

---

**Last Reviewed**: November 14, 2025  
**Training Approach**: Local Mac M4 + TensorFlow Metal (BQML deprecated)



