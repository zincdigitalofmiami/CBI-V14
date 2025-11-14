#!/usr/bin/env python3
"""
COMPREHENSIVE DATA AUDIT - Finds and exports EVERYTHING
No assumptions, no filters, no shortcuts.
"""

import pandas as pd
from google.cloud import bigquery
from pathlib import Path
from tqdm import tqdm
import json
from datetime import datetime

PROJECT_ID = "cbi-v14"
OUTPUT_DIR = Path("GPT_Data/comprehensive_audit")
RAW_DIR = Path("TrainingData/raw")

def get_all_objects(client):
    """Get EVERY object from EVERY dataset - no exceptions."""
    all_objects = []
    
    datasets = [d.dataset_id for d in client.list_datasets() if d.dataset_id != '_SESSION']
    
    print(f"Scanning {len(datasets)} datasets...")
    
    for dataset_id in tqdm(datasets, desc="Scanning datasets"):
        try:
            tables = list(client.list_tables(dataset_id))
            for table in tables:
                try:
                    table_ref = client.get_table(f"{PROJECT_ID}.{dataset_id}.{table.table_id}")
                    all_objects.append({
                        'dataset': dataset_id,
                        'table': table.table_id,
                        'type': table_ref.table_type,
                        'rows': table_ref.num_rows,
                        'cols': len(table_ref.schema),
                        'location': table_ref.location,
                        'created': str(table_ref.created),
                        'modified': str(table_ref.modified),
                        'schema': [{'name': f.name, 'type': f.field_type} for f in table_ref.schema[:10]]  # First 10 cols
                    })
                except Exception as e:
                    all_objects.append({
                        'dataset': dataset_id,
                        'table': table.table_id,
                        'type': 'ERROR',
                        'rows': 0,
                        'cols': 0,
                        'error': str(e)
                    })
        except Exception as e:
            print(f"Error scanning {dataset_id}: {e}")
    
    return all_objects

def export_everything(client, all_objects):
    """Export EVERYTHING - no filtering, no skipping."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    export_log = []
    errors = []
    
    print(f"\nExporting {len(all_objects)} objects...")
    
    for obj in tqdm(all_objects, desc="Exporting"):
        if obj.get('error'):
            errors.append(obj)
            continue
            
        dataset = obj['dataset']
        table = obj['table']
        table_id = f"{PROJECT_ID}.{dataset}.{table}"
        
        try:
            # Export regardless of row count
            query = f"SELECT * FROM `{table_id}`"
            df = client.query(query).to_dataframe()
            
            # Save to external drive
            raw_path = RAW_DIR / dataset / f"{table}.parquet"
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(raw_path, index=False)
            
            # Save to repo
            repo_path = OUTPUT_DIR / f"{dataset}.{table}.parquet"
            df.to_parquet(repo_path, index=False)
            
            export_log.append({
                'dataset': dataset,
                'table': table,
                'type': obj['type'],
                'rows_exported': len(df),
                'cols_exported': len(df.columns),
                'raw_path': str(raw_path),
                'repo_path': str(repo_path),
                'status': 'SUCCESS'
            })
            
        except Exception as e:
            errors.append({
                'dataset': dataset,
                'table': table,
                'type': obj['type'],
                'error': str(e),
                'status': 'ERROR'
            })
    
    return export_log, errors

def main():
    print("=" * 80)
    print("COMPREHENSIVE DATA AUDIT - NO ASSUMPTIONS, NO FILTERS")
    print("=" * 80)
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # Step 1: Find EVERYTHING
    print("\n[STEP 1] Finding ALL objects in ALL datasets...")
    all_objects = get_all_objects(client)
    
    # Save complete inventory
    inventory_df = pd.DataFrame(all_objects)
    inventory_path = OUTPUT_DIR / "complete_inventory.json"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    inventory_df.to_json(inventory_path, orient='records', indent=2)
    inventory_df.to_csv(OUTPUT_DIR / "complete_inventory.csv", index=False)
    
    print(f"\n✅ Found {len(all_objects)} total objects")
    print(f"   - Tables: {sum(1 for o in all_objects if o.get('type') == 'TABLE')}")
    print(f"   - Views: {sum(1 for o in all_objects if o.get('type') == 'VIEW')}")
    print(f"   - Total rows: {sum(o.get('rows', 0) for o in all_objects)}")
    
    # Step 2: Export EVERYTHING
    print("\n[STEP 2] Exporting EVERYTHING...")
    export_log, errors = export_everything(client, all_objects)
    
    # Save export log
    export_df = pd.DataFrame(export_log)
    export_df.to_csv(OUTPUT_DIR / "export_log.csv", index=False)
    
    if errors:
        errors_df = pd.DataFrame(errors)
        errors_df.to_csv(OUTPUT_DIR / "export_errors.csv", index=False)
        print(f"\n⚠️  {len(errors)} objects had errors (see export_errors.csv)")
    
    # Step 3: Generate summary
    print("\n[STEP 3] Generating summary...")
    summary = {
        'audit_date': datetime.now().isoformat(),
        'total_objects': len(all_objects),
        'successfully_exported': len(export_log),
        'errors': len(errors),
        'total_rows_exported': sum(e.get('rows_exported', 0) for e in export_log),
        'datasets': len(set(o['dataset'] for o in all_objects)),
        'breakdown_by_dataset': {}
    }
    
    for dataset in set(o['dataset'] for o in all_objects):
        dataset_objects = [o for o in all_objects if o['dataset'] == dataset]
        summary['breakdown_by_dataset'][dataset] = {
            'total_objects': len(dataset_objects),
            'tables': sum(1 for o in dataset_objects if o.get('type') == 'TABLE'),
            'views': sum(1 for o in dataset_objects if o.get('type') == 'VIEW'),
            'total_rows': sum(o.get('rows', 0) for o in dataset_objects)
        }
    
    summary_path = OUTPUT_DIR / "audit_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("\n" + "=" * 80)
    print("AUDIT COMPLETE")
    print("=" * 80)
    print(f"✅ Exported {len(export_log)} objects")
    print(f"❌ Errors: {len(errors)}")
    print(f"📊 Total rows: {summary['total_rows_exported']:,}")
    print(f"\nFiles saved to:")
    print(f"  - {OUTPUT_DIR}")
    print(f"  - {RAW_DIR}")
    print(f"\nReview:")
    print(f"  - {OUTPUT_DIR / 'complete_inventory.csv'}")
    print(f"  - {OUTPUT_DIR / 'export_log.csv'}")
    if errors:
        print(f"  - {OUTPUT_DIR / 'export_errors.csv'}")

if __name__ == "__main__":
    main()

