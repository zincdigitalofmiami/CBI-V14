#!/usr/bin/env python3
"""
Export Feature Schema for 1M Model
Generates config/1m_feature_schema.json with feature names, types, hash, and min_coverage
"""

import json
import hashlib
import logging
from pathlib import Path
from google.cloud import bigquery
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"

def export_schema():
    """Export feature schema from training dataset"""
    logger.info("Exporting feature schema from training dataset...")
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # Get latest row from training dataset
    query = """
    SELECT *
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    WHERE date = (SELECT MAX(date) FROM `cbi-v14.models_v4.training_dataset_super_enriched`)
    LIMIT 1
    """
    
    df = client.query(query).to_dataframe()
    
    if df.empty:
        raise ValueError("No training data found for latest date")
    
    # Exclude metadata and target columns
    exclude_cols = ['date', 'target_1w', 'target_1m', 'target_3m', 'target_6m', 'soybean_oil_price']
    exclude_cols += [f'target_D{i}' for i in range(1, 31)]  # Exclude future target columns
    
    feature_cols = [col for col in df.columns if col not in exclude_cols and not col.startswith('_')]
    
    # Add 1W signals if not present (they'll be injected later)
    required_1w_signals = ['volatility_score_1w', 'delta_1w_vs_spot', 'momentum_1w_7d', 'short_bias_score_1w']
    for signal in required_1w_signals:
        if signal not in feature_cols:
            feature_cols.append(signal)
    
    # Sort for consistent hash
    feature_cols = sorted(feature_cols)
    
    # Calculate hash
    feature_hash = hashlib.md5(','.join(feature_cols).encode()).hexdigest()
    
    # Get feature types from DataFrame
    feature_types = {}
    for col in feature_cols:
        if col in df.columns:
            dtype = str(df[col].dtype)
            # Map pandas dtypes to simple types
            if 'float' in dtype or 'int' in dtype:
                feature_types[col] = 'FLOAT64'
            elif 'object' in dtype or 'string' in dtype:
                feature_types[col] = 'STRING'
            else:
                feature_types[col] = 'FLOAT64'  # Default
        else:
            feature_types[col] = 'FLOAT64'  # Default for injected signals
    
    # Define min_coverage for critical features
    min_coverage = {
        'volatility_score_1w': 0.8,  # 1W signal (always required)
        # Add other critical features based on actual importance
        # Examples (adjust based on actual training data):
        # 'f_china_imports_30d': 0.8,
        # 'f_usd_brl_7d_avg': 0.8,
    }
    
    # Build schema
    schema = {
        "feature_count": len(feature_cols),
        "features": feature_cols,
        "feature_names": feature_cols,  # Alias for compatibility
        "feature_types": feature_types,
        "hash": feature_hash,
        "min_coverage": min_coverage,
        "description": "1M Feature Schema - 209 Phase 0/1 features + 4 1W signals = 213 total",
        "version": "1.0",
        "export_date": pd.Timestamp.now().isoformat() + 'Z'
    }
    
    # Save schema
    schema_path = Path("config/1m_feature_schema.json")
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    with open(schema_path, 'w') as f:
        json.dump(schema, f, indent=2)
    
    logger.info(f"✅ Schema exported: {schema_path}")
    logger.info(f"  Feature count: {len(feature_cols)}")
    logger.info(f"  Hash: {feature_hash}")
    logger.info(f"  Critical features with min_coverage: {len(min_coverage)}")
    
    return schema

if __name__ == "__main__":
    try:
        schema = export_schema()
        print(f"\n✅ Success! Schema exported to config/1m_feature_schema.json")
        print(f"Features: {schema['feature_count']}")
    except Exception as e:
        logger.error(f"\n❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

