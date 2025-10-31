#!/usr/bin/env python3
"""
Complete Model Retraining - Super-Enriched Dataset
Sequential, safe, precise training with complete data (197 features)
"""

from google.cloud import bigquery
from datetime import datetime
import time
import sys

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("🚀 COMPLETE MODEL RETRAINING - SUPER-ENRICHED DATASET")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Dataset: models_v4.training_dataset_super_enriched (197 features)")
print("=" * 80)
print()

# Verify dataset exists
print("🔍 Verifying super-enriched dataset...")
dataset_check = """
SELECT COUNT(*) as row_count
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
"""
result = client.query(dataset_check).to_dataframe()
row_count = result['row_count'].iloc[0]
print(f"✅ Dataset verified: {row_count} rows")
print()

# Check feature count
feature_check = """
SELECT COUNT(*) as feature_count
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'training_dataset_super_enriched'
AND column_name NOT IN ('date', 'target_1w', 'target_1m', 'target_3m', 'target_6m')
"""
result = client.query(feature_check).to_dataframe()
feature_count = result['feature_count'].iloc[0]
print(f"✅ Features verified: {feature_count} features")
print()

if feature_count < 190:
    print("⚠️  WARNING: Expected 197 features, got {feature_count}")
    print("   Proceeding anyway...")
    print()

print("=" * 80)
print("RETRAINING SEQUENCE")
print("=" * 80)
print()

# Models to train
models_to_train = [
    # Enriched Boosted Tree Models (Best performers)
    ('zl_boosted_tree_1w_complete', 'target_1w', 'BOOSTED_TREE_REGRESSOR', '1 week'),
    ('zl_boosted_tree_1m_complete', 'target_1m', 'BOOSTED_TREE_REGRESSOR', '1 month'),
    ('zl_boosted_tree_3m_complete', 'target_3m', 'BOOSTED_TREE_REGRESSOR', '3 months'),
    ('zl_boosted_tree_6m_complete', 'target_6m', 'BOOSTED_TREE_REGRESSOR', '6 months'),
    
    # DNN Models (Now with enough features)
    ('zl_dnn_1w_complete', 'target_1w', 'DNN_REGRESSOR', '1 week'),
    ('zl_dnn_1m_complete', 'target_1m', 'DNN_REGRESSOR', '1 month'),
]

models_trained = []
models_failed = []

for i, (model_name, target_col, model_type, horizon) in enumerate(models_to_train, 1):
    print(f"\n{'='*70}")
    print(f"MODEL {i}/{len(models_to_train)}: {model_name}")
    print(f"Horizon: {horizon}")
    print(f"Target: {target_col}")
    print(f"Type: {model_type}")
    print('='*70)
    
    # Verify target has data
    check_query = f"""
    SELECT COUNT(*) as row_count
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    WHERE {target_col} IS NOT NULL
    """
    
    result = client.query(check_query).to_dataframe()
    row_count = result['row_count'].iloc[0]
    
    print(f"✅ Training rows: {row_count}")
    
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
        print(f"\n🔄 Starting training (estimated 5-15 minutes)...")
        job = client.query(training_query)
        
        # Wait for completion
        print(f"   Waiting for job to complete...")
        result = job.result()
        
        print(f"✅ SUCCESS: {model_name} trained")
        print(f"   Job ID: {job.job_id}")
        
        # Evaluate immediately
        eval_query = f"""
        SELECT 
            mean_absolute_error,
            mean_squared_error,
            r2_score
        FROM ML.EVALUATE(MODEL `cbi-v14.models_v4.{model_name}`)
        LIMIT 1
        """
        
        print(f"\n📊 Evaluating {model_name}...")
        eval_df = client.query(eval_query).to_dataframe()
        
        mae = float(eval_df['mean_absolute_error'].iloc[0])
        mse = float(eval_df['mean_squared_error'].iloc[0])
        r2 = float(eval_df['r2_score'].iloc[0])
        rmse = mse ** 0.5
        mape = (mae / 50.0) * 100
        
        print(f"   MAE: {mae:.2f}")
        print(f"   RMSE: {rmse:.2f}")
        print(f"   R²: {r2:.3f}")
        print(f"   MAPE: {mape:.2f}%")
        
        if mape < 2.0:
            print(f"   🎯 EXCELLENT: MAPE < 2.0%")
        elif mape < 3.0:
            print(f"   ✅ GOOD: MAPE < 3.0%")
        elif mape < 5.0:
            print(f"   ⚠️  FAIR: MAPE < 5.0%")
        else:
            print(f"   ❌ POOR: MAPE >= 5.0%")
        
        models_trained.append({
            'model': model_name,
            'horizon': horizon,
            'type': model_type,
            'mae': mae,
            'rmse': rmse,
            'r2': r2,
            'mape': mape,
            'status': 'SUCCESS'
        })
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        models_failed.append((model_name, str(e)))
    
    # Wait between models to avoid overloading
    if i < len(models_to_train):
        print(f"\n⏳ Waiting 10 seconds before next model...")
        time.sleep(10)

# Summary
print("\n" + "=" * 80)
print("RETRAINING SUMMARY")
print("=" * 80)

if models_trained:
    print(f"\n✅ Models Trained Successfully: {len(models_trained)}")
    print('-' * 80)
    for m in models_trained:
        status_icon = "🎯" if m['mape'] < 2.0 else "✅" if m['mape'] < 3.0 else "⚠️ " if m['mape'] < 5.0 else "❌"
        print(f"{status_icon} {m['model']} ({m['horizon']}): MAE={m['mae']:.2f}, MAPE={m['mape']:.2f}%")

if models_failed:
    print(f"\n❌ Models Failed: {len(models_failed)}")
    for name, reason in models_failed:
        print(f"   - {name}: {reason}")

print("\n💡 Next: Train AutoML models with super-enriched dataset")
print("=" * 80)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)














