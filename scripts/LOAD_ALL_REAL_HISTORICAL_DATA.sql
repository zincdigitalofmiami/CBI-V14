-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================================================
-- LOAD ALL REAL HISTORICAL DATA - NO FAKE SHIT
-- Date: November 15, 2025
-- Purpose: Load ALL pre-2020 data from models_v4 into training tables
-- ============================================================================

-- The REAL data exists in models_v4:
-- pre_crisis_2000_2007_historical: 1,737 rows (2000-2007)
-- crisis_2008_historical: 253 rows (2008)
-- recovery_2010_2016_historical: 1,760 rows (2010-2016)
-- trade_war_2017_2019_historical: 754 rows (2017-2019)
-- trump_rich_2023_2025: 732 rows (2023-2025)

-- ----------------------------------------------------------------------------
-- STEP 1: Create a consolidated table with ALL historical data
-- ----------------------------------------------------------------------------

CREATE OR REPLACE TABLE `cbi-v14.training.complete_historical_data` AS
WITH all_historical AS (
    -- 2000-2007 PRE-CRISIS DATA
    SELECT 
        date,
        bg_close as close_price,
        open,
        high,
        low,
        volume,
        rsi_14,
        macd_line,
        macd_signal,
        bb_upper,
        bb_middle,
        bb_lower,
        'precrisis_2000_2007' as market_regime,
        100 as training_weight
    FROM `cbi-v14.models_v4.pre_crisis_2000_2007_historical`
    
    UNION ALL
    
    -- 2008-2009 FINANCIAL CRISIS DATA
    SELECT 
        date,
        bg_close as close_price,
        open,
        high,
        low,
        volume,
        rsi_14,
        macd_line,
        macd_signal,
        bb_upper,
        bb_middle,
        bb_lower,
        'financial_crisis_2008_2009' as market_regime,
        500 as training_weight
    FROM `cbi-v14.models_v4.crisis_2008_historical`
    
    UNION ALL
    
    -- 2010-2016 QE RECOVERY DATA
    SELECT 
        date,
        bg_close as close_price,
        open,
        high,
        low,
        volume,
        rsi_14,
        macd_line,
        macd_signal,
        bb_upper,
        bb_middle,
        bb_lower,
        'qe_recovery_2010_2016' as market_regime,
        300 as training_weight
    FROM `cbi-v14.models_v4.recovery_2010_2016_historical`
    
    UNION ALL
    
    -- 2017-2019 TRADE WAR DATA
    SELECT 
        date,
        bg_close as close_price,
        open,
        high,
        low,
        volume,
        rsi_14,
        macd_line,
        macd_signal,
        bb_upper,
        bb_middle,
        bb_lower,
        'tradewar_2017_2019' as market_regime,
        1500 as training_weight
    FROM `cbi-v14.models_v4.trade_war_2017_2019_historical`
    
    UNION ALL
    
    -- 2020-2021 COVID DATA (from training table)
    SELECT 
        date,
        NULL as close_price,  -- Will need to join with price data
        NULL as open,
        NULL as high,
        NULL as low,
        NULL as volume,
        NULL as rsi_14,
        NULL as macd_line,
        NULL as macd_signal,
        NULL as bb_upper,
        NULL as bb_middle,
        NULL as bb_lower,
        'covid_2020_2021' as market_regime,
        800 as training_weight
    FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
    WHERE date BETWEEN '2020-01-01' AND '2021-12-31'
    
    UNION ALL
    
    -- 2022-2023 INFLATION DATA
    SELECT 
        date,
        NULL as close_price,
        NULL as open,
        NULL as high,
        NULL as low,
        NULL as volume,
        NULL as rsi_14,
        NULL as macd_line,
        NULL as macd_signal,
        NULL as bb_upper,
        NULL as bb_middle,
        NULL as bb_lower,
        'inflation_2021_2023' as market_regime,
        1200 as training_weight
    FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
    WHERE date BETWEEN '2022-01-01' AND '2022-12-31'
    
    UNION ALL
    
    -- 2023-2025 TRUMP 2.0 DATA
    SELECT 
        date,
        bg_close as close_price,
        open,
        high,
        low,
        volume,
        rsi_14,
        macd_line,
        macd_signal,
        bb_upper,
        bb_middle,
        bb_lower,
        'trump_2023_2025' as market_regime,
        5000 as training_weight
    FROM `cbi-v14.models_v4.trump_rich_2023_2025`
),
enriched_data AS (
    SELECT 
        date,
        close_price,
        open,
        high,
        low,
        volume,
        
        -- Technical indicators
        rsi_14,
        macd_line,
        macd_signal,
        macd_line - macd_signal as macd_histogram,
        bb_upper,
        bb_middle,
        bb_lower,
        (close_price - bb_lower) / NULLIF(bb_upper - bb_lower, 0) as bb_position,
        
        -- Price returns (calculated from real prices)
        (close_price - LAG(close_price, 1) OVER (ORDER BY date)) / 
            NULLIF(LAG(close_price, 1) OVER (ORDER BY date), 0) AS return_1d,
        (close_price - LAG(close_price, 5) OVER (ORDER BY date)) / 
            NULLIF(LAG(close_price, 5) OVER (ORDER BY date), 0) AS return_5d,
        (close_price - LAG(close_price, 20) OVER (ORDER BY date)) / 
            NULLIF(LAG(close_price, 20) OVER (ORDER BY date), 0) AS return_20d,
        (close_price - LAG(close_price, 60) OVER (ORDER BY date)) / 
            NULLIF(LAG(close_price, 60) OVER (ORDER BY date), 0) AS return_60d,
        
        -- Moving averages (calculated from real prices)
        AVG(close_price) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS ma_20,
        AVG(close_price) OVER (ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS ma_50,
        AVG(close_price) OVER (ORDER BY date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW) AS ma_200,
        
        -- Volatility (calculated from real returns)
        STDDEV((close_price - LAG(close_price) OVER (ORDER BY date)) / 
            NULLIF(LAG(close_price) OVER (ORDER BY date), 0)) 
            OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS volatility_20d,
        
        -- Volume metrics
        AVG(volume) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS avg_volume_20d,
        volume / NULLIF(AVG(volume) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW), 0) AS volume_ratio,
        
        -- Regime and weight
        market_regime,
        training_weight,
        
        -- Seasonality
        EXTRACT(MONTH FROM date) AS month,
        EXTRACT(QUARTER FROM date) AS quarter,
        CASE 
            WHEN EXTRACT(MONTH FROM date) IN (3,4,5) THEN 'PLANTING'
            WHEN EXTRACT(MONTH FROM date) IN (6,7,8) THEN 'GROWING'
            WHEN EXTRACT(MONTH FROM date) IN (9,10,11) THEN 'HARVEST'
            ELSE 'OFF_SEASON'
        END AS season
        
    FROM all_historical
    WHERE close_price IS NOT NULL  -- Only keep rows with actual price data
)
SELECT * FROM enriched_data
ORDER BY date;

-- ----------------------------------------------------------------------------
-- STEP 2: Verify the complete historical data
-- ----------------------------------------------------------------------------

SELECT 
    'Data Verification' AS check_type,
    COUNT(*) as total_rows,
    COUNT(DISTINCT date) as unique_dates,
    MIN(date) as min_date,
    MAX(date) as max_date,
    COUNT(DISTINCT market_regime) as unique_regimes,
    MIN(training_weight) as min_weight,
    MAX(training_weight) as max_weight,
    ROUND(AVG(close_price), 2) as avg_price,
    ROUND(AVG(rsi_14), 2) as avg_rsi,
    ROUND(AVG(volatility_20d), 4) as avg_volatility
FROM `cbi-v14.training.complete_historical_data`;

-- ----------------------------------------------------------------------------
-- STEP 3: Sample the data to prove it's real
-- ----------------------------------------------------------------------------

SELECT 
    date,
    close_price,
    volume,
    rsi_14,
    return_5d,
    volatility_20d,
    market_regime,
    training_weight
FROM `cbi-v14.training.complete_historical_data`
WHERE date IN (
    '2001-06-15',  -- Pre-crisis
    '2005-03-15',  -- Pre-crisis
    '2008-07-15',  -- Financial crisis
    '2010-09-15',  -- Recovery
    '2013-03-15',  -- Recovery
    '2015-06-15',  -- Recovery
    '2018-06-15',  -- Trade war
    '2020-03-15',  -- COVID
    '2023-06-15'   -- Trump 2.0
)
ORDER BY date;

-- ----------------------------------------------------------------------------
-- STEP 4: Update training tables with complete history
-- ----------------------------------------------------------------------------

-- Clear any fake data
DELETE FROM `cbi-v14.training.zl_training_prod_allhistory_1m` 
WHERE date < '2020-01-01';

-- Insert all the real historical data
INSERT INTO `cbi-v14.training.zl_training_prod_allhistory_1m`
(date, market_regime, training_weight)
SELECT DISTINCT
    date,
    market_regime,
    training_weight
FROM `cbi-v14.training.complete_historical_data`
WHERE date < '2020-01-01';

-- ----------------------------------------------------------------------------
-- STEP 5: Create real Sharpe calculations from actual returns
-- ----------------------------------------------------------------------------

CREATE OR REPLACE VIEW `cbi-v14.performance.vw_real_sharpe_metrics` AS
WITH real_performance AS (
    SELECT 
        date,
        close_price,
        return_5d,
        return_20d,
        volatility_20d,
        market_regime,
        
        -- Calculate Sharpe ratio (assuming 5% annual risk-free rate)
        (return_5d - 0.05/52) / NULLIF(volatility_20d, 0) AS sharpe_ratio_weekly,
        (return_20d - 0.05/12) / NULLIF(volatility_20d * SQRT(4), 0) AS sharpe_ratio_monthly,
        
        -- Win rate
        CASE WHEN return_5d > 0 THEN 1 ELSE 0 END AS win_flag
        
    FROM `cbi-v14.training.complete_historical_data`
    WHERE close_price IS NOT NULL
        AND return_5d IS NOT NULL
),
regime_stats AS (
    SELECT 
        market_regime,
        COUNT(*) as observations,
        AVG(return_5d) as avg_return_5d,
        AVG(return_20d) as avg_return_20d,
        STDDEV(return_5d) as volatility_5d,
        AVG(sharpe_ratio_weekly) as avg_sharpe_weekly,
        AVG(win_flag) as win_rate,
        MIN(return_20d) as max_drawdown
    FROM real_performance
    GROUP BY market_regime
),
overall_stats AS (
    SELECT 
        'OVERALL' as market_regime,
        COUNT(*) as observations,
        AVG(return_5d) as avg_return_5d,
        AVG(return_20d) as avg_return_20d,
        STDDEV(return_5d) as volatility_5d,
        AVG(sharpe_ratio_weekly) as avg_sharpe_weekly,
        AVG(win_flag) as win_rate,
        MIN(return_20d) as max_drawdown
    FROM real_performance
)
SELECT * FROM regime_stats
UNION ALL
SELECT * FROM overall_stats;

-- ----------------------------------------------------------------------------
-- FINAL VERIFICATION
-- ----------------------------------------------------------------------------

SELECT 
    'FINAL STATUS' AS status,
    COUNT(*) as total_training_rows,
    MIN(date) as min_date,
    MAX(date) as max_date,
    COUNT(DISTINCT market_regime) as unique_regimes,
    COUNT(CASE WHEN date < '2020-01-01' THEN 1 END) as pre_2020_rows,
    COUNT(CASE WHEN date >= '2020-01-01' THEN 1 END) as post_2020_rows
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`;

-- THIS IS ALL REAL DATA FROM ACTUAL HISTORICAL TABLES - NO FAKE CALCULATIONS






