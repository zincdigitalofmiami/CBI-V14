#!/usr/bin/env python3
"""
Smart CSV Loader for BigQuery
Automatically handles column names, data types, and common CSV issues
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
import sys
import re
import os

def clean_column_name(col):
    """Fix column names for BigQuery compatibility"""
    # Replace special characters with underscore
    col = re.sub(r'[^a-zA-Z0-9_]', '_', str(col))
    # Remove leading numbers
    col = re.sub(r'^[0-9]+', '', col)
    # Replace multiple underscores with single
    col = re.sub(r'_+', '_', col)
    # Remove trailing underscores
    col = col.strip('_')
    # If empty, give it a name
    if not col:
        col = 'column'
    return col.lower()

def infer_schema(df):
    """Automatically determine BigQuery schema from dataframe"""
    schema = []
    for col in df.columns:
        dtype = df[col].dtype
        
        # Determine BigQuery type
        if pd.api.types.is_integer_dtype(dtype):
            bq_type = "INTEGER"
        elif pd.api.types.is_float_dtype(dtype):
            bq_type = "FLOAT"
        elif pd.api.types.is_bool_dtype(dtype):
            bq_type = "BOOLEAN"
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            bq_type = "TIMESTAMP"
        else:
            bq_type = "STRING"
            
        schema.append(bigquery.SchemaField(col, bq_type))
    
    return schema

def smart_load_csv(csv_path, project_id='cbi-v13', dataset_id='raw', table_name=None):
    """
    Intelligently load any CSV into BigQuery
    """
    print(f"\n📊 Processing: {csv_path}")
    
    # Generate table name from filename if not provided
    if not table_name:
        base_name = os.path.basename(csv_path)
        table_name = clean_column_name(base_name.replace('.csv', ''))
    
    # Try different encodings and delimiters
    encodings = ['utf-8', 'latin1', 'cp1252']
    delimiters = [',', '\t', '|', ';']
    
    df = None
    for encoding in encodings:
        for delimiter in delimiters:
            try:
                df = pd.read_csv(csv_path, encoding=encoding, sep=delimiter)
                if len(df.columns) > 1:  # Successful parse
                    print(f"   ✓ Detected: {encoding} encoding, '{delimiter}' delimiter")
                    break
            except:
                continue
        if df is not None and len(df.columns) > 1:
            break
    
    if df is None:
        print(f"   ❌ Could not parse {csv_path}")
        return False
    
    # Clean column names
    original_cols = df.columns.tolist()
    df.columns = [clean_column_name(col) for col in df.columns]
    
    # Handle duplicate column names
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique():
        cols[cols[cols == dup].index.values.tolist()] = [dup + '_' + str(i) if i != 0 else dup for i in range(sum(cols == dup))]
    df.columns = cols
    
    print(f"   ✓ Columns cleaned: {len(df.columns)} columns")
    
    # Convert date columns
    for col in df.columns:
        if 'date' in col.lower() or 'time' in col.lower():
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                print(f"   ✓ Converted {col} to datetime")
            except:
                pass
    
    # Handle special number formats (percentages, currency)
    for col in df.columns:
        if df[col].dtype == 'object':
            # Try to convert percentage strings
            if df[col].astype(str).str.contains('%', na=False).any():
                df[col] = df[col].str.replace('%', '').str.replace(',', '')
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce') / 100
                    print(f"   ✓ Converted {col} from percentage")
                except:
                    pass
            # Try to convert currency/number strings
            elif df[col].astype(str).str.contains('[$,]', na=False, regex=True).any():
                df[col] = df[col].str.replace('$', '').str.replace(',', '')
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    print(f"   ✓ Converted {col} from currency")
                except:
                    pass
    
    # Upload to BigQuery
    client = bigquery.Client(project=project_id)
    table_id = f"{project_id}.{dataset_id}.{table_name}"
    
    # Configure load job
    job_config = bigquery.LoadJobConfig(
        schema=infer_schema(df),
        write_disposition="WRITE_TRUNCATE",  # Replace table if exists
    )
    
    try:
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait for completion
        
        print(f"\n✅ SUCCESS: Loaded {len(df)} rows to {table_id}")
        print(f"   Original columns: {original_cols[:3]}...")
        print(f"   Cleaned columns: {df.columns.tolist()[:3]}...")
        
        # Show sample query
        print(f"\n📝 Test query:")
        print(f"   SELECT * FROM `{table_id}` LIMIT 5")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error loading to BigQuery: {e}")
        return False

def batch_load_all_csvs(directory='.', project_id='cbi-v13'):
    """Load all CSV files in a directory"""
    csv_files = [f for f in os.listdir(directory) if f.endswith('.csv')]
    
    print(f"\n🚀 Found {len(csv_files)} CSV files to process")
    
    results = []
    for csv_file in csv_files:
        result = smart_load_csv(
            csv_path=os.path.join(directory, csv_file),
            project_id=project_id
        )
        results.append((csv_file, result))
    
    # Summary
    print("\n" + "="*60)
    print("📊 LOADING SUMMARY")
    print("="*60)
    
    for filename, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {filename}")
    
    success_count = sum(1 for _, s in results if s)
    print(f"\n✅ Successfully loaded: {success_count}/{len(csv_files)} files")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Load specific file
        smart_load_csv(sys.argv[1])
    else:
        # Load all CSVs in current directory
        batch_load_all_csvs()
