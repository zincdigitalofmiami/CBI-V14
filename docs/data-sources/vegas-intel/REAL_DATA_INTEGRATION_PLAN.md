---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Vegas Intel Real Data Integration Plan
**Status:** Planning  
**Date:** November 6, 2025  
**Objective:** Replace fake event data with real scraped events, rebuild proximity calculations, and restore event-driven features using ONLY real Glide data and FREE services

---

## Executive Summary

**Problem:** Fake event data was removed, leaving event-driven features empty. We need to rebuild the entire event intelligence pipeline using:
- ✅ Real Glide data (142 restaurants, 421 fryers, 142 cuisine multipliers)
- ✅ FREE geocoding (OpenStreetMap Nominatim - already working)
- ✅ FREE event scraping (public sources only)
- ✅ Real proximity math (haversine distance)
- ✅ Real opportunity scoring (using cuisine multipliers)

**Solution:** Build a complete event intelligence pipeline that:
1. Scrapes real events from free public sources
2. Geocodes events using free Nominatim
3. Calculates proximity to restaurants using haversine distance
4. Scores opportunities using real cuisine multipliers
5. Serves data through existing API endpoints

---

## Current State Audit

### ✅ Real Data Assets (Verified Working)

**Glide Data:**
- `vegas_restaurants`: 142 restaurants (151 total, 142 "Open")
- `vegas_fryers`: 421 fryers linked to restaurants
- `vegas_cuisine_multipliers`: 142 restaurants mapped to 40 cuisine types
  - Multiplier range: 0.3 (Nobu Sushi) to 2.2 (Buffets)
  - Complete coverage: 100% of open restaurants

**Geocoding:**
- 92 restaurants geocoded (lat/lng)
- 14 casinos geocoded (lat/lng)
- Script exists: `scripts/geocode_vegas_locations_free.py` (uses free Nominatim)

**API Endpoints (Working with Real Data):**
- `/api/v4/vegas/metrics` - Uses real fryer data + multipliers
- `/api/v4/vegas/customers` - Uses real restaurant data
- `/api/v4/vegas/margin-alerts` - Uses real data + ZL cost

**API Endpoints (Empty - Need Real Events):**
- `/api/v4/vegas/upsell-opportunities` - Returns empty (no events)
- `/api/v4/vegas/heatmap-data` - Returns empty (no events)
- `/api/v4/vegas/events` - Returns empty (no events)

### ❌ Missing Components

**Event Data:**
- No `vegas_events` table (deleted due to fake data)
- No event scraper (deleted)
- No event geocoding

**Proximity Calculations:**
- No `haversine_distance` UDF (deleted)
- No `proximity_multiplier` UDF (deleted)
- No `event_restaurant_impact` view (deleted)

**Opportunity Scoring:**
- No `vegas_opportunity_scores` view (deleted)
- No `vegas_top_opportunities` view (deleted)

---

## Phase 1: Event Data Pipeline (FREE Sources Only)

### 1.1 Event Scraper Design

**FREE Sources (No API Keys Required):**
1. **Vegas.com Events** - Public HTML scraping
2. **LVCVA Calendar** - Public convention calendar
3. **Manual Major Events** - Curated list (F1, Super Bowl, CES, etc.)

**File:** `cbi-v14-ingestion/scrape_vegas_events_real.py`

**Schema:**
```sql
CREATE TABLE `cbi-v14.forecasting_data_warehouse.vegas_events` (
  event_id STRING NOT NULL,
  event_name STRING,
  event_date DATE,
  venue STRING,
  lat FLOAT64,
  lng FLOAT64,
  source STRING,
  source_url STRING,
  event_type STRING,
  expected_attendance INT64,
  scraped_at TIMESTAMP
)
```

**Implementation:**
- Scrape Vegas.com event listings (HTML parsing)
- Scrape LVCVA convention calendar
- Include curated major events (F1, Super Bowl, CES, NFR)
- Geocode venues using free Nominatim (same as restaurants)
- Store in BigQuery with deduplication (event_id = MD5(event_name + date + venue))

**Rate Limits:**
- Nominatim: 1 request/second (already implemented)
- Vegas.com: Polite scraping (2-3 second delays)
- LVCVA: Polite scraping (2-3 second delays)

### 1.2 Event Geocoding

**Strategy:** Geocode during scraping (same as deleted script did)
- Use existing `FreeGeocoder` class pattern
- Integrate into scraper (no separate step needed)
- Cache results to avoid re-geocoding

---

## Phase 2: Proximity Calculations

### 2.1 BigQuery UDFs

**File:** `bigquery_sql/CREATE_PROXIMITY_FUNCTIONS.sql`

**Haversine Distance:**
```sql
CREATE OR REPLACE FUNCTION `cbi-v14.forecasting_data_warehouse.haversine_distance`(
  lat1 FLOAT64, lon1 FLOAT64, lat2 FLOAT64, lon2 FLOAT64
) RETURNS FLOAT64 AS ((
  ACOS(
    SIN(RADIANS(lat1)) * SIN(RADIANS(lat2)) + 
    COS(RADIANS(lat1)) * COS(RADIANS(lat2)) * COS(RADIANS(lon2) - RADIANS(lon1))
  ) * 6371  -- Earth radius in km
));
```

**Proximity Multiplier:**
```sql
CREATE OR REPLACE FUNCTION `cbi-v14.forecasting_data_warehouse.proximity_multiplier`(
  distance_km FLOAT64
) RETURNS FLOAT64 AS ((
  CASE
    WHEN distance_km <= 0.5 THEN 2.5  -- Very close (walking distance)
    WHEN distance_km <= 1.0 THEN 2.0  -- Close
    WHEN distance_km <= 2.0 THEN 1.5  -- Medium
    WHEN distance_km <= 5.0 THEN 1.2  -- Far
    ELSE 1.0                          -- Very far / no impact
  END
));
```

### 2.2 Event-Restaurant Impact View

**File:** `bigquery_sql/CREATE_EVENT_RESTAURANT_IMPACT.sql`

**Purpose:** Calculate proximity-based impact of events on restaurants

**Key Calculations:**
- Distance: `haversine_distance(event_lat, event_lng, restaurant_lat, restaurant_lng)`
- Proximity multiplier: `proximity_multiplier(distance_km)`
- Attendance multiplier: Based on expected_attendance tiers
- Combined impact: `proximity_multiplier × attendance_multiplier`
- Baseline weekly gallons: `(total_fryer_capacity_lbs × 4 TPM) / 7.6 × oil_multiplier`
- Event surge gallons: `baseline_weekly_gallons × (event_days/7) × combined_impact_score`

**Filters:**
- Only restaurants with `lat IS NOT NULL` and `lng IS NOT NULL`
- Only events with `lat IS NOT NULL` and `lng IS NOT NULL`
- Only events within 10km of restaurants
- Only events in next 90 days

---

## Phase 3: Opportunity Scoring

### 3.1 Opportunity Scores View

**File:** `bigquery_sql/CREATE_OPPORTUNITY_SCORING.sql`

**Purpose:** Composite scoring system for ranking upsell opportunities

**Score Components (0-100 total):**
- **Proximity Score (30 points max):** `(1 - distance_km/10.0) * 30`
- **Attendance Score (30 points max):** `(expected_attendance / 100000.0) * 30`
- **Fryer Score (20 points max):** `(fryer_count / 10.0) * 20`
- **Cuisine Score (10 points max):** `(oil_multiplier / 2.5) * 10`
- **Revenue Score (10 points max):** `(revenue_opportunity / 10000.0) * 10`

**Composite Score:**
```sql
opportunity_score = ROUND(
  proximity_score + attendance_score + fryer_score + cuisine_score + revenue_score,
  0
)
```

**Urgency Classification:**
- `IMMEDIATE ACTION`: days_until <= 7
- `HIGH PRIORITY`: days_until <= 30
- `MODERATE`: days_until <= 90
- `MONITOR`: days_until > 90

### 3.2 Top Opportunities View

**File:** Same SQL file, second view

**Purpose:** Filter and rank top opportunities

**Filters:**
- `opportunity_score >= 30` (minimum meaningful score)
- `days_until >= 0 AND days_until <= 90` (upcoming only)
- `ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY opportunity_score DESC) = 1` (top restaurant per event)

**Limit:** 50 top opportunities

---

## Phase 4: API Endpoint Restoration

### 4.1 Upsell Opportunities Endpoint

**File:** `dashboard-nextjs/src/app/api/v4/vegas/upsell-opportunities/route.ts`

**Current State:** Returns empty array (LIMIT 0 query)

**New Query:**
```sql
SELECT 
  CONCAT(event_id, '_', restaurant_id) as id,
  restaurant_name as venue_name,
  event_name,
  event_date,
  3 as event_duration_days,
  expected_attendance,
  event_surge_gallons as oil_demand_surge_gal,
  revenue_opportunity as revenue_usd,
  urgency_classification as urgency,
  opportunity_score_display,
  opportunity_score,
  distance_km,
  days_until,
  analysis_bullets,
  restaurant_name as messaging_strategy_target,
  CONCAT(event_name, ' on ', FORMAT_DATE('%B %d, %Y', event_date)) as messaging_strategy_monthly_forecast,
  CONCAT('Expected surge: +', CAST(event_surge_gallons as STRING), ' gallons. Revenue opportunity: $', FORMAT("%'d", CAST(revenue_opportunity as INT64))) as messaging_strategy_message,
  CONCAT('Contact ', CAST(days_until - 7 as STRING), ' days before event') as messaging_strategy_timing,
  CONCAT('$', FORMAT("%'d", CAST(revenue_opportunity as INT64)), ' incremental revenue') as messaging_strategy_value_prop,
  true as calculation_available
FROM `cbi-v14.forecasting_data_warehouse.vegas_top_opportunities`
WHERE days_until >= 0 AND days_until <= 90
ORDER BY opportunity_score DESC
LIMIT 20
```

**Fallback:** If view doesn't exist, return empty array (graceful degradation)

### 4.2 Heat Map Data Endpoint

**File:** `dashboard-nextjs/src/app/api/v4/vegas/heatmap-data/route.ts`

**Current State:** Returns empty array (LIMIT 0 query)

**New Query:**
```sql
WITH event_points AS (
  SELECT 
    event_lat as lat,
    event_lng as lng,
    AVG(combined_impact_score) as weight,
    'event' as type,
    ANY_VALUE(event_name) as name
  FROM `cbi-v14.forecasting_data_warehouse.event_restaurant_impact`
  WHERE event_lat IS NOT NULL AND event_lng IS NOT NULL
  GROUP BY event_lat, event_lng
),
restaurant_points AS (
  SELECT 
    r.lat,
    r.lng,
    CAST(COUNT(DISTINCT e.event_id) as FLOAT64) as weight,
    'restaurant' as type,
    r.MHXYO as name
  FROM `cbi-v14.forecasting_data_warehouse.vegas_restaurants` r
  LEFT JOIN `cbi-v14.forecasting_data_warehouse.event_restaurant_impact` e
    ON r.glide_rowID = e.restaurant_id
  WHERE r.lat IS NOT NULL AND r.lng IS NOT NULL
  GROUP BY r.lat, r.lng, r.MHXYO
)
SELECT lat, lng, weight, type, name
FROM event_points
WHERE weight > 0
UNION ALL
SELECT lat, lng, weight, type, name
FROM restaurant_points
WHERE weight > 0
ORDER BY weight DESC
LIMIT 200
```

**Fallback:** If view doesn't exist, return empty array

---

## Phase 5: Testing & Validation

### 5.1 Data Quality Checks

**Event Data:**
- Verify all events have `event_date >= CURRENT_DATE()`
- Verify all events have geocoded coordinates (lat/lng)
- Verify attendance estimates are reasonable (1000-500000)
- Check for duplicate events (same name + date + venue)

**Proximity Calculations:**
- Verify haversine distance is accurate (test with known coordinates)
- Verify proximity multipliers are within expected range (1.0-2.5)
- Verify impact scores are reasonable

**Opportunity Scoring:**
- Verify scores are between 0-100
- Verify top opportunities are ranked correctly
- Verify urgency classifications match days_until

### 5.2 API Endpoint Testing

**Upsell Opportunities:**
- Test with real events → should return opportunities
- Test with no events → should return empty array (graceful)
- Test with invalid parameters → should handle errors

**Heat Map:**
- Test with real events → should return points
- Test with no events → should return empty array
- Verify coordinates are valid (lat: -90 to 90, lng: -180 to 180)

### 5.3 Frontend Testing

**EventDrivenUpsell Component:**
- Verify opportunities display correctly
- Verify analysis bullets render
- Verify AI message generation works
- Verify empty state displays when no events

**VegasHeatMap Component:**
- Verify map renders with OpenStreetMap tiles
- Verify points display with correct colors
- Verify popups show correct data
- Verify empty state displays when no data

---

## Implementation Checklist

### Phase 1: Event Scraper
- [ ] Create `scrape_vegas_events_real.py` script
- [ ] Implement Vegas.com scraper
- [ ] Implement LVCVA scraper
- [ ] Add curated major events
- [ ] Integrate geocoding (free Nominatim)
- [ ] Test scraper with real sources
- [ ] Run scraper and verify events in BigQuery

### Phase 2: Proximity Functions
- [ ] Create `CREATE_PROXIMITY_FUNCTIONS.sql`
- [ ] Run haversine_distance UDF creation
- [ ] Run proximity_multiplier UDF creation
- [ ] Test UDFs with known coordinates
- [ ] Create `CREATE_EVENT_RESTAURANT_IMPACT.sql`
- [ ] Run event_restaurant_impact view creation
- [ ] Verify view returns data

### Phase 3: Opportunity Scoring
- [ ] Create `CREATE_OPPORTUNITY_SCORING.sql`
- [ ] Run vegas_opportunity_scores view creation
- [ ] Run vegas_top_opportunities view creation
- [ ] Verify scores are calculated correctly
- [ ] Verify top opportunities are ranked

### Phase 4: API Restoration
- [ ] Update `/api/v4/vegas/upsell-opportunities/route.ts`
- [ ] Update `/api/v4/vegas/heatmap-data/route.ts`
- [ ] Test endpoints with real data
- [ ] Test endpoints with empty data (graceful degradation)
- [ ] Deploy to Vercel

### Phase 5: Testing
- [ ] Run data quality checks
- [ ] Test all API endpoints
- [ ] Test frontend components
- [ ] Verify no fake data remains
- [ ] Verify all calculations use real multipliers

---

## Cost Analysis

**FREE Services (No Cost):**
- OpenStreetMap Nominatim: Free (1 req/sec limit)
- OpenStreetMap tiles: Free
- Web scraping: Free (public sources)
- BigQuery UDFs: Free (compute only)

**BigQuery Costs:**
- Event storage: ~$0.01/month (estimated 50-100 events)
- View queries: ~$0.05/month (estimated 100 queries/day)
- **Total: <$0.10/month**

---

## Risk Mitigation

**Event Scraper Failures:**
- Implement retry logic for network errors
- Cache geocoded venues to avoid re-geocoding
- Manual fallback: curated major events list

**Missing Geocoding:**
- Filter out events without coordinates
- Log failures for manual review
- Use approximate coordinates for known venues

**No Events Available:**
- Graceful degradation: empty arrays
- Frontend shows "No Event Data" message
- No errors thrown

---

## Success Criteria

1. ✅ Real events scraped from free sources (minimum 10 events)
2. ✅ All events geocoded successfully (minimum 80% success rate)
3. ✅ Proximity calculations working (haversine distance accurate)
4. ✅ Opportunity scoring using real multipliers (all 142 restaurants)
5. ✅ API endpoints return real data (not empty)
6. ✅ Dashboard displays real opportunities (not fake data)
7. ✅ Zero fake data in production
8. ✅ All calculations use real Glide multipliers

---

## Timeline

**Phase 1 (Event Scraper):** 2-3 hours
- Scraper implementation
- Geocoding integration
- Testing with real sources

**Phase 2 (Proximity Functions):** 1-2 hours
- UDF creation
- View creation
- Testing

**Phase 3 (Opportunity Scoring):** 1-2 hours
- View creation
- Testing
- Validation

**Phase 4 (API Restoration):** 1 hour
- Endpoint updates
- Testing
- Deployment

**Phase 5 (Testing):** 1-2 hours
- End-to-end testing
- Validation
- Bug fixes

**Total Estimated Time:** 6-10 hours

---

## Next Steps

1. Review and approve this plan
2. Begin Phase 1: Event scraper implementation
3. Test with real sources
4. Proceed through phases sequentially
5. Deploy to production after all tests pass

---

**End of Plan**







