# Vegas Intel Page - Sales Page with Tools

## Page Name: "Vegas Intel"
**PAGE TYPE:** SALES PAGE WITH TOOLS
**PURPOSE:** Kevin's revenue playground - Sales intelligence and upsell opportunity identification
**REVENUE MODEL:** Expected upsell only. No hard revenue. Kevin does the math.

**CORE PRINCIPLE:** KEVIN FULL CONTROL
- ALL AI suggestions are editable in real-time
- No historical data? Kevin adds/overrides
- AI provides starting points → Kevin owns the math
- Every field is editable → Live ROI recalculation
- Kevin saves scenarios → Scenario Library

---

## Tone & Language Style (DIRECT TO KEVIN)

**CORE MESSAGE:** Direct, encouraging, profit-focused with attitude. Speak to Kevin like a partner who knows what he's doing.

**Language Examples:**
- "Vegas = Kevin's profit lab. Fryers surge. He sets price. ROI breathes. He wins."
- "Assumptions. Adjustments. Alpha."
- "Stay sharp."
- "Fryers surge. You decide. Profit follows."
- "This is your playground. Make it count."
- "ROI target met? Auto-book. You're in control."
- "High confidence customer. 85% acceptance rate. Pitch it."
- "Event surge detected. Opportunity locked. Your move."

**Tone Guidelines:**
- **Confident:** Assume Kevin knows what he's doing
- **Action-oriented:** Short, punchy statements
- **Direct:** No fluff, straight to the point
- **Encouraging:** "You got this" energy
- **Profit-focused:** Always tie back to ROI, revenue, wins
- **Respectful:** Treat Kevin like an expert, not a beginner

**Where to Use:**
- Page header/motto
- AI suggestion tooltips
- Event forecast cards
- ROI calculation displays
- Confidence meter labels
- Scenario library names
- Tanker scheduler notifications

**Avoid:**
- Long explanations (keep it short)
- Passive language ("you should consider..." → "Do this.")
- Doubt ("might want to..." → "Set this.")
- Corporate speak ("leverage" → "use")
- Apologetic tone (be confident, not tentative)

## Page Header / Motto

**Primary Header Text:**
```
Vegas = Kevin's profit lab.
Fryers surge. He sets price. ROI breathes. He wins.

Assumptions. Adjustments. Alpha.

Stay sharp.
```

**Alternative Header Variations:**
- "Fryers surge. You decide. Profit follows."
- "This is your playground. Make it count."
- "Event surge detected. Opportunity locked. Your move."

---

## KEVIN OVERRIDE MODE - FULLY EDITABLE FIELDS

**PHILOSOPHY:** AI provides starting points. Kevin edits. Math recalculates. Kevin owns the outcome.

**Editable Fields Table:**

| Field | AI Default | Kevin Edit | Locked |
|-------|-----------|-----------|--------|
| Upsell % | 68% | ✅ Editable | 🔒 No |
| Price/gal | $8.20 | ✅ Editable | 🔒 No |
| Delivery Cost | $0.45/gal | ✅ Editable | 🔒 No |
| Company Margin | 18% | ✅ Editable | 🔒 No |
| Tanker Cost | $1,200 | ✅ Editable | 🔒 No |
| Labor Cost | $180 | ✅ Editable | 🔒 No |
| Cuisine Factor | 1.8× | ✅ Editable | 🔒 No |
| Fryer Count | Auto | ✅ Editable | 🔒 No |
| Surge Gallons | Auto | ✅ Editable | 🔒 No |
| ZL Cost | $7.50 | ❌ Locked | 🔒 Yes (from Dashboard) |

**Override Behavior:**
- AI suggests → Kevin edits → Live recalculation → ROI updates instantly
- No historical data? Kevin enters value → System uses Kevin's value
- Kevin saves scenario → Becomes reusable template
- Kevin can reset → Returns to AI defaults

**AI Respects Kevin:**
- "AI suggested 68%. Kevin overrode to 80%. ROI jumps to 3.9x. Saved as 'F1 Aggressive'."
- "No historical upsell data for Nobu. Kevin entered 85%. Using Kevin's value."

---

## Core Components

### 1. Fryer Data Engine (Live Calculation) - KEVIN OVERRIDE MODE
- Total Fryers: 146 (41 active) - **FROM GLIDE API** → [Kevin edit: 152] ✅
- Current Weekly Usage: 9,996 gal - **FROM GLIDE API** → [Kevin edit: 10,200 gal] ✅
- Fryer capacity utilization analysis
- Oil consumption per fryer type (cuisine-based)
- **Scheduling Availability:** When restaurants can receive deliveries - **FROM GLIDE API (Restaurant Groups/Restaurants - scheduling fields)**
- **Delivery Timing:** When upsold oil needs to arrive - **FROM GLIDE API (event-based scheduling requirements)**

**Kevin Can Edit:**
- Fryer count (add/remove fryers, new installations)
- Current usage (override API data)
- Capacity utilization multipliers

### 2. Event Surge Forecast (Next 7 Days) - KEVIN OVERRIDE MODE
- F1 WEEKEND (340% surge example)
  - Expected Gallons Needed: +3,390 gal → [Kevin edit: +3,800 gal] ✅
  - Expected Upsell Opportunity: 68% → [Kevin edit: 80%] ✅
  - Upsell Potential: 2,303 gal → [Kevin edit: 3,040 gal] ✅
- Individual events (Chainsmokers @ Encore, Kaskade @ Marquee, etc.)
  - +14 gal/day per event → [Kevin edit: +18 gal/day] ✅
  - Upsell %: 65-70% → [Kevin edit: 75%] ✅
  - Upsell potential per event → [Auto-recalculates] ✅

**Kevin Can Edit:**
- Expected gallons (override AI forecast)
- Upsell % (override AI suggestion)
- Event multiplier (override AI calculation)

### 3. Kevin's Playground - FULLY EDITABLE PANEL (Collapsible, Live ROI Calculator)

**Scenario Selector:** F1 Weekend, etc. → [Kevin can name scenario: "F1 Aggressive"] ✅

**Inputs (All Editable):**
- Upsell %: 68% → [Kevin edit: 80%] ✅
- Price/gal: $8.20 → [Kevin edit: $8.50] ✅
- Delivery Cost: $0.45/gal → [Kevin edit: $0.38] ✅
- Company Margin: 18% → [Kevin edit: 22%] ✅
- Tanker Cost: $1,200 → [Kevin edit: $1,100] ✅
- Labor Cost: $180 → [Kevin edit: $160] ✅
- ZL Cost: $7.50/gal (locked from Dashboard) 🔒

**Cuisine Oil Intensity Multipliers (Editable):**
- Club / Pool: 1.8× → [Kevin edit: 2.0×] ✅
- Steakhouse: 1.2× → [Kevin edit: 1.3×] ✅
- Bakery: 0.6× → [Kevin edit: 0.5×] ✅
- Dump & Refill: 2.0× → [Kevin edit: 2.2×] ✅
- Italian: 1.5× → [Kevin edit: 1.6×] ✅
- Chinese: 1.4× → [Kevin edit: 1.5×] ✅
- Sushi: 0.3× → [Kevin edit: 0.4×] ✅

**Action Buttons:**
- [SAVE SCENARIO] - Save current settings as named scenario
- [LOAD SCENARIO] - Load saved scenario from library
- [RESET TO AI] - Reset all fields to AI defaults

**Live ROI Calculation (RE-RUNS ON EVERY EDIT):**
```
UPSELL_GALLONS = SURGE_GALLONS × UPSELL_% (Kevin edited)
GROSS_REVENUE = UPSELL_GALLONS × PRICE_PER_GAL (Kevin edited)
COGS = UPSELL_GALLONS × ZL_COST (locked from Dashboard)
DELIVERY_COST = (UPSELL_GALLONS / 3000) × TANKER_COST (Kevin edited) + LABOR (Kevin edited)
NET_PROFIT = GROSS_REVENUE - COGS - DELIVERY_COST
ROI = GROSS_REVENUE / (COGS + DELIVERY_COST)
MARGIN = NET_PROFIT / GROSS_REVENUE × 100
```

**Example Output (After Kevin Override):**
- Kevin edited: 80% upsell, $8.50/gal, $1,100 tanker, $160 labor
- Upsell Gallons: 3,040 gal (Kevin's override)
- Gross Revenue: 3,040 gal × $8.50 = $25,840
- Cost of Goods: 3,040 × $7.50 = $22,800
- Delivery: 1 tanker = $1,100 + $160 = $1,260
- Net Profit: $25,840 - $22,800 - $1,260 = $1,780
- ROI: 3.9x (jumped from 2.8x after Kevin's edits)
- Margin: 6.9% (improved from 1.2%)

**AI Suggestion After Kevin Override:**
- "Kevin override: 80% upsell → ROI 3.9x. Tanker: 1. Saved as 'F1 Aggressive'."

### 4. Event Forecasting Cards (Stacked) - KEVIN EDITS INLINE
- F1 WEEKEND - HIGH IMPACT
  - Expected Gallons: +3,390 → [Kevin edit: +3,800] ✅
  - Upsell: 68% → [Kevin edit: 80%] ✅
  - Upsell Potential: 2,303 gal → [Auto-updates to 3,040 gal] ✅
  - AI: "Kevin override: 80% upsell → ROI 3.9x. Tanker: 1."
- Encore Beach Club - Chainsmokers
  - +14 gal/day → [Kevin edit: +18 gal/day] ✅
  - Upsell: 70% → [Kevin edit: 75%] ✅
  - Upsell: 9.8 gal → [Auto-updates] ✅
  - AI: "3 fryers. Club cuisine. Premium delivery. Kevin: 75% upsell."

### 5. Strip Map: Fryer + Upsell Heat - PIN-LEVEL EDITS

**Map Design Guide:**
- Use attached map image as style/design reference
- Visual style: Clean, modern, heat-based color coding
- Pin clusters for restaurant density
- Heat overlay for upsell potential intensity

**Pin Features (All Editable):**
- Pin: Nobu - Paris
  - 3 fryers → [Kevin edit: +1 fryer (new install)] ✅
  - Surge: +1,836 lb → [Kevin edit: +2,200 lb] ✅
  - Upsell: 72% → [Kevin edit: 85%] ✅
  - ROI: 3.1x → [Kevin sees 4.2x after edit] ✅
  - AI PIN: "Kevin added fryer → +$1,800/month. Approve?"
- Pin: Serrano Vista Cafe
  - 2 fryers → Archived → Upsell: 0%
  - [Kevin can reactivate if needed] ✅

**Map AI Overlay:**
- "Top 5 upsell pins: 1,800 gal potential. ROI 2.9x avg."
- "Kevin edited 3 pins. New aggregate: 2,100 gal. ROI 3.4x."

**Map Interactions:**
- Click pin → Edit panel opens
- Edit inline → Live ROI update
- Heat map updates → Reflects Kevin's edits
- Pin clustering → Groups by upsell potential

---

## AI Suggestions (From Kevin's Inputs)

**Pricing Intelligence (Direct Tone):**
- "$8.20/gal + 68% upsell = ROI 2.8x. Bump to $8.50? ROI 3.4x. One extra tanker. Worth it."
- "ROI target: 2.5x. Current: 2.8x. You're locked. Auto-book ready."

**Upsell Opportunities (Direct Tone):**
- "F1: 2,303 gal upsell. 18% margin = $414 profit. Tanker approved. Go."
- "Event surge: 3,390 gal. Upsell potential: 68%. Your call."

**Event-Based Recommendations (Direct Tone):**
- "3 fryers. Club cuisine. Premium delivery. Pitch it."
- "High-confidence customer. 85% acceptance. Set price. Execute."

---

## Data Sources

### Glide API Integration (8 DATA SOURCES - LOCKED CONFIGURATION)
**Status:** ✅ OPERATIONAL (5,628 rows loaded)  
**Endpoint:** `https://api.glideapp.io/api/function/queryTables`  
**App ID:** `6262JQJdNjhra79M25e4` (NEW - LOCKED)  
**Bearer Token:** `460c9ee4-edcb-43cc-86b5-929e2bb94351` (stored in secrets)  
**Access Level:** Business plan or above required

1. **Restaurants** (`native-table-ojIjQjDcDAEOpdtZG5Ao`) → `vegas_restaurants` (151 rows)
   - Individual restaurant details, location, oil usage patterns
   - **Feeds:** CustomerRelationshipMatrix, EventDrivenUpsell
   - **Key Data:** Restaurant name, location, current usage, delivery schedules

2. **Casinos** (`native-table-Gy2xHsC7urEttrz80hS7`) → `vegas_casinos` (31 rows)
   - Casino-level data for event coordination and high-volume opportunities
   - **Feeds:** EventVolumeMultipliers, SalesIntelligenceOverview
   - **Key Data:** Casino events, restaurant affiliations, premium pricing tolerance

3. **Fryers** (`native-table-r2BIqSLhezVbOKGeRJj8`) → `vegas_fryers` (421 rows)
   - Fryer capacity, oil consumption calculations, baseline demand
   - **Feeds:** ALL components (foundation for volume calculations)
   - **Key Data:** Fryer count, capacity (lb), turns per month, base gallons

4. **Export List** (`native-table-PLujVF4tbbiIi9fzrWg8`) → `vegas_export_list` (3,176 rows)
   - Customer export lists for targeted campaigns, upsell opportunities
   - **Feeds:** EventDrivenUpsell (AI targeting), CustomerRelationshipMatrix
   - **Key Data:** Customer segments, campaign history, acceptance rates

5. **CSV Scheduled Reports** (`native-table-pF4uWe5mpzoeGZbDQhPK`) → `vegas_scheduled_reports` (28 rows)
   - Automated reporting data, historical trends, performance tracking
   - **Feeds:** SalesIntelligenceOverview, MarginProtectionAlerts
   - **Key Data:** Report schedules, trend calculations, alert triggers

6. **Shifts** (`native-table-K53E3SQsgOUB4wdCJdAN`) → `vegas_shifts` (148 rows)
   - Delivery shift scheduling, route optimization, capacity planning
   - **Feeds:** EventDrivenUpsell (delivery timing), logistics planning
   - **Key Data:** Shift times, driver availability, delivery capacity

7. **Shift Casinos** (`native-table-G7cMiuqRgWPhS0ICRRyy`) → `vegas_shift_casinos` (440 rows)
   - Casino-specific shift scheduling for high-priority deliveries
   - **Feeds:** EventVolumeMultipliers (casino event delivery coordination)
   - **Key Data:** Casino shift schedules, premium delivery windows

8. **Shift Restaurants** (`native-table-QgzI2S9pWL584rkOhWBA`) → `vegas_shift_restaurants` (1,233 rows)
   - Restaurant-specific shift scheduling for regular deliveries
   - **Feeds:** CustomerRelationshipMatrix (delivery reliability scoring)
   - **Key Data:** Restaurant shift schedules, preferred delivery windows

**Data Flow Architecture:**
```
Glide API (8 sources) 
  → Python Ingestion Script (ingest_glide_vegas_data.py)
  → BigQuery (8 tables: vegas_*)
  → Dashboard API Routes (/api/v4/vegas/*)
  → React Components (5 Vegas components)
```

### Dashboard Integration
- ZL Cost: Pulled from Dashboard forecast ($7.50/gal example)
- Forecast data: Used for price impact calculations

### Event Calendar
- Vegas events with attendee projections
- Event type classification
- Event → cuisine type matching

---

## Visual-First Design Philosophy

**CORE PRINCIPLE:** VISUAL DOMINANCE + KEVIN CONTROL
- Charts show AI → Kevin edits inline → Live recalc
- Visual elements are editable (not just display)
- Every chart/tool respects Kevin Override Mode

**Primary Visuals:**
1. Fryer surge timeline chart (main visual) - **Editable surge values**
2. Strip map with heat visualization - **Pin-level edits, map design from attached image**
3. Event forecasting cards (stacked) - **Inline editing**
4. ROI calculator panel (collapsible) - **Kevin's Playground, fully editable**

**Map Design Reference:**
- Use attached map image as style/design guide
- Clean, modern aesthetic
- Heat-based color coding for upsell intensity
- Pin clusters for restaurant density
- Interactive pins → Edit panel on click

**AI Integration:**
- AI suggestions appear as contextual tooltips (starting points only)
- Pricing recommendations overlay on event cards (Kevin can override)
- ROI insights display in assumption panel (updates on every Kevin edit)
- AI respects Kevin's overrides → Shows "Kevin override" messaging

**Language Overlay:**
- All text uses direct, encouraging tone (see Tone & Language Style section)
- Short, punchy statements on visual elements
- Profit-focused messaging throughout
- "You" language (direct address to Kevin)
- "Kevin override" messaging when Kevin edits AI suggestions

---

## AI Reasoning Components (HEAVY AI INTEGRATION)

### 1. Sales Intelligence AI
- Market trend analysis from restaurant sales data
- Price elasticity calculations based on historical sales
- Demand pattern recognition (peak hours, days, seasons)
- Competitive intelligence from restaurant groups
- Revenue impact projections from price changes
- Sales velocity indicators (rapid vs slow-moving inventory)

### 2. Fryer Math AI Engine
- Current fryer usage calculation (baseline demand) - **FROM GLIDE API**
- Fryer capacity utilization analysis - **FROM GLIDE API (fryer count)**
- Oil consumption per fryer type (different cuisines = different consumption rates)
- Peak usage pattern recognition
- Maintenance downtime impact calculations
- Efficiency optimization recommendations
- Usage per fryer type: Italian (high), Chinese (high), American (medium), Sushi (low), etc.
- **Upsell Calculation Formula:**
  ```
  BASE_UPSELL = (fryer_count × avg_gallons_per_fryer_per_week) × event_multiplier
  PAST_USE_ADJUSTMENT = (current_usage / historical_avg_usage) × adjustment_factor
  EVENT_BOOST = event_attendee_count × event_type_multiplier × cuisine_match_multiplier
  TARGETING_BOOST = demographic_match_score × psychographic_match_score
  FINAL_UPSELL = BASE_UPSELL × PAST_USE_ADJUSTMENT × EVENT_BOOST × TARGETING_BOOST
  ```

### 3. Expected Volumes AI
- Event-based volume forecasting (traffic projections → oil demand)
- Historical event volume patterns
- Seasonal volume adjustments
- Day-of-week volume patterns
- Special event volume multipliers
- Cumulative volume projections (multiple concurrent events)
- Attendee count → oil consumption correlation

### 4. Event Type Intelligence AI
- Event type classification (conventions, concerts, sports, festivals, trade shows, etc.)
- Event type → cuisine type matching:
  - Italian food festival → High fryer usage → High oil demand
  - Sushi convention → Low fryer usage → Low oil demand
  - Fast food expo → Very high fryer usage → Very high oil demand
- Attendee count → oil demand correlation
- Event duration impact (3-day convention vs 1-day concert)
- Event location impact (strip vs downtown = different restaurant mix)
- Event demographic profile → consumption pattern prediction

### 5. Demographics AI Analysis
- Age group analysis (younger demographics = more fried food consumption)
- Income level impact (affluent = different cuisine preferences, less fried food)
- Geographic origin (domestic vs international visitors = different dining patterns)
- Group size patterns (families vs singles vs business groups)
- Stay duration impact (weekend vs week-long stays = different consumption rates)
- Demographic → fryer usage correlation matrix

### 6. Psychographics AI Analysis
- Lifestyle preferences (health-conscious vs indulgent = different consumption)
- Dining behavior patterns (casual vs fine dining = different fryer usage)
- Price sensitivity indicators (budget-conscious = more fried food)
- Experience-seeking behavior (trying new cuisines = variable fryer usage)
- Social influence factors (group dining decisions)
- Cultural preferences (ethnic cuisine demand patterns)

---

## Integration with Forecasting

**Price Forecast Integration:**
- ZL cost pulled from Dashboard forecast
- Demand surge calculations feed into supply/demand balance
- Price impact from Las Vegas restaurant demand
- Event-driven price volatility predictions

**Multi-Factor Demand Model:**
- Combines: Fryer data + Event types + Demographics + Psychographics
- Generates: Expected oil demand with confidence intervals
- Outputs: Demand-side price pressure indicators
- Updates: Price forecasts with demand-side adjustments

---

## Sidebar Menu Integration

**7-Page Structure:**
1. Dashboard (all business: where it's going & why)
2. **Vegas** (all sales: Kevin's revenue engine) ← THIS PAGE
3. Sentiment (market mood)
4. Legislation (quantified policy & real signal reasoning)
5. Strategy (scenario sliders & what-if reasoning)
6. Trade (geopolitical risk, palm wars, biofuel matrix, rapeseed sub, soy alternatives)
7. Biofuels (mandate pull-through, UCO dynamics, refinery pipeline)

**Sidebar Menu:** One-word titles (Dashboard, Vegas, Sentiment, Legislation, Strategy, Trade, Biofuels)

---

## Implementation Requirements

### Backend
- Glide API integration (Python functions)
- Fryer usage calculations
- Event surge forecasting
- ROI calculation engine
- AI reasoning engine integration

### Frontend
- Fryer surge timeline chart
- Strip map with pins and heat visualization
- Event forecasting cards
- Kevin's Assumption Panel (collapsible)
- Live ROI calculator
- AI suggestion overlays

### Data Flow (Complete Pipeline)

**Glide API Data Extraction:**
1. Restaurant Groups → Scheduling availability, delivery windows
2. Restaurants → Current usage, delivery timing, location, scheduling constraints
3. Fryers → Fryer count, current usage, capacity utilization

**Upsell Calculation Pipeline:**
```
GLIDE API DATA:
├─ Fryer Count (per restaurant)
├─ Current Usage (baseline gallons/week)
├─ Scheduling Availability (when can receive delivery)
├─ Delivery Timing (when needed for event)
└─ Past Usage History (historical consumption patterns)

↓

AI REASONING ENGINE:
├─ Event Type → Cuisine Match → Fryer Usage Multiplier
├─ Demographics → Consumption Pattern → Targeting Boost
├─ Psychographics → Behavior Prediction → Upsell Confidence
└─ Past Use Analysis → Trend Adjustment → Usage Projection

↓

UPSELL CALCULATION:
FINAL_UPSELL = 
  (fryer_count × avg_gallons_per_fryer) × 
  event_multiplier × 
  past_use_adjustment × 
  demographic_boost × 
  psychographic_boost

↓

KEVIN'S ASSUMPTION PANEL:
├─ Apply upsell % slider
├─ Set price/gal
├─ Calculate ROI
└─ Generate AI suggestions

↓

TANKER SCHEDULER:
├─ Check scheduling availability (from Glide API)
├─ Verify delivery timing (when restaurant can receive)
├─ Auto-book if ROI threshold met
└─ Route optimization (multiple restaurants)
```

---

## Key Metrics to Display

**Fryer Metrics:**
- Total fryers (146)
- Active fryers (41)
- Current weekly usage (9,996 gal)
- Capacity utilization %

**Event Metrics:**
- Expected gallons surge (+3,390 gal for F1 example)
- Upsell opportunity % (68% for F1 example)
- Upsell potential (2,303 gal for F1 example)

**ROI Metrics:**
- Gross revenue
- Cost of goods
- Delivery cost
- Net profit
- ROI multiplier
- Margin %

**AI Insights:**
- Pricing recommendations
- Upsell opportunity identification
- Tanker requirements
- Profit projections

---

## CREATIVE SUGGESTIONS - VEGAS SALES ONLY

### 1. Scenario Library (KEVIN SAVES OVERRIDES)
**Purpose:** Kevin saves his overrides as reusable scenarios. AI suggestions are starting points. Kevin owns the final configs.

**Features:**
- Save Kevin's overrides as named scenarios
- Store all Kevin's edits (upsell %, price, costs, cuisine factors, fryer counts)
- Quick-load scenarios from library
- Compare scenarios side-by-side
- Kevin's scenario = Kevin's math = Kevin's wins

**Kevin's Saved Scenarios:**
- **F1 Aggressive** → 80% upsell, $8.50/gal, ROI 3.9x
  - Kevin's override: Bumped upsell from 68% to 80%, price from $8.20 to $8.50
  - Result: ROI jumped from 2.8x to 3.9x
- **F1 Volume Play** → 90% upsell, $7.80/gal, ROI 2.1x
  - Kevin's override: Max volume, lower price, higher upsell %
- **Chainsmokers Safe** → 60% upsell, $8.00/gal
  - Kevin's override: Conservative approach for smaller event

**Scenario Storage:**
- All Kevin's edits saved (not just AI defaults)
- Cuisine factors included
- Fryer count overrides included
- Surge gallon overrides included
- Named by Kevin (e.g., "F1 Aggressive", "Volume Play")

**Use Case:**
- Kevin edits AI suggestions → Creates "F1 Aggressive" → Saves
- Before F1 weekend → Kevin loads "F1 Aggressive" → All his edits restored
- Kevin compares scenarios → Side-by-side ROI comparison
- Kevin wins → Scenario becomes reusable template

**Data Storage:**
- Save to BigQuery: `cbi-v14.predictions_uc1.vegas_scenarios`
- Columns: scenario_name, event_type, upsell_pct, price_per_gal, delivery_cost, company_margin, tanker_cost, labor_cost, cuisine_factors_json, fryer_overrides_json, surge_overrides_json, roi_result, created_at, created_by

### 2. Tanker Scheduler
**Purpose:** Auto-book tankers based on Kevin's ROI target

**Features:**
- Set ROI target threshold (e.g., "Auto-book if ROI > 2.5x")
- Automatic tanker booking when ROI threshold met
- Integration with tanker booking system/API
- Schedule optimization (combine multiple deliveries)
- Tanker capacity planning (3,000 gal per tanker)
- Delivery route optimization
- Cost minimization (reduce empty runs)

**Auto-Booking Logic:**
```
IF (calculated_roi >= kevin_roi_target) THEN
  IF (upsell_gallons >= 3000) THEN
    book_tanker_count = CEIL(upsell_gallons / 3000)
    schedule_delivery(event_date - 1 day)  // Deliver 1 day before event
  END IF
END IF
```

**Kevin's Controls:**
- ROI Target: [slider] 2.5x (minimum ROI to auto-book)
- Auto-book toggle: [checkbox] Enabled/Disabled
- Notification preferences: Email/SMS when tanker auto-booked
- Manual override: Cancel auto-booked tankers

**Use Case:**
- F1 weekend: 2,303 gal upsell, ROI 2.8x → Auto-books 1 tanker (meets 2.5x threshold)
  - **Message:** "ROI 2.8x. Threshold met. Tanker auto-booked. You're locked."
- Chainsmokers event: 9.8 gal upsell, ROI 3.2x → No auto-book (below 3,000 gal minimum)
  - **Message:** "ROI 3.2x. Below 3K gal minimum. Manual review needed."
- Multiple events: Combines deliveries if within same route/timeframe
  - **Message:** "Route optimized. 3 deliveries combined. Cost saved."

**Data Storage:**
- Tanker bookings: `cbi-v14.predictions_uc1.vegas_tanker_schedule`
- Columns: booking_id, event_name, event_date, gallons, tanker_count, delivery_date, route_optimization, auto_booked, kevin_approved, created_at

### 3. Upsell Confidence Meter
**Purpose:** AI predicts upsell % based on customer history

**Features:**
- AI-powered upsell confidence prediction per customer/restaurant
- Historical upsell success rate tracking
- Customer segmentation (high/medium/low confidence)
- Predictive model based on:
  - Past upsell acceptance rates
  - Customer relationship duration
  - Event type history
  - Price sensitivity analysis
  - Payment history (prompt vs delayed)
  - Relationship strength indicators

**Confidence Calculation:**
```
UPSELL_CONFIDENCE = 
  (historical_acceptance_rate × 0.4) +
  (relationship_duration_score × 0.2) +
  (event_type_match_score × 0.2) +
  (price_sensitivity_score × 0.1) +
  (payment_history_score × 0.1)
```

**Visual Display:**
- Confidence meter (gauge chart): 0-100%
- Color coding:
  - Green (70-100%): High confidence - "Locked. Pitch it."
  - Yellow (40-69%): Medium confidence - "Maybe. Adjust price."
  - Red (0-39%): Low confidence - "Skip or deep discount."
- Per-restaurant confidence scores
- Aggregate confidence for event (average of all restaurants)

**Tone on Confidence Meter:**
- High: "85% confidence. History: 12/15 accepted. Premium pricing works. Execute."
- Medium: "60% confidence. History: 6/10 accepted. Price-sensitive. Adjust or skip."
- Low: "25% confidence. History: 2/10 accepted. Price-sensitive. Skip or deep discount."

**AI Reasoning (Direct Tone):**
- "Nobu - Paris: 85% confidence. 12/15 upsells accepted. Premium pricing? They're in."
- "Serrano Vista Cafe: 25% confidence. 2/10 accepted. Price-sensitive. Skip or deep discount."
- "F1 Weekend: 72% aggregate confidence. 15 restaurants, 12 high-confidence. Your move."

**Customer History Tracking:**
- Store in BigQuery: `cbi-v14.predictions_uc1.vegas_customer_history`
- Columns: restaurant_id, restaurant_name, total_upsell_attempts, successful_upsells, acceptance_rate, avg_price_accepted, relationship_start_date, last_upsell_date, customer_segment

**Integration:**
- Pull customer data from Restaurant Groups/Restaurants Glide API
- Match customer ID to historical upsell attempts
- Calculate confidence scores in real-time
- Update confidence meter as Kevin adjusts pricing/scenarios

---

## Complete Upsell Calculation Formula

### Multi-Factor Upsell Calculation

**Data Sources (All from Glide API):**
1. **Fryer Count** (from Fryers table)
2. **Current Usage** (from Restaurants table)
3. **Past Usage** (historical from Restaurants table)
4. **Scheduling Availability** (from Restaurant Groups/Restaurants)
5. **Delivery Timing** (from Restaurants - when needed for event)

**Calculation Formula:**
```
BASE_UPSELL_GALLONS = 
  (fryer_count × avg_gallons_per_fryer_per_week) × 
  event_duration_days / 7

PAST_USE_ADJUSTMENT = 
  IF (current_usage > historical_avg_usage) THEN
    current_usage / historical_avg_usage  // Growing restaurant
  ELSE
    historical_avg_usage / current_usage  // Declining, adjust down
  END IF

EVENT_MULTIPLIER = 
  event_attendee_count × 
  event_type_multiplier × 
  cuisine_match_score ×
  event_duration_multiplier

DEMOGRAPHIC_BOOST = 
  (age_group_consumption_score × 0.3) +
  (income_level_score × 0.2) +
  (geographic_origin_score × 0.2) +
  (group_size_score × 0.15) +
  (stay_duration_score × 0.15)

PSYCHOGRAPHIC_BOOST = 
  (lifestyle_match_score × 0.4) +
  (dining_behavior_score × 0.3) +
  (price_sensitivity_score × 0.2) +
  (cultural_preference_score × 0.1)

TARGETING_SCORE = 
  (demographic_boost × 0.6) +
  (psychographic_boost × 0.4)

FINAL_UPSELL_GALLONS = 
  BASE_UPSELL_GALLONS × 
  PAST_USE_ADJUSTMENT × 
  EVENT_MULTIPLIER × 
  TARGETING_SCORE

DELIVERY_TIMING = 
  event_start_date - delivery_lead_time_days
  (constrained by scheduling_availability from Glide API)
```

**Example Calculation:**
- Restaurant: Nobu - Paris
- Fryer Count: 3 (from Glide API)
- Current Usage: 450 gal/week (from Glide API)
- Past Usage (avg): 420 gal/week (from Glide API)
- Event: F1 Weekend (100,000 attendees, 3 days, Italian cuisine focus)
- Demographics: High-income, international visitors, weekend stays
- Psychographics: Experience-seeking, premium dining, price-insensitive

```
BASE_UPSELL = (3 × 150 gal/week) × (3 days / 7) = 193 gal
PAST_USE_ADJUSTMENT = 450 / 420 = 1.07 (growing restaurant)
EVENT_MULTIPLIER = 100,000 × 0.8 (convention) × 1.2 (Italian cuisine) × 1.5 (3-day) = 144,000
DEMOGRAPHIC_BOOST = (0.9 × 0.3) + (0.8 × 0.2) + (0.7 × 0.2) + (0.6 × 0.15) + (0.8 × 0.15) = 0.78
PSYCHOGRAPHIC_BOOST = (0.85 × 0.4) + (0.9 × 0.3) + (0.7 × 0.2) + (0.8 × 0.1) = 0.82
TARGETING_SCORE = (0.78 × 0.6) + (0.82 × 0.4) = 0.796
FINAL_UPSELL = 193 × 1.07 × (144,000 / 10,000 normalized) × 0.796 = ~2,100 gal
DELIVERY_TIMING = F1_start_date - 1 day (if scheduling available)
```

**Scheduling Integration:**
- Check Glide API for restaurant scheduling availability
- Verify delivery window matches restaurant's availability
- If conflict: Adjust delivery timing or flag for manual review
- Route optimization: Combine deliveries to restaurants with compatible scheduling windows

---

## IDEAS ONLY - SALES VISUALIZATION ENGINE

**⚠️ IMPORTANT: IDEAS ONLY - DO NOT ADD ANYTHING THAT IS NOT POSSIBLE OR REQUIRES HEAVY TOOLING**

**This section contains creative ideas for future enhancements. All ideas must be feasible with existing data sources and lightweight implementation.**

### Event Impact Chart (Primary Visual Idea)

**Concept:** Revenue Opportunity Timeline with Kevin's Intelligence

**Chart Architecture (Data Sources - Existing Only):**
- **Base Revenue Line:** From Glide App integration (Restaurants table - current usage) + historical sales data (if available in BigQuery)
- **Event Spike Overlays:** Las Vegas event calendar (external data source - would need integration) with volume multipliers
- **Forecast Revenue:** Based on fryer TPM × capacity + event timing (calculated from Glide API data)
- **Customer Breakdown:** Color-coded by customer tier and relationship status (from Glide API Restaurant Groups)
- **Margin Visualization:** Line thickness from crush_margin calculations (if available from Dashboard ZL price data)

**Feasibility:**
- ✅ Base Revenue Line: Yes (Glide API data)
- ✅ Customer Breakdown: Yes (Glide API Restaurant Groups)
- ✅ Margin Visualization: Yes (if crush_margin available from Dashboard)
- ⚠️ Event Spike Overlays: Requires LV event calendar integration (external data source)
- ⚠️ Historical Sales: Depends on data availability in BigQuery

### AI-Powered Visual Intelligence (Feature Integration Ideas)

**Opportunity Bubbles:**
- "F1 weekend: event_vol_mult 3.4x = $47,200 opportunity"
- **Data Source:** Calculated from fryer surge × upsell % × price/gal
- **Feasibility:** ✅ Yes (uses existing calculation engine)

**Risk Indicators:**
- "Venetian risk: competitor 8% below from palm_spread advantage"
- **Data Source:** Requires palm_spread data (may not be available)
- **Feasibility:** ⚠️ Depends on palm_spread data availability

**Pipeline Visualization:**
- CRM integration with close probability scoring
- **Data Source:** Would require CRM integration (external tooling)
- **Feasibility:** ❌ Requires heavy tooling - NOT RECOMMENDED

**Territory Heat Map:**
- Geographic analysis with weather_us_midwest_daily impact
- **Data Source:** Weather data (if available from NOAA integration)
- **Feasibility:** ⚠️ Depends on weather data availability

### Kevin's Sales Intelligence (Multi-Source Ideas)

**Event Analysis:**
- "F1 spike coincides with vix_current uptick - margin risk"
- **Data Source:** VIX data (if available from Dashboard/sentiment data)
- **Feasibility:** ⚠️ Depends on VIX data availability

**Customer Psychology:**
- "MGM pattern: 72-hour lead, sensitive above $53 from zl_price_current"
- **Data Source:** Historical customer data from Glide API + ZL price from Dashboard
- **Feasibility:** ✅ Yes (uses existing Glide API + Dashboard ZL price)

**Mathematical Validation:**
- "F1 calculation: 3.4x × 850 base = 2,890 gallons verified"
- **Data Source:** Calculated from existing formula
- **Feasibility:** ✅ Yes (uses existing calculation engine)

### Implementation Priority (Ideas Only)

**HIGH PRIORITY (Easy to Implement):**
1. ✅ Opportunity Bubbles - Uses existing calculation engine
2. ✅ Customer Psychology Patterns - Uses Glide API + Dashboard ZL price
3. ✅ Mathematical Validation - Uses existing formulas

**MEDIUM PRIORITY (Requires Data Integration):**
1. ⚠️ Event Spike Overlays - Requires LV event calendar integration
2. ⚠️ Margin Visualization - Requires crush_margin data from Dashboard
3. ⚠️ Territory Heat Map - Requires weather data integration

**LOW PRIORITY (Requires Heavy Tooling):**
1. ❌ Pipeline Visualization - Requires CRM integration (NOT RECOMMENDED)
2. ❌ Risk Indicators (palm_spread) - Requires palm spread data source

**Notes:**
- All ideas must respect Kevin Override Mode (editable fields)
- All visualizations must follow Visual-First Design Philosophy
- All AI suggestions must use direct tone (see Tone & Language Style section)
- No heavy tooling or external integrations unless explicitly approved

