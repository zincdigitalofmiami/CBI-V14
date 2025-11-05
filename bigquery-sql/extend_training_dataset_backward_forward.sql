-- ============================================
-- EXTEND TRAINING DATASET BACKWARD AND FORWARD
-- Adds missing dates from 2020-01-02 to 2025-11-02
-- ============================================

-- Step 1: Get date range to extend
WITH date_range_to_add AS (
  SELECT date
  FROM UNNEST(GENERATE_DATE_ARRAY(
    DATE('2020-01-02'),  -- Start from earliest available
    DATE('2025-11-02')   -- Through latest available
  )) AS date
  WHERE date NOT IN (
    SELECT DISTINCT date 
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    WHERE zl_price_current IS NOT NULL
  )
),

-- Step 2: Get ZL price data from Yahoo Finance
yahoo_prices AS (
  SELECT 
    date,
    Close AS zl_price_current,
    Volume AS volume,
    High AS high,
    Low AS low,
    Open AS open_price
  FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
  WHERE symbol = 'ZL=F'
    AND date IN (SELECT date FROM date_range_to_add)
),

-- Step 3: Get other commodity prices from Yahoo
other_commodities AS (
  SELECT 
    date,
    MAX(IF(symbol = 'ZS=F', Close, NULL)) AS soybeans_price,
    MAX(IF(symbol = 'ZC=F', Close, NULL)) AS corn_price,
    MAX(IF(symbol = 'ZM=F', Close, NULL)) AS soybean_meal_price,
    MAX(IF(symbol = 'CL=F', Close, NULL)) AS crude_price,
    MAX(IF(symbol = 'GC=F', Close, NULL)) AS gold_price,
    MAX(IF(symbol = 'DX-Y.NYB', Close, NULL)) AS dxy_price,
    MAX(IF(symbol = '^VIX', Close, NULL)) AS vix_price
  FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
  WHERE date IN (SELECT date FROM date_range_to_add)
  GROUP BY date
),

-- Step 4: Get technical indicators for ZL
zl_indicators AS (
  SELECT 
    date,
    MAX(IF(symbol = 'ZL=F', rsi_14, NULL)) AS zl_rsi_14,
    MAX(IF(symbol = 'ZL=F', macd_line, NULL)) AS zl_macd_line,
    MAX(IF(symbol = 'ZL=F', macd_signal, NULL)) AS zl_macd_signal,
    MAX(IF(symbol = 'ZL=F', bb_middle, NULL)) AS zl_bb_middle,
    MAX(IF(symbol = 'ZL=F', bb_upper, NULL)) AS zl_bb_upper,
    MAX(IF(symbol = 'ZL=F', bb_lower, NULL)) AS zl_bb_lower
  FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
  WHERE symbol = 'ZL=F'
    AND date IN (SELECT date FROM date_range_to_add)
  GROUP BY date
),

-- Step 5: Combine all data
extended_data AS (
  SELECT 
    dr.date,
    yp.zl_price_current,
    yp.volume,
    yp.high,
    yp.low,
    yp.open_price AS open,
    oc.soybeans_price,
    oc.corn_price,
    oc.soybean_meal_price,
    oc.crude_price,
    oc.gold_price,
    oc.dxy_price,
    oc.vix_price,
    zi.zl_rsi_14,
    zi.zl_macd_line,
    zi.zl_macd_signal,
    zi.zl_bb_middle,
    zi.zl_bb_upper,
    zi.zl_bb_lower,
    -- Calculate targets (1w, 1m, 3m, 6m ahead)
    (SELECT Close 
     FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
     WHERE symbol = 'ZL=F' AND date = DATE_ADD(dr.date, INTERVAL 7 DAY)
     LIMIT 1) AS target_1w,
    (SELECT Close 
     FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
     WHERE symbol = 'ZL=F' AND date = DATE_ADD(dr.date, INTERVAL 30 DAY)
     LIMIT 1) AS target_1m,
    (SELECT Close 
     FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
     WHERE symbol = 'ZL=F' AND date = DATE_ADD(dr.date, INTERVAL 90 DAY)
     LIMIT 1) AS target_3m,
    (SELECT Close 
     FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
     WHERE symbol = 'ZL=F' AND date = DATE_ADD(dr.date, INTERVAL 180 DAY)
     LIMIT 1) AS target_6m
  FROM date_range_to_add dr
  LEFT JOIN yahoo_prices yp ON dr.date = yp.date
  LEFT JOIN other_commodities oc ON dr.date = oc.date
  LEFT JOIN zl_indicators zi ON dr.date = zi.date
  WHERE yp.zl_price_current IS NOT NULL  -- Only add rows with price data
)

-- Step 6: Insert into training dataset
INSERT INTO `cbi-v14.models_v4.training_dataset_super_enriched`
SELECT 
  date,
  zl_price_current,
  volume,
  high,
  low,
  open,
  -- Other prices (will be joined later via views)
  soybeans_price,
  corn_price,
  soybean_meal_price,
  crude_price,
  gold_price,
  dxy_price,
  vix_price,
  -- Technical indicators
  zl_rsi_14,
  zl_macd_line,
  zl_macd_signal,
  zl_bb_middle,
  zl_bb_upper,
  zl_bb_lower,
  -- Targets
  target_1w,
  target_1m,
  target_3m,
  target_6m,
  -- All other columns will be NULL initially, populated by feature engineering
  CURRENT_TIMESTAMP() AS updated_at
FROM extended_data
WHERE date NOT IN (
  SELECT DISTINCT date 
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
)
ORDER BY date;



