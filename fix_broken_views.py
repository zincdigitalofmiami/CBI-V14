#!/usr/bin/env python3
"""
FIX BROKEN DASHBOARD VIEWS
Repairs all 11 broken views by updating their source table references
"""

from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

def fix_broken_views():
    """Fix all broken dashboard views"""
    
    fixes = {
        # Fix commodity prices views - remove reference to non-existent sunflower_oil_prices
        'vw_commodity_prices_daily': """
            CREATE OR REPLACE VIEW `cbi-v14.curated.vw_commodity_prices_daily` AS
            SELECT 
                CAST(time AS DATE) as date,
                'soybean_oil' as commodity,
                close as price,
                volume,
                high as high_price,
                low as low_price
            FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
            UNION ALL
            SELECT 
                CAST(time AS DATE) as date,
                'palm_oil' as commodity,
                close as price,
                volume,
                high as high_price,
                low as low_price
            FROM `cbi-v14.forecasting_data_warehouse.palm_oil_prices`
            UNION ALL
            SELECT 
                CAST(time AS DATE) as date,
                'crude_oil' as commodity,
                close as price,
                volume,
                high as high_price,
                low as low_price
            FROM `cbi-v14.forecasting_data_warehouse.crude_oil_prices`
            UNION ALL
            SELECT 
                CAST(time AS DATE) as date,
                'corn' as commodity,
                close as price,
                volume,
                high as high_price,
                low as low_price
            FROM `cbi-v14.forecasting_data_warehouse.corn_prices`
            ORDER BY date DESC, commodity
        """,
        
        'vw_dashboard_commodity_prices': """
            CREATE OR REPLACE VIEW `cbi-v14.curated.vw_dashboard_commodity_prices` AS
            SELECT 
                CAST(time AS DATE) as date,
                close as soybean_oil_price,
                volume as soybean_oil_volume,
                LAG(close, 1) OVER (ORDER BY time) as prev_price,
                (close - LAG(close, 1) OVER (ORDER BY time)) / 
                    NULLIF(LAG(close, 1) OVER (ORDER BY time), 0) * 100 as daily_change_pct
            FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
            WHERE time >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
            ORDER BY date DESC
        """,
        
        # Fix weather views - use actual weather tables
        'vw_dashboard_weather_intelligence': """
            CREATE OR REPLACE VIEW `cbi-v14.curated.vw_dashboard_weather_intelligence` AS
            SELECT 
                date,
                'Brazil' as region,
                AVG(temp_avg_c) as avg_temp,
                SUM(precip_mm) as total_precip,
                NULL as avg_humidity
            FROM `cbi-v14.forecasting_data_warehouse.weather_brazil_daily`
            WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            GROUP BY date
            UNION ALL
            SELECT 
                date,
                'Argentina' as region,
                AVG(temp_avg_c) as avg_temp,
                SUM(precip_mm) as total_precip,
                NULL as avg_humidity
            FROM `cbi-v14.forecasting_data_warehouse.weather_argentina_daily`
            WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            GROUP BY date
            UNION ALL
            SELECT 
                date,
                'US Midwest' as region,
                AVG(temp_avg_c) as avg_temp,
                SUM(precip_mm) as total_precip,
                NULL as avg_humidity
            FROM `cbi-v14.forecasting_data_warehouse.weather_us_midwest_daily`
            WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            GROUP BY date
            ORDER BY date DESC, region
        """,
        
        'vw_weather_daily': """
            CREATE OR REPLACE VIEW `cbi-v14.curated.vw_weather_daily` AS
            SELECT * FROM `cbi-v14.curated.vw_dashboard_weather_intelligence`
        """,
        
        'vw_weather_global_daily': """
            CREATE OR REPLACE VIEW `cbi-v14.curated.vw_weather_global_daily` AS
            SELECT 
                date,
                AVG(CASE WHEN region = 'Brazil' THEN avg_temp END) as brazil_temp,
                AVG(CASE WHEN region = 'Argentina' THEN avg_temp END) as argentina_temp,
                AVG(CASE WHEN region = 'US Midwest' THEN avg_temp END) as us_temp,
                SUM(CASE WHEN region = 'Brazil' THEN total_precip END) as brazil_precip,
                SUM(CASE WHEN region = 'Argentina' THEN total_precip END) as argentina_precip,
                SUM(CASE WHEN region = 'US Midwest' THEN total_precip END) as us_precip
            FROM `cbi-v14.curated.vw_dashboard_weather_intelligence`
            GROUP BY date
            ORDER BY date DESC
        """,
        
        # Fix economic views
        'vw_fed_rates_realtime': """
            CREATE OR REPLACE VIEW `cbi-v14.curated.vw_fed_rates_realtime` AS
            SELECT 
                CAST(time AS DATE) as date,
                indicator,
                value as rate,
                source_name,
                confidence_score
            FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
            WHERE indicator IN ('fed_funds_rate', 'ten_year_treasury', 'two_year_treasury')
                AND CAST(time AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
                AND CAST(time AS DATE) <= CURRENT_DATE()  -- Fix future dates issue
            ORDER BY date DESC, indicator
        """,
        
        'vw_treasury_daily': """
            CREATE OR REPLACE VIEW `cbi-v14.curated.vw_treasury_daily` AS
            SELECT 
                CAST(time AS DATE) as date,
                MAX(CASE WHEN indicator = 'ten_year_treasury' THEN value END) as ten_year_yield,
                MAX(CASE WHEN indicator = 'two_year_treasury' THEN value END) as two_year_yield,
                MAX(CASE WHEN indicator = 'fed_funds_rate' THEN value END) as fed_funds_rate
            FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
            WHERE indicator IN ('fed_funds_rate', 'ten_year_treasury', 'two_year_treasury')
                AND CAST(time AS DATE) <= CURRENT_DATE()  -- Fix future dates
            GROUP BY date
            ORDER BY date DESC
        """,
        
        # Fix news/intelligence views
        'vw_news_intel_daily': """
            CREATE OR REPLACE VIEW `cbi-v14.curated.vw_news_intel_daily` AS
            SELECT 
                CAST(published AS DATE) as date,
                COUNT(*) as article_count,
                AVG(intelligence_score) as avg_sentiment,
                MAX(intelligence_score) as max_sentiment,
                MIN(intelligence_score) as min_sentiment,
                STRING_AGG(DISTINCT source, ', ' LIMIT 5) as top_sources
            FROM `cbi-v14.forecasting_data_warehouse.news_intelligence`
            WHERE published >= DATE_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
            GROUP BY date
            ORDER BY date DESC
        """,
        
        'vw_multi_source_intelligence_summary': """
            CREATE OR REPLACE VIEW `cbi-v14.curated.vw_multi_source_intelligence_summary` AS
            SELECT 
                CURRENT_DATE() as report_date,
                (SELECT COUNT(*) FROM `cbi-v14.forecasting_data_warehouse.news_intelligence` 
                 WHERE published >= DATE_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)) as weekly_news_count,
                (SELECT AVG(sentiment_score) FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
                 WHERE timestamp >= DATE_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)) as weekly_social_sentiment,
                (SELECT MAX(close) FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
                 WHERE time >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)) as weekly_high_price,
                (SELECT MIN(close) FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
                 WHERE time >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)) as weekly_low_price
        """,
        
        # Fix priority indicators view
        'vw_priority_indicators_daily': """
            CREATE OR REPLACE VIEW `cbi-v14.curated.vw_priority_indicators_daily` AS
            WITH latest_prices AS (
                SELECT 
                    CAST(time AS DATE) as date,
                    close as soybean_oil_price,
                    volume
                FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
                WHERE time >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            ),
            latest_weather AS (
                SELECT 
                    date,
                    AVG(temp_avg_c) as brazil_temp,
                    SUM(precip_mm) as brazil_precip
                FROM `cbi-v14.forecasting_data_warehouse.weather_brazil_daily`
                WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                GROUP BY date
            ),
            latest_sentiment AS (
                SELECT 
                    CAST(timestamp AS DATE) as date,
                    AVG(sentiment_score) as avg_sentiment
                FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
                WHERE timestamp >= DATE_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
                GROUP BY date
            )
            SELECT 
                p.date,
                p.soybean_oil_price,
                p.volume,
                w.brazil_temp,
                w.brazil_precip,
                s.avg_sentiment,
                -- Calculate 7-day moving average
                AVG(p.soybean_oil_price) OVER (ORDER BY p.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as ma_7d,
                -- Calculate daily return
                (p.soybean_oil_price - LAG(p.soybean_oil_price, 1) OVER (ORDER BY p.date)) / 
                    NULLIF(LAG(p.soybean_oil_price, 1) OVER (ORDER BY p.date), 0) * 100 as daily_return_pct
            FROM latest_prices p
            LEFT JOIN latest_weather w ON p.date = w.date
            LEFT JOIN latest_sentiment s ON p.date = s.date
            ORDER BY p.date DESC
        """
    }
    
    # Execute fixes
    fixed_count = 0
    failed_count = 0
    
    for view_name, create_sql in fixes.items():
        try:
            logger.info(f"Fixing view: {view_name}")
            query_job = client.query(create_sql)
            query_job.result()
            logger.info(f"✅ Fixed: {view_name}")
            fixed_count += 1
        except Exception as e:
            logger.error(f"❌ Failed to fix {view_name}: {str(e)[:200]}")
            failed_count += 1
    
    print(f"\n{'='*80}")
    print(f"VIEW REPAIR SUMMARY")
    print(f"{'='*80}")
    print(f"✅ Successfully fixed: {fixed_count} views")
    print(f"❌ Failed to fix: {failed_count} views")
    
    # Test the fixed views
    print(f"\n{'='*80}")
    print(f"TESTING FIXED VIEWS")
    print(f"{'='*80}")
    
    for view_name in fixes.keys():
        try:
            test_query = f"SELECT COUNT(*) as cnt FROM `cbi-v14.curated.{view_name}` LIMIT 1"
            result = client.query(test_query).to_dataframe()
            count = result['cnt'].iloc[0] if len(result) > 0 else 0
            status = "✅" if count > 0 else "⚠️"
            print(f"{status} {view_name}: {count:,} rows")
        except Exception as e:
            print(f"❌ {view_name}: Test failed - {str(e)[:60]}")

if __name__ == "__main__":
    fix_broken_views()
