#!/usr/bin/env python3
"""
CREATE SIMPLE TRAINING VIEW - ALL DATA FOR BIG 7
"""

from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_training_view():
    """Create simple but complete training view"""
    client = bigquery.Client(project='cbi-v14')
    
    logger.info("🎯 Creating training view...")
    try:
        query = """
        CREATE OR REPLACE VIEW `cbi-v14.models.vw_big7_training_data` AS
        SELECT DISTINCT
            DATE(s.time) as feature_date,
            
            -- TARGET
            s.close as zl_price,
            s.open as zl_open,
            s.high as zl_high,
            s.low as zl_low,
            s.volume as zl_volume,
            
            -- COMMODITIES
            soy.close as soybean_price,
            corn.close as corn_price,
            wheat.close as wheat_price,
            cotton.close as cotton_price,
            crude.close_price as crude_oil_price,
            palm.close as palm_oil_price,
            dxy.close_price as usd_index,
            
            -- VIX & RATES
            vix.close as vix_level,
            treasury.close as treasury_10y_yield,
            
            -- WEATHER
            AVG(CASE WHEN w.station_id LIKE 'INMET_%' THEN w.precip_mm END) 
                OVER (PARTITION BY DATE(s.time)) as brazil_precip,
            AVG(CASE WHEN w.station_id LIKE 'GHCND:AR%' THEN w.precip_mm END) 
                OVER (PARTITION BY DATE(s.time)) as argentina_precip,
            AVG(CASE WHEN w.station_id LIKE 'GHCND:US%' THEN w.precip_mm END) 
                OVER (PARTITION BY DATE(s.time)) as us_precip,
            
            -- RETURNS (simple calculation)
            (s.close - LAG(s.close) OVER (ORDER BY s.time)) / NULLIF(LAG(s.close) OVER (ORDER BY s.time), 0) as zl_return_1d,
            
            -- MOVING AVERAGES
            AVG(s.close) OVER (ORDER BY s.time ROWS BETWEEN 9 PRECEDING AND CURRENT ROW) as zl_ma_10d,
            AVG(s.close) OVER (ORDER BY s.time ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as zl_ma_20d,
            
            -- VOLATILITY
            STDDEV(s.close) OVER (ORDER BY s.time ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as zl_volatility_20d
            
        FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices` s
        LEFT JOIN `cbi-v14.forecasting_data_warehouse.soybean_prices` soy
            ON DATE(s.time) = DATE(soy.time)
        LEFT JOIN `cbi-v14.forecasting_data_warehouse.corn_prices` corn
            ON DATE(s.time) = DATE(corn.time)
        LEFT JOIN `cbi-v14.forecasting_data_warehouse.wheat_prices` wheat
            ON DATE(s.time) = DATE(wheat.time)
        LEFT JOIN `cbi-v14.forecasting_data_warehouse.cotton_prices` cotton
            ON DATE(s.time) = DATE(cotton.time)
        LEFT JOIN `cbi-v14.forecasting_data_warehouse.crude_oil_prices` crude
            ON DATE(s.time) = crude.date
        LEFT JOIN `cbi-v14.forecasting_data_warehouse.palm_oil_prices` palm
            ON s.time = palm.time
        LEFT JOIN `cbi-v14.forecasting_data_warehouse.usd_index_prices` dxy
            ON DATE(s.time) = dxy.date
        LEFT JOIN `cbi-v14.forecasting_data_warehouse.vix_daily` vix
            ON DATE(s.time) = vix.date
        LEFT JOIN `cbi-v14.forecasting_data_warehouse.treasury_prices` treasury
            ON DATE(s.time) = DATE(treasury.date) AND treasury.symbol = 'TNX'
        LEFT JOIN `cbi-v14.forecasting_data_warehouse.weather_data` w
            ON DATE(s.time) = w.date
        WHERE s.symbol = 'ZL'
        ORDER BY feature_date DESC
        """
        
        job = client.query(query)
        job.result()
        logger.info("✅ Created training view!")
        
        # Check the data
        query = """
        SELECT 
            COUNT(*) as total_records,
            MIN(feature_date) as min_date,
            MAX(feature_date) as max_date,
            COUNT(zl_price) as zl_records,
            COUNT(corn_price) as corn_records,
            COUNT(vix_level) as vix_records,
            COUNT(treasury_10y_yield) as treasury_records
        FROM `cbi-v14.models.vw_big7_training_data`
        """
        
        result = client.query(query).to_dataframe()
        row = result.iloc[0]
        
        logger.info("\n" + "="*80)
        logger.info("🎯 TRAINING DATA READY!")
        logger.info("="*80)
        logger.info(f"✅ Total Records: {row['total_records']:,}")
        logger.info(f"✅ Date Range: {row['min_date']} to {row['max_date']}")
        logger.info(f"✅ ZL Records: {row['zl_records']:,}")
        logger.info(f"✅ Corn Records: {row['corn_records']:,}")
        logger.info(f"✅ VIX Records: {row['vix_records']:,}")
        logger.info(f"✅ Treasury Records: {row['treasury_records']:,}")
        
    except Exception as e:
        logger.error(f"❌ Failed: {e}")

if __name__ == "__main__":
    create_training_view()
