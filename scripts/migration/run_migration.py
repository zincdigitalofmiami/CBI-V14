#!/usr/bin/env python3
'''
WARNING: This file has been cleaned of ALL fake data.
Any functions that relied on fake data have been disabled.
Must be rewritten to use REAL data from BigQuery or APIs.
ZERO TOLERANCE FOR FAKE DATA.
'''

import os
from google.cloud import bigquery

# Configuration
PROJECT_ID = "cbi-v14"
MAPPING_FILE_PATH = "docs/plans/TABLE_MAPPING_MATRIX.md"
DRY_RUN = False  # Set to True to print actions without executing them

def parse_mapping_file(file_path):
    """Parses the markdown mapping file and returns a list of migration tasks."""
    tasks = []
    with open(file_path, 'r') as f:
        lines = f.readlines()

    # Find the start of the mapping table
    table_start_index = -1
    for i, line in enumerate(lines):
        if "| Legacy Dataset" in line:
            table_start_index = i + 2
            break
    
    if table_start_index == -1:
        raise ValueError("Could not find the mapping table in the markdown file.")

    current_legacy_dataset = None
    # Process each line in the table
    for line in lines[table_start_index:]:
        if not line.strip() or line.startswith("---"):
            continue
        
        parts = [p.strip().replace('**', '').replace('`', '') for p in line.split('|')]
        if len(parts) < 8:
            continue

        legacy_dataset = parts[1]
        if legacy_dataset:
            current_legacy_dataset = legacy_dataset
        else:
            legacy_dataset = current_legacy_dataset

        legacy_table = parts[2]
        table_type = parts[3]
        new_dataset = parts[4]
        new_table = parts[5]
        action = parts[6]
        notes = parts[7]

# REMOVED:         # Skip header and placeholder rows # NO FAKE DATA
        if legacy_dataset == "Legacy Dataset" or "..." in legacy_table:
            continue

        tasks.append({
            "legacy_dataset": legacy_dataset,
            "legacy_table": legacy_table,
            "type": table_type,
            "new_dataset": new_dataset,
            "new_table": new_table,
            "action": action,
            "notes": notes,
        })
    return tasks

def execute_migration(tasks, client):
    """Executes the migration tasks based on the parsed mapping."""
    print(f"Starting migration for {len(tasks)} tasks...")

    for task in tasks:
        legacy_full_id = f"{PROJECT_ID}.{task['legacy_dataset']}.{task['legacy_table']}"
        new_full_id = f"{PROJECT_ID}.{task['new_dataset']}.{task['new_table']}"

        print("-" * 50)
        print(f"Processing: {legacy_full_id} -> {new_full_id}")
        print(f"Action: {task['action']}")

        if task['action'].lower() == 'migrate':
            if task['type'].lower() == 'table':
                print(f"  Attempting to copy table...")
                if not DRY_RUN:
                    try:
                        job = client.copy_table(legacy_full_id, new_full_id)
                        job.result()  # Wait for the job to complete
                        print(f"  SUCCESS: Copied {legacy_full_id} to {new_full_id}")
                    except Exception as e:
                        print(f"  ERROR: Could not copy {legacy_full_id}. Reason: {e}")
                else:
                    print(f"  DRY RUN: Would copy {legacy_full_id} to {new_full_id}")
            else:
                print(f"  SKIPPING: Migration for views must be done manually by recreating the query.")

        elif task['action'].lower() == 'recreate':
            print(f"  MANUAL ACTION REQUIRED: Recreate view '{new_full_id}' with updated logic.")

        elif task['action'].lower() == 'archive':
            archive_table_id = f"{PROJECT_ID}.archive.{task['legacy_dataset']}_{task['legacy_table']}"
            print(f"  Attempting to archive table to {archive_table_id}...")
            if not DRY_RUN:
                try:
                    job = client.copy_table(legacy_full_id, archive_table_id)
                    job.result()
                    print(f"  SUCCESS: Archived {legacy_full_id} to {archive_table_id}")
                except Exception as e:
                    print(f"  ERROR: Could not archive {legacy_full_id}. Reason: {e}")
            else:
                print(f"  DRY RUN: Would archive {legacy_full_id} to {archive_table_id}")
        
        else:
            print(f"  WARNING: Unknown action '{task['action']}'. Skipping.")

    print("-" * 50)
    print("Migration script finished.")

if __name__ == "__main__":
    if not os.path.exists(MAPPING_FILE_PATH):
        print(f"ERROR: Mapping file not found at '{MAPPING_FILE_PATH}'")
    else:
        migration_tasks = parse_mapping_file(MAPPING_FILE_PATH)
        bq_client = bigquery.Client(project=PROJECT_ID)
        execute_migration(migration_tasks, bq_client)
