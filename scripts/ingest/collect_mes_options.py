#!/usr/bin/env python3
"""
Collect MES Options Data from DataBento
========================================

Collects MES (Micro E-mini S&P 500) options data from DataBento GLBX.MDP3.
MES options are accessible via MES.OPT parent symbol (3,516+ contracts confirmed).

Output: Raw options data stored in TrainingData/raw/databento_mes_options/

⚠️ CRITICAL: NO FAKE DATA ⚠️
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import logging
import sys
import subprocess

# Add project root to path
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
RAW_DIR = EXTERNAL_DRIVE / "TrainingData/raw/databento_mes_options"
RAW_DIR.mkdir(parents=True, exist_ok=True)

def get_databento_client():
    """Get DataBento Historical API client."""
    import os
    import subprocess
    
    try:
        import databento as db
    except ImportError:
        logger.error("❌ databento package not installed. Run: pip install databento")
        raise
    
    # Try multiple sources for API key (in order of preference)
    api_key = None
    
    # 1. Try macOS keychain first (most reliable)
    keychain_locations = [
        ("databento", "databento_api_key"),
        ("default", "cbi-v14.DATABENTO_API_KEY"),
    ]
    for account, service in keychain_locations:
        try:
            result = subprocess.run(
                ["security", "find-generic-password", "-w", "-a", account, "-s", service],
                capture_output=True,
                text=True,
                check=True
            )
            api_key = result.stdout.strip()
            if api_key:
                logger.debug(f"Found API key in keychain: {account}/{service}")
                break
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    # 2. Try environment variable
    if not api_key:
        api_key = os.environ.get("DATABENTO_API_KEY")
        if api_key:
            logger.debug("Found API key in DATABENTO_API_KEY environment variable")
    
    # 3. Try keychain_manager utility
    if not api_key:
        try:
            api_key = get_api_key("DATABENTO_API_KEY")
            if api_key:
                logger.debug("Found API key via keychain_manager")
        except:
            pass
    
    if not api_key:
        logger.error("❌ DATABENTO_API_KEY not found in any source")
        raise ValueError("DataBento API key not found")
    
    return db.Historical(api_key)

def collect_mes_options_definitions(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Collect MES options contract definitions.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        
    Returns:
        DataFrame with option contract definitions
    """
    logger.info(f"Collecting MES options definitions from {start_date} to {end_date}")
    
    client = get_databento_client()
    
    try:
        data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            schema="definition",
            stype_in="parent",
            symbols=["MES.OPT"],
            start=start_date,
            end=end_date,
        )
        
        records = []
        count = 0
        for msg in data:
            records.append({
                'ts_event': msg.hd.ts_event if hasattr(msg, 'hd') else None,
                'instrument_id': msg.hd.instrument_id if hasattr(msg, 'hd') else None,
                'raw_symbol': msg.raw_symbol,
                'asset': msg.asset,
                'security_type': msg.security_type,
                'underlying': msg.underlying if hasattr(msg, 'underlying') else None,
                'strike_price': msg.strike_price if hasattr(msg, 'strike_price') else None,
                'expiration': msg.expiration if hasattr(msg, 'expiration') else None,
                'currency': msg.currency if hasattr(msg, 'currency') else None,
                'contract_multiplier': msg.contract_multiplier if hasattr(msg, 'contract_multiplier') else None,
            })
            count += 1
        
        df = pd.DataFrame(records)
        logger.info(f"✅ Collected {len(df)} MES option contract definitions")
        
        if len(df) > 0:
            logger.info(f"   Date range: {df['ts_event'].min() if 'ts_event' in df.columns else 'N/A'} to {df['ts_event'].max() if 'ts_event' in df.columns else 'N/A'}")
            logger.info(f"   Unique symbols: {df['raw_symbol'].nunique() if 'raw_symbol' in df.columns else 0}")
        
        return df
        
    except Exception as e:
        logger.error(f"❌ Error collecting MES options definitions: {e}")
        raise

def collect_mes_options_ohlcv(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Collect MES options OHLCV data.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        
    Returns:
        DataFrame with options OHLCV data
    """
    logger.info(f"Collecting MES options OHLCV from {start_date} to {end_date}")
    
    client = get_databento_client()
    
    try:
        data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            schema="ohlcv-1d",
            stype_in="parent",
            symbols=["MES.OPT"],
            start=start_date,
            end=end_date,
        )
        
        records = []
        count = 0
        for msg in data:
            records.append({
                'ts_event': msg.hd.ts_event if hasattr(msg, 'hd') else None,
                'instrument_id': msg.hd.instrument_id if hasattr(msg, 'hd') else None,
                'open': msg.open if hasattr(msg, 'open') else None,
                'high': msg.high if hasattr(msg, 'high') else None,
                'low': msg.low if hasattr(msg, 'low') else None,
                'close': msg.close if hasattr(msg, 'close') else None,
                'volume': msg.volume if hasattr(msg, 'volume') else None,
            })
            count += 1
            if count % 1000 == 0:
                logger.info(f"   Processed {count} records...")
        
        df = pd.DataFrame(records)
        logger.info(f"✅ Collected {len(df)} MES options OHLCV records")
        
        return df
        
    except Exception as e:
        logger.error(f"❌ Error collecting MES options OHLCV: {e}")
        # OHLCV might not be available for all options, log and continue
        logger.warning(f"   MES options OHLCV may not be available - this is expected for some options")
        return pd.DataFrame()

def save_data(df: pd.DataFrame, filename: str):
    """Save DataFrame to parquet file."""
    if df.empty:
        logger.warning(f"⚠️  No data to save for {filename}")
        return
    
    filepath = RAW_DIR / filename
    df.to_parquet(filepath, index=False)
    logger.info(f"✅ Saved {len(df)} rows to {filepath}")

def main():
    """Main collection function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Collect MES options data from DataBento')
    parser.add_argument('--start', type=str, default=None, help='Start date (YYYY-MM-DD), defaults to 30 days ago')
    parser.add_argument('--end', type=str, default=None, help='End date (YYYY-MM-DD), defaults to today')
    parser.add_argument('--definitions-only', action='store_true', help='Only collect contract definitions')
    parser.add_argument('--ohlcv-only', action='store_true', help='Only collect OHLCV data')
    
    args = parser.parse_args()
    
    # Set date range
    end_date = args.end or datetime.now().strftime('%Y-%m-%d')
    start_date = args.start or (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    logger.info(f"🚀 Starting MES options collection")
    logger.info(f"   Date range: {start_date} to {end_date}")
    logger.info(f"   Output directory: {RAW_DIR}")
    
    try:
        # Collect definitions (always needed for symbol mapping)
        if not args.ohlcv_only:
            logger.info("\n📋 Collecting MES options contract definitions...")
            df_defs = collect_mes_options_definitions(start_date, end_date)
            if not df_defs.empty:
                save_data(df_defs, f'mes_options_definitions_{start_date}_{end_date}.parquet')
        
        # Collect OHLCV data
        if not args.definitions_only:
            logger.info("\n📊 Collecting MES options OHLCV data...")
            df_ohlcv = collect_mes_options_ohlcv(start_date, end_date)
            if not df_ohlcv.empty:
                save_data(df_ohlcv, f'mes_options_ohlcv_{start_date}_{end_date}.parquet')
        
        logger.info("\n✅ MES options collection complete!")
        
    except Exception as e:
        logger.error(f"\n❌ Collection failed: {e}")
        raise

if __name__ == '__main__':
    main()

