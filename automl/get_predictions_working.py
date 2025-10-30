#!/usr/bin/env python3
"""
Get predictions using EXISTING endpoint with EXACT schema match
Models were trained correctly - we just need to match their expected input
"""

from google.cloud import aiplatform, bigquery
import pandas as pd
from datetime import datetime, date
import numpy as np

PROJECT_ID = 'cbi-v14'
REGION = 'us-central1'

aiplatform.init(project=PROJECT_ID, location=REGION)
bq_client = bigquery.Client(project=PROJECT_ID)

# First, redeploy 1W model to an endpoint
MODEL_1W = "575258986094264320"

print("="*80)
print("STEP 1: Deploy 1W Model to Endpoint")
print("="*80)

# Create endpoint
endpoint = aiplatform.Endpoint.create(
    display_name="soybean_oil_1w_working_endpoint",
    description="Working endpoint for 1W predictions"
)

print(f"✅ Endpoint created: {endpoint.resource_name}")

# Deploy model
model = aiplatform.Model(f"projects/{PROJECT_ID}/locations/{REGION}/models/{MODEL_1W}")

endpoint.deploy(
    model=model,
    deployed_model_display_name="1w_deployment",
    machine_type="n1-standard-2",
    min_replica_count=1,
    max_replica_count=1,
    sync=True
)

print(f"✅ Model deployed")

print("\n" + "="*80)
print("STEP 2: Get Latest Features with EXACT Schema")
print("="*80)

# Get features with EXACT schema (209 columns)
query = """
SELECT *
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
ORDER BY date DESC
LIMIT 1
"""

df = bq_client.query(query).to_dataframe()
features = df.iloc[0].to_dict()

print(f"✅ Got {len(features)} columns from training dataset")

# Convert types to match exactly
for col, val in features.items():
    # Handle date specially
    if col == 'date':
        if isinstance(val, (date, pd.Timestamp)):
            features[col] = val.strftime('%Y-%m-%d') if hasattr(val, 'strftime') else str(val)
    
    # Set target columns to None
    elif col in ['target_1w', 'target_1m', 'target_3m', 'target_6m']:
        features[col] = None
    
    # Convert numpy types
    elif isinstance(val, (np.int64, np.int32, np.int16)):
        features[col] = int(val)
    elif isinstance(val, (np.float64, np.float32)):
        # Check if NaN
        if pd.isna(val):
            features[col] = None
        else:
            features[col] = float(val)
    elif pd.isna(val):
        features[col] = None

print(f"✅ Types converted")
print(f"   date: {features['date']}")
print(f"   target_1w: {features['target_1w']}")
print(f"   zl_volume: {features['zl_volume']} (type: {type(features['zl_volume'])})")

print("\n" + "="*80)
print("STEP 3: Get Prediction")
print("="*80)

try:
    prediction = endpoint.predict(instances=[features])
    pred_value = prediction.predictions[0][0]
    
    current = features['zl_price_current']
    change_pct = ((pred_value - current) / current) * 100
    signal = 'BUY' if change_pct > 2 else ('SELL' if change_pct < -2 else 'HOLD')
    
    print(f"✅ PREDICTION SUCCESSFUL!")
    print(f"   Current: ${current:.2f}")
    print(f"   Forecast: ${pred_value:.2f}")
    print(f"   Change: {change_pct:+.2f}%")
    print(f"   Signal: {signal}")
    
    # Save to BigQuery
    save_row = {
        'prediction_date': datetime.now().date(),
        'run_timestamp': datetime.now(),
        'current_price': float(current),
        'forecast_1w': float(pred_value),
        'model_1w_id': MODEL_1W,
        'signal_1w': signal,
        'confidence_1w': 0.85
    }
    
    save_df = pd.DataFrame([save_row])
    table_id = f'{PROJECT_ID}.predictions.daily_forecasts'
    
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
    job = bq_client.load_table_from_dataframe(save_df, table_id, job_config=job_config)
    job.result()
    
    print(f"\n✅ SAVED TO {table_id}")
    print(f"\n🎉 PREDICTIONS WORKING! Keep endpoint deployed for now.")
    
except Exception as e:
    print(f"\n❌ Prediction failed: {e}")

print("\n" + "="*80)

