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
import sys
from datetime import datetime

# Add parent directory to path for feature catalog
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from training.features.feature_catalog import FeatureCatalog
from training.utils.model_saver import save_model_with_metadata

def get_repo_root():
    """Find the repository root by looking for a marker file."""
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / "QUICK_REFERENCE.txt").exists():
            return parent
    raise FileNotFoundError("Repository root not found.")

def train_lightgbm(data_path: Path, horizon: str, model_dir: Path):
    """Trains and saves a LightGBM DART model using ALL available features."""
    print(f"\n--- Training LightGBM DART for {horizon} horizon ---")
    try:
        df = pd.read_parquet(data_path)
        
        # Use comprehensive feature catalog - ALL features except targets
        available_cols = set(df.columns)
        feature_cols = FeatureCatalog.get_features_for_model('tree')
        
        # Filter to only features that exist in dataset
        feature_cols = [col for col in feature_cols if col in available_cols]
        
        # Fallback: if catalog features missing, use all numeric except targets
        if len(feature_cols) < 100:
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            feature_cols = [col for col in numeric_cols if col not in FeatureCatalog.EXCLUDED]
        
        print(f"Using {len(feature_cols)} features")
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
        
        # Log feature importance
        feature_importance = pd.DataFrame({
            'feature': feature_cols,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print(f"\nTop 10 features by importance:")
        print(feature_importance.head(10).to_string(index=False))
        
        # Save model with metadata using utility
        model_subdir = save_model_with_metadata(
            model=model,
            model_dir=model_dir,
            model_name="lightgbm_dart",
            feature_cols=feature_cols,
            feature_importance=feature_importance,
            training_config={
                'boosting_type': 'dart',
                'num_leaves': 31,
                'learning_rate': 0.05,
                'n_estimators': model.n_estimators_,
                'horizon': horizon
            },
            metrics={
                'train_mape': train_mape,
                'val_mape': val_mape,
                'n_estimators_used': model.n_estimators_
            },
            model_type="lightgbm"
        )
        
        print(f"✅ LightGBM DART model for {horizon} saved to {model_subdir}")
        print(f"✅ All metadata files saved")
    except Exception as e:
        print(f"❌ Failed to train LightGBM for {horizon}: {e}")

def train_xgboost(data_path: Path, horizon: str, model_dir: Path):
    """Trains and saves an XGBoost DART model using ALL available features."""
    print(f"\n--- Training XGBoost DART for {horizon} horizon ---")
    try:
        df = pd.read_parquet(data_path)
        
        # Use comprehensive feature catalog - ALL features except targets
        available_cols = set(df.columns)
        feature_cols = FeatureCatalog.get_features_for_model('tree')
        
        # Filter to only features that exist in dataset
        feature_cols = [col for col in feature_cols if col in available_cols]
        
        # Fallback: if catalog features missing, use all numeric except targets
        if len(feature_cols) < 100:
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            feature_cols = [col for col in numeric_cols if col not in FeatureCatalog.EXCLUDED]
        
        print(f"Using {len(feature_cols)} features")
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
        
        # Log feature importance
        feature_importance = pd.DataFrame({
            'feature': feature_cols,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print(f"\nTop 10 features by importance:")
        print(feature_importance.head(10).to_string(index=False))
        
        # Save model with metadata using utility
        model_subdir = save_model_with_metadata(
            model=model,
            model_dir=model_dir,
            model_name="xgboost_dart",
            feature_cols=feature_cols,
            feature_importance=feature_importance,
            training_config={
                'booster': 'dart',
                'max_depth': 8,
                'learning_rate': 0.03,
                'n_estimators': model.best_iteration if hasattr(model, 'best_iteration') else 1000,
                'horizon': horizon
            },
            metrics={
                'train_mape': train_mape,
                'val_mape': val_mape,
                'best_iteration': model.best_iteration if hasattr(model, 'best_iteration') else None
            },
            model_type="xgboost"
        )
        
        print(f"✅ XGBoost DART model for {horizon} saved to {model_subdir}")
        print(f"✅ All metadata files saved")
    except Exception as e:
        print(f"❌ Failed to train XGBoost for {horizon}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Train baseline tree-based models.")
    parser.add_argument("--horizon", required=True, help="Forecast horizon (e.g., 1w, 1m).")
    parser.add_argument("--model", choices=['lightgbm', 'xgboost', 'all'], default='all', help="Model to train.")
    parser.add_argument(
        "--data-path",
        help="Optional Parquet dataset path. Overrides default TrainingData/exports location."
    )
    
    args = parser.parse_args()
    
    repo_root = get_repo_root()
    # New naming: zl_training_{surface}_allhistory_{horizon}.parquet
    surface = getattr(args, 'surface', 'prod')  # Default to prod surface
    data_path = Path(args.data_path).expanduser() if args.data_path else repo_root / f"TrainingData/exports/zl_training_{surface}_allhistory_{args.horizon}.parquet"
    # New model path: Models/local/horizon_{h}/{surface}/{family}/{model}_v{ver}/
    model_dir = repo_root / f"Models/local/horizon_{args.horizon}/{surface}/baselines"
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
