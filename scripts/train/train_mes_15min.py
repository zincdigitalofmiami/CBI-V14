#!/usr/bin/env python3
"""
Train a 15-minute MES micro-confirmation predictor with time-series splits.

Input:
- TrainingData/exports/mes_15min_training.parquet

Model:
- GradientBoostingRegressor with TimeSeriesSplit (e.g., 5 splits)

Outputs:
- TrainingData/exports/mes_models/mes_15min_gbr.pkl
- TrainingData/exports/mes_15min_predictions.parquet (datetime, y_true, y_pred)
"""

from pathlib import Path
import logging
import pickle
import shutil
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
TEST_MODE = False  # Set to True for test runs (overwrites _test/ folder, no versioning)

DRIVE = Path('/Volumes/Satechi Hub/Projects/CBI-V14')
EXPORTS = DRIVE / 'TrainingData/exports'

# Conditional model path: _test/ for test runs, production otherwise
if TEST_MODE:
    MODELDIR = EXPORTS / '_test/mes_models'
else:
    MODELDIR = EXPORTS / 'mes_models'

def main():
    if TEST_MODE:
        logger.info("🧪 TEST MODE: Outputs to _test/ folder (will overwrite)")
        # Clean test folder if in test mode
        if MODELDIR.exists():
            shutil.rmtree(MODELDIR)
            logger.info(f"🧹 Cleaned test folder: {MODELDIR}")
        MODELDIR.mkdir(parents=True, exist_ok=True)
    else:
        MODELDIR.mkdir(parents=True, exist_ok=True)
    
    data_path = EXPORTS / 'mes_15min_training.parquet'
    if not data_path.exists():
        logger.error(f"Missing dataset: {data_path}")
        return
    df = pd.read_parquet(data_path)
    df = df.sort_values('datetime').reset_index(drop=True)
    y = df['target_mes15_ret_1bar'].values
    X = df.drop(columns=['target_mes15_ret_1bar']).copy()
    # Remove non-numeric columns except datetime (keep for output)
    dt = X['datetime'] if 'datetime' in X.columns else None
    if 'datetime' in X.columns:
        X = X.drop(columns=['datetime'])
    X = X.select_dtypes(include=['number']).fillna(0.0)

    # TimeSeriesSplit
    tscv = TimeSeriesSplit(n_splits=5)
    oof_pred = np.zeros(len(y))
    model = GradientBoostingRegressor(random_state=42)

    for fold, (tr, va) in enumerate(tscv.split(X)):
        Xtr, ytr = X.iloc[tr], y[tr]
        Xva, yva = X.iloc[va], y[va]
        model.fit(Xtr, ytr)
        oof_pred[va] = model.predict(Xva)
        rmse = mean_squared_error(yva, oof_pred[va], squared=False)
        logger.info(f"Fold {fold+1} RMSE: {rmse:.6f}")

    # Refit on full data
    model.fit(X, y)
    with open(MODELDIR / 'mes_15min_gbr.pkl', 'wb') as f:
        pickle.dump(model, f)

    # In-sample predictions for now
    yhat = model.predict(X)
    out = pd.DataFrame({'datetime': dt if dt is not None else df.index, 'y_true': y, 'y_pred': yhat})
    out_path = EXPORTS / 'mes_15min_predictions.parquet'
    out.to_parquet(out_path, index=False)
    logger.info(f"Saved predictions to {out_path} ({len(out)} rows)")

if __name__ == '__main__':
    main()

