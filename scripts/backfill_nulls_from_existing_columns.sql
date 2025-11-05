-- ============================================================================
-- NULL ELIMINATION: Backfill from EXISTING columns (no API needed)
-- Strategy: Map/copy/calculate from columns we already have
-- ============================================================================

-- STEP 1: Map weather columns (they exist with different names)
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched`
SET 
  -- Brazil weather (copy from existing columns)
  brazil_temp_c = COALESCE(brazil_temp_c, weather_brazil_temp),
  brazil_precip_mm = COALESCE(brazil_precip_mm, weather_brazil_precip),
  
  -- Argentina weather (copy from existing columns)
  argentina_temp_c = COALESCE(argentina_temp_c, weather_argentina_temp),
  argentina_precip_mm = COALESCE(argentina_precip_mm, argentina_precip_mm),  -- Check if exists
  
  -- Calculate conditions scores from temp + precip
  brazil_conditions_score = COALESCE(brazil_conditions_score, 
    100 - LEAST(50, ABS(weather_brazil_temp - 25) * 2 + CASE 
      WHEN weather_brazil_precip < 50 THEN (50 - weather_brazil_precip)
      WHEN weather_brazil_precip > 150 THEN (weather_brazil_precip - 150) / 2
      ELSE 0 
    END)
  ),
  
  argentina_conditions_score = COALESCE(argentina_conditions_score,
    100 - LEAST(50, ABS(weather_argentina_temp - 22) * 2)
  ),
  
  -- Calculate heat stress days (temp > 35C = stress)
  brazil_heat_stress_days = COALESCE(brazil_heat_stress_days,
    CASE WHEN weather_brazil_temp > 35 THEN 1 ELSE 0 END
  ),
  
  argentina_heat_stress_days = COALESCE(argentina_heat_stress_days,
    CASE WHEN weather_argentina_temp > 35 THEN 1 ELSE 0 END
  ),
  
  -- Calculate drought days (precip < 20mm = drought)
  brazil_drought_days = COALESCE(brazil_drought_days,
    CASE WHEN weather_brazil_precip < 20 THEN 1 ELSE 0 END
  ),
  
  argentina_drought_days = COALESCE(argentina_drought_days,
    CASE WHEN argentina_precip_mm < 20 THEN 1 ELSE 0 END
  ),
  
  -- Calculate flood days (precip > 150mm = flood)
  brazil_flood_days = COALESCE(brazil_flood_days,
    CASE WHEN weather_brazil_precip > 150 THEN 1 ELSE 0 END
  ),
  
  argentina_flood_days = COALESCE(argentina_flood_days,
    CASE WHEN argentina_precip_mm > 150 THEN 1 ELSE 0 END
  ),
  
  -- Global weather risk (composite)
  global_weather_risk_score = COALESCE(global_weather_risk_score,
    (
      CASE WHEN weather_brazil_temp > 35 OR weather_brazil_precip < 20 OR weather_brazil_precip > 150 THEN 30 ELSE 0 END +
      CASE WHEN weather_argentina_temp > 35 THEN 20 ELSE 0 END +
      CASE WHEN us_midwest_drought_days = 1 THEN 50 ELSE 0 END
    )
  ),
  
  -- Calculate return_1d from price
  return_1d = COALESCE(return_1d,
    (zl_price_current - LAG(zl_price_current) OVER (ORDER BY date)) / 
    NULLIF(LAG(zl_price_current) OVER (ORDER BY date), 0)
  )

WHERE TRUE;

-- STEP 2: Verify results
SELECT 
  'AFTER BACKFILL FROM EXISTING' AS status,
  COUNTIF(brazil_temp_c IS NULL) AS brazil_temp_nulls,
  COUNTIF(argentina_temp_c IS NULL) AS argentina_temp_nulls,
  COUNTIF(brazil_conditions_score IS NULL) AS brazil_conditions_nulls,
  COUNTIF(return_1d IS NULL) AS return_1d_nulls
FROM `cbi-v14.models_v4.training_dataset_super_enriched`;



