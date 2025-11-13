#!/usr/bin/env python3
"""
Train simple baseline neural network models (LSTM, GRU) using TensorFlow/Keras.
This script is optimized for Apple Silicon (M4) with tensorflow-metal.
"""
import argparse
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow import keras
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from pathlib import Path
import gc

def get_repo_root():
    """Find the repository root by looking for a marker file."""
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / "QUICK_REFERENCE.txt").exists():
            return parent
    raise FileNotFoundError("Repository root not found.")

def configure_gpu():
    """Configure TensorFlow to use the Metal GPU on Apple Silicon."""
    try:
        physical_devices = tf.config.list_physical_devices('GPU')
        if physical_devices:
            tf.config.experimental.set_memory_growth(physical_devices[0], True)
            print("✅ Metal GPU configured for memory growth.")
        else:
            print("⚠️ No GPU found. Running on CPU.")
    except Exception as e:
        print(f"Could not configure GPU: {e}")

def create_sequences(X_data, y_data, time_steps=30):
    """Create sequences for time series forecasting."""
    Xs, ys = [], []
    for i in range(len(X_data) - time_steps):
        v = X_data.iloc[i:(i + time_steps)].values
        Xs.append(v)
        ys.append(y_data.iloc[i + time_steps])
    return np.array(Xs), np.array(ys)

def train_neural_model(data_path: Path, horizon: str, model_type: str, model_dir: Path):
    """Trains and saves a simple neural network model."""
    print(f"\n--- Training Simple {model_type.upper()} for {horizon} horizon ---")
    
    try:
        df = pd.read_parquet(data_path)
        
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        feature_cols = [col for col in numeric_cols if 'target' not in col and 'price' not in col]
        target_col = 'zl_price_current'
        
        # Scale features
        scaler = StandardScaler()
        df_scaled = df.copy()
        df_scaled[feature_cols] = scaler.fit_transform(df[feature_cols])

        # Create sequences
        X_seq, y_seq = create_sequences(df_scaled[feature_cols], df_scaled[target_col])
        
        X_train, X_val, y_train, y_val = train_test_split(X_seq, y_seq, test_size=0.2, shuffle=False)

        # Build model
        model = keras.Sequential()
        if model_type == 'lstm':
            model.add(keras.layers.LSTM(units=50, return_sequences=False, input_shape=(X_train.shape[1], X_train.shape[2])))
        elif model_type == 'gru':
            model.add(keras.layers.GRU(units=50, return_sequences=False, input_shape=(X_train.shape[1], X_train.shape[2])))
        
        model.add(keras.layers.Dropout(0.2))
        model.add(keras.layers.Dense(units=25, activation='relu'))
        model.add(keras.layers.Dense(units=1))

        model.compile(optimizer='adam', loss='mean_squared_error')
        
        history = model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            batch_size=32, # Smaller batch size for memory constraints
            epochs=50,
            callbacks=[
                keras.callbacks.EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
                keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=5)
            ],
            verbose=1
        )
        
        output_path = model_dir / f"simple_{model_type}_{horizon}"
        model.save(output_path)
        print(f"✅ Simple {model_type.upper()} model for {horizon} saved to {output_path}")

    except Exception as e:
        print(f"❌ Failed to train {model_type.upper()} for {horizon}: {e}")
    finally:
        # Clear memory after training
        keras.backend.clear_session()
        gc.collect()
        print("Keras session cleared.")

def main():
    parser = argparse.ArgumentParser(description="Train simple baseline neural models.")
    parser.add_argument("--horizon", required=True, help="Forecast horizon (e.g., 1w, 1m).")
    parser.add_argument("--model", choices=['lstm', 'gru', 'all'], default='all', help="Model to train.")
    parser.add_argument(
        "--data-path",
        help="Optional Parquet dataset path. Overrides default TrainingData/exports location."
    )
    
    args = parser.parse_args()
    
    configure_gpu()
    
    repo_root = get_repo_root()
    data_path = Path(args.data_path).expanduser() if args.data_path else repo_root / f"TrainingData/exports/production_training_data_{args.horizon}.parquet"
    model_dir = repo_root / "Models/local/baselines"
    model_dir.mkdir(parents=True, exist_ok=True)

    if not data_path.exists():
        print(f"❌ Data file not found at: {data_path}")
        return

    print(f"Found data for {args.horizon} horizon at {data_path}")

    if args.model in ['lstm', 'all']:
        train_neural_model(data_path, args.horizon, 'lstm', model_dir)
        
    if args.model in ['gru', 'all']:
        train_neural_model(data_path, args.horizon, 'gru', model_dir)
        
    print("\n--- Simple neural baseline training complete! ---")

if __name__ == "__main__":
    main()
