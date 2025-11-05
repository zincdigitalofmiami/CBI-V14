-- ============================================================
-- OPPORTUNITY SCORING SYSTEM (FREE - Pure BigQuery Math)
-- Generates +47% style opportunity scores with detailed analysis
-- ============================================================

CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.vegas_opportunity_scores` AS
WITH base_opportunities AS (
  SELECT 
    event_id,
    restaurant_id,
    event_name,
    restaurant_name,
    event_date,
    event_venue,
    event_type,
    expected_attendance,
    distance_km,
    proximity_multiplier,
    attendance_multiplier,
    combined_impact_score,
    weekly_base_gallons,
    event_surge_gallons,
    revenue_opportunity,
    days_until,
    cuisine_type,
    cuisine_multiplier,
    fryer_count,
    total_capacity_lbs,
    
    -- Revenue score (0-100): Normalize revenue to percentage
    LEAST(100, ROUND((revenue_opportunity / 5000.0) * 100, 0)) as revenue_score,
    
    -- Proximity score (0-100): Closer = higher
    CASE 
      WHEN distance_km < 0.5 THEN 100
      WHEN distance_km < 1.0 THEN 85
      WHEN distance_km < 2.0 THEN 70
      WHEN distance_km < 5.0 THEN 50
      WHEN distance_km < 10.0 THEN 30
      ELSE 10
    END as proximity_score,
    
    -- Urgency score (0-100): Sooner = higher
    CASE 
      WHEN days_until <= 7 THEN 100
      WHEN days_until <= 14 THEN 85
      WHEN days_until <= 30 THEN 70
      WHEN days_until <= 60 THEN 50
      WHEN days_until <= 90 THEN 30
      ELSE 10
    END as urgency_score,
    
    -- Event size score (0-100): Larger = higher
    CASE 
      WHEN expected_attendance >= 100000 THEN 100  -- F1, CES
      WHEN expected_attendance >= 50000 THEN 85    -- SEMA
      WHEN expected_attendance >= 20000 THEN 70    -- Raiders
      WHEN expected_attendance >= 10000 THEN 50    -- Golden Knights
      ELSE 30
    END as event_size_score,
    
    -- Capacity score (0-100): More fryers = higher potential
    CASE 
      WHEN fryer_count >= 10 THEN 100
      WHEN fryer_count >= 5 THEN 80
      WHEN fryer_count >= 3 THEN 60
      ELSE 40
    END as capacity_score
    
  FROM `cbi-v14.forecasting_data_warehouse.event_restaurant_impact`
  WHERE revenue_opportunity > 0
),
scored_opportunities AS (
  SELECT 
    *,
    -- Composite opportunity score (weighted average)
    ROUND(
      (revenue_score * 0.30) +       -- 30% weight on revenue
      (proximity_score * 0.25) +     -- 25% weight on proximity
      (urgency_score * 0.20) +       -- 20% weight on urgency
      (event_size_score * 0.15) +    -- 15% weight on event size
      (capacity_score * 0.10),       -- 10% weight on restaurant capacity
      0
    ) as opportunity_score,
    
    -- Detailed analysis bullets
    ARRAY[
      CONCAT('Event ', event_name, ' expected to draw ', FORMAT("%'d", expected_attendance), ' attendees'),
      CONCAT('Restaurant located ', CAST(ROUND(distance_km, 1) as STRING), ' km from venue (', 
        CASE 
          WHEN distance_km < 0.5 THEN 'walking distance'
          WHEN distance_km < 2.0 THEN 'very close'
          WHEN distance_km < 5.0 THEN 'nearby'
          ELSE 'moderate distance'
        END, ')'),
      CONCAT(CAST(fryer_count as STRING), ' fryers with ', CAST(ROUND(total_capacity_lbs, 0) as STRING), ' lbs capacity (', cuisine_type, ' cuisine ×', CAST(ROUND(cuisine_multiplier, 1) as STRING), ')'),
      CONCAT('Baseline usage: ', CAST(ROUND(weekly_base_gallons, 0) as STRING), ' gal/week'),
      CONCAT('Expected surge: +', CAST(event_surge_gallons as STRING), ' gal during event (+', CAST(ROUND((event_surge_gallons / NULLIF(weekly_base_gallons, 0)) * 100, 0) as STRING), '%)'),
      CONCAT('Recommended action: Contact ', CAST(days_until - 7 as STRING), ' days before event for proactive delivery')
    ] as analysis_bullets
    
  FROM base_opportunities
)
SELECT 
  *,
  -- Display format: +47% style
  CONCAT('+', CAST(opportunity_score as STRING), '%') as opportunity_score_display,
  
  -- Urgency classification
  CASE 
    WHEN urgency_score >= 85 THEN 'IMMEDIATE ACTION'
    WHEN urgency_score >= 70 THEN 'HIGH PRIORITY'
    WHEN urgency_score >= 50 THEN 'MODERATE'
    ELSE 'MONITOR'
  END as urgency_classification
  
FROM scored_opportunities
ORDER BY opportunity_score DESC, revenue_opportunity DESC;


-- ============================================================
-- TOP OPPORTUNITIES VIEW (For Dashboard)
-- ============================================================

CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.vegas_top_opportunities` AS
SELECT 
  ROW_NUMBER() OVER (ORDER BY opportunity_score DESC) as rank,
  event_id,
  restaurant_id,
  event_name,
  restaurant_name,
  event_date,
  event_venue,
  expected_attendance,
  distance_km,
  opportunity_score,
  opportunity_score_display,
  revenue_opportunity,
  event_surge_gallons,
  days_until,
  urgency_classification,
  analysis_bullets,
  proximity_multiplier,
  attendance_multiplier,
  combined_impact_score
FROM `cbi-v14.forecasting_data_warehouse.vegas_opportunity_scores`
WHERE opportunity_score >= 30  -- Minimum 30% opportunity score
ORDER BY opportunity_score DESC
LIMIT 50;

