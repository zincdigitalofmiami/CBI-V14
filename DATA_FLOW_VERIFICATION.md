# Data Flow Verification - Production System
**Last Updated**: November 5, 2025  
**Status**: ✅ PRODUCTION DATASETS RESTORED

---

## 🔄 COMPLETE DATA FLOW (UPDATED NOV 5, 2025)

```
┌────────────────────────────────────────────────────────────┐
│  LAYER 1: DATA INGESTION (Hourly/Daily/Weekly)            │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  • Yahoo Finance (ZL prices) → soybean_oil_prices         │
│  • Alpha Vantage (VIX, indices) → market_indicators       │
│  • Open-Meteo (weather) → weather_data                    │
│  • GDELT (news events) → news_intelligence                │
│  • Scrape Creators (Trump/social) → social_sentiment      │
│  • FRED API (economic) → economic_indicators              │
│  • NOAA API (weather) → weather_data                      │
│  • USDA FAS (exports) → usda_exports                      │
│  • CFTC (positioning) → cftc_data                         │
│  • EIA (biofuels) → biofuel_data                          │
│                                                            │
│  Storage: forecasting_data_warehouse.*                    │
└──────────────────┬─────────────────────────────────────────┘
                   │
                   ↓ FEATURE ENGINEERING & AGGREGATION
                   │
┌────────────────────────────────────────────────────────────┐
│  LAYER 2: FEATURE ENGINEERING                              │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  • Big 8 Signal Calculation → neural.vw_big_eight_signals │
│  • Correlation Matrices → correlation tables              │
│  • Technical Indicators → technical_indicators            │
│  • Weather Aggregations → weather_aggregated              │
│  • Sentiment Scoring → sentiment_scored                   │
│                                                            │
│  Intermediate: signals.*, neural.*, feature tables        │
└──────────────────┬─────────────────────────────────────────┘
                   │
                   ↓ MATERIALIZE TO TRAINING DATASETS
                   │
┌────────────────────────────────────────────────────────────┐
│  LAYER 3: PRODUCTION TRAINING DATASETS (290 features each) │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ✅ production_training_data_1w (1,448 rows, Oct 13)       │
│  ✅ production_training_data_1m (1,347 rows, Sept 10)      │
│  ✅ production_training_data_3m (1,329 rows, June 13)      │
│  ✅ production_training_data_6m (1,198 rows, Feb 4)        │
│                                                            │
│  Storage: models_v4.production_training_data_*            │
│  Features: 290 columns each (see COMPLETE_FEATURE_LIST)   │
└──────────────────┬─────────────────────────────────────────┘
                   │
                   ↓ ML.PREDICT() QUERIES
                   │
┌────────────────────────────────────────────────────────────┐
│  LAYER 4: BQML PRODUCTION MODELS (Trained Nov 4, 2025)     │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ✅ bqml_1w (274 features, MAE 0.393, R² 0.998)            │
│  ✅ bqml_1m (274 features, MAE 0.297, R² 0.987)            │
│  ✅ bqml_3m (268 features, MAE 0.409, R² 0.997)            │
│  ✅ bqml_6m (258 features, MAE 0.401, R² 0.997)            │
│                                                            │
│  Storage: models_v4.bqml_*                                │
│  Type: BOOSTED_TREE_REGRESSOR (100 iterations)            │
└──────────────────┬─────────────────────────────────────────┘
                   │
                   ↓ DAILY PREDICTIONS
                   │
┌────────────────────────────────────────────────────────────┐
│  LAYER 5: PREDICTION OUTPUTS                               │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  predictions_uc1.production_forecasts                     │
│  or predictions.daily_forecasts                           │
│                                                            │
│  Columns:                                                  │
│  • horizon (1w/1m/3m/6m)                                   │
│  • predicted_value (price forecast)                        │
│  • lower_bound_80, upper_bound_80 (confidence interval)    │
│  • forecast_date, target_date                              │
│  • model_name, confidence                                  │
└────────────────────────────────────────────────────────────┘
```

---

## 🚨 CRITICAL CHANGES FROM PREVIOUS SETUP

### OLD (BROKEN):
```
❌ training_dataset_super_enriched (11 columns)
❌ Single table for all horizons
❌ refresh_features_pipeline.py overwrote it daily
```

### NEW (CORRECT):
```
✅ production_training_data_1w/1m/3m/6m (290 columns each)
✅ Separate table per horizon
✅ refresh_features_pipeline.py skips materialization
✅ Manual updates preserve all 290 features
```

---

## 📋 INGESTION REQUIREMENTS

**ALL ingestion scripts must**:
1. Continue updating `forecasting_data_warehouse.*` (existing)
2. **ALSO update ALL 4 `production_training_data_*` tables (NEW)**

**Scripts to modify**:
- scripts/hourly_prices.py
- scripts/daily_weather.py
- ingestion/ingest_social_intelligence_comprehensive.py
- ingestion/backfill_trump_intelligence.py
- ingestion/ingest_market_prices.py
- ingestion/ingest_cftc_positioning_REAL.py
- ingestion/ingest_usda_harvest_api.py
- ingestion/ingest_eia_biofuel_real.py

---

## ✅ VERIFICATION COMMANDS

**Verify datasets exist:**
```bash
bq ls models_v4 | grep "production_training_data"
# Should show 4 tables
```

**Verify feature counts:**
```bash
for h in 1w 1m 3m 6m; do
  echo "=== production_training_data_$h ==="
  bq query --nouse_legacy_sql "
    SELECT COUNT(*) as features 
    FROM \`cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS\` 
    WHERE table_name = 'production_training_data_$h'
  "
done
# Each should show 290 features
```

**Verify models trained:**
```bash
bq query --nouse_legacy_sql "
SELECT model_name, creation_time
FROM \`cbi-v14.models_v4.INFORMATION_SCHEMA.MODELS\`
WHERE model_name IN ('bqml_1w', 'bqml_1m', 'bqml_3m', 'bqml_6m')
ORDER BY model_name
"
# Should show all 4 models created Nov 4, 2025
```

---

**For complete feature list**: See `/COMPLETE_FEATURE_LIST_290.md`  
**For naming conventions**: See `/PRODUCTION_NAMING_CONVENTIONS.md`  
**For system overview**: See `/OFFICIAL_PRODUCTION_SYSTEM.md`







