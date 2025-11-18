#!/usr/bin/env python3
"""
Check Databento batch job status for ZL 1-minute data.
Uses the Databento Historical API to list and check jobs.
"""

import os
import sys
from pathlib import Path
import subprocess

try:
    import databento as db
except ImportError:
    print("Installing databento...")
    subprocess.run([sys.executable, "-m", "pip", "install", "databento"], check=True)
    import databento as db

def get_api_key():
    """Get Databento API key from keychain or environment."""
    # Try keychain first
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-w", "-a", "databento", "-s", "databento_api_key"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    
    # Try environment
    if os.environ.get("DATABENTO_API_KEY"):
        return os.environ["DATABENTO_API_KEY"]
    
    # Try file
    key_file = Path.home() / ".databento.key"
    if key_file.exists():
        return key_file.read_text().strip()
    
    # Try CBI keychain manager
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
        from utils.keychain_manager import get_api_key as get_key
        key = get_key("DATABENTO_API_KEY")
        if key:
            return key
    except:
        pass
    
    return None

def main():
    print("="*80)
    print("DATABENTO BATCH JOBS STATUS CHECK")
    print("="*80)
    
    api_key = get_api_key()
    if not api_key:
        print("\n❌ No API key found!")
        print("\nTo check jobs, provide your Databento API key:")
        print("  security add-generic-password -a databento -s databento_api_key -w 'YOUR_KEY' -U")
        print("\nOr check manually: https://databento.com/portal/batch")
        return 1
    
    print("✅ API key found, connecting to Databento...")
    
    try:
        client = db.Historical(api_key)
        print("✅ Connected\n")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return 1
    
    # List recent jobs
    print("📋 Recent Batch Jobs (last 30 days):")
    print("-" * 80)
    
    try:
        jobs = client.batch.list_jobs()
        
        if not jobs:
            print("No batch jobs found")
            return 0
        
        # Sort by most recent
        jobs = sorted(jobs, key=lambda x: x.ts_received if hasattr(x, 'ts_received') else '', reverse=True)
        
        zl_jobs = []
        for i, job in enumerate(jobs[:20], 1):  # Show last 20 jobs
            job_id = job.id if hasattr(job, 'id') else 'unknown'
            state = job.state if hasattr(job, 'state') else 'unknown'
            symbols = job.symbols if hasattr(job, 'symbols') else []
            schema = job.schema if hasattr(job, 'schema') else 'unknown'
            ts = job.ts_received if hasattr(job, 'ts_received') else 'unknown'
            
            # Check if ZL job
            is_zl = any('ZL' in str(s).upper() for s in symbols) if symbols else False
            is_1m = 'ohlcv-1m' in str(schema).lower() or 'ohlcv-1' in str(schema).lower()
            
            marker = ""
            if is_zl and is_1m:
                marker = " ⭐ ZL 1-MINUTE"
                zl_jobs.append(job)
            elif is_zl:
                marker = " 🔍 ZL (other timeframe)"
            
            print(f"{i}. Job ID: {job_id}{marker}")
            print(f"   Status: {state}")
            print(f"   Symbols: {symbols}")
            print(f"   Schema: {schema}")
            print(f"   Created: {ts}")
            
            if state == 'done':
                print(f"   ✅ READY TO DOWNLOAD")
            elif state in ['queued', 'processing']:
                print(f"   ⏳ Still {state}...")
            print()
        
        # Summary of ZL 1-minute jobs
        if zl_jobs:
            print("="*80)
            print(f"🎯 FOUND {len(zl_jobs)} ZL 1-MINUTE JOB(S)")
            print("="*80)
            
            for job in zl_jobs:
                print(f"\nJob ID: {job.id}")
                print(f"Status: {job.state}")
                
                if job.state == 'done':
                    print(f"\n🎉 JOB IS READY TO DOWNLOAD!")
                    print(f"\nDownload commands:")
                    print(f"  # Via CLI:")
                    print(f"  databento batch download {job.id} --output-dir ~/Downloads")
                    print(f"\n  # Or via portal:")
                    print(f"  https://databento.com/portal/batch/jobs/{job.id}")
                    print(f"\n  # Then extract:")
                    print(f"  cd ~/Downloads")
                    print(f'  unzip -o {job.id}.zip -d "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/databento_zl/{job.id}/"')
                    print(f'  python3 /Users/kirkmusick/Documents/GitHub/CBI-V14/scripts/ingest/aggregate_zl_intraday.py')
                    
                elif job.state in ['queued', 'processing']:
                    print(f"⏳ Job still {job.state}. Check again in a few minutes.")
                    print(f"   Monitor at: https://databento.com/portal/batch/jobs/{job.id}")
        else:
            print("="*80)
            print("❓ No ZL 1-minute jobs found in recent history")
            print("="*80)
            print("\nTo submit a new ZL 1-minute job:")
            print("  python3 scripts/ingest/download_zl_1min_databento.py")
            
    except Exception as e:
        print(f"❌ Error listing jobs: {e}")
        print("\nFallback: Check portal manually")
        print("  https://databento.com/portal/batch")
        return 1
    
    print("\n" + "="*80)
    return 0

if __name__ == "__main__":
    sys.exit(main())

