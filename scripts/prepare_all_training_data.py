#!/usr/bin/env python3
"""
PREPARE ALL TRAINING DATA - RESPECTING ACTUAL SCHEMAS
Gets ALL data ready for Big 7 signals and model training
"""

from google.cloud import bigquery
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def prepare_training_data():
    """Prepare all data for training with correct schemas"""
    client = bigquery.Client(project='cbi-v14')
    
    # 1. CREATE COMPREHENSIVE TRAINING VIEW
    logger.info("🎯 Creating comprehensive training view with ALL data...")
    try:
        query = """
        CREATE OR REPLACE VIEW `cbi-v14.models.vw_big7_training_data` AS
        WITH daily_data AS (
            SELECT DISTINCT
                DATE(s.time) as feature_date,
                
                -- TARGET VARIABLE
                s.close as zl_price,
                
                -- SOYBEAN OIL FEATURES (OHLCV)
                s.open as zl_open,
                s.high as zl_high,
                s.low as zl_low,
                s.volume as zl_volume,
                
                -- OTHER COMMODITIES (all have 'close' column)
                soy.close as soybean_price,
                corn.close as corn_price,
                wheat.close as wheat_price,
                cotton.close as cotton_price,
                
                -- CRUDE OIL (has 'close_price')
                crude.close_price as crude_oil_price,
                
                -- PALM OIL (has 'close')
                palm.close as palm_oil_price,
                
                -- USD INDEX (has 'close_price')
                dxy.close_price as usd_index,
                
                -- VIX (has 'close')
                vix.close as vix_level,
                
                -- TREASURY 10Y (has 'close', not 'value')
                treasury.close as treasury_10y_yield,
                
                -- WEATHER AGGREGATES
                AVG(CASE WHEN w.station_id LIKE 'INMET_%' THEN w.precip_mm END) as brazil_precip,
                AVG(CASE WHEN w.station_id LIKE 'INMET_%' THEN w.temp_max END) as brazil_temp_max,
                AVG(CASE WHEN w.station_id LIKE 'GHCND:AR%' THEN w.precip_mm END) as argentina_precip,
                AVG(CASE WHEN w.station_id LIKE 'GHCND:AR%' THEN w.temp_max END) as argentina_temp_max,
                AVG(CASE WHEN w.station_id LIKE 'GHCND:US%' THEN w.precip_mm END) as us_precip,
                AVG(CASE WHEN w.station_id LIKE 'GHCND:US%' THEN w.temp_max END) as us_temp_max
                
            FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices` s
            
            -- Join other commodities (all use 'time' column)
            LEFT JOIN `cbi-v14.forecasting_data_warehouse.soybean_prices` soy
                ON DATE(s.time) = DATE(soy.time)
            LEFT JOIN `cbi-v14.forecasting_data_warehouse.corn_prices` corn
                ON DATE(s.time) = DATE(corn.time)
            LEFT JOIN `cbi-v14.forecasting_data_warehouse.wheat_prices` wheat
                ON DATE(s.time) = DATE(wheat.time)
            LEFT JOIN `cbi-v14.forecasting_data_warehouse.cotton_prices` cotton
                ON DATE(s.time) = DATE(cotton.time)
                
            -- Crude oil uses 'date' column
            LEFT JOIN `cbi-v14.forecasting_data_warehouse.crude_oil_prices` crude
                ON DATE(s.time) = crude.date
                
            -- Palm oil uses 'time' column
            LEFT JOIN `cbi-v14.forecasting_data_warehouse.palm_oil_prices` palm
                ON s.time = palm.time
                
            -- USD index uses 'date' column
            LEFT JOIN `cbi-v14.forecasting_data_warehouse.usd_index_prices` dxy
                ON DATE(s.time) = dxy.date
                
            -- VIX uses 'date' column
            LEFT JOIN `cbi-v14.forecasting_data_warehouse.vix_daily` vix
                ON DATE(s.time) = vix.date
                
            -- Treasury uses 'date' column (DATETIME type)
            LEFT JOIN `cbi-v14.forecasting_data_warehouse.treasury_prices` treasury
                ON DATE(s.time) = DATE(treasury.date)
                AND treasury.symbol = 'TNX'  -- 10Y Treasury symbol
                
            -- Weather uses 'date' column
            LEFT JOIN `cbi-v14.forecasting_data_warehouse.weather_data` w
                ON DATE(s.time) = w.date
                
            WHERE s.symbol = 'ZL'
            GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15
        ),
        
        social_signals AS (
            -- Add social intelligence signals (aggregated daily)
            SELECT 
                DATE(PARSE_TIMESTAMP('%a %b %d %H:%M:%S %z %Y', created_at)) as signal_date,
                
                -- China sentiment
                AVG(CASE 
                    WHEN LOWER(content) LIKE '%china%' AND LOWER(content) LIKE '%tariff%' THEN 0.9
                    WHEN LOWER(content) LIKE '%china%' AND LOWER(content) LIKE '%trade%' THEN 0.7
                    WHEN LOWER(content) LIKE '%china%' AND LOWER(content) LIKE '%deal%' THEN 0.3
                    ELSE 0.5
                END) as china_sentiment,
                
                -- Trump policy intensity
                COUNT(CASE 
                    WHEN LOWER(content) LIKE '%tariff%' OR LOWER(content) LIKE '%trade war%'
                    THEN 1 
                END) as tariff_mentions,
                
                -- Biofuel signals
                COUNT(CASE 
                    WHEN LOWER(content) LIKE '%biodiesel%' OR LOWER(content) LIKE '%renewable%diesel%'
                    THEN 1 
                END) as biofuel_mentions,
                
                -- Harvest sentiment
                AVG(CASE 
                    WHEN LOWER(content) LIKE '%harvest%' AND LOWER(content) LIKE '%delay%' THEN 0.3
                    WHEN LOWER(content) LIKE '%harvest%' AND LOWER(content) LIKE '%record%' THEN 0.9
                    WHEN LOWER(content) LIKE '%drought%' THEN 0.2
                    ELSE 0.5
                END) as harvest_sentiment,
                
                COUNT(*) as social_volume
                
            FROM `cbi-v14.staging.comprehensive_social_intelligence`
            GROUP BY 1
        )
        
        SELECT 
            d.*,
            
            -- Add social signals
            s.china_sentiment,
            s.tariff_mentions,
            s.biofuel_mentions,
            s.harvest_sentiment,
            s.social_volume,
            
            -- CALCULATE RETURNS
            (d.zl_price - LAG(d.zl_price) OVER (ORDER BY d.feature_date)) / 
                NULLIF(LAG(d.zl_price) OVER (ORDER BY d.feature_date), 0) as zl_return_1d,
            (d.zl_price - LAG(d.zl_price, 5) OVER (ORDER BY d.feature_date)) / 
                NULLIF(LAG(d.zl_price, 5) OVER (ORDER BY d.feature_date), 0) as zl_return_5d,
            (d.zl_price - LAG(d.zl_price, 20) OVER (ORDER BY d.feature_date)) / 
                NULLIF(LAG(d.zl_price, 20) OVER (ORDER BY d.feature_date), 0) as zl_return_20d,
            
            -- CALCULATE VOLATILITY
            STDDEV(d.zl_price) OVER (ORDER BY d.feature_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as zl_volatility_20d,
            STDDEV(d.zl_price) OVER (ORDER BY d.feature_date ROWS BETWEEN 59 PRECEDING AND CURRENT ROW) as zl_volatility_60d,
            
            -- CALCULATE MOVING AVERAGES
            AVG(d.zl_price) OVER (ORDER BY d.feature_date ROWS BETWEEN 9 PRECEDING AND CURRENT ROW) as zl_ma_10d,
            AVG(d.zl_price) OVER (ORDER BY d.feature_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as zl_ma_20d,
            AVG(d.zl_price) OVER (ORDER BY d.feature_date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) as zl_ma_50d,
            
            -- CORRELATIONS (rolling 30-day)
            CORR(d.zl_price, d.crude_oil_price) OVER (ORDER BY d.feature_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as zl_crude_corr_30d,
            CORR(d.zl_price, d.palm_oil_price) OVER (ORDER BY d.feature_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as zl_palm_corr_30d,
            CORR(d.zl_price, d.usd_index) OVER (ORDER BY d.feature_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as zl_dxy_corr_30d,
            CORR(d.zl_price, d.vix_level) OVER (ORDER BY d.feature_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as zl_vix_corr_30d,
            
            -- RSI CALCULATION (14-day)
            100 - (100 / (1 + 
                (AVG(CASE WHEN d.zl_price > LAG(d.zl_price) OVER (ORDER BY d.feature_date) 
                    THEN d.zl_price - LAG(d.zl_price) OVER (ORDER BY d.feature_date) 
                    ELSE 0 END) OVER (ORDER BY d.feature_date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW)) /
                NULLIF(AVG(CASE WHEN d.zl_price < LAG(d.zl_price) OVER (ORDER BY d.feature_date) 
                    THEN LAG(d.zl_price) OVER (ORDER BY d.feature_date) - d.zl_price 
                    ELSE 0 END) OVER (ORDER BY d.feature_date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW), 0)
            )) as zl_rsi_14d
            
        FROM daily_data d
        LEFT JOIN social_signals s ON d.feature_date = s.signal_date
        WHERE d.zl_price IS NOT NULL
        ORDER BY d.feature_date DESC
        """
        
        job = client.query(query)
        job.result()
        logger.info("✅ Created comprehensive training view: models.vw_big7_training_data")
    except Exception as e:
        logger.error(f"❌ Training view creation failed: {e}")
        return
    
    # 2. VERIFY THE TRAINING DATA
    logger.info("\n📊 Verifying training data completeness...")
    try:
        query = """
        SELECT 
            COUNT(*) as total_records,
            MIN(feature_date) as min_date,
            MAX(feature_date) as max_date,
            COUNT(DISTINCT feature_date) as unique_dates,
            
            -- Check data completeness
            COUNT(zl_price) as zl_records,
            COUNT(soybean_price) as soybean_records,
            COUNT(corn_price) as corn_records,
            COUNT(wheat_price) as wheat_records,
            COUNT(cotton_price) as cotton_records,
            COUNT(crude_oil_price) as crude_records,
            COUNT(palm_oil_price) as palm_records,
            COUNT(usd_index) as dxy_records,
            COUNT(vix_level) as vix_records,
            COUNT(treasury_10y_yield) as treasury_records,
            COUNT(brazil_precip) as brazil_weather_records,
            COUNT(china_sentiment) as social_records
            
        FROM `cbi-v14.models.vw_big7_training_data`
        """
        
        result = client.query(query).to_dataframe()
        if not result.empty:
            row = result.iloc[0]
            logger.info("\n" + "="*80)
            logger.info("🎯 TRAINING DATA READY FOR BIG 7 SIGNALS")
            logger.info("="*80)
            logger.info(f"✅ Total Records: {row['total_records']:,}")
            logger.info(f"✅ Date Range: {row['min_date']} to {row['max_date']}")
            logger.info(f"✅ Unique Trading Days: {row['unique_dates']:,}")
            logger.info("\n📊 DATA COMPLETENESS:")
            logger.info(f"   Soybean Oil (ZL): {row['zl_records']:,} records")
            logger.info(f"   Soybean: {row['soybean_records']:,} records")
            logger.info(f"   Corn: {row['corn_records']:,} records")
            logger.info(f"   Wheat: {row['wheat_records']:,} records")
            logger.info(f"   Cotton: {row['cotton_records']:,} records")
            logger.info(f"   Crude Oil: {row['crude_records']:,} records")
            logger.info(f"   Palm Oil: {row['palm_records']:,} records")
            logger.info(f"   USD Index: {row['dxy_records']:,} records")
            logger.info(f"   VIX: {row['vix_records']:,} records")
            logger.info(f"   Treasury 10Y: {row['treasury_records']:,} records")
            logger.info(f"   Brazil Weather: {row['brazil_weather_records']:,} records")
            logger.info(f"   Social Signals: {row['social_records']:,} records")
    except Exception as e:
        logger.error(f"❌ Training data verification failed: {e}")
    
    # 3. CHECK FEATURE QUALITY
    logger.info("\n📈 Checking feature quality...")
    try:
        query = """
        SELECT 
            -- Price statistics
            AVG(zl_price) as avg_zl_price,
            STDDEV(zl_price) as zl_volatility,
            MIN(zl_price) as min_zl_price,
            MAX(zl_price) as max_zl_price,
            
            -- Returns
            AVG(zl_return_1d) * 100 as avg_daily_return_pct,
            STDDEV(zl_return_1d) * 100 as daily_return_volatility_pct,
            
            -- Correlations
            AVG(zl_crude_corr_30d) as avg_crude_correlation,
            AVG(zl_palm_corr_30d) as avg_palm_correlation,
            AVG(zl_vix_corr_30d) as avg_vix_correlation,
            
            -- VIX levels
            AVG(vix_level) as avg_vix,
            MAX(vix_level) as max_vix,
            
            -- Social signals
            AVG(china_sentiment) as avg_china_sentiment,
            SUM(tariff_mentions) as total_tariff_mentions
            
        FROM `cbi-v14.models.vw_big7_training_data`
        WHERE feature_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
        """
        
        result = client.query(query).to_dataframe()
        if not result.empty:
            row = result.iloc[0]
            logger.info("\n📈 FEATURE STATISTICS (Last 365 Days):")
            logger.info(f"   ZL Price: ${row['avg_zl_price']:.2f} (${row['min_zl_price']:.2f} - ${row['max_zl_price']:.2f})")
            logger.info(f"   Daily Return: {row['avg_daily_return_pct']:.3f}% ± {row['daily_return_volatility_pct']:.3f}%")
            logger.info(f"   Crude Correlation: {row['avg_crude_correlation']:.3f}")
            logger.info(f"   Palm Correlation: {row['avg_palm_correlation']:.3f}")
            logger.info(f"   VIX Correlation: {row['avg_vix_correlation']:.3f}")
            logger.info(f"   VIX Level: {row['avg_vix']:.2f} (max: {row['max_vix']:.2f})")
            logger.info(f"   China Sentiment: {row['avg_china_sentiment']:.3f}")
            logger.info(f"   Tariff Mentions: {row['total_tariff_mentions']:.0f}")
    except Exception as e:
        logger.error(f"❌ Feature quality check failed: {e}")
    
    logger.info("\n" + "="*80)
    logger.info("✅ ALL DATA READY FOR BIG 7 SIGNALS AND MODEL TRAINING!")
    logger.info("="*80)

if __name__ == "__main__":
    prepare_training_data()
