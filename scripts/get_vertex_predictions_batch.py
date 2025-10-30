#!/usr/bin/env python3
"""
Get REAL Vertex AI AutoML predictions via Batch Prediction
Then save to BigQuery for dashboard API
"""

from google.cloud import aiplatform, bigquery
from datetime import datetime
import pandas as pd

# Initialize
aiplatform.init(project="cbi-v14", location="us-central1")
bq_client = bigquery.Client(project="cbi-v14")

# Your REAL trained Vertex AI models
VERTEX_MODELS = {
    "1w": "575258986094264320",
    "1m": "274643710967283712",
    "3m": "3157158578716934144",
    "6m": "3788577320223113216"
}

def get_latest_features_for_prediction():
    """Get latest features formatted for prediction"""
    query = """
    SELECT * EXCEPT(date, target_1w, target_1m, target_3m, target_6m)
    FROM `cbi-v14.models_v4.training_dataset_v4`
    ORDER BY date DESC
    LIMIT 1
    """
    df = bq_client.query(query).to_dataframe()
    return df

def run_batch_prediction(model_id, horizon):
    """Run Vertex AI batch prediction"""
    try:
        print(f"\n🔄 Running batch prediction for {horizon} (Model: {model_id})...")
        
        # Get the model
        model = aiplatform.Model(
            model_name=f"projects/cbi-v14/locations/us-central1/models/{model_id}"
        )
        
        # Get features
        features_df = get_latest_features_for_prediction()
        
        # Save features to temp BigQuery table for batch prediction input
        temp_table = f"cbi-v14.models_v4.temp_prediction_input_{horizon}"
        features_df.to_gbq(
            temp_table.replace('cbi-v14.', ''),
            project_id='cbi-v14',
            if_exists='replace'
        )
        
        # Run batch prediction
        batch_prediction_job = model.batch_predict(
            job_display_name=f"dashboard_prediction_{horizon}_{datetime.now().strftime('%Y%m%d_%H%M')}",
            bigquery_source=f"bq://{temp_table}",
            bigquery_destination_prefix=f"bq://cbi-v14.models_v4",
            instances_format="bigquery",
            predictions_format="bigquery",
            sync=True  # Wait for completion
        )
        
        print(f"✅ Batch prediction complete for {horizon}")
        print(f"   Output: {batch_prediction_job.output_info}")
        
        return batch_prediction_job
        
    except Exception as e:
        print(f"❌ Error with {horizon} batch prediction: {e}")
        return None

def extract_predictions_to_api_table():
    """Extract predictions from batch output to simple API table"""
    
    predictions = []
    
    for horizon in VERTEX_MODELS.keys():
        try:
            # Query the batch prediction output
            query = f"""
            SELECT 
                '{horizon}' as horizon,
                predicted_value,
                '{VERTEX_MODELS[horizon]}' as model_id
            FROM `cbi-v14.models_v4.predictions_{horizon}_*`
            ORDER BY _TABLE_SUFFIX DESC
            LIMIT 1
            """
            
            df = bq_client.query(query).to_dataframe()
            
            if not df.empty:
                predictions.append({
                    'horizon': horizon,
                    'forecast_value': float(df['predicted_value'].iloc[0]),
                    'model_id': df['model_id'].iloc[0],
                    'source': 'vertex_ai_automl',
                    'timestamp': datetime.now()
                })
                print(f"✅ Extracted {horizon} prediction: {float(df['predicted_value'].iloc[0]):.2f}")
                
        except Exception as e:
            print(f"⚠️  Could not extract {horizon} prediction: {e}")
    
    # Save to API table
    if predictions:
        df = pd.DataFrame(predictions)
        table_id = "cbi-v14.api.vertex_automl_predictions"
        
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
        job = bq_client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        
        print(f"\n✅ Saved {len(predictions)} predictions to {table_id}")
        return True
    
    return False

if __name__ == "__main__":
    print("=" * 60)
    print("VERTEX AI AUTOML BATCH PREDICTIONS FOR DASHBOARD")
    print("=" * 60)
    
    # Run batch predictions for each horizon
    for horizon, model_id in VERTEX_MODELS.items():
        run_batch_prediction(model_id, horizon)
    
    print("\n" + "=" * 60)
    print("EXTRACTING PREDICTIONS FOR API")
    print("=" * 60)
    
    # Extract and save to API table
    if extract_predictions_to_api_table():
        print("\n🎉 Dashboard now has REAL Vertex AI AutoML predictions!")
    else:
        print("\n❌ Failed to get predictions - models may need deployment")



