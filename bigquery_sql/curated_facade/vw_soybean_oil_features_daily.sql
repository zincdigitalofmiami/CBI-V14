CREATE OR REPLACE VIEW \`cbi-v14.curated.vw_soybean_oil_features_daily\`
OPTIONS(
  friendly_name="vw_soybean_oil_features_daily",
  description="Primary feature view for soybean oil, joining daily prices with weather data. Correctly sourced from soybean_oil_prices (ZL)."
)
AS
WITH price_data AS (
  SELECT 
    DATE(time) as date,
    symbol,
    open as open_price,
    high as high_price,
    low as low_price,
    close as close_price,
    volume
  FROM \`cbi-v14.forecasting_data_warehouse.soybean_oil_prices\` -- AUDIT-CONFIRMED ZL SOURCE
  WHERE symbol = 'ZL=F'
),
weather_pivot AS (
  SELECT 
    date,
    AVG(CASE WHEN region = 'Argentina' THEN precip_mm END) as argentina_precip,
    AVG(CASE WHEN region = 'US' THEN precip_mm END) as us_precip
  FROM \`cbi-v14.forecasting_data_warehouse.weather_data\`
  GROUP BY date
)
SELECT 
  p.date,
  p.symbol,
  p.open_price,
  p.high_price,
  p.low_price,
  p.close_price,
  p.volume,
  COALESCE(w.argentina_precip, 0) as argentina_precip,
  COALESCE(w.us_precip, 0) as us_precip,
  -- Canonical metadata
  'cbi_internal_view' as source_name,
  1.0 as confidence_score, -- View is considered high confidence
  CURRENT_TIMESTAMP() as ingest_timestamp_utc,
  GENERATE_UUID() as provenance_uuid
FROM price_data p
LEFT JOIN weather_pivot w ON p.date = w.date
ORDER BY p.date DESC;
