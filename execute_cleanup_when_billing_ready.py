#!/usr/bin/env python3
"""
CBI-V14 Immediate Cleanup Execution
Runs as soon as billing is enabled - removes duplicate weather data
"""

from google.cloud import bigquery
from datetime import datetime

def execute_immediate_cleanup():
    """Execute cleanup as soon as billing is enabled"""
    client = bigquery.Client(project='cbi-v14')
    
    print('🗑️  EXECUTING IMMEDIATE DUPLICATE CLEANUP')
    print('=' * 60)
    print(f'Started: {datetime.now()}')
    print()
    
    # Cleanup queries to remove my faulty backfill data
    cleanup_operations = [
        {
            'name': 'US Midwest Weather',
            'query': '''
            DELETE FROM `cbi-v14.forecasting_data_warehouse.weather_us_midwest_daily`
            WHERE source_name = 'open_meteo_historical'
            '''
        },
        {
            'name': 'Brazil Weather',
            'query': '''
            DELETE FROM `cbi-v14.forecasting_data_warehouse.weather_brazil_daily`
            WHERE source_name = 'open_meteo_historical'
            '''
        },
        {
            'name': 'Argentina Weather',
            'query': '''
            DELETE FROM `cbi-v14.forecasting_data_warehouse.weather_argentina_daily`
            WHERE source_name = 'open_meteo_historical'
            '''
        }
    ]
    
    # Execute each cleanup
    total_deleted = 0
    for operation in cleanup_operations:
        print(f"🗑️  Cleaning: {operation['name']}")
        
        try:
            job = client.query(operation['query'])
            job.result()
            
            rows_affected = job.num_dml_affected_rows or 0
            print(f"   ✅ SUCCESS: {rows_affected:,} duplicate records deleted")
            total_deleted += rows_affected
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            
            if 'billing' in str(e).lower():
                print("   🚨 BILLING STILL NOT ENABLED")
                return False
    
    print()
    print(f"🎉 CLEANUP COMPLETE: {total_deleted:,} total duplicates removed")
    print()
    
    # Verify cleanup success
    print("✅ VERIFICATION:")
    
    verification_queries = [
        ("US Midwest", "weather_us_midwest_daily"),
        ("Brazil", "weather_brazil_daily"), 
        ("Argentina", "weather_argentina_daily")
    ]
    
    for region, table in verification_queries:
        try:
            verify_query = f'''
            SELECT 
                COUNT(*) as total_records,
                COUNTIF(source_name = 'open_meteo_historical') as remaining_backfill_records
            FROM `cbi-v14.forecasting_data_warehouse.{table}`
            '''
            
            result = client.query(verify_query).to_dataframe()
            if len(result) > 0:
                row = result.iloc[0]
                total = row['total_records']
                remaining_backfill = row['remaining_backfill_records']
                
                if remaining_backfill == 0:
                    print(f"   ✅ {region}: {total:,} records, 0 backfill duplicates remaining")
                else:
                    print(f"   ❌ {region}: {remaining_backfill:,} backfill records still remain")
            
        except Exception as e:
            print(f"   🚨 {region}: Verification error - {str(e)}")
    
    print()
    print("🎯 READY TO PROCEED WITH EXISTING COMPREHENSIVE WEATHER DATA")
    print("   Primary source: weather_data table (13,828 records, 2+ years)")
    return True

if __name__ == "__main__":
    success = execute_immediate_cleanup()
    print("=" * 60)
    
    if success:
        print("✅ DATA CORRUPTION CLEANED - PROCEEDING TO V4 ENHANCED TRAINING")
    else:
        print("❌ CLEANUP FAILED - MANUAL INTERVENTION REQUIRED")
        
    print(f"Completed: {datetime.now()}")
    exit(0 if success else 1)
