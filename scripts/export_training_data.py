#!/usr/bin/env python3
"""
Export training data from BigQuery to Parquet files for local training.
Uses new naming convention: training.zl_training_{full|prod}_allhistory_{horizon}
"""
import argparse
import os
from pathlib import Path
from google.cloud import bigquery
import pandas as pd
import sys

PROJECT_ID = os.getenv("PROJECT", "cbi-v14")

def get_repo_root():
    """Find repository root."""
    current_path = Path(__file__).resolve()
    # Walk up from scripts/export_training_data.py to find repo root
    # Repo root should have .git or src/ or config/ directories
    for parent in current_path.parents:
        if ((parent / ".git").exists() or
            (parent / "src").exists() or
            (parent / "config").exists()):
            return parent
    # Fallback: go up 2 levels from scripts/
    return current_path.parent.parent

def export_training_data(horizon: str, surface: str = "prod", output_dir: Path = None):
    """
    Export training data from BigQuery to Parquet.
    
    Args:
        horizon: One of '1w', '1m', '3m', '6m', '12m'
        surface: 'prod' (≈290 cols) or 'full' (1,948+ cols)
        output_dir: Output directory (default: TrainingData/exports)
    """
    client = bigquery.Client(project=PROJECT_ID)
    
    # New table name
    table_ref = f"{PROJECT_ID}.training.zl_training_{surface}_allhistory_{horizon}"
    
    # Output path
    if output_dir is None:
        repo_root = get_repo_root()
        output_dir = repo_root / "TrainingData" / "exports"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"zl_training_{surface}_allhistory_{horizon}.parquet"
    
    print(f"Exporting {table_ref} → {output_file}")
    
    try:
        # Query data
        query = f"SELECT * FROM `{table_ref}` ORDER BY date"
        df = client.query(query).to_dataframe()
        
        if df.empty:
            print(f"  ⚠️  No data found")
            return False
        
        # FIX: Convert BigQuery DATE columns to pandas datetime
        # BigQuery's DATE type exports as 'dbdate' which pandas/pyarrow doesn't understand
        date_columns = ['date', 'signal_date', 'ingest_date', 'last_updated', 'created_at']
        for col in date_columns:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col])
                    print(f"  🔄 Converted {col} to datetime")
                except Exception as e:
                    print(f"  ⚠️  Could not convert {col}: {e}")
        
        # Also convert any remaining columns with 'dbdate' dtype
        for col in df.columns:
            if str(df[col].dtype) == 'dbdate':
                try:
                    df[col] = pd.to_datetime(df[col])
                    print(f"  🔄 Converted {col} (dbdate) to datetime")
                except Exception as e:
                    print(f"  ⚠️  Could not convert {col}: {e}")
        
        # Save to parquet
        df.to_parquet(output_file, index=False, engine='pyarrow')
        
        print(f"  ✅ Exported {len(df):,} rows, {len(df.columns)} columns")
        print(f"  📁 Saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def export_all_horizons(surface: str = "prod"):
    """Export all horizons."""
    horizons = ["1w", "1m", "3m", "6m", "12m"]
    
    print("="*80)
    print(f"EXPORTING ALL HORIZONS ({surface.upper()} surface)")
    print("="*80)
    print()
    
    results = []
    for horizon in horizons:
        success = export_training_data(horizon, surface)
        results.append(success)
        print()
    
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✅ Success: {sum(results)}/{len(horizons)}")
    print(f"❌ Failed: {len(results) - sum(results)}/{len(horizons)}")
    
    return all(results)

def main():
    parser = argparse.ArgumentParser(description="Export training data from BigQuery to Parquet")
    parser.add_argument("--horizon", choices=["1w", "1m", "3m", "6m", "12m", "all"], 
                       default="all", help="Horizon to export")
    parser.add_argument("--surface", choices=["prod", "full"], default="prod",
                       help="Surface type: prod (≈290 cols) or full (1,948+ cols)")
    parser.add_argument("--output-dir", type=str, help="Output directory")
    
    args = parser.parse_args()
    
    if args.horizon == "all":
        success = export_all_horizons(args.surface)
    else:
        output_dir = Path(args.output_dir) if args.output_dir else None
        success = export_training_data(args.horizon, args.surface, output_dir)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

