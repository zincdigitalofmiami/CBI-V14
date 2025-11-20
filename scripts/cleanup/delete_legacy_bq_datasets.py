#!/usr/bin/env python3
"""
Identify and delete legacy BigQuery datasets to reduce costs
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from google.cloud import bigquery
from datetime import datetime

PROJECT_ID = 'cbi-v14'
LOCATION = 'us-central1'

# Current/production datasets (KEEP THESE)
PRODUCTION_DATASETS = [
    'market_data',
    'raw_intelligence',
    'signals',
    'features',
    'training',
    'regimes',
    'drivers',
    'neural',
    'predictions',
    'monitoring',
    'dim',
    'ops',
    'api',
]

# Legacy patterns to identify
LEGACY_PATTERNS = [
    '_backup_',
    '_tmp',
    'archive',
    'bkp',
    'deprecated',
    'old',
    'models_v4',  # Superseded by training dataset
    'models_v5',
    'forecasting_data_warehouse',  # Superseded by market_data + raw_intelligence
    'curated',  # Superseded by api views
    'staging',  # Superseded by ops
    'dashboard',  # Superseded by api views
    'export_evaluated',  # AutoML exports (old)
    'models_organized',  # Old organization
    'models_trained',
    'models_failed',
    'vegas_intelligence',  # Superseded by raw_intelligence
    'weather',  # Superseded by raw_intelligence
    'yahoo_finance_comprehensive',  # Superseded by market_data
    'performance',  # Superseded by monitoring
    'predictions_uc1',  # Old predictions
    'raw',  # Superseded by raw_intelligence
    'staging_ml',
]


def is_legacy_dataset(dataset_id):
    """Check if dataset is legacy"""
    if dataset_id in PRODUCTION_DATASETS:
        return False
    
    for pattern in LEGACY_PATTERNS:
        if pattern in dataset_id:
            return True
    
    return False


def list_legacy_datasets(client, dry_run=True):
    """List all legacy datasets and their sizes"""
    print("=" * 80)
    print("LEGACY BIGQUERY DATASETS ANALYSIS")
    print(f"Project: {PROJECT_ID}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Get all datasets
    datasets = list(client.list_datasets())
    
    legacy_datasets = []
    production_datasets = []
    
    for dataset in datasets:
        dataset_id = dataset.dataset_id
        
        if is_legacy_dataset(dataset_id):
            legacy_datasets.append(dataset_id)
        else:
            production_datasets.append(dataset_id)
    
    print(f"\nTotal Datasets: {len(datasets)}")
    print(f"Production Datasets: {len(production_datasets)}")
    print(f"Legacy Datasets: {len(legacy_datasets)}")
    
    # Get storage for legacy datasets
    print("\n" + "=" * 80)
    print("LEGACY DATASETS TO DELETE")
    print("=" * 80)
    
    total_legacy_storage = 0
    legacy_details = []
    
    for dataset_id in sorted(legacy_datasets):
        try:
            # Query storage for this dataset
            storage_query = f"""
            SELECT
              SUM(total_logical_bytes) / POW(1024, 3) as logical_gb,
              COUNT(*) as table_count
            FROM `{PROJECT_ID}.{dataset_id}.__TABLES__`
            """
            
            job = client.query(storage_query, location=LOCATION)
            results = list(job.result())
            
            if results:
                row = results[0]
                logical_gb = row.logical_gb or 0
                table_count = row.table_count or 0
                
                total_legacy_storage += logical_gb
                legacy_details.append({
                    'dataset': dataset_id,
                    'storage_gb': logical_gb,
                    'tables': table_count
                })
        except Exception as e:
            print(f"Warning: Could not query {dataset_id}: {e}")
            legacy_details.append({
                'dataset': dataset_id,
                'storage_gb': 0,
                'tables': 0
            })
    
    # Print details
    print(f"\n{'Dataset':<50} {'Storage (GB)':<15} {'Tables':<10}")
    print("-" * 80)
    
    for detail in legacy_details:
        print(f"{detail['dataset']:<50} {detail['storage_gb']:<15.4f} {detail['tables']:<10}")
    
    print("-" * 80)
    print(f"{'TOTAL LEGACY':<50} {total_legacy_storage:<15.4f} {sum(d['tables'] for d in legacy_details):<10}")
    
    # Calculate savings
    storage_cost_savings = total_legacy_storage * 0.020  # Active storage rate
    
    print(f"\nStorage Savings: {total_legacy_storage:.4f} GB × $0.020 = ${storage_cost_savings:.4f}/month")
    
    # Print production datasets
    print("\n" + "=" * 80)
    print("PRODUCTION DATASETS (KEEP)")
    print("=" * 80)
    
    print(f"\n{', '.join(sorted(production_datasets))}")
    
    if dry_run:
        print("\n" + "=" * 80)
        print("DRY RUN MODE - NO DATASETS DELETED")
        print("=" * 80)
        print("\nTo delete legacy datasets, run:")
        print(f"  python3 {Path(__file__).name} --delete")
    
    return legacy_datasets, total_legacy_storage


def delete_legacy_datasets(client, legacy_datasets):
    """Delete legacy datasets"""
    print("\n" + "=" * 80)
    print("DELETING LEGACY DATASETS")
    print("=" * 80)
    
    deleted_count = 0
    failed_count = 0
    
    for dataset_id in legacy_datasets:
        try:
            print(f"\nDeleting: {dataset_id}...")
            client.delete_dataset(
                f"{PROJECT_ID}.{dataset_id}",
                delete_contents=True,  # Delete all tables in dataset
                not_found_ok=True
            )
            print(f"  ✅ Deleted: {dataset_id}")
            deleted_count += 1
        except Exception as e:
            print(f"  ❌ Failed to delete {dataset_id}: {e}")
            failed_count += 1
    
    print("\n" + "=" * 80)
    print("DELETION SUMMARY")
    print("=" * 80)
    print(f"Deleted: {deleted_count}")
    print(f"Failed: {failed_count}")
    print(f"Total: {len(legacy_datasets)}")


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Delete legacy BigQuery datasets')
    parser.add_argument('--delete', action='store_true', help='Actually delete datasets (dry-run by default)')
    parser.add_argument('--yes', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()
    
    # Initialize client
    try:
        client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    except Exception as e:
        print(f"Error initializing BigQuery client: {e}")
        return
    
    # List legacy datasets
    legacy_datasets, total_storage = list_legacy_datasets(client, dry_run=not args.delete)
    
    if args.delete:
        # Confirm deletion
        if not args.yes:
            print("\n" + "=" * 80)
            print("⚠️  WARNING: THIS WILL DELETE DATA PERMANENTLY")
            print("=" * 80)
            print(f"\nAbout to delete {len(legacy_datasets)} datasets ({total_storage:.4f} GB)")
            response = input("\nType 'DELETE' to confirm: ")
            
            if response != 'DELETE':
                print("Aborted.")
                return
        
        # Delete datasets
        delete_legacy_datasets(client, legacy_datasets)
        
        # Re-run analysis
        print("\n" + "=" * 80)
        print("POST-DELETION ANALYSIS")
        print("=" * 80)
        list_legacy_datasets(client, dry_run=True)


if __name__ == "__main__":
    main()





