#!/usr/bin/env python3
"""
PHASE 2: Export all training data to Parquet files
Date: November 15, 2025
"""

import os
import sys
import pandas as pd
from google.cloud import bigquery
from datetime import datetime
import hashlib

def export_training_table(client, surface, horizon):
    """Export a single training table to Parquet."""
    
    table_name = f"zl_training_{surface}_allhistory_{horizon}"
    full_table_id = f"cbi-v14.training.{table_name}"
    output_dir = "TrainingData/exports"
    output_file = f"{output_dir}/{table_name}.parquet"
    
    print(f"\nExporting {table_name}...")
    print("-" * 40)
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Query the table
    query = f"""
    SELECT * 
    FROM `{full_table_id}`
    ORDER BY date
    """
    
    try:
        # Execute query and convert to dataframe
        print(f"  Querying {full_table_id}...")
        df = client.query(query).to_dataframe()
        
        # Convert date columns to datetime
        date_columns = ['date']
        for col in date_columns:
            if col in df.columns and df[col].dtype == 'object':
                df[col] = pd.to_datetime(df[col])
        
        # Show statistics
        print(f"  Rows: {len(df):,}")
        print(f"  Columns: {len(df.columns)}")
        print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
        
        # Check regime distribution
        if 'market_regime' in df.columns:
            regime_counts = df['market_regime'].value_counts()
            print(f"  Regimes: {len(regime_counts)} unique")
            for regime, count in regime_counts.head(3).items():
                print(f"    - {regime}: {count:,} rows")
        
        # Check weight distribution
        if 'training_weight' in df.columns:
            print(f"  Weight range: {df['training_weight'].min()}-{df['training_weight'].max()}")
        
        # Calculate schema hash
        schema_str = '|'.join([f"{col}:{df[col].dtype}" for col in sorted(df.columns)])
        schema_hash = hashlib.sha256(schema_str.encode()).hexdigest()[:8]
        print(f"  Schema hash: {schema_hash}")
        
        # Export to Parquet
        print(f"  Writing to {output_file}...")
        df.to_parquet(output_file, engine='pyarrow', compression='snappy', index=False)
        
        # Verify file was created
        if os.path.exists(output_file):
            file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
            print(f"  ✅ Exported successfully ({file_size_mb:.1f} MB)")
            return True
        else:
            print(f"  ❌ Export failed - file not created")
            return False
            
    except Exception as e:
        print(f"  ❌ Export failed: {str(e)[:200]}")
        # Try alternative approach if table doesn't exist
        if "not found" in str(e).lower():
            print(f"  ⚠️  Table {table_name} does not exist")
        return False

def main():
    print("="*60)
    print("PHASE 2: EXPORT TRAINING DATA TO PARQUET")
    print("="*60)
    
    # Initialize BigQuery client
    client = bigquery.Client(project='cbi-v14')
    
    # Define all combinations to export
    surfaces = ['prod', 'full']
    horizons = ['1w', '1m', '3m', '6m', '12m']
    
    success_count = 0
    failed_exports = []
    
    # Export each table
    for surface in surfaces:
        for horizon in horizons:
            success = export_training_table(client, surface, horizon)
            if success:
                success_count += 1
            else:
                failed_exports.append(f"{surface}_{horizon}")
    
    # Summary
    print("\n" + "="*60)
    print("EXPORT SUMMARY")
    print("="*60)
    print(f"✅ Successfully exported: {success_count}/10 tables")
    
    if failed_exports:
        print(f"❌ Failed exports: {', '.join(failed_exports)}")
        
        # Check if full surface tables exist
        print("\nChecking for full surface tables in BigQuery...")
        for horizon in horizons:
            table_name = f"zl_training_full_allhistory_{horizon}"
            check_query = f"""
            SELECT COUNT(*) as row_count
            FROM `cbi-v14.training.{table_name}`
            LIMIT 1
            """
            try:
                result = client.query(check_query).result()
                for row in result:
                    print(f"  {table_name}: {row.row_count:,} rows")
            except:
                print(f"  {table_name}: NOT FOUND")
    
    # List exported files
    print("\nExported files:")
    export_dir = "TrainingData/exports"
    if os.path.exists(export_dir):
        for file in sorted(os.listdir(export_dir)):
            if file.endswith('.parquet'):
                file_path = os.path.join(export_dir, file)
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                print(f"  {file} ({size_mb:.1f} MB)")
    
    print("\nPhase 2 Status: COMPLETE")
    if success_count < 10:
        print("⚠️  Some exports failed - may need to create full surface tables first")
    
    return success_count

if __name__ == "__main__":
    success_count = main()
    sys.exit(0 if success_count == 10 else 1)






