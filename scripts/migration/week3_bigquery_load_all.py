#!/usr/bin/env python3
"""
Week 3: Load all staged parquet files to BigQuery tables.
Handles the full pipeline load with validation.
"""

import pandas as pd
from pathlib import Path
from google.cloud import bigquery
import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.utils.gcp_utils import get_gcp_project_id

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
STAGING_DIR = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/staging")
PROJECT_ID = get_gcp_project_id()
DATASET_ID = "forecasting_data_warehouse"

# Table mappings
TABLE_MAPPINGS = {
    "yahoo_historical_all_symbols.parquet": "yahoo_historical_prefixed",
    "fred_macro_expanded.parquet": "fred_macro_expanded",
    "weather_granular_daily.parquet": "weather_granular",
    "cftc_commitments.parquet": "cftc_commitments",
    "usda_reports_granular.parquet": "usda_reports_granular",
    "eia_energy_granular.parquet": "eia_energy_granular",
    "alpha_vantage_features.parquet": "alpha_vantage_features",
    "volatility_daily.parquet": "volatility_features",
    "barchart_palm_daily.parquet": "palm_oil_daily",
    "policy_trump_signals.parquet": "policy_trump_signals",
    "es_futures_daily.parquet": "es_futures_daily"  # ES futures with 50+ technical indicators
}

def clean_column_names(df):
    """Clean column names for BigQuery compatibility."""
    df.columns = [
        c.replace('.', '_')
         .replace('/', '_')
         .replace(' ', '_')
         .replace('-', '_')
         .replace('(', '')
         .replace(')', '')
         .replace('[', '')
         .replace(']', '')
        for c in df.columns
    ]
    return df

def load_table_to_bigquery(staging_file, table_name, client):
    """Load a single staging file to BigQuery."""
    file_path = STAGING_DIR / staging_file
    
    if not file_path.exists():
        logger.warning(f"  ⚠️  File not found: {staging_file}")
        return False
    
    try:
        # Load data
        df = pd.read_parquet(file_path)
        df = clean_column_names(df)
        
        # Ensure date column is datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        logger.info(f"  Loading {len(df):,} rows × {len(df.columns)} columns")
        
        # BigQuery table reference
        table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
        
        # Configure load job
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE",  # Replace existing data
            autodetect=True  # Infer schema
        )
        
        # Load to BigQuery
        job = client.load_table_from_dataframe(
            df, table_id, job_config=job_config
        )
        job.result()  # Wait for job to complete
        
        # Verify load
        table = client.get_table(table_id)
        logger.info(f"  ✅ Loaded {table.num_rows:,} rows to {table_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"  ❌ Error loading {staging_file}: {str(e)}")
        return False

def verify_table(table_name, expected_rows, client):
    """Verify a table has been loaded correctly."""
    try:
        table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
        table = client.get_table(table_id)
        
        # Check row count
        actual_rows = table.num_rows
        if actual_rows == 0:
            logger.warning(f"  ⚠️  {table_name}: Empty table")
            return False
        
        # Check schema
        num_columns = len(table.schema)
        
        # Get date range
        query = f"""
        SELECT 
            MIN(date) as min_date,
            MAX(date) as max_date
        FROM `{table_id}`
        WHERE date IS NOT NULL
        """
        
        result = client.query(query).result()
        for row in result:
            min_date = row.min_date
            max_date = row.max_date
            logger.info(f"  ✅ {table_name}: {actual_rows:,} rows, {num_columns} cols, {min_date} to {max_date}")
            return True
            
    except Exception as e:
        logger.error(f"  ❌ Error verifying {table_name}: {str(e)}")
        return False

def main():
    """Load all staged data to BigQuery."""
    logger.info("="*80)
    logger.info("WEEK 3: BIGQUERY LOAD - ALL STAGED DATA")
    logger.info("="*80)
    
    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT_ID)
    logger.info(f"Project: {PROJECT_ID}")
    logger.info(f"Dataset: {DATASET_ID}")
    
    # Load regime calendar first (if exists)
    regime_file = Path("/Volumes/Satechi Hub/Projects/CBI-V14/registry/regime_calendar.parquet")
    if regime_file.exists():
        logger.info("\nLoading regime calendar...")
        df = pd.read_parquet(regime_file)
        df['date'] = pd.to_datetime(df['date'])
        table_id = f"{PROJECT_ID}.features.regime_calendar"
        
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE",
            autodetect=True
        )
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        logger.info(f"  ✅ Loaded {len(df):,} rows to regime_calendar")
    
    # Load all staging tables
    logger.info("\n" + "="*80)
    logger.info("LOADING STAGING TABLES")
    logger.info("="*80)
    
    success_count = 0
    failed_count = 0
    
    for staging_file, table_name in TABLE_MAPPINGS.items():
        logger.info(f"\n{staging_file} → {table_name}")
        if load_table_to_bigquery(staging_file, table_name, client):
            success_count += 1
        else:
            failed_count += 1
    
    # Verification
    logger.info("\n" + "="*80)
    logger.info("VERIFICATION")
    logger.info("="*80)
    
    for staging_file, table_name in TABLE_MAPPINGS.items():
        file_path = STAGING_DIR / staging_file
        if file_path.exists():
            df = pd.read_parquet(file_path)
            verify_table(table_name, len(df), client)
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("SUMMARY")
    logger.info("="*80)
    logger.info(f"✅ Successful loads: {success_count}")
    logger.info(f"❌ Failed loads: {failed_count}")
    
    if failed_count == 0:
        logger.info("\n🎉 ALL TABLES LOADED SUCCESSFULLY!")
        
        # Create master view
        logger.info("\nCreating master features view...")
        query = f"""
        CREATE OR REPLACE VIEW `{PROJECT_ID}.{DATASET_ID}.master_features_all` AS
        SELECT 
            y.*,
            f.* EXCEPT(date),
            w.* EXCEPT(date),
            c.* EXCEPT(date),
            u.* EXCEPT(date),
            e.* EXCEPT(date),
            a.* EXCEPT(date),
            v.* EXCEPT(date),
            p.* EXCEPT(date),
            pol.* EXCEPT(date),
            es.* EXCEPT(date, symbol),  -- Exclude symbol to avoid duplicate with yahoo
            r.regime,
            r.training_weight
        FROM `{PROJECT_ID}.{DATASET_ID}.yahoo_historical_prefixed` y
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.fred_macro_expanded` f USING(date)
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.weather_granular` w USING(date)
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.cftc_commitments` c USING(date)
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.usda_reports_granular` u USING(date)
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.eia_energy_granular` e USING(date)
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.alpha_vantage_features` a USING(date)
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.volatility_features` v USING(date)
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.palm_oil_daily` p USING(date)
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.policy_trump_signals` pol USING(date)
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.es_futures_daily` es USING(date)
        LEFT JOIN `{PROJECT_ID}.features.regime_calendar` r USING(date)
        WHERE y.symbol = 'ZL=F'
        ORDER BY date
        """
        
        client.query(query).result()
        logger.info("  ✅ Created master_features_all view")
    
    return success_count, failed_count

if __name__ == "__main__":
    success, failed = main()
    sys.exit(0 if failed == 0 else 1)
