#!/usr/bin/env python3
"""
Train baseline statistical models (ARIMA, Prophet) on exported Parquet data.
"""
import argparse
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from prophet import Prophet
import joblib
from pathlib import Path
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

def get_repo_root():
    """Find the repository root by looking for a marker file."""
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / "QUICK_REFERENCE.txt").exists():
            return parent
    raise FileNotFoundError("Repository root not found.")

def train_arima(data_path: Path, horizon: str, model_dir: Path):
    """Trains and saves an ARIMA model."""
    print(f"\n--- Training ARIMA for {horizon} horizon ---")
    try:
        df = pd.read_parquet(data_path)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').asfreq('D') # Ensure daily frequency, fill gaps with NaN
        
        # Use a simple target column, assuming it's present
        target_col = 'zl_price_current'
        if target_col not in df.columns:
            print(f"❌ Target column '{target_col}' not found in {data_path}")
            return

        # Forward-fill to handle weekends/holidays before training
        series = df[target_col].ffill()

        # A simple ARIMA order, can be tuned
        model = ARIMA(series, order=(5, 1, 0))
        fitted = model.fit()
        print(f"ARIMA model fitted for {horizon}.")

        model_subdir = model_dir / "arima"
        model_subdir.mkdir(parents=True, exist_ok=True)
        output_path = model_subdir / "model.bin"
        joblib.dump(fitted, output_path)
        print(f"✅ ARIMA model for {horizon} saved to {output_path}")
    except Exception as e:
        print(f"❌ Failed to train ARIMA for {horizon}: {e}")

def train_prophet(data_path: Path, horizon: str, model_dir: Path):
    """Trains and saves a Prophet model."""
    print(f"\n--- Training Prophet for {horizon} horizon ---")
    try:
        df = pd.read_parquet(data_path)
        
        target_col = 'zl_price_current'
        if 'date' not in df.columns or target_col not in df.columns:
            print(f"❌ 'date' or '{target_col}' column not found in {data_path}")
            return
            
        prophet_df = df[['date', target_col]].rename(columns={'date': 'ds', target_col: 'y'})

        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False
        )
        model.fit(prophet_df)
        print(f"Prophet model fitted for {horizon}.")

        model_subdir = model_dir / "prophet"
        model_subdir.mkdir(parents=True, exist_ok=True)
        output_path = model_subdir / "model.bin"
        joblib.dump(model, output_path)
        print(f"✅ Prophet model for {horizon} saved to {output_path}")
    except Exception as e:
        print(f"❌ Failed to train Prophet for {horizon}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Train baseline statistical models.")
    parser.add_argument("--horizon", required=True, help="Forecast horizon (e.g., 1w, 1m).")
    parser.add_argument("--surface", choices=["prod", "full"], default="prod",
                       help="Surface type: prod (≈290 cols) or full (1,948+ cols)")
    parser.add_argument("--model", choices=['arima', 'prophet', 'all'], default='all', help="Model to train.")
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

    if args.model in ['arima', 'all']:
        train_arima(data_path, args.horizon, model_dir)
    
    if args.model in ['prophet', 'all']:
        train_prophet(data_path, args.horizon, model_dir)
        
    print("\n--- Statistical baseline training complete! ---")

if __name__ == "__main__":
    main()
