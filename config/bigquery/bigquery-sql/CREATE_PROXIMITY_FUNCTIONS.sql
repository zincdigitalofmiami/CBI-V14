-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- Vegas Intel - Proximity Calculation Functions
-- FREE Implementation - No External APIs Required
-- Created: November 6, 2025

-- Haversine Distance Function
-- Calculates distance between two lat/lng points in kilometers
CREATE OR REPLACE FUNCTION `cbi-v14.forecasting_data_warehouse.haversine_distance`(
  lat1 FLOAT64, lon1 FLOAT64, lat2 FLOAT64, lon2 FLOAT64
) RETURNS FLOAT64 AS ((
  ACOS(
    SIN(lat1 * 3.141592653589793 / 180.0) * SIN(lat2 * 3.141592653589793 / 180.0) + 
    COS(lat1 * 3.141592653589793 / 180.0) * COS(lat2 * 3.141592653589793 / 180.0) * COS((lon2 - lon1) * 3.141592653589793 / 180.0)
  ) * 6371  -- Earth radius in km
));

-- Proximity Multiplier Function
-- Returns impact multiplier based on distance (closer = higher impact)
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

