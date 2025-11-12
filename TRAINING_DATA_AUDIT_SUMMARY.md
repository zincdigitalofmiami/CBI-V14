# Complete Training Data Audit Summary
**Date**: November 12, 2025  
**Status**: ⚠️ **PRODUCTION TABLES NEED REBUILD**

---

## ✅ **WHAT'S GOOD**

### Historical Data Source ✅
- **soybean_oil_prices**: 6,057 rows (2000-11-13 to 2025-11-05)
- **Historical data present**: ✅ YES (starts 2000-11-13)
- **Coverage**: 25 years complete

### Historical Regime Tables ✅
All 4 tables exist and populated:
- **trade_war_2017_2019_historical**: 754 rows (2017-2019)
- **crisis_2008_historical**: 253 rows (2008)
- **pre_crisis_2000_2007_historical**: 1,737 rows (2000-2007)
- **recovery_2010_2016_historical**: 1,760 rows (2010-2016)
- **Total**: 4,504 rows of historical regime data

### Trump Rich Table ✅
- **trump_rich_2023_2025**: 732 rows (2023-01-03 to 2025-11-06)
- **Status**: Complete and current

---

## ⚠️ **CRITICAL ISSUE: Production Tables Missing Historical Data**

### Current Status
All `production_training_data_*` tables **ONLY** include data from 2020 onwards:

| Table | Date Range | Rows | Features | Historical? |
|-------|------------|------|----------|------------|
| **1w** | 2020-01-02 to 2025-11-06 | 1,472 | 299 | ❌ NO |
| **1m** | 2020-01-06 to 2025-11-06 | 1,404 | 443 | ❌ NO |
| **3m** | 2020-01-02 to 2025-11-06 | 1,475 | 299 | ❌ NO |
| **6m** | 2020-01-02 to 2025-11-06 | 1,473 | 299 | ❌ NO |
| **12m** | 2020-01-02 to 2025-11-06 | 1,473 | 300 | ❌ NO |

### Impact
- **Missing**: ~4,756 rows of historical data (2000-2019) per table
- **Total missing**: ~23,780 rows across all 5 tables
- **Training impact**: Cannot train on historical regimes (2008 crisis, trade wars, etc.)

---

## 📊 **DATA QUALITY ISSUES**

### Date Gaps (Normal - Weekends/Holidays)
All tables have gaps (expected for trading days):
- **1w**: 313 gaps (max 4 days, avg 3.1 days)
- **1m**: 307 gaps (max 6 days, avg 3.4 days)
- **3m**: 294 gaps (max 5 days, avg 3.2 days)
- **6m**: 276 gaps (max 6 days, avg 3.4 days)
- **12m**: 276 gaps (max 6 days, avg 3.4 days)

**Status**: ✅ **NORMAL** - These are weekends/holidays, not data quality issues

### NULL Targets
- **12m table**: 256 NULL targets (17.4%)
  - **Status**: ✅ **EXPECTED** - 12-month horizon requires 12 months of future data
  - **Impact**: Low - these rows can't be used for training anyway

---

## 🎯 **RECOMMENDATIONS**

### Priority 1: Rebuild Production Tables (HIGH)
**Action**: Rebuild all 5 `production_training_data_*` tables with 2000-2025 date range

**Why**:
- Historical data exists in source (`soybean_oil_prices`)
- Historical regime tables exist
- Production tables only have 5 years (2020-2025)
- Missing 20 years of training data

**How**:
1. Use existing SQL: `BACKFILL_PRODUCTION_1M_25YR.sql` (for 1m)
2. Replicate pattern for 1w, 3m, 6m, 12m
3. Test on 1 table first (1m), then replicate

**Time**: 25-75 minutes (5-15 min per table)

**Risk**: LOW - Can test on 1 table first, SQL already exists

### Priority 2: Verify Export Script (MEDIUM)
**Action**: Ensure export script captures all data

**Status**: ✅ **DONE** - Export script already updated to include:
- 6 primary training tables
- 1 historical full dataset
- 5 regime datasets (from production_training_data_1m)
- 4 historical regime tables

**Total**: 16 Parquet files (up from 12)

---

## 📋 **ACTION ITEMS**

### Immediate (Before Day 1 Execution)
- [ ] **Rebuild production_training_data_1m** with 2000-2025 range
- [ ] **Verify rebuild** (check date range)
- [ ] **Rebuild other 4 tables** (1w, 3m, 6m, 12m)
- [ ] **Re-run audit** to verify historical data included

### After Rebuild
- [ ] **Update export script** if needed (likely already done)
- [ ] **Run Day 1 export** to capture all data
- [ ] **Verify exports** include historical data

---

## 📊 **EXPECTED RESULTS AFTER REBUILD**

| Table | Current Rows | Expected Rows | Increase |
|-------|-------------|---------------|----------|
| **1w** | 1,472 | ~6,300 | +329% |
| **1m** | 1,404 | ~6,200 | +342% |
| **3m** | 1,475 | ~6,300 | +327% |
| **6m** | 1,473 | ~6,200 | +321% |
| **12m** | 1,473 | ~6,200 | +321% |

**Total**: ~31,200 rows across all tables (up from ~7,297)

---

## 🎯 **BOTTOM LINE**

### Current State
- ✅ Historical data source: **COMPLETE** (6,057 rows, 2000-2025)
- ✅ Historical regime tables: **COMPLETE** (4,504 rows)
- ❌ Production training tables: **MISSING HISTORICAL** (only 2020-2025)

### Required Action
**Rebuild production_training_data_* tables** to include 2000-2025 data

### Complexity
- **Difficulty**: ⚠️ MODERATE (SQL exists, just needs execution)
- **Time**: 25-75 minutes
- **Risk**: LOW (can test first)

### Impact
- **Before**: 5 years of training data (2020-2025)
- **After**: 25 years of training data (2000-2025)
- **Increase**: +329% to +342% more training data

---

**Status**: ⚠️ **REBUILD REQUIRED** - Production tables missing historical data  
**Next Step**: Run `BACKFILL_PRODUCTION_1M_25YR.sql` to rebuild 1m table, then replicate

