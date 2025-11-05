# VEGAS TABLES AUDIT REPORT - READ ONLY
## Comprehensive Data Structure Analysis

### EXECUTIVE SUMMARY
**Status:** Tables partially created but MISSING CRITICAL FIELDS
**Current Tables:** 3 tables exist (vegas_customers, vegas_fryers, vegas_events)
**Missing:** Key relationships, restaurant details, oil types, location/casino data, cuisine/demographic/psychographic data

---

## DATA MODEL REQUIREMENTS (From Plan)

### Entity Hierarchy:
```
Casino Group (Restaurant Group)
  └── Casino
      └── Restaurant
          └── Fryer (multiple per restaurant)
              ├── Oil Type
              ├── Oil Volume
              ├── TPM (Turns Per Month)
              └── Cuisine Type
```

### Required Fields Per Entity:

#### 1. Restaurant Groups (Casino Groups)
- ✅ Group ID
- ✅ Group Name
- ❌ Casino affiliations
- ❌ Scheduling availability
- ❌ Delivery window preferences
- ❌ Demographic profile
- ❌ Psychographic profile

#### 2. Restaurants (Individual Locations)
- ❌ **MISSING TABLE ENTIRELY**
- Required: restaurant_id, restaurant_name, location, casino, casino_group, cuisine_type, demographic, psychographic, scheduling_availability, delivery_timing, current_usage, historical_usage

#### 3. Fryers
- ✅ fryer_id
- ✅ restaurant_id (but no restaurant table!)
- ✅ fryer_capacity_lb
- ✅ turns_per_month
- ✅ base_daily_gallons
- ✅ is_active
- ❌ oil_type (critical - different oils have different volumes)
- ❌ cuisine_type (critical - cuisine determines oil intensity factor)
- ❌ fryer_type (e.g., Club, Steakhouse, Bakery, Italian, Chinese, Sushi)

#### 4. Customers (Current vegas_customers table)
- ✅ customer_id
- ✅ customer_name
- ✅ account_type
- ✅ relationship_score
- ✅ current_volume
- ✅ last_order_date
- ✅ growth_potential
- ✅ next_action_recommendation
- ❌ **MISSING:** casino_group, casino, location, cuisine_preferences, demographic_profile, psychographic_profile, scheduling_constraints, delivery_preferences

#### 5. Events (Current vegas_events table)
- ✅ event_id
- ✅ event_name
- ✅ event_type
- ✅ event_date
- ✅ location
- ✅ expected_attendance
- ✅ base_daily_traffic
- ✅ cuisine_intensity_factor
- ✅ volume_multiplier
- ✅ event_duration_days
- ✅ revenue_opportunity
- ✅ urgency
- ❌ **MISSING:** affected_restaurants (many-to-many), affected_casinos, demographic_match, psychographic_match

---

## EXISTING DATA STRUCTURES FOUND

### Tables in forecasting_data_warehouse:
- ✅ `vegas_customers` - EXISTS but incomplete
- ✅ `vegas_fryers` - EXISTS but incomplete  
- ✅ `vegas_events` - EXISTS but incomplete
- ❌ `vegas_restaurants` - **MISSING ENTIRELY**

### Views Found:
- `ai_metadata_summary`
- `data_integration_status`
- `metadata_completeness_check`
- `vw_scrapecreator_*` views (4 views)

### Signals Dataset:
- 30+ signal views exist (Big-8 signals, comprehensive aggregates)
- No Vegas-specific signals found

---

## CRITICAL GAPS IDENTIFIED

### 1. RESTAURANT TABLE MISSING
**Impact:** CRITICAL - Cannot link fryers to restaurants properly
**Required Fields:**
- restaurant_id (PRIMARY KEY)
- restaurant_name
- casino_id (FK to casino/casino_group)
- casino_group_id (FK)
- location (address, coordinates)
- cuisine_type (Club, Steakhouse, Bakery, Italian, Chinese, Sushi, etc.)
- demographic_profile (age, income, visitor type)
- psychographic_profile (experience-seeking, price-sensitive, etc.)
- scheduling_availability (JSON or separate table)
- delivery_timing_preferences
- current_weekly_usage_gallons
- historical_usage_patterns

### 2. CASINO/CASINO GROUP STRUCTURE MISSING
**Impact:** HIGH - Cannot group restaurants by casino or casino group
**Required:**
- casino_group_id, casino_group_name
- casino_id, casino_name
- casino_group → casino → restaurant hierarchy

### 3. OIL TYPE MISSING FROM FRYERS
**Impact:** CRITICAL - Different oils have different densities/volumes
**Required:**
- oil_type (Soybean, Canola, Palm, etc.)
- oil_density_lb_per_gal (for volume calculations)
- Current fryer table assumes 7.6 lb/gal (soybean oil) - this is hardcoded

### 4. CUISINE TYPE MISSING FROM FRYERS
**Impact:** CRITICAL - Cuisine determines oil intensity factor (1.8x for clubs, 0.6x for bakeries)
**Required:**
- cuisine_type in fryers table OR
- Link to restaurant table which has cuisine_type

### 5. DEMOGRAPHIC/PSYCHOGRAPHIC DATA MISSING
**Impact:** HIGH - Needed for AI targeting boost calculations
**Required:**
- demographic_match_score calculation
- psychographic_match_score calculation
- Currently referenced in formulas but no data source

### 6. RESTAURANT-FRYER RELATIONSHIP
**Current:** fryers table has restaurant_id
**Issue:** No restaurants table exists, so restaurant_id is orphaned
**Fix:** Create restaurants table first, then ensure proper FK relationship

### 7. EVENT-RESTAURANT RELATIONSHIP
**Current:** Events table has no restaurant associations
**Required:** Many-to-many relationship (event affects multiple restaurants)
**Solution:** Create vegas_event_restaurants junction table

---

## DATA FROM GLIDE API (Per Documentation)

### Restaurant Groups Table (Glide: `native-table-w295hHsL0PHvty2sAFwl`)
**Should contain:**
- Group-level data
- Scheduling availability
- Delivery window preferences
- **Maps to:** Casino Groups

### Restaurants Table (Glide: `native-table-ojIjQjDcDAEOpdtZG5Ao`)
**Should contain:**
- Individual restaurant details
- Current usage patterns
- Scheduling constraints
- Delivery timing requirements
- Location data
- **Maps to:** vegas_restaurants (MISSING TABLE)

### Fryers Table (Glide: `native-table-r2BIqSLhezVbOKGeRJj8`)
**Should contain:**
- Fryer count per restaurant
- Fryer capacity and utilization
- Current weekly/monthly usage
- Fryer type (cuisine-based consumption patterns)
- **Maps to:** vegas_fryers (EXISTS but incomplete)

---

## RECOMMENDED TABLE STRUCTURE

### 1. vegas_casino_groups (NEW)
```sql
casino_group_id STRING PRIMARY KEY
casino_group_name STRING
scheduling_availability JSON
delivery_preferences JSON
demographic_profile JSON
psychographic_profile JSON
ingested_at TIMESTAMP
```

### 2. vegas_casinos (NEW)
```sql
casino_id STRING PRIMARY KEY
casino_name STRING
casino_group_id STRING (FK to vegas_casino_groups)
location STRING
coordinates STRUCT<lat FLOAT64, lng FLOAT64>
ingested_at TIMESTAMP
```

### 3. vegas_restaurants (NEW - CRITICAL)
```sql
restaurant_id STRING PRIMARY KEY
restaurant_name STRING
casino_id STRING (FK to vegas_casinos)
casino_group_id STRING (FK to vegas_casino_groups)
location STRING
coordinates STRUCT<lat FLOAT64, lng FLOAT64>
cuisine_type STRING (Club, Steakhouse, Bakery, Italian, Chinese, Sushi, etc.)
demographic_profile JSON
psychographic_profile JSON
scheduling_availability JSON
delivery_timing_preferences JSON
current_weekly_usage_gallons FLOAT64
historical_usage_patterns JSON
ingested_at TIMESTAMP
```

### 4. vegas_fryers (EXISTS - NEEDS FIELDS)
**Current fields:**
- ✅ fryer_id, restaurant_id, fryer_capacity_lb, turns_per_month, base_daily_gallons, is_active

**Missing fields:**
- ❌ oil_type STRING (Soybean, Canola, Palm, etc.)
- ❌ oil_density_lb_per_gal FLOAT64
- ❌ cuisine_type STRING (should match restaurant, but can override)
- ❌ fryer_model STRING
- ❌ installation_date DATE

### 5. vegas_customers (EXISTS - NEEDS FIELDS)
**Current fields:**
- ✅ customer_id, customer_name, account_type, relationship_score, current_volume, last_order_date, growth_potential, next_action_recommendation

**Missing fields:**
- ❌ casino_group_id STRING (FK)
- ❌ casino_id STRING (FK)
- ❌ primary_restaurant_id STRING (FK)
- ❌ cuisine_preferences JSON
- ❌ demographic_profile JSON
- ❌ psychographic_profile JSON

### 6. vegas_events (EXISTS - NEEDS RELATIONSHIP)
**Current fields:**
- ✅ All basic event fields present

**Missing:**
- ❌ Junction table: vegas_event_restaurants (event_id, restaurant_id, expected_impact_gallons)

### 7. vegas_event_restaurants (NEW - JUNCTION TABLE)
```sql
event_id STRING (FK to vegas_events)
restaurant_id STRING (FK to vegas_restaurants)
expected_impact_gallons FLOAT64
upsell_potential_pct FLOAT64
created_at TIMESTAMP
PRIMARY KEY (event_id, restaurant_id)
```

---

## SUMMARY OF FINDINGS

### ✅ What Exists:
1. Basic table structure started (3 tables)
2. Some core fields present
3. BigQuery infrastructure ready

### ❌ What's Missing:
1. **RESTAURANT TABLE** - CRITICAL MISSING PIECE
2. Casino/Casino Group hierarchy
3. Oil type in fryers
4. Cuisine type linkage (fryer → restaurant → cuisine)
5. Demographic/Psychographic data structures
6. Event-Restaurant many-to-many relationship
7. Location/coordinates data
8. Scheduling/delivery preference structures

### 🔧 Required Actions:
1. Create `vegas_restaurants` table (CRITICAL)
2. Create `vegas_casino_groups` table
3. Create `vegas_casinos` table
4. Add missing fields to `vegas_fryers`
5. Add missing fields to `vegas_customers`
6. Create `vegas_event_restaurants` junction table
7. Update Glide ingestion script to populate all tables correctly

---

## NEXT STEPS (After Review Approved)
1. Create complete table schema with all required fields
2. Update Glide API ingestion script to map all Glide data correctly
3. Ensure proper foreign key relationships
4. Populate tables with real Glide data
5. Verify data integrity and relationships


