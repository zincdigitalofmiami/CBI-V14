#!/usr/bin/env python3
"""
audit_data_sources.py
Audit all BigQuery data sources for Vertex AI training preparation.
Identifies available features, data coverage, and schema consistency.
"""

import os
from google.cloud import bigquery
from datetime import datetime

PROJECT = os.getenv("PROJECT", "cbi-v14")
BQ = bigquery.Client(project=PROJECT)

def audit_production_tables():
    """Audit vertex_ai_training_*_base tables (or production_training_data_* if migrating)."""
    print("=== PRODUCTION TRAINING DATA AUDIT ===\n")
    
    query = """
    SELECT 
        table_name,
        COUNT(*) as column_count,
        COUNTIF(data_type = 'FLOAT64') as float_cols,
        COUNTIF(data_type = 'INT64') as int_cols,
        COUNTIF(data_type = 'STRING') as string_cols,
        COUNTIF(data_type = 'DATE') as date_cols
    FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name LIKE 'vertex_ai_training%_base'  -- Or 'production_training_data%' if migrating
    GROUP BY table_name
    ORDER BY table_name
    """
    
    results = BQ.query(query).to_dataframe()
    print(results.to_string(index=False))
    print()
    
    # Check row counts and date ranges
    for table in ['vertex_ai_training_1m_base', 'vertex_ai_training_3m_base', 
                  'vertex_ai_training_6m_base', 'vertex_ai_training_1w_base']:  # Or production_training_data_* if migrating
        query = f"""
        SELECT 
            MIN(date) as min_date,
            MAX(date) as max_date,
            COUNT(*) as total_rows,
            COUNT(DISTINCT date) as distinct_dates
        FROM `cbi-v14.models_v4.{table}`
        """
        result = BQ.query(query).to_dataframe()
        print(f"{table}:")
        print(result.to_string(index=False))
        print()

def audit_feature_coverage():
    """Check feature coverage across tables."""
    print("=== FEATURE COVERAGE AUDIT ===\n")
    
    query = """
    WITH cols_1m AS (
        SELECT column_name 
        FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = 'vertex_ai_training_1m_base'  -- Or 'production_training_data_1m' if migrating
    ),
    cols_3m AS (
        SELECT column_name 
        FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = 'vertex_ai_training_3m_base'  -- Or 'production_training_data_3m' if migrating
    )
    SELECT 
        COUNT(DISTINCT c1.column_name) as only_in_1m,
        COUNT(DISTINCT c3.column_name) as only_in_3m,
        (SELECT COUNT(*) FROM cols_1m c1 INNER JOIN cols_3m c3 ON c1.column_name = c3.column_name) as common_cols
    FROM cols_1m c1
    FULL OUTER JOIN cols_3m c3 ON c1.column_name = c3.column_name
    """
    
    result = BQ.query(query).to_dataframe()
    print(result.to_string(index=False))
    print()

def audit_data_sources():
    """Audit all data source datasets."""
    print("=== DATA SOURCE DATASETS AUDIT ===\n")
    
    datasets = ['forecasting_data_warehouse', 'neural', 'staging']
    
    for dataset in datasets:
        query = f"""
        SELECT 
            COUNT(*) as table_count,
            SUM(row_count) as total_rows,
            SUM(size_bytes) as total_bytes
        FROM `cbi-v14.{dataset}.__TABLES__`
        WHERE row_count > 0
        """
        result = BQ.query(query).to_dataframe()
        print(f"{dataset}:")
        print(result.to_string(index=False))
        print()

def audit_target_columns():
    """Check target column quality."""
    print("=== TARGET COLUMN AUDIT ===\n")
    
    query = """
    SELECT 
        COUNTIF(target_1m IS NULL) as null_1m,
        COUNTIF(target_3m IS NULL) as null_3m,
        COUNTIF(target_6m IS NULL) as null_6m,
        COUNT(*) as total_rows
    FROM `cbi-v14.models_v4.vertex_ai_training_1m_base`  -- Or production_training_data_1m if migrating
    """
    
    result = BQ.query(query).to_dataframe()
    print(result.to_string(index=False))
    print()

def main():
    """Run all audits."""
    print(f"Vertex AI Data Source Audit - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    print("=" * 60 + "\n")
    
    audit_production_tables()
    audit_feature_coverage()
    audit_data_sources()
    audit_target_columns()
    
    print("=" * 60)
    print("Audit complete.")

if __name__ == "__main__":
    main()

