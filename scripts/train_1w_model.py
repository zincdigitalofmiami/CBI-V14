#!/usr/bin/env python3
"""
Train the 1W BQML model
"""
from google.cloud import bigquery
from pathlib import Path
import sys
from datetime import datetime

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"
MODEL_NAME = "bqml_1w_mean"
SQL_FILE = "bigquery_sql/train_bqml_1w_mean.sql"

client = bigquery.Client(project=PROJECT_ID)

print("="*80)
print("🚀 TRAINING 1W MODEL")
print("="*80)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Model: {MODEL_NAME}")
print(f"SQL File: {SQL_FILE}")
print("="*80)

# Load SQL file
sql_path = Path(__file__).parent.parent / SQL_FILE

if not sql_path.exists():
    print(f"\n❌ SQL file not found: {SQL_FILE}")
    sys.exit(1)

print(f"\n📄 Loading SQL from: {SQL_FILE}")
with open(sql_path, 'r') as f:
    sql_content = f.read()

print(f"✅ SQL loaded ({len(sql_content)} characters)")

# Check if model exists
print(f"\n🔍 Checking if model already exists...")
try:
    query = f"""
    SELECT COUNT(*) as trial_count
    FROM ML.TRIAL_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.{MODEL_NAME}`)
    """
    result = client.query(query).to_dataframe()
    if not result.empty and result.iloc[0]['trial_count'] > 0:
        print(f"  ⚠️  Model exists - will be replaced by training")
except Exception:
    try:
        query = f"""
        SELECT COUNT(*) as iter_count
        FROM ML.TRAINING_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.{MODEL_NAME}`)
        """
        result = client.query(query).to_dataframe()
        if not result.empty:
            print(f"  ⚠️  Model exists - will be replaced by training")
    except Exception:
        print(f"  ✅ Model does not exist - will be created")

# Execute training
print(f"\n🚀 Starting training...")
print(f"  ⏳ This may take 10-30 minutes (hyperparameter tuning with 30 trials)")
print(f"  📊 Model type: BOOSTED_TREE_REGRESSOR")
print(f"  🎯 Target: target_1w")

try:
    # Submit job
    job = client.query(sql_content, job_config=bigquery.QueryJobConfig(
        use_legacy_sql=False,
        job_timeout_ms=3600000  # 1 hour timeout
    ))
    
    print(f"\n  ✅ Training job submitted")
    print(f"  📋 Job ID: {job.job_id}")
    print(f"  ⏳ Waiting for completion...")
    
    # Wait for completion (with progress updates)
    import time
    start_time = time.time()
    last_update = start_time
    
    while not job.done():
        elapsed = time.time() - start_time
        if time.time() - last_update > 60:  # Update every 60 seconds
            elapsed_min = int(elapsed / 60)
            print(f"  ⏳ Still training... ({elapsed_min} minutes elapsed)")
            last_update = time.time()
        time.sleep(5)
    
    # Check for errors
    if job.errors:
        print(f"\n  ❌ Training failed with errors:")
        for error in job.errors:
            print(f"     {error}")
        sys.exit(1)
    
    elapsed_total = time.time() - start_time
    elapsed_min = int(elapsed_total / 60)
    elapsed_sec = int(elapsed_total % 60)
    
    print(f"\n  ✅ Training completed successfully!")
    print(f"  ⏱️  Total time: {elapsed_min} minutes {elapsed_sec} seconds")
    
    # Verify model was created
    print(f"\n🔍 Verifying model was created...")
    try:
        query = f"""
        SELECT COUNT(*) as trial_count
        FROM ML.TRIAL_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.{MODEL_NAME}`)
        """
        result = client.query(query).to_dataframe()
        if not result.empty and result.iloc[0]['trial_count'] > 0:
            trials = int(result.iloc[0]['trial_count'])
            print(f"  ✅ Model created successfully")
            print(f"  📊 Hyperparameter trials: {trials}")
        else:
            # Try TRAINING_INFO
            query = f"""
            SELECT COUNT(*) as iter_count
            FROM ML.TRAINING_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.{MODEL_NAME}`)
            """
            result = client.query(query).to_dataframe()
            if not result.empty:
                iterations = int(result.iloc[0]['iter_count'])
                print(f"  ✅ Model created successfully")
                print(f"  📊 Training iterations: {iterations}")
    except Exception as e:
        print(f"  ⚠️  Could not verify model details: {e}")
        print(f"  ✅ Training job completed - model should exist")
    
    print("\n" + "="*80)
    print("✅ 1W MODEL TRAINING COMPLETE")
    print("="*80)
    print(f"Model: {PROJECT_ID}.{DATASET_ID}.{MODEL_NAME}")
    print(f"Next: Run audit_1w_last_training.py to verify training quality")
    print("="*80)
    
except Exception as e:
    error_str = str(e)
    print(f"\n  ❌ Training failed: {error_str}")
    
    # Provide helpful error messages
    if "timeout" in error_str.lower():
        print(f"\n  💡 Training timed out - try increasing timeout or reducing num_trials")
    elif "null" in error_str.lower():
        print(f"\n  💡 Check for NULL values in training data or data_split column")
    elif "column" in error_str.lower() or "not found" in error_str.lower():
        print(f"\n  💡 Check for missing columns or column name mismatches")
    elif "permission" in error_str.lower() or "access" in error_str.lower():
        print(f"\n  💡 Check BigQuery permissions and dataset access")
    
    sys.exit(1)


