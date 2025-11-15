#!/usr/bin/env python3
"""
⚠️ LEGACY SCRIPT - REFERENCE ONLY ⚠️

This script is NOT used in the current architecture (100% local M4 training).
Kept for reference only.

Current table naming: training.zl_training_prod_allhistory_{horizon}
Legacy tables referenced: models_v4.vertex_ai_training_{horizon}_base
"""
import pandas as pd
from google.cloud import bigquery

def audit_training_schemas():
    """
    Audits the schemas of all vertex_ai_training_*_base tables and reports discrepancies.
    Updated to use new naming convention: vertex_ai_training_{horizon}_base
    
    ⚠️ LEGACY: This script references old table names. Current architecture uses:
    - training.zl_training_prod_allhistory_{horizon}
    """
    client = bigquery.Client(project='cbi-v14')
    datasets = ['models_v4']
    tables_to_audit = [
        'vertex_ai_training_1m_base',  # Or 'production_training_data_1m' if migrating
        'vertex_ai_training_3m_base',  # Or 'production_training_data_3m' if migrating
        'vertex_ai_training_6m_base',  # Or 'production_training_data_6m' if migrating
        'vertex_ai_training_12m_base'  # Or 'production_training_data_12m' if migrating
    ]

    schema_info = {}

    print("="*80)
    print("AUDITING TRAINING DATA SCHEMAS")
    print("="*80)

    for table_name in tables_to_audit:
        try:
            table_ref = client.get_table(f'cbi-v14.models_v4.{table_name}')
            schema = {field.name: field.field_type for field in table_ref.schema}
            schema_info[table_name] = schema
            print(f"✅ Found {table_name} with {len(schema)} columns.")
        except Exception as e:
            print(f"❌ Could not find or access {table_name}: {e}")
            schema_info[table_name] = None

    # Compare schemas
    base_table = 'vertex_ai_training_1m_base'  # Or 'production_training_data_1m' if migrating
    base_schema = schema_info.get(base_table)

    if not base_schema:
        print(f"\nBase table '{base_table}' not found. Cannot compare schemas.")
        return

    print("\n" + "="*80)
    print(f"COMPARING ALL SCHEMAS TO '{base_table}' ({len(base_schema)} columns)")
    print("="*80)

    for table_name, schema in schema_info.items():
        if table_name == base_table or not schema:
            continue

        base_columns = set(base_schema.keys())
        current_columns = set(schema.keys())

        if base_columns == current_columns:
            print(f"✅ {table_name}: Schemas match perfectly!")
        else:
            print(f"❌ {table_name}: Schema mismatch found!")
            missing_from_current = base_columns - current_columns
            extra_in_current = current_columns - base_columns

            if missing_from_current:
                print(f"  - Missing {len(missing_from_current)} columns (present in {base_table} but not here):")
                for col in sorted(list(missing_from_current))[:5]:
                    print(f"    - {col}")
                if len(missing_from_current) > 5:
                    print(f"    - ... and {len(missing_from_current) - 5} more")

            if extra_in_current:
                print(f"  - Has {len(extra_in_current)} extra columns (present here but not in {base_table}):")
                for col in sorted(list(extra_in_current))[:5]:
                    print(f"    - {col}")
                if len(extra_in_current) > 5:
                    print(f"    - ... and {len(extra_in_current) - 5} more")

if __name__ == "__main__":
    audit_training_schemas()
