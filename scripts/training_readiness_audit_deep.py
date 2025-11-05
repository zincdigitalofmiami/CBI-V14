#!/usr/bin/env python3
"""
DEEP TRAINING READINESS AUDIT
Comprehensive pre-training validation
"""
from google.cloud import bigquery
import pandas as pd
from datetime import datetime

PROJECT_ID = "cbi-v14"
client = bigquery.Client(project=PROJECT_ID)

print("="*80)
print("🔍 DEEP TRAINING READINESS AUDIT")
print("="*80)
print(f"Time: {datetime.now()}")
print("="*80)

audit_results = {'errors': [], 'warnings': [], 'passed': []}

# ============================================================================
# 1. CHECK TRAINING VIEWS EXIST
# ============================================================================
print("\n1️⃣  CHECKING TRAINING VIEWS...")
required_views = ['train_1w', 'train_1m', 'train_3m', 'train_6m', '_v_train_core']

for view in required_views:
    query = f"""
    SELECT table_type 
    FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.TABLES` 
    WHERE table_name = '{view}'
    """
    result = client.query(query).to_dataframe()
    
    if len(result) == 0:
        audit_results['errors'].append(f"View {view} does NOT exist")
        print(f"  ❌ {view}: NOT FOUND")
    elif result['table_type'].iloc[0] == 'VIEW':
        audit_results['passed'].append(f"View {view} exists")
        print(f"  ✅ {view}: EXISTS")
    else:
        audit_results['warnings'].append(f"{view} is not a VIEW")
        print(f"  ⚠️  {view}: Not a view (type: {result['table_type'].iloc[0]})")

# ============================================================================
# 2. CHECK FOR ALL-NULL COLUMNS
# ============================================================================
print("\n2️⃣  CHECKING FOR ALL-NULL COLUMNS...")

# Get all numeric columns
cols_query = """
SELECT column_name 
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'training_dataset_super_enriched'
  AND data_type IN ('FLOAT64', 'INT64', 'NUMERIC')
  AND column_name NOT LIKE 'target_%'
ORDER BY column_name
"""
columns = client.query(cols_query).to_dataframe()['column_name'].tolist()

all_null_columns = []
high_null_columns = []

print(f"  Checking {len(columns)} numeric columns...")

for col in columns[:50]:  # Check first 50 for speed
    null_check = f"""
    SELECT 
      COUNTIF({col} IS NULL) as null_count,
      COUNT(*) as total_count,
      ROUND(100.0 * COUNTIF({col} IS NULL) / COUNT(*), 2) as null_pct
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    """
    
    try:
        result = client.query(null_check).to_dataframe()
        null_pct = result['null_pct'].iloc[0]
        
        if null_pct == 100:
            all_null_columns.append(col)
            audit_results['errors'].append(f"{col} is 100% NULL (training will fail)")
        elif null_pct > 90:
            high_null_columns.append(col)
            audit_results['warnings'].append(f"{col} is {null_pct}% NULL")
    except:
        pass

print(f"\n  🔴 ALL-NULL columns (100%): {len(all_null_columns)}")
for col in all_null_columns[:10]:
    print(f"     - {col}")

print(f"\n  🟡 HIGH-NULL columns (>90%): {len(high_null_columns)}")
for col in high_null_columns[:10]:
    print(f"     - {col}")

# ============================================================================
# 3. CHECK TEMPORAL LEAKAGE FEATURES
# ============================================================================
print("\n3️⃣  CHECKING TEMPORAL LEAKAGE FEATURES...")

temporal_leakage_features = [
    'crude_lead1_correlation',
    'palm_lead2_correlation',
    'vix_lead1_correlation',
    'dxy_lead1_correlation',
    'days_to_next_event',
    'event_impact_level',
    'event_vol_mult',
    'tradewar_event_vol_mult'
]

for feature in temporal_leakage_features:
    # Check if column exists
    col_check = f"""
    SELECT column_name 
    FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = 'training_dataset_super_enriched' 
      AND column_name = '{feature}'
    """
    result = client.query(col_check).to_dataframe()
    
    if len(result) > 0:
        audit_results['errors'].append(f"Temporal leakage feature '{feature}' exists in base table")
        print(f"  ❌ {feature}: EXISTS (potential leakage)")
    else:
        audit_results['passed'].append(f"Temporal leakage feature '{feature}' not in base table")
        print(f"  ✅ {feature}: Not in base table (good)")

# ============================================================================
# 4. CHECK LABEL LEAKAGE IN VIEWS
# ============================================================================
print("\n4️⃣  CHECKING LABEL LEAKAGE IN TRAINING VIEWS...")

label_checks = [
    ('train_1w', ['target_1m', 'target_3m', 'target_6m']),
    ('train_1m', ['target_1w', 'target_3m', 'target_6m']),
    ('train_3m', ['target_1w', 'target_1m', 'target_6m']),
    ('train_6m', ['target_1w', 'target_1m', 'target_3m']),
]

for view_name, forbidden_targets in label_checks:
    for target in forbidden_targets:
        check_query = f"""
        SELECT column_name 
        FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{view_name}' 
          AND column_name = '{target}'
        """
        result = client.query(check_query).to_dataframe()
        
        if len(result) > 0:
            audit_results['errors'].append(f"{view_name} contains {target} (label leakage)")
            print(f"  ❌ {view_name} contains {target}")
        else:
            audit_results['passed'].append(f"{view_name} excludes {target}")

print(f"  ✅ Label leakage check complete")

# ============================================================================
# 5. CHECK DATA QUALITY
# ============================================================================
print("\n5️⃣  CHECKING DATA QUALITY...")

# Check row count
row_count_query = """
SELECT COUNT(*) as row_count 
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
"""
row_count = client.query(row_count_query).to_dataframe()['row_count'].iloc[0]

if row_count < 500:
    audit_results['errors'].append(f"Insufficient data: only {row_count} rows")
    print(f"  ❌ Only {row_count} rows (need >500)")
elif row_count < 1000:
    audit_results['warnings'].append(f"Low data: only {row_count} rows")
    print(f"  ⚠️  Only {row_count} rows (recommend >1000)")
else:
    audit_results['passed'].append(f"Sufficient data: {row_count} rows")
    print(f"  ✅ {row_count} rows")

# Check date range
date_range_query = """
SELECT 
  MIN(date) as min_date,
  MAX(date) as max_date,
  DATE_DIFF(MAX(date), MIN(date), DAY) as day_span
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
"""
date_info = client.query(date_range_query).to_dataframe()
min_date = date_info['min_date'].iloc[0]
max_date = date_info['max_date'].iloc[0]
day_span = date_info['day_span'].iloc[0]

print(f"  ✅ Date range: {min_date} to {max_date} ({day_span} days)")

# Check target columns
print("\n  Checking target columns...")
for target in ['target_1w', 'target_1m', 'target_3m', 'target_6m']:
    target_check = f"""
    SELECT 
      COUNTIF({target} IS NOT NULL) as non_null,
      ROUND(100.0 * COUNTIF({target} IS NOT NULL) / COUNT(*), 2) as pct_filled
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    """
    result = client.query(target_check).to_dataframe()
    non_null = result['non_null'].iloc[0]
    pct_filled = result['pct_filled'].iloc[0]
    
    if pct_filled < 50:
        audit_results['errors'].append(f"{target} only {pct_filled}% filled")
        print(f"  ❌ {target}: {pct_filled}% filled (need >50%)")
    else:
        print(f"  ✅ {target}: {pct_filled}% filled")

# ============================================================================
# 6. CHECK TRAIN/TEST SPLIT
# ============================================================================
print("\n6️⃣  CHECKING TRAIN/TEST SPLIT...")

split_query = """
SELECT 
  data_split,
  COUNT(*) as count,
  ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM `cbi-v14.models_v4.training_dataset_super_enriched`), 2) as pct
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE data_split IS NOT NULL
GROUP BY data_split
ORDER BY data_split
"""

try:
    splits = client.query(split_query).to_dataframe()
    
    for _, row in splits.iterrows():
        split_type = row['data_split']
        count = row['count']
        pct = row['pct']
        print(f"  {split_type}: {count} rows ({pct}%)")
        
        if split_type == 'TRAIN' and pct < 60:
            audit_results['warnings'].append(f"TRAIN split only {pct}% (recommend 70-80%)")
        elif split_type == 'TEST' and pct < 10:
            audit_results['warnings'].append(f"TEST split only {pct}% (recommend 15-20%)")
            
except Exception as e:
    audit_results['errors'].append(f"data_split column issue: {str(e)[:100]}")
    print(f"  ❌ Error checking splits: {str(e)[:100]}")

# ============================================================================
# 7. CHECK TRAINING SQL FILES
# ============================================================================
print("\n7️⃣  CHECKING TRAINING SQL FILES...")

import os
sql_files = [
    'bigquery_sql/train_bqml_1w_mean.sql',
    'bigquery_sql/train_bqml_1m_mean.sql',
    'bigquery_sql/train_bqml_3m_mean.sql',
    'bigquery_sql/train_bqml_6m_mean.sql'
]

for sql_file in sql_files:
    if os.path.exists(sql_file):
        print(f"  ✅ {os.path.basename(sql_file)}: EXISTS")
        
        # Check for problematic options
        with open(sql_file, 'r') as f:
            content = f.read()
            
            if 'OPTIMIZATION_STRATEGY' in content:
                audit_results['errors'].append(f"{sql_file} contains OPTIMIZATION_STRATEGY (unsupported)")
                print(f"     ❌ Contains OPTIMIZATION_STRATEGY")
            
            if 'OPTIMIZATION_OBJECTIVE' in content:
                audit_results['errors'].append(f"{sql_file} contains OPTIMIZATION_OBJECTIVE (unsupported)")
                print(f"     ❌ Contains OPTIMIZATION_OBJECTIVE")
                
            if 'MAX_PARALLEL_TRIALS=10' in content or 'MAX_PARALLEL_TRIALS = 10' in content:
                audit_results['errors'].append(f"{sql_file} has MAX_PARALLEL_TRIALS=10 (max is 5)")
                print(f"     ❌ MAX_PARALLEL_TRIALS=10 (should be ≤5)")
    else:
        audit_results['errors'].append(f"{sql_file} NOT FOUND")
        print(f"  ❌ {os.path.basename(sql_file)}: NOT FOUND")

# ============================================================================
# 8. FINAL SUMMARY
# ============================================================================
print("\n" + "="*80)
print("📊 AUDIT SUMMARY")
print("="*80)

print(f"\n✅ PASSED: {len(audit_results['passed'])} checks")
print(f"⚠️  WARNINGS: {len(audit_results['warnings'])} issues")
print(f"❌ ERRORS: {len(audit_results['errors'])} blockers")

if audit_results['errors']:
    print("\n🔴 CRITICAL ERRORS (MUST FIX BEFORE TRAINING):")
    for i, error in enumerate(audit_results['errors'][:20], 1):
        print(f"  {i}. {error}")

if audit_results['warnings']:
    print("\n🟡 WARNINGS (SHOULD FIX):")
    for i, warning in enumerate(audit_results['warnings'][:10], 1):
        print(f"  {i}. {warning}")

print("\n" + "="*80)
if len(audit_results['errors']) == 0:
    print("✅ TRAINING READINESS: PASSED")
    print("   Ready to train models")
else:
    print("❌ TRAINING READINESS: FAILED")
    print(f"   Fix {len(audit_results['errors'])} errors before training")
print("="*80)

# Save results
with open('../docs/training_readiness_audit.txt', 'w') as f:
    f.write("TRAINING READINESS AUDIT\n")
    f.write(f"Time: {datetime.now()}\n")
    f.write(f"Errors: {len(audit_results['errors'])}\n")
    f.write(f"Warnings: {len(audit_results['warnings'])}\n")
    f.write(f"Passed: {len(audit_results['passed'])}\n")

print("\n✅ Audit results saved to: docs/training_readiness_audit.txt")



