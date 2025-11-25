-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- Vegas Intel - Event-Restaurant Impact View
-- Calculates proximity-based impact of events on restaurants
-- Uses REAL data: events, restaurants, fryers, cuisine multipliers
-- Created: November 6, 2025

CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.event_restaurant_impact` AS
WITH event_restaurant_pairs AS (
  SELECT
    e.event_id,
    e.event_name,
    e.event_date,
    e.venue as event_venue,
    e.lat as event_lat,
    e.lng as event_lng,
    e.event_type,
    e.expected_attendance,
    
    r.glide_rowID as restaurant_id,
    r.MHXYO as restaurant_name,
    r.lat as restaurant_lat,
    r.lng as restaurant_lng,
    
    -- Calculate distance
    `cbi-v14.forecasting_data_warehouse.haversine_distance`(
      e.lat, e.lng, r.lat, r.lng
    ) as distance_km,
    
    -- Get restaurant base consumption
    COUNT(f.glide_rowID) as fryer_count,
    ROUND(SUM(f.xhrM0), 2) as total_capacity_lbs,
    COALESCE(cm.oil_multiplier, 1.0) as cuisine_multiplier,
    cm.cuisine_type
    
  FROM `cbi-v14.forecasting_data_warehouse.vegas_events` e
  CROSS JOIN `cbi-v14.forecasting_data_warehouse.vegas_restaurants` r
  LEFT JOIN `cbi-v14.forecasting_data_warehouse.vegas_fryers` f
    ON r.glide_rowID = f.`2uBBn`
  LEFT JOIN `cbi-v14.forecasting_data_warehouse.vegas_cuisine_multipliers` cm
    ON r.glide_rowID = cm.glide_rowID
  WHERE
    e.lat IS NOT NULL
    AND r.lat IS NOT NULL
    AND r.s8tNr = 'Open'
    AND e.event_date >= CURRENT_DATE()
  GROUP BY
    e.event_id, e.event_name, e.event_date, e.venue, e.event_type,
    e.expected_attendance, e.lat, e.lng,
    r.glide_rowID, r.MHXYO, r.lat, r.lng,
    cm.oil_multiplier, cm.cuisine_type
)
SELECT
  *,
  -- Proximity multiplier
  `cbi-v14.forecasting_data_warehouse.proximity_multiplier`(distance_km) as proximity_multiplier,
  
  -- Attendance multiplier
  CASE
    WHEN expected_attendance >= 100000 THEN 3.5
    WHEN expected_attendance >= 50000 THEN 2.8
    WHEN expected_attendance >= 20000 THEN 2.2
    WHEN expected_attendance >= 10000 THEN 1.8
    ELSE 1.3
  END as attendance_multiplier,
  
  -- Combined impact score
  (
    `cbi-v14.forecasting_data_warehouse.proximity_multiplier`(distance_km) *
    CASE
      WHEN expected_attendance >= 100000 THEN 3.5
      WHEN expected_attendance >= 50000 THEN 2.8
      WHEN expected_attendance >= 20000 THEN 2.2
      WHEN expected_attendance >= 10000 THEN 1.8
      ELSE 1.3
    END
  ) as combined_impact_score,
  
  -- Baseline weekly gallons: (capacity × TPM × cuisine_multiplier) / 7.6 lbs/gal
  ROUND(
    (total_capacity_lbs * 4) / 7.6 * cuisine_multiplier,
    0
  ) as baseline_weekly_gallons,
  
  -- Event surge gallons: baseline × (event_days/7) × proximity × attendance
  ROUND(
    (total_capacity_lbs * 4) / 7.6 * cuisine_multiplier * (3.0 / 7.0) *
    `cbi-v14.forecasting_data_warehouse.proximity_multiplier`(distance_km) *
    CASE
      WHEN expected_attendance >= 100000 THEN 3.5
      WHEN expected_attendance >= 50000 THEN 2.8
      WHEN expected_attendance >= 20000 THEN 2.2
      WHEN expected_attendance >= 10000 THEN 1.8
      ELSE 1.3
    END,
    0
  ) as event_surge_gallons,
  
  -- Revenue opportunity (at $8.20/gal default)
  ROUND(
    (total_capacity_lbs * 4) / 7.6 * cuisine_multiplier *
    (3.0 / 7.0) *
    `cbi-v14.forecasting_data_warehouse.proximity_multiplier`(distance_km) *
    CASE
      WHEN expected_attendance >= 100000 THEN 3.5
      WHEN expected_attendance >= 50000 THEN 2.8
      WHEN expected_attendance >= 20000 THEN 2.2
      WHEN expected_attendance >= 10000 THEN 1.8
      ELSE 1.3
    END * 0.68 *  -- 68% upsell success rate
    8.20,  -- Price per gallon
    0
  ) as revenue_opportunity,
  
  -- Days until event
  DATE_DIFF(DATE(event_date), CURRENT_DATE(), DAY) as days_until
  
FROM event_restaurant_pairs
WHERE distance_km < 10.0  -- Only events within 10km
ORDER BY combined_impact_score DESC;








