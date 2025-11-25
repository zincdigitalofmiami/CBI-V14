#!/usr/bin/env python3
"""
Tiny Transformer encoder for long-range dependencies and regime transitions.
Memory-optimized: 2-4 layers, 4 attention heads, d_model=256, batch_size ≤16.
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
from training.advanced.attention_model import MultiHeadAttention


def transformer_encoder_layer(d_model, num_heads, dff, dropout_rate=0.2):
    """Single transformer encoder layer."""
    inputs = layers.Input(shape=(None, d_model))
    
    # Multi-head attention
    attention = MultiHeadAttention(d_model, num_heads)
    attn_output = attention(inputs, inputs, inputs)
    attn_output = layers.Dropout(dropout_rate)(attn_output)
    out1 = layers.LayerNormalization()(inputs + attn_output)
    
    # Feed-forward network
    ffn = keras.Sequential([
        layers.Dense(dff, activation='relu'),
        layers.Dense(d_model)
    ])
    ffn_output = ffn(out1)
    ffn_output = layers.Dropout(dropout_rate)(ffn_output)
    out2 = layers.LayerNormalization()(out1 + ffn_output)
    
    return keras.Model(inputs=inputs, outputs=out2)


def build_tiny_transformer(
    input_shape,
    num_layers=2,
    d_model=256,
    num_heads=4,
    dff=512,
    dropout_rate=0.2,
    output_dim=1
):
    """
    Build tiny transformer encoder.
    
    Args:
        input_shape: (time_steps, num_features)
        num_layers: Number of encoder layers (2-4)
        d_model: Model dimension (256)
        num_heads: Attention heads (4)
        dff: Feed-forward dimension (512)
        dropout_rate: Dropout rate
        output_dim: Output dimension
    """
    inputs = layers.Input(shape=input_shape)
    
    # Project input to d_model
    x = layers.Dense(d_model)(inputs)
    
    # Positional encoding (learned)
    x = layers.Dense(d_model)(x)
    
    # Stack encoder layers
    for _ in range(num_layers):
        encoder_layer = transformer_encoder_layer(d_model, num_heads, dff, dropout_rate)
        x = encoder_layer(x)
    
    # Global pooling and output
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dense(64, activation='relu')(x)
    x = layers.Dropout(dropout_rate)(x)
    outputs = layers.Dense(output_dim)(x)
    
    model = keras.Model(inputs=inputs, outputs=outputs)
    return model


def train_tiny_transformer(
    data_path: Path,
    horizon: str,
    model_dir: Path,
    time_steps=128,
    batch_size=16,
    epochs=50,
    num_layers=2,
    d_model=256,
    num_heads=4
):
    """Train tiny transformer."""
    import pandas as pd
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    
    print(f"\n--- Training Tiny Transformer for {horizon} horizon ---")
    print(f"Architecture: {num_layers} layers, d_model={d_model}, heads={num_heads}")
    
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
        
        model = build_tiny_transformer(
            input_shape=(time_steps, len(feature_cols)),
            num_layers=num_layers,
            d_model=d_model,
            num_heads=num_heads
        )
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.0001),
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
        
        output_path = model_dir / f"transformer_{horizon}"
        model.save(output_path)
        
        import joblib
        joblib.dump(scaler, model_dir / f"transformer_{horizon}_scaler.pkl")
        
        print(f"✅ Transformer model saved to {output_path}")
        
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
    parser.add_argument("--data-path")
    parser.add_argument("--time-steps", type=int, default=128)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--num-layers", type=int, default=2)
    parser.add_argument("--d-model", type=int, default=256)
    parser.add_argument("--num-heads", type=int, default=4)
    
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
    
    train_tiny_transformer(
        data_path=data_path,
        horizon=args.horizon,
        model_dir=model_dir,
        time_steps=args.time_steps,
        batch_size=args.batch_size,
        epochs=args.epochs,
        num_layers=args.num_layers,
        d_model=args.d_model,
        num_heads=args.num_heads
    )

