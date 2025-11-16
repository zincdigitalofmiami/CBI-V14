#!/usr/bin/env python3
"""
Cleanup Legacy BigQuery Data
Removes old datasets/tables to save storage costs

WARNING: This will DELETE data from BigQuery. Use with caution.
"""

from google.cloud import bigquery
import logging
from typing import List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# BigQuery client
client = bigquery.Client(project='cbi-v14', location='us-central1')

# Legacy datasets/tables to remove
LEGACY_DATASETS = [
    'models_v4',  # Old model training data
    'forecasting_data_warehouse',  # Old warehouse (we have yahoo_finance_comprehensive now)
]

# Tables to keep (don't delete these)
KEEP_TABLES = [
    'yahoo_finance_comprehensive',  # Keep this - it's valuable historical data
    'api',  # Keep API tables
    'predictions',  # Keep predictions
    'monitoring',  # Keep monitoring
]

# Tables to remove from datasets we're keeping
TABLES_TO_REMOVE = {
    'forecasting_data_warehouse': [
        'yahoo_finance_historical',  # Replaced by direct Yahoo Finance pull
        'yahoo_finance_enhanced',    # Replaced by direct Yahoo Finance pull
        'training_dataset_super_enriched',  # Old training data
    ]
}


def list_dataset_tables(dataset_id: str) -> List[str]:
    """List all tables in a dataset"""
    try:
        dataset_ref = client.dataset(dataset_id)
        tables = list(client.list_tables(dataset_ref))
        return [table.table_id for table in tables]
    except Exception as e:
        logger.error(f"Error listing tables in {dataset_id}: {e}")
        return []


def delete_table(dataset_id: str, table_id: str) -> bool:
    """Delete a single table"""
    try:
        table_ref = client.dataset(dataset_id).table(table_id)
        client.delete_table(table_ref)
        logger.info(f"  ✅ Deleted: {dataset_id}.{table_id}")
        return True
    except Exception as e:
        logger.error(f"  ❌ Error deleting {dataset_id}.{table_id}: {e}")
        return False


def delete_dataset(dataset_id: str) -> bool:
    """Delete an entire dataset"""
    try:
        dataset_ref = client.dataset(dataset_id)
        client.delete_dataset(dataset_ref, delete_contents=True, not_found_ok=True)
        logger.info(f"  ✅ Deleted dataset: {dataset_id}")
        return True
    except Exception as e:
        logger.error(f"  ❌ Error deleting dataset {dataset_id}: {e}")
        return False


def main():
    """
    Cleanup legacy BigQuery data
    """
    logger.info("="*80)
    logger.info("BIGQUERY LEGACY DATA CLEANUP")
    logger.info("="*80)
    logger.info("WARNING: This will DELETE data from BigQuery!")
    logger.info("")
    
    # Confirm
    response = input("Are you sure you want to delete legacy BigQuery data? (yes/no): ")
    if response.lower() != 'yes':
        logger.info("Cancelled.")
        return
    
    deleted_datasets = 0
    deleted_tables = 0
    
    # Delete entire legacy datasets
    logger.info("\n" + "="*80)
    logger.info("DELETING LEGACY DATASETS")
    logger.info("="*80)
    
    for dataset_id in LEGACY_DATASETS:
        logger.info(f"\nDeleting dataset: {dataset_id}")
        
        # Check if dataset exists
        try:
            dataset_ref = client.dataset(dataset_id)
            dataset = client.get_dataset(dataset_ref)
            
            # List tables first
            tables = list_dataset_tables(dataset_id)
            logger.info(f"  Found {len(tables)} tables in {dataset_id}")
            
            # Delete dataset (this deletes all tables)
            if delete_dataset(dataset_id):
                deleted_datasets += 1
                logger.info(f"  ✅ Dataset {dataset_id} deleted")
            else:
                logger.warning(f"  ⚠️  Could not delete dataset {dataset_id}")
                
        except Exception as e:
            if 'Not found' in str(e):
                logger.info(f"  Dataset {dataset_id} does not exist (already deleted?)")
            else:
                logger.error(f"  ❌ Error with dataset {dataset_id}: {e}")
    
    # Delete specific tables from datasets we're keeping
    logger.info("\n" + "="*80)
    logger.info("DELETING SPECIFIC LEGACY TABLES")
    logger.info("="*80)
    
    for dataset_id, table_list in TABLES_TO_REMOVE.items():
        logger.info(f"\nDataset: {dataset_id}")
        
        for table_id in table_list:
            logger.info(f"  Deleting table: {dataset_id}.{table_id}")
            if delete_table(dataset_id, table_id):
                deleted_tables += 1
    
    # Summary
    logger.info("")
    logger.info("="*80)
    logger.info("CLEANUP COMPLETE")
    logger.info("="*80)
    logger.info(f"✅ Deleted datasets: {deleted_datasets}")
    logger.info(f"✅ Deleted tables: {deleted_tables}")
    logger.info("")
    logger.info("💾 Storage costs should be reduced")
    logger.info("")


if __name__ == "__main__":
    main()
