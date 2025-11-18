#!/usr/bin/env python3
"""
Week 0 Day 3: Apply View Updates to BigQuery
Applies the refactored view definitions after fixing column references.
"""

import os
from google.cloud import bigquery
from typing import List
from datetime import datetime

PROJECT_ID = "cbi-v14"
LOCATION = "us-central1"

def fix_column_references(sql: str) -> str:
    """Fix column references for yahoo_historical_prefixed table."""
    # The legacy soybean_oil_prices table has `time` TIMESTAMP
    # The new yahoo_historical_prefixed table has `date` DATE
    
    # Replace DATE(time) with date (since date is already DATE type)
    sql = sql.replace("DATE(time)", "date")
    
    # Also need to add WHERE symbol = 'ZL' for the new table
    # Find the FROM clause and add WHERE if not present
    if "WHERE symbol = 'ZL'" not in sql and "WHERE symbol='ZL'" not in sql:
        # Add symbol filter after FROM yahoo_historical_prefixed
        sql = sql.replace(
            "FROM `cbi-v14.forecasting_data_warehouse.yahoo_historical_prefixed`",
            "FROM `cbi-v14.forecasting_data_warehouse.yahoo_historical_prefixed`\n            WHERE symbol = 'ZL'"
        )
        # Handle case where WHERE already exists - change to AND
        sql = sql.replace(
            "WHERE symbol = 'ZL'\n            WHERE",
            "WHERE symbol = 'ZL'\n            AND"
        )
    
    return sql

def apply_view_update(client: bigquery.Client, dataset_id: str, view_id: str, sql_file: str) -> bool:
    """Apply updated view definition."""
    try:
        # Read SQL file
        with open(sql_file, 'r') as f:
            sql = f.read()
        
        # Skip header comments
        sql_lines = [line for line in sql.split('\n') if not line.startswith('--')]
        sql = '\n'.join(sql_lines)
        
        # Fix column references
        sql = fix_column_references(sql)
        
        # Update view
        view_ref = f"{PROJECT_ID}.{dataset_id}.{view_id}"
        view = client.get_table(view_ref)
        view.view_query = sql
        client.update_table(view, ["view_query"])
        
        print(f"  ✓ Updated successfully")
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    """Apply all view updates."""
    
    print("\n" + "="*60)
    print("Week 0 Day 3: Apply View Updates")
    print("="*60)
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # Get list of updated SQL files
    update_dir = "/Users/kirkmusick/Documents/GitHub/CBI-V14/docs/migration/view_updates"
    sql_files = [f for f in os.listdir(update_dir) if f.endswith('_updated.sql')]
    
    print(f"\nFound {len(sql_files)} views to update")
    
    success_count = 0
    fail_count = 0
    
    for sql_file in sorted(sql_files):
        # Parse filename: signals_vw_bear_market_regime_updated.sql
        parts = sql_file.replace('_updated.sql', '').split('_', 1)
        dataset_id = parts[0]
        view_id = parts[1]
        
        print(f"\n{dataset_id}.{view_id}:")
        print("-" * 60)
        
        sql_path = os.path.join(update_dir, sql_file)
        if apply_view_update(client, dataset_id, view_id, sql_path):
            success_count += 1
        else:
            fail_count += 1
    
    # Summary
    print("\n" + "="*60)
    print(f"✓ {success_count} views updated successfully")
    if fail_count > 0:
        print(f"✗ {fail_count} views failed")
    print("="*60)
    
    return 0 if fail_count == 0 else 1

if __name__ == "__main__":
    exit(main())

