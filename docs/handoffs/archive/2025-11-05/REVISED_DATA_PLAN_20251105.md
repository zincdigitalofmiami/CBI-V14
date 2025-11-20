---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# REVISED Data Enhancement Plan - Based on Audit
**Date**: November 5, 2025  
**Status**: 🔄 PLAN UPDATED

---

## 🔴 Critical Discoveries

1. **training_dataset_super_enriched**: Only 11 columns (Big 8 signals)
2. **enhanced_features_automl**: Broken view (references non-existent vix_level)
3. **No sentiment columns**: Currently 0 sentiment features in training
4. **Date constraints**: Social data only from Oct 2024 forward

---

## ✅ Realistic Implementation Plan

### Phase 1: GDELT Historical Data (PRIORITY 1)
**Timeline**: 2 days  
**Coverage**: 100% (2020-2025)

```python
# scripts/backfill_gdelt_events.py
def fetch_gdelt_historical():
    """
    GDELT has data from 1979-present
    Query for soybean, China, biofuel events
    Calculate event tone/sentiment
    """
    events = [
        "soybean OR soy",
        "China trade OR Chinese imports",
        "biofuel OR biodiesel OR ethanol",
        "Argentina export",
        "USDA crop"
    ]
    
    # Store in: forecasting_data_warehouse.gdelt_events_daily
    # Columns: date, event_count, avg_tone, goldstein_score
```

### Phase 2: FRED Economic Data (PRIORITY 1)
**Timeline**: 1 day  
**Coverage**: 100% (2020-2025)

```python
# Extend scripts/get_all_missing_data.py
fred_series = {
    'CPIAUCSL': 'cpi',           # Consumer Price Index
    'GDPC1': 'gdp',              # Real GDP
    'DFF': 'fed_funds_rate',     # Fed Funds Rate
    'DGS10': 'treasury_10y',     # 10-Year Treasury
    'DEXCHUS': 'usd_cny',        # USD/CNY Exchange Rate
    'DTWEXBGS': 'dxy',           # Dollar Index
}
```

### Phase 3: USDA Data Enhancement (PRIORITY 1)
**Timeline**: 2 days  
**Coverage**: 100% (available data)

```python
# scripts/enhance_usda_data.py
def fetch_usda_exports():
    """
    USDA FAS Export Sales Reports
    Weekly granularity
    No API key required
    """
    endpoints = [
        "export_sales",      # Weekly export sales
        "wasde",            # Monthly supply/demand
        "crop_progress"     # Weekly crop conditions
    ]
```

### Phase 4: Fix Existing Tables (PRIORITY 2)
**Timeline**: 1 day

1. Fix `enhanced_features_automl` view
2. Create proper feature aggregation
3. Join Big 8 signals with other features

### Phase 5: Web Scraping (PRIORITY 2)
**Timeline**: 3-4 days

1. **RIN Prices**: Scrape EPA EMTS website
2. **Argentina Ports**: Scrape port authority
3. **Freight Rates**: Scrape public sources

---

## 📊 Data Availability Matrix

| Data Source | Historical Coverage | API Available | Action |
|------------|-------------------|---------------|---------|
| GDELT Events | 1979-present | ✅ FREE | Implement |
| FRED Economic | 1960-present | ✅ FREE | Implement |
| USDA FAS | 2010-present | ✅ FREE | Implement |
| NOAA Weather | 1950-present | ✅ Have Key | Enhance |
| Social Media | Oct 2024-present | ✅ Have Key | Limited |
| RIN Prices | 2010-present | ❌ | Scrape |
| Argentina Ports | Varies | ❌ | Scrape |
| Baltic Freight | Paid only | ❌ | Find alt |

---

## 🎯 Adjusted Expectations

### What We WILL Deliver:
1. **GDELT Events**: 100% coverage, 2020-2025
2. **Economic Data**: 100% coverage via FRED
3. **USDA Exports**: 100% available data
4. **Weather**: Enhanced coverage via NOAA

### What We CAN'T Deliver:
1. **Social Sentiment**: Only Oct 2024-forward (13% coverage)
2. **News Sentiment**: Only from subscription start
3. **RIN Historical**: Requires extensive scraping

### Expected Impact:
- **Realistic MAPE Improvement**: 10-15%
- **Feature Coverage**: From 11 → ~50 features
- **NULL Reduction**: Focus on adding NEW features, not filling NULL

---

## 🚀 Immediate Actions

1. **Start GDELT implementation** (highest ROI)
2. **Run FRED data pull** (easy win)
3. **Fix broken views** (unblock features)
4. **USDA enhancement** (free data)

---

## ⚠️ Key Insight

The "258 features" don't exist in the current training dataset. We need to:
1. Find where these features actually are
2. Build a proper feature engineering pipeline
3. Focus on ADDING features, not filling NULLs

**Recommendation**: Proceed with GDELT + FRED + USDA first (100% coverage, free APIs)






