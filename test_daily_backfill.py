#!/usr/bin/env python3
"""Test script to debug daily backfill performance issues."""
import pandas as pd
from datetime import datetime, timedelta, date, timezone
from google.cloud import bigquery
import databento as db
import json
import time

LOG_PATH = "/Users/zincdigital/CBI-V14/.cursor/debug.log"

def debug_log(location, message, data, hypothesis_id=None):
    try:
        entry = {
            "sessionId": "daily-backfill-debug",
            "runId": "test-run",
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000)
        }
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except: pass

PROJECT_ID = 'cbi-v14'
DATASET_ID = 'market_data'
DATASET = 'GLBX.MDP3'
API_KEY = open('/Users/zincdigital/.databento.key').read().strip()

bq = bigquery.Client(project=PROJECT_ID)
dbh = db.Historical(API_KEY)

# Test with just 3 symbols
roots = ['ES', 'CL', 'GC']
start = (date.today() - timedelta(days=365))
end = date.today()

debug_log("test_daily_backfill.py:main", "Script start", {"roots": roots, "start": str(start), "end": str(end)}, "H1")

for root in roots:
    debug_log("test_daily_backfill.py:loop", "Processing symbol", {"root": root}, "H1")
    print(f"\n=== {root} ===")
    
    api_start = time.time()
    debug_log("test_daily_backfill.py:api", "API call start", {"root": root}, "H2")
    
    try:
        data = dbh.timeseries.get_range(
            dataset=DATASET,
            symbols=[f"{root}.FUT"],
            schema='ohlcv-1d',
            start=start.isoformat(),
            end=end.isoformat(),
            stype_in='parent'
        )
        
        api_duration = time.time() - api_start
        debug_log("test_daily_backfill.py:api", "API call complete", {"root": root, "duration_sec": api_duration}, "H2")
        
        df_start = time.time()
        debug_log("test_daily_backfill.py:df", "to_df() start", {"root": root}, "H3")
        
        df = data.to_df()
        
        df_duration = time.time() - df_start
        df_size_mb = df.memory_usage(deep=True).sum() / 1024 / 1024 if not df.empty else 0
        debug_log("test_daily_backfill.py:df", "to_df() complete", {"root": root, "rows": len(df), "size_mb": df_size_mb, "duration_sec": df_duration}, "H3")
        
        print(f"  Got {len(df)} rows, {df_size_mb:.2f} MB")
        print(f"  API: {api_duration:.1f}s, DataFrame: {df_duration:.1f}s")
        
    except Exception as e:
        debug_log("test_daily_backfill.py:error", "Exception", {"root": root, "error": str(e), "error_type": type(e).__name__}, "H4")
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()

debug_log("test_daily_backfill.py:main", "Script complete", {}, "H1")
print("\n✅ Test complete - check logs")

