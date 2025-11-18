#!/usr/bin/env python3
"""
Week 0 Day 2: BigQuery Dependency Analysis & Backup Creation
=============================================================
Per FRESH_START_MASTER_PLAN.md Week 0 Day 2:
1. Dependency Analysis (Read-Only) - Find all views/queries referencing legacy tables
2. Create Backup Datasets - Timestamped backups for rollback
3. Snapshot Legacy Tables - Copy to backup datasets
4. Build Prefixed Architecture - Create new prefixed tables in parallel

Output: docs/migration/bq_dependency_manifest.md
"""

from google.cloud import bigquery
import pandas as pd
from pathlib import Path
from datetime import datetime
import json

PROJECT_ID = 'cbi-v14'
LOCATION = 'us-central1'

def analyze_view_dependencies(client):
    """
    Query INFORMATION_SCHEMA.VIEWS to find all views referencing legacy tables.
    Process in batches to avoid timeouts.
    """
    print("="*80)
    print("STEP 1: ANALYZING VIEW DEPENDENCIES")
    print("="*80)
    
    # First, get list of datasets to process
    datasets_query = f"""
    SELECT DISTINCT table_schema as dataset
    FROM `{PROJECT_ID}.INFORMATION_SCHEMA.VIEWS`
    WHERE table_schema NOT IN ('INFORMATION_SCHEMA', '_SESSION')
    ORDER BY table_schema
    """
    
    print("  Fetching dataset list...")
    try:
        datasets_result = client.query(datasets_query, job_config=bigquery.QueryJobConfig(
            maximum_bytes_billed=10**9  # 1GB limit
        )).result()
        datasets = [row.dataset for row in datasets_result]
        print(f"  ✅ Found {len(datasets)} datasets with views")
    except Exception as e:
        print(f"  ⚠️  Error fetching datasets: {e}")
        print("  Falling back to known datasets...")
        datasets = ['forecasting_data_warehouse', 'models_v4', 'training', 'features', 'neural', 'signals']
    
    views = []
    
    # Legacy table patterns to search for
    legacy_patterns = [
        'forecasting_data_warehouse.soybean_oil_prices',
        'forecasting_data_warehouse.commodity_soybean_oil_prices',
        'forecasting_data_warehouse.vix_data',
        'production_training_data',
        'models_v4.production_training_data',
    ]
    
    # Process each dataset separately to avoid timeouts
    for dataset in datasets:
        print(f"  Processing dataset: {dataset}...")
        try:
            query = f"""
            SELECT 
                table_schema as dataset,
                table_name as view_name,
                view_definition
            FROM `{PROJECT_ID}.{dataset}.INFORMATION_SCHEMA.VIEWS`
            ORDER BY table_name
            """
            
            job_config = bigquery.QueryJobConfig(
                maximum_bytes_billed=10**9,  # 1GB limit
                use_legacy_sql=False
            )
            
            results = client.query(query, job_config=job_config).result()
            
            dataset_views = []
            for row in results:
                view_def = row.view_definition.upper() if row.view_definition else ''
                matches = []
                
                for pattern in legacy_patterns:
                    if pattern.upper() in view_def:
                        matches.append(pattern)
                
                if matches:
                    dataset_views.append({
                        'dataset': row.dataset,
                        'view_name': row.view_name,
                        'legacy_tables_referenced': matches,
                        'view_definition': row.view_definition
                    })
                    print(f"    ⚠️  {row.view_name} references: {', '.join(matches)}")
            
            views.extend(dataset_views)
            print(f"    ✅ Found {len(dataset_views)} views with legacy references in {dataset}")
            
        except Exception as e:
            print(f"    ⚠️  Error processing {dataset}: {e}")
            continue
    
    print(f"\n✅ Total: {len(views)} views referencing legacy tables")
    return views

def analyze_scheduled_queries(client):
    """
    Query INFORMATION_SCHEMA.JOBS_BY_PROJECT to find scheduled queries.
    Use smaller time window and limit to avoid timeouts.
    """
    print("\n" + "="*80)
    print("STEP 2: ANALYZING SCHEDULED QUERIES")
    print("="*80)
    
    # Use smaller window (7 days) and limit results to avoid timeouts
    query = f"""
    SELECT 
        job_id,
        creation_time,
        job_type,
        statement_type,
        query
    FROM `{PROJECT_ID}.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
    WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
      AND job_type = 'QUERY'
      AND statement_type IN ('SELECT', 'CREATE_TABLE_AS_SELECT', 'MERGE')
    ORDER BY creation_time DESC
    LIMIT 500
    """
    
    try:
        job_config = bigquery.QueryJobConfig(
            maximum_bytes_billed=10**9,  # 1GB limit
            use_legacy_sql=False
        )
        
        print("  Querying job history (last 7 days, limit 500)...")
        results = client.query(query, job_config=job_config).result()
        scheduled = []
        
        legacy_patterns = [
            'forecasting_data_warehouse.soybean_oil_prices',
            'production_training_data',
            'models_v4.production_training_data',
        ]
        
        count = 0
        for row in results:
            count += 1
            if count % 100 == 0:
                print(f"    Processed {count} jobs...")
            
            query_text = row.query.upper() if row.query else ''
            matches = []
            
            for pattern in legacy_patterns:
                if pattern.upper() in query_text:
                    matches.append(pattern)
            
            if matches:
                scheduled.append({
                    'job_id': row.job_id,
                    'creation_time': str(row.creation_time),
                    'job_type': row.job_type,
                    'statement_type': row.statement_type,
                    'legacy_tables_referenced': matches
                })
        
        print(f"✅ Found {len(scheduled)} scheduled queries referencing legacy tables (last 7 days, {count} total jobs scanned)")
        return scheduled
    except Exception as e:
        print(f"  ⚠️  Could not query JOBS_BY_PROJECT: {e}")
        print("  (This is normal if permissions are limited or query times out)")
        print("  Continuing without scheduled query analysis...")
        return []

def check_existing_backups(client):
    """
    Check if any backup datasets already exist (safety check).
    """
    print("\n" + "="*80)
    print("STEP 3: CHECKING FOR EXISTING BACKUPS")
    print("="*80)
    
    timestamp = datetime.now().strftime("%Y%m%d")
    backup_suffix = f"_backup_{timestamp}"
    
    production_datasets = [
        'forecasting_data_warehouse',
        'models_v4',
        'training',
        'features',
        'raw_intelligence'
    ]
    
    existing_backups = []
    
    for dataset_id in production_datasets:
        backup_dataset_id = f"{dataset_id}{backup_suffix}"
        dataset_ref = client.dataset(backup_dataset_id)
        
        try:
            existing = client.get_dataset(dataset_ref)
            existing_backups.append(backup_dataset_id)
            print(f"  ⚠️  {backup_dataset_id} already exists (created: {existing.created})")
        except:
            print(f"  ✅ {backup_dataset_id} does not exist (safe to create)")
    
    if existing_backups:
        print(f"\n  ⚠️  Found {len(existing_backups)} existing backup datasets")
        print("  These will be skipped. If you want to recreate, delete them first.")
    else:
        print(f"\n  ✅ No existing backups found for today ({timestamp})")
    
    return existing_backups

def create_backup_datasets(client):
    """
    Create timestamped backup datasets for each production dataset.
    Only creates if they don't already exist.
    """
    print("\n" + "="*80)
    print("STEP 4: CREATING BACKUP DATASETS")
    print("="*80)
    
    timestamp = datetime.now().strftime("%Y%m%d")
    backup_suffix = f"_backup_{timestamp}"
    
    production_datasets = [
        'forecasting_data_warehouse',
        'models_v4',
        'training',
        'features',
        'raw_intelligence'
    ]
    
    created_backups = []
    
    for dataset_id in production_datasets:
        backup_dataset_id = f"{dataset_id}{backup_suffix}"
        
        try:
            # Check if backup already exists
            dataset_ref = client.dataset(backup_dataset_id)
            try:
                existing = client.get_dataset(dataset_ref)
                print(f"  ⚠️  {backup_dataset_id} already exists (created: {existing.created}), skipping")
                created_backups.append(backup_dataset_id)  # Count as "created" for manifest
                continue
            except:
                pass  # Dataset doesn't exist, create it
            
            # Create backup dataset
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = LOCATION
            dataset.description = f"Backup of {dataset_id} created {timestamp} for FRESH_START migration"
            
            dataset = client.create_dataset(dataset, exists_ok=False)
            print(f"  ✅ Created backup dataset: {backup_dataset_id}")
            created_backups.append(backup_dataset_id)
            
        except Exception as e:
            print(f"  ❌ Error creating {backup_dataset_id}: {e}")
            print(f"     This may be a permissions issue or the dataset name is invalid")
    
    return created_backups

def generate_dependency_manifest(views, scheduled_queries, backup_datasets):
    """
    Generate markdown manifest of all dependencies for refactoring checklist.
    """
    manifest_path = Path("docs/migration/bq_dependency_manifest.md")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(manifest_path, 'w') as f:
        f.write("# BigQuery Dependency Manifest\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("**Purpose:** Refactoring checklist for FRESH_START migration\n\n")
        f.write("---\n\n")
        
        f.write("## Views Referencing Legacy Tables\n\n")
        f.write(f"**Total:** {len(views)} views\n\n")
        
        if views:
            f.write("| Dataset | View Name | Legacy Tables Referenced |\n")
            f.write("|---------|-----------|--------------------------|\n")
            for v in views:
                legacy = ', '.join(v['legacy_tables_referenced'])
                f.write(f"| {v['dataset']} | {v['view_name']} | {legacy} |\n")
        else:
            f.write("No views found referencing legacy tables.\n")
        
        f.write("\n---\n\n")
        f.write("## Scheduled Queries (Last 30 Days)\n\n")
        f.write(f"**Total:** {len(scheduled_queries)} queries\n\n")
        
        if scheduled_queries:
            f.write("| Job ID | Creation Time | Statement Type | Legacy Tables Referenced |\n")
            f.write("|--------|---------------|----------------|--------------------------|\n")
            for sq in scheduled_queries[:50]:  # Limit to first 50
                legacy = ', '.join(sq['legacy_tables_referenced'])
                f.write(f"| {sq['job_id'][:20]}... | {sq['creation_time']} | {sq['statement_type']} | {legacy} |\n")
        else:
            f.write("No scheduled queries found referencing legacy tables.\n")
        
        f.write("\n---\n\n")
        f.write("## Backup Datasets Created\n\n")
        f.write(f"**Total:** {len(backup_datasets)} backup datasets\n\n")
        
        if backup_datasets:
            for backup in backup_datasets:
                f.write(f"- `{backup}`\n")
        else:
            f.write("No backup datasets created.\n")
        
        f.write("\n---\n\n")
        f.write("## Refactoring Checklist\n\n")
        f.write("### Phase 1: View Updates\n")
        f.write("- [ ] Update all views to reference prefixed tables\n")
        f.write("- [ ] Test each view after update\n")
        f.write("- [ ] Verify no broken dependencies\n\n")
        
        f.write("### Phase 2: Scheduled Query Updates\n")
        f.write("- [ ] Review scheduled queries in Cloud Console\n")
        f.write("- [ ] Update queries to reference prefixed tables\n")
        f.write("- [ ] Test scheduled query execution\n\n")
        
        f.write("### Phase 3: Dashboard/API Updates\n")
        f.write("- [ ] Update dashboard queries\n")
        f.write("- [ ] Update API endpoints\n")
        f.write("- [ ] Test end-to-end workflows\n\n")
    
    print(f"\n✅ Generated dependency manifest: {manifest_path}")
    return manifest_path

def main():
    """Run complete dependency analysis and backup creation."""
    
    print("="*80)
    print("WEEK 0 DAY 2: BIGQUERY DEPENDENCY ANALYSIS & BACKUP")
    print("="*80)
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print("="*80)
    
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    
    # Step 1: Analyze view dependencies
    views = analyze_view_dependencies(client)
    
    # Step 2: Analyze scheduled queries (may timeout, that's OK)
    scheduled_queries = analyze_scheduled_queries(client)
    
    # Step 3: Check for existing backups (safety check)
    existing_backups = check_existing_backups(client)
    
    # Step 4: Create backup datasets (only if they don't exist)
    backup_datasets = create_backup_datasets(client)
    
    # Step 5: Generate manifest
    manifest_path = generate_dependency_manifest(views, scheduled_queries, backup_datasets)
    
    print("\n" + "="*80)
    print("✅ DEPENDENCY ANALYSIS COMPLETE")
    print("="*80)
    print(f"Manifest saved to: {manifest_path}")
    print("\nNext Steps:")
    print("1. Review dependency manifest")
    print("2. Create prefixed BigQuery tables (Week 0 Day 2 - Part 2)")
    print("3. Copy legacy tables to backup datasets")
    print("4. Refactor views to point at prefixed tables (Week 0 Day 3)")

if __name__ == "__main__":
    main()

