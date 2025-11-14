#!/usr/bin/env python3
"""
Multi-head attention mechanism for dynamic feature weighting and regime pattern matching.
Memory-optimized for 16GB RAM (batch_size ≤16, heads ≤4, d_model ≤256).
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


class MultiHeadAttention(layers.Layer):
    """Multi-head attention layer."""
    
    def __init__(self, d_model, num_heads, **kwargs):
        super().__init__(**kwargs)
        self.d_model = d_model
        self.num_heads = num_heads
        self.depth = d_model // num_heads
        
        self.wq = layers.Dense(d_model)
        self.wk = layers.Dense(d_model)
        self.wv = layers.Dense(d_model)
        self.dense = layers.Dense(d_model)
        
    def split_heads(self, x, batch_size):
        """Split the last dimension into (num_heads, depth)."""
        x = tf.reshape(x, (batch_size, -1, self.num_heads, self.depth))
        return tf.transpose(x, perm=[0, 2, 1, 3])
    
    def call(self, v, k, q):
        batch_size = tf.shape(q)[0]
        
        q = self.wq(q)
        k = self.wk(k)
        v = self.wv(v)
        
        q = self.split_heads(q, batch_size)
        k = self.split_heads(k, batch_size)
        v = self.split_heads(v, batch_size)
        
        # Scaled dot-product attention
        scaled_attention = self.scaled_dot_product_attention(q, k, v)
        scaled_attention = tf.transpose(scaled_attention, perm=[0, 2, 1, 3])
        concat_attention = tf.reshape(scaled_attention, (batch_size, -1, self.d_model))
        
        output = self.dense(concat_attention)
        return output
    
    def scaled_dot_product_attention(self, q, k, v):
        """Calculate scaled dot-product attention."""
        matmul_qk = tf.matmul(q, k, transpose_b=True)
        dk = tf.cast(tf.shape(k)[-1], tf.float32)
        scaled_attention_logits = matmul_qk / tf.math.sqrt(dk)
        attention_weights = tf.nn.softmax(scaled_attention_logits, axis=-1)
        output = tf.matmul(attention_weights, v)
        return output


def build_attention_model(
    input_shape,
    d_model=256,
    num_heads=4,
    dff=512,
    dropout_rate=0.2,
    output_dim=1
):
    """
    Build attention-based model.
    
    Args:
        input_shape: (time_steps, num_features)
        d_model: Model dimension (≤256 for memory)
        num_heads: Number of attention heads (≤4)
        dff: Feed-forward dimension
        dropout_rate: Dropout rate
        output_dim: Output dimension
    """
    inputs = layers.Input(shape=input_shape)
    
    # Project input to d_model dimension
    x = layers.Dense(d_model)(inputs)
    
    # Multi-head attention
    attention = MultiHeadAttention(d_model, num_heads)
    attn_output = attention(x, x, x)
    x = layers.LayerNormalization()(x + attn_output)
    x = layers.Dropout(dropout_rate)(x)
    
    # Feed-forward network
    ffn = keras.Sequential([
        layers.Dense(dff, activation='relu'),
        layers.Dense(d_model)
    ])
    ffn_output = ffn(x)
    x = layers.LayerNormalization()(x + ffn_output)
    x = layers.Dropout(dropout_rate)(x)
    
    # Global pooling and output
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dense(64, activation='relu')(x)
    x = layers.Dropout(dropout_rate)(x)
    outputs = layers.Dense(output_dim)(x)
    
    model = keras.Model(inputs=inputs, outputs=outputs)
    return model


def train_attention_model(
    data_path: Path,
    horizon: str,
    model_dir: Path,
    time_steps=128,  # Can go up to 256 but 128 is safer
    batch_size=16,  # Must be ≤16 for memory
    epochs=50,
    d_model=256,
    num_heads=4
):
    """Train attention model."""
    import pandas as pd
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    
    print(f"\n--- Training Attention Model for {horizon} horizon ---")
    print(f"Architecture: d_model={d_model}, heads={num_heads}, batch_size={batch_size}")
    
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
        
        print(f"Training sequences: {X_train.shape[0]}, Validation: {X_val.shape[0]}")
        
        model = build_attention_model(
            input_shape=(time_steps, len(feature_cols)),
            d_model=d_model,
            num_heads=num_heads
        )
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.0001),  # Lower LR for attention
            loss='mean_squared_error',
            metrics=['mae']
        )
        
        print(f"\nModel summary:")
        model.summary()
        
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
        
        output_path = model_dir / f"attention_{horizon}"
        model.save(output_path)
        
        import joblib
        joblib.dump(scaler, model_dir / f"attention_{horizon}_scaler.pkl")
        
        print(f"✅ Attention model saved to {output_path}")
        
        val_loss, val_mae = model.evaluate(X_val, y_val, verbose=0)
        print(f"Validation MAE: {val_mae:.4f}")
        
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
            print("✅ Metal GPU configured")
    except:
        print("⚠️ Running on CPU")
    
    train_attention_model(
        data_path=data_path,
        horizon=args.horizon,
        model_dir=model_dir,
        time_steps=args.time_steps,
        batch_size=args.batch_size,
        epochs=args.epochs,
        d_model=args.d_model,
        num_heads=args.num_heads
    )

