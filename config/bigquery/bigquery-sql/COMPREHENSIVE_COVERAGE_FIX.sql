-- ============================================
-- COMPREHENSIVE COVERAGE FIX
-- Addresses all 6 root causes identified in the analysis
-- ============================================

-- Create backup before major changes
CREATE OR REPLACE TABLE `cbi-v14.models_v4.training_dataset_pre_coverage_fix_backup` AS
SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched`;

-- ============================================
-- ROOT CAUSE 1: WEEKEND/HOLIDAY HANDLING
-- Create weekend-filled price data (carry Friday → weekend)
-- ============================================

CREATE OR REPLACE TABLE `cbi-v14.models_v4.yahoo_finance_weekend_complete` AS
WITH 
-- Get all training dates including weekends
all_training_dates AS (
  SELECT DISTINCT date
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  ORDER BY date
),

-- Get raw Yahoo Finance data (trading days only)
yahoo_trading_days AS (
  SELECT 
    date,
    symbol,
    Close,
    Volume,
    ROW_NUMBER() OVER (PARTITION BY date, symbol ORDER BY pulled_at DESC) as rn
  FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
  WHERE symbol IN ('ZL=F', 'ZC=F', 'ZW=F', 'CL=F', 'ZM=F', 'FCPO=F', '^VIX', 'DX-Y.NYB')
    AND Close IS NOT NULL
),

-- Filter to latest data per day per symbol
yahoo_clean AS (
  SELECT date, symbol, Close, Volume
  FROM yahoo_trading_days
  WHERE rn = 1
),

-- Create grid of all dates × all symbols
date_symbol_grid AS (
  SELECT 
    atd.date,
    sym.symbol
  FROM all_training_dates atd
  CROSS JOIN (
    SELECT DISTINCT symbol FROM yahoo_clean
  ) sym
),

-- Forward fill prices for weekends/holidays
weekend_filled AS (
  SELECT 
    dsg.date,
    dsg.symbol,
    -- Forward fill price (last known trading price)
    LAST_VALUE(yc.Close IGNORE NULLS) OVER (
      PARTITION BY dsg.symbol 
      ORDER BY dsg.date 
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as Close,
    -- Volume = 0 on weekends/holidays
    CASE 
      WHEN EXTRACT(DAYOFWEEK FROM dsg.date) IN (1, 7) THEN 0  -- Weekend
      WHEN yc.Volume IS NOT NULL THEN yc.Volume  -- Trading day
      ELSE 0  -- Holiday
    END as Volume,
    -- Mark data source for tracking
    CASE 
      WHEN yc.Close IS NOT NULL THEN 'trading_day'
      WHEN EXTRACT(DAYOFWEEK FROM dsg.date) IN (1, 7) THEN 'weekend_filled'
      ELSE 'holiday_filled'
    END as data_source
  FROM date_symbol_grid dsg
  LEFT JOIN yahoo_clean yc ON dsg.date = yc.date AND dsg.symbol = yc.symbol
)

SELECT * FROM weekend_filled
WHERE Close IS NOT NULL  -- Only include dates where we have price data
ORDER BY symbol, date;

-- ============================================
-- ROOT CAUSE 2: MONTHLY UNEMPLOYMENT → DAILY
-- Forward-fill monthly economic data to daily frequency
-- ============================================

CREATE OR REPLACE TABLE `cbi-v14.models_v4.economic_indicators_daily_complete` AS
WITH 
-- Get all training dates
all_training_dates AS (
  SELECT DISTINCT date
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  ORDER BY date
),

-- Get economic indicators (convert time to date)
economic_raw AS (
  SELECT 
    CAST(time AS DATE) as date,
    indicator,
    value
  FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
  WHERE indicator IN (
    'ten_year_treasury', 'usd_cny_rate_fred', 'usd_brl_rate_fred',
    'dollar_index_fred', 'fed_funds_rate', 'unemployment_rate'
  )
  AND value IS NOT NULL
  AND value > 0  -- Remove invalid values
),

-- Create grid of all dates × all indicators
date_indicator_grid AS (
  SELECT 
    atd.date,
    ei.indicator
  FROM all_training_dates atd
  CROSS JOIN (
    SELECT DISTINCT indicator FROM economic_raw
  ) ei
),

-- Forward fill each indicator to daily frequency
daily_filled AS (
  SELECT 
    dig.date,
    dig.indicator,
    -- Forward fill: carry last known value forward
    LAST_VALUE(er.value IGNORE NULLS) OVER (
      PARTITION BY dig.indicator 
      ORDER BY dig.date 
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as value,
    -- Track data freshness
    DATE_DIFF(
      dig.date,
      LAST_VALUE(er.date IGNORE NULLS) OVER (
        PARTITION BY dig.indicator 
        ORDER BY dig.date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
      ),
      DAY
    ) as days_since_last_update,
    -- Mark actual vs filled data
    CASE 
      WHEN er.value IS NOT NULL THEN 'actual'
      ELSE 'forward_filled'
    END as data_source
  FROM date_indicator_grid dig
  LEFT JOIN economic_raw er ON dig.date = er.date AND dig.indicator = er.indicator
)

SELECT * FROM daily_filled
WHERE value IS NOT NULL
  AND days_since_last_update <= 90  -- Don't forward-fill beyond 90 days
ORDER BY indicator, date;

-- ============================================
-- ROOT CAUSE 3-6: ALTERNATIVE SOURCES FOR STALE DATA
-- Note: Yahoo Finance doesn't have CNY=X or BRL=X in our data
-- Use FRED data with forward-fill for recent gaps
-- ============================================

CREATE OR REPLACE TABLE `cbi-v14.models_v4.alternative_fx_rates` AS
WITH 
-- Get all training dates
all_training_dates AS (
  SELECT DISTINCT date
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  ORDER BY date
),

-- Get FRED FX rates
fred_usd_cny AS (
  SELECT 
    CAST(time AS DATE) as date,
    value as usd_cny_rate,
    'fred' as source
  FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
  WHERE indicator = 'usd_cny_rate_fred' AND value IS NOT NULL
),

fred_usd_brl AS (
  SELECT 
    CAST(time AS DATE) as date,
    value as usd_brl_rate,
    'fred' as source
  FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
  WHERE indicator = 'usd_brl_rate_fred' AND value IS NOT NULL
),

-- Forward fill FRED rates for recent dates
fx_filled AS (
  SELECT 
    atd.date,
    -- Forward fill USD/CNY (last known value)
    LAST_VALUE(cny.usd_cny_rate IGNORE NULLS) OVER (
      ORDER BY atd.date 
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as usd_cny_rate,
    -- Forward fill USD/BRL (last known value)
    LAST_VALUE(brl.usd_brl_rate IGNORE NULLS) OVER (
      ORDER BY atd.date 
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as usd_brl_rate
  FROM all_training_dates atd
  LEFT JOIN fred_usd_cny cny ON atd.date = cny.date
  LEFT JOIN fred_usd_brl brl ON atd.date = brl.date
)

SELECT * FROM fx_filled
WHERE date IS NOT NULL
ORDER BY date;

-- ============================================
-- COMPREHENSIVE UPDATE: Apply all fixes
-- ============================================

MERGE `cbi-v14.models_v4.training_dataset_super_enriched` AS target
USING (
  WITH 
  -- Aggregate weekend-filled Yahoo data
  yahoo_agg AS (
    SELECT 
      date,
      MAX(CASE WHEN symbol = 'ZL=F' THEN Close END) as zl_close,
      MAX(CASE WHEN symbol = 'ZL=F' THEN Volume END) as zl_volume,
      MAX(CASE WHEN symbol = 'ZC=F' THEN Close END) as corn_close,
      MAX(CASE WHEN symbol = 'ZW=F' THEN Close END) as wheat_close,
      MAX(CASE WHEN symbol = 'CL=F' THEN Close END) as crude_close,
      MAX(CASE WHEN symbol = 'ZM=F' THEN Close END) as meal_close,
      MAX(CASE WHEN symbol = 'FCPO=F' THEN Close END) as palm_close,
      MAX(CASE WHEN symbol = '^VIX' THEN Close END) as vix_close,
      MAX(CASE WHEN symbol = 'DX-Y.NYB' THEN Close END) as dxy_close
    FROM `cbi-v14.models_v4.yahoo_finance_weekend_complete`
    GROUP BY date
  ),
  
  -- Aggregate daily-filled economic data
  econ_agg AS (
    SELECT 
      date,
      MAX(CASE WHEN indicator = 'ten_year_treasury' THEN value END) as treasury_yield,
      MAX(CASE WHEN indicator = 'unemployment_rate' THEN value END) as unemployment_rate,
      MAX(CASE WHEN indicator = 'fed_funds_rate' THEN value END) as fed_funds_rate,
      MAX(CASE WHEN indicator = 'dollar_index_fred' THEN value END) as dollar_index
    FROM `cbi-v14.models_v4.economic_indicators_daily_complete`
    GROUP BY date
  ),
  
  -- Alternative FX rates
  fx_rates AS (
    SELECT 
      date,
      usd_cny_rate,
      usd_brl_rate
    FROM `cbi-v14.models_v4.alternative_fx_rates`
  )
  
  -- Combine all data sources
  SELECT 
    COALESCE(y.date, e.date, fx.date) as date,
    
    -- Yahoo Finance fills
    y.zl_close, y.zl_volume, y.corn_close, y.wheat_close,
    y.crude_close, y.meal_close, y.palm_close, y.vix_close, y.dxy_close,
    
    -- Economic indicator fills
    e.treasury_yield, e.unemployment_rate, e.fed_funds_rate, e.dollar_index,
    
    -- FX rate fills
    fx.usd_cny_rate, fx.usd_brl_rate
    
  FROM yahoo_agg y
  FULL OUTER JOIN econ_agg e ON y.date = e.date
  FULL OUTER JOIN fx_rates fx ON COALESCE(y.date, e.date) = fx.date
  WHERE COALESCE(y.date, e.date, fx.date) IS NOT NULL
  
) AS source ON target.date = source.date
WHEN MATCHED THEN UPDATE SET
  -- Yahoo Finance updates (fill NULLs only)
  zl_price_current = COALESCE(target.zl_price_current, source.zl_close),
  zl_volume = COALESCE(target.zl_volume, source.zl_volume),
  corn_price = COALESCE(target.corn_price, source.corn_close),
  wheat_price = COALESCE(target.wheat_price, source.wheat_close),
  crude_oil_wti_new = COALESCE(target.crude_oil_wti_new, source.crude_close),
  crude_price = COALESCE(target.crude_price, source.crude_close),
  soybean_meal_price = COALESCE(target.soybean_meal_price, source.meal_close),
  palm_price = COALESCE(target.palm_price, source.palm_close),
  vix_level = COALESCE(target.vix_level, source.vix_close),
  vix_index_new = COALESCE(target.vix_index_new, source.vix_close),
  dxy_level = COALESCE(target.dxy_level, source.dxy_close),
  dollar_index = COALESCE(target.dollar_index, source.dxy_close),
  usd_index = COALESCE(target.usd_index, source.dxy_close),
  
  -- Economic indicator updates (fill NULLs only)
  treasury_10y_yield = COALESCE(target.treasury_10y_yield, source.treasury_yield),
  unemployment_rate = COALESCE(target.unemployment_rate, source.unemployment_rate),
  econ_unemployment_rate = COALESCE(target.econ_unemployment_rate, source.unemployment_rate),
  fed_funds_rate = COALESCE(target.fed_funds_rate, source.fed_funds_rate),
  
  -- FX rate updates (fill NULLs only)  
  usd_cny_rate = COALESCE(target.usd_cny_rate, source.usd_cny_rate),
  usd_brl_rate = COALESCE(target.usd_brl_rate, source.usd_brl_rate);

-- ============================================
-- FINAL COVERAGE VERIFICATION
-- ============================================

WITH final_results AS (
  SELECT 
    COUNT(*) as total_rows,
    
    -- Calculate final coverage percentages
    ROUND((1 - COUNTIF(zl_price_current IS NULL) / COUNT(*)) * 100, 1) as zl_price_coverage,
    ROUND((1 - COUNTIF(soybean_meal_price IS NULL) / COUNT(*)) * 100, 1) as meal_coverage,
    ROUND((1 - COUNTIF(treasury_10y_yield IS NULL) / COUNT(*)) * 100, 1) as treasury_coverage,
    ROUND((1 - COUNTIF(unemployment_rate IS NULL) / COUNT(*)) * 100, 1) as unemployment_coverage,
    ROUND((1 - COUNTIF(usd_cny_rate IS NULL) / COUNT(*)) * 100, 1) as usd_cny_coverage,
    ROUND((1 - COUNTIF(usd_brl_rate IS NULL) / COUNT(*)) * 100, 1) as usd_brl_coverage,
    ROUND((1 - COUNTIF(fed_funds_rate IS NULL) / COUNT(*)) * 100, 1) as fed_funds_coverage,
    
    -- Key features for training readiness
    ROUND((1 - COUNTIF(corn_price IS NULL) / COUNT(*)) * 100, 1) as corn_coverage,
    ROUND((1 - COUNTIF(wheat_price IS NULL) / COUNT(*)) * 100, 1) as wheat_coverage,
    ROUND((1 - COUNTIF(vix_level IS NULL) / COUNT(*)) * 100, 1) as vix_coverage,
    
    -- Remaining NULL counts
    COUNTIF(zl_price_current IS NULL) as zl_nulls_remaining,
    COUNTIF(unemployment_rate IS NULL) as unemployment_nulls_remaining
    
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
)

SELECT 
  'COMPREHENSIVE COVERAGE FIX RESULTS' as status,
  total_rows,
  
  -- Show improvements (target: 95%+)
  CONCAT('ZL Price: ', zl_price_coverage, '%') as zl_result,
  CONCAT('Meal Price: ', meal_coverage, '%') as meal_result,
  CONCAT('Treasury: ', treasury_coverage, '%') as treasury_result,
  CONCAT('Unemployment: ', unemployment_coverage, '%') as unemployment_result,
  CONCAT('Fed Funds: ', fed_funds_coverage, '%') as fed_funds_result,
  CONCAT('USD/CNY: ', usd_cny_coverage, '%') as usd_cny_result,
  CONCAT('USD/BRL: ', usd_brl_coverage, '%') as usd_brl_result,
  
  -- Additional key features
  CONCAT('Corn: ', corn_coverage, '%') as corn_result,
  CONCAT('Wheat: ', wheat_coverage, '%') as wheat_result,
  CONCAT('VIX: ', vix_coverage, '%') as vix_result,
  
  -- Training readiness assessment
  CASE 
    WHEN zl_price_coverage >= 95 AND meal_coverage >= 95 AND unemployment_coverage >= 95 
    THEN 'EXCELLENT - READY FOR TRAINING'
    WHEN zl_price_coverage >= 90 AND meal_coverage >= 90 AND unemployment_coverage >= 85 
    THEN 'GOOD - TRAINING READY'
    WHEN zl_price_coverage >= 80 AND meal_coverage >= 80 
    THEN 'ACCEPTABLE - CAN PROCEED'
    ELSE 'NEEDS MORE WORK'
  END as training_readiness,
  
  -- Issues fixed summary
  CASE 
    WHEN unemployment_coverage >= 95 THEN 'Monthly data forward-filled successfully'
    WHEN unemployment_coverage >= 80 THEN 'Partial forward-fill success'
    ELSE 'Forward-fill needs investigation'
  END as monthly_data_fix,
  
  CASE 
    WHEN zl_price_coverage >= 95 THEN 'Weekend/holiday gaps filled successfully'
    WHEN zl_price_coverage >= 85 THEN 'Partial weekend fill success'
    ELSE 'Weekend fill needs investigation'
  END as weekend_fix

FROM final_results;

-- ============================================
-- FEATURE USABILITY CHECK
-- Show which columns can now be included in training
-- ============================================

WITH usability_check AS (
  SELECT 
    'zl_price_current' as column_name,
    COUNTIF(zl_price_current IS NOT NULL) / COUNT(*) as coverage_rate,
    CASE WHEN COUNTIF(zl_price_current IS NOT NULL) / COUNT(*) >= 0.8 THEN 'INCLUDE' ELSE 'EXCLUDE' END as training_decision
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'soybean_meal_price' as column_name,
    COUNTIF(soybean_meal_price IS NOT NULL) / COUNT(*) as coverage_rate,
    CASE WHEN COUNTIF(soybean_meal_price IS NOT NULL) / COUNT(*) >= 0.8 THEN 'INCLUDE' ELSE 'EXCLUDE' END as training_decision
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'unemployment_rate' as column_name,
    COUNTIF(unemployment_rate IS NOT NULL) / COUNT(*) as coverage_rate,
    CASE WHEN COUNTIF(unemployment_rate IS NOT NULL) / COUNT(*) >= 0.8 THEN 'INCLUDE' ELSE 'EXCLUDE' END as training_decision
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'treasury_10y_yield' as column_name,
    COUNTIF(treasury_10y_yield IS NOT NULL) / COUNT(*) as coverage_rate,
    CASE WHEN COUNTIF(treasury_10y_yield IS NOT NULL) / COUNT(*) >= 0.8 THEN 'INCLUDE' ELSE 'EXCLUDE' END as training_decision
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'usd_cny_rate' as column_name,
    COUNTIF(usd_cny_rate IS NOT NULL) / COUNT(*) as coverage_rate,
    CASE WHEN COUNTIF(usd_cny_rate IS NOT NULL) / COUNT(*) >= 0.8 THEN 'INCLUDE' ELSE 'EXCLUDE' END as training_decision
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
)

SELECT 
  column_name,
  ROUND(coverage_rate * 100, 1) as coverage_percentage,
  training_decision
FROM usability_check
ORDER BY coverage_rate DESC;



