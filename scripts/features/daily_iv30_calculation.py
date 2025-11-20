#!/usr/bin/env python3
"""
Daily IV30 Calculation Scheduler
================================

Runs IV30 calculation from DataBento options data daily.
Should be scheduled to run after market close (e.g., 5:00 PM ET).

⚠️ CRITICAL: NO FAKE DATA ⚠️
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.features.calculate_iv30_from_options import (
    get_databento_client,
    calculate_iv30_for_date,
    SYMBOLS
)
# Note: Uses Live API (not Historical) to avoid download costs
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

EXTERNAL_DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
FEATURES_DIR = EXTERNAL_DRIVE / "TrainingData/features"
FEATURES_DIR.mkdir(parents=True, exist_ok=True)

def main():
    """Run daily IV30 calculation for yesterday's trading day."""
    logger.info("="*80)
    logger.info("DAILY IV30 CALCULATION")
    logger.info("="*80)
    
    # Calculate for yesterday (most recent trading day)
    yesterday = (datetime.now() - timedelta(days=1)).date()
    date_str = yesterday.strftime('%Y-%m-%d')
    
    logger.info(f"Calculating IV30 for {date_str}")
    
    # Get DataBento client
    client = get_databento_client()
    if not client:
        logger.error("❌ Cannot proceed without DataBento client")
        return 1
    
    # Calculate IV30 for each symbol
    results = []
    for symbol in SYMBOLS:
        logger.info(f"\nProcessing {symbol}...")
        result = calculate_iv30_for_date(symbol, date_str, client)
        results.append(result)
        
        if result['quality_flag'] == 'ok':
            logger.info(f"  ✅ IV30={result['iv30']:.4f}, quality={result['quality_flag']}")
        elif result['quality_flag'] == 'sparse':
            logger.warning(f"  ⚠️  IV30={result['iv30']:.4f}, quality={result['quality_flag']}")
        else:
            logger.error(f"  ❌ quality={result['quality_flag']}")
    
    # Load existing IV30 data
    iv30_file = FEATURES_DIR / "iv30_from_options.parquet"
    if iv30_file.exists():
        existing_df = pd.read_parquet(iv30_file)
        # Remove yesterday's data if it exists (for re-calculation)
        existing_df = existing_df[
            ~((existing_df['date'] == date_str) & (existing_df['symbol'].isin(SYMBOLS)))
        ]
    else:
        existing_df = pd.DataFrame()
    
    # Append new results
    new_df = pd.DataFrame(results)
    if not existing_df.empty:
        df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        df = new_df
    
    # Sort by date and symbol
    df = df.sort_values(['date', 'symbol']).reset_index(drop=True)
    
    # Save
    df.to_parquet(iv30_file, index=False)
    logger.info(f"\n✅ Updated IV30 data: {iv30_file}")
    logger.info(f"   Total rows: {len(df)}")
    
    # Log quality summary
    quality_summary = df.groupby('quality_flag').size()
    logger.info(f"   Quality breakdown:")
    for flag, count in quality_summary.items():
        logger.info(f"     {flag}: {count}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
