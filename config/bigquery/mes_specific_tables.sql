-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================================================
-- MES-Specific Tables for Private Dashboard Page
-- ============================================================================
-- Date: November 19, 2025
-- Project: CBI-V14 - MES Private Integration (Same Project, Private Page)
--
-- This script creates MES-specific tables that complement the existing
-- ZL infrastructure. MES data shares the same project but has restricted access.
-- ============================================================================

-- Set project
SET @@project_id = 'cbi-v14';

-- ============================================================================
-- MES FEATURE TABLES (in existing features dataset)
-- ============================================================================

-- MES Volume Profile Features
CREATE TABLE IF NOT EXISTS `cbi-v14.features.mes_volume_profile` (
    date DATE NOT NULL,
    session_type STRING,  -- 'RTH', 'ETH', 'GLOBEX'
    
    -- Core Volume Profile Levels
    poc_price FLOAT64,     -- Point of Control (highest volume price)
    vah_price FLOAT64,     -- Value Area High
    val_price FLOAT64,     -- Value Area Low
    
    -- High/Low Volume Nodes
    hvn_prices ARRAY<FLOAT64>,  -- High Volume Node prices
    lvn_prices ARRAY<FLOAT64>,  -- Low Volume Node prices
    
    -- Developing POC
    developing_poc FLOAT64,
    poc_migration_direction STRING,  -- 'UP', 'DOWN', 'STABLE'
    
    -- Distance Metrics
    distance_to_poc FLOAT64,
    distance_to_vah FLOAT64,
    distance_to_val FLOAT64,
    
    -- Profile Characteristics
    value_area_width FLOAT64,
    profile_type STRING,  -- 'P-SHAPE', 'B-SHAPE', 'D-SHAPE', 'NORMAL'
    delta_at_poc FLOAT64,
    volume_at_poc FLOAT64,
    
    -- Multi-timeframe Analysis
    window_10d STRUCT<poc FLOAT64, vah FLOAT64, val FLOAT64>,
    window_20d STRUCT<poc FLOAT64, vah FLOAT64, val FLOAT64>,
    window_63d STRUCT<poc FLOAT64, vah FLOAT64, val FLOAT64>,
    
    -- Cross-Market Confluence
    confluence_with_es INT64,   -- ES futures confluence count
    confluence_with_spy INT64,  -- SPY ETF confluence count
    
    -- Trading Signals
    poc_naked BOOL,  -- POC not revisited
    price_rejected_from_val BOOL,
    price_stuck_in_lvn BOOL,
    volume_profile_confluence_3_or_higher BOOL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY session_type
OPTIONS(
    description='MES Volume Profile features for private dashboard - pure math, no visuals'
);

-- MES Pivot Points
CREATE TABLE IF NOT EXISTS `cbi-v14.features.mes_pivots` (
    date DATE NOT NULL,
    pivot_type STRING NOT NULL,  -- 'DAILY', 'WEEKLY', 'MONTHLY'
    
    -- Classic Pivots
    pivot_point FLOAT64,
    resistance_1 FLOAT64,
    resistance_2 FLOAT64,
    resistance_3 FLOAT64,
    support_1 FLOAT64,
    support_2 FLOAT64,
    support_3 FLOAT64,
    
    -- Fibonacci Pivots
    fib_r1 FLOAT64,
    fib_r2 FLOAT64,
    fib_r3 FLOAT64,
    fib_s1 FLOAT64,
    fib_s2 FLOAT64,
    fib_s3 FLOAT64,
    
    -- Mid-Pivots
    mid_m1 FLOAT64,  -- Between Pivot and S1
    mid_m2 FLOAT64,  -- Between S1 and S2
    mid_m3 FLOAT64,  -- Between Pivot and R1
    mid_m4 FLOAT64,  -- Between R1 and R2
    
    -- Distance Metrics
    distance_to_pivot FLOAT64,
    closest_level_type STRING,  -- 'R1', 'S1', 'PIVOT', etc.
    closest_level_distance FLOAT64,
    
    -- Confluence Detection
    confluence_zone_price FLOAT64,
    confluence_strength INT64,  -- Number of overlapping levels
    
    -- Trading Signals
    pivot_rejection BOOL,       -- Price rejected from pivot
    pivot_breakthrough BOOL,    -- Clean break through pivot
    price_between_r1_s1 BOOL,   -- Consolidation zone
    weekly_pivot_flip BOOL,     -- Weekly pivot changed from support to resistance
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY pivot_type
OPTIONS(
    description='MES Pivot Point features for private dashboard - classic, Fibonacci, and mid-pivots'
);

-- MES Fibonacci Retracements and Extensions
CREATE TABLE IF NOT EXISTS `cbi-v14.features.mes_fibonacci` (
    date DATE NOT NULL,
    swing_window STRING,  -- '5D', '10D', '20D', '63D'
    
    -- Swing Points
    swing_high FLOAT64,
    swing_high_date DATE,
    swing_low FLOAT64,
    swing_low_date DATE,
    swing_range FLOAT64,
    
    -- Retracement Levels
    fib_0 FLOAT64,     -- Swing low (0%)
    fib_236 FLOAT64,   -- 23.6% retracement
    fib_382 FLOAT64,   -- 38.2% retracement
    fib_500 FLOAT64,   -- 50% retracement
    fib_618 FLOAT64,   -- 61.8% retracement (golden ratio)
    fib_786 FLOAT64,   -- 78.6% retracement
    fib_100 FLOAT64,   -- Swing high (100%)
    
    -- Extension Levels
    ext_1272 FLOAT64,  -- 127.2% extension
    ext_1618 FLOAT64,  -- 161.8% extension (golden extension)
    ext_2000 FLOAT64,  -- 200% extension
    ext_2618 FLOAT64,  -- 261.8% extension
    
    -- Current Position
    current_fib_level FLOAT64,  -- Current price as % of swing
    distance_to_618 FLOAT64,
    distance_to_1618 FLOAT64,
    
    -- Trading Signals
    near_618_retrace BOOL,       -- Within 0.25% of 61.8%
    near_1618_extension BOOL,    -- Within 0.25% of 161.8%
    bounced_from_fib BOOL,       -- Price bounced from major fib
    fib_cluster_detected BOOL,   -- Multiple fib levels converge
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY swing_window
OPTIONS(
    description='MES Fibonacci retracement and extension features - auto-detected swings'
);

-- MES GARCH/EGARCH Volatility Features
CREATE TABLE IF NOT EXISTS `cbi-v14.features.mes_garch_vol` (
    date DATE NOT NULL,
    
    -- Standard GARCH(1,1) Parameters
    omega FLOAT64,      -- Volatility constant
    alpha FLOAT64,      -- ARCH term (shock magnitude)
    beta FLOAT64,       -- GARCH term (persistence)
    
    -- EGARCH Extensions (asymmetric)
    gamma FLOAT64,      -- Leverage effect (negative shocks)
    
    -- Student-t Distribution Parameters
    nu FLOAT64,         -- Degrees of freedom (fat tails)
    lambda FLOAT64,     -- Skewness parameter
    
    -- External Regressors
    delta_vix FLOAT64,  -- VIX coefficient in variance equation
    delta_vvix FLOAT64, -- VVIX (vol of vol) coefficient
    
    -- Volatility Forecasts
    vol_forecast_1d FLOAT64,
    vol_forecast_5d FLOAT64,
    vol_forecast_21d FLOAT64,
    
    -- Volatility Metrics
    vix_level FLOAT64,
    vvix_level FLOAT64,
    realized_vol_5d FLOAT64,
    realized_vol_21d FLOAT64,
    vol_of_vol_estimate FLOAT64,
    
    -- Value at Risk
    var_95_1d FLOAT64,  -- 1-day 95% VaR
    var_99_1d FLOAT64,  -- 1-day 99% VaR
    cvar_95_1d FLOAT64, -- Conditional VaR (Expected Shortfall)
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
OPTIONS(
    description='MES GARCH/EGARCH volatility forecasts - standard model before Markov switching'
);

-- MES Markov-Switching EGARCH Features (Enhanced)
CREATE TABLE IF NOT EXISTS `cbi-v14.features.mes_ms_egarch_vol` (
    date DATE NOT NULL,
    
    -- Current Regime Probabilities
    prob_bull_calm FLOAT64,      -- Regime 1: Low vol, positive drift
    prob_bear_grinding FLOAT64,  -- Regime 2: High vol, negative drift
    prob_crash_panic FLOAT64,    -- Regime 3: Extreme vol, leverage effect
    
    -- Regime Assignment
    current_regime STRING,  -- 'BULL', 'BEAR', 'CRASH'
    regime_duration_days INT64,
    
    -- Forecasted Regime Probabilities (next 10 days)
    forecast_prob_bull_calm ARRAY<FLOAT64>,
    forecast_prob_bear_grinding ARRAY<FLOAT64>,
    forecast_prob_crash_panic ARRAY<FLOAT64>,
    
    -- Conditional Volatility Forecasts by Horizon
    forecast_vol_1d FLOAT64,
    forecast_vol_5d FLOAT64,
    forecast_vol_10d FLOAT64,
    
    -- Transition Matrix (3x3)
    transition_matrix ARRAY<ARRAY<FLOAT64>>,
    
    -- Regime-Specific Parameters (Bull Calm)
    bull_calm_omega FLOAT64,
    bull_calm_alpha FLOAT64,
    bull_calm_gamma FLOAT64,
    bull_calm_beta FLOAT64,
    bull_calm_lambda FLOAT64,
    bull_calm_nu FLOAT64,
    bull_calm_drift FLOAT64,
    
    -- Regime-Specific Parameters (Bear Grinding)
    bear_grinding_omega FLOAT64,
    bear_grinding_alpha FLOAT64,
    bear_grinding_gamma FLOAT64,
    bear_grinding_beta FLOAT64,
    bear_grinding_lambda FLOAT64,
    bear_grinding_nu FLOAT64,
    bear_grinding_drift FLOAT64,
    
    -- Regime-Specific Parameters (Crash Panic)
    crash_panic_omega FLOAT64,
    crash_panic_alpha FLOAT64,
    crash_panic_gamma FLOAT64,
    crash_panic_beta FLOAT64,
    crash_panic_lambda FLOAT64,
    crash_panic_nu FLOAT64,
    crash_panic_drift FLOAT64,
    
    -- Exogenous Regressor Coefficients
    delta_vix_current FLOAT64,
    delta_fed_current FLOAT64,
    delta_dxy_current FLOAT64,
    delta_yield_current FLOAT64,
    delta_fomc_current FLOAT64,
    delta_trump_current FLOAT64,
    
    -- Risk Metrics
    prob_crash_next_5d FLOAT64,
    crash_alert BOOL,  -- True if P(Crash|next5d) > 0.15
    var_99_hit_rate FLOAT64,
    backtest_rmse FLOAT64,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
OPTIONS(
    description='MES Markov-switching EGARCH with exogenous regressors - 3-regime model'
);

-- ============================================================================
-- MES PREDICTIONS TABLE (View-Only for Dashboard)
-- ============================================================================

CREATE TABLE IF NOT EXISTS `cbi-v14.predictions.mes_predictions_view_only` (
    prediction_date DATE NOT NULL,
    horizon STRING NOT NULL,  -- '1min', '5min', '15min', '1h', '1d', '7d', '30d', '3m', '6m'
    
    -- Quantile Forecasts
    q05 FLOAT64,  -- 5th percentile
    q10 FLOAT64,  -- 10th percentile
    q25 FLOAT64,  -- 25th percentile
    q50 FLOAT64,  -- Median forecast
    q75 FLOAT64,  -- 75th percentile
    q90 FLOAT64,  -- 90th percentile
    q95 FLOAT64,  -- 95th percentile
    
    -- Point Forecast
    point_forecast FLOAT64,
    
    -- Probability Distributions
    prob_down_3pct_5d FLOAT64,   -- P(drop > 3% in 5 days)
    prob_down_5pct_21d FLOAT64,  -- P(drop > 5% in 21 days)
    prob_up_5pct_21d FLOAT64,    -- P(rise > 5% in 21 days)
    
    -- Regime Context
    expected_regime STRING,
    regime_transition_probs STRUCT<
        bull_to_bear FLOAT64,
        bull_to_crash FLOAT64,
        bear_to_bull FLOAT64,
        bear_to_crash FLOAT64,
        crash_to_bull FLOAT64,
        crash_to_bear FLOAT64
    >,
    
    -- Top Drivers (SHAP)
    top_drivers ARRAY<STRUCT<
        feature_name STRING,
        shap_value FLOAT64,
        current_value FLOAT64,
        contribution_pct FLOAT64
    >>,
    
    -- Risk Metrics
    expected_sharpe_ratio FLOAT64,
    expected_sortino_ratio FLOAT64,
    max_drawdown_forecast FLOAT64,
    
    -- Technical Levels
    nearest_resistance FLOAT64,
    nearest_support FLOAT64,
    poc_level FLOAT64,
    pivot_level FLOAT64,
    fib_618_level FLOAT64,
    
    -- Model Metadata
    model_id STRING,
    model_family STRING,  -- 'NEURAL', 'TREE', 'ENSEMBLE'
    monte_carlo_paths INT64,
    garch_regime STRING,
    
    -- Trading Signals (View Only - NOT for live trading)
    signal_type STRING,  -- 'BULLISH', 'BEARISH', 'NEUTRAL'
    conviction FLOAT64,  -- 0-1 confidence score
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY prediction_date
CLUSTER BY horizon
OPTIONS(
    description='MES predictions for private dashboard page - VIEW ONLY, not for live trading'
);

-- ============================================================================
-- MES CORRELATION MONITORING
-- ============================================================================

CREATE TABLE IF NOT EXISTS `cbi-v14.monitoring.mes_zl_correlation` (
    date DATE NOT NULL,
    
    -- Rolling Correlations
    mes_zl_corr_20d FLOAT64,
    mes_zl_corr_60d FLOAT64,
    mes_zl_corr_250d FLOAT64,
    
    -- Regime-Conditional Correlations
    corr_bull_regime FLOAT64,
    corr_bear_regime FLOAT64,
    corr_crash_regime FLOAT64,
    
    -- Correlation Regime Classification
    correlation_regime STRING,  -- 'NORMAL', 'ELEVATED', 'BREAKDOWN'
    
    -- Spillover Metrics
    mes_to_zl_spillover FLOAT64,  -- Directional causality
    zl_to_mes_spillover FLOAT64,
    vix_mediation_effect FLOAT64,  -- VIX as transmission channel
    energy_transmission FLOAT64,   -- CL → MES → ZL pathway
    
    -- Alerts
    alert_triggered BOOL,  -- True if abs(corr) > 0.70
    alert_message STRING,
    
    -- Historical Context
    correlation_percentile_1y FLOAT64,
    correlation_percentile_5y FLOAT64,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
OPTIONS(
    description='MES-ZL correlation monitoring for risk management and spillover tracking'
);

-- ============================================================================
-- ACCESS CONTROL (Row-Level Security)
-- ============================================================================

-- Create row access policy for MES data in master_features
CREATE OR REPLACE ROW ACCESS POLICY mes_data_access
ON `cbi-v14.features.master_features`
GRANT TO (
    "serviceAccount:dashboard@cbi-v14.iam.gserviceaccount.com",
    "user:kirkmusick@gmail.com",  -- Admin access
    "serviceAccount:admin@cbi-v14.iam.gserviceaccount.com"
)
FILTER USING (
    -- Allow ZL data for everyone
    symbol != 'MES' 
    -- Allow MES data only for authorized users
    OR SESSION_USER() IN (
        'kirkmusick@gmail.com',
        'serviceAccount:mes-viewer@cbi-v14.iam.gserviceaccount.com',
        'serviceAccount:admin@cbi-v14.iam.gserviceaccount.com'
    )
);

-- Create API views for dashboard consumption
CREATE OR REPLACE VIEW `cbi-v14.api.vw_mes_private` AS
SELECT 
    date,
    -- Price Data
    databento_close as price,
    databento_open as open,
    databento_high as high,
    databento_low as low,
    databento_volume as volume,
    
    -- Returns
    returns_1d,
    returns_5d,
    
    -- Volatility
    vol_realized_20d,
    vix_close,
    
    -- MES-Specific Features
    mes_poc_distance,
    mes_pivot_confluence,
    mes_fib_618_distance,
    
    -- Regime & Risk
    ms_egarch_current_regime,
    prob_crash_next_5d,
    mes_zl_correlation
    
FROM `cbi-v14.features.master_features`
WHERE symbol = 'MES'
  AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY);

-- Grant access to the view
GRANT `roles/bigquery.dataViewer` 
ON TABLE `cbi-v14.api.vw_mes_private`
TO "serviceAccount:dashboard@cbi-v14.iam.gserviceaccount.com";

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify all MES tables were created
SELECT 
    table_schema,
    table_name,
    creation_time,
    row_count
FROM `cbi-v14.INFORMATION_SCHEMA.TABLES`
WHERE table_name LIKE 'mes_%'
ORDER BY table_schema, table_name;

-- Verify row-level security is active
SELECT 
    table_name,
    row_access_policy_name,
    grantee,
    filter_predicate
FROM `cbi-v14.INFORMATION_SCHEMA.ROW_ACCESS_POLICIES`
WHERE table_name = 'master_features';




