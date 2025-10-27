#!/usr/bin/env python3
"""
Create Data Validation Pipeline
Continuous monitoring of data quality to protect our models
"""

from google.cloud import bigquery
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

def create_data_validation_view():
    """
    Create comprehensive data validation view
    Monitors staleness, anomalies, completeness, and quality
    """
    
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.models.vw_data_quality_checks` AS
    WITH soybean_oil_checks AS (
        SELECT 
            'soybean_oil_prices' as table_name,
            COUNT(*) as row_count,
            COUNT(DISTINCT DATE(time)) as unique_days,
            MAX(DATE(time)) as latest_date,
            DATE_DIFF(CURRENT_DATE(), MAX(DATE(time)), DAY) as days_stale,
            COUNT(DISTINCT symbol) as symbol_count,
            COUNTIF(close IS NULL) as null_prices,
            COUNTIF(close <= 0) as invalid_prices,
            MAX(ABS((close - LAG(close) OVER (ORDER BY time)) / 
                NULLIF(LAG(close) OVER (ORDER BY time), 0))) as max_daily_change,
            COUNT(DISTINCT DATE(time)) - COUNT(DISTINCT CASE WHEN symbol = 'ZL' THEN DATE(time) END) as contaminated_days
        FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
    ),
    crude_oil_checks AS (
        SELECT 
            'crude_oil_prices' as table_name,
            COUNT(*) as row_count,
            COUNT(DISTINCT date) as unique_days,
            MAX(date) as latest_date,
            DATE_DIFF(CURRENT_DATE(), MAX(date), DAY) as days_stale,
            COUNT(DISTINCT symbol) as symbol_count,
            COUNTIF(close_price IS NULL) as null_prices,
            COUNTIF(close_price <= 0) as invalid_prices,
            MAX(ABS((close_price - LAG(close_price) OVER (ORDER BY date)) / 
                NULLIF(LAG(close_price) OVER (ORDER BY date), 0))) as max_daily_change,
            0 as contaminated_days
        FROM `cbi-v14.forecasting_data_warehouse.crude_oil_prices`
    ),
    social_sentiment_checks AS (
        SELECT 
            'social_sentiment' as table_name,
            COUNT(*) as row_count,
            COUNT(DISTINCT DATE(timestamp)) as unique_days,
            MAX(DATE(timestamp)) as latest_date,
            DATE_DIFF(CURRENT_DATE(), MAX(DATE(timestamp)), DAY) as days_stale,
            1 as symbol_count,  -- Not applicable
            COUNTIF(sentiment_score IS NULL) as null_prices,
            COUNTIF(sentiment_score < 0 OR sentiment_score > 1) as invalid_prices,
            0 as max_daily_change,  -- Not applicable
            0 as contaminated_days
        FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
    ),
    weather_checks AS (
        SELECT 
            'weather_data' as table_name,
            COUNT(*) as row_count,
            COUNT(DISTINCT date) as unique_days,
            MAX(date) as latest_date,
            DATE_DIFF(CURRENT_DATE(), MAX(date), DAY) as days_stale,
            COUNT(DISTINCT station_id) as symbol_count,  -- Stations instead of symbols
            COUNTIF(temp_max IS NULL AND precip_mm IS NULL) as null_prices,
            COUNTIF(temp_max < -50 OR temp_max > 60) as invalid_prices,  -- Reasonable temp range
            0 as max_daily_change,
            0 as contaminated_days
        FROM `cbi-v14.forecasting_data_warehouse.weather_data`
    ),
    cftc_checks AS (
        SELECT 
            'cftc_cot' as table_name,
            COUNT(*) as row_count,
            COUNT(DISTINCT report_date) as unique_days,
            MAX(report_date) as latest_date,
            DATE_DIFF(CURRENT_DATE(), MAX(report_date), DAY) as days_stale,
            COUNT(DISTINCT commodity) as symbol_count,
            COUNTIF(open_interest IS NULL) as null_prices,
            COUNTIF(open_interest <= 0) as invalid_prices,
            0 as max_daily_change,
            COUNTIF(managed_money_long = 0 AND managed_money_short = 0) as contaminated_days  -- Suspicious zeros
        FROM `cbi-v14.forecasting_data_warehouse.cftc_cot`
    ),
    vix_checks AS (
        SELECT 
            'vix_daily' as table_name,
            COUNT(*) as row_count,
            COUNT(DISTINCT date) as unique_days,
            MAX(date) as latest_date,
            DATE_DIFF(CURRENT_DATE(), MAX(date), DAY) as days_stale,
            1 as symbol_count,
            COUNTIF(close IS NULL) as null_prices,
            COUNTIF(close <= 0 OR close > 100) as invalid_prices,  -- VIX range
            MAX(ABS((close - LAG(close) OVER (ORDER BY date)) / 
                NULLIF(LAG(close) OVER (ORDER BY date), 0))) as max_daily_change,
            0 as contaminated_days
        FROM `cbi-v14.forecasting_data_warehouse.vix_daily`
    ),
    palm_oil_checks AS (
        SELECT 
            'palm_oil_prices' as table_name,
            COUNT(*) as row_count,
            COUNT(DISTINCT DATE(time)) as unique_days,
            MAX(DATE(time)) as latest_date,
            DATE_DIFF(CURRENT_DATE(), MAX(DATE(time)), DAY) as days_stale,
            COUNT(DISTINCT symbol) as symbol_count,
            COUNTIF(close_price IS NULL) as null_prices,
            COUNTIF(close_price <= 0) as invalid_prices,
            MAX(ABS((close_price - LAG(close_price) OVER (ORDER BY time)) / 
                NULLIF(LAG(close_price) OVER (ORDER BY time), 0))) as max_daily_change,
            0 as contaminated_days
        FROM `cbi-v14.forecasting_data_warehouse.palm_oil_prices`
    ),
    all_checks AS (
        SELECT * FROM soybean_oil_checks
        UNION ALL SELECT * FROM crude_oil_checks
        UNION ALL SELECT * FROM social_sentiment_checks
        UNION ALL SELECT * FROM weather_checks
        UNION ALL SELECT * FROM cftc_checks
        UNION ALL SELECT * FROM vix_checks
        UNION ALL SELECT * FROM palm_oil_checks
    )
    SELECT 
        *,
        CASE 
            WHEN days_stale > 7 THEN 'CRITICAL_STALE'
            WHEN days_stale > 3 THEN 'STALE_DATA'
            WHEN symbol_count > 1 AND table_name LIKE '%prices' THEN 'CONTAMINATION'
            WHEN null_prices > row_count * 0.05 THEN 'NULL_VALUES'
            WHEN invalid_prices > 0 THEN 'INVALID_PRICES'
            WHEN max_daily_change > 0.30 THEN 'ANOMALY_DETECTED'
            WHEN contaminated_days > 0 THEN 'DATA_QUALITY_ISSUE'
            WHEN days_stale <= 1 THEN 'HEALTHY'
            ELSE 'CHECK_NEEDED'
        END as status,
        
        CASE 
            WHEN days_stale > 7 THEN 1  -- Critical
            WHEN days_stale > 3 THEN 2  -- Warning
            WHEN contaminated_days > 0 THEN 2  -- Warning
            WHEN null_prices > row_count * 0.05 THEN 2  -- Warning
            ELSE 3  -- OK
        END as priority,
        
        CURRENT_TIMESTAMP() as check_timestamp
        
    FROM all_checks
    ORDER BY priority, days_stale DESC
    """
    
    try:
        client.query(query).result()
        logger.info("✅ Created monitoring.vw_data_quality_checks successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create data validation view: {e}")
        return False

def create_anomaly_detection_view():
    """
    Create anomaly detection view for price movements
    Flags suspicious patterns that need investigation
    """
    
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.models.vw_price_anomalies` AS
    WITH price_stats AS (
        SELECT 
            DATE(time) as date,
            close as price,
            symbol,
            
            -- Calculate returns
            (close - LAG(close, 1) OVER (PARTITION BY symbol ORDER BY time)) / 
             NULLIF(LAG(close, 1) OVER (PARTITION BY symbol ORDER BY time), 0) as daily_return,
            
            -- Rolling statistics
            AVG(close) OVER (
                PARTITION BY symbol ORDER BY time 
                ROWS BETWEEN 29 PRECEDING AND 1 PRECEDING
            ) as ma_30d,
            
            STDDEV(close) OVER (
                PARTITION BY symbol ORDER BY time 
                ROWS BETWEEN 29 PRECEDING AND 1 PRECEDING
            ) as stddev_30d,
            
            -- Volume analysis
            volume,
            AVG(volume) OVER (
                PARTITION BY symbol ORDER BY time 
                ROWS BETWEEN 29 PRECEDING AND 1 PRECEDING
            ) as avg_volume_30d
            
        FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
        WHERE symbol = 'ZL'
    )
    SELECT 
        date,
        symbol,
        price,
        daily_return,
        
        -- Z-score for price
        (price - ma_30d) / NULLIF(stddev_30d, 0) as price_zscore,
        
        -- Volume spike detection
        volume / NULLIF(avg_volume_30d, 0) as volume_ratio,
        
        -- Anomaly flags
        CASE 
            WHEN ABS(daily_return) > 0.10 THEN 'EXTREME_MOVE'
            WHEN ABS((price - ma_30d) / NULLIF(stddev_30d, 0)) > 3 THEN 'THREE_SIGMA_EVENT'
            WHEN volume > avg_volume_30d * 3 THEN 'VOLUME_SPIKE'
            WHEN daily_return > 0.05 AND volume > avg_volume_30d * 2 THEN 'BREAKOUT'
            WHEN daily_return < -0.05 AND volume > avg_volume_30d * 2 THEN 'BREAKDOWN'
            ELSE 'NORMAL'
        END as anomaly_type,
        
        -- Severity score
        GREATEST(
            ABS(daily_return) * 10,  -- Return component
            ABS((price - ma_30d) / NULLIF(stddev_30d, 0)),  -- Z-score component
            LOG(volume / NULLIF(avg_volume_30d, 0) + 1)  -- Volume component
        ) as anomaly_severity
        
    FROM price_stats
    WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
    ORDER BY date DESC
    """
    
    try:
        client.query(query).result()
        logger.info("✅ Created monitoring.vw_price_anomalies successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create anomaly detection view: {e}")
        return False

def run_validation_checks():
    """Run validation checks and report issues"""
    
    # Check data quality
    quality_query = """
    SELECT 
        table_name,
        status,
        days_stale,
        row_count,
        null_prices,
        contaminated_days
    FROM `cbi-v14.models.vw_data_quality_checks`
    WHERE status != 'HEALTHY'
    ORDER BY priority
    """
    
    print("\n" + "=" * 80)
    print("DATA QUALITY ISSUES DETECTED")
    print("=" * 80)
    
    try:
        result = client.query(quality_query).result()
        issues = list(result)
        
        if issues:
            for row in issues:
                print(f"\n❌ {row.table_name}:")
                print(f"   Status: {row.status}")
                print(f"   Days stale: {row.days_stale}")
                print(f"   Rows: {row.row_count}")
                if row.null_prices > 0:
                    print(f"   NULL values: {row.null_prices}")
                if row.contaminated_days > 0:
                    print(f"   Contaminated days: {row.contaminated_days}")
        else:
            print("✅ All data sources healthy!")
            
    except Exception as e:
        print(f"Error running quality checks: {e}")
    
    # Check recent anomalies
    anomaly_query = """
    SELECT 
        date,
        symbol,
        price,
        daily_return,
        anomaly_type,
        anomaly_severity
    FROM `cbi-v14.models.vw_price_anomalies`
    WHERE anomaly_type != 'NORMAL'
    AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    ORDER BY anomaly_severity DESC
    LIMIT 5
    """
    
    print("\n" + "=" * 80)
    print("RECENT PRICE ANOMALIES (Last 7 Days)")
    print("=" * 80)
    
    try:
        result = client.query(anomaly_query).result()
        anomalies = list(result)
        
        if anomalies:
            for row in anomalies:
                print(f"\n⚠️ {row.date} - {row.anomaly_type}:")
                print(f"   Price: ${row.price:.2f}")
                print(f"   Daily return: {row.daily_return*100:.2f}%")
                print(f"   Severity: {row.anomaly_severity:.2f}")
        else:
            print("✅ No significant anomalies detected")
            
    except Exception as e:
        print(f"Error checking anomalies: {e}")

def main():
    """Create data validation pipeline"""
    print("=" * 80)
    print("CREATING DATA VALIDATION PIPELINE")
    print("=" * 80)
    print("\nThis monitors:")
    print("  • Data freshness (staleness)")
    print("  • Data quality (nulls, invalid values)")
    print("  • Data contamination (wrong symbols)")
    print("  • Price anomalies (extreme moves)")
    print("  • Volume spikes")
    
    # Create validation views
    print("\n1. Creating data quality checks view...")
    success1 = create_data_validation_view()
    
    print("\n2. Creating anomaly detection view...")
    success2 = create_anomaly_detection_view()
    
    if success1 and success2:
        print("\n3. Running validation checks...")
        run_validation_checks()
        
        print("\n" + "=" * 80)
        print("✅ DATA VALIDATION PIPELINE COMPLETE")
        print("=" * 80)
        print("\nMonitoring views created:")
        print("  • models.vw_data_quality_checks")
        print("  • models.vw_price_anomalies")
        print("\nRun validation checks daily to ensure data quality!")
    else:
        print("\n❌ Failed to create validation pipeline")
    
    return success1 and success2

if __name__ == "__main__":
    main()
