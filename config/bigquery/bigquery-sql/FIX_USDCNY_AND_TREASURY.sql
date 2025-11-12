-- ============================================
-- FIX USD/CNY RATE AND TREASURY 10Y YIELD
-- Get both to 100% coverage
-- ============================================

-- Step 1: Check USD/CNY availability in currency_data table
SELECT 
  'USD/CNY Availability Check' as check_type,
  COUNT(*) as total_records,
  COUNT(DISTINCT date) as unique_dates,
  MIN(date) as earliest_date,
  MAX(date) as latest_date,
  COUNTIF(rate IS NOT NULL AND rate > 0) as valid_rates
FROM `cbi-v14.forecasting_data_warehouse.currency_data`
WHERE from_currency = 'USD' AND to_currency = 'CNY';

-- Step 2: Create USD/CNY daily data from currency_data table
CREATE OR REPLACE TABLE `cbi-v14.models_v4.usd_cny_daily_complete` AS
WITH 
-- Get all training dates
training_dates AS (
  SELECT DISTINCT date
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  ORDER BY date
),

-- Get USD/CNY from currency_data table
currency_usd_cny AS (
  SELECT 
    date,
    rate as usd_cny_rate,
    'currency_data' as source
  FROM `cbi-v14.forecasting_data_warehouse.currency_data`
  WHERE from_currency = 'USD' AND to_currency = 'CNY'
    AND rate IS NOT NULL
    AND rate > 0
    AND rate < 20  -- Sanity check: USD/CNY typically 6-8 range
),

-- Forward-fill USD/CNY to daily frequency
usd_cny_daily_filled AS (
  SELECT 
    td.date,
    -- Forward fill USD/CNY rate
    LAST_VALUE(cu.usd_cny_rate IGNORE NULLS) OVER (
      ORDER BY td.date 
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as usd_cny_rate,
    -- Track data freshness
    DATE_DIFF(
      td.date,
      LAST_VALUE(cu.date IGNORE NULLS) OVER (
        ORDER BY td.date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
      ),
      DAY
    ) as days_since_update,
    -- Track data source
    LAST_VALUE(cu.source IGNORE NULLS) OVER (
      ORDER BY td.date 
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as data_source
  FROM training_dates td
  LEFT JOIN currency_usd_cny cu ON td.date = cu.date
)

SELECT 
  date,
  usd_cny_rate,
  days_since_update,
  data_source,
  -- Quality flags
  CASE 
    WHEN days_since_update <= 7 THEN 'fresh'
    WHEN days_since_update <= 30 THEN 'acceptable'
    WHEN days_since_update <= 90 THEN 'stale'
    ELSE 'very_stale'
  END as data_quality
FROM usd_cny_daily_filled
WHERE usd_cny_rate IS NOT NULL
ORDER BY date;

-- Step 3: Apply USD/CNY fix to training dataset
MERGE `cbi-v14.models_v4.training_dataset_super_enriched` AS target
USING (
  SELECT 
    date,
    usd_cny_rate
  FROM `cbi-v14.models_v4.usd_cny_daily_complete`
  WHERE data_quality IN ('fresh', 'acceptable', 'stale')  -- Exclude very_stale
  QUALIFY ROW_NUMBER() OVER (PARTITION BY date ORDER BY days_since_update ASC) = 1  -- One row per date
) AS source
ON target.date = source.date
WHEN MATCHED THEN UPDATE SET
  usd_cny_rate = COALESCE(target.usd_cny_rate, source.usd_cny_rate);

-- Step 4: Fill Treasury 10Y gaps with Yahoo Finance ^TNX
-- ^TNX has 1,467 records covering 2020-01-02 to 2025-10-31
CREATE OR REPLACE TABLE `cbi-v14.models_v4.treasury_10y_yahoo_complete` AS
WITH 
-- Get all training dates
training_dates AS (
  SELECT DISTINCT date
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  ORDER BY date
),

-- Get 10-year treasury from Yahoo Finance ^TNX
yahoo_tnx AS (
  SELECT 
    date,
    Close as treasury_10y_yield,
    'yahoo_tnx' as source
  FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
  WHERE symbol = '^TNX'  -- 10-Year Treasury Note Yield
    AND Close IS NOT NULL
    AND Close > 0
    AND Close < 20  -- Sanity check: yields typically 0-10%
  QUALIFY ROW_NUMBER() OVER (PARTITION BY date ORDER BY pulled_at DESC) = 1
),

-- Forward-fill treasury to all dates (including weekends)
treasury_daily_filled AS (
  SELECT 
    td.date,
    -- Forward fill treasury yield
    LAST_VALUE(yt.treasury_10y_yield IGNORE NULLS) OVER (
      ORDER BY td.date 
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as treasury_10y_yield,
    -- Track data freshness
    DATE_DIFF(
      td.date,
      LAST_VALUE(yt.date IGNORE NULLS) OVER (
        ORDER BY td.date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
      ),
      DAY
    ) as days_since_update,
    -- Track data source
    LAST_VALUE(yt.source IGNORE NULLS) OVER (
      ORDER BY td.date 
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as data_source
  FROM training_dates td
  LEFT JOIN yahoo_tnx yt ON td.date = yt.date
)

SELECT 
  date,
  treasury_10y_yield,
  days_since_update,
  data_source,
  -- Quality flags
  CASE 
    WHEN days_since_update <= 7 THEN 'fresh'
    WHEN days_since_update <= 30 THEN 'acceptable'
    WHEN days_since_update <= 90 THEN 'stale'
    ELSE 'very_stale'
  END as data_quality
FROM treasury_daily_filled
WHERE treasury_10y_yield IS NOT NULL
ORDER BY date;

-- Step 5: Apply Treasury fix to training dataset
MERGE `cbi-v14.models_v4.training_dataset_super_enriched` AS target
USING (
  SELECT 
    date,
    treasury_10y_yield
  FROM `cbi-v14.models_v4.treasury_10y_yahoo_complete`
  WHERE data_quality IN ('fresh', 'acceptable', 'stale')  -- Exclude very_stale
  QUALIFY ROW_NUMBER() OVER (PARTITION BY date ORDER BY days_since_update ASC) = 1  -- One row per date
) AS source
ON target.date = source.date
WHEN MATCHED THEN UPDATE SET
  treasury_10y_yield = COALESCE(target.treasury_10y_yield, source.treasury_10y_yield);

-- Step 6: Final verification of all improvements
WITH final_coverage AS (
  SELECT 
    COUNT(*) as total_rows,
    
    -- Key metrics
    ROUND((1 - COUNTIF(zl_price_current IS NULL) / COUNT(*)) * 100, 1) as zl_price_coverage,
    ROUND((1 - COUNTIF(soybean_meal_price IS NULL) / COUNT(*)) * 100, 1) as meal_coverage,
    ROUND((1 - COUNTIF(unemployment_rate IS NULL) / COUNT(*)) * 100, 1) as unemployment_coverage,
    ROUND((1 - COUNTIF(treasury_10y_yield IS NULL) / COUNT(*)) * 100, 1) as treasury_coverage,
    ROUND((1 - COUNTIF(usd_cny_rate IS NULL) / COUNT(*)) * 100, 1) as usd_cny_coverage,
    ROUND((1 - COUNTIF(fed_funds_rate IS NULL) / COUNT(*)) * 100, 1) as fed_funds_coverage,
    
    -- Additional features
    ROUND((1 - COUNTIF(corn_price IS NULL) / COUNT(*)) * 100, 1) as corn_coverage,
    ROUND((1 - COUNTIF(wheat_price IS NULL) / COUNT(*)) * 100, 1) as wheat_coverage,
    ROUND((1 - COUNTIF(vix_level IS NULL) / COUNT(*)) * 100, 1) as vix_coverage,
    ROUND((1 - COUNTIF(palm_price IS NULL) / COUNT(*)) * 100, 1) as palm_coverage,
    
    -- Count features ready for training (>80% coverage)
    (CASE WHEN COUNTIF(zl_price_current IS NOT NULL) / COUNT(*) >= 0.8 THEN 1 ELSE 0 END +
     CASE WHEN COUNTIF(soybean_meal_price IS NOT NULL) / COUNT(*) >= 0.8 THEN 1 ELSE 0 END +
     CASE WHEN COUNTIF(unemployment_rate IS NOT NULL) / COUNT(*) >= 0.8 THEN 1 ELSE 0 END +
     CASE WHEN COUNTIF(treasury_10y_yield IS NOT NULL) / COUNT(*) >= 0.8 THEN 1 ELSE 0 END +
     CASE WHEN COUNTIF(usd_cny_rate IS NOT NULL) / COUNT(*) >= 0.8 THEN 1 ELSE 0 END +
     CASE WHEN COUNTIF(fed_funds_rate IS NOT NULL) / COUNT(*) >= 0.8 THEN 1 ELSE 0 END +
     CASE WHEN COUNTIF(corn_price IS NOT NULL) / COUNT(*) >= 0.8 THEN 1 ELSE 0 END +
     CASE WHEN COUNTIF(wheat_price IS NOT NULL) / COUNT(*) >= 0.8 THEN 1 ELSE 0 END +
     CASE WHEN COUNTIF(vix_level IS NOT NULL) / COUNT(*) >= 0.8 THEN 1 ELSE 0 END +
     CASE WHEN COUNTIF(palm_price IS NOT NULL) / COUNT(*) >= 0.8 THEN 1 ELSE 0 END) as features_ready_for_training
    
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
)

SELECT 
  'FINAL COVERAGE RESULTS - POST USD/CNY & TREASURY FIX' as status,
  total_rows,
  
  -- Core features
  CONCAT('ZL Price: ', zl_price_coverage, '%') as zl_result,
  CONCAT('Meal Price: ', meal_coverage, '%') as meal_result,
  CONCAT('Unemployment: ', unemployment_coverage, '%') as unemployment_result,
  CONCAT('Treasury: ', treasury_coverage, '%') as treasury_result,
  CONCAT('USD/CNY: ', usd_cny_coverage, '%') as usd_cny_result,
  CONCAT('Fed Funds: ', fed_funds_coverage, '%') as fed_funds_result,
  
  -- Additional features
  CONCAT('Corn: ', corn_coverage, '%') as corn_result,
  CONCAT('Wheat: ', wheat_coverage, '%') as wheat_result,
  CONCAT('VIX: ', vix_coverage, '%') as vix_result,
  CONCAT('Palm: ', palm_coverage, '%') as palm_result,
  
  -- Training readiness
  CONCAT(features_ready_for_training, ' features ready (≥80% coverage)') as training_features,
  
  CASE 
    WHEN usd_cny_coverage >= 95 AND treasury_coverage >= 95 
    THEN 'PERFECT - ALL FEATURES READY'
    WHEN usd_cny_coverage >= 80 AND treasury_coverage >= 90 
    THEN 'EXCELLENT - READY FOR TRAINING'
    WHEN features_ready_for_training >= 8 
    THEN 'GOOD - SUFFICIENT FOR TRAINING'
    ELSE 'NEEDS REVIEW'
  END as final_assessment

FROM final_coverage;

