#!/usr/bin/env python3
"""
Build MES 15-minute training dataset for micro confirmations.

Inputs:
- TrainingData/staging/mes_15min.parquet
- TrainingData/staging/mes_15min_features.parquet

Target:
- Next 1 bar (15m) return of mes_close (y+1)

Output:
- TrainingData/exports/mes_15min_training.parquet
"""

from pathlib import Path
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DRIVE = Path('/Volumes/Satechi Hub/Projects/CBI-V14')
STAGING = DRIVE / 'TrainingData/staging'
EXPORTS = DRIVE / 'TrainingData/exports'

def main():
    price = pd.read_parquet(STAGING / 'mes_15min.parquet')
    feat = pd.read_parquet(STAGING / 'mes_15min_features.parquet')
    price['datetime'] = pd.to_datetime(price['datetime'])
    feat['datetime'] = pd.to_datetime(feat['datetime'])
    df = price.merge(feat, on='datetime', how='left').sort_values('datetime').reset_index(drop=True)
    df['target_mes15_ret_1bar'] = df['mes_close'].pct_change().shift(-1)
    df = df.dropna(subset=['target_mes15_ret_1bar'])
    out = EXPORTS / 'mes_15min_training.parquet'
    EXPORTS.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    logger.info(f"Saved {len(df)} rows × {len(df.columns)} cols to {out}")

if __name__ == '__main__':
    main()

