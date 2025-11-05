-- ============================================
-- Integrate Yahoo Finance Technical Indicators into Training Dataset
-- Joins technical indicators (RSI, MACD, Bollinger Bands) and related commodity data
-- ============================================

-- Step 1: Create view with all Yahoo Finance data pivoted by symbol
CREATE OR REPLACE VIEW `cbi-v14.market_data.yahoo_indicators_wide` AS
WITH pivoted AS (
  SELECT 
    date,
    -- Soybean Oil (main target) technical indicators
    MAX(IF(symbol = 'ZL=F', rsi_14, NULL)) AS zl_rsi_14,
    MAX(IF(symbol = 'ZL=F', macd_line, NULL)) AS zl_macd_line,
    MAX(IF(symbol = 'ZL=F', macd_signal, NULL)) AS zl_macd_signal,
    MAX(IF(symbol = 'ZL=F', macd_histogram, NULL)) AS zl_macd_histogram,
    MAX(IF(symbol = 'ZL=F', bb_middle, NULL)) AS zl_bb_middle,
    MAX(IF(symbol = 'ZL=F', bb_upper, NULL)) AS zl_bb_upper,
    MAX(IF(symbol = 'ZL=F', bb_lower, NULL)) AS zl_bb_lower,
    MAX(IF(symbol = 'ZL=F', bb_percent, NULL)) AS zl_bb_percent,
    
    -- Related commodities technical indicators
    MAX(IF(symbol = 'ZS=F', rsi_14, NULL)) AS soybeans_rsi_14,
    MAX(IF(symbol = 'ZC=F', rsi_14, NULL)) AS corn_rsi_14,
    MAX(IF(symbol = 'ZM=F', rsi_14, NULL)) AS soybean_meal_rsi_14,
    MAX(IF(symbol = 'ZW=F', rsi_14, NULL)) AS wheat_rsi_14,
    MAX(IF(symbol = 'CL=F', rsi_14, NULL)) AS crude_rsi_14,
    MAX(IF(symbol = 'GC=F', rsi_14, NULL)) AS gold_rsi_14,
    
    -- FX and economic indicators
    MAX(IF(symbol = 'DX-Y.NYB', Close, NULL)) AS dxy_price,
    MAX(IF(symbol = 'DX-Y.NYB', rsi_14, NULL)) AS dxy_rsi_14,
    MAX(IF(symbol = '^VIX', Close, NULL)) AS vix_price,
    MAX(IF(symbol = '^VIX', rsi_14, NULL)) AS vix_rsi_14,
    
    -- Related commodity prices with technical indicators (using _yahoo suffix to avoid conflicts)
    MAX(IF(symbol = 'ZS=F', Close, NULL)) AS soybeans_price_yahoo,
    MAX(IF(symbol = 'ZC=F', Close, NULL)) AS corn_price_yahoo,
    MAX(IF(symbol = 'ZM=F', Close, NULL)) AS soybean_meal_price_yahoo,
    MAX(IF(symbol = 'CL=F', Close, NULL)) AS crude_price_yahoo,
    
    -- Cross-asset momentum
    MAX(IF(symbol = 'ZS=F', return_7d, NULL)) AS soybeans_return_7d,
    MAX(IF(symbol = 'ZC=F', return_7d, NULL)) AS corn_return_7d,
    MAX(IF(symbol = 'CL=F', return_7d, NULL)) AS crude_return_7d,
    
    -- Stock indices (market sentiment)
    MAX(IF(symbol = '^GSPC', Close, NULL)) AS sp500_price,
    MAX(IF(symbol = '^GSPC', return_1d, NULL)) AS sp500_return_1d,
    MAX(IF(symbol = '^VIX', Close, NULL)) AS vix_close,
    
    -- Bonds (interest rates)
    MAX(IF(symbol = '^TNX', Close, NULL)) AS treasury_10y_yield_yahoo,
    MAX(IF(symbol = '^TYX', Close, NULL)) AS treasury_30y_yield,
    
    -- Soft commodities (substitutes)
    MAX(IF(symbol = 'SB=F', Close, NULL)) AS sugar_price,
    MAX(IF(symbol = 'CT=F', Close, NULL)) AS cotton_price,
    MAX(IF(symbol = 'KC=F', Close, NULL)) AS coffee_price,
    
    -- Metals (inflation hedge)
    MAX(IF(symbol = 'GC=F', Close, NULL)) AS gold_price_yahoo,
    MAX(IF(symbol = 'SI=F', Close, NULL)) AS silver_price,
    
    -- Currencies
    MAX(IF(symbol = 'EURUSD=X', Close, NULL)) AS eurusd_rate,
    MAX(IF(symbol = 'GBPUSD=X', Close, NULL)) AS gbpusd_rate,
    MAX(IF(symbol = 'JPY=X', Close, NULL)) AS usdjpy_rate,
    MAX(IF(symbol = 'CAD=X', Close, NULL)) AS usdcad_rate
    
  FROM `cbi-v14.market_data.yahoo_finance_enhanced`
  WHERE date IS NOT NULL
  GROUP BY date
)

SELECT 
  date,
  -- ZL Technical Indicators (main target)
  zl_rsi_14,
  zl_macd_line,
  zl_macd_signal,
  zl_macd_histogram,
  zl_bb_middle,
  zl_bb_upper,
  zl_bb_lower,
  zl_bb_percent,
  
  -- Related Commodity Technical Indicators
  soybeans_rsi_14,
  corn_rsi_14,
  soybean_meal_rsi_14,
  wheat_rsi_14,
  crude_rsi_14,
  gold_rsi_14,
  dxy_rsi_14,
  vix_rsi_14,
  
  -- Cross-Asset Prices (using _yahoo suffix to avoid conflicts with existing columns)
  soybeans_price_yahoo,
  corn_price_yahoo,
  soybean_meal_price_yahoo,
  crude_price_yahoo,
  gold_price_yahoo,
  silver_price_yahoo,
  
  -- Returns & Momentum
  soybeans_return_7d,
  corn_return_7d,
  crude_return_7d,
  sp500_return_1d,
  
  -- Economic Indicators
  dxy_price,
  vix_close,
  sp500_price,
  treasury_10y_yield_yahoo,
  treasury_30y_yield,
  eurusd_rate,
  gbpusd_rate,
  usdjpy_rate,
  usdcad_rate,
  
  -- Soft Commodities
  sugar_price,
  cotton_price,
  coffee_price
  
FROM pivoted
WHERE date IS NOT NULL;

-- Step 2: Join to training dataset
-- This will be used to enhance training_dataset_super_enriched
-- Run this as a view or table update depending on your architecture

-- Example: Update existing training dataset
-- ALTER TABLE `cbi-v14.models_v4.training_dataset_super_enriched`
-- ADD COLUMN IF NOT EXISTS zl_rsi_14 FLOAT64,
-- ADD COLUMN IF NOT EXISTS zl_macd_line FLOAT64,
-- ... etc

-- Then run:
-- UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
-- SET
--   zl_rsi_14 = y.zl_rsi_14,
--   zl_macd_line = y.zl_macd_line,
--   ...
-- FROM `cbi-v14.models_v4.yahoo_indicators_wide` y
-- WHERE t.date = y.date;

