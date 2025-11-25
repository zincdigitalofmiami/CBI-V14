#!/usr/bin/env python3
"""
Regime-Aware Ensemble Meta-Learner.
Combines predictions from all base models with regime-aware weighting.
Crisis = weight 1W models more, Calm = weight 6M models more.
"""
import pandas as pd
import numpy as np
import lightgbm as lgb
from pathlib import Path
import joblib
import sys
import glob

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from training.features.feature_catalog import FeatureCatalog


def collect_base_model_predictions(
    data_path: Path,
    model_dir: Path,
    horizon: str
):
    """
    Collect out-of-fold predictions from all base models.
    
    Returns:
        DataFrame with columns: [pred_lgbm, pred_xgb, pred_lstm, pred_gru, pred_tcn, ...]
    """
    predictions = {}
    
    # Load models and generate predictions
    model_files = {
        'lightgbm': model_dir.parent / 'baselines' / f'lightgbm_dart_{horizon}.pkl',
        'xgboost': model_dir.parent / 'baselines' / f'xgboost_dart_{horizon}.pkl',
        'lstm': model_dir.parent / 'baselines' / f'simple_lstm_{horizon}',
        'gru': model_dir.parent / 'baselines' / f'simple_gru_{horizon}',
        'tcn': model_dir.parent / 'advanced' / f'tcn_{horizon}',
        'cnn_lstm': model_dir.parent / 'advanced' / f'cnn_lstm_{horizon}',
        'lstm_2layer': model_dir.parent / 'advanced' / f'lstm_2layer_{horizon}',
        'attention': model_dir.parent / 'advanced' / f'attention_{horizon}',
    }
    
    df = pd.read_parquet(data_path)
    available_cols = set(df.columns)
    feature_cols = FeatureCatalog.get_features_for_model('tree')
    feature_cols = [col for col in feature_cols if col in available_cols]
    
    if len(feature_cols) < 100:
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        feature_cols = [col for col in numeric_cols if col not in FeatureCatalog.EXCLUDED]
    
    X = df[feature_cols].fillna(0)
    
    # Tree models
    for name, model_path in model_files.items():
        if 'lightgbm' in name or 'xgboost' in name:
            if model_path.exists():
                try:
                    model = joblib.load(model_path)
                    pred = model.predict(X)
                    predictions[f'pred_{name}'] = pred
                    print(f"✅ Loaded {name} predictions")
                except Exception as e:
                    print(f"⚠️  Could not load {name}: {e}")
    
    # Neural models (would need to load scalers and create sequences)
    # For now, skip if not available
    
    if len(predictions) == 0:
        print("⚠️  No base model predictions found. Train base models first.")
        return None
    
    return pd.DataFrame(predictions)


def train_regime_ensemble(
    data_path: Path,
    model_dir: Path,
    horizon: str,
    regime_classifier_path: Path = None
):
    """
    Train regime-aware ensemble meta-learner.
    
    Args:
        data_path: Training data path
        model_dir: Directory with base models
        horizon: Forecast horizon
        regime_classifier_path: Path to regime classifier
    """
    print(f"\n--- Training Regime-Aware Ensemble for {horizon} horizon ---")
    
    try:
        df = pd.read_parquet(data_path)
        target_col = 'zl_price_current'
        y = df[target_col].values
        
        # Collect base model predictions
        print("Collecting base model predictions...")
        base_predictions = collect_base_model_predictions(data_path, model_dir, horizon)
        
        if base_predictions is None or len(base_predictions.columns) < 2:
            print("❌ Need at least 2 base models. Train base models first.")
            return None
        
        # Get regime labels if classifier available
        regime_context = None
        if regime_classifier_path and regime_classifier_path.exists():
            try:
                regime_classifier = joblib.load(regime_classifier_path)
                available_cols = set(df.columns)
                feature_cols = FeatureCatalog.get_features_for_model('tree')
                feature_cols = [col for col in feature_cols if col in available_cols]
                
                if len(feature_cols) < 100:
                    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
                    feature_cols = [col for col in numeric_cols if col not in FeatureCatalog.EXCLUDED]
                
                X_features = df[feature_cols].fillna(0)
                regime_predictions = regime_classifier.predict(X_features)
                regime_probs = regime_classifier.predict_proba(X_features)
                
                # Add regime features
                regime_context = pd.DataFrame({
                    'regime': regime_predictions,
                    'prob_crisis': regime_probs[:, 0] if regime_probs.shape[1] > 0 else 0,
                    'prob_bull': regime_probs[:, 1] if regime_probs.shape[1] > 1 else 0,
                    'prob_bear': regime_probs[:, 2] if regime_probs.shape[1] > 2 else 0,
                    'prob_normal': regime_probs[:, 3] if regime_probs.shape[1] > 3 else 0,
                })
                
                print("✅ Added regime context")
            except Exception as e:
                print(f"⚠️  Could not load regime classifier: {e}")
        
        # Combine base predictions with regime context
        meta_features = base_predictions.copy()
        if regime_context is not None:
            # One-hot encode regime
            regime_dummies = pd.get_dummies(regime_context['regime'], prefix='regime')
            meta_features = pd.concat([meta_features, regime_dummies], axis=1)
            meta_features = pd.concat([meta_features, regime_context[['prob_crisis', 'prob_bull', 'prob_bear', 'prob_normal']]], axis=1)
        
        # Train/test split
        split_idx = int(len(meta_features) * 0.8)
        X_train, X_test = meta_features.iloc[:split_idx], meta_features.iloc[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Train meta-learner
        print(f"Training meta-learner on {len(X_train)} samples with {len(X_train.columns)} features...")
        meta_learner = lgb.LGBMRegressor(
            boosting_type='dart',
            num_leaves=31,
            learning_rate=0.05,
            n_estimators=1000,
            objective='regression_l1',
            n_jobs=-1,
            random_state=42
        )
        
        meta_learner.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            callbacks=[
                lgb.early_stopping(50, verbose=False),
                lgb.log_evaluation(period=200)
            ]
        )
        
        # Evaluate
        train_pred = meta_learner.predict(X_train)
        test_pred = meta_learner.predict(X_test)
        
        train_mae = np.mean(np.abs(train_pred - y_train))
        test_mae = np.mean(np.abs(test_pred - y_test))
        
        print(f"\nMeta-learner performance:")
        print(f"  Training MAE: {train_mae:.4f}")
        print(f"  Test MAE: {test_mae:.4f}")
        
        # Compare to best base model
        base_maes = {}
        for col in base_predictions.columns:
            base_maes[col] = np.mean(np.abs(base_predictions[col].iloc[split_idx:] - y_test))
        
        best_base_mae = min(base_maes.values())
        best_base_name = min(base_maes, key=base_maes.get)
        
        print(f"\nBest base model: {best_base_name} (MAE: {best_base_mae:.4f})")
        improvement = (best_base_mae - test_mae) / best_base_mae * 100
        print(f"Ensemble improvement: {improvement:.2f}%")
        
        if test_mae < best_base_mae:
            print(f"✅ Ensemble beats best base model!")
        else:
            print(f"⚠️  Ensemble does not beat best base model")
        
        # Save model
        output_path = model_dir / f"regime_ensemble_{horizon}.pkl"
        joblib.dump(meta_learner, output_path)
        
        # Save feature importance
        importance = pd.DataFrame({
            'feature': meta_features.columns,
            'importance': meta_learner.feature_importances_
        }).sort_values('importance', ascending=False)
        
        importance_path = model_dir / f"regime_ensemble_{horizon}_importance.csv"
        importance.to_csv(importance_path, index=False)
        
        print(f"\n✅ Regime ensemble saved to {output_path}")
        print(f"✅ Feature importance saved to {importance_path}")
        
        return meta_learner
        
    except Exception as e:
        print(f"❌ Failed to train regime ensemble: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--horizon", required=True)
    parser.add_argument("--data-path")
    parser.add_argument("--regime-classifier")
    
    args = parser.parse_args()
    
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
    model_dir = repo_root / f"Models/local/horizon_{args.horizon}/{surface}/ensemble"
    regime_classifier_path = Path(args.regime_classifier).expanduser() if args.regime_classifier else repo_root / f"Models/local/horizon_{args.horizon}/{surface}/regime/regime_classifier.pkl"
    
    train_regime_ensemble(
        data_path=data_path,
        model_dir=model_dir,
        horizon=args.horizon,
        regime_classifier_path=regime_classifier_path
    )

