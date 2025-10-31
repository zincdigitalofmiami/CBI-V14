#!/usr/bin/env python3
"""
TEMPORARY ENDPOINT STRATEGY:
1. Deploy models to endpoints
2. Get predictions  
3. Save to BigQuery
4. UNDEPLOY immediately
Cost: ~$2-5 for a few hours
"""

from google.cloud import aiplatform, bigquery
from datetime import datetime
import time

PROJECT_ID = 'cbi-v14'
REGION = 'us-central1'

aiplatform.init(project=PROJECT_ID, location=REGION)
bq_client = bigquery.Client(project=PROJECT_ID)

MODELS = {
    "1w": "575258986094264320",
    "1m": "274643710967283712",
    "3m": "3157158578716934144",
    "6m": "3788577320223113216"
}

print("="*80)
print("TEMPORARY ENDPOINT PREDICTIONS")
print("="*80)

# Get input features
query = """
SELECT * EXCEPT(target_1w, target_1m, target_3m, target_6m)
FROM `cbi-v14.models.training_dataset`
ORDER BY date DESC
LIMIT 1
"""
features_df = bq_client.query(query).to_dataframe()
features = features_df.iloc[0].to_dict()

print(f"✅ Got features: {len(features)} columns")

predictions = {}
endpoints_to_cleanup = []

try:
    for horizon, model_id in MODELS.items():
        print(f"\n{'='*80}")
        print(f"🚀 {horizon.upper()}")
        print(f"{'='*80}")
        
        # Get model
        model = aiplatform.Model(f"projects/{PROJECT_ID}/locations/{REGION}/models/{model_id}")
        
        # Create endpoint
        endpoint = aiplatform.Endpoint.create(
            display_name=f"temp_{horizon}_endpoint",
            description=f"Temporary endpoint for {horizon} predictions"
        )
        endpoints_to_cleanup.append(endpoint)
        print(f"✅ Endpoint created: {endpoint.resource_name}")
        
        # Deploy model (minimum replicas)
        print(f"⏳ Deploying model...")
        endpoint.deploy(
            model=model,
            deployed_model_display_name=f"temp_{horizon}_deployment",
            machine_type="n1-standard-2",
            min_replica_count=1,
            max_replica_count=1,
            sync=True
        )
        print(f"✅ Model deployed")
        
        # Make prediction
        print(f"🔮 Getting prediction...")
        prediction = endpoint.predict(instances=[features])
        pred_value = prediction.predictions[0][0]
        print(f"✅ Prediction: ${pred_value:.2f}")
        
        predictions[horizon] = {
            'forecast': float(pred_value),
            'model_id': model_id,
            'timestamp': datetime.now()
        }
        
        # Undeploy immediately (stop billing)
        print(f"💰 Undeploying to stop billing...")
        deployed_models = endpoint.list_models()
        for deployed_model in deployed_models:
            endpoint.undeploy(deployed_model_id=deployed_model.id, sync=True)
        print(f"✅ Undeployed (billing stopped)")

    # Save all predictions to BigQuery
    print(f"\n{'='*80}")
    print("💾 SAVING TO BIGQUERY")
    print(f"{'='*80}")
    
    current_price = float(features_df['zl_price_current'].iloc[0])
    
    row = {
        "prediction_date": datetime.now().date(),
        "current_price": current_price,
        "forecast_1w": predictions['1w']['forecast'],
        "forecast_1m": predictions['1m']['forecast'],
        "forecast_3m": predictions['3m']['forecast'],
        "forecast_6m": predictions['6m']['forecast'],
        "model_1w_id": predictions['1w']['model_id'],
        "model_1m_id": predictions['1m']['model_id'],
        "model_3m_id": predictions['3m']['model_id'],
        "model_6m_id": predictions['6m']['model_id'],
        "created_timestamp": datetime.now()
    }
    
    # Generate signals
    for horizon in ['1w', '1m', '3m', '6m']:
        forecast = predictions[horizon]['forecast']
        change = ((forecast - current_price) / current_price) * 100
        
        if change > 2:
            signal = "BUY"
        elif change < -2:
            signal = "SELL"
        else:
            signal = "HOLD"
        
        row[f"signal_{horizon}"] = signal
        row[f"confidence_{horizon}"] = 0.85
        
        print(f"{horizon.upper()}: ${forecast:.2f} ({change:+.1f}%) → {signal}")
    
    import pandas as pd
    df = pd.DataFrame([row])
    
    table_id = "cbi-v14.predictions.daily_forecasts"
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
    job = bq_client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    
    print(f"\n✅ SAVED TO {table_id}")
    
finally:
    # Cleanup: Delete endpoints
    print(f"\n{'='*80}")
    print("🗑️  CLEANUP: Deleting endpoints")
    print(f"{'='*80}")
    
    for endpoint in endpoints_to_cleanup:
        try:
            endpoint.delete(sync=True)
            print(f"✅ Deleted {endpoint.display_name}")
        except Exception as e:
            print(f"⚠️  Could not delete {endpoint.display_name}: {e}")

print(f"\n{'='*80}")
print("✅ DONE - ALL ENDPOINTS REMOVED")
print("💰 Cost: ~$1-2 for deployment time")
print("📊 Dashboard can now read from predictions.daily_forecasts")
print(f"{'='*80}")

