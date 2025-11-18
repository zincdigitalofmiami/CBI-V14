# Verification Issues Found
**Date:** November 15, 2025  
**Audit Type:** Comprehensive Data Verification

---

## Critical Issues (P0 - Must Fix Immediately)

### 1. Training Table Regime Placeholders
**Table:** `training.zl_training_prod_allhistory_1m`  
**Issue:** All 1,404 rows have `market_regime='allhistory'` and `training_weight=1`  
**Impact:** Cannot perform regime-weighted training  
**Fix:**
```sql
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET market_regime = rc.regime
FROM `cbi-v14.training.regime_calendar` rc
WHERE t.date = rc.date;

UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET training_weight = CAST(rw.weight AS INT64)
FROM `cbi-v14.training.regime_weights` rw
WHERE t.market_regime = rw.regime;
```
**Repeat for all 10 training tables**

### 2. Missing Pre-2020 Data in Training Tables
**Issue:** All training tables start from 2020, missing 2000-2019 (20 years)  
**Impact:** Models cannot learn from historical patterns  
**Available Data:** 5,236 rows in models_v4 historical tables  
**Fix:**
```sql
INSERT INTO `cbi-v14.training.zl_training_prod_allhistory_1m` 
(date, market_regime, training_weight)
SELECT date, 'precrisis_2000_2007', 100
FROM `cbi-v14.models_v4.pre_crisis_2000_2007_historical`
WHERE date NOT IN (SELECT date FROM `cbi-v14.training.zl_training_prod_allhistory_1m`);

-- Repeat for:
-- crisis_2008_historical (regime='financial_crisis_2008_2009', weight=500)
-- recovery_2010_2016_historical (regime='recovery_2010_2016', weight=300)
-- trade_war_2017_2019_historical (regime='tradewar_2017_2019', weight=1500)
```

### 3. Missing Join Tables
**Tables Referenced but Don't Exist:**
- `raw_intelligence.commodity_soybean_oil_prices` - Used in BUILD_TRAINING_TABLES_NEW_NAMING.sql line 37
- `forecasting_data_warehouse.vix_data` - Used in BUILD_TRAINING_TABLES_NEW_NAMING.sql line 57

**Fix Options:**
1. Create missing tables
2. Update SQL to use existing tables:
   - Use `forecasting_data_warehouse.soybean_oil_prices` instead
   - Use `forecasting_data_warehouse.vix_daily` instead

---

## High Priority Issues (P1)

### 4. Incomplete Regime Assignments
**Issue:** Training tables only have 1-3 unique regimes (expected 7+)  
**Current State:**
- Most tables: 3 regimes (covid_2020_2021, inflation_2021_2023, trump_2023_2025)
- 1m table: 1 regime ('allhistory') - CRITICAL
- Expected: 7+ regimes including precrisis, crisis, recovery, tradewar, etc.

**Fix:** Execute UPDATE statements from BUILD_TRAINING_TABLES_NEW_NAMING.sql lines 181-220

### 5. Missing API View
**View:** `api.vw_ultimate_adaptive_signal`  
**Issue:** Referenced but doesn't exist  
**Impact:** Dashboard/API cannot access signals  
**Fix:** Create view per EXECUTION_PLAN_FINAL_20251115.md Phase 4A

---

## Medium Priority Issues (P2)

### 6. Sharpe View Placeholder Warning
**View:** `performance.vw_soybean_sharpe_metrics`  
**Issue:** View definition contains "placeholder" text  
**Impact:** May indicate incomplete implementation  
**Fix:** Review view definition and remove placeholder references

### 7. SQL Files with Placeholder Defaults
**Files:**
- `config/bigquery/bigquery-sql/BUILD_TRAINING_TABLES_NEW_NAMING.sql` lines 127-128
- `config/bigquery/bigquery-sql/UPDATE_BIOFUEL_ALL_FEATURES.sql` lines 108-109

**Issue:** Default values set to placeholders (should be overridden by UPDATE statements)  
**Impact:** If UPDATE statements fail, tables will have placeholder values  
**Fix:** Ensure UPDATE statements always execute after table creation

---

## Summary

**Total Issues Found:** 7
- **Critical (P0):** 3
- **High Priority (P1):** 2
- **Medium Priority (P2):** 2

**Data Status:**
- ✅ 1.87M rows loaded across 453 tables
- ✅ No 0.5 placeholder pattern in production price data
- ✅ Historical data verified real (5,236 rows)
- ❌ Training tables have placeholder regimes
- ❌ Missing pre-2020 data in training tables
- ❌ Some join tables missing

**Next Steps:**
1. Execute regime UPDATE statements (P0)
2. Load pre-2020 historical data (P0)
3. Fix missing join table references (P0)
4. Create missing API view (P1)
5. Review Sharpe view definition (P2)


