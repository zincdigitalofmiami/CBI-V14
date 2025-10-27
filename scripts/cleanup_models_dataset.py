#!/usr/bin/env python3
"""
Surgical cleanup of models dataset - remove all non-essential objects
Only keep the 16 production models and training_dataset_final_v1
"""

from google.cloud import bigquery
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print(f"MODELS DATASET CLEANUP - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# ONLY KEEP THESE ESSENTIAL OBJECTS
essential_objects = [
    # 16 Production Models
    'zl_boosted_tree_1w_production', 'zl_boosted_tree_1m_production',
    'zl_boosted_tree_3m_production', 'zl_boosted_tree_6m_production',
    'zl_dnn_1w_production', 'zl_dnn_1m_production',
    'zl_dnn_3m_production', 'zl_dnn_6m_production',
    'zl_linear_production_1w', 'zl_linear_production_1m',
    'zl_linear_production_3m', 'zl_linear_production_6m',
    'zl_arima_production_1w', 'zl_arima_production_1m',
    'zl_arima_production_3m', 'zl_arima_production_6m',
    # Training dataset
    'training_dataset_final_v1'
]

print("\n1. LISTING ALL OBJECTS IN MODELS DATASET:")
print("-"*80)

# Get all tables and views
tables = list(client.list_tables('cbi-v14.models'))
models = list(client.list_models('cbi-v14.models'))

print(f"\nFound {len(tables)} tables/views:")
for table in tables:
    status = "✓ KEEP" if table.table_id in essential_objects else "✗ DELETE"
    print(f"  [{status}] {table.table_id}")

print(f"\nFound {len(models)} models:")
for model in models:
    status = "✓ KEEP" if model.model_id in essential_objects else "✗ DELETE"
    print(f"  [{status}] {model.model_id}")

print("\n2. STARTING CLEANUP:")
print("-"*80)

deleted_count = 0
kept_count = 0
error_count = 0

# Delete all non-essential tables
for table in tables:
    if table.table_id not in essential_objects:
        print(f"Deleting table: {table.table_id}")
        try:
            client.delete_table(f"cbi-v14.models.{table.table_id}")
            print(f"  ✓ Deleted")
            deleted_count += 1
        except Exception as e:
            print(f"  ✗ Error: {str(e)[:80]}")
            error_count += 1
    else:
        print(f"Keeping table: {table.table_id}")
        kept_count += 1

# Delete all non-essential models
for model in models:
    if model.model_id not in essential_objects:
        print(f"Deleting model: {model.model_id}")
        try:
            client.delete_model(f"cbi-v14.models.{model.model_id}")
            print(f"  ✓ Deleted")
            deleted_count += 1
        except Exception as e:
            print(f"  ✗ Error: {str(e)[:80]}")
            error_count += 1
    else:
        print(f"Keeping model: {model.model_id}")
        kept_count += 1

print("\n3. CLEANUP SUMMARY:")
print("-"*80)
print(f"  Objects deleted: {deleted_count}")
print(f"  Objects kept: {kept_count}")
print(f"  Errors: {error_count}")

print("\n4. FINAL VERIFICATION:")
print("-"*80)

# List remaining objects
remaining_tables = list(client.list_tables('cbi-v14.models'))
remaining_models = list(client.list_models('cbi-v14.models'))

print(f"\nRemaining tables/views ({len(remaining_tables)}):")
for table in remaining_tables:
    print(f"  ✓ {table.table_id}")

print(f"\nRemaining models ({len(remaining_models)}):")
for model in remaining_models:
    print(f"  ✓ {model.model_id}")

print("\nCLEANUP COMPLETE.")
