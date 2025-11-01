#!/usr/bin/env python3
"""
1M Feature Assembler with 1W Signal Injection
Assembles 209 Phase 0/1 features + 4 1W signals = 213 total features
FIXED: Pivots signals_1w table, joins on timestamp
"""

import json
import logging
import math
from datetime import datetime
from google.cloud import bigquery
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"

def load_schema_contract():
    """Load immutable schema contract"""
    contract_path = Path('config/schema_contract.json')
    if not contract_path.exists():
        logger.warning(f"Schema contract not found: {contract_path}. Features will not be filled with contract.")
        return None
    
    with open(contract_path, 'r') as f:
        contract = json.load(f)
    
    return contract

def fill_missing_schema_fields(instance: dict, required_fields: list) -> dict:
    """
    AutoML requires ALL training columns present (even targets as None)
    Ensures ALL columns from schema contract exist in prediction payload
    """
    return {key: instance.get(key, None) for key in required_fields}

def get_latest_209_features():
    """Get latest 209 features from training dataset"""
    logger.info("Fetching 209 Phase 0/1 features...")
    
    client = bigquery.Client(project=PROJECT_ID)
    
    query = """
    SELECT *
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    WHERE date = (SELECT MAX(date) FROM `cbi-v14.models_v4.training_dataset_super_enriched`)
    LIMIT 1
    """
    
    df = client.query(query).to_dataframe()
    
    if df.empty:
        raise ValueError("No training data found for latest date")
    
    # Get all columns except targets and date
    feature_cols = [col for col in df.columns 
                   if col not in ['date', 'target_1w', 'target_1m', 'target_3m', 'target_6m']]
    
    features = df.iloc[0].to_dict()
    date = features.pop('date', None)
    
    logger.info(f"Fetched {len(feature_cols)} features for date: {date}")
    
    return features, date

def get_latest_1w_signals():
    """Get latest 1W signals with pivot (FIXED: handles timestamp join)"""
    logger.info("Fetching 1W signals...")
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # FIXED: Pivot signals_1w table (signals stored as rows, need to pivot to columns)
    query = """
    SELECT 
      as_of_timestamp,
      MAX(CASE WHEN signal_name = 'volatility_score_1w' THEN signal_value END) AS volatility_score_1w,
      MAX(CASE WHEN signal_name = 'delta_1w_vs_spot' THEN signal_value END) AS delta_1w_vs_spot,
      MAX(CASE WHEN signal_name = 'momentum_1w_7d' THEN signal_value END) AS momentum_1w_7d,
      MAX(CASE WHEN signal_name = 'short_bias_score_1w' THEN signal_value END) AS short_bias_score_1w,
      MAX(CASE WHEN signal_name = 'rolled_forecast_7d' THEN rolled_forecast_7d_json END) AS rolled_forecast_7d_json
    FROM `cbi-v14.forecasting_data_warehouse.signals_1w`
    WHERE as_of_timestamp = (SELECT MAX(as_of_timestamp) FROM `cbi-v14.forecasting_data_warehouse.signals_1w`)
    GROUP BY as_of_timestamp
    """
    
    try:
        df = client.query(query).to_dataframe()
        
        if df.empty:
            logger.warning("No 1W signals found - using defaults")
            return {
                'volatility_score_1w': 0.0,
                'delta_1w_vs_spot': 0.0,
                'momentum_1w_7d': 0.0,
                'short_bias_score_1w': 0.0,
                'rolled_forecast_7d': None
            }
        
        signals = df.iloc[0].to_dict()
        
        # Parse rolled_forecast_7d JSON if present
        if signals.get('rolled_forecast_7d_json'):
            try:
                signals['rolled_forecast_7d'] = json.loads(signals['rolled_forecast_7d_json'])
                del signals['rolled_forecast_7d_json']
            except:
                signals['rolled_forecast_7d'] = None
        else:
            signals['rolled_forecast_7d'] = None
        
        # Remove timestamp (not needed in features)
        signals.pop('as_of_timestamp', None)
        
        logger.info(f"Fetched 4 1W signals: {list(signals.keys())}")
        return signals
        
    except Exception as e:
        logger.warning(f"Failed to fetch 1W signals: {e} - using defaults")
        return {
            'volatility_score_1w': 0.0,
            'delta_1w_vs_spot': 0.0,
            'momentum_1w_7d': 0.0,
            'short_bias_score_1w': 0.0,
            'rolled_forecast_7d': None
        }

def assemble_features():
    """Assemble complete feature vector: 209 + 4 = 213 features"""
    logger.info("Assembling features...")
    
    # Get 209 features
    features_209, date = get_latest_209_features()
    
    # Get 1W signals
    signals_1w = get_latest_1w_signals()
    
    # Merge (signals are separate keys)
    complete_features = {**features_209}
    
    # Add 1W signals (4 features)
    for key in ['volatility_score_1w', 'delta_1w_vs_spot', 'momentum_1w_7d', 'short_bias_score_1w']:
        complete_features[key] = signals_1w.get(key, 0.0)
    
    # Store rolled_forecast separately (not a feature, used for gate blend)
    # Ensure it's a list of 7 floats
    rolled = signals_1w.get('rolled_forecast_7d')
    if rolled is not None and isinstance(rolled, list) and len(rolled) == 7:
        complete_features['_rolled_forecast_7d'] = [float(x) for x in rolled]
    else:
        complete_features['_rolled_forecast_7d'] = None
    
    # Convert to proper types (skip metadata keys)
    for key, value in complete_features.items():
        if key.startswith('_'):
            continue  # Skip metadata keys like _rolled_forecast_7d
        if value is None:
            complete_features[key] = 0.0
        elif isinstance(value, (int, float)):
            # Handle NaN values
            if isinstance(value, float) and math.isnan(value):
                complete_features[key] = 0.0
            else:
                complete_features[key] = float(value)
        else:
            complete_features[key] = str(value)
    
    feature_count = len([k for k in complete_features.keys() 
                        if not k.startswith('_') and not k.startswith('target_')])
    
    logger.info(f"Assembled {feature_count} features (expected 213)")
    logger.info(f"Features include: {', '.join(list(complete_features.keys())[:10])}...")
    
    return complete_features, date

def save_features(features, output_path):
    """Save assembled features to JSON"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(features, f, indent=2)
    
    logger.info(f"Features saved to {output_path}")

def main() -> tuple:
    logger.info("=" * 80)
    logger.info("1M FEATURE ASSEMBLER")
    logger.info("=" * 80)
    
    try:
        features, date = assemble_features()
        
        # CRITICAL: Apply schema contract - ensure ALL 210 columns exist (targets as None)
        contract = load_schema_contract()
        if contract:
            required_columns = contract['columns']
            features = fill_missing_schema_fields(features, required_columns)
            
            # Explicitly set target columns to None (AutoML requires presence, not value)
            target_cols = [c for c in required_columns if c.startswith('target_')]
            for target in target_cols:
                features[target] = None
            
            logger.info(f"Applied schema contract: {len(features)} columns (includes targets as None)")
        
        # Save to file for predictor job
        save_features(features, 'features_1m_latest.json')
        
        logger.info("=" * 80)
        logger.info("✅ FEATURE ASSEMBLY COMPLETE")
        logger.info(f"Total features: {len([k for k in features.keys() if not k.startswith('_')])}")
        logger.info(f"Date: {date}")
        logger.info("=" * 80)
        
        return features, date
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error("❌ FEATURE ASSEMBLY FAILED")
        logger.error(f"Error: {e}")
        logger.error("=" * 80)
        raise

if __name__ == "__main__":
    main()

