#!/usr/bin/env python3
"""
Update TABLE_MAPPING_MATRIX.md with actual BigQuery table inventory
Pulls directly from BigQuery and external drive
"""

import os
import sys
from pathlib import Path
from google.cloud import bigquery
from datetime import datetime
import pandas as pd
import json

# Add repo root to path
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))

PROJECT_ID = "cbi-v14"
BQ_REGION = "us-central1"

# External drive paths to check
EXTERNAL_DRIVE_PATHS = [
    "/Volumes/Satechi Hub",
    "/Volumes/ExternalDrive",
    "/Volumes/Seagate",
    "/Volumes/Backup",
    "/media/external",
    "/mnt/external"
]

def get_bigquery_client():
    """Get BigQuery client"""
    try:
        client = bigquery.Client(project=PROJECT_ID, location=BQ_REGION)
        return client
    except Exception as e:
        print(f"❌ Failed to create BigQuery client: {e}")
        sys.exit(1)

def get_all_datasets(client):
    """Get all datasets in the project"""
    datasets = []
    for dataset in client.list_datasets():
        datasets.append(dataset.dataset_id)
    return sorted(datasets)

def get_tables_in_dataset(client, dataset_id):
    """Get all tables and views in a dataset"""
    try:
        dataset_ref = client.dataset(dataset_id)
        tables = list(client.list_tables(dataset_ref))
        
        table_info = []
        for table in tables:
            try:
                table_ref = dataset_ref.table(table.table_id)
                table_obj = client.get_table(table_ref)
                
                # Get row count and size
                row_count = table_obj.num_rows if table_obj.num_rows else 0
                size_bytes = table_obj.num_bytes if table_obj.num_bytes else 0
                
                # Get creation time
                created = table_obj.created.strftime('%Y-%m-%d') if table_obj.created else 'Unknown'
                
                # Determine type
                table_type = 'VIEW' if table_obj.table_type == 'VIEW' else 'TABLE'
                
                # Get partitioning info
                partitioning = 'None'
                if table_obj.time_partitioning:
                    partitioning = f"PARTITION BY {table_obj.time_partitioning.field or 'DATE(_PARTITIONTIME)'}"
                if table_obj.range_partitioning:
                    partitioning = f"PARTITION BY RANGE({table_obj.range_partitioning.field})"
                
                # Get clustering
                clustering = 'None'
                if table_obj.clustering_fields:
                    clustering = ', '.join(table_obj.clustering_fields)
                
                table_info.append({
                    'dataset': dataset_id,
                    'table_name': table.table_id,
                    'type': table_type,
                    'row_count': row_count,
                    'size_mb': round(size_bytes / (1024 * 1024), 2),
                    'created': created,
                    'partitioning': partitioning,
                    'clustering': clustering,
                    'description': table_obj.description or ''
                })
            except Exception as e:
                print(f"  ⚠️  Error getting info for {dataset_id}.{table.table_id}: {e}")
                table_info.append({
                    'dataset': dataset_id,
                    'table_name': table.table_id,
                    'type': 'UNKNOWN',
                    'row_count': 0,
                    'size_mb': 0,
                    'created': 'Unknown',
                    'partitioning': 'Unknown',
                    'clustering': 'Unknown',
                    'description': f'Error: {str(e)}'
                })
        
        return table_info
    except Exception as e:
        print(f"❌ Error listing tables in {dataset_id}: {e}")
        return []

def check_external_drive():
    """Check external drive for data files"""
    external_data = {
        'found': False,
        'path': None,
        'files': []
    }
    
    for drive_path in EXTERNAL_DRIVE_PATHS:
        path = Path(drive_path)
        if path.exists() and path.is_dir():
            external_data['found'] = True
            external_data['path'] = str(path)
            
            # Look for common data file patterns
            patterns = ['*.parquet', '*.csv', '*.json', '*.ndjson']
            for pattern in patterns:
                files = list(path.rglob(pattern))
                external_data['files'].extend([str(f) for f in files])  # Show ALL files
            
            break
    
    return external_data

def generate_mapping_matrix(bq_tables, external_data):
    """Generate updated table mapping matrix markdown"""
    
    # Group tables by dataset
    tables_by_dataset = {}
    for table in bq_tables:
        dataset = table['dataset']
        if dataset not in tables_by_dataset:
            tables_by_dataset[dataset] = []
        tables_by_dataset[dataset].append(table)
    
    # Sort datasets
    sorted_datasets = sorted(tables_by_dataset.keys())
    
    # Generate markdown
    markdown = f"""# CBI-V14: Table Mapping Matrix

**Last Updated**: {datetime.now().strftime('%B %d, %Y')}
**Status**: AUTO-GENERATED FROM BIGQUERY INVENTORY
**Source**: Direct BigQuery query + external drive scan

This document is automatically generated from the actual BigQuery table inventory and external drive contents.

---

## Current BigQuery Inventory

### Dataset Summary

| Dataset | Tables | Views | Total Objects | Total Rows | Total Size (MB) |
|---------|--------|-------|---------------|------------|----------------|
"""
    
    # Calculate summary stats
    for dataset in sorted_datasets:
        tables = tables_by_dataset[dataset]
        table_count = sum(1 for t in tables if t['type'] == 'TABLE')
        view_count = sum(1 for t in tables if t['type'] == 'VIEW')
        total_rows = sum(t['row_count'] for t in tables)
        total_size = sum(t['size_mb'] for t in tables)
        
        markdown += f"| `{dataset}` | {table_count} | {view_count} | {len(tables)} | {total_rows:,} | {total_size:.2f} |\n"
    
    markdown += "\n---\n\n### Detailed Table Inventory\n\n"
    
    # Generate detailed table list by dataset
    for dataset in sorted_datasets:
        tables = sorted(tables_by_dataset[dataset], key=lambda x: x['table_name'])
        
        markdown += f"#### Dataset: `{dataset}`\n\n"
        markdown += "| Table/View Name | Type | Rows | Size (MB) | Created | Partitioning | Clustering | Description |\n"
        markdown += "|-----------------|------|------|-----------|---------|---------------|------------|-------------|\n"
        
        for table in tables:
            name = table['table_name']
            type_str = table['type']
            rows = f"{table['row_count']:,}" if table['row_count'] > 0 else "0"
            size = f"{table['size_mb']:.2f}" if table['size_mb'] > 0 else "0.00"
            created = table['created']
            partitioning = table['partitioning']  # Show full partitioning info
            clustering = table['clustering']  # Show full clustering info
            desc = table['description'] or ""  # Show full description
            
            markdown += f"| `{name}` | {type_str} | {rows} | {size} | {created} | {partitioning} | {clustering} | {desc} |\n"
        
        markdown += "\n"
    
    # Add external drive section
    markdown += "---\n\n## External Drive Inventory\n\n"
    
    if external_data['found']:
        markdown += f"**External Drive Found**: `{external_data['path']}`\n\n"
        markdown += f"**Files Found**: {len(external_data['files'])} data files\n\n"
        
        if external_data['files']:
            markdown += f"### All Data Files ({len(external_data['files'])} total)\n\n"
            for file_path in sorted(external_data['files']):  # Show ALL files, sorted
                markdown += f"- `{file_path}`\n"
    else:
        markdown += "**Status**: No external drive found at expected paths.\n\n"
        markdown += "**Checked Paths**:\n"
        for path in EXTERNAL_DRIVE_PATHS:
            markdown += f"- `{path}`\n"
    
    markdown += "\n---\n\n"
    
    # Add migration mapping section (preserve existing structure)
    markdown += """## Migration Mapping

### New Dataset Architecture

| Dataset                | Purpose                                             |
| ---------------------- | --------------------------------------------------- |
| `raw_intelligence`     | Raw, unprocessed source data.                       |
| `features`             | Engineered features for modeling.                   |
| `training`             | Final, versioned training sets.                     |
| `predictions`          | Model outputs and generated signals.                |
| `monitoring`           | Performance metrics, data quality, model registry.  |
| `archive`              | Snapshots and retired legacy objects.               |
| `vegas_intelligence`   | Data for the "Vegas Intel" sales dashboard.         |

### Naming Convention

`asset_function_scope_regime_horizon`

-   **asset**: `zl` (Soybean Oil)
-   **function**: `features`, `training`, `predictions`, etc.
-   **scope**: `full` (research), `prod` (production), or model type.
-   **regime**: `crisis`, `tradewar`, `all`, etc.
-   **horizon**: `1w`, `1m`, `3m`, etc.

---

### Migration Status

**Note**: This section should be manually maintained based on migration progress.

| Legacy Dataset                  | Legacy Table/View Name                          | Type  | New Dataset            | New Table/View Name                                   | Status      | Notes                                                              |
| ------------------------------- | ----------------------------------------------- | ----- | ---------------------- | ----------------------------------------------------- | ----------- | ------------------------------------------------------------------ |
| *See detailed inventory above for current state* | | | | | | |

---

### Action Plan

1.  **Review & Refine**: The project team will review this inventory and refine the mappings.
2.  **Script Development**: A script will be created to perform the `Migrate` and `Recreate` actions.
3.  **Execution**: The migration script will be run in a controlled environment.
4.  **Validation**: Post-migration, data and views will be validated against the old structure.
5.  **Decommission**: Once validated, legacy datasets will be backed up to the `archive` and then decommissioned.

---

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**BigQuery Project**: `{PROJECT_ID}`  
**Region**: `{BQ_REGION}`
"""
    
    return markdown

def main():
    """Main execution"""
    print("=" * 80)
    print("TABLE MAPPING MATRIX UPDATER")
    print("=" * 80)
    print(f"Project: {PROJECT_ID}")
    print(f"Region: {BQ_REGION}")
    print()
    
    # Get BigQuery client
    print("📊 Connecting to BigQuery...")
    client = get_bigquery_client()
    
    # Get all datasets
    print("📋 Listing datasets...")
    datasets = get_all_datasets(client)
    print(f"   Found {len(datasets)} datasets: {', '.join(datasets)}")
    print()
    
    # Get all tables
    print("🔍 Scanning tables and views...")
    all_tables = []
    for dataset_id in datasets:
        print(f"   Scanning {dataset_id}...", end=" ")
        tables = get_tables_in_dataset(client, dataset_id)
        all_tables.extend(tables)
        print(f"Found {len(tables)} objects")
    
    print(f"\n   Total: {len(all_tables)} tables/views found")
    print()
    
    # Check external drive
    print("💾 Checking external drive...")
    external_data = check_external_drive()
    if external_data['found']:
        print(f"   ✅ Found external drive at: {external_data['path']}")
        print(f"   Found {len(external_data['files'])} data files")
    else:
        print("   ⚠️  No external drive found")
    print()
    
    # Generate markdown
    print("📝 Generating updated matrix...")
    markdown = generate_mapping_matrix(all_tables, external_data)
    
    # Write to file
    output_path = repo_root / "docs" / "plans" / "TABLE_MAPPING_MATRIX.md"
    print(f"💾 Writing to: {output_path}")
    with open(output_path, 'w') as f:
        f.write(markdown)
    
    print()
    print("=" * 80)
    print("✅ TABLE MAPPING MATRIX UPDATED SUCCESSFULLY")
    print("=" * 80)
    print(f"   Output: {output_path}")
    print(f"   Tables/Views: {len(all_tables)}")
    print(f"   Datasets: {len(datasets)}")
    print()

if __name__ == "__main__":
    main()

