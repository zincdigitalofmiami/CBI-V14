# Vertex AI Dataset Audit Results

**Date:** November 7, 2025  
**Audit Script:** `vertex-ai/data/audit_vertex_training_datasets.py`  
**Status:** ❌ CRITICAL ISSUES FOUND

---

## Executive Summary

Comprehensive audit of 4 training tables identified **1 critical issue** that will prevent Vertex AI training.

### PASSES ✅
- ✅ All target columns: 0 NULLs (ready for training)
- ✅ All dates: No duplicates
- ✅ String columns: <5000 unique values (AutoML compatible)
- ✅ Boolean columns: None found
- ✅ Reserved column names: None found
- ✅ NULL percentage: Sampled columns OK

### CRITICAL ISSUES ❌
- ❌ **Feature count mismatch:** 1M table has 444 columns, others have 300 columns (144 column difference)

### WARNINGS ⚠️
- ⚠️ Mixed frequency gaps (1-6 days) - Expected for trading data with weekends/holidays

---

## Detailed Audit Results

### 1. Schema Contract Check

**Table Column Counts:**
| Table | Columns | Data Types |
|-------|---------|------------|
| production_training_data_1m | 444 | FLOAT64: 373, INT64: 68, STRING: 2, DATE: 1 |
| production_training_data_3m | 300 | FLOAT64: 231, INT64: 67, STRING: 1, DATE: 1 |
| production_training_data_6m | 300 | FLOAT64: 231, INT64: 67, STRING: 1, DATE: 1 |
| production_training_data_1w | 300 | FLOAT64: 231, INT64: 67, STRING: 1, DATE: 1 |

**Result:** ❌ FAIL - Inconsistent feature counts

### 2. Target Column Validation

| Table | Target | NULL Count | Total Rows | NULL % | Min | Max | Avg |
|-------|--------|------------|------------|--------|-----|-----|-----|
| production_training_data_1m | target_1m | 0 | 1,404 | 0.0% | 25.05 | 90.60 | 52.85 |
| production_training_data_3m | target_3m | 0 | 1,475 | 0.0% | 24.99 | 90.60 | 51.13 |
| production_training_data_6m | target_6m | 0 | 1,473 | 0.0% | 27.97 | 90.60 | 49.72 |
| production_training_data_1w | target_1w | 0 | 1,472 | 0.0% | 24.99 | 90.60 | 51.86 |

**Result:** ✅ PASS - All targets have 0 NULL values

### 3. Date/Time Column Validation

| Table | Total Rows | Distinct Dates | Min Date | Max Date | Status |
|-------|------------|----------------|----------|----------|--------|
| production_training_data_1m | 1,404 | 1,404 | 2020-01-06 | 2025-11-06 | PASS |
| production_training_data_3m | 1,475 | 1,475 | 2020-01-02 | 2025-11-06 | PASS |
| production_training_data_6m | 1,473 | 1,473 | 2020-01-02 | 2025-11-06 | PASS |
| production_training_data_1w | 1,472 | 1,472 | 2020-01-02 | 2025-11-06 | PASS |

**Result:** ✅ PASS - No duplicate dates

### 4. String Feature Validation

| Table | String Columns | Unique Values | Status |
|-------|----------------|---------------|--------|
| production_training_data_1m | volatility_regime | 3 | ✅ PASS |
| production_training_data_1m | yahoo_data_source | 1 | ✅ PASS |
| production_training_data_3m | volatility_regime | 3 | ✅ PASS |
| production_training_data_6m | volatility_regime | 3 | ✅ PASS |
| production_training_data_1w | volatility_regime | 3 | ✅ PASS |

**Result:** ✅ PASS - All string columns <5000 unique values

### 5. Frequency Consistency

| Table | Distinct Gaps | Min Gap | Max Gap | Median Gap | Status |
|-------|---------------|---------|---------|------------|--------|
| production_training_data_1m | 6 | 1 day | 6 days | 1 day | ⚠️ Mixed |
| production_training_data_3m | 5 | 1 day | 5 days | 1 day | ✅ OK |
| production_training_data_6m | 6 | 1 day | 6 days | 1 day | ⚠️ Mixed |
| production_training_data_1w | 4 | 1 day | 4 days | 1 day | ✅ OK |

**Result:** ⚠️ WARNING - Mixed frequencies (expected for trading data)

### 6. NULL Percentage Check

Sampled first 10 numeric columns from each table:
- ✅ production_training_data_1m: No high-NULL columns
- ✅ production_training_data_3m: No high-NULL columns
- ✅ production_training_data_6m: No high-NULL columns
- ✅ production_training_data_1w: No high-NULL columns

**Result:** ✅ PASS (based on sample)

### 7. Boolean Column Check

**Result:** ✅ PASS - No boolean columns found in any table

### 8. Reserved Column Name Check

**Result:** ✅ PASS - No reserved column names found

### 9. Data Quality Summary

| Table | Total Rows | Date Range | Days Covered |
|-------|------------|------------|--------------|
| production_training_data_1m | 1,404 | 2020-01-06 to 2025-11-06 | 2,131 days |
| production_training_data_3m | 1,475 | 2020-01-02 to 2025-11-06 | 2,135 days |
| production_training_data_6m | 1,473 | 2020-01-02 to 2025-11-06 | 2,135 days |
| production_training_data_1w | 1,472 | 2020-01-02 to 2025-11-06 | 2,135 days |

---

## Extra Columns in production_training_data_1m

The 1M table has 144 additional columns not present in other tables. Sample of extra columns:

**Stock Data:**
- ADM (Archer Daniels Midland): analyst_target, beta, close, market_cap, pe_ratio
- BG (Bunge): analyst_target, beta, close, market_cap, pe_ratio
- CF (CF Industries): analyst_target, beta, close, market_cap, pe_ratio

**Commodity/Currency Data:**
- Brent crude: close, ma_200d, ma_30d, macd_line, rsi_14
- BRLUSD (Brazilian Real): close, ma_30d, momentum_10, roc_10, rsi_14

**Biofuel Data:**
- biodiesel_margin, biodiesel_spread, biodiesel_spread_ma30, biodiesel_spread_vol, biofuel_crack

These appear to be valuable market features that should likely be added to other tables rather than removed.

---

## Critical Issues Requiring Action

### Issue #1: Feature Count Mismatch (CRITICAL)

**Problem:** Vertex AI AutoML requires all training tables to have identical feature lists.

**Impact:** Training will fail immediately if tables have different column counts.

**Options:**
1. **Option A (Recommended):** Add the 144 missing columns to 3m/6m/1w tables
   - Pros: Retains valuable market data, more features = better predictions
   - Cons: More work to backfill data

2. **Option B:** Remove 144 columns from 1m table to match others
   - Pros: Faster to implement
   - Cons: Loses valuable market intelligence

**Recommendation:** Option A - Add columns to maintain rich feature set

---

## Action Items

### Critical (Must Fix Before Training)
1. ❗ **Standardize feature counts:**
   - Add 144 missing columns to production_training_data_3m
   - Add 144 missing columns to production_training_data_6m
   - Add 144 missing columns to production_training_data_1w
   - OR: Remove 144 columns from production_training_data_1m

### High Priority (Should Fix)
2. 📋 **Create production_training_data_12m table:**
   - Add 12-month horizon for long-term forecasting
   - Must match final feature count (444 or 300 columns)

### Medium Priority (Nice to Have)
3. 🔍 **Full NULL percentage audit:**
   - Current audit only sampled 10 columns
   - Run full audit on all numeric columns

---

## Next Steps

1. Identify all 144 extra columns (complete list)
2. Decide: Add to other tables or remove from 1m
3. Create schema alignment script
4. Execute alignment across all tables
5. Re-run this audit to verify fixes
6. Proceed to Vertex AI dataset creation

---

**Status:** BLOCKED - Cannot proceed to Vertex AI training until feature counts are standardized.

**Estimated Fix Time:** 2-4 hours (depending on Option A vs Option B)

