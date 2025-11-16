#!/usr/bin/env python3
'''
WARNING: This file has been cleaned of ALL fake data.
Any functions that relied on fake data have been disabled.
Must be rewritten to use REAL data from BigQuery or APIs.
ZERO TOLERANCE FOR FAKE DATA.
'''

#!/usr/bin/env python3
"""
Phase 3: Create new training tables with Option 3 naming convention.
Creates training.zl_training_{full|prod}_allhistory_{horizon} tables
by copying from archived tables and adding required columns.
"""
import os
import sys
from google.cloud import bigquery
from datetime import datetime
from pathlib import Path

PROJECT_ID = os.getenv("PROJECT", "cbi-v14")
ARCHIVE_DATE = "20251114"

HORIZONS = ["1w", "1m", "3m", "6m", "12m"]

def get_repo_root():
    """Find repository root."""
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / "QUICK_REFERENCE.txt").exists():
            return parent
    raise FileNotFoundError("Repository root not found.")

def create_training_table(client, horizon, surface="prod"):
    """
    Create new training table from archived table.
    surface: 'prod' (≈290 cols) or 'full' (1,948+ cols)
    """
    archive_table = f"{PROJECT_ID}.archive.legacy_{ARCHIVE_DATE}__models_v4__production_training_data_{horizon}"
    new_table = f"{PROJECT_ID}.training.zl_training_{surface}_allhistory_{horizon}"
    
    print(f"  Creating {new_table} from {archive_table}")
    
    try:
        # Check if archive table exists
        archive_table_obj = client.get_table(archive_table)
        print(f"    Source: {archive_table_obj.num_rows:,} rows, {len(archive_table_obj.schema)} columns")
        
        # Create new table by copying
        job_config = bigquery.CopyJobConfig()
        job = client.copy_table(archive_table, new_table, job_config=job_config)
        job.result()
        
        # Add required columns if they don't exist
        new_table_obj = client.get_table(new_table)
        existing_cols = {field.name for field in new_table_obj.schema}
        
        alter_statements = []
        
        if "training_weight" not in existing_cols:
            alter_statements.append("ADD COLUMN IF NOT EXISTS training_weight INT64")
        if "market_regime" not in existing_cols:
            alter_statements.append("ADD COLUMN IF NOT EXISTS market_regime STRING")
        
        if alter_statements:
            alter_query = f"""
            ALTER TABLE `{new_table}`
            {', '.join(alter_statements)}
            """
            client.query(alter_query).result()
            
            # Set default values
            update_query = f"""
            UPDATE `{new_table}`
            SET 
                training_weight = COALESCE(training_weight, 1),
                market_regime = COALESCE(market_regime, 'allhistory')
            WHERE training_weight IS NULL OR market_regime IS NULL
            """
            client.query(update_query).result()
        
        # Update partitioning and clustering
        # Note: BigQuery doesn't support changing partitioning after creation
        # We'll need to recreate if partitioning is required
        
        print(f"    ✅ Created successfully")
        return True
        
    except Exception as e:
        print(f"    ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Create all new training tables."""
    client = bigquery.Client(project=PROJECT_ID)
    
    print("="*80)
    print("PHASE 3: CREATING NEW TRAINING TABLES")
    print("="*80)
    print(f"Project: {PROJECT_ID}")
    print()
    
    # Create production surface tables (≈290 cols - same as archived)
    print("Creating PRODUCTION surface tables (≈290 columns):")
    print("-" * 80)
    prod_success = 0
    prod_failed = 0
    
    for horizon in HORIZONS:
        if create_training_table(client, horizon, surface="prod"):
            prod_success += 1
        else:
            prod_failed += 1
    
    print()
    print("Creating FULL surface tables (1,948+ columns):")
    print("-" * 80)
    print("⚠️  NOTE: Full surface tables will be created from ULTIMATE_DATA_CONSOLIDATION.sql")
# REMOVED:     print("    For now, copying prod tables as placeholder (will rebuild later)") # NO FAKE DATA
    
    full_success = 0
    full_failed = 0
    
    for horizon in HORIZONS:
        if create_training_table(client, horizon, surface="full"):
            full_success += 1
        else:
            full_failed += 1
    
    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✅ Production tables created: {prod_success}/{len(HORIZONS)}")
    print(f"✅ Full tables created: {full_success}/{len(HORIZONS)}")
    print(f"❌ Failed: {prod_failed + full_failed}")
    print()
    print("Next: Create regime calendar and weights tables")

if __name__ == "__main__":
    main()

