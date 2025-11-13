#!/usr/bin/env python3
"""
Generate Daily Forecasts for all horizons and save them to BigQuery.
"""
import argparse
from pathlib import Path
import pandas as pd
import joblib
import tensorflow as tf
from google.cloud import bigquery
import numpy as np

def get_repo_root():
    """Finds the repository root."""
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / "QUICK_REFERENCE.txt").exists():
            return parent
    raise FileNotFoundError("Repository root not found.")

def load_model(model_path: Path):
    """Loads a saved model (PKL or TensorFlow SavedModel)."""
    if model_path.suffix == '.pkl':
        return joblib.load(model_path)
    else:
        return tf.keras.models.load_model(model_path)

def generate_forecasts(horizon: str, model_dir: Path, data_dir: Path, client: bigquery.Client):
    """Generates and uploads forecasts for a given horizon."""
    print(f"\n--- Generating forecasts for {horizon} horizon ---")
    
    # Load data
    data_path = data_dir / f"processed_training_data_{horizon}.parquet"
    if not data_path.exists():
        print(f"⚠️ Processed data not found for {horizon} at {data_path}. Skipping.")
        return
        
    df = pd.read_parquet(data_path)
    
    # Prepare the last sequence for prediction
    # This is a simplified example; a real implementation would be more robust
    latest_data = df.tail(30) # Assuming a lookback of 30 for neural models
    
    # Example for a simple feature set
    feature_cols = [col for col in df.columns if col not in ['date', 'zl_price_current'] and 'target' not in col]
    X_pred = latest_data[feature_cols]

    # Find and load the best model for this horizon
    # In a real system, this would come from MLflow or a model registry
    model_path = model_dir / f"simple_lstm_{horizon}" # Example
    if not model_path.exists():
        print(f"⚠️ Model not found for {horizon} at {model_path}. Skipping.")
        return
        
    model = load_model(model_path)
    
    # Make prediction (this is highly simplified)
    # A real implementation needs to match the training preprocessing (scaling, sequences)
    # For demonstration, we'll just pretend to predict
    prediction = model.predict(np.array([X_pred.values]))[0][0]
    
    forecast_df = pd.DataFrame({
        'prediction_date': [pd.Timestamp.now().date()],
        'horizon': [horizon],
        'predicted_price': [prediction],
        'model_used': [model_path.name]
    })
    
    # Upload to BigQuery
    table_id = "cbi-v14.predictions.daily_forecasts"
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        schema=[
            bigquery.SchemaField("prediction_date", "DATE"),
            bigquery.SchemaField("horizon", "STRING"),
            bigquery.SchemaField("predicted_price", "FLOAT"),
            bigquery.SchemaField("model_used", "STRING"),
        ]
    )
    
    try:
        job = client.load_table_from_dataframe(forecast_df, table_id, job_config=job_config)
        job.result()
        print(f"✅ Forecast for {horizon} uploaded to {table_id}.")
    except Exception as e:
        print(f"❌ Failed to upload forecast for {horizon}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Generate daily forecasts.")
    parser.add_argument("--horizon", required=True, help="Horizon to forecast (e.g., 1w, 1m, or 'all').")
    
    args = parser.parse_args()
    
    repo_root = get_repo_root()
    model_dir = repo_root / "Models/local/baselines"
    data_dir = repo_root / "TrainingData/processed"
    
    client = bigquery.Client()
    
    horizons = ['1w', '1m', '3m', '6m', '12m'] if args.horizon == 'all' else [args.horizon]
    
    for horizon in horizons:
        generate_forecasts(horizon, model_dir, data_dir, client)
        
    print("\n--- Daily forecast generation complete! ---")

if __name__ == "__main__":
    main()
