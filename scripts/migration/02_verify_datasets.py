#!/usr/bin/env python3
"""
Verify that all required datasets exist before proceeding with migration.
"""
import os
import sys
from google.cloud import bigquery
from pathlib import Path

PROJECT_ID = os.getenv("PROJECT", "cbi-v14")

REQUIRED_DATASETS = [
    "archive",
    "raw_intelligence",
    "features",
    "training",
    "predictions",
    "monitoring",
    "vegas_intelligence",
]

def main():
    """Verify all datasets exist."""
    client = bigquery.Client(project=PROJECT_ID)
    
    print("="*80)
    print("PHASE 2: VERIFYING DATASETS")
    print("="*80)
    print()
    
    existing = []
    missing = []
    
    for dataset_id in REQUIRED_DATASETS:
        dataset_ref = f"{PROJECT_ID}.{dataset_id}"
        try:
            dataset = client.get_dataset(dataset_ref)
            existing.append(dataset_id)
            print(f"✅ {dataset_id:25s} - EXISTS (location: {dataset.location})")
        except Exception:
            missing.append(dataset_id)
            print(f"❌ {dataset_id:25s} - MISSING")
    
    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✅ Existing: {len(existing)}/{len(REQUIRED_DATASETS)}")
    
    if missing:
        print(f"❌ Missing: {len(missing)}")
        print()
        print("Run the SQL script to create missing datasets:")
        print("  bq query --use_legacy_sql=false < scripts/migration/01_create_datasets.sql")
        return False
    else:
        print()
        print("✅ All required datasets exist!")
        print("Ready to proceed with Phase 3: Create new tables/views")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

