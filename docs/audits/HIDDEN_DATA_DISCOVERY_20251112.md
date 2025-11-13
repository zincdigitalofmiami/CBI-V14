# Hidden Data Discovery Report
**Date**: November 12, 2025  
**Discovery Scripts**: `scripts/find_hidden_data_fast.py`, `scripts/check_historical_sources.py`

---

## 🎯 Executive Summary

**Total Datasets Discovered**: 24 (previously only checking 2-3)  
**Total Tables Found**: 231  
**Historical Data Sources Found**: 11+ tables with 5+ years of data  
**Key Finding**: **24.2 years of currency data** with **4,763 pre-2020 rows**!

---

## 📊 All Datasets Discovered

1. `api` - 1 table
2. `archive` - (error accessing)
3. `archive_consolidation_nov6` - 4 tables
4. `bkp` - 8 tables (backup tables)
5. `curated` - 2 tables
6. `dashboard` - 3 tables
7. `deprecated` - 2 tables
8. `export_evaluated_data_items_cbi_v14_automl_pilot_1w_2025_10_28T10_08_35_327Z` - 1 table
9. `forecasting_data_warehouse` - **81 tables** (main data warehouse)
10. `market_data` - 4 tables
11. `model_backups_oct27` - (error accessing)
12. `models` - 22 tables
13. `models_v4` - **72 tables** (production models)
14. `models_v5` - (error accessing)
15. `neural` - (error accessing)
16. `performance` - (error accessing)
17. `predictions` - 4 tables
18. `predictions_uc1` - 4 tables
19. `raw` - (error accessing)
20. `signals` - 1 table
21. `staging` - 11 tables
22. `staging_ml` - (error accessing)
23. `weather` - 1 table
24. `yahoo_finance_comprehensive` - 10 tables

---

## 🎯 HISTORICAL DATA SOURCES FOUND

### ⭐ **CRITICAL FINDING: Pre-2020 Currency Data**

**`models_v4.currency_complete`**:
- **Rows**: 6,287
- **Date Range**: **2001-08-27 to 2025-11-05**
- **Span**: **24.2 years** (8,836 days)
- **Unique Dates**: 6,287
- **🎯 PRE-2020 DATA**: **4,763 rows** (2001-2019)
- **Status**: ✅ **MAJOR HISTORICAL DATA SOURCE**

This is the **ONLY** table found with significant pre-2020 data!

### Other Historical Sources (5+ years, but post-2020)

1. **`models_v4.economic_indicators_daily_complete`**
   - 11,893 rows
   - 5.8 years (2020-01-02 to 2025-11-03)
   - 2,043 unique dates
   - ⚠️ No pre-2020 data

2. **`models_v4.yahoo_finance_weekend_complete`**
   - 14,301 rows
   - 5.8 years (2020-01-02 to 2025-11-03)
   - 2,043 unique dates
   - ⚠️ No pre-2020 data

3. **`models_v4.usd_cny_daily_complete`**
   - 5,021 rows
   - 5.8 years (2020-01-02 to 2025-11-03)
   - 2,043 unique dates
   - ⚠️ No pre-2020 data

4. **`models_v4.treasury_10y_yahoo_complete`**
   - 2,043 rows
   - 5.8 years (2020-01-02 to 2025-11-03)
   - 2,043 unique dates
   - ⚠️ No pre-2020 data

5. **`models_v4.palm_price_daily_complete`**
   - 2,045 rows
   - 5.8 years (2020-01-02 to 2025-11-03)
   - 2,043 unique dates
   - ⚠️ No pre-2020 data

6. **`models_v4.palm_oil_complete`**
   - 1,842 rows
   - 5.0 years (2020-10-21 to 2025-11-05)
   - ⚠️ No pre-2020 data

7. **`models.complete_signals_features`**
   - 1,263 rows
   - 5.0 years (2020-10-21 to 2025-10-13)
   - ⚠️ No pre-2020 data

8. **`models.training_data_complete_all_intelligence`**
   - 1,263 rows
   - 5.0 years (2020-10-21 to 2025-10-13)
   - ⚠️ No pre-2020 data

9. **`models_v4._ARCHIVED_training_dataset_baseline_complete`**
   - 1,251 rows
   - 5.0 years (2020-10-21 to 2025-10-13)
   - ⚠️ No pre-2020 data

10. **`models_v4.full_220_comprehensive_2yr`**
    - 482 rows
    - 1.8 years (2024-01-02 to 2025-11-06)
    - ⚠️ No pre-2020 data

---

## 📦 ARCHIVED/BACKUP TABLES

### models_v4 Archived Tables (13 tables found)

All have ~1,251 rows (2020-2025 data):

- `_ARCHIVED_archive_training_dataset_20251027_pre_update` - 1,251 rows
- `_ARCHIVED_archive_training_dataset_DUPLICATES_20251027` - 1,263 rows
- `_ARCHIVED_archive_training_dataset_super_enriched_20251027_final` - 1,251 rows
- `_ARCHIVED_training_dataset_backup_20251028` - 1,251 rows
- `_ARCHIVED_training_dataset_baseline_clean` - 1,251 rows
- `_ARCHIVED_training_dataset_baseline_complete` - 1,251 rows
- `_ARCHIVED_training_dataset_clean` - 1,251 rows
- `_ARCHIVED_training_dataset_snapshot_20251028_pre_update` - 1,251 rows
- `baseline_1m_comprehensive_2yr_55_symbols_backup` - 482 rows
- `training_dataset_pre_coverage_fix_backup` - 2,045 rows
- `training_dataset_pre_forwardfill_backup` - 2,043 rows
- `training_dataset_pre_integration_backup` - 2,136 rows
- `training_dataset_super_enriched_backup` - 2,045 rows

### bkp Dataset Backup Tables

**Soybean Oil Price Backups**:
- `bkp.soybean_oil_prices_backup_20251021_152417` - 2,255 rows (2021-12-15 to 2025-10-21)
- `bkp.soybean_oil_prices_backup_20251021_152537` - 2,255 rows (2021-12-15 to 2025-10-21)
- `bkp.soybean_oil_prices_20251010T231754Z` - 525 rows (2023-09-12 to 2025-10-10)
- `bkp.soybean_oil_prices_SAFETY_20251021_180706` - (not checked)
- `bkp.crude_oil_prices_SAFETY_20251021_180706` - (not checked)

**Note**: Backup tables only contain recent data (2021+), not historical pre-2020 data.

---

## 💰 PRICE/COMMODITY TABLES DISCOVERED

Found **48 potential price/commodity tables** across datasets:

### forecasting_data_warehouse (30+ price tables):
- `soybean_oil_prices`, `soybean_prices`, `soybean_meal_prices`
- `palm_oil_prices`, `canola_oil_prices`, `rapeseed_oil_prices`
- `corn_prices`, `wheat_prices`, `cotton_prices`, `cocoa_prices`
- `crude_oil_prices`, `gold_prices`, `natural_gas_prices`
- `sp500_prices`, `treasury_prices`, `usd_index_prices`
- `biofuel_prices`
- `futures_prices_barchart`, `futures_prices_cme_public`
- `futures_prices_investing`, `futures_prices_marketwatch`
- `futures_sentiment_tradingview`
- `hourly_prices`, `realtime_prices`
- `ers_oilcrops_monthly`

### models_v4 (price-related):
- `palm_oil_complete`, `palm_price_daily_complete`
- `treasury_10y_yahoo_complete`

---

## 🔍 KEY FINDINGS

### ✅ What We Found

1. **24.2 years of currency data** (2001-2025) with **4,763 pre-2020 rows**
2. **Multiple "complete" tables** with 5+ years of data (2020-2025)
3. **231 total tables** across 24 datasets
4. **Extensive backup/archive tables** (though most are post-2020)

### ❌ What's Still Missing

1. **Pre-2020 soybean oil prices** - No historical data found (only 5 years: 2020-2025)
2. **Pre-2020 economic indicators** - All "complete" tables start from 2020
3. **Pre-2020 training data** - All production training tables start from 2020
4. **125+ years of historical data** - Not found anywhere

### 🎯 Critical Discovery

**`models_v4.currency_complete`** is the **ONLY** significant pre-2020 data source found:
- Contains **4,763 rows** of pre-2020 currency data (2001-2019)
- This can be used to:
  - Train models on historical currency patterns
  - Understand pre-2020 market regimes
  - Build currency-based features for historical periods

---

## 📋 RECOMMENDATIONS

### Immediate Actions

1. **Use `currency_complete` for historical analysis**:
   ```sql
   SELECT * 
   FROM `cbi-v14.models_v4.currency_complete`
   WHERE date < '2020-01-01'
   ORDER BY date
   ```

2. **Check `models.FINAL_TRAINING_DATASET_COMPLETE`**:
   - Had schema error, needs investigation
   - Might contain historical training data

3. **Investigate `yahoo_finance_comprehensive` dataset**:
   - 10 tables found, not fully explored
   - Might contain historical price data

### Long-term Actions

1. **Backfill historical soybean oil prices** (1900-2020)
2. **Backfill historical economic indicators** (pre-2020)
3. **Rebuild production training tables** with historical data once backfilled
4. **Create historical regime datasets** using currency_complete and other sources

---

## 📊 DATA AVAILABILITY MATRIX

| Data Type | Pre-2020 | 2020-2025 | Status |
|-----------|----------|-----------|--------|
| Currency Data | ✅ 4,763 rows (2001-2019) | ✅ 1,524 rows | ✅ Available |
| Soybean Oil Prices | ❌ None | ✅ 1,301 rows | ⚠️ Missing historical |
| Economic Indicators | ❌ None | ✅ 11,893 rows | ⚠️ Missing historical |
| Treasury/Yield | ❌ None | ✅ 2,043 rows | ⚠️ Missing historical |
| Palm Oil | ❌ None | ✅ 1,842 rows | ⚠️ Missing historical |
| Training Data | ❌ None | ✅ 1,400+ rows | ⚠️ Missing historical |

---

## 🎯 NEXT STEPS

1. ✅ **Document all discovered tables** (this report)
2. 🔄 **Investigate `yahoo_finance_comprehensive` dataset** for historical data
3. 🔄 **Check `models.FINAL_TRAINING_DATASET_COMPLETE`** schema
4. 🔄 **Use `currency_complete`** for historical regime analysis
5. 📋 **Plan historical data backfill** strategy

---

**Last Updated**: November 12, 2025  
**Discovery Scripts**: 
- `scripts/find_hidden_data_fast.py`
- `scripts/check_historical_sources.py`

