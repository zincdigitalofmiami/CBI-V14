#!/usr/bin/env python3
"""
Comprehensive NULL Audit - Find all all-NULL columns and diagnose root causes
"""
from google.cloud import bigquery
import pandas as pd
from datetime import datetime
import sys

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"
BASE_TABLE = "training_dataset_super_enriched"
VIEW_NAME = "train_1w"
TARGET_COL = "target_1w"

client = bigquery.Client(project=PROJECT_ID)

print("="*80)
print("🔍 COMPREHENSIVE NULL AUDIT")
print("="*80)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Base Table: {BASE_TABLE}")
print(f"Training View: {VIEW_NAME}")
print("="*80)

# Step 1: Find all columns in base table
print("\n1️⃣  FINDING ALL COLUMNS IN BASE TABLE...")
query = f"""
SELECT column_name, data_type
FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = '{BASE_TABLE}'
AND column_name NOT IN ('date')
ORDER BY column_name
"""
cols_df = client.query(query).to_dataframe()
all_columns = cols_df['column_name'].tolist()

print(f"  ✅ Found {len(all_columns)} columns in base table")

# Step 2: Check for all-NULL columns
print("\n2️⃣  CHECKING FOR ALL-NULL COLUMNS...")
all_null_cols = []
partial_null_cols = []

# Check in batches to avoid timeout
batch_size = 50
for i in range(0, len(all_columns), batch_size):
    batch = all_columns[i:i+batch_size]
    print(f"  Checking batch {i//batch_size + 1} ({len(batch)} columns)...")
    
    # Build query to check multiple columns at once
    col_checks = []
    for col in batch:
        col_checks.append(f"COUNTIF(`{col}` IS NOT NULL) as `{col}_non_null`")
    
    query = f"""
    SELECT 
      COUNT(*) as total_rows,
      {', '.join(col_checks)}
    FROM `{PROJECT_ID}.{DATASET_ID}.{BASE_TABLE}`
    """
    
    try:
        result = client.query(query).to_dataframe()
        total_rows = int(result.iloc[0]['total_rows'])
        
        for col in batch:
            col_key = f"{col}_non_null"
            if col_key in result.columns:
                non_null = int(result.iloc[0][col_key])
                if non_null == 0:
                    all_null_cols.append(col)
                    print(f"    ❌ {col}: ALL NULL (0/{total_rows})")
                elif non_null < total_rows * 0.1:  # Less than 10% populated
                    partial_null_cols.append((col, non_null, total_rows))
                    print(f"    ⚠️  {col}: {non_null}/{total_rows} ({non_null/total_rows*100:.1f}% populated)")
    except Exception as e:
        print(f"    ⚠️  Error checking batch: {str(e)[:100]}")

print(f"\n  📊 Summary:")
print(f"     All-NULL columns: {len(all_null_cols)}")
print(f"     Partially NULL columns (<10%): {len(partial_null_cols)}")

# Step 3: Categorize all-NULL columns by type
print("\n3️⃣  CATEGORIZING ALL-NULL COLUMNS...")
categories = {
    'economic': [],
    'weather': [],
    'market': [],
    'temporal_leakage': [],
    'other': []
}

for col in all_null_cols:
    col_lower = col.lower()
    if 'gdp' in col_lower or 'econ' in col_lower or 'unemployment' in col_lower or 'treasury' in col_lower:
        categories['economic'].append(col)
    elif 'temp' in col_lower or 'precip' in col_lower or 'weather' in col_lower or 'drought' in col_lower or 'flood' in col_lower or 'heat' in col_lower or 'conditions' in col_lower:
        categories['weather'].append(col)
    elif 'price' in col_lower or 'meal' in col_lower or 'soybean' in col_lower or 'futures' in col_lower:
        categories['market'].append(col)
    elif 'lead' in col_lower or 'correlation' in col_lower or 'event' in col_lower or 'tradewar' in col_lower:
        categories['temporal_leakage'].append(col)
    else:
        categories['other'].append(col)

for cat, cols in categories.items():
    if cols:
        print(f"\n  📁 {cat.upper()} ({len(cols)} columns):")
        for col in sorted(cols):
            print(f"     - {col}")

# Step 4: Check for source data availability
print("\n4️⃣  CHECKING SOURCE DATA AVAILABILITY...")
print("  Checking raw data tables...")

# List all tables in dataset
query = f"""
SELECT table_name
FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.TABLES`
WHERE table_type = 'BASE TABLE'
AND table_name LIKE '%raw%' OR table_name LIKE '%source%' OR table_name LIKE '%gdp%' OR table_name LIKE '%weather%' OR table_name LIKE '%meal%'
"""
try:
    raw_tables = client.query(query).to_dataframe()['table_name'].tolist()
    print(f"  ✅ Found {len(raw_tables)} potential source tables:")
    for table in raw_tables[:10]:  # Show first 10
        print(f"     - {table}")
    if len(raw_tables) > 10:
        print(f"     ... and {len(raw_tables) - 10} more")
except Exception as e:
    print(f"  ⚠️  Could not list source tables: {str(e)[:100]}")

# Step 5: Generate recommendations
print("\n" + "="*80)
print("📋 RECOMMENDATIONS")
print("="*80)

print("\n🔧 IMMEDIATE FIXES (for training):")
print(f"  Add {len(all_null_cols)} all-NULL columns to EXCEPT clause:")
for col in sorted(all_null_cols):
    print(f"    {col},")

print("\n🔧 PROPER FIXES (backfill data):")
for cat, cols in categories.items():
    if cols and cat != 'temporal_leakage':  # Don't fix temporal leakage, just exclude
        print(f"\n  {cat.upper()} ({len(cols)} columns):")
        print(f"    1. Check source data availability")
        print(f"    2. Backfill using historical data or interpolation")
        print(f"    3. Example columns: {', '.join(sorted(cols)[:3])}")

print("\n📝 Next Steps:")
print("  1. Run: python3 scripts/backfill_null_columns.py")
print("  2. Or: Add all-NULL columns to EXCEPT clause temporarily")
print("  3. Then: Retry training")

print("\n" + "="*80)

# Save results
results = {
    'all_null_columns': sorted(all_null_cols),
    'partial_null_columns': [(col, non_null, total) for col, non_null, total in partial_null_cols],
    'categories': {k: sorted(v) for k, v in categories.items()},
    'timestamp': datetime.now().isoformat()
}

import json
with open('/tmp/null_audit_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✅ Results saved to /tmp/null_audit_results.json")
print("="*80)

sys.exit(0)









