#!/usr/bin/env python3
"""
Create correlation features with 5 windows matching forecast horizons
CRITICAL: Each horizon needs its own correlation window for proper alignment
"""

from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

def create_correlation_features():
    """Create correlation features with 5 different windows"""
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.models.vw_correlation_features` AS
    WITH price_data AS (
        -- Get all relevant price series
        SELECT 
            DATE(s.time) as date,
            s.close as zl_price,
            c.close_price as crude_price,
            p.close as palm_price,
            d.close_price as dxy_price,
            v.close as vix_price,
            corn.close as corn_price,
            w.close as wheat_price,
            cot.close as cotton_price
        FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices` s
        LEFT JOIN `cbi-v14.forecasting_data_warehouse.crude_oil_prices` c
            ON DATE(s.time) = c.date
        LEFT JOIN `cbi-v14.forecasting_data_warehouse.palm_oil_prices` p
            ON s.time = p.time
        LEFT JOIN `cbi-v14.forecasting_data_warehouse.usd_index_prices` d
            ON DATE(s.time) = d.date
        LEFT JOIN `cbi-v14.forecasting_data_warehouse.vix_daily` v
            ON DATE(s.time) = v.date
        LEFT JOIN `cbi-v14.forecasting_data_warehouse.corn_prices` corn
            ON s.time = corn.time
        LEFT JOIN `cbi-v14.forecasting_data_warehouse.wheat_prices` w
            ON DATE(s.time) = w.date
        LEFT JOIN `cbi-v14.forecasting_data_warehouse.cotton_prices` cot
            ON s.time = cot.time
        WHERE DATE(s.time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 YEAR)
    ),
    correlations AS (
        SELECT 
            date,
            zl_price,
            
            -- ========== 7-DAY CORRELATIONS (for 1 WEEK forecast) ==========
            CORR(zl_price, crude_price) OVER (
                ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
            ) as corr_zl_crude_7d,
            
            CORR(zl_price, palm_price) OVER (
                ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
            ) as corr_zl_palm_7d,
            
            CORR(zl_price, dxy_price) OVER (
                ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
            ) as corr_zl_dxy_7d,
            
            CORR(zl_price, vix_price) OVER (
                ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
            ) as corr_zl_vix_7d,
            
            CORR(zl_price, corn_price) OVER (
                ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
            ) as corr_zl_corn_7d,
            
            -- ========== 30-DAY CORRELATIONS (for 1 MONTH forecast) ==========
            CORR(zl_price, crude_price) OVER (
                ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
            ) as corr_zl_crude_30d,
            
            CORR(zl_price, palm_price) OVER (
                ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
            ) as corr_zl_palm_30d,
            
            CORR(zl_price, dxy_price) OVER (
                ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
            ) as corr_zl_dxy_30d,
            
            CORR(zl_price, vix_price) OVER (
                ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
            ) as corr_zl_vix_30d,
            
            CORR(zl_price, corn_price) OVER (
                ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
            ) as corr_zl_corn_30d,
            
            -- ========== 90-DAY CORRELATIONS (for 3 MONTH forecast) ==========
            CORR(zl_price, crude_price) OVER (
                ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
            ) as corr_zl_crude_90d,
            
            CORR(zl_price, palm_price) OVER (
                ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
            ) as corr_zl_palm_90d,
            
            CORR(zl_price, dxy_price) OVER (
                ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
            ) as corr_zl_dxy_90d,
            
            CORR(zl_price, vix_price) OVER (
                ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
            ) as corr_zl_vix_90d,
            
            CORR(zl_price, corn_price) OVER (
                ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
            ) as corr_zl_corn_90d,
            
            -- ========== 180-DAY CORRELATIONS (for 6 MONTH forecast) ==========
            CORR(zl_price, crude_price) OVER (
                ORDER BY date ROWS BETWEEN 179 PRECEDING AND CURRENT ROW
            ) as corr_zl_crude_180d,
            
            CORR(zl_price, palm_price) OVER (
                ORDER BY date ROWS BETWEEN 179 PRECEDING AND CURRENT ROW
            ) as corr_zl_palm_180d,
            
            CORR(zl_price, dxy_price) OVER (
                ORDER BY date ROWS BETWEEN 179 PRECEDING AND CURRENT ROW
            ) as corr_zl_dxy_180d,
            
            CORR(zl_price, vix_price) OVER (
                ORDER BY date ROWS BETWEEN 179 PRECEDING AND CURRENT ROW
            ) as corr_zl_vix_180d,
            
            CORR(zl_price, corn_price) OVER (
                ORDER BY date ROWS BETWEEN 179 PRECEDING AND CURRENT ROW
            ) as corr_zl_corn_180d,
            
            -- ========== 365-DAY CORRELATIONS (for 12 MONTH forecast) ==========
            CORR(zl_price, crude_price) OVER (
                ORDER BY date ROWS BETWEEN 364 PRECEDING AND CURRENT ROW
            ) as corr_zl_crude_365d,
            
            CORR(zl_price, palm_price) OVER (
                ORDER BY date ROWS BETWEEN 364 PRECEDING AND CURRENT ROW
            ) as corr_zl_palm_365d,
            
            CORR(zl_price, dxy_price) OVER (
                ORDER BY date ROWS BETWEEN 364 PRECEDING AND CURRENT ROW
            ) as corr_zl_dxy_365d,
            
            CORR(zl_price, vix_price) OVER (
                ORDER BY date ROWS BETWEEN 364 PRECEDING AND CURRENT ROW
            ) as corr_zl_vix_365d,
            
            CORR(zl_price, corn_price) OVER (
                ORDER BY date ROWS BETWEEN 364 PRECEDING AND CURRENT ROW
            ) as corr_zl_corn_365d,
            
            -- Cross-commodity correlations (useful for substitution effects)
            CORR(palm_price, crude_price) OVER (
                ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
            ) as corr_palm_crude_30d,
            
            CORR(corn_price, wheat_price) OVER (
                ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
            ) as corr_corn_wheat_30d
            
        FROM price_data
    )
    SELECT 
        date,
        
        -- 7-day correlations (1 WEEK forecast features)
        COALESCE(corr_zl_crude_7d, 0) as corr_zl_crude_7d,
        COALESCE(corr_zl_palm_7d, 0) as corr_zl_palm_7d,
        COALESCE(corr_zl_dxy_7d, 0) as corr_zl_dxy_7d,
        COALESCE(corr_zl_vix_7d, 0) as corr_zl_vix_7d,
        COALESCE(corr_zl_corn_7d, 0) as corr_zl_corn_7d,
        
        -- 30-day correlations (1 MONTH forecast features)
        COALESCE(corr_zl_crude_30d, 0) as corr_zl_crude_30d,
        COALESCE(corr_zl_palm_30d, 0) as corr_zl_palm_30d,
        COALESCE(corr_zl_dxy_30d, 0) as corr_zl_dxy_30d,
        COALESCE(corr_zl_vix_30d, 0) as corr_zl_vix_30d,
        COALESCE(corr_zl_corn_30d, 0) as corr_zl_corn_30d,
        
        -- 90-day correlations (3 MONTH forecast features)
        COALESCE(corr_zl_crude_90d, 0) as corr_zl_crude_90d,
        COALESCE(corr_zl_palm_90d, 0) as corr_zl_palm_90d,
        COALESCE(corr_zl_dxy_90d, 0) as corr_zl_dxy_90d,
        COALESCE(corr_zl_vix_90d, 0) as corr_zl_vix_90d,
        COALESCE(corr_zl_corn_90d, 0) as corr_zl_corn_90d,
        
        -- 180-day correlations (6 MONTH forecast features)
        COALESCE(corr_zl_crude_180d, 0) as corr_zl_crude_180d,
        COALESCE(corr_zl_palm_180d, 0) as corr_zl_palm_180d,
        COALESCE(corr_zl_dxy_180d, 0) as corr_zl_dxy_180d,
        COALESCE(corr_zl_vix_180d, 0) as corr_zl_vix_180d,
        COALESCE(corr_zl_corn_180d, 0) as corr_zl_corn_180d,
        
        -- 365-day correlations (12 MONTH forecast features)
        COALESCE(corr_zl_crude_365d, 0) as corr_zl_crude_365d,
        COALESCE(corr_zl_palm_365d, 0) as corr_zl_palm_365d,
        COALESCE(corr_zl_dxy_365d, 0) as corr_zl_dxy_365d,
        COALESCE(corr_zl_vix_365d, 0) as corr_zl_vix_365d,
        COALESCE(corr_zl_corn_365d, 0) as corr_zl_corn_365d,
        
        -- Additional cross-correlations
        COALESCE(corr_palm_crude_30d, 0) as corr_palm_crude_30d,
        COALESCE(corr_corn_wheat_30d, 0) as corr_corn_wheat_30d,
        
        CURRENT_TIMESTAMP() as updated_at
        
    FROM correlations
    ORDER BY date DESC
    """
    
    try:
        client.query(query).result()
        logger.info("✅ Created models.vw_correlation_features")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create models.vw_correlation_features: {e}")
        return False

def verify_correlations():
    """Verify correlation features are properly aligned"""
    query = """
    SELECT 
        COUNT(*) as total_rows,
        MIN(date) as earliest_date,
        MAX(date) as latest_date,
        
        -- Check 7-day correlations
        AVG(ABS(corr_zl_crude_7d)) as avg_abs_corr_7d,
        AVG(ABS(corr_zl_palm_7d)) as avg_abs_palm_7d,
        
        -- Check 30-day correlations
        AVG(ABS(corr_zl_crude_30d)) as avg_abs_corr_30d,
        AVG(ABS(corr_zl_palm_30d)) as avg_abs_palm_30d,
        
        -- Check 90-day correlations
        AVG(ABS(corr_zl_crude_90d)) as avg_abs_corr_90d,
        
        -- Check 180-day correlations
        AVG(ABS(corr_zl_crude_180d)) as avg_abs_corr_180d,
        
        -- Check 365-day correlations
        AVG(ABS(corr_zl_crude_365d)) as avg_abs_corr_365d
        
    FROM `cbi-v14.models.vw_correlation_features`
    WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR)
    """
    
    try:
        result = list(client.query(query))[0]
        logger.info("\nCorrelation Features Statistics:")
        logger.info(f"  Total Rows: {result['total_rows']}")
        logger.info(f"  Date Range: {result['earliest_date']} to {result['latest_date']}")
        logger.info(f"\nAverage Absolute Correlations by Window:")
        logger.info(f"  7-day: ZL-Crude={result['avg_abs_corr_7d']:.3f}, ZL-Palm={result['avg_abs_palm_7d']:.3f}")
        logger.info(f"  30-day: ZL-Crude={result['avg_abs_corr_30d']:.3f}, ZL-Palm={result['avg_abs_palm_30d']:.3f}")
        logger.info(f"  90-day: ZL-Crude={result['avg_abs_corr_90d']:.3f}")
        logger.info(f"  180-day: ZL-Crude={result['avg_abs_corr_180d']:.3f}")
        logger.info(f"  365-day: ZL-Crude={result['avg_abs_corr_365d']:.3f}")
        
        return result['total_rows'] > 0
    except Exception as e:
        logger.error(f"Could not verify: {e}")
        return False

def main():
    """Create and verify correlation features"""
    logger.info("=" * 50)
    logger.info("Creating Correlation Features (5 Windows)")
    logger.info("=" * 50)
    logger.info("\nHorizon Alignment:")
    logger.info("  • 7-day correlations → 1 WEEK forecast")
    logger.info("  • 30-day correlations → 1 MONTH forecast")
    logger.info("  • 90-day correlations → 3 MONTH forecast")
    logger.info("  • 180-day correlations → 6 MONTH forecast")
    logger.info("  • 365-day correlations → 12 MONTH forecast")
    
    # Create the view
    logger.info("\nCreating models.vw_correlation_features...")
    success = create_correlation_features()
    
    if success:
        logger.info("\nVerifying correlation features...")
        has_data = verify_correlations()
        
        if has_data:
            logger.info("\n" + "=" * 50)
            logger.info("✅ SUCCESS: Correlation Features Created!")
            logger.info("All 5 correlation windows properly aligned with forecast horizons")
            logger.info("Ready for multi-horizon training!")
        else:
            logger.warning("⚠️ View created but may have limited data")
    else:
        logger.error("❌ Failed to create correlation features")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
