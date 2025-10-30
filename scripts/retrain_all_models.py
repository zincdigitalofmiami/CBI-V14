#!/usr/bin/env python3
"""
RETRAIN ALL MODELS WITH COMPLETE 172-FEATURE DATASET
Using the enhanced training dataset with CFTC, Treasury, Economic indicators, etc.
"""

from google.cloud import bigquery
from datetime import datetime
import time

client = bigquery.Client(project='cbi-v14')

print(f"RETRAINING ALL MODELS WITH COMPLETE FEATURES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)
print("Using enhanced training dataset with 172 features")
print("="*80)

# Define all models to train
models_to_train = [
    # Boosted Trees (BEST PERFORMERS)
    {
        'name': 'zl_boosted_tree_1w_production_v2',
        'type': 'BOOSTED_TREE_REGRESSOR',
        'target': 'target_1w',
        'options': {
            'max_iterations': 100,
            'early_stop': True,
            'min_tree_child_weight': 10,
            'subsample': 0.8,
            'max_tree_depth': 10,
            'l1_reg': 0.1,
            'l2_reg': 0.1
        }
    },
    {
        'name': 'zl_boosted_tree_1m_production_v2',
        'type': 'BOOSTED_TREE_REGRESSOR',
        'target': 'target_1m',
        'options': {
            'max_iterations': 100,
            'early_stop': True,
            'min_tree_child_weight': 10,
            'subsample': 0.8,
            'max_tree_depth': 10,
            'l1_reg': 0.1,
            'l2_reg': 0.1
        }
    },
    {
        'name': 'zl_boosted_tree_3m_production_v2',
        'type': 'BOOSTED_TREE_REGRESSOR',
        'target': 'target_3m',
        'options': {
            'max_iterations': 100,
            'early_stop': True,
            'min_tree_child_weight': 10,
            'subsample': 0.8,
            'max_tree_depth': 10,
            'l1_reg': 0.1,
            'l2_reg': 0.1
        }
    },
    {
        'name': 'zl_boosted_tree_6m_production_v2',
        'type': 'BOOSTED_TREE_REGRESSOR',
        'target': 'target_6m',
        'options': {
            'max_iterations': 100,
            'early_stop': True,
            'min_tree_child_weight': 10,
            'subsample': 0.8,
            'max_tree_depth': 10,
            'l1_reg': 0.1,
            'l2_reg': 0.1
        }
    },
    # DNN Models (with normalization)
    {
        'name': 'zl_dnn_1w_production_v2',
        'type': 'DNN_REGRESSOR',
        'target': 'target_1w',
        'options': {
            'hidden_units': [128, 64, 32],
            'activation_fn': 'RELU',
            'dropout': 0.2,
            'batch_size': 32,
            'learn_rate': 0.001,
            'optimizer': 'ADAM',
            'max_iterations': 200,
            'early_stop': True,
            'min_rel_progress': 0.0001
        }
    },
    {
        'name': 'zl_dnn_1m_production_v2',
        'type': 'DNN_REGRESSOR',
        'target': 'target_1m',
        'options': {
            'hidden_units': [128, 64, 32],
            'activation_fn': 'RELU',
            'dropout': 0.2,
            'batch_size': 32,
            'learn_rate': 0.001,
            'optimizer': 'ADAM',
            'max_iterations': 200,
            'early_stop': True,
            'min_rel_progress': 0.0001
        }
    },
    {
        'name': 'zl_dnn_3m_production_v2',
        'type': 'DNN_REGRESSOR',
        'target': 'target_3m',
        'options': {
            'hidden_units': [128, 64, 32],
            'activation_fn': 'RELU',
            'dropout': 0.2,
            'batch_size': 32,
            'learn_rate': 0.001,
            'optimizer': 'ADAM',
            'max_iterations': 200,
            'early_stop': True,
            'min_rel_progress': 0.0001
        }
    },
    {
        'name': 'zl_dnn_6m_production_v2',
        'type': 'DNN_REGRESSOR',
        'target': 'target_6m',
        'options': {
            'hidden_units': [128, 64, 32],
            'activation_fn': 'RELU',
            'dropout': 0.2,
            'batch_size': 32,
            'learn_rate': 0.001,
            'optimizer': 'ADAM',
            'max_iterations': 200,
            'early_stop': True,
            'min_rel_progress': 0.0001
        }
    },
    # ARIMA Models
    {
        'name': 'zl_arima_production_1w_v2',
        'type': 'ARIMA_PLUS',
        'target': 'target_1w',
        'options': {
            'time_series_timestamp_col': 'date',
            'time_series_data_col': 'target_1w',
            'auto_arima': True,
            'data_frequency': 'DAILY',
            'decompose_time_series': True,
            'clean_spikes_and_dips': True,
            'adjust_step_changes': True,
            'holiday_region': 'US'
        }
    },
    {
        'name': 'zl_arima_production_1m_v2',
        'type': 'ARIMA_PLUS',
        'target': 'target_1m',
        'options': {
            'time_series_timestamp_col': 'date',
            'time_series_data_col': 'target_1m',
            'auto_arima': True,
            'data_frequency': 'DAILY',
            'decompose_time_series': True,
            'clean_spikes_and_dips': True,
            'adjust_step_changes': True,
            'holiday_region': 'US'
        }
    },
    # Linear Models (baselines)
    {
        'name': 'zl_linear_production_1w_v2',
        'type': 'LINEAR_REGRESSION',
        'target': 'target_1w',
        'options': {
            'optimize_strategy': 'AUTO_STRATEGY',
            'l1_reg': 0.1,
            'l2_reg': 0.1
        }
    },
    {
        'name': 'zl_linear_production_1m_v2',
        'type': 'LINEAR_REGRESSION',
        'target': 'target_1m',
        'options': {
            'optimize_strategy': 'AUTO_STRATEGY',
            'l1_reg': 0.1,
            'l2_reg': 0.1
        }
    }
]

# Track job IDs
job_ids = []
successful_models = []
failed_models = []

print(f"\nSubmitting {len(models_to_train)} model training jobs...")
print("-"*80)

for model in models_to_train:
    model_name = model['name']
    model_type = model['type']
    target = model['target']
    options = model['options']
    
    print(f"\nTraining {model_name} ({model_type})...")
    print(f"  Target: {target}")
    
    # Build OPTIONS clause
    options_str = []
    for key, value in options.items():
        if isinstance(value, bool):
            options_str.append(f"{key}={str(value).upper()}")
        elif isinstance(value, str):
            options_str.append(f"{key}='{value}'")
        elif isinstance(value, list):
            options_str.append(f"{key}={value}")
        else:
            options_str.append(f"{key}={value}")
    
    options_clause = f"OPTIONS(\n    model_type='{model_type}',\n    input_label_cols=['{target}'],\n    " + ',\n    '.join(options_str) + "\n)"
    
    # Build query based on model type
    if model_type == 'ARIMA_PLUS':
        # ARIMA needs only date and target
        query = f"""
        CREATE OR REPLACE MODEL `cbi-v14.models.{model_name}`
        OPTIONS(
            model_type='ARIMA_PLUS',
            time_series_timestamp_col='date',
            time_series_data_col='{target}',
            auto_arima=TRUE,
            data_frequency='DAILY',
            decompose_time_series=TRUE,
            clean_spikes_and_dips=TRUE,
            adjust_step_changes=TRUE,
            holiday_region='US'
        ) AS
        SELECT 
            date,
            {target}
        FROM `cbi-v14.models.training_dataset`
        WHERE {target} IS NOT NULL
        ORDER BY date
        """
    elif model_type == 'DNN_REGRESSOR':
        # DNN with feature normalization
        query = f"""
        CREATE OR REPLACE MODEL `cbi-v14.models.{model_name}`
        TRANSFORM(
            -- Normalize price features to 0-1 range
            (zl_price_current - 30) / 30 AS zl_price_normalized,
            SAFE_DIVIDE(zl_volume, 10000) AS volume_normalized,
            -- Keep correlations as-is (already -1 to 1)
            corr_zl_crude_30d,
            corr_zl_palm_30d,
            corr_zl_corn_30d,
            corr_zl_dxy_30d,
            -- Normalize VIX
            SAFE_DIVIDE(vix_level, 100) AS vix_normalized,
            -- Normalize economic indicators
            SAFE_DIVIDE(econ_gdp_growth, 10) AS gdp_normalized,
            SAFE_DIVIDE(econ_inflation_rate, 10) AS inflation_normalized,
            SAFE_DIVIDE(econ_unemployment_rate, 20) AS unemployment_normalized,
            -- CFTC features
            SAFE_DIVIDE(cftc_spec_net_pct, 100) AS cftc_spec_normalized,
            SAFE_DIVIDE(cftc_comm_net_pct, 100) AS cftc_comm_normalized,
            -- Keep target
            {target}
        )
        {options_clause} AS
        SELECT 
            zl_price_current,
            zl_volume,
            corr_zl_crude_30d,
            corr_zl_palm_30d,
            corr_zl_corn_30d,
            corr_zl_dxy_30d,
            vix_level,
            econ_gdp_growth,
            econ_inflation_rate,
            econ_unemployment_rate,
            SAFE_DIVIDE(cftc_managed_net, cftc_open_interest) * 100 AS cftc_spec_net_pct,
            SAFE_DIVIDE(cftc_commercial_net, cftc_open_interest) * 100 AS cftc_comm_net_pct,
            {target}
        FROM `cbi-v14.models.training_dataset`
        WHERE {target} IS NOT NULL
        """
    else:
        # Boosted Tree and Linear - use all features
        exclude_targets = [t for t in ['target_1w', 'target_1m', 'target_3m', 'target_6m'] if t != target]
        query = f"""
        CREATE OR REPLACE MODEL `cbi-v14.models.{model_name}`
        {options_clause} AS
        SELECT 
            * EXCEPT(date, {', '.join(exclude_targets)})
        FROM `cbi-v14.models.training_dataset`
        WHERE {target} IS NOT NULL
        """
    
    try:
        # Submit job
        job = client.query(query)
        job_ids.append((model_name, job.job_id, model_type))
        print(f"  ✓ Job submitted: {job.job_id}")
        
        # For quick models, wait briefly
        if model_type in ['LINEAR_REGRESSION']:
            time.sleep(2)
            
    except Exception as e:
        print(f"  ✗ Error submitting job: {str(e)[:100]}")
        failed_models.append((model_name, str(e)[:100]))

print("\n" + "="*80)
print("ALL TRAINING JOBS SUBMITTED")
print("="*80)

print(f"\nSubmitted {len(job_ids)} training jobs")
print(f"Failed to submit: {len(failed_models)}")

if job_ids:
    print("\nMonitoring training progress...")
    print("-"*80)
    
    # Wait a bit for jobs to start
    time.sleep(10)
    
    # Check status
    for model_name, job_id, model_type in job_ids:
        try:
            job = client.get_job(job_id)
            if job.state == 'DONE':
                if job.errors:
                    print(f"✗ {model_name}: FAILED - {job.errors[0]['message'][:50]}")
                    failed_models.append((model_name, job.errors[0]['message'][:50]))
                else:
                    print(f"✓ {model_name}: COMPLETED")
                    successful_models.append(model_name)
            else:
                print(f"⏳ {model_name}: {job.state}")
                successful_models.append(model_name)  # Assume will complete
        except Exception as e:
            print(f"? {model_name}: Unable to check status")

print("\n" + "="*80)
print("TRAINING SUMMARY")
print("="*80)

print(f"\nSuccessfully submitted: {len(successful_models)} models")
if successful_models:
    print("Models training:")
    for model in successful_models[:10]:
        print(f"  ✓ {model}")
    if len(successful_models) > 10:
        print(f"  ... and {len(successful_models)-10} more")

if failed_models:
    print(f"\nFailed: {len(failed_models)} models")
    for model, error in failed_models:
        print(f"  ✗ {model}: {error}")

print("\n" + "="*80)
print("NEXT STEPS")
print("="*80)
print("""
1. Wait 5-15 minutes for all models to complete training
2. Check model performance with ML.EVALUATE
3. The Boosted Tree models should show improved MAE with new features
4. Expected MAE < 1.0 with CFTC positioning and economic indicators

To check status:
  SELECT * FROM `cbi-v14.models.INFORMATION_SCHEMA.MODELS`
  WHERE model_name LIKE '%_v2'
  ORDER BY creation_time DESC

To evaluate:
  SELECT * FROM ML.EVALUATE(MODEL `cbi-v14.models.zl_boosted_tree_1w_production_v2`)
""")
