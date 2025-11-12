# Chris & Kevin's Needs - Comprehensive Analysis
**Complete Requirements & Use Cases**

---

## 👤 CHRIS STACY - U.S. Oil Solutions (Primary Client)

### Business Context
- **Company:** U.S. Oil Solutions (Las Vegas)
- **Role:** Procurement decision-maker for soybean oil (ZL futures)
- **Use Case:** Make better timing decisions on when to buy soybean oil contracts
- **Current Baseline:** 7.8% MAPE (needs improvement)

---

## 🎯 CHRIS'S PRIMARY NEEDS

### 1. **PROCUREMENT TIMING SIGNALS** (CRITICAL)

**What Chris Needs:**
- **BUY/WAIT/MONITOR signals** with clear confidence levels
- **Price targets** (current vs. predicted)
- **Timeframe recommendations** (when to execute)
- **Risk assessment** (LOW/MEDIUM/HIGH risk levels)

**Current Implementation:**
- `ProcurementSignal` component in dashboard
- API: `/api/v4/procurement-timing`
- Signals based on:
  - Price momentum (5-day)
  - VIX regime (CRISIS/HIGH_FEAR/ELEVATED/NORMAL/COMPLACENT)
  - Moving averages (20-day MA)
  - Forecast confidence intervals

**Signal Logic:**
- **BUY:** Prices trending up >2%, secure contracts before increases
- **WAIT:** Prices expected to decline >2%, wait for better entry
- **MONITOR:** Stable conditions, watch for opportunities

**Success Criteria:**
- Beat 7.8% MAPE baseline
- Provide actionable signals (not just predictions)
- Clear risk management (confidence intervals)

---

### 2. **CHRIS'S FOUR CRITICAL FACTORS** (Dashboard Priority)

**Identified by Chris as most important for visualization:**

#### Factor 1: **China Purchases/Cancellations** (Medium-term driver)
- **What:** China import volumes, cancellation flags
- **Why:** Negative correlation (-0.813) - when China buys less, prices SURGE
- **Dashboard Display:**
  - Import volume (MT)
  - Status: BOYCOTT ACTIVE / STRONG DEMAND / NORMAL
  - Impact: +/- $X.XX per cwt
  - Timeline: Through Q1 2026 / Ongoing
- **Data Source:** `china_soybean_imports` table
- **Component:** `ChrisFourFactors` (China Demand section)

#### Factor 2: **Harvest Updates** (Short-term volatility driver)
- **What:** Brazil/Argentina/US harvest progress, export capacity
- **Why:** Supply pressure affects short-term price volatility
- **Dashboard Display:**
  - Brazil harvest % complete
  - Argentina tax status (competitive vs. normal)
  - Impact: +/- $X.XX per cwt
  - Description: Supply glut developing / Normal supply
- **Data Source:** `harvest_pace` feature, `argentina_export_tax`
- **Component:** `ChrisFourFactors` (Supply Pressure section)

#### Factor 3: **Biofuel Markets** (Long-term trend driver)
- **What:** EPA RFS mandates, biodiesel demand, RIN prices
- **Why:** Industrial demand creates long-term price support
- **Dashboard Display:**
  - RIN prices (D4, D5, D6)
  - Industrial demand index
  - Impact: +$X.XX per cwt
  - Trend: Growing demand / Stable
- **Data Source:** `rin_d4_price`, `industrial_demand_index`, `biofuel_cascade`
- **Component:** `ChrisFourFactors` (New Uses for Soy Oil section)

#### Factor 4: **Palm Oil Substitution** (Competitive threat)
- **What:** Palm oil spread, substitution risk
- **Why:** When palm oil is cheap, buyers substitute away from soy oil
- **Dashboard Display:**
  - Spread ($/MT premium)
  - Substitution risk: High / Medium / Low
  - Impact: -$X.XX per cwt (if high risk)
  - Assessment: Risk of substitution / Neutral impact
- **Data Source:** `palm_oil_spot_price`, palm spread calculations
- **Component:** `ChrisFourFactors` (Palm Oil Threat section)

**Net Impact Calculation:**
- Sum of all 4 factors
- Display: "BEARISH SHORT-TERM → Wait for lower prices" or "BULLISH → Buy now"

---

### 3. **FORECAST ACCURACY REQUIREMENTS**

**Performance Targets (REALISTIC):**
- **1M Horizon:** MAPE 2-4%, R² 0.75-0.85 (beats 7.8% baseline)
- **3M Horizon:** MAPE 3-6%, R² 0.65-0.80 (beats 7.8% baseline)
- **6M Horizon:** MAPE 4-8%, R² 0.55-0.75 (competitive)
- **12M Horizon:** MAPE 6-12%, R² 0.40-0.65 (industry standard)

**What Success Really Means:**
- ✅ **Better than baseline:** Improve on 7.8% MAPE (even 5-6% is a win)
- ✅ **Actionable for Chris:** Clear signals for procurement decisions
- ✅ **Explainable:** Understand which drivers matter most (feature importance)
- ✅ **Risk-aware:** Confidence intervals (P10/P50/P90) for uncertainty management
- ✅ **Consistent:** Reliable across different market regimes

**Business Value:**
- The goal isn't perfect prediction (impossible in commodity markets)
- The goal is **consistently better decision-making** than gut feel or simple trend analysis
- Even 3-5% MAPE provides institutional-grade insights for procurement timing

---

### 4. **DASHBOARD FEATURES CHRIS NEEDS**

**Current Price & Forecasts:**
- Current ZL price (soybean oil futures)
- 1W, 1M, 3M, 6M, 12M forecasts
- Confidence intervals (P10/P50/P90)
- Predicted change percentage

**Market Intelligence:**
- **Crush Margin** (0.961 correlation - #1 predictor!)
  - Real-time crush spread calculation
  - Trend indicators (↑/↓)
  - Alert when margin is HIGH (buying opportunity)
- **China Demand Tracker** (daily updates)
  - Import volumes
  - Cancellation flags
  - US vs Brazil competition
- **Fed/Dollar Dashboard** (live feeds)
  - DXY index
  - Fed funds rate
  - Real rates (inflation-adjusted)
- **Tariff Threat Level** (33 features!)
  - Trade war intensity
  - Trump policy events
  - Impact scores

**Risk Indicators:**
- VIX levels (market stress)
- Palm oil correlations
- CFTC positioning (smart money flows)

**Translation Layer:**
- Convert institutional signals (UBS/GS style) → business language
- "Market fear creating buying opportunity" instead of "VIX > 25"
- "Supply glut developing" instead of "Harvest pace > 70%"

---

### 5. **DATA REQUIREMENTS FOR CHRIS**

**Must-Have Data Sources:**
1. **Price Data:** Yahoo Finance (224 symbols), CME, Barchart
2. **Economic Indicators:** FRED (Fed funds, employment, inflation, spreads)
3. **Commodity Fundamentals:** USDA WASDE, ERS Oilcrops, export sales
4. **Geopolitical:** Trump policy intelligence, China imports, tariff data
5. **Market Sentiment:** VIX, social sentiment, news intelligence
6. **Biofuel Markets:** RIN prices, RFS mandates, biodiesel/ethanol prices
7. **Weather/Logistics:** Brazil/Argentina weather, freight, port logistics
8. **Technical Indicators:** RSI, MACD, Bollinger Bands (30 indicators × 224 symbols)
9. **Correlations:** Cross-asset correlations (palm oil, crude, corn, wheat)
10. **CFTC Positioning:** Money manager net positions, commercial positioning

**Data Freshness Requirements:**
- **Prices:** < 2 days old
- **Economic data:** < 30 days old
- **News/sentiment:** Daily updates
- **Forecasts:** Daily generation

**Data Quality:**
- No 100% NULL columns
- Cross-validation against Yahoo Finance (<7% difference)
- Corruption detection (impossible values caught)
- Automated freshness monitoring

---

## 👤 KEVIN - Sales/Operations (Secondary User)

### Business Context
- **Company:** U.S. Oil Solutions (Las Vegas)
- **Role:** Sales/operations for casino restaurant customers
- **Use Case:** Event-driven upsell opportunities, customer relationship management
- **Data Source:** Glide App (READ ONLY - 5,628 rows)

---

## 🎯 KEVIN'S PRIMARY NEEDS

### 1. **VEGAS INTEL DASHBOARD** (Event-Driven Sales)

**Purpose:** Identify upsell opportunities at Las Vegas casino restaurants based on:
- Event schedules (conferences, concerts, holidays)
- Restaurant fryer capacity
- Historical consumption patterns
- Customer relationship status

**Current Implementation:**
- Vegas Intel page: `/vegas`
- 5 dashboard components operational
- 5 API routes with real calculations
- Real fryer math from 408 fryers, 151 restaurants

---

### 2. **SALES INTELLIGENCE OVERVIEW**

**What Kevin Needs:**
- **Total customers:** 151 restaurants
- **Revenue potential:** $62,845 (calculated from real fryer data)
- **Top opportunities:** Ranked by potential revenue
- **Customer segmentation:** By fryer count, relationship status

**Data Sources:**
- `vegas_restaurants` (151 restaurants)
- `vegas_fryers` (421 fryers, 408 linked)
- `vegas_casinos` (31 casinos)
- `vegas_export_list` (3,176 service records)

**Component:** `SalesIntelligenceOverview`

---

### 3. **EVENT-DRIVEN UPSELL OPPORTUNITIES**

**What Kevin Needs:**
- **Top 20 opportunities** ranked by revenue potential
- **Event details:** Dates, duration, multiplier
- **Restaurant details:** Name, fryer count, capacity
- **Revenue calculation:** Based on real fryer math

**Fryer Math Formula:**
```
BASE_WEEKLY_GALLONS = (capacity_lbs × 4 TPM) / 7.6 lbs/gal
EVENT_SURGE = BASE_WEEKLY × (event_days / 7) × multiplier
UPSELL_GALLONS = EVENT_SURGE × upsell_%
REVENUE = UPSELL_GALLONS × price/gal
```

**Example (Real Data):**
- Buffet: 8 fryers, 549 lbs capacity → 289 gal/week baseline
- Event surge (3 days, 2.0x): 248 gallons
- Upsell (68%): 169 gallons
- Revenue ($8.20/gal): **$1,384**

**Component:** `EventDrivenUpsell`

**API:** `/api/v4/vegas/upsell-opportunities`

---

### 4. **CUSTOMER RELATIONSHIP MATRIX**

**What Kevin Needs:**
- **Customer scoring:** By fryer count (85/70/50/30 points)
- **Relationship status:** Active, At-Risk, Inactive, Prospect
- **Contact information:** Chef names, emails
- **Delivery schedules:** Daily, certain days

**Scoring System:**
- **85 points:** 8+ fryers (high value)
- **70 points:** 4-7 fryers (medium value)
- **50 points:** 2-3 fryers (low-medium value)
- **30 points:** 1 fryer (low value)

**Component:** `CustomerRelationshipMatrix`

**API:** `/api/v4/vegas/customers`

---

### 5. **EVENT VOLUME MULTIPLIERS**

**What Kevin Needs:**
- **Casino surge forecasts:** 1.3x - 3.4x multipliers
- **Event types:** Conferences, concerts, holidays, sports events
- **Duration:** Default 3 days (Kevin can override)
- **Cuisine multipliers:** Applied per restaurant type

**Cuisine Multipliers (Implemented):**
- **Buffet:** 2.2× (highest - constant frying)
- **Fried Chicken:** 2.0× (primary protein fried)
- **Cajun:** 1.9× (heavy fried seafood)
- **Pool/Club:** 1.8× (wings, tenders, fries)
- **Pub:** 1.7× (wings, fish & chips)
- **Burgers:** 1.6× (burgers + fries)
- **Italian:** 1.5× (calamari, fried apps)
- **Chinese:** 1.4× (stir-fry, spring rolls)
- **Steakhouse:** 1.2× (moderate frying)
- **Sushi:** 0.3× (minimal - tempura only)
- **Bakery:** 0.6× (low - donuts only)

**Component:** `EventVolumeMultipliers`

**API:** `/api/v4/vegas/events`

---

### 6. **MARGIN PROTECTION ALERTS**

**What Kevin Needs:**
- **Volume-based risk alerts:** When customers are at risk
- **Margin calculations:** Revenue - COGS - Delivery - Labor
- **ROI thresholds:** Alert when ROI < 1.0 (not profitable)
- **Price sensitivity:** Alert when ZL cost changes significantly

**Alert Types:**
- **High Volume Risk:** Customer ordering >20% above baseline
- **Margin Compression:** ROI dropping below 1.0
- **Price Spike:** ZL cost increased >5% in 7 days
- **Delivery Cost Risk:** Delivery distance >50 miles

**Component:** `MarginProtectionAlerts`

**API:** `/api/v4/vegas/margin-alerts`

---

### 7. **KEVIN'S OVERRIDE CAPABILITIES**

**What Kevin Can Edit:**
- ✅ **Event duration:** Default 3 days (Kevin can change)
- ✅ **Event multiplier:** Default 2.0x, range: 1.0-3.4x
- ✅ **Upsell %:** Default 68%, range: 40-90%
- ✅ **Price/gal:** Default $8.20 (Kevin can adjust)
- ✅ **Tanker cost:** Default $1,200
- ✅ **Labor cost:** Default $180
- ✅ **Delivery cost:** Default $0.45/gal
- ✅ **TPM (Turns Per Month):** Default 4

**Locked (From Dashboard):**
- 🔒 **ZL Cost:** $7.50/gal (from soybean oil forecast - cannot override)

**Kevin's Workflow:**
1. See AI suggestions (based on real fryer math)
2. Edit any assumption (price, multiplier, upsell %)
3. ROI recalculates live
4. Save scenario if profitable
5. Execute or adjust

**Example Override:**
- AI suggests: Buffet opportunity, ROI 0.96x (NOT PROFITABLE)
- Kevin edits: Price $8.20 → **$9.00**
- ROI: 0.96x → **1.05x** ✅ (NOW PROFITABLE)
- Kevin saves: "Buffet Premium Pricing" → Scenario Library
- Next event: Kevin loads saved scenario → All edits restored

---

### 8. **DATA REQUIREMENTS FOR KEVIN**

**Must-Have Data Sources:**
1. **Glide App Data (READ ONLY):**
   - `vegas_restaurants` (151 restaurants)
   - `vegas_fryers` (421 fryers)
   - `vegas_casinos` (31 casinos)
   - `vegas_export_list` (3,176 service records)
   - `vegas_shifts` (148 shifts)
   - `vegas_shift_casinos` (440 casino shifts)
   - `vegas_shift_restaurants` (1,233 restaurant shifts)
   - `vegas_scheduled_reports` (28 reports)

2. **Event Data:**
   - Conference schedules
   - Concert dates
   - Holiday calendars
   - Sports events

3. **Forecast Data:**
   - ZL cost (soybean oil price) - from Chris's forecast
   - Price trends (for margin calculations)

**Data Freshness Requirements:**
- **Glide data:** Daily sync (READ ONLY)
- **Event data:** Weekly updates
- **Forecast data:** Daily (from Chris's models)

**Critical Constraint:**
- 🚨 **GLIDE IS READ ONLY** - Never write to Glide
- Data flows ONE WAY: Glide → BigQuery → Dashboard
- Query only, never modify Glide under any circumstances

---

## 🎯 SHARED NEEDS (Both Chris & Kevin)

### 1. **DASHBOARD ARCHITECTURE**

**Requirements:**
- **Institutional-grade UI:** Goldman Sachs / JPMorgan standard
- **Real-time updates:** Auto-refresh every 1-5 minutes
- **Mobile responsive:** Works on phone/tablet
- **No fake data:** 100% model-driven, all values from trained models/warehouse

**Current Implementation:**
- Next.js 15.5.6 dashboard
- Vercel deployment
- Real-time API routes
- Institutional gauge components

---

### 2. **DATA QUALITY & RELIABILITY**

**Requirements:**
- **No NULL data:** All features COALESCED with smart defaults
- **Cross-validation:** Prices verified against Yahoo Finance
- **Corruption detection:** Automated guardrails catch impossible values
- **Freshness monitoring:** Alert when data is stale

**Current Status:**
- ✅ All features checked, no 100% NULL columns
- ✅ Cross-validation against Yahoo Finance (<7% difference)
- ✅ Automated freshness monitoring
- ✅ Corruption detection active

---

### 3. **EXPLAINABILITY**

**Requirements:**
- **Feature importance:** Understand which drivers matter most
- **Confidence intervals:** P10/P50/P90 for risk management
- **Reason codes:** Why prices are moving (not just predictions)
- **Translation layer:** Institutional signals → business language

**Current Implementation:**
- Vertex AI feature importance rankings
- Confidence intervals in all forecasts
- Reason codes in procurement signals
- Business language in dashboard components

---

## 📊 SUMMARY: WHAT EACH PERSON NEEDS

### CHRIS (Procurement Decision-Maker)
1. ✅ **BUY/WAIT/MONITOR signals** with confidence levels
2. ✅ **Four Critical Factors** dashboard (China, Harvest, Biofuel, Palm)
3. ✅ **Forecast accuracy** better than 7.8% MAPE baseline
4. ✅ **Price targets** (current vs. predicted)
5. ✅ **Risk management** (confidence intervals, VIX regimes)
6. ✅ **Explainability** (why prices move, feature importance)

### KEVIN (Sales/Operations)
1. ✅ **Event-driven upsell opportunities** (top 20 ranked)
2. ✅ **Customer relationship matrix** (scored by fryer count)
3. ✅ **Revenue calculations** (real fryer math, $62,845 potential)
4. ✅ **Override capabilities** (edit assumptions, save scenarios)
5. ✅ **Margin protection alerts** (ROI thresholds, volume risks)
6. ✅ **Cuisine multipliers** (applied per restaurant type)

### SHARED
1. ✅ **Institutional-grade dashboard** (GS/JPM standard)
2. ✅ **Real-time updates** (auto-refresh)
3. ✅ **Data quality** (no NULLs, cross-validated)
4. ✅ **Explainability** (feature importance, reason codes)

---

## 🚀 CURRENT STATUS

**Chris's Dashboard:**
- ✅ Procurement signals operational
- ✅ Four Critical Factors component live
- ✅ Forecast API routes working
- ✅ Vertex AI models trained (1W, 3M, 6M)

**Kevin's Dashboard:**
- ✅ Vegas Intel page complete
- ✅ 5 components operational
- ✅ 5 API routes with real calculations
- ✅ Real fryer math from 408 fryers
- ✅ Cuisine multipliers implemented

**Next Steps:**
- Train 12M horizon model (for Chris)
- Add more event data sources (for Kevin)
- Improve forecast accuracy (beat 7.8% MAPE)
- Add more explainability features

---

**Last Updated:** November 6, 2025
**Status:** ✅ Both dashboards operational, ready for production use

