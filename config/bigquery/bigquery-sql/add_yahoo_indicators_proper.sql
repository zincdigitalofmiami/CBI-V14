-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- Add Yahoo Technical Indicators - Following Existing Pattern
-- Pattern from backfill_from_scraped_data.sql: LEFT JOIN from forecasting_data_warehouse
-- ============================================

-- Step 1: Create pivoted view of yahoo indicators (following existing pattern)
CREATE OR REPLACE VIEW `cbi-v14.models_v4.yahoo_indicators_wide` AS
WITH pivoted AS (
  SELECT 
    date,
    -- ZL Technical Indicators
    MAX(IF(symbol = 'ZL=F', rsi_14, NULL)) AS zl_rsi_14,
    MAX(IF(symbol = 'ZL=F', macd_line, NULL)) AS zl_macd_line,
    MAX(IF(symbol = 'ZL=F', macd_signal, NULL)) AS zl_macd_signal,
    MAX(IF(symbol = 'ZL=F', macd_histogram, NULL)) AS zl_macd_histogram,
    MAX(IF(symbol = 'ZL=F', bb_middle, NULL)) AS zl_bb_middle,
    MAX(IF(symbol = 'ZL=F', bb_upper, NULL)) AS zl_bb_upper,
    MAX(IF(symbol = 'ZL=F', bb_lower, NULL)) AS zl_bb_lower,
    MAX(IF(symbol = 'ZL=F', bb_percent, NULL)) AS zl_bb_percent,
    MAX(IF(symbol = 'ZL=F', ma_7, NULL)) AS zl_ma_7,
    MAX(IF(symbol = 'ZL=F', ma_30, NULL)) AS zl_ma_30,
    MAX(IF(symbol = 'ZL=F', ma_90, NULL)) AS zl_ma_90,
    
    -- Related Commodity RSI
    MAX(IF(symbol = 'ZS=F', rsi_14, NULL)) AS soybeans_rsi_14,
    MAX(IF(symbol = 'ZC=F', rsi_14, NULL)) AS corn_rsi_14,
    MAX(IF(symbol = 'ZM=F', rsi_14, NULL)) AS soybean_meal_rsi_14,
    MAX(IF(symbol = 'ZW=F', rsi_14, NULL)) AS wheat_rsi_14,
    MAX(IF(symbol = 'CL=F', rsi_14, NULL)) AS crude_rsi_14,
    MAX(IF(symbol = 'GC=F', rsi_14, NULL)) AS gold_rsi_14,
    
    -- FX/Economic
    MAX(IF(symbol = 'DX-Y.NYB', Close, NULL)) AS dxy_price_yahoo,
    MAX(IF(symbol = 'DX-Y.NYB', rsi_14, NULL)) AS dxy_rsi_14,
    MAX(IF(symbol = '^VIX', Close, NULL)) AS vix_price_yahoo,
    MAX(IF(symbol = '^VIX', rsi_14, NULL)) AS vix_rsi_14,
    
    -- Prices (_yahoo suffix to avoid conflicts)
    MAX(IF(symbol = 'ZS=F', Close, NULL)) AS soybeans_price_yahoo,
    MAX(IF(symbol = 'ZC=F', Close, NULL)) AS corn_price_yahoo,
    MAX(IF(symbol = 'ZM=F', Close, NULL)) AS soybean_meal_price_yahoo,
    MAX(IF(symbol = 'CL=F', Close, NULL)) AS crude_price_yahoo,
    MAX(IF(symbol = 'GC=F', Close, NULL)) AS gold_price_yahoo,
    MAX(IF(symbol = 'SI=F', Close, NULL)) AS silver_price,
    
    -- Returns
    MAX(IF(symbol = 'ZS=F', return_7d, NULL)) AS soybeans_return_7d,
    MAX(IF(symbol = 'ZC=F', return_7d, NULL)) AS corn_return_7d,
    MAX(IF(symbol = 'CL=F', return_7d, NULL)) AS crude_return_7d,
    MAX(IF(symbol = '^GSPC', return_1d, NULL)) AS sp500_return_1d,
    
    -- Indices/Bonds
    MAX(IF(symbol = '^GSPC', Close, NULL)) AS sp500_price,
    MAX(IF(symbol = '^TNX', Close, NULL)) AS treasury_10y_yield_yahoo,
    MAX(IF(symbol = '^TYX', Close, NULL)) AS treasury_30y_yield,
    
    -- Soft Commodities
    MAX(IF(symbol = 'SB=F', Close, NULL)) AS sugar_price,
    MAX(IF(symbol = 'CT=F', Close, NULL)) AS cotton_price,
    MAX(IF(symbol = 'KC=F', Close, NULL)) AS coffee_price,
    
    -- Currencies
    MAX(IF(symbol = 'EURUSD=X', Close, NULL)) AS eurusd_rate,
    MAX(IF(symbol = 'GBPUSD=X', Close, NULL)) AS gbpusd_rate,
    MAX(IF(symbol = 'JPY=X', Close, NULL)) AS usdjpy_rate,
    MAX(IF(symbol = 'CAD=X', Close, NULL)) AS usdcad_rate
    
  FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`  -- FOLLOWING PATTERN
  WHERE date IS NOT NULL
  GROUP BY date
)
SELECT * FROM pivoted WHERE date IS NOT NULL;

-- Step 2: Enhance _v_train_core with LEFT JOIN (exact pattern from backfill_from_scraped_data.sql)
-- This replaces the simple SELECT * with an enriched version
CREATE OR REPLACE VIEW `cbi-v14.models_v4._v_train_core` AS
SELECT 
  base.*,
  -- Yahoo Finance Technical Indicators
  yahoo.zl_rsi_14,
  yahoo.zl_macd_line,
  yahoo.zl_macd_signal,
  yahoo.zl_macd_histogram,
  yahoo.zl_bb_middle,
  yahoo.zl_bb_upper,
  yahoo.zl_bb_lower,
  yahoo.zl_bb_percent,
  yahoo.zl_ma_7,
  yahoo.zl_ma_30,
  yahoo.zl_ma_90,
  yahoo.soybeans_rsi_14,
  yahoo.corn_rsi_14,
  yahoo.soybean_meal_rsi_14,
  yahoo.wheat_rsi_14,
  yahoo.crude_rsi_14,
  yahoo.gold_rsi_14,
  yahoo.dxy_rsi_14,
  yahoo.vix_rsi_14,
  yahoo.soybeans_price_yahoo,
  yahoo.corn_price_yahoo,
  yahoo.soybean_meal_price_yahoo,
  yahoo.crude_price_yahoo,
  yahoo.gold_price_yahoo,
  yahoo.silver_price,
  yahoo.soybeans_return_7d,
  yahoo.corn_return_7d,
  yahoo.crude_return_7d,
  yahoo.sp500_return_1d,
  yahoo.dxy_price_yahoo,
  yahoo.vix_price_yahoo,
  yahoo.sp500_price,
  yahoo.treasury_10y_yield_yahoo,
  yahoo.treasury_30y_yield,
  yahoo.eurusd_rate,
  yahoo.gbpusd_rate,
  yahoo.usdjpy_rate,
  yahoo.usdcad_rate,
  yahoo.sugar_price,
  yahoo.cotton_price,
  yahoo.coffee_price
FROM `cbi-v14.models_v4.training_dataset_super_enriched` base
LEFT JOIN `cbi-v14.models_v4.yahoo_indicators_wide` yahoo
  ON base.date = yahoo.date;

