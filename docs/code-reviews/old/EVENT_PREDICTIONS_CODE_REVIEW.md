# EVENT PREDICTIONS CODE REVIEW - READ ONLY
## Analysis of `lib/eventPredictions.ts` vs Current Table Structure

### EXECUTIVE SUMMARY
**Status:** Code exists with comprehensive data model, but tables are incomplete
**Finding:** The TypeScript interfaces define the CORRECT data structure - tables need to match this
**Gap:** Current BigQuery tables are missing most fields defined in this code

---

## DATA STRUCTURE COMPARISON

### 1. RESTAURANT Interface (TypeScript)

**TypeScript Definition:**
```typescript
interface Restaurant {
  id: string;
  name: string;
  venue_id: string;           // FK to Venue
  venue_name: string;          // Denormalized for display
  cuisine_type: string;        // CRITICAL for multipliers
  fryer_count: number;         // Number of fryers
  capacity_lbs: number;        // Total capacity in pounds
  oil_type: string;            // Oil type (soybean, canola, etc.)
  active: boolean;             // Active status
}
```

**Current BigQuery Table:** `vegas_restaurants` - **DOES NOT EXIST**
**Required Fields Missing:**
- ❌ restaurant_id (PRIMARY KEY)
- ❌ restaurant_name
- ❌ venue_id (FK to venues/casinos)
- ❌ venue_name
- ❌ cuisine_type (CRITICAL - used in multiplier calculations)
- ❌ fryer_count (aggregated from fryers table)
- ❌ capacity_lbs (aggregated from fryers)
- ❌ oil_type (CRITICAL - different oils have different densities)
- ❌ active status

---

### 2. VENUE Interface (TypeScript)

**TypeScript Definition:**
```typescript
interface Venue {
  id: string;
  name: string;
  group: string;               // Casino group name
  location: string;
  restaurant_count: number;    // Aggregated count
  total_fryers: number;        // Aggregated count
  baseline_visitors: number;   // Daily visitor baseline
  active: boolean;
}
```

**Current BigQuery Table:** `vegas_casinos` - **DOES NOT EXIST**
**Required Fields:**
- ❌ casino_id (PRIMARY KEY)
- ❌ casino_name
- ❌ casino_group (FK or string)
- ❌ location
- ❌ restaurant_count (could be calculated)
- ❌ total_fryers (could be calculated)
- ❌ baseline_visitors (needed for event multiplier calculations)
- ❌ active status

**Note:** Venue = Casino in our model

---

### 3. EVENT Interface (TypeScript)

**TypeScript Definition:**
```typescript
interface Event {
  id: string;
  name: string;
  venue_id: string;           // FK to Venue
  type: string;               // Event type (F1 Race, Convention, etc.)
  start_date: string;
  end_date: string;
  expected_attendance: number;
}
```

**Current BigQuery Table:** `vegas_events` - **EXISTS but INCOMPLETE**
**Current Fields:**
- ✅ event_id
- ✅ event_name
- ✅ event_type
- ✅ event_date (but needs start_date and end_date)
- ✅ location
- ✅ expected_attendance
- ✅ base_daily_traffic
- ✅ cuisine_intensity_factor
- ✅ volume_multiplier
- ✅ event_duration_days
- ✅ revenue_opportunity
- ✅ urgency

**Missing/Incorrect:**
- ❌ venue_id (has location as string, but no venue_id FK)
- ❌ start_date (has event_date - need to verify if this is start or if we need both)
- ❌ end_date (missing - have event_duration_days but not end_date)

---

### 4. EVENT TYPE Definitions (TypeScript)

**TypeScript Definition:**
```typescript
const eventTypeDefinitions: { [key: string]: { 
  attendance: number,      // Attendance multiplier
  oil: number,             // Oil consumption multiplier
  lead: number             // Lead time in days
} } = {
  'F1 Race': { attendance: 3.4, oil: 2.8, lead: 3 },
  'Major Fight': { attendance: 4.1, oil: 3.5, lead: 2 },
  'Convention': { attendance: 1.9, oil: 1.7, lead: 5 },
  // ... etc
}
```

**Current BigQuery Table:** `vegas_event_types` - **DOES NOT EXIST**
**Required:**
- ❌ event_type_id
- ❌ event_type_name
- ❌ attendance_multiplier
- ❌ oil_consumption_multiplier
- ❌ lead_time_days
- ❌ demographic_profile (JSON)

**Impact:** These multipliers are hardcoded in TypeScript - should be in BigQuery for flexibility

---

### 5. CUISINE AFFINITY Mappings (TypeScript)

**TypeScript Definition:**
```typescript
interface CuisineAffinity {
  cuisine_type: string;
  event_types: { [key: string]: number };  // Event type to multiplier
}

const cuisineAffinities: CuisineAffinity[] = [
  {
    cuisine_type: 'steakhouse',
    event_types: {
      'F1 Race': 1.8,
      'Major Fight': 1.6,
      'Convention': 1.0,
      // ... etc
    }
  },
  // ... 11 cuisine types total
]
```

**Current BigQuery Table:** `vegas_cuisine_affinities` - **DOES NOT EXIST**
**Required:**
- ❌ cuisine_type
- ❌ event_type
- ❌ multiplier (FLOAT64)

**Impact:** Restaurant multipliers are hardcoded - should be queryable from BigQuery

---

### 6. CUISINE BASE USAGE (TypeScript)

**TypeScript Definition:**
```typescript
const cuisineBaseUsage: { [key: string]: number } = {
  'fast_food': 15,      // lbs per fryer per week
  'american': 10,
  'steakhouse': 5,
  // ... 16 cuisine types
}
```

**Current BigQuery Table:** `vegas_cuisine_base_usage` - **DOES NOT EXIST**
**Required:**
- ❌ cuisine_type
- ❌ base_usage_lbs_per_fryer_per_week (FLOAT64)

**Impact:** Base usage calculations are hardcoded

---

### 7. DEMOGRAPHIC PROFILE (TypeScript)

**TypeScript Definition:**
```typescript
interface DemographicProfile {
  age_groups: { [key: string]: number };      // e.g. {"18-25": 0.3, "26-40": 0.5}
  gender_ratio_male: number;                  // 0-1 scale
  income_levels: { [key: string]: number };   // e.g. {"high": 0.4, "medium": 0.5}
  cuisine_preferences: { [key: string]: number };
  meal_frequency: number;                     // average meals per day
  spending_profile: string;                   // "luxury", "value", "budget"
}
```

**Current BigQuery Tables:**
- ❌ `vegas_demographic_profiles` - **DOES NOT EXIST**
- ❌ No demographic data in any existing table

**Required:**
- ❌ profile_id (could be linked to restaurant, venue, or event)
- ❌ age_groups (JSON)
- ❌ gender_ratio_male (FLOAT64)
- ❌ income_levels (JSON)
- ❌ cuisine_preferences (JSON)
- ❌ meal_frequency (FLOAT64)
- ❌ spending_profile (STRING)

---

### 8. RECOMMENDATION Interface (TypeScript)

**TypeScript Definition:**
```typescript
interface Recommendation {
  id: string;
  venue_id: string;
  venue_name: string;
  restaurant_id: string;
  restaurant_name: string;
  cuisine_type: string;
  event_id: string;
  event_name: string;
  event_type: string;
  event_start: string;
  event_end: string;
  forecast_id: string;
  forecast_price: number;
  recommended_purchase_date: string;
  days_until_purchase: number;
  normal_weekly_usage: number;
  event_usage: number;
  additional_oil_needed: number;
  restaurant_multiplier: number;
  event_multiplier: number;
  total_multiplier: number;
  estimated_cost: number;
  urgency_level: 'HIGH' | 'MEDIUM' | 'LOW';
  fryer_count: number;
  recommendation: 'BUY' | 'WAIT' | 'MONITOR' | 'LOCK NOW';
  notes: string;
}
```

**Current BigQuery Table:** `vegas_recommendations` - **DOES NOT EXIST**
**Impact:** Recommendations are generated on-the-fly, not stored for historical analysis

---

### 9. FRYER Data (Current vs Required)

**Current `vegas_fryers` Table:**
- ✅ fryer_id
- ✅ restaurant_id (but no restaurant table exists!)
- ✅ fryer_capacity_lb
- ✅ turns_per_month (TPM)
- ✅ base_daily_gallons (calculated)
- ✅ is_active

**Missing (from TypeScript logic):**
- ❌ oil_type (restaurant has it, but fryer should have it too - different fryers can use different oils)
- ❌ cuisine_type (should match restaurant, but can override)
- ❌ fryer_model/type

**Note:** TypeScript aggregates fryer data into restaurant.fryer_count and restaurant.capacity_lbs

---

## CRITICAL BUSINESS LOGIC ANALYSIS

### 1. Multiplier Calculation Chain
```
Event Type → Event Multiplier (from eventTypeDefinitions)
  +
Restaurant Cuisine → Restaurant Multiplier (from cuisineAffinities)
  =
Total Multiplier
```

**Current State:**
- ✅ Event multipliers: Hardcoded in TypeScript
- ✅ Restaurant multipliers: Hardcoded in TypeScript
- ❌ Tables: No lookup tables exist for these multipliers

**Required Tables:**
- `vegas_event_types` (with multipliers)
- `vegas_cuisine_affinities` (cuisine × event_type → multiplier)

---

### 2. Oil Usage Calculation
```
Base Usage (lbs per fryer per week) = cuisineBaseUsage[cuisine_type]
Daily Usage = (fryer_count × base_usage) / 7
Event Usage = daily_usage × event_duration × total_multiplier
Additional Oil = event_usage - (daily_usage × event_duration)
```

**Current State:**
- ✅ Logic: Fully defined in TypeScript
- ❌ Data: cuisineBaseUsage is hardcoded
- ❌ Data: Need restaurant table with cuisine_type and fryer_count

**Required:**
- `vegas_cuisine_base_usage` table
- `vegas_restaurants` table with cuisine_type and aggregated fryer_count

---

### 3. Event-Restaurant Matching
```
For each event:
  Find restaurants where restaurant.venue_id === event.venue_id
  For each matching restaurant:
    Calculate recommendation
```

**Current State:**
- ✅ Logic: Event has venue_id, Restaurant has venue_id
- ❌ Data: No restaurants table exists
- ❌ Data: Events table has location (string) but no venue_id

**Required:**
- `vegas_restaurants` table (CRITICAL)
- `vegas_events` table needs venue_id field
- `vegas_venues`/`vegas_casinos` table

---

## MAPPING: TypeScript Interfaces → BigQuery Tables

### Required Tables (Based on TypeScript Code):

1. **vegas_venues** (or vegas_casinos)
   - Maps to: `Venue` interface
   - Fields: id, name, group, location, restaurant_count, total_fryers, baseline_visitors, active

2. **vegas_restaurants** (CRITICAL - MISSING)
   - Maps to: `Restaurant` interface
   - Fields: id, name, venue_id, venue_name, cuisine_type, fryer_count, capacity_lbs, oil_type, active

3. **vegas_fryers** (EXISTS but incomplete)
   - Current: fryer_id, restaurant_id, fryer_capacity_lb, turns_per_month, base_daily_gallons, is_active
   - Missing: oil_type, cuisine_type (can derive from restaurant)

4. **vegas_events** (EXISTS but needs venue_id)
   - Current: Has location (string) but no venue_id FK
   - Need: venue_id (FK to venues), start_date, end_date

5. **vegas_event_types** (NEW)
   - Maps to: `eventTypeDefinitions` object
   - Fields: event_type_id, event_type_name, attendance_multiplier, oil_consumption_multiplier, lead_time_days

6. **vegas_cuisine_affinities** (NEW)
   - Maps to: `cuisineAffinities` array
   - Fields: cuisine_type, event_type, multiplier

7. **vegas_cuisine_base_usage** (NEW)
   - Maps to: `cuisineBaseUsage` object
   - Fields: cuisine_type, base_usage_lbs_per_fryer_per_week

8. **vegas_demographic_profiles** (NEW)
   - Maps to: `DemographicProfile` interface
   - Fields: profile_id, linked_to (restaurant/venue/event), age_groups (JSON), gender_ratio_male, income_levels (JSON), cuisine_preferences (JSON), meal_frequency, spending_profile

9. **vegas_recommendations** (OPTIONAL - for historical tracking)
   - Maps to: `Recommendation` interface
   - All fields from interface

10. **vegas_forecasts** (EXISTS in predictions dataset)
    - Maps to: `Forecast` interface
    - Should link to recommendations

---

## KEY FINDINGS

### ✅ What the Code Defines (Correct):
1. Complete data model with all required fields
2. Business logic for multipliers and calculations
3. Proper relationships (Restaurant → Venue, Event → Venue)
4. Cuisine-based multipliers (11 cuisine types)
5. Event type multipliers (7 event types)
6. Demographic/psychographic structure (though not fully used in calculations)

### ❌ What's Missing in BigQuery:
1. **vegas_restaurants** table - CRITICAL MISSING PIECE
2. **vegas_venues**/vegas_casinos table
3. **vegas_event_types** lookup table
4. **vegas_cuisine_affinities** lookup table
5. **vegas_cuisine_base_usage** lookup table
6. **vegas_demographic_profiles** table
7. **venue_id** in vegas_events table
8. **start_date** and **end_date** in vegas_events (currently only event_date)

### 🔧 Data Flow Issues:
1. Code expects: `restaurant.venue_id` → `event.venue_id` matching
2. Current: Events have `location` (string), no venue_id
3. Current: No restaurants table exists, so matching impossible

### 💡 Business Logic Insights:
1. **Multiplier Chain:** Event Type → Restaurant Cuisine → Total Multiplier
2. **Oil Calculation:** Base usage per cuisine × fryer count × multipliers
3. **Timing:** Lead time based on event type (2-10 days before event)
4. **Urgency:** Based on days until purchase (≤3 = HIGH, ≤7 = MEDIUM, >7 = LOW)

---

## RECOMMENDATIONS

### Priority 1 (CRITICAL):
1. Create `vegas_restaurants` table with all fields from `Restaurant` interface
2. Create `vegas_venues`/`vegas_casinos` table
3. Add `venue_id` to `vegas_events` table
4. Add `start_date` and `end_date` to `vegas_events` table

### Priority 2 (HIGH):
5. Create `vegas_event_types` lookup table
6. Create `vegas_cuisine_affinities` lookup table
7. Create `vegas_cuisine_base_usage` lookup table
8. Add `oil_type` to `vegas_fryers` table

### Priority 3 (MEDIUM):
9. Create `vegas_demographic_profiles` table
10. Create `vegas_recommendations` table for historical tracking
11. Link recommendations to forecasts from predictions dataset

---

## CONCLUSION

**The TypeScript code is CORRECT and COMPLETE** - it defines the proper data model.
**The BigQuery tables are INCOMPLETE** - they don't match the code's expectations.

**Action Required:** Create tables to match the TypeScript interfaces exactly.
**No changes needed to the TypeScript code** - it's well-structured and correct.


