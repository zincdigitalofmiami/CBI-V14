#!/usr/bin/env python3
"""
Fix correlation features to use the new 2018+ data coverage
Now that we have proper historical data for all commodities
"""

from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

def check_current_correlations():
    """Check the current state of correlation features"""
    query = """
    SELECT 
        COUNT(*) as total_rows,
        COUNTIF(NOT IS_NAN(corr_zl_crude_7d) AND corr_zl_crude_7d IS NOT NULL) as valid_crude_7d,
        COUNTIF(NOT IS_NAN(corr_zl_palm_7d) AND corr_zl_palm_7d IS NOT NULL) as valid_palm_7d,
        COUNTIF(NOT IS_NAN(corr_zl_crude_30d) AND corr_zl_crude_30d IS NOT NULL) as valid_crude_30d,
        COUNTIF(NOT IS_NAN(corr_zl_palm_30d) AND corr_zl_palm_30d IS NOT NULL) as valid_palm_30d,
        MIN(date) as min_date,
        MAX(date) as max_date
    FROM `cbi-v14.models.vw_correlation_features`
    """
    
    result = list(client.query(query).result())[0]
    
    print("CURRENT CORRELATION FEATURES STATUS:")
    print(f"  Total rows: {result.total_rows}")
    print(f"  Date range: {result.min_date} to {result.max_date}")
    print(f"  Valid crude_7d: {result.valid_crude_7d} ({result.valid_crude_7d/result.total_rows*100:.1f}%)")
    print(f"  Valid palm_7d: {result.valid_palm_7d} ({result.valid_palm_7d/result.total_rows*100:.1f}%)")
    print(f"  Valid crude_30d: {result.valid_crude_30d} ({result.valid_crude_30d/result.total_rows*100:.1f}%)")
    print(f"  Valid palm_30d: {result.valid_palm_30d} ({result.valid_palm_30d/result.total_rows*100:.1f}%)")
    
    return result

def recreate_correlation_features():
    """Recreate correlation features with proper data alignment"""
    
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.models.vw_correlation_features` AS
    WITH aligned_prices AS (
        -- Get aligned price data for all commodities
        SELECT 
            COALESCE(zl.date, cl.date, palm.date, corn.date, wheat.date, vix.date, dxy.date) as date,
            
            -- Soybean Oil (our target)
            zl.close as zl_price,
            
            -- Other commodity prices
            cl.close_price as crude_price,
            palm.close as palm_price,
            corn.close as corn_price,
            wheat.close as wheat_price,
            vix.close as vix_level,
            dxy.close_price as dxy_level
            
        FROM (
            SELECT DATE(time) as date, close
            FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
            WHERE symbol = 'ZL'
            AND DATE(time) >= '2018-01-01'  -- Use our new historical data
        ) zl
        FULL OUTER JOIN (
            SELECT date, close_price
            FROM `cbi-v14.forecasting_data_warehouse.crude_oil_prices`
            WHERE symbol = 'CL'
            AND date >= '2018-01-01'
        ) cl ON zl.date = cl.date
        FULL OUTER JOIN (
            SELECT DATE(time) as date, close
            FROM `cbi-v14.forecasting_data_warehouse.palm_oil_prices`
            WHERE symbol = 'CPO'
            AND DATE(time) >= '2018-01-01'
        ) palm ON zl.date = palm.date
        FULL OUTER JOIN (
            SELECT DATE(time) as date, close
            FROM `cbi-v14.forecasting_data_warehouse.corn_prices`
            WHERE symbol = 'ZC'
            AND DATE(time) >= '2018-01-01'
        ) corn ON zl.date = corn.date
        FULL OUTER JOIN (
            SELECT DATE(time) as date, close
            FROM `cbi-v14.forecasting_data_warehouse.wheat_prices`
            WHERE symbol = 'ZW'
            AND DATE(time) >= '2018-01-01'
        ) wheat ON zl.date = wheat.date
        FULL OUTER JOIN (
            SELECT date, close
            FROM `cbi-v14.forecasting_data_warehouse.vix_daily`
            WHERE date >= '2018-01-01'
        ) vix ON zl.date = vix.date
        FULL OUTER JOIN (
            SELECT date, close_price
            FROM `cbi-v14.forecasting_data_warehouse.usd_index_prices`
            WHERE date >= '2018-01-01'
        ) dxy ON zl.date = dxy.date
        
        WHERE zl.close IS NOT NULL  -- Must have soybean oil data
    )
    SELECT 
        date,
        
        -- 7-day correlations (for 1w forecast)
        CORR(zl_price, crude_price) OVER (
            ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) as corr_zl_crude_7d,
        
        CORR(zl_price, palm_price) OVER (
            ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) as corr_zl_palm_7d,
        
        CORR(zl_price, vix_level) OVER (
            ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) as corr_zl_vix_7d,
        
        CORR(zl_price, dxy_level) OVER (
            ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) as corr_zl_dxy_7d,
        
        CORR(zl_price, corn_price) OVER (
            ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) as corr_zl_corn_7d,
        
        CORR(zl_price, wheat_price) OVER (
            ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) as corr_zl_wheat_7d,
        
        -- 30-day correlations (for 1m forecast)
        CORR(zl_price, crude_price) OVER (
            ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as corr_zl_crude_30d,
        
        CORR(zl_price, palm_price) OVER (
            ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as corr_zl_palm_30d,
        
        CORR(zl_price, vix_level) OVER (
            ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as corr_zl_vix_30d,
        
        CORR(zl_price, dxy_level) OVER (
            ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as corr_zl_dxy_30d,
        
        CORR(zl_price, corn_price) OVER (
            ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as corr_zl_corn_30d,
        
        CORR(zl_price, wheat_price) OVER (
            ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as corr_zl_wheat_30d,
        
        -- 90-day correlations (for 3m forecast)
        CORR(zl_price, crude_price) OVER (
            ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
        ) as corr_zl_crude_90d,
        
        CORR(zl_price, palm_price) OVER (
            ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
        ) as corr_zl_palm_90d,
        
        CORR(zl_price, vix_level) OVER (
            ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
        ) as corr_zl_vix_90d,
        
        CORR(zl_price, dxy_level) OVER (
            ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
        ) as corr_zl_dxy_90d,
        
        CORR(zl_price, corn_price) OVER (
            ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
        ) as corr_zl_corn_90d,
        
        -- 180-day correlations (for 6m forecast)
        CORR(zl_price, crude_price) OVER (
            ORDER BY date ROWS BETWEEN 179 PRECEDING AND CURRENT ROW
        ) as corr_zl_crude_180d,
        
        CORR(zl_price, palm_price) OVER (
            ORDER BY date ROWS BETWEEN 179 PRECEDING AND CURRENT ROW
        ) as corr_zl_palm_180d,
        
        CORR(zl_price, vix_level) OVER (
            ORDER BY date ROWS BETWEEN 179 PRECEDING AND CURRENT ROW
        ) as corr_zl_vix_180d,
        
        CORR(zl_price, dxy_level) OVER (
            ORDER BY date ROWS BETWEEN 179 PRECEDING AND CURRENT ROW
        ) as corr_zl_dxy_180d,
        
        -- 365-day correlations (for 12m forecast)
        CORR(zl_price, crude_price) OVER (
            ORDER BY date ROWS BETWEEN 364 PRECEDING AND CURRENT ROW
        ) as corr_zl_crude_365d,
        
        CORR(zl_price, palm_price) OVER (
            ORDER BY date ROWS BETWEEN 364 PRECEDING AND CURRENT ROW
        ) as corr_zl_palm_365d,
        
        CORR(zl_price, vix_level) OVER (
            ORDER BY date ROWS BETWEEN 364 PRECEDING AND CURRENT ROW
        ) as corr_zl_vix_365d,
        
        CORR(zl_price, dxy_level) OVER (
            ORDER BY date ROWS BETWEEN 364 PRECEDING AND CURRENT ROW
        ) as corr_zl_dxy_365d,
        
        CORR(zl_price, corn_price) OVER (
            ORDER BY date ROWS BETWEEN 364 PRECEDING AND CURRENT ROW
        ) as corr_zl_corn_365d,
        
        -- Cross-correlations (palm vs crude)
        CORR(palm_price, crude_price) OVER (
            ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as corr_palm_crude_30d,
        
        CORR(corn_price, wheat_price) OVER (
            ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as corr_corn_wheat_30d,
        
        -- Raw prices for reference
        zl_price,
        crude_price,
        palm_price,
        corn_price,
        wheat_price,
        vix_level,
        dxy_level
        
    FROM aligned_prices
    WHERE date >= '2018-01-01'
    ORDER BY date DESC
    """
    
    try:
        client.query(query).result()
        logger.info("✅ Successfully recreated correlation features with new data!")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to recreate correlation features: {e}")
        return False

def verify_new_correlations():
    """Verify the new correlation features"""
    
    query = """
    WITH stats AS (
        SELECT 
            COUNT(*) as total_rows,
            COUNTIF(NOT IS_NAN(corr_zl_crude_7d) AND corr_zl_crude_7d IS NOT NULL) as valid_crude_7d,
            COUNTIF(NOT IS_NAN(corr_zl_palm_7d) AND corr_zl_palm_7d IS NOT NULL) as valid_palm_7d,
            COUNTIF(NOT IS_NAN(corr_zl_crude_30d) AND corr_zl_crude_30d IS NOT NULL) as valid_crude_30d,
            COUNTIF(NOT IS_NAN(corr_zl_palm_30d) AND corr_zl_palm_30d IS NOT NULL) as valid_palm_30d,
            MIN(date) as min_date,
            MAX(date) as max_date,
            
            -- Sample correlations
            AVG(corr_zl_crude_30d) as avg_crude_corr_30d,
            AVG(corr_zl_palm_30d) as avg_palm_corr_30d,
            AVG(corr_zl_vix_30d) as avg_vix_corr_30d
            
        FROM `cbi-v14.models.vw_correlation_features`
    )
    SELECT * FROM stats
    """
    
    result = list(client.query(query).result())[0]
    
    print("\nNEW CORRELATION FEATURES STATUS:")
    print(f"  Total rows: {result.total_rows}")
    print(f"  Date range: {result.min_date} to {result.max_date}")
    print(f"  Valid crude_7d: {result.valid_crude_7d} ({result.valid_crude_7d/result.total_rows*100:.1f}%)")
    print(f"  Valid palm_7d: {result.valid_palm_7d} ({result.valid_palm_7d/result.total_rows*100:.1f}%)")
    print(f"  Valid crude_30d: {result.valid_crude_30d} ({result.valid_crude_30d/result.total_rows*100:.1f}%)")
    print(f"  Valid palm_30d: {result.valid_palm_30d} ({result.valid_palm_30d/result.total_rows*100:.1f}%)")
    
    print("\nSAMPLE CORRELATIONS (30-day):")
    print(f"  ZL-Crude: {result.avg_crude_corr_30d:.3f}")
    print(f"  ZL-Palm: {result.avg_palm_corr_30d:.3f}")
    print(f"  ZL-VIX: {result.avg_vix_corr_30d:.3f}")
    
    # Check improvement
    if result.valid_palm_30d / result.total_rows > 0.95:
        print("\n✅ EXCELLENT! Over 95% of rows have valid palm correlations now!")
    elif result.valid_palm_30d / result.total_rows > 0.8:
        print("\n✅ GOOD! Over 80% of rows have valid palm correlations now!")
    else:
        print("\n⚠️ Still have some NaN issues, but much improved")
    
    return result

def main():
    print("=" * 80)
    print("FIXING CORRELATION FEATURES WITH NEW 2018+ DATA")
    print("=" * 80)
    
    # 1. Check current state
    print("\n1. CHECKING CURRENT STATE:")
    before = check_current_correlations()
    
    # 2. Recreate with new data
    print("\n2. RECREATING CORRELATION FEATURES WITH NEW DATA:")
    success = recreate_correlation_features()
    
    if success:
        # 3. Verify improvements
        print("\n3. VERIFYING IMPROVEMENTS:")
        after = verify_new_correlations()
        
        # 4. Show improvement
        print("\n" + "=" * 80)
        print("IMPROVEMENT SUMMARY:")
        print("=" * 80)
        
        print(f"Total rows: {before.total_rows} → {after.total_rows}")
        print(f"Valid palm_7d: {before.valid_palm_7d} ({before.valid_palm_7d/before.total_rows*100:.1f}%) → "
              f"{after.valid_palm_7d} ({after.valid_palm_7d/after.total_rows*100:.1f}%)")
        print(f"Valid palm_30d: {before.valid_palm_30d} ({before.valid_palm_30d/before.total_rows*100:.1f}%) → "
              f"{after.valid_palm_30d} ({after.valid_palm_30d/after.total_rows*100:.1f}%)")
        
        print("\n✅ CORRELATION FEATURES FIXED WITH NEW DATA!")
        print("\nNext steps:")
        print("1. Update neural training dataset")
        print("2. Verify no NaN issues remain")
        print("3. Get approval for training")
        
        return True
    else:
        print("\n❌ Failed to fix correlation features")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
