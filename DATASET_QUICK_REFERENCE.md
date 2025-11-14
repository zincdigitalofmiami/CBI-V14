# 📊 DATASET QUICK REFERENCE
**Last Updated**: November 14, 2025  
**Status**: Current Production State

---

## 🎯 PRIMARY DATASETS (Production)

| Dataset | Location | Tables | Purpose |
|---------|----------|--------|---------|
| **forecasting_data_warehouse** | `cbi-v14.forecasting_data_warehouse` | 97 | Primary production data (commodities, indicators, news) |
| **models_v4** | `cbi-v14.models_v4` | 93 | Training data, models, regime tables |
| **signals** | `cbi-v14.signals` | 34 | Signal views for trading |
| **yahoo_finance_comprehensive** | `cbi-v14.yahoo_finance_comprehensive` | 10 | Historical market data (2000-2025) |

---

## 📊 KEY TABLES BY PURPOSE

### Commodity Prices (25-year history)
- `forecasting_data_warehouse.soybean_oil_prices` - 6,057 rows
- `forecasting_data_warehouse.soybean_prices` - 15,708 rows
- `forecasting_data_warehouse.corn_prices` - 15,623 rows
- `forecasting_data_warehouse.wheat_prices` - 15,631 rows
- `forecasting_data_warehouse.soybean_meal_prices` - 10,775 rows
- `forecasting_data_warehouse.crude_oil_prices` - 10,859 rows
- `forecasting_data_warehouse.natural_gas_prices` - 11,567 rows
- `forecasting_data_warehouse.gold_prices` - 11,555 rows
- `forecasting_data_warehouse.silver_prices` - 4,798 rows
- `forecasting_data_warehouse.copper_prices` - 4,800 rows

### Market Indicators
- `forecasting_data_warehouse.vix_daily` - 6,271 rows
- `forecasting_data_warehouse.sp500_prices` - 10,579 rows
- `forecasting_data_warehouse.usd_index_prices` - 11,636 rows
- `forecasting_data_warehouse.economic_indicators` - 72,553 rows

### Training Data
- `models_v4.production_training_data_1w` - 1,472 rows
- `models_v4.production_training_data_1m` - 1,404 rows
- `models_v4.production_training_data_3m` - 1,475 rows
- `models_v4.production_training_data_6m` - 1,473 rows
- `models_v4.production_training_data_12m` - 1,473 rows

### Historical Regime Tables
- `models_v4.pre_crisis_2000_2007_historical` - 1,737 rows
- `models_v4.crisis_2008_historical` - 253 rows
- `models_v4.recovery_2010_2016_historical` - 1,760 rows
- `models_v4.trade_war_2017_2019_historical` - 754 rows

### Historical Source (The "Lost" Dataset)
- `yahoo_finance_comprehensive.yahoo_normalized` - **314,381 rows** (55 symbols, 2000-2025)
- `yahoo_finance_comprehensive.all_symbols_20yr` - 57,397 rows
- `yahoo_finance_comprehensive.biofuel_components_raw` - 42,367 rows

---

## 🔍 WHERE TO FIND DATA

### For Historical Market Data (2000-2025)
```
cbi-v14.yahoo_finance_comprehensive.yahoo_normalized
```
- 314,381 rows, 55 symbols, 233,060 pre-2020 rows

### For Production Commodity Prices
```
cbi-v14.forecasting_data_warehouse.{commodity}_prices
```
- 13 commodities with 25-year history (2000-2025)

### For Training Data
```
cbi-v14.models_v4.production_training_data_{horizon}
```
- Horizons: 1w, 1m, 3m, 6m, 12m

### For Historical Regimes
```
cbi-v14.models_v4.{regime}_historical
```
- pre_crisis_2000_2007, crisis_2008, recovery_2010_2016, trade_war_2017_2019

### For Trading Signals
```
cbi-v14.signals.vw_{signal_name}
```
- 34 signal views available

### For Economic History (126 years!)
```
cbi-v14.bkp.economic_indicators_SAFETY_20251021_180706
```
- 7,523 rows covering 126 years

### For Seasonality Features
```
cbi-v14.models.vw_seasonality_features
```
- 449,283 rows (largest table in system)

---

## 📊 LARGEST TABLES

| Table | Dataset | Rows | Purpose |
|-------|---------|------|---------|
| `vw_seasonality_features` | models | 449,283 | Seasonality features |
| `yahoo_normalized` | yahoo_finance_comprehensive | 314,381 | Historical market data |
| `economic_indicators` | forecasting_data_warehouse | 72,553 | Economic data |
| `currency_data` | forecasting_data_warehouse | 59,187 | Currency/FX data |
| `all_symbols_20yr` | yahoo_finance_comprehensive | 57,397 | 20-year symbol data |

---

## ✅ VERIFIED DATASETS

**All 24 datasets present**:
- ✅ forecasting_data_warehouse (97 tables)
- ✅ models_v4 (93 tables)
- ✅ signals (34 views)
- ✅ yahoo_finance_comprehensive (10 tables) - **The "lost" dataset - FOUND**
- ✅ models (30 tables)
- ✅ curated (30 tables)
- ✅ bkp (8 tables)
- ✅ staging (11 tables)
- ✅ And 16 more datasets

**Total**: 400+ tables/views, 1.5+ million rows

---

## 🚨 CRITICAL GAPS

| Table | Current | Needed | Status |
|-------|---------|--------|--------|
| `cftc_cot` | 944 rows | 5,000+ | ❌ Need historical backfill |
| `china_soybean_imports` | 22 rows | 500+ | ❌ Need historical backfill |
| `baltic_dry_index` | Missing | 5,000+ | ❌ Need to create |

---

**Quick Reference**: Keep this file updated as datasets change  
**Full Inventory**: See `docs/audits/COMPLETE_DATASET_INVENTORY_20251114.md`
