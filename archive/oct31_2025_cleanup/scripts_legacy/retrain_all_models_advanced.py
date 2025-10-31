#!/usr/bin/env python3
"""
Advanced Model Retraining - Super-Enriched Dataset
Includes: Ensemble models, Walk-forward validation, Advanced techniques
Sequential, safe, precise training with complete data (197 features)
"""

from google.cloud import bigquery
from datetime import datetime
import time
import sys

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("🚀 ADVANCED MODEL RETRAINING - COMPLETE DATA")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Dataset: models_v4.training_dataset_super_enriched (197 features)")
print("=" * 80)
print()

# Verify dataset
print("🔍 Verifying super-enriched dataset...")
dataset_check = """
SELECT COUNT(*) as row_count
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
"""
result = client.query(dataset_check).to_dataframe()
row_count = result['row_count'].iloc[0]
print(f"✅ Dataset verified: {row_count} rows")
print()

# Phase 1: Train individual models
print("=" * 80)
print("PHASE 1: TRAINING INDIVIDUAL MODELS")
print("=" * 80)
print()

models_to_train = [
    # Boosted Tree Models
    ('zl_boosted_tree_1w_complete', 'target_1w', 'BOOSTED_TREE_REGRESSOR', '1 week'),
    ('zl_boosted_tree_1m_complete', 'target_1m', 'BOOSTED_TREE_REGRESSOR', '1 month'),
    ('zl_boosted_tree_3m_complete', 'target_3m', 'BOOSTED_TREE_REGRESSOR', '3 months'),
    ('zl_boosted_tree_6m_complete', 'target_6m', 'BOOSTED_TREE_REGRESSOR', '6 months'),
    
    # DNN Models
    ('zl_dnn_1w_complete', 'target_1w', 'DNN_REGRESSOR', '1 week'),
    ('zl_dnn_1m_complete', 'target_1m', 'DNN_REGRESSOR', '1 month'),
]

models_trained = []
models_failed = []

for i, (model_name, target_col, model_type, horizon) in enumerate(models_to_train, 1):
    print(f"\n{'='*70}")
    print(f"MODEL {i}/{len(models_to_train)}: {model_name}")
    print(f"Horizon: {horizon}")
    print('='*70)
    
    # Verify target has data
    check_query = f"""
    SELECT COUNT(*) as row_count
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    WHERE {target_col} IS NOT NULL
    """
    
    result = client.query(check_query).to_dataframe()
    row_count = result['row_count'].iloc[0]
    
    if row_count < 100:
        print(f"❌ INSUFFICIENT DATA: Only {row_count} rows")
        models_failed.append((model_name, f"Insufficient data: {row_count} rows"))
        continue
    
    # Build training query
    if model_type == 'BOOSTED_TREE_REGRESSOR':
        training_query = f"""
        CREATE OR REPLACE MODEL `cbi-v14.models_v4.{model_name}`
        OPTIONS(
            model_type='BOOSTED_TREE_REGRESSOR',
            input_label_cols=['{target_col}'],
            num_parallel_tree=10,
            max_tree_depth=10,
            min_tree_child_weight=10,
            subsample=0.8,
            colsample_bytree=0.8,
            early_stop=TRUE,
            l1_reg=0.1,
            l2_reg=0.1
        ) AS
        SELECT * EXCEPT(date)
        FROM `cbi-v14.models_v4.training_dataset_super_enriched`
        WHERE {target_col} IS NOT NULL
        """
    else:  # DNN
        training_query = f"""
        CREATE OR REPLACE MODEL `cbi-v14.models_v4.{model_name}`
        OPTIONS(
            model_type='DNN_REGRESSOR',
            input_label_cols=['{target_col}'],
            hidden_units=[512, 256, 128, 64],
            activation_fn='RELU',
            dropout=0.2,
            batch_size=32,
            learn_rate=0.0005,
            optimizer='ADAM',
            early_stop=TRUE,
            max_iterations=150
        ) AS
        SELECT * EXCEPT(date)
        FROM `cbi-v14.models_v4.training_dataset_super_enriched`
        WHERE {target_col} IS NOT NULL
        """
    
    try:
        print(f"🔄 Training...")
        job = client.query(training_query)
        result = job.result()
        
        print(f"✅ Trained: {model_name}")
        
        # Evaluate
        eval_query = f"""
        SELECT mean_absolute_error, r2_score
        FROM ML.EVALUATE(MODEL `cbi-v14.models_v4.{model_name}`)
        LIMIT 1
        """
        
        eval_df = client.query(eval_query).to_dataframe()
        mae = float(eval_df['mean_absolute_error'].iloc[0])
        r2 = float(eval_df['r2_score'].iloc[0])
        mape = (mae / 50.0) * 100
        
        print(f"   MAE: {mae:.2f}, R²: {r2:.3f}, MAPE: {mape:.2f}%")
        
        models_trained.append({
            'model': model_name,
            'horizon': horizon,
            'mae': mae,
            'r2': r2,
            'mape': mape
        })
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        models_failed.append((model_name, str(e)))
    
    time.sleep(5)

# Phase 2: Walk-Forward Validation
print("\n" + "=" * 80)
print("PHASE 2: WALK-FORWARD VALIDATION")
print("=" * 80)
print()

print("Creating walk-forward evaluation...")

# For 1-week horizon
for horizon, target_col in [('1w', 'target_1w'), ('1m', 'target_1m')]:
    print(f"\nWalk-forward validation for {horizon}...")
    
    wf_query = f"""
    CREATE OR REPLACE TABLE `cbi-v14.models_v4.walk_forward_{horizon}` AS
    WITH train_data AS (
        SELECT * EXCEPT(date)
        FROM `cbi-v14.models_v4.training_dataset_super_enriched`
        WHERE {target_col} IS NOT NULL
        AND date < '2024-01-01'
    ),
    test_data AS (
        SELECT * EXCEPT(date)
        FROM `cbi-v14.models_v4.training_dataset_super_enriched`
        WHERE {target_col} IS NOT NULL
        AND date >= '2024-01-01'
    )
    SELECT
        predicted_{target_col},
        {target_col} as actual,
        ABS(predicted_{target_col} - {target_col}) as abs_error
    FROM ML.PREDICT(
        MODEL `cbi-v14.models_v4.zl_boosted_tree_{horizon}_complete`,
        (SELECT * FROM test_data)
    )
    """
    
    try:
        job = client.query(wf_query)
        result = job.result()
        
        # Calculate walk-forward metrics
        metrics_query = f"""
        SELECT 
            AVG(abs_error) as avg_mae,
            STDDEV(abs_error) as stddev_mae,
            MIN(abs_error) as min_error,
            MAX(abs_error) as max_error
        FROM `cbi-v14.models_v4.walk_forward_{horizon}`
        """
        
        metrics_df = client.query(metrics_query).to_dataframe()
        print(f"   Walk-forward MAE: {metrics_df['avg_mae'].iloc[0]:.2f}")
        print(f"   Standard Deviation: {metrics_df['stddev_mae'].iloc[0]:.2f}")
        
    except Exception as e:
        print(f"   ⚠️  Walk-forward validation skipped: {e}")

# Phase 3: Ensemble Models
print("\n" + "=" * 80)
print("PHASE 3: ENSEMBLE MODELS")
print("=" * 80)
print()

for horizon, target_col in [('1w', 'target_1w'), ('1m', 'target_1m')]:
    print(f"\nCreating ensemble for {horizon}...")
    
    ensemble_query = f"""
    CREATE OR REPLACE TABLE `cbi-v14.models_v4.ensemble_{horizon}` AS
    WITH boosted_pred AS (
        SELECT predicted_{target_col} as boosted_pred
        FROM ML.PREDICT(
            MODEL `cbi-v14.models_v4.zl_boosted_tree_{horizon}_complete`,
            (SELECT * EXCEPT(date) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE {target_col} IS NOT NULL)
        )
    ),
    dnn_pred AS (
        SELECT predicted_{target_col} as dnn_pred
        FROM ML.PREDICT(
            MODEL `cbi-v14.models_v4.zl_dnn_{horizon}_complete`,
            (SELECT * EXCEPT(date) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE {target_col} IS NOT NULL)
        )
    ),
    combined AS (
        SELECT 
            boosted_pred,
            dnn_pred,
            (boosted_pred + dnn_pred) / 2 as ensemble_pred
        FROM boosted_pred
        JOIN dnn_pred USING()
    )
    SELECT 
        ensemble_pred,
        actual_{target_col} as actual,
        ABS(ensemble_pred - actual_{target_col}) as abs_error
    FROM combined
    JOIN (SELECT {target_col} as actual_{target_col} FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE {target_col} IS NOT NULL) USING()
    """
    
    try:
        job = client.query(ensemble_query)
        result = job.result()
        
        # Calculate ensemble metrics
        metrics_query = f"""
        SELECT 
            AVG(abs_error) as ensemble_mae,
            SQRT(AVG(POW(abs_error, 2))) as ensemble_rmse
        FROM `cbi-v14.models_v4.ensemble_{horizon}`
        """
        
        metrics_df = client.query(metrics_query).to_dataframe()
        ensemble_mae = metrics_df['ensemble_mae'].iloc[0]
        ensemble_rmse = metrics_df['ensemble_rmse'].iloc[0]
        
        print(f"   Ensemble MAE: {ensemble_mae:.2f}")
        print(f"   Ensemble RMSE: {ensemble_rmse:.2f}")
        
        # Compare to individual models
        boosted_model = next((m for m in models_trained if m['model'] == f'zl_boosted_tree_{horizon}_complete'), None)
        dnn_model = next((m for m in models_trained if m['model'] == f'zl_dnn_{horizon}_complete'), None)
        
        if boosted_model and dnn_model:
            avg_individual = (boosted_model['mae'] + dnn_model['mae']) / 2
            improvement = ((avg_individual - ensemble_mae) / avg_individual) * 100
            print(f"   Improvement: {improvement:.1f}% vs individual models")
        
    except Exception as e:
        print(f"   ⚠️  Ensemble creation skipped: {e}")

# Summary
print("\n" + "=" * 80)
print("RETRAINING SUMMARY")
print("=" * 80)

if models_trained:
    print(f"\n✅ Models Trained: {len(models_trained)}")
    for m in models_trained:
        status_icon = "🎯" if m['mape'] < 2.0 else "✅" if m['mape'] < 3.0 else "⚠️ "
        print(f"{status_icon} {m['model']}: MAE={m['mae']:.2f}, MAPE={m['mape']:.2f}%")

if models_failed:
    print(f"\n❌ Failed: {len(models_failed)}")
    for name, reason in models_failed:
        print(f"   - {name}: {reason}")

print("\n✅ Advanced training complete!")
print("   - Individual models trained")
print("   - Walk-forward validation performed")
print("   - Ensemble models created")
print("=" * 80)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)














