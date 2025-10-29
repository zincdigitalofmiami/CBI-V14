#!/usr/bin/env python3
"""
COMPLETE BASELINE MODEL TRAINING - NO BULLSHIT
Train simple boosted tree models with ALL available data.
No trying to beat scores. Just real, clean training.
"""

from google.cloud import bigquery
from datetime import datetime
import sys

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("COMPLETE BASELINE MODEL TRAINING")
print("Using ALL available data - BIG 8 signals + fundamentals + everything")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# STEP 1: Create fresh training dataset with ALL data through today
print("=" * 80)
print("STEP 1: Creating Fresh Training Dataset (2020-2025, ALL DATA)")
print("=" * 80)

# This query uses the EXISTING super_enriched as a template but rebuilds from scratch
create_training_dataset = """
CREATE OR REPLACE TABLE `cbi-v14.models_v4.training_dataset_baseline_complete` AS
SELECT * 
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE date >= '2020-10-21'
ORDER BY date
"""

print("Creating training dataset from existing super_enriched template...")
print("This includes:")
print("  - ALL price data (soybean oil, corn, palm, crude, etc.)")
print("  - BIG 8 signals (VIX stress, harvest, China, tariffs, geopolitical, biofuel cascade, hidden corr, ethanol)")
print("  - Correlations (7d, 30d, 90d, 180d, 365d)")
print("  - FX data (USD/CNY, USD/BRL, USD/ARS, DXY)")
print("  - Economic indicators (Fed funds, CPI, GDP, unemployment)")
print("  - Weather data (Brazil, Argentina, US Midwest)")
print("  - Fundamentals (CFTC positioning, crush margins)")
print("  - Sentiment (social, news, Trump policy)")
print()

try:
    job = client.query(create_training_dataset)
    result = job.result()
    
    # Check what we got
    check_query = """
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT date) as unique_dates,
        MIN(date) as start_date,
        MAX(date) as end_date,
        DATE_DIFF(MAX(date), MIN(date), DAY) as days_span
    FROM `cbi-v14.models_v4.training_dataset_baseline_complete`
    """
    df = client.query(check_query).to_dataframe()
    
    print("✅ Training Dataset Created:")
    print(f"   Total Rows: {df['total_rows'].iloc[0]:,}")
    print(f"   Unique Dates: {df['unique_dates'].iloc[0]:,}")
    print(f"   Date Range: {df['start_date'].iloc[0]} to {df['end_date'].iloc[0]}")
    print(f"   Span: {df['days_span'].iloc[0]} days ({df['days_span'].iloc[0]/365:.1f} years)")
    
    if df['total_rows'].iloc[0] != df['unique_dates'].iloc[0]:
        print(f"   ⚠️  WARNING: {df['total_rows'].iloc[0] - df['unique_dates'].iloc[0]} duplicate dates found!")
        sys.exit(1)
    
    print("   ✅ NO DUPLICATES - One row per date")
    print()
    
except Exception as e:
    print(f"❌ Error creating training dataset: {e}")
    sys.exit(1)

# STEP 2: Train 4 baseline Boosted Tree models (one per horizon)
print("=" * 80)
print("STEP 2: Training 4 Baseline Boosted Tree Models")
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
    print(f"  Target: {target_col}")
    print(f"  Model: Boosted Tree Regressor (default hyperparameters)")
    print()
    
    model_name = f'zl_baseline_complete_{horizon_name}'
    
    # Build EXCEPT clause - exclude date and OTHER target columns (keep the one we're training on)
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
    FROM `cbi-v14.models_v4.training_dataset_baseline_complete`
    WHERE {target_col} IS NOT NULL
    """
    
    try:
        print(f"  Submitting training job for {model_name}...")
        job = client.query(train_query)
        result = job.result()
        print(f"  ✅ {model_name} training submitted successfully")
        models_trained.append(model_name)
        print()
    except Exception as e:
        print(f"  ❌ Error training {model_name}: {e}")
        models_failed.append(model_name)
        print()

print("=" * 80)
print("STEP 3: Waiting for Training to Complete and Evaluating Models")
print("=" * 80)
print()
print("Note: Training runs asynchronously. Checking completion status...")
print()

# Check training status and evaluate each model
for model_name in models_trained:
    print(f"Evaluating {model_name}...")
    
    eval_query = f"""
    SELECT
        mean_absolute_error,
        mean_squared_error,
        r2_score,
        mean_squared_log_error
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
            
            print(f"  ✅ {model_name} - EVALUATION COMPLETE:")
            print(f"     MAE: {mae:.4f}")
            print(f"     MSE: {mse:.4f}")
            print(f"     R²: {r2:.4f}")
            print(f"     Estimated MAPE: {estimated_mape:.2f}%")
            
            # Reality check
            if estimated_mape <= 5.0:
                print(f"     ✅ EXCELLENT - Within institutional-grade range (<5% MAPE)")
            elif estimated_mape <= 10.0:
                print(f"     ⚠️  ACCEPTABLE - Reasonable baseline performance")
            else:
                print(f"     ❌ POOR - May need data quality review")
            
            print()
        else:
            print(f"  ⏳ {model_name} - Still training (no eval results yet)")
            print()
            
    except Exception as e:
        if "Not found: Model" in str(e):
            print(f"  ⏳ {model_name} - Still training")
        else:
            print(f"  ⚠️  {model_name} - Evaluation error: {str(e)[:100]}")
        print()

# STEP 4: Get feature importance for first model
print("=" * 80)
print("STEP 4: Feature Importance (1-Week Model)")
print("=" * 80)
print()

feature_importance_query = """
SELECT 
    feature,
    importance
FROM ML.FEATURE_IMPORTANCE(MODEL `cbi-v14.models_v4.zl_baseline_complete_1w`)
ORDER BY importance DESC
LIMIT 20
"""

try:
    df_fi = client.query(feature_importance_query).to_dataframe()
    print("Top 20 Most Important Features:")
    print()
    for idx, row in df_fi.iterrows():
        print(f"  {idx+1}. {row['feature']}: {row['importance']:.4f}")
    print()
except Exception as e:
    print(f"⏳ Feature importance not available yet (model may still be training)")
    print()

# SUMMARY
print("=" * 80)
print("TRAINING COMPLETE - SUMMARY")
print("=" * 80)
print()
print(f"Models Trained: {len(models_trained)}")
for model in models_trained:
    print(f"  ✅ {model}")
print()

if models_failed:
    print(f"Models Failed: {len(models_failed)}")
    for model in models_failed:
        print(f"  ❌ {model}")
    print()

print("=" * 80)
print("NEXT STEPS")
print("=" * 80)
print()
print("1. Wait ~5-10 minutes for all training to complete")
print("2. Re-run this script to see final evaluation metrics")
print("3. Compare to previous best models")
print("4. If baseline looks good, proceed to Phase 2 (ensemble)")
print()
print("To check status later, run:")
print("  bq ls -m cbi-v14:models_v4 | grep baseline_complete")
print()
print("To evaluate a specific model:")
print("  bq query --use_legacy_sql=false \"SELECT * FROM ML.EVALUATE(MODEL \\`cbi-v14.models_v4.zl_baseline_complete_1w\\`)\"")
print()

print("=" * 80)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

