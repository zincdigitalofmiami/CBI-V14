-- curated.vw_volatility_daily
-- VIX and volatility metrics facade view
CREATE OR REPLACE VIEW `cbi-v14.curated.vw_volatility_daily` AS
SELECT
  DATE(data_date) AS date,
  symbol,
  SAFE_CAST(last_price AS FLOAT64) AS last_price,
  SAFE_CAST(iv_hv_ratio AS FLOAT64) AS iv_hv_ratio,
  SAFE_CAST(implied_vol AS FLOAT64) AS implied_vol,
  SOURCE_NAME,
  CONFIDENCE_SCORE,
  INGEST_TIMESTAMP_UTC,
  PROVENANCE_UUID
FROM `cbi-v14.forecasting_data_warehouse.volatility_data`;









