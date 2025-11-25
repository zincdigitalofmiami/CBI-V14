#!/usr/bin/env python3
"""
Build Forex Features for BigQuery
==================================

Calculates technical indicators and features for forex futures:
- 6L (BRL), 6E (EUR), 6J (JPY), 6C (CAD), 6B (GBP), 6A (AUD), CNH (Yuan)

Inputs:
- TrainingData/raw/databento_forex/*.parquet

Outputs:
- TrainingData/staging/forex_features.parquet (all symbols combined, prefixed)

Features:
- Technical indicators (RSI, MACD, Bollinger Bands, Moving Averages)
- Volatility (realized vol, ATR)
- Cross-currency correlations
- Currency strength indices

⚠️ CRITICAL: NO FAKE DATA ⚠️
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

from src.utils.fx_features import (
    FOREX_SYMBOLS,
    add_symbol_technicals,
    add_cross_currency_features,
    add_zl_fx_correlations,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
RAW_DIR = DRIVE / "TrainingData/raw/databento_forex"
STAGING_DIR = DRIVE / "TrainingData/staging"
STAGING_DIR.mkdir(parents=True, exist_ok=True)

def main():
    logger.info("🚀 Building Forex Features")
    logger.info("=" * 60)
    
    # Load only full history files (2010-06-06), skip partial files
    forex_files = list(RAW_DIR.glob("*_daily_2010-06-06_*.parquet"))
    if not forex_files:
        logger.warning(f"⚠️  No full history forex files found in {RAW_DIR}")
        logger.info("   Run collect_databento_forex.py --start 2010-06-06 first")
        return
    
    logger.info(f"Found {len(forex_files)} full history forex files")
    
    # Load and combine all forex data (one per symbol, use the full history file)
    symbol_files = {}
    for f in forex_files:
        symbol = f.name.split('_')[0].lower()
        if symbol not in symbol_files:
            symbol_files[symbol] = f
    
    all_dfs = []
    for symbol, f in symbol_files.items():
        try:
            df = pd.read_parquet(f)
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            all_dfs.append(df)
            logger.info(f"   Loaded {f.name}: {len(df)} rows")
        except Exception as e:
            logger.warning(f"   Failed to load {f.name}: {e}")
    
    if not all_dfs:
        logger.error("❌ No forex data loaded")
        return
    
    # Merge all symbols on date (memory-efficient: process one at a time, keep only essential cols)
    # Extract only essential columns to reduce memory footprint
    essential_dfs = []
    for df in all_dfs:
        date_col = 'date'
        essential_cols = [date_col]
        # Add all price columns (close, high, low, volume)
        for suffix in ['_close', '_high', '_low', '_volume']:
            cols = [c for c in df.columns if c.endswith(suffix)]
            essential_cols.extend(cols)
        
        essential_df = df[essential_cols].copy()
        essential_dfs.append(essential_df)
        logger.info(f"   Extracted {len(essential_cols)} columns from {df.shape[0]} rows")
    
    if not essential_dfs:
        logger.error("❌ No essential columns found")
        return
    
    # Merge sequentially (outer join to keep all dates)
    logger.info("   Merging currencies on date...")
    combined = essential_dfs[0].copy()
    for i, df in enumerate(essential_dfs[1:], 1):
        logger.info(f"   Merging currency {i+1}/{len(essential_dfs)}...")
        combined = combined.merge(df, on='date', how='outer')
        # Force garbage collection periodically
        if i % 2 == 0:
            import gc
            gc.collect()
    
    combined = combined.sort_values('date').reset_index(drop=True)
    logger.info(f"   ✅ Merged to {len(combined)} rows × {len(combined.columns)} cols")
    logger.info(f"\n✅ Combined {len(combined)} rows × {len(combined.columns)} cols")
    
    # Calculate features for each symbol
    for symbol in FOREX_SYMBOLS:
        if f"{symbol}_close" in combined.columns:
            combined = add_symbol_technicals(combined, symbol)
    
    # Calculate cross-currency features
    combined = add_cross_currency_features(combined)
    
    # Calculate ZL-FX correlations (critical for export competitiveness)
    combined = add_zl_fx_correlations(combined, STAGING_DIR, logger=logger)
    
    # Save to staging
    output_file = STAGING_DIR / "forex_features.parquet"
    combined.to_parquet(output_file, index=False)
    logger.info(f"\n💾 Saved to {output_file}")
    logger.info(f"   Rows: {len(combined)}, Columns: {len(combined.columns)}")
    
    logger.info("\n✅ Forex Feature Build Complete!")

if __name__ == '__main__':
    main()
