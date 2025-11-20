#!/usr/bin/env python3
"""
Download ALL Databento Historical Data - Complete Universe
===========================================================

Per MASTER_PLAN.md lines 175-184, 227-259:
- DataBento is PRIMARY for all futures 2010-present
- Yahoo Finance is bridge for ZL ONLY 2000-2010
- Historical DataBento downloads ARE APPROVED (included in plan)
- "ALL futures 2010-present (primary source)"

This script downloads ALL futures historical from Databento for CBI-V14.
User directive: "we need it all, and dont forget about the weather segmentations"

COMPLETE DOWNLOAD LIST (26 symbols):
- ZL, ZS, ZM (Soy Complex) - 1-minute + daily
- MES, ES (Equity Indices - verify MES, download ES) - 1-minute + daily  
- NQ, MNQ, RTY, M2K (Additional Indices) - daily
- CL, HO, NG, RB, BZ, QM (Energy Complex) - daily
- GC, SI, HG, PA, PL (Metals) - daily
- ZC, ZW, ZR, ZO (Grains Complex) - daily
- FX futures already collected (6E, 6A, 6B, 6C, 6J, 6L, CNH)

Date Range: 2010-06-06 to present (15+ years) - APPROVED PER PLAN
Dataset: GLBX.MDP3 (CME Globex)
Cost: $0 (included in DataBento CME MDP 3.0 plan)
Total Est. Size: 8-10 GB

Requirements:
    pip install databento

Setup:
    export DATABENTO_API_KEY="db-cSwxrJxRGGbqSBX74iuh9gqPrF4xf"
    # Or store in Keychain: security add-generic-password -s databento_api_key -a $USER -w 'YOUR_KEY'
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import databento as db
import time
import subprocess

# Configuration
DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
BASE_OUTPUT_DIR = DRIVE / "TrainingData/raw"
BASE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Date range
START_DATE = "2010-06-06"  # Databento historical start
END_DATE = datetime.now().strftime("%Y-%m-%d")

# Databento configuration
DATASET = "GLBX.MDP3"  # CME Globex MDP 3.0

# Complete symbol universe organized by priority
DOWNLOAD_PLAN = {
    # TIER 1: CRITICAL - Soy Complex & Core Indices
    "tier1_critical": {
        "symbols": [
            {"root": "ZL", "desc": "Soybean Oil", "schemas": ["ohlcv-1m", "ohlcv-1d"], "exchange": "CBOT"},
            {"root": "ZS", "desc": "Soybeans", "schemas": ["ohlcv-1m", "ohlcv-1d"], "exchange": "CBOT"},
            {"root": "ZM", "desc": "Soybean Meal", "schemas": ["ohlcv-1m", "ohlcv-1d"], "exchange": "CBOT"},
            {"root": "ES", "desc": "E-mini S&P 500", "schemas": ["ohlcv-1d"], "exchange": "CME"},
        ],
        "priority": 1,
        "est_size_gb": 7.5
    },
    
    # TIER 2: HIGH PRIORITY - Energy Complex
    "tier2_energy": {
        "symbols": [
            {"root": "CL", "desc": "WTI Crude Oil", "schemas": ["ohlcv-1d"], "exchange": "NYMEX"},
            {"root": "HO", "desc": "Heating Oil (ULSD)", "schemas": ["ohlcv-1d"], "exchange": "NYMEX"},
            {"root": "NG", "desc": "Natural Gas", "schemas": ["ohlcv-1d"], "exchange": "NYMEX"},
            {"root": "RB", "desc": "RBOB Gasoline", "schemas": ["ohlcv-1d"], "exchange": "NYMEX"},
        ],
        "priority": 2,
        "est_size_gb": 0.02
    },
    
    # TIER 3: HIGH PRIORITY - Grains
    "tier3_grains": {
        "symbols": [
            {"root": "ZC", "desc": "Corn", "schemas": ["ohlcv-1d"], "exchange": "CBOT"},
            {"root": "ZW", "desc": "Wheat", "schemas": ["ohlcv-1d"], "exchange": "CBOT"},
        ],
        "priority": 3,
        "est_size_gb": 0.01
    },
    
    # TIER 4: IMPORTANT - Additional Indices
    "tier4_indices": {
        "symbols": [
            {"root": "NQ", "desc": "E-mini Nasdaq-100", "schemas": ["ohlcv-1d"], "exchange": "CME"},
            {"root": "MNQ", "desc": "Micro Nasdaq", "schemas": ["ohlcv-1d"], "exchange": "CME", "start_date": "2019-03-18"},
            {"root": "RTY", "desc": "E-mini Russell 2000", "schemas": ["ohlcv-1d"], "exchange": "CME"},
            {"root": "M2K", "desc": "Micro Russell", "schemas": ["ohlcv-1d"], "exchange": "CME", "start_date": "2019-03-18"},
        ],
        "priority": 4,
        "est_size_gb": 0.02
    },
    
    # TIER 5: IMPORTANT - Metals
    "tier5_metals": {
        "symbols": [
            {"root": "GC", "desc": "Gold", "schemas": ["ohlcv-1d"], "exchange": "COMEX"},
            {"root": "SI", "desc": "Silver", "schemas": ["ohlcv-1d"], "exchange": "COMEX"},
            {"root": "HG", "desc": "Copper", "schemas": ["ohlcv-1d"], "exchange": "COMEX"},
        ],
        "priority": 5,
        "est_size_gb": 0.015
    },
    
    # TIER 6: ADDITIONAL COVERAGE
    "tier6_additional": {
        "symbols": [
            {"root": "BZ", "desc": "Brent Crude", "schemas": ["ohlcv-1d"], "exchange": "NYMEX"},
            {"root": "QM", "desc": "E-mini Crude", "schemas": ["ohlcv-1d"], "exchange": "NYMEX"},
            {"root": "PA", "desc": "Palladium", "schemas": ["ohlcv-1d"], "exchange": "COMEX"},
            {"root": "PL", "desc": "Platinum", "schemas": ["ohlcv-1d"], "exchange": "COMEX"},
            {"root": "ZR", "desc": "Rough Rice", "schemas": ["ohlcv-1d"], "exchange": "CBOT"},
            {"root": "ZO", "desc": "Oats", "schemas": ["ohlcv-1d"], "exchange": "CBOT"},
            {"root": "LE", "desc": "Live Cattle", "schemas": ["ohlcv-1d"], "exchange": "CME"},
            {"root": "GF", "desc": "Feeder Cattle", "schemas": ["ohlcv-1d"], "exchange": "CME"},
            {"root": "HE", "desc": "Lean Hogs", "schemas": ["ohlcv-1d"], "exchange": "CME"},
        ],
        "priority": 6,
        "est_size_gb": 0.04
    }
}


def get_api_key():
    """Get Databento API key from environment or Keychain."""
    # Try environment first
    api_key = os.environ.get("DATABENTO_API_KEY")
    
    # Try ~/.databento.key
    if not api_key:
        key_file = Path.home() / ".databento.key"
        if key_file.exists():
            api_key = key_file.read_text().strip()
    
    # Try macOS Keychain
    if not api_key:
        try:
            result = subprocess.run(
                ["security", "find-generic-password", "-s", "databento_api_key", "-w"],
                capture_output=True,
                text=True,
                check=True
            )
            api_key = result.stdout.strip()
        except:
            pass
    
    return api_key


def submit_download_job(client, symbol_info, schema, output_subdir):
    """Submit a Databento batch download job."""
    root = symbol_info["root"]
    desc = symbol_info["desc"]
    start = symbol_info.get("start_date", START_DATE)
    
    # For parent symbology, need to use ROOT.FUT format
    symbol = f"{root}.FUT"
    
    print(f"\n  📊 {root} ({desc}) - {schema}")
    print(f"     Symbol: {symbol}")
    print(f"     Date range: {start} to {END_DATE}")
    
    output_dir = BASE_OUTPUT_DIR / output_subdir / root.lower()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        job = client.batch.submit_job(
            dataset=DATASET,
            symbols=[symbol],  # Use ROOT.FUT format
            schema=schema,
            start=start,
            end=END_DATE,
            stype_in="parent",  # Parent symbology (continuous)
            encoding="json",
            compression="zstd",
            pretty_px=True,  # Pretty print prices
            pretty_ts=True,  # Pretty print timestamps
            split_duration="month" if schema == "ohlcv-1m" else "day",  # Monthly for 1-min, daily for daily bars
            delivery="download"  # Download delivery
        )
        
        # Handle both dict and object responses
        if isinstance(job, dict):
            job_id = job.get('id', 'unknown')
            job_state = job.get('state', 'submitted')
        else:
            job_id = job.id if hasattr(job, 'id') else 'unknown'
            job_state = job.state if hasattr(job, 'state') else 'submitted'
        
        print(f"     ✅ Job submitted: {job_id}")
        print(f"        Status: {job_state}")
        print(f"        Output: {output_dir}/")
        
        return {
            "root": root,
            "schema": schema,
            "job_id": job_id,
            "output_dir": output_dir,
            "status": job_state
        }
        
    except Exception as e:
        print(f"     ❌ Error: {e}")
        return None


def main():
    """Download ALL historical Databento data."""
    
    print("="*80)
    print("DATABENTO COMPLETE HISTORICAL DOWNLOAD")
    print("="*80)
    print(f"\nDataset: {DATASET}")
    print(f"Date Range: {START_DATE} to {END_DATE}")
    print(f"Output Base: {BASE_OUTPUT_DIR}/")
    
    # Get API key
    api_key = get_api_key()
    if not api_key:
        print("\n❌ DATABENTO_API_KEY not found!")
        print("\nOptions:")
        print("  1. export DATABENTO_API_KEY='db-cSwxrJxRGGbqSBX74iuh9gqPrF4xf'")
        print("  2. Save to ~/.databento.key")
        print("  3. Add to Keychain: security add-generic-password -s databento_api_key -a $USER -w 'YOUR_KEY'")
        return 1
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    # Initialize client
    print("\n🔌 Connecting to Databento...")
    client = db.Historical(api_key)
    
    # Track all jobs
    all_jobs = []
    total_symbols = sum(len(tier["symbols"]) for tier in DOWNLOAD_PLAN.values())
    total_downloads = sum(len(sym["schemas"]) for tier in DOWNLOAD_PLAN.values() for sym in tier["symbols"])
    
    print(f"\n📦 Total symbols: {total_symbols}")
    print(f"📊 Total downloads: {total_downloads} (some symbols have multiple timeframes)")
    print(f"💾 Estimated total size: ~{sum(tier['est_size_gb'] for tier in DOWNLOAD_PLAN.values()):.1f} GB")
    
    # Process each tier
    for tier_name, tier_info in sorted(DOWNLOAD_PLAN.items(), key=lambda x: x[1]["priority"]):
        print(f"\n{'='*80}")
        print(f"TIER {tier_info['priority']}: {tier_name.upper().replace('TIER', '').replace('_', ' ')}")
        print(f"{'='*80}")
        print(f"Symbols: {len(tier_info['symbols'])}")
        print(f"Est. Size: {tier_info['est_size_gb']} GB")
        
        for symbol_info in tier_info["symbols"]:
            for schema in symbol_info["schemas"]:
                # Determine output subdirectory
                if schema == "ohlcv-1m":
                    subdir = f"databento_{symbol_info['root'].lower()}_1min"
                else:
                    subdir = f"databento_{symbol_info['root'].lower()}"
                
                job_info = submit_download_job(client, symbol_info, schema, subdir)
                if job_info:
                    all_jobs.append(job_info)
                
                # Brief pause to avoid rate limits
                time.sleep(1)
    
    # Summary
    print("\n" + "="*80)
    print("DOWNLOAD JOBS SUMMARY")
    print("="*80)
    print(f"\n✅ Total jobs submitted: {len(all_jobs)}")
    print(f"📦 Symbols requested: {len(set(j['root'] for j in all_jobs))}")
    
    print("\n📋 Job IDs:")
    for job in all_jobs:
        print(f"  • {job['root']:6s} {job['schema']:12s} → {job['job_id']}")
    
    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("""
1. Monitor jobs at: https://databento.com/portal/batch/jobs

2. Download completed jobs:
   databento batch download <JOB_ID> --output-dir <OUTPUT_DIR>
   
   Or use the Databento Portal to download all at once.

3. Extract files to appropriate directories:
   - databento_zl/      (ZL daily + 1-minute)
   - databento_zs/      (ZS daily + 1-minute)
   - databento_zm/      (ZM daily + 1-minute)
   - databento_es/      (ES daily)
   - databento_energy/  (CL, HO, NG, RB, BZ, QM)
   - databento_grains/  (ZC, ZW, ZR, ZO)
   - databento_indices/ (NQ, MNQ, RTY, M2K)
   - databento_metals/  (GC, SI, HG, PA, PL)
   - databento_livestock/ (LE, GF, HE)

4. Load to BigQuery:
   python3 scripts/ingest/load_databento_to_bigquery.py

5. Verify master_features population:
   bq query "SELECT COUNT(*) FROM cbi-v14.features.master_features"

ALL DATA INCLUDED IN YOUR DATABENTO PLAN - NO EXTRA COST ✅
""")
    
    # Save job list for tracking
    jobs_file = BASE_OUTPUT_DIR / "databento_download_jobs.txt"
    with open(jobs_file, "w") as f:
        f.write(f"Databento Download Jobs - {datetime.now().isoformat()}\n")
        f.write("="*80 + "\n\n")
        for job in all_jobs:
            f.write(f"{job['root']:6s} {job['schema']:12s} {job['job_id']}  →  {job['output_dir']}\n")
    
    print(f"\n💾 Job list saved to: {jobs_file}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

