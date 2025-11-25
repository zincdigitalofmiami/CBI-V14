#!/usr/bin/env python3
"""
Generate predictions using locally trained models (NO Vertex AI needed).
Loads models from Models/local/ and generates predictions for all horizons.
"""
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
import sys
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from training.features.feature_catalog import FeatureCatalog


def get_repo_root():
    """Find repository root."""
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / "QUICK_REFERENCE.txt").exists() or (parent / ".git").exists():
            return parent
    raise FileNotFoundError("Repository root not found")


def load_local_model(model_path: Path, model_type: str):
    """Load a locally trained model."""
    if not model_path.exists():
        return None
    
    try:
        if model_type in ['lightgbm', 'xgboost', 'regime_ensemble']:
            return joblib.load(model_path)
        elif model_type in ['lstm', 'gru', 'tcn', 'cnn_lstm', 'attention', 'transformer']:
            import tensorflow as tf
            return tf.keras.models.load_model(str(model_path))
        else:
            return joblib.load(model_path)
    except Exception as e:
        print(f"⚠️  Could not load {model_path}: {e}")
        return None


def prepare_features(df: pd.DataFrame, feature_cols: list, scaler_path: Path = None):
    """Prepare features for prediction."""
    # Select features
    X = df[feature_cols].fillna(0)
    
    # Apply scaler if provided (for neural models)
    if scaler_path and scaler_path.exists():
        scaler = joblib.load(scaler_path)
        X_scaled = pd.DataFrame(
            scaler.transform(X),
            columns=feature_cols,
            index=X.index
        )
        return X, X_scaled
    
    return X, None


def predict_with_tree_model(model, X: pd.DataFrame):
    """Predict using tree-based model (LightGBM, XGBoost)."""
    return model.predict(X.iloc[-1:].values)[0]


def predict_with_neural_model(model, X_scaled: pd.DataFrame, time_steps: int = 30):
    """Predict using neural model (LSTM, GRU, TCN, etc.)."""
    import tensorflow as tf
    
    # Create sequence
    if len(X_scaled) < time_steps:
        # Pad with last values if not enough history
        padding = pd.concat([X_scaled.iloc[-1:]] * (time_steps - len(X_scaled)))
        sequence = pd.concat([padding, X_scaled]).values
    else:
        sequence = X_scaled.iloc[-time_steps:].values
    
    # Reshape for model input: (1, time_steps, num_features)
    sequence = sequence.reshape(1, time_steps, sequence.shape[1])
    
    # Predict
    prediction = model.predict(sequence, verbose=0)[0][0]
    return float(prediction)


def generate_local_predictions(
    horizon: str = 'all',
    data_path: Path = None,
    model_dir: Path = None
):
    """
    Generate predictions using locally trained models.
    
    Args:
        horizon: 'all', '1w', '1m', '3m', '6m', '12m'
        data_path: Path to latest training data (for features)
        model_dir: Directory with trained models
    """
    repo_root = get_repo_root()
    
    if data_path is None:
        # Use latest training data export (new naming)
        surface = getattr(args, 'surface', 'prod') if hasattr(args, 'surface') else 'prod'
        horizon = getattr(args, 'horizon', '1m') if hasattr(args, 'horizon') else '1m'
        data_path = repo_root / f"TrainingData/exports/zl_training_{surface}_allhistory_{horizon}.parquet"
    
    if model_dir is None:
        model_dir = repo_root / "Models/local"
    
    print("="*80)
    print("🔮 LOCAL PREDICTION GENERATION (No Vertex AI)")
    print("="*80)
    print(f"Data: {data_path}")
    print(f"Models: {model_dir}")
    print()
    
    # Load latest data
    if not data_path.exists():
        print(f"❌ Data file not found: {data_path}")
        return None
    
    df = pd.read_parquet(data_path)
    print(f"✅ Loaded data: {len(df)} rows, latest date: {df['date'].max() if 'date' in df.columns else 'N/A'}")
    
    # Get features
    available_cols = set(df.columns)
    feature_cols = FeatureCatalog.get_features_for_model('tree')
    feature_cols = [col for col in feature_cols if col in available_cols]
    
    if len(feature_cols) < 100:
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        feature_cols = [col for col in numeric_cols if col not in FeatureCatalog.EXCLUDED]
    
    print(f"✅ Using {len(feature_cols)} features")
    
    # Prepare features
    X, X_scaled = prepare_features(df, feature_cols)
    
    # Models to try (in order of preference)
    horizons_to_check = ['1w', '1m', '3m', '6m', '12m'] if horizon == 'all' else [horizon]
    
    predictions = {}
    
    for hz in horizons_to_check:
        print(f"\n{'='*60}")
        print(f"  {hz.upper()} HORIZON")
        print(f"{'='*60}")
        
        hz_predictions = {}
        
        # Try ensemble first (best)
        ensemble_path = model_dir / "ensemble" / f"regime_ensemble_{hz}.pkl"
        if ensemble_path.exists():
            print(f"  Trying regime ensemble...")
            model = load_local_model(ensemble_path, 'regime_ensemble')
            if model:
                try:
                    pred = predict_with_tree_model(model, X)
                    hz_predictions['ensemble'] = pred
                    print(f"    ✅ Ensemble: ${pred:.2f}")
                except Exception as e:
                    print(f"    ❌ Ensemble failed: {e}")
        
        # Try LightGBM
        lgbm_path = model_dir / "baselines" / f"lightgbm_dart_{hz}.pkl"
        if lgbm_path.exists():
            print(f"  Trying LightGBM...")
            model = load_local_model(lgbm_path, 'lightgbm')
            if model:
                try:
                    pred = predict_with_tree_model(model, X)
                    hz_predictions['lightgbm'] = pred
                    print(f"    ✅ LightGBM: ${pred:.2f}")
                except Exception as e:
                    print(f"    ❌ LightGBM failed: {e}")
        
        # Try XGBoost
        xgb_path = model_dir / "baselines" / f"xgboost_dart_{hz}.pkl"
        if xgb_path.exists():
            print(f"  Trying XGBoost...")
            model = load_local_model(xgb_path, 'xgboost')
            if model:
                try:
                    pred = predict_with_tree_model(model, X)
                    hz_predictions['xgboost'] = pred
                    print(f"    ✅ XGBoost: ${pred:.2f}")
                except Exception as e:
                    print(f"    ❌ XGBoost failed: {e}")
        
        # Try neural models (if X_scaled available)
        if X_scaled is not None:
            neural_models = [
                ('lstm', model_dir / "baselines" / f"simple_lstm_{hz}"),
                ('tcn', model_dir / "advanced" / f"tcn_{hz}"),
                ('attention', model_dir / "advanced" / f"attention_{hz}"),
            ]
            
            for name, model_path in neural_models:
                if model_path.exists():
                    print(f"  Trying {name.upper()}...")
                    model = load_local_model(model_path, name)
                    scaler_path = model_path.parent / f"{model_path.name}_scaler.pkl"
                    
                    if model:
                        try:
                            # Re-prepare with scaler
                            _, X_scaled_neural = prepare_features(df, feature_cols, scaler_path)
                            if X_scaled_neural is not None:
                                pred = predict_with_neural_model(model, X_scaled_neural)
                                hz_predictions[name] = pred
                                print(f"    ✅ {name.upper()}: ${pred:.2f}")
                        except Exception as e:
                            print(f"    ❌ {name.upper()} failed: {e}")
        
        if hz_predictions:
            # Use ensemble if available, otherwise best tree model
            if 'ensemble' in hz_predictions:
                predictions[hz] = {
                    'value': hz_predictions['ensemble'],
                    'model': 'ensemble',
                    'all_models': hz_predictions
                }
            elif 'lightgbm' in hz_predictions:
                predictions[hz] = {
                    'value': hz_predictions['lightgbm'],
                    'model': 'lightgbm',
                    'all_models': hz_predictions
                }
            elif 'xgboost' in hz_predictions:
                predictions[hz] = {
                    'value': hz_predictions['xgboost'],
                    'model': 'xgboost',
                    'all_models': hz_predictions
                }
            else:
                # Use first available
                first_model = list(hz_predictions.keys())[0]
                predictions[hz] = {
                    'value': hz_predictions[first_model],
                    'model': first_model,
                    'all_models': hz_predictions
                }
        else:
            print(f"    ⚠️  No models found for {hz}")
    
    # Print summary
    print(f"\n{'='*80}")
    print("📊 PREDICTION SUMMARY")
    print(f"{'='*80}")
    
    if predictions:
        for hz, pred_info in predictions.items():
            print(f"{hz.upper():6s}: ${pred_info['value']:8.2f} (model: {pred_info['model']})")
            if len(pred_info['all_models']) > 1:
                print(f"         Other models: {', '.join([f'{k}: ${v:.2f}' for k, v in pred_info['all_models'].items() if k != pred_info['model']])}")
        
        print(f"\n✅ Generated {len(predictions)} predictions locally (NO Vertex AI)")
    else:
        print("❌ No predictions generated - train models first!")
    
    return predictions


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate predictions using local models")
    parser.add_argument("--horizon", default="all", choices=['all', '1w', '1m', '3m', '6m', '12m'])
    parser.add_argument("--data-path", help="Path to training data")
    parser.add_argument("--model-dir", help="Directory with trained models")
    
    args = parser.parse_args()
    
    predictions = generate_local_predictions(
        horizon=args.horizon,
        data_path=Path(args.data_path).expanduser() if args.data_path else None,
        model_dir=Path(args.model_dir).expanduser() if args.model_dir else None
    )

