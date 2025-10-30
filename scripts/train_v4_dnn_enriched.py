#!/usr/bin/env python3
"""
Train V4 DNN Models with ENRICHED DATASET (179 features)
Fixes the poor performance by using the same dataset as enriched models
"""

from google.cloud import bigquery
from datetime import datetime
import sys

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("🚀 TRAINING V4 DNN MODELS - ENRICHED DATASET")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Location: us-central1")
print(f"Training Data: models.training_dataset_enhanced (179 features)")
print("=" * 80)
print()

print("📋 Context: Previous DNN models had MAE 5-6 due to insufficient features (28)")
print("🔧 Fix: Training on enriched dataset with 179 features")
print("🎯 Goal: Achieve MAE < 2.0 (match enriched boosted tree performance)")
print()

# Get all numeric columns that need normalization
columns_query = """
SELECT column_name, data_type
FROM `cbi-v14.models.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'training_dataset_enhanced'
AND column_name NOT IN ('date', 'target_1w', 'target_1m', 'target_3m', 'target_6m')
AND data_type IN ('FLOAT64', 'INT64')
ORDER BY column_name
"""

print("🔍 Identifying numeric columns for normalization...")
numeric_cols = client.query(columns_query).to_dataframe()
print(f"✅ Found {len(numeric_cols)} numeric columns to normalize")
print()

# Build TRANSFORM clause
transform_lines = []
for _, row in numeric_cols.iterrows():
    col_name = row['column_name']
    transform_lines.append(f"        ML.STANDARD_SCALER({col_name}) OVER() AS {col_name}")

transform_clause = ",\n".join(transform_lines)

# Train both DNN models with better architecture
horizons = [
    ('1w', 'target_1w', [512, 256, 128, 64]),  # Larger architecture for more features
    ('1m', 'target_1m', [512, 256, 128, 64])
]

models_trained = []
models_failed = []

for horizon, target_col, hidden_units in horizons:
    model_name = f"zl_dnn_{horizon}_v4_enriched"
    
    print(f"\n{'='*70}")
    print(f"TRAINING: {model_name}")
    print(f"Horizon: {horizon}")
    print(f"Target: {target_col}")
    print(f"Hidden Units: {hidden_units}")
    print(f"Features: {len(numeric_cols)} (vs 28 in previous attempt)")
    print(f"Normalization: STANDARD_SCALER")
    print('='*70)
    
    training_query = f"""
    CREATE OR REPLACE MODEL `cbi-v14.models_v4.{model_name}`
    TRANSFORM(
{transform_clause},
        {target_col}
    )
    OPTIONS(
        model_type='DNN_REGRESSOR',
        hidden_units={hidden_units},
        activation_fn='RELU',
        dropout=0.2,
        batch_size=32,
        learn_rate=0.0005,
        optimizer='ADAM',
        input_label_cols=['{target_col}'],
        data_split_method='AUTO_SPLIT',
        early_stop=TRUE,
        max_iterations=150
    ) AS
    SELECT * EXCEPT(date) 
    FROM `cbi-v14.models.training_dataset_enhanced`
    WHERE {target_col} IS NOT NULL
    """
    
    try:
        print(f"\n🔄 Starting training (this will take ~10-15 minutes)...")
        job = client.query(training_query)
        
        # Wait for completion
        print(f"   Waiting for job to complete...")
        result = job.result()
        
        print(f"✅ SUCCESS: {model_name} trained")
        print(f"   Job ID: {job.job_id}")
        
        # Immediately evaluate
        eval_query = f"""
        SELECT * FROM ML.EVALUATE(MODEL `cbi-v14.models_v4.{model_name}`)
        """
        
        print(f"\n📊 Evaluating {model_name}...")
        eval_df = client.query(eval_query).to_dataframe()
        
        mae = float(eval_df['mean_absolute_error'].iloc[0])
        r2 = float(eval_df['r2_score'].iloc[0])
        mape = (mae / 50.0) * 100
        
        print(f"   MAE: {mae:.2f}")
        print(f"   R²: {r2:.3f}")
        print(f"   MAPE: {mape:.2f}%")
        
        if mae < 2.0:
            print(f"   🎯 EXCELLENT: MAE < 2.0 (exceeds target)")
        elif mae < 3.0:
            print(f"   ✅ GOOD: MAE < 3.0 (acceptable)")
        elif mae < 5.0:
            print(f"   ⚠️  IMPROVED: MAE < 5.0 (but not as good as enriched boosted tree)")
        else:
            print(f"   ❌ STILL POOR: MAE >= 5.0 (needs investigation)")
        
        models_trained.append({
            'model': model_name,
            'mae': mae,
            'r2': r2,
            'mape': mape,
            'status': 'SUCCESS'
        })
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        models_failed.append((model_name, str(e)))

# Summary
print("\n" + "=" * 80)
print("TRAINING SUMMARY")
print("=" * 80)

if models_trained:
    print(f"\n✅ Models Trained Successfully: {len(models_trained)}")
    for m in models_trained:
        if m['mae'] < 2.0:
            status_icon = "🎯"
        elif m['mae'] < 3.0:
            status_icon = "✅"
        elif m['mae'] < 5.0:
            status_icon = "⚠️ "
        else:
            status_icon = "❌"
        print(f"   {status_icon} {m['model']}: MAE={m['mae']:.2f}, R²={m['r2']:.3f}, MAPE={m['mape']:.2f}%")

if models_failed:
    print(f"\n❌ Models Failed: {len(models_failed)}")
    for name, reason in models_failed:
        print(f"   - {name}: {reason}")

print("\n💡 Comparison:")
print("   Previous DNN (28 features): MAE 5-6, MAPE 10-12%")
print("   Enriched Boosted Tree (179 features): MAE 1.5-1.8, MAPE 3-3.6%")
print("   New DNN (179 features): Expected MAE < 3.0")
print("=" * 80)













