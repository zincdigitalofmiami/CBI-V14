"""
Model saving utilities for consistent model artifact management.
Ensures all models save metadata files in the new naming structure.
"""
from pathlib import Path
from datetime import datetime
import json
import pandas as pd
import joblib
from typing import Dict, List, Optional, Any

def save_model_with_metadata(
    model: Any,
    model_dir: Path,
    model_name: str,
    version: str = "v001",
    feature_cols: Optional[List[str]] = None,
    feature_importance: Optional[pd.DataFrame] = None,
    training_config: Optional[Dict] = None,
    metrics: Optional[Dict] = None,
    model_type: str = "sklearn"  # sklearn, tensorflow, lightgbm, xgboost
) -> Path:
    """
    Save model with all required metadata files.
    
    Args:
        model: Trained model object
        model_dir: Base directory (e.g., Models/local/horizon_1m/prod/baselines)
        model_name: Model name (e.g., lightgbm_dart)
        version: Version string (e.g., v001)
        feature_cols: List of feature column names used
        feature_importance: DataFrame with feature importance
        training_config: Dictionary of training hyperparameters
        metrics: Dictionary of evaluation metrics
        model_type: Type of model (determines save format)
    
    Returns:
        Path to model subdirectory
    """
    # Create version directory
    model_subdir = model_dir / f"{model_name}_{version}"
    model_subdir.mkdir(parents=True, exist_ok=True)
    
    # Save model based on type
    if model_type == "sklearn":
        model_path = model_subdir / "model.pkl"
        joblib.dump(model, model_path)
    elif model_type == "lightgbm":
        model_path = model_subdir / "model.bin"
        model.booster_.save_model(str(model_path))
    elif model_type == "xgboost":
        model_path = model_subdir / "model.bin"
        model.save_model(str(model_path))
    elif model_type == "tensorflow":
        model_path = model_subdir / "model.h5"
        model.save(str(model_path))
    else:
        model_path = model_subdir / "model.pkl"
        joblib.dump(model, model_path)
    
    # Save metadata files
    run_id = f"{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 1. columns_used.txt
    if feature_cols:
        columns_file = model_subdir / "columns_used.txt"
        columns_file.write_text("\n".join(feature_cols))
    
    # 2. run_id.txt
    run_id_file = model_subdir / "run_id.txt"
    run_id_file.write_text(run_id)
    
    # 3. feature_importance.csv
    if feature_importance is not None:
        importance_file = model_subdir / "feature_importance.csv"
        feature_importance.to_csv(importance_file, index=False)
    
    # 4. training_config.json
    if training_config:
        config_file = model_subdir / "training_config.json"
        # Convert numpy types to native Python types for JSON serialization
        config_serializable = {}
        for k, v in training_config.items():
            if hasattr(v, 'item'):  # numpy scalar
                config_serializable[k] = v.item()
            elif isinstance(v, (list, tuple)):
                config_serializable[k] = [x.item() if hasattr(x, 'item') else x for x in v]
            else:
                config_serializable[k] = v
        config_file.write_text(json.dumps(config_serializable, indent=2))
    
    # 5. metrics.json
    if metrics:
        metrics_file = model_subdir / "metrics.json"
        metrics_serializable = {}
        for k, v in metrics.items():
            if hasattr(v, 'item'):
                metrics_serializable[k] = v.item()
            else:
                metrics_serializable[k] = v
        metrics_file.write_text(json.dumps(metrics_serializable, indent=2))
    
    # 6. model_info.txt (summary)
    info_file = model_subdir / "model_info.txt"
    info_content = f"""Model: {model_name}
Version: {version}
Run ID: {run_id}
Model Type: {model_type}
Created: {datetime.now().isoformat()}
Model Path: {model_path.name}
Features: {len(feature_cols) if feature_cols else 'N/A'}
"""
    if metrics:
        info_content += "\nMetrics:\n"
        for k, v in metrics.items():
            info_content += f"  {k}: {v}\n"
    info_file.write_text(info_content)
    
    return model_subdir

