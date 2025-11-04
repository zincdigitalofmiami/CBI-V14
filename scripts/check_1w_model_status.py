#!/usr/bin/env python3
"""
Check 1W model status after training
"""
from google.cloud import bigquery
import sys

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"
MODEL_NAME = "bqml_1w_mean"

client = bigquery.Client(project=PROJECT_ID)

print("="*80)
print("🔍 CHECKING 1W MODEL STATUS")
print("="*80)

# Try multiple methods to check if model exists
model_exists = False

# Method 1: Try ML.TRIAL_INFO
print("\n1️⃣  Checking ML.TRIAL_INFO...")
try:
    query = f"""
    SELECT COUNT(*) as trial_count
    FROM ML.TRIAL_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.{MODEL_NAME}`)
    """
    result = client.query(query).to_dataframe()
    if not result.empty and result.iloc[0]['trial_count'] > 0:
        model_exists = True
        print(f"  ✅ Model exists (hyperparameter-tuned)")
        print(f"     Trials: {int(result.iloc[0]['trial_count'])}")
except Exception as e:
    print(f"  ❌ Model not found via TRIAL_INFO: {str(e)[:100]}")

# Method 2: Try ML.TRAINING_INFO
if not model_exists:
    print("\n2️⃣  Checking ML.TRAINING_INFO...")
    try:
        query = f"""
        SELECT COUNT(*) as iter_count
        FROM ML.TRAINING_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.{MODEL_NAME}`)
        """
        result = client.query(query).to_dataframe()
        if not result.empty:
            model_exists = True
            iterations = int(result.iloc[0]['iter_count'])
            print(f"  ✅ Model exists (regular training)")
            print(f"     Iterations: {iterations}")
            
            # Get training details
            query = f"""
            SELECT 
              MAX(iteration) as max_iter,
              MIN(loss) as min_loss,
              MAX(loss) as max_loss
            FROM ML.TRAINING_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.{MODEL_NAME}`)
            """
            details = client.query(query).to_dataframe()
            if not details.empty:
                print(f"     Max iteration: {int(details.iloc[0]['max_iter'])}")
                print(f"     Loss range: [{details.iloc[0]['min_loss']:.4f}, {details.iloc[0]['max_loss']:.4f}]")
    except Exception as e:
        print(f"  ❌ Model not found via TRAINING_INFO: {str(e)[:100]}")

# Method 3: Try listing models in dataset
if not model_exists:
    print("\n3️⃣  Checking dataset tables/views...")
    try:
        query = f"""
        SELECT table_name, table_type
        FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.TABLES`
        WHERE table_name = '{MODEL_NAME}'
        """
        result = client.query(query).to_dataframe()
        if len(result) > 0:
            print(f"  ✅ Found in INFORMATION_SCHEMA: {result.iloc[0]['table_type']}")
            model_exists = True
        else:
            print(f"  ❌ Model not found in INFORMATION_SCHEMA")
    except Exception as e:
        print(f"  ❌ Error checking INFORMATION_SCHEMA: {str(e)[:100]}")

print("\n" + "="*80)
if model_exists:
    print("✅ MODEL EXISTS")
    print(f"   Model: {PROJECT_ID}.{DATASET_ID}.{MODEL_NAME}")
    print("\n   Next steps:")
    print("   1. Run: python3 scripts/audit_1w_last_training.py")
    print("   2. Check model performance metrics")
else:
    print("❌ MODEL NOT FOUND")
    print("\n   Possible issues:")
    print("   1. Training job may have failed silently")
    print("   2. Model creation is still in progress")
    print("   3. Check BigQuery job logs for errors")
    print("\n   Check recent jobs:")
    print("   - Go to BigQuery Console → Job History")
    print("   - Look for CREATE MODEL job with errors")
print("="*80)

sys.exit(0 if model_exists else 1)


