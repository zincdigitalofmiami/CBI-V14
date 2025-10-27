# CRITICAL DATA ACQUISITION PLAN
**For Robust Neural Training & Feature-Rich Dashboard**

## Executive Summary
We have good price data but are MISSING critical fundamental and positioning data that institutional traders use. This limits our model's ability to predict turning points and understand market regime changes.

## TOP 5 IMMEDIATE PRIORITIES

### 1. 📊 CFTC COT POSITIONING DATA
**Impact: HIGH - Shows what smart money is doing**

#### What We Need:
- **500+ weekly reports** (10 years history)
- Managed Money Net Positions
- Producer/Merchant Hedging
- Spreading positions

#### How to Get It:
```python
# Option 1: CFTC.gov API
url = "https://publicreporting.cftc.gov/api/ExportAPI"
# Download legacy COT reports + current

# Option 2: Quandl/Nasdaq Data Link
# Has historical CFTC data cleaned

# Option 3: Manual CSV downloads
# https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm
```

#### Dashboard Features This Enables:
- "Smart Money Positioning" gauge
- Extreme positioning alerts
- Commercial vs Speculator divergence
- Position-based reversal signals

---

### 2. 🌾 USDA WASDE REPORTS
**Impact: HIGH - Fundamental supply/demand driver**

#### What We Need:
- **120+ monthly reports** (10 years)
- US/Global Production estimates
- Ending Stocks
- Yield projections

#### How to Get It:
```python
# Option 1: USDA NASS QuickStats API
api_key = "YOUR_KEY"
base_url = "http://quickstats.nass.usda.gov/api/api_GET/"

# Option 2: Parse WASDE PDFs
# https://www.usda.gov/oce/commodity/wasde/

# Option 3: USDA PSD Online database
# https://apps.fas.usda.gov/psdonline/
```

#### Dashboard Features This Enables:
- Supply/Demand balance tracker
- Stocks-to-use ratio trends
- Yield deviation alerts
- WASDE surprise factor

---

### 3. 🇨🇳 CHINA IMPORT DATA
**Impact: HIGH - 60% of global demand**

#### What We Need:
- **Monthly customs data**
- Soybean/Oil import volumes
- Origin country breakdown
- Crush margins in China

#### How to Get It:
```python
# Option 1: China Customs (GACC) - Chinese only
# http://www.customs.gov.cn/

# Option 2: USDA FAS GATS database
# https://apps.fas.usda.gov/gats/default.aspx

# Option 3: Trade data APIs
# UN Comtrade, TradeMap, or commercial providers
```

#### Dashboard Features This Enables:
- China demand tracker
- Import pace vs seasonal
- Origin switching indicator
- Crush margin arbitrage

---

### 4. 🏭 CRUSH MARGINS & BOARD CRUSH
**Impact: HIGH - Processing economics**

#### What We Need:
- **Daily calculations**
- Soybean - (Meal + Oil) spread
- Regional crush margins
- Capacity utilization

#### How to Get It:
```python
# Calculate from futures:
crush_margin = (
    soybean_meal_price * 0.022 +  # 44 lbs meal per bushel
    soybean_oil_price * 0.11 +    # 11 lbs oil per bushel
    - soybean_price
)

# Or scrape from:
# - CME daily bulletin
# - USDA AMS reports
```

#### Dashboard Features This Enables:
- Crush margin chart
- Demand destruction alerts
- Processing profitability gauge
- Meal vs Oil value driver

---

### 5. 🇧🇷🇦🇷 BRAZIL/ARGENTINA CROP DATA
**Impact: HIGH - 50% of global supply**

#### What We Need:
- **Weekly progress reports**
- Planting/Harvest pace
- Crop conditions
- Export lineups

#### How to Get It:
```python
# Brazil - CONAB reports
# https://www.conab.gov.br/info-agro/safras/graos

# Argentina - Buenos Aires Grain Exchange
# https://www.bolsadecereales.com/

# USDA FAS Crop Progress
# https://ipad.fas.usda.gov/cropexplorer/
```

#### Dashboard Features This Enables:
- South America crop tracker
- Harvest pace vs normal
- Weather impact assessment
- Export competition index

---

## ADDITIONAL HIGH-VALUE DATA

### 6. 💰 RIN PRICES (Biofuel Credits)
- D4 (Biodiesel) and D6 (Ethanol) daily
- Critical for soy oil demand
- Sources: OPIS, Argus, EPA EMTS

### 7. 🚢 VESSEL TRACKING
- Grain vessel lineups at ports
- Export inspections
- Sources: USDA, Vessel tracking APIs

### 8. 📈 OPTIONS DATA
- ZL implied volatility
- Put/Call skew
- Open interest by strike
- Source: CME DataMine

### 9. 💱 FX RATES
- BRL, ARS, CNY daily
- Export competitiveness
- Source: FRED API or XE

### 10. 🌴 PALM OIL FUNDAMENTALS
- MPOB monthly stocks
- Indonesia export tax
- Source: MPOB, Reuters

---

## IMPLEMENTATION PRIORITY

### Phase 1: IMMEDIATE (This Week)
1. **CFTC COT Data** - Historical download + weekly updates
2. **USDA WASDE** - Parse last 24 reports minimum
3. **Crush Margins** - Calculate daily from futures

### Phase 2: QUICK WINS (Next Week)
4. **China Imports** - USDA GATS data
5. **Brazil/Argentina** - USDA FAS reports
6. **FX Rates** - FRED API integration

### Phase 3: ADVANCED (Month 1)
7. **RIN Prices** - Find reliable source
8. **Vessel Tracking** - USDA export inspections
9. **Options Data** - CME settlement data
10. **Palm Oil** - MPOB monthly reports

---

## EXPECTED IMPACT ON MODEL

### With Current Data Only:
- MAPE: 5-7%
- Directional Accuracy: 55-60%
- Can't detect: Positioning extremes, fundamental shifts

### With Priority Data Added:
- MAPE: 2-3% (50% improvement!)
- Directional Accuracy: 70-75%
- Can detect: Reversals, regime changes, supply shocks

### Feature Importance Expected:
1. CFTC Positioning: 25%
2. Crush Margins: 20%
3. China Imports: 15%
4. WASDE Stocks: 15%
5. Weather/Progress: 10%
6. Prices/Technical: 10%
7. Other: 5%

---

## DASHBOARD ENHANCEMENTS

### New Pages/Sections Enabled:
1. **"Smart Money Dashboard"** - CFTC positioning analysis
2. **"Fundamental Scorecard"** - WASDE supply/demand
3. **"China Demand Tracker"** - Import pace and margins
4. **"Crush Economics"** - Processing profitability
5. **"Global Supply Monitor"** - Brazil/Argentina progress

### New Signals/Alerts:
- Extreme positioning reversal alert
- WASDE surprise factor
- China buying acceleration/deceleration
- Crush margin collapse warning
- South America weather shock alert

---

## COST ESTIMATE

### Free Sources:
- CFTC COT data
- USDA WASDE/NASS/FAS
- FRED (FX rates)
- Most government data

### Paid Sources (Optional):
- Commercial data feeds: $500-2000/month
- Vessel tracking: $200-500/month
- Options data: $100-300/month
- News/Reuters: $500-1000/month

### Recommended Approach:
**Start with FREE government sources** - This gets us 80% of the value at zero cost!

---

## NEXT STEPS

1. **Set up CFTC COT data pipeline** (2 hours)
2. **Create WASDE parser** (3 hours)
3. **Build crush margin calculator** (1 hour)
4. **Integrate China import data** (2 hours)
5. **Add Brazil/Argentina progress** (2 hours)

**Total Time: 10 hours for massive improvement!**

---

*This data acquisition will transform our model from "price-based" to "fundamentals-aware" - matching what Goldman Sachs and other institutions use.*
