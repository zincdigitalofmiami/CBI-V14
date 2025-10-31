#!/usr/bin/env python3
"""
Generate predictions for 1W, 1M, 3M, 6M using sequential endpoint deployment
Uses predict_frame view (no target columns - matches current training_dataset_super_enriched)
"""
from google.cloud import aiplatform
from google.cloud import bigquery
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = 'cbi-v14'
REGION = 'us-central1'

aiplatform.init(project=PROJECT_ID, location=REGION)
bq_client = bigquery.Client(project=PROJECT_ID, location=REGION)

# Use existing endpoint
ENDPOINT_ID = '7286867078038945792'

MODELS = {
    '1W': {'id': '575258986094264320', 'name': 'cbi_v14_automl_pilot_1w', 'mape': 2.02, 'days': 7},
    '1M': {'id': '274643710967283712', 'name': 'soybean_oil_1m_model_FINAL_20251029_1147', 'mape': 2.5, 'days': 30},
    '3M': {'id': '3157158578716934144', 'name': 'soybean_oil_3m_final_v14_20251029_0808', 'mape': 2.68, 'days': 90},
    '6M': {'id': '3788577320223113216', 'name': 'soybean_oil_6m_model_v14_20251028_1737', 'mape': 2.51, 'days': 180},
}

def get_prediction_data():
    """Get latest data from predict_frame view (no target columns)"""
    query = """
    SELECT * 
    FROM `cbi-v14.models_v4.predict_frame`
    LIMIT 1
    """
    df = bq_client.query(query).to_dataframe()
    
    if df.empty:
        raise ValueError("predict_frame is empty - no data available")
    
    logger.info(f"✅ Got {len(df.columns)} columns from predict_frame")
    
    # Convert to dict and handle types
    features = df.iloc[0].to_dict()
    
    # Convert date to string
    if 'date' in features:
        if isinstance(features['date'], (datetime, pd.Timestamp)):
            features['date'] = features['date'].strftime('%Y-%m-%d')
        else:
            features['date'] = str(features['date'])
    
    # Convert types for Vertex AI
    for col, val in features.items():
        if pd.isna(val) or val is None:
            features[col] = None
        elif isinstance(val, (np.int64, np.int32, np.int16)):
            features[col] = int(val)
        elif isinstance(val, (np.float64, np.float32)):
            features[col] = float(val)
        elif isinstance(val, (bool, np.bool_)):
            features[col] = bool(val)
        else:
            features[col] = str(val)
    
    logger.info(f"✅ Types converted - date: {features.get('date')}")
    return features

def save_prediction(horizon, prediction_value, model_info):
    """Save to monthly_vertex_predictions table"""
    today = datetime.now().date()
    target_date = today + timedelta(days=model_info['days'])
    
    data = {
        'horizon': horizon,
        'prediction_date': today.isoformat(),
        'target_date': target_date.isoformat(),
        'predicted_price': float(prediction_value),
        'confidence_lower': float(prediction_value * (1 - model_info['mape']/100)),
        'confidence_upper': float(prediction_value * (1 + model_info['mape']/100)),
        'mape': float(model_info['mape']),
        'model_id': model_info['id'],
        'model_name': model_info['name'],
        'created_at': datetime.now().isoformat()
    }
    
    errors = bq_client.insert_rows_json('cbi-v14.predictions.monthly_vertex_predictions', [data])
    if errors == []:
        logger.info(f'✅ Saved {horizon} to BigQuery: ${prediction_value:.2f}')
        return True
    else:
        logger.error(f'❌ Error saving {horizon}: {errors}')
        return False

# Main process
logger.info("="*80)
logger.info("GENERATING ALL PREDICTIONS (1W, 1M, 3M, 6M)")
logger.info("="*80)

endpoint = aiplatform.Endpoint(f'projects/1065708057795/locations/{REGION}/endpoints/{ENDPOINT_ID}')
logger.info(f'✅ Using endpoint: {endpoint.display_name}\n')

# Get prediction instance once
instance = get_prediction_data()

success_count = 0
for horizon, model_info in MODELS.items():
    logger.info(f'{"="*60}')
    logger.info(f'  {horizon} HORIZON')
    logger.info(f'{"="*60}')
    
    try:
        model = aiplatform.Model(f"projects/1065708057795/locations/{REGION}/models/{model_info['id']}")
        logger.info(f'🚀 Deploying {model_info["name"]}...')
        
        endpoint.deploy(
            model=model,
            deployed_model_display_name=f'{horizon}_model',
            machine_type='n1-standard-2',
            min_replica_count=1,
            max_replica_count=1,
            sync=True
        )
        logger.info(f'✅ Deployed!')
        
        # Predict
        response = endpoint.predict(instances=[instance])
        
        # Extract prediction (handle different response formats)
        pred_raw = response.predictions[0]
        if isinstance(pred_raw, dict):
            prediction_value = float(pred_raw.get('value', pred_raw.get('prediction', pred_raw)))
        else:
            prediction_value = float(pred_raw)
        
        logger.info(f'✅ Prediction: ${prediction_value:.2f}')
        
        # Save to BigQuery
        if save_prediction(horizon, prediction_value, model_info):
            success_count += 1
        
        # Undeploy immediately
        endpoint.undeploy_all(sync=True)
        logger.info(f'✅ Undeployed\n')
        
    except Exception as e:
        logger.error(f'❌ Error: {str(e)}\n')
        try:
            endpoint.undeploy_all()
        except:
            pass

logger.info(f'{"="*60}')
logger.info(f'  COMPLETE! Success: {success_count}/4 horizons')
logger.info(f'{"="*60}')

