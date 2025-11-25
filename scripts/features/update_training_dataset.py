#!/usr/bin/env python3
"""
Master Training Dataset Refresh Script
- Consolidates all 209 feature engineering steps.
- Reads from fresh, raw data sources.
- Overwrites the stale training_dataset_super_enriched table.
- Includes guardrails to prevent running on stale data.
"""

from google.cloud import bigquery
from datetime import datetime, timedelta
import logging

# --- CONFIGURATION ---
PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"
TARGET_TABLE = "training_dataset_super_enriched"
SQL_SOURCE_FILE = "/Users/zincdigital/CBI-V14/scripts/CREATE_FULL_TRAINING_DATASET.sql"
LOG_FILE = "/Users/zincdigital/CBI-V14/logs/data_refresh.log"
MAX_STALE_DAYS = 3

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

client = bigquery.Client(project=PROJECT_ID)

def run_data_freshness_guardrail():
    """
    Guardrail: Abort if raw price data is too old.
    """
    logger.info("--- GUARDRAIL: Checking raw data freshness...")
    try:
        query = "SELECT MAX(time) as latest_price_time FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`"
        result = list(client.query(query))
        if not result or not result[0].latest_price_time:
            raise ValueError("Raw price table is empty.")

        latest_time = result[0].latest_price_time
        if latest_time.tzinfo:
            latest_time = latest_time.replace(tzinfo=None)

        days_old = (datetime.utcnow() - latest_time).days

        if days_old > MAX_STALE_DAYS:
            raise ValueError(f"Raw price data is {days_old} days old (max allowed: {MAX_STALE_DAYS}). Aborting.")
        
        logger.info(f"✅ Raw price data is {days_old} days old. Proceeding.")
        return True
    except Exception as e:
        logger.error(f"❌ GUARDRAIL FAILED: {e}")
        return False

def get_master_sql():
    """Reads the master SQL and converts it to a CREATE OR REPLACE TABLE statement."""
    with open(SQL_SOURCE_FILE, 'r') as f:
        sql = f.read()
    
    # Replace the VIEW creation with TABLE creation for performance
    # This is critical for making a static, reliable dataset for training
    sql = sql.replace(
        "CREATE OR REPLACE VIEW `cbi-v14.models.vw_neural_training_dataset` AS",
        f"CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.{TARGET_TABLE}` AS"
    )
    return sql

def main():
    """Execute the full data refresh pipeline."""
    logger.info("="*60)
    logger.info("STARTING MASTER TRAINING DATASET REFRESH")
    logger.info("="*60)

    # 1. Run Guardrail Check
    if not run_data_freshness_guardrail():
        exit(1)

    # 2. Get and Execute the Master SQL Query
    logger.info("\n--- STEP 1: Rebuilding the feature table...")
    try:
        master_sql = get_master_sql()
        logger.info("Executing master feature generation query... (This may take several minutes)")
        job = client.query(master_sql)
        job.result()  # Wait for the job to complete
        
        # Verify the result
        table = client.get_table(f"{PROJECT_ID}.{DATASET_ID}.{TARGET_TABLE}")
        latest_date_query = f"SELECT MAX(date) FROM `{PROJECT_ID}.{DATASET_ID}.{TARGET_TABLE}`"
        latest_date = list(client.query(latest_date_query))[0][0]

        logger.info(f"✅ Successfully rebuilt `{TARGET_TABLE}`.")
        logger.info(f"   - Rows: {table.num_rows}")
        logger.info(f"   - Columns: {len(table.schema)}")
        logger.info(f"   - Latest Date: {latest_date.strftime('%Y-%m-%d')}")
        
    except Exception as e:
        logger.error(f"❌ FAILED to rebuild feature table: {e}")
        exit(1)

    logger.info("\n" + "="*60)
    logger.info("MASTER TRAINING DATASET REFRESH COMPLETE")
    logger.info("="*60)

if __name__ == "__main__":
    main()











