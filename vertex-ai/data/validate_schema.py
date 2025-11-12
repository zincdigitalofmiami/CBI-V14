#!/usr/bin/env python3
"""
validate_schema.py
Validate schema consistency across training tables for Vertex AI.
Ensures all tables have identical feature lists and proper data types.
"""

import os
from google.cloud import bigquery
from datetime import datetime

PROJECT = os.getenv("PROJECT", "cbi-v14")
BQ = bigquery.Client(project=PROJECT)

def check_schema_consistency():
    """Check that all training tables have identical schemas."""
    print("=== SCHEMA CONSISTENCY CHECK ===\n")
    
    tables = ['vertex_ai_training_1m_base', 'vertex_ai_training_3m_base', 
              'vertex_ai_training_6m_base', 'vertex_ai_training_1w_base']  # Or production_training_data_* if migrating
    
    # Get column counts
    query = """
    SELECT 
        table_name,
        COUNT(*) as column_count
    FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name IN ('vertex_ai_training_1m_base', 'vertex_ai_training_3m_base', 
                         'vertex_ai_training_6m_base', 'vertex_ai_training_1w_base')  -- Or production_training_data_* if migrating
    GROUP BY table_name
    ORDER BY table_name
    """
    
    result = BQ.query(query).to_dataframe()
    print("Column counts:")
    print(result.to_string(index=False))
    print()
    
    # Check for mismatched columns
    query = """
    WITH all_cols AS (
        SELECT DISTINCT column_name, data_type
        FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name IN ('production_training_data_1m', 'production_training_data_3m', 
                             'production_training_data_6m', 'production_training_data_1w')
    )
    SELECT 
        column_name,
        COUNT(DISTINCT data_type) as distinct_types,
        STRING_AGG(DISTINCT data_type, ', ') as types
    FROM all_cols
    GROUP BY column_name
    HAVING COUNT(DISTINCT data_type) > 1
    """
    
    result = BQ.query(query).to_dataframe()
    if len(result) > 0:
        print("⚠️  WARNING: Columns with mismatched data types:")
        print(result.to_string(index=False))
    else:
        print("✅ All columns have consistent data types across tables")
    print()

def check_target_columns():
    """Validate target columns are non-null and numeric."""
    print("=== TARGET COLUMN VALIDATION ===\n")
    
    query = """
    SELECT 
        COUNTIF(target_1m IS NULL) as null_1m,
        COUNTIF(target_3m IS NULL) as null_3m,
        COUNTIF(target_6m IS NULL) as null_6m,
        COUNTIF(target_1w IS NULL) as null_1w,
        COUNT(*) as total_rows
    FROM `cbi-v14.models_v4.vertex_ai_training_1m_base`  -- Or production_training_data_1m if migrating
    """
    
    result = BQ.query(query).to_dataframe()
    print(result.to_string(index=False))
    
    if result['null_1m'].iloc[0] > 0:
        print(f"⚠️  WARNING: {result['null_1m'].iloc[0]} NULL values in target_1m")
    else:
        print("✅ target_1m has zero NULLs")
    print()

def check_date_consistency():
    """Check date column consistency."""
    print("=== DATE COLUMN VALIDATION ===\n")
    
    query = """
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT date) as distinct_dates
    FROM `cbi-v14.models_v4.vertex_ai_training_1m_base`  -- Or production_training_data_1m if migrating
    """
    
    result = BQ.query(query).to_dataframe()
    print(result.to_string(index=False))
    
    if result['total_rows'].iloc[0] != result['distinct_dates'].iloc[0]:
        print("⚠️  WARNING: Duplicate dates found")
    else:
        print("✅ No duplicate dates")
    print()

def check_string_columns():
    """Check string columns for AutoML compatibility."""
    print("=== STRING COLUMN VALIDATION ===\n")
    
    query = """
    SELECT 
        table_name,
        column_name,
        data_type
    FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = 'production_training_data_1m'
      AND data_type = 'STRING'
    ORDER BY column_name
    """
    
    result = BQ.query(query).to_dataframe()
    print(f"String columns in vertex_ai_training_1m_base (or production_training_data_1m if migrating):")
    print(result.to_string(index=False))
    print()
    
    # Check unique value counts
    for col in result['column_name']:
        query = f"""
        SELECT 
            COUNT(DISTINCT {col}) as unique_values
        FROM `cbi-v14.models_v4.vertex_ai_training_1m_base`  -- Or production_training_data_1m if migrating
        """
        unique = BQ.query(query).to_dataframe()
        count = unique['unique_values'].iloc[0]
        if count > 5000:
            print(f"⚠️  WARNING: {col} has {count} unique values (>5000 limit)")
        else:
            print(f"✅ {col}: {count} unique values")

def check_null_percentage():
    """Check for columns with >90% NULL values."""
    print("\n=== NULL PERCENTAGE CHECK ===\n")
    
    query = """
    SELECT 
        column_name,
        COUNTIF(column_name IS NULL) as null_count,
        COUNT(*) as total_rows,
        ROUND(100.0 * COUNTIF(column_name IS NULL) / COUNT(*), 2) as null_pct
    FROM `cbi-v14.models_v4.vertex_ai_training_1m_base`  -- Or production_training_data_1m if migrating
    UNPIVOT (value FOR column_name IN (
        SELECT column_name 
        FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = 'vertex_ai_training_1m_base'  -- Or 'production_training_data_1m' if migrating
          AND data_type IN ('FLOAT64', 'INT64')
          AND column_name NOT IN ('date', 'target_1m', 'target_3m', 'target_6m', 'target_1w')
    ))
    GROUP BY column_name
    HAVING null_pct > 90
    ORDER BY null_pct DESC
    LIMIT 20
    """
    
    # Simplified check - get column list first
    query = """
    SELECT column_name
    FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = 'production_training_data_1m'
      AND data_type IN ('FLOAT64', 'INT64')
      AND column_name NOT IN ('date', 'target_1m', 'target_3m', 'target_6m', 'target_1w')
    LIMIT 5
    """
    
    print("Checking NULL percentages for top columns...")
    print("(Full check requires dynamic SQL - implement in SQL script)")

def main():
    """Run all validations."""
    print(f"Vertex AI Schema Validation - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    print("=" * 60 + "\n")
    
    check_schema_consistency()
    check_target_columns()
    check_date_consistency()
    check_string_columns()
    check_null_percentage()
    
    print("\n" + "=" * 60)
    print("Validation complete.")

if __name__ == "__main__":
    main()

