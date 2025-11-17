#!/usr/bin/env python3
"""
Verify Daily Updates for Google Cloud Marketplace Datasets
==========================================================
Tests that datasets are accessible daily and updated daily
Checks latest data dates, update schedules, and access patterns
"""

import os
from google.cloud import bigquery
from datetime import datetime, timedelta
import pandas as pd
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

# Datasets to verify
# NOTE: Google Marketplace datasets are BACKUP ONLY
# Primary sources: FRED API, Yahoo Finance API, INMET Brazil API
DATASETS_TO_VERIFY = {
    'noaa_gsod': {
        'dataset_id': 'bigquery-public-data.noaa_gsod',
        'table_pattern': 'gsod*',
        'date_column': 'date',
        'expected_update': 'daily',
        'description': 'NOAA Global Surface Summary of Day (BACKUP for NOAA API)',
        'role': 'backup'  # Backup for NOAA API if it fails
    },
    'noaa_gfs': {
        'dataset_id': 'bigquery-public-data.noaa_global_forecast_system',
        'table_name': 'NOAA_GFS0P25',
        'date_column': 'forecast_date',
        'expected_update': 'daily',
        'description': 'NOAA Global Forecast System (FORECAST DATA - not historical)',
        'role': 'forecast'  # Forecast data, not historical replacement
    },
    'gdelt_events': {
        'dataset_id': 'gdelt-bq.gdeltv2.events',
        'table_name': 'events_partitioned',
        'date_column': 'SQLDATE',
        'expected_update': 'daily',
        'description': 'GDELT Global Events (PRIMARY - no API access)',
        'role': 'primary'  # Primary source - we don't have API access
    },
    'bls_cpi': {
        'dataset_id': 'bigquery-public-data.bls',
        'table_name': 'cpi_u',
        'date_column': 'date',
        'expected_update': 'monthly',
        'description': 'BLS Consumer Price Index (SUPPLEMENT to FRED, not replacement)',
        'role': 'supplement'  # Supplement to FRED CPI
    },
    'bls_unemployment': {
        'dataset_id': 'bigquery-public-data.bls',
        'table_name': 'unemployment_cps',
        'date_column': 'date',
        'expected_update': 'monthly',
        'description': 'BLS Unemployment Data (SUPPLEMENT to FRED, not replacement)',
        'role': 'supplement'  # Supplement to FRED unemployment
    },
    'fec': {
        'dataset_id': 'bigquery-public-data.fec',
        'table_pattern': 'candidate_*',
        'date_column': None,  # FEC is election-cycle based
        'expected_update': 'irregular',
        'description': 'FEC Campaign Finance (PRIMARY - no API access)',
        'role': 'primary'  # Primary source - we don't have API access
    }
}

def check_latest_data(dataset_info: dict) -> dict:
    """
    Check the latest data date in a dataset.
    """
    dataset_id = dataset_info['dataset_id']
    date_column = dataset_info.get('date_column')
    table_name = dataset_info.get('table_name')
    table_pattern = dataset_info.get('table_pattern')
    
    result = {
        'dataset_id': dataset_id,
        'accessible': False,
        'latest_date': None,
        'days_behind': None,
        'update_frequency': dataset_info.get('expected_update'),
        'error': None
    }
    
    try:
        if table_pattern:
            # Handle wildcard tables (like gsod*)
            if 'gsod' in dataset_id:
                # Check latest year table
                current_year = datetime.now().year
                table_name = f'gsod{current_year}'
                full_table = f"{dataset_id}.{table_name}"
                
                query = f"""
                SELECT 
                    MAX({date_column}) as latest_date,
                    COUNT(*) as row_count
                FROM `{full_table}`
                """
            else:
                # Generic wildcard query
                query = f"""
                SELECT 
                    MAX({date_column}) as latest_date,
                    COUNT(*) as row_count
                FROM `{dataset_id}.{table_pattern}`
                """
        else:
            # Single table
            full_table = f"{dataset_id}.{table_name}"
            
            if date_column:
                if 'SQLDATE' in date_column:
                    # GDELT uses integer dates
                    query = f"""
                    SELECT 
                        PARSE_DATE('%Y%m%d', CAST(MAX({date_column}) AS STRING)) as latest_date,
                        COUNT(*) as row_count
                    FROM `{full_table}`
                    """
                else:
                    query = f"""
                    SELECT 
                        MAX({date_column}) as latest_date,
                        COUNT(*) as row_count
                    FROM `{full_table}`
                    """
            else:
                # No date column - check table metadata
                table_ref = client.get_table(full_table)
                result['accessible'] = True
                result['latest_date'] = 'N/A (no date column)'
                result['table_size'] = table_ref.num_rows
                result['last_modified'] = str(table_ref.modified) if hasattr(table_ref, 'modified') else None
                return result
        
        logger.info(f"Querying {dataset_id} for latest data...")
        df = client.query(query).to_dataframe()
        
        if not df.empty and df['latest_date'].iloc[0] is not None:
            latest_date = pd.to_datetime(df['latest_date'].iloc[0])
            today = datetime.now().date()
            days_behind = (today - latest_date.date()).days
            
            result['accessible'] = True
            result['latest_date'] = str(latest_date.date())
            result['days_behind'] = days_behind
            result['row_count'] = int(df['row_count'].iloc[0])
            
            # Check if update is current
            if dataset_info.get('expected_update') == 'daily':
                if days_behind <= 2:  # Allow 1-2 day lag for processing
                    result['status'] = '✅ CURRENT'
                else:
                    result['status'] = f'⚠️  BEHIND ({days_behind} days)'
            elif dataset_info.get('expected_update') == 'monthly':
                if days_behind <= 35:  # Allow up to 35 days for monthly updates
                    result['status'] = '✅ CURRENT'
                else:
                    result['status'] = f'⚠️  BEHIND ({days_behind} days)'
            else:
                result['status'] = '✅ ACCESSIBLE'
        else:
            result['accessible'] = True
            result['latest_date'] = 'No data found'
            result['status'] = '⚠️  NO DATA'
            
    except Exception as e:
        result['accessible'] = False
        result['error'] = str(e)
        result['status'] = '❌ ERROR'
        logger.error(f"Error checking {dataset_id}: {e}")
    
    return result

def check_update_schedule(dataset_info: dict) -> dict:
    """
    Check update schedule by examining recent data patterns.
    """
    dataset_id = dataset_info['dataset_id']
    date_column = dataset_info.get('date_column')
    table_name = dataset_info.get('table_name')
    table_pattern = dataset_info.get('table_pattern')
    
    result = {
        'dataset_id': dataset_id,
        'update_pattern': 'unknown',
        'recent_dates': [],
        'update_frequency_detected': None
    }
    
    try:
        if table_pattern and 'gsod' in dataset_id:
            # Check last 30 days of current year
            current_year = datetime.now().year
            table_name = f'gsod{current_year}'
            full_table = f"{dataset_id}.{table_name}"
            
            query = f"""
            SELECT DISTINCT {date_column} as date
            FROM `{full_table}`
            WHERE {date_column} >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            ORDER BY date DESC
            LIMIT 30
            """
        elif table_name:
            full_table = f"{dataset_id}.{table_name}"
            
            if 'SQLDATE' in str(date_column):
                query = f"""
                SELECT DISTINCT 
                    PARSE_DATE('%Y%m%d', CAST({date_column} AS STRING)) as date
                FROM `{full_table}`
                WHERE PARSE_DATE('%Y%m%d', CAST({date_column} AS STRING)) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                ORDER BY date DESC
                LIMIT 30
                """
            else:
                query = f"""
                SELECT DISTINCT {date_column} as date
                FROM `{full_table}`
                WHERE {date_column} >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                ORDER BY date DESC
                LIMIT 30
                """
        else:
            return result
        
        df = client.query(query).to_dataframe()
        
        if not df.empty:
            result['recent_dates'] = [str(d.date()) for d in df['date'].tolist()]
            
            # Detect update frequency
            if len(result['recent_dates']) >= 20:
                result['update_frequency_detected'] = 'daily'
                result['update_pattern'] = 'Daily updates confirmed'
            elif len(result['recent_dates']) >= 1:
                result['update_frequency_detected'] = 'irregular'
                result['update_pattern'] = f'Recent data available ({len(result["recent_dates"])} days in last 30)'
            else:
                result['update_frequency_detected'] = 'stale'
                result['update_pattern'] = 'No recent data'
                
    except Exception as e:
        result['error'] = str(e)
        logger.warning(f"Could not check update schedule for {dataset_id}: {e}")
    
    return result

def verify_daily_accessibility() -> dict:
    """
    Verify all datasets are accessible daily and check update status.
    """
    logger.info("="*80)
    logger.info("VERIFYING DAILY ACCESSIBILITY & UPDATES")
    logger.info("="*80)
    
    results = {}
    
    for dataset_key, dataset_info in DATASETS_TO_VERIFY.items():
        logger.info(f"\n{'='*80}")
        logger.info(f"Verifying: {dataset_info['description']}")
        logger.info(f"Dataset: {dataset_info['dataset_id']}")
        logger.info(f"Expected Update: {dataset_info.get('expected_update', 'unknown')}")
        logger.info(f"{'='*80}")
        
        # Check latest data
        latest_check = check_latest_data(dataset_info)
        results[dataset_key] = {
            'latest_check': latest_check,
            'update_schedule': None
        }
        
        logger.info(f"Status: {latest_check['status']}")
        if latest_check.get('latest_date'):
            logger.info(f"Latest Date: {latest_check['latest_date']}")
        if latest_check.get('days_behind') is not None:
            logger.info(f"Days Behind: {latest_check['days_behind']} days")
        if latest_check.get('row_count'):
            logger.info(f"Total Rows: {latest_check['row_count']:,}")
        
        # Check update schedule if daily expected
        if dataset_info.get('expected_update') == 'daily' and latest_check['accessible']:
            schedule_check = check_update_schedule(dataset_info)
            results[dataset_key]['update_schedule'] = schedule_check
            
            logger.info(f"Update Pattern: {schedule_check.get('update_pattern', 'unknown')}")
            if schedule_check.get('recent_dates'):
                logger.info(f"Recent Dates Available: {len(schedule_check['recent_dates'])} days")
                logger.info(f"  Latest: {schedule_check['recent_dates'][0]}")
                logger.info(f"  Oldest: {schedule_check['recent_dates'][-1]}")
    
    return results

def generate_daily_access_report(results: dict):
    """
    Generate comprehensive report on daily accessibility.
    """
    logger.info("\n" + "="*80)
    logger.info("DAILY ACCESSIBILITY REPORT")
    logger.info("="*80)
    logger.info("NOTE: Google Marketplace = Backup/Gap Filler, NOT Replacement")
    logger.info("PRIMARY SOURCES: FRED API, Yahoo Finance API, INMET Brazil API")
    logger.info("="*80)
    
    daily_ready = []
    needs_attention = []
    not_accessible = []
    
    for dataset_key, result in results.items():
        latest = result['latest_check']
        dataset_info = DATASETS_TO_VERIFY.get(dataset_key, {})
        role = dataset_info.get('role', 'unknown')
        
        if not latest['accessible']:
            not_accessible.append({
                'dataset': dataset_key,
                'role': role,
                'error': latest.get('error', 'Unknown')
            })
        elif latest.get('status') == '✅ CURRENT':
            daily_ready.append({
                'dataset': dataset_key,
                'role': role,
                'latest_date': latest.get('latest_date'),
                'days_behind': latest.get('days_behind', 0)
            })
        else:
            needs_attention.append({
                'dataset': dataset_key,
                'role': role,
                'status': latest.get('status'),
                'latest_date': latest.get('latest_date'),
                'days_behind': latest.get('days_behind')
            })
    
    logger.info(f"\n✅ DAILY ACCESSIBLE ({len(daily_ready)}):")
    for item in daily_ready:
        role_label = f"[{item['role'].upper()}]" if item.get('role') else ""
        logger.info(f"   - {item['dataset']} {role_label}: Latest {item['latest_date']}, {item['days_behind']} days behind")
    
    if needs_attention:
        logger.info(f"\n⚠️  NEEDS ATTENTION ({len(needs_attention)}):")
        for item in needs_attention:
            role_label = f"[{item['role'].upper()}]" if item.get('role') else ""
            logger.info(f"   - {item['dataset']} {role_label}: {item['status']}")
            logger.info(f"     Latest: {item['latest_date']}, Behind: {item.get('days_behind', 'N/A')} days")
    
    if not_accessible:
        logger.info(f"\n❌ NOT ACCESSIBLE ({len(not_accessible)}):")
        for item in not_accessible:
            role_label = f"[{item['role'].upper()}]" if item.get('role') else ""
            logger.info(f"   - {item['dataset']} {role_label}: {item['error']}")
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("SUMMARY")
    logger.info("="*80)
    logger.info(f"Total Datasets Tested: {len(results)}")
    logger.info(f"✅ Daily Accessible: {len(daily_ready)}")
    logger.info(f"⚠️  Needs Attention: {len(needs_attention)}")
    logger.info(f"❌ Not Accessible: {len(not_accessible)}")
    
    # Recommendations
    logger.info("\n" + "="*80)
    logger.info("RECOMMENDATIONS")
    logger.info("="*80)
    logger.info("REMEMBER: Google Marketplace = Backup/Gap Filler")
    logger.info("PRIMARY SOURCES: FRED API, Yahoo Finance API, INMET Brazil API")
    logger.info("")
    
    if len(daily_ready) == len(results):
        logger.info("✅ ALL GOOGLE MARKETPLACE DATASETS ARE ACCESSIBLE!")
        logger.info("   Ready for backup/supplement use.")
        logger.info("   ⚠️  Still use APIs as PRIMARY sources (FRED, Yahoo, INMET)")
    elif len(daily_ready) > 0:
        logger.info(f"✅ {len(daily_ready)} Google Marketplace datasets ready for backup/supplement use.")
        if needs_attention:
            logger.info(f"⚠️  {len(needs_attention)} datasets need monitoring:")
            for item in needs_attention:
                logger.info(f"   - {item['dataset']} [{item.get('role', 'unknown')}]: Check update schedule")
        logger.info("   ⚠️  Still use APIs as PRIMARY sources (FRED, Yahoo, INMET)")
    else:
        logger.info("❌ NO GOOGLE MARKETPLACE DATASETS CONFIRMED ACCESSIBLE")
        logger.info("   Investigate update schedules and access patterns.")
        logger.info("   ⚠️  Rely on PRIMARY APIs: FRED, Yahoo Finance, INMET")
    
    return {
        'daily_ready': daily_ready,
        'needs_attention': needs_attention,
        'not_accessible': not_accessible,
        'summary': {
            'total': len(results),
            'ready': len(daily_ready),
            'needs_attention': len(needs_attention),
            'not_accessible': len(not_accessible)
        }
    }

def main():
    """
    Main execution: Verify daily accessibility and updates.
    """
    # Verify all datasets
    results = verify_daily_accessibility()
    
    # Generate report
    report = generate_daily_access_report(results)
    
    # Save report
    output_dir = Path("/Volumes/Satechi Hub/Projects/CBI-V14/docs/data-sources/google-marketplace")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    import json
    report_file = output_dir / f"daily_access_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump({
            'verification_date': datetime.now().isoformat(),
            'results': results,
            'report': report
        }, f, indent=2, default=str)
    
    logger.info(f"\n✅ Report saved to: {report_file}")
    
    return report

if __name__ == "__main__":
    main()
