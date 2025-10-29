#!/usr/bin/env python3
"""Wait for all training to complete and generate final summary"""
from google.cloud import bigquery
from datetime import datetime
import time
import json

client = bigquery.Client(project='cbi-v14')

# Load submitted jobs
with open('logs/submitted_training_jobs.json', 'r') as f:
    submitted = json.load(f)

target_models = [j['name'] for j in submitted['jobs']]

print("="*80)
print("WAITING FOR TRAINING COMPLETION")
print("="*80)
print(f"Target: {len(target_models)} models\n")

start_wait = datetime.now()
max_wait_minutes = 45

while True:
    completed_models = []
    
    for name in target_models:
        try:
            client.get_model(f'cbi-v14.models.{name}')
            completed_models.append(name)
        except:
            pass
    
    elapsed = (datetime.now() - start_wait).total_seconds() / 60
    pct = (len(completed_models) / len(target_models)) * 100
    
    print(f"\r[{datetime.now().strftime('%H:%M:%S')}] {len(completed_models)}/16 complete ({pct:.0f}%) - Elapsed: {elapsed:.1f} min", end='', flush=True)
    
    if len(completed_models) >= 16:
        print("\n\n✅ ALL MODELS COMPLETE!")
        break
    
    if elapsed > max_wait_minutes:
        print(f"\n\n⏰ Timeout after {max_wait_minutes} minutes")
        break
    
    time.sleep(10)

# Generate final summary
print("\n" + "="*80)
print("GENERATING FINAL EVALUATION SUMMARY")
print("="*80)

results_by_horizon = {}

for horizon in ['1w', '1m', '3m', '6m']:
    results_by_horizon[horizon] = []
    
    for job_info in submitted['jobs']:
        if job_info['horizon'] == horizon:
            name = job_info['name']
            model_type = job_info['type']
            
            try:
                model = client.get_model(f'cbi-v14.models.{name}')
                
                # Get evaluation metrics
                eval_query = f"SELECT * FROM ML.EVALUATE(MODEL `cbi-v14.models.{name}`)"
                eval_df = client.query(eval_query).to_dataframe()
                
                if len(eval_df) > 0:
                    mae = eval_df.mean_absolute_error.values[0] if 'mean_absolute_error' in eval_df.columns else None
                    rmse = (eval_df.mean_squared_error.values[0] ** 0.5) if 'mean_squared_error' in eval_df.columns else None
                    r2 = eval_df.r2_score.values[0] if 'r2_score' in eval_df.columns else None
                    
                    results_by_horizon[horizon].append({
                        'name': name,
                        'type': model_type,
                        'mae': mae,
                        'rmse': rmse,
                        'r2': r2,
                        'status': 'SUCCESS'
                    })
                else:
                    results_by_horizon[horizon].append({
                        'name': name,
                        'type': model_type,
                        'status': 'NO_EVAL'
                    })
            except Exception as e:
                results_by_horizon[horizon].append({
                    'name': name,
                    'type': model_type,
                    'status': 'FAILED',
                    'error': str(e)[:100]
                })

# Print results
print("\n📊 FINAL RESULTS BY HORIZON:\n")

for horizon in ['1w', '1m', '3m', '6m']:
    print(f"\n{horizon} Forecast ({horizon.replace('w','week').replace('m','month')}):")
    print("-" * 80)
    
    horizon_results = results_by_horizon[horizon]
    valid_results = [r for r in horizon_results if r['status'] == 'SUCCESS' and r.get('mae')]
    
    if valid_results:
        # Sort by MAE
        valid_results.sort(key=lambda x: x['mae'])
        
        for r in valid_results:
            print(f"  {r['name']:35s} MAE: {r['mae']:8.4f}  RMSE: {r['rmse']:8.4f}  R²: {r.get('r2', 0):8.4f}")
        
        best = valid_results[0]
        print(f"\n  🏆 BEST: {best['name']} (MAE: {best['mae']:.4f})")
    else:
        print("  ⏳ Evaluation pending...")

# Save complete results
with open('logs/final_training_results.json', 'w') as f:
    json.dump({
        'timestamp': datetime.now().isoformat(),
        'total_models': len(target_models),
        'completed': len(completed_models),
        'results_by_horizon': results_by_horizon
    }, f, indent=2, default=str)

print("\n" + "="*80)
print("✅ Results saved to: logs/final_training_results.json")
print("="*80)










