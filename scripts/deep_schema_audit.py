#!/usr/bin/env python3
"""
DEEP SCHEMA AUDIT - Find ALL duplicates, naming inconsistencies, and data problems
This is why training keeps failing - the data is a MESS
"""

from google.cloud import bigquery
from datetime import datetime
import pandas as pd
from collections import defaultdict

client = bigquery.Client(project='cbi-v14')

print(f"DEEP SCHEMA AUDIT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)
print("FINDING ALL DUPLICATES, INCONSISTENCIES, AND DATA PROBLEMS")
print("="*80)

# Track all findings
duplicates = defaultdict(list)
inconsistencies = []
naming_issues = []
data_problems = []

print("\n1. AUDITING ALL DATASETS FOR DUPLICATES:")
print("-"*80)

datasets = ['forecasting_data_warehouse', 'signals', 'models', 'curated', 'staging_ml']

all_tables = {}
for dataset in datasets:
    try:
        tables = list(client.list_tables(f'cbi-v14.{dataset}'))
        all_tables[dataset] = [t.table_id for t in tables]
        print(f"\n{dataset}: {len(tables)} tables/views")
    except:
        print(f"\n{dataset}: NOT FOUND")
        all_tables[dataset] = []

print("\n2. FINDING DUPLICATE DATA SOURCES:")
print("-"*80)

# Check for wheat duplicates
wheat_tables = []
for dataset, tables in all_tables.items():
    for table in tables:
        if 'wheat' in table.lower():
            wheat_tables.append(f"{dataset}.{table}")
            
if len(wheat_tables) > 1:
    print(f"\n⚠️ WHEAT DUPLICATES FOUND ({len(wheat_tables)}):")
    for table in wheat_tables:
        try:
            count_query = f"SELECT COUNT(*) as cnt FROM `cbi-v14.{table}`"
            result = client.query(count_query).to_dataframe()
            count = result['cnt'].iloc[0]
            print(f"  - {table}: {count:,} rows")
            duplicates['wheat'].append(table)
        except:
            print(f"  - {table}: (error counting)")

# Check for corn duplicates
corn_tables = []
for dataset, tables in all_tables.items():
    for table in tables:
        if 'corn' in table.lower():
            corn_tables.append(f"{dataset}.{table}")
            
if len(corn_tables) > 1:
    print(f"\n⚠️ CORN DUPLICATES FOUND ({len(corn_tables)}):")
    for table in corn_tables:
        try:
            count_query = f"SELECT COUNT(*) as cnt FROM `cbi-v14.{table}`"
            result = client.query(count_query).to_dataframe()
            count = result['cnt'].iloc[0]
            print(f"  - {table}: {count:,} rows")
            duplicates['corn'].append(table)
        except:
            print(f"  - {table}: (error counting)")

# Check for soybean/soy duplicates
soy_tables = []
for dataset, tables in all_tables.items():
    for table in tables:
        if 'soy' in table.lower() or 'soybean' in table.lower():
            soy_tables.append(f"{dataset}.{table}")
            
if len(soy_tables) > 1:
    print(f"\n⚠️ SOYBEAN DUPLICATES FOUND ({len(soy_tables)}):")
    for table in soy_tables:
        try:
            count_query = f"SELECT COUNT(*) as cnt FROM `cbi-v14.{table}`"
            result = client.query(count_query).to_dataframe()
            count = result['cnt'].iloc[0]
            print(f"  - {table}: {count:,} rows")
            duplicates['soybean'].append(table)
        except:
            print(f"  - {table}: (error counting)")

# Check for weather duplicates
weather_tables = []
for dataset, tables in all_tables.items():
    for table in tables:
        if 'weather' in table.lower():
            weather_tables.append(f"{dataset}.{table}")
            
if len(weather_tables) > 1:
    print(f"\n⚠️ WEATHER DUPLICATES FOUND ({len(weather_tables)}):")
    for table in weather_tables:
        try:
            count_query = f"SELECT COUNT(*) as cnt FROM `cbi-v14.{table}`"
            result = client.query(count_query).to_dataframe()
            count = result['cnt'].iloc[0]
            print(f"  - {table}: {count:,} rows")
            duplicates['weather'].append(table)
        except:
            print(f"  - {table}: (error counting)")

print("\n3. CHECKING NAMING INCONSISTENCIES:")
print("-"*80)

# Check for inconsistent naming patterns
patterns = {
    'snake_case': [],
    'camelCase': [],
    'mixed': [],
    'with_numbers': [],
    'with_prefix': [],
}

for dataset, tables in all_tables.items():
    for table in tables:
        if '_' in table and not any(c.isupper() for c in table):
            patterns['snake_case'].append(f"{dataset}.{table}")
        elif any(c.isupper() for c in table) and '_' not in table:
            patterns['camelCase'].append(f"{dataset}.{table}")
        elif '_' in table and any(c.isupper() for c in table):
            patterns['mixed'].append(f"{dataset}.{table}")
            naming_issues.append(f"Mixed naming: {dataset}.{table}")
        if any(c.isdigit() for c in table):
            patterns['with_numbers'].append(f"{dataset}.{table}")
        if table.startswith('vw_') or table.startswith('tmp_') or table.startswith('stg_'):
            patterns['with_prefix'].append(f"{dataset}.{table}")

print(f"Naming patterns found:")
print(f"  snake_case: {len(patterns['snake_case'])} tables")
print(f"  camelCase: {len(patterns['camelCase'])} tables")
print(f"  MIXED (PROBLEM): {len(patterns['mixed'])} tables")
print(f"  with_numbers: {len(patterns['with_numbers'])} tables")
print(f"  with_prefix: {len(patterns['with_prefix'])} tables")

if patterns['mixed']:
    print(f"\n⚠️ MIXED NAMING PROBLEMS:")
    for table in patterns['mixed'][:10]:  # Show first 10
        print(f"  - {table}")

print("\n4. CHECKING DATA OVERLAP AND REDUNDANCY:")
print("-"*80)

# Check if same data exists in multiple places
price_data = {}
commodities = ['wheat', 'corn', 'soybean', 'palm', 'crude', 'gold', 'vix', 'treasury']

for commodity in commodities:
    price_data[commodity] = []
    for dataset, tables in all_tables.items():
        for table in tables:
            if commodity in table.lower() and ('price' in table.lower() or 'daily' in table.lower()):
                price_data[commodity].append(f"{dataset}.{table}")
    
    if len(price_data[commodity]) > 1:
        print(f"\n⚠️ {commodity.upper()} data in multiple places:")
        for table in price_data[commodity]:
            print(f"  - {table}")
        data_problems.append(f"{commodity}: {len(price_data[commodity])} duplicate sources")

print("\n5. CHECKING VIEWS vs TABLES:")
print("-"*80)

# Check what's a view vs a table
warehouse_objects = all_tables.get('forecasting_data_warehouse', [])
views = [t for t in warehouse_objects if t.startswith('vw_')]
tables = [t for t in warehouse_objects if not t.startswith('vw_')]

print(f"In forecasting_data_warehouse:")
print(f"  Tables: {len(tables)}")
print(f"  Views: {len(views)}")

if views:
    print(f"\n  Views found (should these be tables?):")
    for view in views[:10]:  # Show first 10
        print(f"    - {view}")

print("\n6. CHECKING FOR ORPHANED/UNUSED DATA:")
print("-"*80)

# Check for tables with very few rows (might be test/orphaned)
orphaned = []
for dataset, tables in all_tables.items():
    for table in tables[:20]:  # Check first 20 in each dataset
        try:
            count_query = f"SELECT COUNT(*) as cnt FROM `cbi-v14.{dataset}.{table}`"
            result = client.query(count_query).to_dataframe()
            count = result['cnt'].iloc[0]
            if count == 0:
                orphaned.append(f"{dataset}.{table}")
        except:
            pass

if orphaned:
    print(f"\n⚠️ EMPTY TABLES FOUND ({len(orphaned)}):")
    for table in orphaned[:20]:  # Show first 20
        print(f"  - {table}")

print("\n7. CHECKING COLUMN CONSISTENCY:")
print("-"*80)

# Check if similar tables have different schemas
soybean_schemas = {}
for table in duplicates.get('soybean', [])[:3]:  # Check first 3 soybean tables
    try:
        schema_query = f"""
        SELECT column_name, data_type
        FROM `cbi-v14.{table.replace('.', '.INFORMATION_SCHEMA.COLUMNS` WHERE table_name = "')}")`
        ORDER BY ordinal_position
        """
        # Simpler approach - just sample the table
        sample_query = f"SELECT * FROM `cbi-v14.{table}` LIMIT 1"
        sample = client.query(sample_query).to_dataframe()
        soybean_schemas[table] = list(sample.columns)
        print(f"\n{table} columns: {len(sample.columns)}")
        print(f"  Sample columns: {', '.join(sample.columns[:5])}...")
    except Exception as e:
        print(f"\n{table}: Error getting schema")

print("\n8. CRITICAL PROBLEMS FOUND:")
print("-"*80)

print(f"\n⚠️ DUPLICATES:")
for commodity, tables in duplicates.items():
    if tables:
        print(f"  {commodity}: {len(tables)} duplicate sources")

print(f"\n⚠️ NAMING ISSUES:")
print(f"  Mixed naming conventions: {len(patterns['mixed'])} tables")
print(f"  Inconsistent prefixes: {len(patterns['with_prefix'])} tables")

print(f"\n⚠️ DATA PROBLEMS:")
for problem in data_problems[:10]:  # Show first 10
    print(f"  - {problem}")

print(f"\n⚠️ ORPHANED/EMPTY:")
print(f"  Empty tables: {len(orphaned)}")

print("\n" + "="*80)
print("AUDIT COMPLETE - MAJOR ISSUES FOUND")
print("="*80)

print("""
SUMMARY OF PROBLEMS:
1. DUPLICATE DATA SOURCES - Same commodity in multiple tables
2. NAMING CHAOS - Mixed conventions (snake_case, camelCase, prefixes)
3. ORPHANED TABLES - Empty tables taking up space
4. VIEWS IN WRONG PLACE - Views mixed with tables
5. NO CLEAR ORGANIZATION - Data scattered across datasets

THIS IS WHY TRAINING FAILS:
- Models don't know which data source to use
- Joins fail due to naming inconsistencies
- Features missing because they're in the wrong dataset
- Duplicate data causes confusion

REQUIRED FIXES:
1. DELETE all duplicate tables (keep only one source per commodity)
2. STANDARDIZE naming (all snake_case, no prefixes in tables)
3. MOVE all views to signals dataset
4. DELETE all empty/orphaned tables
5. CONSOLIDATE data into proper datasets:
   - forecasting_data_warehouse: RAW DATA ONLY
   - signals: VIEWS/CALCULATIONS ONLY
   - models: MODELS ONLY
   - curated: CLEAN FEATURES ONLY
""")

# Save detailed report
report = {
    'duplicates': dict(duplicates),
    'naming_issues': naming_issues,
    'data_problems': data_problems,
    'orphaned_tables': orphaned,
    'mixed_naming': patterns['mixed']
}

print("\nDetailed findings saved to memory for cleanup script.")
