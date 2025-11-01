#!/usr/bin/env python3
"""
1M Predictor Job (Interim - Single Endpoint, Mean Only)
Uses existing deployed model until 90-model architecture is ready
"""

import json
import numpy as np
import logging
from datetime import datetime
from pathlib import Path
from google.cloud import bigquery, aiplatform
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"
LOCATION = "us-central1"

def load_schema_contract():
    """Load immutable schema contract"""
    contract_path = Path('config/schema_contract.json')
    if not contract_path.exists():
        raise FileNotFoundError(f"Schema contract not found: {contract_path}. Run generate_schema_contract.py first.")
    
    with open(contract_path, 'r') as f:
        contract = json.load(f)
    
    return contract

def fill_missing_schema_fields(instance: dict, required_fields: list) -> dict:
    """
    AutoML requires ALL training columns present (even targets as None)
    Ensures ALL columns from schema contract exist in prediction payload
    """
    return {key: instance.get(key, None) for key in required_fields}

def load_config():
    """Load endpoint configuration"""
    config_path = Path('config/vertex_1m_config.json')
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    
    with open(config_path, 'r') as f:
        return json.load(f)

def load_features():
    """Load assembled features and re-run assembler to get date"""
    # Run assembler to get both features and source_date
    import importlib.util
    spec = importlib.util.spec_from_file_location("assembler", Path(__file__).parent / "1m_feature_assembler.py")
    assembler = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(assembler)
    
    features, source_date = assembler.main()
    
    return features, source_date

def call_vertex_endpoint(features, source_date, endpoint_id):
    """Call Vertex AI endpoint and get mean predictions"""
    logger.info(f"Calling endpoint {endpoint_id}...")
    
    aiplatform.init(project=PROJECT_ID, location=LOCATION)
    endpoint = aiplatform.Endpoint(endpoint_id)
    
    # Load schema contract
    contract = load_schema_contract()
    required_columns = contract['columns']
    
    # CRITICAL: Apply schema contract - ensure ALL 210 columns exist (targets as None)
    # Only remove metadata keys (starting with '_')
    features_clean = {k: v for k, v in features.items() if not k.startswith('_')}
    
    # Ensure date is properly formatted
    if hasattr(source_date, 'strftime'):
        date_str = source_date.strftime('%Y-%m-%d')
    else:
        date_str = str(source_date)
    
    features_clean['date'] = date_str
    
    # CRITICAL: Fill ALL missing schema fields (targets must exist as None)
    features_clean = fill_missing_schema_fields(features_clean, required_columns)
    
    # Verify we have all required columns
    missing = set(required_columns) - set(features_clean.keys())
    if missing:
        raise ValueError(f"Missing required columns after fill: {missing}")
    
    logger.info(f"Applied schema contract: {len(features_clean)} columns (targets as None)")
    logger.info(f"Date field: {date_str} (from training data)")
    
    # Log target columns are None (as expected)
    target_cols = [c for c in required_columns if c.startswith('target_')]
    for target in target_cols:
        if features_clean.get(target) is not None:
            logger.warning(f"Target column {target} is not None: {features_clean.get(target)}")
    
    # Make prediction
    predictions = endpoint.predict(instances=[features_clean])
    pred_output = predictions.predictions[0]
    
    # Handle output (existing model returns single mean value)
    logger.info(f"Prediction output type: {type(pred_output)}")
    logger.info(f"Prediction output: {pred_output}")
    
    # Model should return mean forecast (single value or array)
    if isinstance(pred_output, (int, float)):
        # Single value - use as mean for all 30 days (simplification)
        mean_forecast = float(pred_output)
        mean_array = [mean_forecast] * 30
        logger.info(f"Single mean value: {mean_forecast:.2f}")
    elif isinstance(pred_output, list):
        # Array - could be 30-day forecast
        mean_array = [float(v) for v in pred_output]
        if len(mean_array) == 1:
            # Single value in array
            mean_array = mean_array * 30
        elif len(mean_array) < 30:
            # Extend to 30 days
            logger.warning(f"Only {len(mean_array)} predictions, extending to 30 days")
            last_val = mean_array[-1]
            mean_array.extend([last_val] * (30 - len(mean_array)))
        elif len(mean_array) > 30:
            # Truncate to 30 days
            mean_array = mean_array[:30]
    else:
        raise ValueError(f"Unexpected output type: {type(pred_output)}")
    
    # Create temporary q10/q90 bands (mean ± 10%)
    q10_array = [m * 0.9 for m in mean_array]
    q90_array = [m * 1.1 for m in mean_array]
    
    logger.info(f"Sample D+1: q10={q10_array[0]:.2f}, mean={mean_array[0]:.2f}, q90={q90_array[0]:.2f}")
    
    return q10_array, mean_array, q90_array

def write_to_bigquery(q10, mean, q90, as_of_timestamp):
    """Write predictions to BigQuery"""
    logger.info("Writing predictions to BigQuery...")
    
    client = bigquery.Client(project=PROJECT_ID, location='us-central1')
    table_id = f"{PROJECT_ID}.forecasting_data_warehouse.predictions_1m"
    
    rows = []
    for day in range(30):
        future_day = day + 1
        
        row = {
            'as_of_timestamp': as_of_timestamp,
            'future_day': future_day,
            'q10': float(q10[day]),
            'mean': float(mean[day]),
            'q90': float(q90[day]),
            'gate_weight': 1.0,  # No blend in interim version
            'blended': False,  # No blend in interim version
            'model_version': 'interim_single_endpoint',
            'created_at': datetime.utcnow().isoformat() + 'Z'
        }
        rows.append(row)
    
    # Delete existing rows for this timestamp (idempotency)
    delete_query = f"""
    DELETE FROM `{table_id}`
    WHERE as_of_timestamp = TIMESTAMP('{as_of_timestamp}')
    """
    
    try:
        client.query(delete_query, location='us-central1').result()
        logger.info(f"Deleted existing rows for {as_of_timestamp}")
    except Exception as e:
        logger.warning(f"Delete query failed: {e}")
    
    # Insert new rows
    errors = client.insert_rows_json(table_id, rows)
    if errors:
        raise ValueError(f"BigQuery insert errors: {errors}")
    
    logger.info(f"✅ Inserted {len(rows)} prediction rows")
    return len(rows)

def main():
    logger.info("=" * 80)
    logger.info("1M PREDICTOR JOB (INTERIM - SINGLE ENDPOINT)")
    logger.info("=" * 80)
    
    try:
        # Load config
        config = load_config()
        endpoint_id = config['endpoint_id']
        
        # Load features (includes source_date)
        features, source_date = load_features()
        logger.info(f"Loaded {len(features)} features from date: {source_date}")
        
        # Call Vertex endpoint (pass source_date for schema compatibility)
        q10, mean, q90 = call_vertex_endpoint(features, source_date, endpoint_id)
        
        # Write to BigQuery
        as_of_timestamp = datetime.utcnow().isoformat() + 'Z'
        row_count = write_to_bigquery(q10, mean, q90, as_of_timestamp)
        
        logger.info("=" * 80)
        logger.info("✅ PREDICTOR JOB COMPLETE")
        logger.info(f"Rows written: {row_count}")
        logger.info(f"As of: {as_of_timestamp}")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error("❌ PREDICTOR JOB FAILED")
        logger.error(f"Error: {e}")
        logger.error("=" * 80)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

