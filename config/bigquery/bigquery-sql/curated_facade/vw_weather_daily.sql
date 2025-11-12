-- curated.vw_weather_daily
-- Canonical weather aggregate facade view
CREATE OR REPLACE VIEW `cbi-v14.curated.vw_weather_daily` AS
SELECT
  DATE(date) AS date,
  region,
  SAFE_CAST(AVG(precip_mm) AS FLOAT64) AS precip_mm_avg,
  SAFE_CAST(MAX(temp_max) AS FLOAT64)  AS temp_max_c,
  SAFE_CAST(MIN(temp_min) AS FLOAT64)  AS temp_min_c,
  MAX(source_name)          AS source_name,
  MAX(confidence_score)     AS confidence_score,
  MAX(ingest_timestamp_utc) AS ingest_timestamp_utc,
  MAX(provenance_uuid)      AS provenance_uuid
FROM `cbi-v14.forecasting_data_warehouse.weather_data`
GROUP BY 1, 2;









