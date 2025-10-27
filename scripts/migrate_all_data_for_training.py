#!/usr/bin/env python3
"""
MIGRATE ALL DATA FOR TRAINING - RESPECTING DIFFERENT SCHEMAS
Gets ALL the data ready for Big 7 signals and model training
"""

from google.cloud import bigquery
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_all_data():
    """Safely migrate all data respecting different schemas"""
    client = bigquery.Client(project='cbi-v14')
    
    # 1. MOVE USDA HARVEST DATA (staging -> main)
    logger.info("🌾 Migrating USDA harvest data...")
    try:
        # First check if harvest_progress table has the right schema
        query = """
        INSERT INTO `cbi-v14.forecasting_data_warehouse.harvest_progress` 
        (report_date, country, crop_type, crop_year, progress_pct, five_year_avg_pct, 
         vs_5yr_avg, vs_prior_week, days_ahead_behind, yield_estimate, yield_vs_trend, 
         moisture_content, source, confidence_score, ingest_timestamp_utc, provenance_uuid)
        SELECT 
            harvest_date as report_date,
            state as country,  -- US states
            'SOYBEAN' as crop_type,
            CAST(year AS STRING) as crop_year,
            harvest_percentage as progress_pct,
            50.0 as five_year_avg_pct,  -- Default value
            0.0 as vs_5yr_avg,
            0.0 as vs_prior_week,
            0 as days_ahead_behind,
            0.0 as yield_estimate,
            0.0 as yield_vs_trend,
            0.0 as moisture_content,
            source,
            0.8 as confidence_score,
            created_at as ingest_timestamp_utc,
            GENERATE_UUID() as provenance_uuid
        FROM `cbi-v14.staging.usda_harvest_progress`
        WHERE harvest_date NOT IN (
            SELECT report_date 
            FROM `cbi-v14.forecasting_data_warehouse.harvest_progress`
        )
        """
        
        job = client.query(query)
        result = job.result()
        logger.info(f"✅ Migrated {result.total_rows} harvest records")
    except Exception as e:
        logger.error(f"❌ Harvest migration failed: {e}")
    
    # 2. MOVE BIOFUEL POLICY DATA (staging -> main)
    logger.info("⛽ Migrating biofuel policy data...")
    try:
        query = """
        INSERT INTO `cbi-v14.forecasting_data_warehouse.biofuel_metrics`
        (report_date, ethanol_production_thousand_barrels, biodiesel_production_thousand_barrels,
         ethanol_stocks_thousand_barrels, d4_rin_price, d6_rin_price, soybean_oil_price,
         biodiesel_price, soybean_oil_biodiesel_crush_margin, ethanol_production_vs_capacity,
         ethanol_stocks_vs_5yr_avg, crush_margin_vs_trend, policy_impact_score, source,
         confidence_score, ingest_timestamp_utc, provenance_uuid)
        SELECT 
            date as report_date,
            0.0 as ethanol_production_thousand_barrels,
            CASE 
                WHEN policy_type LIKE '%Biodiesel%' THEN mandate_volume / 42.0
                ELSE 0.0
            END as biodiesel_production_thousand_barrels,
            0.0 as ethanol_stocks_thousand_barrels,
            0.0 as d4_rin_price,
            0.0 as d6_rin_price,
            0.0 as soybean_oil_price,
            0.0 as biodiesel_price,
            0.0 as soybean_oil_biodiesel_crush_margin,
            0.0 as ethanol_production_vs_capacity,
            0.0 as ethanol_stocks_vs_5yr_avg,
            0.0 as crush_margin_vs_trend,
            COALESCE(mandate_volume, 0.0) as policy_impact_score,
            source_name as source,
            confidence_score,
            ingest_timestamp_utc,
            provenance_uuid
        FROM `cbi-v14.staging.biofuel_policy`
        WHERE date NOT IN (
            SELECT report_date 
            FROM `cbi-v14.forecasting_data_warehouse.biofuel_metrics`
        )
        """
        
        job = client.query(query)
        result = job.result()
        logger.info(f"✅ Migrated {result.total_rows} biofuel policy records")
    except Exception as e:
        logger.error(f"❌ Biofuel policy migration failed: {e}")
    
    # 3. ENSURE SOCIAL INTELLIGENCE IS ACCESSIBLE
    logger.info("💬 Checking social intelligence data...")
    try:
        query = """
        SELECT 
            COUNT(*) as total_records,
            MIN(DATE(PARSE_TIMESTAMP('%a %b %d %H:%M:%S %z %Y', created_at))) as min_date,
            MAX(DATE(PARSE_TIMESTAMP('%a %b %d %H:%M:%S %z %Y', created_at))) as max_date,
            COUNT(DISTINCT platform) as platforms,
            COUNT(DISTINCT author) as unique_authors
        FROM `cbi-v14.staging.comprehensive_social_intelligence`
        """
        
        result = client.query(query).to_dataframe()
        if not result.empty:
            logger.info(f"✅ Social Intelligence: {result['total_records'].iloc[0]} records")
            logger.info(f"   Date Range: {result['min_date'].iloc[0]} to {result['max_date'].iloc[0]}")
            logger.info(f"   Platforms: {result['platforms'].iloc[0]}, Authors: {result['unique_authors'].iloc[0]}")
    except Exception as e:
        logger.error(f"❌ Social intelligence check failed: {e}")
    
    # 4. CHECK ALL COMMODITY PRICES
    logger.info("📊 Verifying commodity price data...")
    commodities = [
        ('soybean_oil_prices', 'time', 'close'),
        ('soybean_prices', 'time', 'close'),
        ('corn_prices', 'time', 'close'),
        ('wheat_prices', 'time', 'close'),
        ('cotton_prices', 'time', 'close'),
        ('crude_oil_prices', 'date', 'close_price'),
        ('palm_oil_prices', 'time', 'close'),
        ('usd_index_prices', 'date', 'close_price')
    ]
    
    for table, date_col, price_col in commodities:
        try:
            if date_col == 'time':
                date_expr = f"DATE({date_col})"
            else:
                date_expr = date_col
                
            query = f"""
            SELECT 
                COUNT(*) as row_count,
                MIN({date_expr}) as min_date,
                MAX({date_expr}) as max_date,
                AVG({price_col}) as avg_price,
                STDDEV({price_col}) as price_volatility
            FROM `cbi-v14.forecasting_data_warehouse.{table}`
            """
            
            result = client.query(query).to_dataframe()
            if not result.empty:
                row = result.iloc[0]
                logger.info(f"✅ {table}: {row['row_count']} rows, ${row['avg_price']:.2f} avg, "
                           f"dates: {row['min_date']} to {row['max_date']}")
        except Exception as e:
            logger.error(f"❌ {table} check failed: {e}")
    
    # 5. CHECK RATES AND YIELDS
    logger.info("📈 Verifying rates and yields...")
    try:
        query = """
        SELECT 
            COUNT(*) as treasury_count,
            AVG(value) as avg_10y_yield,
            MIN(date) as min_date,
            MAX(date) as max_date
        FROM `cbi-v14.forecasting_data_warehouse.treasury_prices`
        WHERE indicator = '10_year_treasury'
        """
        
        result = client.query(query).to_dataframe()
        if not result.empty:
            row = result.iloc[0]
            logger.info(f"✅ 10Y Treasury: {row['treasury_count']} rows, "
                       f"{row['avg_10y_yield']:.2f}% avg yield")
    except Exception as e:
        logger.error(f"❌ Treasury check failed: {e}")
    
    # 6. CHECK VIX DATA
    logger.info("📉 Verifying VIX data...")
    try:
        query = """
        SELECT 
            COUNT(*) as vix_count,
            AVG(close) as avg_vix,
            MAX(close) as max_vix,
            MIN(date) as min_date,
            MAX(date) as max_date
        FROM `cbi-v14.forecasting_data_warehouse.vix_daily`
        """
        
        result = client.query(query).to_dataframe()
        if not result.empty:
            row = result.iloc[0]
            logger.info(f"✅ VIX: {row['vix_count']} rows, "
                       f"avg: {row['avg_vix']:.2f}, max: {row['max_vix']:.2f}")
    except Exception as e:
        logger.error(f"❌ VIX check failed: {e}")
    
    # 7. CREATE MASTER TRAINING VIEW
    logger.info("🎯 Creating master training view...")
    try:
        query = """
        CREATE OR REPLACE VIEW `cbi-v14.models.vw_big7_training_data` AS
        WITH daily_data AS (
            SELECT DISTINCT
                DATE(s.time) as feature_date,
                
                -- Target variable
                s.close as zl_price,
                
                -- Price features
                s.open as zl_open,
                s.high as zl_high,
                s.low as zl_low,
                s.volume as zl_volume,
                
                -- Other commodities (using correct schemas!)
                soy.close as soybean_price,
                corn.close as corn_price,
                wheat.close as wheat_price,
                cotton.close as cotton_price,
                crude.close_price as crude_oil_price,
                palm.close as palm_oil_price,
                dxy.close_price as usd_index,
                
                -- VIX
                vix.close as vix_level,
                
                -- Treasury yields
                treasury.value as treasury_10y_yield,
                
                -- Weather (aggregated)
                AVG(CASE WHEN w.station_id LIKE 'INMET_%' THEN w.precip_mm END) as brazil_precip,
                AVG(CASE WHEN w.station_id LIKE 'GHCND:AR%' THEN w.precip_mm END) as argentina_precip,
                AVG(CASE WHEN w.station_id LIKE 'GHCND:US%' THEN w.precip_mm END) as us_precip,
                
                -- Harvest progress
                MAX(h.progress_pct) as harvest_progress,
                
                -- Biofuel metrics
                MAX(b.policy_impact_score) as biofuel_policy_score
                
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
                ON DATE(s.time) = treasury.date AND treasury.indicator = '10_year_treasury'
            LEFT JOIN `cbi-v14.forecasting_data_warehouse.weather_data` w
                ON DATE(s.time) = w.date
            LEFT JOIN `cbi-v14.forecasting_data_warehouse.harvest_progress` h
                ON DATE(s.time) = h.report_date
            LEFT JOIN `cbi-v14.forecasting_data_warehouse.biofuel_metrics` b
                ON DATE(s.time) = b.report_date
            WHERE s.symbol = 'ZL'
            GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15
        )
        SELECT 
            *,
            -- Calculate returns
            (zl_price - LAG(zl_price) OVER (ORDER BY feature_date)) / 
                LAG(zl_price) OVER (ORDER BY feature_date) as zl_return_1d,
            (zl_price - LAG(zl_price, 5) OVER (ORDER BY feature_date)) / 
                LAG(zl_price, 5) OVER (ORDER BY feature_date) as zl_return_5d,
            
            -- Calculate volatility
            STDDEV(zl_price) OVER (ORDER BY feature_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as zl_volatility_20d,
            
            -- Correlations (rolling 30-day)
            CORR(zl_price, crude_oil_price) OVER (ORDER BY feature_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as zl_crude_corr_30d,
            CORR(zl_price, palm_oil_price) OVER (ORDER BY feature_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as zl_palm_corr_30d
            
        FROM daily_data
        ORDER BY feature_date DESC
        """
        
        job = client.query(query)
        job.result()
        logger.info("✅ Created master training view: models.vw_big7_training_data")
    except Exception as e:
        logger.error(f"❌ Training view creation failed: {e}")
    
    # Final summary
    logger.info("\n" + "="*80)
    logger.info("📊 DATA MIGRATION SUMMARY")
    logger.info("="*80)
    
    # Count total training records
    try:
        query = """
        SELECT 
            COUNT(*) as total_records,
            MIN(feature_date) as min_date,
            MAX(feature_date) as max_date,
            COUNT(DISTINCT feature_date) as unique_dates
        FROM `cbi-v14.models.vw_big7_training_data`
        WHERE zl_price IS NOT NULL
        """
        
        result = client.query(query).to_dataframe()
        if not result.empty:
            row = result.iloc[0]
            logger.info(f"🎯 TRAINING DATA READY:")
            logger.info(f"   Total Records: {row['total_records']}")
            logger.info(f"   Date Range: {row['min_date']} to {row['max_date']}")
            logger.info(f"   Unique Days: {row['unique_dates']}")
    except Exception as e:
        logger.error(f"❌ Training data summary failed: {e}")

if __name__ == "__main__":
    migrate_all_data()
