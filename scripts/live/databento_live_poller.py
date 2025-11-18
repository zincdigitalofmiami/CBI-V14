#!/usr/bin/env python3
"""
DataBento live 1m poller (forward-only ingestion)

Pulls recent 1m OHLCV bars from GLBX.MDP3 for a list of futures roots using
parent symbology (e.g., ES.FUT) and writes outrights (spreads excluded) as
partitioned Parquet under TrainingData/live/{root}/1m/date=YYYY-MM-DD/.

Designed to be run as a cron/systemd job or simple loop. Keeps a per-root
state file with the last ingested timestamp to avoid duplicates.

Usage examples:
  python3 scripts/live/databento_live_poller.py --roots ES,ZL --once
  python3 scripts/live/databento_live_poller.py --roots ES,ZL --interval 60

Requirements:
  - DATABENTO_API_KEY in environment (server-only)
  - pip install databento pandas pyarrow python-dateutil
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from datetime import timedelta

import pandas as pd

try:
    import databento as db
except Exception as e:
    print(f"databento import error: {e}")
    sys.exit(1)

try:
    from dateutil import parser as dateparser
except Exception:
    dateparser = None
    import datetime

# Optional Google Cloud clients (for GCS + BigQuery mirror)
try:
    from google.cloud import storage  # type: ignore
    from google.cloud import bigquery  # type: ignore
except Exception:
    storage = None
    bigquery = None

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
LIVE_DIR = DRIVE / "TrainingData/live"


def iso_to_dt(s):
    if dateparser:
        return dateparser.isoparse(str(s))
    return datetime.datetime.fromisoformat(str(s).replace('Z', '+00:00'))


def load_state(root: str) -> dict:
    state_path = LIVE_DIR / root / "1m" / "state.json"
    if state_path.exists():
        try:
            return json.loads(state_path.read_text())
        except Exception:
            return {}
    return {}


def save_state(root: str, state: dict):
    state_path = LIVE_DIR / root / "1m" / "state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = state_path.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(state_path)


def write_partition(root: str, df: pd.DataFrame):
    if df is None or df.empty:
        return 0
    # Ensure datetime index to derive date partition
    ts_col = df.index.name if df.index.name else None
    if not ts_col:
        # try detect ts_* column
        for c in df.columns:
            if str(c).startswith('ts'):
                ts_col = c
                break
        if ts_col:
            df = df.set_index(ts_col)

    if df.index.name is None:
        raise ValueError("Timestamp index not found; cannot create date partition")

    # Add root column for clarity
    df = df.copy()
    df['root'] = root

    # Split by date and write parts
    total = 0
    written_files = []
    for date_key, group in df.groupby(df.index.date):
        date_str = pd.Timestamp(date_key).strftime('%Y-%m-%d')
        out_dir = LIVE_DIR / root / "1m" / f"date={date_str}"
        out_dir.mkdir(parents=True, exist_ok=True)
        part_file = out_dir / f"part-{int(pd.Timestamp.utcnow().timestamp())}.parquet"
        # Minimal columns; keep symbol/instrument for later roll logic
        cols = ['open', 'high', 'low', 'close', 'volume', 'symbol', 'instrument_id', 'publisher_id', 'root']
        use_cols = [c for c in cols if c in group.columns]
        group.to_parquet(part_file, engine='pyarrow', index=True, columns=use_cols)
        total += len(group)
        written_files.append(str(part_file))
    return total, written_files


def _load_mirror_state(root: str) -> dict:
    state_path = LIVE_DIR / root / "1m" / "gcs_mirror_state.json"
    if state_path.exists():
        try:
            return json.loads(state_path.read_text())
        except Exception:
            return {"uploaded_files": {}}
    return {"uploaded_files": {}}


def _save_mirror_state(root: str, state: dict):
    state_path = LIVE_DIR / root / "1m" / "gcs_mirror_state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = state_path.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(state_path)


def _gcs_upload_and_bq_load(
    root: str,
    dates: list[str],
    gcs_bucket: str,
    gcs_prefix: str,
    bq_project: str,
    bq_dataset: str,
    bq_table: str = "futures_ohlcv_1m_live",
):
    if storage is None or bigquery is None:
        print("GCS/BQ libraries not available. Skipping mirror.")
        return

    # Initialize clients (ADC must be configured)
    try:
        st_client = storage.Client(project=bq_project)
        bq_client = bigquery.Client(project=bq_project)
    except Exception as e:
        print(f"GCS/BQ client init failed: {e}")
        return

    bucket = st_client.bucket(gcs_bucket)
    mirror_state = _load_mirror_state(root)
    uploaded = mirror_state.get("uploaded_files", {})

    uris_to_load = []
    for d in dates:
        part_dir = LIVE_DIR / root / "1m" / f"date={d}"
        if not part_dir.exists():
            continue
        for part in sorted(part_dir.glob("*.parquet")):
            part_str = str(part.resolve())
            if uploaded.get(part_str):
                continue
            # Upload to GCS under prefix: .../root=<root>/date=<d>/filename
            blob_path = f"{gcs_prefix}/root={root}/date={d}/{part.name}"
            blob = bucket.blob(blob_path)
            try:
                blob.upload_from_filename(part_str)
                gcs_uri = f"gs://{gcs_bucket}/{blob_path}"
                uris_to_load.append(gcs_uri)
                uploaded[part_str] = gcs_uri
                print(f"Uploaded {part.name} -> {gcs_uri}")
            except Exception as e:
                print(f"Upload failed for {part.name}: {e}")

    # Save state early to avoid re-uploads even if load fails (idempotent loads handled by BQ)
    mirror_state["uploaded_files"] = uploaded
    _save_mirror_state(root, mirror_state)

    if not uris_to_load:
        return

    # Load into partitioned table (table must exist with partitioning on DATE(ts_event))
    table_id = f"{bq_project}.{bq_dataset}.{bq_table}"
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        autodetect=True,
    )
    try:
        load_job = bq_client.load_table_from_uri(uris_to_load, table_id, job_config=job_config)
        load_job.result()
        print(f"Loaded {len(uris_to_load)} file(s) into {table_id}")
    except Exception as e:
        print(f"BQ load failed: {e}")


def poll_once(
    client: "db.Historical",
    root: str,
    lookback_minutes: int = 120,
    mirror_to_bq: bool = False,
    gcs_bucket: str | None = None,
    gcs_prefix: str = "market_data/futures_ohlcv_1m_live",
    bq_project: str | None = None,
    bq_dataset: str | None = None,
) -> int:
    parent_symbol = f"{root}.FUT"

    # Align to dataset end and compute start based on state or lookback
    rng = client.metadata.get_dataset_range('GLBX.MDP3')
    end_s = rng['schema']['ohlcv-1m']['end']
    end_dt = iso_to_dt(end_s)

    state = load_state(root)
    last_ts = state.get('last_ts')
    if last_ts:
        start_dt = iso_to_dt(last_ts) + timedelta(minutes=1)
        # safety: if start after end, back off
        if start_dt > end_dt:
            start_dt = end_dt - timedelta(minutes=lookback_minutes)
    else:
        start_dt = end_dt - timedelta(minutes=lookback_minutes)

    start_s = start_dt.strftime('%Y-%m-%dT%H:%M:%S')
    end_s2 = end_dt.strftime('%Y-%m-%dT%H:%M:%S')

    # Fetch 1m OHLCV
    data = client.timeseries.get_range(
        dataset='GLBX.MDP3',
        symbols=[parent_symbol],
        stype_in='parent',
        schema='ohlcv-1m',
        start=start_s,
        end=end_s2,
    )
    df = data.to_df() if hasattr(data, 'to_df') else data.to_pandas()
    if df is None or df.empty:
        return 0

    # Exclude calendar spreads
    try:
        df = df[~df['symbol'].astype(str).str.contains('-')]
    except Exception:
        pass

    # Write partitions
    wrote, files = write_partition(root, df)

    # Update state with the max timestamp
    try:
        new_last = str(df.index.max())
        state['last_ts'] = new_last
        save_state(root, state)
    except Exception:
        pass

    # Optional mirror to GCS + BQ
    if mirror_to_bq and gcs_bucket and bq_project and bq_dataset:
        # Determine which dates we just wrote
        try:
            dates = sorted({pd.Timestamp(ts).strftime('%Y-%m-%d') for ts in df.index})
            _gcs_upload_and_bq_load(
                root=root,
                dates=dates,
                gcs_bucket=gcs_bucket,
                gcs_prefix=gcs_prefix,
                bq_project=bq_project,
                bq_dataset=bq_dataset,
            )
        except Exception as e:
            print(f"Mirror step failed: {e}")

    return wrote


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--roots', required=True, help='Comma-separated futures roots, e.g., ES,ZL,CL')
    ap.add_argument('--interval', type=int, default=0, help='Loop interval seconds (0 = run once)')
    ap.add_argument('--lookback', type=int, default=120, help='Minutes to backfill on first run')
    ap.add_argument('--once', action='store_true', help='Run once and exit')
    # Optional GCS + BigQuery mirror
    ap.add_argument('--mirror-bq', action='store_true', help='Upload new parts to GCS and load into BigQuery')
    ap.add_argument('--gcs-bucket', help='GCS bucket for parquet uploads')
    ap.add_argument('--gcs-prefix', default='market_data/futures_ohlcv_1m_live', help='GCS prefix/path')
    ap.add_argument('--bq-project', help='BigQuery project ID')
    ap.add_argument('--bq-dataset', help='BigQuery dataset name (e.g., market_data)')
    args = ap.parse_args()

    api_key = os.environ.get('DATABENTO_API_KEY')
    if not api_key:
        print('ERROR: DATABENTO_API_KEY not set')
        return 2

    client = db.Historical(api_key)
    roots = [r.strip().upper() for r in args.roots.split(',') if r.strip()]

    def run_cycle():
        total = 0
        for root in roots:
            try:
                n = poll_once(
                    client,
                    root,
                    args.lookback,
                    mirror_to_bq=args.mirror_bq,
                    gcs_bucket=args.gcs_bucket,
                    gcs_prefix=args.gcs_prefix,
                    bq_project=args.bq_project,
                    bq_dataset=args.bq_dataset,
                )
                print(f"{root}: wrote {n} bars")
                total += n
            except Exception as e:
                print(f"{root}: error {e}")
        return total

    if args.once or args.interval <= 0:
        run_cycle()
        return 0

    # Looping mode
    while True:
        run_cycle()
        time.sleep(max(5, args.interval))


if __name__ == '__main__':
    sys.exit(main())
