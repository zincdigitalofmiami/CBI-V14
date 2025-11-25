#!/usr/bin/env python3
"""
Temporal Convolutional Network (TCN) for time series forecasting.
Optimized for Apple Silicon M4 with TensorFlow Metal.
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


class TemporalBlock(layers.Layer):
    """Temporal block with dilated convolution, weight norm, and residual connection."""
    
    def __init__(self, filters, kernel_size, dilation_rate, dropout_rate=0.2, **kwargs):
        super().__init__(**kwargs)
        self.filters = filters
        self.kernel_size = kernel_size
        self.dilation_rate = dilation_rate
        self.dropout_rate = dropout_rate
        
        # Two dilated convolutions
        self.conv1 = layers.Conv1D(
            filters=filters,
            kernel_size=kernel_size,
            dilation_rate=dilation_rate,
            padding='causal',
            activation='relu'
        )
        self.conv2 = layers.Conv1D(
            filters=filters,
            kernel_size=kernel_size,
            dilation_rate=dilation_rate,
            padding='causal',
            activation='relu'
        )
        
        self.dropout1 = layers.Dropout(dropout_rate)
        self.dropout2 = layers.Dropout(dropout_rate)
        
        # Residual connection (1x1 conv if dimensions don't match)
        self.residual = None
        
    def build(self, input_shape):
        # If input channels != output channels, need 1x1 conv for residual
        if input_shape[-1] != self.filters:
            self.residual = layers.Conv1D(filters=self.filters, kernel_size=1)
        super().build(input_shape)
    
    def call(self, inputs, training=False):
        # First conv block
        x = self.conv1(inputs)
        x = self.dropout1(x, training=training)
        
        # Second conv block
        x = self.conv2(x)
        x = self.dropout2(x, training=training)
        
        # Residual connection
        if self.residual:
            residual = self.residual(inputs)
        else:
            residual = inputs
        
        return layers.ReLU()(x + residual)


def build_tcn_model(
    input_shape,
    num_filters=64,
    kernel_size=3,
    num_blocks=4,
    dropout_rate=0.2,
    output_dim=1
):
    """
    Build TCN model.
    
    Args:
        input_shape: (time_steps, num_features)
        num_filters: Number of filters per block
        kernel_size: Convolution kernel size
        num_blocks: Number of temporal blocks
        dropout_rate: Dropout rate
        output_dim: Output dimension (1 for regression)
    
    Returns:
        Compiled Keras model
    """
    inputs = layers.Input(shape=input_shape)
    
    # Stack temporal blocks with exponentially increasing dilation
    x = inputs
    for i in range(num_blocks):
        dilation_rate = 2 ** i
        x = TemporalBlock(
            filters=num_filters,
            kernel_size=kernel_size,
            dilation_rate=dilation_rate,
            dropout_rate=dropout_rate
        )(x)
    
    # Global pooling and output
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dense(64, activation='relu')(x)
    x = layers.Dropout(dropout_rate)(x)
    outputs = layers.Dense(output_dim)(x)
    
    model = keras.Model(inputs=inputs, outputs=outputs)
    
    return model


def train_tcn_model(
    data_path: Path,
    horizon: str,
    model_dir: Path,
    time_steps=30,
    batch_size=32,
    epochs=50,
    num_filters=64,
    num_blocks=4
):
    """
    Train TCN model on time series data.
    
    Args:
        data_path: Path to Parquet training data
        horizon: Forecast horizon (1w, 1m, etc.)
        model_dir: Directory to save model
        time_steps: Sequence length
        batch_size: Batch size (≤32 for memory)
        epochs: Training epochs
        num_filters: TCN filters per block
        num_blocks: Number of TCN blocks
    """
    import pandas as pd
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    
    print(f"\n--- Training TCN for {horizon} horizon ---")
    print(f"Architecture: {num_blocks} blocks, {num_filters} filters, kernel_size=3")
    
    try:
        # Load data
        df = pd.read_parquet(data_path)
        
        # Get features
        available_cols = set(df.columns)
        feature_cols = FeatureCatalog.get_features_for_model('neural')
        feature_cols = [col for col in feature_cols if col in available_cols]
        
        if len(feature_cols) < 100:
            numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
            feature_cols = [col for col in numeric_cols if col not in FeatureCatalog.EXCLUDED]
        
        print(f"Using {len(feature_cols)} features")
        target_col = 'zl_price_current'
        
        # Scale features
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
        
        # Train/val split
        X_train, X_val, y_train, y_val = train_test_split(
            X_seq, y_seq, test_size=0.2, shuffle=False
        )
        
        print(f"Training sequences: {X_train.shape[0]}, Validation: {X_val.shape[0]}")
        
        # Build model
        model = build_tcn_model(
            input_shape=(time_steps, len(feature_cols)),
            num_filters=num_filters,
            num_blocks=num_blocks,
            dropout_rate=0.2
        )
        
        # Compile with FP16 mixed precision
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='mean_squared_error',
            metrics=['mae']
        )
        
        print(f"\nModel summary:")
        model.summary()
        
        # Train
        history = model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            batch_size=batch_size,
            epochs=epochs,
            callbacks=[
                keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=10,
                    restore_best_weights=True
                ),
                keras.callbacks.ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=0.5,
                    patience=5,
                    min_lr=1e-6
                )
            ],
            verbose=1
        )
        
        # Save model
        output_path = model_dir / f"tcn_{horizon}"
        model.save(output_path)
        
        # Save scaler
        import joblib
        scaler_path = model_dir / f"tcn_{horizon}_scaler.pkl"
        joblib.dump(scaler, scaler_path)
        
        print(f"\n✅ TCN model saved to {output_path}")
        print(f"✅ Scaler saved to {scaler_path}")
        
        # Final metrics
        val_loss, val_mae = model.evaluate(X_val, y_val, verbose=0)
        print(f"Validation MAE: {val_mae:.4f}")
        
    except Exception as e:
        print(f"❌ Failed to train TCN: {e}")
        import traceback
        traceback.print_exc()
    finally:
        keras.backend.clear_session()
        gc.collect()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Train TCN model")
    parser.add_argument("--horizon", required=True, help="Forecast horizon")
    parser.add_argument("--data-path", help="Path to Parquet data")
    parser.add_argument("--time-steps", type=int, default=30, help="Sequence length")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--epochs", type=int, default=50, help="Epochs")
    parser.add_argument("--num-filters", type=int, default=64, help="TCN filters")
    parser.add_argument("--num-blocks", type=int, default=4, help="TCN blocks")
    
    args = parser.parse_args()
    
    # Get repo root
    current_path = Path(__file__).resolve()
    repo_root = None
    for parent in current_path.parents:
        if (parent / "QUICK_REFERENCE.txt").exists() or (parent / ".git").exists():
            repo_root = parent
            break
    
    if not repo_root:
        raise FileNotFoundError("Repository root not found")
    
    # New naming: zl_training_{surface}_allhistory_{horizon}.parquet
    surface = getattr(args, 'surface', 'prod')  # Default to prod surface
    data_path = Path(args.data_path).expanduser() if args.data_path else repo_root / f"TrainingData/exports/zl_training_{surface}_allhistory_{args.horizon}.parquet"
    # New model path: Models/local/horizon_{h}/{surface}/{family}/{model}_v{ver}/
    model_dir = repo_root / f"Models/local/horizon_{args.horizon}/{surface}/advanced"
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure GPU
    try:
        physical_devices = tf.config.list_physical_devices('GPU')
        if physical_devices:
            tf.config.experimental.set_memory_growth(physical_devices[0], True)
            print("✅ Metal GPU configured")
    except:
        print("⚠️ Running on CPU")
    
    train_tcn_model(
        data_path=data_path,
        horizon=args.horizon,
        model_dir=model_dir,
        time_steps=args.time_steps,
        batch_size=args.batch_size,
        epochs=args.epochs,
        num_filters=args.num_filters,
        num_blocks=args.num_blocks
    )

