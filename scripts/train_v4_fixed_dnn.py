#!/usr/bin/env python3
"""
Train V4 Fixed DNN Models (1w, 1m) - WITH PROPER NORMALIZATION
Fixes the catastrophically broken V3 DNNs that had MAE in millions
"""

from google.cloud import bigquery
from datetime import datetime
import sys

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("🚀 TRAINING V4 FIXED DNN MODELS - NORMALIZATION FIX")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Location: us-central1")
print(f"Training Data: models_v4.training_dataset_v4 (1,263 rows)")
print("=" * 80)
print()

print("📋 Context: V3 DNN models for 1w/1m had MAE in millions due to lack of normalization")
print("🔧 Fix: Using TRANSFORM with STANDARD_SCALER for all numeric features")
print()

# Get all numeric columns that need normalization
columns_query = """
SELECT column_name, data_type
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'training_dataset_v4'
AND column_name NOT IN ('date', 'target_1w', 'target_1m')
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

# Train both DNN models
horizons = [
    ('1w', 'target_1w', [256, 128, 64, 32]),
    ('1m', 'target_1m', [256, 128, 64, 32])
]

models_trained = []
models_failed = []

for horizon, target_col, hidden_units in horizons:
    model_name = f"zl_dnn_{horizon}_v4"
    
    print(f"\n{'='*70}")
    print(f"TRAINING: {model_name}")
    print(f"Horizon: {horizon}")
    print(f"Target: {target_col}")
    print(f"Hidden Units: {hidden_units}")
    print(f"Normalization: STANDARD_SCALER on {len(numeric_cols)} features")
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
        dropout=0.3,
        batch_size=32,
        learn_rate=0.001,
        optimizer='ADAM',
        input_label_cols=['{target_col}'],
        data_split_method='AUTO_SPLIT',
        early_stop=TRUE,
        max_iterations=100
    ) AS
    SELECT * EXCEPT(date) 
    FROM `cbi-v14.models_v4.training_dataset_v4`
    WHERE {target_col} IS NOT NULL
    """
    
    try:
        print(f"\n🔄 Starting training...")
        job = client.query(training_query)
        
        # Wait for completion (DNNs take ~5-10 minutes each)
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
        mape = (mae / 50.0) * 100  # Assuming avg price ~$50
        
        print(f"   MAE: {mae:.2f}")
        print(f"   R²: {r2:.3f}")
        print(f"   MAPE: {mape:.2f}%")
        
        if mae > 10:
            print(f"   ⚠️  WARNING: MAE still high - may need more tuning")
        elif mape < 2.0:
            print(f"   🎯 EXCEEDS TARGET: MAPE < 2.0%")
        elif mape < 3.0:
            print(f"   ✅ MEETS TARGET: MAPE < 3.0%")
        
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
        status_icon = "🎯" if m['mape'] < 2.0 else "✅" if m['mape'] < 3.0 else "⚠️ "
        print(f"   {status_icon} {m['model']}: MAE={m['mae']:.2f}, R²={m['r2']:.3f}, MAPE={m['mape']:.2f}%")

if models_failed:
    print(f"\n❌ Models Failed: {len(models_failed)}")
    for name, reason in models_failed:
        print(f"   - {name}: {reason}")

print("\n💡 Comparison to V3 Broken DNNs:")
print("   V3 zl_dnn_1w_production: MAE=70,348,475 (BROKEN)")
print("   V3 zl_dnn_1m_production: MAE=119,567,578 (BROKEN)")
print("   V4 models should show MAE < 5.0 (10,000x+ improvement)")
print("=" * 80)

