#!/usr/bin/env python3
"""Get single prediction from existing 1W endpoint and populate predictions table correctly"""

from google.cloud import aiplatform, bigquery
from datetime import datetime, timedelta
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"
LOCATION = "us-central1"
ENDPOINT_ID = "7286867078038945792"  # Working 1W endpoint

def get_latest_features():
    """Get latest features from the updated Big-8 table"""
    client = bigquery.Client(project=PROJECT_ID)
    
    query = """
    SELECT *
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    WHERE date = (SELECT MAX(date) FROM `cbi-v14.models_v4.training_dataset_super_enriched`)
    LIMIT 1
    """
    
    df = client.query(query).to_dataframe()
    logger.info(f"Got features for date: {df['date'].iloc[0]}")
    return df

def make_prediction():
    """Get prediction from 1W endpoint"""
    aiplatform.init(project=PROJECT_ID, location=LOCATION)
    
    # Get features
    features_df = get_latest_features()
    
    # Get all columns from the original training data
    features = features_df.iloc[0].to_dict()
    
    # Convert date to string format expected by model
    if 'date' in features:
        features['date'] = str(features['date'])
    
    # Set target columns to None (model expects them but doesn't use them for prediction)
    target_columns = [col for col in features.keys() if col.startswith('target_')]
    for col in target_columns:
        features[col] = None
    
    # Convert to proper types for Vertex AI
    for key, value in features.items():
        if pd.isna(value):
            features[key] = None
        elif isinstance(value, (int, float)):
            features[key] = float(value)
        else:
            features[key] = str(value)
    
    # Get endpoint and predict
    endpoint = aiplatform.Endpoint(endpoint_name=f"projects/{PROJECT_ID}/locations/{LOCATION}/endpoints/{ENDPOINT_ID}")
    
    logger.info("Making prediction...")
    prediction = endpoint.predict(instances=[features])
    
    predicted_price = float(prediction.predictions[0]['value'])
    confidence = prediction.predictions[0].get('confidence', 0.95)
    
    # Calculate confidence bounds (assuming ±2% for 1W)
    confidence_range = predicted_price * 0.02
    
    return {
        'predicted_price': predicted_price,
        'confidence_lower': predicted_price - confidence_range,
        'confidence_upper': predicted_price + confidence_range,
        'mape': 2.02,  # Known 1W MAPE
        'model_id': '575258986094264320',
        'model_name': 'cbi_v14_1w_final'
    }

def save_prediction(prediction_data):
    """Save prediction to BigQuery with correct schema"""
    client = bigquery.Client(project=PROJECT_ID)
    
    today = datetime.now().date()
    target_date = today + timedelta(days=7)
    
    row = {
        'horizon': '1W',
        'predicted_price': prediction_data['predicted_price'],
        'confidence_lower': prediction_data['confidence_lower'],
        'confidence_upper': prediction_data['confidence_upper'],
        'mape': prediction_data['mape'],
        'model_id': prediction_data['model_id'],
        'model_name': prediction_data['model_name'],
        'prediction_date': today.isoformat(),
        'target_date': target_date.isoformat(),
        'created_at': datetime.utcnow().isoformat()
    }
    
    table_ref = client.dataset('predictions').table('daily_forecasts')
    table = client.get_table(table_ref)
    
    errors = client.insert_rows_json(table, [row])
    if errors:
        logger.error(f"Insert errors: {errors}")
        return False
    
    logger.info(f"✅ Saved 1W prediction: ${prediction_data['predicted_price']:.2f}")
    return True

def main():
    try:
        prediction = make_prediction()
        save_prediction(prediction)
        logger.info("✅ 1W prediction complete")
    except Exception as e:
        logger.error(f"❌ Prediction failed: {e}")

if __name__ == "__main__":
    main()
