-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- FIX REMAINING 9 COLUMNS (99.56% NULL)
-- Attempts to fill: CPI, GDP, US Midwest Weather
-- ============================================

-- ============================================
-- PART 1: CPI YEAR-OVER-YEAR (cpi_yoy)
-- Calculate from limited CPIAUCSL data
-- ============================================

CREATE OR REPLACE TABLE `cbi-v14.models_v4.cpi_yoy_daily` AS
WITH 
-- Get all training dates
training_dates AS (
  SELECT DISTINCT date
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  ORDER BY date
),

-- Get CPI data (monthly)
cpi_monthly AS (
  SELECT 
    CAST(time AS DATE) as date,
    value as cpi_value
  FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
  WHERE indicator = 'CPIAUCSL' AND value IS NOT NULL
),

-- Calculate YoY change (monthly CPI, calculate vs same month previous year)
cpi_with_yoy AS (
  SELECT 
    c1.date,
    c1.cpi_value,
    c2.cpi_value as cpi_value_prev_year,
    (c1.cpi_value / c2.cpi_value - 1) * 100 as cpi_yoy
  FROM cpi_monthly c1
  LEFT JOIN cpi_monthly c2 
    ON EXTRACT(YEAR FROM c1.date) = EXTRACT(YEAR FROM c2.date) + 1
    AND EXTRACT(MONTH FROM c1.date) = EXTRACT(MONTH FROM c2.date)
),

-- Forward-fill to daily and back-fill early dates
cpi_daily_filled AS (
  SELECT 
    td.date,
    -- Forward fill CPI YoY
    LAST_VALUE(cwy.cpi_yoy IGNORE NULLS) OVER (
      ORDER BY td.date 
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as cpi_yoy
  FROM training_dates td
  LEFT JOIN cpi_with_yoy cwy ON td.date = cwy.date
)

SELECT 
  date,
  cpi_yoy
FROM cpi_daily_filled
WHERE cpi_yoy IS NOT NULL
ORDER BY date;

-- Apply CPI YoY fix
MERGE `cbi-v14.models_v4.training_dataset_super_enriched` AS target
USING (
  SELECT date, cpi_yoy
  FROM `cbi-v14.models_v4.cpi_yoy_daily`
  QUALIFY ROW_NUMBER() OVER (PARTITION BY date ORDER BY date DESC) = 1
) AS source
ON target.date = source.date
WHEN MATCHED THEN UPDATE SET
  cpi_yoy = COALESCE(target.cpi_yoy, source.cpi_yoy);

-- ============================================
-- PART 2: GDP GROWTH (econ_gdp_growth, gdp_growth)
-- Note: GDP data needs to be fetched from FRED API first
-- This script assumes FRED data will be fetched using scripts/fetch_fred_economic_data.py
-- For now, we'll check if any GDP data exists
-- ============================================

-- Check if GDP data exists in economic_indicators
SELECT 
  'GDP DATA CHECK' as check_type,
  COUNT(*) as total_gdp_records,
  COUNT(DISTINCT CAST(time AS DATE)) as unique_dates,
  MIN(CAST(time AS DATE)) as earliest,
  MAX(CAST(time AS DATE)) as latest
FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
WHERE indicator LIKE '%GDP%' AND value IS NOT NULL;

-- If GDP data exists, create daily forward-filled version
CREATE OR REPLACE TABLE `cbi-v14.models_v4.gdp_growth_daily` AS
WITH 
training_dates AS (
  SELECT DISTINCT date
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  ORDER BY date
),

-- Get GDP data (quarterly typically)
gdp_data AS (
  SELECT 
    CAST(time AS DATE) as date,
    value as gdp_value
  FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
  WHERE (indicator LIKE '%GDP%' OR indicator = 'GDPC1') 
    AND value IS NOT NULL
    AND value > 0
),

-- Calculate quarterly growth rate
gdp_growth_calc AS (
  SELECT 
    g1.date,
    (g1.gdp_value / LAG(g1.gdp_value) OVER (ORDER BY g1.date) - 1) * 100 as gdp_growth
  FROM gdp_data g1
),

-- Forward-fill to daily
gdp_daily_filled AS (
  SELECT 
    td.date,
    LAST_VALUE(gg.gdp_growth IGNORE NULLS) OVER (
      ORDER BY td.date 
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as gdp_growth
  FROM training_dates td
  LEFT JOIN gdp_growth_calc gg ON td.date = gg.date
)

SELECT 
  date,
  gdp_growth
FROM gdp_daily_filled
WHERE gdp_growth IS NOT NULL
ORDER BY date;

-- Apply GDP growth fix (if data exists)
MERGE `cbi-v14.models_v4.training_dataset_super_enriched` AS target
USING (
  SELECT date, gdp_growth
  FROM `cbi-v14.models_v4.gdp_growth_daily`
  QUALIFY ROW_NUMBER() OVER (PARTITION BY date ORDER BY date DESC) = 1
) AS source
ON target.date = source.date
WHEN MATCHED THEN UPDATE SET
  econ_gdp_growth = COALESCE(target.econ_gdp_growth, source.gdp_growth),
  gdp_growth = COALESCE(target.gdp_growth, source.gdp_growth);

-- ============================================
-- PART 3: US MIDWEST WEATHER
-- Check if weather_us_midwest_daily has data, if not, check other sources
-- ============================================

-- Check what weather data exists
SELECT 
  'US MIDWEST WEATHER CHECK' as check_type,
  COUNT(*) as total_records,
  MIN(date) as earliest,
  MAX(date) as latest
FROM `cbi-v14.forecasting_data_warehouse.weather_us_midwest_daily`;

-- If weather_us_midwest_daily is empty, check weather_data table
SELECT 
  'WEATHER_DATA TABLE CHECK' as check_type,
  COUNT(*) as total_records,
  COUNT(DISTINCT date) as unique_dates,
  MIN(date) as earliest,
  MAX(date) as latest,
  COUNTIF(region = 'US_Midwest' OR region LIKE '%Midwest%') as midwest_records
FROM `cbi-v14.forecasting_data_warehouse.weather_data`;

-- Create US Midwest weather daily complete (if data exists)
CREATE OR REPLACE TABLE `cbi-v14.models_v4.us_midwest_weather_daily` AS
WITH 
training_dates AS (
  SELECT DISTINCT date
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  ORDER BY date
),

-- Get US Midwest weather from weather_data table
weather_midwest AS (
  SELECT 
    date,
    (temp_max + temp_min) / 2.0 as temp_c,  -- Calculate average from max/min
    precip_mm,
    temp_max,
    temp_min
  FROM `cbi-v14.forecasting_data_warehouse.weather_data`
  WHERE region = 'US_Midwest'
    AND temp_max IS NOT NULL
    AND temp_min IS NOT NULL
),

-- Aggregate and forward-fill
weather_daily_filled AS (
  SELECT 
    td.date,
    -- Forward fill temperature
    LAST_VALUE(wm.temp_c IGNORE NULLS) OVER (
      ORDER BY td.date 
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as temp_c,
    -- Forward fill precipitation
    LAST_VALUE(wm.precip_mm IGNORE NULLS) OVER (
      ORDER BY td.date 
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as precip_mm
  FROM training_dates td
  LEFT JOIN weather_midwest wm ON td.date = wm.date
)

SELECT 
  date,
  temp_c,
  precip_mm,
  -- Calculate derived fields
  CASE WHEN temp_c > 30 THEN 1 ELSE 0 END as heat_stress_days,
  CASE WHEN precip_mm < 5 AND temp_c > 25 THEN 1 ELSE 0 END as drought_days,
  CASE WHEN precip_mm > 50 THEN 1 ELSE 0 END as flood_days,
  -- Simple conditions score (0-100 scale)
  CASE 
    WHEN temp_c BETWEEN 15 AND 25 AND precip_mm BETWEEN 5 AND 30 THEN 100
    WHEN temp_c BETWEEN 10 AND 30 AND precip_mm BETWEEN 0 AND 50 THEN 75
    WHEN temp_c BETWEEN 5 AND 35 AND precip_mm BETWEEN 0 AND 100 THEN 50
    ELSE 25
  END as conditions_score
FROM weather_daily_filled
WHERE temp_c IS NOT NULL
ORDER BY date;

-- Apply US Midwest weather fix (if data exists)
MERGE `cbi-v14.models_v4.training_dataset_super_enriched` AS target
USING (
  SELECT 
    date,
    temp_c as us_midwest_temp_c,
    precip_mm as us_midwest_precip_mm,
    conditions_score as us_midwest_conditions_score,
    heat_stress_days as us_midwest_heat_stress_days,
    drought_days as us_midwest_drought_days,
    flood_days as us_midwest_flood_days
  FROM `cbi-v14.models_v4.us_midwest_weather_daily`
  QUALIFY ROW_NUMBER() OVER (PARTITION BY date ORDER BY date DESC) = 1
) AS source
ON target.date = source.date
WHEN MATCHED THEN UPDATE SET
  us_midwest_temp_c = COALESCE(target.us_midwest_temp_c, source.us_midwest_temp_c),
  us_midwest_precip_mm = COALESCE(target.us_midwest_precip_mm, source.us_midwest_precip_mm),
  us_midwest_conditions_score = COALESCE(target.us_midwest_conditions_score, source.us_midwest_conditions_score),
  us_midwest_heat_stress_days = COALESCE(target.us_midwest_heat_stress_days, source.us_midwest_heat_stress_days),
  us_midwest_drought_days = COALESCE(target.us_midwest_drought_days, source.us_midwest_drought_days),
  us_midwest_flood_days = COALESCE(target.us_midwest_flood_days, source.us_midwest_flood_days);

-- ============================================
-- PART 4: FINAL STATUS CHECK
-- ============================================

SELECT 
  'REMAINING NULLS STATUS' as check_type,
  COUNT(*) as total_rows,
  
  -- Count remaining NULLs
  COUNTIF(cpi_yoy IS NULL) as cpi_yoy_nulls,
  COUNTIF(econ_gdp_growth IS NULL) as econ_gdp_growth_nulls,
  COUNTIF(gdp_growth IS NULL) as gdp_growth_nulls,
  COUNTIF(us_midwest_temp_c IS NULL) as us_midwest_temp_nulls,
  COUNTIF(us_midwest_precip_mm IS NULL) as us_midwest_precip_nulls,
  COUNTIF(us_midwest_conditions_score IS NULL) as us_midwest_conditions_nulls,
  COUNTIF(us_midwest_heat_stress_days IS NULL) as us_midwest_heat_nulls,
  COUNTIF(us_midwest_drought_days IS NULL) as us_midwest_drought_nulls,
  COUNTIF(us_midwest_flood_days IS NULL) as us_midwest_flood_nulls,
  
  -- Coverage percentages
  ROUND((1 - COUNTIF(cpi_yoy IS NULL) / COUNT(*)) * 100, 1) as cpi_yoy_coverage,
  ROUND((1 - COUNTIF(econ_gdp_growth IS NULL) / COUNT(*)) * 100, 1) as econ_gdp_coverage,
  ROUND((1 - COUNTIF(gdp_growth IS NULL) / COUNT(*)) * 100, 1) as gdp_growth_coverage,
  ROUND((1 - COUNTIF(us_midwest_temp_c IS NULL) / COUNT(*)) * 100, 1) as us_midwest_temp_coverage
  
FROM `cbi-v14.models_v4.training_dataset_super_enriched`;

