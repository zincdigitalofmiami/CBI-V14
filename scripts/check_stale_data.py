#!/usr/bin/env python3
"""
Comprehensive Stale Data Check for All Day 1 Export Datasets
Checks data freshness, date gaps, and completeness for all 12 export datasets
"""
from google.cloud import bigquery
from datetime import datetime, timedelta
import sys
from typing import Dict, List, Optional, Tuple

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"
WAREHOUSE_DATASET = "forecasting_data_warehouse"

client = bigquery.Client(project=PROJECT_ID)

print("="*80)
print("🔍 COMPREHENSIVE STALE DATA CHECK - ALL DAY 1 DATASETS")
print("="*80)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Project: {PROJECT_ID}")
print("="*80)

all_checks_passed = True
stale_issues = []
warnings = []
freshness_report = []

# Define all datasets to check
DATASETS_TO_CHECK = {
    # Primary Training Tables
    'production_training_data_1w': {
        'table': f'{PROJECT_ID}.{DATASET_ID}.production_training_data_1w',
        'date_col': 'date',
        'expected_fresh_days': 7,  # Should be within 7 days
        'description': '1W horizon training data',
        'min_rows': 1000
    },
    'production_training_data_1m': {
        'table': f'{PROJECT_ID}.{DATASET_ID}.production_training_data_1m',
        'date_col': 'date',
        'expected_fresh_days': 7,
        'description': '1M horizon training data',
        'min_rows': 1000
    },
    'production_training_data_3m': {
        'table': f'{PROJECT_ID}.{DATASET_ID}.production_training_data_3m',
        'date_col': 'date',
        'expected_fresh_days': 7,
        'description': '3M horizon training data',
        'min_rows': 1000
    },
    'production_training_data_6m': {
        'table': f'{PROJECT_ID}.{DATASET_ID}.production_training_data_6m',
        'date_col': 'date',
        'expected_fresh_days': 7,
        'description': '6M horizon training data',
        'min_rows': 1000
    },
    'production_training_data_12m': {
        'table': f'{PROJECT_ID}.{DATASET_ID}.production_training_data_12m',
        'date_col': 'date',
        'expected_fresh_days': 7,
        'description': '12M horizon training data',
        'min_rows': 1000
    },
    'trump_rich_2023_2025': {
        'table': f'{PROJECT_ID}.{DATASET_ID}.trump_rich_2023_2025',
        'date_col': 'date',
        'expected_fresh_days': 7,
        'description': 'Trump-era training table',
        'min_rows': 700,
        'expected_max_date': '2025-12-31'  # Should extend to end of 2025
    },
    # Historical Full Dataset
    'historical_full': {
        'table': f'{PROJECT_ID}.{WAREHOUSE_DATASET}.soybean_oil_prices',
        'date_col': 'time',  # Note: Uses 'time' (TIMESTAMP), not 'date'
        'expected_fresh_days': 7,  # Should have recent data
        'description': 'Historical full dataset (125+ years)',
        'min_rows': 10000
    }
}

# Regime-specific datasets (filtered from production_training_data_1m)
REGIME_DATASETS = {
    'trump_2.0_2023_2025': {
        'base_table': f'{PROJECT_ID}.{DATASET_ID}.production_training_data_1m',
        'date_filter': "date >= '2023-01-01' AND date < '2026-01-01'",
        'expected_min_date': '2023-01-01',
        'expected_max_date': '2025-12-31',
        'description': 'Trump 2.0 regime (2023-2025)'
    },
    'trade_war_2017_2019': {
        'base_table': f'{PROJECT_ID}.{DATASET_ID}.production_training_data_1m',
        'date_filter': "date >= '2017-01-01' AND date < '2020-01-01'",
        'expected_min_date': '2017-01-01',
        'expected_max_date': '2019-12-31',
        'description': 'Trade war regime (2017-2019)',
        'note': 'WARNING: Base table only starts from 2020 - this regime will have no data'
    },
    'inflation_2021_2022': {
        'base_table': f'{PROJECT_ID}.{DATASET_ID}.production_training_data_1m',
        'date_filter': "date >= '2021-01-01' AND date < '2023-01-01'",
        'expected_min_date': '2021-01-01',
        'expected_max_date': '2022-12-31',
        'description': 'Inflation regime (2021-2022)'
    },
    'crisis_2008_2020': {
        'base_table': f'{PROJECT_ID}.{DATASET_ID}.production_training_data_1m',
        'date_filter': "(date >= '2008-01-01' AND date < '2009-01-01') OR (date >= '2020-01-01' AND date < '2021-01-01')",
        'expected_min_date': '2008-01-01',
        'expected_max_date': '2020-12-31',
        'description': 'Crisis regime (2008 + 2020)',
        'note': 'WARNING: Base table only starts from 2020 - only 2020 crisis data will be present'
    },
    'historical_pre2000': {
        'base_table': f'{PROJECT_ID}.{DATASET_ID}.production_training_data_1m',
        'date_filter': "date < '2000-01-01'",
        'expected_max_date': '1999-12-31',
        'description': 'Historical pre-2000',
        'note': 'WARNING: Base table only starts from 2020 - this regime will have no data'
    }
}

def check_table_exists(table_path: str) -> bool:
    """Check if table exists"""
    try:
        parts = table_path.split('.')
        if len(parts) != 3:
            return False
        project, dataset, table = parts
        
        query = f"""
        SELECT COUNT(*) as table_exists
        FROM `{project}.{dataset}.INFORMATION_SCHEMA.TABLES`
        WHERE table_name = '{table}'
        """
        result = client.query(query).to_dataframe()
        return result.iloc[0]['table_exists'] > 0
    except Exception as e:
        print(f"  ❌ Error checking table existence: {e}")
        return False

def check_data_freshness(table_path: str, date_col: str, expected_fresh_days: int) -> Optional[Dict]:
    """Check data freshness and return statistics"""
    try:
        # Handle both DATE and TIMESTAMP columns
        if date_col == 'time':
            # TIMESTAMP column - need to convert to DATE
            date_expr = f"DATE({date_col})"
            max_date_expr = f"DATE(MAX({date_col}))"
        else:
            # DATE column
            date_expr = date_col
            max_date_expr = f"MAX({date_col})"
        
        query = f"""
        SELECT 
            COUNT(*) as total_rows,
            MIN({date_expr}) as earliest_date,
            MAX({date_expr}) as latest_date,
            DATE_DIFF(CURRENT_DATE(), {max_date_expr}, DAY) as days_behind,
            COUNT(DISTINCT {date_expr}) as unique_dates,
            COUNT(*) - COUNT(DISTINCT {date_expr}) as duplicate_dates
        FROM `{table_path}`
        WHERE {date_col} IS NOT NULL
        """
        result = client.query(query).to_dataframe()
        
        if result.empty or result.iloc[0]['total_rows'] == 0:
            return None
        
        row = result.iloc[0]
        return {
            'total_rows': int(row['total_rows']),
            'earliest_date': row['earliest_date'],
            'latest_date': row['latest_date'],
            'days_behind': int(row['days_behind']) if row['days_behind'] is not None else None,
            'unique_dates': int(row['unique_dates']),
            'duplicate_dates': int(row['duplicate_dates'])
        }
    except Exception as e:
        print(f"  ❌ Error checking freshness: {e}")
        return None

def check_date_gaps(table_path: str, date_col: str, max_gap_days: int = 30) -> List[Tuple]:
    """Check for significant gaps in date sequences"""
    try:
        # Handle both DATE and TIMESTAMP columns
        if date_col == 'time':
            date_expr = f"DATE({date_col})"
        else:
            date_expr = date_col
        
        query = f"""
        WITH date_sequence AS (
            SELECT 
                {date_expr} as date_val,
                LAG({date_expr}) OVER (ORDER BY {date_expr}) as prev_date
            FROM `{table_path}`
            WHERE {date_col} IS NOT NULL
            ORDER BY {date_expr}
        )
        SELECT 
            prev_date as gap_start,
            date_val as gap_end,
            DATE_DIFF(date_val, prev_date, DAY) as gap_days
        FROM date_sequence
        WHERE prev_date IS NOT NULL
          AND DATE_DIFF(date_val, prev_date, DAY) > {max_gap_days}
        ORDER BY gap_days DESC
        LIMIT 10
        """
        result = client.query(query).to_dataframe()
        
        gaps = []
        for _, row in result.iterrows():
            gaps.append((row['gap_start'], row['gap_end'], int(row['gap_days'])))
        
        return gaps
    except Exception as e:
        print(f"  ⚠️  Error checking date gaps: {e}")
        return []

def check_dataset(name: str, config: Dict):
    """Comprehensive check for a dataset"""
    global all_checks_passed, stale_issues, warnings, freshness_report
    
    print(f"\n{'='*80}")
    print(f"📊 CHECKING: {name}")
    print(f"   {config['description']}")
    print(f"{'='*80}")
    
    table_path = config['table']
    date_col = config['date_col']
    expected_fresh_days = config.get('expected_fresh_days', 7)
    
    # Check table exists
    if not check_table_exists(table_path):
        print(f"  ❌ Table does not exist: {table_path}")
        stale_issues.append(f"{name}: Table missing")
        all_checks_passed = False
        return
    
    print(f"  ✅ Table exists")
    
    # Check data freshness
    freshness = check_data_freshness(table_path, date_col, expected_fresh_days)
    
    if not freshness:
        print(f"  ❌ No data found in table")
        stale_issues.append(f"{name}: No data")
        all_checks_passed = False
        return
    
    # Report freshness
    print(f"  📊 Total rows: {freshness['total_rows']:,}")
    print(f"  📅 Date range: {freshness['earliest_date']} to {freshness['latest_date']}")
    print(f"  📈 Unique dates: {freshness['unique_dates']:,}")
    
    if freshness['duplicate_dates'] > 0:
        print(f"  ⚠️  Duplicate dates: {freshness['duplicate_dates']:,}")
        warnings.append(f"{name}: {freshness['duplicate_dates']} duplicate dates")
    
    # Check if data is stale
    days_behind = freshness['days_behind']
    if days_behind is not None:
        print(f"  ⏰ Days behind current date: {days_behind}")
        
        if days_behind > expected_fresh_days:
            status = "🔴 STALE"
            if days_behind > 30:
                status = "🔴 VERY STALE"
            elif days_behind > 60:
                status = "🔴 CRITICALLY STALE"
            
            print(f"  {status}: Data is {days_behind} days old (expected < {expected_fresh_days} days)")
            stale_issues.append(f"{name}: {days_behind} days stale (latest: {freshness['latest_date']})")
            all_checks_passed = False
        else:
            print(f"  ✅ Data is fresh ({days_behind} days old)")
    else:
        print(f"  ⚠️  Could not calculate days behind")
        warnings.append(f"{name}: Could not determine freshness")
    
    # Check minimum rows
    min_rows = config.get('min_rows', 0)
    if freshness['total_rows'] < min_rows:
        print(f"  ⚠️  Low row count: {freshness['total_rows']:,} (< {min_rows:,} expected)")
        warnings.append(f"{name}: Low row count ({freshness['total_rows']:,} < {min_rows:,})")
    
    # Check expected max date if specified
    expected_max_date = config.get('expected_max_date')
    if expected_max_date:
        latest_date_str = str(freshness['latest_date']).split()[0]  # Get date part only
        if latest_date_str < expected_max_date:
            print(f"  ⚠️  Latest date ({latest_date_str}) is before expected max ({expected_max_date})")
            warnings.append(f"{name}: Latest date {latest_date_str} < expected {expected_max_date}")
    
    # Check for date gaps
    print(f"  🔍 Checking for date gaps (>30 days)...")
    gaps = check_date_gaps(table_path, date_col, max_gap_days=30)
    if gaps:
        print(f"  ⚠️  Found {len(gaps)} significant date gaps:")
        for gap_start, gap_end, gap_days in gaps[:5]:  # Show top 5
            print(f"     Gap: {gap_start} to {gap_end} ({gap_days} days)")
        warnings.append(f"{name}: {len(gaps)} date gaps found")
    else:
        print(f"  ✅ No significant date gaps found")
    
    # Store freshness report
    freshness_report.append({
        'dataset': name,
        'latest_date': freshness['latest_date'],
        'days_behind': days_behind,
        'total_rows': freshness['total_rows'],
        'status': 'STALE' if (days_behind and days_behind > expected_fresh_days) else 'FRESH'
    })

def check_regime_dataset(name: str, config: Dict):
    """Check regime-specific dataset (filtered from base table)"""
    global all_checks_passed, stale_issues, warnings
    
    print(f"\n{'='*80}")
    print(f"📊 CHECKING REGIME: {name}")
    print(f"   {config['description']}")
    if 'note' in config:
        print(f"   ⚠️  {config['note']}")
    print(f"{'='*80}")
    
    base_table = config['base_table']
    date_filter = config['date_filter']
    
    # Check base table exists
    if not check_table_exists(base_table):
        print(f"  ❌ Base table does not exist: {base_table}")
        stale_issues.append(f"{name}: Base table missing")
        all_checks_passed = False
        return
    
    try:
        # Query regime-specific data
        query = f"""
        SELECT 
            COUNT(*) as total_rows,
            MIN(date) as earliest_date,
            MAX(date) as latest_date,
            DATE_DIFF(CURRENT_DATE(), DATE(MAX(date)), DAY) as days_behind,
            COUNT(DISTINCT date) as unique_dates
        FROM `{base_table}`
        WHERE {date_filter}
          AND date IS NOT NULL
        """
        result = client.query(query).to_dataframe()
        
        if result.empty or result.iloc[0]['total_rows'] == 0:
            if 'note' in config and 'WARNING' in config['note']:
                # Expected missing data - don't treat as critical error
                print(f"  ⚠️  No data found for regime filter (expected - see note above)")
                warnings.append(f"{name}: No data matching regime filter (expected due to base table date range)")
            else:
                print(f"  ❌ No data found for regime filter")
                stale_issues.append(f"{name}: No data matching regime filter")
                all_checks_passed = False
            return
        
        row = result.iloc[0]
        total_rows = int(row['total_rows'])
        earliest_date = row['earliest_date']
        latest_date = row['latest_date']
        days_behind = int(row['days_behind']) if row['days_behind'] is not None else None
        unique_dates = int(row['unique_dates'])
        
        print(f"  ✅ Data found: {total_rows:,} rows")
        print(f"  📅 Date range: {earliest_date} to {latest_date}")
        print(f"  📈 Unique dates: {unique_dates:,}")
        
        # Check expected date ranges
        expected_min = config.get('expected_min_date')
        expected_max = config.get('expected_max_date')
        
        if expected_min:
            earliest_str = str(earliest_date).split()[0]
            if earliest_str > expected_min:
                print(f"  ⚠️  Earliest date ({earliest_str}) is after expected min ({expected_min})")
                warnings.append(f"{name}: Earliest date {earliest_str} > expected {expected_min}")
        
        if expected_max:
            latest_str = str(latest_date).split()[0]
            if latest_str < expected_max:
                print(f"  ⚠️  Latest date ({latest_str}) is before expected max ({expected_max})")
                warnings.append(f"{name}: Latest date {latest_str} < expected {expected_max}")
        
        # Check if data is stale (for current regime)
        if 'trump_2.0' in name and days_behind is not None:
            if days_behind > 7:
                print(f"  🔴 STALE: Current regime data is {days_behind} days old")
                stale_issues.append(f"{name}: {days_behind} days stale")
                all_checks_passed = False
            else:
                print(f"  ✅ Current regime data is fresh ({days_behind} days old)")
        
    except Exception as e:
        print(f"  ❌ Error checking regime dataset: {e}")
        stale_issues.append(f"{name}: Check failed - {e}")
        all_checks_passed = False

# Run checks for all primary datasets
print("\n" + "="*80)
print("CHECKING PRIMARY TRAINING TABLES")
print("="*80)

for name, config in DATASETS_TO_CHECK.items():
    check_dataset(name, config)

# Run checks for regime-specific datasets
print("\n" + "="*80)
print("CHECKING REGIME-SPECIFIC DATASETS")
print("="*80)

for name, config in REGIME_DATASETS.items():
    check_regime_dataset(name, config)

# Final summary
print("\n" + "="*80)
print("📋 STALE DATA CHECK SUMMARY")
print("="*80)

if all_checks_passed:
    print("✅ ALL DATASETS ARE FRESH - No stale data detected")
else:
    print("❌ STALE DATA DETECTED - Review issues below")

if stale_issues:
    print(f"\n🔴 STALE DATA ISSUES ({len(stale_issues)}):")
    for issue in stale_issues:
        print(f"   - {issue}")

if warnings:
    print(f"\n⚠️  WARNINGS ({len(warnings)}):")
    for warning in warnings:
        print(f"   - {warning}")

# Freshness summary table
print(f"\n📊 FRESHNESS SUMMARY:")
print(f"{'Dataset':<40} {'Latest Date':<15} {'Days Behind':<15} {'Status':<10}")
print("-" * 80)
for report in freshness_report:
    latest = str(report['latest_date']).split()[0] if report['latest_date'] else 'N/A'
    days = report['days_behind'] if report['days_behind'] is not None else 'N/A'
    status = report['status']
    print(f"{report['dataset']:<40} {latest:<15} {str(days):<15} {status:<10}")

print("="*80)

# Exit with error code if stale data found
if not all_checks_passed:
    print("\n❌ ACTION REQUIRED: Fix stale data issues before proceeding with Day 1 exports")
    sys.exit(1)
else:
    print("\n✅ ALL CHECKS PASSED - Ready for Day 1 data exports")

