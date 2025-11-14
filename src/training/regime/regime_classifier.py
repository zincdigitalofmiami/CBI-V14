#!/usr/bin/env python3
"""
Regime Classifier: Detects Crisis/Bull/Bear/Normal market regimes.
Uses LightGBM for fast, accurate classification (>95% target accuracy).
"""
import pandas as pd
import numpy as np
import lightgbm as lgb
from pathlib import Path
import joblib
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from training.features.feature_catalog import FeatureCatalog


def create_regime_labels(df):
    """
    Create regime labels based on market conditions.
    
    Regimes:
    - Crisis: VIX > 30 OR extreme volatility OR major drawdown
    - Bull: Strong uptrend, low volatility, positive momentum
    - Bear: Downtrend, high volatility, negative momentum
    - Normal: Everything else
    """
    labels = []
    
    for idx, row in df.iterrows():
        # Get volatility and price features
        vix = row.get('vix_level', row.get('vix_index_new', row.get('vix_yahoo_close', 20)))
        volatility = row.get('volatility_30d', row.get('historical_volatility_30d', 0.15))
        return_30d = row.get('return_7d', 0) * 4.3  # Approximate 30d return
        
        # Crisis: High VIX or extreme volatility
        if vix > 30 or volatility > 0.4:
            labels.append('crisis')
        # Bull: Strong positive momentum, low volatility
        elif return_30d > 0.1 and volatility < 0.25:
            labels.append('bull')
        # Bear: Negative momentum, high volatility
        elif return_30d < -0.1 or (volatility > 0.3 and return_30d < 0):
            labels.append('bear')
        # Normal: Everything else
        else:
            labels.append('normal')
    
    return np.array(labels)


def train_regime_classifier(
    data_path: Path,
    model_dir: Path,
    target_accuracy=0.95
):
    """
    Train regime classifier.
    
    Args:
        data_path: Path to training data
        model_dir: Directory to save model
        target_accuracy: Target accuracy (>0.95)
    """
    print("\n--- Training Regime Classifier ---")
    
    try:
        df = pd.read_parquet(data_path)
        
        # Create regime labels
        print("Creating regime labels...")
        y_regime = create_regime_labels(df)
        
        # Get features
        available_cols = set(df.columns)
        feature_cols = FeatureCatalog.get_features_for_model('tree')
        feature_cols = [col for col in feature_cols if col in available_cols]
        
        if len(feature_cols) < 100:
            numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
            feature_cols = [col for col in numeric_cols if col not in FeatureCatalog.EXCLUDED]
        
        print(f"Using {len(feature_cols)} features")
        
        X = df[feature_cols].fillna(0)
        
        # Train/test split
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y_regime[:split_idx], y_regime[split_idx:]
        
        # Train classifier
        print("Training LightGBM classifier...")
        classifier = lgb.LGBMClassifier(
            objective='multiclass',
            num_class=4,
            boosting_type='dart',
            num_leaves=31,
            learning_rate=0.05,
            n_estimators=1000,
            n_jobs=-1,
            random_state=42
        )
        
        classifier.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            callbacks=[
                lgb.early_stopping(50, verbose=False),
                lgb.log_evaluation(period=100)
            ]
        )
        
        # Evaluate
        train_acc = classifier.score(X_train, y_train)
        test_acc = classifier.score(X_test, y_test)
        
        print(f"\nTraining Accuracy: {train_acc:.4f}")
        print(f"Test Accuracy: {test_acc:.4f}")
        
        if test_acc < target_accuracy:
            print(f"⚠️  Accuracy {test_acc:.4f} below target {target_accuracy}")
        else:
            print(f"✅ Accuracy {test_acc:.4f} meets target {target_accuracy}")
        
        # Save model
        output_path = model_dir / "regime_classifier.pkl"
        joblib.dump(classifier, output_path)
        
        # Save feature importance
        importance = pd.DataFrame({
            'feature': feature_cols,
            'importance': classifier.feature_importances_
        }).sort_values('importance', ascending=False)
        
        importance_path = model_dir / "regime_classifier_importance.csv"
        importance.to_csv(importance_path, index=False)
        
        print(f"\n✅ Regime classifier saved to {output_path}")
        print(f"✅ Feature importance saved to {importance_path}")
        
        # Print regime distribution
        print("\nRegime distribution:")
        regime_counts = pd.Series(y_regime).value_counts()
        for regime, count in regime_counts.items():
            pct = count / len(y_regime) * 100
            print(f"  {regime}: {count} ({pct:.1f}%)")
        
        return classifier
        
    except Exception as e:
        print(f"❌ Failed to train regime classifier: {e}")
        import traceback
        traceback.print_exc()
        return None


def predict_regime(classifier, X):
    """Predict regime for given features."""
    if classifier is None:
        return 'normal'  # Default
    
    predictions = classifier.predict(X)
    probabilities = classifier.predict_proba(X)
    
    return predictions, probabilities


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", help="Path to training data")
    parser.add_argument("--horizon", default="1m", help="Horizon for data file")
    
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
    model_dir = repo_root / f"Models/local/horizon_{args.horizon}/{surface}/regime"
    model_dir.mkdir(parents=True, exist_ok=True)
    
    train_regime_classifier(
        data_path=data_path,
        model_dir=model_dir
    )

