#!/usr/bin/env python3
"""
Find all columns that are 100% NULL in training view
"""
from google.cloud import bigquery
import sys

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"
VIEW_NAME = "train_1w"
TARGET_COL = "target_1w"

client = bigquery.Client(project=PROJECT_ID)

print("="*80)
print("🔍 FINDING ALL NULL COLUMNS")
print("="*80)
print(f"View: {VIEW_NAME}")
print(f"Target: {TARGET_COL}")
print()

# Get all columns in view
query = f"""
SELECT column_name
FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = '{VIEW_NAME}'
AND column_name NOT IN ('date', '{TARGET_COL}', 'target_1m', 'target_3m', 'target_6m')
ORDER BY column_name
"""
cols_df = client.query(query).to_dataframe()
all_columns = cols_df['column_name'].tolist()

print(f"Checking {len(all_columns)} columns...")
print()

all_null_cols = []
checked = 0

# Check each column
for col in all_columns:
    checked += 1
    try:
        q = f"""
        SELECT 
          COUNT(*) as total,
          COUNTIF(`{col}` IS NOT NULL) as non_null
        FROM `{PROJECT_ID}.{DATASET_ID}.{VIEW_NAME}`
        WHERE {TARGET_COL} IS NOT NULL
        """
        r = client.query(q).to_dataframe()
        total = int(r.iloc[0]['total'])
        non_null = int(r.iloc[0]['non_null'])
        
        if non_null == 0 and total > 0:
            all_null_cols.append(col)
            print(f"  ❌ {col}: ALL NULL ({non_null}/{total})")
        
        if checked % 50 == 0:
            print(f"  ... checked {checked}/{len(all_columns)} columns ...")
            
    except Exception as e:
        error_str = str(e).lower()
        if 'not found' in error_str or 'unknown' in error_str:
            pass
        else:
            print(f"  ⚠️  {col}: Error - {str(e)[:80]}")

print()
print("="*80)
print(f"📋 RESULTS: Found {len(all_null_cols)} all-NULL columns")
print("="*80)

if all_null_cols:
    print("\nColumns to exclude (add to EXCEPT clause):")
    for col in sorted(all_null_cols):
        print(f"    {col},")
    
    print("\n" + "="*80)
    print("COPY THIS TO TRAINING SQL:")
    print("="*80)
    for col in sorted(all_null_cols):
        print(f"    {col},  -- All NULL")
else:
    print("\n✅ No all-NULL columns found!")

print("="*80)
sys.exit(0)










