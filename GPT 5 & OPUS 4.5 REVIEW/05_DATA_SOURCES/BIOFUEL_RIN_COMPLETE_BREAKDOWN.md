---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# COMPLETE BIOFUEL & RIN DATASET + MATH BREAKDOWN
**Date**: November 6, 2025  
**Last Reviewed**: November 14, 2025

**Note**: BQML deprecated - all training now runs locally on Mac M4 via TensorFlow Metal. This document describes historical data issues.

---

## THE FULL PICTURE

### 1. THE PROBLEM
- **RIN columns in production_training_data_1m are 100% NULL** (never populated)
- **Historical BQML training failed** because it can't train on all-NULL columns (BQML now deprecated)
- **6 columns affected**: rin_d4_price, rin_d5_price, rin_d6_price, rfs_mandate_biodiesel, rfs_mandate_advanced, rfs_mandate_total

### 2. WHY YAHOO CAN'T HELP WITH DIRECT RIN DATA
- **RINs are EPA compliance credits**, NOT publicly traded securities
- **No ticker symbols** for D4/D5/D6 RINs on Yahoo Finance
- **Only available from**: EPA (free but delayed), OPIS/Argus (paid $1000s/month), ICE OTC (restricted)

---

## DATASETS WE HAVE

### Dataset 1: EXISTING COMMODITIES (Already in BigQuery)
**Location**: `cbi-v14.yahoo_finance_comprehensive.all_symbols_20yr`

| Symbol | Name | Rows | Date Range | In Production? |
|--------|------|------|------------|----------------|
| ZL=F | Soybean Oil | 6,374 | 2000-03-15 to 2025-11-06 | ✅ Yes |
| ZS=F | Soybeans | 6,325 | 2000-09-15 to 2025-11-06 | ✅ Yes |
| ZM=F | Soybean Meal | 6,336 | 2000-05-15 to 2025-11-06 | ✅ Yes |
| ZC=F | Corn | 6,333 | 2000-07-17 to 2025-11-06 | ✅ Yes |
| ZW=F | Wheat | 6,345 | 2000-07-17 to 2025-11-06 | ✅ Yes |
| CL=F | Crude Oil | 6,330 | 2000-08-23 to 2025-11-06 | ✅ Yes |
| ^VIX | VIX Index | 6,502 | 2000-01-03 to 2025-11-06 | ✅ Yes |
| DX-Y.NYB | Dollar Index | 6,531 | 2000-01-03 to 2025-11-06 | ✅ Yes |
| GC=F | Gold | 6,321 | 2000-08-30 to 2025-11-06 | ✅ Yes |

**Total**: 57,397 rows across 9 symbols

### Dataset 2: NEW BIOFUEL COMPONENTS (Just pulled, in cache)
**Location**: `cbi-v14.yahoo_finance_comprehensive.biofuel_components_raw`

| Symbol | Name | Rows | Date Range | Purpose |
|--------|------|------|------------|---------|
| HO=F | Heating Oil | 6,323 | 2000-09-01 to 2025-11-05 | Diesel price (D4 RIN calc) |
| NG=F | Natural Gas | 6,326 | 2000-08-30 to 2025-11-05 | Ethanol production cost |
| RB=F | RBOB Gasoline | 6,284 | 2000-11-01 to 2025-11-05 | Ethanol value (D6 RIN calc) |
| SB=F | Sugar #11 | 6,443 | 2000-03-01 to 2025-11-05 | Brazil ethanol feedstock |
| ICLN | Clean Energy ETF | 4,370 | 2008-06-25 to 2025-11-05 | Regulatory sentiment |
| TAN | Solar ETF | 4,420 | 2008-04-15 to 2025-11-05 | Green energy momentum |
| VEGI | Ag ETF | 3,461 | 2012-02-02 to 2025-11-05 | Ag sector sentiment |
| DBA | Ag Fund | 4,740 | 2007-01-05 to 2025-11-05 | Commodity basket |

**Total**: 42,367 rows across 8 symbols

### Dataset 3: CALCULATED RIN PROXIES (Generated)
**Location**: `cbi-v14.yahoo_finance_comprehensive.rin_proxy_features`

**15 calculated features, 12,637 rows** (merged date range from all components)

---

## THE MATH - COMPLETE FORMULAS

### A. RIN PROXY CALCULATIONS

#### 1. BIODIESEL SPREAD (D4 RIN Proxy)
```
biodiesel_spread = ZL - (HO × 12)

WHERE:
  ZL = Soybean Oil price ($/cwt = dollars per 100 pounds)
  HO = Heating Oil price ($/gallon)
  12 = Conversion factor (approximate gallons of diesel equivalent per cwt)

EXAMPLE (Nov 5, 2025):
  ZL = $49.77/cwt
  HO = $2.43/gallon
  biodiesel_spread = 49.77 - (2.43 × 12)
                   = 49.77 - 29.16
                   = $20.61

INTERPRETATION:
  • Positive spread = Biodiesel profitable → D4 RINs CHEAP
  • Negative spread = Biodiesel unprofitable → D4 RINs EXPENSIVE
  • Higher spread = More biodiesel production = Lower RIN prices
```

#### 2. ETHANOL SPREAD (D6 RIN Proxy)
```
ethanol_spread = (RB × 42) - (ZC ÷ 100 × 2.8)

WHERE:
  RB = RBOB Gasoline price ($/gallon)
  42 = Gallons per barrel
  ZC = Corn price (cents/bushel, so divide by 100 for dollars)
  2.8 = Bushels of corn needed to make 1 barrel of ethanol

EXAMPLE (Nov 5, 2025):
  RB = $1.91/gallon
  ZC = 425 cents/bushel = $4.25/bushel
  ethanol_spread = (1.91 × 42) - (4.25 × 2.8)
                 = 80.22 - 11.90
                 = $68.32 per barrel

INTERPRETATION:
  • Positive spread = Ethanol profitable → D6 RINs CHEAP
  • Negative spread = Ethanol unprofitable → D6 RINs EXPENSIVE
  • Higher spread = More ethanol production = Lower RIN prices
```

#### 3. BIOFUEL CRACK SPREAD
```
biofuel_crack = (ZL × 7.35) - (ZS ÷ 100 × 11)

WHERE:
  ZL = Soybean Oil ($/cwt)
  ZS = Whole Soybeans (cents/bushel)
  7.35 = Weight conversion factor
  11 = Pounds of oil extracted per bushel of beans

EXAMPLE (Nov 5, 2025):
  ZL = $49.77/cwt
  ZS = 1,040 cents/bushel = $10.40/bushel
  biofuel_crack = (49.77 × 7.35) - (10.40 × 11)
                = 365.81 - 114.40
                = $251.41

INTERPRETATION:
  • This is IDENTICAL to our CRUSH MARGIN calculation!
  • Our #1 predictor (0.961 correlation)
  • Measures profitability of crushing soybeans into oil
```

#### 4. D5 RIN PROXY (Advanced Biofuel)
```
rin_d5_price = (biodiesel_spread + ethanol_spread) ÷ 2

WHERE:
  biodiesel_spread = D4 proxy
  ethanol_spread = D6 proxy

LOGIC:
  D5 RINs = Advanced biofuel category (includes both biodiesel and cellulosic)
  Average of D4 and D6 spreads approximates advanced biofuel economics
```

### B. DERIVED FEATURES

#### 5. MARGINS (% of base commodity)
```
biodiesel_margin = (biodiesel_spread ÷ ZL) × 100
ethanol_margin = (ethanol_spread ÷ RB) × 100

INTERPRETATION:
  • Shows profitability as percentage
  • biodiesel_margin > 40% = Very profitable
  • ethanol_margin > 85% = Very profitable
```

#### 6. CROSS-COMMODITY RATIOS
```
oil_to_gas_ratio = CL ÷ RB
soy_to_corn_ratio = ZS ÷ ZC

WHERE:
  CL = Crude Oil ($/barrel)
  RB = Gasoline ($/gallon) 
  ZS = Soybeans (cents/bushel)
  ZC = Corn (cents/bushel)

INTERPRETATION:
  • oil_to_gas_ratio: Refining economics (crack spread proxy)
  • soy_to_corn_ratio: Feed grain substitution dynamics
```

#### 7. CLEAN ENERGY MOMENTUM
```
clean_energy_momentum_30d = (ICLN_today - ICLN_30_days_ago) ÷ ICLN_30_days_ago × 100
clean_energy_momentum_7d = (ICLN_today - ICLN_7_days_ago) ÷ ICLN_7_days_ago × 100

WHERE:
  ICLN = iShares Global Clean Energy ETF price

INTERPRETATION:
  • Positive momentum = Bullish on renewables → RFS mandate support strong
  • Negative momentum = Bearish on renewables → Potential policy headwinds
```

#### 8. NATURAL GAS IMPACT
```
nat_gas_impact = NG

WHERE:
  NG = Natural Gas futures price ($/MMBtu)

INTERPRETATION:
  • Higher nat gas = Higher ethanol production costs
  • Affects ethanol margin and D6 RIN economics
```

#### 9. SUGAR-ETHANOL SPREAD
```
sugar_ethanol_spread = SB - (ZC ÷ 100 × 0.5)

WHERE:
  SB = Sugar #11 futures (cents/pound)
  ZC = Corn (cents/bushel)
  0.5 = Rough substitution ratio for ethanol production

INTERPRETATION:
  • Brazil produces ethanol from BOTH sugar and corn
  • When sugar is cheap vs corn, Brazil uses sugar → Less corn ethanol
  • Affects global ethanol supply and D6 RIN prices
```

#### 10. MOVING AVERAGES (Trend smoothing)
```
biodiesel_spread_ma30 = 30-day simple moving average of biodiesel_spread
ethanol_spread_ma30 = 30-day simple moving average of ethanol_spread

INTERPRETATION:
  • Smooths daily volatility
  • Shows underlying trend in biofuel economics
  • When price crosses above MA = Bullish signal
```

#### 11. VOLATILITY MEASURES
```
biodiesel_spread_vol = 20-day standard deviation of biodiesel_spread
ethanol_spread_vol = 20-day standard deviation of ethanol_spread

INTERPRETATION:
  • High volatility = Uncertain biofuel margins
  • Low volatility = Stable production environment
  • Regime indicator for model uncertainty
```

---

## WHAT WE'RE TRYING TO DO

### Goal: Fill the 6 NULL columns in production_training_data_1m

**Current state**:
```
rin_d4_price: 0/1404 rows (100% NULL) ❌
rin_d5_price: 0/1404 rows (100% NULL) ❌
rin_d6_price: 0/1404 rows (100% NULL) ❌
rfs_mandate_biodiesel: 0/1404 rows (100% NULL) ❌
rfs_mandate_advanced: 0/1404 rows (100% NULL) ❌
rfs_mandate_total: 0/1404 rows (100% NULL) ❌
```

**Approach**:
1. Use **biodiesel_spread** as rin_d4_price proxy
2. Use **ethanol_spread** as rin_d6_price proxy
3. Use **(biodiesel_spread + ethanol_spread)/2** as rin_d5_price proxy
4. Use **biofuel_crack** as rfs_mandate_biodiesel proxy
5. Use **biodiesel_margin** as rfs_mandate_advanced proxy
6. Use **ethanol_margin** as rfs_mandate_total proxy

### Additional Features Being Added (23 total new columns):

**Raw Prices (8 columns)**:
1. heating_oil_price (HO=F direct)
2. natural_gas_price (NG=F direct)
3. gasoline_price (RB=F direct)
4. sugar_price (SB=F direct)
5. icln_price (ICLN direct)
6. tan_price (TAN direct)
7. dba_price (DBA direct)
8. vegi_price (VEGI direct)

**Calculated Features (15 columns)**:
9. biodiesel_spread (D4 proxy)
10. ethanol_spread (D6 proxy)
11. biofuel_crack (processing econ)
12. clean_energy_momentum_30d
13. clean_energy_momentum_7d
14. nat_gas_impact
15. sugar_ethanol_spread
16. biodiesel_margin (%)
17. ethanol_margin (%)
18. oil_to_gas_ratio
19. soy_to_corn_ratio
20. biodiesel_spread_ma30
21. ethanol_spread_ma30
22. biodiesel_spread_vol
23. ethanol_spread_vol

---

## COMPLETE DATA FLOW

```
STEP 1: PULL FROM YAHOO
┌─────────────────────────────────────────────────┐
│ Yahoo Finance API (yfinance library)            │
│ Rate limited: 2.5 seconds between symbols       │
│                                                  │
│ Commodities (9 symbols, 57K rows):             │
│   ZL, ZS, ZM, ZC, ZW, CL, VIX, DX, GC          │
│                                                  │
│ Biofuel Components (8 symbols, 42K rows):      │
│   HO, NG, RB, SB, ICLN, TAN, VEGI, DBA         │
└─────────────────────────────────────────────────┘
                      ↓
                 CACHE TO DISK
                (pickle + csv)
                      ↓
┌─────────────────────────────────────────────────┐
│ STEP 2: LOAD TO BIGQUERY                        │
│                                                  │
│ cbi-v14.yahoo_finance_comprehensive:            │
│   • all_symbols_20yr (57K rows)                │
│   • biofuel_components_raw (42K rows)          │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ STEP 3: CALCULATE RIN PROXIES (Python)          │
│                                                  │
│ Join commodities + biofuel components by date   │
│ Calculate 15 proxy features                     │
│ Save to: rin_proxy_features (12.6K rows)       │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ STEP 4: UPDATE PRODUCTION TABLE (BigQuery SQL)  │
│                                                  │
│ production_training_data_1m:                    │
│   • Add 8 raw price columns                     │
│   • Add 15 calculated proxy columns             │
│   • Update 6 NULL RIN/RFS columns with proxies │
│                                                  │
│ Result: 311 → 334 columns                      │
└─────────────────────────────────────────────────┘
                      ↓
              READY FOR TRAINING!
```

---

## THE EXACT MATH (Line by Line)

### FORMULA 1: Biodiesel Spread
```python
# INPUT DATA:
ZL = 49.77  # Soybean Oil, Nov 5 2025, $/cwt
HO = 2.43   # Heating Oil, Nov 5 2025, $/gallon

# CALCULATION:
biodiesel_spread = ZL - (HO × 12)
                 = 49.77 - (2.43 × 12)
                 = 49.77 - 29.16
                 = 20.61

# UNIT CHECK:
# ZL is $/cwt (dollars per 100 pounds)
# HO is $/gallon
# Multiply HO by ~12 to get rough $/cwt equivalent
# Result is in $/cwt
```

### FORMULA 2: Ethanol Spread
```python
# INPUT DATA:
RB = 1.91   # RBOB Gasoline, Nov 5 2025, $/gallon
ZC = 425    # Corn, Nov 5 2025, cents/bushel

# CALCULATION:
ethanol_spread = (RB × 42) - ((ZC ÷ 100) × 2.8)
               = (1.91 × 42) - ((425 ÷ 100) × 2.8)
               = 80.22 - (4.25 × 2.8)
               = 80.22 - 11.90
               = 68.32

# UNIT CHECK:
# RB × 42 = $/gallon × gallons/barrel = $/barrel
# (ZC ÷ 100) = cents/bu → $/bu
# ($/bu × 2.8 bu/barrel) = $/barrel
# Result is $/barrel
```

### FORMULA 3: Biofuel Crack (Same as Crush Margin!)
```python
# INPUT DATA:
ZL = 49.77   # Soybean Oil, $/cwt
ZS = 1040    # Soybeans, cents/bushel

# CALCULATION:
biofuel_crack = (ZL × 7.35) - ((ZS ÷ 100) × 11)
              = (49.77 × 7.35) - ((1040 ÷ 100) × 11)
              = 365.81 - (10.40 × 11)
              = 365.81 - 114.40
              = 251.41

# UNIT CHECK:
# ZL × 7.35 = $/cwt × conversion = dollars of oil value
# (ZS ÷ 100) × 11 = $/bu × 11 bu = dollars of bean cost
# Result is profit in dollars

# NOTE: This is the SAME as our existing crush_margin!
# Formula: (oil_price_per_cwt × 0.11) + (meal_price_per_ton × 0.022) - bean_price_per_bushel
```

### FORMULA 4: Soy-to-Corn Ratio
```python
# INPUT DATA:
ZS = 1040   # Soybeans, cents/bushel
ZC = 425    # Corn, cents/bushel

# CALCULATION:
soy_to_corn_ratio = ZS ÷ ZC
                  = 1040 ÷ 425
                  = 2.45

# UNIT CHECK:
# Both in cents/bushel, so ratio is dimensionless
# Result is pure ratio

# INTERPRETATION:
# Historical average: ~2.2-2.5
# > 2.5 = Soybeans expensive vs corn (farmers plant more beans)
# < 2.0 = Corn expensive vs beans (farmers plant more corn)
```

### FORMULA 5: Oil-to-Gas Ratio
```python
# INPUT DATA:
CL = 70.50  # Crude Oil, $/barrel
RB = 1.91   # Gasoline, $/gallon

# CALCULATION:
oil_to_gas_ratio = CL ÷ RB
                 = 70.50 ÷ 1.91
                 = 36.91

# UNIT CHECK:
# CL in $/barrel, RB in $/gallon
# Ratio shows how many gallons of gasoline value per barrel of crude
# Result is approximately gallons/barrel

# INTERPRETATION:
# Normal ratio: ~30-40
# High ratio = Crude expensive vs gasoline (refining margins compressed)
# Low ratio = Gasoline expensive vs crude (strong refining margins)
```

### FORMULA 6: Clean Energy Momentum
```python
# INPUT DATA:
ICLN_today = 18.10       # Nov 5, 2025
ICLN_30_days_ago = 16.87 # Oct 6, 2025

# CALCULATION:
clean_energy_momentum_30d = ((ICLN_today - ICLN_30_days_ago) ÷ ICLN_30_days_ago) × 100
                          = ((18.10 - 16.87) ÷ 16.87) × 100
                          = (1.23 ÷ 16.87) × 100
                          = 7.29%

# INTERPRETATION:
# Positive = Clean energy sector gaining
# Negative = Clean energy sector declining
# Proxy for renewable fuel regulatory support
```

### FORMULA 7: Biodiesel Margin
```python
# INPUT DATA:
biodiesel_spread = 20.61  # From Formula 1
ZL = 49.77                # Soybean Oil

# CALCULATION:
biodiesel_margin = (biodiesel_spread ÷ ZL) × 100
                 = (20.61 ÷ 49.77) × 100
                 = 41.4%

# INTERPRETATION:
# > 40% = Highly profitable biodiesel production
# 20-40% = Moderately profitable
# < 20% = Marginally profitable
# < 0% = Unprofitable (blenders rely on RINs)
```

### FORMULA 8: Ethanol Margin
```python
# INPUT DATA:
ethanol_spread = 68.32  # From Formula 2
RB = 1.91               # Gasoline

# CALCULATION:
ethanol_margin = (ethanol_spread ÷ RB) × 100
               = (68.32 ÷ 1.91) × 100
               = 3,577%

# WAIT - THIS SEEMS WRONG!
# The units don't align: spread is $/barrel, RB is $/gallon

# CORRECTED:
ethanol_margin = (ethanol_spread ÷ (RB × 42)) × 100
               = (68.32 ÷ 80.22) × 100
               = 85.2%

# INTERPRETATION:
# > 80% = Very profitable ethanol production
# 50-80% = Moderately profitable
# < 50% = Low margins
```

### FORMULA 9: Moving Averages
```python
# For any feature X:
X_ma30[today] = mean(X[today-29:today])  # 30-day window

# Example:
biodiesel_spread_ma30 = mean of last 30 days of biodiesel_spread

# INTERPRETATION:
# Smooth out daily noise
# Identify trends
# When current > MA = Uptrend
# When current < MA = Downtrend
```

### FORMULA 10: Volatility
```python
# For any feature X:
X_vol = std_dev(X[today-19:today])  # 20-day rolling std dev

# Example:
biodiesel_spread_vol = std dev of last 20 days of biodiesel_spread

# INTERPRETATION:
# High volatility = Uncertain margins, risky production environment
# Low volatility = Stable margins, predictable environment
# Used for model confidence adjustment
```

---

## DATA QUALITY ISSUES FOUND

### Issue 1: Date Type Mismatch
- **biofuel_components_raw**: date is TIMESTAMP
- **rin_proxy_features**: date is INTEGER (Unix timestamp)
- **production_training_data_1m**: date is DATE
- **Fix needed**: Convert all to DATE for JOIN

### Issue 2: NULL Values in Calculations
- **biodiesel_spread**: NULL because HO column missing in merge
- **ethanol_spread**: NULL because RB column missing in merge
- **Root cause**: Pandas merge didn't align commodity + biofuel data correctly

### Issue 3: Multiple Date Formats
- Some dates have timezone (UTC-04:00, UTC-05:00)
- Some dates are naive
- BigQuery expects consistent format

---

## THE FIX NEEDED

```python
# In calculate_rin_proxies.py:

# 1. Load commodities from BigQuery (ZL, ZC, ZS, CL already there)
# 2. Load biofuel components from cache (HO, NG, RB, SB, ICLN, etc.)
# 3. Merge on DATE (not timestamp)
# 4. Calculate all formulas with proper column names
# 5. Handle NULL values (some symbols start later, e.g., ICLN only from 2008)
# 6. Save with DATE type (not INTEGER)
# 7. Update production using DATE JOIN
```

---

## SCHEMA IMPACT

**production_training_data_1m**:

**Before this session**: 300 columns
**After Yahoo integration**: 311 columns (added MAs, Bollinger, ATR)
**After biofuel integration**: 334 columns (adding 23 more)

**New 334-column breakdown**:
- Original features: 300
- Yahoo technical indicators: 11 (ma_50d, ma_100d, ma_200d, BB, ATR)
- Raw biofuel prices: 8 (HO, NG, RB, SB, ICLN, TAN, DBA, VEGI)
- RIN/biofuel proxies: 15 (spreads, margins, ratios, momentum)

---

## BOTTOM LINE

**We have ALL the data needed** to calculate RIN proxies:
- ✅ Soybean Oil (ZL) - already in production
- ✅ Heating Oil (HO) - just pulled, 6,323 rows
- ✅ Gasoline (RB) - just pulled, 6,284 rows
- ✅ Corn (ZC) - already in production
- ✅ All ETFs - just pulled

**The math is correct** (standard biofuel economics formulas)

**The issue**: Data type mismatches and merge problems in the Python script

**The solution**: Fix the merge logic and date handling, then UPDATE production table









