#!/usr/bin/env python3
"""
Create MES futures daily parquet from Databento JSON/Parquet downloads.
Scans /TrainingData/raw/databento_mes for ohlcv-1d files, merges, and writes
to /TrainingData/staging/mes_futures_daily.parquet with mes_ prefixed cols.
"""

import json
from pathlib import Path
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
RAW_DIR = DRIVE / "TrainingData/raw/databento_mes"
OUT = DRIVE / "TrainingData/staging/mes_futures_daily.parquet"

def load_one(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == '.parquet':
        df = pd.read_parquet(path)
    elif path.suffix.lower() == '.json':
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            if isinstance(data, dict) and 'data' in data:
                records = data['data']
            else:
                records = data
            # Flatten nested hd structure
            flat = []
            for r in records:
                hd = r.get('hd', {})
                flat.append({
                    'ts_event': hd.get('ts_event'),
                    'open': r.get('open'),
                    'high': r.get('high'),
                    'low': r.get('low'),
                    'close': r.get('close'),
                    'volume': r.get('volume'),
                    'symbol': r.get('symbol')
                })
            df = pd.DataFrame.from_records(flat)
        except json.JSONDecodeError:
            # NDJSON (one record per line)
            records = []
            with open(path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    records.append(json.loads(line))
            # Flatten hd.ts_event
            flat = []
            for r in records:
                hd = r.get('hd', {})
                flat.append({
                    'ts_event': hd.get('ts_event'),
                    'open': r.get('open'),
                    'high': r.get('high'),
                    'low': r.get('low'),
                    'close': r.get('close'),
                    'volume': r.get('volume'),
                    'symbol': r.get('symbol')
                })
            df = pd.DataFrame(flat)
    else:
        raise ValueError(f"Unsupported type {path}")
    # Databento ohlcv schema columns: ts_event, open, high, low, close, volume
    tcol = 'ts_event' if 'ts_event' in df.columns else ('time' if 'time' in df.columns else 'timestamp')
    df['date'] = pd.to_datetime(df[tcol]).dt.date
    df['date'] = pd.to_datetime(df['date'])
    keep = ['date','open','high','low','close','volume','symbol']
    for k in keep:
        if k not in df.columns:
            raise ValueError(f"Missing {k} in {path}")
    
    # STRICT symbol validation - FAIL FAST if missing
    if 'symbol' not in df.columns:
        raise ValueError(f"Missing symbol column in {path} - fix data source")
    
    # Enforce outright-only MES contracts
    df = df[df['symbol'].str.match(r'^MES[A-Z]\d+$', na=False)]
    if df.empty:
        raise ValueError(f"No valid MES outright contracts in {path} after filtering")
    
    # Numeric coercion
    for col in ('open', 'high', 'low', 'close', 'volume'):
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['open', 'high', 'low', 'close'])
    
    if df.empty:
        raise ValueError(f"No valid numeric OHLCV data in {path}")
    
    return df[keep]

def main():
    files = sorted(list(RAW_DIR.glob('**/*ohlcv-1d*.*')))
    if not files:
        logger.warning(f"No ohlcv-1d files found in {RAW_DIR}")
        return
    parts = []
    for f in files:
        try:
            df = load_one(f)
            parts.append(df)
            logger.info(f"Loaded {f.name}: {len(df)} rows")
        except Exception as e:
            logger.warning(f"Skip {f.name}: {e}")
    if not parts:
        logger.warning("No data to write")
        return
    merged = pd.concat(parts, ignore_index=True)
    
    # Group by date AND symbol to avoid mixing contracts
    daily_by_sym = merged.groupby(['date', 'symbol'], as_index=False).agg(
        open=('open','first'), high=('high','max'), low=('low','min'), close=('close','last'), volume=('volume','sum')
    )
    
    # Select highest-volume contract per date
    idx = daily_by_sym.groupby('date')['volume'].idxmax()
    merged = daily_by_sym.loc[idx].drop(columns=['symbol']).sort_values('date')
    
    merged = merged.rename(columns={'open':'mes_open','high':'mes_high','low':'mes_low','close':'mes_close','volume':'mes_volume'})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    merged.to_parquet(OUT, index=False)
    logger.info(f"Saved {len(merged)} rows × {len(merged.columns)} to {OUT}")

if __name__ == '__main__':
    main()
