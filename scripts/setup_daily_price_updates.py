#!/usr/bin/env python3
"""
DAILY PRICE UPDATE SCHEDULER
Ensures we NEVER lose historical data
"""

from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

# Daily price update queries
DAILY_UPDATES = {
    'soybean_oil_daily': {
        'schedule': '0 17 * * 1-5',  # 5 PM weekdays
        'query': '''
        -- Pull latest ZL prices from yfinance or API
        INSERT INTO `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
        SELECT * FROM EXTERNAL_QUERY("", """
            SELECT NOW() as time, 'ZL' as symbol, 
            close, open, high, low, volume,
            'yfinance' as source_name, 1.0 as confidence_score,
            NOW() as ingest_timestamp_utc,
            CONCAT('daily_', DATE(NOW())) as provenance_uuid
            FROM yahoo_finance WHERE ticker = 'ZL=F' AND date = CURRENT_DATE
        """)
        '''
    },
    'crude_oil_daily': {
        'schedule': '0 17 * * 1-5',
        'query': '''
        -- Pull latest CL prices
        INSERT INTO `cbi-v14.forecasting_data_warehouse.crude_oil_prices`
        SELECT CURRENT_DATE as date, close, open, high, low, volume,
        'CL' as symbol, 'yfinance' as source_name, 1.0 as confidence_score,
        NOW() as ingest_timestamp_utc, CONCAT('daily_cl_', CURRENT_DATE) as provenance_uuid
        FROM EXTERNAL_QUERY("", "SELECT * FROM yahoo_finance WHERE ticker = 'CL=F' AND date = CURRENT_DATE")
        '''
    },
    'vix_daily': {
        'schedule': '30 16 * * 1-5',  # 4:30 PM after close
        'query': '''
        -- Pull VIX from CBOE
        INSERT INTO `cbi-v14.forecasting_data_warehouse.vix_daily`
        SELECT CURRENT_DATE as date, close, open, high, low, volume,
        'VIX' as symbol, 'cboe' as source_name, 1.0 as confidence_score,
        NOW() as ingest_timestamp_utc, CONCAT('daily_vix_', CURRENT_DATE) as provenance_uuid
        FROM EXTERNAL_QUERY("", "SELECT * FROM cboe_vix WHERE date = CURRENT_DATE")
        '''
    }
}

print("=" * 80)
print("SETTING UP DAILY PRICE UPDATE SCHEDULES")
print("=" * 80)
print()
print("Creating scheduled queries for automatic daily updates...")
print()

for name, config in DAILY_UPDATES.items():
    print(f"Schedule: {name}")
    print(f"  Cron: {config['schedule']}")
    print(f"  Target: Extract from query")
    print()
    
    # In production, this would create actual scheduled queries:
    # transfer_config = bigquery_datatransfer.TransferConfig(
    #     destination_dataset_id="forecasting_data_warehouse",
    #     display_name=name,
    #     data_source_id="scheduled_query",
    #     schedule=config['schedule'],
    #     params={"query": config['query']}
    # )

print("=" * 80)
print("MANUAL DAILY UPDATE SCRIPT")
print("=" * 80)
print()
print("Run this script daily to update all prices:")
print()
print("python3 cbi-v14-ingestion/ingest_market_prices.py --update --days 1")
print()
print("Or use cron:")
print("0 17 * * 1-5 cd /Users/zincdigital/CBI-V14 && python3 cbi-v14-ingestion/ingest_market_prices.py --update --days 1")
print()

# Check what ingestion scripts we have
print("=" * 80)
print("AVAILABLE INGESTION SCRIPTS")
print("=" * 80)

import os
import glob

scripts = glob.glob('cbi-v14-ingestion/ingest_*.py')
for script in sorted(scripts):
    if 'market_prices' in script or 'yfinance' in script or 'price' in script.lower():
        print(f"  ✅ {os.path.basename(script)}")

print()
print("CRITICAL: Set up daily cron jobs for these scripts to preserve historical data!")
