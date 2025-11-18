#!/usr/bin/env python3
"""
Train MES models per surface/horizon and ensemble predictions.
Surfaces: daily_only, daily_intra
Horizons: 1w (5d), 1m (20d)

Models: Simple baselines (ElasticNet + GradientBoostingRegressor) to keep deps light.
Ensemble: mean of model predictions.

Outputs:
- TrainingData/exports/mes_models/{surface}_{horizon}_{model}.pkl
- TrainingData/exports/mes_predictions_{horizon}.parquet (date, y_pred_{surface}_{model}, y_pred_ens)
"""

from pathlib import Path
import logging
import pickle
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import ElasticNet
from sklearn.ensemble import GradientBoostingRegressor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DRIVE = Path('/Volumes/Satechi Hub/Projects/CBI-V14')
EXPORTS = DRIVE / 'TrainingData/exports'
MODELS = EXPORTS / 'mes_models'

SURFACES = ['daily_only', 'daily_intra']
HORIZONS = ['1w','1m']

def load_dataset(surface, horizon):
    path = EXPORTS / f'mes_training_{surface}_{horizon}.parquet'
    df = pd.read_parquet(path)
    df = df.sort_values('date')
    return df

def build_features_targets(df: pd.DataFrame):
    y = df['target_mes_ret'].values
    drop_cols = [c for c in ['date','target_mes_ret'] if c in df.columns]
    X = df.drop(columns=drop_cols)
    # Keep only numeric
    X = X.select_dtypes(include=['number']).fillna(0.0)
    return X, y

def train_models(surface, horizon):
    df = load_dataset(surface, horizon)
    X, y = build_features_targets(df)

    # Pipelines
    scaler = ColumnTransformer([('num', StandardScaler(), list(X.columns))], remainder='drop')
    models = {
        'elastic': Pipeline([('scaler', scaler), ('mdl', ElasticNet(alpha=0.001, l1_ratio=0.2, max_iter=2000))]),
        'gbr': Pipeline([('mdl', GradientBoostingRegressor(random_state=42))])
    }

    preds = {}
    for name, pipe in models.items():
        pipe.fit(X, y)
        MODELS.mkdir(parents=True, exist_ok=True)
        with open(MODELS / f'{surface}_{horizon}_{name}.pkl', 'wb') as f:
            pickle.dump(pipe, f)
        preds[name] = pipe.predict(X)
        logger.info(f"Trained {name} on {surface}/{horizon} ({len(y)} rows)")

    # Ensemble (mean)
    ens = sum(preds.values()) / len(preds)
    out_pred = df[['date']].copy()
    for name, p in preds.items():
        out_pred[f'y_pred_{surface}_{name}'] = p
    out_pred[f'y_pred_{surface}_ens'] = ens
    return out_pred

def main():
    all_preds = []
    for h in HORIZONS:
        surf_preds = []
        for s in SURFACES:
            surf_preds.append(train_models(s, h))
        # Merge per-horizon predictions across surfaces on date
        merged = surf_preds[0]
        for p in surf_preds[1:]:
            merged = merged.merge(p, on='date', how='outer')
        # Final simple ensemble across surfaces (mean of y_pred_*_ens where available)
        ens_cols = [c for c in merged.columns if c.endswith('_ens')]
        merged[f'y_pred_ensemble_{h}'] = merged[ens_cols].mean(axis=1)
        out_path = EXPORTS / f'mes_predictions_{h}.parquet'
        merged.to_parquet(out_path, index=False)
        logger.info(f'Saved predictions to {out_path} ({len(merged)} rows)')

if __name__ == '__main__':
    main()

