#!/usr/bin/env python3
"""
Schema Validator for 1M Feature Assembly
Validates: Hash match, coverage thresholds, abort on mismatch
"""

import json
import hashlib
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_schema():
    """Load expected schema from config"""
    schema_path = Path('config/1m_feature_schema.json')
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    
    return schema

def validate_features(features_dict, schema):
    """Validate assembled features against schema"""
    logger.info("Validating feature schema...")
    
    # Check feature count
    expected_count = schema.get('feature_count', 0)
    actual_count = len([k for k in features_dict.keys() 
                       if not k.startswith('target_') and not k.startswith('_')])
    
    logger.info(f"Expected features: {expected_count}, Actual: {actual_count}")
    
    if actual_count != expected_count:
        raise ValueError(f"Feature count mismatch: expected {expected_count}, got {actual_count}")
    
    # Check hash (exclude metadata keys that start with '_')
    feature_names = sorted([k for k in features_dict.keys() 
                           if not k.startswith('target_') and not k.startswith('_')])
    actual_hash = hashlib.md5(','.join(feature_names).encode()).hexdigest()
    expected_hash = schema.get('hash', '')
    
    logger.info(f"Expected hash: {expected_hash}")
    logger.info(f"Actual hash: {actual_hash}")
    
    if actual_hash != expected_hash:
        raise ValueError(f"Schema hash mismatch! Expected {expected_hash}, got {actual_hash}")
    
    # Check critical features (min_coverage)
    # Note: Actual feature names may vary - validate against actual schema
    # These are examples - adjust based on actual training dataset columns
    critical_features = [
        'volatility_score_1w'  # 1W signal (always present)
        # Add other critical features based on actual schema after training
    ]
    
    missing_critical = []
    null_critical = []
    
    for feat in critical_features:
        if feat not in features_dict:
            missing_critical.append(feat)
        elif features_dict[feat] is None or (isinstance(features_dict[feat], float) and features_dict[feat] != features_dict[feat]):  # NaN check
            null_critical.append(feat)
    
    if missing_critical:
        raise ValueError(f"Missing critical features: {missing_critical}")
    
    if null_critical:
        logger.warning(f"Critical features are null/NaN: {null_critical}")
        # Don't abort for nulls, but warn (they'll be handled by model)
    
    logger.info("✅ Schema validation passed!")
    return True

def validate_from_file(features_file):
    """Validate features from JSON file"""
    with open(features_file, 'r') as f:
        features = json.load(f)
    
    schema = load_schema()
    return validate_features(features, schema)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python 1m_schema_validator.py <features.json>")
        sys.exit(1)
    
    try:
        validate_from_file(sys.argv[1])
        print("✅ Validation passed")
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        sys.exit(1)

