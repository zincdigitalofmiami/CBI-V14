#!/usr/bin/env python3
"""
Build MES training datasets for two surfaces and multiple horizons.

Surfaces:
- daily_only: 2000→present (uses daily features only)
- daily_intra: >=2010-06-06 (adds intraday overlays and confirmation features)

Inputs (staging expected):
- mes_futures_daily.parquet
- mes_daily_aggregated.parquet (optional for daily_intra)
- mes_confirmation_features.parquet (optional for daily_intra)
- fred_macro_expanded.parquet (drivers: fred_vix, fred_usd_broad_index, fred_treasury_10y)

Outputs (exports):
- TrainingData/exports/mes_training_{surface}_{horizon}.parquet

Targets:
- For horizon '1w' => 5 trading days ahead pct return of mes_close
- For horizon '1m' => 20 trading days ahead pct return
"""

from pathlib import Path
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DRIVE = Path('/Volumes/Satechi Hub/Projects/CBI-V14')
STAGING = DRIVE / 'TrainingData/staging'
EXPORTS = DRIVE / 'TrainingData/exports'

HORIZONS = {
    '1w': 5,
    '1m': 20
}

def load_base():
    mes = pd.read_parquet(STAGING / 'mes_futures_daily.parquet')
    fred = pd.read_parquet(STAGING / 'fred_macro_expanded.parquet')
    for df in (mes, fred):
        df['date'] = pd.to_datetime(df['date'])
    base = mes.merge(fred[['date','fred_vix','fred_usd_broad_index','fred_treasury_10y']], on='date', how='left')
    base = base.sort_values('date').reset_index(drop=True)
    return base

def add_intra(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    # MES intraday microstructure
    path = STAGING / 'mes_daily_aggregated.parquet'
    if path.exists():
        micro = pd.read_parquet(path)
        micro['date'] = pd.to_datetime(micro['date'])
        out = out.merge(micro, on='date', how='left')
    # Confirmation features
    cpath = STAGING / 'mes_confirmation_features.parquet'
    if cpath.exists():
        conf = pd.read_parquet(cpath)
        conf['date'] = pd.to_datetime(conf['date'])
        out = out.merge(conf, on='date', how='left')
    return out

def add_targets(df: pd.DataFrame, horizon_days: int) -> pd.DataFrame:
    df = df.sort_values('date').reset_index(drop=True)
    df['target_mes_ret'] = df['mes_close'].pct_change(periods=horizon_days).shift(-horizon_days)
    return df

def build_surface(surface: str):
    base = load_base()
    if surface == 'daily_only':
        df = base
    elif surface == 'daily_intra':
        df = add_intra(base)
        # Filter to dates where intraday overlays mostly exist (>=2010-06-06)
        df = df[df['date'] >= '2010-06-06']
    else:
        raise ValueError('unknown surface')

    # Feature cleanup: forward‑fill macro drivers
    for col in ['fred_vix','fred_usd_broad_index','fred_treasury_10y']:
        if col in df.columns:
            df[col] = df[col].ffill()

    # Build per horizon
    EXPORTS.mkdir(parents=True, exist_ok=True)
    for h, days in HORIZONS.items():
        d = add_targets(df.copy(), days)
        # Drop rows with NaN target
        d = d.dropna(subset=['target_mes_ret'])
        out_path = EXPORTS / f'mes_training_{surface}_{h}.parquet'
        d.to_parquet(out_path, index=False)
        logger.info(f'Saved {len(d)} rows × {len(d.columns)} to {out_path}')

def main():
    build_surface('daily_only')
    build_surface('daily_intra')

if __name__ == '__main__':
    main()

