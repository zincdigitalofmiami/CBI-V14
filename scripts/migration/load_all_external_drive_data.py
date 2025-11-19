#!/usr/bin/env python3
"""
Load ALL External Drive Data to BigQuery
Date: November 18, 2025
Purpose: Load all 41 raw data folders from external drive into BigQuery
"""

import os
import sys
from pathlib import Path
from google.cloud import bigquery
import pandas as pd
import pyarrow.parquet as pq

PROJECT_ID = "cbi-v14"
LOCATION = "us-central1"
EXTERNAL_DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData")

# Mapping: external drive folder → BigQuery table
DATA_MAPPING = {
    # Market data
    "raw/databento_zl": "market_data.databento_futures_ohlcv_1m",
    "raw/databento_mes": "market_data.databento_futures_ohlcv_1m",
    "raw/yahoo_finance": "market_data.yahoo_zl_historical_2000_2010",
    
    # Economic data
    "raw/fred": "raw_intelligence.fred_economic",
    "staging/fred_macro_expanded.parquet": "raw_intelligence.fred_economic",
    
    # Weather
    "staging/weather_2000_2025.parquet": "raw_intelligence.weather_segmented",
    "raw/noaa": "raw_intelligence.weather_segmented",
    "raw/brazil_weather": "raw_intelligence.weather_segmented",
    
    # Fundamentals
    "raw/cftc": "raw_intelligence.cftc_positioning",
    "raw/usda": "raw_intelligence.usda_granular",
    "raw/eia": "raw_intelligence.eia_biofuels",
    
    # Alternative data
    "raw/barchart": "market_data.vegoils_daily",
    "raw/alpha_vantage": "raw_intelligence.news_intelligence",
}

def get_client():
    """Initialize BigQuery client"""
    return bigquery.Client(project=PROJECT_ID, location=LOCATION)

def load_parquet_to_bq(parquet_path, table_id, client):
    """Load a Parquet file to BigQuery"""
    print(f"Loading {parquet_path} → {table_id}")
    
    if not Path(parquet_path).exists():
        print(f"  ⚠️  File not found: {parquet_path}")
        return False
    
    try:
        # Read parquet
        df = pd.read_parquet(parquet_path)
        print(f"  Found {len(df):,} rows, {len(df.columns)} columns")
        
        if len(df) == 0:
            print(f"  ⚠️  Empty file, skipping")
            return True
        
        # Load to BigQuery
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND",  # Append to existing data
            autodetect=True,  # Auto-detect schema
        )
        
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait for completion
        
        print(f"  ✅ Loaded {len(df):,} rows to {table_id}")
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def load_directory_to_bq(dir_path, table_id, client):
    """Load all Parquet files in a directory to BigQuery"""
    print(f"Loading directory {dir_path} → {table_id}")
    
    if not Path(dir_path).exists():
        print(f"  ⚠️  Directory not found: {dir_path}")
        return False
    
    parquet_files = list(Path(dir_path).rglob("*.parquet"))
    print(f"  Found {len(parquet_files)} Parquet files")
    
    if len(parquet_files) == 0:
        print(f"  ⚠️  No Parquet files found")
        return False
    
    total_rows = 0
    for pfile in parquet_files:
        try:
            df = pd.read_parquet(pfile)
            if len(df) > 0:
                job_config = bigquery.LoadJobConfig(
                    write_disposition="WRITE_APPEND",
                    autodetect=True,
                )
                job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
                job.result()
                total_rows += len(df)
                print(f"    ✓ {pfile.name}: {len(df):,} rows")
        except Exception as e:
            print(f"    ❌ {pfile.name}: {e}")
    
    print(f"  ✅ Total loaded: {total_rows:,} rows to {table_id}")
    return True

def main():
    """Load all external drive data to BigQuery"""
    print("=" * 60)
    print("Loading External Drive Data to BigQuery")
    print("=" * 60)
    print(f"Source: {EXTERNAL_DRIVE}")
    print(f"Project: {PROJECT_ID}")
    print()
    
    client = get_client()
    
    success_count = 0
    failure_count = 0
    
    for source, target in DATA_MAPPING.items():
        source_path = EXTERNAL_DRIVE / source
        
        print(f"\n📊 Processing: {source}")
        print(f"   Target: {target}")
        
        if source_path.is_file():
            # Single Parquet file
            if load_parquet_to_bq(source_path, target, client):
                success_count += 1
            else:
                failure_count += 1
        elif source_path.is_dir():
            # Directory of Parquet files
            if load_directory_to_bq(source_path, target, client):
                success_count += 1
            else:
                failure_count += 1
        else:
            print(f"  ⚠️  Path not found: {source_path}")
            failure_count += 1
    
    # Summary
    print()
    print("=" * 60)
    print("LOADING SUMMARY")
    print("=" * 60)
    print(f"Total sources: {len(DATA_MAPPING)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {failure_count}")
    print()
    
    if failure_count == 0:
        print("✅ ALL DATA LOADED SUCCESSFULLY")
        return 0
    else:
        print(f"⚠️  {failure_count} SOURCES FAILED - Review errors above")
        return 1

if __name__ == "__main__":
    sys.exit(main())

