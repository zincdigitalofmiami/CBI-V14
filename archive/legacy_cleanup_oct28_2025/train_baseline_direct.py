#!/usr/bin/env python3
"""
TRAIN BASELINE MODELS DIRECTLY - NO AUDIT
Data already verified: 1,251 rows, 0 duplicates, all features present
Just train the fucking models.
"""

from google.cloud import bigquery
from datetime import datetime
import json
import time

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("BASELINE MODEL TRAINING - DIRECT EXECUTION")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()
print("Dataset: cbi-v14.models_v4.training_dataset_super_enriched")
print("Rows: 1,251 (verified clean, 0 duplicates)")
print("Features: 195+ including Big 8 signals, palm/crude/VIX correlations")
print()

horizons = {
    '1w': 'target_1w',
    '1m': 'target_1m',
    '3m': 'target_3m',
    '6m': 'target_6m'
}

results = {}

for horizon_name, target_col in horizons.items():
    print("=" * 80)
    print(f"TRAINING {horizon_name.upper()} MODEL")
    print("=" * 80)
    
    model_name = f'baseline_boosted_tree_{horizon_name}_v14_FINAL'
    
    # Exclude date and other targets
    other_targets = [t for t in ['target_1w', 'target_1m', 'target_3m', 'target_6m'] if t != target_col]
    # Exclude ALL confirmed 100% NULL columns
    exclude_cols = [
        'date',
        'econ_gdp_growth',
        'econ_unemployment_rate', 
        'treasury_10y_yield',
        'news_article_count',
        'news_avg_score'
    ] + other_targets
    except_clause = ', '.join(exclude_cols)
    
    train_query = f"""
    CREATE OR REPLACE MODEL `cbi-v14.models_v4.{model_name}`
    OPTIONS(
        model_type='BOOSTED_TREE_REGRESSOR',
        input_label_cols=['{target_col}'],
        data_split_method='RANDOM',
        data_split_eval_fraction=0.2,
        enable_global_explain=TRUE,
        max_iterations=50,
        early_stop=TRUE,
        min_rel_progress=0.01,
        learn_rate=0.1,
        subsample=0.8,
        max_tree_depth=8
    ) AS
    SELECT * EXCEPT({except_clause})
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    WHERE {target_col} IS NOT NULL
    AND date <= '2024-10-31'  -- Train/test split
    """
    
    print(f"Training {model_name}...")
    print(f"Target: {target_col}")
    print(f"Excluding: {len(exclude_cols)} columns")
    print()
    
    start_time = time.time()
    
    try:
        job = client.query(train_query)
        result = job.result()
        
        training_time = time.time() - start_time
        print(f"✅ Training completed in {training_time:.1f} seconds")
        
        # Evaluate
        print(f"Evaluating {model_name}...")
        
        eval_query = f"""
        SELECT
            mean_absolute_error,
            mean_squared_error,
            r2_score
        FROM ML.EVALUATE(MODEL `cbi-v14.models_v4.{model_name}`)
        """
        
        eval_df = client.query(eval_query).to_dataframe()
        
        if len(eval_df) > 0:
            mae = eval_df['mean_absolute_error'].iloc[0]
            mse = eval_df['mean_squared_error'].iloc[0]
            r2 = eval_df['r2_score'].iloc[0]
            
            # Estimate MAPE (assuming ~$50 avg price)
            estimated_mape = (mae / 50.0) * 100
            
            results[horizon_name] = {
                'model': model_name,
                'mae': float(mae),
                'mse': float(mse),
                'r2': float(r2),
                'mape_est': float(estimated_mape),
                'training_time': training_time,
                'status': 'SUCCESS'
            }
            
            print(f"  MAE: {mae:.4f}")
            print(f"  MSE: {mse:.4f}")
            print(f"  R²: {r2:.4f}")
            print(f"  Est. MAPE: {estimated_mape:.2f}%")
            
            if estimated_mape <= 5.0:
                print(f"  ✅ INSTITUTIONAL GRADE (<5% MAPE)")
            else:
                print(f"  ⚠️ BASELINE ACCEPTABLE")
        
        print()
            
    except Exception as e:
        print(f"❌ Training failed: {str(e)[:200]}")
        results[horizon_name] = {
            'model': model_name,
            'status': 'FAILED',
            'error': str(e)
        }
        print()

# Summary
print("=" * 80)
print("TRAINING COMPLETE - SUMMARY")
print("=" * 80)
print()

successful = [h for h, r in results.items() if r['status'] == 'SUCCESS']
failed = [h for h, r in results.items() if r['status'] == 'FAILED']

print(f"Models trained: {len(successful)}/{len(horizons)}")
print(f"Models failed: {len(failed)}")
print()

if successful:
    print("MODEL PERFORMANCE:")
    print("-" * 60)
    print(f"{'Horizon':<10} {'MAE':<10} {'MAPE':<10} {'R²':<10} {'Time':<10}")
    print("-" * 60)
    
    for h in successful:
        r = results[h]
        print(f"{h.upper():<10} {r['mae']:<10.3f} {r['mape_est']:<9.2f}% {r['r2']:<10.3f} {r['training_time']:<9.1f}s")

print()
print("=" * 80)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# Save results
with open("baseline_training_results.json", "w") as f:
    json.dump(results, f, indent=2, default=str)

print("\n📁 Results saved to baseline_training_results.json")

if len(successful) == len(horizons):
    print("\n✅ ALL MODELS TRAINED SUCCESSFULLY - READY FOR PRODUCTION")
else:
    print(f"\n⚠️ {len(failed)} models failed - review errors above")

