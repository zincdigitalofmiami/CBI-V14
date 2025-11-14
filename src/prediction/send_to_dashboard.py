#!/usr/bin/env python3
"""
Send local predictions to Vercel dashboard via BigQuery.
Dashboard reads from BigQuery, so we write predictions there.
"""
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from google.cloud import bigquery
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from prediction.generate_local_predictions import generate_local_predictions


def send_predictions_to_bigquery(
    predictions: dict,
    project_id: str = 'cbi-v14',
    dataset_id: str = 'predictions',
    table_id: str = 'local_predictions'
):
    """
    Send local predictions to BigQuery for dashboard consumption.
    
    Args:
        predictions: Dict from generate_local_predictions() {horizon: {value, model, ...}}
        project_id: GCP project
        dataset_id: BigQuery dataset
        table_id: Table name
    """
    client = bigquery.Client(project=project_id)
    
    # Prepare data
    rows = []
    for horizon, pred_info in predictions.items():
        # Calculate target date based on horizon
        horizon_days = {
            '1w': 7,
            '1m': 30,
            '3m': 90,
            '6m': 180,
            '12m': 365
        }
        
        target_date = datetime.now().date() + timedelta(days=horizon_days.get(horizon, 30))
        
        rows.append({
            'prediction_date': datetime.now().date(),
            'horizon': horizon,
            'target_date': target_date,
            'predicted_price': pred_info['value'],
            'model_used': pred_info['model'],
            'current_price': None,  # Will be filled from latest data
            'predicted_change': None,
            'predicted_change_pct': None,
            'confidence_lower': None,  # Can add if quantile models available
            'confidence_upper': None,  # Can add if quantile models available
            'created_at': datetime.now()
        })
    
    if not rows:
        print("⚠️  No predictions to send")
        return False
    
    # Create DataFrame
    df = pd.DataFrame(rows)
    
    # Get current price from latest training data
    try:
        repo_root = Path(__file__).parent.parent.parent
        # New naming: zl_training_{surface}_allhistory_{horizon}.parquet
        data_path = repo_root / "TrainingData/exports/zl_training_prod_allhistory_1m.parquet"
        if data_path.exists():
            latest_data = pd.read_parquet(data_path)
            if 'zl_price_current' in latest_data.columns:
                current_price = latest_data['zl_price_current'].iloc[-1]
                df['current_price'] = current_price
                df['predicted_change'] = df['predicted_price'] - current_price
                df['predicted_change_pct'] = (df['predicted_change'] / current_price) * 100
    except Exception as e:
        print(f"⚠️  Could not get current price: {e}")
    
    # Write to BigQuery - use new naming: predictions.zl_{horizon}_inference_{model}_v{version}
    # For now, keep daily_forecasts for dashboard compatibility (will migrate later)
    table_ref = f"{project_id}.predictions.daily_forecasts"
    
    # Map horizon to dashboard format (1w -> 1W, 1m -> 1M, etc.)
    horizon_map = {
        '1w': '1W',
        '1m': '1M',
        '3m': '3M',
        '6m': '6M',
        '12m': '12M'
    }
    
    # Update rows with dashboard-compatible format
    for row in rows:
        row['horizon'] = horizon_map.get(row['horizon'], row['horizon'].upper())
        row['model_id'] = f"local_{row['model_used']}"
        row['model_name'] = f"Local {row['model_used'].upper()} Model"
        row['mape'] = None  # Will be calculated if available
    
    df = pd.DataFrame(rows)
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",  # Append new predictions (dashboard reads latest)
        schema=[
            bigquery.SchemaField("prediction_date", "DATE"),
            bigquery.SchemaField("horizon", "STRING"),
            bigquery.SchemaField("target_date", "DATE"),
            bigquery.SchemaField("predicted_price", "FLOAT64"),
            bigquery.SchemaField("model_id", "STRING"),
            bigquery.SchemaField("model_name", "STRING"),
            bigquery.SchemaField("current_price", "FLOAT64"),
            bigquery.SchemaField("predicted_change", "FLOAT64"),
            bigquery.SchemaField("predicted_change_pct", "FLOAT64"),
            bigquery.SchemaField("confidence_lower", "FLOAT64"),
            bigquery.SchemaField("confidence_upper", "FLOAT64"),
            bigquery.SchemaField("mape", "FLOAT64"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
        ]
    )
    
    try:
        job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
        job.result()
        print(f"✅ Predictions sent to BigQuery: {table_ref}")
        print(f"   Rows written: {len(df)}")
        return True
    except Exception as e:
        print(f"❌ Failed to write to BigQuery: {e}")
        import traceback
        traceback.print_exc()
        return False


def send_to_dashboard(
    horizon: str = 'all',
    data_path: Path = None,
    model_dir: Path = None
):
    """
    Complete workflow: Generate local predictions → Send to BigQuery → Dashboard reads.
    
    Args:
        horizon: 'all' or specific horizon
        data_path: Path to training data
        model_dir: Directory with models
    """
    print("="*80)
    print("📤 SENDING LOCAL PREDICTIONS TO DASHBOARD")
    print("="*80)
    
    # Step 1: Generate local predictions
    print("\nStep 1: Generating local predictions...")
    predictions = generate_local_predictions(
        horizon=horizon,
        data_path=data_path,
        model_dir=model_dir
    )
    
    if not predictions:
        print("❌ No predictions generated. Train models first!")
        return False
    
    # Step 2: Send to BigQuery
    print("\nStep 2: Sending predictions to BigQuery...")
    success = send_predictions_to_bigquery(predictions)
    
    if success:
        print("\n" + "="*80)
        print("✅ COMPLETE!")
        print("="*80)
        print("Dashboard will automatically read predictions from BigQuery.")
        print("Refresh your dashboard to see new predictions.")
        return True
    else:
        print("\n❌ Failed to send predictions to BigQuery")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Send local predictions to dashboard")
    parser.add_argument("--horizon", default="all", choices=['all', '1w', '1m', '3m', '6m', '12m'])
    parser.add_argument("--data-path", help="Path to training data")
    parser.add_argument("--model-dir", help="Directory with trained models")
    
    args = parser.parse_args()
    
    send_to_dashboard(
        horizon=args.horizon,
        data_path=Path(args.data_path).expanduser() if args.data_path else None,
        model_dir=Path(args.model_dir).expanduser() if args.model_dir else None
    )

