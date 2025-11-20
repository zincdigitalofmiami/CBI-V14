---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Non-Training Features Documentation

## Overview
This document identifies columns in the final dataset that should be **excluded from training** due to being static metadata, join keys, or non-predictive constants.

Last updated: 2025-11-17

---

## 1. Unprefixed Columns (2)

These columns are intentional join keys and regime identifiers:

### `regime`
- **Type**: Categorical
- **Purpose**: Market regime identifier for training weight assignment
- **Values**: 15 unique regimes (e.g., "financial_crisis", "china_tariffs", etc.)
- **Status**: **Keep for training weight assignment**, but not a feature itself

### `training_weight`
- **Type**: Numeric
- **Purpose**: Sample weight for regime-aware training
- **Values**: 50-1000 scale
- **Status**: **Keep for training**, used as sample weight, not a feature

---

## 2. Static Columns (34)

These columns have no variance and provide no predictive information:

### Yahoo Finance (2 columns)
- `yahoo_stock_splits`: All zeros (futures don't split)
- `yahoo_dividends`: All zeros (futures don't pay dividends)

### CFTC Metadata (32 columns)
Constant identifier columns that don't vary:
- `cftc_CFTC_Contract_Market_Code`: Static contract code
- `cftc_CFTC_Region_Code`: Static region code
- `cftc_CFTC_Commodity_Code`: Static commodity code
- `cftc_Pct_of_Open_Interest_All`: Constant percentage
- `cftc_Pct_of_Open_Interest_Old`: Constant percentage
- `cftc_Pct_of_Open_Interest_Other`: Constant percentage
- `cftc_CFTC_Contract_Market_Code_Quotes`: Quoted version of contract code
- `cftc_CFTC_Commodity_Code_Quotes`: Quoted version of commodity code
- *(Additional 24 CFTC percentage and metadata columns)*

**Action**: Drop these columns before training or mark as `feature_used=False` in feature config.

---

## 3. High-Null Columns (280 columns)

These columns have >50% null values due to limited temporal coverage:

### USDA Data (15 columns)
- **Coverage**: Only years 2000-2025 annual data (1,047 rows mapped to Jan 1 of each year)
- **Null rate**: ~83% (1,047 of 6,380 rows have data)
- **Columns**: All `usda_wasde_*` columns (corn/soybean production, yield, acreage, stocks)
- **Action**: 
  - Impute with forward-fill or annual averages
  - Or train separate models for post-2000 data only

### CFTC Data (195 columns)
- **Coverage**: Only 2020-2025 (261 rows)
- **Null rate**: ~96% (261 of 6,380 rows have data)
- **Columns**: All `cftc_*` positioning columns
- **Action**:
  - Forward-fill for recent predictions
  - Or train regime-specific models for post-2020 data

### Alpha Vantage (Some columns)
- **Coverage**: Varies by symbol (forex, commodities, technicals)
- **Null rate**: Varies, but generally good coverage (100% for most)
- **Action**: Forward-fill or drop low-coverage symbols

### Weather Data (Some columns)
- **Coverage**: Regional/temporal gaps
- **Null rate**: <30% for most
- **Action**: Impute with regional averages or seasonal patterns

---

## 4. Join Keys

These columns are used for merging data, not prediction:

- `date`: Primary temporal key
- `symbol`: Asset identifier (always "ZL=F" for this dataset)
- `timestamp`: Intraday time marker (if present)

**Action**: Exclude from features, but keep for alignment/validation.

---

## 5. Expected Column Name Mismatches (Fixed)

### Previously Expected But Not Found:
- `market_regime` → Now correctly using `regime`
- `weather_us_iowa_prcp_mm` → Now correctly using `weather_us_iowa_PRCP` (NOAA uppercase)

These have been **corrected in `registry/join_spec.yaml`**.

---

## 6. Missing/Skipped Data

### ES Intraday Data
- **Status**: Skipped in Alpha Vantage staging
- **Files**: `es_intraday_1min.parquet`, `es_intraday_5min.parquet`, etc.
- **Action**: Requires separate aggregation strategy to roll intraday into daily features
- **Priority**: Low — daily data already captured

### Manual Data Sources (Not Yet Integrated)
- EPA RIN prices: Requires manual download
- World Bank Pink Sheet: Using alternative API instead
- USDA FAS Export Sales: API authentication needed

---

## Feature Selection Recommendations

### Drop Before Training:
1. All 34 static columns (zero variance)
2. All 2 unprefixed columns (join keys, not features)
3. Join keys (`date`, `symbol`, `timestamp`)

### Impute or Handle:
1. USDA columns (83% null): Forward-fill or annual averages
2. CFTC columns (96% null): Forward-fill or regime-specific models
3. Weather columns (<30% null): Regional/seasonal imputation

### Use for Weighting:
1. `training_weight`: Apply as sample weight in model training
2. `regime`: Use for regime-specific validation splits

---

## Total Feature Count

- **Total columns**: 1,118
- **Join keys**: 2 (`date`, `symbol`)
- **Regime columns**: 2 (`regime`, `training_weight`)
- **Static columns**: 34
- **Usable features**: ~1,080 (after dropping static/join keys)
- **High-quality features**: ~800 (after dropping high-null columns)

---

## Notes

- This document should be updated as new data sources are integrated
- Feature selection should be validated empirically (SHAP, ablation studies)
- Regime-specific models may have different feature availability





