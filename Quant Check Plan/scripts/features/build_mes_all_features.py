#!/usr/bin/env python3
"""
Build ALL MES Features for All Horizons
========================================

Calculates technical indicators and features for all 12 MES horizons:
- Intraday: 1min, 5min, 15min, 30min, 1hr, 4hr
- Daily+: 1d, 7d, 30d
- Monthly: 3m, 6m, 12m

Outputs:
- TrainingData/staging/mes_{horizon}_features.parquet for each horizon

⚠️ CRITICAL: NO FAKE DATA ⚠️
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
STAGING_DIR = DRIVE / "TrainingData/staging"

HORIZONS = [
    '1min', '5min', '15min', '30min', '1hr', '4hr',
    '1d', '7d', '30d', '3m', '6m', '12m'
]

def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI (Relative Strength Index)."""
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period, min_periods=1).mean()
    loss = (-delta.clip(upper=0)).rolling(period, min_periods=1).mean()
    rs = gain / (loss.replace(0, np.nan) + 1e-10)
    return 100 - (100 / (1 + rs))

def macd(series: pd.Series, fast=12, slow=26, signal=9):
    """Calculate MACD (Moving Average Convergence Divergence)."""
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    line = ema_fast - ema_slow
    sig = line.ewm(span=signal, adjust=False).mean()
    hist = line - sig
    return line, sig, hist

def bollinger_bands(series: pd.Series, period=20, std_dev=2):
    """Calculate Bollinger Bands."""
    sma = series.rolling(period, min_periods=1).mean()
    std = series.rolling(period, min_periods=1).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    width = upper - lower
    position = (series - lower) / (width + 1e-10)
    return upper, lower, width, position

def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate ATR (Average True Range)."""
    high = df['mes_high']
    low = df['mes_low']
    close = df['mes_close']
    
    hl = high - low
    hc = (high - close.shift()).abs()
    lc = (low - close.shift()).abs()
    
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.rolling(period, min_periods=1).mean()

def calculate_technical_indicators(df: pd.DataFrame, horizon: str) -> pd.DataFrame:
    """Calculate all technical indicators for a horizon."""
    if df.empty or 'mes_close' not in df.columns:
        logger.warning(f"   ⚠️  No data or missing mes_close for {horizon}")
        return df
    
    prefix = f"mes_{horizon}_"
    
    # Sort by datetime/date
    date_col = 'datetime' if 'datetime' in df.columns else 'date'
    if date_col not in df.columns:
        logger.warning(f"   ⚠️  No date/datetime column for {horizon}")
        return df
    
    df = df.sort_values(date_col).copy()
    
    # RSI
    df[f'{prefix}rsi_14'] = rsi(df['mes_close'], 14)
    df[f'{prefix}rsi_7'] = rsi(df['mes_close'], 7)
    df[f'{prefix}rsi_21'] = rsi(df['mes_close'], 21)
    
    # MACD
    macd_line, macd_sig, macd_hist = macd(df['mes_close'])
    df[f'{prefix}macd_line'] = macd_line
    df[f'{prefix}macd_signal'] = macd_sig
    df[f'{prefix}macd_hist'] = macd_hist
    
    # Moving Averages
    for period in [5, 10, 20, 50, 100, 200]:
        df[f'{prefix}sma_{period}'] = df['mes_close'].rolling(period, min_periods=1).mean()
        df[f'{prefix}ema_{period}'] = df['mes_close'].ewm(span=period, adjust=False).mean()
    
    # Bollinger Bands
    bb_upper, bb_lower, bb_width, bb_pos = bollinger_bands(df['mes_close'], 20, 2)
    df[f'{prefix}bb_upper'] = bb_upper
    df[f'{prefix}bb_lower'] = bb_lower
    df[f'{prefix}bb_width'] = bb_width
    df[f'{prefix}bb_position'] = bb_pos
    
    # ATR (if high/low available)
    if 'mes_high' in df.columns and 'mes_low' in df.columns:
        df[f'{prefix}atr_14'] = atr(df, 14)
        df[f'{prefix}atr_7'] = atr(df, 7)
    
    # Returns
    df[f'{prefix}return_1d'] = df['mes_close'].pct_change(1)
    df[f'{prefix}return_7d'] = df['mes_close'].pct_change(7)
    df[f'{prefix}return_30d'] = df['mes_close'].pct_change(30)
    
    # Volatility (realized)
    for period in [5, 10, 20, 30, 60]:
        df[f'{prefix}vol_{period}d'] = df['mes_close'].pct_change().rolling(period, min_periods=period//2).std()
    
    # Price position relative to MAs
    for period in [20, 50, 200]:
        if f'{prefix}sma_{period}' in df.columns:
            df[f'{prefix}dist_sma_{period}'] = (df['mes_close'] - df[f'{prefix}sma_{period}']) / (df[f'{prefix}sma_{period}'] + 1e-10)
    
    # Volume features (if available)
    if 'mes_volume' in df.columns:
        df[f'{prefix}volume_sma_20'] = df['mes_volume'].rolling(20, min_periods=1).mean()
        df[f'{prefix}volume_ratio'] = df['mes_volume'] / (df[f'{prefix}volume_sma_20'] + 1e-10)
        df[f'{prefix}volume_trend'] = df['mes_volume'].rolling(5, min_periods=1).mean() / (df['mes_volume'].rolling(20, min_periods=1).mean() + 1e-10)
    
    logger.info(f"   ✅ Calculated {len([c for c in df.columns if c.startswith(prefix)])} features for {horizon}")
    return df

def main():
    logger.info("🚀 Building ALL MES Features for All Horizons")
    logger.info("=" * 60)
    
    for horizon in HORIZONS:
        input_file = STAGING_DIR / f"mes_{horizon}.parquet"
        output_file = STAGING_DIR / f"mes_{horizon}_features.parquet"
        
        if not input_file.exists():
            logger.warning(f"⚠️  Missing input file: {input_file}")
            continue
        
        logger.info(f"\n📊 Processing {horizon}...")
        
        try:
            df = pd.read_parquet(input_file)
            if df.empty:
                logger.warning(f"   ⚠️  Empty file: {input_file}")
                continue
            
            # Calculate features
            df_features = calculate_technical_indicators(df, horizon)
            
            # Save
            df_features.to_parquet(output_file, index=False)
            logger.info(f"   💾 Saved {len(df_features)} rows × {len(df_features.columns)} cols to {output_file}")
            
        except Exception as e:
            logger.error(f"   ❌ Error processing {horizon}: {e}")
            continue
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ MES Feature Build Complete!")

if __name__ == '__main__':
    main()





