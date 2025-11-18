#!/usr/bin/env python3
"""
Add MES correlation confirmation features vs VIX, USD broad index, and 10Y yield.

Inputs (staging):
- /TrainingData/staging/mes_futures_daily.parquet   (mes_open/mes_high/mes_low/mes_close/mes_volume)
- /TrainingData/staging/fred_macro_expanded.parquet (fred_vix, fred_usd_broad_index, fred_treasury_10y, ...)

Output (staging):
- /TrainingData/staging/mes_confirmation_features.parquet
  Columns prefixed mes_corr_* (except date)

Method:
- Compute daily pct returns for MES close and drivers (VIX, USD, 10Y), then rolling correlations
  over 30D and 90D windows. Using returns mitigates spurious correlation vs levels.

Naming:
- mes_corr_vix_ret_30d, mes_corr_vix_ret_90d
- mes_corr_usd_ret_30d, mes_corr_usd_ret_90d
- mes_corr_t10y_ret_30d, mes_corr_t10y_ret_90d
"""

from pathlib import Path
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/staging")

def main():
    mes_path = DRIVE / 'mes_futures_daily.parquet'
    fred_path = DRIVE / 'fred_macro_expanded.parquet'
    out_path = DRIVE / 'mes_confirmation_features.parquet'

    if not mes_path.exists():
        logger.error(f"Missing MES daily file: {mes_path}")
        return
    if not fred_path.exists():
        logger.error(f"Missing FRED macro file: {fred_path}")
        return

    mes = pd.read_parquet(mes_path)
    fred = pd.read_parquet(fred_path)

    # Ensure date
    for df in (mes, fred):
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])

    # Select required columns from FRED
    cols = ['date', 'fred_vix', 'fred_usd_broad_index', 'fred_treasury_10y',
            'fred_yield_spread_10y2y', 'fred_yield_spread_10y3m', 'fred_treasury_2y', 'fred_treasury_3mo']
    fred_sel = fred[[c for c in cols if c in fred.columns]].copy()

    # Merge
    df = mes[['date', 'mes_close']].merge(fred_sel, on='date', how='left').sort_values('date')

    # Returns (pct change)
    df['mes_ret'] = df['mes_close'].pct_change()
    if 'fred_vix' in df.columns:
        df['vix_ret'] = df['fred_vix'].pct_change()
    if 'fred_usd_broad_index' in df.columns:
        df['usd_ret'] = df['fred_usd_broad_index'].pct_change()
    if 'fred_treasury_10y' in df.columns:
        df['t10y_ret'] = df['fred_treasury_10y'].pct_change()
    if 'fred_treasury_2y' in df.columns:
        df['t2y_ret'] = df['fred_treasury_2y'].pct_change()
    if 'fred_treasury_3mo' in df.columns:
        df['t3m_ret'] = df['fred_treasury_3mo'].pct_change()
    if 'fred_yield_spread_10y2y' in df.columns:
        df['yc2_ret'] = df['fred_yield_spread_10y2y'].pct_change()
    if 'fred_yield_spread_10y3m' in df.columns:
        df['yc3m_ret'] = df['fred_yield_spread_10y3m'].pct_change()

    # Rolling correlations
    for win in (30, 90):
        if 'vix_ret' in df.columns:
            df[f'mes_corr_vix_ret_{win}d'] = df['mes_ret'].rolling(win, min_periods=win//2).corr(df['vix_ret'])
        if 'usd_ret' in df.columns:
            df[f'mes_corr_usd_ret_{win}d'] = df['mes_ret'].rolling(win, min_periods=win//2).corr(df['usd_ret'])
        if 't10y_ret' in df.columns:
            df[f'mes_corr_t10y_ret_{win}d'] = df['mes_ret'].rolling(win, min_periods=win//2).corr(df['t10y_ret'])
        if 't2y_ret' in df.columns:
            df[f'mes_corr_t2y_ret_{win}d'] = df['mes_ret'].rolling(win, min_periods=win//2).corr(df['t2y_ret'])
        if 't3m_ret' in df.columns:
            df[f'mes_corr_t3m_ret_{win}d'] = df['mes_ret'].rolling(win, min_periods=win//2).corr(df['t3m_ret'])
        if 'yc2_ret' in df.columns:
            df[f'mes_corr_yield_spread_10y2y_ret_{win}d'] = df['mes_ret'].rolling(win, min_periods=win//2).corr(df['yc2_ret'])
        if 'yc3m_ret' in df.columns:
            df[f'mes_corr_yield_spread_10y3m_ret_{win}d'] = df['mes_ret'].rolling(win, min_periods=win//2).corr(df['yc3m_ret'])

    # Output only correlation features + date
    out_cols = [c for c in df.columns if c.startswith('mes_corr_')] + ['date']
    out = df[out_cols].copy()
    out = out.sort_values('date').reset_index(drop=True)

    out.to_parquet(out_path, index=False)
    logger.info(f"Saved {len(out)} rows × {len(out.columns)} to {out_path}")

if __name__ == '__main__':
    main()
