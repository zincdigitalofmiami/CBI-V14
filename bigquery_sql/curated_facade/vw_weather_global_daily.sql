CREATE OR REPLACE VIEW `cbi-v14.curated.vw_weather_global_daily`
OPTIONS(
  friendly_name="vw_weather_global_daily",
  description="Unified global weather data from all regional weather tables. Combines Brazil, Argentina, Paraguay, Uruguay, and US Midwest weather data with geopolitical weighting for Trump tariff scenario analysis."
)
AS
WITH all_weather_data AS (
  -- Brazil weather (30% weight - Mato Grosso production belt)
  SELECT 
    date,
    station_id,
    state as region,
    'Brazil' as country,
    precip_mm,
    temp_max_c as temp_max,
    temp_min_c as temp_min,
    source_name,
    confidence_score,
    ingest_timestamp_utc,
    provenance_uuid,
    0.30 as geopolitical_weight,
    'Mato Grosso production belt - critical for soybean exports' as geopolitical_notes
  FROM `cbi-v14.forecasting_data_warehouse.weather_brazil_daily`
  
  UNION ALL
  
  -- Argentina weather (40% weight - Rosario port critical)
  SELECT 
    date,
    station_id,
    province as region,
    'Argentina' as country,
    precip_mm,
    temp_max_c as temp_max,
    temp_min_c as temp_min,
    source_name,
    confidence_score,
    ingest_timestamp_utc,
    provenance_uuid,
    0.40 as geopolitical_weight,
    'Rosario port critical - largest soybean export hub' as geopolitical_notes
  FROM `cbi-v14.forecasting_data_warehouse.weather_argentina_daily`
  
  UNION ALL
  
  -- Paraguay weather (15% weight - China hedge if US collapses)
  SELECT 
    date,
    station_id,
    region,
    'Paraguay' as country,
    precip_mm,
    temp_max_c as temp_max,
    temp_min_c as temp_min,
    source_name,
    confidence_score,
    ingest_timestamp_utc,
    provenance_uuid,
    0.15 as geopolitical_weight,
    'China hedge if US collapses - strategic alternative supplier' as geopolitical_notes
  FROM `cbi-v14.forecasting_data_warehouse.weather_paraguay_daily`
  
  UNION ALL
  
  -- Uruguay weather (5% weight - boutique quality supplier)
  SELECT 
    date,
    station_id,
    region,
    'Uruguay' as country,
    precip_mm,
    temp_max_c as temp_max,
    temp_min_c as temp_min,
    source_name,
    confidence_score,
    ingest_timestamp_utc,
    provenance_uuid,
    0.05 as geopolitical_weight,
    'Boutique quality supplier - premium market segment' as geopolitical_notes
  FROM `cbi-v14.forecasting_data_warehouse.weather_uruguay_daily`
  
  UNION ALL
  
  -- US Midwest weather (10% weight - domestic supply monitoring)
  SELECT 
    date,
    station_id,
    state as region,
    'USA' as country,
    precip_mm,
    temp_max_c as temp_max,
    temp_min_c as temp_min,
    source_name,
    confidence_score,
    ingest_timestamp_utc,
    provenance_uuid,
    0.10 as geopolitical_weight,
    'Domestic supply monitoring - Trump tariff impact assessment' as geopolitical_notes
  FROM `cbi-v14.forecasting_data_warehouse.weather_us_midwest_daily`
  
  UNION ALL
  
  -- Legacy weather data (backup)
  SELECT 
    date,
    station_id,
    region,
    CASE 
      WHEN region LIKE '%Brazil%' THEN 'Brazil'
      WHEN region LIKE '%Argentina%' THEN 'Argentina'
      WHEN region LIKE '%Paraguay%' THEN 'Paraguay'
      WHEN region LIKE '%Uruguay%' THEN 'Uruguay'
      WHEN region LIKE '%US%' OR region LIKE '%USA%' THEN 'USA'
      ELSE 'Unknown'
    END as country,
    precip_mm,
    temp_max,
    temp_min,
    source_name,
    confidence_score,
    ingest_timestamp_utc,
    provenance_uuid,
    CASE 
      WHEN region LIKE '%Argentina%' THEN 0.40
      WHEN region LIKE '%Brazil%' THEN 0.30
      WHEN region LIKE '%Paraguay%' THEN 0.15
      WHEN region LIKE '%Uruguay%' THEN 0.05
      WHEN region LIKE '%US%' OR region LIKE '%USA%' THEN 0.10
      ELSE 0.10
    END as geopolitical_weight,
    'Legacy data - geopolitical weighting applied' as geopolitical_notes
  FROM `cbi-v14.forecasting_data_warehouse.weather_data`
  WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)  -- Only recent legacy data
)
SELECT 
  date,
  station_id,
  region,
  country,
  precip_mm,
  temp_max,
  temp_min,
  source_name,
  confidence_score,
  ingest_timestamp_utc,
  provenance_uuid,
  geopolitical_weight,
  geopolitical_notes,
  -- Add calculated fields
  CASE 
    WHEN temp_max IS NOT NULL AND temp_min IS NOT NULL 
    THEN ROUND((temp_max + temp_min) / 2, 2)
    ELSE NULL 
  END as temp_avg,
  CASE 
    WHEN temp_max IS NOT NULL AND temp_min IS NOT NULL 
    THEN temp_max - temp_min
    ELSE NULL 
  END as temp_range,
  -- Weather stress indicators
  CASE 
    WHEN temp_max > 35 THEN 'Heat Stress'
    WHEN temp_min < 5 THEN 'Cold Stress'
    WHEN precip_mm > 50 THEN 'Excessive Rain'
    WHEN precip_mm < 1 AND temp_max > 30 THEN 'Drought Risk'
    ELSE 'Normal'
  END as weather_stress,
  -- Production impact scoring
  CASE 
    WHEN temp_max > 35 OR temp_min < 5 THEN 'High Risk'
    WHEN precip_mm > 50 OR (precip_mm < 1 AND temp_max > 30) THEN 'Medium Risk'
    ELSE 'Low Risk'
  END as production_risk
FROM all_weather_data
ORDER BY date DESC, geopolitical_weight DESC, country, region;
