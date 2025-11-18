#!/usr/bin/env python3
"""
Aggregate MES intraday data to daily OHLCV and microstructure features.
Handles multiple timeframes and creates daily features.
Strictly no proxies.

Inputs (raw):
- Databento downloads placed under:
  /Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/databento_mes/
  Files can be Parquet (.parquet) or Databento JSON (.json) with pretty_ts/pretty_px.

Outputs (staging):
- /Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/staging/mes_daily_aggregated.parquet
  Columns prefixed with mes_ (except date)
"""

import json
import re
from pathlib import Path
from datetime import datetime
import logging
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

EXTERNAL_DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
RAW_DIR = EXTERNAL_DRIVE / "TrainingData/raw/databento_mes"
STAGING_DIR = EXTERNAL_DRIVE / "TrainingData/staging"

# We will include typical timeframes used for features; detection is dynamic from filenames
DESIRED_TIMEFRAMES = ['1min', '5min', '15min', '30min', '60min', '240min']

def _detect_timeframe_from_name(name: str) -> str:
    m = re.search(r"ohlcv-(\d+[smhd])", name)
    if m:
        tf = m.group(1)
        if tf == '1h':
            return '60min'
        if tf == '4h':
            return '240min'
        if tf.endswith('m') and tf != '1m':
            # convert like 5m -> 5min
            return tf.replace('m','min')
        if tf == '1m':
            return '1min'
        return tf
    # fallback on tokens
    for tf in DESIRED_TIMEFRAMES:
        if tf in name:
            return tf
    return 'unknown'

def _load_one_file(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == '.parquet':
        df = pd.read_parquet(path)
        # try common column mappings
        if 'datetime' not in df.columns:
            for col in ('timestamp', 'time', 'ts_event'):
                if col in df.columns:
                    df['datetime'] = pd.to_datetime(df[col])
                    break
        if 'datetime' not in df.columns:
            # best effort from index
            if isinstance(df.index, pd.DatetimeIndex):
                df = df.reset_index().rename(columns={'index': 'datetime'})
            else:
                raise ValueError(f"No datetime column in {path}")
        return df
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
        # Expect pretty_ts/pretty_px => ts_event ISO string and numeric ohlcv
        time_col = 'ts_event' if 'ts_event' in df.columns else ('time' if 'time' in df.columns else 'timestamp')
        df['datetime'] = pd.to_datetime(df[time_col])
        # ensure required columns exist
        for col in ('open', 'high', 'low', 'close', 'volume'):
            if col not in df.columns:
                raise ValueError(f"Missing column {col} in {path}")
        
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
        
        return df
    else:
        raise ValueError(f"Unsupported file type: {path}")

def load_intraday_files() -> pd.DataFrame:
    if not RAW_DIR.exists():
        logger.warning(f"Raw directory not found: {RAW_DIR}")
        return pd.DataFrame()

    files = sorted(list(RAW_DIR.glob("**/*ohlcv*.*")))
    if not files:
        logger.warning(f"No intraday files found under {RAW_DIR}")
        return pd.DataFrame()

    all_dfs = []
    for f in files:
        try:
            timeframe = _detect_timeframe_from_name(f.name)
            if timeframe not in DESIRED_TIMEFRAMES:
                logger.info(f"Skipping {f.name} (timeframe {timeframe})")
                continue
            df = _load_one_file(f)
            df['timeframe'] = timeframe
            all_dfs.append(df[['datetime', 'open', 'high', 'low', 'close', 'volume', 'symbol', 'timeframe']])
            logger.info(f"Loaded {f.name}: {len(df)} rows ({timeframe})")
        except Exception as e:
            logger.warning(f"Failed to load {f.name}: {e}")

    if not all_dfs:
        return pd.DataFrame()
    combined = pd.concat(all_dfs, ignore_index=True)

    # Resample from 1min to 5/15/30/60min if needed (per symbol to avoid mixing contracts)
    if '1min' in combined['timeframe'].unique():
        df1 = combined[combined['timeframe'] == '1min'].copy()
        df1['datetime'] = pd.to_datetime(df1['datetime'])
        rules = {'5min':'5T', '15min':'15T', '30min':'30T', '60min':'60T', '240min':'240T'}
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
    
    if not daily.empty:
        daily['mes_daily_range'] = daily['high'] - daily['low']
        daily['mes_daily_range_pct'] = daily['mes_daily_range'] / daily['open'] * 100.0
        daily['mes_daily_return'] = daily['close'] - daily['open']
        daily['mes_daily_return_pct'] = daily['mes_daily_return'] / daily['open'] * 100.0
        daily = daily.rename(columns={
            'open': 'mes_open', 'high': 'mes_high', 'low': 'mes_low',
            'close': 'mes_close', 'volume': 'mes_volume'
        })
    return daily

def microstructure_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['date'] = df['datetime'].dt.date
    df['date'] = pd.to_datetime(df['date'])
    feats = []
    for (date, timeframe), g in df.groupby(['date', 'timeframe']):
        if len(g) < 2:
            continue
        ret = g['close'].pct_change()
        realized_vol = ret.std()
        hl_vol = ((g['high'] / g['low']).apply(np.log) ** 2).mean() ** 0.5
        vwap = (g['close'] * g['volume']).sum() / max(g['volume'].sum(), 1)
        feats.append({'date': date, 'timeframe': timeframe, 'realized_vol': realized_vol, 'hl_vol': hl_vol, 'vwap': vwap, 'num_bars': len(g)})
    if not feats:
        return pd.DataFrame()
    fdf = pd.DataFrame(feats)
    piv = fdf.pivot(index='date', columns='timeframe')
    piv.columns = [f"mes_{c[1]}_{c[0]}" for c in piv.columns]
    return piv.reset_index()

def main():
    logger.info("MES INTRADAY AGGREGATION")
    df = load_intraday_files()
    if df.empty:
        logger.warning("No MES intraday data found.")
        return
    daily = aggregate_to_daily(df)
    micro = microstructure_features(df)
    out = daily if micro.empty else daily.merge(micro, on='date', how='left')
    out_path = STAGING_DIR / "mes_daily_aggregated.parquet"
    out.to_parquet(out_path, index=False)
    logger.info(f"Saved {len(out)} rows × {len(out.columns)} cols to {out_path}")

if __name__ == "__main__":
    main()
