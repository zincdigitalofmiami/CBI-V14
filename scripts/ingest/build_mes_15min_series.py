#!/usr/bin/env python3
"""
Build a continuous 15-minute OHLCV series for MES from Databento 1-minute files.

Input: TrainingData/raw/databento_mes/**/ohlcv-1m*.json|.parquet (pretty_ts/pretty_px)
Output: TrainingData/staging/mes_15min.parquet with columns:
  datetime, mes_open, mes_high, mes_low, mes_close, mes_volume
"""

from pathlib import Path
import json
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
RAW = DRIVE / "TrainingData/raw/databento_mes"
OUT = DRIVE / "TrainingData/staging/mes_15min.parquet"

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
            records = []
            with open(path, 'r') as f:
                for line in f:
                    line=line.strip()
                    if not line:
                        continue
                    records.append(json.loads(line))
            flat=[]
            for r in records:
                hd=r.get('hd',{})
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
        raise ValueError(f"Unsupported file: {path}")
    tcol = 'ts_event' if 'ts_event' in df.columns else ('timestamp' if 'timestamp' in df.columns else 'time')
    df['datetime'] = pd.to_datetime(df[tcol])
    keep = ['datetime','open','high','low','close','volume','symbol']
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
    files = sorted(list(RAW.glob('**/*ohlcv-1m*.*')))
    if not files:
        logger.error(f"No 1m files found under {RAW}")
        return
    parts = []
    for f in files:
        try:
            df = load_one(f)  # Now includes validated symbol
            parts.append(df)
            logger.info(f"Loaded {f.name}: {len(df)} rows")
        except Exception as e:
            logger.warning(f"Skip {f.name}: {e}")
    if not parts:
        logger.error("No valid files loaded.")
        return
    
    df1 = pd.concat(parts, ignore_index=True)
    
    # Numeric coercion (already done in load_one, but ensure)
    for col in ('open','high','low','close','volume'):
        df1[col] = pd.to_numeric(df1[col], errors='coerce')
    df1 = df1.dropna(subset=['open','high','low','close'])
    
    # Resample per symbol to avoid mixing contracts
    logger.info(f"Resampling {len(df1)} 1m bars across {df1['symbol'].nunique()} symbols to 15min...")
    resampled = []
    for sym, g in df1.groupby('symbol'):
        g = g.set_index('datetime').sort_index()
        r = g.resample('15T').agg({
            'open':'first', 'high':'max', 'low':'min',
            'close':'last', 'volume':'sum'
        })
        r['symbol'] = sym
        resampled.append(r.reset_index())
    
    df_all = pd.concat(resampled, ignore_index=True)
    logger.info(f"Resampled to {len(df_all)} 15min bars")
    
    # CONTRACT CALENDAR: Prevent intraday oscillation during roll weeks
    # Use daily contract selection (highest volume over rolling 7D window)
    df_all['date'] = df_all['datetime'].dt.date
    
    # Compute 7-day rolling volume per symbol
    daily_vol = df_all.groupby(['date','symbol'])['volume'].sum().reset_index()
    daily_vol = daily_vol.sort_values('date')
    
    logger.info("Building contract calendar (7-day rolling volume window)...")
    active_contracts = {}
    for date in sorted(daily_vol['date'].unique()):
        # Look back 7 days (or less if start of data)
        lookback = pd.Timestamp(date) - pd.Timedelta(days=7)
        recent = daily_vol[daily_vol['date'] >= lookback.date()]
        recent = recent[recent['date'] <= date]
        
        # Pick symbol with highest total volume in window
        sym_vol = recent.groupby('symbol')['volume'].sum()
        active_contracts[date] = sym_vol.idxmax() if not sym_vol.empty else None
    
    # Map active contract back to 15m bars
    df_all['active_contract'] = df_all['date'].map(active_contracts)
    df_all = df_all[df_all['symbol'] == df_all['active_contract']]
    logger.info(f"Selected {len(df_all)} 15min bars from active contract chain")
    
    # Final output
    r = df_all.drop(columns=['symbol','date','active_contract']).sort_values('datetime')
    r = r.rename(columns={
        'open':'mes_open', 'high':'mes_high', 'low':'mes_low',
        'close':'mes_close', 'volume':'mes_volume'
    })
    
    OUT.parent.mkdir(parents=True, exist_ok=True)
    r.to_parquet(OUT, index=False)
    logger.info(f"Saved {len(r)} rows × {len(r.columns)} to {OUT}")

if __name__ == '__main__':
    main()
