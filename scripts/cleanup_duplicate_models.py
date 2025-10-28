#!/usr/bin/env python3
"""Delete ALL duplicate and old models - keep only 16 production models"""
from google.cloud import bigquery

client = bigquery.Client(project='cbi-v14')

# KEEP THESE 16 PRODUCTION MODELS ONLY
keep_models = {
    'zl_boosted_tree_1w_production',
    'zl_boosted_tree_1m_production',
    'zl_boosted_tree_3m_production',
    'zl_boosted_tree_6m_production',
    'zl_dnn_1w_production',
    'zl_dnn_1m_production',
    'zl_dnn_3m_production',
    'zl_dnn_6m_production',
    'zl_linear_production_1w',
    'zl_linear_production_1m',
    'zl_linear_production_3m',
    'zl_linear_production_6m',
    'zl_arima_production_1w',
    'zl_arima_production_1m',
    'zl_arima_production_3m',
    'zl_arima_production_6m'
}

# Get ALL models
all_models_query = "SELECT model_name FROM `cbi-v14.models.INFORMATION_SCHEMA.MODELS`"
all_models = [row.model_name for row in client.query(all_models_query).result()]

# Identify models to DELETE
to_delete = [m for m in all_models if m not in keep_models]

print("="*80)
print("MODEL CLEANUP - DELETING DUPLICATES AND OLD MODELS")
print("="*80)
print(f"\nTotal models found: {len(all_models)}")
print(f"Production models to KEEP: {len(keep_models)}")
print(f"Duplicates/old to DELETE: {len(to_delete)}")

print(f"\n\nDELETING {len(to_delete)} OLD/DUPLICATE MODELS:")
print("-"*80)

deleted = 0
for model_name in to_delete:
    print(f"Deleting: {model_name}")
    try:
        client.delete_model(f"cbi-v14.models.{model_name}")
        deleted += 1
    except Exception as e:
        print(f"  Error: {str(e)[:50]}")

print(f"\n{'='*80}")
print(f"✅ CLEANUP COMPLETE: {deleted}/{len(to_delete)} deleted")
print("="*80)
print(f"\nRemaining models: {len(all_models) - deleted}")
print("These are your 16 production models ONLY.")









