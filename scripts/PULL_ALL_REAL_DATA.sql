-- ============================================================================
-- PULL IN ALL FUCKING DATA - NO PLACEHOLDERS, NO BULLSHIT
-- Date: November 15, 2025
-- Purpose: Load EVERYTHING - all prices, all features, all indicators
-- ============================================================================

-- ----------------------------------------------------------------------------
-- STEP 1: PULL ALL HISTORICAL DATA FROM YAHOO FINANCE (2000-2025)
-- ----------------------------------------------------------------------------

-- Get ALL soybean data from yahoo_finance_comprehensive
CREATE OR REPLACE TABLE `cbi-v14.forecasting_data_warehouse.soybean_prices_complete` 
PARTITION BY DATE(Date)
CLUSTER BY Symbol AS
SELECT 
  Date AS time,
  Symbol AS symbol,
  Open AS open,
  High AS high,
  Low AS low,
  Close AS close,
  Volume AS volume,
  `Adj Close` AS adj_close,
  -- Calculate all technical indicators
  AVG(Close) OVER (PARTITION BY Symbol ORDER BY Date ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS ma_5,
  AVG(Close) OVER (PARTITION BY Symbol ORDER BY Date ROWS BETWEEN 9 PRECEDING AND CURRENT ROW) AS ma_10,
  AVG(Close) OVER (PARTITION BY Symbol ORDER BY Date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS ma_20,
  AVG(Close) OVER (PARTITION BY Symbol ORDER BY Date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS ma_50,
  AVG(Close) OVER (PARTITION BY Symbol ORDER BY Date ROWS BETWEEN 99 PRECEDING AND CURRENT ROW) AS ma_100,
  AVG(Close) OVER (PARTITION BY Symbol ORDER BY Date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW) AS ma_200,
  
  -- RSI calculation
  AVG(CASE WHEN Close > LAG(Close) OVER (PARTITION BY Symbol ORDER BY Date) 
       THEN Close - LAG(Close) OVER (PARTITION BY Symbol ORDER BY Date) ELSE 0 END) 
       OVER (PARTITION BY Symbol ORDER BY Date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS avg_gain_14,
  AVG(CASE WHEN Close < LAG(Close) OVER (PARTITION BY Symbol ORDER BY Date) 
       THEN ABS(Close - LAG(Close) OVER (PARTITION BY Symbol ORDER BY Date)) ELSE 0 END) 
       OVER (PARTITION BY Symbol ORDER BY Date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS avg_loss_14,
       
  -- Bollinger Bands
  AVG(Close) OVER (PARTITION BY Symbol ORDER BY Date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS bb_middle,
  STDDEV(Close) OVER (PARTITION BY Symbol ORDER BY Date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS bb_std,
  
  -- MACD
  AVG(Close) OVER (PARTITION BY Symbol ORDER BY Date ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) AS ema_12,
  AVG(Close) OVER (PARTITION BY Symbol ORDER BY Date ROWS BETWEEN 25 PRECEDING AND CURRENT ROW) AS ema_26,
  
  -- Volume indicators
  AVG(Volume) OVER (PARTITION BY Symbol ORDER BY Date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS avg_volume_20,
  SUM(Volume * Close) OVER (PARTITION BY Symbol ORDER BY Date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) / 
    SUM(Volume) OVER (PARTITION BY Symbol ORDER BY Date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS vwap_20,
  
  -- Price changes
  (Close - LAG(Close, 1) OVER (PARTITION BY Symbol ORDER BY Date)) / NULLIF(LAG(Close, 1) OVER (PARTITION BY Symbol ORDER BY Date), 0) AS return_1d,
  (Close - LAG(Close, 5) OVER (PARTITION BY Symbol ORDER BY Date)) / NULLIF(LAG(Close, 5) OVER (PARTITION BY Symbol ORDER BY Date), 0) AS return_5d,
  (Close - LAG(Close, 20) OVER (PARTITION BY Symbol ORDER BY Date)) / NULLIF(LAG(Close, 20) OVER (PARTITION BY Symbol ORDER BY Date), 0) AS return_20d,
  (Close - LAG(Close, 60) OVER (PARTITION BY Symbol ORDER BY Date)) / NULLIF(LAG(Close, 60) OVER (PARTITION BY Symbol ORDER BY Date), 0) AS return_60d,
  (Close - LAG(Close, 252) OVER (PARTITION BY Symbol ORDER BY Date)) / NULLIF(LAG(Close, 252) OVER (PARTITION BY Symbol ORDER BY Date), 0) AS return_252d,
  
  -- Volatility
  STDDEV(Close) OVER (PARTITION BY Symbol ORDER BY Date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS volatility_20d,
  STDDEV(Close) OVER (PARTITION BY Symbol ORDER BY Date ROWS BETWEEN 59 PRECEDING AND CURRENT ROW) AS volatility_60d,
  
  -- High/Low indicators
  MAX(High) OVER (PARTITION BY Symbol ORDER BY Date ROWS BETWEEN 251 PRECEDING AND CURRENT ROW) AS high_52w,
  MIN(Low) OVER (PARTITION BY Symbol ORDER BY Date ROWS BETWEEN 251 PRECEDING AND CURRENT ROW) AS low_52w,
  
  CURRENT_TIMESTAMP() AS updated_at
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE Symbol IN ('ZL=F', 'ZS=F', 'ZM=F', 'ZC=F', 'ZW=F', 'CL=F', 'GC=F', 'SI=F', 'DX-Y.NYB', '^VIX', '^TNX')
  AND Date >= '2000-01-01';

-- ----------------------------------------------------------------------------
-- STEP 2: PULL ALL ECONOMIC INDICATORS
-- ----------------------------------------------------------------------------

CREATE OR REPLACE TABLE `cbi-v14.raw_intelligence.all_economic_indicators` 
PARTITION BY DATE(date)
CLUSTER BY indicator_name AS
SELECT * FROM (
  -- GDP data
  SELECT 
    date,
    'GDP' AS indicator_name,
    gdp_value AS value,
    'FRED' AS source
  FROM `cbi-v14.forecasting_data_warehouse.gdp_data`
  
  UNION ALL
  
  -- CPI data
  SELECT 
    date,
    'CPI' AS indicator_name,
    cpi_value AS value,
    'FRED' AS source
  FROM `cbi-v14.forecasting_data_warehouse.cpi_data`
  
  UNION ALL
  
  -- Unemployment
  SELECT 
    date,
    'UNEMPLOYMENT' AS indicator_name,
    unemployment_rate AS value,
    'FRED' AS source
  FROM `cbi-v14.forecasting_data_warehouse.unemployment_data`
  
  UNION ALL
  
  -- Interest rates
  SELECT 
    DATE(time) AS date,
    CONCAT('TREASURY_', symbol) AS indicator_name,
    last AS value,
    'FRED' AS source
  FROM `cbi-v14.forecasting_data_warehouse.treasury_prices`
  
  UNION ALL
  
  -- Dollar index
  SELECT 
    Date AS date,
    'DOLLAR_INDEX' AS indicator_name,
    Close AS value,
    'YAHOO' AS source
  FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
  WHERE Symbol = 'DX-Y.NYB'
);

-- ----------------------------------------------------------------------------
-- STEP 3: PULL ALL WEATHER DATA
-- ----------------------------------------------------------------------------

CREATE OR REPLACE TABLE `cbi-v14.raw_intelligence.all_weather_data`
PARTITION BY DATE(date)
CLUSTER BY region AS
SELECT 
  date,
  region,
  country,
  state,
  temperature_avg,
  temperature_max,
  temperature_min,
  precipitation_mm,
  humidity_pct,
  wind_speed_kmh,
  soil_moisture_pct,
  drought_index,
  frost_days,
  growing_degree_days,
  CASE 
    WHEN region IN ('IOWA', 'ILLINOIS', 'INDIANA', 'MINNESOTA', 'OHIO') THEN 'US_CORN_BELT'
    WHEN region IN ('RIO_GRANDE_DO_SUL', 'PARANA', 'MATO_GROSSO') THEN 'BRAZIL_SOY'
    WHEN region IN ('BUENOS_AIRES', 'CORDOBA', 'SANTA_FE') THEN 'ARGENTINA_SOY'
    ELSE 'OTHER'
  END AS production_region,
  CURRENT_TIMESTAMP() AS updated_at
FROM `cbi-v14.forecasting_data_warehouse.weather_data`;

-- ----------------------------------------------------------------------------
-- STEP 4: PULL ALL USDA REPORTS DATA
-- ----------------------------------------------------------------------------

CREATE OR REPLACE TABLE `cbi-v14.raw_intelligence.all_usda_data`
PARTITION BY DATE(report_date)
CLUSTER BY report_type AS
SELECT 
  report_date,
  report_type,
  commodity,
  country,
  metric_name,
  metric_value,
  unit,
  forecast_value,
  previous_value,
  (metric_value - previous_value) / NULLIF(previous_value, 0) AS change_pct,
  CASE 
    WHEN ABS((metric_value - forecast_value) / NULLIF(forecast_value, 0)) > 0.05 THEN 'SURPRISE'
    ELSE 'EXPECTED'
  END AS market_reaction,
  CURRENT_TIMESTAMP() AS updated_at
FROM `cbi-v14.forecasting_data_warehouse.usda_reports`;

-- ----------------------------------------------------------------------------
-- STEP 5: PULL ALL FUTURES POSITIONS (COT DATA)
-- ----------------------------------------------------------------------------

CREATE OR REPLACE TABLE `cbi-v14.raw_intelligence.all_cot_data`
PARTITION BY DATE(report_date)
CLUSTER BY commodity AS
SELECT 
  report_date,
  commodity,
  contract_market_name,
  open_interest_all,
  
  -- Commercial positions (hedgers)
  commercial_long,
  commercial_short,
  commercial_net,
  commercial_long - LAG(commercial_long) OVER (PARTITION BY commodity ORDER BY report_date) AS commercial_long_change,
  commercial_short - LAG(commercial_short) OVER (PARTITION BY commodity ORDER BY report_date) AS commercial_short_change,
  
  -- Non-commercial positions (speculators)
  noncommercial_long,
  noncommercial_short,
  noncommercial_net,
  noncommercial_long - LAG(noncommercial_long) OVER (PARTITION BY commodity ORDER BY report_date) AS spec_long_change,
  noncommercial_short - LAG(noncommercial_short) OVER (PARTITION BY commodity ORDER BY report_date) AS spec_short_change,
  
  -- Small traders
  nonreportable_long,
  nonreportable_short,
  
  -- Calculate sentiment indicators
  SAFE_DIVIDE(noncommercial_long, noncommercial_long + noncommercial_short) AS spec_long_ratio,
  SAFE_DIVIDE(commercial_short, commercial_long + commercial_short) AS commercial_hedge_ratio,
  
  -- Historical percentiles
  PERCENT_RANK() OVER (PARTITION BY commodity ORDER BY noncommercial_net) AS spec_net_percentile,
  PERCENT_RANK() OVER (PARTITION BY commodity ORDER BY commercial_net) AS commercial_net_percentile,
  
  CURRENT_TIMESTAMP() AS updated_at
FROM `cbi-v14.forecasting_data_warehouse.cot_reports`;

-- ----------------------------------------------------------------------------
-- STEP 6: PULL ALL SUPPLY/DEMAND DATA
-- ----------------------------------------------------------------------------

CREATE OR REPLACE TABLE `cbi-v14.raw_intelligence.all_supply_demand`
PARTITION BY DATE(date)
CLUSTER BY commodity, country AS
SELECT 
  date,
  commodity,
  country,
  crop_year,
  
  -- Supply side
  planted_area_ha,
  harvested_area_ha,
  yield_mt_per_ha,
  production_mt,
  beginning_stocks_mt,
  imports_mt,
  total_supply_mt,
  
  -- Demand side
  domestic_consumption_mt,
  exports_mt,
  crush_mt,
  feed_use_mt,
  food_use_mt,
  industrial_use_mt,
  total_demand_mt,
  
  -- Balance
  ending_stocks_mt,
  stocks_to_use_ratio,
  
  -- Year-over-year changes
  (production_mt - LAG(production_mt) OVER (PARTITION BY commodity, country ORDER BY date)) / 
    NULLIF(LAG(production_mt) OVER (PARTITION BY commodity, country ORDER BY date), 0) AS production_yoy,
  (exports_mt - LAG(exports_mt) OVER (PARTITION BY commodity, country ORDER BY date)) / 
    NULLIF(LAG(exports_mt) OVER (PARTITION BY commodity, country ORDER BY date), 0) AS exports_yoy,
  (ending_stocks_mt - LAG(ending_stocks_mt) OVER (PARTITION BY commodity, country ORDER BY date)) / 
    NULLIF(LAG(ending_stocks_mt) OVER (PARTITION BY commodity, country ORDER BY date), 0) AS stocks_yoy,
    
  CURRENT_TIMESTAMP() AS updated_at
FROM `cbi-v14.forecasting_data_warehouse.supply_demand_data`;

-- ----------------------------------------------------------------------------
-- STEP 7: PULL ALL EXPORT/IMPORT INSPECTION DATA
-- ----------------------------------------------------------------------------

CREATE OR REPLACE TABLE `cbi-v14.raw_intelligence.all_trade_flows`
PARTITION BY DATE(week_ending)
CLUSTER BY commodity, destination AS
SELECT 
  week_ending,
  commodity,
  origin_country,
  destination_country AS destination,
  
  -- Weekly volumes
  weekly_exports_mt,
  cumulative_exports_mt,
  
  -- Comparisons
  prior_week_exports_mt,
  prior_year_same_week_mt,
  prior_year_cumulative_mt,
  
  -- Calculate pace
  (weekly_exports_mt - prior_week_exports_mt) / NULLIF(prior_week_exports_mt, 0) AS week_over_week_change,
  (cumulative_exports_mt - prior_year_cumulative_mt) / NULLIF(prior_year_cumulative_mt, 0) AS year_over_year_pace,
  
  -- Outstanding sales
  outstanding_sales_mt,
  new_sales_mt,
  cancellations_mt,
  
  -- Market share
  SAFE_DIVIDE(weekly_exports_mt, SUM(weekly_exports_mt) OVER (PARTITION BY week_ending, commodity)) AS market_share,
  
  CURRENT_TIMESTAMP() AS updated_at
FROM `cbi-v14.forecasting_data_warehouse.export_inspections`;

-- ----------------------------------------------------------------------------
-- STEP 8: PULL ALL CRUSH/PROCESSING DATA
-- ----------------------------------------------------------------------------

CREATE OR REPLACE TABLE `cbi-v14.raw_intelligence.all_crush_data`
PARTITION BY DATE(report_date)
CLUSTER BY country AS
SELECT 
  report_date,
  country,
  
  -- Monthly crush volumes
  soybeans_crushed_mt,
  oil_produced_mt,
  meal_produced_mt,
  
  -- Crush margins
  soybean_price_usd,
  oil_price_usd,
  meal_price_usd,
  (oil_price_usd * oil_yield + meal_price_usd * meal_yield - soybean_price_usd) AS gross_crush_margin,
  
  -- Capacity utilization
  crush_capacity_mt,
  SAFE_DIVIDE(soybeans_crushed_mt, crush_capacity_mt) AS capacity_utilization,
  
  -- Year-over-year
  LAG(soybeans_crushed_mt, 12) OVER (PARTITION BY country ORDER BY report_date) AS prior_year_crush,
  (soybeans_crushed_mt - LAG(soybeans_crushed_mt, 12) OVER (PARTITION BY country ORDER BY report_date)) /
    NULLIF(LAG(soybeans_crushed_mt, 12) OVER (PARTITION BY country ORDER BY report_date), 0) AS crush_yoy_change,
    
  CURRENT_TIMESTAMP() AS updated_at
FROM `cbi-v14.forecasting_data_warehouse.crush_reports`;

-- ----------------------------------------------------------------------------
-- STEP 9: PULL ALL VESSEL/SHIPPING DATA
-- ----------------------------------------------------------------------------

CREATE OR REPLACE TABLE `cbi-v14.raw_intelligence.all_shipping_data`
PARTITION BY DATE(date)
CLUSTER BY route AS
SELECT 
  date,
  route,
  vessel_type,
  origin_port,
  destination_port,
  
  -- Freight rates
  freight_rate_usd_per_mt,
  bunker_fuel_price_usd,
  
  -- Vessel counts
  vessels_loading,
  vessels_in_transit,
  vessels_waiting,
  
  -- Volume estimates
  estimated_volume_mt,
  
  -- Baltic Dry Index components
  baltic_dry_index,
  capesize_index,
  panamax_index,
  supramax_index,
  
  -- Time charter rates
  capesize_tc_avg,
  panamax_tc_avg,
  
  -- Route-specific premiums
  (freight_rate_usd_per_mt - AVG(freight_rate_usd_per_mt) OVER (PARTITION BY vessel_type ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW)) AS freight_premium,
  
  CURRENT_TIMESTAMP() AS updated_at
FROM `cbi-v14.forecasting_data_warehouse.shipping_data`;

-- ----------------------------------------------------------------------------
-- STEP 10: PULL ALL CURRENCY DATA
-- ----------------------------------------------------------------------------

CREATE OR REPLACE TABLE `cbi-v14.raw_intelligence.all_fx_rates`
PARTITION BY DATE(date)
CLUSTER BY currency_pair AS
SELECT 
  Date AS date,
  CONCAT(SUBSTR(Symbol, 1, 3), '/', SUBSTR(Symbol, 4, 3)) AS currency_pair,
  Open AS open,
  High AS high,
  Low AS low,
  Close AS close,
  
  -- Calculate returns
  (Close - LAG(Close, 1) OVER (PARTITION BY Symbol ORDER BY Date)) / NULLIF(LAG(Close, 1) OVER (PARTITION BY Symbol ORDER BY Date), 0) AS return_1d,
  (Close - LAG(Close, 5) OVER (PARTITION BY Symbol ORDER BY Date)) / NULLIF(LAG(Close, 5) OVER (PARTITION BY Symbol ORDER BY Date), 0) AS return_5d,
  (Close - LAG(Close, 20) OVER (PARTITION BY Symbol ORDER BY Date)) / NULLIF(LAG(Close, 20) OVER (PARTITION BY Symbol ORDER BY Date), 0) AS return_20d,
  
  -- Moving averages
  AVG(Close) OVER (PARTITION BY Symbol ORDER BY Date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS ma_50,
  AVG(Close) OVER (PARTITION BY Symbol ORDER BY Date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW) AS ma_200,
  
  -- Volatility
  STDDEV(Close) OVER (PARTITION BY Symbol ORDER BY Date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS volatility_30d,
  
  CURRENT_TIMESTAMP() AS updated_at
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE Symbol IN ('BRL=X', 'CNY=X', 'ARS=X', 'EUR=X', 'CAD=X', 'AUD=X', 'INR=X', 'RUB=X')
  AND Date >= '2000-01-01';

-- ----------------------------------------------------------------------------
-- STEP 11: PULL ALL ENERGY PRICES
-- ----------------------------------------------------------------------------

CREATE OR REPLACE TABLE `cbi-v14.raw_intelligence.all_energy_prices`
PARTITION BY DATE(date)
CLUSTER BY commodity AS
SELECT 
  Date AS date,
  CASE 
    WHEN Symbol = 'CL=F' THEN 'WTI_CRUDE'
    WHEN Symbol = 'BZ=F' THEN 'BRENT_CRUDE'
    WHEN Symbol = 'NG=F' THEN 'NATURAL_GAS'
    WHEN Symbol = 'RB=F' THEN 'GASOLINE'
    WHEN Symbol = 'HO=F' THEN 'HEATING_OIL'
    ELSE Symbol
  END AS commodity,
  Open AS open,
  High AS high,
  Low AS low,
  Close AS close,
  Volume AS volume,
  
  -- Returns
  (Close - LAG(Close, 1) OVER (PARTITION BY Symbol ORDER BY Date)) / NULLIF(LAG(Close, 1) OVER (PARTITION BY Symbol ORDER BY Date), 0) AS return_1d,
  (Close - LAG(Close, 5) OVER (PARTITION BY Symbol ORDER BY Date)) / NULLIF(LAG(Close, 5) OVER (PARTITION BY Symbol ORDER BY Date), 0) AS return_5d,
  
  -- Crack spread (if crude)
  CASE 
    WHEN Symbol = 'CL=F' THEN 
      (SELECT AVG(c2.Close * 42 - c1.Close * 3) FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized` c2 
       WHERE c2.Symbol = 'RB=F' AND c2.Date = Date) 
  END AS crack_spread,
  
  CURRENT_TIMESTAMP() AS updated_at
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE Symbol IN ('CL=F', 'BZ=F', 'NG=F', 'RB=F', 'HO=F', 'NATGAS=F')
  AND Date >= '2000-01-01';

-- ----------------------------------------------------------------------------
-- STEP 12: PULL ALL EQUITY INDICES
-- ----------------------------------------------------------------------------

CREATE OR REPLACE TABLE `cbi-v14.raw_intelligence.all_equity_indices`
PARTITION BY DATE(date)
CLUSTER BY index_name AS
SELECT 
  Date AS date,
  CASE 
    WHEN Symbol = '^GSPC' THEN 'SP500'
    WHEN Symbol = '^DJI' THEN 'DOW_JONES'
    WHEN Symbol = '^IXIC' THEN 'NASDAQ'
    WHEN Symbol = '^RUT' THEN 'RUSSELL_2000'
    WHEN Symbol = '^VIX' THEN 'VIX'
    WHEN Symbol = '^TNX' THEN '10Y_TREASURY'
    ELSE Symbol
  END AS index_name,
  Open AS open,
  High AS high,
  Low AS low,
  Close AS close,
  Volume AS volume,
  
  -- Calculate fear/greed indicators
  CASE 
    WHEN Symbol = '^VIX' AND Close > 30 THEN 'EXTREME_FEAR'
    WHEN Symbol = '^VIX' AND Close > 20 THEN 'FEAR'
    WHEN Symbol = '^VIX' AND Close < 15 THEN 'GREED'
    ELSE 'NEUTRAL'
  END AS market_sentiment,
  
  -- Returns
  (Close - LAG(Close, 1) OVER (PARTITION BY Symbol ORDER BY Date)) / NULLIF(LAG(Close, 1) OVER (PARTITION BY Symbol ORDER BY Date), 0) AS return_1d,
  (Close - LAG(Close, 5) OVER (PARTITION BY Symbol ORDER BY Date)) / NULLIF(LAG(Close, 5) OVER (PARTITION BY Symbol ORDER BY Date), 0) AS return_5d,
  
  CURRENT_TIMESTAMP() AS updated_at
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE Symbol IN ('^GSPC', '^DJI', '^IXIC', '^RUT', '^VIX', '^TNX', '^FTSE', '^N225', '^HSI')
  AND Date >= '2000-01-01';

-- ----------------------------------------------------------------------------
-- STEP 13: CREATE MASTER FEATURE TABLE WITH EVERYTHING
-- ----------------------------------------------------------------------------

CREATE OR REPLACE TABLE `cbi-v14.features.master_feature_universe`
PARTITION BY DATE(date)
CLUSTER BY date AS
SELECT 
  p.time AS date,
  
  -- Core soybean prices
  p.close AS zl_price,
  p.open AS zl_open,
  p.high AS zl_high,
  p.low AS zl_low,
  p.volume AS zl_volume,
  p.return_1d AS zl_return_1d,
  p.return_5d AS zl_return_5d,
  p.return_20d AS zl_return_20d,
  p.return_60d AS zl_return_60d,
  p.volatility_20d AS zl_volatility_20d,
  p.ma_20 AS zl_ma_20,
  p.ma_50 AS zl_ma_50,
  p.ma_200 AS zl_ma_200,
  
  -- Related commodities
  corn.close AS corn_price,
  corn.return_5d AS corn_return_5d,
  wheat.close AS wheat_price,
  wheat.return_5d AS wheat_return_5d,
  
  -- Energy
  oil.close AS crude_oil_price,
  oil.return_5d AS oil_return_5d,
  
  -- Currencies
  brl.close AS usd_brl,
  brl.return_5d AS brl_return_5d,
  cny.close AS usd_cny,
  cny.return_5d AS cny_return_5d,
  
  -- Market indicators
  vix.close AS vix_level,
  CASE 
    WHEN vix.close > 30 THEN 'CRISIS'
    WHEN vix.close > 20 THEN 'ELEVATED'
    ELSE 'NORMAL'
  END AS vix_regime,
  
  sp500.close AS sp500_level,
  sp500.return_5d AS sp500_return_5d,
  
  -- COT positioning
  cot.spec_net_percentile AS spec_positioning,
  cot.commercial_hedge_ratio AS commercial_hedging,
  
  -- Supply/demand
  sd.stocks_to_use_ratio AS global_stocks_use,
  sd.production_yoy AS production_change,
  sd.exports_yoy AS exports_change,
  
  -- Weather
  w.drought_index AS us_drought_index,
  w.precipitation_mm AS brazil_precip,
  w.temperature_avg AS argentina_temp,
  
  -- Seasonality
  EXTRACT(MONTH FROM p.time) AS month,
  EXTRACT(WEEK FROM p.time) AS week_of_year,
  CASE 
    WHEN EXTRACT(MONTH FROM p.time) IN (3,4,5) THEN 'PLANTING'
    WHEN EXTRACT(MONTH FROM p.time) IN (6,7,8) THEN 'GROWING'
    WHEN EXTRACT(MONTH FROM p.time) IN (9,10,11) THEN 'HARVEST'
    ELSE 'OFF_SEASON'
  END AS season,
  
  -- Crush margins
  cr.gross_crush_margin AS crush_margin,
  cr.capacity_utilization AS crush_utilization,
  
  -- Trade flows
  tf.year_over_year_pace AS export_pace,
  tf.outstanding_sales_mt AS outstanding_sales,
  
  -- Shipping
  sh.freight_rate_usd_per_mt AS freight_rate,
  sh.baltic_dry_index AS baltic_dry,
  
  -- Calculate composite indicators
  (p.return_5d + corn.return_5d + wheat.return_5d) / 3 AS grain_complex_momentum,
  ABS(brl.return_5d) + ABS(cny.return_5d) AS fx_volatility,
  
  CURRENT_TIMESTAMP() AS updated_at
  
FROM `cbi-v14.forecasting_data_warehouse.soybean_prices_complete` p

-- Join all related commodities
LEFT JOIN `cbi-v14.forecasting_data_warehouse.soybean_prices_complete` corn
  ON p.time = corn.time AND corn.symbol = 'ZC=F'
  
LEFT JOIN `cbi-v14.forecasting_data_warehouse.soybean_prices_complete` wheat  
  ON p.time = wheat.time AND wheat.symbol = 'ZW=F'
  
LEFT JOIN `cbi-v14.raw_intelligence.all_energy_prices` oil
  ON DATE(p.time) = oil.date AND oil.commodity = 'WTI_CRUDE'
  
LEFT JOIN `cbi-v14.raw_intelligence.all_fx_rates` brl
  ON DATE(p.time) = brl.date AND brl.currency_pair = 'BRL/USD'
  
LEFT JOIN `cbi-v14.raw_intelligence.all_fx_rates` cny
  ON DATE(p.time) = cny.date AND cny.currency_pair = 'CNY/USD'
  
LEFT JOIN `cbi-v14.raw_intelligence.all_equity_indices` vix
  ON DATE(p.time) = vix.date AND vix.index_name = 'VIX'
  
LEFT JOIN `cbi-v14.raw_intelligence.all_equity_indices` sp500
  ON DATE(p.time) = sp500.date AND sp500.index_name = 'SP500'
  
LEFT JOIN `cbi-v14.raw_intelligence.all_cot_data` cot
  ON DATE(p.time) = cot.report_date AND cot.commodity = 'SOYBEANS'
  
LEFT JOIN `cbi-v14.raw_intelligence.all_supply_demand` sd
  ON DATE(p.time) = sd.date AND sd.commodity = 'SOYBEANS' AND sd.country = 'WORLD'
  
LEFT JOIN `cbi-v14.raw_intelligence.all_weather_data` w
  ON DATE(p.time) = w.date AND w.production_region = 'US_CORN_BELT'
  
LEFT JOIN `cbi-v14.raw_intelligence.all_crush_data` cr
  ON DATE(p.time) = cr.report_date AND cr.country = 'USA'
  
LEFT JOIN `cbi-v14.raw_intelligence.all_trade_flows` tf
  ON DATE(p.time) = tf.week_ending AND tf.commodity = 'SOYBEANS' AND tf.destination = 'CHINA'
  
LEFT JOIN `cbi-v14.raw_intelligence.all_shipping_data` sh
  ON DATE(p.time) = sh.date AND sh.route = 'US_GULF_CHINA'

WHERE p.symbol = 'ZL=F'
  AND p.time >= '2000-01-01';

-- ----------------------------------------------------------------------------
-- VERIFICATION - COUNT EVERYTHING WE LOADED
-- ----------------------------------------------------------------------------

SELECT 'Data Load Summary' AS report;

SELECT 
  'soybean_prices_complete' AS table_name,
  COUNT(*) AS row_count,
  MIN(time) AS min_date,
  MAX(time) AS max_date
FROM `cbi-v14.forecasting_data_warehouse.soybean_prices_complete`

UNION ALL

SELECT 
  'all_economic_indicators',
  COUNT(*),
  MIN(date),
  MAX(date)
FROM `cbi-v14.raw_intelligence.all_economic_indicators`

UNION ALL

SELECT 
  'all_weather_data',
  COUNT(*),
  MIN(date),
  MAX(date)
FROM `cbi-v14.raw_intelligence.all_weather_data`

UNION ALL

SELECT 
  'master_feature_universe',
  COUNT(*),
  MIN(date),
  MAX(date)
FROM `cbi-v14.features.master_feature_universe`;

-- THIS IS REAL DATA, NO FUCKING PLACEHOLDERS!


