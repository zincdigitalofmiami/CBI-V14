-- ============================================================================
-- BUILD WEATHER HISTORY
-- Sources: BigQuery Public Datasets (NOAA GSOD, Storm Events)
-- Date: 2025-11-24
-- COMPLIANT: Universal Calculator Standard v1.0
-- ============================================================================

-- ============================================================================
-- 1. SEGMENTED WEATHER HISTORY (NOAA GSOD)
-- ============================================================================
-- GSOD = Global Surface Summary of Day
-- Units: temp in F, precip in hundredths of inches, wind in knots
-- Note: Region mapping is approximate; station coordinates define boundaries

CREATE OR REPLACE TABLE `cbi-v14.raw_intelligence.weather_segmented`
PARTITION BY date
CLUSTER BY region, state AS

WITH raw_weather AS (
  SELECT 
    PARSE_DATE('%Y%m%d', CONCAT(year, mo, da)) AS date,
    stn AS station_id,
    name AS station_name,
    state,
    'US' AS country,
    -- Lat/Lon for region calculation
    CAST(lat AS FLOAT64) AS lat,
    CAST(lon AS FLOAT64) AS lon,
    -- Temperature (F)
    CAST(temp AS FLOAT64) AS temp_avg,
    CAST(min AS FLOAT64) AS temp_min,
    CAST(max AS FLOAT64) AS temp_max,
    -- Precipitation (inches, convert from hundredths)
    SAFE_DIVIDE(CAST(prcp AS FLOAT64), 100) AS precip_in,
    -- Wind (knots)
    CAST(wdsp AS FLOAT64) AS wind_speed,
    -- Snow/rain flags
    CAST(fog AS INT64) AS fog_flag,
    CAST(rain_drizzle AS INT64) AS rain_flag,
    CAST(snow_ice_pellets AS INT64) AS snow_flag,
    CAST(hail AS INT64) AS hail_flag
  FROM `bigquery-public-data.noaa_gsod.gsod20*`
  WHERE _TABLE_SUFFIX BETWEEN '10' AND '25'  -- 2010-2025
    AND lat IS NOT NULL
    AND lon IS NOT NULL
    AND SAFE_CAST(lat AS FLOAT64) BETWEEN 25 AND 50  -- Continental US
    AND SAFE_CAST(lon AS FLOAT64) BETWEEN -125 AND -65
)

SELECT
  date,
  station_id,
  station_name,
  state,
  country,
  lat,
  lon,
  -- Region segmentation based on soy belt geography
  CASE
    -- Midwest Core (IA, IL, IN, OH, MN, WI, MI, MO)
    WHEN lat BETWEEN 38 AND 48 AND lon BETWEEN -97 AND -80 THEN 'US_Midwest_Core'
    -- Great Plains (NE, KS, SD, ND)
    WHEN lat BETWEEN 37 AND 49 AND lon BETWEEN -104 AND -97 THEN 'US_Great_Plains'
    -- Delta Region (AR, MS, LA)
    WHEN lat BETWEEN 29 AND 37 AND lon BETWEEN -94 AND -88 THEN 'US_Delta'
    -- Gulf Coast (TX coast, LA coast)
    WHEN lat BETWEEN 26 AND 32 AND lon BETWEEN -98 AND -88 THEN 'US_Gulf_Coast'
    -- Southeast (AL, GA, SC)
    WHEN lat BETWEEN 30 AND 36 AND lon BETWEEN -88 AND -79 THEN 'US_Southeast'
    ELSE 'US_Other'
  END AS region,
  -- Weather metrics
  temp_avg,
  temp_min,
  temp_max,
  precip_in,
  wind_speed,
  fog_flag,
  rain_flag,
  snow_flag,
  hail_flag,
  -- GDD calculation: max(0, (Tmax + Tmin)/2 - base_temp)
  -- Using 50F base for soybeans
  GREATEST(0, SAFE_DIVIDE(COALESCE(temp_max, 0) + COALESCE(temp_min, 0), 2) - 50) AS gdd_50f,
  CURRENT_TIMESTAMP() AS ingestion_ts
FROM raw_weather
WHERE date IS NOT NULL
  AND temp_avg IS NOT NULL;


-- ============================================================================
-- 2. STORM EVENTS HISTORY (NOAA Severe Storms)
-- ============================================================================
-- Captures drought, flood, hail, excessive heat events
-- Critical for crop damage and logistics disruption signals

CREATE OR REPLACE TABLE `cbi-v14.raw_intelligence.storm_events`
PARTITION BY event_date
CLUSTER BY event_type, state AS

SELECT
  DATE(event_begin_time) AS event_date,
  DATE(event_end_time) AS event_end_date,
  event_id,
  event_type,
  state,
  state_fips,
  cz_name AS county_zone_name,
  cz_type AS county_zone_type,
  -- Location
  begin_lat,
  begin_lon,
  end_lat,
  end_lon,
  -- Damage (COALESCE per Universal Calculator Standard)
  COALESCE(damage_crops, 0) AS damage_crops,
  COALESCE(damage_property, 0) AS damage_property,
  -- Casualties
  COALESCE(deaths_direct, 0) AS deaths_direct,
  COALESCE(deaths_indirect, 0) AS deaths_indirect,
  COALESCE(injuries_direct, 0) AS injuries_direct,
  COALESCE(injuries_indirect, 0) AS injuries_indirect,
  -- Narrative
  event_narrative,
  episode_narrative,
  -- Magnitude (for tornado/wind)
  magnitude,
  magnitude_type,
  -- Timestamps
  event_begin_time,
  event_end_time,
  CURRENT_TIMESTAMP() AS ingestion_ts
FROM `bigquery-public-data.noaa_historic_severe_storms.storms_*`
WHERE _TABLE_SUFFIX >= '2010'
  AND event_type IN (
    'Drought',
    'Flood',
    'Flash Flood',
    'Coastal Flood',
    'Hail',
    'Excessive Heat',
    'Heat',
    'Frost/Freeze',
    'Tornado',
    'Thunderstorm Wind',
    'High Wind',
    'Wildfire'
  )
  AND event_begin_time IS NOT NULL;


-- ============================================================================
-- 3. WEATHER FEATURES (DAILY AGGREGATION BY REGION)
-- ============================================================================
-- Aggregates station-level data to regional daily features
-- These become inputs to features.weather_daily_region

CREATE OR REPLACE TABLE `cbi-v14.features.weather_daily_region`
PARTITION BY date
CLUSTER BY region AS

WITH regional_daily AS (
  SELECT
    date,
    region,
    -- Temperature aggregations
    AVG(temp_avg) AS temp_avg,
    MIN(temp_min) AS temp_min,
    MAX(temp_max) AS temp_max,
    STDDEV_SAMP(temp_avg) AS temp_std,
    -- Precipitation aggregations
    AVG(COALESCE(precip_in, 0)) AS precip_avg,
    SUM(COALESCE(precip_in, 0)) AS precip_total,
    MAX(COALESCE(precip_in, 0)) AS precip_max,
    -- Wind
    AVG(wind_speed) AS wind_avg,
    MAX(wind_speed) AS wind_max,
    -- GDD
    AVG(gdd_50f) AS gdd_avg,
    SUM(gdd_50f) AS gdd_total,
    -- Station count (data quality indicator)
    COUNT(DISTINCT station_id) AS station_count,
    -- Weather event flags
    SUM(fog_flag) AS fog_stations,
    SUM(rain_flag) AS rain_stations,
    SUM(snow_flag) AS snow_stations,
    SUM(hail_flag) AS hail_stations
  FROM `cbi-v14.raw_intelligence.weather_segmented`
  GROUP BY date, region
),

-- Add rolling statistics and anomalies
with_rolling AS (
  SELECT
    rd.*,
    -- 7-day rolling temperature
    AVG(temp_avg) OVER (
      PARTITION BY region 
      ORDER BY date 
      ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS temp_avg_7d,
    -- 30-day rolling temperature
    AVG(temp_avg) OVER (
      PARTITION BY region 
      ORDER BY date 
      ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS temp_avg_30d,
    -- 30-day rolling precipitation
    SUM(precip_total) OVER (
      PARTITION BY region 
      ORDER BY date 
      ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS precip_30d_total,
    -- 30-day cumulative GDD
    SUM(gdd_total) OVER (
      PARTITION BY region 
      ORDER BY date 
      ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS gdd_30d_cumulative,
    -- Temperature standard deviation for anomaly calculation
    STDDEV_SAMP(temp_avg) OVER (
      PARTITION BY region 
      ORDER BY date 
      ROWS BETWEEN 59 PRECEDING AND CURRENT ROW
    ) AS temp_std_60d,
    -- Historical mean (60-day)
    AVG(temp_avg) OVER (
      PARTITION BY region 
      ORDER BY date 
      ROWS BETWEEN 59 PRECEDING AND CURRENT ROW
    ) AS temp_mean_60d
  FROM regional_daily rd
)

SELECT
  date,
  region,
  temp_avg,
  temp_min,
  temp_max,
  temp_avg_7d,
  temp_avg_30d,
  -- Temperature anomaly (z-score)
  SAFE_DIVIDE(temp_avg - temp_mean_60d, NULLIF(temp_std_60d, 0)) AS temp_anomaly_zscore,
  precip_avg,
  precip_total,
  precip_max,
  precip_30d_total,
  wind_avg,
  wind_max,
  gdd_avg,
  gdd_total,
  gdd_30d_cumulative,
  station_count,
  fog_stations,
  rain_stations,
  snow_stations,
  hail_stations,
  CURRENT_TIMESTAMP() AS processed_at
FROM with_rolling;


-- ============================================================================
-- 4. STORM EVENTS DAILY AGGREGATION
-- ============================================================================
-- Aggregates storm events to daily counts by region

CREATE OR REPLACE TABLE `cbi-v14.features.storm_events_daily`
PARTITION BY date
CLUSTER BY region AS

SELECT
  event_date AS date,
  CASE
    WHEN state IN ('IA', 'IL', 'IN', 'OH', 'MN', 'WI', 'MI', 'MO') THEN 'US_Midwest_Core'
    WHEN state IN ('NE', 'KS', 'SD', 'ND') THEN 'US_Great_Plains'
    WHEN state IN ('AR', 'MS', 'LA') THEN 'US_Delta'
    WHEN state IN ('TX', 'LA') AND begin_lat < 32 THEN 'US_Gulf_Coast'
    WHEN state IN ('AL', 'GA', 'SC') THEN 'US_Southeast'
    ELSE 'US_Other'
  END AS region,
  -- Event counts by type
  COUNTIF(event_type = 'Drought') AS drought_events,
  COUNTIF(event_type IN ('Flood', 'Flash Flood', 'Coastal Flood')) AS flood_events,
  COUNTIF(event_type = 'Hail') AS hail_events,
  COUNTIF(event_type IN ('Excessive Heat', 'Heat')) AS heat_events,
  COUNTIF(event_type = 'Frost/Freeze') AS freeze_events,
  COUNTIF(event_type = 'Tornado') AS tornado_events,
  COUNTIF(event_type IN ('Thunderstorm Wind', 'High Wind')) AS wind_events,
  COUNTIF(event_type = 'Wildfire') AS wildfire_events,
  -- Total events
  COUNT(*) AS total_events,
  -- Damage totals
  SUM(damage_crops) AS total_crop_damage,
  SUM(damage_property) AS total_property_damage,
  -- Casualty totals
  SUM(deaths_direct + deaths_indirect) AS total_deaths,
  SUM(injuries_direct + injuries_indirect) AS total_injuries,
  CURRENT_TIMESTAMP() AS processed_at
FROM `cbi-v14.raw_intelligence.storm_events`
GROUP BY event_date, 
  CASE
    WHEN state IN ('IA', 'IL', 'IN', 'OH', 'MN', 'WI', 'MI', 'MO') THEN 'US_Midwest_Core'
    WHEN state IN ('NE', 'KS', 'SD', 'ND') THEN 'US_Great_Plains'
    WHEN state IN ('AR', 'MS', 'LA') THEN 'US_Delta'
    WHEN state IN ('TX', 'LA') AND begin_lat < 32 THEN 'US_Gulf_Coast'
    WHEN state IN ('AL', 'GA', 'SC') THEN 'US_Southeast'
    ELSE 'US_Other'
  END;


-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT 'weather_segmented' AS table_name, COUNT(*) AS row_count, MIN(date) AS min_date, MAX(date) AS max_date
FROM `cbi-v14.raw_intelligence.weather_segmented`
UNION ALL
SELECT 'storm_events', COUNT(*), MIN(event_date), MAX(event_date)
FROM `cbi-v14.raw_intelligence.storm_events`
UNION ALL
SELECT 'weather_daily_region', COUNT(*), MIN(date), MAX(date)
FROM `cbi-v14.features.weather_daily_region`
UNION ALL
SELECT 'storm_events_daily', COUNT(*), MIN(date), MAX(date)
FROM `cbi-v14.features.storm_events_daily`;


