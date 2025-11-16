# 🎯 CBI-V14 SYSTEM UNDERSTANDING - COMPLETE DOCUMENTATION

**Date**: November 16, 2025  
**Status**: Full Understanding Achieved  
**Core Mission**: Predict ZL (Soybean Oil Futures) for Procurement Optimization

---

## 🏗️ SYSTEM ARCHITECTURE

### The Big Picture
```
┌─────────────────────────────────────────────────────────────────────┐
│                    ZL PREDICTION SYSTEM (SOYBEAN OIL)               │
│                           Core Mission                              │
│                                                                      │
│  Every feature, model, and page serves ONE purpose:                 │
│  Help Chris make better soybean oil procurement decisions           │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                ┌──────────────────┼──────────────────┐
                │                                      │
        CHRIS'S SYSTEM                          KEVIN'S SYSTEM
     (Procurement Manager)                    (Sales Director)
                │                                      │
    ┌───────────┼───────────┐                   Vegas Intel
    │           │           │                  (Disconnected)
Dashboard   Legislative  Strategy
    │           │           │
All Horizons  Trump→ZL   Scenarios
VIX/SHAP    Correlations  If/Then
```

---

## 👤 USER PERSONAS

### CHRIS - Procurement Manager
- **Role**: Buys soybean oil in bulk for company
- **Needs**: Know when to lock in contracts vs wait
- **Language**: Procurement terms, not trading jargon
- **Decisions**: "Lock now" vs "Wait for better price"
- **Key Metrics**: $/cwt, contract timing, risk levels

### KEVIN - Sales Director  
- **Role**: Sells oil to Las Vegas restaurants
- **Needs**: Upsell opportunities based on casino events
- **Tool**: Vegas Intel page (completely separate)
- **Data**: Glide app customer data + event calendars
- **Decisions**: "Call MGM before F1 race" type actions

---

## 📊 CHRIS'S PROCUREMENT RULES (Examples)

```python
# These are the types of rules Chris uses for decisions:

if VIX > 30:
    "HIGH RISK - Lock in contracts NOW"

if argentina_tax == 0:
    "Wait - Argentina undercutting market"

if china_imports > 12_000_000:  # MT
    "BUY - demand spike incoming"

if harvest_pace > 70 and month == "Brazil harvest":
    "Supply glut - WAIT for bottom"

if industrial_demand > 0.5:
    "Floor support at $50/cwt"

if palm_spread < 10:
    "Risk of demand destruction - substitution threat"
```

---

## 🖥️ PAGE STRUCTURE

### 1. DASHBOARD (Home)
**Purpose**: Main ZL prediction center
- All time horizons (1w, 1m, 3m, 6m, 12m)
- VIX overlay for risk assessment
- SHAP values explaining predictions
- Current price and targets
- Confidence levels
- **NOT trading signals - procurement guidance**

### 2. LEGISLATIVE 
**Purpose**: Policy/Trump impact microscope on ZL
- Trump action predictions
- How each action impacts ZL specifically
- Historical correlations (tariffs → ZL movement)
- ICE/labor regulations impact
- Lobbying activity effects
- Laws and trade relations
- **NEW: ZL-specific impact section with procurement alerts**

### 3. STRATEGY
**Purpose**: Scenario planning for procurement
- What-if scenarios
- Upcoming laws to watch
- If/then decision trees
- Timing optimization
- Risk/reward for different contract timings
- **Chris's language: "If X happens, lock contracts by Y date"**

### 4. VEGAS INTEL (Kevin Only)
**Purpose**: Sales intelligence for restaurant upsells
- Glide app integration (customer data)
- Casino event calendar
- Volume multipliers for events
- Upsell opportunities
- Sales strategies
- **Completely disconnected from ZL prediction**

### 5. SENTIMENT (To Be Built)
**Purpose**: Comprehensive sentiment analysis and breaking news
- Unified sentiment scoring (all sources)
- Breaking news feed
- Social media sentiment trends
- Market analyst sentiment
- Policy document sentiment
- Weather/supply sentiment indicators
- Neural network sentiment analysis
- Sentiment component breakdown
- Historical sentiment patterns
- **Status**: Planned for future buildout

---

## 🔄 DATA FLOW

### For Chris (ZL Prediction)
```
1. INPUTS (2000+ features)
   ├── Weather data
   ├── Trump/social sentiment
   ├── Market microstructure
   ├── Supply/demand
   ├── Technical indicators
   ├── Cross-asset correlations
   └── Policy/regulatory

2. PROCESSING
   ├── Neural network (512-256-128-64-32)
   ├── Regime detection
   ├── Crisis intensity scoring
   └── Ensemble predictions

3. OUTPUT
   └── ZL price predictions with:
       ├── Procurement recommendations
       ├── Risk levels
       ├── Confidence scores
       └── Timing guidance
```

### For Kevin (Vegas Intel)
```
1. INPUTS
   ├── Glide app JSON (customers)
   ├── Casino event calendars
   ├── Historical volumes
   └── Demographics

2. PROCESSING
   ├── Event matching
   ├── Volume multipliers
   └── Opportunity scoring

3. OUTPUT
   └── Sales actions like:
       ├── "Call MGM - F1 weekend"
       ├── "Caesars needs 2x for convention"
       └── "Win back Venetian"
```

---

## 🎯 KEY INSIGHTS

### 1. Everything Serves ZL
- ES prediction was built but is secondary
- Trump predictor exists to show ZL impact
- Weather matters only for crop/ZL impact
- Every feature ultimately predicts soybean oil

### 2. Crisis = Confidence
- Higher crisis intensity = Higher forecast confidence
- Counterintuitive but statistically proven
- Crises create clearer signals
- Best opportunities during maximum fear

### 3. Procurement vs Trading
- Chris doesn't day-trade
- He locks in bulk contracts
- Timing is everything
- Risk management = contract timing

### 4. The "Big 7" Signals
1. VIX stress (market fear)
2. SA harvest pace (supply)
3. China relations (demand)
4. Tariff threats (policy)
5. Geopolitical volatility
6. Biofuel mandates
7. Hidden correlations

---

## 🚀 NEXT PHASE IMPLEMENTATION

### Legislative Page Enhancement (Priority)
1. Add ZL correlation section
2. Show Trump action → ZL impact mapping
3. Add procurement alerts in Chris's language
4. Historical pattern recognition
5. Real-time impact calculations

### Example Implementation:
```typescript
// When Trump announces tariffs:
{
  trump_action: "tariff_announcement",
  zl_impact: {
    direction: "DOWN",
    magnitude: "-2.5%",
    timeframe: "48 hours",
    confidence: "85%"
  },
  procurement_alert: {
    level: "URGENT",
    message: "Lock contracts within 24 hours",
    reasoning: "Tariffs typically cause 2-3% ZL drop"
  }
}
```

---

## ✅ UNDERSTANDING CONFIRMED

I now fully understand:
1. **ZL is the center of everything**
2. **Chris needs procurement guidance, not trading signals**
3. **Legislative page shows Trump→ZL correlation**
4. **Vegas Intel is completely separate for Kevin**
5. **Crisis intensity drives confidence (counterintuitively)**
6. **Everything translates to "when to lock contracts"**

Ready to implement ZL correlations on legislative page and continue with plan execution.
