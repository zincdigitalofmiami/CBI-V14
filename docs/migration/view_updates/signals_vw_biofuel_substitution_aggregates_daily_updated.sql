-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- Updated signals.vw_biofuel_substitution_aggregates_daily
-- Updated: 2025-11-17 17:57:49

WITH rfs AS (
  SELECT 
    DATE(time) as date,
    MAX(CASE WHEN indicator LIKE '%rfs_total_mandate%' THEN value END) as rfs_mandate_bgal,
    MAX(CASE WHEN indicator LIKE '%biomass_diesel%' THEN value END) as biodiesel_mandate_bgal
  FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
  WHERE indicator LIKE '%rfs%' OR indicator LIKE '%biodiesel%'
  GROUP BY date
),
palm AS (
  SELECT 
    DATE(time) as date,
    yahoo_close as palm_oil_price_usd
  FROM `cbi-v14.forecasting_data_warehouse.palm_oil_prices`
),
soy AS (
  SELECT 
    DATE(time) as date,
    yahoo_close as soybean_oil_price_usd
  FROM `cbi-v14.forecasting_data_warehouse.yahoo_historical_prefixed`
)
SELECT 
  COALESCE(rfs.date, palm.date, soy.date) as date,
  rfs.rfs_mandate_bgal,
  rfs.biodiesel_mandate_bgal,
  palm.palm_oil_price_usd,
  soy.soybean_oil_price_usd,
  SAFE_DIVIDE(soy.soybean_oil_price_usd, palm.palm_oil_price_usd) as soy_palm_price_ratio,
  -- Palm substitution signal (higher ratio = more substitution pressure)
  CASE 
    WHEN SAFE_DIVIDE(soy.soybean_oil_price_usd, palm.palm_oil_price_usd) > 1.2 THEN 0.8
    WHEN SAFE_DIVIDE(soy.soybean_oil_price_usd, palm.palm_oil_price_usd) > 1.1 THEN 0.6
    WHEN SAFE_DIVIDE(soy.soybean_oil_price_usd, palm.palm_oil_price_usd) < 0.9 THEN 0.2
    ELSE 0.4
  END as palm_substitution_signal,
  -- Biofuel economics index (mandate growth + price competitiveness)
  COALESCE(rfs.biodiesel_mandate_bgal, 0) * 0.7 + 
  (1 - SAFE_DIVIDE(soy.soybean_oil_price_usd, 1000)) * 0.3 as biofuel_economics_index
FROM rfs
FULL OUTER JOIN palm ON rfs.date = palm.date
FULL OUTER JOIN soy ON COALESCE(rfs.date, palm.date) = soy.date
WHERE COALESCE(rfs.date, palm.date, soy.date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
ORDER BY date DESC