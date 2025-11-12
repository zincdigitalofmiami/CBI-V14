#!/usr/bin/env python3
"""
Tree-Based Baselines - LightGBM DART, XGBoost DART
Day 2, Track B: Train tree models for all 5 horizons
M4 16GB Optimized: CPU-friendly, 8-10 threads
"""
import os
import argparse
import polars as pl
import mlflow
import numpy as np
from datetime import datetime
import lightgbm as lgb
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit

# Environment setup
EXTERNAL_DRIVE = os.getenv("EXTERNAL_DRIVE", "/Volumes/Satechi Hub")
CBI_V14_REPO = os.getenv("CBI_V14_REPO", f"{EXTERNAL_DRIVE}/Projects/CBI-V14")
TRAINING_DATA = f"{CBI_V14_REPO}/TrainingData"
MODELS_DIR = f"{CBI_V14_REPO}/Models/local/baselines"
MLFLOW_DIR = f"{CBI_V14_REPO}/Models/mlflow"

# MLflow setup
mlflow.set_tracking_uri(f"file://{MLFLOW_DIR}")
mlflow.set_experiment("baselines_tree")

def load_training_data(horizon):
    """Load cached training data"""
    data_path = f"{TRAINING_DATA}/exports/production_training_data_{horizon}.parquet"
    
    print(f"Loading data: {data_path}")
    df = pl.read_parquet(data_path)
    
    print(f"✅ Loaded {len(df)} rows × {len(df.columns)} columns")
    return df

def prepare_features(df, target_col):
    """Prepare features for tree models"""
    # Exclude target and date columns
    exclude_cols = ['date', target_col] + [col for col in df.columns if col.startswith('target_')]
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Convert to numpy
    X = df.select(feature_cols).to_numpy()
    y = df[target_col].to_numpy()
    
    # Split train/val (80/20)
    split_idx = int(len(X) * 0.8)
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]
    
    return X_train, X_val, y_train, y_val, feature_cols

def train_lightgbm_dart(X_train, X_val, y_train, y_val, horizon):
    """Train LightGBM DART model"""
    print(f"\n{'='*60}")
    print(f"Training LightGBM DART for {horizon}")
    print(f"{'='*60}")
    
    with mlflow.start_run(run_name=f"lgbm_dart_{horizon}"):
        # Parameters (optimized for M4 Mac)
        params = {
            'boosting_type': 'dart',
            'objective': 'regression',
            'metric': 'mape',
            'num_leaves': 31,
            'max_depth': 6,
            'learning_rate': 0.05,
            'n_estimators': 2000,
            'num_threads': 8,  # M4 has 10 cores, leave 2 for OS
            'verbose': -1
        }
        
        # Log parameters
        for k, v in params.items():
            mlflow.log_param(k, v)
        mlflow.log_param("model_type", "LightGBM_DART")
        mlflow.log_param("horizon", horizon)
        
        # Train
        model = lgb.LGBMRegressor(**params)
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            callbacks=[lgb.early_stopping(stopping_rounds=100, verbose=False)]
        )
        
        # Predictions
        train_pred = model.predict(X_train)
        val_pred = model.predict(X_val)
        
        # Metrics
        train_mape = np.mean(np.abs((y_train - train_pred) / y_train)) * 100
        val_mape = np.mean(np.abs((y_val - val_pred) / y_val)) * 100
        
        mlflow.log_metric("train_mape", train_mape)
        mlflow.log_metric("val_mape", val_mape)
        mlflow.log_metric("n_estimators_used", model.n_estimators_)
        
        # Save model
        os.makedirs(MODELS_DIR, exist_ok=True)
        model_path = f"{MODELS_DIR}/lgbm_dart_{horizon}.txt"
        model.booster_.save_model(model_path)
        mlflow.log_artifact(model_path)
        
        print(f"✅ LightGBM DART {horizon}: Train MAPE={train_mape:.2f}%, Val MAPE={val_mape:.2f}%")
        print(f"   Estimators used: {model.n_estimators_}")
        
        return model, val_mape

def train_xgboost_dart(X_train, X_val, y_train, y_val, horizon):
    """Train XGBoost DART model"""
    print(f"\n{'='*60}")
    print(f"Training XGBoost DART for {horizon}")
    print(f"{'='*60}")
    
    with mlflow.start_run(run_name=f"xgb_dart_{horizon}"):
        # Parameters
        params = {
            'booster': 'dart',
            'objective': 'reg:squarederror',
            'max_depth': 8,
            'learning_rate': 0.03,
            'n_estimators': 2000,
            'tree_method': 'hist',  # Fast histogram method
            'n_jobs': 8
        }
        
        # Log parameters
        for k, v in params.items():
            mlflow.log_param(k, v)
        mlflow.log_param("model_type", "XGBoost_DART")
        mlflow.log_param("horizon", horizon)
        
        # Train
        model = xgb.XGBRegressor(**params)
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            early_stopping_rounds=100,
            verbose=False
        )
        
        # Predictions
        train_pred = model.predict(X_train)
        val_pred = model.predict(X_val)
        
        # Metrics
        train_mape = np.mean(np.abs((y_train - train_pred) / y_train)) * 100
        val_mape = np.mean(np.abs((y_val - val_pred) / y_val)) * 100
        
        mlflow.log_metric("train_mape", train_mape)
        mlflow.log_metric("val_mape", val_mape)
        mlflow.log_metric("best_iteration", model.best_iteration)
        
        # Save model
        model_path = f"{MODELS_DIR}/xgb_dart_{horizon}.json"
        model.save_model(model_path)
        mlflow.log_artifact(model_path)
        
        print(f"✅ XGBoost DART {horizon}: Train MAPE={train_mape:.2f}%, Val MAPE={val_mape:.2f}%")
        print(f"   Best iteration: {model.best_iteration}")
        
        return model, val_mape

def main():
    parser = argparse.ArgumentParser(description="Train tree-based baseline models")
    parser.add_argument("--horizon", required=True, choices=["1w", "1m", "3m", "6m", "12m"], help="Prediction horizon")
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
    
    # Load data
    df = load_training_data(horizon)
    X_train, X_val, y_train, y_val, feature_cols = prepare_features(df, target_col)
    
    print(f"📊 Data prepared:")
    print(f"   Training: {len(X_train)} samples × {len(feature_cols)} features")
    print(f"   Validation: {len(X_val)} samples")
    print()
    
    # Train all tree models
    results = {}
    
    try:
        _, results['lgbm_dart'] = train_lightgbm_dart(X_train, X_val, y_train, y_val, horizon)
    except Exception as e:
        print(f"❌ LightGBM DART failed: {e}")
        results['lgbm_dart'] = None
    
    try:
        _, results['xgb_dart'] = train_xgboost_dart(X_train, X_val, y_train, y_val, horizon)
    except Exception as e:
        print(f"❌ XGBoost DART failed: {e}")
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
        best_model = min((k, v) for k, v in results.items() if v is not None, key=lambda x: x[1])
        print(f"\n🏆 Best model: {best_model[0]} (MAPE = {best_model[1]:.2f}%)")
    
    print("="*80)
    print()

if __name__ == "__main__":
    main()

