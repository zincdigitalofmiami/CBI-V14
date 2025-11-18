#!/usr/bin/env python3
"""
Server-side helper to fetch the latest 1m bar from DataBento for a given root.

Usage:
  python3 scripts/api/databento_latest_1m.py --root ES [--minutes 60]

Requirements:
  - Environment variable DATABENTO_API_KEY must be set (server-side only)
  - pip install databento

Notes:
  - Uses parent symbology: "{ROOT}.FUT" (e.g., ES.FUT, ZL.FUT)
  - Excludes calendar spreads (symbols containing '-')
  - Picks the "front" bar by highest last-minute volume among outrights in the window
  - Aligns window to dataset end to avoid requesting beyond availability
"""

import argparse
import json
import os
import sys
from datetime import timedelta

try:
    import databento as db
except Exception as e:
    print(json.dumps({
        'ok': False,
        'error': f"databento_import_error: {e}"
    }))
    sys.exit(1)

try:
    from dateutil import parser as dateparser
except Exception:
    # very small fallback without dateutil
    dateparser = None
    import datetime


def to_iso(dt):
    try:
        return dt.isoformat()
    except Exception:
        return str(dt)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', required=True, help='Futures root, e.g., ES, MES, ZL')
    p.add_argument('--minutes', type=int, default=60, help='Lookback minutes (default: 60)')
    args = p.parse_args()

    api_key = os.environ.get('DATABENTO_API_KEY')
    if not api_key:
        print(json.dumps({'ok': False, 'error': 'missing_api_key'}))
        return 2

    root = args.root.strip().upper()
    if not root.isalpha() or len(root) > 5:
        print(json.dumps({'ok': False, 'error': 'invalid_root'}))
        return 2

    try:
        client = db.Historical(api_key)
    except Exception as e:
        print(json.dumps({'ok': False, 'error': f'connect_error: {e}'}))
        return 1

    # Align window to dataset end to avoid requesting beyond availability
    try:
        rng = client.metadata.get_dataset_range('GLBX.MDP3')
        end_s = rng['schema']['ohlcv-1m']['end']
        if dateparser:
            end_dt = dateparser.isoparse(str(end_s))
        else:
            # naive fallback (may not preserve TZ)
            end_dt = datetime.datetime.fromisoformat(str(end_s).replace('Z', '+00:00'))
        start_dt = end_dt - timedelta(minutes=args.minutes)
        window_start = start_dt.strftime('%Y-%m-%dT%H:%M:%S')
        window_end = end_dt.strftime('%Y-%m-%dT%H:%M:%S')
    except Exception as e:
        print(json.dumps({'ok': False, 'error': f'range_error: {e}'}))
        return 1

    parent_symbol = f"{root}.FUT"
    try:
        data = client.timeseries.get_range(
            dataset='GLBX.MDP3',
            symbols=[parent_symbol],
            stype_in='parent',
            schema='ohlcv-1m',
            start=window_start,
            end=window_end,
        )
        if hasattr(data, 'to_df'):
            df = data.to_df()
        else:
            df = data.to_pandas()
    except Exception as e:
        print(json.dumps({'ok': False, 'error': f'get_range_failed: {e}'}))
        return 1

    if df is None or len(df) == 0:
        print(json.dumps({'ok': False, 'error': 'no_data'}))
        return 0

    # Exclude spreads
    try:
        mask_outright = ~df['symbol'].astype(str).str.contains('-')
        df_out = df[mask_outright].copy()
    except Exception:
        df_out = df.copy()

    if len(df_out) == 0:
        print(json.dumps({'ok': False, 'error': 'no_outrights_in_window'}))
        return 0

    # Get last bar per outright symbol
    try:
        last_bars = df_out.groupby('symbol').tail(1)
        # Pick front candidate by largest last-minute volume
        front = last_bars.sort_values('volume', ascending=False).head(1).iloc[0]
        front_symbol = str(front['symbol'])
        bar = {
            'open': float(front.get('open', None)) if 'open' in front else None,
            'high': float(front.get('high', None)) if 'high' in front else None,
            'low': float(front.get('low', None)) if 'low' in front else None,
            'close': float(front.get('close', None)) if 'close' in front else None,
            'volume': int(front.get('volume', 0)) if 'volume' in front else 0,
        }
    except Exception as e:
        print(json.dumps({'ok': False, 'error': f'aggregation_error: {e}'}))
        return 1

    # Build summary with a few candidates
    try:
        sample_candidates = last_bars.sort_values('volume', ascending=False).head(5)
        candidates = [
            {
                'symbol': str(row['symbol']),
                'close': float(row.get('close', None)) if 'close' in row else None,
                'volume': int(row.get('volume', 0)) if 'volume' in row else 0,
            }
            for _, row in sample_candidates.iterrows()
        ]
    except Exception:
        candidates = []

    print(json.dumps({
        'ok': True,
        'root': root,
        'parent': parent_symbol,
        'window': {'start': window_start, 'end': window_end},
        'front_symbol': front_symbol,
        'bar': bar,
        'candidates': candidates,
        'total_rows': int(len(df_out)),
    }))
    return 0


if __name__ == '__main__':
    sys.exit(main())

