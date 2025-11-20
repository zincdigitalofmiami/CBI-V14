#!/usr/bin/env python3
"""
Verify CME Options-on-Futures Access (DataBento GLBX.MDP3)
=========================================================

Checks parent symbology access for common options roots:
- ES.OPT, MES.OPT, OZL.OPT (Soy Oil), OZS.OPT (Soybeans), OZM.OPT (Soy Meal)

Outputs a simple summary (row counts by raw_symbol) to confirm entitlement.

Usage:
  python3 scripts/reference/verify_options_access.py --start 2025-01-01 --end 2025-11-20 

Notes:
- Reads API key from macOS Keychain (preferred) or env var DATABENTO_API_KEY.
- Uses definition schema only (lightweight).
"""

import argparse
import logging
from pathlib import Path
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.keychain_manager import get_api_key  # noqa: E402


def get_databento_historical():
    try:
        import databento as db  # type: ignore
    except ImportError:
        logger.error("databento not installed. pip install databento")
        sys.exit(1)

    # Prefer Keychain, fallback to env
    api_key = get_api_key("DATABENTO_API_KEY")
    if not api_key:
        logger.error("DATABENTO_API_KEY not found (Keychain/env)")
        sys.exit(2)

    try:
        client = db.Historical(api_key)
        return client
    except Exception as e:
        logger.error(f"Failed to init DataBento Historical client: {e}")
        sys.exit(3)


def main():
    parser = argparse.ArgumentParser(description="Verify options-on-futures access via definition schema")
    parser.add_argument("--start", default="2025-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", default="2025-11-20", help="End date (YYYY-MM-DD)")
    parser.add_argument("--symbols", nargs="*", default=["ES.OPT", "MES.OPT", "OZL.OPT", "OZS.OPT", "OZM.OPT"], help="Parent symbols to test")
    args = parser.parse_args()

    client = get_databento_historical()

    logger.info(f"Testing definition access for: {', '.join(args.symbols)}")
    try:
        data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            schema="definition",
            stype_in="parent",
            symbols=args.symbols,
            start=args.start,
            end=args.end,
        )
        df = data.to_df()
        if df.empty:
            logger.warning("No definitions returned. Check entitlements or date range.")
            print("result=empty")
            sys.exit(4)

        # Basic summary
        cols = [c for c in ["raw_symbol", "security_type", "underlying", "expiration", "strike_price"] if c in df.columns]
        print(df[cols].head(10))
        counts = df.groupby("raw_symbol").size().sort_values(ascending=False)
        print("\nCounts by raw_symbol:\n", counts.head(20))
        print("\nOK")
    except Exception as e:
        logger.error(f"Error fetching definitions: {e}")
        sys.exit(5)


if __name__ == "__main__":
    main()

