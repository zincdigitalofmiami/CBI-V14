#!/usr/bin/env python3
"""
Build forward-only continuous series from live 1m outrights.

Reads TrainingData/live/{root}/1m/date=YYYY-MM-DD/*.parquet, selects the
"front" symbol for each minute by highest per-minute volume across outrights,
and writes a continuous series to TrainingData/live_continuous/{root}/1m/
partitioned by date.

This is forward-only: it won't rewrite historical days. Intended to be run
periodically (e.g., every few minutes or hourly).

Usage:
  python3 scripts/ingest/build_forward_continuous.py --root ES --days 2
  python3 scripts/ingest/build_forward_continuous.py --root ZL --date 2025-11-18

Requirements:
  - pandas, pyarrow
"""

import argparse
from pathlib import Path
import sys
import pandas as pd
import pyarrow.dataset as ds

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
LIVE_DIR = DRIVE / "TrainingData/live"
OUT_DIR = DRIVE / "TrainingData/live_continuous"


def read_live_1m(root: str, dates: list[str]) -> pd.DataFrame:
    root_dir = LIVE_DIR / root / "1m"
    frames = []
    for d in dates:
        part = root_dir / f"date={d}"
        if not part.exists():
            continue
        dataset = ds.dataset(str(part), format="parquet")
        table = dataset.to_table()
        df = table.to_pandas()
        # Ensure ts index
        if df.index.name is None:
            # try to find ts column
            ts_col = None
            for c in df.columns:
                if str(c).startswith('ts'):
                    ts_col = c
                    break
            if ts_col:
                df = df.set_index(ts_col)
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames).sort_index()
    # Filter sanity: exclude spreads if any slipped in
    try:
        df = df[~df['symbol'].astype(str).str.contains('-')]
    except Exception:
        pass
    return df


def build_continuous(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    # Last bar per minute per symbol might be multiple symbols per ts
    # For each timestamp, pick the symbol with highest volume at that ts
    grp = df.groupby(['symbol'])
    # Normalize index to minute (already minute bars)
    # Combine all symbols at each ts
    def pick_front(group: pd.DataFrame) -> pd.DataFrame:
        return group
    # Reindex not necessary; we will pivot then argmax by volume
    pivot = df[['volume']].copy()
    # Compute per-ts winner
    winners = df.groupby(df.index).apply(lambda g: g.sort_values('volume', ascending=False).head(1))
    winners = winners.droplevel(0)
    # Build continuous by taking OHLCV from winner rows
    cont = winners[['open', 'high', 'low', 'close', 'volume']].copy()
    cont['symbol_front'] = winners['symbol']
    return cont


def write_continuous(root: str, cont: pd.DataFrame):
    if cont.empty:
        return 0
    out_root = OUT_DIR / root / "1m"
    total = 0
    for date_key, group in cont.groupby(cont.index.date):
        date_str = pd.Timestamp(date_key).strftime('%Y-%m-%d')
        out_dir = out_root / f"date={date_str}"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"part-{int(pd.Timestamp.utcnow().timestamp())}.parquet"
        group.to_parquet(out_file, engine='pyarrow', index=True)
        total += len(group)
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--date', help='YYYY-MM-DD (single day)')
    ap.add_argument('--days', type=int, default=1, help='Process last N days including today')
    args = ap.parse_args()

    # Determine dates to process
    if args.date:
        dates = [args.date]
    else:
        today = pd.Timestamp.utcnow().tz_localize('UTC').date()
        dates = [(pd.Timestamp(today) - pd.Timedelta(days=i)).strftime('%Y-%m-%d') for i in range(max(1, args.days))]
        dates = sorted(set(dates))

    df = read_live_1m(args.root.upper(), dates)
    if df.empty:
        print('No live data found for requested dates')
        return 0
    cont = build_continuous(df)
    n = write_continuous(args.root.upper(), cont)
    print(f'Wrote {n} continuous bars for {args.root.upper()} over {len(dates)} day(s)')
    return 0


if __name__ == '__main__':
    sys.exit(main())

