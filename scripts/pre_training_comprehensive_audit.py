#!/usr/bin/env python3
"""
Comprehensive Pre-Training Audit
Verify everything is correct before massive retraining
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("🔍 COMPREHENSIVE PRE-TRAINING AUDIT")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

issues_found = []
warnings = []

# 1. Verify Super-Enriched Dataset Exists
print("=" * 80)
print("1. VERIFYING SUPER-ENRICHED DATASET")
print("=" * 80)

try:
    dataset_check = """
    SELECT COUNT(*) as row_count
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    """
    result = client.query(dataset_check).to_dataframe()
    row_count = result['row_count'].iloc[0]
    print(f"✅ Dataset exists: {row_count} rows")
    
    if row_count < 1000:
        issues_found.append(f"CRITICAL: Only {row_count} rows in dataset")
except Exception as e:
    issues_found.append(f"CRITICAL: Dataset does not exist: {e}")

# 2. Check Feature Count
print("\n" + "=" * 80)
print("2. CHECKING FEATURE COUNT")
print("=" * 80)

try:
    feature_check = """
    SELECT column_name, data_type
    FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = 'training_dataset_super_enriched'
    AND column_name NOT IN ('date', 'target_1w', 'target_1m', 'target_3m', 'target_6m')
    ORDER BY column_name
    """
    features_df = client.query(feature_check).to_dataframe()
    feature_count = len(features_df)
    print(f"✅ Total features: {feature_count}")
    
    if feature_count < 190:
        warnings.append(f"Expected 197 features, got {feature_count}")
    
    # Check for critical features
    critical_features = ['usd_brl_rate', 'usd_cny_rate', 'fed_funds_rate', 'real_yield', 'yield_curve', 'supply_demand_ratio', 'vix_index_new']
    missing_features = []
    for feature in critical_features:
        if feature not in features_df['column_name'].values:
            missing_features.append(feature)
    
    if missing_features:
        issues_found.append(f"CRITICAL: Missing features: {missing_features}")
    else:
        print("✅ All critical features present")
        
except Exception as e:
    issues_found.append(f"CRITICAL: Cannot check features: {e}")

# 3. Verify Target Columns
print("\n" + "=" * 80)
print("3. VERIFYING TARGET COLUMNS")
print("=" * 80)

targets = ['target_1w', 'target_1m', 'target_3m', 'target_6m']
for target in targets:
    try:
        target_check = f"""
        SELECT 
            COUNT(*) as total_rows,
            COUNT({target}) as non_null_rows,
            MIN({target}) as min_val,
            MAX({target}) as max_val,
            AVG({target}) as avg_val
        FROM `cbi-v14.models_v4.training_dataset_super_enriched`
        """
        result = client.query(target_check).to_dataframe()
        
        total = result['total_rows'].iloc[0]
        non_null = result['non_null_rows'].iloc[0]
        min_val = result['min_val'].iloc[0]
        max_val = result['max_val'].iloc[0]
        avg_val = result['avg_val'].iloc[0]
        
        print(f"✅ {target}: {non_null}/{total} rows, range ${min_val:.2f}-${max_val:.2f}, avg ${avg_val:.2f}")
        
        if non_null < 100:
            issues_found.append(f"CRITICAL: {target} has only {non_null} non-null rows")
        if min_val < 0:
            issues_found.append(f"CRITICAL: {target} has negative values")
            
    except Exception as e:
        issues_found.append(f"CRITICAL: Cannot check {target}: {e}")

# 4. Check Data Quality
print("\n" + "=" * 80)
print("4. CHECKING DATA QUALITY")
print("=" * 80)

# Check for NULLs in critical features
critical_features_check = ['usd_brl_rate', 'usd_cny_rate', 'fed_funds_rate', 'vix_index_new']
for feature in critical_features_check:
    try:
        null_check = f"""
        SELECT COUNT(*) as null_count
        FROM `cbi-v14.models_v4.training_dataset_super_enriched`
        WHERE {feature} IS NULL OR {feature} = 0
        """
        result = client.query(null_check).to_dataframe()
        null_count = result['null_count'].iloc[0]
        
        if null_count > 500:
            warnings.append(f"{feature}: {null_count} null/zero values (may need handling)")
        else:
            print(f"✅ {feature}: {null_count} null/zero values")
    except Exception as e:
        warnings.append(f"Cannot check {feature}: {e}")

# 5. Verify Date Range
print("\n" + "=" * 80)
print("5. VERIFYING DATE RANGE")
print("=" * 80)

try:
    date_check = """
    SELECT 
        MIN(date) as min_date,
        MAX(date) as max_date,
        COUNT(DISTINCT date) as unique_dates
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    """
    result = client.query(date_check).to_dataframe()
    min_date = result['min_date'].iloc[0]
    max_date = result['max_date'].iloc[0]
    unique_dates = result['unique_dates'].iloc[0]
    
    print(f"✅ Date range: {min_date} to {max_date}")
    print(f"✅ Unique dates: {unique_dates}")
    
    if max_date < '2025-01-01':
        warnings.append(f"Max date is old: {max_date}")
        
except Exception as e:
    issues_found.append(f"Cannot check dates: {e}")

# 6. Check Derived Feature Tables
print("\n" + "=" * 80)
print("6. CHECKING DERIVED FEATURE TABLES")
print("=" * 80)

derived_tables = ['fx_derived_features', 'monetary_derived_features', 'fundamentals_derived_features', 'volatility_derived_features']
for table in derived_tables:
    try:
        check = f"""
        SELECT COUNT(*) as row_count
        FROM `cbi-v14.models_v4.{table}`
        """
        result = client.query(check).to_dataframe()
        row_count = result['row_count'].iloc[0]
        print(f"✅ {table}: {row_count} rows")
        
        if row_count == 0:
            issues_found.append(f"CRITICAL: {table} is empty")
    except Exception as e:
        issues_found.append(f"CRITICAL: {table} does not exist: {e}")

# 7. Verify Fresh Data
print("\n" + "=" * 80)
print("7. VERIFYING DATA FRESHNESS")
print("=" * 80)

try:
    freshness_check = """
    SELECT 
        indicator,
        MAX(time) as latest_time
    FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
    WHERE indicator IN ('usd_brl_rate', 'usd_cny_rate', 'fed_funds_rate', 'vix_index')
    GROUP BY indicator
    """
    result = client.query(freshness_check).to_dataframe()
    
    for _, row in result.iterrows():
        latest = row['latest_time']
        age_hours = (datetime.now() - latest).total_seconds() / 3600
        print(f"✅ {row['indicator']}: {latest} ({age_hours:.1f}h ago)")
        
        if age_hours > 72:
            warnings.append(f"{row['indicator']} is {age_hours:.1f} hours old")
except Exception as e:
    warnings.append(f"Cannot check freshness: {e}")

# 8. Check for Duplicates
print("\n" + "=" * 80)
print("8. CHECKING FOR DUPLICATES")
print("=" * 80)

try:
    duplicate_check = """
    SELECT date, COUNT(*) as count
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    GROUP BY date
    HAVING COUNT(*) > 1
    """
    result = client.query(duplicate_check).to_dataframe()
    
    if len(result) > 0:
        issues_found.append(f"CRITICAL: Found {len(result)} duplicate dates")
    else:
        print("✅ No duplicate dates")
except Exception as e:
    warnings.append(f"Cannot check duplicates: {e}")

# Summary
print("\n" + "=" * 80)
print("AUDIT SUMMARY")
print("=" * 80)

if issues_found:
    print(f"\n❌ CRITICAL ISSUES FOUND: {len(issues_found)}")
    for issue in issues_found:
        print(f"   ❌ {issue}")
else:
    print("\n✅ NO CRITICAL ISSUES")

if warnings:
    print(f"\n⚠️  WARNINGS: {len(warnings)}")
    for warning in warnings:
        print(f"   ⚠️  {warning}")
else:
    print("\n✅ NO WARNINGS")

print("\n" + "=" * 80)
if issues_found:
    print("🚨 TRAINING SHOULD NOT PROCEED - FIX ISSUES FIRST")
else:
    print("✅ TRAINING CLEARED TO PROCEED")
print("=" * 80)










