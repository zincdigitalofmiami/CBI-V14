#!/usr/bin/env python3
"""
Data Quality Validation BEFORE Training Data Exports
Validates all training datasets before exporting to Parquet
"""
from google.cloud import bigquery
from datetime import datetime
import sys
from pathlib import Path

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"

client = bigquery.Client(project=PROJECT_ID)

print("="*80)
print("🔍 DATA QUALITY VALIDATION - PRE-EXPORT CHECKS")
print("="*80)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Project: {PROJECT_ID}")
print(f"Dataset: {DATASET_ID}")
print("="*80)

all_checks_passed = True
issues = []
warnings = []

# Tables to validate
TABLES_TO_CHECK = {
    'trump_rich_2023_2025': {
        'target_col': None,  # No target column
        'min_rows': 700,
        'expected_features': 42,
        'description': 'Trump-era training table (42 neural drivers)'
    },
    'production_training_data_1w': {
        'target_col': 'target_1w',
        'min_rows': 1000,
        'expected_features': 290,
        'description': '1W horizon training data (290 features)'
    },
    'production_training_data_1m': {
        'target_col': 'target_1m',
        'min_rows': 1000,
        'expected_features': 290,
        'description': '1M horizon training data (290 features)'
    },
    'production_training_data_3m': {
        'target_col': 'target_3m',
        'min_rows': 1000,
        'expected_features': 290,
        'description': '3M horizon training data (290 features)'
    },
    'production_training_data_6m': {
        'target_col': 'target_6m',
        'min_rows': 1000,
        'expected_features': 290,
        'description': '6M horizon training data (290 features)'
    },
    'production_training_data_12m': {
        'target_col': 'target_12m',
        'min_rows': 1000,
        'expected_features': 290,
        'description': '12M horizon training data (290 features)'
    }
}

def check_table_exists(table_name):
    """Check if table exists in BigQuery"""
    try:
        query = f"""
        SELECT COUNT(*) as table_exists
        FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.TABLES`
        WHERE table_name = '{table_name}'
        """
        result = client.query(query).to_dataframe()
        return result.iloc[0]['table_exists'] > 0
    except Exception as e:
        print(f"  ❌ Error checking table existence: {e}")
        return False

def check_table_quality(table_name, config):
    """Comprehensive quality check for a table"""
    global all_checks_passed, issues, warnings
    
    print(f"\n{'='*80}")
    print(f"📊 VALIDATING: {table_name}")
    print(f"   {config['description']}")
    print(f"{'='*80}")
    
    # Check table exists
    if not check_table_exists(table_name):
        print(f"  ❌ Table '{table_name}' does not exist")
        issues.append(f"Table {table_name} missing")
        all_checks_passed = False
        return False
    
    print(f"  ✅ Table exists")
    
    # Get table schema
    try:
        table_ref = client.dataset(DATASET_ID).table(table_name)
        table_obj = client.get_table(table_ref)
        column_count = len(table_obj.schema)
        
        print(f"  📊 Column count: {column_count}")
        
        if abs(column_count - config['expected_features']) > 10:
            print(f"  ⚠️  Column count mismatch: expected ~{config['expected_features']}, got {column_count}")
            warnings.append(f"{table_name}: Column count {column_count} vs expected {config['expected_features']}")
    except Exception as e:
        print(f"  ❌ Error getting schema: {e}")
        issues.append(f"{table_name}: Schema check failed: {e}")
        all_checks_passed = False
        return False
    
    # Check row count and target quality
    if config['target_col']:
        try:
            query = f"""
            SELECT 
                COUNT(*) as total_rows,
                COUNTIF({config['target_col']} IS NOT NULL) as valid_targets,
                COUNTIF({config['target_col']} IS NULL) as null_targets,
                MIN({config['target_col']}) as min_target,
                MAX({config['target_col']}) as max_target,
                AVG({config['target_col']}) as avg_target,
                STDDEV({config['target_col']}) as stddev_target,
                MIN(date) as earliest_date,
                MAX(date) as latest_date
            FROM `{PROJECT_ID}.{DATASET_ID}.{table_name}`
            """
            stats = client.query(query).to_dataframe().iloc[0]
            
            total_rows = int(stats['total_rows'])
            valid_targets = int(stats['valid_targets'])
            null_targets = int(stats['null_targets'])
            
            print(f"  📊 Total rows: {total_rows:,}")
            print(f"  ✅ Valid targets: {valid_targets:,}")
            
            if null_targets > 0:
                print(f"  ⚠️  NULL targets: {null_targets:,} ({null_targets/total_rows*100:.1f}%)")
                if null_targets / total_rows > 0.05:
                    warnings.append(f"{table_name}: {null_targets} NULL targets ({null_targets/total_rows*100:.1f}%)")
            
            if total_rows < config['min_rows']:
                print(f"  ❌ INSUFFICIENT DATA: {total_rows} rows (< {config['min_rows']} minimum)")
                issues.append(f"{table_name}: Insufficient rows ({total_rows} < {config['min_rows']})")
                all_checks_passed = False
            
            if valid_targets < config['min_rows'] * 0.9:
                print(f"  ❌ INSUFFICIENT VALID TARGETS: {valid_targets} valid (< {config['min_rows'] * 0.9:.0f} minimum)")
                issues.append(f"{table_name}: Insufficient valid targets ({valid_targets})")
                all_checks_passed = False
            
            print(f"\n  📈 Target Statistics:")
            print(f"     Min: ${stats['min_target']:.2f}")
            print(f"     Max: ${stats['max_target']:.2f}")
            print(f"     Avg: ${stats['avg_target']:.2f}")
            print(f"     StdDev: ${stats['stddev_target']:.2f}")
            
            if stats['min_target'] <= 0:
                print(f"  ⚠️  Negative or zero target values detected")
                warnings.append(f"{table_name}: Negative/zero targets")
            
            print(f"\n  📅 Date Range:")
            print(f"     Earliest: {stats['earliest_date']}")
            print(f"     Latest: {stats['latest_date']}")
            
        except Exception as e:
            print(f"  ❌ Error checking data quality: {e}")
            issues.append(f"{table_name}: Data quality check failed: {e}")
            all_checks_passed = False
    else:
        # No target column - just check row count
        try:
            query = f"""
            SELECT 
                COUNT(*) as total_rows,
                MIN(date) as earliest_date,
                MAX(date) as latest_date
            FROM `{PROJECT_ID}.{DATASET_ID}.{table_name}`
            """
            stats = client.query(query).to_dataframe().iloc[0]
            total_rows = int(stats['total_rows'])
            
            print(f"  📊 Total rows: {total_rows:,}")
            
            if total_rows < config['min_rows']:
                print(f"  ❌ INSUFFICIENT DATA: {total_rows} rows (< {config['min_rows']} minimum)")
                issues.append(f"{table_name}: Insufficient rows ({total_rows} < {config['min_rows']})")
                all_checks_passed = False
            
            print(f"\n  📅 Date Range:")
            print(f"     Earliest: {stats['earliest_date']}")
            print(f"     Latest: {stats['latest_date']}")
            
        except Exception as e:
            print(f"  ❌ Error checking data: {e}")
            issues.append(f"{table_name}: Data check failed: {e}")
            all_checks_passed = False
    
    return True

# Run checks for all tables
print("\n" + "="*80)
print("RUNNING QUALITY CHECKS FOR ALL TRAINING TABLES")
print("="*80)

for table_name, config in TABLES_TO_CHECK.items():
    check_table_quality(table_name, config)

# Final summary
print("\n" + "="*80)
print("📋 VALIDATION SUMMARY")
print("="*80)

if all_checks_passed:
    print("✅ ALL CHECKS PASSED - Ready for export")
    if warnings:
        print(f"\n⚠️  Warnings ({len(warnings)}):")
        for warning in warnings:
            print(f"   - {warning}")
else:
    print("❌ VALIDATION FAILED - Fix issues before exporting")
    print(f"\n❌ Issues ({len(issues)}):")
    for issue in issues:
        print(f"   - {issue}")
    if warnings:
        print(f"\n⚠️  Warnings ({len(warnings)}):")
        for warning in warnings:
            print(f"   - {warning}")

print("="*80)

# Exit with error code if checks failed
if not all_checks_passed:
    sys.exit(1)

