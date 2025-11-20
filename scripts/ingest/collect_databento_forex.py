#!/usr/bin/env python3
"""
Collect Forex Futures Data from DataBento
==========================================

Collects daily OHLCV for major FX futures:
- 6L (BRL/USD - Brazilian Real)
- 6E (EUR/USD - Euro)
- 6J (JPY/USD - Japanese Yen)
- 6C (CAD/USD - Canadian Dollar)
- 6B (GBP/USD - British Pound)
- 6A (AUD/USD - Australian Dollar)
- CNH (CNH/USD - Chinese Yuan)

Outputs:
- TrainingData/raw/databento_forex/{symbol}_daily_{start}_{end}.parquet

⚠️ CRITICAL: NO FAKE DATA ⚠️
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import logging
import sys
import subprocess
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

EXTERNAL_DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
RAW_DIR = EXTERNAL_DRIVE / "TrainingData/raw/databento_forex"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Forex symbols to collect
FOREX_SYMBOLS = ['6L', '6E', '6J', '6C', '6B', '6A', 'CNH']

def get_api_key(service_name: str = "databento_api_key") -> str:
    """Retrieve API key from macOS Keychain, environment variable, or local file."""
    # Try macOS keychain first
    keychain_locations = [
        ("databento", "databento_api_key"),
        ("default", "cbi-v14.DATABENTO_API_KEY"),
    ]
    for account, service in keychain_locations:
        try:
            result = subprocess.run(
                ["security", "find-generic-password", "-w", "-a", account, "-s", service],
                capture_output=True, text=True, check=True
            )
            api_key = result.stdout.strip()
            if api_key:
                logger.info(f"✅ API key loaded from macOS Keychain (service: {service})")
                return api_key
        except subprocess.CalledProcessError:
            continue
        except Exception as e:
            logger.debug(f"Error accessing keychain for service {service}: {e}")

    # Try environment variable
    api_key = os.environ.get("DATABENTO_API_KEY")
    if api_key:
        logger.info("✅ API key loaded from environment variable")
        return api_key

    # Try local file
    key_file = Path.home() / ".databento.key"
    if key_file.exists():
        api_key = key_file.read_text().strip()
        if api_key:
            logger.info(f"✅ API key loaded from {key_file}")
            return api_key

    logger.error("❌ DATABENTO_API_KEY not found in any source")
    return None

def get_databento_client():
    """Get DataBento Live API client."""
    try:
        import databento as db
    except ImportError:
        logger.error("❌ databento package not installed. Run: pip install databento")
        return None

    api_key = get_api_key()
    if not api_key:
        raise ValueError("DataBento API key not found")

    # Use Historical API for timeseries queries (Live API doesn't have timeseries)
    return db.Historical(key=api_key)

def collect_forex_symbol(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Collect daily OHLCV for a forex symbol."""
    logger.info(f"Collecting {symbol} from {start_date} to {end_date}")
    client = get_databento_client()
    if not client:
        return pd.DataFrame()

    try:
        # Use parent symbology for futures
        parent_symbol = f"{symbol}.FUT"
        
        data = client.timeseries.get_range(
            dataset='GLBX.MDP3',
            schema='ohlcv-1d',
            stype_in='parent',
            symbols=[parent_symbol],
            start=start_date,
            end=end_date,
        )
        
        df = data.to_df()
        if df.empty:
            logger.warning(f"⚠️  No {symbol} data found for {start_date} to {end_date}")
            return pd.DataFrame()

        logger.info(f"✅ Collected {len(df)} {symbol} records")
        logger.info(f"   Date range: {df.index.min()} to {df.index.max()}")

        # Standardize columns
        df = df.reset_index()
        if 'ts_event' in df.columns:
            df['date'] = pd.to_datetime(df['ts_event']).dt.date
        elif 'datetime' in df.columns:
            df['date'] = pd.to_datetime(df['datetime']).dt.date
        else:
            df['date'] = pd.to_datetime(df.index).date if isinstance(df.index, pd.DatetimeIndex) else None

        # Rename columns with prefix
        rename_map = {
            'open': f'{symbol.lower()}_open',
            'high': f'{symbol.lower()}_high',
            'low': f'{symbol.lower()}_low',
            'close': f'{symbol.lower()}_close',
            'volume': f'{symbol.lower()}_volume',
        }
        
        for old_col, new_col in rename_map.items():
            if old_col in df.columns:
                df[new_col] = pd.to_numeric(df[old_col], errors='coerce')

        # Keep only date and prefixed columns
        keep_cols = ['date'] + [c for c in df.columns if c.startswith(symbol.lower())]
        df = df[keep_cols].copy()

        # Save to raw directory
        output_file = RAW_DIR / f"{symbol.lower()}_daily_{start_date}_{end_date}.parquet"
        df.to_parquet(output_file, index=False)
        logger.info(f"✅ Saved {len(df)} rows to {output_file}")

        return df

    except Exception as e:
        logger.error(f"❌ Error collecting {symbol}: {e}")
        return pd.DataFrame()

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Collect forex futures data from DataBento.")
    parser.add_argument("--start", type=str, default=(datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
                        help="Start date (YYYY-MM-DD). Defaults to 1 year ago.")
    parser.add_argument("--end", type=str, default=datetime.now().strftime('%Y-%m-%d'),
                        help="End date (YYYY-MM-DD). Defaults to today.")
    parser.add_argument("--symbols", type=str, nargs='+', default=FOREX_SYMBOLS,
                        help=f"Forex symbols to collect. Default: {FOREX_SYMBOLS}")
    args = parser.parse_args()

    start_date = args.start
    end_date = args.end

    logger.info("🚀 Starting Forex Futures Collection")
    logger.info(f"   Date range: {start_date} to {end_date}")
    logger.info(f"   Symbols: {args.symbols}")
    logger.info(f"   Output directory: {RAW_DIR}")
    logger.info("")

    all_data = []
    for symbol in args.symbols:
        df = collect_forex_symbol(symbol, start_date, end_date)
        if not df.empty:
            all_data.append(df)

    if all_data:
        # Combine all symbols
        combined = pd.concat(all_data, ignore_index=True)
        # Merge on date (outer join to keep all dates)
        combined = combined.groupby('date').first().reset_index()
        
        output_file = RAW_DIR / f"forex_combined_{start_date}_{end_date}.parquet"
        combined.to_parquet(output_file, index=False)
        logger.info(f"\n✅ Combined forex data: {len(combined)} rows × {len(combined.columns)} cols")
        logger.info(f"   Saved to: {output_file}")

    logger.info("\n✅ Forex collection complete!")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f"\n❌ Collection failed: {e}")
        sys.exit(1)
