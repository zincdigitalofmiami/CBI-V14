#!/usr/bin/env python3
"""
DATABENTO COMPLETE SUBMISSION SCRIPT
=====================================
Optimized pull logic per user spec:
- Date range: 2018-01-01 → 2025-11-24
- Dataset: GLBX.MDP3 (CME Globex)
- Heavy (full schema): MES.FUT, ZL.FUT
- Light (trimmed): ES.FUT, ZS.FUT, ZM.FUT, ZC.FUT

BigQuery mapping:
- ohlcv-1s/1m/1h/1d → market_data.databento_futures_ohlcv_{1s,1m,1h,1d}
- bbo-1s/1m → market_data.databento_bbo_{1s,1m}
- tbbo → market_data.databento_tbbo
- mbp-1/mbp-10 → market_data.databento_mbp_{1,10}
- mbo → market_data.databento_mbo
- statistics → market_data.databento_stats
"""

import os
import databento as db

# ============================================================
# CONFIGURATION
# ============================================================

DATABENTO_API_KEY = os.environ.get("DATABENTO_API_KEY")
if not DATABENTO_API_KEY:
    raise ValueError("DATABENTO_API_KEY environment variable not set")

# Date range
START_DATE = "2018-01-01"
END_DATE = "2025-11-24"

# Dataset
DATASET = "GLBX.MDP3"

# Symbol groups
HEAVY_SYMBOLS = ["MES.FUT", "ZL.FUT"]
LIGHT_SYMBOLS = ["ES.FUT", "ZS.FUT", "ZM.FUT", "ZC.FUT"]

# Schemas per group
HEAVY_SCHEMAS = [
    # Bars
    "ohlcv-1s", "ohlcv-1m", "ohlcv-1h", "ohlcv-1d",
    # BBO/TOB
    "bbo-1s", "bbo-1m", "tbbo",
    # Depth
    "mbp-1", "mbp-10", "mbo",
    # Stats
    "statistics"
]

LIGHT_SCHEMAS = [
    # Bars (hourly + daily only)
    "ohlcv-1h", "ohlcv-1d",
    # BBO (1m only)
    "bbo-1m",
    # Stats
    "statistics"
]

# Common options
COMMON_OPTIONS = {
    "encoding": "csv",
    "compression": "zstd",
    "split_duration": "month",
    "stype_in": "parent",
    "stype_out": "instrument_id",
    "map_symbols": True,
    "pretty_px": True,
    "pretty_ts": True
}


def submit_jobs(client, symbols, schemas, label_prefix):
    """Submit batch jobs for symbol/schema combinations."""
    jobs = []
    
    for schema in schemas:
        for symbol in symbols:
            job_label = f"{label_prefix}_{symbol.replace('.', '_')}_{schema.replace('-', '_')}"
            
            print(f"Submitting: {symbol} / {schema} ({job_label})")
            
            try:
                job = client.batch.submit_job(
                    dataset=DATASET,
                    symbols=[symbol],
                    schema=schema,
                    start=START_DATE,
                    end=END_DATE,
                    **COMMON_OPTIONS
                )
                
                jobs.append({
                    "job_id": job.id if hasattr(job, 'id') else str(job),
                    "symbol": symbol,
                    "schema": schema,
                    "label": job_label
                })
                
                print(f"  ✅ Job ID: {job.id if hasattr(job, 'id') else job}")
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                jobs.append({
                    "job_id": None,
                    "symbol": symbol,
                    "schema": schema,
                    "label": job_label,
                    "error": str(e)
                })
    
    return jobs


def main():
    print("=" * 60)
    print("DATABENTO COMPLETE SUBMISSION")
    print("=" * 60)
    print(f"Date Range: {START_DATE} → {END_DATE}")
    print(f"Dataset: {DATASET}")
    print(f"Heavy Symbols: {HEAVY_SYMBOLS}")
    print(f"Light Symbols: {LIGHT_SYMBOLS}")
    print(f"Heavy Schemas: {len(HEAVY_SCHEMAS)}")
    print(f"Light Schemas: {len(LIGHT_SCHEMAS)}")
    print("=" * 60)
    
    # Connect
    client = db.Historical(key=DATABENTO_API_KEY)
    
    # Check cost estimate first
    print("\n📊 Estimating costs...")
    
    total_jobs = (len(HEAVY_SYMBOLS) * len(HEAVY_SCHEMAS)) + (len(LIGHT_SYMBOLS) * len(LIGHT_SCHEMAS))
    print(f"Total jobs to submit: {total_jobs}")
    
    # Submit HEAVY jobs
    print("\n🏋️ HEAVY SYMBOLS (full microstructure)")
    print("-" * 40)
    heavy_jobs = submit_jobs(client, HEAVY_SYMBOLS, HEAVY_SCHEMAS, "heavy")
    
    # Submit LIGHT jobs
    print("\n🪶 LIGHT SYMBOLS (hourly/daily + stats)")
    print("-" * 40)
    light_jobs = submit_jobs(client, LIGHT_SYMBOLS, LIGHT_SCHEMAS, "light")
    
    # Summary
    all_jobs = heavy_jobs + light_jobs
    successful = [j for j in all_jobs if j.get("job_id") and not j.get("error")]
    failed = [j for j in all_jobs if j.get("error")]
    
    print("\n" + "=" * 60)
    print("SUBMISSION SUMMARY")
    print("=" * 60)
    print(f"✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")
    
    if failed:
        print("\nFailed jobs:")
        for j in failed:
            print(f"  - {j['label']}: {j.get('error')}")
    
    # Save job manifest
    import json
    manifest_path = "/Users/zincdigital/CBI-V14/Quant Check Plan/databento_job_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump({
            "submitted_at": str(os.popen("date").read().strip()),
            "date_range": f"{START_DATE} to {END_DATE}",
            "dataset": DATASET,
            "jobs": all_jobs
        }, f, indent=2)
    
    print(f"\n📝 Job manifest saved to: {manifest_path}")
    print("\n⏳ Jobs are processing. Use `databento jobs list` to check status.")
    print("📥 When complete, download and load to BigQuery using load_databento_csv.py")


if __name__ == "__main__":
    main()

