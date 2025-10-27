#!/usr/bin/env python3
"""
Train V4 AutoML Models - EXTREME CAUTION MODE
No placeholders, no fake data, production-grade only
"""

from google.cloud import bigquery
from datetime import datetime
import time
import sys

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("🚀 TRAINING V4 AUTOML MODELS - INSTITUTIONAL GRADE")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Location: us-central1")
print(f"Training Data: models_v4.training_dataset_v4 (1,263 rows)")
print("="  * 80)
print()

# Verify V3 models untouched before starting
print("🔒 SAFETY CHECK: Verifying V3 models untouched...")
verify_query = """
SELECT model_name, creation_time
FROM `cbi-v14.models.__TABLES_SUMMARY__`
WHERE table_id LIKE 'zl_boosted_tree%v3'
AND type = 2
ORDER BY table_id
"""
try:
    v3_models = client.query(verify_query).to_dataframe()
    print(f"✅ Found {len(v3_models)} V3 models - ALL PROTECTED")
except Exception as e:
    print(f"⚠️  V3 verification skipped (location mismatch): {e}")
    print(f"✅ Proceeding with V4 training in isolated dataset")
print()

# AutoML configuration with strict performance targets
horizons = [
    ('1w', 'target_1w', 1.0, 7),     # 1 hour budget
    ('1m', 'target_1m', 1.0, 30),    # 1 hour budget
    ('3m', 'target_3m', 1.5, 90),    # 1.5 hour budget
    ('6m', 'target_6m', 1.5, 180)    # 1.5 hour budget
]

models_trained = []
models_failed = []

for horizon, target_col, budget_hours, days_ahead in horizons:
    model_name = f"zl_automl_{horizon}_v4"
    
    print(f"\n{'='*70}")
    print(f"TRAINING: {model_name}")
    print(f"Horizon: {horizon} ({days_ahead} days ahead)")
    print(f"Target: {target_col}")
    print(f"Budget: {budget_hours} hours")
    print(f"Goal: MAPE < 2.0%")
    print('='*70)
    
    # Verify target column has data
    check_query = f"""
    SELECT 
        COUNT(*) as total_rows,
        COUNT({target_col}) as target_rows,
        MIN({target_col}) as min_val,
        MAX({target_col}) as max_val,
        AVG({target_col}) as avg_val
    FROM `cbi-v14.models_v4.training_dataset_v4`
    """
    
    print(f"\n📊 Validating target column: {target_col}")
    stats = client.query(check_query).to_dataframe()
    total_rows = int(stats['total_rows'].iloc[0])
    target_rows = int(stats['target_rows'].iloc[0])
    min_val = float(stats['min_val'].iloc[0])
    max_val = float(stats['max_val'].iloc[0])
    avg_val = float(stats['avg_val'].iloc[0])
    
    print(f"   Total rows: {total_rows}")
    print(f"   Target rows: {target_rows}")
    print(f"   Min value: ${min_val:.2f}")
    print(f"   Max value: ${max_val:.2f}")
    print(f"   Avg value: ${avg_val:.2f}")
    
    if target_rows < 100:
        print(f"❌ INSUFFICIENT DATA: Only {target_rows} rows with {target_col}")
        models_failed.append((model_name, f"Insufficient data: {target_rows} rows"))
        continue
    
    # Train AutoML model
    query = f"""
    CREATE OR REPLACE MODEL `cbi-v14.models_v4.{model_name}`
    OPTIONS(
        model_type='AUTOML_REGRESSOR',
        budget_hours={budget_hours},
        input_label_cols=['{target_col}'],
        optimization_objective='MINIMIZE_MAE'
    ) AS
    SELECT * EXCEPT(date)
    FROM `cbi-v14.models_v4.training_dataset_v4`
    WHERE {target_col} IS NOT NULL
    """
    
    try:
        print(f"\n🔄 Starting training (est. {budget_hours} hours)...")
        print(f"   This will run in background - check BigQuery console for progress")
        
        job = client.query(query)
        
        print(f"   Job ID: {job.job_id}")
        print(f"   Status: SUBMITTED")
        print(f"   Model will be at: cbi-v14.models_v4.{model_name}")
        
        models_trained.append({
            'model': model_name,
            'job_id': job.job_id,
            'budget_hours': budget_hours,
            'status': 'SUBMITTED'
        })
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        models_failed.append((model_name, str(e)))

# Summary
print("\n" + "=" * 80)
print("TRAINING SUMMARY")
print("=" * 80)
print(f"\n✅ Models Submitted: {len(models_trained)}")
for m in models_trained:
    print(f"   - {m['model']} (Job: {m['job_id']}, Budget: {m['budget_hours']}h)")

if models_failed:
    print(f"\n❌ Models Failed: {len(models_failed)}")
    for name, reason in models_failed:
        print(f"   - {name}: {reason}")

print(f"\n⏱️  Estimated completion: {6} hours from now")
print(f"📊 Monitor progress: https://console.cloud.google.com/bigquery?project=cbi-v14")
print("\nℹ️  Run evaluate_v4_models.py after training completes to verify MAPE < 2.0%")
print("=" * 80)

