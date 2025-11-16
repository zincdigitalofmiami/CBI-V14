#!/usr/bin/env python3
"""
Export regime_calendar and regime_weights from BigQuery to local parquet files.
Required for Phase 2 feature engineering in the 25-year data enrichment plan.

Author: AI Assistant
Date: November 16, 2025
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
from google.cloud import bigquery
from google.cloud import storage

# Configuration
PROJECT_ID = 'cbi-v14'
DATASET_ID = 'training'
LOCATION = 'us-central1'
TEMP_BUCKET = 'cbi-v14-migration-us-central1'
DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
REGISTRY_DIR = DRIVE / "registry"

def export_regime_files():
    """Export regime_calendar and regime_weights from BigQuery to local parquet files."""
    
    print("="*80)
    print("EXPORTING REGIME FILES FROM BIGQUERY")
    print("="*80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target: {REGISTRY_DIR}")
    print()
    
    # Initialize clients
    bq_client = bigquery.Client(project=PROJECT_ID)
    storage_client = storage.Client(project=PROJECT_ID)
    
    # Ensure registry directory exists
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    
    # Define tables to export
    tables = [
        {
            'name': 'regime_calendar',
            'table_id': f'{PROJECT_ID}.{DATASET_ID}.regime_calendar',
            'expected_cols': ['date', 'regime'],
            'validation': {
                'date_range': ('2000-01-01', '2025-12-31'),
                'regime_count': (7, 11)
            }
        },
        {
            'name': 'regime_weights', 
            'table_id': f'{PROJECT_ID}.{DATASET_ID}.regime_weights',
            'expected_cols': ['regime', 'weight', 'start_date', 'end_date'],
            'validation': {
                'weight_range': (50, 500),
                'regime_count': (7, 11)
            }
        }
    ]
    
    for table_info in tables:
        print(f"\n{'='*40}")
        print(f"Exporting: {table_info['name']}")
        print(f"{'='*40}")
        
        try:
            # Step 1: Export to GCS
            gcs_uri = f"gs://{TEMP_BUCKET}/{table_info['name']}.parquet"
            output_file = REGISTRY_DIR / f"{table_info['name']}.parquet"
            
            print(f"1. Exporting to GCS: {gcs_uri}")
            
            # Configure extraction job
            job_config = bigquery.ExtractJobConfig()
            job_config.destination_format = bigquery.DestinationFormat.PARQUET
            job_config.compression = bigquery.Compression.SNAPPY
            
            # Run extraction
            extract_job = bq_client.extract_table(
                table_info['table_id'],
                gcs_uri,
                location=LOCATION,
                job_config=job_config
            )
            
            # Wait for job completion
            extract_job.result()
            print(f"   ✅ Export to GCS complete")
            
            # Step 2: Download from GCS to local
            print(f"2. Downloading to local: {output_file}")
            
            bucket = storage_client.bucket(TEMP_BUCKET)
            blob = bucket.blob(f"{table_info['name']}.parquet")
            
            # Download to local file
            blob.download_to_filename(str(output_file))
            print(f"   ✅ Download complete")
            
            # Step 3: Load and validate
            print(f"3. Validating exported data...")
            df = pd.read_parquet(output_file)
            
            # Check columns
            missing_cols = set(table_info['expected_cols']) - set(df.columns)
            if missing_cols:
                raise ValueError(f"Missing expected columns: {missing_cols}")
            print(f"   ✅ Columns verified: {list(df.columns)}")
            
            # Check row count
            print(f"   ✅ Rows: {len(df):,}")
            
            # Table-specific validation
            if table_info['name'] == 'regime_calendar':
                # Check date range
                df['date'] = pd.to_datetime(df['date'])
                actual_min = df['date'].min().strftime('%Y-%m-%d')
                actual_max = df['date'].max().strftime('%Y-%m-%d')
                expected_min, expected_max = table_info['validation']['date_range']
                
                if actual_min > expected_min:
                    print(f"   ⚠️ Warning: Start date {actual_min} is later than expected {expected_min}")
                if actual_max < expected_max:
                    print(f"   ⚠️ Warning: End date {actual_max} is earlier than expected {expected_max}")
                else:
                    print(f"   ✅ Date range: {actual_min} to {actual_max}")
                
                # Check regime count
                regime_count = df['regime'].nunique()
                min_regimes, max_regimes = table_info['validation']['regime_count']
                if not (min_regimes <= regime_count <= max_regimes):
                    raise ValueError(f"Regime count {regime_count} not in expected range {min_regimes}-{max_regimes}")
                print(f"   ✅ Unique regimes: {regime_count}")
                print(f"   Regimes: {sorted(df['regime'].unique())}")
                
            elif table_info['name'] == 'regime_weights':
                # Check weight range
                min_weight = df['weight'].min()
                max_weight = df['weight'].max()
                expected_min, expected_max = table_info['validation']['weight_range']
                
                if not (expected_min <= min_weight and max_weight <= expected_max):
                    raise ValueError(f"Weight range {min_weight}-{max_weight} not in expected range {expected_min}-{expected_max}")
                print(f"   ✅ Weight range: {min_weight}-{max_weight}")
                
                # Check regime count
                regime_count = df['regime'].nunique()
                min_regimes, max_regimes = table_info['validation']['regime_count']
                if not (min_regimes <= regime_count <= max_regimes):
                    raise ValueError(f"Regime count {regime_count} not in expected range {min_regimes}-{max_regimes}")
                print(f"   ✅ Unique regimes: {regime_count}")
                
                # Show regime weights
                print("\n   Regime weights:")
                for _, row in df.iterrows():
                    print(f"     - {row['regime']}: {row['weight']}")
            
            # Step 4: Clean up GCS temp file
            print(f"4. Cleaning up GCS temp file...")
            blob.delete()
            print(f"   ✅ Temp file deleted")
            
            print(f"\n✅ SUCCESS: {table_info['name']} exported to {output_file}")
            
        except Exception as e:
            print(f"\n❌ ERROR exporting {table_info['name']}: {str(e)}")
            sys.exit(1)
    
    print("\n" + "="*80)
    print("✅ ALL REGIME FILES EXPORTED SUCCESSFULLY")
    print("="*80)
    print(f"Files saved to: {REGISTRY_DIR}")
    print("Ready for Phase 2 feature engineering")
    
    return True

if __name__ == "__main__":
    # Check if external drive is mounted
    if not DRIVE.exists():
        print(f"❌ ERROR: External drive not mounted at {DRIVE}")
        print("Please mount the Satechi Hub and try again")
        sys.exit(1)
    
    # Run export
    export_regime_files()
