-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- INTEGRATE WEATHER DATA INTO TRAINING DATASET
-- Add weather-based features for Brazil, Argentina, and US soybean regions
-- ============================================

-- Step 1: Create weather features from raw weather data
CREATE OR REPLACE TABLE `cbi-v14.models_v4.weather_features` AS
WITH weather_metrics AS (
  -- Daily weather aggregations by region
  SELECT
    DATE(date) as date,
    region,

    -- Temperature metrics (critical for crop development)
    AVG(temp_max) as avg_max_temp,
    AVG(temp_min) as avg_min_temp,
    AVG((temp_max + temp_min)/2) as avg_mean_temp,
    MAX(temp_max) as max_temp,
    MIN(temp_min) as min_temp,

    -- Precipitation metrics (critical for drought/flood risk)
    SUM(precip_mm) as total_precip_mm,
    AVG(precip_mm) as avg_daily_precip,
    MAX(precip_mm) as max_daily_precip,
    COUNT(CASE WHEN precip_mm < 1 THEN 1 END) as dry_days,
    COUNT(CASE WHEN precip_mm > 50 THEN 1 END) as heavy_rain_days,

    -- Weather extremes (risk indicators)
    COUNT(CASE WHEN temp_max > 35 THEN 1 END) as extreme_heat_days,
    COUNT(CASE WHEN temp_min < 5 THEN 1 END) as frost_days,
    COUNT(CASE WHEN precip_mm > 100 THEN 1 END) as flood_risk_days,

    -- Growing conditions score (0-100, higher is better)
    CASE
      WHEN AVG((temp_max + temp_min)/2) BETWEEN 20 AND 30
           AND SUM(precip_mm) BETWEEN 50 AND 150 THEN 90  -- Optimal conditions
      WHEN AVG((temp_max + temp_min)/2) BETWEEN 15 AND 35
           AND SUM(precip_mm) BETWEEN 25 AND 200 THEN 70  -- Good conditions
      WHEN (AVG((temp_max + temp_min)/2) < 15 OR AVG((temp_max + temp_min)/2) > 35)
           OR SUM(precip_mm) < 25 THEN 30  -- Poor conditions
      ELSE 50  -- Average conditions
    END as growing_conditions_score

  FROM `cbi-v14.forecasting_data_warehouse.weather_data`
  WHERE date >= '2020-01-01'
    AND region IN ('Brazil', 'Argentina', 'United States', 'Iowa', 'Illinois', 'Minnesota')
  GROUP BY DATE(date), region
),

-- Aggregate by key soybean regions
brazil_weather AS (
  SELECT
    date,
    'brazil' as region_group,
    AVG(avg_mean_temp) as temp_mean_c,
    SUM(total_precip_mm) as precip_total_mm,
    AVG(growing_conditions_score) as conditions_score,
    SUM(extreme_heat_days) as heat_stress_days,
    SUM(dry_days) as drought_days,
    SUM(heavy_rain_days) as flood_days
  FROM weather_metrics
  WHERE region LIKE '%Brazil%'
  GROUP BY date
),

argentina_weather AS (
  SELECT
    date,
    'argentina' as region_group,
    AVG(avg_mean_temp) as temp_mean_c,
    SUM(total_precip_mm) as precip_total_mm,
    AVG(growing_conditions_score) as conditions_score,
    SUM(extreme_heat_days) as heat_stress_days,
    SUM(dry_days) as drought_days,
    SUM(heavy_rain_days) as flood_days
  FROM weather_metrics
  WHERE region LIKE '%Argentina%'
  GROUP BY date
),

us_weather AS (
  SELECT
    date,
    'us_midwest' as region_group,
    AVG(avg_mean_temp) as temp_mean_c,
    SUM(total_precip_mm) as precip_total_mm,
    AVG(growing_conditions_score) as conditions_score,
    SUM(extreme_heat_days) as heat_stress_days,
    SUM(dry_days) as drought_days,
    SUM(heavy_rain_days) as flood_days
  FROM weather_metrics
  WHERE region IN ('Iowa', 'Illinois', 'Minnesota', 'United States')
  GROUP BY date
)

-- Combine all regions into wide format
SELECT
  COALESCE(b.date, a.date, u.date) as date,

  -- Brazil weather features
  b.temp_mean_c as brazil_temp_c,
  b.precip_total_mm as brazil_precip_mm,
  b.conditions_score as brazil_conditions_score,
  b.heat_stress_days as brazil_heat_stress_days,
  b.drought_days as brazil_drought_days,
  b.flood_days as brazil_flood_days,

  -- Argentina weather features
  a.temp_mean_c as argentina_temp_c,
  a.precip_total_mm as argentina_precip_mm,
  a.conditions_score as argentina_conditions_score,
  a.heat_stress_days as argentina_heat_stress_days,
  a.drought_days as argentina_drought_days,
  a.flood_days as argentina_flood_days,

  -- US Midwest weather features
  u.temp_mean_c as us_midwest_temp_c,
  u.precip_total_mm as us_midwest_precip_mm,
  u.conditions_score as us_midwest_conditions_score,
  u.heat_stress_days as us_midwest_heat_stress_days,
  u.drought_days as us_midwest_drought_days,
  u.flood_days as us_midwest_flood_days,

  -- Composite weather risk score
  (
    COALESCE(b.conditions_score, 50) * 0.4 +  -- Brazil (40% of global supply)
    COALESCE(a.conditions_score, 50) * 0.3 +  -- Argentina (30% of global supply)
    COALESCE(u.conditions_score, 50) * 0.3    -- US (30% of global supply)
  ) / 100.0 as global_weather_risk_score,

  CURRENT_TIMESTAMP() as created_at

FROM brazil_weather b
FULL OUTER JOIN argentina_weather a ON b.date = a.date
FULL OUTER JOIN us_weather u ON COALESCE(b.date, a.date) = u.date;

-- Step 2: Update training dataset with weather features
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET
  -- Brazil weather
  brazil_temp_c = w.brazil_temp_c,
  brazil_precip_mm = w.brazil_precip_mm,
  brazil_conditions_score = w.brazil_conditions_score,
  brazil_heat_stress_days = w.brazil_heat_stress_days,
  brazil_drought_days = w.brazil_drought_days,
  brazil_flood_days = w.brazil_flood_days,

  -- Argentina weather
  argentina_temp_c = w.argentina_temp_c,
  argentina_precip_mm = w.argentina_precip_mm,
  argentina_conditions_score = w.argentina_conditions_score,
  argentina_heat_stress_days = w.argentina_heat_stress_days,
  argentina_drought_days = w.argentina_drought_days,
  argentina_flood_days = w.argentina_flood_days,

  -- US Midwest weather
  us_midwest_temp_c = w.us_midwest_temp_c,
  us_midwest_precip_mm = w.us_midwest_precip_mm,
  us_midwest_conditions_score = w.us_midwest_conditions_score,
  us_midwest_heat_stress_days = w.us_midwest_heat_stress_days,
  us_midwest_drought_days = w.us_midwest_drought_days,
  us_midwest_flood_days = w.us_midwest_flood_days,

  -- Global weather risk
  global_weather_risk_score = w.global_weather_risk_score

FROM `cbi-v14.models_v4.weather_features` w
WHERE t.date = w.date;

-- Step 3: Verify integration
SELECT
  'Weather Integration Results' as check_type,
  COUNTIF(brazil_temp_c IS NOT NULL) as brazil_weather_rows,
  COUNTIF(argentina_temp_c IS NOT NULL) as argentina_weather_rows,
  COUNTIF(us_midwest_temp_c IS NOT NULL) as us_weather_rows,
  COUNTIF(global_weather_risk_score IS NOT NULL) as global_risk_rows,
  COUNT(*) as total_rows,
  ROUND(AVG(global_weather_risk_score), 3) as avg_global_risk
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE global_weather_risk_score IS NOT NULL;

-- Step 4: Clean up temp table
DROP TABLE IF EXISTS `cbi-v14.models_v4.weather_features`;


