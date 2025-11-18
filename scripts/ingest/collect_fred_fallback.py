#!/usr/bin/env python3

"""
FRED Data Collection Fallback Script
====================================
Uses existing FRED data from staging until we get a valid API key.

The issue: Current key (98AE1A55-11D0-304B-A5A5-F3FF61E86A31) is wrong format
- FRED requires: 32 lowercase alphanumeric chars, no hyphens
- Current key: UUID format with uppercase and hyphens

Solution: Use existing 16 series from staging/fred_macro_expanded.parquet
"""

import pandas as pd
from pathlib import Path
import logging
import os

# Setup paths - use absolute path from environment
BASE_DIR = Path("/Users/kirkmusick/Documents/GitHub/CBI-V14")
STAGING_DIR = BASE_DIR / "staging"
RAW_DIR = BASE_DIR / "data" / "raw" / "fred"

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def use_existing_fred_data():
    """
    Load existing FRED data from staging (16 series, 9,452 rows)
    This data was collected earlier with a valid API key.
    """
    staging_file = STAGING_DIR / "fred_macro_expanded.parquet"
    
    if not staging_file.exists():
        raise FileNotFoundError(f"Staging file not found: {staging_file}")
    
    # Load existing data
    df = pd.read_parquet(staging_file)
    
    logger.info(f"✅ Loaded existing FRED data: {len(df)} rows, {df.shape[1]} columns")
    logger.info(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    
    # List available series
    fred_cols = [c for c in df.columns if c.startswith('fred_')]
    logger.info(f"   Available series ({len(fred_cols)}): {', '.join(fred_cols[:5])}...")
    
    # Also save a copy to raw directory for reference
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_file = RAW_DIR / "fred_fallback_data.parquet"
    df.to_parquet(raw_file)
    logger.info(f"   Saved copy to: {raw_file}")
    
    return df

def get_valid_api_key_instructions():
    """
    Instructions for getting a valid FRED API key
    """
    instructions = """
    ================================================================================
    TO GET A VALID FRED API KEY:
    ================================================================================
    
    1. Go to: https://fred.stlouisfed.org/docs/api/api_key.html
    2. Click "Request API Key" (free, instant)
    3. You'll get a 32-character lowercase alphanumeric key
       Example format: abcd1234efgh5678ijkl9012mnop3456
    
    4. Store in macOS Keychain:
       security add-generic-password -a "cbi-v14" -s "FRED_API_KEY" -w "your_key_here" -U
    
    5. Update scripts/ingest/collect_fred_comprehensive.py to use keychain:
       from src.utils.keychain_manager import get_api_key
       FRED_API_KEY = get_api_key('FRED_API_KEY')
    
    Current invalid key: 98AE1A55-11D0-304B-A5A5-F3FF61E86A31
    - Wrong: Contains hyphens and uppercase (UUID format)  
    - Right: 32 lowercase alphanumeric characters only
    
    ================================================================================
    """
    print(instructions)
    return instructions

def main():
    """
    Main function - use existing data as fallback
    """
    logger.info("=" * 80)
    logger.info("FRED DATA FALLBACK - Using Existing Staging Data")
    logger.info("=" * 80)
    
    try:
        # Use existing data
        df = use_existing_fred_data()
        
        # Show what we have
        logger.info("\nExisting FRED series (prefixed):")
        for col in sorted([c for c in df.columns if c.startswith('fred_')]):
            non_null = df[col].notna().sum()
            logger.info(f"  • {col}: {non_null:,} values")
        
        logger.info("\n✅ SUCCESS: Using existing FRED data (16 series)")
        logger.info("   This data is sufficient for current training needs")
        logger.info("   Full 60-series expansion deferred to Week 3")
        
    except Exception as e:
        logger.error(f"❌ FAILED: {str(e)}")
        logger.info("\nShowing instructions for getting valid API key...")
        get_valid_api_key_instructions()
        raise
    
    logger.info("\n" + "=" * 80)
    logger.info("COMPLETE - Existing FRED data available for pipeline")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
