#!/usr/bin/env python3
"""
Volatility Data Ingestion (NO SIGNALS)
Extracts volatility metrics only, ignores buy/sell signals
"""

import pandas as pd
from google.cloud import bigquery
from pathlib import Path
import os
import sys
from datetime import datetime
import logging
from bigquery_utils import safe_load_to_bigquery

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"
TABLE_ID = "volatility_data"

def get_repo_root():
    """Get repository root directory (handles external drive and symlink)"""
    script_dir = Path(__file__).parent.parent.parent
    # Check if we're on external drive
    if str(script_dir).startswith('/Volumes/Satechi Hub'):
        return script_dir
    # Check symlink
    symlink_path = Path.home() / 'Documents' / 'GitHub' / 'CBI-V14'
    if symlink_path.exists() and symlink_path.is_symlink():
        return symlink_path.resolve()
    return script_dir

def find_volatility_file():
    """Find volatility CSV file in data directory"""
    repo_root = get_repo_root()
    
    # Try multiple possible locations
    possible_paths = [
        repo_root / 'data' / 'csv' / 'historical-prices-10-03-2025.csv',
        repo_root / 'data' / 'csv' / 'historical-prices*.csv',
        repo_root / 'TrainingData' / 'raw' / 'historical-prices*.csv',
        Path('/Volumes/Satechi Hub/Projects/CBI-V14/data/csv/historical-prices-10-03-2025.csv'),
    ]
    
    for path in possible_paths:
        if '*' in str(path):
            # Try glob pattern
            matches = list(path.parent.glob(path.name))
            if matches:
                # Return most recent file by modification time
                return max(matches, key=lambda p: p.stat().st_mtime)
        elif path.exists():
            return path
    
    return None

def process_volatility_csv(file_path):
    """Process volatility CSV, extract metrics only (no signals)"""
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded CSV with {len(df)} rows, {len(df.columns)} columns")
        
        # Check required columns exist
        required_cols = ['Symbol', 'Name', 'Last', 'IV/HV', 'Imp Vol']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Extract only volatility columns, skip all signals
        df_clean = df[required_cols].copy()
        
        # Clean column names
        df_clean = df_clean.rename(columns={
            'Symbol': 'symbol',
            'Name': 'contract',
            'Last': 'last_price',
            'IV/HV': 'iv_hv_ratio',
            'Imp Vol': 'implied_vol'
        })
        
        # Validate and convert data types
        df_clean['last_price'] = pd.to_numeric(df_clean['last_price'], errors='coerce')
        df_clean['iv_hv_ratio'] = pd.to_numeric(df_clean['iv_hv_ratio'], errors='coerce')
        
        # Convert implied vol from percentage string to float
        if df_clean['implied_vol'].dtype == 'object':
            df_clean['implied_vol'] = pd.to_numeric(df_clean['implied_vol'].str.replace('%', '', regex=False), errors='coerce')
        else:
            df_clean['implied_vol'] = pd.to_numeric(df_clean['implied_vol'], errors='coerce')
        
        # Drop rows where numeric conversion failed
        df_clean.dropna(subset=['last_price', 'iv_hv_ratio', 'implied_vol'], inplace=True)
        
        # Validate ranges
        df_clean = df_clean[
            (df_clean['implied_vol'] >= 0) & 
            (df_clean['implied_vol'] <= 200) &  # Max 200% implied vol
            (df_clean['last_price'] > 0) &
            (df_clean['iv_hv_ratio'] > 0)
        ]
        
        # Add data date
        df_clean['data_date'] = datetime.now().date()
        
        logger.info(f"Processed {len(df_clean)} valid volatility records")
        return df_clean
        
    except Exception as e:
        logger.error(f"Error processing CSV: {e}")
        raise

def check_duplicates(client, df):
    """Check for existing records to prevent duplicates"""
    if df.empty:
        return df
    
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    try:
        # Get existing records for today
        today = datetime.now().date()
        query = f"""
            SELECT DISTINCT symbol, data_date
            FROM `{table_ref}`
            WHERE data_date = '{today}'
        """
        existing = client.query(query).to_dataframe()
        
        if not existing.empty:
            existing_keys = set(zip(existing['symbol'], existing['data_date']))
            df_keys = set(zip(df['symbol'], df['data_date']))
            duplicates = df_keys & existing_keys
            
            if duplicates:
                logger.warning(f"Found {len(duplicates)} duplicate records, filtering...")
                df = df[~df.set_index(['symbol', 'data_date']).index.isin(duplicates)]
                logger.info(f"After deduplication: {len(df)} new records")
        
    except Exception as e:
        logger.warning(f"Could not check duplicates (table may not exist): {e}")
    
    return df

def load_to_bigquery(df):
    """Load volatility data to BigQuery"""
    if df.empty:
        logger.warning("No data to load")
        return
    
    client = bigquery.Client(project=PROJECT_ID)
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    # Check for duplicates
    df = check_duplicates(client, df)
    
    if df.empty:
        logger.info("All records already exist in BigQuery")
        return
    
    schema = [
        bigquery.SchemaField("symbol", "STRING"),
        bigquery.SchemaField("contract", "STRING"),
        bigquery.SchemaField("last_price", "FLOAT64"),
        bigquery.SchemaField("iv_hv_ratio", "FLOAT64"),
        bigquery.SchemaField("implied_vol", "FLOAT64"),
        bigquery.SchemaField("data_date", "DATE"),
    ]
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        schema=schema,
    )
    
    job = safe_load_to_bigquery(client, df, table_ref, job_config)
    job.result()
    
    logger.info(f"✅ Loaded {len(df)} volatility records (no signals)")

def main():
    logger.info("🚀 Starting volatility data ingestion...")
    
    vol_file = find_volatility_file()
    
    if vol_file is None:
        logger.error("❌ No volatility file found")
        logger.info("Searched in:")
        logger.info(f"  - {get_repo_root() / 'data' / 'csv'}")
        logger.info(f"  - {get_repo_root() / 'TrainingData' / 'raw'}")
        logger.info("Please ensure volatility CSV file exists in data/csv/ directory")
        sys.exit(1)
    
    logger.info(f"📁 Found volatility file: {vol_file}")
    
    try:
        df = process_volatility_csv(vol_file)
        load_to_bigquery(df)
        logger.info(f"✅ Volatility data ingestion complete: {len(df)} contracts loaded")
    except Exception as e:
        logger.error(f"❌ Volatility ingestion failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
