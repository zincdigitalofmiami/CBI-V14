#!/usr/bin/env python3
"""
Simplified Model Training - Focus on one working model per type
"""
from google.cloud import bigquery
client = bigquery.Client(project='cbi-v14')

print("STEP 1: VERIFY TRAINING DATA")
print("="*60)

# Check if training_dataset exists and has data
check_query = """
SELECT COUNT(*) as row_count, 
       COUNT(target_1w) as target_1w_count 
FROM `cbi-v14.models.training_dataset`
"""
result = client.query(check_query).to_dataframe()
row_count = result.row_count.iloc[0]
target_count = result.target_1w_count.iloc[0]

print(f"Training data: {row_count} rows, {target_count} with target_1w")

if row_count == 0 or target_count == 0:
    print("ERROR: No training data available")
    exit(1)

# Train a simple boosted tree model first
print("\n" + "="*60)
print("STEP 2: TRAIN SIMPLE TEST MODEL")
print("="*60)
print("Training a single Boosted Tree model to verify everything works...")

query = """
CREATE OR REPLACE MODEL `cbi-v14.models.zl_boosted_tree_1w_simple`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1w'],
  max_iterations=50
) AS
SELECT
  zl_price_current,
  zl_price_lag1,
  zl_price_lag7,
  zl_price_lag30,
  target_1w
FROM `cbi-v14.models.training_dataset`
WHERE target_1w IS NOT NULL
"""

try:
    job = client.query(query)
    print(f"✓ Job submitted: {job.job_id}")
    print("\nTraining is in progress. This will take ~5 minutes.")
    print("\nTo verify completion, run:")
    print("  bq ls --models cbi-v14:models | grep zl_boosted_tree_1w_simple")
except Exception as e:
    print(f"✗ Error submitting job: {str(e)}")
    print("\nTroubleshooting: Check if the dataset exists and has proper permissions")
