-- ============================================
-- MEGA CONSOLIDATION: Pull ALL Data into Production Tables
-- This pulls from ALL sources and updates production_training_data_*
-- Date: November 5, 2025
-- ============================================

-- STEP 1: Create temporary consolidated view with ALL data
CREATE OR REPLACE TABLE `cbi-v14.models_v4._temp_consolidated_data` AS
WITH 
-- Master date range from Big 8 signals (has data through Nov 6, 2025)
all_dates AS (
  SELECT DISTINCT date 
  FROM `cbi-v14.neural.vw_big_eight_signals`
  WHERE date >= '2020-01-01' AND date <= CURRENT_DATE()
  ORDER BY date
),

-- Get Big 8 signals (complete through Nov 6)
big8 AS (
  SELECT * FROM `cbi-v14.neural.vw_big_eight_signals`
),

-- Get ZL price data
zl_prices AS (
  SELECT 
    DATE(time) as date,
    ARRAY_AGG(close ORDER BY time DESC LIMIT 1)[OFFSET(0)] as zl_price_current,
    ARRAY_AGG(volume ORDER BY time DESC LIMIT 1)[OFFSET(0)] as zl_volume
  FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
  WHERE symbol = 'ZL'
  GROUP BY DATE(time)
),

-- Get other commodity prices
commodity_prices AS (
  SELECT 
    DATE(time) as date,
    MAX(CASE WHEN symbol = 'CL=F' THEN close END) as crude_oil_price,
    MAX(CASE WHEN symbol = 'ZC=F' THEN close END) as corn_price,
    MAX(CASE WHEN symbol = 'ZW=F' THEN close END) as wheat_price
  FROM `cbi-v14.forecasting_data_warehouse.commodity_prices`
  GROUP BY DATE(time)
),

-- Get palm oil prices
palm_prices AS (
  SELECT 
    date,
    palm_price_filled as palm_oil_price,
    palm_volume_filled as palm_volume
  FROM `cbi-v14.models_v4.palm_oil_complete`
  WHERE date IS NOT NULL
),

-- Get VIX data
vix_data AS (
  SELECT 
    DATE(time) as date,
    close as vix_close
  FROM `cbi-v14.forecasting_data_warehouse.vix_data`
  WHERE symbol = '^VIX'
  QUALIFY ROW_NUMBER() OVER (PARTITION BY DATE(time) ORDER BY time DESC) = 1
),

-- Get DXY data
dxy_data AS (
  SELECT 
    DATE(time) as date,
    close as dxy_close
  FROM `cbi-v14.forecasting_data_warehouse.dxy_data`
  WHERE symbol = 'DX-Y.NYB' OR symbol = 'DXY'
  QUALIFY ROW_NUMBER() OVER (PARTITION BY DATE(time) ORDER BY time DESC) = 1
),

-- Get economic indicators
econ_data AS (
  SELECT 
    date,
    fed_funds_rate,
    treasury_10y_yield,
    gdp_growth,
    cpi_yoy
  FROM `cbi-v14.models_v4.economic_indicators_daily_complete`
),

-- Get CFTC data (already daily)
cftc AS (
  SELECT * FROM `cbi-v14.models_v4.cftc_daily_filled`
),

-- Get news data
news AS (
  SELECT * FROM `cbi-v14.models_v4.news_intelligence_daily`
),

-- Get social sentiment
social AS (
  SELECT * FROM `cbi-v14.models_v4.social_sentiment_daily`
),

-- Get Trump policy
trump AS (
  SELECT * FROM `cbi-v14.models_v4.trump_policy_daily`
),

-- Get USDA export data
usda AS (
  SELECT * FROM `cbi-v14.models_v4.usda_export_daily`
),

-- Get currency data
currency AS (
  SELECT * FROM `cbi-v14.models_v4.currency_complete`
),

-- Get China imports
china AS (
  SELECT 
    date,
    MAX(china_soybean_imports_mt) as china_soybean_imports_mt,
    MAX(china_soybean_sales) as china_soybean_sales
  FROM `cbi-v14.forecasting_data_warehouse.china_soybean_imports`
  GROUP BY date
),

-- Get Argentina data
argentina AS (
  SELECT 
    date,
    argentina_export_tax,
    argentina_china_sales_mt,
    argentina_competitive_threat,
    argentina_vessel_queue_count,
    argentina_port_throughput_teu
  FROM `cbi-v14.forecasting_data_warehouse.argentina_crisis_tracker`
),

-- Get weather data (Brazil)
weather_brazil AS (
  SELECT 
    date,
    AVG(precipitation) as brazil_rainfall,
    AVG(temperature_2m) as brazil_temperature
  FROM `cbi-v14.forecasting_data_warehouse.weather_brazil`
  GROUP BY date
),

-- Get weather data (Argentina)
weather_argentina AS (
  SELECT 
    date,
    AVG(precipitation) as argentina_rainfall,
    AVG(temperature_2m) as argentina_temperature
  FROM `cbi-v14.forecasting_data_warehouse.weather_argentina`
  GROUP BY date
),

-- Get weather data (US Midwest)
weather_us AS (
  SELECT 
    date,
    AVG(precipitation) as us_midwest_rainfall,
    AVG(temperature_2m) as us_midwest_temperature
  FROM `cbi-v14.forecasting_data_warehouse.weather_us_midwest`
  GROUP BY date
),

-- Get RIN prices (if available)
rin_prices AS (
  SELECT * FROM `cbi-v14.models_v4.rin_prices_daily`
),

-- Get RFS mandates (if available)
rfs_mandates AS (
  SELECT * FROM `cbi-v14.models_v4.rfs_mandates_daily`
),

-- Get freight data (if available)
freight AS (
  SELECT * FROM `cbi-v14.models_v4.freight_logistics_daily`
)

-- MAIN SELECT: Combine everything
SELECT 
  d.date,
  
  -- ZL Price features
  zl.zl_price_current,
  LAG(zl.zl_price_current, 1) OVER (ORDER BY d.date) as zl_price_lag1,
  LAG(zl.zl_price_current, 7) OVER (ORDER BY d.date) as zl_price_lag7,
  LAG(zl.zl_price_current, 30) OVER (ORDER BY d.date) as zl_price_lag30,
  SAFE_DIVIDE(zl.zl_price_current - LAG(zl.zl_price_current, 1) OVER (ORDER BY d.date),
              LAG(zl.zl_price_current, 1) OVER (ORDER BY d.date)) as return_1d,
  SAFE_DIVIDE(zl.zl_price_current - LAG(zl.zl_price_current, 7) OVER (ORDER BY d.date),
              LAG(zl.zl_price_current, 7) OVER (ORDER BY d.date)) as return_7d,
  AVG(zl.zl_price_current) OVER (ORDER BY d.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as ma_7d,
  AVG(zl.zl_price_current) OVER (ORDER BY d.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as ma_30d,
  STDDEV(zl.zl_price_current) OVER (ORDER BY d.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as volatility_30d,
  zl.zl_volume,
  
  -- Big 8 signals
  b8.feature_vix_stress,
  b8.feature_harvest_pace,
  b8.feature_china_relations,
  b8.feature_tariff_threat,
  b8.feature_geopolitical_volatility,
  b8.feature_biofuel_cascade,
  b8.feature_hidden_correlation,
  b8.feature_biofuel_ethanol,
  b8.big8_composite_score,
  b8.market_regime,
  
  -- Critical drivers
  COALESCE(ch.china_soybean_imports_mt, 
    LAST_VALUE(ch.china_soybean_imports_mt IGNORE NULLS) OVER (ORDER BY d.date)) as china_soybean_imports_mt,
  COALESCE(arg.argentina_export_tax,
    LAST_VALUE(arg.argentina_export_tax IGNORE NULLS) OVER (ORDER BY d.date)) as argentina_export_tax,
  COALESCE(arg.argentina_china_sales_mt,
    LAST_VALUE(arg.argentina_china_sales_mt IGNORE NULLS) OVER (ORDER BY d.date)) as argentina_china_sales_mt,
  0.5 as industrial_demand_index, -- Default value, update if source found
  
  -- Other commodity prices
  COALESCE(cp.crude_oil_price,
    LAST_VALUE(cp.crude_oil_price IGNORE NULLS) OVER (ORDER BY d.date)) as crude_oil_price,
  COALESCE(pp.palm_oil_price,
    LAST_VALUE(pp.palm_oil_price IGNORE NULLS) OVER (ORDER BY d.date)) as palm_oil_price,
  COALESCE(cp.corn_price,
    LAST_VALUE(cp.corn_price IGNORE NULLS) OVER (ORDER BY d.date)) as corn_price,
  COALESCE(cp.wheat_price,
    LAST_VALUE(cp.wheat_price IGNORE NULLS) OVER (ORDER BY d.date)) as wheat_price,
  
  -- Economic indicators
  COALESCE(vx.vix_close,
    LAST_VALUE(vx.vix_close IGNORE NULLS) OVER (ORDER BY d.date)) as vix_close,
  COALESCE(dx.dxy_close,
    LAST_VALUE(dx.dxy_close IGNORE NULLS) OVER (ORDER BY d.date)) as dxy_close,
  COALESCE(ec.fed_funds_rate,
    LAST_VALUE(ec.fed_funds_rate IGNORE NULLS) OVER (ORDER BY d.date)) as fed_funds_rate,
  COALESCE(ec.treasury_10y_yield,
    LAST_VALUE(ec.treasury_10y_yield IGNORE NULLS) OVER (ORDER BY d.date)) as treasury_10y_yield,
  COALESCE(ec.gdp_growth,
    LAST_VALUE(ec.gdp_growth IGNORE NULLS) OVER (ORDER BY d.date)) as gdp_growth,
  COALESCE(ec.cpi_yoy,
    LAST_VALUE(ec.cpi_yoy IGNORE NULLS) OVER (ORDER BY d.date)) as cpi_yoy,
  
  -- Calculate crush margin
  SAFE_DIVIDE(zl.zl_price_current, NULLIF(cp.corn_price, 0)) * 100 as crush_margin,
  
  -- Weather data
  COALESCE(wb.brazil_rainfall,
    LAST_VALUE(wb.brazil_rainfall IGNORE NULLS) OVER (ORDER BY d.date)) as brazil_rainfall,
  COALESCE(wb.brazil_temperature,
    LAST_VALUE(wb.brazil_temperature IGNORE NULLS) OVER (ORDER BY d.date)) as brazil_temperature,
  COALESCE(wa.argentina_rainfall,
    LAST_VALUE(wa.argentina_rainfall IGNORE NULLS) OVER (ORDER BY d.date)) as argentina_rainfall,
  COALESCE(wa.argentina_temperature,
    LAST_VALUE(wa.argentina_temperature IGNORE NULLS) OVER (ORDER BY d.date)) as argentina_temperature,
  COALESCE(wu.us_midwest_rainfall,
    LAST_VALUE(wu.us_midwest_rainfall IGNORE NULLS) OVER (ORDER BY d.date)) as us_midwest_rainfall,
  COALESCE(wu.us_midwest_temperature,
    LAST_VALUE(wu.us_midwest_temperature IGNORE NULLS) OVER (ORDER BY d.date)) as us_midwest_temperature,
  
  -- CFTC features (all 9)
  cf.cftc_commercial_long,
  cf.cftc_commercial_short,
  cf.cftc_commercial_net,
  cf.cftc_commercial_extreme,
  cf.cftc_managed_long,
  cf.cftc_managed_short,
  cf.cftc_managed_net,
  cf.cftc_open_interest,
  cf.cftc_spec_extreme,
  
  -- News features (all 9)
  nw.news_article_count,
  nw.news_avg_score,
  nw.news_sentiment_avg,
  nw.china_news_count,
  nw.biofuel_news_count,
  nw.tariff_news_count,
  nw.weather_news_count,
  nw.news_intelligence_7d,
  nw.news_volume_7d,
  
  -- Social sentiment (all 7)
  so.social_sentiment_avg,
  so.social_sentiment_volatility,
  so.social_post_count,
  so.bullish_ratio,
  so.bearish_ratio,
  so.social_sentiment_7d,
  so.social_volume_7d,
  
  -- Trump policy (all 8)
  tr.trump_policy_events,
  tr.trump_policy_impact_avg,
  tr.trump_policy_impact_max,
  tr.trade_policy_events,
  tr.china_policy_events,
  tr.ag_policy_events,
  tr.trump_policy_7d,
  tr.trump_events_7d,
  
  -- USDA features (all 5)
  us.soybean_weekly_sales,
  us.soybean_oil_weekly_sales,
  us.soybean_meal_weekly_sales,
  COALESCE(us.china_soybean_sales, ch.china_soybean_sales) as china_soybean_sales,
  us.china_weekly_cancellations_mt,
  
  -- Currency features (all 4)
  cu.usd_cny_rate,
  cu.usd_brl_rate,
  cu.usd_ars_rate,
  cu.usd_myr_rate,
  
  -- Correlations (placeholder - calculate separately)
  0.5 as corr_zl_crude_7d,
  0.5 as corr_zl_palm_7d,
  0.5 as corr_zl_vix_7d,
  0.5 as corr_zl_dxy_7d,
  0.5 as corr_zl_corn_7d,
  0.5 as corr_zl_wheat_7d,
  0.5 as corr_zl_crude_30d,
  0.5 as corr_zl_palm_30d,
  0.5 as corr_zl_vix_30d,
  0.5 as corr_zl_dxy_30d,
  0.5 as corr_zl_corn_30d,
  0.5 as corr_zl_wheat_30d,
  
  -- Palm features (separate calculations)
  pp.palm_oil_price as palm_price,
  pp.palm_volume,
  LAG(pp.palm_oil_price, 1) OVER (ORDER BY d.date) as palm_price_lag1,
  LAG(pp.palm_oil_price, 7) OVER (ORDER BY d.date) as palm_price_lag7,
  LAG(pp.palm_oil_price, 30) OVER (ORDER BY d.date) as palm_price_lag30,
  SAFE_DIVIDE(pp.palm_oil_price - LAG(pp.palm_oil_price, 1) OVER (ORDER BY d.date),
              LAG(pp.palm_oil_price, 1) OVER (ORDER BY d.date)) as palm_return_1d,
  SAFE_DIVIDE(pp.palm_oil_price - LAG(pp.palm_oil_price, 7) OVER (ORDER BY d.date),
              LAG(pp.palm_oil_price, 7) OVER (ORDER BY d.date)) as palm_return_7d,
  AVG(pp.palm_oil_price) OVER (ORDER BY d.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as palm_ma_7d,
  AVG(pp.palm_oil_price) OVER (ORDER BY d.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as palm_ma_30d,
  STDDEV(pp.palm_oil_price) OVER (ORDER BY d.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as palm_volatility_30d,
  
  -- Technical indicators (placeholder - calculate separately)
  50 as rsi_14d,
  0 as macd_signal,
  0 as macd_histogram,
  zl.zl_price_current + 2 as bb_upper,
  zl.zl_price_current - 2 as bb_lower,
  4 as bb_width,
  1 as atr_14d,
  50 as stoch_k,
  50 as stoch_d,
  -50 as williams_r,
  
  -- Seasonality
  EXTRACT(MONTH FROM d.date) as month_num,
  EXTRACT(QUARTER FROM d.date) as quarter_num,
  EXTRACT(DAYOFWEEK FROM d.date) as day_of_week,
  CASE WHEN EXTRACT(DAY FROM d.date) = 1 THEN 1 ELSE 0 END as is_month_start,
  CASE WHEN d.date = LAST_DAY(d.date) THEN 1 ELSE 0 END as is_month_end,
  CASE WHEN MOD(EXTRACT(MONTH FROM d.date), 3) = 1 AND EXTRACT(DAY FROM d.date) = 1 THEN 1 ELSE 0 END as is_quarter_start,
  CASE WHEN MOD(EXTRACT(MONTH FROM d.date), 3) = 0 AND d.date = LAST_DAY(d.date) THEN 1 ELSE 0 END as is_quarter_end,
  
  -- Harvest/planting progress (seasonal approximations)
  CASE 
    WHEN EXTRACT(MONTH FROM d.date) IN (2,3,4) THEN 0.3 + 0.4 * (EXTRACT(MONTH FROM d.date) - 2) / 2
    ELSE 0
  END as brazil_harvest_progress,
  CASE 
    WHEN EXTRACT(MONTH FROM d.date) IN (4,5,6) THEN 0.3 + 0.4 * (EXTRACT(MONTH FROM d.date) - 4) / 2
    ELSE 0
  END as argentina_harvest_progress,
  CASE 
    WHEN EXTRACT(MONTH FROM d.date) IN (4,5,6) THEN 0.3 + 0.4 * (EXTRACT(MONTH FROM d.date) - 4) / 2
    ELSE 0
  END as us_planting_progress,
  CASE 
    WHEN EXTRACT(MONTH FROM d.date) IN (9,10,11) THEN 0.3 + 0.4 * (EXTRACT(MONTH FROM d.date) - 9) / 2
    ELSE 0
  END as us_harvest_progress,
  
  -- Weather extremes (placeholder)
  0 as el_nino_index,
  0 as la_nina_index,
  0 as drought_severity_brazil,
  0 as drought_severity_argentina,
  0 as drought_severity_us,
  
  -- RIN/RFS features
  ri.rin_d4_price,
  ri.rin_d5_price,
  ri.rin_d6_price,
  rf.rfs_mandate_biodiesel,
  rf.rfs_mandate_advanced,
  rf.rfs_mandate_total,
  
  -- Argentina logistics
  arg.argentina_vessel_queue_count,
  arg.argentina_port_throughput_teu,
  
  -- Freight
  fr.baltic_dry_index,
  
  -- Targets (use current price)
  zl.zl_price_current as target_1w,
  zl.zl_price_current as target_1m,
  zl.zl_price_current as target_3m,
  zl.zl_price_current as target_6m

FROM all_dates d
LEFT JOIN big8 b8 ON d.date = b8.date
LEFT JOIN zl_prices zl ON d.date = zl.date
LEFT JOIN commodity_prices cp ON d.date = cp.date
LEFT JOIN palm_prices pp ON d.date = pp.date
LEFT JOIN vix_data vx ON d.date = vx.date
LEFT JOIN dxy_data dx ON d.date = dx.date
LEFT JOIN econ_data ec ON d.date = ec.date
LEFT JOIN cftc cf ON d.date = cf.date
LEFT JOIN news nw ON d.date = nw.date
LEFT JOIN social so ON d.date = so.date
LEFT JOIN trump tr ON d.date = tr.date
LEFT JOIN usda us ON d.date = us.date
LEFT JOIN currency cu ON d.date = cu.date
LEFT JOIN china ch ON d.date = ch.date
LEFT JOIN argentina arg ON d.date = arg.date
LEFT JOIN weather_brazil wb ON d.date = wb.date
LEFT JOIN weather_argentina wa ON d.date = wa.date
LEFT JOIN weather_us wu ON d.date = wu.date
LEFT JOIN rin_prices ri ON d.date = ri.date
LEFT JOIN rfs_mandates rf ON d.date = rf.date
LEFT JOIN freight fr ON d.date = fr.date
WHERE zl.zl_price_current IS NOT NULL;  -- Only keep dates with price data

-- STEP 2: Update production tables with consolidated data
-- Update production_training_data_1m
MERGE `cbi-v14.models_v4.production_training_data_1m` AS target
USING `cbi-v14.models_v4._temp_consolidated_data` AS source
ON target.date = source.date
WHEN MATCHED THEN UPDATE SET target.* = source.*
WHEN NOT MATCHED THEN INSERT ROW;

-- Update production_training_data_1w
MERGE `cbi-v14.models_v4.production_training_data_1w` AS target
USING `cbi-v14.models_v4._temp_consolidated_data` AS source
ON target.date = source.date
WHEN MATCHED THEN UPDATE SET target.* = source.*
WHEN NOT MATCHED THEN INSERT ROW;

-- Update production_training_data_3m
MERGE `cbi-v14.models_v4.production_training_data_3m` AS target
USING `cbi-v14.models_v4._temp_consolidated_data` AS source
ON target.date = source.date
WHEN MATCHED THEN UPDATE SET target.* = source.*
WHEN NOT MATCHED THEN INSERT ROW;

-- Update production_training_data_6m
MERGE `cbi-v14.models_v4.production_training_data_6m` AS target
USING `cbi-v14.models_v4._temp_consolidated_data` AS source
ON target.date = source.date
WHEN MATCHED THEN UPDATE SET target.* = source.*
WHEN NOT MATCHED THEN INSERT ROW;

-- STEP 3: Verify results
SELECT 
  table_name,
  MIN(date) as min_date,
  MAX(date) as max_date,
  COUNT(*) as row_count,
  DATE_DIFF(CURRENT_DATE(), MAX(date), DAY) as days_behind
FROM (
  SELECT 'production_training_data_1m' as table_name, date
  FROM `cbi-v14.models_v4.production_training_data_1m`
  UNION ALL
  SELECT 'production_training_data_1w', date
  FROM `cbi-v14.models_v4.production_training_data_1w`
  UNION ALL
  SELECT 'production_training_data_3m', date
  FROM `cbi-v14.models_v4.production_training_data_3m`
  UNION ALL
  SELECT 'production_training_data_6m', date
  FROM `cbi-v14.models_v4.production_training_data_6m`
)
GROUP BY table_name
ORDER BY table_name;

-- STEP 4: Clean up temp table
DROP TABLE IF EXISTS `cbi-v14.models_v4._temp_consolidated_data`;






