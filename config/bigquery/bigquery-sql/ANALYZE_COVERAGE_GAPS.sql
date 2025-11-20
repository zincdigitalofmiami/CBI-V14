-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- ANALYZE COVERAGE GAPS AND MISSING DATA
-- Find out why we only got 71.9% coverage
-- ============================================

-- 1. DATE RANGE ANALYSIS
-- Check the date ranges of training dataset vs source tables
WITH date_ranges AS (
  SELECT 
    'training_dataset' as source,
    MIN(date) as earliest_date,
    MAX(date) as latest_date,
    COUNT(DISTINCT date) as total_dates
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'yahoo_finance_enhanced' as source,
    MIN(date) as earliest_date,
    MAX(date) as latest_date,
    COUNT(DISTINCT date) as total_dates
  FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
  WHERE symbol IN ('ZL=F', 'ZM=F', '^VIX', 'DX-Y.NYB')
  
  UNION ALL
  
  SELECT 
    'economic_indicators' as source,
    MIN(CAST(time AS DATE)) as earliest_date,
    MAX(CAST(time AS DATE)) as latest_date,
    COUNT(DISTINCT CAST(time AS DATE)) as total_dates
  FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
  WHERE indicator IN ('ten_year_treasury', 'unemployment_rate', 'usd_cny_rate_fred')
)
SELECT * FROM date_ranges ORDER BY source;

-- 2. MISSING DATES ANALYSIS
-- Find specific date gaps where training dataset has dates but source tables don't
WITH missing_yahoo_dates AS (
  SELECT 
    t.date,
    'yahoo_missing' as gap_type,
    COUNTIF(y.date IS NULL) as missing_count
  FROM `cbi-v14.models_v4.training_dataset_super_enriched` t
  LEFT JOIN (
    SELECT DISTINCT date 
    FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
    WHERE symbol IN ('ZL=F', 'ZM=F') AND Close IS NOT NULL
  ) y ON t.date = y.date
  WHERE y.date IS NULL
  GROUP BY t.date
  ORDER BY t.date DESC
  LIMIT 20
),

missing_economic_dates AS (
  SELECT 
    t.date,
    'economic_missing' as gap_type,
    COUNTIF(e.date IS NULL) as missing_count
  FROM `cbi-v14.models_v4.training_dataset_super_enriched` t
  LEFT JOIN (
    SELECT DISTINCT CAST(time AS DATE) as date
    FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
    WHERE indicator IN ('ten_year_treasury', 'unemployment_rate') AND value IS NOT NULL
  ) e ON t.date = e.date
  WHERE e.date IS NULL
  GROUP BY t.date
  ORDER BY t.date DESC
  LIMIT 20
)

SELECT * FROM missing_yahoo_dates
UNION ALL
SELECT * FROM missing_economic_dates
ORDER BY date DESC;

-- 3. UNEMPLOYMENT COVERAGE ANALYSIS
-- Why unemployment only got 4% coverage
WITH unemployment_analysis AS (
  SELECT 
    'unemployment_in_economic_indicators' as check_type,
    COUNT(*) as total_records,
    COUNT(DISTINCT CAST(time AS DATE)) as unique_dates,
    MIN(CAST(time AS DATE)) as earliest_date,
    MAX(CAST(time AS DATE)) as latest_date
  FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
  WHERE indicator = 'unemployment_rate' AND value IS NOT NULL
  
  UNION ALL
  
  SELECT 
    'training_dataset_total_dates' as check_type,
    COUNT(*) as total_records,
    COUNT(DISTINCT date) as unique_dates,
    MIN(date) as earliest_date,
    MAX(date) as latest_date
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  
  UNION ALL
  
  SELECT 
    'unemployment_successful_matches' as check_type,
    COUNT(*) as total_records,
    COUNT(DISTINCT date) as unique_dates,
    MIN(date) as earliest_date,
    MAX(date) as latest_date
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE unemployment_rate IS NOT NULL
)
SELECT * FROM unemployment_analysis;

-- 4. SYMBOL AVAILABILITY CHECK
-- Check which symbols are actually available in yahoo_finance_enhanced
WITH symbol_check AS (
  SELECT 
    symbol,
    COUNT(*) as total_records,
    COUNT(DISTINCT date) as unique_dates,
    MIN(date) as earliest_date,
    MAX(date) as latest_date,
    COUNTIF(Close IS NOT NULL) as valid_prices
  FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
  WHERE symbol IN ('ZL=F', 'ZC=F', 'ZW=F', 'CL=F', 'ZM=F', 'FCPO=F', '^VIX', 'DX-Y.NYB')
  GROUP BY symbol
  ORDER BY symbol
)
SELECT * FROM symbol_check;

-- 5. INDICATOR AVAILABILITY CHECK
-- Check which economic indicators are actually available
WITH indicator_check AS (
  SELECT 
    indicator,
    COUNT(*) as total_records,
    COUNT(DISTINCT CAST(time AS DATE)) as unique_dates,
    MIN(CAST(time AS DATE)) as earliest_date,
    MAX(CAST(time AS DATE)) as latest_date,
    COUNTIF(value IS NOT NULL) as valid_values
  FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
  WHERE indicator IN (
    'ten_year_treasury', 'usd_cny_rate_fred', 'usd_brl_rate_fred',
    'dollar_index_fred', 'fed_funds_rate', 'unemployment_rate'
  )
  GROUP BY indicator
  ORDER BY indicator
)
SELECT * FROM indicator_check;

-- 6. WEEKEND/HOLIDAY GAP ANALYSIS
-- Check if missing dates are weekends (markets closed)
WITH weekend_analysis AS (
  SELECT 
    'weekend_dates_in_training' as check_type,
    COUNT(*) as weekend_count
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE EXTRACT(DAYOFWEEK FROM date) IN (1, 7)  -- Sunday = 1, Saturday = 7
  
  UNION ALL
  
  SELECT 
    'weekend_dates_with_yahoo_data' as check_type,
    COUNT(DISTINCT y.date) as weekend_count
  FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced` y
  WHERE EXTRACT(DAYOFWEEK FROM y.date) IN (1, 7)
    AND symbol = 'ZL=F' AND Close IS NOT NULL
)
SELECT * FROM weekend_analysis;

-- 7. RECENT DATA AVAILABILITY
-- Check if the issue is recent dates vs older dates
WITH recency_analysis AS (
  SELECT 
    'last_30_days' as period,
    COUNT(*) as training_dates,
    COUNT(DISTINCT y.date) as yahoo_matches,
    ROUND(COUNT(DISTINCT y.date) / COUNT(*) * 100, 1) as match_rate
  FROM `cbi-v14.models_v4.training_dataset_super_enriched` t
  LEFT JOIN (
    SELECT DISTINCT date 
    FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
    WHERE symbol = 'ZL=F' AND Close IS NOT NULL
  ) y ON t.date = y.date
  WHERE t.date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
  
  UNION ALL
  
  SELECT 
    'last_90_days' as period,
    COUNT(*) as training_dates,
    COUNT(DISTINCT y.date) as yahoo_matches,
    ROUND(COUNT(DISTINCT y.date) / COUNT(*) * 100, 1) as match_rate
  FROM `cbi-v14.models_v4.training_dataset_super_enriched` t
  LEFT JOIN (
    SELECT DISTINCT date 
    FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
    WHERE symbol = 'ZL=F' AND Close IS NOT NULL
  ) y ON t.date = y.date
  WHERE t.date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
  
  UNION ALL
  
  SELECT 
    'older_than_90_days' as period,
    COUNT(*) as training_dates,
    COUNT(DISTINCT y.date) as yahoo_matches,
    ROUND(COUNT(DISTINCT y.date) / COUNT(*) * 100, 1) as match_rate
  FROM `cbi-v14.models_v4.training_dataset_super_enriched` t
  LEFT JOIN (
    SELECT DISTINCT date 
    FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
    WHERE symbol = 'ZL=F' AND Close IS NOT NULL
  ) y ON t.date = y.date
  WHERE t.date < DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
)
SELECT * FROM recency_analysis;

-- 8. FORWARD FILL OPPORTUNITY ANALYSIS
-- Check if we can forward-fill monthly/quarterly data (like unemployment)
WITH forward_fill_analysis AS (
  SELECT 
    'unemployment_monthly_gaps' as analysis_type,
    COUNT(*) as total_gaps,
    AVG(DATE_DIFF(next_date, date, DAY)) as avg_gap_days,
    MAX(DATE_DIFF(next_date, date, DAY)) as max_gap_days
  FROM (
    SELECT 
      CAST(time AS DATE) as date,
      LEAD(CAST(time AS DATE)) OVER (ORDER BY time) as next_date
    FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
    WHERE indicator = 'unemployment_rate' AND value IS NOT NULL
  )
  WHERE next_date IS NOT NULL
)
SELECT * FROM forward_fill_analysis;



