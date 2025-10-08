#!/usr/bin/env python3
import os
import argparse
import pandas as pd
from google.cloud import bigquery
from pathlib import Path
from bigquery_utils import safe_load_to_bigquery

# Configuration
PROJECT_ID = os.environ.get("PROJECT_ID", "cbi-v14")
DATASET_ID = os.environ.get("DATASET_ID", "forecasting_data_warehouse")
CSV_DIR = Path(os.environ.get("CSV_DIR", "/Users/zincdigital/CBI-V14/data/csv"))

# Contract prefix to canonical table mapping (one table per commodity)
ROUTING = {
    'ZL': 'soybean_oil_prices',   # Soybean Oil
    'ZS': 'soybean_prices',       # Soybeans
    'ZM': 'soybean_meal_prices',  # Soybean Meal
    'ZC': 'corn_prices',          # Corn
    'CT': 'cotton_prices',        # Cotton
    'CC': 'cocoa_prices',         # Cocoa
    'ZN': 'treasury_prices',      # 10Y Treasury Note
    'FC': 'palm_oil_prices',      # Palm Oil (FCPO - Bursa Malaysia)
    'FCPO': 'palm_oil_prices',    # Palm Oil alternate naming
    'PALM': 'palm_oil_prices',    # Palm Oil generic
}

def normalize_df(df: pd.DataFrame, symbol: str = None) -> pd.DataFrame:
    # Remove trailing lines like "Downloaded from..."
    if 'Time' in df.columns:
        df = df[~df['Time'].astype(str).str.contains('Downloaded', na=False)]

    # Standardize column names
    rename_map = {
        'Time': 'time',
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Last': 'close',
        'Close': 'close',
        'Volume': 'volume',
    }
    df = df.rename(columns=rename_map)
    df['time'] = pd.to_datetime(df['time'], errors='coerce')
    df = df.dropna(subset=['time', 'close'])
    df['volume'] = pd.to_numeric(df.get('volume', 0), errors='coerce').fillna(0).astype('int64')
    
    # Add canonical metadata
    import uuid
    df['source_name'] = 'Barchart'
    df['confidence_score'] = 0.90  # High confidence for Barchart data
    df['ingest_timestamp_utc'] = pd.Timestamp.utcnow()
    df['provenance_uuid'] = str(uuid.uuid4())
    
    # Select columns based on what exists in target table
    base_cols = ['time', 'open', 'high', 'low', 'close', 'volume']
    meta_cols = ['source_name', 'confidence_score', 'ingest_timestamp_utc', 'provenance_uuid']
    
    # Only include columns that exist
    available_cols = [c for c in base_cols if c in df.columns]
    return df[available_cols + meta_cols]

def derive_symbol_and_table(contract: str):
    contract = contract.upper()
    prefix = ''.join([c for c in contract if c.isalpha()])[:2]  # e.g., ZL, ZS, ZN
    symbol = prefix
    table = ROUTING.get(prefix)
    return symbol, table

def main():
    parser = argparse.ArgumentParser(description="Route Barchart CSVs to canonical commodity tables")
    parser.add_argument('--dry-run', action='store_true', help='Print file→table mapping without loading')
    parser.add_argument('--load', action='store_true', help='Load mapped files into canonical tables')
    parser.add_argument('--skip-symbols', default="", help='Comma-separated list of symbols to skip (e.g., ZL,FL)')
    parser.add_argument('--only-symbols', default="", help='Comma-separated list of symbols to include exclusively')
    args = parser.parse_args()

    csv_files = sorted(CSV_DIR.glob("*price-history*.csv"))
    if not csv_files:
        print("No CSV files found in", CSV_DIR)
        return

    client = bigquery.Client(project=PROJECT_ID)
    total_rows = 0

    print(f"PROJECT_ID={PROJECT_ID} DATASET_ID={DATASET_ID}")
    print("Mode:", "DRY-RUN" if args.dry_run and not args.load else "LOAD")

    skip = {s.strip().upper() for s in args.skip_symbols.split(',') if s.strip()}
    only = {s.strip().upper() for s in args.only_symbols.split(',') if s.strip()}

    for csv_file in csv_files:
        contract = csv_file.stem.split('_')[0]
        symbol, table = derive_symbol_and_table(contract)
        if not table:
            print(f"SKIP: {csv_file.name} → Unknown mapping for contract '{contract}'")
            continue

        # Filters
        if only and symbol not in only:
            print(f"SKIP (only-symbols): {csv_file.name} → symbol={symbol}")
            continue
        if symbol in skip:
            print(f"SKIP (skip-symbols): {csv_file.name} → symbol={symbol}")
            continue

        full_table_id = f"{PROJECT_ID}.{DATASET_ID}.{table}"
        df_raw = pd.read_csv(csv_file)
        df = normalize_df(df_raw)
        df.insert(1, 'symbol', symbol)

        print(f"MAP: {csv_file.name} → symbol={symbol} → table={full_table_id} rows={len(df)}")

        if args.load:
            job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
            job = safe_load_to_bigquery(client, df, full_table_id, job_config)
            if job:
                total_rows += len(df)

    if args.load:
        print(f"\nLoaded total rows: {total_rows}")

if __name__ == "__main__":
    main()
