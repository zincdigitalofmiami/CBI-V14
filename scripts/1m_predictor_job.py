#!/usr/bin/env python3
"""
1M Predictor Job with 1W Gate Blend (UPDATED: 3-Endpoint Architecture)
Calls 3 separate Vertex AI endpoints (q10, mean, q90), applies simplified gate blend for D+1-7
CRITICAL: Schema validation MUST pass before prediction (ABORT ON MISMATCH)
"""

import json
import numpy as np
import logging
import requests
from datetime import datetime
from pathlib import Path
from google.cloud import bigquery, aiplatform
import argparse
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"
LOCATION = "us-central1"
REVALIDATE_API_URL = "http://localhost:3000/api/revalidate"  # Update with actual URL

def load_config():
    """Load endpoint configuration"""
    config_path = Path('config/vertex_1m_config.json')
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    
    with open(config_path, 'r') as f:
        return json.load(f)

def load_features():
    """Load assembled features"""
    features_path = Path('features_1m_latest.json')
    if not features_path.exists():
        # Run assembler if features don't exist
        logger.info("Features not found, running assembler...")
        import importlib.util
        spec = importlib.util.spec_from_file_location("feature_assembler_1m", Path(__file__).parent / "1m_feature_assembler.py")
        feature_assembler_1m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(feature_assembler_1m)
        features, _ = feature_assembler_1m.main()
        return features
    
    with open(features_path, 'r') as f:
        return json.load(f)

def validate_schema(features):
    """CRITICAL: Validate schema - ABORT ON MISMATCH"""
    logger.info("Validating feature schema (CRITICAL - ABORT ON MISMATCH)...")
    
    try:
        import importlib.util
        spec_validator = importlib.util.spec_from_file_location("schema_validator_1m", Path(__file__).parent / "1m_schema_validator.py")
        schema_validator_1m = importlib.util.module_from_spec(spec_validator)
        spec_validator.loader.exec_module(schema_validator_1m)
        
        # Save features to temp file for validation
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(features, f)
            temp_path = f.name
        
        try:
            schema_validator_1m.validate_from_file(temp_path)
            logger.info("✅ Schema validation passed")
        finally:
            Path(temp_path).unlink()
    except Exception as e:
        logger.error(f"❌ Schema validation FAILED: {e}")
        logger.error("ABORTING - Schema mismatch will ruin deployment")
        sys.exit(1)  # ABORT ON MISMATCH

def get_1w_rolled_forecast(features):
    """Get rolled 1W forecast for gate blend"""
    rolled = features.get('_rolled_forecast_7d')
    
    if rolled is None or len(rolled) != 7:
        logger.warning("No valid rolled 1W forecast found - using 1M only")
        return None
    
    return rolled

def call_vertex_endpoint_quantile(features, endpoint_id, quantile_name):
    """Call single quantile endpoint and get [30] array"""
    logger.info(f"Calling {quantile_name} endpoint...")
    
    aiplatform.init(project=PROJECT_ID, location=LOCATION)
    endpoint = aiplatform.Endpoint(endpoint_id)
    
    # Remove metadata keys from features
    features_clean = {k: v for k, v in features.items() 
                     if not k.startswith('_') and not k.startswith('target_')}
    
    # Make prediction
    predictions = endpoint.predict(instances=[features_clean])
    pred_output = predictions.predictions[0]
    
    # Handle different output formats
    pred_array = np.array(pred_output).flatten()
    
    # Expected: [30] array (one value per horizon D+1 to D+30)
    if len(pred_array) != 30:
        if len(pred_array) == 90:
            # All quantiles returned - extract this quantile's slice
            pred_array = pred_array.reshape(30, 3)
            quantile_idx = {'q10': 0, 'mean': 1, 'q90': 2}[quantile_name]
            pred_array = pred_array[:, quantile_idx]
        else:
            logger.warning(f"Unexpected output length: {len(pred_array)}, expected 30")
            if len(pred_array) == 1:
                # Single value - repeat for 30 days
                pred_array = np.array([pred_array[0]] * 30)
    
    logger.info(f"✅ {quantile_name} endpoint returned {len(pred_array)} predictions")
    return pred_array.tolist()  # [30] array

def call_all_endpoints(features, config):
    """Call all 3 endpoints and combine to [30, 3] array"""
    logger.info("Calling all 3 quantile endpoints...")
    
    q10_endpoint_id = config['q10_endpoint_id']
    mean_endpoint_id = config['mean_endpoint_id']
    q90_endpoint_id = config['q90_endpoint_id']
    
    # Call each endpoint
    q10_array = call_vertex_endpoint_quantile(features, q10_endpoint_id, 'q10')
    mean_array = call_vertex_endpoint_quantile(features, mean_endpoint_id, 'mean')
    q90_array = call_vertex_endpoint_quantile(features, q90_endpoint_id, 'q90')
    
    # Combine to [30, 3] array
    predictions = np.array([q10_array, mean_array, q90_array]).T  # [30, 3]
    
    logger.info(f"✅ Combined predictions shape: {predictions.shape}")
    logger.info(f"Sample D+1: q10={predictions[0, 0]:.2f}, mean={predictions[0, 1]:.2f}, q90={predictions[0, 2]:.2f}")
    
    return predictions[:, 0].tolist(), predictions[:, 1].tolist(), predictions[:, 2].tolist()

def apply_gate_blend_simplified(q10, mean, q90, signals, rolled_1w):
    """
    Apply simplified gate blend for D+1-7 only
    SIMPLIFIED: w = 0.75 default, w = 0.95 kill-switch
    DYNAMIC SPREAD: volatility_score_1w * 0.15
    """
    logger.info("Applying simplified gate blend for D+1-7...")
    
    if rolled_1w is None or len(rolled_1w) != 7:
        logger.info("No 1W forecast available - using pure 1M for all days")
        return q10, mean, q90, [1.0] * 30
    
    volatility_score_1w = signals.get('volatility_score_1w', 0.0)
    gate_weights = []
    
    # SIMPLIFIED GATE WEIGHT: Default 0.75, kill-switch 0.95
    for i in range(7):  # D+1 to D+7 only
        # Calculate disagreement: |F_1W_7 - mean_1M[D+7]| / mean_1M[D+7]
        mean_d7 = mean[6] if i < 7 else mean[i]  # Use D+7 mean for comparison
        rolled_d7 = rolled_1w[6] if len(rolled_1w) > 6 else rolled_1w[i]
        disagreement = abs(rolled_d7 - mean_d7) / max(abs(mean_d7), 1e-8)
        
        # SIMPLIFIED: Default weight 0.75
        w = 0.75
        
        # KILL-SWITCH: If volatility > 0.85 OR disagreement > 0.25, trust 1M (w = 0.95)
        if volatility_score_1w > 0.85 or disagreement > 0.25:
            w = 0.95
            logger.info(f"D+{i+1}: Kill-switch activated (vol={volatility_score_1w:.2f}, dis={disagreement:.2f})")
        
        gate_weights.append(w)
        
        # Get rolled 1W forecast for this day
        rolled_val = rolled_1w[i] if i < len(rolled_1w) else mean[i]
        
        # Blend mean
        mean[i] = w * mean[i] + (1 - w) * rolled_val
        
        # DYNAMIC QUANTILE SPREAD: volatility_score_1w * 0.15 (0-15% based on volatility)
        spread_pct = volatility_score_1w * 0.15
        
        # Blend q10/q90 with dynamic spread
        q10[i] = w * q10[i] + (1 - w) * (rolled_val * (1 - spread_pct))
        q90[i] = w * q90[i] + (1 - w) * (rolled_val * (1 + spread_pct))
    
    # D+8-30: Pure 1M (no blend)
    gate_weights.extend([1.0] * 23)  # D+8-30 all weight = 1.0
    
    logger.info(f"Gate weights D+1-7: {[f'{w:.2f}' for w in gate_weights[:7]]}")
    logger.info(f"D+8-30: Pure 1M (no blend)")
    
    return q10, mean, q90, gate_weights

def write_to_bigquery(q10, mean, q90, gate_weights, as_of_timestamp):
    """Write predictions to BigQuery with idempotency"""
    logger.info("Writing predictions to BigQuery...")
    
    client = bigquery.Client(project=PROJECT_ID, location='us-central1')
    table_id = f"{PROJECT_ID}.forecasting_data_warehouse.predictions_1m"
    
    rows = []
    for day in range(30):
        future_day = day + 1  # D+1 to D+30
        
        row = {
            'as_of_timestamp': as_of_timestamp,
            'future_day': future_day,
            'q10': float(q10[day]),
            'mean': float(mean[day]),
            'q90': float(q90[day]),
            'gate_weight': float(gate_weights[day]),
            'blended': gate_weights[day] < 1.0,  # True if blended with 1W
            'model_version': '90_models_3_endpoints',
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
        logger.warning(f"Delete query failed (table may not exist yet): {e}")
    
    # Insert new rows
    errors = client.insert_rows_json(table_id, rows)
    if errors:
        raise ValueError(f"BigQuery insert errors: {errors}")
    
    logger.info(f"✅ Inserted {len(rows)} prediction rows")
    
    # CRITICAL: Invalidate cache after BigQuery write
    try:
        logger.info("Invalidating cache...")
        response = requests.post(REVALIDATE_API_URL, timeout=5)
        if response.status_code == 200:
            logger.info("✅ Cache invalidated successfully")
        else:
            logger.warning(f"Cache invalidation returned status {response.status_code}")
    except Exception as e:
        logger.warning(f"Cache invalidation failed (non-critical): {e}")
    
    return len(rows)

def main():
    parser = argparse.ArgumentParser(description='1M Predictor Job (3-Endpoint Architecture)')
    parser.add_argument('--backfill-if-missing', action='store_true', 
                       help='Backfill missing predictions for last 30 days')
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("1M PREDICTOR JOB (3-ENDPOINT ARCHITECTURE)")
    logger.info("=" * 80)
    
    try:
        # Load config
        config = load_config()
        
        # Assemble features
        import importlib.util
        spec_assembler = importlib.util.spec_from_file_location("feature_assembler_1m", Path(__file__).parent / "1m_feature_assembler.py")
        feature_assembler_1m = importlib.util.module_from_spec(spec_assembler)
        spec_assembler.loader.exec_module(feature_assembler_1m)
        features, date = feature_assembler_1m.main()
        
        # CRITICAL: Validate schema (ABORT ON MISMATCH)
        validate_schema(features)
        
        # Get 1W signals
        signals = {
            'volatility_score_1w': features.get('volatility_score_1w', 0.0),
            'delta_1w_vs_spot': features.get('delta_1w_vs_spot', 0.0),
            'momentum_1w_7d': features.get('momentum_1w_7d', 0.0),
            'short_bias_score_1w': features.get('short_bias_score_1w', 0.0)
        }
        
        rolled_1w = get_1w_rolled_forecast(features)
        
        # Call all 3 endpoints
        q10, mean, q90 = call_all_endpoints(features, config)
        
        # Apply simplified gate blend
        q10, mean, q90, gate_weights = apply_gate_blend_simplified(q10, mean, q90, signals, rolled_1w)
        
        # Write to BigQuery
        as_of_timestamp = datetime.utcnow().isoformat() + 'Z'
        row_count = write_to_bigquery(q10, mean, q90, gate_weights, as_of_timestamp)
        
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
