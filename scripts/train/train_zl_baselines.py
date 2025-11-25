#!/usr/bin/env python3
"""
Train ZL Baselines with Walk-Forward Validation
================================================
Trains LightGBM baseline models for all ZL horizons using:
- Walk-forward validation (time series proper)
- Sample weights from training_weight column
- Proper train/validation splits

Horizons: 1w, 1m, 3m, 6m, 12m (price level targets)

Author: CBI-V14 System
Date: November 25, 2025
"""

import logging
import json
import joblib
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import lightgbm as lgb

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData")
EXPORTS = DRIVE / "exports"
MODELS = DRIVE / "models/zl_baselines"

# Horizons
HORIZONS = ['1w', '1m', '3m', '6m', '12m']

# Columns to exclude from features
EXCLUDE_COLS = [
    'date', 'symbol', 'symbol_x', 'symbol_y', 'regime', 'training_weight', 
    'horizon', 'horizon_days', 'as_of_date', 'price_col_used',
    'target_zl_1w', 'target_zl_1m', 'target_zl_3m', 'target_zl_6m', 'target_zl_12m'
]

# String columns to exclude (LightGBM can't handle object dtype)
STRING_COLS_TO_EXCLUDE = [
    'weather_us_illinois_region', 'weather_us_iowa_region', 'weather_us_indiana_region',
    'weather_us_nebraska_region', 'weather_us_ohio_region', 'vol_regime'
]

# LightGBM baseline parameters (conservative for first run)
LGB_PARAMS = {
    'objective': 'regression',
    'metric': ['mae', 'rmse'],
    'boosting_type': 'gbdt',
    'num_leaves': 31,
    'learning_rate': 0.05,
    'feature_fraction': 0.8,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'verbose': -1,
    'seed': 42,
    'n_jobs': -1,
}


def load_training_data(horizon: str) -> pd.DataFrame:
    """Load training export for given horizon."""
    path = EXPORTS / f"zl_training_prod_allhistory_{horizon}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Training export not found: {path}")
    
    df = pd.read_parquet(path)
    df['date'] = pd.to_datetime(df['date'])
    logger.info(f"Loaded {horizon}: {len(df):,} rows × {len(df.columns)} columns")
    return df


def get_feature_columns(df: pd.DataFrame) -> list:
    """Get list of feature columns (exclude targets, metadata, string cols, etc)."""
    feature_cols = [c for c in df.columns if c not in EXCLUDE_COLS 
                    and c not in STRING_COLS_TO_EXCLUDE
                    and not c.startswith('target_')]
    
    # Also exclude any remaining object dtype columns
    numeric_cols = []
    for col in feature_cols:
        if df[col].dtype in ['float64', 'float32', 'int64', 'int32', 'bool']:
            numeric_cols.append(col)
    
    return numeric_cols


def calculate_metrics(y_true, y_pred) -> dict:
    """Calculate regression metrics."""
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    
    return {
        'mae': round(mae, 4),
        'rmse': round(rmse, 4),
        'r2': round(r2, 4),
        'mape': round(mape, 2)
    }


def walk_forward_split(df: pd.DataFrame, train_pct: float = 0.8):
    """
    Walk-forward split: train on first train_pct, validate on remainder.
    For time series, we NEVER shuffle - maintain temporal order.
    """
    df = df.sort_values('date').reset_index(drop=True)
    split_idx = int(len(df) * train_pct)
    
    train_df = df.iloc[:split_idx].copy()
    val_df = df.iloc[split_idx:].copy()
    
    return train_df, val_df


def train_horizon(horizon: str) -> dict:
    """Train baseline model for a single horizon."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Training ZL Baseline: {horizon}")
    logger.info(f"{'='*60}")
    
    # Load data
    df = load_training_data(horizon)
    target_col = f'target_zl_{horizon}'
    
    # Drop rows with null target
    df = df.dropna(subset=[target_col])
    
    # Walk-forward split
    train_df, val_df = walk_forward_split(df, train_pct=0.8)
    logger.info(f"Train: {len(train_df):,} rows ({train_df['date'].min()} to {train_df['date'].max()})")
    logger.info(f"Val:   {len(val_df):,} rows ({val_df['date'].min()} to {val_df['date'].max()})")
    
    # Get feature columns
    feature_cols = get_feature_columns(df)
    logger.info(f"Features: {len(feature_cols)}")
    
    # Prepare data
    X_train = train_df[feature_cols].fillna(0)
    y_train = train_df[target_col]
    w_train = train_df['training_weight'] if 'training_weight' in train_df.columns else None
    
    X_val = val_df[feature_cols].fillna(0)
    y_val = val_df[target_col]
    
    # Create LightGBM datasets
    train_data = lgb.Dataset(X_train, label=y_train, weight=w_train)
    val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
    
    # Train model
    logger.info("Training LightGBM...")
    model = lgb.train(
        LGB_PARAMS,
        train_data,
        num_boost_round=500,
        valid_sets=[train_data, val_data],
        valid_names=['train', 'val'],
        callbacks=[
            lgb.early_stopping(50, verbose=False),
            lgb.log_evaluation(100)
        ]
    )
    
    # Predictions
    y_pred_train = model.predict(X_train)
    y_pred_val = model.predict(X_val)
    
    # Metrics
    train_metrics = calculate_metrics(y_train, y_pred_train)
    val_metrics = calculate_metrics(y_val, y_pred_val)
    
    logger.info(f"\nTrain: MAE={train_metrics['mae']}, MAPE={train_metrics['mape']}%, R²={train_metrics['r2']}")
    logger.info(f"Val:   MAE={val_metrics['mae']}, MAPE={val_metrics['mape']}%, R²={val_metrics['r2']}")
    
    # Feature importance
    importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importance(importance_type='gain')
    }).sort_values('importance', ascending=False)
    
    top_10 = importance.head(10)['feature'].tolist()
    logger.info(f"\nTop 10 features: {top_10}")
    
    # Save model
    MODELS.mkdir(parents=True, exist_ok=True)
    model_path = MODELS / f"lgb_zl_{horizon}_baseline.pkl"
    joblib.dump(model, model_path)
    logger.info(f"✅ Saved model to: {model_path}")
    
    # Save metadata
    metadata = {
        'horizon': horizon,
        'target_col': target_col,
        'features_count': len(feature_cols),
        'train_rows': len(train_df),
        'val_rows': len(val_df),
        'train_date_min': str(train_df['date'].min().date()),
        'train_date_max': str(train_df['date'].max().date()),
        'val_date_min': str(val_df['date'].min().date()),
        'val_date_max': str(val_df['date'].max().date()),
        'train_metrics': train_metrics,
        'val_metrics': val_metrics,
        'best_iteration': model.best_iteration,
        'top_features': importance.head(20).to_dict('records'),
        'created_at': datetime.now().isoformat(),
        'lgb_params': LGB_PARAMS
    }
    
    metadata_path = MODELS / f"lgb_zl_{horizon}_baseline_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return {
        'horizon': horizon,
        'train_metrics': train_metrics,
        'val_metrics': val_metrics,
        'best_iteration': model.best_iteration,
        'model_path': str(model_path)
    }


def main():
    """Train all ZL baselines."""
    logger.info("="*60)
    logger.info("ZL Baseline Training - All Horizons")
    logger.info("="*60)
    
    # Ensure output directory exists
    MODELS.mkdir(parents=True, exist_ok=True)
    
    all_results = []
    
    for horizon in HORIZONS:
        try:
            result = train_horizon(horizon)
            all_results.append(result)
        except Exception as e:
            logger.error(f"Error training {horizon}: {e}")
            continue
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("TRAINING SUMMARY")
    logger.info("="*60)
    
    summary_data = []
    for r in all_results:
        summary_data.append({
            'Horizon': r['horizon'],
            'Val MAE': r['val_metrics']['mae'],
            'Val MAPE': f"{r['val_metrics']['mape']}%",
            'Val R²': r['val_metrics']['r2'],
            'Iterations': r['best_iteration']
        })
    
    summary_df = pd.DataFrame(summary_data)
    print("\n" + summary_df.to_string(index=False))
    
    # Save summary
    summary_path = MODELS / "training_summary.json"
    with open(summary_path, 'w') as f:
        json.dump({
            'created_at': datetime.now().isoformat(),
            'horizons': all_results
        }, f, indent=2)
    
    logger.info(f"\n✅ All models trained and saved to: {MODELS}")
    
    return all_results


if __name__ == "__main__":
    main()

