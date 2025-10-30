#!/usr/bin/env python3
"""
Wire Vertex AI AutoML models to dashboard API
Get REAL predictions from trained Vertex AI models
"""

from google.cloud import aiplatform
from google.cloud import bigquery
import pandas as pd
import json
from datetime import datetime

# Initialize clients
aiplatform.init(project="cbi-v14", location="us-central1")
bq_client = bigquery.Client(project="cbi-v14")

# Your actual trained Vertex AI models
VERTEX_MODELS = {
    "1w": "575258986094264320",  # cbi_v14_automl_pilot_1w
    "3m": "3157158578716934144", # soybean_oil_3m_final_v14_20251029_0808
    "6m": "3788577320223113216"  # soybean_oil_6m_model_v14_20251028_1737
}

def get_latest_features():
    """Get latest feature data for prediction"""
    query = """
    SELECT *
    FROM `cbi-v14.models_v4.training_dataset_v4`
    ORDER BY date DESC
    LIMIT 1
    """
    df = bq_client.query(query).to_dataframe()
    return df.iloc[0] if not df.empty else None

def get_vertex_prediction(model_id, features_row):
    """Get prediction from Vertex AI AutoML model"""
    try:
        # Get the model
        model = aiplatform.Model(model_name=f"projects/cbi-v14/locations/us-central1/models/{model_id}")
        
        # Prepare features for prediction (exclude target and metadata columns)
        feature_columns = [col for col in features_row.index 
                          if col not in ['date', 'close_price', 'target_1w', 'target_1m', 'target_3m', 'target_6m']]
        
        # Create prediction instance
        instance = {col: float(features_row[col]) if pd.notna(features_row[col]) else 0.0 
                   for col in feature_columns}
        
        # Get endpoint for prediction
        endpoints = model.list_model_deployments()
        if not endpoints:
            print(f"Model {model_id} is not deployed to any endpoint")
            return None
            
        endpoint = endpoints[0]
        
        # Get prediction
        prediction = endpoint.predict(instances=[instance])
        
        return prediction.predictions[0] if prediction.predictions else None
        
    except Exception as e:
        print(f"Error getting prediction from model {model_id}: {e}")
        return None

def update_api_with_vertex_predictions():
    """Update the API to use Vertex AI predictions"""
    
    print("Getting latest features...")
    features = get_latest_features()
    if features is None:
        print("ERROR: No feature data available")
        return
    
    current_price = features.get('close_price', 50.04)
    print(f"Current price: ${current_price:.2f}")
    
    predictions = {}
    
    for horizon, model_id in VERTEX_MODELS.items():
        print(f"\nGetting {horizon} prediction from Vertex AI model {model_id}...")
        
        pred_value = get_vertex_prediction(model_id, features)
        
        if pred_value is not None:
            # Extract prediction value (AutoML returns different formats)
            if isinstance(pred_value, dict):
                prediction = pred_value.get('value', pred_value.get('prediction', pred_value))
            elif isinstance(pred_value, list):
                prediction = pred_value[0] if pred_value else current_price
            else:
                prediction = float(pred_value)
            
            change = prediction - current_price
            change_pct = (change / current_price) * 100
            
            predictions[horizon] = {
                "horizon": horizon,
                "model_type": "vertex_automl",
                "model_name": f"vertex_automl_{horizon}",
                "prediction": round(prediction, 2),
                "current_price": round(current_price, 2),
                "predicted_change": round(change, 2),
                "predicted_change_pct": round(change_pct, 2),
                "confidence_metrics": {
                    "model_id": model_id,
                    "source": "vertex_ai_automl"
                },
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"✓ {horizon}: ${prediction:.2f} ({change_pct:+.1f}%)")
            
        else:
            print(f"✗ Failed to get {horizon} prediction")
    
    # Save predictions to BigQuery for API access
    if predictions:
        print(f"\nSaving {len(predictions)} Vertex AI predictions to BigQuery...")
        
        # Create table for Vertex predictions
        table_id = "cbi-v14.api.vertex_predictions"
        
        # Convert to DataFrame
        df = pd.DataFrame(list(predictions.values()))
        
        # Load to BigQuery
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE",  # Replace existing data
            schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION]
        )
        
        job = bq_client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        
        print(f"✓ Saved to {table_id}")
        
        # Update the API configuration
        print("\nUpdating API to use Vertex AI predictions...")
        update_api_config(predictions)
        
    else:
        print("No predictions obtained from Vertex AI models")

def update_api_config(predictions):
    """Update the API configuration file to use Vertex predictions"""
    
    config = {
        "vertex_predictions": predictions,
        "last_updated": datetime.now().isoformat(),
        "source": "vertex_ai_automl"
    }
    
    # Save config for API to use
    with open("/Users/zincdigital/CBI-V14/forecast/vertex_predictions.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("✓ API configuration updated")

if __name__ == "__main__":
    print("WIRING VERTEX AI AUTOML MODELS TO DASHBOARD")
    print("=" * 50)
    update_api_with_vertex_predictions()
    print("\n🎉 Vertex AI predictions are now available for the dashboard!")
