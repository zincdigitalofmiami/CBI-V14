#!/usr/bin/env python3
"""Check training completion status"""
from google.cloud import bigquery
from datetime import datetime
import json

client = bigquery.Client(project='cbi-v14')

# Load submitted jobs
with open('logs/submitted_training_jobs.json', 'r') as f:
    submitted = json.load(f)

print("="*80)
print("TRAINING COMPLETION CHECK")
print("="*80)
print(f"Check Time: {datetime.now().isoformat()}")
print(f"Jobs Submitted: {submitted['total_submitted']}\n")

completed = []
running = []
failed = []

for job_info in submitted['jobs']:
    name = job_info['name']
    job_id = job_info['job_id']
    
    try:
        # Check if model exists
        model = client.get_model(f'cbi-v14.models.{name}')
        completed.append({
            'name': name,
            'type': job_info['type'],
            'horizon': job_info['horizon'],
            'created': model.created
        })
    except:
        # Check job status
        try:
            job = client.get_job(job_id)
            if job.state == 'RUNNING':
                running.append(name)
            elif job.state in ['PENDING', 'QUEUED']:
                running.append(name)
            else:
                failed.append((name, job.state, str(job.errors) if job.errors else 'Unknown'))
        except:
            running.append(name)  # Assume still running if we can't get status

print(f"✅ Complete: {len(completed)}/16")
print(f"⏳ Running: {len(running)}/16")
print(f"❌ Failed: {len(failed)}/16")

if completed:
    print("\n" + "="*80)
    print("COMPLETED MODELS:")
    print("="*80)
    for horizon in ['1w', '1m', '3m', '6m']:
        horizon_models = [m for m in completed if m['horizon'] == horizon]
        if horizon_models:
            print(f"\n{horizon} ({len(horizon_models)}/4):")
            for m in horizon_models:
                print(f"  ✅ {m['name']:35s} ({m['type']})")

if running:
    print("\n" + "="*80)
    print(f"STILL TRAINING ({len(running)}):")
    print("="*80)
    for name in running[:10]:
        print(f"  ⏳ {name}")
    if len(running) > 10:
        print(f"  ... and {len(running)-10} more")

if failed:
    print("\n" + "="*80)
    print(f"FAILED ({len(failed)}):")
    print("="*80)
    for name, state, error in failed:
        print(f"  ❌ {name}: {state} - {error[:60]}")

print("\n" + "="*80)

if len(completed) == 16:
    print("🎉 ALL 16 MODELS COMPLETE!")
    print("\nReady for production deployment!")
elif len(completed) > 0:
    pct = (len(completed) / 16) * 100
    print(f"⏳ Training {pct:.0f}% complete")
    print(f"Estimated time remaining: {(16-len(completed)) * 2} - {(16-len(completed)) * 4} minutes")
else:
    print("⏳ Training jobs queued...")

print("="*80)





