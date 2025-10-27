# CURRENT DATA STATUS - WHAT WE ACTUALLY HAVE

## ✅ DATA WE HAVE (Working)

### Commodity Futures
- **Soybean Oil (ZL)**: 1,935 rows ✅
- **Soybeans**: 543 rows ✅
- **Corn**: 533 rows ✅
- **Wheat**: 577 rows ✅
- **Cotton**: 533 rows ✅
- **Soybean Meal**: Data present ✅

### Energy/Spot Prices
- **Crude Oil**: 2,265 rows (BUT symbol is "CRUDE_OIL_PRICES" not "CL") ⚠️
- **Natural Gas**: 10 rows
- **Palm Oil**: 421 rows
- **Canola Oil**: Data present
- **Rapeseed Oil**: Data present
- **Sunflower Oil**: 1 row

### Financial/Indices
- **VIX**: 508 rows ✅
- **Treasury/10Y Yield**: 288 rows ✅
- **USD Index (DXY)**: 1,022 rows in economic_indicators ✅
- **Gold**: 10 rows
- **Cocoa**: 466 rows

### Macroeconomic (in economic_indicators)
- **Fed Funds Rate**: 1,492 rows ✅
- **10-Year Treasury**: 1,025 rows ✅
- **Dollar Index**: 1,022 rows ✅
- **CPI Inflation**: 76 rows ✅

### Currencies (in currency_data)
- **USD/BRL**: 12,524 rows ✅ (Brazil Real - critical for soy)
- **USD/CNY**: 15,423 rows ✅ (Chinese Yuan - critical for imports)
- **USD/ARS**: 18,507 rows ✅ (Argentine Peso)
- **USD/MYR**: 12,498 rows ✅ (Malaysian Ringgit - palm oil)

### Fundamental/Supply-Demand
- **Brazil Soy Production**: 291 rows ✅
- **Brazil Soy Area**: 291 rows ✅
- **Brazil Soy Yield**: 281 rows ✅
- **China Soy Imports**: 3 rows (LIMITED!)
- **Weather Data**: 13,828 rows ✅

### Intelligence/Sentiment
- **Social Sentiment**: 3,718 rows ✅
- **Trump Policy Intelligence**: 215 rows ✅
- **Biofuel Policy**: 30 rows ✅

## ❌ CRITICAL PROBLEMS

### 1. SCHEMA CHAOS
- **Different date columns**: Some use `date:DATE`, others `time:TIMESTAMP`, others `timestamp:TIMESTAMP`
- **Different price columns**: Some use `close`, others `close_price`
- **This prevents proper joins and causes NaN in correlations!**

### 2. SYMBOL CONTAMINATION
- `crude_oil_prices` has "CRUDE_OIL_PRICES" as symbol instead of "CL"
- Similar issues in other tables
- This breaks symbol-based filtering

### 3. EMPTY CRITICAL TABLES
- **CFTC COT**: 0 rows (positioning data) ❌
- **USDA Export Sales**: 0 rows (demand data) ❌

### 4. MISSING DATA
- **S&P 500**: Not found (needed for risk-on/risk-off) ❌
- **Limited China import data**: Only 3 rows

## 🔧 WHAT NEEDS FIXING

### Immediate Fixes (Blocking Training)
1. Fix correlation view to handle different schemas
2. Fix symbol contamination in crude_oil_prices
3. Populate CFTC COT and USDA export sales from staging
4. Delete duplicate training view (vw_neural_training_dataset_v2_FIXED)

### Data Additions Needed
1. S&P 500 index data
2. More China import data
3. More complete CFTC positioning data

### Training Requirements
- Need to train SEPARATE models for:
  - Commodity futures (price-based)
  - Financial indices (VIX, yields - percentage-based)
  - Fundamentals (volumes, not prices)
  - Currencies (exchange rates)
- Each needs different handling in correlations and features

## 📊 DATA TYPES THAT NEED DIFFERENT HANDLING

1. **FUTURES** (ZL, ZC, ZW) - cents/bushel or cents/lb, need contract months
2. **SPOT PRICES** (crude, palm) - need currency conversion
3. **INDICES** (VIX, DXY) - NOT prices, they're percentages/indices
4. **YIELDS** (Treasury) - Interest rates in %, not commodity prices
5. **FUNDAMENTALS** (CFTC, USDA) - volumes/quantities, NOT prices
6. **SENTIMENT** - scores 0-1, cannot directly correlate with prices
7. **WEATHER** - temperature/precipitation, affects prices but isn't one
8. **CURRENCIES** - Exchange rates, need special correlation handling
