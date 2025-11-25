#!/usr/bin/env python3
"""
Tree-Based Baselines - LightGBM DART, XGBoost DART
Day 2, Track B: Train tree models for all 5 horizons
M4 16GB Optimized: CPU-friendly, 8-10 threads
Enhanced with M4 configs and evaluation pipeline
"""
import os
import sys
import argparse
import polars as pl
import mlflow
import numpy as np
from datetime import datetime
from pathlib import Path
import lightgbm as lgb
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit

# Add src to path for imports
# Correctly navigate up from src/training/baselines to the project root
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from training.config.m4_config import (
    LIGHTGBM_CONFIG, XGBOOST_CONFIG, get_config_for_model, EVALUATION_THRESHOLDS
)
from training.evaluation.metrics import (
    comprehensive_evaluation, print_evaluation_summary, calculate_sharpe
)

# Environment setup
EXTERNAL_DRIVE = os.getenv("EXTERNAL_DRIVE", "/Volumes/Satechi Hub")
CBI_V14_REPO = os.getenv("CBI_V14_REPO", f"{EXTERNAL_DRIVE}/Projects/CBI-V14")
TRAINING_DATA = f"{CBI_V14_REPO}/TrainingData"
MLFLOW_DIR = f"{CBI_V14_REPO}/Models/mlflow"

# MLflow setup
mlflow.set_tracking_uri(f"file://{MLFLOW_DIR}")
mlflow.set_experiment("baselines_tree")

def load_training_data(horizon, surface="prod"):
    """Load cached training data (new naming convention)"""
    data_path = f"{TRAINING_DATA}/exports/zl_training_{surface}_allhistory_{horizon}.parquet"
    
    print(f"Loading data: {data_path}")
    df = pl.read_parquet(data_path)
    
    print(f"✅ Loaded {len(df)} rows × {len(df.columns)} columns")
    return df

def prepare_features(df, target_col):
    """Prepare features for tree models with walk-forward validation"""
    # Exclude target and date columns
    exclude_cols = ['date', target_col] + [col for col in df.columns if col.startswith('target_')]
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Sort by date for walk-forward split
    if 'date' in df.columns:
        df_sorted = df.sort('date')
    else:
        df_sorted = df
    
    # Walk-forward split: last 20% for validation
    split_idx = int(len(df_sorted) * 0.8)
    df_train = df_sorted[:split_idx]
    df_val = df_sorted[split_idx:]
    
    # Convert to numpy
    X_train = df_train.select(feature_cols).to_numpy()
    X_val = df_val.select(feature_cols).to_numpy()
    y_train = df_train[target_col].to_numpy()
    y_val = df_val[target_col].to_numpy()
    
    return X_train, X_val, y_train, y_val, feature_cols, df_val

def train_lightgbm_dart(X_train, X_val, y_train, y_val, horizon, models_dir, df_val=None):
    """Train LightGBM DART model with M4-optimized config"""
    print(f"\n{'='*60}")
    print(f"Training LightGBM DART for {horizon}")
    print(f"{'='*60}")
    
    with mlflow.start_run(run_name=f"lgbm_dart_{horizon}"):
        # Get M4-optimized config
        config = get_config_for_model('lightgbm', horizon)
        
        # Log parameters
        for k, v in config.items():
            mlflow.log_param(k, v)
        mlflow.log_param("model_type", "LightGBM_DART")
        mlflow.log_param("horizon", horizon)
        
        # Train
        model = lgb.LGBMRegressor(**config)
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            callbacks=[lgb.early_stopping(stopping_rounds=100, verbose=False)]
        )
        
        # Predictions
        train_pred = model.predict(X_train)
        val_pred = model.predict(X_val)
        
        # Basic metrics
        train_mape = np.mean(np.abs((y_train - train_pred) / y_train)) * 100
        val_mape = np.mean(np.abs((y_val - val_pred) / y_val)) * 100
        
        mlflow.log_metric("train_mape", train_mape)
        mlflow.log_metric("val_mape", val_mape)
        mlflow.log_metric("n_estimators_used", model.n_estimators_)
        
        # Comprehensive evaluation if validation dataframe provided
        if df_val is not None:
            try:
                # Add predictions to validation dataframe
                df_eval = df_val.with_columns([
                    pl.Series("y_pred", val_pred),
                    pl.Series("y_true", y_val)
                ])
                
                eval_results = comprehensive_evaluation(
                    df_eval,
                    y_true_col="y_true",
                    y_pred_col="y_pred",
                    horizon=horizon
                )
                
                # Log regime-specific metrics
                if 'by_regime' in eval_results:
                    for regime, metrics in eval_results['by_regime'].items():
                        mlflow.log_metric(f"mape_{regime}", metrics.get('mape', np.nan))
                        if 'sharpe' in metrics:
                            mlflow.log_metric(f"sharpe_{regime}", metrics['sharpe'])
                
                # Check against thresholds
                target_mape = EVALUATION_THRESHOLDS['mape_max'].get(horizon, 10.0)
                if val_mape <= target_mape:
                    mlflow.log_param("meets_mape_threshold", True)
                else:
                    mlflow.log_param("meets_mape_threshold", False)
                    print(f"   ⚠️  MAPE {val_mape:.2f}% exceeds threshold {target_mape:.2f}%")
            except Exception as e:
                print(f"   ⚠️  Comprehensive evaluation failed: {e}")
        
        # Save model
        os.makedirs(models_dir, exist_ok=True)
        model_subdir = f"{models_dir}/lightgbm_dart"
        os.makedirs(model_subdir, exist_ok=True)
        model_path = f"{model_subdir}/model.bin"
        model.booster_.save_model(model_path)
        mlflow.log_artifact(model_path)
        
        print(f"✅ LightGBM DART {horizon}: Train MAPE={train_mape:.2f}%, Val MAPE={val_mape:.2f}%")
        print(f"   Estimators used: {model.n_estimators_}")
        
        return model, val_mape

def train_xgboost_dart(X_train, X_val, y_train, y_val, horizon, models_dir, df_val=None):
    """Train XGBoost DART model with M4-optimized config"""
    print(f"\n{'='*60}")
    print(f"Training XGBoost DART for {horizon}")
    print(f"{'='*60}")
    
    with mlflow.start_run(run_name=f"xgb_dart_{horizon}"):
        # Get M4-optimized config
        config = get_config_for_model('xgboost', horizon)
        
        # Log parameters
        for k, v in config.items():
            mlflow.log_param(k, v)
        mlflow.log_param("model_type", "XGBoost_DART")
        mlflow.log_param("horizon", horizon)
        
        # Train
        model = xgb.XGBRegressor(**config)
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            early_stopping_rounds=100,
            verbose=False
        )
        
        # Predictions
        train_pred = model.predict(X_train)
        val_pred = model.predict(X_val)
        
        # Basic metrics
        train_mape = np.mean(np.abs((y_train - train_pred) / y_train)) * 100
        val_mape = np.mean(np.abs((y_val - val_pred) / y_val)) * 100
        
        mlflow.log_metric("train_mape", train_mape)
        mlflow.log_metric("val_mape", val_mape)
        mlflow.log_metric("best_iteration", model.best_iteration)
        
        # Comprehensive evaluation if validation dataframe provided
        if df_val is not None:
            try:
                df_eval = df_val.with_columns([
                    pl.Series("y_pred", val_pred),
                    pl.Series("y_true", y_val)
                ])
                
                eval_results = comprehensive_evaluation(
                    df_eval,
                    y_true_col="y_true",
                    y_pred_col="y_pred",
                    horizon=horizon
                )
                
                if 'by_regime' in eval_results:
                    for regime, metrics in eval_results['by_regime'].items():
                        mlflow.log_metric(f"mape_{regime}", metrics.get('mape', np.nan))
                        if 'sharpe' in metrics:
                            mlflow.log_metric(f"sharpe_{regime}", metrics['sharpe'])
            except Exception as e:
                print(f"   ⚠️  Comprehensive evaluation failed: {e}")
        
        # Save model
        model_subdir = f"{models_dir}/xgboost_dart"
        os.makedirs(model_subdir, exist_ok=True)
        model_path = f"{model_subdir}/model.bin"
        model.save_model(model_path)
        mlflow.log_artifact(model_path)
        
        print(f"✅ XGBoost DART {horizon}: Train MAPE={train_mape:.2f}%, Val MAPE={val_mape:.2f}%")
        print(f"   Best iteration: {model.best_iteration}")
        
        return model, val_mape

def main():
    parser = argparse.ArgumentParser(description="Train tree-based baseline models")
    parser.add_argument("--horizon", required=True, choices=["1w", "1m", "3m", "6m", "12m"], help="Prediction horizon")
    parser.add_argument("--surface", choices=["prod", "full"], default="prod",
                       help="Surface type: prod (≈290 cols) or full (1,948+ cols)")
    args = parser.parse_args()
    
    horizon = args.horizon
    target_col = f"target_{horizon}"
    
    print("="*80)
    print(f"🌳 TREE-BASED BASELINES - {horizon.upper()}")
    print("="*80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"CPU threads: 8 (optimized for M4 Mac)")
    print(f"MLflow tracking: file://{MLFLOW_DIR}")
    print("="*80)
    print()
    
    # Setup model directory (new naming)
    surface = args.surface
    models_dir = f"{CBI_V14_REPO}/Models/local/horizon_{horizon}/{surface}/baselines"
    
    # Load data
    df = load_training_data(horizon, surface)
    X_train, X_val, y_train, y_val, feature_cols, df_val = prepare_features(df, target_col)
    
    print(f"📊 Data prepared:")
    print(f"   Training: {len(X_train)} samples × {len(feature_cols)} features")
    print(f"   Validation: {len(X_val)} samples")
    print()
    
    # Train all tree models
    results = {}
    
    try:
        _, results['lgbm_dart'] = train_lightgbm_dart(
            X_train, X_val, y_train, y_val, horizon, models_dir, df_val
        )
    except Exception as e:
        print(f"❌ LightGBM DART failed: {e}")
        import traceback
        traceback.print_exc()
        results['lgbm_dart'] = None
    
    try:
        _, results['xgb_dart'] = train_xgboost_dart(
            X_train, X_val, y_train, y_val, horizon, models_dir, df_val
        )
    except Exception as e:
        print(f"❌ XGBoost DART failed: {e}")
        import traceback
        traceback.print_exc()
        results['xgb_dart'] = None
    
    # Summary
    print("\n" + "="*80)
    print(f"📊 TREE BASELINES SUMMARY - {horizon.upper()}")
    print("="*80)
    
    for model_name, mape in results.items():
        if mape is not None:
            print(f"✅ {model_name:20s}: Val MAPE = {mape:6.2f}%")
        else:
            print(f"❌ {model_name:20s}: FAILED")
    
    if any(v is not None for v in results.values()):
        best_model = min((item for item in results.items() if item[1] is not None), key=lambda x: x[1])
        print(f"\n🏆 Best model: {best_model[0]} (MAPE = {best_model[1]:.2f}%)")
    
    print("="*80)
    print()

if __name__ == "__main__":
    main()

