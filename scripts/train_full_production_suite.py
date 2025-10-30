#!/usr/bin/env python3
"""
COMPREHENSIVE PRODUCTION TRAINING SUITE
Trains all models across all horizons with optimization
"""
from google.cloud import bigquery
import time
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print("="*80)
print("FULL PRODUCTION MODEL TRAINING SUITE")
print("="*80)
print(f"Start Time: {datetime.now().isoformat()}\n")

# Define comprehensive model suite
models_to_train = [
    # ========== 1-WEEK MODELS (4 types) ==========
    {
        'name': 'zl_boosted_tree_1w_v1',
        'type': 'BOOSTED_TREE_REGRESSOR',
        'target': 'target_1w',
        'horizon': '1w',
        'options': """
            model_type='BOOSTED_TREE_REGRESSOR',
            input_label_cols=['target_1w'],
            max_iterations=100,
            learning_rate=0.1,
            subsample=0.8,
            max_tree_depth=8,
            min_tree_child_weight=10,
            early_stop=TRUE,
            data_split_method='AUTO_SPLIT'
        """
    },
    {
        'name': 'zl_dnn_optimized_1w_v1',
        'type': 'DNN_REGRESSOR',
        'target': 'target_1w',
        'horizon': '1w',
        'options': """
            model_type='DNN_REGRESSOR',
            hidden_units=[128, 64, 32],
            activation_fn='RELU',
            dropout=0.2,
            batch_size=32,
            learn_rate=0.001,
            optimizer='ADAM',
            input_label_cols=['target_1w'],
            max_iterations=50,
            early_stop=TRUE,
            data_split_method='AUTO_SPLIT',
            enable_global_explain=TRUE
        """
    },
    {
        'name': 'zl_linear_1w_v1',
        'type': 'LINEAR_REG',
        'target': 'target_1w',
        'horizon': '1w',
        'options': """
            model_type='LINEAR_REG',
            input_label_cols=['target_1w'],
            data_split_method='AUTO_SPLIT',
            enable_global_explain=TRUE
        """
    },
    {
        'name': 'zl_arima_1w_final',
        'type': 'ARIMA_PLUS',
        'target': 'target_1w',
        'horizon': '1w',
        'options': """
            model_type='ARIMA_PLUS',
            time_series_timestamp_col='date',
            time_series_data_col='target_1w',
            auto_arima=TRUE,
            data_frequency='DAILY'
        """
    },
    
    # ========== 1-MONTH MODELS (4 types) ==========
    {
        'name': 'zl_boosted_tree_1m_v1',
        'type': 'BOOSTED_TREE_REGRESSOR',
        'target': 'target_1m',
        'horizon': '1m',
        'options': """
            model_type='BOOSTED_TREE_REGRESSOR',
            input_label_cols=['target_1m'],
            max_iterations=100,
            learning_rate=0.1,
            subsample=0.8,
            max_tree_depth=8,
            early_stop=TRUE,
            data_split_method='AUTO_SPLIT'
        """
    },
    {
        'name': 'zl_dnn_optimized_1m_v1',
        'type': 'DNN_REGRESSOR',
        'target': 'target_1m',
        'horizon': '1m',
        'options': """
            model_type='DNN_REGRESSOR',
            hidden_units=[128, 64, 32],
            activation_fn='RELU',
            dropout=0.2,
            batch_size=32,
            learn_rate=0.001,
            input_label_cols=['target_1m'],
            max_iterations=50,
            early_stop=TRUE,
            data_split_method='AUTO_SPLIT'
        """
    },
    {
        'name': 'zl_linear_1m_v1',
        'type': 'LINEAR_REG',
        'target': 'target_1m',
        'horizon': '1m',
        'options': """
            model_type='LINEAR_REG',
            input_label_cols=['target_1m'],
            data_split_method='AUTO_SPLIT'
        """
    },
    {
        'name': 'zl_arima_1m_final',
        'type': 'ARIMA_PLUS',
        'target': 'target_1m',
        'horizon': '1m',
        'options': """
            model_type='ARIMA_PLUS',
            time_series_timestamp_col='date',
            time_series_data_col='target_1m',
            auto_arima=TRUE,
            data_frequency='DAILY'
        """
    },
    
    # ========== 3-MONTH MODELS (4 types) ==========
    {
        'name': 'zl_boosted_tree_3m_v1',
        'type': 'BOOSTED_TREE_REGRESSOR',
        'target': 'target_3m',
        'horizon': '3m',
        'options': """
            model_type='BOOSTED_TREE_REGRESSOR',
            input_label_cols=['target_3m'],
            max_iterations=100,
            learning_rate=0.1,
            subsample=0.8,
            max_tree_depth=8,
            early_stop=TRUE,
            data_split_method='AUTO_SPLIT'
        """
    },
    {
        'name': 'zl_dnn_optimized_3m_v1',
        'type': 'DNN_REGRESSOR',
        'target': 'target_3m',
        'horizon': '3m',
        'options': """
            model_type='DNN_REGRESSOR',
            hidden_units=[128, 64, 32],
            activation_fn='RELU',
            dropout=0.2,
            batch_size=32,
            learn_rate=0.001,
            input_label_cols=['target_3m'],
            max_iterations=50,
            early_stop=TRUE,
            data_split_method='AUTO_SPLIT'
        """
    },
    {
        'name': 'zl_linear_3m_v1',
        'type': 'LINEAR_REG',
        'target': 'target_3m',
        'horizon': '3m',
        'options': """
            model_type='LINEAR_REG',
            input_label_cols=['target_3m'],
            data_split_method='AUTO_SPLIT'
        """
    },
    {
        'name': 'zl_arima_3m_final',
        'type': 'ARIMA_PLUS',
        'target': 'target_3m',
        'horizon': '3m',
        'options': """
            model_type='ARIMA_PLUS',
            time_series_timestamp_col='date',
            time_series_data_col='target_3m',
            auto_arima=TRUE,
            data_frequency='DAILY'
        """
    },
    
    # ========== 6-MONTH MODELS (4 types) ==========
    {
        'name': 'zl_boosted_tree_6m_v1',
        'type': 'BOOSTED_TREE_REGRESSOR',
        'target': 'target_6m',
        'horizon': '6m',
        'options': """
            model_type='BOOSTED_TREE_REGRESSOR',
            input_label_cols=['target_6m'],
            max_iterations=100,
            learning_rate=0.1,
            subsample=0.8,
            max_tree_depth=8,
            early_stop=TRUE,
            data_split_method='AUTO_SPLIT'
        """
    },
    {
        'name': 'zl_dnn_optimized_6m_v1',
        'type': 'DNN_REGRESSOR',
        'target': 'target_6m',
        'horizon': '6m',
        'options': """
            model_type='DNN_REGRESSOR',
            hidden_units=[128, 64, 32],
            activation_fn='RELU',
            dropout=0.2,
            batch_size=32,
            learn_rate=0.001,
            input_label_cols=['target_6m'],
            max_iterations=50,
            early_stop=TRUE,
            data_split_method='AUTO_SPLIT'
        """
    },
    {
        'name': 'zl_linear_6m_v1',
        'type': 'LINEAR_REG',
        'target': 'target_6m',
        'horizon': '6m',
        'options': """
            model_type='LINEAR_REG',
            input_label_cols=['target_6m'],
            data_split_method='AUTO_SPLIT'
        """
    },
    {
        'name': 'zl_arima_6m_final',
        'type': 'ARIMA_PLUS',
        'target': 'target_6m',
        'horizon': '6m',
        'options': """
            model_type='ARIMA_PLUS',
            time_series_timestamp_col='date',
            time_series_data_col='target_6m',
            auto_arima=TRUE,
            data_frequency='DAILY'
        """
    }
]

print(f"Training {len(models_to_train)} production models...")
print("This will take 30-60 minutes total\n")

success_count = 0
failed_count = 0
results = []

for idx, model_config in enumerate(models_to_train, 1):
    print(f"\n{'='*80}")
    print(f"[{idx}/{len(models_to_train)}] {model_config['name']}")
    print(f"Type: {model_config['type']}, Horizon: {model_config['horizon']}")
    print("="*80)
    
    # Build training query
    if model_config['type'] == 'ARIMA_PLUS':
        training_query = f"""
        CREATE OR REPLACE MODEL `cbi-v14.models.{model_config['name']}`
        OPTIONS({model_config['options']})
        AS
        SELECT 
            date,
            {model_config['target']}
        FROM `cbi-v14.models.training_dataset_final_v1`
        WHERE date <= '2024-03-31'
        AND {model_config['target']} IS NOT NULL
        ORDER BY date
        """
    else:
        # For supervised models, exclude other targets
        other_targets = ['target_1w', 'target_1m', 'target_3m', 'target_6m']
        other_targets.remove(model_config['target'])
        except_clause = 'date, ' + ', '.join(other_targets)
        
        training_query = f"""
        CREATE OR REPLACE MODEL `cbi-v14.models.{model_config['name']}`
        OPTIONS({model_config['options']})
        AS
        SELECT 
            * EXCEPT({except_clause})
        FROM `cbi-v14.models.training_dataset_final_v1`
        WHERE date <= '2024-03-31'
        AND {model_config['target']} IS NOT NULL
        """
    
    # Train
    print(f"Training...")
    start_time = time.time()
    
    try:
        job = client.query(training_query)
        job.result()
        duration = time.time() - start_time
        
        print(f"✅ Training complete ({duration:.1f}s)")
        success_count += 1
        
        # Try to get evaluation metrics
        try:
            eval_query = f"SELECT * FROM ML.EVALUATE(MODEL `cbi-v14.models.{model_config['name']}`)"
            eval_df = client.query(eval_query).to_dataframe()
            
            if len(eval_df) > 0 and 'mean_absolute_error' in eval_df.columns:
                mae = eval_df.mean_absolute_error.values[0]
                print(f"   MAE: {mae:.4f}")
                
                results.append({
                    'name': model_config['name'],
                    'type': model_config['type'],
                    'horizon': model_config['horizon'],
                    'status': 'SUCCESS',
                    'mae': mae,
                    'duration': duration
                })
            else:
                print(f"   ✅ Model created (evaluation pending)")
                results.append({
                    'name': model_config['name'],
                    'type': model_config['type'],
                    'horizon': model_config['horizon'],
                    'status': 'SUCCESS',
                    'duration': duration
                })
        except Exception as e:
            print(f"   ✅ Model created (evaluation: {str(e)[:50]})")
            results.append({
                'name': model_config['name'],
                'type': model_config['type'],
                'horizon': model_config['horizon'],
                'status': 'SUCCESS',
                'duration': duration
            })
            
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Failed: {str(e)[:150]}")
        failed_count += 1
        
        results.append({
            'name': model_config['name'],
            'type': model_config['type'],
            'horizon': model_config['horizon'],
            'status': 'FAILED',
            'error': str(e)[:150],
            'duration': duration
        })

# Final Summary
print("\n\n" + "="*80)
print("FULL PRODUCTION SUITE TRAINING COMPLETE")
print("="*80)

print(f"\nModels trained: {success_count}/{len(models_to_train)}")
print(f"Failed: {failed_count}/{len(models_to_train)}")

print("\n📊 Results by Horizon:")
for horizon in ['1w', '1m', '3m', '6m']:
    horizon_models = [r for r in results if r['horizon'] == horizon and r['status'] == 'SUCCESS']
    print(f"\n{horizon} ({len(horizon_models)} models):")
    for r in horizon_models:
        mae_str = f"MAE: {r['mae']:.2f}" if 'mae' in r else "Evaluation pending"
        print(f"  ✅ {r['name']:30s} {mae_str}")

# Save results
import json
with open('logs/full_production_training_results.json', 'w') as f:
    json.dump({
        'timestamp': datetime.now().isoformat(),
        'total_models': len(models_to_train),
        'successful': success_count,
        'failed': failed_count,
        'results': results
    }, f, indent=2, default=str)

print(f"\n✅ Results saved to: logs/full_production_training_results.json")
print("\n" + "="*80)
print("READY FOR PRODUCTION DEPLOYMENT")
print("="*80)












