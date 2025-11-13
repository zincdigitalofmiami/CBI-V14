# Training Data Review Report - Post Historical Backfill
**Date**: November 12, 2025  
**Status**: ⚠️ **EXPORT SCRIPT NEEDS UPDATE**

---

## ✅ WHAT WAS BACKFILLED

### Historical Data Integration (Complete)
- **Table**: `forecasting_data_warehouse.soybean_oil_prices`
- **Before**: 1,301 rows (2020-2025)
- **After**: 6,057 rows (2000-2025)
- **Added**: 4,756 historical rows (+365%)

### New Regime Tables Created (4 tables)
1. **`models_v4.trade_war_2017_2019_historical`** - 754 rows
2. **`models_v4.crisis_2008_historical`** - 253 rows
3. **`models_v4.pre_crisis_2000_2007_historical`** - 1,737 rows
4. **`models_v4.recovery_2010_2016_historical`** - 1,760 rows

**Total**: 4,504 rows of historical regime data

---

## ⚠️ WHAT'S MISSING IN EXPORT SCRIPT

### Current Export Script Issues

1. **Historical Regime Tables NOT Exported** ❌
   - Script exports 5 regime datasets filtered from `production_training_data_1m`
   - Does NOT export the 4 new historical regime tables
   - These tables have different structure (raw prices, not feature-engineered)

2. **Historical Data Export Uses Old Query** ⚠️
   - Current query only labels regimes, doesn't use full 25-year dataset
   - Should export all 6,057 rows (2000-2025)

3. **Production Training Tables May Be Outdated** ⚠️
   - `production_training_data_*` tables built from old 5-year dataset
   - Need to verify if they include historical data (2000-2025)
   - If not, tables need to be rebuilt with extended date range

---

## 🔧 REQUIRED UPDATES

### 1. Update Export Script (`scripts/export_training_data.py`)

**Add Historical Regime Table Exports**:
```python
# Add to EXPORT_CONFIG or create separate function
HISTORICAL_REGIME_TABLES = [
    {
        'table': 'trade_war_2017_2019_historical',
        'output_file': f'{TRAINING_DATA_EXPORTS}/trade_war_2017_2019_historical.parquet',
        'description': 'Trade war regime (2017-2019) - 754 rows'
    },
    {
        'table': 'crisis_2008_historical',
        'output_file': f'{TRAINING_DATA_EXPORTS}/crisis_2008_historical.parquet',
        'description': '2008 financial crisis - 253 rows'
    },
    {
        'table': 'pre_crisis_2000_2007_historical',
        'output_file': f'{TRAINING_DATA_EXPORTS}/pre_crisis_2000_2007_historical.parquet',
        'description': 'Pre-crisis period (2000-2007) - 1,737 rows'
    },
    {
        'table': 'recovery_2010_2016_historical',
        'output_file': f'{TRAINING_DATA_EXPORTS}/recovery_2010_2016_historical.parquet',
        'description': 'Post-crisis recovery (2010-2016) - 1,760 rows'
    }
]
```

**Update Historical Data Export**:
- Change query to export all 6,057 rows (not just labeled)
- Include all columns from `soybean_oil_prices` table
- Add proper regime labels for all periods

**Update Regime Export Function**:
- Keep existing 5 regime exports (filtered from production_training_data_1m)
- Add 4 new historical regime exports (from new tables)
- Total: 9 regime datasets

### 2. Verify Production Training Tables

**Check if tables include historical data**:
```sql
-- Check date range of production tables
SELECT 
    MIN(date) as earliest_date,
    MAX(date) as latest_date,
    COUNT(*) as row_count
FROM `cbi-v14.models_v4.production_training_data_1m`;
```

**If tables only go back to 2020**:
- Need to rebuild `production_training_data_*` tables with extended date range
- Use 2000-2025 instead of 2020-2025
- This will add 4,756 rows to each horizon table

### 3. Update Regime Export Logic

**Current**: Exports 5 regimes filtered from `production_training_data_1m`
- trump_2.0_2023_2025
- trade_war_2017_2019
- inflation_2021_2022
- crisis_2008_2020
- historical_pre2000

**Should Export**: 9 regimes total
- **5 from production_training_data_1m** (feature-engineered, 2020+)
- **4 from historical tables** (raw prices, 2000-2019)

---

## 📊 EXPECTED EXPORT TOTALS (After Updates)

### Primary Training Tables (6)
- production_training_data_1w.parquet
- production_training_data_1m.parquet
- production_training_data_3m.parquet
- production_training_data_6m.parquet
- production_training_data_12m.parquet
- trump_rich_2023_2025.parquet

### Historical Full Dataset (1)
- historical_full.parquet (6,057 rows, 2000-2025)

### Regime-Specific Datasets (9 total)
**From production_training_data_1m** (5):
- trump_2.0_2023_2025.parquet
- trade_war_2017_2019.parquet
- inflation_2021_2022.parquet
- crisis_2008_2020.parquet
- historical_pre2000.parquet

**From historical regime tables** (4):
- trade_war_2017_2019_historical.parquet (754 rows)
- crisis_2008_historical.parquet (253 rows)
- pre_crisis_2000_2007_historical.parquet (1,737 rows)
- recovery_2010_2016_historical.parquet (1,760 rows)

**Total**: 16 Parquet files (up from 12)

---

## 🎯 ACTION ITEMS

### Immediate (Before Day 1 Execution)
1. ✅ **Update export script** to include 4 historical regime tables
2. ✅ **Update historical data export** to use full 25-year dataset
3. ✅ **Verify production training tables** include historical data
4. ✅ **Test export script** with new tables

### If Production Tables Need Rebuild
1. ⚠️ **Rebuild production_training_data_* tables** with 2000-2025 date range
2. ⚠️ **Verify feature engineering** works with historical data
3. ⚠️ **Test training** with extended datasets

### Documentation
1. ✅ **Update DAY_1_DATA_EXPORT_MANIFEST.md** with new regime tables
2. ✅ **Update QUICK_REFERENCE.txt** if needed

---

## 📋 VERIFICATION CHECKLIST

Before running Day 1 export:

- [ ] Export script includes 4 historical regime tables
- [ ] Historical data export uses full 6,057 rows
- [ ] Production training tables verified (date range check)
- [ ] All 16 expected files listed in export script
- [ ] Export script tested (dry run or small subset)

---

## 🚀 RECOMMENDATION

**Priority**: HIGH - Update export script before Day 1 execution

**Impact**: 
- Without updates: Missing 4,504 rows of historical regime data
- With updates: Complete 25-year training dataset available

**Time Estimate**: 30 minutes to update and test export script

---

**Status**: Export script needs updates to capture all backfilled data  
**Next Step**: Update `scripts/export_training_data.py` with historical regime tables

