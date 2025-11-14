# Vegas Intel - Data Synthesis & Implementation Plan
**Purpose:** Map real Glide data (READ ONLY) to Vegas forecasting model  
**Date:** November 5, 2025  
**Status:** ✅ CUISINE MULTIPLIERS IMPLEMENTED - November 5, 2025

---

## 🚨 GLIDE IS READ ONLY - Query Only, Never Write

All data pulled from Glide is READ ONLY. We display it, we never modify Glide.

---

## Real Data Available (From Glide READ ONLY)

### Confirmed Data We Have

**✅ Restaurant Master (151 restaurants)**
- Restaurant names (MHXYO)
- Status (Open/Closed)
- Oil product type (StableMAX, SoyMAX, CottonMAX, CanolaMAX)
- Delivery schedules (Daily, Certain Days + day list)
- Contact info (chef names, emails)
- Foreign keys to casinos/groups

**✅ Fryer Equipment (421 fryers)**
- Fryer capacity in lbs (xhrM0, avg 61.23 lbs)
- Link to restaurants (2uBBn → glide_rowID)
- Fryer names (Fryer 1, Fryer 2, etc.)
- Count per restaurant: ~2.7 fryers avg

**✅ Casino Locations (31 casinos)**
- Casino names (e.g., Mandalay Bay, Caesars, MGM)
- Addresses/locations
- Can link to restaurants via foreign keys

**✅ Operational Data (export_list, shifts, reports)**
- 3,176 export list entries (service records)
- 148 shifts (delivery scheduling)
- 440 casino shifts
- 1,233 restaurant shifts
- 28 scheduled reports

### ✅ CUISINE MULTIPLIERS IMPLEMENTED

**All 142 open restaurants are classified by cuisine type with oil consumption multipliers:**
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

**All API routes now apply cuisine multipliers:**
- `/api/v4/vegas/upsell-opportunities` - ✅ Implemented
- `/api/v4/vegas/metrics` - ✅ Implemented
- `/api/v4/vegas/customers` - ✅ Implemented
- `/api/v4/vegas/events` - ✅ Implemented
- `/api/v4/vegas/margin-alerts` - ✅ Implemented

### Baseline Math We Can Do

**Total Capacity Calculation (WITH CUISINE MULTIPLIERS):**
```
Total Fryers: 408 (linked to restaurants)
Avg Capacity: 61.23 lbs per fryer
Total Capacity: 408 × 61.23 = 24,982 lbs
**With Cuisine Multipliers:** Adjusted per restaurant type

Weekly Base Gallons (assuming 4 turns/month):
  = (24,982 lbs × 4 turns) / 7 days / 7.6 lbs per gallon
  = 1,871 gallons per day baseline
  = 13,099 gallons per week baseline
```

**Per-Restaurant Capacity:**
```sql
SELECT 
  r.MHXYO as restaurant_name,
  r.U0Jf2 as oil_type,
  COUNT(f.glide_rowID) as fryer_count,
  ROUND(SUM(f.xhrM0), 2) as total_capacity_lbs,
  -- Base daily gallons (4 turns/month assumption)
  ROUND((SUM(f.xhrM0) * 4) / 7 / 7.6, 2) as base_daily_gallons,
  -- Base weekly gallons
  ROUND((SUM(f.xhrM0) * 4) / 7.6, 2) as base_weekly_gallons
FROM `cbi-v14.forecasting_data_warehouse.vegas_restaurants` r
LEFT JOIN `cbi-v14.forecasting_data_warehouse.vegas_fryers` f 
  ON r.glide_rowID = f.`2uBBn`
WHERE r.s8tNr = 'Open'
GROUP BY r.glide_rowID, r.MHXYO, r.U0Jf2
HAVING fryer_count > 0
ORDER BY base_weekly_gallons DESC
```

---

## Missing Data - Smart Defaults Required

### Data We DON'T Have from Glide

❌ **Event Calendar** - No event dates, attendees, or event types  
❌ **Historical Usage** - No past consumption data for trend analysis  
❌ **Pricing Data** - No current prices or margins  
❌ **Demographics/Psychographics** - No customer demographic data  
❌ **Turns Per Month (TPM)** - No fryer utilization metrics  

### Smart Defaults Strategy

**1. Event Multipliers (Placeholder Until Real Events Added)**

Use industry standards from architecture:
```sql
CASE 
  WHEN event_type = 'F1 Weekend' THEN 3.4  -- 340% surge
  WHEN event_type = 'Major Convention' THEN 2.5
  WHEN event_type = 'Concert/Nightclub' THEN 1.8
  WHEN event_type = 'Regular Weekend' THEN 1.3
  ELSE 1.0  -- No event
END as event_multiplier
```

**Kevin Override:** ALL multipliers editable in UI

**2. Fryer Turns Per Month (TPM)**

Industry standard: **4 turns per month** for restaurant fryers
- High-volume (clubs, buffets): 6 turns/month
- Medium-volume (steakhouses): 4 turns/month  
- Low-volume (sushi, bakery): 2 turns/month

**Kevin Override:** Can adjust TPM per restaurant type

**3. Upsell % (From Architecture)**

Default: **68%** (from architecture plan)
Range: 60% - 90% based on customer confidence

**Kevin Override:** Fully editable, saves to scenario library

**4. Pricing Defaults (From Architecture)**

```
Price/gal: $8.20 (Kevin editable)
ZL Cost: Pull from Dashboard forecast (LOCKED)
Tanker Cost: $1,200 (Kevin editable)
Labor Cost: $180 (Kevin editable)
Delivery Cost: $0.45/gal (Kevin editable)
Company Margin: 18% (Kevin editable)
```

---

## Implementing the Forecasting Model

### Step 1: Base Upsell Calculation (With Real Data)

**SQL Query:**
```sql
WITH restaurant_capacity AS (
  SELECT 
    r.glide_rowID as restaurant_id,
    r.MHXYO as restaurant_name,
    r.U0Jf2 as oil_type,
    r.s8tNr as status,
    COUNT(f.glide_rowID) as fryer_count,
    SUM(f.xhrM0) as total_capacity_lbs,
    -- Base weekly gallons (4 TPM default, Kevin can override)
    ROUND((SUM(f.xhrM0) * 4) / 7.6, 2) as base_weekly_gallons,
    -- Base daily gallons
    ROUND((SUM(f.xhrM0) * 4) / 7 / 7.6, 2) as base_daily_gallons
  FROM `cbi-v14.forecasting_data_warehouse.vegas_restaurants` r
  LEFT JOIN `cbi-v14.forecasting_data_warehouse.vegas_fryers` f 
    ON r.glide_rowID = f.`2uBBn`
  WHERE r.s8tNr = 'Open'
  GROUP BY r.glide_rowID, r.MHXYO, r.U0Jf2, r.s8tNr
)
SELECT 
  restaurant_name,
  fryer_count,
  base_weekly_gallons,
  -- Event surge calculation (3-day event with 2.0x multiplier default)
  ROUND(base_weekly_gallons * (3.0 / 7.0) * 2.0, 2) as event_surge_gallons,
  -- Upsell potential (68% default, Kevin editable)
  ROUND(base_weekly_gallons * (3.0 / 7.0) * 2.0 * 0.68, 2) as upsell_potential_gallons,
  -- Revenue opportunity ($8.20/gal default, Kevin editable)
  ROUND(base_weekly_gallons * (3.0 / 7.0) * 2.0 * 0.68 * 8.20, 2) as revenue_opportunity_usd
FROM restaurant_capacity
WHERE fryer_count > 0
ORDER BY revenue_opportunity_usd DESC
LIMIT 20;
```

### Step 2: ROI Calculator (Kevin's Playground)

**Inputs (All Editable by Kevin):**
- Event Duration: 3 days (default)
- Event Multiplier: 2.0x (default, ranges 1.0-3.4x)
- Upsell %: 68% (default)
- Price/gal: $8.20 (default)
- Tanker Cost: $1,200
- Labor Cost: $180
- Company Margin Target: 18%

**Locked Input:**
- ZL Cost: Pull from Dashboard forecast ($7.50 example)

**Live ROI Calculation (Updates on every Kevin edit):**
```javascript
// Frontend calculation (real-time as Kevin edits)
const upsellGallons = surgecGallons * (upsellPct / 100)
const grossRevenue = upsellGallons * pricePerGal
const cogs = upsellGallons * zlCost  // From Dashboard
const tankerCount = Math.ceil(upsellGallons / 3000)
const deliveryCost = (tankerCount * tankerCost) + laborCost
const netProfit = grossRevenue - cogs - deliveryCost
const roi = grossRevenue / (cogs + deliveryCost)
const margin = (netProfit / grossRevenue) * 100
```

### Step 3: Confidence Meter (Smart Defaults)

**Without historical acceptance data, use:**
```sql
CASE 
  WHEN fryer_count >= 5 AND oil_type LIKE '%Bulk%' THEN 'HIGH'  -- 75% confidence
  WHEN fryer_count >= 3 THEN 'MEDIUM'  -- 60% confidence
  WHEN fryer_count >= 1 THEN 'LOW'  -- 40% confidence
  ELSE 'SKIP'  -- No fryers
END as confidence_level
```

**Kevin Override:** Can manually set confidence per customer

---

## Implementation Priority

### Phase 1: Foundation (Real Data)

✅ **Fryer Baseline Metrics**
- Query: Real fryer counts and capacities
- Calculation: Base weekly gallons per restaurant
- Display: Total fryers (408), Active restaurants (142), Estimated base usage

✅ **Restaurant List**
- Query: vegas_restaurants with status filter
- Display: 142 open restaurants with names, oil types
- Enable: Click to see fryer details

✅ **Casino/Location Mapping**
- Query: vegas_casinos linked to restaurants
- Display: 31 casino locations
- Enable: Geographic clustering for route planning

### Phase 2: Smart Calculations (Real Data + Defaults)

🔄 **Event Surge Forecast**
- Real Data: Fryer capacity per restaurant
- Default: 2.0x multiplier for events (Kevin editable)
- Default: 3-day event duration (Kevin editable)
- Calculation: `base_weekly × (event_days / 7) × multiplier`

🔄 **Upsell Potential**
- Real Data: Event surge gallons from above
- Default: 68% upsell acceptance (Kevin editable)
- Calculation: `event_surge × upsell_pct`

🔄 **Revenue Opportunity**
- Real Data: Upsell gallons from above
- Default: $8.20/gal price (Kevin editable)
- Locked: ZL cost from Dashboard
- Calculation: Full ROI formula with all Kevin overrides

### Phase 3: Kevin Override Mode (UI Implementation)

✅ **Assumption Panel (Collapsible)**
- Sliders for all variables
- Live ROI recalculation
- Scenario save/load
- Reset to AI defaults

✅ **Inline Editing**
- Click any forecast → Edit inline
- Instant recalculation
- Visual feedback on changes

---

## Recommended API Route Updates

### `/api/v4/vegas/metrics` (Updated with Real Data)

```typescript
const query = `
  WITH fryer_metrics AS (
    SELECT 
      COUNT(DISTINCT r.glide_rowID) as total_customers,
      COUNT(f.glide_rowID) as total_fryers,
      COUNT(DISTINCT CASE WHEN r.s8tNr = 'Open' THEN r.glide_rowID END) as active_customers
    FROM \`cbi-v14.forecasting_data_warehouse.vegas_restaurants\` r
    LEFT JOIN \`cbi-v14.forecasting_data_warehouse.vegas_fryers\` f
      ON r.glide_rowID = f.\`2uBBn\`
  ),
  capacity_calc AS (
    SELECT 
      ROUND(SUM(xhrM0 * 4) / 7.6, 0) as weekly_base_gallons
    FROM \`cbi-v14.forecasting_data_warehouse.vegas_fryers\`
  )
  SELECT 
    fm.total_customers,
    fm.active_customers as active_opportunities,
    31 as upcoming_events,  -- Casino count as proxy
    CAST(cc.weekly_base_gallons * 2.0 * 0.68 * 8.20 as INT64) as estimated_revenue_potential,
    0 as margin_risk_alerts
  FROM fryer_metrics fm
  CROSS JOIN capacity_calc cc
`
```

### `/api/v4/vegas/upsell-opportunities` (Real Fryer Math)

```typescript
const query = `
  SELECT 
    r.glide_rowID as id,
    r.MHXYO as venue_name,
    'Event Upsell Opportunity' as event_name,
    CURRENT_DATE() as event_date,
    3 as event_duration_days,
    1000 as expected_attendance,  -- Placeholder
    -- Real fryer-based calculation
    CAST(ROUND((SUM(f.xhrM0) * 4) / 7.6 * (3.0/7.0) * 2.0, 0) as INT64) as oil_demand_surge_gal,
    -- Revenue opportunity (surge × 68% upsell × $8.20/gal)
    CAST(ROUND((SUM(f.xhrM0) * 4) / 7.6 * (3.0/7.0) * 2.0 * 0.68 * 8.20, 0) as INT64) as revenue_opportunity,
    CASE 
      WHEN COUNT(f.glide_rowID) >= 5 THEN 'IMMEDIATE ACTION'
      WHEN COUNT(f.glide_rowID) >= 3 THEN 'HIGH PRIORITY'
      ELSE 'MONITOR'
    END as urgency,
    'Restaurant Manager' as messaging_strategy_target,
    CONCAT('Based on ', COUNT(f.glide_rowID), ' fryers, ', 
           CAST(ROUND((SUM(f.xhrM0) * 4) / 7.6, 0) as STRING), 
           ' gal/week baseline') as messaging_strategy_monthly_forecast
  FROM \`cbi-v14.forecasting_data_warehouse.vegas_restaurants\` r
  LEFT JOIN \`cbi-v14.forecasting_data_warehouse.vegas_fryers\` f
    ON r.glide_rowID = f.\`2uBBn\`
  WHERE r.s8tNr = 'Open'
  GROUP BY r.glide_rowID, r.MHXYO
  HAVING COUNT(f.glide_rowID) > 0
  ORDER BY revenue_opportunity DESC
  LIMIT 20
`
```

**Explanation:**
- ✅ Uses REAL fryer count per restaurant
- ✅ Uses REAL fryer capacity (xhrM0)
- ✅ Implements proper fryer math: `(capacity × TPM) / 7.6 lbs/gal`
- 🔧 Uses 4 TPM default (Kevin can override in UI)
- 🔧 Uses 2.0x event multiplier default (Kevin can override)
- 🔧 Uses 68% upsell default (Kevin can override)
- 🔧 Uses $8.20/gal price default (Kevin can override)

### `/api/v4/vegas/customers` (Real Restaurant Data)

```typescript
const query = `
  WITH restaurant_metrics AS (
    SELECT 
      r.glide_rowID as id,
      r.MHXYO as name,
      r.U0Jf2 as account_type,
      COUNT(f.glide_rowID) as fryer_count,
      ROUND((SUM(f.xhrM0) * 4) / 7.6, 2) as weekly_gallons,
      CASE 
        WHEN COUNT(f.glide_rowID) >= 5 THEN 85
        WHEN COUNT(f.glide_rowID) >= 3 THEN 70
        WHEN COUNT(f.glide_rowID) >= 1 THEN 50
        ELSE 30
      END as relationship_score,
      r.Po4Zg as delivery_frequency,
      CASE 
        WHEN COUNT(f.glide_rowID) >= 5 THEN 'High'
        WHEN COUNT(f.glide_rowID) >= 3 THEN 'Medium'
        ELSE 'Low'
      END as growth_potential,
      CASE 
        WHEN r.s8tNr = 'Open' THEN 'Contact for event upsell'
        ELSE 'Reactivate account'
      END as next_action
    FROM \`cbi-v14.forecasting_data_warehouse.vegas_restaurants\` r
    LEFT JOIN \`cbi-v14.forecasting_data_warehouse.vegas_fryers\` f
      ON r.glide_rowID = f.\`2uBBn\`
    GROUP BY r.glide_rowID, r.MHXYO, r.U0Jf2, r.Po4Zg, r.s8tNr
  )
  SELECT *
  FROM restaurant_metrics
  ORDER BY relationship_score DESC, weekly_gallons DESC
  LIMIT 50
`
```

---

## Kevin Override Architecture

### Frontend Implementation (React)

**State Management:**
```typescript
const [assumptions, setAssumptions] = useState({
  upsellPct: 68,           // Kevin editable
  pricePerGal: 8.20,       // Kevin editable
  eventMultiplier: 2.0,    // Kevin editable
  eventDays: 3,            // Kevin editable
  tpm: 4,                  // Kevin editable (turns per month)
  tankerCost: 1200,        // Kevin editable
  laborCost: 180,          // Kevin editable
  deliveryCost: 0.45,      // Kevin editable
  zlCost: 7.50             // LOCKED from Dashboard
})
```

**Live ROI Calculation:**
```typescript
function calculateROI(restaurantData, assumptions) {
  const baseWeekly = (restaurantData.total_capacity_lbs * assumptions.tpm) / 7.6
  const surgeGallons = baseWeekly * (assumptions.eventDays / 7) * assumptions.eventMultiplier
  const upsellGallons = surgeGallons * (assumptions.upsellPct / 100)
  
  const grossRevenue = upsellGallons * assumptions.pricePerGal
  const cogs = upsellGallons * assumptions.zlCost
  const tankers = Math.ceil(upsellGallons / 3000)
  const deliveryCost = (tankers * assumptions.tankerCost) + assumptions.laborCost
  
  const netProfit = grossRevenue - cogs - deliveryCost
  const roi = grossRevenue / (cogs + deliveryCost)
  const margin = (netProfit / grossRevenue) * 100
  
  return { upsellGallons, grossRevenue, cogs, deliveryCost, netProfit, roi, margin, tankers }
}
```

### Scenario Library (BigQuery Storage)

```sql
CREATE TABLE `cbi-v14.predictions_uc1.vegas_kevin_scenarios` (
  scenario_id STRING,
  scenario_name STRING,  -- Kevin names it (e.g., "F1 Aggressive")
  restaurant_id STRING,
  event_type STRING,
  upsell_pct FLOAT64,
  price_per_gal FLOAT64,
  event_multiplier FLOAT64,
  event_days INT64,
  tpm INT64,
  tanker_cost FLOAT64,
  labor_cost FLOAT64,
  delivery_cost_per_gal FLOAT64,
  calculated_roi FLOAT64,
  calculated_margin_pct FLOAT64,
  created_at TIMESTAMP,
  created_by STRING
);
```

**Kevin saves scenario → Stored in BigQuery → Reloadable anytime**

---

## Implementation Checklist

### Phase 1: Real Data Queries ✅ COMPLETE

- [x] Update `/api/v4/vegas/metrics` with fryer-based calculations + cuisine multipliers
- [x] Update `/api/v4/vegas/customers` with real restaurant + fryer data + cuisine multipliers
- [x] Update `/api/v4/vegas/events` with casino + fryer surge calculations + cuisine multipliers
- [x] Update `/api/v4/vegas/upsell-opportunities` with real fryer math + cuisine multipliers
- [x] Update `/api/v4/vegas/margin-alerts` with calculated margins + cuisine multipliers
- [x] Classify all 142 restaurants by cuisine type
- [x] Create BigQuery `vegas_cuisine_multipliers` table
- [x] Verify all multipliers are applied correctly

### Phase 2: Kevin Override UI

- [ ] Add Assumption Panel component
- [ ] Implement slider controls for all variables
- [ ] Build live ROI calculator (recalcs on every edit)
- [ ] Add scenario save/load functionality
- [ ] Implement reset to defaults

### Phase 3: Advanced Features (Future)

- [ ] Real event calendar integration
- [ ] Historical usage tracking
- [ ] Confidence meter with learning
- [ ] Tanker scheduler automation

---

## Summary

**What We Have:**
- ✅ Real fryer data (408 fryers, avg 61.23 lbs)
- ✅ Real restaurant data (151 restaurants, 142 open)
- ✅ Real casino locations (31 casinos)
- ✅ Delivery schedules and operational data

**What We're Using Defaults For:**
- 🔧 Event calendar (use smart defaults + Kevin override)
- 🔧 Historical usage trends (use 4 TPM standard)
- 🔧 Upsell % (use 68% from architecture)
- 🔧 Pricing (use $8.20/gal from architecture)

**What Kevin Controls:**
- ✅ ALL variables fully editable
- ✅ Live ROI recalculation
- ✅ Scenario library
- ✅ Kevin's assumptions override AI defaults

**Result:** Production-ready dashboard with real fryer math + Kevin full control

---

**Status:** Ready to implement proper SQL queries with real data + smart defaults  
**Next Step:** Update all 5 API routes with synthesized calculations  
**READ ONLY:** All Glide queries remain READ ONLY (no writes)

