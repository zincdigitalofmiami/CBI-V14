-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- curated.vw_economic_daily
-- Canonical economic indicators facade view
CREATE OR REPLACE VIEW `cbi-v14.curated.vw_economic_daily` AS
SELECT
  DATE(time) AS date,
  MAX(IF(indicator = 'ten_year_treasury', value, NULL)) AS yield_10yr,
  MAX(IF(indicator = 'dollar_index', value, NULL))       AS dollar_index,
  MAX(IF(indicator = 'fed_funds_rate', value, NULL))     AS fed_funds_rate,
  MAX(IF(indicator = 'crude_oil_wti', value, NULL))      AS crude_oil_wti,
  MAX(IF(indicator = 'usd_cny_rate', value, NULL))       AS usd_cny_rate,
  MAX(IF(indicator = 'usd_brl_rate', value, NULL))       AS usd_brl_rate,
  MAX(IF(indicator = 'cpi_inflation', value, NULL))      AS cpi_inflation,
  MAX(source_name) AS source_name,
  MAX(confidence_score) AS confidence_score,
  MAX(ingest_timestamp_utc) AS ingest_timestamp_utc,
  MAX(provenance_uuid) AS provenance_uuid
FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
GROUP BY 1;









