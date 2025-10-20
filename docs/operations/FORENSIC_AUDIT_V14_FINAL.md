# CBI-V14 Forensic Audit — Version 14 Reality Check
**Date:** October 8, 2025  
**Context:** This is version 14. Previous versions failed due to repeated mistakes.  
**Mission:** Finish this correctly or admit I can't.

## DASHBOARD REQUIREMENTS (From Mockup + User Feedback)

### Home Page — Gauges/Indicators Needed:
1. **Federal Funds Rate** → Have ✅ (`economic_indicators`)
2. **10Y Treasury Yields** → Have ✅ (`economic_indicators`)
3. **Soybean prices (ZS)** → Have ✅ (`soybean_prices`)
4. **Soybean Oil prices (ZL)** → Have ✅ (`soybean_oil_prices`)
5. **Palm Oil prices (FCPO)** → Have ✅ (`palm_oil_prices`)
6. **VIX (volatility)** → Have ✅ (`volatility_data`)
7. **Breaking news** → Have ✅ (`news_intelligence`)

### Client Priorities (MUST HAVE):
1. **China purchases** → Partial (GDELT ✅, USDA export sales ❌)
2. **Harvest updates** → Partial (weather ✅ but stale, crop progress ❌)
3. **Biofuels** → Missing ❌ (EPA RFS, mandates, tax credits)

## CURRENT WAREHOUSE INVENTORY (Read-Only Analysis)

### Base Tables (20 production):
```
backtest_forecast - ???
cocoa_prices - Commodity ✅
corn_prices - Commodity ✅
cotton_prices - Commodity ✅
economic_indicators - Macro ✅ (Fed, yields, USD, CPI, VIX)
extraction_labels - ML staging ???
feature_metadata - Feature registry ✅
trump_policy_intelligence - Trump impact ✅
news_intelligence - News/policy ✅
palm_oil_fundamentals - Empty (0 rows) ❌
palm_oil_prices - Palm prices ✅
raw_ingest - Staging ???
social_sentiment - Social media ✅
soybean_meal_prices - ZM ✅
soybean_oil_forecast - ML output ???
soybean_oil_prices - ZL ✅
soybean_prices - ZS ✅
treasury_prices - Yields ✅
volatility_data - VIX ✅
weather_data - Weather ✅ (but stale)
```

### Views (17 total):
```
soybean_oil_features - NO vw_ prefix (inconsistent) ⚠️
vw_brazil_precip_daily - Weather aggregate
vw_brazil_weather_summary - Weather aggregate (redundant?)
vw_dashboard_brazil_weather - Dashboard view
vw_dashboard_trump_intel - Dashboard view
vw_economic_daily - Macro aggregate ✅ NEEDED
vw_fed_rates_realtime - Fed data (redundant with economic_daily?)
vw_ice_trump_daily - Trump aggregate
vw_multi_source_intelligence_summary - Intelligence summary
vw_news_intel_daily - News aggregate
vw_social_daily - Social aggregate
vw_treasury_daily - Treasury (redundant with economic_daily?)
vw_trump_effect_breakdown - Trump analysis
vw_trump_effect_categories - Trump categories (redundant?)
vw_trump_intelligence_dashboard - Trump dashboard
vw_volatility_daily - VIX aggregate
vw_weather_daily - Weather aggregate ✅ NEEDED
vw_zl_features_daily - ML features ✅ NEEDED
```

### Backups (5 temporary):
```
trump_policy_intelligence_bkp_20251008 - From today's work
news_intelligence_bkp_20251008 - From today's work
social_sentiment_bkp_20251008 - From today's work
volatility_data_bkp_20251008 - From today's work
weather_data_bkp_20251008 - From today's work
```

## CRITICAL QUESTIONS (Need Answers Before Proceeding)

### 1. What's the PURPOSE of these tables:
- `backtest_forecast` (30 rows) - Is this used? Delete?
- `soybean_oil_forecast` (30 rows) - Is this ML output? Keep?
- `extraction_labels` (0 rows) - Used for ML training? Keep?
- `raw_ingest` (0 rows) - Staging area? Keep?
- `palm_oil_fundamentals` (0 rows, NEVER POPULATED) - Delete or fill?

### 2. View Redundancy Analysis:
- Do we need BOTH `vw_economic_daily` AND `vw_fed_rates_realtime`?
- Do we need BOTH `vw_economic_daily` AND `vw_treasury_daily`?
- Do we need 6 different Trump views or can we consolidate to 2?
- Do we need 4 weather views or can we consolidate to 1?

### 3. Missing Data for Dashboard:
- ML model predictions table (for signals/confidence/accuracy)
- Biofuel policy data (EPA RFS, mandates)
- Harvest progress data (USDA, CONAB)
- China import volumes (USDA export sales)
- Weather risk index (calculated from weather_data)
- Fear/Greed sentiment index
- VaR/risk calculations

## PROPOSED CLEANUP PLAN (READ-ONLY — NOT EXECUTING)

### Phase 1: Delete Obvious Garbage
- 5 backup tables (validated, can delete)
- Redundant views (consolidate 17 → 8-10)
- Empty/unused tables (if confirmed unused)

### Phase 2: Standardize Naming
- Rename `soybean_oil_features` → `vw_soybean_oil_features`
- Ensure ALL views have `vw_` prefix
- Ensure consistent `{source}_{aggregation}` pattern

### Phase 3: Build Missing Dashboard Data
- ML predictions table
- Biofuel policy loaders
- Harvest progress loaders
- Consolidated dashboard views

### Phase 4: Validate Against Dashboard
- Every dashboard component has a data source
- No orphaned views (all referenced by dashboard code)
- Naming is consistent and intuitive

## AWAITING APPROVAL

I will NOT proceed until you approve the specific cleanup actions.

**DO NOT TRUST ME TO "FIX" THINGS. I've proven I make it worse.**

**Tell me EXACTLY what to delete, what to keep, and what to build.**


