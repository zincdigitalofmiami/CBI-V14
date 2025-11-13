#!/usr/bin/env python3
"""
Comprehensive Hidden Data Discovery
Finds ALL data sources across ALL BigQuery datasets
"""
from google.cloud import bigquery
from datetime import datetime
import sys
from collections import defaultdict

PROJECT_ID = "cbi-v14"
client = bigquery.Client(project=PROJECT_ID)

print("="*80)
print("🔍 COMPREHENSIVE HIDDEN DATA DISCOVERY")
print("="*80)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Project: {PROJECT_ID}")
print("="*80)

# Discover all datasets
print("\n" + "="*80)
print("STEP 1: DISCOVERING ALL DATASETS")
print("="*80)

try:
    # Use BigQuery client API to list datasets
    all_datasets = []
    for dataset in client.list_datasets(project=PROJECT_ID):
        all_datasets.append(dataset.dataset_id)
    
    all_datasets.sort()
    print(f"\n📊 Found {len(all_datasets)} datasets:")
    for ds in all_datasets:
        print(f"   - {ds}")
except Exception as e:
    print(f"❌ Error discovering datasets: {e}")
    # Fallback to INFORMATION_SCHEMA
    try:
        datasets_query = f"""
        SELECT schema_name as dataset_id
        FROM `{PROJECT_ID}.INFORMATION_SCHEMA.SCHEMATA`
        ORDER BY schema_name
        """
        datasets_df = client.query(datasets_query).to_dataframe()
        all_datasets = datasets_df['dataset_id'].tolist()
        print(f"\n📊 Found {len(all_datasets)} datasets (via INFORMATION_SCHEMA):")
        for ds in all_datasets:
            print(f"   - {ds}")
    except Exception as e2:
        print(f"❌ Fallback also failed: {e2}")
        sys.exit(1)

# Discover all tables across all datasets
print("\n" + "="*80)
print("STEP 2: DISCOVERING ALL TABLES")
print("="*80)

all_tables = []
dataset_table_map = defaultdict(list)

for dataset_id in all_datasets:
    try:
        query = f"""
        SELECT 
            table_name,
            table_type,
            creation_time
        FROM `{PROJECT_ID}.{dataset_id}.INFORMATION_SCHEMA.TABLES`
        WHERE table_type = 'BASE TABLE'
        ORDER BY table_name
        """
        result = client.query(query).to_dataframe()
        
        if not result.empty:
            for _, row in result.iterrows():
                table_info = {
                    'dataset': dataset_id,
                    'table': row['table_name'],
                    'type': row['table_type'],
                    'created': row['creation_time']
                }
                all_tables.append(table_info)
                dataset_table_map[dataset_id].append(row['table_name'])
            
            print(f"\n📊 {dataset_id}: {len(result)} tables")
    except Exception as e:
        print(f"  ⚠️  Error querying {dataset_id}: {e}")

print(f"\n📊 Total tables found: {len(all_tables)}")

# Check each table for data
print("\n" + "="*80)
print("STEP 3: ANALYZING ALL TABLES FOR DATA")
print("="*80)

tables_with_data = []
tables_with_historical_data = []
date_column_map = {}

for table_info in all_tables:
    dataset = table_info['dataset']
    table = table_info['table']
    table_path = f"{PROJECT_ID}.{dataset}.{table}"
    
    try:
        # Get row count
        count_query = f"SELECT COUNT(*) as row_count FROM `{table_path}`"
        count_result = client.query(count_query).to_dataframe()
        row_count = int(count_result.iloc[0]['row_count']) if not count_result.empty else 0
        
        if row_count == 0:
            continue
        
        # Try to find date columns
        schema_query = f"""
        SELECT column_name, data_type
        FROM `{PROJECT_ID}.{dataset}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{table}'
          AND (
            LOWER(column_name) LIKE '%date%' 
            OR LOWER(column_name) LIKE '%time%'
            OR LOWER(column_name) LIKE '%timestamp%'
            OR data_type IN ('DATE', 'DATETIME', 'TIMESTAMP')
          )
        ORDER BY ordinal_position
        """
        schema_result = client.query(schema_query).to_dataframe()
        
        date_cols = []
        if not schema_result.empty:
            date_cols = schema_result['column_name'].tolist()
        
        # If we found date columns, get date range
        date_range = None
        earliest_date = None
        latest_date = None
        date_span_years = None
        
        if date_cols:
            # Try the first date column
            date_col = date_cols[0]
            
            # Determine if it needs DATE() conversion
            col_type = schema_result[schema_result['column_name'] == date_col]['data_type'].iloc[0]
            
            if col_type in ['TIMESTAMP', 'DATETIME']:
                date_expr = f"DATE({date_col})"
            else:
                date_expr = date_col
            
            try:
                date_query = f"""
                SELECT 
                    MIN({date_expr}) as earliest_date,
                    MAX({date_expr}) as latest_date,
                    DATE_DIFF(MAX({date_expr}), MIN({date_expr}), DAY) as date_span_days
                FROM `{table_path}`
                WHERE {date_col} IS NOT NULL
                """
                date_result = client.query(date_query).to_dataframe()
                
                if not date_result.empty and date_result.iloc[0]['earliest_date']:
                    earliest_date = date_result.iloc[0]['earliest_date']
                    latest_date = date_result.iloc[0]['latest_date']
                    span_days = int(date_result.iloc[0]['date_span_days']) if date_result.iloc[0]['date_span_days'] else 0
                    date_span_years = span_days / 365.25
                    
                    date_range = f"{earliest_date} to {latest_date}"
            except Exception as e:
                pass  # Date query failed, skip
        
        table_info['row_count'] = row_count
        table_info['date_columns'] = date_cols
        table_info['date_range'] = date_range
        table_info['earliest_date'] = earliest_date
        table_info['latest_date'] = latest_date
        table_info['date_span_years'] = date_span_years
        
        tables_with_data.append(table_info)
        
        # Check if it has historical data (more than 5 years)
        if date_span_years and date_span_years > 5:
            tables_with_historical_data.append(table_info)
            
    except Exception as e:
        # Skip tables we can't query
        continue

# Sort by row count
tables_with_data.sort(key=lambda x: x.get('row_count', 0), reverse=True)
tables_with_historical_data.sort(key=lambda x: x.get('date_span_years', 0), reverse=True)

# Report findings
print("\n" + "="*80)
print("📊 TABLES WITH DATA (Top 50 by row count)")
print("="*80)

print(f"\n{'Dataset':<30} {'Table':<40} {'Rows':<15} {'Date Range':<30} {'Years':<10}")
print("-" * 125)

for table_info in tables_with_data[:50]:
    dataset = table_info['dataset']
    table = table_info['table']
    rows = table_info.get('row_count', 0)
    date_range = table_info.get('date_range', 'No dates')
    years = f"{table_info.get('date_span_years', 0):.1f}" if table_info.get('date_span_years') else 'N/A'
    
    # Truncate long names
    dataset_display = dataset[:28] + '..' if len(dataset) > 30 else dataset
    table_display = table[:38] + '..' if len(table) > 40 else table
    date_display = date_range[:28] + '..' if len(date_range) > 30 else date_range
    
    print(f"{dataset_display:<30} {table_display:<40} {rows:>13,} {date_display:<30} {years:>10}")

# Historical data report
print("\n" + "="*80)
print("📅 TABLES WITH HISTORICAL DATA (>5 years)")
print("="*80)

if tables_with_historical_data:
    print(f"\n{'Dataset':<30} {'Table':<40} {'Years':<10} {'Date Range':<40}")
    print("-" * 120)
    
    for table_info in tables_with_historical_data[:30]:
        dataset = table_info['dataset']
        table = table_info['table']
        years = table_info.get('date_span_years', 0)
        date_range = table_info.get('date_range', 'No dates')
        
        dataset_display = dataset[:28] + '..' if len(dataset) > 30 else dataset
        table_display = table[:38] + '..' if len(table) > 40 else table
        date_display = date_range[:38] + '..' if len(date_range) > 40 else date_range
        
        print(f"{dataset_display:<30} {table_display:<40} {years:>8.1f} {date_display:<40}")
else:
    print("\n⚠️  No tables found with >5 years of historical data")

# Look for archived/backup tables
print("\n" + "="*80)
print("📦 ARCHIVED/BACKUP TABLES (Potential Historical Data)")
print("="*80)

archived_tables = [t for t in tables_with_data if any(
    keyword in t['table'].lower() 
    for keyword in ['archive', 'backup', 'historical', 'old', 'legacy', 'snapshot']
)]

if archived_tables:
    print(f"\nFound {len(archived_tables)} archived/backup tables:")
    for table_info in archived_tables[:20]:
        dataset = table_info['dataset']
        table = table_info['table']
        rows = table_info.get('row_count', 0)
        date_range = table_info.get('date_range', 'No dates')
        print(f"  📦 {dataset}.{table}: {rows:,} rows, {date_range}")
else:
    print("\n⚠️  No archived/backup tables found")

# Look for price/commodity tables
print("\n" + "="*80)
print("💰 PRICE/COMMODITY TABLES")
print("="*80)

price_tables = [t for t in tables_with_data if any(
    keyword in t['table'].lower() 
    for keyword in ['price', 'prices', 'futures', 'commodity', 'oil', 'corn', 'wheat', 'soy']
)]

if price_tables:
    print(f"\nFound {len(price_tables)} price/commodity tables:")
    for table_info in sorted(price_tables, key=lambda x: x.get('row_count', 0), reverse=True)[:30]:
        dataset = table_info['dataset']
        table = table_info['table']
        rows = table_info.get('row_count', 0)
        date_range = table_info.get('date_range', 'No dates')
        years = table_info.get('date_span_years', 0)
        print(f"  💰 {dataset}.{table}: {rows:,} rows, {years:.1f} years, {date_range}")
else:
    print("\n⚠️  No price/commodity tables found")

# Summary statistics
print("\n" + "="*80)
print("📊 SUMMARY STATISTICS")
print("="*80)

total_rows = sum(t.get('row_count', 0) for t in tables_with_data)
tables_with_dates = len([t for t in tables_with_data if t.get('date_range')])
tables_historical = len(tables_with_historical_data)

print(f"\n📊 Total tables with data: {len(tables_with_data)}")
print(f"📊 Total rows across all tables: {total_rows:,}")
print(f"📊 Tables with date columns: {tables_with_dates}")
print(f"📊 Tables with >5 years of history: {tables_historical}")

# Dataset breakdown
print(f"\n📊 Tables by dataset:")
for dataset in sorted(dataset_table_map.keys()):
    count = len(dataset_table_map[dataset])
    data_count = len([t for t in tables_with_data if t['dataset'] == dataset])
    print(f"   {dataset}: {data_count}/{count} tables have data")

print("="*80)

# Save detailed report
report_file = "docs/audits/HIDDEN_DATA_DISCOVERY_20251112.md"
print(f"\n💾 Saving detailed report to: {report_file}")

