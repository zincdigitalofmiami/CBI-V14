#!/usr/bin/env python3
"""
Aggregate ZL intraday data to daily OHLCV and microstructure features.
Reads Databento JSON/Parquet from TrainingData/raw/databento_zl and writes
TrainingData/staging/zl_daily_aggregated.parquet with zl_ prefix.
"""

import json
import re
from pathlib import Path
import logging
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

EXTERNAL_DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
RAW_DIR = EXTERNAL_DRIVE / "TrainingData/raw/databento_zl"
STAGING_DIR = EXTERNAL_DRIVE / "TrainingData/staging"

DESIRED_TIMEFRAMES = ['1min', '5min', '15min', '30min', '60min', '240min']

def _detect_timeframe_from_name(name: str) -> str:
    m = re.search(r"ohlcv-(\d+[smhd])", name)
    if m:
        tf = m.group(1)
        if tf == '1h':
            return '60min'
        if tf.endswith('m') and tf != '1m':
            return tf.replace('m','min')
        if tf == '1m':
            return '1min'
        return tf
    for tf in DESIRED_TIMEFRAMES:
        if tf in name:
            return tf
    return 'unknown'

def _load_one_file(path: Path) -> pd.DataFrame:
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
            df = pd.DataFrame(flat)
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
        raise ValueError(f"Unsupported file type: {path}")
    # datetime
    if 'datetime' not in df.columns:
        for col in ('ts_event', 'timestamp', 'time'):
            if col in df.columns:
                df['datetime'] = pd.to_datetime(df[col])
                break
    if 'datetime' not in df.columns and isinstance(df.index, pd.DatetimeIndex):
        df = df.reset_index().rename(columns={'index': 'datetime'})
    # ensure cols
    for col in ('open', 'high', 'low', 'close', 'volume'):
        if col not in df.columns:
            raise ValueError(f"Missing column {col} in {path}")
    
    # STRICT symbol validation - FAIL FAST if missing
    if 'symbol' not in df.columns:
        raise ValueError(f"Missing symbol column in {path} - fix data source")
    
    # Enforce outright-only ZL contracts
    df = df[df['symbol'].str.match(r'^ZL[A-Z]\d+$', na=False)]
    if df.empty:
        raise ValueError(f"No valid ZL outright contracts in {path} after filtering")
    
    # Numeric coercion
    for col in ('open', 'high', 'low', 'close', 'volume'):
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['open', 'high', 'low', 'close'])
    
    if df.empty:
        raise ValueError(f"No valid numeric OHLCV data in {path}")
    
    return df[['datetime','open','high','low','close','volume','symbol']]

def load_intraday_files() -> pd.DataFrame:
    files = sorted(list(RAW_DIR.glob('**/*ohlcv*.*')))
    if not files:
        logger.warning(f"No intraday files in {RAW_DIR}")
        return pd.DataFrame()
    parts = []
    for f in files:
        try:
            tf = _detect_timeframe_from_name(f.name)
            if tf not in DESIRED_TIMEFRAMES:
                continue
            df = _load_one_file(f)
            df['timeframe'] = tf
            parts.append(df[['datetime','open','high','low','close','volume','symbol','timeframe']])
            logger.info(f"Loaded {f.name}: {len(df)} rows ({tf})")
        except Exception as e:
            logger.warning(f"Skip {f.name}: {e}")
    if not parts:
        return pd.DataFrame()
    combined = pd.concat(parts, ignore_index=True)

    # Resample from 1min to 5/15/30/60/240 where needed (per symbol to avoid mixing contracts)
    if '1min' in combined['timeframe'].unique():
        df1 = combined[combined['timeframe'] == '1min'].copy()
        df1['datetime'] = pd.to_datetime(df1['datetime'])
        rules = {'5min':'5T','15min':'15T','30min':'30T','60min':'60T','240min':'240T'}
        for tf, rule in rules.items():
            try:
                resampled_parts = []
                for sym, g in df1.groupby('symbol'):
                    g = g.set_index('datetime').sort_index()
                    r = g.resample(rule).agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'})
                    r = r.dropna(subset=['open','high','low','close'])
                    if not r.empty:
                        r = r.reset_index().rename(columns={'index':'datetime'})
                        r['symbol'] = sym
                        r['timeframe'] = tf
                        resampled_parts.append(r)
                if resampled_parts:
                    r_all = pd.concat(resampled_parts, ignore_index=True)
                    combined = pd.concat([combined, r_all[['datetime','open','high','low','close','volume','symbol','timeframe']]], ignore_index=True)
                    logger.info(f"Resampled 1min -> {tf}: {len(r_all)} rows")
            except Exception as e:
                logger.warning(f"Resample to {tf} failed: {e}")
    return combined

def aggregate_to_daily(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['date'] = pd.to_datetime(df['datetime']).dt.date
    df['date'] = pd.to_datetime(df['date'])
    
    # Group by date AND symbol first to avoid mixing contracts
    df_with_sym = df.groupby(['date', 'symbol']).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).reset_index()
    
    # Select highest-volume contract per date
    idx = df_with_sym.groupby('date')['volume'].idxmax()
    daily = df_with_sym.loc[idx].drop(columns=['symbol'])
    
    daily = daily.rename(columns={'open':'zl_open','high':'zl_high','low':'zl_low','close':'zl_close','volume':'zl_volume'})
    daily['zl_daily_range'] = daily['zl_high'] - daily['zl_low']
    daily['zl_daily_return'] = daily['zl_close'] - daily['zl_open']
    daily['zl_daily_range_pct'] = daily['zl_daily_range'] / daily['zl_open'] * 100.0
    daily['zl_daily_return_pct'] = daily['zl_daily_return'] / daily['zl_open'] * 100.0
    return daily

def microstructure_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['date'] = df['datetime'].dt.date
    df['date'] = pd.to_datetime(df['date'])
    feats = []
    for (date, tf), g in df.groupby(['date','timeframe']):
        if len(g) < 2:
            continue
        ret = g['close'].pct_change()
        realized_vol = ret.std()
        hl_vol = ((g['high']/g['low']).apply(np.log)**2).mean()**0.5
        vwap = (g['close']*g['volume']).sum() / max(g['volume'].sum(),1)
        feats.append({'date':date,'timeframe':tf,'realized_vol':realized_vol,'hl_vol':hl_vol,'vwap':vwap,'num_bars':len(g)})
    if not feats:
        return pd.DataFrame()
    fdf = pd.DataFrame(feats)
    piv = fdf.pivot(index='date', columns='timeframe')
    piv.columns = [f"zl_{c[1]}_{c[0]}" for c in piv.columns]
    return piv.reset_index()

def main():
    logger.info("ZL INTRADAY AGGREGATION")
    df = load_intraday_files()
    if df.empty:
        logger.warning("No ZL intraday data found.")
        return
    daily = aggregate_to_daily(df)
    micro = microstructure_features(df)
    out = daily if micro.empty else daily.merge(micro, on='date', how='left')
    out_path = STAGING_DIR / 'zl_daily_aggregated.parquet'
    out.to_parquet(out_path, index=False)
    logger.info(f"Saved {len(out)} rows × {len(out.columns)} to {out_path}")

if __name__ == '__main__':
    main()
