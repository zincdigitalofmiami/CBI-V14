#!/usr/bin/env python3
"""
Pre-Phase 1 Audit: Check all prerequisites before training BQML models
"""
from google.cloud import bigquery
import sys

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"

client = bigquery.Client(project=PROJECT_ID)

print("="*60)
print("🔍 PRE-PHASE 1 AUDIT: BQML TRAINING PREREQUISITES")
print("="*60)

all_checks_passed = True
issues = []

# 1. Check residual quantiles
print("\n1️⃣  RESIDUAL QUANTILES:")
try:
    query = f"""
    SELECT horizon, q10_residual, q90_residual, n_samples
    FROM `{PROJECT_ID}.{DATASET_ID}.residual_quantiles`
    WHERE source = 'vertex_ai_extracted'
    ORDER BY horizon
    """
    results = client.query(query).to_dataframe()
    
    expected_horizons = {'1w', '1m', '3m', '6m'}
    found_horizons = set(results['horizon'].tolist())
    
    if expected_horizons - found_horizons:
        print(f"  ❌ Missing horizons: {expected_horizons - found_horizons}")
        issues.append(f"Missing residual quantiles for: {expected_horizons - found_horizons}")
        all_checks_passed = False
    else:
        print(f"  ✅ All 4 horizons present")
        for _, row in results.iterrows():
            if row['q10_residual'] >= row['q90_residual']:
                print(f"  ❌ {row['horizon']}: Invalid quantiles")
                issues.append(f"{row['horizon']}: q10 >= q90")
                all_checks_passed = False
except Exception as e:
    print(f"  ❌ Error: {e}")
    issues.append(f"Residual quantiles check failed: {e}")
    all_checks_passed = False

# 2. Check training views exist and have correct structure
print("\n2️⃣  TRAINING VIEWS:")
views_config = {
    'train_1w': {'target': 'target_1w', 'exclude': ['target_1m', 'target_3m', 'target_6m']},
    'train_1m': {'target': 'target_1m', 'exclude': ['target_1w', 'target_3m', 'target_6m']},
    'train_3m': {'target': 'target_3m', 'exclude': ['target_1w', 'target_1m', 'target_6m']},
    'train_6m': {'target': 'target_6m', 'exclude': ['target_1w', 'target_1m', 'target_3m']}
}

for view_name, config in views_config.items():
    try:
        # Check view exists
        query = f"""
        SELECT COUNT(*) as col_count
        FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{view_name}'
        """
        col_count = client.query(query).to_dataframe().iloc[0]['col_count']
        
        # Check target exists
        query = f"""
        SELECT COUNT(*) as has_target
        FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{view_name}' AND column_name = '{config['target']}'
        """
        has_target = client.query(query).to_dataframe().iloc[0]['has_target']
        
        # Check label leakage
        exclude_list = ','.join([f"'{t}'" for t in config['exclude']])
        query = f"""
        SELECT COUNT(*) as leakage_count
        FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{view_name}' AND column_name IN ({exclude_list})
        """
        leakage = client.query(query).to_dataframe().iloc[0]['leakage_count']
        
        # Check row count and NULL targets
        query = f"""
        SELECT 
          COUNT(*) as total_rows,
          COUNTIF({config['target']} IS NOT NULL) as valid_targets
        FROM `{PROJECT_ID}.{DATASET_ID}.{view_name}`
        """
        row_check = client.query(query).to_dataframe()
        total_rows = row_check['total_rows'].iloc[0]
        valid_targets = row_check['valid_targets'].iloc[0]
        
        view_ok = True
        if col_count < 200 or col_count > 210:
            print(f"  ⚠️  {view_name}: Column count {col_count} (expected 200-210)")
            issues.append(f"{view_name}: Column count {col_count} outside expected range")
            view_ok = False
        
        if not has_target:
            print(f"  ❌ {view_name}: Missing target column {config['target']}")
            issues.append(f"{view_name}: Missing target {config['target']}")
            view_ok = False
            all_checks_passed = False
        
        if leakage > 0:
            print(f"  ❌ {view_name}: Label leakage - {leakage} other targets found")
            issues.append(f"{view_name}: Label leakage detected")
            view_ok = False
            all_checks_passed = False
        
        if valid_targets < 500:
            print(f"  ⚠️  {view_name}: Only {valid_targets} valid targets (<500 recommended)")
            issues.append(f"{view_name}: Low valid target count ({valid_targets})")
        
        if view_ok:
            print(f"  ✅ {view_name}: {col_count} cols, {total_rows} rows, {valid_targets} valid targets")
            
    except Exception as e:
        print(f"  ❌ {view_name}: Error - {str(e)[:80]}")
        issues.append(f"{view_name}: Check failed - {e}")
        all_checks_passed = False

# 3. Check predict_frame for Phase 3
print("\n3️⃣  PREDICT_FRAME VIEW (Phase 3):")
try:
    query = f"""
    SELECT COUNT(*) as col_count
    FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = 'predict_frame'
    """
    col_count = client.query(query).to_dataframe().iloc[0]['col_count']
    
    query = f"SELECT COUNT(*) as row_count FROM `{PROJECT_ID}.{DATASET_ID}.predict_frame`"
    row_count = client.query(query).to_dataframe().iloc[0]['row_count']
    
    if col_count < 200:
        print(f"  ⚠️  predict_frame: Only {col_count} columns (expected ~205)")
        issues.append(f"predict_frame: Low column count ({col_count})")
    else:
        print(f"  ✅ predict_frame: {col_count} cols, {row_count} rows")
except Exception as e:
    print(f"  ⚠️  predict_frame: Could not check - {e}")
    issues.append(f"predict_frame: Check failed - {e}")

# 4. Check for date column in training views
print("\n4️⃣  DATE COLUMN CHECK:")
for view_name in views_config.keys():
    try:
        query = f"""
        SELECT COUNT(*) as has_date
        FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{view_name}' AND column_name = 'date'
        """
        has_date = client.query(query).to_dataframe().iloc[0]['has_date']
        if has_date:
            print(f"  ✅ {view_name}: Has date column")
        else:
            print(f"  ⚠️  {view_name}: Missing date column (needed for train/val split)")
            issues.append(f"{view_name}: Missing date column")
    except Exception as e:
        print(f"  ⚠️  {view_name}: Could not check date column")

print("\n" + "="*60)
if all_checks_passed and len([i for i in issues if '❌' in str(i) or 'Missing' in str(i)]) == 0:
    print("✅ ALL CRITICAL CHECKS PASSED")
    print("✅ Ready to proceed with Phase 1 (BQML Training)")
else:
    print("⚠️  SOME ISSUES FOUND")
    print("\nIssues to address:")
    for issue in issues:
        print(f"  - {issue}")
    print("\n⚠️  Review issues above before proceeding to Phase 1")
print("="*60)

sys.exit(0 if all_checks_passed else 1)


