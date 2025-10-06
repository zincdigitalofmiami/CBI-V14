#!/usr/bin/env python3
"""
ZL Futures Price Ingestion from local CSV files (no external APIs)
Loads daily OHLCV data into BigQuery from files under data/csv/*
"""

import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timedelta
import time
import sys
import argparse
from bigquery_utils import safe_load_to_bigquery

import os

PROJECT_ID = os.environ.get("PROJECT_ID", "cbi-v14")
DATASET_ID = os.environ.get("DATASET_ID", "forecasting_data_warehouse")
TABLE_ID = "soybean_prices_clean"
SYMBOL = "ZL"  # Soybean oil futures

def load_csv_files(csv_dir: str) -> pd.DataFrame:
    """
    Load ZL futures data from local CSV files and normalize columns.
    Accepts files like data/csv/zl*_price-history*.csv (Barchart-style).
    """
    import glob
    pattern1 = os.path.join(csv_dir, "zl*_price-history*.csv")
    pattern2 = os.path.join(csv_dir, "ZL*_price-history*.csv")
    files = sorted(set(glob.glob(pattern1)) | set(glob.glob(pattern2)))
    if not files:
        print(f"No CSV files found in {csv_dir} matching ZL patterns.")
        return pd.DataFrame()

    frames = []
    for path in files:
        try:
            df = pd.read_csv(path)
            cols = {c: c.strip().lower() for c in df.columns}
            df = df.rename(columns=cols)

            # Common column names mapping
            if 'date' in df.columns:
                df['time'] = pd.to_datetime(df['date'], errors='coerce', utc=True)
            elif 'time' in df.columns:
                df['time'] = pd.to_datetime(df['time'], errors='coerce', utc=True)
            else:
                print(f"  Skipping {os.path.basename(path)}: no date/time column")
                continue

            # Normalize price columns with common Barchart variants
            alias_map = {
                'open': ['open'],
                'high': ['high'],
                'low': ['low'],
                'close': ['close', 'close/last', 'close_last', 'last', 'settle'],
                'volume': ['volume', 'vol']
            }
            for target, candidates in alias_map.items():
                if target not in df.columns:
                    for c in candidates:
                        if c in df.columns:
                            df[target] = df[c]
                            break

            # Derive symbol from filename if missing
            if 'symbol' not in df.columns:
                fname = os.path.basename(path)
                sym = 'ZL'
                df['symbol'] = sym

            keep_cols = ['time','symbol','open','high','low','close','volume']
            for c in keep_cols:
                if c not in df.columns:
                    df[c] = pd.NA
            df = df[keep_cols]

            # Drop rows without time or close
            df = df.dropna(subset=['time','close'])

            # Remove duplicates
            df = df.drop_duplicates(subset=['time','symbol'])

            frames.append(df)
            print(f"  Loaded {len(df)} rows from {os.path.basename(path)}")
        except Exception as e:
            print(f"  Failed to load {path}: {e}")

    if not frames:
        return pd.DataFrame()
    merged = pd.concat(frames, ignore_index=True)
    merged = merged.sort_values(['time','symbol'])
    return merged

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
        job = safe_load_to_bigquery(client, df, table_ref, job_config)
        job.result()  # Wait for completion
        print(f"  Success: Loaded {len(df)} rows")
        return True
    except Exception as e:
        print(f"  BigQuery load failed: {e}")
        return False

def backfill_from_csv(csv_dir: str) -> int:
    """Load all ZL CSVs in the given directory into BigQuery."""
    df = load_csv_files(csv_dir)
    if df.empty:
        print("No data found from CSVs.")
        return 0
    ok = load_to_bigquery(df, PROJECT_ID, DATASET_ID, TABLE_ID)
    return len(df) if ok else 0

def update_from_csv(csv_path: str) -> int:
    """Load a single CSV file update (append)."""
    folder = os.path.dirname(csv_path)
    df = load_csv_files(folder)
    if df.empty:
        print("No data found from CSV update.")
        return 0
    ok = load_to_bigquery(df, PROJECT_ID, DATASET_ID, TABLE_ID)
    return len(df) if ok else 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest ZL futures data from local CSV files")
    parser.add_argument("--from-csv-dir", dest="csv_dir", default=os.path.join(os.path.dirname(__file__), "..", "data", "csv"), help="Directory containing ZL CSV files")
    args = parser.parse_args()

    rows = backfill_from_csv(os.path.abspath(args.csv_dir))
    sys.exit(0 if rows > 0 else 1)
