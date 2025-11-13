#!/usr/bin/env python3
"""
Train baseline tree-based models (LightGBM, XGBoost) on exported Parquet data.
"""
import argparse
import pandas as pd
import lightgbm as lgb
import xgboost as xgb
from sklearn.model_selection import train_test_split
import joblib
from pathlib import Path

def get_repo_root():
    """Find the repository root by looking for a marker file."""
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / "QUICK_REFERENCE.txt").exists():
            return parent
    raise FileNotFoundError("Repository root not found.")

def train_lightgbm(data_path: Path, horizon: str, model_dir: Path):
    """Trains and saves a LightGBM DART model."""
    print(f"\n--- Training LightGBM DART for {horizon} horizon ---")
    try:
        df = pd.read_parquet(data_path)
        
        # Simple feature selection: use numeric types, exclude identifiers/targets
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        feature_cols = [col for col in numeric_cols if 'target' not in col and 'price' not in col]
        target_col = 'zl_price_current'
        
        X = df[feature_cols]
        y = df[target_col]
        
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, shuffle=False)
        
        model = lgb.LGBMRegressor(
            boosting_type='dart',
            num_leaves=31,
            learning_rate=0.05,
            n_estimators=1000,
            objective='regression_l1',
            n_jobs=-1,
            random_state=42
        )
        
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(period=200)]
        )
        
        output_path = model_dir / f"lightgbm_dart_{horizon}.pkl"
        joblib.dump(model, output_path)
        print(f"✅ LightGBM DART model for {horizon} saved to {output_path}")
    except Exception as e:
        print(f"❌ Failed to train LightGBM for {horizon}: {e}")

def train_xgboost(data_path: Path, horizon: str, model_dir: Path):
    """Trains and saves an XGBoost DART model."""
    print(f"\n--- Training XGBoost DART for {horizon} horizon ---")
    try:
        df = pd.read_parquet(data_path)
        
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        feature_cols = [col for col in numeric_cols if 'target' not in col and 'price' not in col]
        target_col = 'zl_price_current'

        X = df[feature_cols]
        y = df[target_col]
        
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, shuffle=False)

        model = xgb.XGBRegressor(
            booster='dart',
            objective='reg:squarederror',
            eval_metric='mae',
            learning_rate=0.05,
            n_estimators=1000,
            n_jobs=-1,
            random_state=42
        )

        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            early_stopping_rounds=50,
            verbose=False
        )

        output_path = model_dir / f"xgboost_dart_{horizon}.pkl"
        joblib.dump(model, output_path)
        print(f"✅ XGBoost DART model for {horizon} saved to {output_path}")
    except Exception as e:
        print(f"❌ Failed to train XGBoost for {horizon}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Train baseline tree-based models.")
    parser.add_argument("--horizon", required=True, help="Forecast horizon (e.g., 1w, 1m).")
    parser.add_argument("--model", choices=['lightgbm', 'xgboost', 'all'], default='all', help="Model to train.")
    
    args = parser.parse_args()
    
    repo_root = get_repo_root()
    data_path = repo_root / f"TrainingData/exports/production_training_data_{args.horizon}.parquet"
    model_dir = repo_root / "Models/local/baselines"
    model_dir.mkdir(parents=True, exist_ok=True)

    if not data_path.exists():
        print(f"❌ Data file not found at: {data_path}")
        return

    print(f"Found data for {args.horizon} horizon at {data_path}")

    if args.model in ['lightgbm', 'all']:
        train_lightgbm(data_path, args.horizon, model_dir)
        
    if args.model in ['xgboost', 'all']:
        train_xgboost(data_path, args.horizon, model_dir)
        
    print("\n--- Tree-based baseline training complete! ---")

if __name__ == "__main__":
    main()
