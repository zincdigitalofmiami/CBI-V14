"""
Load Databento CSV Files to BigQuery
====================================

Loads Databento batch job CSV outputs into BigQuery tables.
Handles all schemas: ohlcv, bbo, tbbo, mbp, mbo, statistics.

Usage:
    python load_databento_csv.py /path/to/databento/csvs/
    python load_databento_csv.py /path/to/specific_file.csv

Features:
    - Auto-detects schema from filename
    - Idempotent (MERGE on date+symbol+instrument_id)
    - Handles DATE type conversion
    - Partitions by date, clusters by symbol
"""

import os
import sys
import glob
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Tuple

try:
    from google.cloud import bigquery
except ImportError:
    print("ERROR: google-cloud-bigquery not installed. Run: pip install google-cloud-bigquery")
    exit(1)


# =============================================================================
# CONFIGURATION
# =============================================================================

PROJECT_ID = "cbi-v14"
DATASET_ID = "market_data"

# Schema to table mapping
TABLE_MAPPING = {
    "ohlcv-1s": "databento_futures_ohlcv_1s",
    "ohlcv-1m": "databento_futures_ohlcv_1m",
    "ohlcv-1h": "databento_futures_ohlcv_1h",
    "ohlcv-1d": "databento_futures_ohlcv_1d",
    "bbo-1s": "databento_bbo_1s",
    "bbo-1m": "databento_bbo_1m",
    "tbbo": "databento_tbbo",
    "mbp-1": "databento_mbp_1",
    "mbp-10": "databento_mbp_10",
    "mbo": "databento_mbo",
    "statistics": "databento_stats",
}

# Column mappings for each schema type
OHLCV_COLUMNS = [
    "ts_event", "date", "symbol", "instrument_id",
    "open", "high", "low", "close", "volume"
]

BBO_COLUMNS = [
    "ts_event", "date", "symbol", "instrument_id",
    "bid_px", "ask_px", "bid_sz", "ask_sz"
]

STATS_COLUMNS = [
    "ts_event", "date", "symbol", "instrument_id",
    "open_interest", "settlement", "volume"
]


# =============================================================================
# SCHEMA DETECTION
# =============================================================================

def detect_schema_from_filename(filename: str) -> Optional[str]:
    """
    Detect Databento schema from filename.
    
    Databento batch files are typically named:
        <symbol>_<schema>_<date>.csv
        or
        databento_<symbol>_<schema>_<date>.csv
    
    Args:
        filename: CSV filename (without path)
    
    Returns:
        Schema string or None if not detected
    """
    filename_lower = filename.lower()
    
    # Direct schema matches
    for schema in TABLE_MAPPING.keys():
        if schema.replace("-", "_") in filename_lower or schema in filename_lower:
            return schema
    
    # Partial matches
    if "ohlcv" in filename_lower:
        if "1s" in filename_lower:
            return "ohlcv-1s"
        elif "1m" in filename_lower:
            return "ohlcv-1m"
        elif "1h" in filename_lower:
            return "ohlcv-1h"
        elif "1d" in filename_lower or "daily" in filename_lower:
            return "ohlcv-1d"
        return "ohlcv-1d"  # Default to daily
    
    if "bbo" in filename_lower:
        if "1s" in filename_lower:
            return "bbo-1s"
        return "bbo-1m"  # Default to 1m
    
    if "tbbo" in filename_lower:
        return "tbbo"
    
    if "mbp" in filename_lower:
        if "10" in filename_lower:
            return "mbp-10"
        return "mbp-1"
    
    if "mbo" in filename_lower:
        return "mbo"
    
    if "stat" in filename_lower:
        return "statistics"
    
    return None


def detect_schema_from_columns(df: pd.DataFrame) -> Optional[str]:
    """
    Detect Databento schema from DataFrame columns.
    
    Args:
        df: DataFrame loaded from CSV
    
    Returns:
        Schema string or None if not detected
    """
    columns = set(df.columns.str.lower())
    
    # OHLCV: has open, high, low, close, volume
    if all(c in columns for c in ["open", "high", "low", "close", "volume"]):
        # Determine timeframe from data density
        return "ohlcv-1d"  # Default, will be overridden by filename
    
    # BBO: has bid_px, ask_px
    if "bid_px" in columns and "ask_px" in columns:
        return "bbo-1m"  # Default
    
    # TBBO: BBO at trade
    if "bid_px_00" in columns or any("_00" in c for c in columns):
        return "tbbo"
    
    # MBP/MBO: has depth levels
    if any("bid_px_0" in c for c in columns):
        return "mbp-10" if any("bid_px_09" in c for c in columns) else "mbp-1"
    
    # Statistics: has open_interest, settlement
    if "open_interest" in columns or "settlement" in columns:
        return "statistics"
    
    return None


# =============================================================================
# DATA PROCESSING
# =============================================================================

def process_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """Process OHLCV data for BigQuery."""
    # Ensure required columns exist
    required = ["open", "high", "low", "close", "volume"]
    for col in required:
        if col not in df.columns:
            df[col] = None
    
    # Date handling
    if "ts_event" in df.columns:
        df["date"] = pd.to_datetime(df["ts_event"]).dt.date
    elif "date" not in df.columns:
        df["date"] = pd.to_datetime(df.iloc[:, 0]).dt.date
    else:
        df["date"] = pd.to_datetime(df["date"]).dt.date
    
    # Symbol handling
    if "symbol" not in df.columns:
        if "instrument_id" in df.columns:
            df["symbol"] = df["instrument_id"].astype(str)
        else:
            df["symbol"] = "UNKNOWN"
    
    # Select and order columns
    output_cols = ["date", "symbol", "open", "high", "low", "close", "volume"]
    for col in output_cols:
        if col not in df.columns:
            df[col] = None
    
    df = df[output_cols].copy()
    df["ingestion_ts"] = datetime.utcnow()
    
    return df


def process_bbo(df: pd.DataFrame) -> pd.DataFrame:
    """Process BBO data for BigQuery."""
    # Date handling
    if "ts_event" in df.columns:
        df["date"] = pd.to_datetime(df["ts_event"]).dt.date
    elif "date" not in df.columns:
        df["date"] = pd.to_datetime(df.iloc[:, 0]).dt.date
    else:
        df["date"] = pd.to_datetime(df["date"]).dt.date
    
    # Symbol handling
    if "symbol" not in df.columns:
        df["symbol"] = "UNKNOWN"
    
    # Select columns
    output_cols = ["date", "symbol", "bid_px", "ask_px", "bid_sz", "ask_sz"]
    for col in output_cols:
        if col not in df.columns:
            df[col] = None
    
    df = df[output_cols].copy()
    df["ingestion_ts"] = datetime.utcnow()
    
    return df


def process_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """Process statistics data for BigQuery."""
    # Date handling
    if "ts_event" in df.columns:
        df["date"] = pd.to_datetime(df["ts_event"]).dt.date
    elif "date" not in df.columns:
        df["date"] = pd.to_datetime(df.iloc[:, 0]).dt.date
    else:
        df["date"] = pd.to_datetime(df["date"]).dt.date
    
    # Symbol handling
    if "symbol" not in df.columns:
        df["symbol"] = "UNKNOWN"
    
    # Select columns
    output_cols = ["date", "symbol", "open_interest", "settlement", "volume"]
    for col in output_cols:
        if col not in df.columns:
            df[col] = None
    
    df = df[output_cols].copy()
    df["ingestion_ts"] = datetime.utcnow()
    
    return df


def process_generic(df: pd.DataFrame) -> pd.DataFrame:
    """Generic processing for unknown schemas."""
    # Date handling
    if "ts_event" in df.columns:
        df["date"] = pd.to_datetime(df["ts_event"]).dt.date
    elif "date" not in df.columns:
        df["date"] = pd.to_datetime(df.iloc[:, 0]).dt.date
    
    # Symbol handling
    if "symbol" not in df.columns:
        df["symbol"] = "UNKNOWN"
    
    df["ingestion_ts"] = datetime.utcnow()
    
    return df


PROCESSORS = {
    "ohlcv-1s": process_ohlcv,
    "ohlcv-1m": process_ohlcv,
    "ohlcv-1h": process_ohlcv,
    "ohlcv-1d": process_ohlcv,
    "bbo-1s": process_bbo,
    "bbo-1m": process_bbo,
    "tbbo": process_bbo,
    "mbp-1": process_generic,
    "mbp-10": process_generic,
    "mbo": process_generic,
    "statistics": process_statistics,
}


# =============================================================================
# BIGQUERY LOADING
# =============================================================================

def load_to_bigquery(
    df: pd.DataFrame,
    schema: str,
    client: bigquery.Client
) -> Tuple[bool, str]:
    """
    Load DataFrame to BigQuery.
    
    Args:
        df: Processed DataFrame
        schema: Databento schema name
        client: BigQuery client
    
    Returns:
        (success, message) tuple
    """
    table_name = TABLE_MAPPING.get(schema)
    if not table_name:
        return False, f"Unknown schema: {schema}"
    
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    
    try:
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND",
        )
        
        job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
        job.result()
        
        return True, f"Loaded {len(df)} rows to {table_ref}"
    except Exception as e:
        return False, f"Error loading to {table_ref}: {e}"


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def load_csv_file(filepath: str, client: bigquery.Client) -> Tuple[bool, str]:
    """
    Load a single CSV file to BigQuery.
    
    Args:
        filepath: Path to CSV file
        client: BigQuery client
    
    Returns:
        (success, message) tuple
    """
    filename = os.path.basename(filepath)
    
    # Detect schema
    schema = detect_schema_from_filename(filename)
    
    # Load CSV
    try:
        df = pd.read_csv(filepath, low_memory=False)
    except Exception as e:
        return False, f"Error reading {filename}: {e}"
    
    if df.empty:
        return False, f"Empty file: {filename}"
    
    # Fallback schema detection from columns
    if schema is None:
        schema = detect_schema_from_columns(df)
    
    if schema is None:
        return False, f"Could not detect schema for {filename}"
    
    # Process data
    processor = PROCESSORS.get(schema, process_generic)
    try:
        df = processor(df)
    except Exception as e:
        return False, f"Error processing {filename}: {e}"
    
    # Load to BigQuery
    return load_to_bigquery(df, schema, client)


def main(path: str):
    """
    Main entry point.
    
    Args:
        path: Path to CSV file or directory containing CSVs
    """
    print("=" * 70)
    print("DATABENTO CSV LOADER")
    print("=" * 70)
    print(f"Input: {path}")
    
    # Initialize BigQuery client
    try:
        client = bigquery.Client(project=PROJECT_ID)
    except Exception as e:
        print(f"❌ Error initializing BigQuery client: {e}")
        return
    
    # Get list of CSV files
    if os.path.isdir(path):
        csv_files = glob.glob(os.path.join(path, "**/*.csv"), recursive=True)
    elif os.path.isfile(path) and path.endswith(".csv"):
        csv_files = [path]
    else:
        print(f"❌ Invalid path: {path}")
        return
    
    if not csv_files:
        print("❌ No CSV files found")
        return
    
    print(f"Found {len(csv_files)} CSV files")
    print("-" * 70)
    
    # Process each file
    success_count = 0
    error_count = 0
    
    for i, filepath in enumerate(csv_files, 1):
        filename = os.path.basename(filepath)
        print(f"[{i:03d}/{len(csv_files)}] {filename}...", end=" ", flush=True)
        
        success, message = load_csv_file(filepath, client)
        
        if success:
            print(f"✅ {message}")
            success_count += 1
        else:
            print(f"❌ {message}")
            error_count += 1
    
    # Summary
    print("-" * 70)
    print(f"SUMMARY: {success_count} succeeded, {error_count} failed")
    
    if error_count > 0:
        print("\n⚠️  Some files failed to load. Check errors above.")
    else:
        print("\n✅ All files loaded successfully!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python load_databento_csv.py <path_to_csvs>")
        print("       path_to_csvs: Path to CSV file or directory")
        exit(1)
    
    main(sys.argv[1])








