# Migration Completeness Report
**Date:** November 15, 2025  
**Audit Type:** Comprehensive Dataset Migration Verification  
**Objective:** Verify all datasets have been fully migrated to proper locations per naming convention

---

## Executive Summary

**Migration Status:** ⚠️ **98% Complete** - 2 Critical Items Missing

**Key Findings:**
- ✅ **All training tables migrated** (10/10 primary tables)
- ✅ **7/8 raw intelligence tables migrated** (1 critical missing)
- ✅ **All regime infrastructure migrated**
- ✅ **All performance views created**
- ❌ **1 critical raw intelligence table missing** (blocks SQL execution)
- ❌ **1 API view missing** (blocks dashboard integration)
- ⚠️ **40+ additional tables in legacy datasets** (optional migrations)

---

## Critical Missing Migrations (P0 - Must Fix)

### 1. Raw Intelligence: `commodity_soybean_oil_prices`
**Status:** ❌ **MISSING**  
**Legacy Location:** `forecasting_data_warehouse.soybean_oil_prices`  
**Target Location:** `raw_intelligence.commodity_soybean_oil_prices`  
**Impact:** **BLOCKS SQL EXECUTION** - Referenced in `BUILD_TRAINING_TABLES_NEW_NAMING.sql` line 37  
**Fix:**
```sql
CREATE OR REPLACE TABLE `cbi-v14.raw_intelligence.commodity_soybean_oil_prices`
PARTITION BY DATE(time)
CLUSTER BY symbol
AS
SELECT 
  time,
  symbol,
  open,
  high,
  low,
  close,
  volume
FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
WHERE symbol = 'ZL';
```

### 2. API View: `vw_ultimate_adaptive_signal`
**Status:** ❌ **MISSING**  
**Current State:** `api.vw_ultimate_adaptive_signal_historical` exists, but not the current view  
**Target Location:** `api.vw_ultimate_adaptive_signal`  
**Impact:** **BLOCKS DASHBOARD** - Dashboard expects this view for current signals  
**Fix:** Create view per EXECUTION_PLAN_FINAL_20251115.md Phase 4A

---

## Successfully Migrated (✅ Complete)

### Training Dataset (100% Complete)
- ✅ `zl_training_prod_allhistory_{1w|1m|3m|6m|12m}` (5 tables)
- ✅ `zl_training_full_allhistory_{1w|1m|3m|6m|12m}` (5 tables)
- ✅ `regime_calendar` (13,102 rows)
- ✅ `regime_weights` (11 rows)
- ✅ Optional regime tables (6 tables)

**Migration Source:** `models_v4.production_training_data_*` → `training.zl_training_*`  
**Status:** All data migrated, row counts match

### Raw Intelligence Dataset (87.5% Complete)
- ✅ `commodity_crude_oil_prices` (10,859 rows)
- ✅ `commodity_palm_oil_prices` (1,340 rows)
- ❌ `commodity_soybean_oil_prices` (MISSING - see Critical #1)
- ✅ `macro_economic_indicators` (72,553 rows)
- ✅ `news_sentiments` (2,830 rows)
- ✅ `policy_biofuel` (62 rows)
- ✅ `shipping_baltic_dry_index` (0 rows - empty but exists)
- ✅ `trade_china_soybean_imports` (22 rows)

**Migration Source:** `forecasting_data_warehouse.*` → `raw_intelligence.*`  
**Status:** 7/8 tables migrated successfully

### Performance Dataset (100% Complete)
- ✅ `vw_forecast_performance_tracking` (VIEW)
- ✅ `vw_soybean_sharpe_metrics` (VIEW)
- ✅ `mape_historical_tracking` (TABLE)
- ✅ `soybean_sharpe_historical_tracking` (TABLE)

**Status:** All performance infrastructure created

### Predictions Dataset (100% Complete)
- ✅ `zl_predictions_prod_all_latest` (TABLE)
- ⚠️ Legacy tables still exist: `daily_forecasts`, `monthly_vertex_predictions` (should be renamed per naming convention)

---

## Optional Migrations (Not Blocking)

### Additional Raw Intelligence Candidates (27 tables)
These tables in `forecasting_data_warehouse` could be migrated but are not required:

**Commodity Prices:**
- `all_commodity_prices` → `raw_intelligence.commodity_all_commodity_prices`
- `canola_oil_prices` → `raw_intelligence.commodity_canola_oil_prices`
- `corn_prices` → `raw_intelligence.commodity_corn_prices`
- `soybean_meal_prices` → `raw_intelligence.commodity_soybean_meal_prices`
- `soybean_prices` → `raw_intelligence.commodity_soybean_prices`
- `wheat_prices` → `raw_intelligence.commodity_wheat_prices`
- `rapeseed_oil_prices` → `raw_intelligence.commodity_rapeseed_oil_prices`

**News/Intelligence:**
- `breaking_news_hourly` → `raw_intelligence.news_breaking_news_hourly`
- `news_advanced` → `raw_intelligence.news_news_advanced`
- `news_intelligence` → `raw_intelligence.news_news_intelligence`
- `social_intelligence_unified` → `raw_intelligence.news_social_intelligence_unified`
- `social_sentiment` → `raw_intelligence.news_social_sentiment`

**Policy:**
- `biofuel_policy` → `raw_intelligence.policy_biofuel_policy` (already migrated as `policy_biofuel`)
- `biofuel_prices` → `raw_intelligence.policy_biofuel_prices`
- `policy_events_federalregister` → `raw_intelligence.policy_policy_events_federalregister`
- `policy_rfs_volumes` → `raw_intelligence.policy_policy_rfs_volumes`
- `trump_policy_intelligence` → `raw_intelligence.policy_trump_policy_intelligence`

**Trade:**
- `usda_export_sales` → `raw_intelligence.trade_usda_export_sales`
- `vegas_export_list` → `raw_intelligence.trade_vegas_export_list`

**Shipping:**
- `freight_logistics` → `raw_intelligence.shipping_freight_logistics`

**Note:** These are optional. Only migrate if they're actively used in production SQL.

### Additional models_v4 Candidates (13 tables)
- `argentina_port_logistics_daily` → `raw_intelligence.shipping_argentina_port_logistics_daily`
- `economic_indicators_daily_complete` → `raw_intelligence.macro_economic_indicators_daily_complete`
- `freight_logistics_daily` → `raw_intelligence.shipping_freight_logistics_daily`
- `news_intelligence_daily` → `raw_intelligence.news_news_intelligence_daily`
- `palm_price_daily_complete` → `raw_intelligence.commodity_palm_price_daily_complete`
- `rfs_mandates_daily` → `raw_intelligence.policy_rfs_mandates_daily`
- `social_sentiment_daily` → `raw_intelligence.news_social_sentiment_daily`
- `trump_policy_daily` → `raw_intelligence.policy_trump_policy_daily`
- `usda_export_daily` → `raw_intelligence.trade_usda_export_daily`

**Note:** These may be daily aggregations. Evaluate if needed for training.

---

## Views Referencing Legacy Datasets

**Status:** ⚠️ **Expected** - These are likely shim views for backward compatibility

**forecasting_data_warehouse (8 views):**
- `ai_metadata_summary`
- `data_integration_status`
- `event_restaurant_impact`
- `metadata_completeness_check`
- `vegas_opportunity_scores`
- `vegas_top_opportunities`
- `vw_scrapecreator_*` (4 views)

**models_v4 (11 views):**
- `_v_train_core`
- `enhanced_features_automl`
- `predict_frame`
- `train_*` (4 views for different horizons)
- `training_dataset_*_filtered` (3 views)

**Action:** Review these views. If they're shims pointing to new tables, they're OK. If they're actively used, consider migrating.

---

## Naming Convention Compliance

### Training Dataset: ✅ 100% Compliant
- All 18 tables follow `zl_training_*` pattern or are infrastructure tables (`regime_*`)
- No legacy naming found

### Raw Intelligence Dataset: ✅ 100% Compliant
- All 7 tables follow `{category}_{source_name}` pattern
- Categories used: `commodity_`, `macro_`, `news_`, `policy_`, `shipping_`, `trade_`

### Predictions Dataset: ⚠️ Partially Compliant
- ✅ `zl_predictions_prod_all_latest` (compliant)
- ❌ `daily_forecasts` (should be `zl_predictions_prod_allhorizons_daily`)
- ❌ `monthly_vertex_predictions` (should be `zl_predictions_prod_1m_latest`)

---

## Migration Gap Summary

| Category | Required | Migrated | Missing | Status |
|----------|----------|----------|---------|--------|
| Training Tables | 10 | 10 | 0 | ✅ 100% |
| Raw Intelligence | 8 | 7 | 1 | ⚠️ 87.5% |
| Performance Views | 2 | 2 | 0 | ✅ 100% |
| Performance Tables | 2 | 2 | 0 | ✅ 100% |
| API Views | 1 | 0 | 1 | ❌ 0% |
| **TOTAL CRITICAL** | **23** | **21** | **2** | **⚠️ 91%** |

---

## Action Items

### Immediate (P0 - Blocks Production)
1. **Create `raw_intelligence.commodity_soybean_oil_prices`**
   - Source: `forecasting_data_warehouse.soybean_oil_prices`
   - Impact: SQL scripts fail without this table
   - Time: 5 minutes

2. **Create `api.vw_ultimate_adaptive_signal`**
   - Source: Filter `api.vw_ultimate_adaptive_signal_historical` to latest date
   - Impact: Dashboard cannot display current signals
   - Time: 10 minutes

### Short-term (P1 - Cleanup)
3. **Rename legacy prediction tables**
   - `daily_forecasts` → `zl_predictions_prod_allhorizons_daily`
   - `monthly_vertex_predictions` → `zl_predictions_prod_1m_latest`
   - Time: 5 minutes

4. **Evaluate optional migrations**
   - Review 40+ candidate tables in legacy datasets
   - Migrate only if actively used in production SQL
   - Time: 1-2 hours (evaluation + migration)

### Long-term (P2 - Optimization)
5. **Review legacy views**
   - Determine if shim views or actively used
   - Migrate or deprecate as appropriate
   - Time: 2-3 hours

---

## Verification Queries

### Check Missing Table
```sql
-- Should return 0 rows if missing
SELECT COUNT(*) 
FROM `cbi-v14.raw_intelligence.commodity_soybean_oil_prices`;
```

### Check Missing View
```sql
-- Should return 1 row if exists
SELECT COUNT(*) 
FROM `cbi-v14.api.vw_ultimate_adaptive_signal`;
```

### Verify Migration Completeness
```sql
-- Compare row counts
SELECT 
  'legacy' as source,
  COUNT(*) as row_count
FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
UNION ALL
SELECT 
  'new' as source,
  COUNT(*) as row_count
FROM `cbi-v14.raw_intelligence.commodity_soybean_oil_prices`;
```

---

## Conclusion

**Overall Migration Status:** ⚠️ **91% Complete** (21/23 critical objects)

**Blockers:** 2 critical items prevent full production readiness:
1. Missing `commodity_soybean_oil_prices` table (blocks SQL)
2. Missing `vw_ultimate_adaptive_signal` view (blocks dashboard)

**Recommendation:** Fix the 2 critical items immediately, then evaluate optional migrations based on actual usage.

---

**Report Generated:** November 15, 2025  
**Data Sources:** Direct BigQuery queries + verification audit  
**Next Review:** After critical fixes are applied
