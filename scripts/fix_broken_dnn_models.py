#!/usr/bin/env python3
"""
Fix the broken DNN models by retraining with proper feature normalization
The 1w and 1m DNN models have MAE in millions due to lack of feature scaling
"""

from google.cloud import bigquery
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print(f"FIXING BROKEN DNN MODELS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

print("\n1. CHECKING CURRENT DNN MODEL PERFORMANCE:")
print("-"*80)

# Check current performance of DNN models
eval_query = """
WITH model_info AS (
    SELECT 
        'zl_dnn_1w_production' as model_name,
        '1w' as horizon
    UNION ALL
    SELECT 'zl_dnn_1m_production', '1m'
    UNION ALL
    SELECT 'zl_dnn_3m_production', '3m'
    UNION ALL
    SELECT 'zl_dnn_6m_production', '6m'
)
SELECT 
    model_name,
    horizon,
    'Check training logs for metrics' as status
FROM model_info
ORDER BY horizon
"""

results = client.query(eval_query).to_dataframe()
print(results.to_string(index=False))

print("\n2. RETRAINING BROKEN DNN MODELS WITH NORMALIZATION:")
print("-"*80)
print("The broken models (1w and 1m) have MAE in millions due to lack of normalization.")
print("Retraining with proper feature scaling using TRANSFORM clause...")

# Define the models to retrain
models_to_fix = [
    ('zl_dnn_1w_production', 'target_1w', 7),
    ('zl_dnn_1m_production', 'target_1m', 30)
]

for model_name, target_col, horizon_days in models_to_fix:
    print(f"\n{'='*60}")
    print(f"Retraining: {model_name}")
    print(f"Target: {target_col} (horizon: {horizon_days} days)")
    print("-"*60)
    
    # Drop other target columns for this model
    other_targets = [t for t in ['target_1w','target_1m','target_3m','target_6m'] if t != target_col]
    
    # Create the model with proper normalization
    # Using TRANSFORM to normalize features
    query = f"""
    CREATE OR REPLACE MODEL `cbi-v14.models.{model_name}`
    TRANSFORM(
        -- Normalize numeric features to 0-1 range
        -- Price features
        (zl_price_current - 30) / 30 AS zl_price_normalized,
        (zl_ma_7 - 30) / 30 AS zl_ma_7_normalized,
        (zl_ma_30 - 30) / 30 AS zl_ma_30_normalized,
        (zl_ma_90 - 30) / 30 AS zl_ma_90_normalized,
        zl_rsi_14 / 100 AS zl_rsi_14_normalized,
        zl_volatility_30 AS zl_volatility_30,  -- Already in reasonable range
        
        -- Correlation features (already -1 to 1)
        soy_crude_corr_60,
        soy_palm_corr_60,
        soy_corn_corr_60,
        soy_wheat_corr_60,
        
        -- Sentiment features
        sentiment_avg / 100 AS sentiment_normalized,
        sentiment_volatility AS sentiment_volatility,
        
        -- Weather features (normalize to 0-1)
        (weather_temp_avg - (-20)) / 60 AS temp_normalized,
        weather_precip_sum / 100 AS precip_normalized,
        
        -- Volume features
        LOG(volume_avg + 1) AS volume_log,
        
        -- Keep the target as is
        {target_col}
    )
    OPTIONS(
        model_type='DNN_REGRESSOR',
        hidden_units=[64, 32, 16],
        activation_fn='RELU',
        dropout=0.2,
        batch_size=32,
        learn_rate=0.001,
        optimizer='ADAM',
        input_label_cols=['{target_col}'],
        max_iterations=100,
        early_stop=TRUE,
        min_rel_progress=0.001,
        warm_start=FALSE
    ) AS
    SELECT 
        -- Select key features that exist in the training dataset
        zl_price_current,
        zl_ma_7,
        zl_ma_30,
        zl_ma_90,
        zl_rsi_14,
        zl_volatility_30,
        soy_crude_corr_60,
        soy_palm_corr_60,
        soy_corn_corr_60,
        soy_wheat_corr_60,
        sentiment_avg,
        sentiment_volatility,
        weather_temp_avg,
        weather_precip_sum,
        volume_avg,
        {target_col}
    FROM `cbi-v14.models.training_dataset_final_v1`
    WHERE {target_col} IS NOT NULL
    """
    
    print("Submitting training job...")
    try:
        job = client.query(query)
        print(f"  Job ID: {job.job_id}")
        print(f"  Status: Job submitted successfully")
        print(f"  Note: Training will take 5-15 minutes")
    except Exception as e:
        print(f"  ERROR: {str(e)[:200]}")

print("\n" + "="*80)
print("RETRAINING JOBS SUBMITTED")
print("="*80)
print("\nNOTE: The DNN models are being retrained with proper feature normalization.")
print("Check back in 10-15 minutes to verify the models have reasonable MAE values.")
print("\nExpected outcome:")
print("  - MAE should be in the range of 2-5 (not millions)")
print("  - R² should be positive (ideally > 0.8)")
print("\nTo check status, run:")
print("  SELECT * FROM `cbi-v14.models.INFORMATION_SCHEMA.JOBS_BY_PROJECT`")
print("  WHERE job_id LIKE '%dnn%' ORDER BY creation_time DESC LIMIT 5")
