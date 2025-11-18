#!/usr/bin/env python3
"""
Fetch OHLCV range from DataBento for a root and timeframe.

Examples:
  python3 scripts/api/databento_ohlcv_range.py --root ES --tf 1m --minutes 90
  python3 scripts/api/databento_ohlcv_range.py --root ZL --tf 1h --hours 48
  python3 scripts/api/databento_ohlcv_range.py --root ES --tf 1d --days 365

Output (JSON):
{
  ok: true,
  meta: { root, schema, window: { start, end } },
  front_symbol: "ESZ5",
  bars: [ { ts: "...", symbol: "ESZ5", o,h,l,c,v }, ... ]
}

Notes:
  - Uses GLBX.MDP3 and parent symbology {ROOT}.FUT
  - Excludes calendar spreads (symbols containing '-')
  - If --front-only is set (default false), returns only bars for detected front outright
  - Aligns queries to dataset end when lookback is specified
"""

import argparse
import json
import os
import sys
from datetime import timedelta

try:
    import databento as db
except Exception as e:
    print(json.dumps({'ok': False, 'error': f'databento_import_error: {e}'}))
    sys.exit(1)

try:
    from dateutil import parser as dateparser
except Exception:
    dateparser = None
    import datetime


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', required=True, help='Futures root, e.g., ES, MES, ZL')
    p.add_argument('--tf', choices=['1m', '1h', '1d'], default='1m', help='Timeframe')
    lb = p.add_mutually_exclusive_group()
    lb.add_argument('--minutes', type=int)
    lb.add_argument('--hours', type=int)
    lb.add_argument('--days', type=int)
    p.add_argument('--start')
    p.add_argument('--end')
    p.add_argument('--front-only', action='store_true', default=False)
    args = p.parse_args()

    api_key = os.environ.get('DATABENTO_API_KEY')
    if not api_key:
        print(json.dumps({'ok': False, 'error': 'missing_api_key'}))
        return 2

    root = args.root.strip().upper()
    if not root.isalpha() or len(root) > 5:
        print(json.dumps({'ok': False, 'error': 'invalid_root'}))
        return 2

    schema_map = {'1m': 'ohlcv-1m', '1h': 'ohlcv-1h', '1d': 'ohlcv-1d'}
    schema = schema_map[args.tf]

    # Build start/end
    start_s = args.start
    end_s = args.end
    try:
        client = db.Historical(api_key)
    except Exception as e:
        print(json.dumps({'ok': False, 'error': f'connect_error: {e}'}))
        return 1

    if not (start_s and end_s):
        # Align to dataset end
        try:
            rng = client.metadata.get_dataset_range('GLBX.MDP3')
            ds_end_s = rng['schema'][schema]['end']
            if dateparser:
                ds_end = dateparser.isoparse(str(ds_end_s))
            else:
                ds_end = datetime.datetime.fromisoformat(str(ds_end_s).replace('Z', '+00:00'))
        except Exception as e:
            print(json.dumps({'ok': False, 'error': f'range_error: {e}'}))
            return 1

        lookback = timedelta()
        if args.minutes:
            lookback = timedelta(minutes=args.minutes)
        elif args.hours:
            lookback = timedelta(hours=args.hours)
        elif args.days:
            lookback = timedelta(days=args.days)
        else:
            lookback = timedelta(minutes=60)  # sensible default

        start_dt = ds_end - lookback
        start_s = start_dt.strftime('%Y-%m-%dT%H:%M:%S')
        end_s = ds_end.strftime('%Y-%m-%dT%H:%M:%S')

    parent_symbol = f"{root}.FUT"
    try:
        data = client.timeseries.get_range(
            dataset='GLBX.MDP3',
            symbols=[parent_symbol],
            stype_in='parent',
            schema=schema,
            start=start_s,
            end=end_s,
        )
        if hasattr(data, 'to_df'):
            df = data.to_df()
        else:
            df = data.to_pandas()
    except Exception as e:
        print(json.dumps({'ok': False, 'error': f'get_range_failed: {e}'}))
        return 1

    if df is None or len(df) == 0:
        print(json.dumps({'ok': False, 'error': 'no_data', 'meta': {'root': root, 'schema': schema, 'window': {'start': start_s, 'end': end_s}}}))
        return 0

    # Identify timestamp column (index name or first ts_* column)
    ts_col = None
    try:
        if getattr(df.index, 'name', None):
            ts_col = df.index.name
        else:
            for c in df.columns:
                if str(c).startswith('ts'):
                    ts_col = c
                    break
    except Exception:
        ts_col = None

    # Spread filter and optional front-only
    df_out = df.copy()
    try:
        mask_outright = ~df_out['symbol'].astype(str).str.contains('-')
        df_out = df_out[mask_outright]
    except Exception:
        pass

    # Compute front symbol by last bar volume
    front_symbol = None
    try:
        last_bars = df_out.groupby('symbol').tail(1)
        if len(last_bars) > 0:
            front_symbol = str(last_bars.sort_values('volume', ascending=False).head(1).iloc[0]['symbol'])
    except Exception:
        pass

    if args.front_only and front_symbol:
        df_out = df_out[df_out['symbol'] == front_symbol]

    # Build bars array
    bars = []
    try:
        if ts_col and df_out.index.name == ts_col:
            iterator = df_out.itertuples()
            for row in iterator:
                ts = str(row.Index)
                rec = {
                    'ts': ts,
                    'symbol': str(getattr(row, 'symbol', None)),
                    'open': float(getattr(row, 'open', None)) if hasattr(row, 'open') else None,
                    'high': float(getattr(row, 'high', None)) if hasattr(row, 'high') else None,
                    'low': float(getattr(row, 'low', None)) if hasattr(row, 'low') else None,
                    'close': float(getattr(row, 'close', None)) if hasattr(row, 'close') else None,
                    'volume': int(getattr(row, 'volume', 0)) if hasattr(row, 'volume') else 0,
                }
                bars.append(rec)
        else:
            # fallback
            for _, r in df_out.iterrows():
                ts = None
                for c in df_out.columns:
                    if str(c).startswith('ts'):
                        ts = str(r[c])
                        break
                rec = {
                    'ts': ts,
                    'symbol': str(r.get('symbol')),
                    'open': float(r.get('open')) if 'open' in r else None,
                    'high': float(r.get('high')) if 'high' in r else None,
                    'low': float(r.get('low')) if 'low' in r else None,
                    'close': float(r.get('close')) if 'close' in r else None,
                    'volume': int(r.get('volume', 0)) if 'volume' in r else 0,
                }
                bars.append(rec)
    except Exception as e:
        print(json.dumps({'ok': False, 'error': f'serialization_error: {e}'}))
        return 1

    print(json.dumps({
        'ok': True,
        'meta': { 'root': root, 'schema': schema, 'window': { 'start': start_s, 'end': end_s } },
        'front_symbol': front_symbol,
        'bars': bars,
    }))
    return 0


if __name__ == '__main__':
    sys.exit(main())

