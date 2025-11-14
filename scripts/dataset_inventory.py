#!/usr/bin/env python3
"""
COMPREHENSIVE DATASET INVENTORY
Find all datasets, verify lost datasets are present, create complete inventory
"""

from google.cloud import bigquery
from datetime import datetime
import sys

client = bigquery.Client(project='cbi-v14')

print("="*80)
print("COMPREHENSIVE DATASET INVENTORY")
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

all_datasets = {}
large_datasets = []
historical_datasets = []

# Get all datasets
print("\n" + "="*80)
print("DISCOVERING ALL DATASETS")
print("="*80)

try:
    datasets = list(client.list_datasets())
    print(f"\nFound {len(datasets)} datasets in project cbi-v14:\n")
    
    for dataset in datasets:
        dataset_id = dataset.dataset_id
        print(f"  📁 {dataset_id}")
        
        # Get tables in this dataset
        try:
            tables = list(client.list_tables(dataset_id))
            all_datasets[dataset_id] = {
                'tables': len(tables),
                'dataset_ref': dataset
            }
        except Exception as e:
            print(f"     ⚠️ Error listing tables: {str(e)[:60]}")
            all_datasets[dataset_id] = {
                'tables': 0,
                'error': str(e)[:100]
            }
    
except Exception as e:
    print(f"❌ Error listing datasets: {str(e)[:100]}")
    sys.exit(1)

# Detailed analysis of each dataset
print("\n" + "="*80)
print("DETAILED DATASET ANALYSIS")
print("="*80)

for dataset_id, info in sorted(all_datasets.items()):
    print(f"\n{'='*80}")
    print(f"DATASET: {dataset_id}")
    print(f"{'='*80}")
    
    try:
        # Get table details using INFORMATION_SCHEMA
        query = f"""
        SELECT 
            table_name,
            table_type
        FROM `{dataset_id}.INFORMATION_SCHEMA.TABLES`
        ORDER BY table_name
        """
        result = client.query(query).result()
        
        tables_info = []
        
        for row in result:
            tables_info.append({
                'name': row.table_name,
                'type': row.table_type
            })
        
        # Now get row counts for each table
        print(f"\nFound {len(tables_info)} tables/views")
        
        # Sample a few tables to get row counts
        large_tables = []
        for table in tables_info[:20]:  # Check first 20 tables
            try:
                count_query = f"SELECT COUNT(*) as cnt FROM `cbi-v14.{dataset_id}.{table['name']}` LIMIT 1"
                count_result = client.query(count_query).result()
                row_count = list(count_result)[0].cnt
                if row_count > 1000:
                    large_tables.append({'name': table['name'], 'rows': row_count, 'type': table['type']})
            except:
                pass  # Skip if can't query
        
        if large_tables:
            print(f"\nLarge Tables (>1K rows):")
            print("-"*80)
            for table in sorted(large_tables, key=lambda x: x['rows'], reverse=True)[:10]:
                status = "✅" if table['rows'] > 10000 else "⚠️"
                print(f"  {status} {table['name']:40} | {table['rows']:12,} rows | {table['type']}")
        
        # Check for historical data
        historical_count = sum(1 for t in tables_info if 'historical' in t['name'].lower())
        if historical_count > 0 or len(large_tables) > 5:
            total_rows = sum(t['rows'] for t in large_tables)
            historical_datasets.append({
                'dataset': dataset_id,
                'tables': len(tables_info),
                'total_rows': total_rows,
                'historical_tables': historical_count
            })
        
        # Check for large datasets
        total_rows = sum(t['rows'] for t in large_tables)
        if total_rows > 100000:
            large_datasets.append({
                'dataset': dataset_id,
                'total_rows': total_rows,
                'tables': len(tables_info)
            })
        
        all_datasets[dataset_id]['details'] = {
            'total_rows': total_rows,
            'tables': tables_info,
            'large_tables': large_tables
        }
        
    except Exception as e:
        print(f"  ❌ Error analyzing dataset: {str(e)[:100]}")
        all_datasets[dataset_id]['error'] = str(e)[:100]

# Check for the "lost" datasets
print("\n" + "="*80)
print("VERIFYING PREVIOUSLY 'LOST' DATASETS")
print("="*80)

lost_datasets_to_check = [
    'yahoo_finance_comprehensive',
    'bkp',
    'archive_consolidation_nov6',
    'models',
    'archive',
]

for dataset_name in lost_datasets_to_check:
    if dataset_name in all_datasets:
        info = all_datasets[dataset_name]
        print(f"\n✅ FOUND: {dataset_name}")
        if 'details' in info:
            print(f"   Tables: {len(info['details']['tables'])}")
            print(f"   Total Rows: {info['details']['total_rows']:,}")
            print(f"   Size: {info['details']['total_size_mb']:.1f} MB")
            
            # Show top tables
            top_tables = sorted(info['details']['tables'], key=lambda x: x['rows'], reverse=True)[:5]
            print(f"   Top Tables:")
            for table in top_tables:
                print(f"     • {table['name']}: {table['rows']:,} rows")
        else:
            print(f"   ⚠️ Could not analyze (error: {info.get('error', 'unknown')})")
    else:
        print(f"\n❌ NOT FOUND: {dataset_name}")

# Large datasets summary
print("\n" + "="*80)
print("LARGE DATASETS (>100K ROWS)")
print("="*80)

if large_datasets:
    for ds in sorted(large_datasets, key=lambda x: x['total_rows'], reverse=True):
        print(f"\n📊 {ds['dataset']:40}")
        print(f"   Total Rows: {ds['total_rows']:,}")
        print(f"   Size: {ds['size_mb']:.1f} MB")
        print(f"   Tables: {ds['tables']}")
else:
    print("  No datasets with >100K rows found")

# Historical datasets summary
print("\n" + "="*80)
print("HISTORICAL DATASETS")
print("="*80)

if historical_datasets:
    for ds in sorted(historical_datasets, key=lambda x: x['total_rows'], reverse=True):
        print(f"\n📊 {ds['dataset']:40}")
        print(f"   Total Rows: {ds['total_rows']:,}")
        print(f"   Tables: {ds['tables']}")
        print(f"   Historical Tables: {ds['historical_tables']}")
else:
    print("  No historical datasets identified")

# Complete inventory
print("\n" + "="*80)
print("COMPLETE DATASET INVENTORY")
print("="*80)

print(f"\nTotal Datasets: {len(all_datasets)}")
print(f"Large Datasets (>100K rows): {len(large_datasets)}")
print(f"Historical Datasets: {len(historical_datasets)}")

print(f"\nAll Datasets:")
print("-"*80)
for dataset_id, info in sorted(all_datasets.items()):
    if 'details' in info:
        print(f"  {dataset_id:40} | {info['details']['total_rows']:12,} rows | {len(info['details']['tables']):3} tables")
    else:
        print(f"  {dataset_id:40} | ERROR: {info.get('error', 'unknown')}")

# Check specific critical datasets
print("\n" + "="*80)
print("CRITICAL DATASETS VERIFICATION")
print("="*80)

critical_datasets = {
    'forecasting_data_warehouse': 'Primary production data',
    'models_v4': 'Training data and models',
    'yahoo_finance_comprehensive': 'Previously lost historical data',
    'signals': 'Signal views',
    'bkp': 'Backups',
}

for dataset_id, description in critical_datasets.items():
    if dataset_id in all_datasets:
        info = all_datasets[dataset_id]
        status = "✅" if 'details' in info else "⚠️"
        print(f"\n{status} {dataset_id:40} | {description}")
        if 'details' in info:
            print(f"   Location: cbi-v14.{dataset_id}")
            print(f"   Tables: {len(info['details']['tables'])}")
            print(f"   Total Rows: {info['details']['total_rows']:,}")
            print(f"   Size: {info['details']['total_size_mb']:.1f} MB")
        else:
            print(f"   ⚠️ Could not analyze")
    else:
        print(f"\n❌ {dataset_id:40} | {description} | NOT FOUND")

print("\n" + "="*80)
print("INVENTORY COMPLETE")
print("="*80)
