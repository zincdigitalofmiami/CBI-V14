#!/usr/bin/env python3
"""
Create all BigQuery tables for 1M forecasting system
Run this script once before starting the prediction pipeline
"""

import logging
from pathlib import Path
from google.cloud import bigquery

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"

def create_table_from_sql(sql_file_path):
    """Execute SQL file to create table"""
    logger.info(f"Executing {sql_file_path}...")
    
    client = bigquery.Client(project=PROJECT_ID)
    
    with open(sql_file_path, 'r') as f:
        sql = f.read()
    
    try:
        job = client.query(sql, location='us-central1')  # Explicit location
        job.result()  # Wait for completion
        logger.info(f"✅ Created table from {sql_file_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create table from {sql_file_path}: {e}")
        logger.error(f"SQL error details: {str(e)}")
        return False

def main():
    logger.info("=" * 80)
    logger.info("CREATE ALL BIGQUERY TABLES")
    logger.info("=" * 80)
    
    sql_dir = Path(__file__).parent.parent / "bigquery_sql"
    
    tables = [
        "create_predictions_1m_table.sql",
        "create_signals_1w_table.sql",
        "create_shap_drivers_table.sql"
    ]
    
    success_count = 0
    for table_file in tables:
        sql_path = sql_dir / table_file
        if sql_path.exists():
            if create_table_from_sql(sql_path):
                success_count += 1
        else:
            logger.warning(f"SQL file not found: {sql_path}")
    
    logger.info("=" * 80)
    logger.info(f"Created {success_count}/{len(tables)} tables")
    logger.info("Note: agg_1m_latest is created by aggregator job (not a table, materialized view)")
    logger.info("=" * 80)
    
    if success_count == len(tables):
        logger.info("✅ All tables created successfully!")
    else:
        logger.warning("⚠️ Some tables failed to create. Check logs above.")

if __name__ == "__main__":
    main()

