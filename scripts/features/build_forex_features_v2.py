#!/usr/bin/env python3
"""
Build Forex Features V2 - Ultra Memory Efficient
================================================

Process each currency separately, save features, then do a simple date-aligned join.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
RAW_DIR = DRIVE / "TrainingData/raw/databento_forex"
STAGING_DIR = DRIVE / "TrainingData/staging/forex_individual"
STAGING_DIR.mkdir(parents=True, exist_ok=True)

def calculate_features_for_symbol(symbol: str, df: pd.DataFrame) -> pd.DataFrame:
    """Calculate all features for a single currency."""
    logger.info(f"   Processing {symbol}...")
    
    prefix = f"fx_{symbol}_"
    df = df.sort_values('date').copy()
    
    # Rename columns for consistency
    close_col = f"{symbol}_close"
    high_col = f"{symbol}_high"
    low_col = f"{symbol}_low"
    
    if close_col not in df.columns:
        logger.warning(f"   Missing {close_col}")
        return pd.DataFrame()
    
    # Returns
    df[f'{prefix}return_1d'] = df[close_col].pct_change(1)
    df[f'{prefix}return_7d'] = df[close_col].pct_change(7)
    df[f'{prefix}return_30d'] = df[close_col].pct_change(30)
    
    # RSI
    def rsi(series, period=14):
        delta = series.diff()
        gain = delta.clip(lower=0).rolling(period, min_periods=period//2).mean()
        loss = (-delta.clip(upper=0)).rolling(period, min_periods=period//2).mean()
        rs = gain / (loss + 1e-10)
        return 100 - (100 / (1 + rs))
    
    df[f'{prefix}rsi_14'] = rsi(df[close_col], 14)
    df[f'{prefix}rsi_7'] = rsi(df[close_col], 7)
    
    # MACD
    ema_12 = df[close_col].ewm(span=12, adjust=False).mean()
    ema_26 = df[close_col].ewm(span=26, adjust=False).mean()
    macd_line = ema_12 - ema_26
    macd_signal = macd_line.ewm(span=9, adjust=False).mean()
    df[f'{prefix}macd_line'] = macd_line
    df[f'{prefix}macd_signal'] = macd_signal
    df[f'{prefix}macd_hist'] = macd_line - macd_signal
    
    # Moving Averages
    for period in [5, 10, 20, 50, 100]:
        df[f'{prefix}sma_{period}'] = df[close_col].rolling(period, min_periods=period//2).mean()
        df[f'{prefix}ema_{period}'] = df[close_col].ewm(span=period, adjust=False).mean()
    
    # Bollinger Bands
    sma_20 = df[close_col].rolling(20, min_periods=10).mean()
    std_20 = df[close_col].rolling(20, min_periods=10).std()
    df[f'{prefix}bb_upper'] = sma_20 + (std_20 * 2)
    df[f'{prefix}bb_lower'] = sma_20 - (std_20 * 2)
    df[f'{prefix}bb_width'] = df[f'{prefix}bb_upper'] - df[f'{prefix}bb_lower']
    df[f'{prefix}bb_position'] = (df[close_col] - df[f'{prefix}bb_lower']) / (df[f'{prefix}bb_width'] + 1e-10)
    
    # Volatility
    for period in [5, 10, 20, 30]:
        df[f'{prefix}vol_{period}d'] = df[close_col].pct_change().rolling(period, min_periods=period//2).std()
    
    # ATR
    if high_col in df.columns and low_col in df.columns:
        hl = df[high_col] - df[low_col]
        hc = (df[high_col] - df[close_col].shift()).abs()
        lc = (df[low_col] - df[close_col].shift()).abs()
        tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        df[f'{prefix}atr_14'] = tr.rolling(14, min_periods=7).mean()
    
    # Keep only date and feature columns
    feature_cols = ['date'] + [c for c in df.columns if c.startswith(prefix)]
    df_out = df[feature_cols].copy()
    
    logger.info(f"   ✅ {symbol}: {len(feature_cols)-1} features")
    return df_out

def main():
    logger.info("🚀 Building Forex Features V2 (Ultra Memory Efficient)")
    logger.info("=" * 60)
    
    # Step 1: Process each currency individually
    forex_files = {f.name.split('_')[0].lower(): f for f in RAW_DIR.glob("*_daily_2010-06-06_*.parquet")}
    
    if not forex_files:
        logger.error("❌ No full history forex files found")
        return
    
    logger.info(f"Step 1: Processing {len(forex_files)} currencies individually...")
    
    for symbol, filepath in sorted(forex_files.items()):
        try:
            df = pd.read_parquet(filepath)
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date']).dt.date
            
            df_features = calculate_features_for_symbol(symbol, df)
            
            if not df_features.empty:
                output_file = STAGING_DIR / f"{symbol}_features.parquet"
                df_features.to_parquet(output_file, index=False)
                logger.info(f"   💾 Saved {output_file.name}")
            
        except Exception as e:
            logger.error(f"   ❌ Error processing {symbol}: {e}")
            continue
    
    # Step 2: Combine all feature files (simple date-aligned join)
    logger.info("\nStep 2: Combining all currency features...")
    
    feature_files = sorted(STAGING_DIR.glob("*_features.parquet"))
    if not feature_files:
        logger.error("❌ No feature files found")
        return
    
    # Load all at once (they're now much smaller - only features, no raw OHLCV)
    dfs = []
    for f in feature_files:
        df = pd.read_parquet(f)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        dfs.append(df)
        logger.info(f"   Loaded {f.name}: {len(df)} rows × {len(df.columns)} cols")
    
    # Merge on date (outer join to keep all dates)
    combined = dfs[0]
    for df in dfs[1:]:
        combined = combined.merge(df, on='date', how='outer')
    
    combined = combined.sort_values('date').reset_index(drop=True)
    logger.info(f"   ✅ Combined: {len(combined)} rows × {len(combined.columns)} cols")
    
    # Step 3: Add cross-currency features
    logger.info("\nStep 3: Adding cross-currency features...")
    
    # Currency strength index
    ret_cols = [c for c in combined.columns if 'return_1d' in c]
    if ret_cols:
        combined['fx_strength_index'] = combined[ret_cols].mean(axis=1)
        combined['fx_volatility_regime'] = pd.cut(
            combined[ret_cols].std(axis=1),
            bins=[-np.inf, 0.01, 0.02, 0.05, np.inf],
            labels=['low', 'normal', 'high', 'crisis']
        )
        logger.info(f"   ✅ Added strength index and volatility regime")
    
    # Key correlations only (to save memory)
    key_pairs = [
        ('6l', 'cnh', 'BRL-CNY'),
        ('6e', '6j', 'EUR-JPY'),
        ('6l', '6e', 'BRL-EUR'),
    ]
    
    for sym1, sym2, name in key_pairs:
        col1 = f'fx_{sym1}_return_1d'
        col2 = f'fx_{sym2}_return_1d'
        if col1 in combined.columns and col2 in combined.columns:
            combined[f'fx_corr_{sym1}_{sym2}_30d'] = combined[col1].rolling(30, min_periods=15).corr(combined[col2])
            combined[f'fx_corr_{sym1}_{sym2}_90d'] = combined[col1].rolling(90, min_periods=45).corr(combined[col2])
            logger.info(f"   ✅ Added {name} correlations")
    
    # Save final output
    output_file = DRIVE / "TrainingData/staging/forex_features.parquet"
    combined.to_parquet(output_file, index=False)
    logger.info(f"\n💾 Saved to {output_file}")
    logger.info(f"   Rows: {len(combined):,}, Columns: {len(combined.columns)}")
    
    # Summary
    feature_count = len([c for c in combined.columns if c.startswith('fx_')])
    logger.info(f"\n✅ Forex Feature Build Complete!")
    logger.info(f"   Total Features: {feature_count}")
    logger.info(f"   Date Range: {combined['date'].min()} to {combined['date'].max()}")

if __name__ == '__main__':
    main()




