#!/usr/bin/env python3
"""
Daily Data Pull and Migration Script
Pulls fresh data from various sources and migrates staging to main tables
"""

from google.cloud import bigquery
import requests
import pandas as pd
from datetime import datetime, timedelta
import logging
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client()

def pull_trump_social_data():
    """Pull fresh Trump and social data for today"""
    logger.info("Pulling fresh Trump/social data...")
    
    # This would integrate with scrapecreator.com API
    # For now, showing the structure
    
    try:
        # Example structure for scrapecreator.com integration
        # api_key = os.environ.get('SCRAPECREATOR_API_KEY')
        # response = requests.get(
        #     'https://api.scrapecreator.com/v1/scrape',
        #     params={
        #         'query': 'Trump tariff China soybean agriculture',
        #         'sources': ['twitter', 'reddit', 'news'],
        #         'date': datetime.now().strftime('%Y-%m-%d')
        #     },
        #     headers={'Authorization': f'Bearer {api_key}'}
        # )
        
        logger.info("Would pull from scrapecreator.com here")
        # Process and save to staging
        
    except Exception as e:
        logger.error(f"Error pulling social data: {e}")

def migrate_staging_to_main():
    """Migrate all staging data to main tables"""
    logger.info("Starting staging to main migration...")
    
    migrations = [
        {
            'name': 'CFTC COT Data',
            'source': 'staging.cftc_cot',
            'target': 'forecasting_data_warehouse.cftc_cot',
            'check_query': '''
                SELECT COUNT(*) as staging_count 
                FROM `cbi-v14.staging.cftc_cot`
            ''',
            'migrate_query': '''
                INSERT INTO `cbi-v14.forecasting_data_warehouse.cftc_cot`
                SELECT * FROM `cbi-v14.staging.cftc_cot`
                WHERE report_date NOT IN (
                    SELECT DISTINCT report_date 
                    FROM `cbi-v14.forecasting_data_warehouse.cftc_cot`
                )
            '''
        },
        {
            'name': 'Trump Policy Intelligence',
            'source': 'staging.trump_policy_intelligence',
            'target': 'forecasting_data_warehouse.trump_policy_intelligence',
            'check_query': '''
                SELECT COUNT(*) as staging_count 
                FROM `cbi-v14.staging.trump_policy_intelligence`
            ''',
            'migrate_query': '''
                INSERT INTO `cbi-v14.forecasting_data_warehouse.trump_policy_intelligence`
                SELECT * FROM `cbi-v14.staging.trump_policy_intelligence`
                WHERE provenance_uuid NOT IN (
                    SELECT DISTINCT provenance_uuid 
                    FROM `cbi-v14.forecasting_data_warehouse.trump_policy_intelligence`
                    WHERE provenance_uuid IS NOT NULL
                )
            '''
        },
        {
            'name': 'Social Intelligence',
            'source': 'staging.comprehensive_social_intelligence',
            'target': 'forecasting_data_warehouse.social_sentiment',
            'check_query': '''
                SELECT COUNT(*) as staging_count 
                FROM `cbi-v14.staging.comprehensive_social_intelligence`
            ''',
            'migrate_query': '''
                INSERT INTO `cbi-v14.forecasting_data_warehouse.social_sentiment`
                SELECT 
                    platform,
                    handle as subreddit,
                    content as title,
                    CAST(likes AS INT64) as score,
                    CAST(replies AS INT64) as comments,
                    (soy_score + china_score + policy_score + urgency_score + biofuel_score + weather_score) / 6.0 as sentiment_score,
                    PARSE_TIMESTAMP('%a %b %d %H:%M:%S %z %Y', created_at) as timestamp,
                    CASE 
                        WHEN total_relevance > 0.7 THEN 'high'
                        WHEN total_relevance > 0.4 THEN 'medium'
                        ELSE 'low'
                    END as market_relevance,
                    source_name,
                    confidence_score,
                    ingest_timestamp_utc,
                    provenance_uuid
                FROM `cbi-v14.staging.comprehensive_social_intelligence`
                WHERE provenance_uuid NOT IN (
                    SELECT DISTINCT provenance_uuid 
                    FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
                    WHERE provenance_uuid IS NOT NULL
                )
            '''
        }
    ]
    
    for migration in migrations:
        try:
            # Check if there's data to migrate
            check_result = client.query(migration['check_query']).to_dataframe()
            staging_count = check_result.iloc[0]['staging_count']
            
            if staging_count > 0:
                logger.info(f"Migrating {migration['name']}: {staging_count} rows in staging")
                
                # Perform migration
                job = client.query(migration['migrate_query'])
                job.result()
                
                # Verify migration
                verify_query = f"SELECT COUNT(*) as cnt FROM `cbi-v14.{migration['target']}`"
                result = client.query(verify_query).to_dataframe()
                logger.info(f"✅ {migration['name']}: Now {result.iloc[0]['cnt']} total rows in main table")
            else:
                logger.info(f"ℹ️ {migration['name']}: No new data to migrate")
                
        except Exception as e:
            logger.error(f"❌ Error migrating {migration['name']}: {e}")

def setup_daily_schedules():
    """Setup scheduled queries for daily data pulls"""
    logger.info("Setting up daily scheduled queries...")
    
    schedules = [
        {
            'name': 'daily_weather_update',
            'schedule': '0 6 * * *',  # 6 AM daily
            'query': '''
                -- This would be a scheduled query to pull weather data
                -- Can integrate with Open-Meteo or other weather APIs
                SELECT CURRENT_TIMESTAMP() as run_time
            '''
        },
        {
            'name': 'daily_price_update',
            'schedule': '30 16 * * 1-5',  # 4:30 PM weekdays (after market close)
            'query': '''
                -- This would pull end-of-day price data
                SELECT CURRENT_TIMESTAMP() as run_time
            '''
        },
        {
            'name': 'daily_social_sentiment',
            'schedule': '0 */4 * * *',  # Every 4 hours
            'query': '''
                -- This would aggregate social sentiment
                SELECT CURRENT_TIMESTAMP() as run_time
            '''
        }
    ]
    
    logger.info("Schedule templates created (would be implemented in BigQuery Scheduled Queries)")
    for schedule in schedules:
        logger.info(f"  - {schedule['name']}: {schedule['schedule']}")

def verify_system_readiness():
    """Final verification of system readiness for training"""
    logger.info("\n" + "="*80)
    logger.info("SYSTEM READINESS VERIFICATION")
    logger.info("="*80)
    
    checks = [
        ('Soybean Oil Prices', 'SELECT COUNT(*) as cnt FROM `cbi-v14.raw_intelligence.commodity_soybean_oil_prices`'),
        ('Trump Policy Data', 'SELECT COUNT(*) as cnt FROM `cbi-v14.forecasting_data_warehouse.trump_policy_intelligence`'),
        ('Social Sentiment', 'SELECT COUNT(*) as cnt FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`'),
        ('CFTC COT Data', 'SELECT COUNT(*) as cnt FROM `cbi-v14.forecasting_data_warehouse.cftc_cot`'),
        ('Training Data', 'SELECT COUNT(*) as cnt FROM `cbi-v14.models.vw_big7_training_data`'),
        ('Signal Universe', 'SELECT COUNT(*) as cnt FROM `cbi-v14.signals.vw_comprehensive_signal_universe` WHERE signal_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)')
    ]
    
    all_ready = True
    for name, query in checks:
        try:
            result = client.query(query).to_dataframe()
            count = result.iloc[0]['cnt']
            status = '✅' if count > 0 else '❌'
            logger.info(f"{status} {name}: {count:,} rows")
            if count == 0:
                all_ready = False
        except Exception as e:
            logger.error(f"❌ {name}: Error - {e}")
            all_ready = False
    
    if all_ready:
        logger.info("\n✅ SYSTEM IS READY FOR TRAINING!")
    else:
        logger.info("\n⚠️ Some components need attention before training")
    
    return all_ready

if __name__ == "__main__":
    logger.info("Starting daily data pull and migration process...")
    
    # 1. Pull fresh data
    pull_trump_social_data()
    
    # 2. Migrate staging to main
    migrate_staging_to_main()
    
    # 3. Setup schedules (informational)
    setup_daily_schedules()
    
    # 4. Verify system readiness
    is_ready = verify_system_readiness()
    
    logger.info("\n" + "="*80)
    if is_ready:
        logger.info("✅ DAILY PROCESS COMPLETE - SYSTEM READY FOR TRAINING")
    else:
        logger.info("⚠️ DAILY PROCESS COMPLETE - CHECK LOGS FOR ISSUES")
    logger.info("="*80)
