#!/usr/bin/env python3
"""
Train remaining enriched models (1m, 3m, 6m)
"""

from google.cloud import bigquery
from datetime import datetime
import time

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("🚀 TRAINING REMAINING ENRICHED MODELS")
print("=" * 80)
print()

horizons = [
    ('1m', 'target_1m'),
    ('3m', 'target_3m'),
    ('6m', 'target_6m')
]

for horizon, target in horizons:
    model_name = f"zl_boosted_tree_{horizon}_v3_enriched"
    
    print(f"Training: {model_name} at {datetime.now().strftime('%H:%M:%S')}")
    
    train_query = f"""
    CREATE OR REPLACE MODEL `cbi-v14.models.{model_name}`
    OPTIONS(
        model_type='BOOSTED_TREE_REGRESSOR',
        input_label_cols=['{target}'],
        data_split_method='RANDOM',
        data_split_eval_fraction=0.2,
        max_iterations=50,
        learn_rate=0.1,
        early_stop=TRUE,
        min_tree_child_weight=10,
        subsample=0.8,
        max_tree_depth=8
    ) AS
    SELECT * EXCEPT(date)
    FROM `cbi-v14.models.training_dataset`
    WHERE {target} IS NOT NULL;
    """
    
    try:
        job = client.query(train_query)
        job.result()
        print(f"   ✅ {model_name} trained successfully")
        
        # Evaluate immediately
        eval_query = f"""
        SELECT 
            mean_absolute_error,
            mean_squared_error,
            r2_score
        FROM ML.EVALUATE(
            MODEL `cbi-v14.models.{model_name}`,
            (SELECT * EXCEPT(date) FROM `cbi-v14.models.training_dataset` WHERE {target} IS NOT NULL)
        )
        LIMIT 1;
        """
        
        eval_df = client.query(eval_query).to_dataframe()
        
        if not eval_df.empty:
            mae = float(eval_df['mean_absolute_error'].iloc[0])
            r2 = float(eval_df['r2_score'].iloc[0])
            mape = (mae / 50.0) * 100
            
            print(f"   📊 MAE: {mae:.2f}, R²: {r2:.3f}, MAPE: {mape:.2f}%")
            
            if mape < 2.5:
                print(f"   ⭐⭐⭐ EXCELLENT!")
            elif mape < 3.5:
                print(f"   ⭐⭐ VERY GOOD!")
            else:
                print(f"   ⭐ GOOD")
        
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)}")
    
    print()
    time.sleep(1)

print("=" * 80)
print("✅ ALL ENRICHED MODELS TRAINED!")
print("=" * 80)

