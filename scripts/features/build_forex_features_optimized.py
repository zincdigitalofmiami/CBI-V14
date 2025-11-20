#!/usr/bin/env python3
"""
Build Forex Features (Optimized for Large Datasets)
====================================================

Processes currencies individually, then combines to avoid memory issues.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

from src.utils.fx_features import FOREX_SYMBOLS, add_symbol_technicals

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
RAW_DIR = DRIVE / "TrainingData/raw/databento_forex"
STAGING_DIR = DRIVE / "TrainingData/staging"
STAGING_DIR.mkdir(parents=True, exist_ok=True)

def main():
    logger.info("🚀 Building Forex Features (Optimized)")
    logger.info("=" * 60)
    
    # Load full history files only
    forex_files = {f.name.split('_')[0].lower(): f for f in RAW_DIR.glob("*_daily_2010-06-06_*.parquet")}
    
    if not forex_files:
        logger.error("❌ No full history forex files found")
        return
    
    logger.info(f"Found {len(forex_files)} currencies")
    
    # Process each currency individually and save features
    processed_dfs = []
    for symbol, filepath in forex_files.items():
        logger.info(f"\n📊 Processing {symbol}...")
        try:
            df = pd.read_parquet(filepath)
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            
            # Calculate features
            df_features = add_symbol_technicals(df, symbol)
            
            # Keep only date + features (drop raw OHLCV to save memory)
            feature_cols = ['date'] + [c for c in df_features.columns if c.startswith(f'fx_{symbol}_')]
            df_features = df_features[feature_cols].copy()
            
            processed_dfs.append(df_features)
            logger.info(f"   ✅ {symbol}: {len(df_features)} rows, {len(feature_cols)-1} features")
            
        except Exception as e:
            logger.error(f"   ❌ Error processing {symbol}: {e}")
            continue
    
    if not processed_dfs:
        logger.error("❌ No currencies processed")
        return
    
    # Merge all on date (merge 2 at a time, save intermediate to disk)
    logger.info("\n🔗 Merging all currencies...")
    
    # Find common date range
    date_ranges = [(df['date'].min(), df['date'].max()) for df in processed_dfs]
    common_start = max(d[0] for d in date_ranges)
    common_end = min(d[1] for d in date_ranges)
    logger.info(f"   Common date range: {common_start} to {common_end}")
    
    # Filter to common range
    filtered_dfs = []
    for df in processed_dfs:
        df_filtered = df[(df['date'] >= common_start) & (df['date'] <= common_end)].copy()
        df_filtered = df_filtered.set_index('date')
        filtered_dfs.append(df_filtered)
    
    # Merge 2 at a time, save intermediate results
    import gc
    current = filtered_dfs[0]
    for i in range(1, len(filtered_dfs)):
        logger.info(f"   Merging {i+1}/{len(filtered_dfs)}...")
        current = current.join(filtered_dfs[i], how='inner')
        # Force garbage collection every 2 merges
        if i % 2 == 0:
            gc.collect()
    
    combined = current.reset_index().sort_values('date')
    logger.info(f"   ✅ Merged: {len(combined)} rows × {len(combined.columns)} cols")
    
    # Save immediately to free memory
    output_file = STAGING_DIR / "forex_features.parquet"
    combined.to_parquet(output_file, index=False)
    logger.info(f"   💾 Saved base features to {output_file}")
    
    # Reload and add cross-currency features (process in smaller chunks)
    logger.info("\n📊 Adding cross-currency features...")
    combined = pd.read_parquet(output_file)
    
    ret_cols = [c for c in combined.columns if c.endswith('_ret')]
    
    # Currency strength index
    if ret_cols:
        combined['fx_strength_index'] = combined[ret_cols].mean(axis=1)
        combined['fx_volatility_regime'] = pd.cut(
            combined[ret_cols].std(axis=1),
            bins=[0, 0.01, 0.02, 0.05, 1.0],
            labels=['low', 'normal', 'high', 'crisis']
        )
    
    # Currency spreads
    close_cols = {sym: f'fx_{sym}_close' for sym in FOREX_SYMBOLS}
    if close_cols.get('6l') in combined.columns and close_cols.get('cnh') in combined.columns:
        combined['fx_spread_brl_cny'] = combined[close_cols['6l']] - combined[close_cols['cnh']]
    
    # Save again
    combined.to_parquet(output_file, index=False)
    logger.info(f"   ✅ Added basic cross-currency features")
    
    # Save
    output_file = STAGING_DIR / "forex_features.parquet"
    combined.to_parquet(output_file, index=False)
    logger.info(f"\n💾 Saved to {output_file}")
    logger.info(f"   Rows: {len(combined)}, Columns: {len(combined.columns)}")
    
    logger.info("\n✅ Forex Feature Build Complete!")

if __name__ == '__main__':
    main()
