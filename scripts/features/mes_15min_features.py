#!/usr/bin/env python3
"""
Compute MES 15-minute micro-confirmation features for trading.

Inputs:
- TrainingData/staging/mes_15min.parquet (datetime, mes_open, mes_high, mes_low, mes_close, mes_volume)

Outputs:
- TrainingData/staging/mes_15min_features.parquet (datetime + mes15_* features)

Features (minimal, no external deps):
- Momentum: RSI(14), MACD(12,26,9)
- Volatility: ATR(14), Bollinger(20,2) width/position
- Trend alignment: 60min/240min SMA distances sampled to 15m grid
- Daily pivots (from prior day OHLC) and distances
"""

from pathlib import Path
import logging
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DRIVE = Path('/Volumes/Satechi Hub/Projects/CBI-V14')
SRC = DRIVE / 'TrainingData/staging/mes_15min.parquet'
OUT = DRIVE / 'TrainingData/staging/mes_15min_features.parquet'

def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period, min_periods=1).mean()
    loss = (-delta.clip(upper=0)).rolling(period, min_periods=1).mean()
    rs = gain / (loss.replace(0, np.nan))
    return 100 - (100 / (1 + rs))

def macd(series: pd.Series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    line = ema_fast - ema_slow
    sig = line.ewm(span=signal, adjust=False).mean()
    hist = line - sig
    return line, sig, hist

def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    hl = df['mes_high'] - df['mes_low']
    hc = (df['mes_high'] - df['mes_close'].shift()).abs()
    lc = (df['mes_low'] - df['mes_close'].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.rolling(period, min_periods=1).mean()

def daily_pivots(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d['date'] = d['datetime'].dt.normalize()  # Use normalize() instead of dt.date for proper datetime
    daily = d.groupby('date').agg(
        high=('mes_high','max'), low=('mes_low','min'), close=('mes_close','last')
    ).shift(1).dropna()
    piv = (daily['high'] + daily['low'] + daily['close']) / 3.0
    r1 = 2*piv - daily['low']; s1 = 2*piv - daily['high']
    r2 = piv + (daily['high'] - daily['low']); s2 = piv - (daily['high'] - daily['low'])
    daily_feat = pd.DataFrame({'pivot':piv,'r1':r1,'s1':s1,'r2':r2,'s2':s2})
    # Index is already datetime from groupby on normalized datetime
    return daily_feat

def trend_ma(df: pd.DataFrame, rule: str) -> pd.Series:
    r = df.set_index('datetime').resample(rule).agg({'mes_close':'last'}).ffill()
    ma = r['mes_close'].rolling(20, min_periods=5).mean()
    # map back to 15m grid
    ma_upsampled = ma.reindex(df.set_index('datetime').index, method='ffill')
    return ma_upsampled.reset_index(drop=True)

def main():
    if not SRC.exists():
        logger.error(f"Missing source: {SRC}")
        return
    df = pd.read_parquet(SRC)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('datetime').reset_index(drop=True)

    # Momentum/volatility
    df['mes15_rsi_14'] = rsi(df['mes_close'], 14)
    macd_line, macd_sig, macd_hist = macd(df['mes_close'])
    df['mes15_macd_line'] = macd_line
    df['mes15_macd_signal'] = macd_sig
    df['mes15_macd_hist'] = macd_hist

    bb_mid = df['mes_close'].rolling(20, min_periods=5).mean()
    bb_std = df['mes_close'].rolling(20, min_periods=5).std()
    df['mes15_bb_upper'] = bb_mid + 2*bb_std
    df['mes15_bb_lower'] = bb_mid - 2*bb_std
    df['mes15_bb_width'] = df['mes15_bb_upper'] - df['mes15_bb_lower']
    df['mes15_bb_pos'] = (df['mes_close'] - df['mes15_bb_lower']) / (df['mes15_bb_width'] + 1e-10)
    df['mes15_atr_14'] = atr(df, 14)

    # Trend alignment (1h and 4h MAs mapped to 15m grid)
    df['mes15_ma_60min'] = trend_ma(df, '60T')
    df['mes15_ma_240min'] = trend_ma(df, '240T')
    df['mes15_dist_ma60'] = (df['mes_close'] - df['mes15_ma_60min']) / (df['mes15_ma_60min'] + 1e-10)
    df['mes15_dist_ma240'] = (df['mes_close'] - df['mes15_ma_240min']) / (df['mes15_ma_240min'] + 1e-10)

    # Daily pivots & distances
    piv = daily_pivots(df)
    dd = df.copy()
    dd['date'] = dd['datetime'].dt.normalize()
    piv = piv.reindex(dd['date']).reset_index(drop=True)
    for col in ['pivot','r1','s1','r2','s2']:
        df[f'mes15_pivot_{col}'] = piv[col].values
        df[f'mes15_dist_{col}'] = (df['mes_close'] - piv[col].values) / (piv[col].values + 1e-10)

    # Save
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df[['datetime'] + [c for c in df.columns if c.startswith('mes15_')]].to_parquet(OUT, index=False)
    logger.info(f"Saved {len(df)} rows × features to {OUT}")

if __name__ == '__main__':
    main()

