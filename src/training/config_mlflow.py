#!/usr/bin/env python3
"""
MLflow Configuration for CBI-V14 Training
Sets up tracking, experiments, and artifact storage
"""
import os
import mlflow
from pathlib import Path

# External drive paths
EXTERNAL_DRIVE = os.getenv("EXTERNAL_DRIVE", "/Volumes/Satechi Hub")
CBI_V14_REPO = os.getenv("CBI_V14_REPO", f"{EXTERNAL_DRIVE}/Projects/CBI-V14")
MLFLOW_DIR = f"{CBI_V14_REPO}/Models/mlflow"

# Set MLflow tracking URI
mlflow.set_tracking_uri(f"file://{MLFLOW_DIR}")

print(f"✅ MLflow tracking URI: file://{MLFLOW_DIR}")

# Create experiments
EXPERIMENTS = {
    'baselines_statistical': 'Statistical baselines (ARIMA, Prophet, ETS)',
    'baselines_tree': 'Tree-based baselines (LightGBM, XGBoost DART)',
    'baselines_neural': 'Simple neural baselines (1-layer LSTM, GRU, FFN)',
    'advanced_neural': 'Advanced neural architectures (2-layer, TCN, CNN-LSTM)',
    'regime_models': 'Regime-specific models (crisis, bull, bear, normal)',
    'volatility': 'Volatility forecasting models',
    'ensemble': 'Ensemble meta-learners',
    'validation': 'Walk-forward validation results'
}

def setup_experiments():
    """Create all MLflow experiments"""
    for exp_name, description in EXPERIMENTS.items():
        try:
            exp = mlflow.get_experiment_by_name(exp_name)
            if exp is None:
                exp_id = mlflow.create_experiment(
                    exp_name,
                    artifact_location=f"file://{MLFLOW_DIR}/artifacts/{exp_name}",
                    tags={"project": "CBI-V14", "phase": "baseline"}
                )
                print(f"✅ Created experiment: {exp_name} (ID: {exp_id})")
            else:
                print(f"✅ Experiment exists: {exp_name} (ID: {exp.experiment_id})")
        except Exception as e:
            print(f"⚠️  Error with experiment {exp_name}: {e}")

if __name__ == "__main__":
    print("="*80)
    print("🔧 MLFLOW CONFIGURATION")
    print("="*80)
    print(f"Project: CBI-V14")
    print(f"MLflow Directory: {MLFLOW_DIR}")
    print("="*80)
    print()
    
    setup_experiments()
    
    print()
    print("="*80)
    print("✅ MLflow configuration complete")
    print("="*80)
    print()
    print("To view MLflow UI:")
    print(f"  cd {CBI_V14_REPO}")
    print(f"  mlflow ui --backend-store-uri file://{MLFLOW_DIR}")
    print("  Then open: http://localhost:5000")
    print()

