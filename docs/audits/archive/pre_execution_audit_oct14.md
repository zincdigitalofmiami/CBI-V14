# Pre-Execution Audit Report
**Date:** October 14, 2025  
**Status:** Complete  
**Purpose:** Safety audit before Ultimate Signal Architecture build

---

## AUDIT FINDINGS

### 1. Dataset Inventory

**EXISTING DATASETS:**
- ✅ `forecasting_data_warehouse` - 50 tables, 12 views
- ✅ `curated` - 19 views
- ✅ `models` - 2 views, 4 tables
- ✅ `staging` - 7 tables

**MISSING DATASETS (MUST CREATE):**
- ❌ `signals` - Does not exist
- ❌ `neural` - Does not exist
- ❌ `api` - Does not exist
- ❌ `performance` - Does not exist

**ACTION:** Create these 4 datasets in Phase 2A before building views.

---

### 2. Current View Count

**CURATED:** 19 views
- vw_client_insights_daily
- vw_client_multi_horizon_forecast
- vw_commodity_prices_daily
- vw_crush_margins_daily
- vw_dashboard_commodity_prices
- vw_dashboard_fundamentals
- vw_dashboard_weather_intelligence
- vw_economic_daily
- vw_fed_rates_realtime
- vw_multi_source_intelligence_summary
- vw_news_intel_daily
- vw_palm_soy_spread_daily
- vw_social_intelligence
- vw_soybean_oil_features_daily
- vw_soybean_oil_quote
- vw_treasury_daily
- vw_volatility_daily
- vw_weather_daily
- vw_weather_global_daily

**FORECASTING_DATA_WAREHOUSE:** 12 views
- vw_brazil_precip_daily
- vw_brazil_weather_summary
- vw_dashboard_brazil_weather
- vw_dashboard_trump_intel
- vw_fed_rates_realtime
- vw_ice_trump_daily
- vw_multi_source_intelligence_summary
- vw_news_intel_daily
- vw_treasury_daily
- vw_trump_effect_breakdown
- vw_trump_effect_categories
- vw_trump_intelligence_dashboard

**MODELS:** 2 views
- vw_master_feature_set_v1
- vw_master_feature_set_v2

---

### 3. Critical Table Row Counts

| Table | Rows | Status | Priority |
|---|---|---|---|
| soybean_oil_prices | 531 | ✅ Good | - |
| economic_indicators | 6,757 | ✅ Excellent | - |
| trump_policy_intelligence | 208 | ✅ Good | - |
| biofuel_production | 24 | ⚠️ Minimal | Expand in Phase 1 |
| biofuel_policy | 0 | ❌ EMPTY | **CRITICAL - Phase 1A** |

---

### 4. Duplicate Views (MUST RESOLVE)

**DUPLICATES FOUND:**
- `vw_fed_rates_realtime` - Exists in BOTH curated AND forecasting_data_warehouse
- `vw_multi_source_intelligence_summary` - Exists in BOTH curated AND forecasting_data_warehouse
- `vw_news_intel_daily` - Exists in BOTH curated AND forecasting_data_warehouse  
- `vw_treasury_daily` - Exists in BOTH curated AND forecasting_data_warehouse

**ACTION:** Keep curated versions (they're pass-throughs), delete forecasting_data_warehouse versions in Phase 2B.

---

### 5. Redundant Views (MUST DELETE)

**BRAZIL WEATHER (3 redundant views):**
- vw_brazil_precip_daily
- vw_brazil_weather_summary
- vw_dashboard_brazil_weather

**ACTION:** Delete all 3 after creating consolidated `curated.vw_weather_br_daily` in Phase 2B.

**TRUMP INTELLIGENCE (4 redundant views):**
- vw_trump_effect_breakdown
- vw_trump_effect_categories
- vw_trump_intelligence_dashboard
- vw_ice_trump_daily

**ACTION:** Delete all 4 after dependency check. Replace with 2 new views in Phase 2.

---

### 6. Naming Compliance Issues

**AMBIGUOUS NAMES (Need Renaming per Standard):**
- `vw_multi_source_intelligence_summary` → Should be `vw_econ_aggregates_daily`
- `vw_news_intel_daily` → Should be `vw_news_commodity_daily`
- `vw_social_intelligence` → Should be `vw_sentiment_social_multi_daily`
- `vw_client_insights_daily` → Should be `vw_dashboard_client_display_daily` (move to api dataset)

**ACTION:** Create new standard-named views, update FastAPI, then delete old names.

---

### 7. Critical Data Gaps

**EMPTY STAGING TABLES:**
- `staging.biofuel_policy`: 0 rows (BLOCKER for biofuel analysis)
- `staging.usda_export_sales`: 5 rows (insufficient for China trade intelligence)
- `staging.cftc_cot`: Does not exist yet (BLOCKER for positioning analysis)

**MISSING DATA:**
- CFTC positioning data
- EPA biofuel mandates
- Multi-source social sentiment (only 22 Reddit rows currently)
- Institutional analyst forecasts
- Congressional/lobbying intelligence

**ACTION:** Phase 1 fills all these gaps before building signal aggregates.

---

### 8. Existing Assets (Can Leverage)

**WORKING DATA:**
- ✅ 531 soybean oil prices
- ✅ 6,757 economic indicators (includes CONAB Brazil harvest data)
- ✅ 208 Trump policy intelligence rows
- ✅ Weather data for BR/AR/US regions
- ✅ Crush margins view operational
- ✅ Palm-soy spread view operational

**WORKING MODELS:**
- ✅ `models.zl_forecast_baseline_v1` (30 ARIMA forecasts)
- ✅ `models.zl_price_training_base` (historical data)
- ✅ `models.zl_timesfm_training_v1` (102 training rows with features)

---

## AUDIT SUMMARY

**READY TO PROCEED:** ✅ Yes  
**BLOCKERS:** None (all gaps fillable in Phase 1)  
**RISK LEVEL:** Low (clear dependencies mapped, datasets identified)  
**ESTIMATED TIMELINE:** 4 days as planned  

**NEXT STEP:** Create missing datasets (signals, neural, api, performance), then begin Phase 1 data collection.

---

**Audit completed successfully. Proceeding to execution.**



