#!/usr/bin/env python3
"""
Comprehensive catalog of models dataset to identify duplicates and test artifacts
"""
from google.cloud import bigquery
import pandas as pd
from datetime import datetime
import re

client = bigquery.Client(project='cbi-v14')

print("="*80)
print("COMPREHENSIVE MODELS DATASET CATALOG")
print("="*80)
print(f"Timestamp: {datetime.now().isoformat()}\n")

# Get all tables and views
all_objects = []

# Get tables
tables_query = """
SELECT 
    table_name,
    table_type,
    creation_time,
    TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), creation_time, DAY) as age_days
FROM `cbi-v14.models.INFORMATION_SCHEMA.TABLES`
ORDER BY creation_time DESC
"""

tables_df = client.query(tables_query).to_dataframe()

# Add size information for each table
sizes = []
for _, row in tables_df.iterrows():
    try:
        table_ref = client.get_table(f"cbi-v14.models.{row['table_name']}")
        sizes.append({
            'table_name': row['table_name'],
            'row_count': table_ref.num_rows if hasattr(table_ref, 'num_rows') else None,
            'size_bytes': table_ref.num_bytes if hasattr(table_ref, 'num_bytes') else None,
            'size_mb': round(table_ref.num_bytes / 1024 / 1024, 2) if hasattr(table_ref, 'num_bytes') and table_ref.num_bytes else None
        })
    except Exception as e:
        sizes.append({
            'table_name': row['table_name'],
            'row_count': None,
            'size_bytes': None,
            'size_mb': None
        })

sizes_df = pd.DataFrame(sizes)
tables_df = tables_df.merge(sizes_df, on='table_name', how='left')

print(f"Total Objects: {len(tables_df)}")
print(f"  Tables: {len(tables_df[tables_df.table_type == 'BASE TABLE'])}")
print(f"  Views: {len(tables_df[tables_df.table_type == 'VIEW'])}")
print(f"  Models: {len(tables_df[tables_df.table_type == 'MODEL'])}\n")

# Categorize objects by pattern
patterns = {
    'test': r'.*test.*|.*tmp.*|.*temp.*|.*diagnostic.*|.*simple.*',
    'versioned': r'.*_v\d+$|.*_v\d+_.*',
    'fixed_suffix': r'.*_FIXED$|.*_fixed$',
    'real_suffix': r'.*_real$|.*_REAL$',
    'precomputed': r'.*_precomputed$',
    'training': r'.*training.*',
    'vw_prefix': r'^vw_.*',
    'model': r'zl_.*|.*_model$'
}

categorized = {key: [] for key in patterns.keys()}
categorized['other'] = []

for _, row in tables_df.iterrows():
    name = row['table_name']
    categorized_flag = False
    
    for category, pattern in patterns.items():
        if re.match(pattern, name, re.IGNORECASE):
            categorized[category].append(name)
            categorized_flag = True
            break
    
    if not categorized_flag:
        categorized['other'].append(name)

# Print categorization
print("\n" + "="*80)
print("CATEGORIZATION BY PATTERN")
print("="*80)

for category, items in categorized.items():
    if items:
        print(f"\n{category.upper()} ({len(items)} objects):")
        for item in sorted(items):
            obj_info = tables_df[tables_df.table_name == item].iloc[0]
            type_str = obj_info.table_type
            print(f"  - {item:50s} {type_str:8s} {obj_info.age_days:4.0f}d old")

# Identify potential duplicates (similar names)
print("\n" + "="*80)
print("POTENTIAL DUPLICATES (Similar Names)")
print("="*80)

base_names = {}
for name in tables_df.table_name.values:
    # Strip version suffixes, _fixed, _real, etc.
    base = re.sub(r'_v\d+$|_v\d+_\w+$|_FIXED$|_fixed$|_real$|_REAL$|_final$|_FINAL$', '', name)
    if base not in base_names:
        base_names[base] = []
    base_names[base].append(name)

duplicates = {k: v for k, v in base_names.items() if len(v) > 1}

if duplicates:
    print(f"\nFound {len(duplicates)} sets of potential duplicates:\n")
    for base, variants in sorted(duplicates.items()):
        print(f"\n{base}:")
        for variant in sorted(variants):
            obj_info = tables_df[tables_df.table_name == variant].iloc[0]
            type_str = obj_info.table_type
            size_str = f"{obj_info.size_mb:.2f} MB" if pd.notna(obj_info.size_mb) else "N/A"
            rows_str = f"{obj_info.row_count:,}" if pd.notna(obj_info.row_count) else "N/A"
            print(f"  → {variant:50s} {type_str:15s} {rows_str:>10s} rows  {size_str:>12s}  {obj_info.age_days:4.0f}d")
else:
    print("\nNo obvious duplicates found.")

# Check for objects not used in views (orphaned tables)
print("\n" + "="*80)
print("DEPENDENCY ANALYSIS")
print("="*80)

# Get all view definitions
views_query = """
SELECT table_name, view_definition
FROM `cbi-v14.models.INFORMATION_SCHEMA.VIEWS`
"""
try:
    views_df = client.query(views_query).to_dataframe()
    
    # Extract all referenced tables from view definitions
    referenced_tables = set()
    for _, row in views_df.iterrows():
        view_def = str(row.view_definition)
        # Find all table references
        refs = re.findall(r'`cbi-v14\.models\.([^`]+)`', view_def)
        refs += re.findall(r'models\.([a-zA-Z0-9_]+)', view_def)
        referenced_tables.update(refs)
    
    # Find tables that are NOT referenced
    all_tables = set(tables_df[tables_df.table_type == 'BASE TABLE'].table_name.values)
    orphaned_tables = all_tables - referenced_tables
    
    print(f"\nTotal materialized tables: {len(all_tables)}")
    print(f"Referenced in views: {len(all_tables - orphaned_tables)}")
    print(f"Orphaned (not referenced): {len(orphaned_tables)}")
    
    if orphaned_tables:
        print("\nOrphaned tables:")
        for table in sorted(orphaned_tables):
            obj_info = tables_df[tables_df.table_name == table].iloc[0]
            size_str = f"{obj_info.size_mb:.2f} MB" if pd.notna(obj_info.size_mb) else "N/A"
            print(f"  - {table:50s} {size_str:>12s}  {obj_info.age_days:4.0f}d old")
            
except Exception as e:
    print(f"Error analyzing dependencies: {e}")

# Summary statistics
print("\n" + "="*80)
print("STORAGE SUMMARY")
print("="*80)

total_size_mb = tables_df.size_mb.sum()
print(f"\nTotal storage: {total_size_mb:.2f} MB")

# Top 10 largest objects
print("\nTop 10 largest objects:")
top_10 = tables_df.nlargest(10, 'size_mb')
for _, row in top_10.iterrows():
    type_str = row.table_type
    size_str = f"{row.size_mb:.2f} MB" if pd.notna(row.size_mb) else "N/A"
    print(f"  {row.table_name:50s} {type_str:15s} {size_str:>12s}")

# Export full catalog to CSV
output_file = 'logs/models_dataset_catalog.csv'
tables_df.to_csv(output_file, index=False)
print(f"\n✅ Full catalog exported to: {output_file}")

print("\n" + "="*80)
print("RECOMMENDATIONS")
print("="*80)

recommendations = []

# Check for test/diagnostic objects
test_objects = [name for name in tables_df.table_name.values 
                if re.match(r'.*test.*|.*tmp.*|.*temp.*|.*diagnostic.*|.*simple.*', name, re.IGNORECASE)]
if test_objects:
    recommendations.append({
        'priority': 'HIGH',
        'action': 'DELETE',
        'objects': test_objects,
        'reason': 'Test/diagnostic objects with no production value'
    })

# Check for duplicates with version suffixes
duplicate_versions = []
for base, variants in duplicates.items():
    if len(variants) > 1:
        # Keep the newest, suggest deleting older versions
        variants_with_age = [(v, tables_df[tables_df.table_name == v].iloc[0].age_days) for v in variants]
        variants_with_age.sort(key=lambda x: x[1])  # Sort by age
        old_versions = [v[0] for v in variants_with_age[1:]]  # All but newest
        if old_versions:
            duplicate_versions.extend(old_versions)

if duplicate_versions:
    recommendations.append({
        'priority': 'MEDIUM',
        'action': 'REVIEW & DELETE',
        'objects': duplicate_versions,
        'reason': 'Older versions - newer version exists'
    })

if recommendations:
    print("\nRecommendations for cleanup:\n")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. [{rec['priority']}] {rec['action']}")
        print(f"   Reason: {rec['reason']}")
        print(f"   Objects ({len(rec['objects'])}):")
        for obj in sorted(rec['objects'])[:5]:
            obj_info = tables_df[tables_df.table_name == obj].iloc[0]
            type_str = obj_info.table_type
            print(f"     - {obj} ({type_str})")
        if len(rec['objects']) > 5:
            print(f"     ... and {len(rec['objects']) - 5} more")
        print()
else:
    print("\n✅ No cleanup recommendations - dataset looks clean!")

print("="*80)

