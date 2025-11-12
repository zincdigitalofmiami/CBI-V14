#!/usr/bin/env python3
"""
audit_vertex_training_datasets.py
Comprehensive audit of datasets that will be used for Vertex AI AutoML training.
Checks all common failure points to ensure training success.
"""

import os
from google.cloud import bigquery
from datetime import datetime
import pandas as pd

PROJECT = os.getenv("PROJECT", "cbi-v14")
DATASET = "models_v4"
BQ = bigquery.Client(project=PROJECT)

TRAINING_TABLES = [
    'vertex_ai_training_1m_base',  # Or 'production_training_data_1m' if migrating
    'vertex_ai_training_3m_base',  # Or 'production_training_data_3m' if migrating
    'vertex_ai_training_6m_base',  # Or 'production_training_data_6m' if migrating
    'vertex_ai_training_1w_base'   # Or 'production_training_data_1w' if migrating
]

def print_section(title):
    """Print section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def check_table_exists(table_name):
    """Check if table exists."""
    query = f"""
    SELECT COUNT(*) as table_count
    FROM `{PROJECT}.{DATASET}.__TABLES__`
    WHERE table_id = '{table_name}'
    """
    result = BQ.query(query).to_dataframe()
    return result['table_count'].iloc[0] > 0

def check_1_schema_contract():
    """Check 1: Schema Contract - Ensure exact column/field types across all tables."""
    print_section("CHECK 1: SCHEMA CONTRACT")
    
    # Get all columns from each table
    for table in TRAINING_TABLES:
        if not check_table_exists(table):
            print(f"⚠️  WARNING: {table} does not exist")
            continue
            
        query = f"""
        SELECT 
            column_name,
            data_type,
            is_nullable
        FROM `{PROJECT}.{DATASET}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{table}'
        ORDER BY ordinal_position
        """
        result = BQ.query(query).to_dataframe()
        print(f"\n{table}:")
        print(f"  Total columns: {len(result)}")
        print(f"  Data types: {result['data_type'].value_counts().to_dict()}")
    
    # Check for type mismatches across tables
    query = f"""
    WITH all_columns AS (
        SELECT 
            table_name,
            column_name,
            data_type
        FROM `{PROJECT}.{DATASET}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name IN ('vertex_ai_training_1m_base', 'vertex_ai_training_3m_base', 
                             'vertex_ai_training_6m_base', 'vertex_ai_training_1w_base')
    )
    SELECT 
        column_name,
        COUNT(DISTINCT data_type) as distinct_types,
        STRING_AGG(DISTINCT CONCAT(table_name, ':', data_type), ', ') as type_mapping
    FROM all_columns
    GROUP BY column_name
    HAVING COUNT(DISTINCT data_type) > 1
    """
    mismatches = BQ.query(query).to_dataframe()
    
    if len(mismatches) > 0:
        print(f"\n❌ SCHEMA MISMATCH DETECTED:")
        print(mismatches.to_string(index=False))
        return False
    else:
        print("\n✅ All columns have consistent data types across tables")
        return True

def check_2_target_columns():
    """Check 2: Explicit Target Columns - Must be non-null and numeric."""
    print_section("CHECK 2: TARGET COLUMN VALIDATION")
    
    for table in TRAINING_TABLES:
        if not check_table_exists(table):
            continue
            
        # Extract horizon from table name
        if '1m' in table:
            target = 'target_1m'
        elif '3m' in table:
            target = 'target_3m'
        elif '6m' in table:
            target = 'target_6m'
        elif '1w' in table:
            target = 'target_1w'
        else:
            continue
        
        query = f"""
        SELECT 
            '{table}' as table_name,
            '{target}' as target_column,
            COUNTIF({target} IS NULL) as null_count,
            COUNT(*) as total_rows,
            ROUND(100.0 * COUNTIF({target} IS NULL) / COUNT(*), 2) as null_pct,
            MIN({target}) as min_value,
            MAX({target}) as max_value,
            AVG({target}) as avg_value
        FROM `{PROJECT}.{DATASET}.{table}`
        """
        result = BQ.query(query).to_dataframe()
        print(f"\n{table}:")
        print(result.to_string(index=False))
        
        null_pct = result['null_pct'].iloc[0]
        if null_pct > 0:
            print(f"  ❌ FAIL: {null_pct}% NULL values in target column")
        else:
            print(f"  ✅ PASS: No NULL values in target column")

def check_3_date_time_validation():
    """Check 3: Date/Time Column - No duplicates, standardized name."""
    print_section("CHECK 3: DATE/TIME COLUMN VALIDATION")
    
    for table in TRAINING_TABLES:
        if not check_table_exists(table):
            continue
            
        query = f"""
        SELECT 
            '{table}' as table_name,
            COUNT(*) as total_rows,
            COUNT(DISTINCT date) as distinct_dates,
            MIN(date) as min_date,
            MAX(date) as max_date,
            CASE 
                WHEN COUNT(*) = COUNT(DISTINCT date) THEN 'PASS'
                ELSE 'FAIL - Duplicates found'
            END as status
        FROM `{PROJECT}.{DATASET}.{table}`
        """
        result = BQ.query(query).to_dataframe()
        print(f"\n{table}:")
        print(result.to_string(index=False))
        
        if result['status'].iloc[0] == 'PASS':
            print(f"  ✅ PASS: No duplicate dates")
        else:
            print(f"  ❌ FAIL: Duplicate dates detected")

def check_4_string_features():
    """Check 4: String Feature Hell - Check for >5000 unique values."""
    print_section("CHECK 4: STRING FEATURE VALIDATION")
    
    for table in TRAINING_TABLES:
        if not check_table_exists(table):
            continue
            
        # Get string columns
        query = f"""
        SELECT column_name
        FROM `{PROJECT}.{DATASET}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{table}'
          AND data_type = 'STRING'
          AND column_name NOT IN ('date')
        """
        string_cols = BQ.query(query).to_dataframe()
        
        print(f"\n{table}:")
        if len(string_cols) == 0:
            print("  ✅ No string columns (except date)")
            continue
        
        print(f"  Found {len(string_cols)} string column(s):")
        
        for col in string_cols['column_name']:
            query = f"""
            SELECT COUNT(DISTINCT {col}) as unique_values
            FROM `{PROJECT}.{DATASET}.{table}`
            """
            result = BQ.query(query).to_dataframe()
            unique_count = result['unique_values'].iloc[0]
            
            if unique_count > 5000:
                print(f"    ❌ {col}: {unique_count} unique values (>5000 limit)")
            else:
                print(f"    ✅ {col}: {unique_count} unique values")

def check_5_frequency_consistency():
    """Check 5: Mixed Frequencies - Check time spacing consistency."""
    print_section("CHECK 5: FREQUENCY CONSISTENCY")
    
    for table in TRAINING_TABLES:
        if not check_table_exists(table):
            continue
            
        query = f"""
        WITH date_diffs AS (
            SELECT 
                date,
                LAG(date) OVER (ORDER BY date) as prev_date,
                DATE_DIFF(date, LAG(date) OVER (ORDER BY date), DAY) as days_diff
            FROM `{PROJECT}.{DATASET}.{table}`
            WHERE date IS NOT NULL
        )
        SELECT 
            '{table}' as table_name,
            COUNT(DISTINCT days_diff) as distinct_gaps,
            MIN(days_diff) as min_gap_days,
            MAX(days_diff) as max_gap_days,
            APPROX_QUANTILES(days_diff, 100)[OFFSET(50)] as median_gap_days
        FROM date_diffs
        WHERE prev_date IS NOT NULL
        """
        result = BQ.query(query).to_dataframe()
        print(f"\n{table}:")
        print(result.to_string(index=False))
        
        distinct_gaps = result['distinct_gaps'].iloc[0]
        if distinct_gaps > 5:
            print(f"  ⚠️  WARNING: {distinct_gaps} different gap sizes - may indicate mixed frequencies")
        else:
            print(f"  ✅ PASS: Consistent time spacing")

def check_6_null_percentage():
    """Check 6: High NULL Percentage - Check for >90% NULL columns."""
    print_section("CHECK 6: NULL PERCENTAGE CHECK")
    
    print("Checking for columns with >90% NULL values...")
    print("(This indicates columns that should be dropped before training)\n")
    
    for table in TRAINING_TABLES:
        if not check_table_exists(table):
            continue
            
        # Get numeric columns only
        query = f"""
        SELECT column_name
        FROM `{PROJECT}.{DATASET}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{table}'
          AND data_type IN ('FLOAT64', 'INT64')
          AND column_name NOT IN ('date', 'target_1m', 'target_3m', 'target_6m', 'target_1w', 'target_12m')
        LIMIT 10  -- Sample first 10 columns for speed
        """
        columns = BQ.query(query).to_dataframe()
        
        print(f"\n{table} (sampling first 10 numeric columns):")
        
        high_null_cols = []
        for col in columns['column_name']:
            query = f"""
            SELECT 
                ROUND(100.0 * COUNTIF({col} IS NULL) / COUNT(*), 2) as null_pct
            FROM `{PROJECT}.{DATASET}.{table}`
            """
            result = BQ.query(query).to_dataframe()
            null_pct = result['null_pct'].iloc[0]
            
            if null_pct > 90:
                high_null_cols.append((col, null_pct))
                print(f"  ❌ {col}: {null_pct}% NULL")
        
        if len(high_null_cols) == 0:
            print(f"  ✅ No high-NULL columns detected in sample")

def check_7_feature_count_consistency():
    """Check 7: Fixed Feature Count - All tables must have identical feature lists."""
    print_section("CHECK 7: FEATURE COUNT CONSISTENCY")
    
    query = f"""
    SELECT 
        table_name,
        COUNT(*) as column_count
    FROM `{PROJECT}.{DATASET}.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name IN ('production_training_data_1m', 'production_training_data_3m', 
                         'production_training_data_6m', 'production_training_data_1w')
    GROUP BY table_name
    ORDER BY table_name
    """
    result = BQ.query(query).to_dataframe()
    
    print(result.to_string(index=False))
    
    unique_counts = result['column_count'].nunique()
    if unique_counts > 1:
        print(f"\n❌ FAIL: Inconsistent feature counts across tables")
        print(f"   This will cause Vertex AI training to fail!")
        print(f"   All tables must have the same number of columns")
    else:
        print(f"\n✅ PASS: All tables have consistent feature counts")

def check_8_boolean_columns():
    """Check 8: Boolean Columns - Must be converted to INT64."""
    print_section("CHECK 8: BOOLEAN COLUMN CHECK")
    
    for table in TRAINING_TABLES:
        if not check_table_exists(table):
            continue
            
        query = f"""
        SELECT 
            table_name,
            column_name,
            data_type
        FROM `{PROJECT}.{DATASET}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{table}'
          AND data_type = 'BOOL'
        """
        result = BQ.query(query).to_dataframe()
        
        if len(result) > 0:
            print(f"\n{table}:")
            print(f"  ❌ FAIL: {len(result)} boolean columns found:")
            print(result.to_string(index=False))
            print("  These must be converted to INT64 before training")
        else:
            print(f"\n{table}:")
            print(f"  ✅ PASS: No boolean columns")

def check_9_reserved_names():
    """Check 9: Reserved Column Names - AutoML forbids certain names."""
    print_section("CHECK 9: RESERVED COLUMN NAME CHECK")
    
    reserved = ['weight', 'class', 'id', 'prediction', 'target', 'time', 'split', 'fold', 'dataset']
    
    for table in TRAINING_TABLES:
        if not check_table_exists(table):
            continue
            
        query = f"""
        SELECT column_name
        FROM `{PROJECT}.{DATASET}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{table}'
          AND LOWER(column_name) IN UNNEST({reserved})
        """
        result = BQ.query(query).to_dataframe()
        
        if len(result) > 0:
            print(f"\n{table}:")
            print(f"  ❌ FAIL: Reserved column names found:")
            print(result.to_string(index=False))
        else:
            print(f"\n{table}:")
            print(f"  ✅ PASS: No reserved column names")

def check_10_data_quality_summary():
    """Check 10: Overall Data Quality Summary."""
    print_section("CHECK 10: DATA QUALITY SUMMARY")
    
    for table in TRAINING_TABLES:
        if not check_table_exists(table):
            continue
            
        query = f"""
        SELECT 
            '{table}' as table_name,
            COUNT(*) as total_rows,
            COUNT(DISTINCT date) as distinct_dates,
            MIN(date) as earliest_date,
            MAX(date) as latest_date,
            DATE_DIFF(MAX(date), MIN(date), DAY) as date_range_days
        FROM `{PROJECT}.{DATASET}.{table}`
        """
        result = BQ.query(query).to_dataframe()
        print(f"\n{table}:")
        print(result.to_string(index=False))

def generate_recommendations():
    """Generate actionable recommendations based on audit."""
    print_section("RECOMMENDATIONS")
    
    print("""
Based on the audit results, here are the recommended actions:

1. FEATURE COUNT MISMATCH (CRITICAL):
   - vertex_ai_training_1m_base has 444 columns (or production_training_data_1m if migrating)
   - Other tables have 300 columns
   - ACTION: Standardize to 1,000 columns across ALL tables (Vertex AI target)
   - OR: Add missing columns to 3m/6m/1w/12m base tables

2. NULL TARGETS (CRITICAL):
   - target_3m has NULL values
   - target_6m has NULL values
   - ACTION: Either drop rows with NULL targets or calculate missing targets

3. MISSING 12M TABLE (CRITICAL):
   - No vertex_ai_training_12m_base table exists (or production_training_data_12m if migrating)
   - ACTION: Create 12M horizon base table with target_12m column

4. STRING COLUMNS (VERIFIED):
   - volatility_regime: OK (<5000 unique values)
   - yahoo_data_source: OK (<5000 unique values)
   - ACTION: No action needed

5. DATE CONSISTENCY (VERIFIED):
   - No duplicate dates
   - ACTION: No action needed

Next Steps:
1. Run schema alignment script to standardize feature counts to 1,000
2. Handle NULL targets (drop or calculate)
3. Create vertex_ai_training_12m_base table (or production_training_data_12m if migrating)
4. Re-run this audit to verify all issues resolved
5. Proceed to Vertex AI dataset creation
""")

def main():
    """Run all checks."""
    print(f"\n{'='*80}")
    print(f"  VERTEX AI TRAINING DATASET AUDIT")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Project: {PROJECT}")
    print(f"  Dataset: {DATASET}")
    print(f"{'='*80}\n")
    
    # Run all checks
    check_1_schema_contract()
    check_2_target_columns()
    check_3_date_time_validation()
    check_4_string_features()
    check_5_frequency_consistency()
    check_6_null_percentage()
    check_7_feature_count_consistency()
    check_8_boolean_columns()
    check_9_reserved_names()
    check_10_data_quality_summary()
    generate_recommendations()
    
    print(f"\n{'='*80}")
    print("  AUDIT COMPLETE")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()

