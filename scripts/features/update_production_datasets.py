#!/usr/bin/env python3
"""
Update production_training_data_* tables with latest data from source tables
Runs comprehensive data integration to bring datasets current
"""

from google.cloud import bigquery
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"

def update_production_datasets():
    """Run COMPREHENSIVE_DATA_INTEGRATION_FIXED.sql to update all production datasets"""
    client = bigquery.Client(project=PROJECT_ID)
    
    logger.info("="*70)
    logger.info("UPDATING PRODUCTION TRAINING DATASETS")
    logger.info("="*70)
    logger.info(f"Start: {datetime.now().isoformat()}")
    
    # Read the comprehensive integration SQL
    sql_file = "bigquery-sql/COMPREHENSIVE_DATA_INTEGRATION_FIXED.sql"
    
    try:
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        logger.info(f"📄 Loaded SQL from {sql_file}")
        
        # Execute the integration
        logger.info("🔨 Running comprehensive data integration...")
        logger.info("   This will update ALL source tables and features")
        
        job = client.query(sql_content)
        job.result()  # Wait for completion
        
        logger.info("✅ Comprehensive integration complete")
        
        # Now update production_training_data tables from the updated source
        for horizon in ['1w', '1m', '3m', '6m']:
            logger.info(f"\n📊 Updating production_training_data_{horizon}...")
            
            update_query = f"""
            CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.production_training_data_{horizon}` AS
            SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.training_dataset_pre_integration_backup`
            WHERE target_{horizon} IS NOT NULL
            """
            
            job = client.query(update_query)
            job.result()
            
            # Verify
            verify_query = f"""
            SELECT 
              COUNT(*) as rows,
              MAX(date) as latest_date
            FROM `{PROJECT_ID}.{DATASET_ID}.production_training_data_{horizon}`
            """
            result = client.query(verify_query).to_dataframe()
            
            logger.info(f"✅ production_training_data_{horizon} updated:")
            logger.info(f"   Rows: {result.iloc[0]['rows']}")
            logger.info(f"   Latest: {result.iloc[0]['latest_date']}")
        
        logger.info("\n" + "="*70)
        logger.info("✅ ALL PRODUCTION DATASETS UPDATED")
        logger.info(f"End: {datetime.now().isoformat()}")
        logger.info("="*70)
        
    except FileNotFoundError:
        logger.error(f"❌ SQL file not found: {sql_file}")
        raise
    except Exception as e:
        logger.error(f"❌ Update failed: {e}")
        raise

if __name__ == "__main__":
    update_production_datasets()








