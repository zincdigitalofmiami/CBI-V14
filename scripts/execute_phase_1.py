#!/usr/bin/env python3
"""
Phase 1: BQML Model Training
Train all 4 BQML models (1w, 1m, 3m, 6m)
"""
from google.cloud import bigquery
from pathlib import Path
import sys
import subprocess

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"

client = bigquery.Client(project=PROJECT_ID)

def run_pre_audit():
    """Run pre-flight audit before training"""
    print("Running pre-flight audit...")
    result = subprocess.run(
        ['python3', 'scripts/pre_phase_1_audit.py'],
        cwd=Path(__file__).parent.parent
    )
    return result.returncode == 0

def train_model(sql_file, model_name, description):
    """Train a single BQML model"""
    print(f"\n📊 {description}...")
    sql_path = Path(__file__).parent.parent / sql_file
    
    if not sql_path.exists():
        print(f"  ❌ SQL file not found: {sql_file}")
        return False
    
    try:
        with open(sql_path, 'r') as f:
            sql_content = f.read()
        
        print(f"  🚀 Starting training for {model_name}...")
        print(f"  ⏳ This may take 5-15 minutes...")
        
        # Execute training
        job = client.query(sql_content)
        job.result()  # Wait for completion
        
        print(f"  ✅ {model_name} training completed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Training failed: {str(e)[:200]}")
        return False

def main():
    print("="*60)
    print("🚀 PHASE 1: BQML MODEL TRAINING")
    print("="*60)
    
    # Run pre-flight audit
    if not run_pre_audit():
        print("\n❌ Pre-flight audit failed. Review errors above.")
        sys.exit(1)
    
    print("\n✅ Pre-flight audit passed. Proceeding with training...")
    
    # Training sequence
    models = [
        ('bigquery_sql/train_bqml_1w_mean.sql', 'bqml_1w_mean', 'Training 1-Week Model'),
        ('bigquery_sql/train_bqml_1m_mean.sql', 'bqml_1m_mean', 'Training 1-Month Model'),
        ('bigquery_sql/train_bqml_3m_mean.sql', 'bqml_3m_mean', 'Training 3-Month Model'),
        ('bigquery_sql/train_bqml_6m_mean.sql', 'bqml_6m_mean', 'Training 6-Month Model'),
    ]
    
    success_count = 0
    failed_count = 0
    
    for sql_file, model_name, description in models:
        if train_model(sql_file, model_name, description):
            success_count += 1
        else:
            failed_count += 1
            print(f"\n⚠️  {model_name} failed - check errors above")
    
    print("\n" + "="*60)
    print("✅ PHASE 1 EXECUTION COMPLETE")
    print("="*60)
    print(f"Successfully trained: {success_count}/4 models")
    print(f"Failed: {failed_count}/4 models")
    
    if failed_count > 0:
        print("\n⚠️  Some models failed to train. Review errors and retry.")
        sys.exit(1)
    
    print("\n✅ All 4 models trained successfully!")
    print("Next: Phase 2 - Model Evaluation & Residual Quantiles")
    print("="*60)

if __name__ == "__main__":
    main()



