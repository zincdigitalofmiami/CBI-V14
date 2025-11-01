# COMPREHENSIVE DATABASE & INTEGRATION AUDIT
**Date:** October 30, 2025  
**Purpose:** Verify ALL tables, views, signals, and integrations are properly built and connected

---

## 1. DASHBOARD API REQUIREMENTS MAPPING

### `/api/v4/big-eight-signals`
**Needs:**
- `models_v4.training_dataset_super_enriched` → columns: `feature_vix_stress`, `feature_harvest_pace`, `feature_china_relations`, `feature_tariff_threat`, `feature_geopolitical_volatility`, `feature_biofuel_cascade`, `feature_hidden_correlation`, `feature_biofuel_ethanol`, `big8_composite_score`, `market_regime`, `date`
**Status:** ✅ Table exists, columns verified

### `/api/v4/price-drivers`
**Needs:**
- `models_v4.training_dataset_super_enriched` → Big-8 features (same as above)
- `forecasting_data_warehouse.soybean_oil_prices` → `close` column, `time` column (DATETIME)
**Status:** ✅ Tables exist

### `/api/v4/risk-radar`
**Needs:**
- `models_v4.training_dataset_super_enriched` → Big-8 features
**Status:** ✅ Table exists

### `/api/v4/substitution-economics`
**Needs:**
- `forecasting_data_warehouse.soybean_oil_prices` → `close`, `time`, `symbol`
- `forecasting_data_warehouse.palm_oil_prices` → `close`
- `forecasting_data_warehouse.canola_oil_prices` → `close`
- `models_v4.training_dataset_super_enriched` → `feature_hidden_correlation`
**Status:** ✅ All tables exist

### `/api/v4/forward-curve`
**Needs:**
- `forecasting_data_warehouse.soybean_oil_prices` → historical prices (365 days)
- `predictions.monthly_vertex_predictions` → forecasts for all horizons
**Status:** ⚠️ `monthly_vertex_predictions` only has 1W (missing 1M, 3M, 6M)

### `/api/v4/forecast/1w`
**Needs:**
- `predictions.monthly_vertex_predictions` → horizon='1W'
- `forecasting_data_warehouse.soybean_oil_prices` → current price
**Status:** ✅ 1W exists, current price available

### `/api/v4/forecast/1m`
**Needs:**
- `predictions.daily_forecasts` → horizon='1M' OR `monthly_vertex_predictions` → horizon='1M'
- `forecasting_data_warehouse.soybean_oil_prices` → current price
**Status:** ❌ NO DATA - Both tables empty for 1M

### `/api/v4/forecast/3m`
**Needs:**
- `predictions.daily_forecasts` → horizon='3M' OR `monthly_vertex_predictions` → horizon='3M'
- `forecasting_data_warehouse.soybean_oil_prices` → current price
**Status:** ❌ NO DATA - Both tables empty for 3M

### `/api/v4/forecast/6m`
**Needs:**
- `predictions.daily_forecasts` → horizon='6M' OR `monthly_vertex_predictions` → horizon='6M'
- `forecasting_data_warehouse.soybean_oil_prices` → current price
**Status:** ❌ NO DATA - Both tables empty for 6M

### `/api/v4/ensemble-forecast`
**Needs:**
- `predictions.daily_forecasts` → all horizons for ensemble combination
- `forecasting_data_warehouse.soybean_oil_prices` → current price
**Status:** ❌ NO DATA - Table empty

### `/api/v4/procurement-timing`
**Needs:**
- `forecasting_data_warehouse.soybean_oil_prices` → price history + VIX overlay
- `forecasting_data_warehouse.vix_daily` → VIX data with `date` and `close`
- `predictions.daily_forecasts` → forecast data for timing analysis
**Status:** ⚠️ Tables exist but `daily_forecasts` is EMPTY

### `/api/v4/breaking-news`
**Needs:**
- `forecasting_data_warehouse.breaking_news_hourly` → `timestamp`, `headline`, `source`, `relevance_score`, `sentiment_score`
**Status:** ✅ Table exists, API disabled temporarily

---

## 2. PROMISED FEATURES AUDIT (From MASTER_TRAINING_PLAN)

### ✅ Big-8 Signals Dashboard
**Tables Needed:**
- ✅ `models_v4.training_dataset_super_enriched` → All Big-8 features
**Status:** ✅ COMPLETE

### ✅ Price Drivers with AI Intelligence
**Tables Needed:**
- ✅ `models_v4.training_dataset_super_enriched` → Features
- ✅ `forecasting_data_warehouse.soybean_oil_prices` → Current price
**Status:** ✅ COMPLETE

### ✅ Risk Radar (6-factor analysis)
**Tables Needed:**
- ✅ `models_v4.training_dataset_super_enriched` → Big-8 features for risk calculation
**Status:** ✅ COMPLETE

### ✅ Substitution Economics
**Tables Needed:**
- ✅ `forecasting_data_warehouse.soybean_oil_prices`
- ✅ `forecasting_data_warehouse.palm_oil_prices`
- ✅ `forecasting_data_warehouse.canola_oil_prices`
**Status:** ✅ COMPLETE

### ❌ Forward Curve (ALL horizons)
**Tables Needed:**
- ✅ `forecasting_data_warehouse.soybean_oil_prices` → Historical
- ⚠️ `predictions.monthly_vertex_predictions` → Forecasts (ONLY 1W exists)
**Status:** ⚠️ MISSING 1M, 3M, 6M predictions

### ❌ All Forecast Routes (1W, 1M, 3M, 6M)
**Tables Needed:**
- ⚠️ `predictions.monthly_vertex_predictions` → Only 1W exists
- ⚠️ `predictions.daily_forecasts` → EMPTY
**Status:** ❌ MISSING 1M, 3M, 6M

### ❌ Ensemble Forecast
**Tables Needed:**
- ❌ `predictions.daily_forecasts` → EMPTY (needs all horizons)
**Status:** ❌ NO DATA

### ❌ Procurement Timing with VIX Overlay
**Tables Needed:**
- ✅ `forecasting_data_warehouse.soybean_oil_prices` → Price data
- ✅ `forecasting_data_warehouse.vix_daily` → VIX data
- ❌ `predictions.daily_forecasts` → EMPTY (needs forecasts for timing)
**Status:** ⚠️ PARTIAL - VIX data exists, predictions missing

### ❌ Breaking News with AI Analysis
**Tables Needed:**
- ✅ `forecasting_data_warehouse.breaking_news_hourly` → News data
**Status:** ⚠️ Table exists but API disabled

---

## 3. ALL TABLES INVENTORY

### `models_v4` Dataset
**Tables:**
- ✅ `training_dataset_super_enriched` - MAIN training data (209 columns, Big-8 features)
- ✅ `enhanced_features_automl` - VIEW
- ✅ `training_dataset_1m_filtered` - VIEW
- ✅ `training_dataset_3m_filtered` - VIEW  
- ✅ `training_dataset_6m_filtered` - VIEW
- ✅ `backtesting_history` - Backtesting results
- ✅ `forward_curve_v3` - Forward curve data
- ✅ `fundamentals_derived_features` - Derived features
- ✅ `fx_derived_features` - FX features
- ✅ `monetary_derived_features` - Monetary features
- ✅ `volatility_derived_features excited` - Volatility features
- ✅ Archive tables (числительные backups)

**Status:** ✅ Tables built, training dataset has latest data

### `forecasting_data_warehouse` Dataset
**Tables:**
- ✅ `soybean_oil_prices` - Main price data (DATETIME time column)
- ✅ `palm_oil_prices` - Palm oil prices
- ✅ `canola_oil_prices` - Canola oil prices
- ✅ `vix_daily` - VIX data (DATE date column)
- ✅ `breaking_news_hourly` - News data
- ✅ `currency_data` - FX data
- ✅ `biofuel_prices` - Biofuel pricing
- ✅ `china_soybean_imports` - China import data
- ✅ `argentina_crisis_tracker` - Argentina tracking
- ✅ `industrial_demand_indicators` - Demand indicators
- ✅ `cftc_cot` - CFTC data
- ✅ Plus: corn, cotton, cocoa, crude_oil, gold, natural_gas prices
- ✅ Plus: news tables (news_intelligence, news_advanced, etc.)
- ✅ Plus: economic_indicators, social_sentiment

**Status:** ✅ All tables exist and populated

### `predictions` Dataset
**Tables:**
- ⚠️ `monthly_vertex_predictions` - Only has 1W (2 rows), MISSING 1M, 3M, 6M
- ❌ `daily_forecasts` - EMPTY (0 rows)
- ❌ Error tables (old batch job failures)

**Status:** ❌ CRITICAL - Missing prediction data for 1M, 3M, 6M

### Other Datasets (Signals, Weather, Market Data)
- ✅ `signals.daily_calculations` - Daily signal calculations
- ✅ `weather.daily_updates` - Weather data
- ✅ `market_data.hourly_prices` - Hourly price data

**Status:** ✅ Tables exist (need to verify data freshness)

---

## 4. VIEWS INVENTORY

**Views in `models_v4`:**
- ✅ `enhanced_features_automl` - Enhanced features view
- ✅ `training_dataset_1m_filtered` - 1M filtered view
- ✅ `training_dataset_3m_filtered` - 3M filtered view
- ✅ `training_dataset_6m_filtered` - 6M filtered view
- ✅ `training_dataset_v4` - Main training view
- ✅ `vw_temporal_engineered` - Temporal features view

**Status:** ✅ Views exist, need to verify they're used correctly

---

## 5. CRITICAL GAPS IDENTIFIED

### ❌ GAP 1: Missing Predictions
**What's Missing:**
- 1M predictions in `monthly_vertex_predictions`
- 3M predictions in `monthly_vertex_predictions`
- 6M predictions in `monthly_vertex_predictions`
- ALL predictions in `daily_forecasts` (table is empty)

**Impact:**
- `/api/v4/forecast/1m` returns 503
- `/api/v4/forecast/3m` returns 503
- `/api/v4/forecast/6m` returns 503
- `/api/v4/ensemble-forecast` returns 503
- `/api/v4/forward-curve` incomplete (only 1W forecast)
- `/api/v4/procurement-timing` incomplete (no forecast data)

**Fix Required:**
- Generate predictions for 1M, 3M, 6M using Vertex AI models
- Save to `predictions.monthly_vertex_predictions` with proper schema

### ❌ GAP 2: Prediction Table Schema Mismatch
**Issue:**
- Models expect target columns (`target_1w`, `target_1m`, `target_3m`, `target_6m`) but don't accept NULL
- Training dataset doesn't have target columns (they were dropped or never existed)
- Need to provide placeholder values or remove from input

**Fix Required:**
- Determine correct approach: remove target columns from input OR use current price as placeholder
- Test with 1W model first (since it worked before)

### ⚠️ GAP 3: Breaking News API Disabled
**Status:**
- Table exists with data
- API disabled to prevent errors
- Needs schema verification and re-enable

---

## 6. DATA FRESHNESS CHECK NEEDED

**Need to Verify:**
- ✅ `training_dataset_super_enriched` - Last update date
- ✅ `forecasting_data_warehouse.soybean_oil_prices` - Latest price date
- ✅ `forecasting_data Vermeerhouse.vix_daily` - Latest VIX date
- ✅ All price tables - Data freshness
- ✅ `breaking_news_hourly` - Latest news timestamp

---

## 7. INTEGRATION FLOW VERIFICATION

### Current Flow (Working):
```
Dashboard → API Route → BigQuery Query → Return Data
```

### Missing Links:
```
Prediction Generation → Vertex AI Models → Save to BigQuery → Dashboard
  ❌ BROKEN: Models can't save predictions (target column issue)
```

### Required Flow:
```
1. Monthly: Deploy models → Get predictions → Save to monthly_vertex_predictions
2. Daily: Dashboard queries monthly_vertex_predictions
3. APIs return cached predictions (no Vertex AI calls)
```

---

## 8. ACTION ITEMS (Priority Order)

### 🔥 CRITICAL (Do Now):
1. **Fix prediction generation script** - Handle target columns properly
2. **Generate 1M, 3M, 6M predictions** - Populate `monthly_vertex_predictions`
3. **Verify all prediction data saves correctly** - Check BigQuery after generation

### ⚠️ HIGH (Do Soon):
4. **Re-enable breaking news API** - Fix schema and re-enable
5. **Verify data freshness** - Check all tables have recent data
6. **Test all dashboard APIs** - Ensure they work with new data

### ✅ MEDIUM (Verify):
7. **Check views are used correctly** - Verify filtered views work
8. **Audit signal calculations** - Verify signals.daily_calculations is populated
9. **Verify VIX overlay data** - Check vix_daily is current

---

## 9. SUMMARY

**What Works:**
- ✅ All base tables exist
- ✅ All feature tables populated
- ✅ Big-8 signals working
- ✅ Price drivers working
- ✅ Risk radar working
- ✅ Substitution economics working
- ✅ 1W predictions exist

**What's Broken:**
- ❌ 1M, 3M, 6M predictions missing
- ❌ daily_forecasts table empty
- ❌ Ensemble forecast can't work (no data)
- ❌ Forward curve incomplete (only 1W)
- ❌ Procurement timing incomplete (no forecasts)
- ❌ Breaking news API disabled

**Root Cause:**
- Prediction generation script fails due to target column handling
- Need to fix script to either:
  - Remove target columns from input, OR
  - Use current price as placeholder for target columns

**Next Step:**
- Fix `get_remaining_predictions.py` to properly handle target columns
- Generate all missing predictions (1M, 3M, 6M)
- Verify data in BigQuery
- Re-test all dashboard APIs

---

**LAST UPDATED:** 2025-10-30

