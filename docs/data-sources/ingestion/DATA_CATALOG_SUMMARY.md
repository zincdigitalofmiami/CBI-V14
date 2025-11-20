---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# 📊 CBI-V14 DATA CATALOG SUMMARY
**Date:** November 5, 2025  
**Last Reviewed:** November 14, 2025  
**Purpose:** Master reference for ALL available data

**Note**: BQML deprecated - production tables serve as data sources for local Mac M4 + TensorFlow Metal training.

---

## 🎯 KEY DISCOVERIES

### 1. ✅ **YOU HAVE MASSIVE DATA RESOURCES**
- **50+ tables** in `forecasting_data_warehouse`
- **300 features** in production training datasets
- **5+ years** of historical data
- **56 heavy hitter features** (VIX, Tariffs, Biofuels)

### 2. 🔥 **VERTEX AI EXPORT DATA FOUND!**
```
export_evaluated_data_items_cbi_v14_automl_pilot_1w_2025_10_28T10_08_35_327Z.evaluated_data_items
- 200+ columns of ALL features
- 112 rows (2020-2025)
- Perfect for validation/backtesting
```

### 3. 💪 **HEAVY HITTERS CONFIRMED**
| Category | Features | Coverage | Status |
|----------|----------|----------|--------|
| VIX/Volatility | 14 | 100% | ✅ EXCELLENT |
| Tariffs/Trade | 33! | 64-100% | ✅ STRONG |
| Biofuels | 9 | Mixed | ⚠️ Needs RIN/RFS |

---

## 📍 DATA LOCATIONS

### Primary Sources
```
cbi-v14.forecasting_data_warehouse/
├── 50+ tables with raw data
├── All prices (soybean, palm, corn, wheat, crude)
├── VIX, CFTC, China imports
├── Trump policy, news, sentiment
└── Weather, freight, biofuel data

cbi-v14.models_v4/
├── production_training_data_1w (300 features)
├── production_training_data_1m (300 features)
├── production_training_data_3m (300 features)
├── production_training_data_6m (300 features)
└── All daily aggregations

cbi-v14.neural/
└── vw_big_eight_signals (Current through Nov 6!)
```

---

## 🎯 CONSOLIDATION TARGET

**ALL data should flow into:**
```sql
production_training_data_1w  -- 300 features → Export to Parquet → Local Mac M4 Training
production_training_data_1m  -- 300 features → Export to Parquet → Local Mac M4 Training
production_training_data_3m  -- 300 features → Export to Parquet → Local Mac M4 Training
production_training_data_6m  -- 300 features → Export to Parquet → Local Mac M4 Training
```

**Data Flow**: BigQuery → Parquet Export → Local Mac M4 Training → Predictions → BigQuery

---

## 📝 ACTION ITEMS

1. **Run consolidation** to update production tables with ALL available data
2. **Archive old tables** to avoid confusion
3. **Set up pipelines** to keep data current
4. **Use Vertex AI export** for validation

---

**Full details in:** `CBI_V14_COMPLETE_EXECUTION_PLAN.md` → Section: "MASTER DATA CATALOG"
