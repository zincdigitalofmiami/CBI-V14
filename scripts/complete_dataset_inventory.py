#!/usr/bin/env python3
"""
COMPLETE DATASET INVENTORY - Direct Approach
Find all datasets, list all tables, verify lost datasets
"""

from google.cloud import bigquery
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print("="*80)
print("COMPLETE DATASET INVENTORY")
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# Get all datasets
print("\n" + "="*80)
print("ALL DATASETS IN PROJECT")
print("="*80)

datasets = list(client.list_datasets())
print(f"\nFound {len(datasets)} datasets:\n")

dataset_inventory = {}

for dataset in sorted(datasets, key=lambda x: x.dataset_id):
    dataset_id = dataset.dataset_id
    print(f"📁 {dataset_id}")
    
    # Get tables
    try:
        tables = list(client.list_tables(dataset_id))
        dataset_inventory[dataset_id] = {
            'table_count': len(tables),
            'tables': [t.table_id for t in tables]
        }
        print(f"   {len(tables)} tables/views")
    except Exception as e:
        print(f"   ⚠️ Error: {str(e)[:60]}")
        dataset_inventory[dataset_id] = {'error': str(e)[:100]}

# Check critical datasets in detail
print("\n" + "="*80)
print("CRITICAL DATASETS - DETAILED ANALYSIS")
print("="*80)

critical_datasets = [
    'yahoo_finance_comprehensive',  # The "lost" dataset
    'forecasting_data_warehouse',   # Primary production
    'models_v4',                     # Training data
    'bkp',                          # Backups
    'archive_consolidation_nov6',   # Archive
    'models',                       # Legacy models
    'signals',                      # Signal views
]

for dataset_id in critical_datasets:
    if dataset_id not in dataset_inventory:
        print(f"\n❌ {dataset_id}: NOT FOUND")
        continue
    
    print(f"\n{'='*80}")
    print(f"DATASET: {dataset_id}")
    print(f"{'='*80}")
    
    if 'error' in dataset_inventory[dataset_id]:
        print(f"  ⚠️ Error: {dataset_inventory[dataset_id]['error']}")
        continue
    
    tables = dataset_inventory[dataset_id]['tables']
    print(f"\nTotal Tables/Views: {len(tables)}")
    
    # Show all tables
    if len(tables) <= 20:
        print(f"\nAll Tables:")
        for table in sorted(tables):
            print(f"  • {table}")
    else:
        print(f"\nFirst 20 Tables:")
        for table in sorted(tables)[:20]:
            print(f"  • {table}")
        print(f"  ... and {len(tables) - 20} more")
    
    # Check for large tables
    print(f"\nChecking row counts for key tables...")
    large_tables = []
    
    # Check all tables for row counts
    for table_name in sorted(tables)[:30]:  # Check first 30
        try:
            query = f"SELECT COUNT(*) as cnt FROM `cbi-v14.{dataset_id}.{table_name}`"
            result = client.query(query).result()
            row_count = list(result)[0].cnt
            
            if row_count > 1000:
                large_tables.append({'name': table_name, 'rows': row_count})
        except Exception as e:
            # Skip views or tables we can't query
            pass
    
    if large_tables:
        print(f"\nLarge Tables (>1K rows):")
        print("-"*80)
        for table in sorted(large_tables, key=lambda x: x['rows'], reverse=True):
            status = "✅" if table['rows'] > 10000 else "⚠️"
            print(f"  {status} {table['name']:45} | {table['rows']:12,} rows")
        
        total_rows = sum(t['rows'] for t in large_tables)
        print(f"\n  Total: {total_rows:,} rows across {len(large_tables)} large tables")
    else:
        print("  No large tables found (>1K rows)")

# Verify the "lost" yahoo_finance_comprehensive dataset
print("\n" + "="*80)
print("VERIFYING PREVIOUSLY 'LOST' DATASET")
print("="*80)

if 'yahoo_finance_comprehensive' in dataset_inventory:
    print("\n✅ yahoo_finance_comprehensive DATASET FOUND!")
    print(f"   Location: cbi-v14.yahoo_finance_comprehensive")
    print(f"   Tables: {dataset_inventory['yahoo_finance_comprehensive']['table_count']}")
    
    # Check main table
    try:
        query = """
        SELECT 
            COUNT(*) as total_rows,
            COUNT(DISTINCT symbol) as symbols,
            MIN(date) as min_date,
            MAX(date) as max_date,
            COUNTIF(date < '2020-01-01') as pre_2020_rows
        FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
        """
        result = client.query(query).result()
        row = list(result)[0]
        
        print(f"\n   Main Table (yahoo_normalized):")
        print(f"     • Total Rows: {row.total_rows:,}")
        print(f"     • Symbols: {row.symbols}")
        print(f"     • Date Range: {row.min_date} to {row.max_date}")
        print(f"     • Pre-2020 Rows: {row.pre_2020_rows:,}")
        print(f"     • Status: ✅ CONFIRMED - Dataset is present and accessible")
        
    except Exception as e:
        print(f"   ⚠️ Error querying yahoo_normalized: {str(e)[:100]}")
else:
    print("\n❌ yahoo_finance_comprehensive NOT FOUND!")

# Summary
print("\n" + "="*80)
print("INVENTORY SUMMARY")
print("="*80)

print(f"\nTotal Datasets: {len(datasets)}")
print(f"\nDataset Breakdown:")
print("-"*80)

for dataset_id, info in sorted(dataset_inventory.items()):
    if 'error' in info:
        print(f"  {dataset_id:40} | ERROR")
    else:
        print(f"  {dataset_id:40} | {info['table_count']:3} tables/views")

# Check for other large/historical datasets
print("\n" + "="*80)
print("CHECKING FOR OTHER LARGE/HISTORICAL DATASETS")
print("="*80)

historical_keywords = ['historical', 'archive', 'backup', 'bkp', 'complete', 'comprehensive']

for dataset_id, info in sorted(dataset_inventory.items()):
    if 'error' in info:
        continue
    
    # Check if dataset name suggests historical data
    is_historical = any(keyword in dataset_id.lower() for keyword in historical_keywords)
    
    if is_historical and info['table_count'] > 0:
        print(f"\n📊 {dataset_id}:")
        print(f"   Tables: {info['table_count']}")
        print(f"   Location: cbi-v14.{dataset_id}")
        
        # Show some table names
        if info['tables']:
            print(f"   Sample Tables:")
            for table in sorted(info['tables'])[:5]:
                print(f"     • {table}")
            if len(info['tables']) > 5:
                print(f"     ... and {len(info['tables']) - 5} more")

print("\n" + "="*80)
print("INVENTORY COMPLETE")
print("="*80)
