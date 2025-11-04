#!/usr/bin/env python3
"""
Verify which models exist and their configurations
"""

from google.cloud import bigquery
import json

PROJECT = "cbi-v14"
DATASET = "models_v4"

client = bigquery.Client(project=PROJECT)

models_to_check = [
    'bqml_1w',
    'bqml_1m', 
    'bqml_3m',
    'bqml_6m',
    'bqml_1w_all_features',
    'bqml_1m_all_features',
    'bqml_3m_all_features',
    'bqml_6m_all_features'
]

print("="*80)
print("MODEL CONFIGURATION VERIFICATION")
print("="*80)

results = []

for model_name in models_to_check:
    try:
        model_ref = client.get_model(f"{PROJECT}.{DATASET}.{model_name}")
        
        # Get training options
        training_runs = model_ref.training_runs
        if training_runs:
            latest_run = training_runs[-1]
            options = latest_run.training_options
            
            # Get feature count (approximate from training data)
            feature_count = "N/A"
            try:
                # Try to get schema info
                if hasattr(model_ref, 'feature_columns'):
                    feature_count = len(model_ref.feature_columns) if model_ref.feature_columns else "N/A"
            except:
                pass
            
            results.append({
                'model': model_name,
                'exists': True,
                'creation_time': str(model_ref.created),
                'max_iterations': options.get('num_iterations', options.get('max_iterations', 'N/A')),
                'early_stop': options.get('early_stop', 'N/A'),
                'feature_count': feature_count
            })
        else:
            results.append({
                'model': model_name,
                'exists': True,
                'creation_time': str(model_ref.created),
                'max_iterations': 'N/A',
                'early_stop': 'N/A',
                'feature_count': 'N/A'
            })
    except Exception as e:
        results.append({
            'model': model_name,
            'exists': False,
            'error': str(e)
        })

print("\nResults:")
print("-"*80)
for r in results:
    if r['exists']:
        print(f"\n✅ {r['model']}:")
        print(f"   Created: {r['creation_time']}")
        print(f"   Iterations: {r['max_iterations']}")
        print(f"   Early Stop: {r['early_stop']}")
        print(f"   Features: {r['feature_count']}")
    else:
        print(f"\n❌ {r['model']}: NOT FOUND")

print("\n" + "="*80)
print("PRODUCTION PREDICTIONS CHECK")
print("="*80)

query = """
SELECT 
  DISTINCT model_name,
  COUNT(*) as count,
  MAX(forecast_date) as latest_forecast
FROM `cbi-v14.predictions_uc1.production_forecasts`
GROUP BY model_name
ORDER BY latest_forecast DESC
"""

result = client.query(query).to_dataframe()
print("\nPredictions table model_name values:")
print(result.to_string(index=False))

print("\n" + "="*80)
print("RECOMMENDATION")
print("="*80)

short_models = [r for r in results if r['exists'] and '_all_features' not in r['model']]
long_models = [r for r in results if r['exists'] and '_all_features' in r['model']]

if short_models and long_models:
    print("\n⚠️  Both model sets exist!")
    print("\nSHORT names (production predictions use these):")
    for m in short_models:
        print(f"  - {m['model']} (iterations: {m['max_iterations']})")
    print("\nLONG names (training files create these):")
    for m in long_models:
        print(f"  - {m['model']} (iterations: {m['max_iterations']})")
    print("\n✅ Use SHORT names in forecast generation to match production predictions")

