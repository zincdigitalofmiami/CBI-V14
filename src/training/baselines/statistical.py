#!/usr/bin/env python3
"""
Statistical Baselines - ARIMA, Prophet, Exponential Smoothing
Day 2, Track A: Train statistical models for all 5 horizons
"""
import os
import argparse
import polars as pl
import mlflow
from pathlib import Path
from datetime import datetime

# Statsmodels imports
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import pmdarima as pm
from prophet import Prophet
import pandas as pd
import numpy as np

# Environment setup
EXTERNAL_DRIVE = os.getenv("EXTERNAL_DRIVE", "/Volumes/Satechi Hub")
CBI_V14_REPO = os.getenv("CBI_V14_REPO", f"{EXTERNAL_DRIVE}/Projects/CBI-V14")
TRAINING_DATA = f"{CBI_V14_REPO}/TrainingData"
MLFLOW_DIR = f"{CBI_V14_REPO}/Models/mlflow"

# MLflow setup
mlflow.set_tracking_uri(f"file://{MLFLOW_DIR}")
mlflow.set_experiment("baselines_statistical")

def load_training_data(horizon, surface="prod"):
    """Load cached training data for horizon (new naming convention)"""
    data_path = f"{TRAINING_DATA}/exports/zl_training_{surface}_allhistory_{horizon}.parquet"
    
    print(f"Loading data from: {data_path}")
    df = pl.read_parquet(data_path)
    
    print(f"✅ Loaded {len(df)} rows × {len(df.columns)} columns")
    return df

def prepare_time_series(df, target_col):
    """Prepare time series for statistical models"""
    # Convert to pandas for statsmodels compatibility
    df_pandas = df.select(['date', target_col]).to_pandas()
    df_pandas = df_pandas.sort_values('date').set_index('date')
    
    # Split train/val (80/20)
    split_idx = int(len(df_pandas) * 0.8)
    train = df_pandas.iloc[:split_idx]
    val = df_pandas.iloc[split_idx:]
    
    return train, val

def train_arima(train, val, target_col, horizon, models_dir):
    """Train ARIMA model"""
    print(f"\n{'='*60}")
    print(f"Training ARIMA for {horizon}")
    print(f"{'='*60}")
    
    with mlflow.start_run(run_name=f"arima_{horizon}"):
        # Log parameters
        mlflow.log_param("model_type", "ARIMA")
        mlflow.log_param("horizon", horizon)
        mlflow.log_param("target", target_col)
        
        # Fit ARIMA
        model = ARIMA(train[target_col], order=(5,1,2))  # Default ARIMA(5,1,2)
        model_fit = model.fit()
        
        # Predictions
        train_pred = model_fit.fittedvalues
        val_pred = model_fit.forecast(steps=len(val))
        
        # Metrics
        train_mape = np.mean(np.abs((train[target_col] - train_pred) / train[target_col])) * 100
        val_mape = np.mean(np.abs((val[target_col] - val_pred) / val[target_col])) * 100
        
        # Log metrics
        mlflow.log_metric("train_mape", train_mape)
        mlflow.log_metric("val_mape", val_mape)
        
        # Save model (new structure: Models/local/horizon_{h}/{surface}/{family}/{model}_v{ver}/)
        model_subdir = f"{models_dir}/arima_v001"
        os.makedirs(model_subdir, exist_ok=True)
        model_path = f"{model_subdir}/model.bin"
        import pickle
        with open(model_path, 'wb') as f:
            pickle.dump(model_fit, f)
        
        mlflow.log_artifact(model_path)
        
        print(f"✅ ARIMA {horizon}: Train MAPE={train_mape:.2f}%, Val MAPE={val_mape:.2f}%")
        
        return model_fit, val_mape

def train_auto_arima(train, val, target_col, horizon, models_dir):
    """Train Auto-ARIMA model"""
    print(f"\n{'='*60}")
    print(f"Training Auto-ARIMA for {horizon}")
    print(f"{'='*60}")
    
    with mlflow.start_run(run_name=f"auto_arima_{horizon}"):
        # Log parameters
        mlflow.log_param("model_type", "Auto-ARIMA")
        mlflow.log_param("horizon", horizon)
        
        # Fit Auto-ARIMA
        model = pm.auto_arima(
            train[target_col],
            seasonal=True,
            m=7,  # Weekly seasonality
            trace=True,
            error_action='ignore',
            suppress_warnings=True,
            stepwise=True
        )
        
        # Predictions
        train_pred = model.predict_in_sample()
        val_pred = model.predict(n_periods=len(val))
        
        # Metrics
        train_mape = np.mean(np.abs((train[target_col] - train_pred) / train[target_col])) * 100
        val_mape = np.mean(np.abs((val[target_col] - val_pred) / val[target_col])) * 100
        
        mlflow.log_metric("train_mape", train_mape)
        mlflow.log_metric("val_mape", val_mape)
        
        # Save model (new structure)
        model_subdir = f"{models_dir}/auto_arima_v001"
        os.makedirs(model_subdir, exist_ok=True)
        model_path = f"{model_subdir}/model.bin"
        import pickle
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        mlflow.log_artifact(model_path)
        
        print(f"✅ Auto-ARIMA {horizon}: Train MAPE={train_mape:.2f}%, Val MAPE={val_mape:.2f}%")
        
        return model, val_mape

def train_prophet(train, val, target_col, horizon, models_dir):
    """Train Facebook Prophet model"""
    print(f"\n{'='*60}")
    print(f"Training Prophet for {horizon}")
    print(f"{'='*60}")
    
    with mlflow.start_run(run_name=f"prophet_{horizon}"):
        # Log parameters
        mlflow.log_param("model_type", "Prophet")
        mlflow.log_param("horizon", horizon)
        
        # Prepare data for Prophet
        prophet_train = pd.DataFrame({
            'ds': train.index,
            'y': train[target_col].values
        })
        
        # Fit Prophet
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False
        )
        model.fit(prophet_train)
        
        # Predictions
        future = model.make_future_dataframe(periods=len(val), freq='D')
        forecast = model.predict(future)
        
        train_pred = forecast['yhat'].iloc[:len(train)].values
        val_pred = forecast['yhat'].iloc[len(train):].values
        
        # Metrics
        train_mape = np.mean(np.abs((train[target_col].values - train_pred) / train[target_col].values)) * 100
        val_mape = np.mean(np.abs((val[target_col].values - val_pred) / val[target_col].values)) * 100
        
        mlflow.log_metric("train_mape", train_mape)
        mlflow.log_metric("val_mape", val_mape)
        
        # Save model (new structure)
        model_subdir = f"{models_dir}/prophet_v001"
        os.makedirs(model_subdir, exist_ok=True)
        model_path = f"{model_subdir}/model.bin"
        import pickle
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        mlflow.log_artifact(model_path)
        
        print(f"✅ Prophet {horizon}: Train MAPE={train_mape:.2f}%, Val MAPE={val_mape:.2f}%")
        
        return model, val_mape

def train_exponential_smoothing(train, val, target_col, horizon, models_dir):
    """Train Exponential Smoothing model"""
    print(f"\n{'='*60}")
    print(f"Training Exponential Smoothing for {horizon}")
    print(f"{'='*60}")
    
    with mlflow.start_run(run_name=f"exp_smoothing_{horizon}"):
        # Log parameters
        mlflow.log_param("model_type", "Exponential_Smoothing")
        mlflow.log_param("horizon", horizon)
        
        # Fit Exponential Smoothing
        model = ExponentialSmoothing(
            train[target_col],
            seasonal_periods=7,
            trend='add',
            seasonal='add'
        )
        model_fit = model.fit()
        
        # Predictions
        train_pred = model_fit.fittedvalues
        val_pred = model_fit.forecast(steps=len(val))
        
        # Metrics
        train_mape = np.mean(np.abs((train[target_col] - train_pred) / train[target_col])) * 100
        val_mape = np.mean(np.abs((val[target_col] - val_pred) / val[target_col])) * 100
        
        mlflow.log_metric("train_mape", train_mape)
        mlflow.log_metric("val_mape", val_mape)
        
        # Save model (new structure)
        model_subdir = f"{models_dir}/exp_smoothing_v001"
        os.makedirs(model_subdir, exist_ok=True)
        model_path = f"{model_subdir}/model.bin"
        import pickle
        with open(model_path, 'wb') as f:
            pickle.dump(model_fit, f)
        
        mlflow.log_artifact(model_path)
        
        print(f"✅ Exp Smoothing {horizon}: Train MAPE={train_mape:.2f}%, Val MAPE={val_mape:.2f}%")
        
        return model_fit, val_mape

def main():
    parser = argparse.ArgumentParser(description="Train statistical baseline models")
    parser.add_argument("--horizon", required=True, choices=["1w", "1m", "3m", "6m", "12m"], help="Prediction horizon")
    parser.add_argument("--surface", choices=["prod", "full"], default="prod",
                       help="Surface type: prod (≈290 cols) or full (1,948+ cols)")
    args = parser.parse_args()
    
    horizon = args.horizon
    target_col = f"target_{horizon}"
    
    print("="*80)
    print(f"🔬 STATISTICAL BASELINES - {horizon.upper()}")
    print("="*80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"MLflow tracking: file://{MLFLOW_DIR}")
    print("="*80)
    print()
    
    # Setup model directory (new naming)
    surface = args.surface
    models_dir = f"{CBI_V14_REPO}/Models/local/horizon_{horizon}/{surface}/baselines"
    
    # Load data
    df = load_training_data(horizon, surface)
    train, val = prepare_time_series(df, target_col)
    
    print(f"\n📊 Data split:")
    print(f"   Training: {len(train)} days")
    print(f"   Validation: {len(val)} days")
    print()
    
    # Train all statistical models
    results = {}
    
    try:
        _, results['arima'] = train_arima(train, val, target_col, horizon, models_dir)
    except Exception as e:
        print(f"❌ ARIMA failed: {e}")
        results['arima'] = None
    
    try:
        _, results['auto_arima'] = train_auto_arima(train, val, target_col, horizon, models_dir)
    except Exception as e:
        print(f"❌ Auto-ARIMA failed: {e}")
        results['auto_arima'] = None
    
    try:
        _, results['prophet'] = train_prophet(train, val, target_col, horizon, models_dir)
    except Exception as e:
        print(f"❌ Prophet failed: {e}")
        results['prophet'] = None
    
    try:
        _, results['exp_smoothing'] = train_exponential_smoothing(train, val, target_col, horizon, models_dir)
    except Exception as e:
        print(f"❌ Exponential Smoothing failed: {e}")
        results['exp_smoothing'] = None
    
    # Summary
    print("\n" + "="*80)
    print(f"📊 STATISTICAL BASELINES SUMMARY - {horizon.upper()}")
    print("="*80)
    
    for model_name, mape in results.items():
        if mape is not None:
            print(f"✅ {model_name:20s}: Val MAPE = {mape:6.2f}%")
        else:
            print(f"❌ {model_name:20s}: FAILED")
    
    best_model = min((k, v) for k, v in results.items() if v is not None, key=lambda x: x[1])
    print(f"\n🏆 Best model: {best_model[0]} (MAPE = {best_model[1]:.2f}%)")
    print("="*80)
    print()

if __name__ == "__main__":
    main()

