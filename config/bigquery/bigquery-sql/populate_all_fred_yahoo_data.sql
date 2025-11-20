-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- POPULATE ALL FRED & YAHOO DATA INTO TRAINING DATASET
-- The data EXISTS in source tables - this fills the NULLs in training_dataset_super_enriched
-- ============================================

-- ============================================
-- PART 1: YAHOO FINANCE DATA (ZL Price & Volume)
-- ============================================

-- Update zl_price_current from yahoo_finance_enhanced
MERGE `cbi-v14.models_v4.training_dataset_super_enriched` t
USING (
  SELECT date, Close, Volume
  FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
  WHERE symbol = 'ZL=F' AND Close IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY date ORDER BY pulled_at DESC) = 1
) y
ON t.date = y.date AND t.zl_price_current IS NULL
WHEN MATCHED THEN
  UPDATE SET zl_price_current = y.Close;

-- Update zl_volume
MERGE `cbi-v14.models_v4.training_dataset_super_enriched` t
USING (
  SELECT date, Volume
  FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
  WHERE symbol = 'ZL=F' AND Volume IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY date ORDER BY pulled_at DESC) = 1
) y
ON t.date = y.date AND t.zl_volume IS NULL
WHEN MATCHED THEN
  UPDATE SET zl_volume = y.Volume;

-- Update targets (future prices)
MERGE `cbi-v14.models_v4.training_dataset_super_enriched` t
USING (
  SELECT date, Close
  FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
  WHERE symbol = 'ZL=F' AND Close IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY date ORDER BY pulled_at DESC) = 1
) y
ON t.date = DATE_SUB(y.date, INTERVAL 7 DAY) AND t.target_1w IS NULL
WHEN MATCHED THEN
  UPDATE SET target_1w = y.Close;

MERGE `cbi-v14.models_v4.training_dataset_super_enriched` t
USING (
  SELECT date, Close
  FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
  WHERE symbol = 'ZL=F' AND Close IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY date ORDER BY pulled_at DESC) = 1
) y
ON t.date = DATE_SUB(y.date, INTERVAL 30 DAY) AND t.target_1m IS NULL
WHEN MATCHED THEN
  UPDATE SET target_1m = y.Close;

MERGE `cbi-v14.models_v4.training_dataset_super_enriched` t
USING (
  SELECT date, Close
  FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
  WHERE symbol = 'ZL=F' AND Close IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY date ORDER BY pulled_at DESC) = 1
) y
ON t.date = DATE_SUB(y.date, INTERVAL 90 DAY) AND t.target_3m IS NULL
WHEN MATCHED THEN
  UPDATE SET target_3m = y.Close;

MERGE `cbi-v14.models_v4.training_dataset_super_enriched` t
USING (
  SELECT date, Close
  FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
  WHERE symbol = 'ZL=F' AND Close IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY date ORDER BY pulled_at DESC) = 1
) y
ON t.date = DATE_SUB(y.date, INTERVAL 180 DAY) AND t.target_6m IS NULL
WHEN MATCHED THEN
  UPDATE SET target_6m = y.Close;

-- ============================================
-- PART 2: COMMODITY PRICES FROM YAHOO
-- ============================================

-- Corn price
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET corn_price = y.Close
FROM (
  SELECT date, Close
  FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
  WHERE symbol = 'ZC=F' AND Close IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY date ORDER BY pulled_at DESC) = 1
) y
WHERE t.date = y.date
  AND t.corn_price IS NULL;

-- Wheat price
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET wheat_price = y.Close
FROM (
  SELECT date, Close
  FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
  WHERE symbol = 'ZW=F' AND Close IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY date ORDER BY pulled_at DESC) = 1
) y
WHERE t.date = y.date
  AND t.wheat_price IS NULL;

-- Crude oil price
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET crude_oil_wti_new = y.Close,
    crude_price = y.Close
FROM (
  SELECT date, Close
  FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
  WHERE symbol = 'CL=F' AND Close IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY date ORDER BY pulled_at DESC) = 1
) y
WHERE t.date = y.date
  AND (t.crude_oil_wti_new IS NULL OR t.crude_price IS NULL);

-- Soybean meal price
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET soybean_meal_price = y.Close
FROM (
  SELECT date, Close
  FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
  WHERE symbol = 'ZM=F' AND Close IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY date ORDER BY pulled_at DESC) = 1
) y
WHERE t.date = y.date
  AND t.soybean_meal_price IS NULL;

-- Palm oil price (FCPO)
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET palm_price = y.Close
FROM (
  SELECT date, Close
  FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
  WHERE symbol = 'FCPO=F' AND Close IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY date ORDER BY pulled_at DESC) = 1
) y
WHERE t.date = y.date
  AND t.palm_price IS NULL;

-- VIX from Yahoo
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET vix_level = y.Close,
    vix_index_new = y.Close
FROM (
  SELECT date, Close
  FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
  WHERE symbol = '^VIX' AND Close IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY date ORDER BY pulled_at DESC) = 1
) y
WHERE t.date = y.date
  AND (t.vix_level IS NULL OR t.vix_index_new IS NULL);

-- DXY (Dollar Index) from Yahoo
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET dxy_level = y.Close,
    dollar_index = y.Close,
    usd_index = y.Close
FROM (
  SELECT date, Close
  FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
  WHERE symbol = 'DX-Y.NYB' AND Close IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY date ORDER BY pulled_at DESC) = 1
) y
WHERE t.date = y.date
  AND (t.dxy_level IS NULL OR t.dollar_index IS NULL OR t.usd_index IS NULL);

-- ============================================
-- PART 3: FRED ECONOMIC DATA
-- ============================================

-- Treasury 10Y Yield
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET treasury_10y_yield = ei.value
FROM (
  SELECT CAST(time AS DATE) as date, value
  FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
  WHERE indicator = 'ten_year_treasury' AND value IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY CAST(time AS DATE) ORDER BY time DESC) = 1
) ei
WHERE t.date = ei.date
  AND t.treasury_10y_yield IS NULL;

-- USD/CNY Rate (FRED)
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET usd_cny_rate = ei.value
FROM (
  SELECT CAST(time AS DATE) as date, value
  FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
  WHERE indicator = 'usd_cny_rate_fred' AND value IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY CAST(time AS DATE) ORDER BY time DESC) = 1
) ei
WHERE t.date = ei.date
  AND t.usd_cny_rate IS NULL;

-- USD/BRL Rate (FRED)
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET usd_brl_rate = ei.value
FROM (
  SELECT CAST(time AS DATE) as date, value
  FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
  WHERE indicator = 'usd_brl_rate_fred' AND value IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY CAST(time AS DATE) ORDER BY time DESC) = 1
) ei
WHERE t.date = ei.date
  AND t.usd_brl_rate IS NULL;

-- Dollar Index (FRED)
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET dollar_index = COALESCE(t.dollar_index, ei.value),
    usd_index = COALESCE(t.usd_index, ei.value)
FROM (
  SELECT CAST(time AS DATE) as date, value
  FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
  WHERE indicator = 'dollar_index_fred' AND value IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY CAST(time AS DATE) ORDER BY time DESC) = 1
) ei
WHERE t.date = ei.date
  AND (t.dollar_index IS NULL OR t.usd_index IS NULL);

-- Fed Funds Rate
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET fed_funds_rate = ei.value
FROM (
  SELECT CAST(time AS DATE) as date, value
  FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
  WHERE indicator = 'fed_funds_rate' AND value IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY CAST(time AS DATE) ORDER BY time DESC) = 1
) ei
WHERE t.date = ei.date
  AND t.fed_funds_rate IS NULL;

-- Unemployment Rate
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET econ_unemployment_rate = ei.value,
    unemployment_rate = ei.value
FROM (
  SELECT CAST(time AS DATE) as date, value
  FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
  WHERE indicator = 'unemployment_rate' AND value IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY CAST(time AS DATE) ORDER BY time DESC) = 1
) ei
WHERE t.date = ei.date
  AND (t.econ_unemployment_rate IS NULL OR t.unemployment_rate IS NULL);

-- CPI Inflation (calculate YoY)
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET cpi_yoy = ei.yoy_change,
    econ_inflation_rate = ei.yoy_change
FROM (
  SELECT 
    CAST(time AS DATE) as date,
    (value / LAG(value, 12) OVER (ORDER BY CAST(time AS DATE)) - 1) * 100 as yoy_change
  FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
  WHERE indicator = 'CPIAUCSL' AND value IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY CAST(time AS DATE) ORDER BY time DESC) = 1
) ei
WHERE t.date = ei.date
  AND ei.yoy_change IS NOT NULL
  AND (t.cpi_yoy IS NULL OR t.econ_inflation_rate IS NULL);

-- GDP Growth (quarterly - forward fill to daily)
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET econ_gdp_growth = ei.growth,
    gdp_growth = ei.growth
FROM (
  SELECT 
    date,
    growth
  FROM (
    SELECT 
      CAST(time AS DATE) as date,
      (value / LAG(value, 1) OVER (ORDER BY CAST(time AS DATE)) - 1) * 100 as growth,
      ROW_NUMBER() OVER (PARTITION BY CAST(time AS DATE) ORDER BY time DESC) as rn
    FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
    WHERE indicator LIKE '%GDP%' AND value IS NOT NULL
  )
  WHERE rn = 1
  QUALIFY ROW_NUMBER() OVER (PARTITION BY DATE_TRUNC(date, QUARTER) ORDER BY date DESC) = 1
) ei
WHERE t.date = ei.date
  AND (t.econ_gdp_growth IS NULL OR t.gdp_growth IS NULL);

-- Forward fill GDP growth to all dates in quarter
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET econ_gdp_growth = q.gdp_growth,
    gdp_growth = q.gdp_growth
FROM (
  SELECT 
    t1.date,
    t2.gdp_growth
  FROM `cbi-v14.models_v4.training_dataset_super_enriched` t1
  CROSS JOIN (
    SELECT 
      DATE_TRUNC(date, QUARTER) as quarter,
      MAX(econ_gdp_growth) as gdp_growth
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    WHERE econ_gdp_growth IS NOT NULL
    GROUP BY quarter
  ) t2
  WHERE DATE_TRUNC(t1.date, QUARTER) = t2.quarter
) q
WHERE t.date = q.date
  AND (t.econ_gdp_growth IS NULL OR t.gdp_growth IS NULL);

-- ============================================
-- PART 4: CALCULATED FIELDS FROM POPULATED DATA
-- ============================================

-- Yield Curve (10Y Treasury - Fed Funds)
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET yield_curve = t.treasury_10y_yield - t.fed_funds_rate
WHERE t.yield_curve IS NULL
  AND t.treasury_10y_yield IS NOT NULL
  AND t.fed_funds_rate IS NOT NULL;

-- 7-day changes
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET usd_cny_7d_change = (t.usd_cny_rate / LAG(t.usd_cny_rate, 7) OVER (ORDER BY t.date) - 1) * 100
WHERE t.usd_cny_7d_change IS NULL
  AND t.usd_cny_rate IS NOT NULL;

UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET usd_brl_7d_change = (t.usd_brl_rate / LAG(t.usd_brl_rate, 7) OVER (ORDER BY t.date) - 1) * 100
WHERE t.usd_brl_7d_change IS NULL
  AND t.usd_brl_rate IS NOT NULL;

UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET dollar_index_7d_change = (t.dollar_index / LAG(t.dollar_index, 7) OVER (ORDER BY t.date) - 1) * 100
WHERE t.dollar_index_7d_change IS NULL
  AND t.dollar_index IS NOT NULL;

UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET wti_7d_change = (t.crude_oil_wti_new / LAG(t.crude_oil_wti_new, 7) OVER (ORDER BY t.date) - 1) * 100
WHERE t.wti_7d_change IS NULL
  AND t.crude_oil_wti_new IS NOT NULL;

-- ============================================
-- SUMMARY
-- ============================================
SELECT 
  'POPULATION COMPLETE' as status,
  COUNT(*) as total_rows,
  COUNTIF(zl_price_current IS NOT NULL) as zl_price_filled,
  COUNTIF(zl_volume IS NOT NULL) as zl_volume_filled,
  COUNTIF(corn_price IS NOT NULL) as corn_price_filled,
  COUNTIF(wheat_price IS NOT NULL) as wheat_price_filled,
  COUNTIF(crude_oil_wti_new IS NOT NULL) as crude_filled,
  COUNTIF(vix_level IS NOT NULL) as vix_filled,
  COUNTIF(dollar_index IS NOT NULL) as dollar_index_filled,
  COUNTIF(treasury_10y_yield IS NOT NULL) as treasury_filled,
  COUNTIF(usd_cny_rate IS NOT NULL) as usd_cny_filled,
  COUNTIF(usd_brl_rate IS NOT NULL) as usd_brl_filled,
  COUNTIF(fed_funds_rate IS NOT NULL) as fed_funds_filled,
  COUNTIF(econ_gdp_growth IS NOT NULL) as gdp_filled,
  COUNTIF(unemployment_rate IS NOT NULL) as unemployment_filled,
  COUNTIF(cpi_yoy IS NOT NULL) as cpi_filled
FROM `cbi-v14.models_v4.training_dataset_super_enriched`;

