#!/usr/bin/env python3
"""
Fix NULL-only columns and train baseline models
Identifies columns with all NULLs, removes them, then trains clean models
"""

from google.cloud import bigquery
from datetime import datetime
import sys

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("FIX NULL COLUMNS AND TRAIN BASELINE MODELS")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# STEP 1: Identify columns with all NULLs
print("=" * 80)
print("STEP 1: Identifying NULL-only Columns")
print("=" * 80)

# Get all column names
columns_query = """
SELECT column_name
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'training_dataset_super_enriched'
AND column_name NOT IN ('date', 'target_1w', 'target_1m', 'target_3m', 'target_6m')
ORDER BY ordinal_position
"""

df_cols = client.query(columns_query).to_dataframe()
all_columns = df_cols['column_name'].tolist()

print(f"Total columns to check: {len(all_columns)}")
print()

# Check each column for NULL percentage
null_columns = []
good_columns = []

print("Checking NULL percentages...")
for idx, col in enumerate(all_columns):
    if idx % 20 == 0:
        print(f"  Checked {idx}/{len(all_columns)} columns...")
    
    try:
        null_check_query = f"""
        SELECT 
            COUNTIF({col} IS NULL) as null_count,
            COUNT(*) as total_count
        FROM `cbi-v14.models_v4.training_dataset_super_enriched`
        """
        df_null = client.query(null_check_query).to_dataframe()
        
        null_count = df_null['null_count'].iloc[0]
        total_count = df_null['total_count'].iloc[0]
        null_pct = (null_count / total_count) * 100
        
        if null_count == total_count:
            null_columns.append(col)
        else:
            good_columns.append(col)
    except Exception as e:
        # If there's an error checking, assume it's bad and exclude it
        print(f"  ⚠️  Error checking {col}: {str(e)[:50]}")
        null_columns.append(col)

print(f"  Checked {len(all_columns)}/{len(all_columns)} columns")
print()

print(f"✅ Good columns (have data): {len(good_columns)}")
print(f"❌ NULL-only columns (to exclude): {len(null_columns)}")

if null_columns:
    print()
    print("Columns to exclude:")
    for col in null_columns:
        print(f"  - {col}")

print()

# STEP 2: Create clean training dataset
print("=" * 80)
print("STEP 2: Creating Clean Training Dataset (No NULL-only columns)")
print("=" * 80)

# Keep date and targets, plus all good columns
columns_to_keep = ['date', 'target_1w', 'target_1m', 'target_3m', 'target_6m'] + good_columns
columns_str = ', '.join([f'`{col}`' for col in columns_to_keep])

create_clean_query = f"""
CREATE OR REPLACE TABLE `cbi-v14.models_v4.training_dataset_baseline_clean` AS
SELECT {columns_str}
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
ORDER BY date
"""

print(f"Creating clean dataset with {len(columns_to_keep)} columns...")
print()

try:
    job = client.query(create_clean_query)
    result = job.result()
    
    # Verify
    verify_query = """
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT date) as unique_dates,
        MIN(date) as start_date,
        MAX(date) as end_date
    FROM `cbi-v14.models_v4.training_dataset_baseline_clean`
    """
    df_verify = client.query(verify_query).to_dataframe()
    
    print("✅ Clean Training Dataset Created:")
    print(f"   Total Rows: {df_verify['total_rows'].iloc[0]:,}")
    print(f"   Unique Dates: {df_verify['unique_dates'].iloc[0]:,}")
    print(f"   Date Range: {df_verify['start_date'].iloc[0]} to {df_verify['end_date'].iloc[0]}")
    print(f"   Features: {len(good_columns)}")
    print()
    
except Exception as e:
    print(f"❌ Error creating clean dataset: {e}")
    sys.exit(1)

# STEP 3: Train 4 baseline models
print("=" * 80)
print("STEP 3: Training 4 Baseline Boosted Tree Models")
print("=" * 80)
print()

horizons = {
    '1w': 'target_1w',
    '1m': 'target_1m',
    '3m': 'target_3m',
    '6m': 'target_6m'
}

models_trained = []
models_failed = []

for horizon_name, target_col in horizons.items():
    print(f"Training {horizon_name} model...")
    
    model_name = f'zl_baseline_clean_{horizon_name}'
    
    # Exclude date and other target columns
    other_targets = [t for t in ['target_1w', 'target_1m', 'target_3m', 'target_6m'] if t != target_col]
    except_clause = ', '.join(['date'] + other_targets)
    
    train_query = f"""
    CREATE OR REPLACE MODEL `cbi-v14.models_v4.{model_name}`
    OPTIONS(
        model_type='BOOSTED_TREE_REGRESSOR',
        input_label_cols=['{target_col}'],
        data_split_method='RANDOM',
        data_split_eval_fraction=0.2,
        enable_global_explain=TRUE,
        max_iterations=50,
        early_stop=TRUE,
        min_rel_progress=0.01,
        learn_rate=0.1,
        subsample=0.8,
        max_tree_depth=8
    ) AS
    SELECT * EXCEPT({except_clause})
    FROM `cbi-v14.models_v4.training_dataset_baseline_clean`
    WHERE {target_col} IS NOT NULL
    """
    
    try:
        print(f"  Submitting training job for {model_name}...")
        job = client.query(train_query)
        result = job.result()
        print(f"  ✅ {model_name} training completed successfully")
        models_trained.append(model_name)
        print()
    except Exception as e:
        print(f"  ❌ Error training {model_name}: {str(e)[:200]}")
        models_failed.append(model_name)
        print()

# STEP 4: Evaluate models
print("=" * 80)
print("STEP 4: Evaluating Trained Models")
print("=" * 80)
print()

results = []

for model_name in models_trained:
    print(f"Evaluating {model_name}...")
    
    eval_query = f"""
    SELECT
        mean_absolute_error,
        mean_squared_error,
        r2_score
    FROM ML.EVALUATE(MODEL `cbi-v14.models_v4.{model_name}`)
    """
    
    try:
        df_eval = client.query(eval_query).to_dataframe()
        
        if len(df_eval) > 0:
            mae = df_eval['mean_absolute_error'].iloc[0]
            mse = df_eval['mean_squared_error'].iloc[0]
            r2 = df_eval['r2_score'].iloc[0]
            
            # Estimate MAPE (assuming ~$50 avg price)
            estimated_mape = (mae / 50.0) * 100
            
            results.append({
                'model': model_name,
                'mae': mae,
                'mse': mse,
                'r2': r2,
                'mape_est': estimated_mape
            })
            
            print(f"  ✅ MAE: {mae:.4f} | R²: {r2:.4f} | Est. MAPE: {estimated_mape:.2f}%")
            
            if estimated_mape <= 5.0:
                print(f"     ✅ EXCELLENT - Institutional-grade (<5% MAPE)")
            elif estimated_mape <= 10.0:
                print(f"     ✅ GOOD - Reasonable baseline")
            else:
                print(f"     ⚠️  ACCEPTABLE - Room for improvement")
            print()
    except Exception as e:
        print(f"  ⚠️  Evaluation error: {str(e)[:100]}")
        print()

# SUMMARY
print("=" * 80)
print("TRAINING COMPLETE - SUMMARY")
print("=" * 80)
print()

print(f"Columns Excluded (NULL-only): {len(null_columns)}")
print(f"Features Used: {len(good_columns)}")
print(f"Models Trained: {len(models_trained)}")
print(f"Models Failed: {len(models_failed)}")
print()

if results:
    print("Model Performance:")
    print()
    for r in results:
        print(f"  {r['model']}:")
        print(f"    MAE: {r['mae']:.4f} | R²: {r['r2']:.4f} | Est. MAPE: {r['mape_est']:.2f}%")
    print()

print("=" * 80)
print("BASELINE MODELS READY")
print("=" * 80)
print()
print("Next steps:")
print("1. Review model performance above")
print("2. If satisfactory, proceed to Phase 2 (ensemble)")
print("3. If not, investigate feature engineering or data quality")
print()
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)




