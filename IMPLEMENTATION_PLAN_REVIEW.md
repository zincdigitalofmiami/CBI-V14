# IMPLEMENTATION PLAN REVIEW - READ ONLY
## Comprehensive Review of Proposed Table Structures & Code

### EXECUTIVE SUMMARY
**Status:** Implementation plan is comprehensive and aligns well with audit findings
**Coverage:** Addresses most critical gaps identified in audit
**Issues Found:** Minor schema adjustments needed, some missing fields
**Overall Assessment:** ✅ GOOD - Ready for implementation with minor corrections

---

## TABLE STRUCTURE REVIEW

### 1. vegas_restaurants Table (CRITICAL - MISSING)

**Proposed Schema:**
```sql
CREATE TABLE IF NOT EXISTS `forecasting_data_warehouse.vegas_restaurants` (
  restaurant_id STRING PRIMARY KEY,
  restaurant_name STRING NOT NULL,
  casino_id STRING,
  casino_name STRING,
  casino_group_id STRING,
  casino_group_name STRING,
  location STRING,
  coordinates STRUCT<lat FLOAT64, lng FLOAT64>,
  cuisine_type STRING NOT NULL,
  demographic_profile JSON,
  psychographic_profile JSON,
  scheduling_availability JSON,
  delivery_timing_preferences JSON,
  current_weekly_usage_gallons FLOAT64,
  fryer_count INT64,
  total_oil_capacity_lbs FLOAT64,
  base_daily_usage_gallons FLOAT64,
  active BOOLEAN,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

**✅ Matches TypeScript Interface:** YES
- ✅ restaurant_id → Restaurant.id
- ✅ restaurant_name → Restaurant.name
- ✅ casino_id → Restaurant.venue_id (venue = casino)
- ✅ casino_name → Restaurant.venue_name
- ✅ cuisine_type → Restaurant.cuisine_type
- ✅ fryer_count → Restaurant.fryer_count
- ✅ total_oil_capacity_lbs → Restaurant.capacity_lbs
- ✅ active → Restaurant.active

**⚠️ Missing Fields:**
- ❌ `oil_type` (STRING) - Restaurant interface has this, needed for density calculations
- ❌ `venue_id` (STRING) - Should match TypeScript Restaurant.venue_id exactly
- ❌ Consider adding `venue_name` denormalized (already have casino_name, but for consistency)

**✅ Additional Fields (Good Extras):**
- ✅ demographic_profile JSON (matches plan requirements)
- ✅ psychographic_profile JSON (matches plan requirements)
- ✅ scheduling_availability JSON (from Glide API requirements)
- ✅ delivery_timing_preferences JSON (from Glide API requirements)
- ✅ coordinates STRUCT (for mapping/geospatial queries)

**Assessment:** ✅ GOOD - Add `oil_type` field

---

### 2. vegas_casino_groups Table (NEW)

**Proposed Schema:**
```sql
CREATE TABLE IF NOT EXISTS `forecasting_data_warehouse.vegas_casino_groups` (
  casino_group_id STRING PRIMARY KEY,
  casino_group_name STRING NOT NULL,
  scheduling_availability JSON,
  delivery_preferences JSON,
  demographic_profile JSON,
  psychographic_profile JSON,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

**✅ Matches TypeScript Interface:** PARTIAL
- ✅ casino_group_id → Venue.group (string)
- ✅ casino_group_name → Venue.group (string)
- ✅ Matches plan requirements for Restaurant Groups

**✅ Additional Fields (Good Extras):**
- ✅ scheduling_availability JSON (from Glide API)
- ✅ delivery_preferences JSON (from Glide API)
- ✅ demographic_profile JSON (matches plan)
- ✅ psychographic_profile JSON (matches plan)

**Assessment:** ✅ GOOD - No changes needed

---

### 3. vegas_casinos Table (NEW)

**Proposed Schema:**
```sql
CREATE TABLE IF NOT EXISTS `forecasting_data_warehouse.vegas_casinos` (
  casino_id STRING PRIMARY KEY,
  casino_name STRING NOT NULL,
  casino_group_id STRING,
  location STRING,
  coordinates STRUCT<lat FLOAT64, lng FLOAT64>,
  base_daily_visitors INT64,
  active BOOLEAN,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  FOREIGN KEY (casino_group_id) REFERENCES vegas_casino_groups(casino_group_id)
);
```

**✅ Matches TypeScript Interface:** YES
- ✅ casino_id → Venue.id
- ✅ casino_name → Venue.name
- ✅ casino_group_id → Venue.group (linked via FK)
- ✅ location → Venue.location
- ✅ base_daily_visitors → Venue.baseline_visitors
- ✅ active → Venue.active

**⚠️ Missing Fields:**
- ❌ `restaurant_count` (INT64) - Venue interface has this, could be calculated but useful for denormalization
- ❌ `total_fryers` (INT64) - Venue interface has this, could be calculated but useful for denormalization

**✅ Additional Fields (Good Extras):**
- ✅ coordinates STRUCT (for mapping)
- ✅ FOREIGN KEY constraint (good data integrity)

**Assessment:** ✅ GOOD - Consider adding denormalized counts for performance

---

### 4. vegas_event_restaurants Junction Table (NEW)

**Proposed Schema:**
```sql
CREATE TABLE IF NOT EXISTS `forecasting_data_warehouse.vegas_event_restaurants` (
  event_id STRING,
  restaurant_id STRING,
  expected_impact_gallons FLOAT64,
  total_multiplier FLOAT64,
  restaurant_multiplier FLOAT64,
  event_multiplier FLOAT64,
  upsell_potential_dollars FLOAT64,
  recommendation STRING,
  urgency_level STRING,
  recommended_purchase_date DATE,
  created_at TIMESTAMP,
  PRIMARY KEY (event_id, restaurant_id),
  FOREIGN KEY (event_id) REFERENCES vegas_events(event_id),
  FOREIGN KEY (restaurant_id) REFERENCES vegas_restaurants(restaurant_id)
);
```

**✅ Matches TypeScript Interface:** YES
- ✅ event_id → Recommendation.event_id
- ✅ restaurant_id → Recommendation.restaurant_id
- ✅ expected_impact_gallons → Recommendation.additional_oil_needed (in lbs, but gallons is fine)
- ✅ total_multiplier → Recommendation.total_multiplier
- ✅ restaurant_multiplier → Recommendation.restaurant_multiplier
- ✅ event_multiplier → Recommendation.event_multiplier
- ✅ recommendation → Recommendation.recommendation ('BUY' | 'WAIT' | 'MONITOR' | 'LOCK NOW')
- ✅ urgency_level → Recommendation.urgency_level ('HIGH' | 'MEDIUM' | 'LOW')
- ✅ recommended_purchase_date → Recommendation.recommended_purchase_date

**⚠️ Missing Fields:**
- ❌ `days_until_purchase` (INT64) - Recommendation interface has this
- ❌ `normal_weekly_usage` (FLOAT64) - Recommendation interface has this
- ❌ `event_usage` (FLOAT64) - Recommendation interface has this
- ❌ `estimated_cost` (FLOAT64) - Recommendation interface has this (vs upsell_potential_dollars)
- ❌ `fryer_count` (INT64) - Recommendation interface has this
- ❌ `notes` (STRING) - Recommendation interface has this
- ❌ `forecast_id` (STRING) - Recommendation interface has this
- ❌ `forecast_price` (FLOAT64) - Recommendation interface has this

**Assessment:** ⚠️ INCOMPLETE - Missing many fields from Recommendation interface

---

### 5. vegas_cuisine_affinities Reference Table (NEW)

**Proposed Schema:**
```sql
CREATE TABLE IF NOT EXISTS `forecasting_data_warehouse.vegas_cuisine_affinities` (
  cuisine_type STRING,
  event_type STRING,
  affinity_multiplier FLOAT64,
  description STRING,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  PRIMARY KEY (cuisine_type, event_type)
);
```

**✅ Matches TypeScript Code:** YES
- ✅ Maps directly to `cuisineAffinities` array in TypeScript
- ✅ cuisine_type → CuisineAffinity.cuisine_type
- ✅ event_type → key in CuisineAffinity.event_types
- ✅ affinity_multiplier → value in CuisineAffinity.event_types

**✅ Additional Fields (Good Extras):**
- ✅ description (for documentation)
- ✅ PRIMARY KEY on (cuisine_type, event_type) - correct

**Assessment:** ✅ PERFECT - No changes needed

---

## UPDATES TO EXISTING TABLES

### 6. vegas_fryers Table Updates

**Proposed ALTER:**
```sql
ALTER TABLE `forecasting_data_warehouse.vegas_fryers`
ADD COLUMN oil_type STRING,
ADD COLUMN oil_density_lb_per_gal FLOAT64,
ADD COLUMN cuisine_type STRING,
ADD COLUMN fryer_model STRING,
ADD COLUMN installation_date DATE,
ADD COLUMN last_service_date DATE;
```

**✅ Matches Requirements:** YES
- ✅ oil_type - CRITICAL (from audit)
- ✅ oil_density_lb_per_gal - CRITICAL (from audit)
- ✅ cuisine_type - CRITICAL (from audit)
- ✅ fryer_model - Good addition
- ✅ installation_date - Good addition
- ✅ last_service_date - Good addition

**Assessment:** ✅ PERFECT - All critical fields included

---

### 7. vegas_customers Table Updates

**Proposed ALTER:**
```sql
ALTER TABLE `forecasting_data_warehouse.vegas_customers`
ADD COLUMN casino_group_id STRING,
ADD COLUMN casino_id STRING,
ADD COLUMN primary_restaurant_id STRING,
ADD COLUMN cuisine_preferences JSON,
ADD COLUMN demographic_profile JSON,
ADD COLUMN psychographic_profile JSON;
```

**✅ Matches Requirements:** YES
- ✅ casino_group_id - From audit
- ✅ casino_id - From audit
- ✅ primary_restaurant_id - From audit
- ✅ cuisine_preferences - From audit
- ✅ demographic_profile - From audit
- ✅ psychographic_profile - From audit

**Assessment:** ✅ PERFECT - All required fields included

---

### 8. vegas_events Table Updates

**Proposed ALTER:**
```sql
ALTER TABLE `forecasting_data_warehouse.vegas_events`
ADD COLUMN affected_casino_ids ARRAY<STRING>,
ADD COLUMN demographic_match JSON,
ADD COLUMN psychographic_match JSON;
```

**⚠️ Missing Critical Fields:**
- ❌ `venue_id` (STRING) - CRITICAL - Event interface has this, needed for matching
- ❌ `start_date` (DATE) - Event interface has this (currently only have event_date)
- ❌ `end_date` (DATE) - Event interface has this (currently have event_duration_days but not end_date)

**✅ Additional Fields (Good Extras):**
- ✅ affected_casino_ids ARRAY - Good for many-to-many
- ✅ demographic_match JSON - Matches plan
- ✅ psychographic_match JSON - Matches plan

**Assessment:** ⚠️ INCOMPLETE - Missing venue_id, start_date, end_date

---

## MISSING TABLES

### 9. vegas_event_types Table (NOT PROPOSED - NEEDED)

**TypeScript Code Has:**
```typescript
const eventTypeDefinitions: { [key: string]: { 
  attendance: number,      // Attendance multiplier
  oil: number,             // Oil consumption multiplier
  lead: number             // Lead time in days
} }
```

**Required Table:**
```sql
CREATE TABLE IF NOT EXISTS `forecasting_data_warehouse.vegas_event_types` (
  event_type_id STRING PRIMARY KEY,
  event_type_name STRING NOT NULL,
  attendance_multiplier FLOAT64,
  oil_consumption_multiplier FLOAT64,
  lead_time_days INT64,
  demographic_profile JSON,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

**Assessment:** ❌ MISSING - Should be added to plan

---

### 10. vegas_cuisine_base_usage Table (NOT PROPOSED - NEEDED)

**TypeScript Code Has:**
```typescript
const cuisineBaseUsage: { [key: string]: number } = {
  'fast_food': 15,      // lbs per fryer per week
  'american': 10,
  // ... 16 cuisine types
}
```

**Required Table:**
```sql
CREATE TABLE IF NOT EXISTS `forecasting_data_warehouse.vegas_cuisine_base_usage` (
  cuisine_type STRING PRIMARY KEY,
  base_usage_lbs_per_fryer_per_week FLOAT64 NOT NULL,
  description STRING,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

**Assessment:** ❌ MISSING - Should be added to plan

---

## DATA POPULATION REVIEW

### 11. Cuisine Affinities Initial Data

**Proposed Data:**
- ✅ 25 rows covering major cuisine types and event types
- ✅ Matches TypeScript `cuisineAffinities` array
- ✅ Includes: sports_bar, steakhouse, bar, italian, fast_food, mexican, buffet, coffee_shop, pizza, bbq, asian

**⚠️ Missing:**
- ❌ Some cuisine types from TypeScript (e.g., 'american', 'seafood', 'deli', 'cafe', 'breakfast')
- ❌ Some event types from TypeScript (e.g., 'Holiday Weekend', 'CES Tech Show')

**Assessment:** ⚠️ INCOMPLETE - Should include all from TypeScript code

---

## CODE REVIEW

### 12. Glide Data Import Script (JavaScript)

**Issues Found:**
1. ❌ API endpoint format: `https://api.glideapp.io/api/tables/${tableId}/rows` - This format wasn't working in our tests
2. ❌ Authentication: Uses `X-Glide-App-ID` header - We tested with `Authorization: Bearer` only
3. ⚠️ Error handling: Minimal error handling
4. ⚠️ Data transformation: `extractCuisineType` function not implemented
5. ⚠️ Missing: Import for casino groups, casinos, fryers

**Assessment:** ⚠️ NEEDS WORK - API format needs verification, error handling needed

---

### 13. Event-Restaurant Processor (JavaScript)

**Issues Found:**
1. ✅ Logic matches TypeScript `generateRecommendations` function
2. ✅ Multiplier calculation matches TypeScript
3. ⚠️ Missing: Forecast integration (uses hardcoded price)
4. ⚠️ Missing: Lead time calculation based on event type
5. ⚠️ SQL injection risk: String interpolation in queries (should use parameterized queries)

**Assessment:** ⚠️ GOOD STRUCTURE - Needs security fixes and forecast integration

---

### 14. API Routes (TypeScript)

**Issues Found:**
1. ✅ Good query structure
2. ✅ Proper joins between tables
3. ⚠️ SQL injection risk: String interpolation in WHERE clauses
4. ✅ Good aggregation logic for venues
5. ✅ Good statistics calculation

**Assessment:** ⚠️ GOOD - Needs security fixes (parameterized queries)

---

## COMPREHENSIVE GAP ANALYSIS

### Missing from Implementation Plan:

1. **vegas_event_types** table - CRITICAL
   - Required for event multiplier lookups
   - Currently hardcoded in TypeScript

2. **vegas_cuisine_base_usage** table - CRITICAL
   - Required for base oil usage calculations
   - Currently hardcoded in TypeScript

3. **vegas_events.venue_id** field - CRITICAL
   - Required for event-restaurant matching
   - Code logic depends on this

4. **vegas_events.start_date** and **end_date** fields - HIGH
   - Event interface requires both
   - Currently only have event_date

5. **vegas_restaurants.oil_type** field - HIGH
   - Restaurant interface has this
   - Needed for density calculations

6. **vegas_event_restaurants** missing fields - MEDIUM
   - Many fields from Recommendation interface missing
   - Could be calculated on-the-fly but better to store

7. **Complete cuisine affinities data** - MEDIUM
   - Missing some cuisine types and event types from TypeScript

8. **Glide API authentication** - HIGH
   - API format needs verification
   - Current format may not work

---

## CORRECTED IMPLEMENTATION PLAN

### Phase 1: Create/Update Tables (CRITICAL)

1. ✅ Create `vegas_restaurants` (add `oil_type` field)
2. ✅ Create `vegas_casino_groups`
3. ✅ Create `vegas_casinos` (consider adding denormalized counts)
4. ✅ Create `vegas_event_restaurants` (add missing Recommendation fields)
5. ✅ Create `vegas_cuisine_affinities`
6. ❌ **ADD:** Create `vegas_event_types` table
7. ❌ **ADD:** Create `vegas_cuisine_base_usage` table
8. ✅ Update `vegas_fryers` (add missing fields)
9. ✅ Update `vegas_customers` (add missing fields)
10. ⚠️ **FIX:** Update `vegas_events` (add `venue_id`, `start_date`, `end_date`)

### Phase 2: Populate Reference Data

1. ✅ Populate `vegas_cuisine_affinities` (complete all from TypeScript)
2. ❌ **ADD:** Populate `vegas_event_types` (from TypeScript `eventTypeDefinitions`)
3. ❌ **ADD:** Populate `vegas_cuisine_base_usage` (from TypeScript `cuisineBaseUsage`)

### Phase 3: Data Import Scripts

1. ⚠️ **FIX:** Verify Glide API endpoint format
2. ⚠️ **FIX:** Verify Glide API authentication
3. ✅ Create restaurant import script
4. ✅ Create casino group import script
5. ✅ Create casino import script
6. ✅ Create fryer import script
7. ⚠️ **FIX:** Add error handling
8. ⚠️ **FIX:** Implement `extractCuisineType` function

### Phase 4: Processing Scripts

1. ✅ Create event-restaurant processor
2. ⚠️ **FIX:** Add forecast integration (query from predictions dataset)
3. ⚠️ **FIX:** Use parameterized queries (security)
4. ⚠️ **FIX:** Add lead time calculation based on event type

### Phase 5: API Routes

1. ✅ Create event intelligence API
2. ⚠️ **FIX:** Use parameterized queries (security)
3. ✅ Test with real data

### Phase 6: Integration

1. ✅ Deploy to Vercel
2. ✅ Connect dashboard components
3. ✅ Set up scheduled jobs
4. ✅ Set up monitoring

---

## PRIORITY CORRECTIONS

### CRITICAL (Must Fix Before Implementation):
1. Add `vegas_event_types` table
2. Add `vegas_cuisine_base_usage` table
3. Add `venue_id` to `vegas_events`
4. Add `start_date` and `end_date` to `vegas_events`
5. Add `oil_type` to `vegas_restaurants`
6. Fix Glide API endpoint/authentication

### HIGH (Should Fix):
1. Complete cuisine affinities data population
2. Add missing fields to `vegas_event_restaurants`
3. Fix SQL injection vulnerabilities
4. Add forecast integration to processor

### MEDIUM (Can Fix Later):
1. Add denormalized counts to `vegas_casinos`
2. Improve error handling in scripts
3. Add more comprehensive logging

---

## FINAL ASSESSMENT

**Overall Plan Quality:** ✅ GOOD (85% complete)
**Critical Gaps:** 6 items need fixing
**High Priority Gaps:** 4 items need fixing
**Ready for Implementation:** ⚠️ AFTER critical fixes

**Recommendation:** 
1. Fix all CRITICAL items first
2. Then proceed with implementation
3. Fix HIGH priority items during implementation
4. Address MEDIUM items as enhancements

The plan is comprehensive and well-structured, but needs these corrections before execution.

