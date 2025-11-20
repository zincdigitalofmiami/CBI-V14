#!/usr/bin/env python3
"""
Download ZL (Soybean Oil) 1-minute OHLCV data from Databento.

This script downloads historical 1-minute bars to fill the gap in ZL microstructure features.
Currently only 1-hour data exists, making zl_60min_* features mathematically incorrect.

Requirements:
    pip install databento

Setup:
    export DATABENTO_API_KEY="your-api-key-here"
    # Or store in ~/.databento.key
"""

import os
from pathlib import Path
from datetime import datetime
import databento as db

# Configuration
DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
OUTPUT_DIR = DRIVE / "TrainingData/raw/databento_zl"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Date range to match existing 1-hour coverage
START_DATE = "2010-06-06"  # First date in existing 1h data
END_DATE = "2025-11-17"    # Latest date in existing 1h data

# Databento configuration
DATASET = "GLBX.MDP3"      # CME Globex MDP 3.0
SYMBOLS = ["ZL"]           # Soybean Oil futures root symbol
SCHEMA = "ohlcv-1m"        # 1-minute OHLCV bars
# Note: Using parent symbology with .FUT suffix for continuous contracts

def main():
    """Download ZL 1-minute data from Databento."""
    
    # Check for API key
    api_key = os.environ.get("DATABENTO_API_KEY")
    if not api_key and Path.home().joinpath(".databento.key").exists():
        api_key = Path.home().joinpath(".databento.key").read_text().strip()
    
    if not api_key:
        print("❌ DATABENTO_API_KEY not found!")
        print("\nSet your API key:")
        print("  export DATABENTO_API_KEY='your-key-here'")
        print("  # Or save to ~/.databento.key")
        return 1
    
    print("="*80)
    print("DATABENTO ZL 1-MINUTE DOWNLOAD")
    print("="*80)
    print(f"\nDataset: {DATASET}")
    print(f"Symbols: {SYMBOLS}")
    print(f"Schema: {SCHEMA}")
    print(f"Date Range: {START_DATE} to {END_DATE}")
    print(f"Output: {OUTPUT_DIR}")
    
    # Initialize client
    client = db.Historical(api_key)
    
    # Submit batch download request
    print("\n📊 Submitting batch download request...")
    
    try:
        # Request historical data
        # Note: Large date ranges are best done via batch API
        # Using parent symbology for continuous contracts
        job = client.batch.submit_job(
            dataset=DATASET,
            symbols=["ZL.FUT"],  # Parent symbology requires .FUT suffix
            schema=SCHEMA,
            start=START_DATE,
            end=END_DATE,
            stype_in="parent",  # Parent symbology (continuous)
            encoding="json",  # JSON with pretty_ts/pretty_px
            compression="zstd",
            split_duration="month",  # Monthly splits for 1-minute data
            pretty_px=True,
            pretty_ts=True,
            delivery="download"
        )
        
        print(f"✅ Job submitted: {job.id}")
        print(f"   Status: {job.state}")
        print(f"\nMonitor your job at: https://databento.com/portal/batch/jobs/{job.id}")
        print("\nOnce complete, download the files and extract to:")
        print(f"  {OUTPUT_DIR}/")
        
        # Provide CLI download command
        print(f"\nOr use CLI to download when ready:")
        print(f"  databento batch download {job.id} --output-dir {OUTPUT_DIR}")
        
    except Exception as e:
        print(f"❌ Error submitting job: {e}")
        print("\nAlternative: Submit via Databento Portal")
        print("  1. Go to https://databento.com/portal/batch")
        print(f"  2. Dataset: {DATASET}")
        print(f"  3. Symbols: {', '.join(SYMBOLS)}")
        print(f"  4. Schema: {SCHEMA}")
        print(f"  5. Date Range: {START_DATE} to {END_DATE}")
        print(f"  6. Symbol Type: parent (use ZL.FUT)")
        print("  7. Encoding: JSON (pretty_ts, pretty_px)")
        print("  8. Compression: zstd")
        print("  9. Download and extract to TrainingData/raw/databento_zl/")
        return 1
    
    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("\n1. Wait for batch job to complete (check portal)")
    print("2. Download and extract files to TrainingData/raw/databento_zl/")
    print("3. Rerun ZL aggregator:")
    print("     python3 scripts/ingest/aggregate_zl_intraday.py")
    print("4. Verify microstructure features are populated:")
    print("     # Check zl_60min_* columns are no longer based on 1h bars")
    print("\n✅ This will fix the ZL microstructure feature accuracy issue.")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())





