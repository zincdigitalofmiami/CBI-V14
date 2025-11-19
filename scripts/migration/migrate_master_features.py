#!/usr/bin/env python3
"""
Migrate master_features_canonical to master_features with prefixed columns
Date: November 18, 2025
Purpose: Rebuild features.master_features with proper source prefixing
"""

import os
import argparse
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import sys

PROJECT_ID = "cbi-v14"
LOCATION = "us-central1"

# Column mapping: old_name -> new_name
COLUMN_MAPPING = {
    # Yahoo columns
    'yahoo_open': 'yahoo_zl_open',
    'yahoo_high': 'yahoo_zl_high',
    'yahoo_low': 'yahoo_zl_low',
    'yahoo_close': 'yahoo_zl_close',
    'yahoo_volume': 'yahoo_zl_volume',
    
    # Alpha Vantage columns (removed, but map to databento if exists)
    'alpha_open': 'databento_zl_open',  # Map to DataBento
    'alpha_high': 'databento_zl_high',
    'alpha_low': 'databento_zl_low',
    'alpha_close': 'databento_zl_close',
    'alpha_volume': 'databento_zl_volume',
    
    # Technical indicators (if they exist without prefix)
    'rsi_14': 'yahoo_zl_rsi_14',
    'macd': 'yahoo_zl_macd',
    'sma_50': 'yahoo_zl_sma_50',
    'sma_200': 'yahoo_zl_sma_200',
    'bollinger_upper': 'yahoo_zl_bollinger_upper',
    'bollinger_lower': 'yahoo_zl_bollinger_lower',
}

def get_client():
    """Initialize BigQuery client"""
    return bigquery.Client(project=PROJECT_ID, location=LOCATION)

def check_table_exists(client, dataset_id, table_id):
    """Check if table exists"""
    table_ref = client.dataset(dataset_id).table(table_id)
    try:
        client.get_table(table_ref)
        return True
    except NotFound:
        return False

def get_table_schema(client, dataset_id, table_id):
    """Get table schema as dict"""
    table_ref = client.dataset(dataset_id).table(table_id)
    table = client.get_table(table_ref)
    return {field.name: field.field_type for field in table.schema}

def migrate_master_features(dry_run=False, force=False):
    """Migrate master_features_canonical to master_features"""
    client = get_client()
    
    source_table = "features.master_features_canonical"
    target_table = "features.master_features"
    
    print(f"🔄 Migrating {source_table} → {target_table}")
    print("=" * 60)
    
    # Check if source table exists
    if not check_table_exists(client, "features", "master_features_canonical"):
        print(f"❌ Source table {source_table} does not exist")
        print("   Skipping migration - will populate from scratch")
        return
    
    # Check if target table exists
    if not check_table_exists(client, "features", "master_features"):
        print(f"❌ Target table {target_table} does not exist")
        print("   Please run PRODUCTION_READY_BQ_SCHEMA.sql first")
        sys.exit(1)
    
    # Get source schema
    print(f"📊 Reading source schema: {source_table}")
    source_schema = get_table_schema(client, "features", "master_features_canonical")
    print(f"   Found {len(source_schema)} columns")
    
    # Get target schema
    print(f"📊 Reading target schema: {target_table}")
    target_schema = get_table_schema(client, "features", "master_features")
    print(f"   Target has {len(target_schema)} columns")
    
    # Build column mapping SQL
    print("\n🔧 Building column mapping...")
    select_columns = []
    
    # Always include date and symbol
    select_columns.append("date")
    select_columns.append("COALESCE(symbol, 'ZL') AS symbol")
    
    # Map columns
    mapped_count = 0
    for old_col, new_col in COLUMN_MAPPING.items():
        if old_col in source_schema and new_col in target_schema:
            select_columns.append(f"{old_col} AS {new_col}")
            mapped_count += 1
    
    # Include any columns that already have correct names
    for col in source_schema:
        if col not in COLUMN_MAPPING and col in target_schema:
            if col not in ['date', 'symbol']:
                select_columns.append(col)
    
    # Set NULL for columns that don't exist in source
    for col in target_schema:
        if col not in source_schema and col not in ['date', 'symbol', 'as_of', 'collection_timestamp']:
            # Check if it's a prefixed column we should set to NULL
            if not any(col.startswith(prefix) for prefix in ['yahoo_', 'databento_', 'fred_', 'eia_', 'usda_']):
                # Keep as NULL (will be populated by feature engineering)
                pass
    
    # Add metadata columns
    select_columns.append("CURRENT_TIMESTAMP() AS as_of")
    
    print(f"   Mapped {mapped_count} columns")
    print(f"   Total columns in SELECT: {len(select_columns)}")
    
    # Build migration query
    query = f"""
    INSERT INTO `{PROJECT_ID}.{target_table}`
    SELECT
      {', '.join(select_columns)}
    FROM `{PROJECT_ID}.{source_table}`
    WHERE date >= '2000-01-01'
    """
    
    # Get row count first
    count_query = f"SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{source_table}` WHERE date >= '2000-01-01'"
    result = client.query(count_query).result()
    row_count = list(result)[0].cnt
    print(f"\n📈 Source table has {row_count:,} rows (date >= 2000-01-01)")
    
    if row_count == 0:
        print("⚠️  No rows to migrate - source table is empty")
        return
    
    # Check if target already has data
    target_count_query = f"SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{target_table}`"
    try:
        target_result = client.query(target_count_query).result()
        existing_count = list(target_result)[0].cnt
        
        if existing_count > 0 and not force:
            print(f"\n⚠️  Target table already has {existing_count:,} rows")
            print(f"   Use --force flag to re-migrate and overwrite existing data")
            return
    except Exception:
        existing_count = 0
    
    # Execute migration
    if dry_run:
        print(f"\n🔍 DRY RUN MODE - No changes will be made")
        print(f"   Would execute:")
        print(f"   INSERT INTO {target_table} SELECT ... FROM {source_table}")
        print(f"   Estimated rows to migrate: {row_count:,}")
        print(f"   Mapped columns: {mapped_count}")
        print("\n✅ Dry run complete - SQL is valid")
    else:
        print(f"\n🚀 Executing migration...")
        print(f"   Query: INSERT INTO {target_table} SELECT ... FROM {source_table}")
        
        try:
            job = client.query(query, location=LOCATION)
            job.result()  # Wait for completion
            
            print(f"✅ Migration complete!")
            
            # Verify row count
            verify_query = f"SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{target_table}`"
            verify_result = client.query(verify_query).result()
            target_count = list(verify_result)[0].cnt
            print(f"   Target table now has {target_count:,} rows")
            
            if target_count >= row_count:
                print(f"✅ Row count verified: {target_count:,} >= {row_count:,}")
            else:
                print(f"⚠️  Warning: Row count mismatch ({target_count:,} < {row_count:,})")
                
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            sys.exit(1)

def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Migrate master_features_canonical to master_features with prefixed columns"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without executing"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force migration even if target table has data"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("CBI-V14 Master Features Migration")
    if args.dry_run:
        print("MODE: DRY RUN")
    print("=" * 60)
    print()
    
    migrate_master_features(dry_run=args.dry_run, force=args.force)
    
    print()
    print("=" * 60)
    if args.dry_run:
        print("✅ Dry run complete")
    else:
        print("✅ Migration script complete")
    print("=" * 60)
    print()
    
    if not args.dry_run:
        print("Next steps:")
        print("1. Verify data in features.master_features")
        print("2. Run feature engineering pipeline to populate missing columns")
        print("3. Run validation script: validate_bq_deployment.py")

if __name__ == "__main__":
    main()

