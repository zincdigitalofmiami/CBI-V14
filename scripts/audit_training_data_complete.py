#!/usr/bin/env python3
"""
Complete Training Data Audit
Comprehensive audit of all training data after historical backfill
"""
from google.cloud import bigquery
from datetime import datetime
import pandas as pd
import os

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"
WAREHOUSE_DATASET = "forecasting_data_warehouse"

client = bigquery.Client(project=PROJECT_ID)

print("="*80)
print("COMPLETE TRAINING DATA AUDIT")
print("="*80)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Project: {PROJECT_ID}")
print("="*80)
print()

# Results storage
audit_results = {
    'production_tables': {},
    'historical_data': {},
    'regime_tables': {},
    'issues': [],
    'recommendations': []
}

# ============================================================================
# 1. AUDIT PRODUCTION TRAINING DATA TABLES
# ============================================================================
print("1. AUDITING PRODUCTION TRAINING DATA TABLES")
print("-"*80)

horizons = ['1w', '1m', '3m', '6m', '12m']

for horizon in horizons:
    table_name = f'production_training_data_{horizon}'
    print(f"\n  📊 {table_name}")
    
    try:
        # Get date range and row count
        query = f"""
        SELECT 
            MIN(date) as earliest_date,
            MAX(date) as latest_date,
            COUNT(*) as row_count,
            COUNT(DISTINCT date) as unique_dates,
            COUNT(*) - COUNT(DISTINCT date) as duplicate_dates
        FROM `{PROJECT_ID}.{DATASET_ID}.{table_name}`
        """
        
        result = client.query(query).to_dataframe()
        
        earliest = result.iloc[0]['earliest_date']
        latest = result.iloc[0]['latest_date']
        row_count = int(result.iloc[0]['row_count'])
        unique_dates = int(result.iloc[0]['unique_dates'])
        duplicates = int(result.iloc[0]['duplicate_dates'])
        
        # Check for historical data
        has_historical = earliest and pd.Timestamp(earliest) < pd.Timestamp('2020-01-01')
        
        # Get feature count
        table_ref = client.get_table(f"{PROJECT_ID}.{DATASET_ID}.{table_name}")
        feature_count = len(table_ref.schema) - 1  # Exclude date column
        
        # Check for NULL targets
        target_col = f'target_{horizon}'
        null_targets_query = f"""
        SELECT COUNT(*) as null_count
        FROM `{PROJECT_ID}.{DATASET_ID}.{table_name}`
        WHERE {target_col} IS NULL
        """
        null_result = client.query(null_targets_query).to_dataframe()
        null_targets = int(null_result.iloc[0]['null_count'])
        
        print(f"     Date range: {earliest} to {latest}")
        print(f"     Rows: {row_count:,}")
        print(f"     Unique dates: {unique_dates:,}")
        print(f"     Features: {feature_count}")
        print(f"     NULL targets: {null_targets:,}")
        
        if duplicates > 0:
            print(f"     ⚠️  WARNING: {duplicates} duplicate dates found")
            audit_results['issues'].append(f"{table_name}: {duplicates} duplicate dates")
        
        if has_historical:
            print(f"     ✅ Historical data included (starts {earliest})")
        else:
            print(f"     ⚠️  NO historical data (starts {earliest})")
            audit_results['issues'].append(f"{table_name}: Missing historical data (starts {earliest})")
            audit_results['recommendations'].append(f"Rebuild {table_name} with 2000-2025 date range")
        
        if null_targets > row_count * 0.1:  # More than 10% NULL
            print(f"     ⚠️  WARNING: {null_targets} NULL targets ({null_targets/row_count*100:.1f}%)")
            audit_results['issues'].append(f"{table_name}: {null_targets} NULL targets ({null_targets/row_count*100:.1f}%)")
        
        audit_results['production_tables'][horizon] = {
            'earliest_date': str(earliest),
            'latest_date': str(latest),
            'row_count': row_count,
            'feature_count': feature_count,
            'has_historical': has_historical,
            'null_targets': null_targets
        }
        
    except Exception as e:
        print(f"     ❌ ERROR: {e}")
        audit_results['issues'].append(f"{table_name}: Error - {e}")

# ============================================================================
# 2. AUDIT HISTORICAL DATA SOURCE
# ============================================================================
print("\n" + "="*80)
print("2. AUDITING HISTORICAL DATA SOURCE")
print("-"*80)

try:
    query = f"""
    SELECT 
        MIN(DATE(time)) as earliest_date,
        MAX(DATE(time)) as latest_date,
        COUNT(*) as row_count,
        COUNT(DISTINCT DATE(time)) as unique_dates,
        COUNT(DISTINCT symbol) as symbols
    FROM `{PROJECT_ID}.{WAREHOUSE_DATASET}.soybean_oil_prices`
    """
    
    result = client.query(query).to_dataframe()
    
    earliest = result.iloc[0]['earliest_date']
    latest = result.iloc[0]['latest_date']
    row_count = int(result.iloc[0]['row_count'])
    unique_dates = int(result.iloc[0]['unique_dates'])
    symbols = int(result.iloc[0]['symbols'])
    
    print(f"  📊 soybean_oil_prices")
    print(f"     Date range: {earliest} to {latest}")
    print(f"     Rows: {row_count:,}")
    print(f"     Unique dates: {unique_dates:,}")
    print(f"     Symbols: {symbols}")
    
    has_historical = earliest and pd.Timestamp(earliest) < pd.Timestamp('2020-01-01')
    
    if has_historical:
        print(f"     ✅ Historical data present (starts {earliest})")
    else:
        print(f"     ⚠️  NO historical data (starts {earliest})")
        audit_results['issues'].append(f"soybean_oil_prices: Missing historical data")
    
    audit_results['historical_data'] = {
        'earliest_date': str(earliest),
        'latest_date': str(latest),
        'row_count': row_count,
        'has_historical': has_historical
    }
    
except Exception as e:
    print(f"  ❌ ERROR: {e}")
    audit_results['issues'].append(f"soybean_oil_prices: Error - {e}")

# ============================================================================
# 3. AUDIT HISTORICAL REGIME TABLES
# ============================================================================
print("\n" + "="*80)
print("3. AUDITING HISTORICAL REGIME TABLES")
print("-"*80)

historical_regime_tables = [
    'trade_war_2017_2019_historical',
    'crisis_2008_historical',
    'pre_crisis_2000_2007_historical',
    'recovery_2010_2016_historical'
]

for table_name in historical_regime_tables:
    print(f"\n  📊 {table_name}")
    
    try:
        # Check if table exists
        query = f"""
        SELECT COUNT(*) as table_exists
        FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.TABLES`
        WHERE table_name = '{table_name}'
        """
        exists_result = client.query(query).to_dataframe()
        
        if exists_result.iloc[0]['table_exists'] == 0:
            print(f"     ❌ Table does not exist")
            audit_results['issues'].append(f"{table_name}: Table does not exist")
            continue
        
        # Get date range and row count
        query = f"""
        SELECT 
            MIN(date) as earliest_date,
            MAX(date) as latest_date,
            COUNT(*) as row_count
        FROM `{PROJECT_ID}.{DATASET_ID}.{table_name}`
        """
        
        result = client.query(query).to_dataframe()
        
        earliest = result.iloc[0]['earliest_date']
        latest = result.iloc[0]['latest_date']
        row_count = int(result.iloc[0]['row_count'])
        
        print(f"     Date range: {earliest} to {latest}")
        print(f"     Rows: {row_count:,}")
        
        if row_count == 0:
            print(f"     ⚠️  WARNING: Table is empty")
            audit_results['issues'].append(f"{table_name}: Table is empty")
        
        audit_results['regime_tables'][table_name] = {
            'earliest_date': str(earliest) if earliest else None,
            'latest_date': str(latest) if latest else None,
            'row_count': row_count
        }
        
    except Exception as e:
        print(f"     ❌ ERROR: {e}")
        audit_results['issues'].append(f"{table_name}: Error - {e}")

# ============================================================================
# 4. AUDIT TRUMP RICH TABLE
# ============================================================================
print("\n" + "="*80)
print("4. AUDITING TRUMP RICH TABLE")
print("-"*80)

try:
    query = f"""
    SELECT 
        MIN(date) as earliest_date,
        MAX(date) as latest_date,
        COUNT(*) as row_count
    FROM `{PROJECT_ID}.{DATASET_ID}.trump_rich_2023_2025`
    """
    
    result = client.query(query).to_dataframe()
    
    earliest = result.iloc[0]['earliest_date']
    latest = result.iloc[0]['latest_date']
    row_count = int(result.iloc[0]['row_count'])
    
    print(f"  📊 trump_rich_2023_2025")
    print(f"     Date range: {earliest} to {latest}")
    print(f"     Rows: {row_count:,}")
    
    audit_results['trump_rich'] = {
        'earliest_date': str(earliest),
        'latest_date': str(latest),
        'row_count': row_count
    }
    
except Exception as e:
    print(f"  ❌ ERROR: {e}")
    audit_results['issues'].append(f"trump_rich_2023_2025: Error - {e}")

# ============================================================================
# 5. CHECK DATA GAPS
# ============================================================================
print("\n" + "="*80)
print("5. CHECKING FOR DATA GAPS")
print("-"*80)

for horizon in horizons:
    table_name = f'production_training_data_{horizon}'
    
    try:
        # Check for gaps in date sequence
        query = f"""
        WITH date_sequence AS (
            SELECT date,
                   LAG(date) OVER (ORDER BY date) as prev_date,
                   DATE_DIFF(date, LAG(date) OVER (ORDER BY date), DAY) as gap_days
            FROM `{PROJECT_ID}.{DATASET_ID}.{table_name}`
            ORDER BY date
        )
        SELECT 
            COUNT(*) as total_gaps,
            MAX(gap_days) as max_gap,
            AVG(gap_days) as avg_gap
        FROM date_sequence
        WHERE gap_days > 1
        """
        
        result = client.query(query).to_dataframe()
        
        total_gaps = int(result.iloc[0]['total_gaps'])
        max_gap = result.iloc[0]['max_gap']
        avg_gap = result.iloc[0]['avg_gap']
        
        if total_gaps > 0:
            print(f"  ⚠️  {table_name}: {total_gaps} gaps found (max: {max_gap} days, avg: {avg_gap:.1f} days)")
            audit_results['issues'].append(f"{table_name}: {total_gaps} date gaps (max: {max_gap} days)")
        else:
            print(f"  ✅ {table_name}: No gaps found")
            
    except Exception as e:
        print(f"  ❌ {table_name}: Error checking gaps - {e}")

# ============================================================================
# 6. SUMMARY REPORT
# ============================================================================
print("\n" + "="*80)
print("AUDIT SUMMARY")
print("="*80)

print("\n📊 PRODUCTION TABLES STATUS:")
for horizon, data in audit_results['production_tables'].items():
    status = "✅" if data['has_historical'] else "⚠️"
    print(f"  {status} {horizon:3s}: {data['row_count']:6,} rows, {data['earliest_date']} to {data['latest_date']}")

print("\n📊 HISTORICAL DATA STATUS:")
if audit_results['historical_data']:
    data = audit_results['historical_data']
    status = "✅" if data['has_historical'] else "⚠️"
    print(f"  {status} soybean_oil_prices: {data['row_count']:6,} rows, {data['earliest_date']} to {data['latest_date']}")

print("\n📊 REGIME TABLES STATUS:")
for table_name, data in audit_results['regime_tables'].items():
    status = "✅" if data['row_count'] > 0 else "⚠️"
    print(f"  {status} {table_name}: {data['row_count']:,} rows")

print("\n⚠️  ISSUES FOUND:")
if audit_results['issues']:
    for i, issue in enumerate(audit_results['issues'], 1):
        print(f"  {i}. {issue}")
else:
    print("  ✅ No issues found")

print("\n💡 RECOMMENDATIONS:")
if audit_results['recommendations']:
    for i, rec in enumerate(audit_results['recommendations'], 1):
        print(f"  {i}. {rec}")
else:
    print("  ✅ No recommendations - data looks good")

# Save results
output_file = f"TRAINING_DATA_AUDIT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
with open(output_file, 'w') as f:
    f.write("# Training Data Audit Report\n")
    f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    f.write("## Production Tables\n\n")
    for horizon, data in audit_results['production_tables'].items():
        f.write(f"### {horizon}\n")
        f.write(f"- Date range: {data['earliest_date']} to {data['latest_date']}\n")
        f.write(f"- Rows: {data['row_count']:,}\n")
        f.write(f"- Features: {data['feature_count']}\n")
        f.write(f"- Has historical: {data['has_historical']}\n\n")
    
    f.write("## Issues\n\n")
    for issue in audit_results['issues']:
        f.write(f"- {issue}\n")
    
    f.write("\n## Recommendations\n\n")
    for rec in audit_results['recommendations']:
        f.write(f"- {rec}\n")

print(f"\n📄 Full report saved to: {output_file}")
print("="*80)

