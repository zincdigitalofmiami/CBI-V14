#!/usr/bin/env python3
"""
Volatility & VIX Collection - Daily Snapshots
==============================================
Collects daily volatility snapshots: VIX (implied vol) + realized volatility for ZL, ES, Palm.

Sources:
- VIX: Yahoo Finance (^VIX) + FRED (VIXCLS) for cross-validation
- Realized Vol: Calculated from price returns (20d, 30d, 60d, 90d rolling windows)
- Vol Regime: Classified based on VIX levels and realized vol percentiles

Prefix: `vol_*` on all columns except `date`

Coverage: Daily snapshots, 2000→present (historical backfill)
"""

import yfinance as yf
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import logging
import time
import sys
import requests

# Add src to path for keychain access
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.keychain_manager import get_api_key

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
EXTERNAL_DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
RAW_DIR = EXTERNAL_DRIVE / "TrainingData/raw/volatility"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Symbols for realized vol calculation
SYMBOLS = {
    'ZL=F': 'soybean_oil',
    'ES=F': 'sp500_emini',  # ES only — no SPY proxy
    'CPO': 'palm_oil',      # Palm composite
}

# Volatility windows (days)
VOL_WINDOWS = [20, 30, 60, 90]

# VIX regime thresholds
VIX_REGIME_THRESHOLDS = {
    'low': 15,
    'medium': 25,
    'high': 35,
    'extreme': 50
}

def fetch_vix_yahoo() -> pd.DataFrame:
    """
    Fetch VIX data from Yahoo Finance.
    
    Returns:
        DataFrame with date and VIX level
    """
    logger.info("Fetching VIX from Yahoo Finance...")
    
    try:
        vix_ticker = yf.Ticker('^VIX')
        # Get max history (25+ years)
        vix_history = vix_ticker.history(period='max')
        
        if vix_history.empty:
            logger.warning("No VIX data from Yahoo Finance")
            return pd.DataFrame()
        
        # Convert to daily format
        df = pd.DataFrame()
        df['date'] = pd.to_datetime(vix_history.index).date
        df['vol_vix_level'] = vix_history['Close'].values
        df['vol_vix_open'] = vix_history['Open'].values
        df['vol_vix_high'] = vix_history['High'].values
        df['vol_vix_low'] = vix_history['Low'].values
        
        logger.info(f"✅ Yahoo VIX: {len(df)} rows ({df['date'].min()} to {df['date'].max()})")
        return df
        
    except Exception as e:
        logger.error(f"❌ Yahoo VIX fetch failed: {e}")
        return pd.DataFrame()

def fetch_vix_fred() -> pd.DataFrame:
    """
    Fetch VIX from FRED (VIXCLS) for cross-validation.
    
    Returns:
        DataFrame with date and VIX level
    """
    logger.info("Fetching VIX from FRED (VIXCLS)...")
    
    try:
        api_key = get_api_key('FRED_API_KEY')
        if not api_key:
            logger.warning("No FRED API key found, skipping FRED VIX")
            return pd.DataFrame()
        
        url = 'https://api.stlouisfed.org/fred/series/observations'
        params = {
            'series_id': 'VIXCLS',
            'api_key': api_key,
            'file_type': 'json',
            'observation_start': '2000-01-01',
            'sort_order': 'asc'
        }
        
        response = requests.get(url, params=params, timeout=60)
        
        if response.status_code != 200:
            logger.warning(f"FRED API returned {response.status_code}")
            return pd.DataFrame()
        
        data = response.json()
        
        if 'observations' not in data:
            logger.warning("No observations in FRED response")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(data['observations'])
        df['date'] = pd.to_datetime(df['date']).dt.date
        df['vol_vix_fred'] = pd.to_numeric(df['value'], errors='coerce')
        df = df[['date', 'vol_vix_fred']].dropna()
        
        logger.info(f"✅ FRED VIX: {len(df)} rows ({df['date'].min()} to {df['date'].max()})")
        return df
        
    except Exception as e:
        logger.error(f"❌ FRED VIX fetch failed: {e}")
        return pd.DataFrame()

def calculate_realized_volatility(symbol: str, proxy_symbol: str = None) -> pd.DataFrame:
    """
    Calculate realized volatility for a symbol using rolling windows.
    
    Args:
        symbol: Symbol to calculate vol for (e.g., 'ZL=F')
        proxy_symbol: Deprecated; no proxies are used
    
    Returns:
        DataFrame with date and realized vol columns
    """
    logger.info(f"Calculating realized volatility for {symbol}...")
    
    try:
        # No proxies allowed; always use the primary symbol
        fetch_symbol = symbol
        ticker = yf.Ticker(fetch_symbol)
        
        # Get max history
        history = ticker.history(period='max')
        
        if history.empty:
            logger.warning(f"No price data for {fetch_symbol}")
            return pd.DataFrame()
        
        # Calculate returns
        history['returns'] = history['Close'].pct_change()
        
        # Calculate realized volatility for each window
        df = pd.DataFrame()
        df['date'] = pd.to_datetime(history.index).date
        
        for window in VOL_WINDOWS:
            # Annualized realized vol (sqrt(252) for daily data)
            df[f'vol_{symbol.replace("=", "").replace("^", "").lower()}_realized_{window}d'] = (
                history['returns'].rolling(window=window).std() * np.sqrt(252) * 100
            ).values
        
        # Drop rows with all NaN
        df = df.dropna(how='all')
        
        logger.info(f"✅ Realized vol for {symbol}: {len(df)} rows")
        return df
        
    except Exception as e:
        logger.error(f"❌ Realized vol calculation failed for {symbol}: {e}")
        return pd.DataFrame()

def classify_vol_regime(vix_df: pd.DataFrame) -> pd.DataFrame:
    """
    Classify volatility regime based on VIX levels.
    
    Args:
        vix_df: DataFrame with vol_vix_level column
    
    Returns:
        DataFrame with vol_regime column
    """
    if vix_df.empty or 'vol_vix_level' not in vix_df.columns:
        return pd.DataFrame()
    
    df = vix_df.copy()
    
    # Classify regime
    def classify_vix(vix_level):
        if pd.isna(vix_level):
            return None
        if vix_level < VIX_REGIME_THRESHOLDS['low']:
            return 'low'
        elif vix_level < VIX_REGIME_THRESHOLDS['medium']:
            return 'medium'
        elif vix_level < VIX_REGIME_THRESHOLDS['high']:
            return 'high'
        elif vix_level < VIX_REGIME_THRESHOLDS['extreme']:
            return 'extreme'
        else:
            return 'extreme'
    
    df['vol_regime'] = df['vol_vix_level'].apply(classify_vix)
    
    # Add percentile ranks
    df['vol_vix_percentile_30d'] = df['vol_vix_level'].rolling(30).apply(
        lambda x: pd.Series(x).rank(pct=True).iloc[-1] if len(x) == 30 else np.nan
    )
    df['vol_vix_percentile_90d'] = df['vol_vix_level'].rolling(90).apply(
        lambda x: pd.Series(x).rank(pct=True).iloc[-1] if len(x) == 90 else np.nan
    )
    
    return df

def main():
    """
    Main collection function: VIX + realized vol for all symbols.
    """
    logger.info("=" * 80)
    logger.info("VOLATILITY & VIX COLLECTION")
    logger.info("=" * 80)
    logger.info("Daily vol snapshots: VIX + realized vol (20d, 30d, 60d, 90d)")
    logger.info("")
    
    # 1. Fetch VIX from Yahoo
    vix_yahoo = fetch_vix_yahoo()
    
    # 2. Fetch VIX from FRED (cross-validation)
    vix_fred = fetch_vix_fred()
    
    # 3. Merge VIX sources
    vix_combined = vix_yahoo.copy() if not vix_yahoo.empty else pd.DataFrame()
    
    if not vix_fred.empty:
        if vix_combined.empty:
            vix_combined = vix_fred.copy()
        else:
            vix_combined = vix_combined.merge(
                vix_fred,
                on='date',
                how='outer',
                suffixes=('', '_fred')
            )
    
    # 4. Calculate realized volatility for each symbol
    realized_vol_dfs = []
    
    for symbol in ['ZL=F', 'ES=F', 'CPO']:
        vol_df = calculate_realized_volatility(symbol)
        if not vol_df.empty:
            realized_vol_dfs.append(vol_df)
        time.sleep(1)  # Rate limiting
    
    # 5. Merge all realized vol DataFrames
    if realized_vol_dfs:
        realized_vol_combined = realized_vol_dfs[0]
        for vol_df in realized_vol_dfs[1:]:
            realized_vol_combined = realized_vol_combined.merge(
                vol_df,
                on='date',
                how='outer'
            )
    else:
        realized_vol_combined = pd.DataFrame()
    
    # 6. Merge VIX with realized vol
    if vix_combined.empty and realized_vol_combined.empty:
        logger.error("❌ No volatility data collected")
        return
    
    if vix_combined.empty:
        volatility_df = realized_vol_combined.copy()
    elif realized_vol_combined.empty:
        volatility_df = vix_combined.copy()
    else:
        volatility_df = vix_combined.merge(
            realized_vol_combined,
            on='date',
            how='outer'
        )
    
    # 7. Classify volatility regime
    volatility_df = classify_vol_regime(volatility_df)
    
    # 8. Sort by date
    volatility_df = volatility_df.sort_values('date').reset_index(drop=True)
    
    # 9. Save raw data
    output_file = RAW_DIR / f"volatility_daily_{datetime.now().strftime('%Y%m%d')}.parquet"
    volatility_df.to_parquet(output_file, index=False)
    
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"✅ VOLATILITY COLLECTION COMPLETE")
    logger.info(f"   Rows: {len(volatility_df):,}")
    logger.info(f"   Date range: {volatility_df['date'].min()} to {volatility_df['date'].max()}")
    logger.info(f"   Columns: {len(volatility_df.columns)}")
    logger.info(f"   Saved to: {output_file}")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
