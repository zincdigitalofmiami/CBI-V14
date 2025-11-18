-- ============================================================================
-- VERIFICATION SQL QUERIES
-- Date: November 15, 2025
-- Purpose: Reusable queries for data verification audits
-- ============================================================================

-- ============================================================================
-- PHASE 1: ROW COUNT VERIFICATION
-- ============================================================================

-- 1.1 Get all table row counts by dataset
SELECT 
    table_schema as dataset,
    table_id as table_name,
    row_count,
    size_bytes,
    CASE 
        WHEN row_count >= 1000000 THEN '1M+'
        WHEN row_count >= 100000 THEN '100K+'
        WHEN row_count >= 10000 THEN '10K+'
        ELSE 'Under 10K'
    END as size_category
FROM `cbi-v14.{dataset}.__TABLES__`
ORDER BY row_count DESC;

-- 1.2 Dataset summary
SELECT 
    table_schema as dataset,
    COUNT(*) as table_count,
    SUM(row_count) as total_rows,
    SUM(size_bytes) as total_bytes,
    COUNTIF(row_count >= 1000000) as tables_1m_plus
FROM `cbi-v14.{dataset}.__TABLES__`
GROUP BY table_schema
ORDER BY total_rows DESC;

-- 1.3 Training tables verification
SELECT 
    'zl_training_prod_allhistory_1m' as table_name,
    COUNT(*) as total_rows,
    COUNT(DISTINCT date) as unique_dates,
    MIN(date) as min_date,
    MAX(date) as max_date,
    COUNT(DISTINCT market_regime) as unique_regimes,
    MIN(training_weight) as min_weight,
    MAX(training_weight) as max_weight,
    COUNTIF(market_regime = 'allhistory') as allhistory_count,
    COUNTIF(training_weight = 1) as weight_1_count,
    COUNTIF(date < '2020-01-01') as pre_2020_rows,
    COUNTIF(date >= '2020-01-01') as post_2020_rows
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`;

-- Repeat for all 10 training tables (1w, 1m, 3m, 6m, 12m × prod/full)

-- 1.4 Historical data verification
SELECT 
    'pre_crisis_2000_2007_historical' as table_name,
    COUNT(*) as total_rows,
    MIN(date) as min_date,
    MAX(date) as max_date,
    COUNT(DISTINCT date) as unique_dates,
    COUNTIF(close IS NOT NULL) as has_price_count,
    ROUND(AVG(close), 2) as avg_price,
    ROUND(MIN(close), 2) as min_price,
    ROUND(MAX(close), 2) as max_price,
    COUNTIF(close = 0.5) as placeholder_05_count,
    ROUND(COUNTIF(close = 0.5) / COUNT(*) * 100, 2) as placeholder_05_pct
FROM `cbi-v14.models_v4.pre_crisis_2000_2007_historical`;

-- Repeat for: crisis_2008_historical, recovery_2010_2016_historical, 
-- trade_war_2017_2019_historical, trump_rich_2023_2025

-- ============================================================================
-- PHASE 2: DATA SOURCE VERIFICATION
-- ============================================================================

-- 2.1 Yahoo Finance data verification
SELECT 
    COUNT(*) as total_rows,
    COUNT(DISTINCT Symbol) as unique_symbols,
    MIN(Date) as min_date,
    MAX(Date) as max_date,
    COUNTIF(Symbol = 'ZL=F') as zl_rows,
    COUNTIF(close = 0.5) as placeholder_05_count,
    COUNTIF(close IS NULL) as null_count,
    ROUND(AVG(close), 2) as avg_close,
    ROUND(MIN(close), 2) as min_close,
    ROUND(MAX(close), 2) as max_close
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`;

-- 2.2 Sample ZL=F data
SELECT 
    Date,
    Symbol,
    close,
    volume,
    rsi_14,
    macd_line
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE Symbol = 'ZL=F'
ORDER BY Date DESC
LIMIT 10;

-- 2.3 Regime data verification
SELECT 
    COUNT(*) as total_rows,
    MIN(date) as min_date,
    MAX(date) as max_date,
    COUNT(DISTINCT regime) as unique_regimes
FROM `cbi-v14.training.regime_calendar`;

SELECT 
    COUNT(*) as total_rows,
    MIN(weight) as min_weight,
    MAX(weight) as max_weight,
    STRING_AGG(DISTINCT regime, ', ' ORDER BY regime) as all_regimes
FROM `cbi-v14.training.regime_weights`;

-- ============================================================================
-- PHASE 3: PLACEHOLDER DETECTION
-- ============================================================================

-- 3.1 Check for 0.5 placeholder in Yahoo data
SELECT 
    COUNTIF(close = 0.5) as close_05_count,
    COUNTIF(open = 0.5) as open_05_count,
    COUNTIF(high = 0.5) as high_05_count,
    COUNTIF(low = 0.5) as low_05_count,
    COUNT(*) as total_rows,
    ROUND(COUNTIF(close = 0.5) / COUNT(*) * 100, 2) as close_05_pct
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE Symbol = 'ZL=F';

-- 3.2 Check for 0.5 placeholder in all_commodity_prices
SELECT 
    COUNTIF(close = 0.5) as close_05_count,
    COUNT(*) as total_rows
FROM `cbi-v14.forecasting_data_warehouse.all_commodity_prices`
WHERE symbol = 'ZL=F';

-- 3.3 Check for other placeholder patterns in training table
SELECT 
    COUNTIF(training_weight = 1) as weight_1_count,
    COUNTIF(training_weight = 0.5) as weight_05_count,
    COUNTIF(market_regime = 'allhistory') as allhistory_count,
    COUNTIF(market_regime IS NULL) as null_regime_count,
    COUNT(*) as total_rows
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`;

-- ============================================================================
-- PHASE 4: JOIN VERIFICATION
-- ============================================================================

-- 4.1 Verify join tables exist
SELECT COUNT(*) as row_count FROM `cbi-v14.neural.vw_big_eight_signals`;
SELECT COUNT(*) as row_count FROM `cbi-v14.raw_intelligence.commodity_soybean_oil_prices`;
SELECT COUNT(*) as row_count FROM `cbi-v14.raw_intelligence.commodity_palm_oil_prices`;
SELECT COUNT(*) as row_count FROM `cbi-v14.forecasting_data_warehouse.vix_data`;
SELECT COUNT(*) as row_count FROM `cbi-v14.training.regime_calendar`;
SELECT COUNT(*) as row_count FROM `cbi-v14.training.regime_weights`;

-- 4.2 Verify API views exist
SELECT COUNT(*) as row_count FROM `cbi-v14.api.vw_ultimate_adaptive_signal` LIMIT 1;
SELECT COUNT(*) as row_count FROM `cbi-v14.performance.vw_forecast_performance_tracking` LIMIT 1;
SELECT COUNT(*) as row_count FROM `cbi-v14.performance.vw_soybean_sharpe_metrics` LIMIT 1;

-- 4.3 Check view definitions for placeholders
SELECT view_definition
FROM `cbi-v14.performance`.INFORMATION_SCHEMA.VIEWS
WHERE table_name = 'vw_soybean_sharpe_metrics';

SELECT view_definition
FROM `cbi-v14.performance`.INFORMATION_SCHEMA.VIEWS
WHERE table_name = 'vw_forecast_performance_tracking';

-- ============================================================================
-- PHASE 5: DATA COMPLETENESS
-- ============================================================================

-- 5.1 Date coverage check
SELECT 
    'training_prod_1m' as table_name,
    MIN(date) as min_date,
    MAX(date) as max_date,
    COUNT(DISTINCT date) as unique_dates,
    COUNT(*) as total_rows,
    CASE 
        WHEN MIN(date) <= '2000-01-01' THEN '✓ Has pre-2020 data'
        ELSE '✗ Missing pre-2020 data'
    END as coverage_status
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`;

-- 5.2 NULL percentage check
SELECT 
    COUNTIF(date IS NULL) as null_dates,
    COUNTIF(market_regime IS NULL) as null_regimes,
    COUNTIF(training_weight IS NULL) as null_weights,
    COUNT(*) as total_rows
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`;

-- 5.3 Regime distribution
SELECT 
    market_regime,
    COUNT(*) as row_count,
    MIN(date) as start_date,
    MAX(date) as end_date,
    MIN(training_weight) as weight
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
GROUP BY market_regime
ORDER BY MIN(date);

-- ============================================================================
-- QUICK VERIFICATION CHECKS
-- ============================================================================

-- Total rows across all datasets
SELECT 
    SUM(row_count) as total_rows_all_datasets
FROM `cbi-v14.{dataset}.__TABLES__`;

-- Tables with 1M+ rows
SELECT 
    table_schema,
    table_id,
    row_count
FROM `cbi-v14.{dataset}.__TABLES__`
WHERE row_count >= 1000000
ORDER BY row_count DESC;

-- Training table summary
SELECT 
    table_id,
    row_count,
    size_bytes
FROM `cbi-v14.training.__TABLES__`
WHERE table_id LIKE 'zl_training_%'
ORDER BY table_id;


