#!/usr/bin/env python3
"""
ASYNC PRODUCTION TRAINING - Submit all jobs at once
Much faster than sequential training
"""
from google.cloud import bigquery
from datetime import datetime
import time

client = bigquery.Client(project='cbi-v14')

print("="*80)
print("ASYNC PRODUCTION MODEL TRAINING")
print("="*80)
print(f"Start Time: {datetime.now().isoformat()}\n")

# Define all 16 models
models = [
    # 1-Week
    ('zl_boosted_tree_1w_v1', 'BOOSTED_TREE_REGRESSOR', 'target_1w', '1w',
     "max_iterations=100, learning_rate=0.1, subsample=0.8, max_tree_depth=8, early_stop=TRUE"),
    ('zl_dnn_1w_production', 'DNN_REGRESSOR', 'target_1w', '1w',
     "hidden_units=[128, 64, 32], dropout=0.2, batch_size=32, learn_rate=0.001, max_iterations=50, early_stop=TRUE"),
    ('zl_linear_production_1w', 'LINEAR_REG', 'target_1w', '1w', ""),
    ('zl_arima_production_1w', 'ARIMA_PLUS', 'target_1w', '1w', "auto_arima=TRUE, data_frequency='DAILY'"),
    
    # 1-Month
    ('zl_boosted_tree_1m_v1', 'BOOSTED_TREE_REGRESSOR', 'target_1m', '1m',
     "max_iterations=100, learning_rate=0.1, subsample=0.8, max_tree_depth=8, early_stop=TRUE"),
    ('zl_dnn_1m_production', 'DNN_REGRESSOR', 'target_1m', '1m',
     "hidden_units=[128, 64, 32], dropout=0.2, batch_size=32, learn_rate=0.001, max_iterations=50, early_stop=TRUE"),
    ('zl_linear_production_1m', 'LINEAR_REG', 'target_1m', '1m', ""),
    ('zl_arima_production_1m', 'ARIMA_PLUS', 'target_1m', '1m', "auto_arima=TRUE, data_frequency='DAILY'"),
    
    # 3-Month
    ('zl_boosted_tree_3m_v1', 'BOOSTED_TREE_REGRESSOR', 'target_3m', '3m',
     "max_iterations=100, learning_rate=0.1, subsample=0.8, max_tree_depth=8, early_stop=TRUE"),
    ('zl_dnn_3m_production', 'DNN_REGRESSOR', 'target_3m', '3m',
     "hidden_units=[128, 64, 32], dropout=0.2, batch_size=32, learn_rate=0.001, max_iterations=50, early_stop=TRUE"),
    ('zl_linear_production_3m', 'LINEAR_REG', 'target_3m', '3m', ""),
    ('zl_arima_production_3m', 'ARIMA_PLUS', 'target_3m', '3m', "auto_arima=TRUE, data_frequency='DAILY'"),
    
    # 6-Month  
    ('zl_boosted_tree_6m_v1', 'BOOSTED_TREE_REGRESSOR', 'target_6m', '6m',
     "max_iterations=100, learning_rate=0.1, subsample=0.8, max_tree_depth=8, early_stop=TRUE"),
    ('zl_dnn_6m_production', 'DNN_REGRESSOR', 'target_6m', '6m',
     "hidden_units=[128, 64, 32], dropout=0.2, batch_size=32, learn_rate=0.001, max_iterations=50, early_stop=TRUE"),
    ('zl_linear_production_6m', 'LINEAR_REG', 'target_6m', '6m', ""),
    ('zl_arima_production_6m', 'ARIMA_PLUS', 'target_6m', '6m', "auto_arima=TRUE, data_frequency='DAILY'")
]

print(f"Submitting {len(models)} training jobs asynchronously...")
print("Jobs will run in parallel - much faster than sequential\n")

submitted_jobs = []

for name, model_type, target, horizon, extra_opts in models:
    print(f"Submitting: {name:35s} ({model_type:25s} {horizon})")
    
    # Build query based on type
    if model_type == 'ARIMA_PLUS':
        query = f"""
        CREATE OR REPLACE MODEL `cbi-v14.models.{name}`
        OPTIONS(
            model_type='ARIMA_PLUS',
            time_series_timestamp_col='date',
            time_series_data_col='{target}',
            {extra_opts}
        ) AS
        SELECT date, {target}
        FROM `cbi-v14.models.training_dataset_final_v1`
        WHERE date <= '2024-03-31' AND {target} IS NOT NULL
        ORDER BY date
        """
    else:
        other_targets = [t for t in ['target_1w', 'target_1m', 'target_3m', 'target_6m'] if t != target]
        except_clause = 'date, ' + ', '.join(other_targets)
        
        opts = f"model_type='{model_type}', input_label_cols=['{target}'], data_split_method='AUTO_SPLIT'"
        if extra_opts:
            opts += ", " + extra_opts
        
        query = f"""
        CREATE OR REPLACE MODEL `cbi-v14.models.{name}`
        OPTIONS({opts})
        AS
        SELECT * EXCEPT({except_clause})
        FROM `cbi-v14.models.training_dataset_final_v1`
        WHERE date <= '2024-03-31' AND {target} IS NOT NULL
        """
    
    try:
        # Submit job without waiting
        job = client.query(query)
        submitted_jobs.append((name, job.job_id, model_type, horizon))
        print(f"   ✅ Job submitted: {job.job_id[:20]}...")
    except Exception as e:
        print(f"   ❌ Failed to submit: {str(e)[:80]}")

print(f"\n{'='*80}")
print(f"✅ {len(submitted_jobs)}/{len(models)} jobs submitted")
print("="*80)
print("\nJobs are now running in parallel in BigQuery.")
print("This will take 15-30 minutes (much faster than sequential 60+ min)")
print("\nMonitor with: bq ls --jobs cbi-v14")
print("Or run: python3 scripts/check_training_completion.py")

# Save job IDs
import json
with open('logs/submitted_training_jobs.json', 'w') as f:
    json.dump({
        'timestamp': datetime.now().isoformat(),
        'total_submitted': len(submitted_jobs),
        'jobs': [{'name': n, 'job_id': j, 'type': t, 'horizon': h} 
                 for n, j, t, h in submitted_jobs]
    }, f, indent=2)

print(f"\n📄 Job IDs saved to: logs/submitted_training_jobs.json")












