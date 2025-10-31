#!/usr/bin/env python3
"""Real-time training progress monitor"""
from google.cloud import bigquery
import time
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

target_models = {
    '1w': ['zl_boosted_tree_1w_v1', 'zl_dnn_optimized_1w_v1', 'zl_linear_1w_v1', 'zl_arima_1w_final'],
    '1m': ['zl_boosted_tree_1m_v1', 'zl_dnn_optimized_1m_v1', 'zl_linear_1m_v1', 'zl_arima_1m_final'],
    '3m': ['zl_boosted_tree_3m_v1', 'zl_dnn_optimized_3m_v1', 'zl_linear_3m_v1', 'zl_arima_3m_final'],
    '6m': ['zl_boosted_tree_6m_v1', 'zl_dnn_optimized_6m_v1', 'zl_linear_6m_v1', 'zl_arima_6m_final']
}

print("="*80)
print("MONITORING TRAINING PROGRESS")
print("="*80)
print(f"Target: 16 production models across 4 horizons\n")

while True:
    completed = {}
    model_details = []
    
    for horizon, models in target_models.items():
        completed[horizon] = 0
        for model_name in models:
            try:
                model = client.get_model(f'cbi-v14.models.{model_name}')
                completed[horizon] += 1
                model_details.append((horizon, model_name, 'COMPLETE', model.created))
            except:
                model_details.append((horizon, model_name, 'PENDING', None))
    
    total = sum(completed.values())
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Progress: {total}/16 models")
    print("="*80)
    
    for horizon in ['1w', '1m', '3m', '6m']:
        progress = '█' * completed[horizon] + '░' * (4 - completed[horizon])
        print(f"  {horizon}: [{progress}] {completed[horizon]}/4")
    
    if total >= 16:
        print("\n✅ ALL 16 MODELS COMPLETE!")
        break
    
    if total == 0:
        print("\n⏳ Training not started yet...")
    
    time.sleep(30)  # Check every 30 seconds

print("\n" + "="*80)
print("FINAL STATUS")
print("="*80)

for horizon, models in target_models.items():
    print(f"\n{horizon} Horizon:")
    for model in models:
        try:
            m = client.get_model(f'cbi-v14.models.{model}')
            print(f"  ✅ {model:30s} (created {m.created.strftime('%H:%M:%S')})")
        except:
            print(f"  ❌ {model:30s} (failed or not created)")

print("\nTraining complete!")














