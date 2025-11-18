#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CBI-V14 - Week 2: Backfill Alpha Vantage Data to BigQuery
==========================================================

Loads the staged Alpha Vantage data into the prefixed BigQuery tables.
"""
import os
import sys
import logging
from pathlib import Path
from google.cloud import bigquery
from google.api_core.exceptions import NotFound

# Setup project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from src.utils.gcp_utils import get_gcp_project_id
except ImportError:
    print("Could not import gcp_utils. Ensure you are running from the project root.")
    sys.exit(1)

import pandas as pd

# Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = get_gcp_project_id()
if not PROJECT_ID:
    logger.error("GCP_PROJECT_ID not found. Exiting.")
    sys.exit(1)

client = bigquery.Client(project=PROJECT_ID)
DATASET_ID = "forecasting_data_warehouse"

# Paths
EXTERNAL_DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
STAGING_FILE = EXTERNAL_DRIVE / "TrainingData/staging/alpha_vantage_features.parquet"

def load_alpha_data_to_bigquery():
    """Load the staged Alpha Vantage data into BigQuery."""
    if not STAGING_FILE.exists():
        logger.error(f"Staging file not found: {STAGING_FILE}")
        return False
    
    logger.info(f"Loading Alpha Vantage data from {STAGING_FILE}")
    df = pd.read_parquet(STAGING_FILE)
    
    logger.info(f"Data shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
    
    # Convert date column to datetime for BigQuery
    df['date'] = pd.to_datetime(df['date'])
    
    # Clean column names for BigQuery (replace special characters)
    df.columns = [c.replace('/', '_').replace(' ', '_').replace('-', '_') for c in df.columns]
    
    # Load to BigQuery - use a single table for all Alpha Vantage data
    table_id = f"{PROJECT_ID}.{DATASET_ID}.alpha_vantage_features"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        source_format=bigquery.SourceFormat.PARQUET,
        autodetect=True,
    )
    
    # Convert DataFrame to Parquet bytes for upload
    import io
    parquet_buffer = io.BytesIO()
    df.to_parquet(parquet_buffer, index=False)
    parquet_buffer.seek(0)
    
    try:
        job = client.load_table_from_file(
            parquet_buffer,
            table_id,
            job_config=job_config
        )
        job.result()  # Wait for job to complete
        
        # Verify load
        table = client.get_table(table_id)
        logger.info(f"✅ Successfully loaded {table.num_rows:,} rows to {table_id}")
        logger.info(f"   Schema: {len(table.schema)} columns")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to load data: {e}")
        return False

def main():
    """Main execution function."""
    logger.info("="*80)
    logger.info("Backfilling Alpha Vantage Data to BigQuery")
    logger.info("="*80)
    
    success = load_alpha_data_to_bigquery()
    
    if success:
        logger.info("="*80)
        logger.info("✅ Alpha Vantage Backfill Complete")
        logger.info("="*80)
    else:
        logger.error("="*80)
        logger.error("❌ Alpha Vantage Backfill Failed")
        logger.error("="*80)
        sys.exit(1)

if __name__ == "__main__":
    main()

