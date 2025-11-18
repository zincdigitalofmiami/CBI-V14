#!/usr/bin/env python3
"""
Phase 6: Create Shim Views for Backward Compatibility
Creates views in models_v4 pointing to new training tables.
"""
import os
import sys
from google.cloud import bigquery

PROJECT_ID = os.getenv("PROJECT", "cbi-v14")

HORIZONS = ["1w", "1m", "3m", "6m", "12m"]

def main():
    """Create all shim views."""
    client = bigquery.Client(project=PROJECT_ID)
    
    print("="*80)
    print("PHASE 6: CREATING SHIM VIEWS")
    print("="*80)
    print()
    
    # Get training dataset location
    try:
        training_dataset = client.get_dataset(f"{PROJECT_ID}.training")
        location = training_dataset.location
        print(f"Training dataset location: {location}")
    except Exception as e:
        print(f"❌ Error getting training dataset: {e}")
        return False
    
    print()
    print("Creating shim views in models_v4:")
    print("-" * 80)
    
    success_count = 0
    failed_count = 0
    
    for horizon in HORIZONS:
        view_name = f"{PROJECT_ID}.models_v4.production_training_data_{horizon}"
        source_table = f"{PROJECT_ID}.training.zl_training_prod_allhistory_{horizon}"
        
        query = f"""
        CREATE OR REPLACE VIEW `{view_name}` AS
        SELECT * FROM `{source_table}`
        """
        
        try:
            job = client.query(query, location=location)
            job.result()
            print(f"  ✅ {view_name.split('.')[-1]}")
            success_count += 1
        except Exception as e:
            print(f"  ❌ {view_name.split('.')[-1]}: {e}")
            failed_count += 1
    
    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✅ Created: {success_count}/{len(HORIZONS)}")
    print(f"❌ Failed: {failed_count}")
    print()
    print("⚠️  NOTE: These shim views will be removed after 30-day grace period")
    print("    Update all scripts/notebooks to use new table names before then.")
    
    return failed_count == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)



