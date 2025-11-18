#!/usr/bin/env python3
"""
Check Databento batch jobs and fetch ZL 1-minute data when ready.

This script checks for queued/completed batch jobs for ZL 1-minute data
and downloads them automatically.
"""

import os
import sys
from pathlib import Path
import subprocess

try:
    import databento as db
except ImportError:
    print("❌ databento not installed. Run: pip install databento")
    sys.exit(1)

# Configuration
DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
RAW_DIR = DRIVE / "TrainingData/raw/databento_zl"
DOWNLOADS_DIR = Path.home() / "Downloads"

def get_api_key():
    """Get Databento API key from environment, keychain, or file."""
    # Try environment variable
    api_key = os.environ.get("DATABENTO_API_KEY")
    if api_key:
        return api_key
    
    # Try keychain (macOS)
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
    
    # Try file
    key_file = Path.home() / ".databento.key"
    if key_file.exists():
        return key_file.read_text().strip()
    
    return None

def main():
    """Check for ZL 1-minute data jobs and fetch when ready."""
    
    print("="*80)
    print("DATABENTO ZL 1-MINUTE DATA FETCHER")
    print("="*80)
    
    # Get API key
    api_key = get_api_key()
    if not api_key:
        print("\n❌ No API key found!")
        print("\nSet your Databento API key:")
        print("  security add-generic-password -a databento -s databento_api_key -w 'YOUR_KEY' -U")
        print("  # OR")
        print("  export DATABENTO_API_KEY='YOUR_KEY'")
        return 1
    
    print(f"\n✅ API key found")
    
    # Initialize client
    try:
        client = db.Historical(api_key)
        print("✅ Connected to Databento")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return 1
    
    # List recent batch jobs
    print("\n📋 Checking recent batch jobs...")
    try:
        jobs = client.batch.list_jobs(since="2025-11-01")  # Last 2 weeks
        
        # Filter for ZL jobs
        zl_jobs = []
        for job in jobs:
            if hasattr(job, 'symbols') and job.symbols:
                if any('ZL' in str(s).upper() for s in job.symbols):
                    zl_jobs.append(job)
        
        if not zl_jobs:
            print("\n⚠️  No ZL jobs found in recent history")
            print("\nTo submit a new job:")
            print("  python3 scripts/ingest/download_zl_1min_databento.py")
            return 0
        
        print(f"\n✅ Found {len(zl_jobs)} ZL job(s):")
        
        for job in zl_jobs:
            print(f"\n  Job ID: {job.id}")
            print(f"  Status: {job.state}")
            print(f"  Symbols: {job.symbols}")
            print(f"  Schema: {job.schema if hasattr(job, 'schema') else 'N/A'}")
            print(f"  Created: {job.ts_received if hasattr(job, 'ts_received') else 'N/A'}")
            
            # If done, download
            if job.state == 'done':
                print(f"\n  🎉 Job is READY! Downloading...")
                
                try:
                    # Download to temp location
                    download_path = DOWNLOADS_DIR / f"{job.id}.zip"
                    
                    print(f"  Downloading to: {download_path}")
                    client.batch.download(job.id, str(download_path))
                    print(f"  ✅ Downloaded: {download_path.stat().st_size / 1024 / 1024:.1f} MB")
                    
                    # Extract to RAW_DIR
                    extract_dir = RAW_DIR / job.id
                    extract_dir.mkdir(parents=True, exist_ok=True)
                    
                    print(f"  📦 Extracting to: {extract_dir}")
                    subprocess.run(["unzip", "-o", str(download_path), "-d", str(extract_dir)], check=True)
                    
                    # Count 1-minute files
                    ohlcv_1m_files = list(extract_dir.glob("**/*ohlcv-1m*.json"))
                    print(f"  ✅ Extracted {len(ohlcv_1m_files)} 1-minute OHLCV files")
                    
                    if ohlcv_1m_files:
                        print(f"\n  🎯 SUCCESS! ZL 1-minute data is ready")
                        print(f"\n  Next step: Rerun ZL aggregator")
                        print(f"    python3 scripts/ingest/aggregate_zl_intraday.py")
                    else:
                        print(f"\n  ⚠️  No 1-minute OHLCV files found in download")
                        print(f"    This might be a different schema")
                    
                except Exception as e:
                    print(f"  ❌ Download failed: {e}")
                    
            elif job.state in ['queued', 'processing']:
                print(f"  ⏳ Job is still {job.state}...")
                print(f"  Check status at: https://databento.com/portal/batch/jobs/{job.id}")
                
            elif job.state == 'expired':
                print(f"  ⚠️  Job has expired - resubmit if needed")
                
    except Exception as e:
        print(f"❌ Error checking jobs: {e}")
        return 1
    
    print("\n" + "="*80)
    return 0

if __name__ == "__main__":
    sys.exit(main())

