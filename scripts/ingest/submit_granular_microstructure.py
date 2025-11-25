"""
Submit Granular Microstructure Jobs to Databento
================================================

Submits batch jobs to Databento for comprehensive futures microstructure data.
Differentiates between HEAVY symbols (full schema set) and LIGHT symbols (reduced set).

Usage:
    export DATABENTO_API_KEY="your_api_key"
    python submit_granular_microstructure.py

Output:
    - Job IDs printed to console
    - Download from https://databento.com/portal/files when complete
    - Load CSVs to BigQuery using load_databento_csv.py
"""

import os
from typing import List, Dict

try:
    import databento as db
except ImportError:
    print("ERROR: databento not installed. Run: pip install databento")
    print("       Also ensure you have a valid API key from databento.com")
    exit(1)


# =============================================================================
# CONFIGURATION
# =============================================================================

API_KEY = os.environ.get("DATABENTO_API_KEY")
if not API_KEY:
    raise ValueError(
        "DATABENTO_API_KEY environment variable not set.\n"
        "Get your API key from https://databento.com/portal/keys"
    )

# Date range - FULL 15-YEAR HISTORY
# 2010-01-01 → 2025-11-24 for complete coverage
START_DATE = "2010-01-01"  # Full 15-year history
END_DATE = "2025-11-24"

# CME Globex dataset
DATASET = "GLBX.MDP3"


# =============================================================================
# SYMBOL CONFIGURATION
# =============================================================================

# HEAVY symbols - get FULL microstructure (all timeframes + deep book)
# These are our primary focus: ZL (Soybean Oil) and MES (Micro E-mini S&P)
# Note: GLBX.MDP3 includes options on futures - ES.OPT and MES.OPT available
HEAVY_SYMBOLS = ["ZL.FUT", "MES.FUT"]

# MES Options symbols (for GEX, vol surface, put/call ratios)
# GLBX.MDP3 includes options on futures (CME Options Add-On ENABLED)
# Confirmed format from DATABENTO_PLAN_VALIDATION.md:
# - ES.OPT, MES.OPT (E-mini and Micro E-mini S&P 500 options)
# - OZL.OPT, OZS.OPT, OZM.OPT (Soybean Oil, Soybeans, Soybean Meal options)
# - Uses stype_in='parent' (same as futures)
# Reference: /Volumes/Satechi Hub/Projects/CBI-V14/docs/features/DATABENTO_PLAN_VALIDATION.md
MES_OPTIONS_SYMBOLS = [
    "ES.OPT",   # E-mini S&P 500 options (confirmed format)
    "MES.OPT",  # Micro E-mini S&P 500 options (confirmed format)
]

# ZL Options symbols (for implied vol, GEX, vol surface, crush spread vol)
# GLBX.MDP3 includes options on futures (CME Options Add-On ENABLED)
# Confirmed format from DATABENTO_PLAN_VALIDATION.md:
# - OZL.OPT (Soybean Oil), OZS.OPT (Soybeans), OZM.OPT (Soybean Meal)
# - Uses stype_in='parent' (same as futures)
# Reference: /Volumes/Satechi Hub/Projects/CBI-V14/docs/features/DATABENTO_PLAN_VALIDATION.md
ZL_OPTIONS_SYMBOLS = [
    "OZL.OPT",  # Soybean Oil options (confirmed format - note O prefix)
    "OZS.OPT",  # Soybeans options (for crush spread vol analysis)
    "OZM.OPT",  # Soybean Meal options (for crush spread vol analysis)
]

# LIGHT symbols - get reduced schemas (hourly/daily + BBO + stats)
# Important cross-asset but don't need tick-by-tick depth
LIGHT_SYMBOLS = [
    "ES.FUT",   # E-mini S&P 500
    "ZS.FUT",   # Soybeans
    "ZM.FUT",   # Soybean Meal  
    "ZC.FUT",   # Corn
    "CL.FUT",   # Crude Oil
    "HO.FUT",   # Heating Oil
]


# =============================================================================
# SCHEMA CONFIGURATION
# =============================================================================

# Full schema set for HEAVY symbols (futures)
SCHEMAS_HEAVY = [
    # --- Price Bars (All timeframes) ---
    "ohlcv-1s",   # Second bars (intraday TA)
    "ohlcv-1m",   # Minute bars (standard)
    "ohlcv-1h",   # Hour bars (context)
    "ohlcv-1d",   # Daily bars (macro)
    
    # --- Best Bid/Offer (BBO) & Top of Book ---
    "bbo-1s",     # BBO sampled every second
    "bbo-1m",     # BBO sampled every minute
    "tbbo",       # BBO at every trade (tick-level transitions)
    
    # --- Depth of Book (The Alpha Source) ---
    "mbp-1",      # L1: Top of book updates
    "mbp-10",     # L2: Top 10 levels (queue pressure features)
    "mbo",        # L3: Full Market-By-Order (VERY LARGE - resting orders)
    
    # --- Market Stats ---
    "statistics"  # Official Open Interest, Settlement, Volume
]

# Options schemas (for MES options - ES.OPT, MES.OPT)
# GLBX.MDP3 options use standard schemas with options symbols
SCHEMAS_OPTIONS = [
    "ohlcv-1d",   # Daily options bars (for vol surface, GEX)
    "ohlcv-1h",   # Hourly options bars (for intraday GEX)
    "trades",     # Options trades (for put/call ratios, volume)
    "quotes",     # Options quotes (for bid/ask, implied vol)
    "statistics", # Options OI, settlement
]

# Reduced schema set for LIGHT symbols
SCHEMAS_LIGHT = [
    "ohlcv-1h",   # Hourly bars
    "ohlcv-1d",   # Daily bars
    "bbo-1m",     # BBO sampled every minute
    "statistics"  # OI, Settlement, Volume
]


# =============================================================================
# JOB SUBMISSION OPTIONS
# =============================================================================

# Common options for all jobs - OPTIMIZED FOR BIGQUERY
# Only using valid parameters per Databento API signature
COMMON_OPTIONS = dict(
    dataset=DATASET,
    start=START_DATE,
    end=END_DATE,
    
    # --- BIGQUERY OPTIMIZATION ---
    encoding="csv",              # CSV for easy BQ loading (not DBN binary)
    compression="none",          # No compression - BQ handles raw CSV better
    split_duration="day",        # Daily files align with BQ partitioning
    
    # --- SYMBOLOGY ---
    stype_in="parent",           # Get full history (all expirations/rolls)
    stype_out="instrument_id",   # Normalized instrument ID in output
    map_symbols=True,            # Include symbol mapping file
    
    # --- FORMATTING ---
    pretty_px=True,              # Human-readable prices
    pretty_ts=True               # Human-readable timestamps
)


# =============================================================================
# BIGQUERY TABLE MAPPING
# =============================================================================

TABLE_MAPPING = {
    # OHLCV bars (futures)
    "ohlcv-1s": "market_data.databento_futures_ohlcv_1s",
    "ohlcv-1m": "market_data.databento_futures_ohlcv_1m",
    "ohlcv-1h": "market_data.databento_futures_ohlcv_1h",
    "ohlcv-1d": "market_data.databento_futures_ohlcv_1d",
    
    # BBO
    "bbo-1s": "market_data.databento_bbo_1s",
    "bbo-1m": "market_data.databento_bbo_1m",
    "tbbo": "market_data.databento_tbbo",
    
    # Market Depth
    "mbp-1": "market_data.databento_mbp_1",
    "mbp-10": "market_data.databento_mbp_10",
    "mbo": "market_data.databento_mbo",
    
    # Statistics
    "statistics": "market_data.databento_stats",
    
    # Options (MES-specific, separate tables)
    # Note: Options use same schemas but different symbols (ES.OPT, MES.OPT)
    # Tables will be in market_data_mes dataset for separation
}


# =============================================================================
# MAIN SUBMISSION FUNCTION
# =============================================================================

def submit_jobs(symbols: List[str], schemas: List[str], label: str) -> Dict[str, str]:
    """
    Submit batch jobs to Databento.
    
    Args:
        symbols: List of symbol strings (e.g., ["ZL.FUT"])
        schemas: List of schema strings (e.g., ["ohlcv-1d"])
        label: Label for logging (e.g., "HEAVY" or "LIGHT")
    
    Returns:
        Dict mapping schema -> job_id
    """
    client = db.Historical(API_KEY)
    job_ids = {}
    
    print(f"\n{'='*70}")
    print(f"Submitting {label} jobs for {len(symbols)} symbols")
    print(f"{'='*70}")
    print(f"Symbols: {', '.join(symbols)}")
    print(f"Schemas: {len(schemas)}")
    print(f"Date Range: {START_DATE} to {END_DATE}")
    
    for symbol in symbols:
        print(f"\n📦 Symbol: {symbol}")
        
        for schema in schemas:
            try:
                print(f"   ...{schema}...", end=" ", flush=True)
                
                # Submit job
                # Options use stype_in='parent' (same as futures) per DATABENTO_PLAN_VALIDATION.md
                # Symbol format: ES.OPT, MES.OPT (confirmed)
                response = client.batch.submit_job(
                    symbols=[symbol],
                    schema=schema,
                    **COMMON_OPTIONS
                )
                
                job_id = response.get("id") or response.get("job_id") or str(response)
                job_ids[f"{symbol}:{schema}"] = job_id
                
                bq_table = TABLE_MAPPING.get(schema, "unknown")
                print(f"✅ Job ID: {job_id} → {bq_table}")
                
            except Exception as e:
                print(f"❌ FAILED: {e}")
                job_ids[f"{symbol}:{schema}"] = f"ERROR: {e}"
    
    return job_ids


def main():
    """Main entry point."""
    print("=" * 70)
    print("DATABENTO MICROSTRUCTURE JOB SUBMISSION")
    print("=" * 70)
    print(f"Start Date: {START_DATE}")
    print(f"End Date: {END_DATE}")
    print(f"Dataset: {DATASET}")
    print(f"Heavy Symbols: {', '.join(HEAVY_SYMBOLS)}")
    print(f"Light Symbols: {', '.join(LIGHT_SYMBOLS)}")
    print(f"MES Options: {', '.join(MES_OPTIONS_SYMBOLS) if MES_OPTIONS_SYMBOLS else 'None'}")
    print(f"ZL Options: {', '.join(ZL_OPTIONS_SYMBOLS) if ZL_OPTIONS_SYMBOLS else 'None'}")
    
    # Submit HEAVY jobs (full microstructure for futures)
    heavy_jobs = submit_jobs(HEAVY_SYMBOLS, SCHEMAS_HEAVY, "HEAVY")
    
    # Submit LIGHT jobs (reduced set)
    light_jobs = submit_jobs(LIGHT_SYMBOLS, SCHEMAS_LIGHT, "LIGHT")
    
    # Submit OPTIONS jobs (for GEX, vol surface, put/call ratios, IV30)
    # GLBX.MDP3 includes options on futures (CME Options Add-On ENABLED)
    # 15 years history, 650,000+ symbols available
    # Confirmed format: ES.OPT, MES.OPT, OZL.OPT, OZS.OPT, OZM.OPT
    # Uses stype_in='parent' (same as futures)
    # Reference: DATABENTO_PLAN_VALIDATION.md
    options_jobs = {}
    
    # MES Options (for MES trading model)
    if MES_OPTIONS_SYMBOLS:
        print("\n" + "=" * 70)
        print("MES OPTIONS (ES.OPT, MES.OPT)")
        print("=" * 70)
        print("Note: Options data for MES GEX, vol surface, put/call ratios")
        print("      GLBX.MDP3 includes options on futures (15 years history)")
        print("      ✅ Symbol format confirmed: ES.OPT, MES.OPT")
        print("      ✅ Uses stype_in='parent' (same as futures)")
        mes_options_jobs = submit_jobs(MES_OPTIONS_SYMBOLS, SCHEMAS_OPTIONS, "MES_OPTIONS")
        options_jobs.update(mes_options_jobs)
    
    # ZL Options (for ZL implied vol, GEX, vol surface)
    if ZL_OPTIONS_SYMBOLS:
        print("\n" + "=" * 70)
        print("ZL OPTIONS (OZL.OPT, OZS.OPT, OZM.OPT)")
        print("=" * 70)
        print("Note: Options data for ZL implied vol, GEX, vol surface, crush spread vol")
        print("      GLBX.MDP3 includes options on futures (15 years history)")
        print("      ✅ Symbol format confirmed: OZL.OPT, OZS.OPT, OZM.OPT (note O prefix)")
        print("      ✅ Uses stype_in='parent' (same as futures)")
        zl_options_jobs = submit_jobs(ZL_OPTIONS_SYMBOLS, SCHEMAS_OPTIONS, "ZL_OPTIONS")
        options_jobs.update(zl_options_jobs)
    
    # Summary
    print("\n" + "=" * 70)
    print("SUBMISSION SUMMARY")
    print("=" * 70)
    
    all_jobs = {**heavy_jobs, **light_jobs, **options_jobs}
    success_count = sum(1 for v in all_jobs.values() if not v.startswith("ERROR"))
    error_count = sum(1 for v in all_jobs.values() if v.startswith("ERROR"))
    
    print(f"Total jobs submitted: {success_count}")
    print(f"Failed jobs: {error_count}")
    
    if error_count > 0:
        print("\n⚠️  Failed jobs:")
        for key, value in all_jobs.items():
            if value.startswith("ERROR"):
                print(f"   - {key}: {value}")
    
    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("1. Monitor job status at: https://databento.com/portal/files")
    print("2. Download completed CSV files")
    print("3. Run: python load_databento_csv.py <path_to_csvs>")
    print("\n🏁 Job submission complete")


if __name__ == "__main__":
    main()

