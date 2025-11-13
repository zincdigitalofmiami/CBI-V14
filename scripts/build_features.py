#!/usr/bin/env python3
"""
Feature Engineering Pipeline for CBI-V14

This script loads raw exported data from TrainingData/exports/, applies a comprehensive
set of feature engineering transformations, and saves the result to 
TrainingData/processed/.

This ensures a consistent, offline feature set for all local model training.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import warnings

warnings.filterwarnings("ignore")

def get_repo_root():
    """Find the repository root by looking for a marker file."""
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / "QUICK_REFERENCE.txt").exists():
            return parent
    raise FileNotFoundError("Repository root not found.")

def apply_feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies a comprehensive suite of feature engineering transformations.
    """
    print(f"Original shape: {df.shape}")
    
    # 1. Ensure date column is datetime
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').set_index('date')

    # 2. Price-based features
    # Use a generic price column if 'zl_price_current' is not available
    price_col = 'zl_price_current'
    if price_col not in df.columns:
        # Find the first available price-like column
        price_col = next((col for col in df.columns if 'price' in col), None)
    
    if price_col:
        # Lag features
        for lag in [1, 3, 5, 10, 21, 63]:
            df[f'{price_col}_lag_{lag}'] = df[price_col].shift(lag)

        # Rolling window features
        for window in [5, 10, 21, 63]:
            df[f'{price_col}_rolling_mean_{window}'] = df[price_col].rolling(window=window).mean()
            df[f'{price_col}_rolling_std_{window}'] = df[price_col].rolling(window=window).std()
            
        # Momentum
        df[f'{price_col}_momentum'] = df[price_col].diff(5)

    # 3. Time-based features
    df['day_of_week'] = df.index.dayofweek
    df['month'] = df.index.month
    df['quarter'] = df.index.quarter
    df['year'] = df.index.year

    # 4. Handle missing values created by transformations (e.g., lags, rolling windows)
    # A simple forward-fill is often effective for time series
    df = df.ffill().bfill()
    
    print(f"Shape after feature engineering: {df.shape}")
    
    return df.reset_index()

def main():
    parser = argparse.ArgumentParser(description="Build features for training datasets.")
    parser.add_argument(
        "--horizon", 
        required=True, 
        help="Forecast horizon to process (e.g., 1w, 1m, or 'all')."
    )
    
    args = parser.parse_args()
    
    repo_root = get_repo_root()
    export_dir = repo_root / "TrainingData/exports"
    processed_dir = repo_root / "TrainingData/processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    horizons = ['1w', '1m', '3m', '6m', '12m'] if args.horizon == 'all' else [args.horizon]
    
    for horizon in horizons:
        print(f"\n--- Processing {horizon} horizon data ---")
        input_path = export_dir / f"production_training_data_{horizon}.parquet"
        output_path = processed_dir / f"processed_training_data_{horizon}.parquet"
        
        if not input_path.exists():
            print(f"⚠️  Warning: Raw data file not found at {input_path}. Skipping.")
            continue
            
        print(f"Loading raw data from {input_path}...")
        raw_df = pd.read_parquet(input_path)
        
        processed_df = apply_feature_engineering(raw_df)
        
        print(f"Saving processed data to {output_path}...")
        processed_df.to_parquet(output_path, index=False)
        print(f"✅ Successfully saved processed data for {horizon} horizon.")

    print("\n--- Feature engineering pipeline complete! ---")

if __name__ == "__main__":
    main()
