#!/usr/bin/env python3
"""
MES 1-Minute Data Collector
Collects MES futures 1-minute OHLCV data from DataBento and saves to staging.

Usage:
    python3 scripts/live/collect_mes_1m.py --once          # Run once
    python3 scripts/live/collect_mes_1m.py --interval 60    # Run every 60 seconds
"""

import argparse
import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

try:
    import databento as db
except ImportError:
    print("ERROR: databento package not installed. Run: pip install databento")
    sys.exit(1)

# Configuration
DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
LIVE_DIR = DRIVE / "TrainingData/live/MES/1m"
STATE_FILE = LIVE_DIR / "state.json"
LIVE_DIR.mkdir(parents=True, exist_ok=True)

def get_api_key():
    """Get DataBento API key from keychain or environment."""
    # Try environment first
    api_key = os.environ.get('DATABENTO_API_KEY')
    if api_key:
        return api_key
    
    # Try keychain
    keychain_locations = [
        ("databento", "databento_api_key"),
        ("default", "cbi-v14.DATABENTO_API_KEY"),
    ]
    for account, service in keychain_locations:
        try:
            result = subprocess.run(
                ["security", "find-generic-password", "-w", "-a", account, "-s", service],
                capture_output=True,
                text=True,
                check=True
            )
            api_key = result.stdout.strip()
            if api_key:
                return api_key
        except:
            continue
    
    return None

def load_state():
    """Load last collection timestamp."""
    if STATE_FILE.exists():
        try:
            import json
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                return state.get('last_ts')
        except:
            return None
    return None

def save_state(timestamp):
    """Save last collection timestamp."""
    import json
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump({'last_ts': str(timestamp)}, f)

def collect_mes_1m(lookback_minutes=120):
    """Collect MES 1-minute data."""
    api_key = get_api_key()
    if not api_key:
        print("ERROR: DATABENTO_API_KEY not found")
        return 0
    
    client = db.Historical(api_key)
    
    # Get dataset range
    try:
        rng = client.metadata.get_dataset_range('GLBX.MDP3')
        end_s = rng['schema']['ohlcv-1m']['end']
        end_dt = datetime.fromisoformat(end_s.replace('Z', '+00:00'))
    except:
        end_dt = datetime.now()
    
    # Determine start time
    last_ts = load_state()
    if last_ts:
        try:
            start_dt = datetime.fromisoformat(last_ts.replace('Z', '+00:00')) + timedelta(minutes=1)
            if start_dt > end_dt:
                start_dt = end_dt - timedelta(minutes=lookback_minutes)
        except:
            start_dt = end_dt - timedelta(minutes=lookback_minutes)
    else:
        start_dt = end_dt - timedelta(minutes=lookback_minutes)
    
    print(f"📊 Collecting MES 1m data: {start_dt} to {end_dt}")
    
    try:
        data = client.timeseries.get_range(
            dataset='GLBX.MDP3',
            symbols=['MES.FUT'],
            stype_in='parent',
            schema='ohlcv-1m',
            start=start_dt.strftime('%Y-%m-%dT%H:%M:%S'),
            end=end_dt.strftime('%Y-%m-%dT%H:%M:%S'),
        )
        
        df = data.to_df()
        if df is None or df.empty:
            print("   No new data")
            return 0
        
        # Exclude calendar spreads
        df = df[~df['symbol'].astype(str).str.contains('-')]
        
        if df.empty:
            print("   No data after filtering spreads")
            return 0
        
        # Group by date and save
        total_rows = 0
        for date_key, group in df.groupby(df.index.date):
            date_str = pd.Timestamp(date_key).strftime('%Y-%m-%d')
            out_dir = LIVE_DIR / f"date={date_str}"
            out_dir.mkdir(parents=True, exist_ok=True)
            
            filename = out_dir / f"mes_1m_{int(datetime.now().timestamp())}.parquet"
            group.to_parquet(filename, index=True)
            total_rows += len(group)
            print(f"   ✅ Saved {len(group)} rows to {filename}")
        
        # Update state
        if not df.empty:
            save_state(df.index.max())
        
        print(f"✅ Total: {total_rows} rows collected")
        return total_rows
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 0

def main():
    parser = argparse.ArgumentParser(description='Collect MES 1-minute data')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--interval', type=int, default=60, help='Collection interval in seconds')
    parser.add_argument('--lookback', type=int, default=120, help='Minutes to backfill on first run')
    
    args = parser.parse_args()
    
    if args.once:
        collect_mes_1m(args.lookback)
        return 0
    
    # Continuous mode
    print(f"🚀 Starting MES 1-minute collection (interval: {args.interval}s)")
    print("   Press Ctrl+C to stop")
    
    try:
        while True:
            collect_mes_1m(args.lookback)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n✅ Collection stopped")

if __name__ == '__main__':
    sys.exit(main())





