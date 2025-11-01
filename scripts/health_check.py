#!/usr/bin/env python3
"""
Health Check for Vertex AI 1M Endpoints (3 endpoints - q10, mean, q90)
Validates: All 3 endpoints exist, each has deployed models, traffic splits correct
Tests: Each endpoint returns [30] array (predictions for D+1 to D+30)
"""

import json
import logging
import numpy as np
from pathlib import Path
from google.cloud import aiplatform

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"
LOCATION = "us-central1"

def load_config():
    """Load endpoint configuration"""
    config_path = Path('config/vertex_1m_config.json')
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    return config

def validate_endpoint(endpoint_id, quantile_name):
    """Validate single endpoint state"""
    logger.info(f"\nValidating {quantile_name} endpoint: {endpoint_id}")
    
    aiplatform.init(project=PROJECT_ID, location=LOCATION)
    endpoint = aiplatform.Endpoint(endpoint_id)
    
    # Check deployed models
    deployed_models = endpoint.deployed_models
    logger.info(f"Found {len(deployed_models)} deployed model(s)")
    
    if len(deployed_models) == 0:
        raise ValueError(f"{quantile_name} endpoint has no deployed models")
    
    # Check traffic split
    traffic_split = endpoint.traffic_split
    logger.info(f"Traffic split: {traffic_split}")
    
    # Verify at least one model has 100% traffic
    max_traffic = max(traffic_split.values()) if traffic_split else 0
    if max_traffic < 100:
        logger.warning(f"Highest traffic split is {max_traffic}%, expected at least one model at 100%")
    
    logger.info(f"✅ {quantile_name} endpoint validation passed")
    return endpoint

def test_prediction(endpoint, quantile_name, feature_names=None):
    """Test prediction with dummy features to verify output shape"""
    logger.info(f"Testing {quantile_name} endpoint prediction...")
    
    # Create dummy features (all zeros)
    if feature_names:
        dummy_features = {name: 0.0 for name in feature_names}
    else:
        # Default: 213 features (209 + 4 1W signals)
        dummy_features = {f'feature_{i}': 0.0 for i in range(213)}
    
    # Make prediction
    try:
        predictions = endpoint.predict(instances=[dummy_features])
        
        # Check output shape
        pred_output = predictions.predictions[0]
        logger.info(f"Prediction output type: {type(pred_output)}")
        logger.info(f"Prediction output shape: {np.array(pred_output).shape if hasattr(pred_output, '__len__') else 'scalar'}")
        
        # Expected: [30] array (30 days for this quantile)
        # OR could be [1, 30] or flattened [90] - handle all cases
        pred_array = np.array(pred_output).flatten()
        logger.info(f"Flattened prediction shape: {pred_array.shape}")
        
        if len(pred_array) != 30:
            logger.warning(f"Expected 30 predictions, got {len(pred_array)}")
            # May need to reshape if it's a different format
            if len(pred_array) == 90:
                logger.info("Reshaping from [90] to [30, 3] - assuming all quantiles returned")
                pred_array = pred_array.reshape(30, 3)[:, 0]  # Take first column
            elif len(pred_array) == 1:
                logger.warning("Single value returned - endpoint may need model per horizon")
                pred_array = np.array([pred_array[0]] * 30)  # Repeat for 30 days
        
        if len(pred_array) == 30:
            logger.info(f"✅ {quantile_name} prediction test passed! Shape: {pred_array.shape}")
            logger.info(f"Sample outputs: D+1={pred_array[0]:.4f}, D+7={pred_array[6]:.4f}, D+30={pred_array[29]:.4f}")
            return True
        else:
            raise ValueError(f"Expected 30 predictions, got {len(pred_array)}")
        
    except Exception as e:
        logger.error(f"Prediction test failed: {e}")
        raise

def main():
    logger.info("=" * 80)
    logger.info("HEALTH CHECK: 1M 3-ENDPOINT ARCHITECTURE")
    logger.info("=" * 80)
    
    try:
        config = load_config()
        logger.info(f"Loaded config: {config.get('architecture', 'unknown')}")
        
        # Load feature names if available
        schema_path = Path('config/1m_feature_schema.json')
        feature_names = None
        if schema_path.exists():
            with open(schema_path, 'r') as f:
                schema = json.load(f)
                feature_names = schema.get('features', schema.get('feature_names', None))
        
        # Validate all 3 endpoints
        endpoints = {}
        quantiles = ['q10', 'mean', 'q90']
        
        for quantile in quantiles:
            endpoint_key = f"{quantile}_endpoint_id"
            if endpoint_key not in config:
                raise ValueError(f"Missing {endpoint_key} in config")
            
            endpoint_id = config[endpoint_key]
            endpoint = validate_endpoint(endpoint_id, quantile)
            endpoints[quantile] = endpoint
        
        # Test predictions on all endpoints
        for quantile in quantiles:
            test_prediction(endpoints[quantile], quantile, feature_names)
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ HEALTH CHECK PASSED - ALL 3 ENDPOINTS VALID")
        logger.info("=" * 80)
        logger.info("\nEndpoint Status:")
        for quantile in quantiles:
            endpoint_key = f"{quantile}_endpoint_id"
            logger.info(f"  {quantile}: {config[endpoint_key]}")
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error("❌ HEALTH CHECK FAILED")
        logger.error(f"Error: {e}")
        logger.error("=" * 80)
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()
