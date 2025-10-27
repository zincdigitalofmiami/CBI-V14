#!/usr/bin/env python3
"""
RETRAIN MODELS WITH FIXED MODEL TYPES
Fixed LINEAR_REGRESSION -> LINEAR_REG and other issues
"""

from google.cloud import bigquery
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print(f"RETRAINING MODELS (FIXED) - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# Models that failed - retrain with correct syntax
models_to_train = [
    # Boosted Trees
    {
        'name': 'zl_boosted_tree_1w_production_v2',
        'target': 'target_1w',
        'query': """
        CREATE OR REPLACE MODEL `cbi-v14.models.zl_boosted_tree_1w_production_v2`
        OPTIONS(
            model_type='BOOSTED_TREE_REGRESSOR',
            input_label_cols=['target_1w'],
            max_iterations=100,
            early_stop=TRUE,
            min_tree_child_weight=10,
            subsample=0.8,
            max_tree_depth=10
        ) AS
        SELECT 
            * EXCEPT(date, target_1m, target_3m, target_6m)
        FROM `cbi-v14.models.training_dataset`
        WHERE target_1w IS NOT NULL
        """
    },
    {
        'name': 'zl_boosted_tree_1m_production_v2',
        'target': 'target_1m',
        'query': """
        CREATE OR REPLACE MODEL `cbi-v14.models.zl_boosted_tree_1m_production_v2`
        OPTIONS(
            model_type='BOOSTED_TREE_REGRESSOR',
            input_label_cols=['target_1m'],
            max_iterations=100,
            early_stop=TRUE,
            min_tree_child_weight=10,
            subsample=0.8,
            max_tree_depth=10
        ) AS
        SELECT 
            * EXCEPT(date, target_1w, target_3m, target_6m)
        FROM `cbi-v14.models.training_dataset`
        WHERE target_1m IS NOT NULL
        """
    },
    {
        'name': 'zl_boosted_tree_3m_production_v2',
        'target': 'target_3m',
        'query': """
        CREATE OR REPLACE MODEL `cbi-v14.models.zl_boosted_tree_3m_production_v2`
        OPTIONS(
            model_type='BOOSTED_TREE_REGRESSOR',
            input_label_cols=['target_3m'],
            max_iterations=100,
            early_stop=TRUE,
            min_tree_child_weight=10,
            subsample=0.8,
            max_tree_depth=10
        ) AS
        SELECT 
            * EXCEPT(date, target_1w, target_1m, target_6m)
        FROM `cbi-v14.models.training_dataset`
        WHERE target_3m IS NOT NULL
        """
    },
    {
        'name': 'zl_boosted_tree_6m_production_v2',
        'target': 'target_6m',
        'query': """
        CREATE OR REPLACE MODEL `cbi-v14.models.zl_boosted_tree_6m_production_v2`
        OPTIONS(
            model_type='BOOSTED_TREE_REGRESSOR',
            input_label_cols=['target_6m'],
            max_iterations=100,
            early_stop=TRUE,
            min_tree_child_weight=10,
            subsample=0.8,
            max_tree_depth=10
        ) AS
        SELECT 
            * EXCEPT(date, target_1w, target_1m, target_3m)
        FROM `cbi-v14.models.training_dataset`
        WHERE target_6m IS NOT NULL
        """
    },
    # DNN Models (simplified)
    {
        'name': 'zl_dnn_1w_production_v2',
        'target': 'target_1w',
        'query': """
        CREATE OR REPLACE MODEL `cbi-v14.models.zl_dnn_1w_production_v2`
        OPTIONS(
            model_type='DNN_REGRESSOR',
            input_label_cols=['target_1w'],
            hidden_units=[64, 32, 16],
            activation_fn='RELU',
            dropout=0.2,
            batch_size=32,
            learn_rate=0.001,
            max_iterations=100
        ) AS
        SELECT 
            * EXCEPT(date, target_1m, target_3m, target_6m)
        FROM `cbi-v14.models.training_dataset`
        WHERE target_1w IS NOT NULL
        """
    },
    {
        'name': 'zl_dnn_1m_production_v2',
        'target': 'target_1m',
        'query': """
        CREATE OR REPLACE MODEL `cbi-v14.models.zl_dnn_1m_production_v2`
        OPTIONS(
            model_type='DNN_REGRESSOR',
            input_label_cols=['target_1m'],
            hidden_units=[64, 32, 16],
            activation_fn='RELU',
            dropout=0.2,
            batch_size=32,
            learn_rate=0.001,
            max_iterations=100
        ) AS
        SELECT 
            * EXCEPT(date, target_1w, target_3m, target_6m)
        FROM `cbi-v14.models.training_dataset`
        WHERE target_1m IS NOT NULL
        """
    },
    # Linear Models (FIXED: LINEAR_REG not LINEAR_REGRESSION)
    {
        'name': 'zl_linear_production_1w_v2',
        'target': 'target_1w',
        'query': """
        CREATE OR REPLACE MODEL `cbi-v14.models.zl_linear_production_1w_v2`
        OPTIONS(
            model_type='LINEAR_REG',
            input_label_cols=['target_1w'],
            optimize_strategy='AUTO_STRATEGY'
        ) AS
        SELECT 
            * EXCEPT(date, target_1m, target_3m, target_6m)
        FROM `cbi-v14.models.training_dataset`
        WHERE target_1w IS NOT NULL
        """
    },
    {
        'name': 'zl_linear_production_1m_v2',
        'target': 'target_1m',
        'query': """
        CREATE OR REPLACE MODEL `cbi-v14.models.zl_linear_production_1m_v2`
        OPTIONS(
            model_type='LINEAR_REG',
            input_label_cols=['target_1m'],
            optimize_strategy='AUTO_STRATEGY'
        ) AS
        SELECT 
            * EXCEPT(date, target_1w, target_3m, target_6m)
        FROM `cbi-v14.models.training_dataset`
        WHERE target_1m IS NOT NULL
        """
    }
]

print(f"Submitting {len(models_to_train)} model training jobs...")
print("-"*80)

job_ids = []
for model in models_to_train:
    print(f"\nTraining {model['name']}...")
    print(f"  Target: {model['target']}")
    
    try:
        job = client.query(model['query'])
        job_ids.append((model['name'], job.job_id))
        print(f"  ✓ Job submitted: {job.job_id}")
    except Exception as e:
        print(f"  ✗ Error: {str(e)[:100]}")

print("\n" + "="*80)
print("TRAINING JOBS SUBMITTED")
print("="*80)

print(f"\nSubmitted {len(job_ids)} jobs successfully")
print("\nModels training:")
for name, job_id in job_ids:
    print(f"  ✓ {name}")

print("\n" + "="*80)
print("EXPECTED TRAINING TIMES")
print("="*80)
print("  Boosted Trees: 5-10 minutes")
print("  DNN: 5-15 minutes")
print("  Linear: 1-2 minutes")
print("  ARIMA: Already completed")

print("\nTo monitor progress:")
print("  python3 scripts/monitor_training.py")
