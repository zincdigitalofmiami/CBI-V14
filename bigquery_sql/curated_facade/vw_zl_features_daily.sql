-- curated.vw_zl_features_daily
-- Soybean oil price/volatility facade view
CREATE OR REPLACE VIEW `cbi-v14.curated.vw_zl_features_daily` AS
WITH base AS (
  SELECT
    DATE(time) AS date,
    symbol,
    SAFE_CAST(open AS FLOAT64)  AS open_price,
    SAFE_CAST(high AS FLOAT64)  AS high_price,
    SAFE_CAST(low AS FLOAT64)   AS low_price,
    SAFE_CAST(close AS FLOAT64) AS close_price,
    SAFE_CAST(volume AS INT64)  AS volume,
    source_name,
    confidence_score,
    ingest_timestamp_utc,
    provenance_uuid
  FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
  WHERE symbol = 'ZL'
)
SELECT
  b.date,
  b.symbol,
  b.open_price,
  b.high_price,
  b.low_price,
  b.close_price,
  b.volume,
  SAFE_CAST(close_price - LAG(close_price) OVER (ORDER BY date) AS FLOAT64) AS price_change,
  ROUND(100.0 * (close_price - LAG(close_price) OVER (ORDER BY date)) / NULLIF(LAG(close_price) OVER (ORDER BY date), 0), 2) AS price_change_pct,
  ROUND(STDDEV(close_price) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW), 4) AS vol_30d,
  ROUND(AVG(close_price) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW), 4) AS ma_30d,
  b.source_name,
  b.confidence_score,
  b.ingest_timestamp_utc,
  b.provenance_uuid
FROM base b;









