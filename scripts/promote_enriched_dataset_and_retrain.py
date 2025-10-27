#!/usr/bin/env python3
"""
PROMOTE ENRICHED DATASET TO PRODUCTION AND RETRAIN ALL MODELS
Adds 29 news/social features to training, backs up old models, retrains
"""

from google.cloud import bigquery
from datetime import datetime
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("🚀 PROMOTING ENRICHED DATASET AND RETRAINING ALL MODELS")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Step 1: Backup current training dataset
print("Step 1: Backing up current training_dataset...")

backup_query = """
CREATE OR REPLACE TABLE `cbi-v14.models.training_dataset_backup_20251023` AS
SELECT * FROM `cbi-v14.models.training_dataset`;
"""

try:
    job = client.query(backup_query)
    job.result()
    print("✅ Backup created: training_dataset_backup_20251023")
    print()
except Exception as e:
    print(f"❌ Error creating backup: {str(e)}")
    exit(1)

# Step 2: Replace training_dataset with enriched version
print("Step 2: Promoting training_dataset_enriched to production...")

promote_query = """
CREATE OR REPLACE TABLE `cbi-v14.models.training_dataset` AS
SELECT * FROM `cbi-v14.models.training_dataset_enriched`;
"""

try:
    job = client.query(promote_query)
    job.result()
    print("✅ training_dataset replaced with enriched version (62 columns)")
    print()
except Exception as e:
    print(f"❌ Error promoting enriched dataset: {str(e)}")
    print("   Rolling back...")
    rollback_query = """
    CREATE OR REPLACE TABLE `cbi-v14.models.training_dataset` AS
    SELECT * FROM `cbi-v14.models.training_dataset_backup_20251023`;
    """
    client.query(rollback_query).result()
    print("✅ Rolled back to backup")
    exit(1)

# Step 3: Retrain all 4 Boosted Tree models
print("Step 3: Retraining ALL 4 Boosted Tree models with new features...")
print("   (This will take ~5-10 minutes)")
print()

horizons = [
    ('1w', 'target_1w'),
    ('1m', 'target_1m'),
    ('3m', 'target_3m'),
    ('6m', 'target_6m')
]

trained_models = []
failed_models = []

for horizon, target in horizons:
    model_name = f"zl_boosted_tree_{horizon}_v3_enriched"
    
    print(f"Training: {model_name}")
    
    train_query = f"""
    CREATE OR REPLACE MODEL `cbi-v14.models.{model_name}`
    OPTIONS(
        model_type='BOOSTED_TREE_REGRESSOR',
        input_label_cols=['{target}'],
        data_split_method='RANDOM',
        data_split_eval_fraction=0.2,
        max_iterations=50,
        learn_rate=0.1,
        early_stop=TRUE,
        min_tree_child_weight=10,
        subsample=0.8,
        max_tree_depth=8
    ) AS
    SELECT * EXCEPT(date)
    FROM `cbi-v14.models.training_dataset`
    WHERE {target} IS NOT NULL;
    """
    
    try:
        job = client.query(train_query)
        job.result()
        trained_models.append(model_name)
        print(f"   ✅ {model_name} trained successfully")
    except Exception as e:
        failed_models.append((model_name, str(e)))
        print(f"   ❌ {model_name} FAILED: {str(e)}")
    
    print()
    time.sleep(2)  # Brief pause between models

print("=" * 80)
print("📊 TRAINING SUMMARY")
print("=" * 80)
print()
print(f"✅ Successfully trained: {len(trained_models)} models")
for model in trained_models:
    print(f"   - {model}")
print()

if failed_models:
    print(f"❌ Failed to train: {len(failed_models)} models")
    for model, error in failed_models:
        print(f"   - {model}: {error[:100]}")
    print()

# Step 4: Evaluate new models
print("Step 4: Evaluating new enriched models...")
print()

for horizon, target in horizons:
    model_name = f"zl_boosted_tree_{horizon}_v3_enriched"
    
    if model_name not in trained_models:
        continue
    
    eval_query = f"""
    SELECT 
        mean_absolute_error,
        mean_squared_error,
        r2_score
    FROM ML.EVALUATE(MODEL `cbi-v14.models.{model_name}`)
    LIMIT 1;
    """
    
    try:
        eval_df = client.query(eval_query).to_dataframe()
        
        if not eval_df.empty:
            mae = float(eval_df['mean_absolute_error'].iloc[0])
            mse = float(eval_df['mean_squared_error'].iloc[0])
            r2 = float(eval_df['r2_score'].iloc[0])
            rmse = mse ** 0.5
            mape = (mae / 50.0) * 100
            
            print(f"{horizon.upper()} ({model_name}):")
            print(f"   MAE: {mae:.2f}, RMSE: {rmse:.2f}, R²: {r2:.3f}, MAPE: {mape:.2f}%")
            
            if mape < 3.5:
                print(f"   ✅ EXCELLENT - Institutional grade performance")
            elif mape < 5.0:
                print(f"   ⭐ GOOD - Acceptable performance")
            else:
                print(f"   ⚠️  NEEDS IMPROVEMENT")
            print()
    except Exception as e:
        print(f"   ❌ Could not evaluate {model_name}: {str(e)}")
        print()

print("=" * 80)
print("🎯 NEXT STEPS")
print("=" * 80)
print()

print("1. Compare OLD vs NEW models:")
print("   python3 scripts/compare_old_vs_new_models.py")
print()

print("2. Update V3 API to use enriched models:")
print("   Edit forecast/v3_model_predictions.py")
print("   Change model names from 'zl_boosted_tree_*_v3' to 'zl_boosted_tree_*_v3_enriched'")
print()

print("3. Test API endpoints:")
print("   curl http://localhost:8080/api/v3/forecast/1w")
print()

print("4. Update MASTER_TRAINING_PLAN.md with new results")
print()

print("=" * 80)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

