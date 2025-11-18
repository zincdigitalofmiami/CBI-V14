#!/usr/bin/env python3
"""
Add palm (CPO) and crude (CL) symbols to Yahoo staging file.
These are needed for views that reference palm_oil_prices and crude_oil_prices.
"""

import pandas as pd
from google.cloud import bigquery
from pathlib import Path

PROJECT_ID = "cbi-v14"
LOCATION = "us-central1"
DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData")

def fetch_palm_data(client: bigquery.Client):
    """Fetch palm oil data from BigQuery."""
    
    query = """
    SELECT 
        DATE(time) as date,
        symbol,
        open as yahoo_open,
        high as yahoo_high,
        low as yahoo_low,
        close as yahoo_close,
        volume as yahoo_volume
    FROM `cbi-v14.forecasting_data_warehouse.palm_oil_prices`
    WHERE symbol IN ('CPO', 'PALM_COMPOSITE')
    ORDER BY time
    """
    
    df = client.query(query, location=LOCATION).to_dataframe()
    print(f"✓ Fetched palm data: {len(df)} rows, symbols: {df['symbol'].unique()}")
    
    return df

def fetch_crude_data(client: bigquery.Client):
    """Fetch crude oil data from BigQuery."""
    
    query = """
    SELECT 
        DATE(time) as date,
        symbol,
        open as yahoo_open,
        high as yahoo_high,
        low as yahoo_low,
        close as yahoo_close,
        volume as yahoo_volume
    FROM `cbi-v14.forecasting_data_warehouse.crude_oil_prices`
    WHERE symbol = 'CL'
    ORDER BY time
    """
    
    df = client.query(query, location=LOCATION).to_dataframe()
    
    # Remove duplicates (there were duplicate rows in the query output)
    df = df.drop_duplicates(subset=['date', 'symbol'])
    
    print(f"✓ Fetched crude data: {len(df)} rows, symbol: {df['symbol'].unique()}")
    
    return df

def merge_with_existing_yahoo(palm_df, crude_df):
    """Merge palm and crude data with existing ZL data."""
    
    staging_file = DRIVE / "staging/yahoo_historical_all_symbols.parquet"
    
    if not staging_file.exists():
        print(f"✗ Staging file not found: {staging_file}")
        return None
    
    # Load existing Yahoo staging (ZL=F only)
    zl_df = pd.read_parquet(staging_file)
    print(f"\nExisting Yahoo staging: {len(zl_df)} rows, symbols: {zl_df['symbol'].unique()}")
    print(f"  Columns: {list(zl_df.columns[:10])}...")
    
    # Prepare palm/crude data to match existing structure
    # ZL has many indicator columns, palm/crude don't - will be NaN
    all_columns = set(zl_df.columns)
    
    for df in [palm_df, crude_df]:
        missing_cols = all_columns - set(df.columns)
        for col in missing_cols:
            df[col] = pd.NA  # Add missing columns as NA
    
    # Reorder columns to match ZL
    palm_df = palm_df[zl_df.columns]
    crude_df = crude_df[zl_df.columns]
    
    # Combine all data
    combined = pd.concat([zl_df, palm_df, crude_df], ignore_index=True)
    
    print(f"\nCombined data:")
    print(f"  Total rows: {len(combined)}")
    print(f"  Symbols: {sorted(combined['symbol'].unique())}")
    print(f"  Date range: {combined['date'].min()} to {combined['date'].max()}")
    print(f"  Columns: {len(combined.columns)}")
    
    # Save updated staging file
    combined.to_parquet(staging_file, index=False)
    print(f"\n✓ Updated {staging_file}")
    
    return combined

def main():
    """Add palm and crude data to Yahoo staging."""
    
    print("="*60)
    print("ADD PALM & CRUDE TO YAHOO STAGING")
    print("="*60)
    
    client = bigquery.Client(project=PROJECT_ID)
    
    print("\n1. Fetching palm oil data...")
    palm_df = fetch_palm_data(client)
    
    print("\n2. Fetching crude oil data...")
    crude_df = fetch_crude_data(client)
    
    print("\n3. Merging with existing Yahoo staging...")
    combined = merge_with_existing_yahoo(palm_df, crude_df)
    
    if combined is not None:
        print("\n" + "="*60)
        print("✓ PALM & CRUDE ADDED TO YAHOO STAGING")
        print("="*60)
        print("\nSummary:")
        print(f"  Total symbols: {combined['symbol'].nunique()}")
        for symbol in sorted(combined['symbol'].unique()):
            count = len(combined[combined['symbol'] == symbol])
            date_range = f"{combined[combined['symbol']==symbol]['date'].min()} to {combined[combined['symbol']==symbol]['date'].max()}"
            print(f"    {symbol}: {count} rows ({date_range})")
    
    return 0

if __name__ == "__main__":
    exit(main())

