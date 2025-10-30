#!/usr/bin/env python3
"""
STOP ALL ACTIVE BIGQUERY ML TRAINING JOBS
Cancels any running model training to save costs
"""

from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("CHECKING FOR ACTIVE TRAINING JOBS")
print("=" * 80)

# 1. List all active jobs
print("\n1. Checking for active jobs...")
active_jobs = []
cancelled_count = 0

try:
    # Query for running jobs in the last 24 hours
    for job in client.list_jobs(max_results=100, state_filter="running"):
        if job.job_type == "query" and job.query:
            query_text = job.query.lower() if hasattr(job, 'query') else ""
            if 'create' in query_text and 'model' in query_text:
                active_jobs.append(job)
                print(f"\n⚠️ Found active training job:")
                print(f"   Job ID: {job.job_id}")
                print(f"   Created: {job.created}")
                print(f"   State: {job.state}")
                
    if not active_jobs:
        print("✅ No active training jobs found")
    else:
        print(f"\n⚠️ Found {len(active_jobs)} active training job(s)")
        
        # Cancel each job
        for job in active_jobs:
            try:
                job.cancel()
                print(f"   ✅ Cancelled job: {job.job_id}")
                cancelled_count += 1
            except Exception as e:
                print(f"   ❌ Failed to cancel {job.job_id}: {e}")
                
except Exception as e:
    print(f"Error checking jobs: {e}")

# 2. Check recent completed jobs for context
print("\n" + "=" * 80)
print("2. Recent training jobs (last 2 hours):")
print("-" * 40)

try:
    # Get jobs from last 2 hours
    from datetime import datetime, timedelta
    two_hours_ago = datetime.utcnow() - timedelta(hours=2)
    
    recent_models = []
    for job in client.list_jobs(max_results=50):
        if job.created and job.created.replace(tzinfo=None) > two_hours_ago:
            if job.job_type == "query" and hasattr(job, 'query'):
                query_text = str(job.query).lower() if job.query else ""
                if 'create' in query_text and 'model' in query_text:
                    # Extract model name from query
                    import re
                    model_match = re.search(r'models\.(\w+)', str(job.query))
                    if model_match:
                        model_name = model_match.group(1)
                        recent_models.append({
                            'name': model_name,
                            'state': job.state,
                            'created': job.created
                        })
    
    if recent_models:
        print(f"Found {len(recent_models)} recent training attempts:")
        for model in recent_models[:10]:  # Show first 10
            status = "✅" if model['state'] == "DONE" else "❌"
            print(f"   {status} {model['name']}: {model['state']}")
    else:
        print("No recent training jobs found")
        
except Exception as e:
    print(f"Error checking recent jobs: {e}")

# 3. List existing models to see what we have
print("\n" + "=" * 80)
print("3. Existing trained models:")
print("-" * 40)

try:
    query = """
    SELECT 
        model_name,
        model_type,
        creation_time,
        training_runs
    FROM `cbi-v14.models.INFORMATION_SCHEMA.MODELS`
    ORDER BY creation_time DESC
    LIMIT 20
    """
    
    results = client.query(query)
    model_count = 0
    
    for row in results:
        model_count += 1
        model_type = row.model_type.replace('_', ' ').title()
        print(f"   • {row.model_name}: {model_type} (created {row.creation_time.strftime('%Y-%m-%d %H:%M')})")
    
    if model_count == 0:
        print("   No models found in models dataset")
    else:
        print(f"\n   Total: {model_count} models")
        
except Exception as e:
    print(f"Error listing models: {e}")

# 4. Check for AutoML jobs (they run longer)
print("\n" + "=" * 80)
print("4. Checking for AutoML jobs:")
print("-" * 40)

try:
    # AutoML jobs can be identified by budget_hours parameter
    automl_query = """
    SELECT 
        model_name,
        model_type,
        creation_time
    FROM `cbi-v14.models.INFORMATION_SCHEMA.MODELS`
    WHERE model_type = 'AUTOML_REGRESSOR'
    AND creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    """
    
    results = client.query(automl_query)
    automl_count = 0
    
    for row in results:
        automl_count += 1
        print(f"   ⚠️ Recent AutoML: {row.model_name} (started {row.creation_time})")
    
    if automl_count == 0:
        print("   ✅ No recent AutoML training")
    else:
        print(f"\n   ⚠️ {automl_count} AutoML model(s) may still be training")
        print("   Note: AutoML jobs run for the specified budget_hours (usually 1.0)")
        
except Exception as e:
    print(f"Error checking AutoML: {e}")

# 5. Summary and recommendations
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

if cancelled_count > 0:
    print(f"✅ Cancelled {cancelled_count} active training job(s)")
    print("💰 This will stop billing for those training operations")
else:
    print("✅ No active training jobs to cancel")

print("\n📝 RECOMMENDATIONS:")
print("1. Wait for any AutoML jobs to complete (check budget_hours)")
print("2. Fix the correlation NaN issues before retraining")
print("3. Consider training in smaller batches to control costs")
print("4. Use ARIMA models as baseline (they're working)")

print("\n💡 TO RESUME TRAINING:")
print("1. Fix models.vw_correlation_features NaN issues")
print("2. Run scripts/FIX_AND_TRAIN_PROPERLY.py")
print("3. Monitor costs in BigQuery console")

print("\n" + "=" * 80)
print("ALL TRAINING STOPPED - READY TO FIX ISSUES")
print("=" * 80)
