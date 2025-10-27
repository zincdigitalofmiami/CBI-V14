#!/usr/bin/env python3
"""
Monitor training progress of all v2 models
"""

from google.cloud import bigquery
from datetime import datetime
import time

client = bigquery.Client(project='cbi-v14')

print(f"MONITORING MODEL TRAINING - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# Expected models
expected_models = [
    'zl_boosted_tree_1w_production_v2',
    'zl_boosted_tree_1m_production_v2',
    'zl_boosted_tree_3m_production_v2',
    'zl_boosted_tree_6m_production_v2',
    'zl_dnn_1w_production_v2',
    'zl_dnn_1m_production_v2',
    'zl_dnn_3m_production_v2',
    'zl_dnn_6m_production_v2',
    'zl_arima_production_1w_v2',
    'zl_arima_production_1m_v2',
    'zl_linear_production_1w_v2',
    'zl_linear_production_1m_v2'
]

# Check current status
models = list(client.list_models('cbi-v14.models'))
v2_models = {m.model_id: m.model_type for m in models if 'v2' in m.model_id}

print(f"\nExpected: {len(expected_models)} models")
print(f"Completed: {len(v2_models)} models")
print("-"*80)

# Show status for each expected model
for model_name in expected_models:
    if model_name in v2_models:
        print(f"✓ {model_name:<40} - {v2_models[model_name]:<20} COMPLETED")
    else:
        print(f"⏳ {model_name:<40} - TRAINING...")

# Check for completed models with evaluation metrics
print("\n" + "="*80)
print("CHECKING PERFORMANCE OF COMPLETED MODELS")
print("="*80)

for model_name in v2_models:
    if 'boosted_tree' in model_name or 'linear' in model_name or 'dnn' in model_name:
        try:
            eval_query = f"""
            SELECT 
                mean_absolute_error as MAE,
                mean_squared_error as MSE,
                r2_score as R2
            FROM ML.EVALUATE(MODEL `cbi-v14.models.{model_name}`)
            """
            
            result = client.query(eval_query).to_dataframe()
            if not result.empty:
                mae = result['MAE'].iloc[0]
                r2 = result['R2'].iloc[0]
                print(f"\n{model_name}:")
                print(f"  MAE: {mae:.4f}")
                print(f"  R²:  {r2:.4f}")
                
                # Compare to old version
                if mae < 1.0:
                    print(f"  🌟 EXCELLENT! MAE < 1.0")
                elif mae < 2.0:
                    print(f"  ✓ GOOD! MAE < 2.0")
                else:
                    print(f"  ⚠️ Check performance")
        except:
            pass

print("\n" + "="*80)
print("TRAINING STATUS SUMMARY")
print("="*80)

completed_types = {}
for model_name, model_type in v2_models.items():
    if model_type not in completed_types:
        completed_types[model_type] = 0
    completed_types[model_type] += 1

for model_type, count in completed_types.items():
    print(f"  {model_type}: {count} models completed")

remaining = len(expected_models) - len(v2_models)
if remaining > 0:
    print(f"\n⏳ Still training: {remaining} models")
    print("  (Boosted Trees and DNNs typically take 5-15 minutes)")
else:
    print(f"\n✓ ALL MODELS COMPLETED!")

print("\nTo check again, run: python3 scripts/monitor_training.py")
