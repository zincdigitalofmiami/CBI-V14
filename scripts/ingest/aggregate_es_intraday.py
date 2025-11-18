#!/usr/bin/env python3
"""
Aggregate ES intraday data to daily OHLCV.
Handles multiple timeframes and creates daily features.
Strictly NO SPY proxy usage.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
EXTERNAL_DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
RAW_DIR = EXTERNAL_DRIVE / "TrainingData/raw/alpha_vantage"
STAGING_DIR = EXTERNAL_DRIVE / "TrainingData/staging"

# Define the exact timeframes to be included in the aggregation
DESIRED_TIMEFRAMES = ['5min', '15min', '30min', '60min']

# ES intraday files (ES only; no SPY proxy)
INTRADAY_PATTERNS = [
    "es_intraday_*.parquet"
]

def load_intraday_files():
    """Load ES intraday files for desired timeframes (no SPY)."""
    all_files = []
    
    for pattern in INTRADAY_PATTERNS:
        files = list(RAW_DIR.glob(pattern))
        all_files.extend(files)
    
    logger.info(f"Found {len(all_files)} total intraday files, filtering for: {', '.join(DESIRED_TIMEFRAMES)}")
    
    all_dfs = []
    for f in all_files:
        try:
            # Extract timeframe from filename to decide whether to load the file
            timeframe = 'unknown'
            if '1min' in f.name:
                timeframe = '1min'
            elif '5min' in f.name:
                timeframe = '5min'
            elif '15min' in f.name:
                timeframe = '15min'
            elif '30min' in f.name:
                timeframe = '30min'
            elif '60min' in f.name:
                timeframe = '60min'
            
            # Skip files that are not in the desired timeframes
            if timeframe not in DESIRED_TIMEFRAMES:
                logger.info(f"  Skipping {f.name} (undesired timeframe: {timeframe})")
                continue

            df = pd.read_parquet(f)
            df['timeframe'] = timeframe # Explicitly set the timeframe column
            
            all_dfs.append(df)
            logger.info(f"  Loaded {f.name}: {len(df)} rows")
            
        except Exception as e:
            logger.warning(f"  Failed to load {f.name}: {e}")
    
    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True)
        return combined
    
    return pd.DataFrame()

def aggregate_to_daily(df):
    """Aggregate intraday data to daily OHLCV."""
    
    # Ensure datetime column
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
    elif 'timestamp' in df.columns:
        df['datetime'] = pd.to_datetime(df['timestamp'])
    elif 'time' in df.columns:
        df['datetime'] = pd.to_datetime(df['time'])
    else:
        logger.error("No datetime column found")
        return pd.DataFrame()
    
    # Extract date
    df['date'] = df['datetime'].dt.date
    df['date'] = pd.to_datetime(df['date'])
    
    # Group by date and aggregate
    daily_agg = df.groupby('date').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).reset_index()
    
    # Add additional features
    if not daily_agg.empty:
        # Daily range
        daily_agg['es_daily_range'] = daily_agg['high'] - daily_agg['low']
        daily_agg['es_daily_range_pct'] = daily_agg['es_daily_range'] / daily_agg['open'] * 100
        
        # Daily return
        daily_agg['es_daily_return'] = daily_agg['close'] - daily_agg['open']
        daily_agg['es_daily_return_pct'] = daily_agg['es_daily_return'] / daily_agg['open'] * 100
        
        # Close position in range
        daily_agg['es_close_position'] = (daily_agg['close'] - daily_agg['low']) / (daily_agg['high'] - daily_agg['low'])
        
        # Rename columns with prefix
        rename_dict = {
            'open': 'es_open',
            'high': 'es_high',
            'low': 'es_low',
            'close': 'es_close',
            'volume': 'es_volume'
        }
        daily_agg = daily_agg.rename(columns=rename_dict)
    
    return daily_agg

def calculate_microstructure_features(df):
    """Calculate microstructure features from intraday data."""
    features = []
    
    # Extract date for grouping
    df['date'] = df['datetime'].dt.date
    df['date'] = pd.to_datetime(df['date'])

    # Group by date and timeframe
    for (date, timeframe), group in df.groupby(['date', 'timeframe']):
        if len(group) > 1:
            # Realized volatility (standard deviation of returns)
            group['return'] = group['close'].pct_change()
            realized_vol = group['return'].std()
            
            # High-low volatility (Parkinson)
            hl_vol = ((group['high'] / group['low']).apply(np.log) ** 2).mean() ** 0.5
            
            # Volume-weighted average price (VWAP)
            vwap = (group['close'] * group['volume']).sum() / group['volume'].sum()
            
            # Number of bars
            num_bars = len(group)
            
            features.append({
                'date': date,
                'timeframe': timeframe,
                'realized_vol': realized_vol,
                'hl_vol': hl_vol,
                'vwap': vwap,
                'num_bars': num_bars
            })
    
    if features:
        features_df = pd.DataFrame(features)
        # Pivot on timeframe to make one row per date
        pivot_df = features_df.pivot(index='date', columns='timeframe')
        # Flatten the multi-level columns
        pivot_df.columns = [f"es_{col[1]}_{col[0]}" for col in pivot_df.columns]
        return pivot_df.reset_index()
    
    return pd.DataFrame()

def main():
    """Main aggregation pipeline."""
    logger.info("="*80)
    logger.info("ES INTRADAY AGGREGATION")
    logger.info("="*80)
    
    # Load intraday data
    logger.info("\n1. Loading intraday files...")
    df = load_intraday_files()
    
    if df.empty:
        logger.warning("No intraday data found")
        return
    
    logger.info(f"   Loaded {len(df):,} intraday records")
    
    # Aggregate to daily
    logger.info("\n2. Aggregating to daily...")
    daily = aggregate_to_daily(df)
    logger.info(f"   Created {len(daily):,} daily records")
    
    # Calculate microstructure features
    logger.info("\n3. Calculating microstructure features...")
    if 'date' in df.columns and 'timeframe' in df.columns:
        micro_features = calculate_microstructure_features(df)
        
        if not micro_features.empty:
            # Merge microstructure features
            daily = daily.merge(micro_features, on='date', how='left')
            logger.info(f"   Added {len(micro_features.columns)-1} microstructure features")
    
    # Save to staging
    logger.info("\n4. Saving to staging...")
    output_path = STAGING_DIR / "es_daily_aggregated.parquet"
    daily.to_parquet(output_path, index=False)
    logger.info(f"   ✅ Saved to {output_path}")
    logger.info(f"   {len(daily)} rows × {len(daily.columns)} columns")
    
    # Show sample
    if not daily.empty and 'date' in daily.columns:
        logger.info("\nDate range: {} to {}".format(
            daily['date'].min(),
            daily['date'].max()
        ))
    
    logger.info("\nColumns created:")
    for col in sorted(daily.columns):
        if col != 'date':
            null_pct = daily[col].isna().sum() / len(daily) * 100
            logger.info(f"  - {col}: {null_pct:.1f}% null")
    
    logger.info("\n✅ ES intraday aggregation complete!")

if __name__ == "__main__":
    main()
