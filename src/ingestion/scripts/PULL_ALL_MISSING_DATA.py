#!/usr/bin/env python3
"""
COMPREHENSIVE MISSING DATA PULL
Pulls all missing/stale data identified in DATA_INGESTION_PIPELINE_AUDIT.md
Uses standardized parsing, routing, and deduplication per DEEP_PARSING_SCHEMA_CALCULATION_AUDIT.md

CRITICAL DATA SOURCES:
1. Production Training Data (56 days stale - Sep 10, 2025)
2. China Imports (21 days stale - Oct 15, 2025)
3. RIN Prices (unknown freshness)
4. Trump Sentiment Quantification (raw data exists, needs processing)
5. Big Eight Signals (verify freshness)
"""

import os
import sys
import subprocess
import time
from datetime import datetime, timedelta
from google.cloud import bigquery
import pandas as pd
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ID = 'cbi-v14'
client = bigquery.Client(project=PROJECT_ID)

def check_data_freshness(table_path, date_column='date'):
    """Check how fresh data is in a table"""
    try:
        # Handle both DATE and TIMESTAMP columns
        query = f"""
        SELECT 
            MAX({date_column}) as latest_date,
            COUNT(*) as row_count,
            DATE_DIFF(CURRENT_DATE(), DATE(MAX({date_column})), DAY) as days_old
        FROM `{table_path}`
        WHERE {date_column} IS NOT NULL
        """
        result = client.query(query).to_dataframe()
        if not result.empty and result.iloc[0]['latest_date']:
            return {
                'latest_date': result.iloc[0]['latest_date'],
                'row_count': result.iloc[0]['row_count'],
                'days_old': result.iloc[0]['days_old']
            }
    except Exception as e:
        logger.error(f"Error checking {table_path}: {e}")
    return None

def run_script(script_path, description, timeout=600):
    """Run a data ingestion script with error handling"""
    logger.info(f"\n🚀 RUNNING: {description}")
    logger.info(f"📁 Script: {script_path}")
    
    if not os.path.exists(script_path):
        logger.warning(f"⚠️  Script not found: {script_path}")
        return False
    
    try:
        result = subprocess.run([
            'python3', script_path
        ], capture_output=True, text=True, timeout=timeout)
        
        if result.returncode == 0:
            logger.info(f"✅ SUCCESS: {description}")
            if result.stdout:
                logger.info(f"📊 Output: {result.stdout.strip()[:200]}")
            return True
        else:
            logger.error(f"❌ ERROR: {description}")
            if result.stderr:
                logger.error(f"🔍 Error: {result.stderr.strip()[:500]}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"⏰ TIMEOUT: {description} ({timeout}s)")
        return False
    except Exception as e:
        logger.error(f"💥 EXCEPTION: {description} - {e}")
        return False

def main():
    """Pull all missing/stale data"""
    logger.info("=" * 100)
    logger.info("🚀 COMPREHENSIVE MISSING DATA PULL")
    logger.info("=" * 100)
    logger.info(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Change to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    # Check current data freshness
    logger.info("\n📊 CHECKING CURRENT DATA FRESHNESS...")
    
    freshness_checks = [
        ('cbi-v14.models_v4.production_training_data_1m', 'date', 'Production Training Data (1M)'),
        ('cbi-v14.forecasting_data_warehouse.china_soybean_imports', 'date', 'China Imports'),
        ('cbi-v14.forecasting_data_warehouse.biofuel_prices', 'date', 'RIN Prices'),
        ('cbi-v14.forecasting_data_warehouse.trump_policy_intelligence', 'timestamp', 'Trump Policy Intelligence'),
        ('cbi-v14.neural.vw_big_eight_signals', 'date', 'Big Eight Signals'),
    ]
    
    freshness_report = {}
    for table_path, date_col, name in freshness_checks:
        freshness = check_data_freshness(table_path, date_col)
        if freshness:
            freshness_report[name] = freshness
            status = "🟢" if freshness['days_old'] <= 7 else "🟡" if freshness['days_old'] <= 30 else "🔴"
            logger.info(f"{status} {name}: {freshness['days_old']} days old (latest: {freshness['latest_date']}, rows: {freshness['row_count']:,})")
        else:
            logger.warning(f"⚠️  {name}: Could not check freshness")
    
    # Define critical data pulls
    critical_pulls = [
        # P0 - CRITICAL (Must fix immediately)
        {
            'script': 'scripts/update_production_datasets.py',
            'description': 'PRODUCTION TRAINING DATA REFRESH (56 days stale!)',
            'priority': 'P0',
            'timeout': 1800  # 30 minutes
        },
        {
            'script': 'ingestion/ingest_china_imports_uncomtrade.py',
            'description': 'CHINA IMPORTS DATA (21 days stale)',
            'priority': 'P0',
            'timeout': 600
        },
        {
            'script': 'ingestion/ingest_epa_rin_prices.py',
            'description': 'RIN PRICES DATA (Critical for features #23-30)',
            'priority': 'P0',
            'timeout': 600
        },
        
        # P1 - HIGH PRIORITY
        {
            'script': 'scripts/TRUMP_SENTIMENT_QUANT_ENGINE.py',
            'description': 'TRUMP SENTIMENT QUANTIFICATION (Process raw data)',
            'priority': 'P1',
            'timeout': 600
        },
        {
            'script': 'scripts/collect_neural_data_sources.py',
            'description': 'BIG EIGHT NEURAL SIGNALS (Verify freshness)',
            'priority': 'P1',
            'timeout': 600
        },
        
        # P2 - MEDIUM PRIORITY (Additional missing data)
        {
            'script': 'ingestion/ingest_usda_harvest_real.py',
            'description': 'USDA HARVEST DATA',
            'priority': 'P2',
            'timeout': 600
        },
        {
            'script': 'ingestion/ingest_epa_rfs_mandates.py',
            'description': 'EPA RFS MANDATES',
            'priority': 'P2',
            'timeout': 600
        },
        {
            'script': 'ingestion/ingest_volatility.py',
            'description': 'VOLATILITY DATA (VIX)',
            'priority': 'P2',
            'timeout': 300
        },
        {
            'script': 'ingestion/multi_source_news.py',
            'description': 'MULTI-SOURCE NEWS INTELLIGENCE',
            'priority': 'P2',
            'timeout': 600
        },
    ]
    
    # Group by priority
    p0_pulls = [p for p in critical_pulls if p['priority'] == 'P0']
    p1_pulls = [p for p in critical_pulls if p['priority'] == 'P1']
    p2_pulls = [p for p in critical_pulls if p['priority'] == 'P2']
    
    success_count = 0
    total_pulls = len(critical_pulls)
    
    logger.info(f"\n🎯 RUNNING {total_pulls} DATA PULLS...")
    logger.info(f"   P0 (Critical): {len(p0_pulls)}")
    logger.info(f"   P1 (High): {len(p1_pulls)}")
    logger.info(f"   P2 (Medium): {len(p2_pulls)}")
    logger.info("=" * 100)
    
    # Execute P0 pulls first
    logger.info("\n🔥 P0 - CRITICAL DATA PULLS")
    logger.info("=" * 100)
    for i, pull in enumerate(p0_pulls, 1):
        logger.info(f"\n📊 PROGRESS: {i}/{len(p0_pulls)} (P0)")
        success = run_script(pull['script'], pull['description'], pull['timeout'])
        if success:
            success_count += 1
        time.sleep(5)  # Delay between pulls
    
    # Execute P1 pulls
    logger.info("\n⚡ P1 - HIGH PRIORITY DATA PULLS")
    logger.info("=" * 100)
    for i, pull in enumerate(p1_pulls, 1):
        logger.info(f"\n📊 PROGRESS: {i}/{len(p1_pulls)} (P1)")
        success = run_script(pull['script'], pull['description'], pull['timeout'])
        if success:
            success_count += 1
        time.sleep(3)
    
    # Execute P2 pulls
    logger.info("\n📋 P2 - MEDIUM PRIORITY DATA PULLS")
    logger.info("=" * 100)
    for i, pull in enumerate(p2_pulls, 1):
        logger.info(f"\n📊 PROGRESS: {i}/{len(p2_pulls)} (P2)")
        success = run_script(pull['script'], pull['description'], pull['timeout'])
        if success:
            success_count += 1
        time.sleep(2)
    
    # Final summary
    logger.info("\n" + "=" * 100)
    logger.info("📊 ALL DATA PULLS COMPLETE!")
    logger.info("=" * 100)
    logger.info(f"✅ Successful: {success_count}/{total_pulls}")
    logger.info(f"❌ Failed: {total_pulls - success_count}/{total_pulls}")
    logger.info(f"⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Re-check freshness
    logger.info("\n📊 RE-CHECKING DATA FRESHNESS...")
    for table_path, date_col, name in freshness_checks:
        freshness = check_data_freshness(table_path, date_col)
        if freshness:
            status = "🟢" if freshness['days_old'] <= 7 else "🟡" if freshness['days_old'] <= 30 else "🔴"
            logger.info(f"{status} {name}: {freshness['days_old']} days old (latest: {freshness['latest_date']})")
    
    if success_count == total_pulls:
        logger.info("\n🎉 ALL DATA PULLS SUCCESSFUL!")
    else:
        logger.warning(f"\n⚠️  {total_pulls - success_count} PULLS FAILED - CHECK LOGS ABOVE")
    
    return success_count == total_pulls

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

