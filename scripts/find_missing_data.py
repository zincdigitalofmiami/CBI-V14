#!/usr/bin/env python3
"""
Comprehensive Missing Data Finder
Identifies all missing, stale, or incomplete data sources
"""
from google.cloud import bigquery
from datetime import datetime, timedelta
import sys
from typing import Dict, List, Optional

PROJECT_ID = "cbi-v14"
WAREHOUSE_DATASET = "forecasting_data_warehouse"
MODELS_DATASET = "models_v4"

client = bigquery.Client(project=PROJECT_ID)

print("="*80)
print("🔍 COMPREHENSIVE MISSING DATA AUDIT")
print("="*80)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Project: {PROJECT_ID}")
print("="*80)

missing_tables = []
stale_tables = []
empty_tables = []
low_data_tables = []
data_quality_issues = []

# Expected data sources based on manifest and ingestion scripts
EXPECTED_DATA_SOURCES = {
    # Commodity Prices
    'soybean_oil_prices': {'dataset': WAREHOUSE_DATASET, 'date_col': 'time', 'min_rows': 1000, 'expected_days_old': 7},
    'palm_oil_prices': {'dataset': WAREHOUSE_DATASET, 'date_col': 'time', 'min_rows': 500, 'expected_days_old': 7},
    'canola_oil_prices': {'dataset': WAREHOUSE_DATASET, 'date_col': 'date', 'min_rows': 500, 'expected_days_old': 7},
    'corn_prices': {'dataset': WAREHOUSE_DATASET, 'date_col': 'time', 'min_rows': 500, 'expected_days_old': 7},
    'crude_oil_prices': {'dataset': WAREHOUSE_DATASET, 'date_col': 'time', 'min_rows': 500, 'expected_days_old': 7},
    'gold_prices': {'dataset': WAREHOUSE_DATASET, 'date_col': 'time', 'min_rows': 500, 'expected_days_old': 7},
    'natural_gas_prices': {'dataset': WAREHOUSE_DATASET, 'date_col': 'time', 'min_rows': 100, 'expected_days_old': 7},
    
    # Market Indicators
    'vix_daily': {'dataset': WAREHOUSE_DATASET, 'date_col': 'date', 'min_rows': 500, 'expected_days_old': 7},
    'cftc_cot': {'dataset': WAREHOUSE_DATASET, 'date_col': 'report_date', 'min_rows': 200, 'expected_days_old': 14},
    'yahoo_finance_enhanced': {'dataset': WAREHOUSE_DATASET, 'date_col': 'date', 'min_rows': 500, 'expected_days_old': 7},
    
    # News & Sentiment
    'news_intelligence': {'dataset': WAREHOUSE_DATASET, 'date_col': 'processed_timestamp', 'min_rows': 100, 'expected_days_old': 1},
    'news_advanced': {'dataset': WAREHOUSE_DATASET, 'date_col': 'published_date', 'min_rows': 100, 'expected_days_old': 1},
    'social_sentiment': {'dataset': WAREHOUSE_DATASET, 'date_col': 'timestamp', 'min_rows': 100, 'expected_days_old': 7},
    'trump_policy_intelligence': {'dataset': WAREHOUSE_DATASET, 'date_col': 'timestamp', 'min_rows': 50, 'expected_days_old': 7},
    
    # Economic Data
    'economic_indicators': {'dataset': WAREHOUSE_DATASET, 'date_col': 'time', 'min_rows': 500, 'expected_days_old': 30},
    'currency_data': {'dataset': WAREHOUSE_DATASET, 'date_col': 'date', 'min_rows': 1000, 'expected_days_old': 7},
    'biofuel_prices': {'dataset': WAREHOUSE_DATASET, 'date_col': 'date', 'min_rows': 100, 'expected_days_old': 7},
    
    # Supply Chain
    'china_soybean_imports': {'dataset': WAREHOUSE_DATASET, 'date_col': 'date', 'min_rows': 50, 'expected_days_old': 30},
    'argentina_crisis_tracker': {'dataset': WAREHOUSE_DATASET, 'date_col': 'date', 'min_rows': 50, 'expected_days_old': 7},
    'industrial_demand_indicators': {'dataset': WAREHOUSE_DATASET, 'date_col': 'date', 'min_rows': 10, 'expected_days_old': 7},
    
    # Weather
    'weather_data': {'dataset': WAREHOUSE_DATASET, 'date_col': 'date', 'min_rows': 1000, 'expected_days_old': 7},
    
    # Training Data
    'production_training_data_1w': {'dataset': MODELS_DATASET, 'date_col': 'date', 'min_rows': 1000, 'expected_days_old': 7},
    'production_training_data_1m': {'dataset': MODELS_DATASET, 'date_col': 'date', 'min_rows': 1000, 'expected_days_old': 7},
    'production_training_data_3m': {'dataset': MODELS_DATASET, 'date_col': 'date', 'min_rows': 1000, 'expected_days_old': 7},
    'production_training_data_6m': {'dataset': MODELS_DATASET, 'date_col': 'date', 'min_rows': 1000, 'expected_days_old': 7},
    'production_training_data_12m': {'dataset': MODELS_DATASET, 'date_col': 'date', 'min_rows': 1000, 'expected_days_old': 7},
    'trump_rich_2023_2025': {'dataset': MODELS_DATASET, 'date_col': 'date', 'min_rows': 700, 'expected_days_old': 7},
}

def get_all_tables_in_dataset(dataset_id: str) -> List[str]:
    """Get all table names in a dataset"""
    try:
        query = f"""
        SELECT table_name
        FROM `{PROJECT_ID}.{dataset_id}.INFORMATION_SCHEMA.TABLES`
        WHERE table_type = 'BASE TABLE'
        ORDER BY table_name
        """
        result = client.query(query).to_dataframe()
        return result['table_name'].tolist() if not result.empty else []
    except Exception as e:
        print(f"  ⚠️  Error listing tables in {dataset_id}: {e}")
        return []

def check_table_data(table_name: str, dataset: str, date_col: str, min_rows: int, expected_days_old: int) -> Dict:
    """Check a table for data completeness and freshness"""
    table_path = f"{PROJECT_ID}.{dataset}.{table_name}"
    
    result = {
        'exists': False,
        'row_count': 0,
        'latest_date': None,
        'days_old': None,
        'status': 'MISSING',
        'issues': []
    }
    
    # Check if table exists
    try:
        query = f"""
        SELECT COUNT(*) as table_exists
        FROM `{PROJECT_ID}.{dataset}.INFORMATION_SCHEMA.TABLES`
        WHERE table_name = '{table_name}'
        """
        exists_result = client.query(query).to_dataframe()
        if exists_result.empty or exists_result.iloc[0]['table_exists'] == 0:
            result['status'] = 'MISSING'
            result['issues'].append('Table does not exist')
            return result
        
        result['exists'] = True
    except Exception as e:
        result['issues'].append(f"Error checking existence: {e}")
        return result
    
    # Check data
    try:
        # Handle different date column types
        # Check if column is TIMESTAMP/DATETIME (needs DATE() conversion) or already DATE
        timestamp_cols = ['time', 'timestamp', 'processed_timestamp', 'published_date', 'ingest_timestamp_utc']
        if date_col in timestamp_cols or 'timestamp' in date_col.lower() or date_col == 'published_date':
            date_expr = f"DATE({date_col})"
            max_date_expr = f"DATE(MAX({date_col}))"
        else:
            date_expr = date_col
            max_date_expr = f"MAX({date_col})"
        
        query = f"""
        SELECT 
            COUNT(*) as row_count,
            MAX({date_expr}) as latest_date,
            DATE_DIFF(CURRENT_DATE(), {max_date_expr}, DAY) as days_behind
        FROM `{table_path}`
        WHERE {date_col} IS NOT NULL
        """
        data_result = client.query(query).to_dataframe()
        
        if data_result.empty:
            result['status'] = 'EMPTY'
            result['issues'].append('No data found')
            return result
        
        row = data_result.iloc[0]
        result['row_count'] = int(row['row_count'])
        result['latest_date'] = row['latest_date']
        result['days_old'] = int(row['days_behind']) if row['days_behind'] is not None else None
        
        # Determine status
        if result['row_count'] == 0:
            result['status'] = 'EMPTY'
            result['issues'].append('Table is empty')
        elif result['row_count'] < min_rows:
            result['status'] = 'LOW_DATA'
            result['issues'].append(f"Only {result['row_count']} rows (expected {min_rows}+)")
        elif result['days_old'] and result['days_old'] > expected_days_old:
            result['status'] = 'STALE'
            result['issues'].append(f"Data is {result['days_old']} days old (expected < {expected_days_old} days)")
        else:
            result['status'] = 'OK'
            
    except Exception as e:
        result['status'] = 'ERROR'
        result['issues'].append(f"Error querying data: {e}")
    
    return result

# Step 1: List all tables in datasets
print("\n" + "="*80)
print("STEP 1: DISCOVERING ALL TABLES")
print("="*80)

warehouse_tables = get_all_tables_in_dataset(WAREHOUSE_DATASET)
models_tables = get_all_tables_in_dataset(MODELS_DATASET)

print(f"\n📊 Found {len(warehouse_tables)} tables in {WAREHOUSE_DATASET}")
print(f"📊 Found {len(models_tables)} tables in {MODELS_DATASET}")

# Step 2: Check expected data sources
print("\n" + "="*80)
print("STEP 2: CHECKING EXPECTED DATA SOURCES")
print("="*80)

results = {}
for table_name, config in EXPECTED_DATA_SOURCES.items():
    print(f"\n🔍 Checking: {table_name}")
    result = check_table_data(
        table_name,
        config['dataset'],
        config['date_col'],
        config['min_rows'],
        config['expected_days_old']
    )
    results[table_name] = result
    
    if result['status'] == 'MISSING':
        print(f"  ❌ MISSING: Table does not exist")
        missing_tables.append(table_name)
    elif result['status'] == 'EMPTY':
        print(f"  ❌ EMPTY: Table exists but has no data")
        empty_tables.append(table_name)
    elif result['status'] == 'LOW_DATA':
        print(f"  ⚠️  LOW DATA: {result['row_count']} rows (expected {config['min_rows']}+)")
        low_data_tables.append(table_name)
    elif result['status'] == 'STALE':
        print(f"  🔴 STALE: {result['days_old']} days old (latest: {result['latest_date']})")
        stale_tables.append(table_name)
    elif result['status'] == 'ERROR':
        print(f"  ❌ ERROR: {', '.join(result['issues'])}")
        data_quality_issues.append(table_name)
    else:
        print(f"  ✅ OK: {result['row_count']:,} rows, {result['days_old']} days old")

# Step 3: Find unexpected tables (might be missing from expected list)
print("\n" + "="*80)
print("STEP 3: FINDING UNEXPECTED TABLES")
print("="*80)

all_expected = set(EXPECTED_DATA_SOURCES.keys())
all_warehouse = set(warehouse_tables)
all_models = set(models_tables)

unexpected_warehouse = all_warehouse - {t for t, c in EXPECTED_DATA_SOURCES.items() if c['dataset'] == WAREHOUSE_DATASET}
unexpected_models = all_models - {t for t, c in EXPECTED_DATA_SOURCES.items() if c['dataset'] == MODELS_DATASET}

if unexpected_warehouse:
    print(f"\n📋 Additional tables in {WAREHOUSE_DATASET} (not in expected list):")
    for table in sorted(unexpected_warehouse):
        print(f"  - {table}")

if unexpected_models:
    print(f"\n📋 Additional tables in {MODELS_DATASET} (not in expected list):")
    for table in sorted(unexpected_models):
        print(f"  - {table}")

# Step 4: Check historical data completeness
print("\n" + "="*80)
print("STEP 4: CHECKING HISTORICAL DATA COMPLETENESS")
print("="*80)

# Check soybean_oil_prices for historical coverage
try:
    query = f"""
    SELECT 
        COUNT(*) as total_rows,
        MIN(DATE(time)) as earliest_date,
        MAX(DATE(time)) as latest_date,
        DATE_DIFF(MAX(DATE(time)), MIN(DATE(time)), DAY) as date_span_days,
        COUNT(DISTINCT DATE(time)) as unique_dates
    FROM `{PROJECT_ID}.{WAREHOUSE_DATASET}.soybean_oil_prices`
    WHERE time IS NOT NULL
    """
    hist_result = client.query(query).to_dataframe()
    if not hist_result.empty:
        row = hist_result.iloc[0]
        print(f"\n📊 Soybean Oil Prices Historical Coverage:")
        print(f"  Total rows: {int(row['total_rows']):,}")
        print(f"  Date range: {row['earliest_date']} to {row['latest_date']}")
        print(f"  Date span: {int(row['date_span_days']):,} days")
        print(f"  Unique dates: {int(row['unique_dates']):,}")
        
        # Check if we have 125+ years as mentioned in manifest
        years_span = int(row['date_span_days']) / 365.25
        if years_span < 10:
            print(f"  ⚠️  WARNING: Only {years_span:.1f} years of data (expected 125+ years)")
            data_quality_issues.append("soybean_oil_prices: Insufficient historical coverage")
except Exception as e:
    print(f"  ❌ Error checking historical data: {e}")

# Step 5: Check production training data date ranges
print("\n" + "="*80)
print("STEP 5: CHECKING PRODUCTION TRAINING DATA DATE RANGES")
print("="*80)

for horizon in ['1w', '1m', '3m', '6m', '12m']:
    table_name = f'production_training_data_{horizon}'
    try:
        query = f"""
        SELECT 
            MIN(date) as earliest_date,
            MAX(date) as latest_date,
            COUNT(*) as row_count,
            DATE_DIFF(MAX(date), MIN(date), DAY) as date_span_days
        FROM `{PROJECT_ID}.{MODELS_DATASET}.{table_name}`
        WHERE date IS NOT NULL
        """
        result = client.query(query).to_dataframe()
        if not result.empty:
            row = result.iloc[0]
            print(f"\n📊 {table_name}:")
            print(f"  Date range: {row['earliest_date']} to {row['latest_date']}")
            print(f"  Rows: {int(row['row_count']):,}")
            print(f"  Span: {int(row['date_span_days']):,} days")
            
            # Check if we're missing historical data
            if str(row['earliest_date']) > '2020-01-01':
                print(f"  ⚠️  WARNING: Missing data before 2020 (earliest: {row['earliest_date']})")
                data_quality_issues.append(f"{table_name}: Missing pre-2020 data")
    except Exception as e:
        print(f"  ❌ Error checking {table_name}: {e}")

# Final Summary
print("\n" + "="*80)
print("📋 MISSING DATA SUMMARY")
print("="*80)

print(f"\n❌ MISSING TABLES ({len(missing_tables)}):")
for table in missing_tables:
    print(f"   - {table}")

print(f"\n❌ EMPTY TABLES ({len(empty_tables)}):")
for table in empty_tables:
    print(f"   - {table}")

print(f"\n⚠️  LOW DATA TABLES ({len(low_data_tables)}):")
for table in low_data_tables:
    result = results[table]
    print(f"   - {table}: {result['row_count']} rows")

print(f"\n🔴 STALE TABLES ({len(stale_tables)}):")
for table in stale_tables:
    result = results[table]
    print(f"   - {table}: {result['days_old']} days old (latest: {result['latest_date']})")

print(f"\n⚠️  DATA QUALITY ISSUES ({len(data_quality_issues)}):")
for issue in data_quality_issues:
    print(f"   - {issue}")

# Summary statistics
total_expected = len(EXPECTED_DATA_SOURCES)
total_ok = sum(1 for r in results.values() if r['status'] == 'OK')
total_issues = len(missing_tables) + len(empty_tables) + len(low_data_tables) + len(stale_tables) + len(data_quality_issues)

print(f"\n📊 OVERALL STATUS:")
print(f"   Expected data sources: {total_expected}")
print(f"   ✅ OK: {total_ok}")
print(f"   ❌ Issues: {total_issues}")

print("="*80)

if total_issues > 0:
    print("\n❌ ACTION REQUIRED: Fix missing/stale data issues")
    sys.exit(1)
else:
    print("\n✅ ALL DATA SOURCES ARE COMPLETE AND FRESH")

