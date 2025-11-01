#!/usr/bin/env python3
"""
predict_all_horizons.py
Generate predictions for all 4 horizons using Vertex AI endpoint deploy/predict/undeploy pattern
"""

import json
import pandas as pd
from google.cloud import bigquery, aiplatform

PROJECT = "cbi-v14"
LOCATION = "us-central1"
BQ = bigquery.Client(project=PROJECT, location=LOCATION)

MODELS = {
    "1W": "575258986094264320",
    "1M": "274643710967283712",
    "3M": "3157158578716934144",
    "6M": "3788577320223113216",
}

# Use existing endpoint or create a temporary one
# For now, we'll use the endpoint deploy/undeploy pattern per model
MACHINE = "n1-standard-2"

def load_predict_row():
    """Load single row from predict_frame_209"""
    df = BQ.query("""
        SELECT * FROM `cbi-v14.models_v4.predict_frame_209` LIMIT 1
    """).to_dataframe()
    
    # Convert pandas NaN → None (Vertex requirement)
    # Also convert int64 to int for JSON serialization
    record = df.to_dict(orient="records")[0]
    
    # Clean up the record for Vertex AI
    cleaned = {}
    for k, v in record.items():
        if pd.isna(v):
            cleaned[k] = None
        elif isinstance(v, (pd.Int64Dtype, pd.Int32Dtype)):
            cleaned[k] = int(v) if pd.notna(v) else None
        else:
            cleaned[k] = v
    
    return cleaned

def predict_once(model_id, instance):
    """Deploy model, predict, undeploy"""
    aiplatform.init(project=PROJECT, location=LOCATION)
    
    # Get model using resource_name
    model_resource_name = f"projects/{PROJECT}/locations/{LOCATION}/models/{model_id}"
    model = aiplatform.Model(model_resource_name=model_resource_name)
    
    # Create temporary endpoint
    endpoint = aiplatform.Endpoint.create(display_name=f"temp_endpoint_{model_id}")
    
    try:
        # Deploy model
        deployed = endpoint.deploy(
            model=model,
            machine_type=MACHINE,
            min_replica_count=1,
            max_replica_count=1,
            deployed_model_display_name=f"temp_{model_id}"
        )
        
        # Wait for deployment
        import time
        time.sleep(30)  # Give it time to deploy
        
        # Predict
        resp = endpoint.predict(instances=[instance])
        
        # Extract prediction value
        pred = resp.predictions[0]
        if isinstance(pred, dict):
            val = float(pred.get('value') or pred.get('prediction') or list(pred.values())[0])
        else:
            val = float(pred)
        
        return val, endpoint.name
    
    finally:
        # Undeploy and delete endpoint
        try:
            endpoint.undeploy(deployed_model_id=deployed.id)
        except:
            pass
        try:
            endpoint.delete()
        except:
            pass

def write_prediction(horizon, predicted_price, model_id):
    """Write prediction to BigQuery"""
    query = """
        INSERT INTO `cbi-v14.predictions.monthly_vertex_predictions`
        (horizon, prediction_date, target_date, predicted_price, confidence_lower, confidence_upper, mape, model_id, model_name, created_at)
        SELECT
          @horizon,
          CURRENT_DATE(),
          DATE_ADD((SELECT date FROM `cbi-v14.models_v4.predict_frame_209` LIMIT 1),
                   INTERVAL CASE @horizon 
                     WHEN '1W' THEN 7 
                     WHEN '1M' THEN 30 
                     WHEN '3M' THEN 90 
                     WHEN '6M' THEN 180 
                   END DAY),
          @price,
          NULL, NULL, NULL,
          @model_id,
          @model_name,
          CURRENT_TIMESTAMP()
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("horizon", "STRING", horizon),
            bigquery.ScalarQueryParameter("price", "FLOAT64", predicted_price),
            bigquery.ScalarQueryParameter("model_id", "STRING", model_id),
            bigquery.ScalarQueryParameter("model_name", "STRING", f"vertex_automl_{horizon.lower()}"),
        ]
    )
    
    BQ.query(query, job_config=job_config).result()

if __name__ == "__main__":
    print("Loading predict row...")
    row = load_predict_row()
    print(f"✅ Loaded row for date: {row.get('date')}")
    
    results = {}
    for hz, mid in MODELS.items():
        print(f"\n🔮 Predicting {hz} (model {mid})...")
        try:
            yhat, endpoint_name = predict_once(mid, row)
            print(f"  ✅ Prediction: {yhat}")
            write_prediction(hz, yhat, mid)
            print(f"  ✅ Written to BigQuery")
            results[hz] = yhat
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results[hz] = None
    
    print("\n" + "="*50)
    print("✅ All horizons processed:")
    for hz, val in results.items():
        print(f"  {hz}: {val}")
    print("="*50)

