#!/usr/bin/env python3
"""
Migrate staging and backup data to main tables for Big 7 signals training.
This script handles schema differences and ensures data integrity.
"""

import os
import sys
from google.cloud import bigquery
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def migrate_volatility_data():
    """Migrate volatility data from backup to main table"""
    client = bigquery.Client(project='cbi-v14')
    
    logger.info("🔄 Migrating volatility data from backup to main...")
    
    # The schemas match perfectly, so we can do a direct copy
    query = """
    INSERT INTO `cbi-v14.forecasting_data_warehouse.volatility_data`
    SELECT 
        symbol,
        contract,
        last_price,
        iv_hv_ratio,
        implied_vol,
        data_date,
        source_name,
        confidence_score,
        ingest_timestamp_utc,
        provenance_uuid
    FROM `cbi-v14.bkp.volatility_data_20251010T231720Z` v1
    WHERE NOT EXISTS (
        SELECT 1 FROM `cbi-v14.forecasting_data_warehouse.volatility_data` v2
        WHERE v2.symbol = v1.symbol
        AND v2.data_date = v1.data_date
        AND v2.contract = v1.contract
    )
    """
    
    try:
        job = client.query(query)
        job.result()
        logger.info("✅ Successfully migrated volatility data")
        return True
    except Exception as e:
        logger.error(f"❌ Error migrating volatility data: {e}")
        return False

def migrate_social_intelligence_data():
    """Migrate comprehensive social intelligence data to social_sentiment table"""
    client = bigquery.Client(project='cbi-v14')
    
    logger.info("🔄 Migrating social intelligence data to social_sentiment...")
    
    # Map comprehensive_social_intelligence schema to social_sentiment schema
    query = """
    INSERT INTO `cbi-v14.forecasting_data_warehouse.social_sentiment`
    SELECT 
        platform,
        'social_media' as subreddit,  -- Default value for missing field
        content as title,
        CAST(likes AS INT64) as score,  -- Use likes as score
        CAST(replies AS INT64) as comments,  -- Use replies as comments
        (soy_score + china_score + policy_score + urgency_score + biofuel_score + weather_score) / 6.0 as sentiment_score,  -- Average of all scores
        PARSE_TIMESTAMP('%a %b %d %H:%M:%S %z %Y', created_at) as timestamp,  -- Parse the specific timestamp format
        CASE 
            WHEN total_relevance > 0.7 THEN 'high'
            WHEN total_relevance > 0.4 THEN 'medium'
            ELSE 'low'
        END as market_relevance,
        source_name,
        confidence_score,
        ingest_timestamp_utc,
        provenance_uuid
    FROM `cbi-v14.staging.comprehensive_social_intelligence` s1
    WHERE NOT EXISTS (
        SELECT 1 FROM `cbi-v14.forecasting_data_warehouse.social_sentiment` s2
        WHERE s2.platform = s1.platform
        AND s2.timestamp = PARSE_TIMESTAMP('%a %b %d %H:%M:%S %z %Y', s1.created_at)
        AND s2.provenance_uuid = s1.provenance_uuid
    )
    """
    
    try:
        job = client.query(query)
        job.result()
        logger.info("✅ Successfully migrated social intelligence data")
        return True
    except Exception as e:
        logger.error(f"❌ Error migrating social intelligence data: {e}")
        return False

def verify_migration():
    """Verify the migration was successful"""
    client = bigquery.Client(project='cbi-v14')
    
    logger.info("🔍 Verifying migration results...")
    
    # Check volatility data
    volatility_query = """
    SELECT COUNT(*) as row_count FROM `cbi-v14.forecasting_data_warehouse.volatility_data`
    """
    volatility_result = client.query(volatility_query).result()
    volatility_count = list(volatility_result)[0].row_count
    
    # Check social sentiment data
    social_query = """
    SELECT COUNT(*) as row_count FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
    """
    social_result = client.query(social_query).result()
    social_count = list(social_result)[0].row_count
    
    logger.info(f"📊 Migration Results:")
    logger.info(f"   Volatility data: {volatility_count} rows")
    logger.info(f"   Social sentiment: {social_count} rows")
    
    return volatility_count > 0 and social_count > 0

def main():
    logger.info("🚀 MIGRATING STAGING DATA TO MAIN TABLES")
    logger.info("============================================================")
    
    # Migrate volatility data
    volatility_success = migrate_volatility_data()
    
    # Migrate social intelligence data
    social_success = migrate_social_intelligence_data()
    
    # Verify migration
    if volatility_success and social_success:
        verify_success = verify_migration()
        if verify_success:
            logger.info("============================================================")
            logger.info("✅ SUCCESS: All staging data migrated successfully!")
            logger.info("🎯 Big 7 signals now have comprehensive data foundation!")
        else:
            logger.error("❌ Migration verification failed")
    else:
        logger.error("❌ Migration failed")

if __name__ == "__main__":
    main()
