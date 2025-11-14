#!/usr/bin/env python3
"""
Simple Neural Baselines - 1-layer LSTM, GRU, Feedforward
Day 2, Track C: Train simple neural models for all 5 horizons
M4 16GB Optimized: FP16 mixed precision, batch_size ≤64, sequential training
"""
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "1"

import argparse
import polars as pl
import mlflow
import numpy as np
from datetime import datetime

import tensorflow as tf
import gc
from tensorflow.keras import mixed_precision, backend as K
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, GRU, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

# MANDATORY: Enable FP16 mixed precision for 16GB RAM
mixed_precision.set_global_policy("mixed_float16")

# Environment setup
EXTERNAL_DRIVE = os.getenv("EXTERNAL_DRIVE", "/Volumes/Satechi Hub")
CBI_V14_REPO = os.getenv("CBI_V14_REPO", f"{EXTERNAL_DRIVE}/Projects/CBI-V14")
TRAINING_DATA = f"{CBI_V14_REPO}/TrainingData"
MLFLOW_DIR = f"{CBI_V14_REPO}/Models/mlflow"

# MLflow setup
mlflow.set_tracking_uri(f"file://{MLFLOW_DIR}")
mlflow.set_experiment("baselines_neural")

def load_training_data(horizon, surface="prod"):
    """Load cached training data (new naming convention)"""
    data_path = f"{TRAINING_DATA}/exports/zl_training_{surface}_allhistory_{horizon}.parquet"
    
    print(f"Loading data: {data_path}")
    df = pl.read_parquet(data_path)
    
    print(f"✅ Loaded {len(df)} rows × {len(df.columns)} columns")
    return df

def prepare_sequences(df, target_col, seq_len=256):
    """Prepare sequences for neural networks"""
    # Exclude target and date columns
    exclude_cols = ['date', target_col] + [col for col in df.columns if col.startswith('target_')]
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Convert to numpy
    data = df.select(feature_cols).to_numpy()
    targets = df[target_col].to_numpy()
    
    # Create sequences
    X, y = [], []
    for i in range(seq_len, len(data)):
        X.append(data[i-seq_len:i])
        y.append(targets[i])
    
    X = np.array(X)
    y = np.array(y)
    
    # Split train/val (80/20)
    split_idx = int(len(X) * 0.8)
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]
    
    return X_train, X_val, y_train, y_val, len(feature_cols)

def build_lstm_model(seq_len, n_features, units=128):
    """Build 1-layer LSTM model"""
    model = Sequential([
        LSTM(units, input_shape=(seq_len, n_features)),
        Dropout(0.2),
        Dense(1)
    ])
    
    model.compile(
        optimizer='adam',
        loss='mse',
        metrics=['mae', 'mape']
    )
    
    return model

def build_gru_model(seq_len, n_features, units=128):
    """Build 1-layer GRU model"""
    model = Sequential([
        GRU(units, input_shape=(seq_len, n_features)),
        Dropout(0.2),
        Dense(1)
    ])
    
    model.compile(
        optimizer='adam',
        loss='mse',
        metrics=['mae', 'mape']
    )
    
    return model

def build_feedforward_model(seq_len, n_features, units=128):
    """Build feedforward (flatten sequences) model"""
    from tensorflow.keras.layers import Flatten
    
    model = Sequential([
        Flatten(input_shape=(seq_len, n_features)),
        Dense(units, activation='relu'),
        Dropout(0.3),
        Dense(64, activation='relu'),
        Dropout(0.2),
        Dense(1)
    ])
    
    model.compile(
        optimizer='adam',
        loss='mse',
        metrics=['mae', 'mape']
    )
    
    return model

def train_model(model, X_train, X_val, y_train, y_val, model_name, horizon, models_dir):
    """Train a neural model with memory-safe settings"""
    
    # Checkpoint path (new structure: Models/local/horizon_{h}/{surface}/{family}/{model}_v{ver}/)
    model_subdir = f"{models_dir}/{model_name}_v001"
    os.makedirs(model_subdir, exist_ok=True)
    checkpoint_path = f"{model_subdir}/model.h5"
    
    # Callbacks
    callbacks = [
        EarlyStopping(patience=12, restore_best_weights=True, verbose=1),
        ModelCheckpoint(checkpoint_path, save_best_only=True, verbose=0)
    ]
    
    # Train with SMALL batch size for 16GB RAM
    history = model.fit(
        X_train, y_train,
        batch_size=64,  # Max for 1-layer models on 16GB RAM
        epochs=100,
        validation_data=(X_val, y_val),
        callbacks=callbacks,
        verbose=1
    )
    
    # Load best weights
    model.load_weights(checkpoint_path)
    
    # Predictions
    train_pred = model.predict(X_train, batch_size=64, verbose=0)
    val_pred = model.predict(X_val, batch_size=64, verbose=0)
    
    # Metrics
    train_mape = np.mean(np.abs((y_train - train_pred.flatten()) / y_train)) * 100
    val_mape = np.mean(np.abs((y_val - val_pred.flatten()) / y_val)) * 100
    
    return history, train_mape, val_mape

def main():
    parser = argparse.ArgumentParser(description="Train simple neural baseline models")
    parser.add_argument("--horizon", required=True, choices=["1w", "1m", "3m", "6m", "12m"], help="Prediction horizon")
    parser.add_argument("--surface", choices=["prod", "full"], default="prod",
                       help="Surface type: prod (≈290 cols) or full (1,948+ cols)")
    args = parser.parse_args()
    
    horizon = args.horizon
    target_col = f"target_{horizon}"
    
    print("="*80)
    print(f"🧠 SIMPLE NEURAL BASELINES - {horizon.upper()}")
    print("="*80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mixed precision: FP16 (MANDATORY for 16GB RAM)")
    print(f"Batch size: 64 (max for 1-layer models)")
    print(f"MLflow tracking: file://{MLFLOW_DIR}")
    
    # Verify GPU
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        print(f"✅ Metal GPU detected: {len(gpus)} device(s)")
    else:
        print("⚠️  No GPU detected - using CPU only")
    
    print("="*80)
    print()
    
    # Setup model directory (new naming)
    surface = args.surface
    models_dir = f"{CBI_V14_REPO}/Models/local/horizon_{horizon}/{surface}/baselines"
    
    # Load data
    df = load_training_data(horizon, surface)
    X_train, X_val, y_train, y_val, n_features = prepare_sequences(df, target_col, seq_len=256)
    
    print(f"📊 Sequences prepared:")
    print(f"   Training: {X_train.shape}")
    print(f"   Validation: {X_val.shape}")
    print(f"   Features: {n_features}")
    print()
    
    # Train all models
    results = {}
    
    # 1-layer LSTM
    print(f"\n{'='*60}")
    print(f"Training 1-Layer LSTM for {horizon}")
    print(f"{'='*60}")
    
    with mlflow.start_run(run_name=f"lstm_1layer_{horizon}"):
        mlflow.log_param("model_type", "LSTM_1layer")
        mlflow.log_param("horizon", horizon)
        mlflow.log_param("units", 128)
        mlflow.log_param("batch_size", 64)
        mlflow.log_param("seq_len", 256)
        
        model = build_lstm_model(256, n_features, units=128)
        _, train_mape, val_mape = train_model(model, X_train, X_val, y_train, y_val, "lstm_1layer", horizon, models_dir)
        
        mlflow.log_metric("train_mape", train_mape)
        mlflow.log_metric("val_mape", val_mape)
        
        results['lstm_1layer'] = val_mape
        print(f"✅ 1-Layer LSTM: Train MAPE={train_mape:.2f}%, Val MAPE={val_mape:.2f}%")
        
        # MANDATORY: Clear session
        K.clear_session()
        import gc; gc.collect()
    
    # 1-layer GRU
    print(f"\n{'='*60}")
    print(f"Training 1-Layer GRU for {horizon}")
    print(f"{'='*60}")
    
    with mlflow.start_run(run_name=f"gru_1layer_{horizon}"):
        mlflow.log_param("model_type", "GRU_1layer")
        mlflow.log_param("horizon", horizon)
        mlflow.log_param("units", 128)
        mlflow.log_param("batch_size", 64)
        
        model = build_gru_model(256, n_features, units=128)
        _, train_mape, val_mape = train_model(model, X_train, X_val, y_train, y_val, "gru_1layer", horizon, models_dir)
        
        mlflow.log_metric("train_mape", train_mape)
        mlflow.log_metric("val_mape", val_mape)
        
        results['gru_1layer'] = val_mape
        print(f"✅ 1-Layer GRU: Train MAPE={train_mape:.2f}%, Val MAPE={val_mape:.2f}%")
        
        # MANDATORY: Clear session
        K.clear_session()
        gc.collect()
    
    # Feedforward
    print(f"\n{'='*60}")
    print(f"Training Feedforward (Dense) for {horizon}")
    print(f"{'='*60}")
    
    with mlflow.start_run(run_name=f"feedforward_{horizon}"):
        mlflow.log_param("model_type", "Feedforward")
        mlflow.log_param("horizon", horizon)
        mlflow.log_param("units", 128)
        mlflow.log_param("batch_size", 64)
        
        model = build_feedforward_model(256, n_features, units=128)
        _, train_mape, val_mape = train_model(model, X_train, X_val, y_train, y_val, "feedforward", horizon, models_dir)
        
        mlflow.log_metric("train_mape", train_mape)
        mlflow.log_metric("val_mape", val_mape)
        
        results['feedforward'] = val_mape
        print(f"✅ Feedforward: Train MAPE={train_mape:.2f}%, Val MAPE={val_mape:.2f}%")
        
        # MANDATORY: Clear session
        K.clear_session()
        gc.collect()
    
    # Summary
    print("\n" + "="*80)
    print(f"📊 SIMPLE NEURAL BASELINES SUMMARY - {horizon.upper()}")
    print("="*80)
    
    for model_name, mape in results.items():
        print(f"✅ {model_name:20s}: Val MAPE = {mape:6.2f}%")
    
    best_model = min(results.items(), key=lambda x: x[1])
    print(f"\n🏆 Best model: {best_model[0]} (MAPE = {best_model[1]:.2f}%)")
    print("="*80)
    print()
    
    print("💾 Models saved to:")
    print(f"   {models_dir}")
    print()

if __name__ == "__main__":
    main()

