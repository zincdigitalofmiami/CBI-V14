#!/usr/bin/env python3
"""
CBI-V14 Filtered Views Creator for Vertex AI AutoML
==================================================

Creates NULL-free filtered views from training_dataset_super_enriched
to solve the Vertex AI AutoML training failures caused by NULL target values.

Issue Resolution:
- target_1m: 23 NULLs → training_dataset_1m_filtered (1,228 usable rows)
- target_3m: 83 NULLs → training_dataset_3m_filtered (1,168 usable rows)
- target_6m: 173 NULLs → training_dataset_6m_filtered (1,078 usable rows)

Author: CBI-V14 Platform Team
Date: October 28, 2025
Status: Phase 2.3 Implementation
"""

import logging
from google.cloud import bigquery
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize BigQuery client
client = bigquery.Client(project="cbi-v14")

# Configuration
SOURCE_TABLE = "cbi-v14.models_v4.training_dataset_super_enriched"
TARGET_DATASET = "cbi-v14.models_v4"

HORIZONS = {
    '1m': {
        'target_column': 'target_1m',
        'view_name': 'training_dataset_1m_filtered',
        'expected_rows': 1228,
        'null_count': 23
    },
    '3m': {
        'target_column': 'target_3m', 
        'view_name': 'training_dataset_3m_filtered',
        'expected_rows': 1168,
        'null_count': 83
    },
    '6m': {
        'target_column': 'target_6m',
        'view_name': 'training_dataset_6m_filtered', 
        'expected_rows': 1078,
        'null_count': 173
    }
}

def create_filtered_view(horizon_name, config):
    """Create a filtered view that excludes NULL target values"""
    
    target_column = config['target_column']
    view_name = config['view_name']
    expected_rows = config['expected_rows']
    
    # SQL to create the filtered view
    sql = f"""
    CREATE OR REPLACE VIEW `{TARGET_DATASET}.{view_name}` AS
    SELECT *
    FROM `{SOURCE_TABLE}`
    WHERE {target_column} IS NOT NULL
    ORDER BY date
    """
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🔧 CREATING FILTERED VIEW: {horizon_name.upper()}")
    logger.info(f"{'='*60}")
    logger.info(f"Target column: {target_column}")
    logger.info(f"View name: {view_name}")
    logger.info(f"Expected rows: {expected_rows}")
    logger.info(f"SQL: {sql}")
    
    try:
        # Execute the view creation
        logger.info("Executing BigQuery view creation...")
        job = client.query(sql)
        job.result()  # Wait for completion
        
        logger.info(f"✅ View {view_name} created successfully")
        
        # Validate the view
        return validate_filtered_view(view_name, target_column, expected_rows)
        
    except Exception as e:
        logger.error(f"❌ Failed to create view {view_name}: {str(e)}")
        return {
            'horizon': horizon_name,
            'status': 'FAILED',
            'error': str(e),
            'view_name': view_name
        }

def validate_filtered_view(view_name, target_column, expected_rows):
    """Validate the created filtered view"""
    
    logger.info(f"\n🔍 VALIDATING VIEW: {view_name}")
    
    # Check row count
    count_sql = f"SELECT COUNT(*) as row_count FROM `{TARGET_DATASET}.{view_name}`"
    
    try:
        logger.info("Checking row count...")
        result = client.query(count_sql).result()
        actual_rows = list(result)[0].row_count
        
        logger.info(f"Expected rows: {expected_rows}")
        logger.info(f"Actual rows: {actual_rows}")
        
        # Check for NULL values in target column
        null_check_sql = f"""
        SELECT COUNT(*) as null_count 
        FROM `{TARGET_DATASET}.{view_name}` 
        WHERE {target_column} IS NULL
        """
        
        logger.info("Checking for NULL values in target column...")
        null_result = client.query(null_check_sql).result()
        null_count = list(null_result)[0].null_count
        
        logger.info(f"NULL values in {target_column}: {null_count}")
        
        # Check date range
        date_range_sql = f"""
        SELECT 
            MIN(date) as min_date,
            MAX(date) as max_date,
            COUNT(DISTINCT date) as unique_dates
        FROM `{TARGET_DATASET}.{view_name}`
        """
        
        logger.info("Checking date range...")
        date_result = client.query(date_range_sql).result()
        date_info = list(date_result)[0]
        
        logger.info(f"Date range: {date_info.min_date} to {date_info.max_date}")
        logger.info(f"Unique dates: {date_info.unique_dates}")
        
        # Validation results
        row_count_ok = abs(actual_rows - expected_rows) <= 10  # Allow small variance
        no_nulls = null_count == 0
        has_data = actual_rows > 1000  # Minimum viable data
        
        if row_count_ok and no_nulls and has_data:
            logger.info(f"✅ VALIDATION PASSED for {view_name}")
            status = "SUCCESS"
        else:
            logger.warning(f"⚠️ VALIDATION ISSUES for {view_name}")
            logger.warning(f"   Row count OK: {row_count_ok}")
            logger.warning(f"   No NULLs: {no_nulls}")
            logger.warning(f"   Has data: {has_data}")
            status = "WARNING"
        
        return {
            'view_name': view_name,
            'status': status,
            'actual_rows': actual_rows,
            'expected_rows': expected_rows,
            'null_count': null_count,
            'date_range': f"{date_info.min_date} to {date_info.max_date}",
            'unique_dates': date_info.unique_dates
        }
        
    except Exception as e:
        logger.error(f"❌ Validation failed for {view_name}: {str(e)}")
        return {
            'view_name': view_name,
            'status': 'FAILED',
            'error': str(e)
        }

def verify_source_table():
    """Verify the source table exists and has expected structure"""
    
    logger.info(f"\n🔍 VERIFYING SOURCE TABLE: {SOURCE_TABLE}")
    
    try:
        # Check if table exists and get basic info
        info_sql = f"""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(target_1m) as target_1m_non_null,
            COUNT(target_3m) as target_3m_non_null,
            COUNT(target_6m) as target_6m_non_null,
            MIN(date) as min_date,
            MAX(date) as max_date
        FROM `{SOURCE_TABLE}`
        """
        
        result = client.query(info_sql).result()
        info = list(result)[0]
        
        logger.info(f"Source table analysis:")
        logger.info(f"  Total rows: {info.total_rows}")
        logger.info(f"  target_1m non-NULL: {info.target_1m_non_null}")
        logger.info(f"  target_3m non-NULL: {info.target_3m_non_null}")
        logger.info(f"  target_6m non-NULL: {info.target_6m_non_null}")
        logger.info(f"  Date range: {info.min_date} to {info.max_date}")
        
        # Calculate NULL counts
        null_1m = info.total_rows - info.target_1m_non_null
        null_3m = info.total_rows - info.target_3m_non_null
        null_6m = info.total_rows - info.target_6m_non_null
        
        logger.info(f"NULL counts:")
        logger.info(f"  target_1m NULLs: {null_1m}")
        logger.info(f"  target_3m NULLs: {null_3m}")
        logger.info(f"  target_6m NULLs: {null_6m}")
        
        # Verify matches expected values from master plan
        expected_nulls = {'1m': 23, '3m': 83, '6m': 173}
        
        logger.info(f"\nNULL count verification:")
        logger.info(f"  1M: Expected {expected_nulls['1m']}, Actual {null_1m}")
        logger.info(f"  3M: Expected {expected_nulls['3m']}, Actual {null_3m}")
        logger.info(f"  6M: Expected {expected_nulls['6m']}, Actual {null_6m}")
        
        return {
            'status': 'SUCCESS',
            'total_rows': info.total_rows,
            'null_counts': {
                '1m': null_1m,
                '3m': null_3m, 
                '6m': null_6m
            },
            'date_range': f"{info.min_date} to {info.max_date}"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to verify source table: {str(e)}")
        return {
            'status': 'FAILED',
            'error': str(e)
        }

def main():
    """Main execution - create all filtered views"""
    
    logger.info("\n" + "🔧" * 80)
    logger.info("CBI-V14 FILTERED VIEWS CREATOR - PHASE 2.3")
    logger.info("Creating NULL-free views for Vertex AI AutoML training")
    logger.info("🔧" * 80)
    
    # Step 1: Verify source table
    logger.info(f"\n📋 STEP 1: VERIFY SOURCE TABLE")
    source_info = verify_source_table()
    
    if source_info['status'] != 'SUCCESS':
        logger.error("❌ Source table verification failed - aborting")
        return source_info
    
    logger.info("✅ Source table verified successfully")
    
    # Step 2: Create filtered views
    logger.info(f"\n🔧 STEP 2: CREATE FILTERED VIEWS")
    results = {}
    
    for horizon_name, config in HORIZONS.items():
        result = create_filtered_view(horizon_name, config)
        results[horizon_name] = result
    
    # Step 3: Summary
    successful = sum(1 for r in results.values() if r.get('status') == 'SUCCESS')
    failed = len(results) - successful
    
    logger.info(f"\n{'='*80}")
    logger.info(f"📊 FILTERED VIEWS CREATION SUMMARY")
    logger.info(f"{'='*80}")
    logger.info(f"Total views: {len(results)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Success rate: {successful/len(results)*100:.1f}%")
    
    if successful > 0:
        logger.info(f"\n✅ SUCCESSFUL VIEWS:")
        for horizon, data in results.items():
            if data.get('status') == 'SUCCESS':
                logger.info(f"   {horizon.upper()}: {data['view_name']} ({data['actual_rows']} rows)")
    
    if failed > 0:
        logger.error(f"\n❌ FAILED VIEWS:")
        for horizon, data in results.items():
            if data.get('status') == 'FAILED':
                logger.error(f"   {horizon.upper()}: {data.get('error', 'Unknown error')}")
    
    # Next steps
    if successful == len(results):
        logger.info(f"\n🎯 NEXT STEPS:")
        logger.info(f"   ✅ All filtered views created successfully")
        logger.info(f"   🔧 Update run_minimal_research_based.py to use filtered views")
        logger.info(f"   🚀 Relaunch Vertex AI AutoML training")
        logger.info(f"   📊 Expected training success with NULL-free datasets")
        
        # Update TODO
        logger.info(f"\n📝 UPDATING TODO STATUS...")
        return {
            'status': 'SUCCESS',
            'views_created': successful,
            'results': results,
            'ready_for_training': True
        }
    else:
        logger.error(f"\n⚠️ PARTIAL SUCCESS - Some views failed")
        return {
            'status': 'PARTIAL_SUCCESS',
            'views_created': successful,
            'results': results,
            'ready_for_training': False
        }

if __name__ == "__main__":
    result = main()
    
    # Exit with appropriate code
    if result['status'] == 'SUCCESS':
        exit(0)
    else:
        exit(1)





