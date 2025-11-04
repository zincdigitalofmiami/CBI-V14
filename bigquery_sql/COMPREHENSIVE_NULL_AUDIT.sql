-- ============================================
-- COMPREHENSIVE NULL AUDIT & DATA QUALITY CHECK
-- Triple-check all nulls, data coverage, and schema integrity
-- ============================================

-- ============================================
-- PART 1: KEY FEATURE NULL CHECK
-- ============================================

WITH key_feature_nulls AS (
  SELECT 
    COUNT(*) as total_rows,
    
    -- Core price/volume
    COUNTIF(zl_price_current IS NULL) as zl_price_nulls,
    COUNTIF(zl_volume IS NULL) as zl_volume_nulls,
    
    -- Targets
    COUNTIF(target_1w IS NULL) as target_1w_nulls,
    COUNTIF(target_1m IS NULL) as target_1m_nulls,
    COUNTIF(target_3m IS NULL) as target_3m_nulls,
    COUNTIF(target_6m IS NULL) as target_6m_nulls,
    
    -- Commodities
    COUNTIF(corn_price IS NULL) as corn_nulls,
    COUNTIF(wheat_price IS NULL) as wheat_nulls,
    COUNTIF(crude_oil_wti_new IS NULL) as crude_nulls,
    COUNTIF(soybean_meal_price IS NULL) as meal_nulls,
    COUNTIF(palm_price IS NULL) as palm_nulls,
    
    -- Economic
    COUNTIF(treasury_10y_yield IS NULL) as treasury_nulls,
    COUNTIF(fed_funds_rate IS NULL) as fed_funds_nulls,
    COUNTIF(unemployment_rate IS NULL) as unemployment_nulls,
    COUNTIF(usd_cny_rate IS NULL) as usd_cny_nulls,
    COUNTIF(usd_brl_rate IS NULL) as usd_brl_nulls,
    COUNTIF(dollar_index IS NULL) as dollar_index_nulls,
    
    -- Market
    COUNTIF(vix_level IS NULL) as vix_nulls,
    COUNTIF(dxy_level IS NULL) as dxy_nulls,
    
    -- Technical indicators
    COUNTIF(rsi_14 IS NULL) as rsi_nulls,
    COUNTIF(macd_line IS NULL) as macd_nulls,
    COUNTIF(bb_upper IS NULL) as bb_upper_nulls
    
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
)

SELECT 
  'KEY FEATURE NULL AUDIT' as audit_section,
  total_rows,
  
  -- Coverage percentages
  ROUND((1 - zl_price_nulls / total_rows) * 100, 1) as zl_price_coverage,
  ROUND((1 - meal_nulls / total_rows) * 100, 1) as meal_coverage,
  ROUND((1 - treasury_nulls / total_rows) * 100, 1) as treasury_coverage,
  ROUND((1 - unemployment_nulls / total_rows) * 100, 1) as unemployment_coverage,
  ROUND((1 - usd_cny_nulls / total_rows) * 100, 1) as usd_cny_coverage,
  ROUND((1 - palm_nulls / total_rows) * 100, 1) as palm_coverage,
  ROUND((1 - fed_funds_nulls / total_rows) * 100, 1) as fed_funds_coverage,
  
  -- Null counts
  zl_price_nulls,
  meal_nulls,
  treasury_nulls,
  unemployment_nulls,
  usd_cny_nulls,
  palm_nulls,
  
  -- Status flags
  CASE WHEN zl_price_nulls = 0 THEN 'PASS' ELSE 'FAIL' END as zl_price_status,
  CASE WHEN meal_nulls = 0 THEN 'PASS' ELSE 'FAIL' END as meal_status,
  CASE WHEN treasury_nulls = 0 THEN 'PASS' ELSE 'FAIL' END as treasury_status,
  CASE WHEN unemployment_nulls <= total_rows * 0.05 THEN 'PASS' ELSE 'FAIL' END as unemployment_status,
  CASE WHEN usd_cny_nulls = 0 THEN 'PASS' ELSE 'FAIL' END as usd_cny_status,
  CASE WHEN palm_nulls <= total_rows * 0.01 THEN 'PASS' ELSE 'FAIL' END as palm_status
  
FROM key_feature_nulls;

-- ============================================
-- PART 2: DATE RANGE & DATA INTEGRITY
-- ============================================

SELECT 
  'DATE RANGE & INTEGRITY' as audit_section,
  COUNT(DISTINCT date) as unique_dates,
  MIN(date) as earliest_date,
  MAX(date) as latest_date,
  DATE_DIFF(MAX(date), MIN(date), DAY) as total_days_span,
  COUNT(*) as total_rows,
  COUNT(*) - COUNT(DISTINCT date) as duplicate_dates,
  CASE WHEN COUNT(*) - COUNT(DISTINCT date) = 0 THEN 'PASS' ELSE 'FAIL' END as duplicate_check
FROM `cbi-v14.models_v4.training_dataset_super_enriched`;

-- ============================================
-- PART 3: SCHEMA VERIFICATION
-- ============================================

SELECT 
  'SCHEMA CHECK' as audit_section,
  COUNT(*) as total_columns,
  COUNTIF(data_type = 'FLOAT64') as float_columns,
  COUNTIF(data_type = 'INT64') as int_columns,
  COUNTIF(data_type = 'STRING') as string_columns,
  COUNTIF(data_type = 'DATE') as date_columns,
  COUNTIF(is_nullable = 'YES') as nullable_columns,
  COUNTIF(is_nullable = 'NO') as non_nullable_columns,
  -- Check for required columns
  COUNTIF(column_name = 'date') as has_date_column,
  COUNTIF(column_name = 'zl_price_current') as has_zl_price,
  COUNTIF(column_name = 'target_1w') as has_target_1w,
  CASE 
    WHEN COUNTIF(column_name = 'date') > 0 AND COUNTIF(column_name = 'zl_price_current') > 0 
    THEN 'PASS'
    ELSE 'FAIL'
  END as required_columns_check
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'training_dataset_super_enriched';

-- ============================================
-- PART 4: DATA QUALITY CHECKS
-- ============================================

WITH quality_checks AS (
  SELECT 
    -- Invalid values check
    COUNTIF(zl_price_current IS NOT NULL AND (zl_price_current <= 0 OR zl_price_current > 1000)) as invalid_zl_prices,
    COUNTIF(zl_volume IS NOT NULL AND zl_volume < 0) as invalid_volumes,
    COUNTIF(treasury_10y_yield IS NOT NULL AND (treasury_10y_yield < 0 OR treasury_10y_yield > 20)) as invalid_treasury,
    COUNTIF(unemployment_rate IS NOT NULL AND (unemployment_rate < 0 OR unemployment_rate > 20)) as invalid_unemployment,
    COUNTIF(usd_cny_rate IS NOT NULL AND (usd_cny_rate <= 0 OR usd_cny_rate > 20)) as invalid_usd_cny,
    COUNTIF(fed_funds_rate IS NOT NULL AND (fed_funds_rate < 0 OR fed_funds_rate > 20)) as invalid_fed_funds,
    COUNTIF(target_1w IS NOT NULL AND target_1w <= 0) as invalid_target_1w,
    
    -- Check for reasonable ranges
    COUNTIF(zl_price_current IS NOT NULL AND zl_price_current BETWEEN 30 AND 80) as reasonable_zl_prices,
    COUNTIF(treasury_10y_yield IS NOT NULL AND treasury_10y_yield BETWEEN 1 AND 8) as reasonable_treasury,
    COUNTIF(unemployment_rate IS NOT NULL AND unemployment_rate BETWEEN 2 AND 10) as reasonable_unemployment
    
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
)

SELECT 
  'DATA QUALITY CHECKS' as audit_section,
  invalid_zl_prices,
  invalid_volumes,
  invalid_treasury,
  invalid_unemployment,
  invalid_usd_cny,
  invalid_fed_funds,
  invalid_target_1w,
  reasonable_zl_prices,
  reasonable_treasury,
  reasonable_unemployment,
  CASE 
    WHEN invalid_zl_prices = 0 AND invalid_volumes = 0 AND invalid_treasury = 0 AND invalid_target_1w = 0
    THEN 'PASS'
    ELSE 'FAIL'
  END as quality_status
FROM quality_checks;

-- ============================================
-- PART 5: TARGET VARIABLE VERIFICATION
-- ============================================

SELECT 
  'TARGET VARIABLE CHECK' as audit_section,
  COUNT(*) as total_rows,
  COUNTIF(target_1w IS NOT NULL) as target_1w_count,
  COUNTIF(target_1m IS NOT NULL) as target_1m_count,
  COUNTIF(target_3m IS NOT NULL) as target_3m_count,
  COUNTIF(target_6m IS NOT NULL) as target_6m_count,
  
  ROUND(COUNTIF(target_1w IS NOT NULL) / COUNT(*) * 100, 1) as target_1w_coverage_pct,
  ROUND(COUNTIF(target_1m IS NOT NULL) / COUNT(*) * 100, 1) as target_1m_coverage_pct,
  ROUND(COUNTIF(target_3m IS NOT NULL) / COUNT(*) * 100, 1) as target_3m_coverage_pct,
  ROUND(COUNTIF(target_6m IS NOT NULL) / COUNT(*) * 100, 1) as target_6m_coverage_pct,
  
  -- Check for logical consistency
  COUNTIF(target_1w IS NOT NULL AND target_1w <= 0) as invalid_target_1w,
  COUNTIF(target_1m IS NOT NULL AND target_1m <= 0) as invalid_target_1m,
  
  CASE 
    WHEN COUNTIF(target_1w IS NOT NULL) / COUNT(*) >= 0.70 THEN 'SUFFICIENT'
    ELSE 'INSUFFICIENT'
  END as target_1w_status
  
FROM `cbi-v14.models_v4.training_dataset_super_enriched`;

-- ============================================
-- PART 6: SOURCE TABLE VERIFICATION
-- ============================================

SELECT 
  'SOURCE TABLE: yahoo_finance_enhanced' as source_check,
  COUNT(*) as total_records,
  COUNT(DISTINCT date) as unique_dates,
  COUNT(DISTINCT symbol) as unique_symbols,
  MIN(date) as earliest,
  MAX(date) as latest,
  COUNTIF(symbol = 'ZL=F' AND Close IS NOT NULL) as zl_records,
  COUNTIF(symbol = '^TNX' AND Close IS NOT NULL) as treasury_records
FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`;

SELECT 
  'SOURCE TABLE: economic_indicators' as source_check,
  COUNT(*) as total_records,
  COUNT(DISTINCT CAST(time AS DATE)) as unique_dates,
  COUNT(DISTINCT indicator) as unique_indicators,
  MIN(CAST(time AS DATE)) as earliest,
  MAX(CAST(time AS DATE)) as latest,
  COUNTIF(indicator = 'ten_year_treasury' AND value IS NOT NULL) as treasury_records,
  COUNTIF(indicator = 'unemployment_rate' AND value IS NOT NULL) as unemployment_records
FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`;

SELECT 
  'SOURCE TABLE: currency_data' as source_check,
  COUNT(*) as total_records,
  COUNT(DISTINCT date) as unique_dates,
  MIN(date) as earliest,
  MAX(date) as latest,
  COUNTIF(from_currency = 'USD' AND to_currency = 'CNY' AND rate IS NOT NULL) as usd_cny_records
FROM `cbi-v14.forecasting_data_warehouse.currency_data`;

-- ============================================
-- PART 7: FINAL TRAINING READINESS ASSESSMENT
-- ============================================

WITH readiness_check AS (
  SELECT 
    (SELECT COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched`) as total_rows,
    (SELECT COUNTIF(zl_price_current IS NOT NULL) / COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched`) as zl_coverage,
    (SELECT COUNTIF(soybean_meal_price IS NOT NULL) / COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched`) as meal_coverage,
    (SELECT COUNTIF(treasury_10y_yield IS NOT NULL) / COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched`) as treasury_coverage,
    (SELECT COUNTIF(unemployment_rate IS NOT NULL) / COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched`) as unemployment_coverage,
    (SELECT COUNTIF(usd_cny_rate IS NOT NULL) / COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched`) as usd_cny_coverage,
    (SELECT COUNTIF(palm_price IS NOT NULL) / COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched`) as palm_coverage,
    (SELECT COUNTIF(fed_funds_rate IS NOT NULL) / COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched`) as fed_funds_coverage,
    (SELECT COUNTIF(target_1w IS NOT NULL) / COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched`) as target_1w_coverage,
    (SELECT COUNT(*) - COUNT(DISTINCT date) FROM `cbi-v14.models_v4.training_dataset_super_enriched`) as duplicate_count
)

SELECT 
  'FINAL TRAINING READINESS ASSESSMENT' as audit_section,
  total_rows,
  ROUND(zl_coverage * 100, 1) as zl_price_pct,
  ROUND(meal_coverage * 100, 1) as meal_pct,
  ROUND(treasury_coverage * 100, 1) as treasury_pct,
  ROUND(unemployment_coverage * 100, 1) as unemployment_pct,
  ROUND(usd_cny_coverage * 100, 1) as usd_cny_pct,
  ROUND(palm_coverage * 100, 1) as palm_pct,
  ROUND(fed_funds_coverage * 100, 1) as fed_funds_pct,
  ROUND(target_1w_coverage * 100, 1) as target_1w_pct,
  duplicate_count,
  
  -- Overall assessment
  CASE 
    WHEN zl_coverage >= 0.95 AND meal_coverage >= 0.95 AND treasury_coverage >= 0.95 
         AND unemployment_coverage >= 0.90 AND usd_cny_coverage >= 0.95
         AND duplicate_count = 0
    THEN 'READY FOR TRAINING'
    WHEN zl_coverage >= 0.90 AND meal_coverage >= 0.90 AND treasury_coverage >= 0.90
    THEN 'GOOD - MINOR ISSUES'
    ELSE 'REVIEW REQUIRED'
  END as overall_status,
  
  -- Count passing features (>=95%)
  (CASE WHEN zl_coverage >= 0.95 THEN 1 ELSE 0 END +
   CASE WHEN meal_coverage >= 0.95 THEN 1 ELSE 0 END +
   CASE WHEN treasury_coverage >= 0.95 THEN 1 ELSE 0 END +
   CASE WHEN unemployment_coverage >= 0.90 THEN 1 ELSE 0 END +
   CASE WHEN usd_cny_coverage >= 0.95 THEN 1 ELSE 0 END +
   CASE WHEN palm_coverage >= 0.95 THEN 1 ELSE 0 END +
   CASE WHEN fed_funds_coverage >= 0.90 THEN 1 ELSE 0 END) as features_passing
  
FROM readiness_check;
