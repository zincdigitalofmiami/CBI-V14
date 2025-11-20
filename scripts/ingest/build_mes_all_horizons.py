#!/usr/bin/env python3
"""
Build ALL MES Training Horizons from 1-Minute Data
==================================================

Creates all 12 MES training horizons from collected 1-minute data:
- Intraday: 1min, 5min, 15min, 30min, 1hr, 4hr
- Daily+: 1d, 7d, 30d
- Monthly: 3m, 6m, 12m

Input: TrainingData/live/MES/1m/date=YYYY-MM-DD/*.parquet
Output: TrainingData/staging/mes_{horizon}.parquet for each horizon

⚠️ CRITICAL: NO FAKE DATA ⚠️
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
LIVE_DIR = DRIVE / "TrainingData/live/MES/1m"
STAGING_DIR = DRIVE / "TrainingData/staging"
STAGING_DIR.mkdir(parents=True, exist_ok=True)

# MES Training Horizons (prod + allhistory)
# Using 'min' instead of deprecated 'T' for pandas resampling
HORIZONS = {
    # Intraday (from 1min resampling)
    '1min': '1min',
    '5min': '5min',
    '15min': '15min',
    '30min': '30min',
    '1hr': '60min',
    '4hr': '240min',
    # Daily+ (from daily aggregation)
    '1d': '1D',
    '7d': '7D',
    '30d': '30D',
    # Monthly (from daily aggregation)
    '3m': '3M',
    '6m': '6M',
    '12m': '12M',
}

def load_all_1m_data() -> pd.DataFrame:
    """Load all 1-minute MES data from live collection."""
    logger.info("Loading all MES 1-minute data...")
    
    if not LIVE_DIR.exists():
        logger.warning(f"Live directory not found: {LIVE_DIR}")
        return pd.DataFrame()
    
    # Find all parquet files
    parquet_files = list(LIVE_DIR.glob("**/*.parquet"))
    if not parquet_files:
        logger.warning(f"No parquet files found in {LIVE_DIR}")
        return pd.DataFrame()
    
    logger.info(f"Found {len(parquet_files)} parquet files")
    
    dfs = []
    for f in parquet_files:
        try:
            df = pd.read_parquet(f)
            
            # Handle datetime - DataBento saves ts_event as index
            if isinstance(df.index, pd.DatetimeIndex):
                # Index is already datetime
                df['datetime'] = df.index
            elif 'ts_event' in df.columns:
                # Handle nanoseconds timestamp (DataBento format)
                ts = df['ts_event']
                if ts.dtype in ['int64', 'int32']:
                    # Convert nanoseconds to datetime
                    df['datetime'] = pd.to_datetime(ts, unit='ns', utc=True)
                else:
                    df['datetime'] = pd.to_datetime(ts, utc=True)
            elif 'datetime' not in df.columns:
                # Try to find datetime column
                for col in ['datetime', 'timestamp', 'time', 'date']:
                    if col in df.columns:
                        df['datetime'] = pd.to_datetime(df[col], utc=True)
                        break
                else:
                    logger.warning(f"No datetime column/index in {f.name}, skipping")
                    continue
            
            # Ensure required columns
            required = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required):
                logger.warning(f"Missing required columns in {f.name}, skipping")
                continue
            
            # Filter to valid MES contracts (exclude spreads)
            if 'symbol' in df.columns:
                df = df[~df['symbol'].astype(str).str.contains('-', na=False)]
            
            dfs.append(df[['datetime'] + required + (['symbol'] if 'symbol' in df.columns else [])])
            
        except Exception as e:
            logger.warning(f"Failed to load {f.name}: {e}")
            continue
    
    if not dfs:
        return pd.DataFrame()
    
    combined = pd.concat(dfs, ignore_index=True)
    combined['datetime'] = pd.to_datetime(combined['datetime'])
    combined = combined.sort_values('datetime').reset_index(drop=True)
    
    logger.info(f"✅ Loaded {len(combined)} total 1-minute bars")
    logger.info(f"   Date range: {combined['datetime'].min()} to {combined['datetime'].max()}")
    
    return combined

def select_active_contract(df: pd.DataFrame) -> pd.DataFrame:
    """
    Select active contract per timestamp using rolling volume window.
    Prevents intraday oscillation during roll weeks.
    """
    if 'symbol' not in df.columns:
        return df
    
    logger.info("Selecting active contract chain...")
    
    # Group by date and symbol to get daily volumes
    df['date'] = df['datetime'].dt.date
    daily_vol = df.groupby(['date', 'symbol'])['volume'].sum().reset_index()
    daily_vol = daily_vol.sort_values('date')
    
    # Build contract calendar using 7-day rolling window
    active_contracts = {}
    for date in sorted(daily_vol['date'].unique()):
        lookback = pd.Timestamp(date) - pd.Timedelta(days=7)
        recent = daily_vol[
            (daily_vol['date'] >= lookback.date()) & 
            (daily_vol['date'] <= date)
        ]
        
        if not recent.empty:
            sym_vol = recent.groupby('symbol')['volume'].sum()
            active_contracts[date] = sym_vol.idxmax()
        else:
            # Fallback: use highest volume symbol for this date
            day_data = daily_vol[daily_vol['date'] == date]
            if not day_data.empty:
                active_contracts[date] = day_data.loc[day_data['volume'].idxmax(), 'symbol']
    
    # Map active contract back to dataframe
    df['active_contract'] = df['date'].map(active_contracts)
    df = df[df['symbol'] == df['active_contract']].copy()
    df = df.drop(columns=['date', 'active_contract'])
    
    logger.info(f"✅ Selected {len(df)} bars from active contract chain")
    return df

def resample_to_horizon(df: pd.DataFrame, horizon: str, rule: str) -> pd.DataFrame:
    """Resample 1-minute data to target horizon."""
    if df.empty:
        return pd.DataFrame()
    
    logger.info(f"Resampling to {horizon} ({rule})...")
    
    # Set datetime as index for resampling
    df_resample = df.set_index('datetime').sort_index()
    
    # Resample OHLCV
    resampled = df_resample.resample(rule).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna(subset=['open', 'high', 'low', 'close'])
    
    if resampled.empty:
        logger.warning(f"   No data after resampling to {horizon}")
        return pd.DataFrame()
    
    # Reset index and rename columns
    resampled = resampled.reset_index()
    resampled = resampled.rename(columns={
        'open': 'mes_open',
        'high': 'mes_high',
        'low': 'mes_low',
        'close': 'mes_close',
        'volume': 'mes_volume'
    })
    
    logger.info(f"   ✅ Created {len(resampled)} {horizon} bars")
    return resampled

def build_daily_horizons(df_daily: pd.DataFrame) -> dict:
    """Build daily+ and monthly horizons from daily data."""
    horizons = {}
    
    if df_daily.empty:
        return horizons
    
    # Ensure date column
    if 'date' not in df_daily.columns:
        df_daily['date'] = pd.to_datetime(df_daily['datetime']).dt.date
        df_daily['date'] = pd.to_datetime(df_daily['date'])
    
    df_daily = df_daily.set_index('date').sort_index()
    
    # Daily horizons
    for horizon, rule in [('1d', '1D'), ('7d', '7D'), ('30d', '30D')]:
        if rule == '1D':
            # 1d is just the daily data
            horizons[horizon] = df_daily.reset_index()
        else:
            resampled = df_daily.resample(rule).agg({
                'mes_open': 'first',
                'mes_high': 'max',
                'mes_low': 'min',
                'mes_close': 'last',
                'mes_volume': 'sum'
            }).dropna()
            horizons[horizon] = resampled.reset_index()
        logger.info(f"   ✅ Created {horizon}: {len(horizons[horizon])} bars")
    
    # Monthly horizons (using 'ME' instead of deprecated 'M')
    for horizon, rule in [('3m', '3ME'), ('6m', '6ME'), ('12m', '12ME')]:
        resampled = df_daily.resample(rule).agg({
            'mes_open': 'first',
            'mes_high': 'max',
            'mes_low': 'min',
            'mes_close': 'last',
            'mes_volume': 'sum'
        }).dropna()
        horizons[horizon] = resampled.reset_index()
        logger.info(f"   ✅ Created {horizon}: {len(horizons[horizon])} bars")
    
    return horizons

def save_horizon(df: pd.DataFrame, horizon: str):
    """Save horizon data to staging."""
    if df.empty:
        logger.warning(f"   ⚠️  No data to save for {horizon}")
        return
    
    output_path = STAGING_DIR / f"mes_{horizon}.parquet"
    df.to_parquet(output_path, index=False)
    logger.info(f"   💾 Saved {len(df)} rows to {output_path}")

def main():
    logger.info("🚀 Building ALL MES Training Horizons")
    logger.info("=" * 60)
    
    # Load all 1-minute data
    df_1m = load_all_1m_data()
    if df_1m.empty:
        logger.error("❌ No 1-minute data found. Run collect_mes_1m.py first.")
        return
    
    # Select active contract chain
    df_1m = select_active_contract(df_1m)
    
    # Build intraday horizons (from 1-minute resampling)
    logger.info("\n📊 Building intraday horizons...")
    intraday_horizons = {}
    
    for horizon, rule in [
        ('1min', '1min'),
        ('5min', '5min'),
        ('15min', '15min'),
        ('30min', '30min'),
        ('1hr', '60min'),
        ('4hr', '240min'),
    ]:
        df_horizon = resample_to_horizon(df_1m, horizon, rule)
        if not df_horizon.empty:
            intraday_horizons[horizon] = df_horizon
            save_horizon(df_horizon, horizon)
    
    # Build daily data first (for daily+ and monthly horizons)
    logger.info("\n📊 Building daily data...")
    df_daily = resample_to_horizon(df_1m, '1d', '1D')
    if not df_daily.empty:
        # Rename datetime to date for daily horizons
        df_daily['date'] = pd.to_datetime(df_daily['datetime']).dt.date
        df_daily['date'] = pd.to_datetime(df_daily['date'])
        df_daily = df_daily.drop(columns=['datetime'])
        save_horizon(df_daily, '1d')
        
        # Build daily+ and monthly horizons
        logger.info("\n📊 Building daily+ and monthly horizons...")
        daily_horizons = build_daily_horizons(df_daily)
        
        for horizon, df_horizon in daily_horizons.items():
            save_horizon(df_horizon, horizon)
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("✅ MES Horizon Build Complete!")
    logger.info(f"   Intraday horizons: {len(intraday_horizons)}")
    logger.info(f"   Daily+ horizons: {len(daily_horizons) if 'daily_horizons' in locals() else 0}")
    logger.info(f"   Total horizons created: {len(intraday_horizons) + len(daily_horizons) if 'daily_horizons' in locals() else len(intraday_horizons) + 1}")

if __name__ == '__main__':
    main()

