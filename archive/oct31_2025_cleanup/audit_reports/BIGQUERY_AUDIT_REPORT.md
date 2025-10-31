# BigQuery Audit Report - October 30, 2025

## 🔍 **COMPLETE AUDIT OF ALL API ROUTES**

### ✅ **DATASETS THAT EXIST:**
- `cbi-v14.forecasting_data_warehouse` ✅
- `cbi-v14.models_v4` ✅
- `cbi-v14.predictions` ✅
- `cbi-v14.intelligence` ❌ **DOES NOT EXIST**

### ✅ **TABLES THAT EXIST:**
- `forecasting_data_warehouse.breaking_news_hourly` ✅
- `forecasting_data_warehouse.soybean_oil_prices` ✅
- `models_v4.training_dataset_super_enriched` ✅
- `predictions.daily_forecasts` ✅
- `predictions.monthly_vertex_predictions` ✅

---

## 🚨 **CRITICAL ISSUES FOUND:**

### **1. BREAKING NEWS API** (`/api/v4/breaking-news`)
**STATUS:** ⚠️ FIXED BUT NEEDS VERIFICATION

**Issue:** 
- Was trying to query `cbi-v14.intelligence.breaking_news` (doesn't exist)
- **FIXED:** Changed to `forecasting_data_warehouse.breaking_news_hourly`

**Schema Used:**
- `timestamp` ✅
- `headline` ✅
- `source` ✅
- `relevance_score` ✅ (used as `impact_score`)
- `sentiment_score` ✅ (used as `sentiment_tone`)

**Status:** ✅ FIXED - Need to test

---

### **2. PRICE DRIVERS API** (`/api/v4/price-drivers`)
**STATUS:** ❌ **CRITICAL - MULTIPLE MISSING COLUMNS**

**Querying from:** `models_v4.training_dataset_super_enriched`

**Columns it's trying to use:**
- ❌ `zl_price_current` - **DOES NOT EXIST**
- ❌ `china_soybean_imports_mt` - **DOES NOT EXIST**
- ❌ `argentina_export_tax` - **DOES NOT EXIST**
- ❌ `industrial_demand_index` - **DOES NOT EXIST**
- ❌ `palm_price` - **DOES NOT EXIST**
- ❌ `zl_crude_corr_30d` - **DOES NOT EXIST**
- ❌ `zl_palm_corr_30d` - **DOES NOT EXIST**
- ❌ `zl_vix_corr_30d` - **DOES NOT EXIST**

**Columns that DO exist in `training_dataset_super_enriched`:**
- ✅ `date`
- ✅ `feature_vix_stress`
- ✅ `feature_harvest_pace`
- ✅ `feature_china_relations`
- ✅ `feature_tariff_threat`
- ✅ `feature_geopolitical_volatility`
- ✅ `feature_biofuel_cascade`
- ✅ `feature_hidden_correlation`
- ✅ `feature_biofuel_ethanol`
- ✅ `big8_composite_score`
- ✅ `market_regime`

**FIX REQUIRED:** Completely rewrite query to use only existing columns

---

### **3. DATASET LOCATION MISMATCH**
**STATUS:** ⚠️ FIXED BUT NEEDS TESTING

**Issue:**
- BigQuery client was defaulting to `us-central1`
- Datasets are in `US` multi-region
- **FIXED:** Added `location: 'US'` to BigQuery client options

**File:** `dashboard-nextjs/src/lib/bigquery.ts`
**Status:** ✅ FIXED

---

### **4. PREDICTIONS DATASET**
**STATUS:** ✅ EXISTS

**Tables:**
- `predictions.daily_forecasts` ✅
  - Columns: horizon, predicted_price, confidence_lower, confidence_upper, mape, model_id, model_name, prediction_date, target_date, created_at
- `predictions.monthly_vertex_predictions` ✅

**Issue:** Some routes query this but get "dataset not found in location us-central1"
**Status:** Should be fixed by location change above

---

### **5. SOYBEAN OIL PRICES TABLE**
**STATUS:** ✅ EXISTS

**Table:** `forecasting_data_warehouse.soybean_oil_prices`
**Columns:**
- ✅ `time`
- ✅ `symbol`
- ✅ `open`
- ✅ `high`
- ✅ `low`
- ✅ `close` ✅ **This is the price column!**
- ✅ `volume`
- ✅ `source_name`
- ✅ `confidence_score`
- ✅ `ingest_timestamp_utc`

**Note:** Price drivers API might need `close` from here instead of non-existent `zl_price_current`

---

## 📋 **SUMMARY OF ALL API ROUTES:**

| API Route | Table Used | Status | Issues |
|-----------|-----------|--------|--------|
| `/api/v4/breaking-news` | `breaking_news_hourly` | ✅ FIXED | None |
| `/api/v4/big-eight-signals` | `training_dataset_super_enriched` | ✅ WORKING | None |
| `/api/v4/price-drivers` | `training_dataset_super_enriched` | ❌ BROKEN | 8 missing columns |
| `/api/v4/ensemble-forecast` | `daily_forecasts` | ⚠️ MAY NEED DATA | Needs predictions |
| `/api/v4/procurement-timing` | `daily_forecasts`, `soybean_oil_prices` | ⚠️ LOCATION ISSUE | May be fixed |
| `/api/v4/risk-radar` | `training_dataset_super_enriched` | ⚠️ NEEDS VERIFICATION | Check columns |
| `/api/v4/substitution-economics` | `soybean_oil_prices`, `training_dataset_super_enriched` | ⚠️ NEEDS VERIFICATION | Check columns |
| `/api/v4/forward-curve` | `soybean_oil_prices`, `monthly_vertex_predictions` | ⚠️ NEEDS VERIFICATION | Check columns |
| `/api/v4/forecast/1w` | `monthly_vertex_predictions` | ⚠️ NEEDS VERIFICATION | Check columns |
| `/api/v4/forecast/1m` | `daily_forecasts` | ⚠️ LOCATION ISSUE | May be fixed |
| `/api/v4/forecast/3m` | `daily_forecasts` | ⚠️ LOCATION ISSUE | May be fixed |
| `/api/v4/forecast/6m` | `daily_forecasts` | ⚠️ LOCATION ISSUE | May be fixed |

---

## 🎯 **IMMEDIATE FIXES REQUIRED:**

1. **CRITICAL:** Fix `/api/v4/price-drivers` - Remove all non-existent column references
2. **HIGH:** Verify all routes using `predictions` dataset work after location fix
3. **MEDIUM:** Verify `risk-radar`, `substitution-economics`, `forward-curve` column references
4. **LOW:** Test breaking news API with actual data

---

## 📝 **NEXT STEPS:**

1. Fix price-drivers route to use only existing columns from `training_dataset_super_enriched`
2. Get current price from `soybean_oil_prices.close` instead of non-existent column
3. Test all APIs after location fix deployment
4. Verify all column references match actual schemas

