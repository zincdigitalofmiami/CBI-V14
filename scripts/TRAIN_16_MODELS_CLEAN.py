#!/usr/bin/env python3
"""
TRAIN 16 MODELS - 4 HORIZONS × 4 ALGORITHMS
Post-audit clean training on canonical vw_neural_training_dataset
"""

from google.cloud import bigquery
from datetime import datetime
import time

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("🚀 TRAINING 16 MODELS - INSTITUTIONAL GRADE")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Configuration
horizons = [
    ('1w', 'target_1w', 7),
    ('1m', 'target_1m', 30),
    ('3m', 'target_3m', 90),
    ('6m', 'target_6m', 180)
]

algorithms = ['dnn', 'lightgbm', 'linear', 'arima']

models_created = []
models_failed = []

# Train each combination
for horizon_name, target_col, days in horizons:
    print(f"\n{'='*70}")
    print(f"HORIZON: {horizon_name.upper()} ({days} days ahead)")
    print('='*70)
    
    for algo in algorithms:
        model_name = f"zl_{algo}_{horizon_name}_v1"
        print(f"\n  Training: {model_name}...")
        
        if algo == 'dnn':
            # Deep Neural Network
            hidden_units = [256, 128, 64] if days < 90 else [512, 256, 128, 64]
            query = f"""
            CREATE OR REPLACE MODEL `cbi-v14.models.{model_name}`
            OPTIONS(
                model_type='DNN_REGRESSOR',
                hidden_units={hidden_units},
                activation_fn='RELU',
                dropout=0.2,
                batch_size=64,
                learn_rate=0.001,
                optimizer='ADAM',
                input_label_cols=['{target_col}'],
                data_split_method='SEQ',
                data_split_col='date',
                max_iterations=200,
                early_stop=TRUE,
                min_rel_progress=0.001
            ) AS
            SELECT * EXCEPT(date, target_1w, target_1m, target_3m, target_6m)
            FROM `cbi-v14.models.vw_neural_training_dataset`
            WHERE {target_col} IS NOT NULL
            AND date >= '2020-01-01'
            """
            
        elif algo == 'lightgbm':
            # LightGBM (Boosted Trees)
            query = f"""
            CREATE OR REPLACE MODEL `cbi-v14.models.{model_name}`
            OPTIONS(
                model_type='BOOSTED_TREE_REGRESSOR',
                booster_type='GBTREE',
                num_parallel_tree=1,
                max_iterations=100,
                early_stop=TRUE,
                min_rel_progress=0.001,
                tree_method='HIST',
                subsample=0.8,
                colsample_bytree=0.8,
                max_tree_depth=6,
                min_tree_child_weight=3,
                l1_reg=0.1,
                l2_reg=1.0,
                learn_rate=0.1,
                input_label_cols=['{target_col}'],
                data_split_method='SEQ',
                data_split_col='date'
            ) AS
            SELECT * EXCEPT(date, target_1w, target_1m, target_3m, target_6m)
            FROM `cbi-v14.models.vw_neural_training_dataset`
            WHERE {target_col} IS NOT NULL
            AND date >= '2020-01-01'
            """
            
        elif algo == 'linear':
            # Linear Regression
            query = f"""
            CREATE OR REPLACE MODEL `cbi-v14.models.{model_name}`
            OPTIONS(
                model_type='LINEAR_REG',
                input_label_cols=['{target_col}'],
                data_split_method='SEQ',
                data_split_col='date',
                l2_reg=0.1,
                optimize_strategy='BATCH_GRADIENT_DESCENT',
                learn_rate_strategy='LINE_SEARCH',
                early_stop=TRUE,
                max_iterations=50
            ) AS
            SELECT * EXCEPT(date, target_1w, target_1m, target_3m, target_6m)
            FROM `cbi-v14.models.vw_neural_training_dataset`
            WHERE {target_col} IS NOT NULL
            AND date >= '2020-01-01'
            """
            
        elif algo == 'arima':
            # ARIMA Plus (time series)
            query = f"""
            CREATE OR REPLACE MODEL `cbi-v14.models.{model_name}`
            OPTIONS(
                model_type='ARIMA_PLUS',
                time_series_timestamp_col='date',
                time_series_data_col='{target_col}',
                auto_arima=TRUE,
                data_frequency='DAILY'
            ) AS
            SELECT 
                date,
                {target_col}
            FROM `cbi-v14.models.vw_neural_training_dataset`
            WHERE {target_col} IS NOT NULL
            AND date >= '2020-01-01'
            """
        
        try:
            start_time = time.time()
            client.query(query).result()
            elapsed = time.time() - start_time
            models_created.append(model_name)
            print(f"    ✅ {model_name} - Trained in {elapsed:.1f}s")
        except Exception as e:
            models_failed.append((model_name, str(e)[:100]))
            print(f"    ❌ {model_name}: {str(e)[:100]}")

# Summary
print("\n" + "=" * 80)
print("TRAINING COMPLETE")
print("=" * 80)
print(f"✅ Successfully trained: {len(models_created)}/{len(horizons) * len(algorithms)} models")
print(f"❌ Failed: {len(models_failed)}")

if models_created:
    print("\n✅ SUCCESSFULLY TRAINED:")
    for model in models_created:
        print(f"   • {model}")

if models_failed:
    print("\n❌ FAILED:")
    for model, error in models_failed:
        print(f"   • {model}: {error}")

print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")










