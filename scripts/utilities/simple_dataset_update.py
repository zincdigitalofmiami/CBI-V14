#!/usr/bin/env python3
"""
Simple update: Copy latest backup to production datasets
Bypasses broken COMPREHENSIVE_DATA_INTEGRATION_FIXED.sql
"""

from google.cloud import bigquery
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"

def simple_update():
    """Copy from backup to production datasets"""
    client = bigquery.Client(project=PROJECT_ID)
    
    logger.info("="*70)
    logger.info("SIMPLE PRODUCTION DATASET UPDATE")
    logger.info("="*70)
    
    # Source: The 290-column backup from Nov 3
    source_table = f"{PROJECT_ID}.{DATASET_ID}.training_dataset_pre_integration_backup"
    
    for horizon in ['1w', '1m', '3m', '6m']:
        logger.info(f"\n📊 Updating production_training_data_{horizon}...")
        
        query = f"""
        CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.production_training_data_{horizon}` AS
        SELECT * FROM `{source_table}`
        WHERE target_{horizon} IS NOT NULL
        """
        
        job = client.query(query)
        job.result()
        
        # Verify
        verify_query = f"""
        SELECT 
          COUNT(*) as rows,
          MAX(date) as latest_date,
          (SELECT COUNT(*) FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.COLUMNS` 
           WHERE table_name = 'production_training_data_{horizon}') as columns
        FROM `{PROJECT_ID}.{DATASET_ID}.production_training_data_{horizon}`
        """
        result = client.query(verify_query).to_dataframe()
        
        logger.info(f"✅ production_training_data_{horizon}:")
        logger.info(f"   Columns: {result.iloc[0]['columns']}")
        logger.info(f"   Rows: {result.iloc[0]['rows']}")
        logger.info(f"   Latest: {result.iloc[0]['latest_date']}")
    
    logger.info("\n" + "="*70)
    logger.info("✅ ALL PRODUCTION DATASETS UPDATED FROM BACKUP")
    logger.info("="*70)
    logger.info("\n⚠️  NEXT: Connect ingestion scripts to update these daily")

if __name__ == "__main__":
    simple_update()







