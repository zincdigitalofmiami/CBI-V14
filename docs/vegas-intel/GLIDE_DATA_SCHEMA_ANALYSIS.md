# Vegas Intel - Glide Data Schema Analysis
**Purpose:** Map Glide column names to forecasting model requirements  
**Status:** 🔍 IN PROGRESS - Analyzing Real Data  
**Date:** November 5, 2025

---

## 🚨 CRITICAL: GLIDE IS READ ONLY

All analysis is for READ ONLY queries only. We NEVER write to Glide.

---

## Data Available vs Forecasting Requirements

### From Architecture Plan - Required Calculations

**Key Formula (from VEGAS_INTEL_SALES_PAGE_ARCHITECTURE.md):**

```
BASE_UPSELL_GALLONS = 
  (fryer_count × avg_gallons_per_fryer_per_week) × 
  event_duration_days / 7

FINAL_UPSELL_GALLONS = 
  BASE_UPSELL_GALLONS × 
  PAST_USE_ADJUSTMENT × 
  EVENT_MULTIPLIER × 
  TARGETING_SCORE

ROI CALCULATION:
UPSELL_GALLONS = SURGE_GALLONS × UPSELL_% (Kevin edited)
GROSS_REVENUE = UPSELL_GALLONS × PRICE_PER_GAL (Kevin edited)
COGS = UPSELL_GALLONS × ZL_COST (locked from Dashboard)
DELIVERY_COST = (UPSELL_GALLONS / 3000) × TANKER_COST + LABOR
NET_PROFIT = GROSS_REVENUE - COGS - DELIVERY_COST
ROI = GROSS_REVENUE / (COGS + DELIVERY_COST)
MARGIN = NET_PROFIT / GROSS_REVENUE × 100
```

---

## Actual Glide Data Schema (READ ONLY)

### Table 1: vegas_restaurants (151 rows)

**Confirmed Columns:**
- `glide_rowID` (STRING) - Unique restaurant ID
- `MHXYO` (STRING) - **Restaurant Name** ✅
- `U0Jf2` (STRING) - **Oil Product Type** (e.g., "StableMAX - Bulk", "SoyMAX - 35# Jib")
- `zPYNY` (INT64) - Unknown (value: 20 in all samples) - possibly default quantity or price multiplier
- `s8tNr` (STRING) - **Restaurant Status** ("Open" / "Closed") ✅
- `Po4Zg` (STRING) - **Delivery Frequency** ("Daily", "Certain Days", "Customer Decides")  ✅
- `lf0gF` (STRING) - **Delivery Days** (e.g., "Monday,Tuesday,Wednesday...") ✅
- `2Ca0T` (STRING) - Foreign key (possibly to casino/group)
- `g5WAm` (STRING) - Foreign key (possibly to another entity)
- `Ie35Z` (STRING) - Contact person (e.g., "Chef Nicholas Beesley")
- `maCR5` (STRING) - Email address
- `08Hj9` (STRING) - Notes/comments
- `uwU2A` (STRING) - Timestamp string
- `g9zbE`, `lA5EU`, `Ny3eQ` (BOOL) - Unknown flags

**Missing for Forecasting:**
- ❌ Current oil usage (gal/week)
- ❌ Past oil usage (historical)
- ❌ Event associations
- ❌ Pricing information

### Table 2: vegas_fryers (421 rows)

**Confirmed Columns:**
- `glide_rowID` (STRING) - Unique fryer ID
- `Name` (STRING) - **Fryer Name** ✅ (e.g., "Fryer 1", "Fryer 4 Countertop")
- `xhrM0` (FLOAT64) - **Fryer Capacity** ✅ (7.7 to 80 lbs based on samples, avg 61.23 lbs)
- `2uBBn` (STRING) - **Foreign Key to Restaurant** ✅ (links to vegas_restaurants.glide_rowID)
- `AeE7m` (BOOL) - Unknown flag

**Available for Calculations:**
- ✅ Fryer count per restaurant (COUNT by 2uBBn)
- ✅ Total fryer capacity per restaurant (SUM xhrM0)
- ✅ Average fryer capacity (AVG xhrM0 = 61.23 lbs)

**Missing for Forecasting:**
- ❌ Turns per month (TPM)
- ❌ Current utilization %
- ❌ Cuisine type (for consumption multipliers)

### Table 3: vegas_casinos (31 rows)

**Confirmed Columns:**
- `glide_rowID` (STRING) - Unique casino ID
- `Name` (STRING) - **Casino Name** ✅ (e.g., "Mandalay Bay", "Suncoast")
- `L9K9x` (STRING) - **Casino Address/Location** ✅
- `ro9f5` (STRING) - Foreign key (possibly to group/parent company)

**Missing for Forecasting:**
- ❌ Event calendar
- ❌ Event dates
- ❌ Expected attendance
- ❌ Event types
- ❌ Volume multipliers

### Table 4: vegas_export_list (3,176 rows)

**Purpose:** Customer export lists - likely contact/targeting data

**Need to Examine:** Haven't looked at schema yet

### Table 5: vegas_scheduled_reports (28 rows)

**Purpose:** Scheduled reports - possibly historical data/trends

**Need to Examine:** Haven't looked at schema yet

### Tables 6-8: Shifts, Shift Casinos, Shift Restaurants

**Purpose:** Delivery scheduling

**Need to Examine:** Sample data shows timestamps (teLOd, tGqQX) and foreign keys (UBrkt)

---

## Baseline Calculations Possible with Current Data

### ✅ What We CAN Calculate

**1. Fryer Math (Baseline)**
```sql
-- Count fryers per restaurant
SELECT 
  r.MHXYO as restaurant_name,
  COUNT(f.glide_rowID) as fryer_count,
  ROUND(SUM(f.xhrM0), 2) as total_capacity_lbs,
  ROUND(AVG(f.xhrM0), 2) as avg_fryer_capacity
FROM vegas_restaurants r
LEFT JOIN vegas_fryers f ON r.glide_rowID = f.`2uBBn`
WHERE r.s8tNr = 'Open'
GROUP BY r.glide_rowID, r.MHXYO
```

**2. Base Daily Gallons (Using Standard Formula)**

From architecture: `(fryer_capacity_lb × turns_per_month) / 7 / 7.6`

Since we don't have turns_per_month, use industry standard:
- **Assumption:** 4 turns per month (typical for restaurants)
- **Formula:** `(total_capacity_lbs × 4) / 7 / 7.6 = base_daily_gallons`

```sql
SELECT 
  r.MHXYO as restaurant_name,
  COUNT(f.glide_rowID) as fryer_count,
  SUM(f.xhrM0) as total_capacity_lbs,
  ROUND((SUM(f.xhrM0) * 4) / 7 / 7.6, 2) as base_daily_gallons,
  ROUND((SUM(f.xhrM0) * 4) / 7.6, 2) as base_weekly_gallons
FROM vegas_restaurants r
LEFT JOIN vegas_fryers f ON r.glide_rowID = f.`2uBBn`
WHERE r.s8tNr = 'Open'
GROUP BY r.glide_rowID, r.MHXYO
```

**3. Total Weekly Capacity**
```
Weekly Base Usage = Total Fryer Capacity × 4 turns / 7.6 lbs per gallon
```

### ❌ What We CANNOT Calculate (Without More Data)

**Missing Data:**
1. **Event Calendar** - No event dates, names, attendance in current tables
2. **Event Multipliers** - No event type classification
3. **Historical Usage** - No past consumption data for PAST_USE_ADJUSTMENT
4. **Demographics/Psychographics** - No customer demographic data
5. **Pricing Data** - No current prices, margins, or historical pricing

---

## Recommended Approach

### Phase 1: Use Available Data (Current State)

**Build dashboard with what we have:**

1. **Fryer Baseline Metrics**
   - Total fryers: 408
   - Active restaurants: 142
   - Avg fryer capacity: 61.23 lbs
   - Estimated weekly base: `(408 fryers × 61.23 lbs × 4 turns) / 7.6 = 13,053 gallons/week`

2. **Restaurant List**
   - 151 restaurants with names and status
   - Delivery schedules (Daily vs Certain Days)
   - Product types (StableMAX, SoyMAX, etc.)

3. **Casino/Location Data**
   - 31 casinos mapped to restaurants (via foreign keys)
   - Location data for route planning

### Phase 2: Add Calculated Placeholders (Smart Defaults)

**For missing data, use industry-standard assumptions:**

1. **Event Multipliers**
   - Default: 1.5x for weekend surge
   - Default: 2.0x for major events (F1, conventions)
   - Kevin can override in UI

2. **Upsell %**
   - Default: 68% (from architecture)
   - Kevin can override

3. **Pricing Defaults**
   - Price/gal: $8.20 (from architecture)
   - ZL Cost: Pull from Dashboard forecast
   - Tanker: $1,200
   - Labor: $180

---

## Next Steps

1. **Create Data Dictionary** - Map all Glide columns to business meanings
2. **Build Smart SQL Queries** - Implement fryer math with available data
3. **Add Industry Defaults** - Use standard assumptions for missing data
4. **Enable Kevin Override** - All calculations editable in UI
5. **Document Limitations** - Clear about what's real data vs assumptions

**Status:** Need to examine remaining tables (export_list, scheduled_reports) and build comprehensive mapping.

---

**READ ONLY REMINDER:** All queries are READ ONLY from Glide. We never write back.







