#!/usr/bin/env python3
"""
Check DataBento live subscription capabilities quickly.

Attempts to instantiate the Live client and list datasets/schemas using
available APIs. Prints a short summary so we can confirm entitlements.

Usage:
  python3 scripts/live/check_live_subscription.py
"""

import os
import sys

try:
    import databento as db
except Exception as e:
    print(f"databento import error: {e}")
    sys.exit(1)


def main() -> int:
    api_key = os.environ.get("DATABENTO_API_KEY")
    if not api_key:
        print("ERROR: DATABENTO_API_KEY not found in environment.")
        return 2

    # Try Live client
    try:
        live = db.Live(key=api_key)
        print("Live client: OK")
    except Exception as e:
        print(f"Live client init failed: {e}")
        return 1

    # Try to list datasets/schemas using metadata where possible
    try:
        hist = db.Historical(api_key)
        datasets = hist.metadata.list_datasets()
        print("Datasets:", ", ".join(datasets))
        schemas = hist.metadata.list_schemas("GLBX.MDP3")
        print("GLBX.MDP3 schemas:", ", ".join(schemas))
    except Exception as e:
        print(f"Metadata listing failed: {e}")

    print("\nQuick note: For live streaming we will subscribe to GLBX.MDP3 with schema 'ohlcv-1m' and roots from the universe.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

