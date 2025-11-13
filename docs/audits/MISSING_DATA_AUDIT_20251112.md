# Missing Data Audit Report
**Date**: November 12, 2025  
**Audit Script**: `scripts/find_missing_data.py`

---

## Executive Summary

**Total Data Sources Checked**: 27  
**✅ OK**: 11 (41%)  
**❌ Issues**: 16 (59%)

### Critical Findings

1. **🔴 STALE DATA** (7 tables): Data not updated in 7+ days
2. **⚠️ LOW DATA** (3 tables): Insufficient rows for reliable training
3. **📉 HISTORICAL DATA GAP**: Only 5 years of soybean oil prices (expected 125+ years)
4. **📅 PRE-2020 DATA MISSING**: All production training data starts from 2020 only

---

## 🔴 STALE DATA (7 Tables)

These tables have not been updated recently and need immediate attention:

| Table | Latest Date | Days Old | Status | Action Required |
|-------|-------------|----------|--------|-----------------|
| `vix_daily` | 2025-10-21 | **22 days** | 🔴 CRITICAL | Run VIX ingestion script |
| `biofuel_prices` | 2025-10-14 | **29 days** | 🔴 CRITICAL | Run EPA RIN prices ingestion |
| `canola_oil_prices` | 2025-10-15 | **28 days** | 🔴 CRITICAL | Run canola oil ingestion |
| `news_advanced` | 2025-10-22 | **21 days** | 🔴 STALE | Run news ingestion |
| `yahoo_finance_enhanced` | 2025-11-03 | **9 days** | 🟡 RECENT | Update ingestion schedule |
| `social_sentiment` | 2025-11-04 | **8 days** | 🟡 RECENT | Update ingestion schedule |
| `news_intelligence` | 2025-11-10 | **2 days** | 🟢 ACCEPTABLE | Monitor closely |

### Recommended Actions

```bash
# Priority 1: Critical stale data
python3 src/ingestion/ingest_volatility.py          # VIX
python3 src/ingestion/ingest_epa_rin_prices.py      # Biofuel prices
python3 src/ingestion/ingest_market_prices.py       # Canola oil

# Priority 2: News and sentiment
python3 src/ingestion/multi_source_news.py          # News advanced
python3 src/ingestion/ingest_social_intelligence_comprehensive.py  # Social sentiment
```

---

## ⚠️ LOW DATA TABLES (3 Tables)

These tables exist but have insufficient data for reliable training:

| Table | Current Rows | Expected | Gap | Action Required |
|-------|--------------|----------|-----|-----------------|
| `cftc_cot` | 86 | 200+ | -114 | Backfill CFTC data |
| `china_soybean_imports` | 22 | 50+ | -28 | Run China imports ingestion |
| `argentina_crisis_tracker` | 10 | 50+ | -40 | Run Argentina tracking |
| `industrial_demand_indicators` | 3 | 10+ | -7 | Run industrial demand ingestion |

### Recommended Actions

```bash
# Backfill missing data
python3 src/ingestion/ingest_cftc_positioning_REAL.py
python3 src/ingestion/ingest_china_imports_uncomtrade.py
python3 src/ingestion/ingest_argentina_port_logistics.py
```

---

## 📉 HISTORICAL DATA GAP

### Soybean Oil Prices

**Current State**:
- Total rows: 1,301
- Date range: **2020-10-21 to 2025-11-05**
- Date span: **5.0 years**
- Expected: **125+ years** (1900-2025)

**Missing**: ~120 years of historical data (1900-2020)

### Impact

- Cannot train on historical patterns (financial crises, trade wars, etc.)
- Missing regime-specific datasets:
  - `trade_war_2017_2019` - No data (base table starts 2020)
  - `crisis_2008_2020` - Only 2020 crisis, missing 2008
  - `historical_pre2000` - No data

### Recommended Actions

```bash
# Backfill historical soybean oil prices
python3 src/ingestion/backfill_prices_yf.py

# Or use bulk historical data loader
python3 src/ingestion/bulk_csv_loader.py
```

---

## 📅 PRE-2020 DATA MISSING

### Production Training Data

All production training tables only start from **2020-01-02**:

| Table | Earliest Date | Missing Period |
|-------|---------------|----------------|
| `production_training_data_1w` | 2020-01-02 | Pre-2020 |
| `production_training_data_1m` | 2020-01-06 | Pre-2020 |
| `production_training_data_3m` | 2020-01-02 | Pre-2020 |
| `production_training_data_6m` | 2020-01-02 | Pre-2020 |
| `production_training_data_12m` | 2020-01-02 | Pre-2020 |

### Impact

- Cannot train on historical regimes (2008 crisis, pre-2020 trade patterns)
- Missing context for long-term market cycles
- Regime-specific training datasets incomplete

### Root Cause

The `production_training_data_*` tables are built from `forecasting_data_warehouse` sources, which only have data from 2020 onwards.

### Recommended Actions

1. **Backfill source data** (soybean oil prices, economic indicators, etc.) to 1900+
2. **Rebuild production training tables** with historical data
3. **Run feature engineering pipeline** on historical data

```bash
# Step 1: Backfill all source data
python3 scripts/PULL_ALL_MISSING_DATA.py

# Step 2: Rebuild production training tables
# (Check config/bigquery/bigquery-sql/PRODUCTION_HORIZON_SPECIFIC/)
```

---

## ✅ DATA SOURCES THAT ARE OK

These tables are fresh and have sufficient data:

- ✅ `soybean_oil_prices` - 1,301 rows, 7 days old
- ✅ `palm_oil_prices` - 1,340 rows, 7 days old
- ✅ `corn_prices` - 1,271 rows, 7 days old
- ✅ `crude_oil_prices` - 1,259 rows, 7 days old
- ✅ `gold_prices` - 1,963 rows, 7 days old
- ✅ `natural_gas_prices` - 1,965 rows, 7 days old
- ✅ `trump_policy_intelligence` - 447 rows, 0 days old
- ✅ `economic_indicators` - 72,553 rows, 7 days old
- ✅ `currency_data` - 59,187 rows, 7 days old
- ✅ `weather_data` - 14,282 rows, 1 day old
- ✅ All `production_training_data_*` tables - Fresh (6 days old)

---

## 📋 ADDITIONAL TABLES DISCOVERED

Found **81 tables** in `forecasting_data_warehouse` and **72 tables** in `models_v4` that are not in the expected list. These may contain additional data sources:

### Notable Additional Tables

**Commodity Prices**:
- `cocoa_prices`, `cotton_prices`, `soybean_prices`, `soybean_meal_prices`
- `wheat_prices`, `rapeseed_oil_prices`
- `sp500_prices`, `treasury_prices`, `usd_index_prices`

**Futures Data**:
- `futures_prices_barchart`, `futures_prices_cme_public`
- `futures_prices_investing`, `futures_prices_marketwatch`
- `hourly_prices`, `realtime_prices`

**USDA Data**:
- `usda_crop_progress`, `usda_export_sales`
- `usda_harvest_progress`, `usda_wasde_soy`
- `ers_oilcrops_monthly`

**Weather Data**:
- `weather_argentina_daily`, `weather_brazil_clean`
- `weather_brazil_daily`, `weather_us_midwest_clean`
- `weather_us_midwest_daily`
- `enso_climate_status`

**News & Intelligence**:
- `breaking_news_hourly`, `news_industry_brownfield`
- `news_market_farmprogress`, `news_reuters`
- `news_ultra_aggressive`, `social_intelligence_unified`

**Policy & Regulatory**:
- `biofuel_policy`, `legislative_bills`
- `policy_events_federalregister`, `policy_rfs_volumes`

**Specialized**:
- `freight_logistics`, `volatility_data`
- `market_analysis_correlations`, `shap_drivers`
- `signals_1w`, `predictions_1m`

---

## 🎯 PRIORITY ACTION PLAN

### Immediate (Today)

1. **Fix stale data** (7 tables):
   ```bash
   python3 src/ingestion/ingest_volatility.py
   python3 src/ingestion/ingest_epa_rin_prices.py
   python3 src/ingestion/ingest_market_prices.py
   ```

2. **Backfill low data** (3 tables):
   ```bash
   python3 src/ingestion/ingest_cftc_positioning_REAL.py
   python3 src/ingestion/ingest_china_imports_uncomtrade.py
   ```

### Short-term (This Week)

3. **Backfill historical soybean oil prices**:
   ```bash
   python3 src/ingestion/backfill_prices_yf.py
   ```

4. **Update news and sentiment ingestion**:
   ```bash
   python3 src/ingestion/multi_source_news.py
   python3 src/ingestion/ingest_social_intelligence_comprehensive.py
   ```

### Medium-term (This Month)

5. **Backfill all pre-2020 source data**
6. **Rebuild production training tables with historical data**
7. **Verify all regime-specific datasets are complete**

---

## 📊 DATA COMPLETENESS METRICS

| Category | Total | OK | Issues | % Complete |
|----------|-------|----|--------|------------|
| Commodity Prices | 7 | 5 | 2 | 71% |
| Market Indicators | 3 | 0 | 3 | 0% |
| News & Sentiment | 4 | 1 | 3 | 25% |
| Economic Data | 3 | 2 | 1 | 67% |
| Supply Chain | 3 | 0 | 3 | 0% |
| Weather | 1 | 1 | 0 | 100% |
| Training Data | 6 | 6 | 0 | 100% |
| **TOTAL** | **27** | **15** | **12** | **56%** |

---

## 🔍 NEXT STEPS

1. **Run stale data fixes** (Priority 1)
2. **Audit additional tables** to see if they contain needed data
3. **Create automated monitoring** to prevent future stale data
4. **Plan historical data backfill** strategy
5. **Update ingestion schedules** for frequently stale sources

---

**Last Updated**: November 12, 2025  
**Next Audit**: After fixing stale data issues

