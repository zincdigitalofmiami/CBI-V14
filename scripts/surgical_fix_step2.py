#!/usr/bin/env python3
"""
Scale up to complete model set once simple model is working
"""
from google.cloud import bigquery
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print(f"STEP 2: SCALE UP TO FULL MODEL SET - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*60)

# Verify the simple model exists and works
try:
    model = client.get_model('cbi-v14.models.zl_boosted_tree_1w_simple')
    print("✓ Simple model exists, now scaling up")
    
    # Try to evaluate it
    eval_query = """
    SELECT mean_absolute_error as MAE, r2_score as R2
    FROM ML.EVALUATE(MODEL `cbi-v14.models.zl_boosted_tree_1w_simple`)
    """
    result = client.query(eval_query).to_dataframe()
    if not result.empty:
        print(f"  Simple model MAE: {result.MAE.iloc[0]:.4f}")
        print(f"  Simple model R²:  {result.R2.iloc[0]:.4f}")
except Exception as e:
    print("✗ Simple model doesn't exist yet or is still training.")
    print("  Run 'bq ls --models cbi-v14:models | grep simple' to check status")
    print(f"  Error: {str(e)[:100]}")
    exit(1)

print("\n" + "="*60)
print("TRAINING FULL MODEL SET (v3)")
print("="*60)

# Define models to train
models = [
    # Boosted Trees (with more features)
    ('zl_boosted_tree_1w_v3', 'BOOSTED_TREE_REGRESSOR', 'target_1w'),
    ('zl_boosted_tree_1m_v3', 'BOOSTED_TREE_REGRESSOR', 'target_1m'),
    ('zl_boosted_tree_3m_v3', 'BOOSTED_TREE_REGRESSOR', 'target_3m'),
    ('zl_boosted_tree_6m_v3', 'BOOSTED_TREE_REGRESSOR', 'target_6m'),
    
    # Linear (baseline models)
    ('zl_linear_1w_v3', 'LINEAR_REG', 'target_1w'),
    ('zl_linear_1m_v3', 'LINEAR_REG', 'target_1m'),
    ('zl_linear_3m_v3', 'LINEAR_REG', 'target_3m'),
    ('zl_linear_6m_v3', 'LINEAR_REG', 'target_6m'),
    
    # ARIMA (time series)
    ('zl_arima_1w_v3', 'ARIMA_PLUS', 'target_1w'),
    ('zl_arima_1m_v3', 'ARIMA_PLUS', 'target_1m')
]

successful_jobs = []
failed_jobs = []

# Train each model
for model_name, model_type, target in models:
    print(f"\nTraining {model_name} ({model_type})...")
    
    # Customize query based on model type
    if model_type == 'BOOSTED_TREE_REGRESSOR':
        # Use more features for boosted trees
        query = f"""
        CREATE OR REPLACE MODEL `cbi-v14.models.{model_name}`
        OPTIONS(
          model_type='{model_type}',
          input_label_cols=['{target}'],
          max_iterations=75,
          early_stop=TRUE,
          min_tree_child_weight=10,
          subsample=0.85,
          max_tree_depth=8
        ) AS
        SELECT
          zl_price_current,
          zl_price_lag1,
          zl_price_lag7,
          zl_price_lag30,
          return_1d,
          return_7d,
          ma_7d,
          ma_30d,
          volatility_30d,
          vix_level,
          crude_price,
          palm_price,
          corn_price,
          dxy_level,
          corr_zl_crude_30d,
          corr_zl_palm_30d,
          corr_zl_vix_30d,
          corr_zl_dxy_30d,
          cftc_commercial_net,
          cftc_managed_net,
          cftc_open_interest,
          treasury_10y_yield,
          econ_gdp_growth,
          econ_inflation_rate,
          news_article_count,
          {target}
        FROM `cbi-v14.models.training_dataset`
        WHERE {target} IS NOT NULL
        """
    elif model_type == 'LINEAR_REG':
        # Simpler features for linear models
        query = f"""
        CREATE OR REPLACE MODEL `cbi-v14.models.{model_name}`
        OPTIONS(
          model_type='{model_type}',
          input_label_cols=['{target}'],
          optimize_strategy='AUTO_STRATEGY'
        ) AS
        SELECT
          zl_price_current,
          zl_price_lag1,
          zl_price_lag7,
          return_1d,
          return_7d,
          ma_30d,
          vix_level,
          {target}
        FROM `cbi-v14.models.training_dataset`
        WHERE {target} IS NOT NULL
        """
    else:  # ARIMA_PLUS
        query = f"""
        CREATE OR REPLACE MODEL `cbi-v14.models.{model_name}`
        OPTIONS(
          model_type='ARIMA_PLUS',
          time_series_timestamp_col='date',
          time_series_data_col='{target}',
          auto_arima=TRUE,
          data_frequency='DAILY'
        ) AS
        SELECT
          date,
          {target}
        FROM `cbi-v14.models.training_dataset`
        WHERE {target} IS NOT NULL
        ORDER BY date
        """
    
    try:
        job = client.query(query)
        print(f"  ✓ Job submitted: {job.job_id[:20]}...")
        successful_jobs.append((model_name, job.job_id))
    except Exception as e:
        print(f"  ✗ Error: {str(e)[:80]}")
        failed_jobs.append((model_name, str(e)[:80]))

print("\n" + "="*60)
print("TRAINING SUMMARY")
print("="*60)
print(f"Successfully submitted: {len(successful_jobs)} jobs")
print(f"Failed: {len(failed_jobs)} jobs")

if successful_jobs:
    print("\nModels training:")
    for name, _ in successful_jobs[:5]:
        print(f"  ✓ {name}")
    if len(successful_jobs) > 5:
        print(f"  ... and {len(successful_jobs)-5} more")

if failed_jobs:
    print("\nFailed models:")
    for name, error in failed_jobs:
        print(f"  ✗ {name}: {error}")

print("\n" + "="*60)
print("NEXT STEPS")
print("="*60)
print("1. Wait 5-10 minutes for models to complete")
print("2. Run: bq ls --models cbi-v14:models | grep v3")
print("3. Once complete, run surgical_fix_step3.py to clean up")
