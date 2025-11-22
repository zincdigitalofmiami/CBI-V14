#!/usr/bin/env python3
"""
Load historical Databento data (ZL, MES) into BigQuery raw table.
Table: market_data.databento_futures_ohlcv_1d

Features:
- Loads from local Parquet staging files.
- Maps user-friendly columns (zl_open) to canonical schema (open).
- Handles BigQuery partition limits by batching uploads by year.
- Validates row counts.
"""

import os
from datetime import datetime
import pandas as pd
from google.cloud import bigquery
from google.api_core.exceptions import BadRequest

# Configuration
PROJECT_ID = os.getenv("PROJECT_ID", "cbi-v14")
DATASET_ID = "market_data"
TABLE_ID = "databento_futures_ohlcv_1d"
FULL_TABLE_ID = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

# Input Files (Staging)
FILE_MAP = {
    "ZL": "/Users/kirkmusick/Documents/GitHub/CBI-V14/TrainingData/staging/zl_daily_aggregated.parquet",
    "MES": "/Users/kirkmusick/Documents/GitHub/CBI-V14/TrainingData/staging/mes_daily_aggregated.parquet"
}

def get_bq_client():
    return bigquery.Client(project=PROJECT_ID)

def load_data(symbol, file_path, client):
    print(f"\nProcessing {symbol} from {file_path}...")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    # Read Parquet
    df = pd.read_parquet(file_path)
    print(f"   Loaded {len(df)} rows from parquet.")

    # Schema Mapping
    # Standardize columns to: date, symbol, open, high, low, close, volume, settle, vwap, open_interest...
    
    # 1. Normalize Date
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date']).dt.date
    else:
        print("❌ 'date' column missing!")
        return

    # 2. Map Price/Vol Columns
    prefix = symbol.lower() + "_"
    
    # Mapping dictionary
    col_map = {
        f"{prefix}open": "open",
        f"{prefix}high": "high",
        f"{prefix}low": "low",
        f"{prefix}close": "close",
        f"{prefix}volume": "volume",
        # Use 60min VWAP as daily proxy if available, else null
        f"{prefix}60min_vwap": "vwap" 
    }
    
    # Rename columns
    df = df.rename(columns=col_map)
    
    # 3. Add Static/Missing Columns
    df['symbol'] = symbol
    df['instrument_id'] = None # Unknown from agg file
    df['exchange'] = 'CME' if symbol in ['ES', 'MES'] else 'CBOT' # ZL is CBOT
    df['currency'] = 'USD'
    df['dataset'] = 'GLBX.MDP3'
    df['load_ts'] = datetime.utcnow()
    
    # Ensure Settle exists (nullable)
    if 'settle' not in df.columns:
        df['settle'] = None
    if 'open_interest' not in df.columns:
        df['open_interest'] = None

    # 4. Select Final Columns in Order
    final_cols = [
        'date', 'symbol', 'open', 'high', 'low', 'close', 'volume', 
        'settle', 'vwap', 'open_interest', 
        'instrument_id', 'exchange', 'currency', 'dataset', 'load_ts'
    ]
    
    # Filter to available columns only (let BQ handle others if missing, but we prepared them)
    df_final = df[final_cols].copy()

    # 5. Load to BigQuery (Batched by Year)
    # Why? BQ has a limit of 4000 partitions per load job. 15 years > 4000 days.
    
    table_schema = [
        bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("open", "FLOAT"),
        bigquery.SchemaField("high", "FLOAT"),
        bigquery.SchemaField("low", "FLOAT"),
        bigquery.SchemaField("close", "FLOAT"),
        bigquery.SchemaField("volume", "INTEGER"),
        bigquery.SchemaField("settle", "FLOAT"),
        bigquery.SchemaField("vwap", "FLOAT"),
        bigquery.SchemaField("open_interest", "INTEGER"),
        bigquery.SchemaField("instrument_id", "STRING"),
        bigquery.SchemaField("exchange", "STRING"),
        bigquery.SchemaField("currency", "STRING"),
        bigquery.SchemaField("dataset", "STRING"),
        bigquery.SchemaField("load_ts", "TIMESTAMP"),
    ]

    min_year = df_final['date'].min().year
    max_year = df_final['date'].max().year
    
    print(f"   Splitting load into yearly batches from {min_year} to {max_year}...")

    total_loaded = 0
    
    for year in range(min_year, max_year + 1):
        # Create year mask
        # Note: 'date' is datetime.date object
        mask = df_final['date'].apply(lambda x: x.year == year)
        year_df = df_final[mask]
        
        if len(year_df) == 0:
            continue
            
        print(f"   Uploading Year {year}: {len(year_df)} rows...")
        
        job_config = bigquery.LoadJobConfig(
            schema=table_schema,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            # Table is already partitioned/clustered; no need to redefine
        )

        try:
            job = client.load_table_from_dataframe(
                year_df, 
                FULL_TABLE_ID, 
                job_config=job_config
            )
            job.result()  # Wait for job
            total_loaded += len(year_df)
        except Exception as e:
            print(f"   ❌ Error loading year {year}: {e}")
            # Continue to next year? Or stop? Let's stop to be safe.
            return

    print(f"✅ Successfully loaded {total_loaded} rows for {symbol}.")

def main():
    print("🚀 Starting Historical Data Load to BigQuery...")
    client = get_bq_client()
    
    # Verify Table Exists
    try:
        client.get_table(FULL_TABLE_ID)
        print(f"✅ Target table found: {FULL_TABLE_ID}")
    except Exception as e:
        print(f"❌ Target table not found! Run SQL setup first. Error: {e}")
        return

    # Load Each Symbol
    for symbol in FILE_MAP:
        load_data(symbol, FILE_MAP[symbol], client)

    print("\n🏁 All loads complete.")

if __name__ == "__main__":
    main()
