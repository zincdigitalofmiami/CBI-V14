#!/usr/bin/env python3
"""
Archive all legacy BigQuery tables to archive.legacy_YYYYMMDD__{dataset}__{table}
Preserves schema, partitioning, clustering, and adds metadata columns.
"""
import os
from google.cloud import bigquery
from datetime import datetime
from pathlib import Path
import sys

PROJECT_ID = os.getenv("PROJECT", "cbi-v14")
ARCHIVE_DATE = datetime.now().strftime("%Y%m%d")

def get_repo_root():
    """Find repository root."""
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / "QUICK_REFERENCE.txt").exists():
            return parent
    raise FileNotFoundError("Repository root not found.")

def archive_table(client, source_dataset, source_table, archive_dataset="archive"):
    """Archive a single table to archive dataset."""
    source_ref = f"{PROJECT_ID}.{source_dataset}.{source_table}"
    archive_table_name = f"legacy_{ARCHIVE_DATE}__{source_dataset}__{source_table}"
    archive_ref = f"{PROJECT_ID}.{archive_dataset}.{archive_table_name}"
    
    print(f"  Archiving {source_ref} → {archive_ref}")
    
    try:
        # Get source table metadata
        source_table_obj = client.get_table(source_ref)
        
        # Create archive table with COPY
        job_config = bigquery.CopyJobConfig()
        job = client.copy_table(source_ref, archive_ref, job_config=job_config)
        job.result()
        
        # Add metadata columns
        alter_query = f"""
        ALTER TABLE `{archive_ref}`
        ADD COLUMN IF NOT EXISTS archived_date DATE,
        ADD COLUMN IF NOT EXISTS original_location STRING,
        ADD COLUMN IF NOT EXISTS migration_version STRING
        """
        
        client.query(alter_query).result()
        
        # Update metadata
        update_query = f"""
        UPDATE `{archive_ref}`
        SET 
            archived_date = DATE('{datetime.now().date()}'),
            original_location = '{source_ref}',
            migration_version = '1.0'
        WHERE archived_date IS NULL
        """
        
        client.query(update_query).result()
        
        print(f"    ✅ Archived successfully")
        return True
        
    except Exception as e:
        print(f"    ❌ Failed: {e}")
        return False

def main():
    """Archive all legacy tables."""
    client = bigquery.Client(project=PROJECT_ID)
    
    print("="*80)
    print("PHASE 1: ARCHIVING LEGACY TABLES")
    print("="*80)
    print(f"Archive Date: {ARCHIVE_DATE}")
    print(f"Project: {PROJECT_ID}")
    print()
    
    # Ensure archive dataset exists
    archive_dataset_ref = f"{PROJECT_ID}.archive"
    try:
        client.get_dataset(archive_dataset_ref)
        print(f"✅ Archive dataset exists: {archive_dataset_ref}")
    except Exception:
        print(f"Creating archive dataset: {archive_dataset_ref}")
        dataset = bigquery.Dataset(archive_dataset_ref)
        dataset.location = "us-central1"
        dataset.description = "Legacy table snapshots and historical regimes"
        client.create_dataset(dataset, exists_ok=True)
    
    print()
    
    # Tables to archive from models_v4
    models_v4_tables = [
        "production_training_data_1w",
        "production_training_data_1m",
        "production_training_data_3m",
        "production_training_data_6m",
        "production_training_data_12m",
        "trump_rich_2023_2025",
        "crisis_2008_historical",
        "pre_crisis_2000_2007_historical",
        "recovery_2010_2016_historical",
        "trade_war_2017_2019_historical",
    ]
    
    # Archive models_v4 tables
    print("Archiving models_v4 tables:")
    print("-" * 80)
    archived_count = 0
    failed_count = 0
    
    for table_name in models_v4_tables:
        try:
            # Check if table exists
            table_ref = f"{PROJECT_ID}.models_v4.{table_name}"
            client.get_table(table_ref)
            
            if archive_table(client, "models_v4", table_name):
                archived_count += 1
            else:
                failed_count += 1
        except Exception as e:
            print(f"  ⚠️  {table_name} - Not found or error: {e}")
    
    print()
    print("="*80)
    print("ARCHIVE SUMMARY")
    print("="*80)
    print(f"✅ Successfully archived: {archived_count}")
    print(f"❌ Failed: {failed_count}")
    print()
    print(f"All archived tables are in: {PROJECT_ID}.archive.legacy_{ARCHIVE_DATE}__*")
    print()
    print("⚠️  NOTE: Raw intelligence tables (forecasting_data_warehouse.*) will be")
    print("    migrated in Phase 2, not archived (they're source data).")

if __name__ == "__main__":
    main()



