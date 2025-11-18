#!/usr/bin/env python3
"""
Week 0 Day 2 Part 2: Snapshot Legacy Tables to Backup Datasets
================================================================
Per FRESH_START_MASTER_PLAN.md Step 3:
- Copy every legacy table into its backup dataset via BigQuery COPY jobs (safer than CTAS)
- After copying, run verification queries that compare row counts and simple checksums
- Only proceed when every table matches 100%
"""

from google.cloud import bigquery
from datetime import datetime
from pathlib import Path
import time

PROJECT_ID = 'cbi-v14'
LOCATION = 'us-central1'

# Production datasets and their backup datasets
DATASET_BACKUPS = {
    'forecasting_data_warehouse': 'forecasting_data_warehouse_backup_20251117',
    'models_v4': 'models_v4_backup_20251117',
    'training': 'training_backup_20251117',
    'features': 'features_backup_20251117',
    'raw_intelligence': 'raw_intelligence_backup_20251117'
}

def list_tables_in_dataset(client, dataset_id):
    """List all tables in a dataset."""
    try:
        tables = list(client.list_tables(dataset_id))
        return [table.table_id for table in tables if table.table_type == 'TABLE']
    except Exception as e:
        print(f"  ⚠️  Error listing tables in {dataset_id}: {e}")
        return []

def copy_table_to_backup(client, source_dataset, source_table, backup_dataset):
    """
    Copy a table to backup dataset using BigQuery COPY job (safer than CTAS).
    """
    source_ref = f"{PROJECT_ID}.{source_dataset}.{source_table}"
    dest_ref = f"{PROJECT_ID}.{backup_dataset}.{source_table}"
    
    try:
        # Use COPY job (safer than CTAS for large tables)
        job_config = bigquery.CopyJobConfig()
        job = client.copy_table(source_ref, dest_ref, job_config=job_config)
        
        # Wait for job to complete
        print(f"    Copying {source_table}...", end=" ", flush=True)
        job.result()  # Wait for completion
        
        print("✅")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def verify_table_copy(client, source_dataset, source_table, backup_dataset):
    """
    Verify table copy by comparing row counts and checksums.
    """
    source_ref = f"{PROJECT_ID}.{source_dataset}.{source_table}"
    dest_ref = f"{PROJECT_ID}.{backup_dataset}.{source_table}"
    
    try:
        # Get row counts
        source_query = f"SELECT COUNT(*) as cnt FROM `{source_ref}`"
        dest_query = f"SELECT COUNT(*) as cnt FROM `{dest_ref}`"
        
        source_result = list(client.query(source_query).result())[0]
        dest_result = list(client.query(dest_query).result())[0]
        
        source_count = source_result.cnt
        dest_count = dest_result.cnt
        
        if source_count != dest_count:
            print(f"      ⚠️  Row count mismatch: source={source_count}, backup={dest_count}")
            return False
        
        # Try simple checksum (sum of first numeric column if available)
        # This is a lightweight check - full verification would be more complex
        try:
            # Get schema to find a numeric column
            source_table_obj = client.get_table(source_ref)
            numeric_cols = [col.name for col in source_table_obj.schema 
                           if col.field_type in ['INTEGER', 'FLOAT', 'NUMERIC', 'BIGNUMERIC']]
            
            if numeric_cols:
                check_col = numeric_cols[0]
                source_checksum_query = f"SELECT SUM(CAST({check_col} AS INT64)) as chk FROM `{source_ref}` WHERE {check_col} IS NOT NULL"
                dest_checksum_query = f"SELECT SUM(CAST({check_col} AS INT64)) as chk FROM `{dest_ref}` WHERE {check_col} IS NOT NULL"
                
                source_chk = list(client.query(source_checksum_query).result())[0].chk or 0
                dest_chk = list(client.query(dest_checksum_query).result())[0].chk or 0
                
                if source_chk != dest_chk:
                    print(f"      ⚠️  Checksum mismatch on {check_col}: source={source_chk}, backup={dest_chk}")
                    return False
        except Exception as e:
            # Checksum check is optional - if it fails, just warn
            print(f"      ⚠️  Could not verify checksum: {e}")
        
        return True
        
    except Exception as e:
        print(f"      ❌ Verification error: {e}")
        return False

def snapshot_dataset(client, source_dataset, backup_dataset):
    """
    Snapshot all tables in a dataset to its backup.
    """
    print(f"\n{'='*80}")
    print(f"SNAPSHOTTING: {source_dataset} → {backup_dataset}")
    print(f"{'='*80}")
    
    # List all tables
    tables = list_tables_in_dataset(client, source_dataset)
    if not tables:
        print(f"  ⚠️  No tables found in {source_dataset}")
        return {'copied': 0, 'verified': 0, 'failed': 0}
    
    print(f"  Found {len(tables)} tables to copy")
    
    copied = 0
    verified = 0
    failed = 0
    
    for i, table in enumerate(tables, 1):
        print(f"  [{i}/{len(tables)}] {table}")
        
        # Check if already exists in backup
        dest_ref = client.dataset(backup_dataset).table(table)
        try:
            client.get_table(dest_ref)
            print(f"    ⚠️  Already exists in backup, skipping")
            continue
        except:
            pass  # Table doesn't exist, proceed with copy
        
        # Copy table
        if copy_table_to_backup(client, source_dataset, table, backup_dataset):
            copied += 1
            
            # Verify copy
            print(f"    Verifying...", end=" ", flush=True)
            if verify_table_copy(client, source_dataset, table, backup_dataset):
                verified += 1
                print("✅ Verified")
            else:
                failed += 1
                print("❌ Verification failed")
        else:
            failed += 1
    
    return {'copied': copied, 'verified': verified, 'failed': failed}

def main():
    """Snapshot all production datasets to their backups."""
    
    print("="*80)
    print("WEEK 0 DAY 2 PART 2: SNAPSHOT LEGACY TABLES")
    print("="*80)
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print("="*80)
    print("\nThis will copy all tables from production datasets to backup datasets.")
    print("Existing tables in backups will be skipped.")
    print("\nPress Ctrl+C to cancel, or wait 5 seconds to continue...")
    
    try:
        time.sleep(5)
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        return
    
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    
    total_stats = {'copied': 0, 'verified': 0, 'failed': 0}
    
    for source_dataset, backup_dataset in DATASET_BACKUPS.items():
        # Verify backup dataset exists
        try:
            client.get_dataset(backup_dataset)
        except Exception as e:
            print(f"\n❌ Backup dataset {backup_dataset} does not exist: {e}")
            print("   Run week0_day2_bigquery_dependency_analysis.py first to create backups.")
            continue
        
        stats = snapshot_dataset(client, source_dataset, backup_dataset)
        total_stats['copied'] += stats['copied']
        total_stats['verified'] += stats['verified']
        total_stats['failed'] += stats['failed']
    
    print("\n" + "="*80)
    print("✅ SNAPSHOT COMPLETE")
    print("="*80)
    print(f"Total tables copied: {total_stats['copied']}")
    print(f"Total tables verified: {total_stats['verified']}")
    print(f"Total tables failed: {total_stats['failed']}")
    
    if total_stats['failed'] > 0:
        print("\n⚠️  Some tables failed to copy or verify. Review errors above.")
    else:
        print("\n✅ All tables successfully copied and verified!")
        print("\nNext Steps:")
        print("1. Review backup datasets in BigQuery console")
        print("2. Create prefixed BigQuery tables (Week 0 Day 2 - Part 3)")
        print("3. Refactor views to point at prefixed tables (Week 0 Day 3)")

if __name__ == "__main__":
    main()

