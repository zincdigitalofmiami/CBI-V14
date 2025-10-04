#!/usr/bin/env python3
"""
ZL Futures Price Ingestion from Polygon.io
Backfills 5 years of daily OHLCV data into BigQuery
"""

import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timedelta
import time
import sys
import argparse

POLYGON_API_KEY = "NviTUrYkic8_0Tk_mHj63W8luEvcTyMJ"
PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"
TABLE_ID = "soybean_prices"
SYMBOL = "ZL"  # Soybean oil futures

def fetch_polygon_data(symbol, start_date, end_date, max_retries=3):
    """
    Fetch daily aggregates from Polygon.io with retry logic
    
    API Docs: https://polygon.io/docs/stocks/get_v2_aggs_ticker__stocksticker__range__multiplier___timespan___from___to
    Rate limit: 5 requests/minute on free tier
    """
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{start_date}/{end_date}"
    params = {
        "apiKey": POLYGON_API_KEY,
        "adjusted": "true",
        "sort": "asc",
        "limit": 50000  # Polygon max
    }
    
    for attempt in range(max_retries):
        try:
            print(f"  Fetching {symbol} from {start_date} to {end_date} (attempt {attempt + 1})")
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 429:
                print(f"  Rate limited. Waiting 60 seconds...")
                time.sleep(60)
                continue
                
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "ERROR":
                print(f"  API Error: {data.get('error', 'Unknown error')}")
                return None
                
            if "results" not in data or not data["results"]:
                print(f"  No data returned for {start_date} to {end_date}")
                return None
                
            print(f"  Success: {len(data['results'])} bars retrieved")
            return data["results"]
            
        except requests.exceptions.RequestException as e:
            print(f"  Request failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                return None
    
    return None

def polygon_to_dataframe(results, symbol):
    """
    Convert Polygon.io results to BigQuery-compatible DataFrame
    
    Polygon schema:
    - t: timestamp in milliseconds
    - o: open price
    - h: high price
    - l: low price
    - c: close price
    - v: volume
    """
    if not results:
        return pd.DataFrame()
    
    df = pd.DataFrame(results)
    
    # Convert milliseconds to datetime
    df['time'] = pd.to_datetime(df['t'], unit='ms', utc=True)
    
    # Rename columns to match BigQuery schema
    df = df.rename(columns={
        'o': 'open',
        'h': 'high',
        'l': 'low',
        'c': 'close',
        'v': 'volume'
    })
    
    # Add symbol column
    df['symbol'] = symbol
    
    # Select only needed columns in correct order
    df = df[['time', 'symbol', 'open', 'high', 'low', 'close', 'volume']]
    
    # Remove any duplicates
    df = df.drop_duplicates(subset=['time', 'symbol'])
    
    return df

def load_to_bigquery(df, project_id, dataset_id, table_id):
    """
    Load DataFrame to BigQuery with error handling
    Uses WRITE_APPEND to avoid overwriting existing data
    """
    if df.empty:
        print("  Empty DataFrame, skipping BigQuery load")
        return False
    
    client = bigquery.Client(project=project_id)
    table_ref = f"{project_id}.{dataset_id}.{table_id}"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",  # Append to existing data
        schema=[
            bigquery.SchemaField("time", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("open", "FLOAT64"),
            bigquery.SchemaField("high", "FLOAT64"),
            bigquery.SchemaField("low", "FLOAT64"),
            bigquery.SchemaField("close", "FLOAT64", mode="REQUIRED"),
            bigquery.SchemaField("volume", "INT64"),
        ],
    )
    
    try:
        print(f"  Loading {len(df)} rows to {table_ref}")
        job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
        job.result()  # Wait for completion
        print(f"  Success: Loaded {len(df)} rows")
        return True
    except Exception as e:
        print(f"  BigQuery load failed: {e}")
        return False

def backfill_historical_data(symbol, years=5):
    """
    Backfill historical data in 6-month chunks to avoid API limits
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)
    
    print(f"\nBackfilling {symbol} from {start_date.date()} to {end_date.date()}")
    print("=" * 60)
    
    chunk_months = 6
    current_start = start_date
    total_rows = 0
    
    while current_start < end_date:
        current_end = min(current_start + timedelta(days=chunk_months * 30), end_date)
        
        start_str = current_start.strftime("%Y-%m-%d")
        end_str = current_end.strftime("%Y-%m-%d")
        
        print(f"\nChunk: {start_str} to {end_str}")
        
        # Fetch data
        results = fetch_polygon_data(symbol, start_str, end_str)
        
        if results:
            # Convert to DataFrame
            df = polygon_to_dataframe(results, symbol)
            
            # Load to BigQuery
            if load_to_bigquery(df, PROJECT_ID, DATASET_ID, TABLE_ID):
                total_rows += len(df)
        
        # Move to next chunk
        current_start = current_end + timedelta(days=1)
        
        # Rate limiting: wait 12 seconds between chunks (5 req/min)
        if current_start < end_date:
            print("  Waiting 12 seconds (rate limit)...")
            time.sleep(12)
    
    print(f"\n{'=' * 60}")
    print(f"Backfill complete: {total_rows} total rows loaded")
    return total_rows

def update_recent_data(symbol, days=5):
    """
    Update with most recent data (for daily refresh)
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    print(f"\nUpdating {symbol} for last {days} days")
    print("=" * 60)
    
    results = fetch_polygon_data(symbol, start_str, end_str)
    
    if results:
        df = polygon_to_dataframe(results, symbol)
        if load_to_bigquery(df, PROJECT_ID, DATASET_ID, TABLE_ID):
            print(f"Update complete: {len(df)} rows loaded")
            return len(df)
    
    print("Update failed")
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest ZL futures data from Polygon.io")
    parser.add_argument("--backfill", action="store_true", help="Backfill 5 years of historical data")
    parser.add_argument("--years", type=int, default=5, help="Number of years to backfill (default: 5)")
    parser.add_argument("--update", action="store_true", help="Update with last 5 days of data")
    parser.add_argument("--days", type=int, default=5, help="Number of days to update (default: 5)")
    
    args = parser.parse_args()
    
    if args.backfill:
        rows = backfill_historical_data(SYMBOL, years=args.years)
        sys.exit(0 if rows > 0 else 1)
    elif args.update:
        rows = update_recent_data(SYMBOL, days=args.days)
        sys.exit(0 if rows > 0 else 1)
    else:
        parser.print_help()
        sys.exit(1)
