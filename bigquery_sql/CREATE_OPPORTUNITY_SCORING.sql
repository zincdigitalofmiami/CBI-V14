-- Vegas Intel - Opportunity Scoring Views
-- Composite scoring system for ranking upsell opportunities
-- Uses REAL cuisine multipliers from Glide data
-- Created: November 6, 2025

-- Base opportunity scores view
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.vegas_opportunity_scores` AS
WITH base_data AS (
  SELECT
    eri.event_id,
    eri.event_name,
    eri.event_date,
    eri.event_venue,
    eri.event_lat,
    eri.event_lng,
    eri.event_type,
    eri.expected_attendance,
    eri.restaurant_id,
    eri.restaurant_name,
    eri.restaurant_lat,
    eri.restaurant_lng,
    eri.distance_km,
    eri.fryer_count,
    eri.total_capacity_lbs,
    eri.cuisine_multiplier,
    eri.cuisine_type,
    eri.proximity_multiplier,
    eri.attendance_multiplier,
    eri.combined_impact_score,
    eri.baseline_weekly_gallons,
    eri.event_surge_gallons,
    eri.revenue_opportunity,
    eri.days_until
  FROM `cbi-v14.forecasting_data_warehouse.event_restaurant_impact` eri
),
scored_data AS (
  SELECT
    bd.*,
    -- Score components (0-100)
    (1 - (bd.distance_km / 10.0)) * 30 as score_proximity,  -- Max 30 points for proximity
    LEAST((bd.expected_attendance / 100000.0) * 30, 30) as score_attendance,  -- Max 30 points for attendance (100k attendees)
    LEAST((bd.fryer_count / 10.0) * 20, 20) as score_fryers,  -- Max 20 points for 10+ fryers
    LEAST((bd.cuisine_multiplier / 2.5) * 10, 10) as score_cuisine,  -- Max 10 points for high multiplier (Buffet 2.2)
    LEAST((bd.revenue_opportunity / 10000.0) * 10, 10) as score_revenue,  -- Max 10 points for $10k+ revenue
    -- Composite score
    ROUND(
      (1 - (bd.distance_km / 10.0)) * 30 +
      LEAST((bd.expected_attendance / 100000.0) * 30, 30) +
      LEAST((bd.fryer_count / 10.0) * 20, 20) +
      LEAST((bd.cuisine_multiplier / 2.5) * 10, 10) +
      LEAST((bd.revenue_opportunity / 10000.0) * 10, 10),
      0
    ) as opportunity_score
  FROM base_data bd
)
SELECT
  sd.*,
  -- Urgency classification
  CASE
    WHEN sd.days_until <= 7 THEN 'IMMEDIATE ACTION'
    WHEN sd.days_until <= 30 THEN 'HIGH PRIORITY'
    WHEN sd.days_until <= 90 THEN 'MODERATE'
    ELSE 'MONITOR'
  END as urgency_classification,
  -- Analysis bullets
  [
    CONCAT('Event ', sd.event_name, ' expected to draw ', FORMAT("%'d", sd.expected_attendance), ' attendees'),
    CONCAT('Restaurant located ', ROUND(sd.distance_km, 1), ' km from venue (',
      CASE WHEN sd.distance_km <= 0.5 THEN 'walking distance' ELSE 'short drive' END, ')'),
    CONCAT(CAST(sd.fryer_count as STRING), ' fryers with ', CAST(ROUND(sd.total_capacity_lbs) as STRING), ' lbs capacity (', sd.cuisine_type, ' ×', CAST(ROUND(sd.cuisine_multiplier, 1) as STRING), ')'),
    CONCAT('Baseline usage: ', CAST(sd.baseline_weekly_gallons as STRING), ' gal/week'),
    CONCAT('Expected surge: +', CAST(sd.event_surge_gallons as STRING), ' gal during event (+', CAST(ROUND(sd.event_surge_gallons / NULLIF(sd.baseline_weekly_gallons, 0) * 100, 0) as STRING), '%)'),
    CONCAT('Recommended action: Contact ', CAST(GREATEST(sd.days_until - 7, 0) as STRING), ' days before event for proactive delivery')
  ] as analysis_bullets,
  CONCAT('+', CAST(ROUND(sd.opportunity_score, 0) as STRING), '%') as opportunity_score_display
FROM scored_data sd
WHERE sd.opportunity_score >= 30  -- Filter for meaningful opportunities
ORDER BY sd.opportunity_score DESC;

-- Top opportunities view (one per event, top restaurant)
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.vegas_top_opportunities` AS
SELECT
  *,
  ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY opportunity_score DESC) as rn
FROM `cbi-v14.forecasting_data_warehouse.vegas_opportunity_scores`
WHERE days_until >= 0 AND days_until <= 90
QUALIFY rn = 1
ORDER BY opportunity_score DESC
LIMIT 50;

