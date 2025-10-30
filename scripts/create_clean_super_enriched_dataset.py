#!/usr/bin/env python3
"""
Create Clean Super-Enriched Dataset
Remove all-NULL columns, handle sparse data intelligently
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("CLEANING SUPER-ENRICHED DATASET")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Step 1: Identify columns with all NULL/zero values
print("Step 1: Identifying all-NULL columns...")
cols_query = """
SELECT column_name
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'training_dataset_super_enriched'
AND column_name NOT IN ('date', 'target_1w', 'target_1m', 'target_3m', 'target_6m')
ORDER BY column_name
"""

cols_df = client.query(cols_query).to_dataframe()
all_null_cols = []

for col in cols_df['column_name'].tolist():
    check_query = f"""
    SELECT COUNT(*) as non_null_count
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    WHERE {col} IS NOT NULL AND {col} != 0
    """
    result = client.query(check_query).to_dataframe()
    if result['non_null_count'].iloc[0] == 0:
        all_null_cols.append(col)

print(f"Found {len(all_null_cols)} columns with all NULL/zero values")
print(f"Removing these columns...")
print()

# Step 2: Get valid columns
valid_cols = [col for col in cols_df['column_name'].tolist() if col not in all_null_cols]
valid_cols_str = ', '.join(valid_cols)
valid_cols_str = 'date, ' + valid_cols_str + ', target_1w, target_1m, target_3m, target_6m'

# Step 3: Create clean dataset with intelligent handling
print("Step 2: Creating clean dataset with sparse data handling...")

clean_query = f"""
CREATE OR REPLACE TABLE `cbi-v14.models_v4.training_dataset_super_enriched` AS
SELECT DISTINCT
    date,
    {valid_cols_str},
    target_1w,
    target_1m,
    target_3m,
    target_6m
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
ORDER BY date
"""

job = client.query(clean_query)
result = job.result()

# Step 4: Verify
verify_query = """
SELECT 
    COUNT(*) as total_rows,
    COUNT(DISTINCT date) as unique_dates
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
"""

verify_df = client.query(verify_query).to_dataframe()
print(f"✅ Clean dataset created: {verify_df['total_rows'].iloc[0]} rows, {verify_df['unique_dates'].iloc[0]} unique dates")

# Check feature count
feature_check = """
SELECT COUNT(*) as feature_count
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'training_dataset_super_enriched'
AND column_name NOT IN ('date', 'target_1w', 'target_1m', 'target_3m', 'target_6m')
"""

feature_df = client.query(feature_check).to_dataframe()
print(f"✅ Features: {feature_df['feature_count'].iloc[0]} (was 197, removed {len(all_null_cols)} all-NULL columns)")
print()

print("=" * 80)
print("CLEAN DATASET READY FOR TRAINING")
print("=" * 80)
print(f"Removed: {len(all_null_cols)} all-NULL columns")
print(f"Retained: {feature_df['feature_count'].iloc[0]} features")
print(f"Rows: {verify_df['total_rows'].iloc[0]}")
print("=" * 80)












