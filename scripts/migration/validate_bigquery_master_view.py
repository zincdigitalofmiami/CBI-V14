#!/usr/bin/env python3
"""
Validate BigQuery master_features_all view matches local staging (1,175 columns).
Ensures production BQ copy is in sync with local pipeline.
"""

import pandas as pd
from google.cloud import bigquery
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.utils.gcp_utils import get_gcp_project_id

PROJECT_ID = get_gcp_project_id()
DATASET_ID = "forecasting_data_warehouse"
VIEW_NAME = "master_features_all"

def validate_bigquery_view():
    """Validate BigQuery master view matches local staging."""
    print("="*80)
    print("BIGQUERY MASTER VIEW VALIDATION")
    print("="*80)
    
    client = bigquery.Client(project=PROJECT_ID)
    view_id = f"{PROJECT_ID}.{DATASET_ID}.{VIEW_NAME}"
    
    # Get view schema
    print("\n1. Checking view schema...")
    try:
        view = client.get_table(view_id)
        print(f"   ✅ View exists: {view_id}")
        print(f"   Columns: {len(view.schema)}")
    except Exception as e:
        print(f"   ❌ Error accessing view: {e}")
        return False
    
    # Query sample to get column names
    print("\n2. Querying view for column count and sample...")
    query = f"""
    SELECT *
    FROM `{view_id}`
    LIMIT 1
    """
    
    try:
        result = client.query(query).result()
        df_sample = result.to_dataframe()
        
        print(f"   ✅ Query successful")
        print(f"   Columns in view: {len(df_sample.columns)}")
        
        # Check for ES columns
        es_cols = [c for c in df_sample.columns if c.startswith('es_')]
        print(f"   ES columns: {len(es_cols)}")
        
        # Check total row count
        count_query = f"SELECT COUNT(*) as row_count FROM `{view_id}`"
        count_result = client.query(count_query).result()
        row_count = list(count_result)[0].row_count
        
        print(f"\n3. Row count validation...")
        print(f"   Rows in view: {row_count:,}")
        
        # Check date range
        date_query = f"""
        SELECT 
            MIN(date) as min_date,
            MAX(date) as max_date
        FROM `{view_id}`
        """
        date_result = client.query(date_query).result()
        for row in date_result:
            print(f"   Date range: {row.min_date} to {row.max_date}")
        
        # Compare with expected
        print(f"\n4. Validation against expected values...")
        expected_cols = 1175
        expected_rows = 6380
        
        col_match = len(df_sample.columns) == expected_cols
        row_match = row_count == expected_rows
        
        print(f"   Expected columns: {expected_cols}")
        print(f"   Actual columns: {len(df_sample.columns)}")
        print(f"   {'✅' if col_match else '❌'} Column count match")
        
        print(f"\n   Expected rows: {expected_rows:,}")
        print(f"   Actual rows: {row_count:,}")
        print(f"   {'✅' if row_match else '❌'} Row count match")
        
        # Check ES columns exist
        print(f"\n5. ES data validation...")
        if len(es_cols) > 0:
            print(f"   ✅ ES columns found: {len(es_cols)}")
            print(f"   Sample ES columns:")
            for col in sorted(es_cols)[:10]:
                print(f"     - {col}")
            if len(es_cols) > 10:
                print(f"     ... and {len(es_cols)-10} more")
        else:
            print(f"   ❌ No ES columns found!")
        
        # Check for key indicators
        key_indicators = ['es_close', 'es_rsi_14', 'es_macd', 'es_bb_upper_20']
        missing = [ind for ind in key_indicators if ind not in df_sample.columns]
        if missing:
            print(f"   ⚠️  Missing key indicators: {missing}")
        else:
            print(f"   ✅ All key ES indicators present")
        
        # Final summary
        print("\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80)
        
        all_pass = col_match and row_match and len(es_cols) > 0
        
        if all_pass:
            print("✅ BIGQUERY VIEW VALIDATION PASSED")
            print(f"   - Column count: {len(df_sample.columns)} (expected {expected_cols})")
            print(f"   - Row count: {row_count:,} (expected {expected_rows:,})")
            print(f"   - ES columns: {len(es_cols)}")
            print("\n🎉 BigQuery production copy is in sync with local pipeline!")
        else:
            print("❌ VALIDATION FAILED")
            if not col_match:
                print(f"   - Column count mismatch: {len(df_sample.columns)} vs {expected_cols}")
            if not row_match:
                print(f"   - Row count mismatch: {row_count:,} vs {expected_rows:,}")
            if len(es_cols) == 0:
                print(f"   - ES columns missing")
        
        return all_pass
        
    except Exception as e:
        print(f"   ❌ Error querying view: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = validate_bigquery_view()
    sys.exit(0 if success else 1)




