#!/usr/bin/env python3
"""
comprehensive_data_inventory.py
Complete inventory of ALL available data sources across all datasets.
This is the foundation for proper Vertex AI architecture.
"""

import os
from google.cloud import bigquery
from datetime import datetime
import pandas as pd

PROJECT = os.getenv("PROJECT", "cbi-v14")
BQ = bigquery.Client(project=PROJECT)

DATASETS = [
    'forecasting_data_warehouse',
    'models_v4',
    'neural',
    'staging'
]

def get_table_inventory(dataset_id):
    """Get complete inventory of tables in a dataset."""
    query = f"""
    SELECT 
        table_id as table_name,
        row_count,
        size_bytes,
        TIMESTAMP_MILLIS(creation_time) as created
    FROM `{PROJECT}.{dataset_id}.__TABLES__`
    WHERE row_count > 0
    ORDER BY row_count DESC
    """
    return BQ.query(query).to_dataframe()

def get_table_schema(dataset_id, table_name):
    """Get schema for a specific table."""
    query = f"""
    SELECT 
        column_name,
        data_type,
        is_nullable
    FROM `{PROJECT}.{dataset_id}.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = '{table_name}'
    ORDER BY ordinal_position
    """
    return BQ.query(query).to_dataframe()

def get_date_range(dataset_id, table_name):
    """Try to get date range for tables with date/time columns."""
    # First check if table has a date column
    schema_query = f"""
    SELECT column_name
    FROM `{PROJECT}.{dataset_id}.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = '{table_name}'
      AND (data_type = 'DATE' OR data_type = 'TIMESTAMP' OR LOWER(column_name) LIKE '%date%' OR LOWER(column_name) = 'time')
    LIMIT 1
    """
    date_col_result = BQ.query(schema_query).to_dataframe()
    
    if len(date_col_result) == 0:
        return None, None, None
    
    date_col = date_col_result['column_name'].iloc[0]
    
    try:
        query = f"""
        SELECT 
            MIN({date_col}) as min_date,
            MAX({date_col}) as max_date,
            COUNT(DISTINCT {date_col}) as distinct_dates
        FROM `{PROJECT}.{dataset_id}.{table_name}`
        """
        result = BQ.query(query).to_dataframe()
        return result['min_date'].iloc[0], result['max_date'].iloc[0], result['distinct_dates'].iloc[0]
    except:
        return None, None, None

def analyze_dataset(dataset_id):
    """Comprehensive analysis of a dataset."""
    print(f"\n{'='*80}")
    print(f"DATASET: {dataset_id}")
    print(f"{'='*80}\n")
    
    inventory = get_table_inventory(dataset_id)
    
    if len(inventory) == 0:
        print(f"No tables with data found in {dataset_id}")
        return
    
    print(f"Total tables with data: {len(inventory)}")
    print(f"Total rows across all tables: {inventory['row_count'].sum():,}")
    print(f"Total size: {inventory['size_bytes'].sum() / 1024 / 1024:.2f} MB\n")
    
    print("Top 20 tables by row count:")
    print(inventory[['table_name', 'row_count']].head(20).to_string(index=False))
    
    return inventory

def analyze_time_series_potential(dataset_id, inventory):
    """Analyze which tables are suitable for time series training."""
    print(f"\n\nTIME SERIES ANALYSIS FOR {dataset_id}:")
    print("-" * 80)
    
    time_series_tables = []
    
    for _, row in inventory.head(20).iterrows():  # Check top 20 tables
        table_name = row['table_name']
        min_date, max_date, distinct_dates = get_date_range(dataset_id, table_name)
        
        if min_date:
            time_series_tables.append({
                'table': table_name,
                'rows': row['row_count'],
                'min_date': min_date,
                'max_date': max_date,
                'distinct_dates': distinct_dates
            })
            print(f"\n{table_name}:")
            print(f"  Rows: {row['row_count']:,}")
            print(f"  Date Range: {min_date} to {max_date}")
            print(f"  Distinct Dates: {distinct_dates:,}")
    
    return pd.DataFrame(time_series_tables)

def identify_feature_potential():
    """Identify total feature potential across all datasets."""
    print(f"\n\n{'='*80}")
    print("FEATURE POTENTIAL ANALYSIS")
    print(f"{'='*80}\n")
    
    total_features = 0
    
    for dataset_id in DATASETS:
        query = f"""
        SELECT 
            COUNT(DISTINCT table_name) as table_count,
            COUNT(*) as total_columns
        FROM `{PROJECT}.{dataset_id}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name IN (
            SELECT table_id 
            FROM `{PROJECT}.{dataset_id}.__TABLES__`
            WHERE row_count > 0
        )
        """
        result = BQ.query(query).to_dataframe()
        
        table_count = result['table_count'].iloc[0]
        col_count = result['total_columns'].iloc[0]
        total_features += col_count
        
        print(f"{dataset_id}:")
        print(f"  Tables: {table_count}")
        print(f"  Total Columns: {col_count}")
    
    print(f"\nTOTAL RAW FEATURE POTENTIAL: {total_features} columns")
    print(f"Vertex AI Limit: 1,000 columns")
    print(f"Feature Selection Ratio: {total_features}/1000 = {total_features/1000:.1f}x (need to select top features)")

def main():
    """Run comprehensive data inventory."""
    print(f"\n{'='*80}")
    print(f"COMPREHENSIVE DATA INVENTORY")
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Project: {PROJECT}")
    print(f"{'='*80}\n")
    
    all_inventories = {}
    all_time_series = {}
    
    # Analyze each dataset
    for dataset_id in DATASETS:
        try:
            inventory = analyze_dataset(dataset_id)
            if inventory is not None and len(inventory) > 0:
                all_inventories[dataset_id] = inventory
                time_series = analyze_time_series_potential(dataset_id, inventory)
                if len(time_series) > 0:
                    all_time_series[dataset_id] = time_series
        except Exception as e:
            print(f"Error analyzing {dataset_id}: {e}")
    
    # Feature potential
    identify_feature_potential()
    
    # Summary
    print(f"\n\n{'='*80}")
    print("EXECUTIVE SUMMARY")
    print(f"{'='*80}\n")
    
    total_tables = sum(len(inv) for inv in all_inventories.values())
    total_rows = sum(inv['row_count'].sum() for inv in all_inventories.values())
    
    print(f"Total Datasets Analyzed: {len(DATASETS)}")
    print(f"Total Tables with Data: {total_tables}")
    print(f"Total Rows Available: {total_rows:,}")
    print(f"\nTime Series Tables Found: {sum(len(ts) for ts in all_time_series.values())}")
    
    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("="*80)
    print("""
1. Review time series tables - identify which have 50+ years of data
2. Design feature consolidation strategy
3. Determine how to join disparate time series (daily, weekly, monthly)
4. Design feature engineering pipeline
5. Implement feature selection (reduce to 1,000 columns for Vertex AI)
6. Create Trump-era filtered training datasets
    """)

if __name__ == "__main__":
    main()

