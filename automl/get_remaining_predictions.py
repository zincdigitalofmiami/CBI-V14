"""
Get predictions for 1M, 3M, 6M using EXISTING endpoint
Uses soybean_oil_1w_working_endpoint (7286867078038945792)
"""
from google.cloud import aiplatform
from google.cloud import bigquery
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

aiplatform.init(project='cbi-v14', location='us-central1')
bq_client = bigquery.Client(project='cbi-v14')

# USE EXISTING ENDPOINT - NO NEW ENDPOINTS!
ENDPOINT_ID = '7286867078038945792'

MODELS = {
    '1M': {'id': '274643710967283712', 'name': 'soybean_oil_1m_model_FINAL_20251029_1147', 'mape': 2.5, 'days': 30},
    '3M': {'id': '3157158578716934144', 'name': 'soybean_oil_3m_final_v14_20251029_0808', 'mape': 2.68, 'days': 90},
    '6M': {'id': '3788577320223113216', 'name': 'soybean_oil_6m_model_v14_20251028_1737', 'mape': 2.51, 'days': 180},
}

def get_prediction_data():
    """Get latest data with schema fixes"""
    query = 'SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched` ORDER BY date DESC LIMIT 1'
    df = bq_client.query(query).to_dataframe()
    
    # Schema fixes
    int_cols = df.select_dtypes(include=['int64', 'Int64']).columns.tolist()
    for col in int_cols:
        df[col] = df[col].astype(str)
    
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    df = df.replace({np.nan: None})
    
    # Models require target columns - set to null for predictions
    target_cols = ['target_1w', 'target_1m', 'target_3m', 'target_6m']
    for col in target_cols:
        if col not in df.columns:
            df[col] = None
    
    return df.to_dict('records')[0]

def save_prediction(horizon, prediction_value, model_info):
    """Save to BigQuery"""
    data = {
        'horizon': horizon,
        'prediction_date': datetime.now().date().isoformat(),
        'target_date': (datetime.now().date() + timedelta(days=model_info['days'])).isoformat(),
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
        logger.info(f'✅ Saved {horizon} to BigQuery')
    else:
        logger.error(f'❌ Error: {errors}')

# Main process
endpoint = aiplatform.Endpoint(f'projects/1065708057795/locations/us-central1/endpoints/{ENDPOINT_ID}')
logger.info(f'✅ Using endpoint: {endpoint.display_name}\n')

instance = get_prediction_data()

for horizon, model_info in MODELS.items():
    logger.info(f'{"="*60}')
    logger.info(f'  {horizon} HORIZON')
    logger.info(f'{"="*60}')
    
    try:
        model = aiplatform.Model(f"projects/1065708057795/locations/us-central1/models/{model_info['id']}")
        logger.info(f'🚀 Deploying {model_info["name"]}...')
        
        endpoint.deploy(
            model=model,
            deployed_model_display_name=f'{horizon}_model',
            machine_type='n1-standard-2',  # Smaller machine to save quota
            min_replica_count=1,
            max_replica_count=1,
            sync=True
        )
        logger.info(f'✅ Deployed!')
        
        response = endpoint.predict(instances=[instance])
        prediction = response.predictions[0]['value']
        logger.info(f'✅ Prediction: ${prediction:.2f}')
        
        save_prediction(horizon, prediction, model_info)
        
        endpoint.undeploy_all()
        logger.info(f'✅ Undeployed\n')
        
    except Exception as e:
        logger.error(f'❌ Error: {str(e)}\n')
        try:
            endpoint.undeploy_all()
        except:
            pass

logger.info(f'{"="*60}')
logger.info(f'  COMPLETE!')
logger.info(f'{"="*60}')


