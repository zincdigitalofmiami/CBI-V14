#!/usr/bin/env python3
"""
Upload local predictions to BigQuery for dashboard consumption.
Walks Models/local/ directory and uploads all prediction files to BigQuery.

Creates per-model tables: predictions.zl_{horizon}_inference_{model}_v{version}
Creates latest views: predictions.vw_zl_{horizon}_latest
"""
import os
import sys
from pathlib import Path
from datetime import datetime
from google.cloud import bigquery
import pandas as pd
from typing import List, Dict

PROJECT_ID = os.getenv("PROJECT", "cbi-v14")
PREDICTIONS_DATASET = "predictions"

def get_repo_root():
    """Find repository root."""
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / "QUICK_REFERENCE.txt").exists() or (parent / ".git").exists():
            return parent
    return current_path.parent.parent

def discover_prediction_files(models_dir: Path) -> List[Dict]:
    """
    Walk Models/local/ and find all predictions.parquet files.
    
    Expected structure:
    Models/local/horizon_{h}/{surface}/{family}/{model}_v{ver}/predictions.parquet
    
    Returns list of dicts with: horizon, surface, family, model, version, file_path
    """
    prediction_files = []
    
    if not models_dir.exists():
        print(f"⚠️  Models directory not found: {models_dir}")
        return prediction_files
    
    for pred_file in models_dir.rglob("predictions.parquet"):
        try:
            # Parse path structure
            parts = pred_file.relative_to(models_dir).parts
            
            # Expected: horizon_{h}/{surface}/{family}/{model}_v{ver}/predictions.parquet
            if len(parts) < 5:
                print(f"⚠️  Skipping {pred_file} - unexpected path structure")
                continue
            
            horizon_dir = parts[0]  # e.g., "horizon_1w"
            surface = parts[1]      # e.g., "prod" or "full"
            family = parts[2]       # e.g., "baselines", "advanced"
            model_dir = parts[3]    # e.g., "lightgbm_dart_v001"
            
            # Extract horizon
            if not horizon_dir.startswith("horizon_"):
                continue
            horizon = horizon_dir.replace("horizon_", "")
            
            # Extract model name and version
            if "_v" in model_dir:
                model_name, version = model_dir.rsplit("_v", 1)
                version = f"v{version}"
            else:
                model_name = model_dir
                version = "v001"
            
            prediction_files.append({
                "horizon": horizon,
                "surface": surface,
                "family": family,
                "model": model_name,
                "version": version,
                "file_path": pred_file
            })
            
        except Exception as e:
            print(f"⚠️  Error parsing {pred_file}: {e}")
            continue
    
    return prediction_files

def upload_predictions_to_table(
    client: bigquery.Client,
    predictions_df: pd.DataFrame,
    horizon: str,
    model: str,
    version: str
):
    """Upload predictions to BigQuery table."""
    
    # Table name: zl_{horizon}_inference_{model}_{version}
    table_id = f"{PROJECT_ID}.{PREDICTIONS_DATASET}.zl_{horizon}_inference_{model}_{version}"
    
    # Ensure required schema
    required_columns = {
        "as_of_date": "DATE",
        "horizon": "STRING",
        "current_price": "FLOAT64",
        "predicted_price": "FLOAT64",
        "predicted_return": "FLOAT64",
        "model_name": "STRING",
        "model_version": "STRING",
        "surface": "STRING",
        "created_at": "TIMESTAMP"
    }
    
    # Add missing columns with defaults
    if "as_of_date" not in predictions_df.columns and "date" in predictions_df.columns:
        predictions_df["as_of_date"] = pd.to_datetime(predictions_df["date"]).dt.date
    
    if "horizon" not in predictions_df.columns:
        predictions_df["horizon"] = horizon
    
    if "model_name" not in predictions_df.columns:
        predictions_df["model_name"] = model
    
    if "model_version" not in predictions_df.columns:
        predictions_df["model_version"] = version
    
    if "created_at" not in predictions_df.columns:
        predictions_df["created_at"] = datetime.now()
    
    # Write to BigQuery
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        create_disposition=bigquery.CreateDisposition.CREATE_IF_NEEDED,
        schema_update_options=[
            bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION
        ]
    )
    
    try:
        job = client.load_table_from_dataframe(
            predictions_df,
            table_id,
            job_config=job_config
        )
        job.result()
        print(f"  ✅ Uploaded {len(predictions_df)} rows to {table_id}")
        return True
    except Exception as e:
        print(f"  ❌ Upload failed: {e}")
        return False

def create_latest_views(client: bigquery.Client, horizons: List[str]):
    """Create vw_zl_{horizon}_latest views for each horizon."""
    
    for horizon in horizons:
        view_id = f"{PROJECT_ID}.{PREDICTIONS_DATASET}.vw_zl_{horizon}_latest"
        
        # View SQL: get latest prediction per as_of_date
        view_query = f"""
        CREATE OR REPLACE VIEW `{view_id}` AS
        SELECT *
        FROM `{PROJECT_ID}.{PREDICTIONS_DATASET}.zl_{horizon}_inference_*`
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY as_of_date 
            ORDER BY created_at DESC
        ) = 1
        """
        
        try:
            client.query(view_query).result()
            print(f"  ✅ Created view: {view_id}")
        except Exception as e:
            print(f"  ❌ View creation failed for {horizon}: {e}")

def main():
    """Main upload pipeline."""
    print("="*80)
    print("UPLOAD LOCAL PREDICTIONS TO BIGQUERY")
    print("="*80)
    print()
    
    repo_root = get_repo_root()
    models_dir = repo_root / "Models" / "local"
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # Discover prediction files
    print("🔍 Scanning for prediction files...")
    pred_files = discover_prediction_files(models_dir)
    
    if not pred_files:
        print("⚠️  No prediction files found")
        print(f"   Expected: {models_dir}/horizon_*/{{surface}}/{{family}}/{{model}}_v*/predictions.parquet")
        return
    
    print(f"✅ Found {len(pred_files)} prediction files")
    print()
    
    # Upload each file
    print("📤 Uploading predictions...")
    print("-"*80)
    
    uploaded_count = 0
    failed_count = 0
    horizons_found = set()
    
    for pred_info in pred_files:
        print(f"\n{pred_info['horizon']}/{pred_info['surface']}/{pred_info['family']}/{pred_info['model']}_{pred_info['version']}")
        
        try:
            # Load predictions
            df = pd.read_parquet(pred_info["file_path"])
            
            # Add metadata
            df["surface"] = pred_info["surface"]
            
            # Upload
            if upload_predictions_to_table(
                client,
                df,
                pred_info["horizon"],
                pred_info["model"],
                pred_info["version"]
            ):
                uploaded_count += 1
                horizons_found.add(pred_info["horizon"])
            else:
                failed_count += 1
                
        except Exception as e:
            print(f"  ❌ Error processing file: {e}")
            failed_count += 1
    
    print()
    print("="*80)
    print("CREATING LATEST VIEWS")
    print("="*80)
    
    if horizons_found:
        create_latest_views(client, sorted(horizons_found))
    
    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✅ Uploaded: {uploaded_count}/{len(pred_files)}")
    print(f"❌ Failed: {failed_count}")
    print(f"📊 Horizons: {', '.join(sorted(horizons_found))}")
    print()
    print("Dashboard can now read from:")
    for h in sorted(horizons_found):
        print(f"  - predictions.vw_zl_{h}_latest")

if __name__ == "__main__":
    main()

