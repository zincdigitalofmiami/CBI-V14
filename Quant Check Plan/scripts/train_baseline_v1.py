"""
ZL v1 Baseline Training - LightGBM
Trains a simple LightGBM model on the ZL feature data.

This is the FIRST BASELINE to prove the pipeline works.
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')

# Config
PROJECT = 'cbi-v14'
TRAINING_VIEW = f'{PROJECT}.training.vw_zl_1m_v1'

def load_training_data():
    """Load training data from BigQuery."""
    client = bigquery.Client(project=PROJECT)
    
    query = f"""
        SELECT *
        FROM `{TRAINING_VIEW}`
        WHERE target_1m IS NOT NULL
        ORDER BY trade_date
    """
    
    df = client.query(query).to_dataframe()
    return df

def prepare_features(df):
    """Prepare feature matrix and targets."""
    feature_cols = [
        'return_1d', 'return_5d', 'return_21d',
        'ma_5', 'ma_21', 'ma_63',
        'volatility_21d', 'rsi_14',
        'close'
    ]
    
    # Create train/val/test splits
    train_df = df[df['split'] == 'train'].copy()
    val_df = df[df['split'] == 'val'].copy()
    test_df = df[df['split'] == 'test'].copy()
    
    X_train = train_df[feature_cols]
    y_train = train_df['target_1m']
    w_train = train_df['sample_weight']
    
    X_val = val_df[feature_cols]
    y_val = val_df['target_1m']
    
    X_test = test_df[feature_cols]
    y_test = test_df['target_1m']
    
    return X_train, y_train, w_train, X_val, y_val, X_test, y_test, test_df

def train_model(X_train, y_train, w_train, X_val, y_val):
    """Train LightGBM model."""
    
    # Create datasets
    train_data = lgb.Dataset(X_train, label=y_train, weight=w_train)
    val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
    
    # Parameters (conservative for baseline)
    params = {
        'objective': 'regression',
        'metric': 'mae',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.9,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1,
        'seed': 42
    }
    
    # Train with early stopping
    model = lgb.train(
        params,
        train_data,
        num_boost_round=1000,
        valid_sets=[train_data, val_data],
        valid_names=['train', 'val'],
        callbacks=[
            lgb.early_stopping(stopping_rounds=50),
            lgb.log_evaluation(period=100)
        ]
    )
    
    return model

def evaluate_model(model, X_test, y_test, test_df):
    """Evaluate model on test set."""
    
    y_pred = model.predict(X_test)
    
    # Metrics
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    # Direction accuracy
    actual_direction = (y_test > 0).astype(int)
    pred_direction = (y_pred > 0).astype(int)
    direction_acc = (actual_direction == pred_direction).mean()
    
    # By regime
    print("\n" + "=" * 60)
    print("TEST SET RESULTS")
    print("=" * 60)
    print(f"\nOverall Metrics:")
    print(f"  MAE:  {mae:.4f} ({mae*100:.2f}%)")
    print(f"  RMSE: {rmse:.4f} ({rmse*100:.2f}%)")
    print(f"  R²:   {r2:.4f}")
    print(f"  Direction Accuracy: {direction_acc:.1%}")
    
    # Feature importance
    print("\nFeature Importance:")
    importance = pd.DataFrame({
        'feature': model.feature_name(),
        'importance': model.feature_importance('gain')
    }).sort_values('importance', ascending=False)
    print(importance.to_string(index=False))
    
    # By regime
    print("\nBy Regime:")
    test_df = test_df.copy()
    test_df['y_pred'] = y_pred
    for regime in test_df['regime_name'].unique():
        regime_df = test_df[test_df['regime_name'] == regime]
        regime_mae = mean_absolute_error(regime_df['target_1m'], regime_df['y_pred'])
        regime_dir = ((regime_df['target_1m'] > 0) == (regime_df['y_pred'] > 0)).mean()
        print(f"  {regime}: MAE={regime_mae:.4f}, Dir={regime_dir:.1%}, N={len(regime_df)}")
    
    return {
        'mae': mae,
        'rmse': rmse,
        'r2': r2,
        'direction_accuracy': direction_acc
    }

def main():
    print("=" * 60)
    print("ZL v1 BASELINE TRAINING")
    print("=" * 60)
    
    # 1. Load data
    print("\n1. Loading training data from BigQuery...")
    df = load_training_data()
    print(f"   Loaded {len(df)} rows")
    print(f"   Date range: {df['trade_date'].min()} to {df['trade_date'].max()}")
    
    # 2. Prepare features
    print("\n2. Preparing features...")
    X_train, y_train, w_train, X_val, y_val, X_test, y_test, test_df = prepare_features(df)
    print(f"   Train: {len(X_train)} rows")
    print(f"   Val:   {len(X_val)} rows")
    print(f"   Test:  {len(X_test)} rows")
    
    # 3. Train model
    print("\n3. Training LightGBM model...")
    model = train_model(X_train, y_train, w_train, X_val, y_val)
    print(f"   Best iteration: {model.best_iteration}")
    
    # 4. Evaluate
    print("\n4. Evaluating on test set...")
    metrics = evaluate_model(model, X_test, y_test, test_df)
    
    # 5. Save model
    model_path = 'Quant Check Plan/models/zl_baseline_v1.txt'
    model.save_model(model_path)
    print(f"\n✅ Model saved to {model_path}")
    
    print("\n" + "=" * 60)
    print("BASELINE COMPLETE")
    print("=" * 60)
    
    return metrics

if __name__ == '__main__':
    main()





