#!/usr/bin/env python3
"""
Multi-layer LSTM/GRU models for deeper temporal pattern learning.
"""
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from pathlib import Path
import gc
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from training.features.feature_catalog import FeatureCatalog


def build_multi_layer_lstm_model(
    input_shape,
    lstm_units=[64, 32],
    dropout_rate=0.3,
    model_type='lstm',
    output_dim=1
):
    """
    Build 2-layer LSTM or GRU model.
    
    Args:
        input_shape: (time_steps, num_features)
        lstm_units: List of units per layer
        dropout_rate: Dropout rate
        model_type: 'lstm' or 'gru'
        output_dim: Output dimension
    """
    inputs = layers.Input(shape=input_shape)
    
    x = inputs
    layer_class = layers.LSTM if model_type == 'lstm' else layers.GRU
    
    # First layer (returns sequences for second layer)
    x = layer_class(
        units=lstm_units[0],
        return_sequences=True,
        dropout=dropout_rate,
        recurrent_dropout=dropout_rate
    )(x)
    
    # Second layer
    if len(lstm_units) > 1:
        x = layer_class(
            units=lstm_units[1],
            return_sequences=False,
            dropout=dropout_rate,
            recurrent_dropout=dropout_rate
        )(x)
    
    # Dense layers
    x = layers.Dense(64, activation='relu')(x)
    x = layers.Dropout(dropout_rate)(x)
    outputs = layers.Dense(output_dim)(x)
    
    model = keras.Model(inputs=inputs, outputs=outputs)
    return model


def train_multi_layer_model(
    data_path: Path,
    horizon: str,
    model_dir: Path,
    model_type='lstm',
    time_steps=30,
    batch_size=32,
    epochs=50,
    lstm_units=[64, 32]
):
    """Train multi-layer LSTM/GRU model."""
    import pandas as pd
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    
    print(f"\n--- Training 2-layer {model_type.upper()} for {horizon} horizon ---")
    
    try:
        df = pd.read_parquet(data_path)
        available_cols = set(df.columns)
        feature_cols = FeatureCatalog.get_features_for_model('neural')
        feature_cols = [col for col in feature_cols if col in available_cols]
        
        if len(feature_cols) < 100:
            numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
            feature_cols = [col for col in numeric_cols if col not in FeatureCatalog.EXCLUDED]
        
        print(f"Using {len(feature_cols)} features")
        target_col = 'zl_price_current'
        
        scaler = StandardScaler()
        df_scaled = df.copy()
        df_scaled[feature_cols] = scaler.fit_transform(df[feature_cols])
        
        # Create sequences
        X_seq, y_seq = [], []
        for i in range(len(df_scaled) - time_steps):
            X_seq.append(df_scaled[feature_cols].iloc[i:i+time_steps].values)
            y_seq.append(df_scaled[target_col].iloc[i+time_steps])
        
        X_seq = np.array(X_seq)
        y_seq = np.array(y_seq)
        
        X_train, X_val, y_train, y_val = train_test_split(X_seq, y_seq, test_size=0.2, shuffle=False)
        
        model = build_multi_layer_lstm_model(
            input_shape=(time_steps, len(feature_cols)),
            lstm_units=lstm_units,
            model_type=model_type
        )
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='mean_squared_error',
            metrics=['mae']
        )
        
        history = model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            batch_size=batch_size,
            epochs=epochs,
            callbacks=[
                keras.callbacks.EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
                keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5)
            ],
            verbose=1
        )
        
        output_path = model_dir / f"{model_type}_2layer_{horizon}"
        model.save(output_path)
        
        import joblib
        joblib.dump(scaler, model_dir / f"{model_type}_2layer_{horizon}_scaler.pkl")
        
        print(f"✅ 2-layer {model_type.upper()} model saved to {output_path}")
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        keras.backend.clear_session()
        gc.collect()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--horizon", required=True)
    parser.add_argument("--model-type", choices=['lstm', 'gru'], default='lstm')
    parser.add_argument("--data-path")
    parser.add_argument("--time-steps", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=50)
    
    args = parser.parse_args()
    
    current_path = Path(__file__).resolve()
    repo_root = None
    for parent in current_path.parents:
        if (parent / "QUICK_REFERENCE.txt").exists() or (parent / ".git").exists():
            repo_root = parent
            break
    
    # New naming: zl_training_{surface}_allhistory_{horizon}.parquet
    surface = getattr(args, 'surface', 'prod')  # Default to prod surface
    data_path = Path(args.data_path).expanduser() if args.data_path else repo_root / f"TrainingData/exports/zl_training_{surface}_allhistory_{args.horizon}.parquet"
    # New model path: Models/local/horizon_{h}/{surface}/{family}/{model}_v{ver}/
    model_dir = repo_root / f"Models/local/horizon_{args.horizon}/{surface}/advanced"
    model_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        physical_devices = tf.config.list_physical_devices('GPU')
        if physical_devices:
            tf.config.experimental.set_memory_growth(physical_devices[0], True)
    except:
        pass
    
    train_multi_layer_model(
        data_path=data_path,
        horizon=args.horizon,
        model_dir=model_dir,
        model_type=args.model_type,
        time_steps=args.time_steps,
        batch_size=args.batch_size,
        epochs=args.epochs
    )

