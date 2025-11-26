#!/usr/bin/env python3
"""
Download ALL Databento Historical Data → DIRECT TO BIGQUERY
============================================================

WORKFLOW: Databento API → BigQuery (NO EXTERNAL DRIVE!)

Per MASTER_PLAN.md:
- DataBento is PRIMARY for all futures 2010-present
- ALL data goes DIRECTLY to BigQuery

DOWNLOAD LIST:
- ZL: 1-minute and daily (2010-present)
- MES: 1-second, 1-minute, and daily (2019-present)
- ES: 1-minute and daily (2010-present)
- Plus all other symbols: ZS, ZM, CL, HO, NG, etc.

Target BigQuery Tables:
- market_data.databento_futures_ohlcv_1d (daily)
- market_data.databento_futures_ohlcv_1h (hourly)
- market_data.databento_futures_ohlcv_1m (1-minute)
- market_data.databento_futures_ohlcv_1s (1-second, MES only)

Requirements:
    pip install databento google-cloud-bigquery pandas pyarrow db-dtypes

Usage:
    python3 scripts/ingest/download_ALL_databento_historical.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import pandas as pd
from google.cloud import bigquery
import time
import subprocess
import json

# #region agent log
LOG_PATH = Path("/Users/zincdigital/CBI-V14/.cursor/debug.log")
def debug_log(location, message, data, hypothesis_id=None):
    try:
        entry = {
            "sessionId": "daily-backfill-debug",
            "runId": os.environ.get("RUN_ID", "run1"),
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000)
        }
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except: pass
# #endregion

try:
    import databento as db
except ImportError:
    print("❌ databento not installed. Run: pip install databento")
    sys.exit(1)

# Configuration - DIRECT TO BIGQUERY
PROJECT_ID = "cbi-v14"
DATASET_ID = "market_data"
DATABENTO_DATASET = "GLBX.MDP3"  # CME Globex MDP 3.0

# BQ Table mapping by schema
BQ_TABLE_MAP = {
    "ohlcv-1s": "databento_futures_ohlcv_1s",
    "ohlcv-1m": "databento_futures_ohlcv_1m",
    "ohlcv-1h": "databento_futures_ohlcv_1h",
    "ohlcv-1d": "databento_futures_ohlcv_1d",
}

# Download plan - ZL ENGINE ONLY (5 roots, daily only)
# Focus: ZL + supporting symbols for first baselines
DOWNLOAD_PLAN = [
    # ZL - Soybean Oil (PRIMARY) - daily only for now
    {"root": "ZL", "desc": "Soybean Oil", "schemas": ["ohlcv-1d"], "exchange": "CBOT", "start": "2010-06-06"},
    
    # ZL Supporting Symbols - daily only
    {"root": "ZS", "desc": "Soybeans", "schemas": ["ohlcv-1d"], "exchange": "CBOT", "start": "2010-06-06"},
    {"root": "ZM", "desc": "Soybean Meal", "schemas": ["ohlcv-1d"], "exchange": "CBOT", "start": "2010-06-06"},
    {"root": "CL", "desc": "WTI Crude", "schemas": ["ohlcv-1d"], "exchange": "NYMEX", "start": "2010-06-06"},
    {"root": "HO", "desc": "Heating Oil", "schemas": ["ohlcv-1d"], "exchange": "NYMEX", "start": "2010-06-06"},
]


def get_api_key():
    """Get Databento API key from environment or Keychain."""
    api_key = os.environ.get("DATABENTO_API_KEY")
    
    if not api_key:
        key_file = Path.home() / ".databento.key"
        if key_file.exists():
            api_key = key_file.read_text().strip()
    
    if not api_key:
        try:
            result = subprocess.run(
                ["security", "find-generic-password", "-s", "databento_api_key", "-w"],
                capture_output=True, text=True, check=True
            )
            api_key = result.stdout.strip()
        except:
            pass
    
    return api_key


def get_bq_client():
    """Get BigQuery client."""
    return bigquery.Client(project=PROJECT_ID)


def get_bq_schema_1d():
    """Schema for databento_futures_ohlcv_1d - matches existing BQ table."""
    return [
        bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("open", "FLOAT64"),
        bigquery.SchemaField("high", "FLOAT64"),
        bigquery.SchemaField("low", "FLOAT64"),
        bigquery.SchemaField("close", "FLOAT64"),
        bigquery.SchemaField("volume", "INT64"),
        bigquery.SchemaField("settle", "FLOAT64"),
        bigquery.SchemaField("vwap", "FLOAT64"),
        bigquery.SchemaField("open_interest", "INT64"),
        bigquery.SchemaField("instrument_id", "STRING"),
        bigquery.SchemaField("exchange", "STRING"),
        bigquery.SchemaField("currency", "STRING"),
        bigquery.SchemaField("dataset", "STRING"),
        bigquery.SchemaField("load_ts", "TIMESTAMP"),
    ]

def get_bq_schema_intraday():
    """Schema for databento_futures_ohlcv_1m/1s/1h - matches existing BQ table."""
    return [
        bigquery.SchemaField("ts_event", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("root", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("instrument_id", "INT64"),
        bigquery.SchemaField("open", "FLOAT64"),
        bigquery.SchemaField("high", "FLOAT64"),
        bigquery.SchemaField("low", "FLOAT64"),
        bigquery.SchemaField("close", "FLOAT64"),
        bigquery.SchemaField("volume", "INT64"),
        bigquery.SchemaField("open_interest", "INT64"),
        bigquery.SchemaField("is_spread", "BOOL"),
        # NOTE: BigQuery table defines this as scalar STRING, not ARRAY<STRING>
        bigquery.SchemaField("spread_legs", "STRING"),
        bigquery.SchemaField("publisher_id", "INT64"),
        bigquery.SchemaField("priority_tier", "INT64"),
        bigquery.SchemaField("source_published_at", "TIMESTAMP"),
        bigquery.SchemaField("collection_timestamp", "TIMESTAMP"),
    ]


def fetch_and_load_to_bq(client, bq_client, symbol_info, schema, end_date):
    """Fetch data from Databento and load DIRECTLY to BigQuery."""
    root = symbol_info["root"]
    exchange = symbol_info["exchange"]
    start = symbol_info["start"]
    symbol = f"{root}.FUT"  # Use ROOT.FUT format for parent symbology
    
    # #region agent log
    debug_log("download_ALL_databento_historical.py:167", "fetch_and_load_to_bq entry", {"root": root, "schema": schema, "start": start, "end": end_date}, "H1")
    # #endregion
    
    table_name = BQ_TABLE_MAP[schema]
    full_table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    
    print(f"\n  📊 {root} - {schema}")
    print(f"     Date range: {start} to {end_date}")
    print(f"     Target: {full_table_id}")
    
    try:
        # Fetch data from Databento
        print(f"     Fetching from Databento...")
        
        # #region agent log
        api_start = time.time()
        debug_log("download_ALL_databento_historical.py:185", "API call start", {"root": root, "symbol": symbol, "schema": schema}, "H2")
        # #endregion
        
        data = client.timeseries.get_range(
            dataset=DATABENTO_DATASET,
            symbols=[symbol],
            schema=schema,
            start=start,
            end=end_date,
            stype_in="parent",  # Parent symbology for continuous
        )
        
        # #region agent log
        api_duration = time.time() - api_start
        debug_log("download_ALL_databento_historical.py:195", "API call complete", {"root": root, "duration_sec": api_duration}, "H2")
        # #endregion
        
        # Convert to DataFrame
        # #region agent log
        df_start = time.time()
        debug_log("download_ALL_databento_historical.py:198", "to_df() start", {"root": root}, "H3")
        # #endregion
        
        df = data.to_df()
        
        # #region agent log
        df_duration = time.time() - df_start
        df_size_mb = df.memory_usage(deep=True).sum() / 1024 / 1024 if not df.empty else 0
        debug_log("download_ALL_databento_historical.py:201", "to_df() complete", {"root": root, "rows": len(df), "cols": len(df.columns), "size_mb": df_size_mb, "duration_sec": df_duration, "index_duplicates": df.index.duplicated().sum() if hasattr(df.index, 'duplicated') else 0}, "H3")
        # #endregion
        
        if df.empty:
            print(f"     ⚠️ No data returned")
            # #region agent log
            debug_log("download_ALL_databento_historical.py:204", "Empty DataFrame", {"root": root}, "H4")
            # #endregion
            return 0
        
        print(f"     Got {len(df)} rows")
        
        # Reset index to avoid duplicate index issues - PRESERVE ts_event as a column!
        # #region agent log
        debug_log("download_ALL_databento_historical.py:210", "Before reset_index", {"root": root, "index_type": str(type(df.index)), "index_name": str(df.index.name), "index_duplicates": df.index.duplicated().sum() if hasattr(df.index, 'duplicated') else "N/A"}, "H5")
        # #endregion
        
        # CRITICAL: Use drop=False to preserve ts_event (the DatetimeIndex) as a column
        df = df.reset_index(drop=False)
        
        # Filter out spreads (symbols with "-") and aggregate to one row per date
        if 'symbol' in df.columns:
            # #region agent log
            debug_log("download_ALL_databento_historical.py:214", "Before filtering", {"root": root, "unique_symbols": df['symbol'].nunique(), "total_rows": len(df)}, "H4")
            # #endregion
            
            # Remove spreads (contain "-")
            df_outrights = df[~df['symbol'].str.contains('-', na=False)].copy()
            spreads_removed = len(df) - len(df_outrights)
            print(f"     Removed {spreads_removed} spread rows, {len(df_outrights)} outright contracts remain")
            
            if len(df_outrights) == 0:
                print(f"     ⚠️ No outright contracts found!")
                return 0
            
            # For daily data: aggregate to one row per date (sum volume, use OHLC from highest volume contract)
            if schema == "ohlcv-1d" and 'ts_event' in df_outrights.columns:
                df_outrights['_date'] = pd.to_datetime(df_outrights['ts_event']).dt.date
                
                # For each date, find the contract with highest volume (front month proxy)
                idx_max_vol = df_outrights.groupby('_date')['volume'].idxmax()
                df = df_outrights.loc[idx_max_vol].copy()
                df = df.drop(columns=['_date'])
                print(f"     Aggregated to {len(df)} daily bars (one per date, highest volume contract)")
            else:
                df = df_outrights
            
            # #region agent log
            debug_log("download_ALL_databento_historical.py:240", "After filtering", {"root": root, "rows": len(df)}, "H4")
            # #endregion
        
        # Transform to BQ schema - MATCH EXISTING TABLE EXACTLY
        now = datetime.now(timezone.utc).replace(tzinfo=None)  # Fix deprecation warning
        
        # #region agent log
        build_start = time.time()
        debug_log("download_ALL_databento_historical.py:225", "Building df_bq start", {"root": root, "schema": schema, "df_rows": len(df), "df_cols": list(df.columns)[:5]}, "H5")
        # #endregion
        
        if schema == "ohlcv-1d":
            # Daily bars - matches databento_futures_ohlcv_1d schema
            df_bq = pd.DataFrame(index=df.index)  # Use same index as source
            
            # Derive date from ts_event or DatetimeIndex; never from a RangeIndex
            if 'ts_event' in df.columns:
                ts = pd.to_datetime(df['ts_event'])
            elif isinstance(df.index, pd.DatetimeIndex) or pd.api.types.is_datetime64_any_dtype(df.index):
                ts = pd.to_datetime(df.index)
            else:
                raise ValueError("Cannot derive daily date: missing ts_event and DatetimeIndex")
            
            df_bq['date'] = ts.dt.date
            
            df_bq['symbol'] = root
            df_bq['open'] = df['open'].astype(float) if 'open' in df.columns else None
            df_bq['high'] = df['high'].astype(float) if 'high' in df.columns else None
            df_bq['low'] = df['low'].astype(float) if 'low' in df.columns else None
            df_bq['close'] = df['close'].astype(float) if 'close' in df.columns else None
            df_bq['volume'] = df['volume'].astype('Int64') if 'volume' in df.columns else None
            df_bq['settle'] = None
            df_bq['vwap'] = None
            df_bq['open_interest'] = None
            df_bq['instrument_id'] = df['instrument_id'].astype(str) if 'instrument_id' in df.columns else None
            df_bq['exchange'] = exchange
            df_bq['currency'] = 'USD'
            df_bq['dataset'] = DATABENTO_DATASET
            df_bq['load_ts'] = now
            
            bq_schema = get_bq_schema_1d()
            date_col = 'date'
            
        else:
            # Intraday bars (1s, 1m, 1h) - matches databento_futures_ohlcv_1m schema
            df_bq = pd.DataFrame(index=df.index)  # Use same index as source
            
            if 'ts_event' in df.columns:
                df_bq['ts_event'] = pd.to_datetime(df['ts_event'])
            else:
                df_bq['ts_event'] = pd.to_datetime(df.index)
            
            df_bq['root'] = root
            df_bq['symbol'] = df['symbol'].astype(str) if 'symbol' in df.columns else root
            df_bq['instrument_id'] = df['instrument_id'].astype('Int64') if 'instrument_id' in df.columns else None
            df_bq['open'] = df['open'].astype(float) if 'open' in df.columns else None
            df_bq['high'] = df['high'].astype(float) if 'high' in df.columns else None
            df_bq['low'] = df['low'].astype(float) if 'low' in df.columns else None
            df_bq['close'] = df['close'].astype(float) if 'close' in df.columns else None
            df_bq['volume'] = df['volume'].astype('Int64') if 'volume' in df.columns else None
            df_bq['open_interest'] = None
            df_bq['is_spread'] = False
            df_bq['spread_legs'] = None  # Scalar STRING column in BQ
            df_bq['publisher_id'] = df['publisher_id'].astype('Int64') if 'publisher_id' in df.columns else None
            df_bq['priority_tier'] = 1  # Front month
            df_bq['source_published_at'] = now
            df_bq['collection_timestamp'] = now
            
            bq_schema = get_bq_schema_intraday()
            date_col = 'ts_event'
        
        # #region agent log
        build_duration = time.time() - build_start
        df_bq_size_mb = df_bq.memory_usage(deep=True).sum() / 1024 / 1024 if not df_bq.empty else 0
        debug_log("download_ALL_databento_historical.py:332", "df_bq built", {"root": root, "rows": len(df_bq), "cols": len(df_bq.columns), "size_mb": df_bq_size_mb, "duration_sec": build_duration}, "H5")
        # #endregion
        
        # Load to BigQuery in monthly batches (avoid partition limit for intraday)
        total_loaded = 0
        
        if schema == "ohlcv-1d":
            # Daily: batch by year
            # Extract year from date column (date is already date type, not datetime)
            if date_col == 'date':
                # date column is already date type, access .year directly
                df_bq['_year'] = df_bq[date_col].apply(lambda x: x.year if hasattr(x, 'year') else pd.to_datetime(x).year)
            else:
                df_bq['_year'] = pd.to_datetime(df_bq[date_col]).dt.year
            batches = df_bq.groupby('_year')
        else:
            # Intraday: batch by month
            df_bq['_month'] = df_bq[date_col].dt.to_period('M')
            batches = df_bq.groupby('_month')
        
        for batch_key, batch_df in batches:
            batch_df = batch_df.drop(columns=['_year'] if '_year' in batch_df.columns else ['_month'], errors='ignore')
            
            if len(batch_df) == 0:
                continue
            
            job_config = bigquery.LoadJobConfig(
                schema=bq_schema,
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            )
            
            # #region agent log
            bq_start = time.time()
            debug_log("download_ALL_databento_historical.py:356", "BQ load start", {"root": root, "batch": str(batch_key), "rows": len(batch_df)}, "H1")
            # #endregion
            
            job = bq_client.load_table_from_dataframe(
                batch_df, full_table_id, job_config=job_config
            )
            job.result()
            
            # #region agent log
            bq_duration = time.time() - bq_start
            debug_log("download_ALL_databento_historical.py:364", "BQ load complete", {"root": root, "batch": str(batch_key), "rows": len(batch_df), "duration_sec": bq_duration}, "H1")
            # #endregion
            
            total_loaded += len(batch_df)
            print(f"     Loaded {batch_key}: {len(batch_df)} rows")
        
        print(f"     ✅ Total loaded: {total_loaded} rows")
        # #region agent log
        debug_log("download_ALL_databento_historical.py:370", "fetch_and_load_to_bq exit", {"root": root, "total_loaded": total_loaded}, "H1")
        # #endregion
        return total_loaded
        
    except Exception as e:
        print(f"     ❌ Error: {e}")
        # #region agent log
        debug_log("download_ALL_databento_historical.py:375", "Exception caught", {"root": root, "error": str(e), "error_type": type(e).__name__}, "H4")
        # #endregion
        import traceback
        traceback.print_exc()
        return 0


def main():
    """Download ALL historical Databento data → DIRECT TO BIGQUERY."""
    
    print("="*80)
    print("DATABENTO → BIGQUERY DIRECT LOAD")
    print("="*80)
    print(f"\nDataset: {DATABENTO_DATASET}")
    print(f"Target Project: {PROJECT_ID}")
    print("NO EXTERNAL DRIVE - DIRECT TO BQ!")
    
    # Get API key
    api_key = get_api_key()
    if not api_key:
        print("\n❌ DATABENTO_API_KEY not found!")
        print("\nOptions:")
        print("  1. export DATABENTO_API_KEY='your-key'")
        print("  2. Save to ~/.databento.key")
        print("  3. security add-generic-password -s databento_api_key -a $USER -w 'key'")
        return 1
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    # Initialize clients
    print("\n🔌 Connecting...")
    db_client = db.Historical(api_key)
    bq_client = get_bq_client()
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    # Process each symbol/schema
    total_symbols = len(DOWNLOAD_PLAN)
    total_rows = 0
    
    print(f"\n📦 Processing {total_symbols} symbols...")
    
    # #region agent log
    main_start = time.time()
    debug_log("download_ALL_databento_historical.py:431", "Main loop start", {"total_symbols": total_symbols, "end_date": end_date}, "H1")
    # #endregion
    
    for i, symbol_info in enumerate(DOWNLOAD_PLAN, 1):
        root = symbol_info["root"]
        # #region agent log
        symbol_start = time.time()
        debug_log("download_ALL_databento_historical.py:435", "Processing symbol", {"symbol_num": i, "total": total_symbols, "root": root, "schemas": symbol_info["schemas"]}, "H1")
        # #endregion
        
        print(f"\n{'='*80}")
        print(f"[{i}/{total_symbols}] {root} - {symbol_info['desc']}")
        print(f"{'='*80}")
        
        for schema in symbol_info["schemas"]:
            rows = fetch_and_load_to_bq(
                db_client, bq_client, symbol_info, schema, end_date
            )
            total_rows += rows
            time.sleep(1)  # Rate limit
        
        # #region agent log
        symbol_duration = time.time() - symbol_start
        debug_log("download_ALL_databento_historical.py:450", "Symbol complete", {"root": root, "duration_sec": symbol_duration, "rows_this_symbol": rows if 'rows' in locals() else 0}, "H1")
        # #endregion
    
    # Summary
    print("\n" + "="*80)
    print("LOAD COMPLETE")
    print("="*80)
    print(f"✅ Total rows loaded to BigQuery: {total_rows:,}")
    
    # Verify counts
    print("\n📊 Verification:")
    for schema, table in BQ_TABLE_MAP.items():
        result = bq_client.query(f"SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{DATASET_ID}.{table}`").result()
        for row in result:
            print(f"   {table}: {row.cnt:,} rows")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
