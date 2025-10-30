# UNDERSTANDING THE FULL CONTEXT - October 30, 2025

## 🎯 **TODAY'S GOAL:**
Deliver fully functional dashboard with ALL promised features - advanced visualizations, AI intelligence layer, fresh data feeds

## 📊 **WHAT WE HAVE:**

### ✅ **WORKING:**
1. **Vertex AI Models:** 4 models trained, 1W complete (2.02% MAPE), 3M/6M trained
2. **Architecture:** Serverless endpoint trickery strategy decided ($0.60/month vs $576/month)
3. **Dashboard Structure:** Layout, sidebar, headers, basic components exist
4. **Hourly Price Feeds:** Live data (latest: 2025-10-30T14:05)

### ❌ **FAILING FOR DAYS:**
1. **17-day stale Big-8 table** - training_dataset_super_enriched last updated Oct 13
2. **Empty predictions table** - predictions.daily_forecasts has 0 rows
3. **Breaking news** - table exists but wrong schema/API using wrong table
4. **Build errors** - SQL escaping, TypeScript errors, location mismatches
5. **Deployment failures** - Last 3 deployments failed, 7-hour-old code live

---

## 🧩 **THE SCHEMA REALITY:**

### **training_dataset_super_enriched:**
**ACTUAL COLUMNS (from audit):**
- `date`
- `feature_vix_stress`
- `feature_harvest_pace`
- `feature_china_relations`
- `feature_tariff_threat`
- `feature_geopolitical_volatility`
- `feature_biofuel_cascade`
- `feature_hidden_correlation`
- `feature_biofuel_ethanol`
- `big8_composite_score`
- `market_regime`

**PLAN SAYS:** 209 features total
**REALITY:** Only showing 11 columns (likely this is a filtered view OR the table was simplified)

### **What APIs Are Trying to Query (WRONG):**
- ❌ `zl_price_current` - doesn't exist
- ❌ `china_soybean_imports_mt` - doesn't exist
- ❌ `argentina_export_tax` - doesn't exist  
- ❌ `industrial_demand_index` - doesn't exist
- ❌ `palm_price` - doesn't exist
- ❌ `zl_crude_corr_30d` - doesn't exist

**THESE COLUMNS ARE IN OTHER TABLES:**
- ✅ Current price = `forecasting_data_warehouse.soybean_oil_prices.close`
- ✅ China imports = likely in `forecasting_data_warehouse.china_soybean_imports`
- ✅ Argentina tax = likely in `forecasting_data_warehouse.argentina_crisis_tracker`

---

## 🎯 **WHAT THE PLAN SAYS WE NEED:**

### **Price Drivers (Section 2671-2704):**
- Feature importance from Vertex AI models (SHAP values)
- Top drivers like `corr_price` (65%), `target_1w`, `corr_zl_palm_90d`, `crush_margin_30d_ma`
- Translate to dollar impacts: "+$0.12/cwt"
- Plain English: "Price Momentum: Last week's close continuing trend"

**KEY INSIGHT:** Price drivers should come from MODEL FEATURE IMPORTANCE, not raw table columns!

### **Breaking News:**
- Table: `forecasting_data_warehouse.breaking_news_hourly` ✅ EXISTS
- Schema: `timestamp`, `headline`, `summary`, `sentiment_score`, `relevance_score`, `source`, `url`
- But API was querying wrong table (`intelligence.breaking_news` doesn't exist)

### **Predictions:**
- Table: `predictions.daily_forecasts` ✅ EXISTS but EMPTY (0 rows)
- Schema: `horizon`, `predicted_price`, `confidence_lower`, `confidence_upper`, `mape`, `model_id`, `model_name`, `prediction_date`, `target_date`, `created_at`
- Needs to be populated by endpoint trickery script

---

## 🚨 **ROOT CAUSES OF FAILURES:**

1. **Schema Mism Sitting:** Code queries columns that don't exist in training_dataset_super_enriched
2. **Location Mismatch:** BigQuery client using `us-central1`, datasets in `US` multi-region
3. **Wrong Table References:** Breaking news API using non-existent `intelligence.breaking_news`
4. **Incomplete Data:** Predictions table empty, Big-8 table 17 days stale
5. **TypeScript Errors:** Missing type annotations causing build failures
6. **SQL Escaping:** Backticks not properly escaped in template literals

---

## ✅ **WHAT'S BEEN FIXED SO FAR:**
1. ✅ Breaking news API - switched to correct table
2. ✅ BigQuery location - changed to 'US' multi-region
3. ✅ SQL backtick escaping - fixed in risk-radar, 3m route
4. ✅ TypeScript errors - fixed substitution-economics
5. ✅ Build successful - latest deployment ready
6. ✅ Package dependencies - swr installed

---

## 🎯 **WHAT STILL NEEDS FIXING:**

### **CRITICAL (Blocking Dashboard):**
1. ❌ **Price Drivers API** - Completely wrong query, needs to use model feature importance OR join to actual tables
2. ❌ **Predictions Table** - Empty, needs to run endpoint trickery script
3. ❌ **Big-8 Table** - Stale, needs feature refresh pipeline run
4. ⚠️ **Location Issue** - Fixed in code but needs deployment to take effect

### **MEDIUM (Features Broken):**
5. ⚠️ **Substitution Economics** - May have wrong column references
6. ⚠️ **Risk Radar** - Needs column verification
7. ⚠️ **Forward Curve** - Needs predictions data to work
8. ⚠️ **Procurement Timing** - Needs predictions + price data

### **LOW (Nice to Have):**
9. ⚠️ **Ensemble Forecast** - Needs predictions to work
10. ⚠️ **Other forecast routes** - May have location issues

---

## 🎯 **THE CORRECT APPROACH:**

### **For Price Drivers:**
1. Get current price from `soybean_oil_prices.close` (latest row)
2. Get Big-8 feature values from `training_dataset_super_enriched` (11 columns that exist)
3. Get feature importance from MODEL EXPLANATIONS or calculate from prediction variance
4. OR: Use the planned SHAP calculation script (Phase 3.2 in scaffold)

### **For Predictions:**
1. Run `automl/quick_endpoint_predictions.py` to populate `predictions.daily_forecasts`
2. Or wait for monthly cron job on 1st of month

### **For Feature Refresh:**
1. Run `scripts/refresh_features_pipeline.py` to update Big-8 table
2. This should update `training_dataset_super_enriched` to today

---

## 📝 **NEXT STEPS (In Priority Order):**

1. **Fix Price Drivers API** - Remove non-existent columns, use actual data sources
2. **Verify location fix works** - Test after deployment
3. **Run feature refresh** - Update stale Big-8 table
4. **Verify all table schemas** - Make sure column references are correct
5. **Test all APIs** - Ensure they work with real data
6. **Deploy and verify** - Make sure everything is live

---

## 🧠 **KEY INSIGHT:**

The training_dataset_super_enriched table is the **AGGREGATED FEATURE TABLE** with Big-8 signals, not the raw source data. The raw data (prices, imports, etc.) is in other tables. APIs need to either:
- Use only the 11 feature columns that exist, OR
- Join to source tables for raw values

The "209 features" likely refers to the TOTAL FEATURES used in training, but the aggregated table only stores the most important ones (Big-8).

