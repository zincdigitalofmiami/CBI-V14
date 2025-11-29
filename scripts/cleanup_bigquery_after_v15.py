#!/usr/bin/env python3
"""
Cleanup BigQuery after V15 export
Deletes all datasets and tables to avoid storage costs
WARNING: This will DELETE ALL DATA in BigQuery!
"""
import sys
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from datetime import datetime
import json

PROJECT_ID = "cbi-v14"

# Datasets to KEEP (if any - set to empty list to delete everything)
KEEP_DATASETS = []  # Empty = delete everything

# Datasets to DELETE (all others)
DELETE_DATASETS = [
    'api',
    'features',
    'market_data',
    'monitoring',
    'ops',
    'predictions',
    'raw_intelligence',
    'training',
    'utils',
    'views',
    'z_archive_20251119',
]


def confirm_deletion():
    """Require explicit confirmation"""
    print("="*80)
    print("⚠️  WARNING: BIGQUERY DELETION ⚠️")
    print("="*80)
    print()
    print("This script will DELETE ALL DATASETS AND TABLES in BigQuery!")
    print(f"Project: {PROJECT_ID}")
    print()
    print("Datasets to delete:")
    for ds in DELETE_DATASETS:
        print(f"  - {ds}")
    print()
    print("This action CANNOT be undone!")
    print()
    
    response = input("Type 'DELETE ALL' to confirm: ")
    if response != "DELETE ALL":
        print("❌ Deletion cancelled")
        return False
    
    return True


def get_dataset_inventory(client):
    """Get full inventory of datasets and tables"""
    print("\n" + "="*80)
    print("BIGQUERY INVENTORY")
    print("="*80)
    
    datasets = list(client.list_datasets())
    inventory = {}
    
    for ds in datasets:
        dataset_id = ds.dataset_id
        if dataset_id in KEEP_DATASETS:
            print(f"⏭️  SKIPPING (keep): {dataset_id}")
            continue
        
        try:
            tables = list(client.list_tables(dataset_id))
            table_count = 0
            view_count = 0
            total_rows = 0
            
            for t in tables:
                tbl = client.get_table(t)
                if tbl.table_type == 'TABLE':
                    table_count += 1
                    total_rows += tbl.num_rows or 0
                else:
                    view_count += 1
            
            inventory[dataset_id] = {
                'tables': table_count,
                'views': view_count,
                'total_rows': total_rows
            }
            
            print(f"📊 {dataset_id}: {table_count} tables, {view_count} views, {total_rows:,} rows")
            
        except Exception as e:
            print(f"❌ Error reading {dataset_id}: {e}")
    
    return inventory


def delete_dataset(client, dataset_id):
    """Delete a dataset and all its contents"""
    try:
        dataset_ref = client.dataset(dataset_id)
        client.delete_dataset(dataset_ref, delete_contents=True, not_found_ok=True)
        print(f"  ✅ Deleted dataset: {dataset_id}")
        return True
    except Exception as e:
        print(f"  ❌ Failed to delete {dataset_id}: {e}")
        return False


def main():
    print("="*80)
    print("BIGQUERY CLEANUP AFTER V15 EXPORT")
    print("="*80)
    print(f"Date: {datetime.now().isoformat()}")
    print()
    
    # Confirm deletion
    if not confirm_deletion():
        sys.exit(0)
    
    # Connect to BigQuery
    client = bigquery.Client(project=PROJECT_ID)
    
    # Get inventory
    inventory = get_dataset_inventory(client)
    
    if not inventory:
        print("\n✅ No datasets to delete")
        sys.exit(0)
    
    # Delete datasets
    print("\n" + "="*80)
    print("DELETING DATASETS")
    print("="*80)
    
    deleted_count = 0
    failed_count = 0
    
    for dataset_id in DELETE_DATASETS:
        if dataset_id in inventory:
            print(f"\nDeleting {dataset_id}...")
            if delete_dataset(client, dataset_id):
                deleted_count += 1
            else:
                failed_count += 1
    
    # Summary
    print("\n" + "="*80)
    print("CLEANUP SUMMARY")
    print("="*80)
    print(f"✅ Deleted: {deleted_count} datasets")
    if failed_count > 0:
        print(f"❌ Failed: {failed_count} datasets")
    
    # Save log
    log = {
        'date': datetime.now().isoformat(),
        'project': PROJECT_ID,
        'deleted_datasets': deleted_count,
        'failed_datasets': failed_count,
        'inventory': inventory
    }
    
    log_path = f"scripts/bq_cleanup_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(log_path, 'w') as f:
        json.dump(log, f, indent=2)
    
    print(f"\n📝 Log saved: {log_path}")
    print("\n✅ BigQuery cleanup complete!")


if __name__ == "__main__":
    main()

