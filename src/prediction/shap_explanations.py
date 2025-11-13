#!/usr/bin/env python3
"""
Generate SHAP explanations for trained models to understand feature importance.
"""
import argparse
import pandas as pd
import joblib
import shap
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

def get_repo_root():
    """Finds the repository root."""
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / "QUICK_REFERENCE.txt").exists():
            return parent
    raise FileNotFoundError("Repository root not found.")

def generate_shap_explanations(horizon: str, model_dir: Path, data_dir: Path):
    """Generates and saves SHAP explanation plots for a given model."""
    print(f"\n--- Generating SHAP explanations for {horizon} horizon ---")
    
    # Load model
    model_path = model_dir / f"lightgbm_dart_{horizon}.pkl" # Using LightGBM for SHAP
    if not model_path.exists():
        print(f"⚠️ Model not found for {horizon} at {model_path}. Skipping.")
        return
    model = joblib.load(model_path)
    
    # Load data
    data_path = data_dir / f"processed_training_data_{horizon}.parquet"
    if not data_path.exists():
        print(f"⚠️ Processed data not found for {horizon} at {data_path}. Skipping.")
        return
    df = pd.read_parquet(data_path)
    
    # Prepare data for SHAP
    feature_cols = [col for col in df.columns if col not in ['date', 'zl_price_current'] and 'target' not in col]
    X = df[feature_cols]
    
    # Create SHAP explainer
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    
    # Generate and save summary plot
    output_dir = get_repo_root() / "docs/analysis/shap_plots"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        import matplotlib.pyplot as plt
        
        plt.figure()
        shap.summary_plot(shap_values, X, plot_type="bar", max_display=20, show=False)
        plot_path = output_dir / f"shap_summary_{horizon}.png"
        plt.savefig(plot_path, bbox_inches='tight')
        plt.close()
        print(f"✅ SHAP summary plot for {horizon} saved to {plot_path}")
        
    except ImportError:
        print("⚠️ Matplotlib not installed. Skipping plot generation.")
    except Exception as e:
        print(f"❌ Failed to generate SHAP plot for {horizon}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Generate SHAP explanations for models.")
    parser.add_argument("--horizon", required=True, help="Horizon to analyze (e.g., 1w, 1m, or 'all').")
    
    args = parser.parse_args()
    
    repo_root = get_repo_root()
    model_dir = repo_root / "Models/local/baselines"
    data_dir = repo_root / "TrainingData/processed"
    
    horizons = ['1w', '1m', '3m', '6m', '12m'] if args.horizon == 'all' else [args.horizon]
    
    for horizon in horizons:
        generate_shap_explanations(horizon, model_dir, data_dir)
        
    print("\n--- SHAP explanation generation complete! ---")

if __name__ == "__main__":
    main()
