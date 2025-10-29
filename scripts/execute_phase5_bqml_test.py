#!/usr/bin/env python3
"""
PHASE 5: Test BQML Compatibility
"""
from google.cloud import bigquery
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print("="*80)
print("PHASE 5: TESTING BQML COMPATIBILITY")
print("="*80)
print(f"Start Time: {datetime.now().isoformat()}\n")

print("Testing with LINEAR_REG model on 100 rows...")

test_query = """
CREATE OR REPLACE MODEL `cbi-v14.staging_ml.bqml_compatibility_test`
OPTIONS(
    model_type='LINEAR_REG',
    input_label_cols=['target_1w'],
    max_iterations=1
) AS
SELECT * EXCEPT(date, target_1m, target_3m, target_6m)
FROM `cbi-v14.staging_ml.training_dataset_v1`
WHERE target_1w IS NOT NULL
LIMIT 100
"""

try:
    print("Creating test model...")
    job = client.query(test_query)
    result = job.result()
    print("✅ Model created successfully!")
    
    # Evaluate the model
    print("\nEvaluating model...")
    eval_query = """
    SELECT *
    FROM ML.EVALUATE(MODEL `cbi-v14.staging_ml.bqml_compatibility_test`)
    """
    eval_result = client.query(eval_query).to_dataframe()
    print(f"✅ Mean Absolute Error: {eval_result.mean_absolute_error.values[0]:.4f}")
    print(f"✅ R²: {eval_result.r2_score.values[0]:.4f}")
    
    # Clean up test model
    print("\nCleaning up test model...")
    client.query("DROP MODEL `cbi-v14.staging_ml.bqml_compatibility_test`").result()
    print("✅ Test model deleted")
    
    print("\n" + "="*80)
    print("🎯 PHASE 5 COMPLETE - BQML COMPATIBILITY CONFIRMED")
    print("="*80)
    print("\n✅ The training table is BQML-compatible!")
    print("✅ No correlated subquery errors!")
    print("✅ Ready for production model training!")
    
except Exception as e:
    print(f"\n❌ BQML compatibility test FAILED: {e}")
    raise










