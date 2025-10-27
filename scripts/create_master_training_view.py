#!/usr/bin/env python3
"""
Create the master training view with 5 target columns for multi-horizon forecasting
This is the FINAL view that combines ALL features for training 25 models
"""

from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

def create_master_training_view():
    """Create the comprehensive training view with all features and 5 targets"""
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.models.vw_neural_training_dataset_v2` AS
    WITH targets AS (
        -- Create the 5 forecast targets from soybean oil prices
        SELECT 
            DATE(time) as date,
            close as zl_price_current,
            
            -- CRITICAL: 5 horizon targets aligned with correlation windows
            LEAD(close, 7) OVER (ORDER BY time) as target_1w,    -- 7 days ahead
            LEAD(close, 30) OVER (ORDER BY time) as target_1m,   -- 30 days ahead
            LEAD(close, 90) OVER (ORDER BY time) as target_3m,   -- 90 days ahead
            LEAD(close, 180) OVER (ORDER BY time) as target_6m,  -- 180 days ahead
            LEAD(close, 365) OVER (ORDER BY time) as target_12m, -- 365 days ahead
            
            -- Additional price features
            LAG(close, 1) OVER (ORDER BY time) as zl_price_lag1,
            LAG(close, 7) OVER (ORDER BY time) as zl_price_lag7,
            LAG(close, 30) OVER (ORDER BY time) as zl_price_lag30,
            
            -- Price returns
            (close - LAG(close, 1) OVER (ORDER BY time)) / NULLIF(LAG(close, 1) OVER (ORDER BY time), 0) as return_1d,
            (close - LAG(close, 7) OVER (ORDER BY time)) / NULLIF(LAG(close, 7) OVER (ORDER BY time), 0) as return_7d,
            (close - LAG(close, 30) OVER (ORDER BY time)) / NULLIF(LAG(close, 30) OVER (ORDER BY time), 0) as return_30d,
            
            -- Moving averages
            AVG(close) OVER (ORDER BY time ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as ma_7d,
            AVG(close) OVER (ORDER BY time ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as ma_30d,
            AVG(close) OVER (ORDER BY time ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) as ma_90d,
            
            -- Volatility
            STDDEV(close) OVER (ORDER BY time ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as volatility_30d,
            
            -- Volume
            volume as zl_volume,
            AVG(volume) OVER (ORDER BY time ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as avg_volume_30d
            
        FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
        WHERE DATE(time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 YEAR)
        AND symbol = 'ZL'  -- CRITICAL: Only use actual soybean oil data, not SPX or other contamination!
    ),
    big8_signals AS (
        -- Get all Big 8 signals
        SELECT 
            date,
            feature_vix_stress,
            feature_harvest_pace,
            feature_china_relations,
            feature_tariff_threat,
            feature_geopolitical_volatility,
            feature_biofuel_cascade,
            feature_hidden_correlation,
            feature_biofuel_ethanol,
            big8_composite_score,
            market_regime,
            primary_driver
        FROM `cbi-v14.neural.vw_big_eight_signals`
    ),
    correlations AS (
        -- Get all correlation features (5 windows)
        SELECT 
            date,
            -- 7-day correlations (for 1w forecast)
            corr_zl_crude_7d,
            corr_zl_palm_7d,
            corr_zl_dxy_7d,
            corr_zl_vix_7d,
            corr_zl_corn_7d,
            
            -- 30-day correlations (for 1m forecast)
            corr_zl_crude_30d,
            corr_zl_palm_30d,
            corr_zl_dxy_30d,
            corr_zl_vix_30d,
            corr_zl_corn_30d,
            
            -- 90-day correlations (for 3m forecast)
            corr_zl_crude_90d,
            corr_zl_palm_90d,
            corr_zl_dxy_90d,
            corr_zl_vix_90d,
            corr_zl_corn_90d,
            
            -- 180-day correlations (for 6m forecast)
            corr_zl_crude_180d,
            corr_zl_palm_180d,
            corr_zl_dxy_180d,
            corr_zl_vix_180d,
            corr_zl_corn_180d,
            
            -- 365-day correlations (for 12m forecast)
            corr_zl_crude_365d,
            corr_zl_palm_365d,
            corr_zl_dxy_365d,
            corr_zl_vix_365d,
            corr_zl_corn_365d,
            
            -- Cross-correlations
            corr_palm_crude_30d,
            corr_corn_wheat_30d
            
        FROM `cbi-v14.models.vw_correlation_features`
    ),
    elasticities AS (
        -- Get elasticity features
        SELECT 
            date,
            soy_crude_elasticity_7d,
            soy_crude_elasticity_30d,
            palm_substitution_elasticity_7d,
            palm_substitution_elasticity_30d,
            china_demand_elasticity_7d,
            zl_momentum_1d,
            zl_momentum_7d,
            zl_momentum_30d,
            zl_crude_ratio,
            zl_palm_ratio
        FROM `cbi-v14.models.vw_elasticity_features`
    ),
    regimes AS (
        -- Get regime features
        SELECT 
            date,
            vix_regime,
            vix_crisis_flag,
            vix_stress_flag,
            harvest_regime,
            harvest_crisis_flag,
            harvest_stress_flag,
            policy_regime,
            policy_crisis_flag,
            policy_stress_flag,
            geopolitical_regime,
            geo_crisis_flag,
            geo_stress_flag,
            correlation_regime,
            correlation_breakdown_flag,
            extreme_correlation_flag,
            volatility_cluster_strength,
            overall_market_regime
        FROM `cbi-v14.models.vw_regime_features`
    ),
    weather AS (
        -- Get weather features (aggregated)
        SELECT 
            date,
            AVG(CASE WHEN station_id LIKE 'BR%' THEN temp_max END) as brazil_temp,
            AVG(CASE WHEN station_id LIKE 'BR%' THEN precip_mm END) as brazil_precip,
            AVG(CASE WHEN station_id LIKE 'AR%' THEN temp_max END) as argentina_temp,
            AVG(CASE WHEN station_id LIKE 'AR%' THEN precip_mm END) as argentina_precip,
            AVG(CASE WHEN station_id LIKE 'US%' THEN temp_max END) as us_temp,
            AVG(CASE WHEN station_id LIKE 'US%' THEN precip_mm END) as us_precip
        FROM `cbi-v14.forecasting_data_warehouse.weather_data`
        GROUP BY date
    ),
    sentiment AS (
        -- Get social sentiment features (aggregated)
        SELECT 
            DATE(timestamp) as date,
            AVG(sentiment_score) as avg_sentiment,
            COUNT(*) as sentiment_volume,
            STDDEV(sentiment_score) as sentiment_volatility
        FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1095 DAY)
        GROUP BY DATE(timestamp)
    )
    SELECT 
        t.date,
        
        -- ========== TARGET COLUMNS (5 horizons) ==========
        t.target_1w,
        t.target_1m,
        t.target_3m,
        t.target_6m,
        t.target_12m,
        
        -- ========== PRICE FEATURES ==========
        t.zl_price_current,
        t.zl_price_lag1,
        t.zl_price_lag7,
        t.zl_price_lag30,
        t.return_1d,
        t.return_7d,
        t.return_30d,
        t.ma_7d,
        t.ma_30d,
        t.ma_90d,
        t.volatility_30d,
        t.zl_volume,
        t.avg_volume_30d,
        
        -- ========== BIG 8 SIGNALS ==========
        COALESCE(b.feature_vix_stress, 0.5) as feature_vix_stress,
        COALESCE(b.feature_harvest_pace, 0.5) as feature_harvest_pace,
        COALESCE(b.feature_china_relations, 0.5) as feature_china_relations,
        COALESCE(b.feature_tariff_threat, 0.3) as feature_tariff_threat,
        COALESCE(b.feature_geopolitical_volatility, 0.4) as feature_geopolitical_volatility,
        COALESCE(b.feature_biofuel_cascade, 0.5) as feature_biofuel_cascade,
        COALESCE(b.feature_hidden_correlation, 0.0) as feature_hidden_correlation,
        COALESCE(b.feature_biofuel_ethanol, 0.5) as feature_biofuel_ethanol,
        COALESCE(b.big8_composite_score, 0.5) as big8_composite_score,
        
        -- ========== CORRELATION FEATURES (matched to horizons) ==========
        -- 7-day for 1w forecast
        COALESCE(c.corr_zl_crude_7d, 0) as corr_zl_crude_7d,
        COALESCE(c.corr_zl_palm_7d, 0) as corr_zl_palm_7d,
        COALESCE(c.corr_zl_vix_7d, 0) as corr_zl_vix_7d,
        
        -- 30-day for 1m forecast
        COALESCE(c.corr_zl_crude_30d, 0) as corr_zl_crude_30d,
        COALESCE(c.corr_zl_palm_30d, 0) as corr_zl_palm_30d,
        COALESCE(c.corr_zl_vix_30d, 0) as corr_zl_vix_30d,
        
        -- 90-day for 3m forecast
        COALESCE(c.corr_zl_crude_90d, 0) as corr_zl_crude_90d,
        COALESCE(c.corr_zl_palm_90d, 0) as corr_zl_palm_90d,
        
        -- 180-day for 6m forecast
        COALESCE(c.corr_zl_crude_180d, 0) as corr_zl_crude_180d,
        
        -- 365-day for 12m forecast
        COALESCE(c.corr_zl_crude_365d, 0) as corr_zl_crude_365d,
        
        -- ========== ELASTICITY FEATURES ==========
        COALESCE(e.soy_crude_elasticity_30d, 0) as soy_crude_elasticity_30d,
        COALESCE(e.palm_substitution_elasticity_30d, 0) as palm_substitution_elasticity_30d,
        COALESCE(e.china_demand_elasticity_7d, 0) as china_demand_elasticity_7d,
        COALESCE(e.zl_momentum_7d, 0) as zl_momentum_7d,
        COALESCE(e.zl_momentum_30d, 0) as zl_momentum_30d,
        
        -- ========== REGIME FEATURES ==========
        COALESCE(r.vix_crisis_flag, 0) as vix_crisis_flag,
        COALESCE(r.harvest_crisis_flag, 0) as harvest_crisis_flag,
        COALESCE(r.policy_crisis_flag, 0) as policy_crisis_flag,
        COALESCE(r.correlation_breakdown_flag, 0) as correlation_breakdown_flag,
        COALESCE(r.volatility_cluster_strength, 0) as volatility_cluster_strength,
        
        -- ========== WEATHER FEATURES ==========
        COALESCE(w.brazil_temp, 25) as brazil_temp,
        COALESCE(w.brazil_precip, 100) as brazil_precip,
        COALESCE(w.argentina_temp, 20) as argentina_temp,
        COALESCE(w.argentina_precip, 80) as argentina_precip,
        
        -- ========== SENTIMENT FEATURES ==========
        COALESCE(s.avg_sentiment, 0.5) as avg_sentiment,
        COALESCE(s.sentiment_volume, 0) as sentiment_volume,
        
        -- ========== METADATA ==========
        EXTRACT(DAYOFWEEK FROM t.date) as day_of_week,
        EXTRACT(MONTH FROM t.date) as month,
        EXTRACT(QUARTER FROM t.date) as quarter,
        
        CURRENT_TIMESTAMP() as created_at
        
    FROM targets t
    LEFT JOIN big8_signals b ON t.date = b.date
    LEFT JOIN correlations c ON t.date = c.date
    LEFT JOIN elasticities e ON t.date = e.date
    LEFT JOIN regimes r ON t.date = r.date
    LEFT JOIN weather w ON t.date = w.date
    LEFT JOIN sentiment s ON t.date = s.date
    
    -- Only include rows where we have all 5 targets
    WHERE t.target_12m IS NOT NULL
    ORDER BY t.date DESC
    """
    
    try:
        client.query(query).result()
        logger.info("✅ Created models.vw_neural_training_dataset_v2")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create models.vw_neural_training_dataset_v2: {e}")
        return False

def verify_training_data():
    """Verify the training data is complete and properly aligned"""
    query = """
    SELECT 
        COUNT(*) as total_rows,
        MIN(date) as earliest_date,
        MAX(date) as latest_date,
        
        -- Check targets
        COUNT(target_1w) as target_1w_count,
        COUNT(target_1m) as target_1m_count,
        COUNT(target_3m) as target_3m_count,
        COUNT(target_6m) as target_6m_count,
        COUNT(target_12m) as target_12m_count,
        
        -- Check key features
        AVG(feature_vix_stress) as avg_vix,
        AVG(feature_harvest_pace) as avg_harvest,
        AVG(big8_composite_score) as avg_composite,
        
        -- Check correlations
        AVG(ABS(corr_zl_crude_7d)) as avg_corr_7d,
        AVG(ABS(corr_zl_crude_30d)) as avg_corr_30d,
        AVG(ABS(corr_zl_crude_90d)) as avg_corr_90d,
        
        -- Check price stats
        MIN(zl_price_current) as min_price,
        MAX(zl_price_current) as max_price,
        AVG(zl_price_current) as avg_price,
        
        -- Check target price ranges
        MIN(target_1w) as min_target_1w,
        MAX(target_1w) as max_target_1w,
        MIN(target_12m) as min_target_12m,
        MAX(target_12m) as max_target_12m
        
    FROM `cbi-v14.models.vw_neural_training_dataset_v2`
    """
    
    try:
        result = list(client.query(query))[0]
        logger.info("\nTraining Data Statistics:")
        logger.info(f"  Total Rows: {result['total_rows']}")
        logger.info(f"  Date Range: {result['earliest_date']} to {result['latest_date']}")
        
        logger.info(f"\nTarget Coverage:")
        logger.info(f"  1 Week: {result['target_1w_count']} rows")
        logger.info(f"  1 Month: {result['target_1m_count']} rows")
        logger.info(f"  3 Months: {result['target_3m_count']} rows")
        logger.info(f"  6 Months: {result['target_6m_count']} rows")
        logger.info(f"  12 Months: {result['target_12m_count']} rows")
        
        logger.info(f"\nPrice Statistics:")
        logger.info(f"  Current: ${result['min_price']:.2f} - ${result['max_price']:.2f} (avg ${result['avg_price']:.2f})")
        logger.info(f"  1W Target: ${result['min_target_1w']:.2f} - ${result['max_target_1w']:.2f}")
        logger.info(f"  12M Target: ${result['min_target_12m']:.2f} - ${result['max_target_12m']:.2f}")
        
        logger.info(f"\nFeature Averages:")
        logger.info(f"  VIX Stress: {result['avg_vix']:.3f}")
        logger.info(f"  Harvest Pace: {result['avg_harvest']:.3f}")
        logger.info(f"  Big 8 Composite: {result['avg_composite']:.3f}")
        
        logger.info(f"\nCorrelation Windows:")
        logger.info(f"  7-day: {result['avg_corr_7d']:.3f}")
        logger.info(f"  30-day: {result['avg_corr_30d']:.3f}")
        logger.info(f"  90-day: {result['avg_corr_90d']:.3f}")
        
        return result['total_rows'] > 1000  # Need at least 1000 rows for training
        
    except Exception as e:
        logger.error(f"Could not verify: {e}")
        return False

def main():
    """Create and verify the master training view"""
    logger.info("=" * 50)
    logger.info("Creating Master Training View")
    logger.info("=" * 50)
    logger.info("\nThis view combines:")
    logger.info("  • 5 target columns (1w, 1m, 3m, 6m, 12m)")
    logger.info("  • 8 Big signals")
    logger.info("  • 5 correlation windows (matched to horizons)")
    logger.info("  • Elasticity features")
    logger.info("  • Regime features")
    logger.info("  • Weather & sentiment")
    
    # Create the view
    logger.info("\nCreating models.vw_neural_training_dataset_v2...")
    success = create_master_training_view()
    
    if success:
        logger.info("\nVerifying training data...")
        has_enough_data = verify_training_data()
        
        if has_enough_data:
            logger.info("\n" + "=" * 50)
            logger.info("✅ SUCCESS: Master Training View Created!")
            logger.info("Ready to train 25 models:")
            logger.info("  • 5 horizons (1w, 1m, 3m, 6m, 12m)")
            logger.info("  • 5 models per horizon")
            logger.info("  • All features properly aligned")
        else:
            logger.warning("⚠️ View created but may need more data for training")
    else:
        logger.error("❌ Failed to create master training view")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
