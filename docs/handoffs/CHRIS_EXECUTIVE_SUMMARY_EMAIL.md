---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Email: CBI-V14 Platform Overview for Chris Stacy

**To:** Chris Stacy, US Oil Solutions  
**From:** CBI-V14 Development Team  
**Subject:** Your Soybean Oil Forecasting Platform - Data, Dashboard & Capabilities Overview  
**Date:** November 7, 2025

---

## Executive Summary

Your institutional-grade soybean oil (ZL) forecasting platform is being built with **125 years of historical data** (1900-2025), **431,740 data points**, and **1,000+ carefully selected features** using Google Vertex AI AutoML.

The platform translates complex commodity intelligence into **actionable procurement signals** across 4 dashboard pages, plus a specialized revenue optimization tool for Kevin's Vegas operations.

---

## The Data Foundation

### Historical Coverage
- **125 years of economic data** (1900-2025) - fundamentals, FX, monetary policy, volatility
- **25+ years of commodity prices** - 224 symbols including ZL, ZS, ZM, palm oil, crude, currencies
- **5+ years of specialized data** - China imports, weather, biofuel mandates, Trump policy intelligence

### Data Categories (1,000 Selected Features)

**Core Drivers:**
- Soybean oil, meal, and whole bean prices (ZL, ZM, ZS)
- Palm oil prices (FCPO - primary substitute)
- Crude oil & energy prices (processing costs)
- Dollar index & currency rates (export competitiveness)

**Supply Fundamentals:**
- USDA crop reports & harvest progress (US, Brazil, Argentina)
- Weather data (precipitation, temperature, growing conditions)
- Crush margins & processing economics
- Port logistics & freight costs

**Demand Signals:**
- China soybean imports & cancellations (60% of global trade)
- Biofuel mandates & RIN prices (46% of US production)
- Restaurant/foodservice demand proxies
- Industrial uses & biodiesel consumption

**Policy & Geopolitical:**
- Trump policy intelligence (tweets, executive orders, announcements)
- China trade relations & tariff data
- Argentina export taxes & policy changes
- EPA biofuel mandates & regulatory updates

**Market Structure:**
- VIX & volatility indicators
- CFTC positioning (money manager flows)
- Social sentiment & news intelligence
- Economic indicators (Fed rates, inflation, employment)

### Intelligent Regime Weighting

The model uses **all 125 years** but emphasizes recent/relevant periods:
- **Trump 2.0 Era (2023-2025):** 50x weight - current market structure
- **Trade War Era (2017-2019):** 15x weight - tariff/China dynamics
- **Recent Crises:** 5-12x weight - volatility patterns
- **Historical Data:** 1x weight - baseline patterns only

This means the model **focuses on Trump-era dynamics** while learning from historical crises.

---

## Your Dashboard (4 Pages)

### Page 1: DASHBOARD (Daily Procurement Decisions)

**Purpose:** Answer "Should I buy today?"

**What You See:**
- **Procurement Signal:** BUY / WAIT / MONITOR with confidence level
- **Price Forecast:** 1-week, 1-month, 3-month, 6-month predictions with confidence bands
- **Four Critical Factors:**
  - China Status (demand/cancellations)
  - Harvest Progress (supply)
  - Biofuel Demand (46% of market)
  - Palm Oil Spread (substitution economics)
- **Risk Indicators:** Volatility forecast, confidence intervals, directional probability

**Refresh:** Daily updates

---

### Page 2: SENTIMENT (Market Mood)

**Purpose:** Understand what's moving the market RIGHT NOW

**What You See:**
- **News Intelligence:** Latest headlines categorized by impact (China, policy, weather, etc.)
- **Social Sentiment:** Trader/analyst mood from Twitter, Reddit, industry forums
- **Trump Policy Tracker:** Recent announcements, tweets, executive orders affecting ag markets
- **Market Positioning:** CFTC money manager positions (are the pros bullish or bearish?)

**Value:** Know if short-term moves are noise or signal

**Refresh:** Hourly updates

---

### Page 3: STRATEGY (Legislative/Policy Intelligence)

**Purpose:** Long-term strategic planning around policy changes

**What You See:**
- **Trump Effect Overlay:** Visual chart showing how Trump decisions/tweets moved ZL prices
- **Legislative Tracker:** 
  - Farm Bill updates
  - RFS mandate changes
  - Trade negotiations
  - Tariff announcements
- **Policy Impact Scores:** Which policies matter most for your procurement
- **China Relations Dashboard:** Import trends, cancellations, trade war status
- **Regulatory Calendar:** Upcoming EPA decisions, USDA reports, Fed meetings

**Value:** Plan 3-12 months ahead around policy catalysts

**Refresh:** Daily policy updates, real-time for major announcements

---

### Page 4: TRADE INTELLIGENCE (Geopolitical Risk)

**Purpose:** Monitor global supply/demand shifts

**What You See:**
- **Global Supply Map:** 
  - Brazil harvest status & export capacity
  - Argentina weather, taxes, port congestion
  - US planting & growing conditions
- **China Deep Dive:**
  - Import commitments vs actuals
  - Cancellation risk indicators
  - Alternative supplier shifts (Brazil vs US)
- **Shipping & Logistics:**
  - Freight rates (Baltic Dry Index)
  - Port congestion
  - Export pace
- **Competitive Dynamics:**
  - Argentina opportunistic exports
  - Brazil premium/discount to US
  - Global crush margin spreads

**Value:** Understand if supply/demand surprises are coming

**Refresh:** Daily for data, weekly for analysis

---

## Vegas Intel Page (For Kevin's Casino Operations)

### Purpose
Help Kevin's sales team identify **which casino customers** are most likely to need soybean oil (for fryers) and **when** they'll need it, turning forecasting intelligence into **revenue opportunities**.

### How It Works

**Step 1: Customer Intelligence (from Glide)**
- Kevin's team tracks ~3,000+ Vegas restaurants/casinos in Glide app
- Data includes: customer relationship status, historical order volumes, last contact date, decision-maker info

**Step 2: Fryer Math Engine**
- Calculates soybean oil needs based on:
  - Restaurant square footage
  - Cuisine type (Italian uses less oil than Asian/fried food)
  - Convention calendar (high traffic = more fryer use)
  - Vegas event calendar (big events = more customers = more oil)

**Step 3: Procurement Timing Prediction**
- Cross-references:
  - Last order date + typical reorder cycle
  - Upcoming Vegas events (conventions, shows, holidays)
  - Seasonal patterns
  - Current inventory estimates

**Step 4: Actionable Sales Alerts**

**What Kevin's Team Sees:**
- **"Hot Leads" List:** Top 20 accounts likely to order in next 2-4 weeks
- **Call Priority Score:** Who to call first
- **Talking Points:** 
  - "Convention season starts in 3 weeks - time to stock up?"
  - "ZL prices forecast to rise 5% next month - lock in now?"
  - "You typically reorder around now based on last year"
- **Revenue Potential:** Estimated order size based on historical patterns

**Example Alert:**
```
🔥 HIGH PRIORITY: Caesars Palace - Italian Restaurant
- Last order: 45 days ago (typical cycle: 50 days)
- Big convention next week (5,000 attendees)
- Forecast: Prices up 4% in 2 weeks
- Suggested action: Call TODAY with price lock offer
- Est. order value: $12,500
```

### The Intelligence Edge

**Normal Sales:** "Hey, do you need oil?"

**Vegas Intel Sales:** "Hi, I see you have the National Restaurateurs Convention next week with 5,000 attendees. Based on your fryer capacity and typical usage, you'll burn through inventory fast. Also, our forecast shows prices increasing 4% in two weeks. Want to lock in current pricing for a larger order now?"

### Integration with Procurement Dashboard

- If ZL forecast shows **price increase coming:** Push customers to order NOW
- If ZL forecast shows **price decrease coming:** Kevin can stock up, offer deals later
- If **supply disruption forecast:** Proactive outreach to lock in supply
- If **China cancellations:** Prices likely to drop, adjust sales strategy

### Result
Turns Kevin's sales team into **consultative advisors** who call customers at exactly the right time with exactly the right message, backed by institutional-grade forecasting intelligence.

---

## Model Performance Targets

**1-Month Forecast:**
- Target: 2-4% MAPE (beats current 7.8% baseline)
- Directional accuracy: 65-70% (better than coin flip)
- Confidence intervals: 80-90% coverage

**3-Month Forecast:**
- Target: 3-6% MAPE
- Strategic planning timeframe

**6-Month Forecast:**
- Target: 4-8% MAPE
- Contract negotiation timeframe

**Business Value:**
Even 3-5% MAPE provides **institutional-grade insights** for procurement timing. The goal isn't perfect prediction—it's **consistently better decisions** than gut feel or simple trend analysis.

---

## What Makes This Institutional-Grade

**Data Depth:**
- 125 years of economic history
- 431,740 data points
- 1,000 carefully selected features (from 9,213 available)

**Advanced AI:**
- Google Vertex AI AutoML (same platform used by Fortune 500)
- Regime-weighted training (emphasizes Trump-era patterns)
- Automatic feature selection & optimization
- Confidence intervals for risk management

**Real-Time Intelligence:**
- Hourly news/sentiment updates
- Daily forecast refresh
- Real-time policy alerts
- Continuous data pipeline

**Procurement-Focused:**
- Translates complex signals into BUY/WAIT/MONITOR
- Clear confidence levels
- Price targets with ranges
- Risk indicators

---

## Timeline

**Week 1-2:** Data consolidation & feature engineering  
**Week 3:** Vertex AI model training (4 horizons)  
**Week 4:** Evaluation, tuning, validation  
**Week 5-6:** Dashboard development & integration  
**Week 7:** Production deployment & testing  
**Week 8:** Live with daily forecasts

---

## Bottom Line

You're getting a **Goldman Sachs/JP Morgan-level commodity forecasting platform** that:
- Uses 125 years of data intelligently weighted for current market conditions
- Tracks 1,000+ market drivers from China imports to Trump tweets
- Provides 4 forecast horizons (1-week to 6-month)
- Translates complex intelligence into simple BUY/WAIT/MONITOR signals
- Updates daily with the latest data
- Includes Vegas revenue optimization for Kevin's team

**The platform turns institutional-grade commodity intelligence into actionable procurement decisions for your business.**

---

**Questions? Let's discuss.**

