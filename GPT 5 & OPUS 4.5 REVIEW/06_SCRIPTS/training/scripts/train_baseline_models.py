#!/usr/bin/env python3
"""
PHASE 1: BASELINE MODEL TRAINING
Establish performance floor with 3 baseline models
"""
from google.cloud import bigquery
import pandas as pd
from datetime import datetime
import time

client = bigquery.Client(project='cbi-v14')

print("="*80)
print("PHASE 1: BASELINE MODEL TRAINING")
print("="*80)
print(f"Start Time: {datetime.now().isoformat()}\n")

# Create experiment tracking table
print("Setting up experiment tracking...")
tracking_table_query = """
CREATE TABLE IF NOT EXISTS `cbi-v14.models.model_training_log` (
    experiment_id STRING,
    model_name STRING,
    model_type STRING,
    horizon STRING,
    hyperparameters JSON,
    training_start TIMESTAMP,
    training_end TIMESTAMP,
    training_duration_seconds FLOAT64,
    train_mae FLOAT64,
    train_rmse FLOAT64,
    train_r2 FLOAT64,
    val_mae FLOAT64,
    val_rmse FLOAT64,
    val_r2 FLOAT64,
    test_mae FLOAT64,
    test_rmse FLOAT64,
    test_r2 FLOAT64,
    feature_count INT64,
    training_rows INT64,
    notes STRING,
    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
"""
client.query(tracking_table_query).result()
print("✅ Tracking table ready\n")

# Define baseline models to train
baseline_models = [
    {
        'name': 'zl_arima_baseline_1w_v2',
        'type': 'ARIMA_PLUS',
        'horizon': '1w',
        'target': 'target_1w',
        'description': 'ARIMA Plus auto-tuned baseline for 1-week forecast'
    },
    {
        'name': 'zl_linear_baseline_1w_v2',
        'type': 'LINEAR_REG',
        'horizon': '1w',
        'target': 'target_1w',
        'description': 'Linear regression baseline for 1-week forecast'
    },
    {
        'name': 'zl_dnn_baseline_1w_v2',
        'type': 'DNN_REGRESSOR',
        'horizon': '1w',
        'target': 'target_1w',
        'description': 'Simple DNN (64,32) baseline for 1-week forecast'
    }
]

results = []

for idx, model_config in enumerate(baseline_models, 1):
    print(f"\n{'='*80}")
    print(f"[{idx}/{len(baseline_models)}] Training {model_config['name']}")
    print(f"Type: {model_config['type']}, Horizon: {model_config['horizon']}")
    print("="*80)
    
    # Build training query based on model type
    if model_config['type'] == 'ARIMA_PLUS':
        training_query = f"""
        CREATE OR REPLACE MODEL `cbi-v14.models.{model_config['name']}`
        OPTIONS(
            model_type='ARIMA_PLUS',
            time_series_timestamp_col='date',
            time_series_data_col='{model_config['target']}',
            auto_arima=TRUE,
            data_frequency='DAILY'
        ) AS
        SELECT 
            date,
            {model_config['target']}
        FROM `cbi-v14.models.training_dataset_final_v1`
        WHERE date <= '2024-03-31'
        AND {model_config['target']} IS NOT NULL
        ORDER BY date
        """
    elif model_config['type'] == 'LINEAR_REG':
        training_query = f"""
        CREATE OR REPLACE MODEL `cbi-v14.models.{model_config['name']}`
        OPTIONS(
            model_type='LINEAR_REG',
            input_label_cols=['{model_config['target']}'],
            data_split_method='AUTO_SPLIT'
        ) AS
        SELECT 
            * EXCEPT(date, target_1m, target_3m, target_6m)
        FROM `cbi-v14.models.training_dataset_final_v1`
        WHERE date <= '2024-03-31'
        AND {model_config['target']} IS NOT NULL
        """
    else:  # DNN_REGRESSOR
        training_query = f"""
        CREATE OR REPLACE MODEL `cbi-v14.models.{model_config['name']}`
        OPTIONS(
            model_type='DNN_REGRESSOR',
            hidden_units=[64, 32],
            activation_fn='RELU',
            dropout=0.2,
            batch_size=64,
            learn_rate=0.001,
            optimizer='ADAM',
            input_label_cols=['{model_config['target']}'],
            data_split_method='AUTO_SPLIT',
            max_iterations=100,
            early_stop=TRUE
        ) AS
        SELECT 
            * EXCEPT(date, target_1m, target_3m, target_6m)
        FROM `cbi-v14.models.training_dataset_final_v1`
        WHERE date <= '2024-03-31'
        AND {model_config['target']} IS NOT NULL
        """
    
    # Train the model
    print(f"Training (this may take 2-5 minutes)...")
    start_time = time.time()
    
    try:
        job = client.query(training_query)
        job.result()
        duration = time.time() - start_time
        
        print(f"✅ Training complete ({duration:.1f} seconds)")
        
        # Evaluate on validation set
        print("Evaluating on validation set...")
        
        if model_config['type'] == 'ARIMA_PLUS':
            # ARIMA uses built-in evaluation
            eval_query = f"""
            SELECT 
                mean_absolute_error as mae,
                mean_squared_error,
                SQRT(mean_squared_error) as rmse,
                0.0 as r2_score
            FROM ML.EVALUATE(
                MODEL `cbi-v14.models.{model_config['name']}`
            )
            """
        else:
            eval_query = f"""
            SELECT 
                mean_absolute_error as mae,
                mean_squared_error,
                SQRT(mean_squared_error) as rmse,
                r2_score
            FROM ML.EVALUATE(
                MODEL `cbi-v14.models.{model_config['name']}`
            )
            """
        
        eval_result = list(client.query(eval_query).result())[0]
        
        print(f"✅ Evaluation Metrics:")
        print(f"   MAE: {eval_result.mae:.4f}")
        print(f"   RMSE: {eval_result.rmse:.4f}")
        if hasattr(eval_result, 'r2_score'):
            print(f"   R²: {eval_result.r2_score:.4f}")
        
        # Log to tracking table
        log_query = f"""
        INSERT INTO `cbi-v14.models.model_training_log`
        (experiment_id, model_name, model_type, horizon, training_duration_seconds, 
         val_mae, val_rmse, feature_count, notes)
        VALUES (
            GENERATE_UUID(),
            '{model_config['name']}',
            '{model_config['type']}',
            '{model_config['horizon']}',
            {duration},
            {eval_result.mae},
            {eval_result.rmse},
            159,
            'Phase 1 baseline - {model_config["description"]}'
        )
        """
        client.query(log_query).result()
        
        results.append({
            'name': model_config['name'],
            'type': model_config['type'],
            'status': 'SUCCESS',
            'mae': float(eval_result.mae),
            'rmse': float(eval_result.rmse),
            'duration': duration
        })
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Training failed: {str(e)[:200]}")
        
        results.append({
            'name': model_config['name'],
            'type': model_config['type'],
            'status': 'FAILED',
            'error': str(e)[:200],
            'duration': duration
        })

# Summary
print("\n" + "="*80)
print("PHASE 1 BASELINE TRAINING COMPLETE")
print("="*80)

success_count = len([r for r in results if r['status'] == 'SUCCESS'])
print(f"\nModels trained: {success_count}/{len(baseline_models)}")

if success_count > 0:
    print("\n📊 Baseline Performance:")
    for result in results:
        if result['status'] == 'SUCCESS':
            print(f"\n{result['name']}:")
            print(f"   Type: {result['type']}")
            print(f"   MAE: {result['mae']:.4f}")
            print(f"   RMSE: {result['rmse']:.4f}")
            print(f"   Training time: {result['duration']:.1f}s")

print("\n✅ Phase 1 complete. Baseline established.")
print("\nNext: Review performance and proceed with Phase 2 (optimized models)")

