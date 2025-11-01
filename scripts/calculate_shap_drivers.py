#!/usr/bin/env python3
"""
Calculate SHAP Drivers for 1M Model
Computes SHAP contributions, maps to business labels, stores to BigQuery
"""

import json
import logging
import numpy as np
from datetime import datetime
from pathlib import Path
from google.cloud import bigquery
import pandas as pd

# Try to import SHAP (may not be available in all environments)
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logging.warning("SHAP not available - will use simplified importance")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"

def load_business_labels():
    """Load business label dictionary"""
    labels_path = Path('config/shap_business_labels.json')
    if not labels_path.exists():
        raise FileNotFoundError(f"Business labels not found: {labels_path}")
    
    with open(labels_path, 'r') as f:
        config = json.load(f)
    
    return config.get('features', {})

def get_current_and_historical_features(feature_name, current_value):
    """Get historical value for feature to calculate % change"""
    client = bigquery.Client(project=PROJECT_ID)
    
    # Get value 7 days ago (if available in training dataset)
    # Escape feature name to prevent SQL injection
    safe_feature_name = f"`{feature_name}`"
    
    query = f"""
    SELECT {safe_feature_name} as value
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    WHERE date = DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    LIMIT 1
    """
    
    try:
        df = client.query(query).to_dataframe()
        if not df.empty:
            historical_value = float(df.iloc[0]['value'])
            if historical_value != 0:
                change_pct = ((current_value - historical_value) / historical_value) * 100
            else:
                change_pct = 0.0
        else:
            historical_value = current_value
            change_pct = 0.0
    except:
        historical_value = current_value
        change_pct = 0.0
    
    return current_value, historical_value, change_pct

def load_models_for_shap():
    """
    Load models for SHAP calculation (3-endpoint architecture)
    Returns dict with {quantile: model} for mean model (or all 3 if needed)
    """
    import joblib
    from google.cloud import storage
    
    models = {}
    
    # Load mean model for SHAP (represents primary forecast)
    # Models are stored locally after training or can be loaded from GCS
    local_model_dir = Path("models/1m/quantile")
    
    # Try to load mean_D7 model (representative horizon for D+7)
    # In practice, you'd compute SHAP for key horizons: D+7, D+14, D+30
    for horizon in [7, 14, 30]:
        model_path = local_model_dir / f"mean_D{horizon}.pkl"
        if model_path.exists():
            models[f'D{horizon}'] = joblib.load(model_path)
            logger.info(f"Loaded model for D+{horizon} from {model_path}")
    
    # If no local models, return None (will use fallback)
    if not models:
        logger.warning("No local models found - SHAP will use feature importance fallback")
        return None
    
    return models

def calculate_shap_values_3endpoint(models_dict, features_dict, X_sample, horizon=7):
    """
    Calculate SHAP values for 3-endpoint architecture
    Uses mean model for representative horizon (D+7, D+14, or D+30)
    NOTE: SHAP is expensive - use selectively (debugging, one-off analysis)
    """
    if not SHAP_AVAILABLE:
        return None
    
    if not models_dict:
        return None
    
    # Use model for specified horizon, or closest available
    model_key = f'D{horizon}'
    if model_key not in models_dict:
        # Use closest available horizon
        available = sorted([int(k[1:]) for k in models_dict.keys()])
        closest = min(available, key=lambda x: abs(x - horizon))
        model_key = f'D{closest}'
        logger.info(f"Using model for D+{closest} (requested D+{horizon})")
    
    model = models_dict[model_key]
    
    try:
        # Use TreeExplainer for LightGBM
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_sample)
        
        # Handle output format
        if isinstance(shap_values, list):
            shap_values = shap_values[0]  # Use first sample
        if len(shap_values.shape) > 1:
            shap_values = shap_values[0]  # Use first row
        
        logger.info(f"✅ SHAP calculated for D+{horizon} (using {model_key} model)")
        return shap_values
    except Exception as e:
        logger.warning(f"SHAP calculation failed: {e}, using feature importance")
        return None

def compute_shap_drivers(features_dict, future_day=7, models_dict=None):
    """
    Compute SHAP drivers for latest prediction (3-endpoint architecture)
    If models not available, uses simplified importance scores
    NOTE: Only compute for representative horizons (D+7, D+14, D+30) to control cost
    """
    logger.info(f"Computing SHAP drivers for D+{future_day}...")
    
    business_labels = load_business_labels()
    
    # Convert features to array for SHAP
    feature_names = [k for k in features_dict.keys() 
                    if not k.startswith('_') and not k.startswith('target_')]
    X_sample = np.array([[features_dict[f] for f in feature_names]])
    
    # Calculate SHAP values (3-endpoint architecture)
    # Only compute for key horizons to control cost (D+7, D+14, D+30)
    if future_day in [7, 14, 30] and models_dict and SHAP_AVAILABLE:
        shap_values = calculate_shap_values_3endpoint(models_dict, features_dict, X_sample, future_day)
    else:
        shap_values = None
    
    # Fallback: Use simplified importance if SHAP unavailable or not key horizon
    if shap_values is None:
        logger.info(f"Using feature importance fallback for D+{future_day}")
        # Simplified: Use absolute feature values as proxy
        shap_values = np.array([abs(float(features_dict.get(f, 0))) for f in feature_names])
        shap_values = shap_values / shap_values.sum() * 100  # Normalize
    
    # Create driver records
    drivers = []
    # Get predicted price from latest forecast (for dollar impact calculation)
    # If not available, use a default based on historical average
    predicted_price = 50.0  # Default fallback - will be updated from actual predictions
    
    for idx, feature_name in enumerate(feature_names):
        shap_value = float(shap_values[idx]) if shap_values is not None else 0.0
        current_value = float(features_dict.get(feature_name, 0))
        
        # Get historical value and % change
        current_val, historical_val, change_pct = get_current_and_historical_features(
            feature_name, current_value
        )
        
        # Get business label
        label_info = business_labels.get(feature_name, {})
        business_label = label_info.get('business_label', feature_name)
        interpretation = label_info.get('interpretation', 'Feature impact on price')
        category = label_info.get('category', 'Other')
        
        # Calculate dollar impact
        dollar_impact = shap_value * (predicted_price / 100)  # Simplified
        
        # Determine direction
        if shap_value > 0:
            direction = 'bullish' if change_pct > 0 else 'bearish'
        else:
            direction = 'bearish' if change_pct > 0 else 'bullish'
        
        drivers.append({
            'feature_name': feature_name,
            'business_label': business_label,
            'shap_value': shap_value,
            'feature_current_value': current_val,
            'feature_historical_value': historical_val,
            'feature_change_pct': change_pct,
            'interpretation': interpretation,
            'dollar_impact': dollar_impact,
            'direction': direction,
            'category': category
        })
    
    # Sort by absolute SHAP value
    drivers.sort(key=lambda x: abs(x['shap_value']), reverse=True)
    
    logger.info(f"Computed {len(drivers)} SHAP drivers")
    return drivers

def write_shap_to_bigquery(drivers, future_day, as_of_timestamp):
    """Write SHAP drivers to BigQuery"""
    logger.info(f"Writing SHAP drivers for D+{future_day}...")
    
    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.forecasting_data_warehouse.shap_drivers"
    
    rows = []
    for driver in drivers:
        rows.append({
            'as_of_timestamp': as_of_timestamp,
            'future_day': future_day,
            'feature_name': driver['feature_name'],
            'business_label': driver['business_label'],
            'shap_value': driver['shap_value'],
            'feature_current_value': driver['feature_current_value'],
            'feature_historical_value': driver['feature_historical_value'],
            'feature_change_pct': driver['feature_change_pct'],
            'interpretation': driver['interpretation'],
            'dollar_impact': driver['dollar_impact'],
            'direction': driver['direction'],
            'category': driver['category'],
            'model_version': '90_models_3_endpoints',
            'created_at': datetime.utcnow().isoformat()
        })
    
    # Delete existing rows for this timestamp and future_day (idempotency)
    delete_query = f"""
    DELETE FROM `{table_id}`
    WHERE as_of_timestamp = TIMESTAMP('{as_of_timestamp}') AND future_day = {future_day}
    """
    
    try:
        client.query(delete_query).result()
    except Exception as e:
        logger.warning(f"Delete query failed (table may not exist yet): {e}")
    
    # Insert new rows (top 20 drivers per day)
    errors = client.insert_rows_json(table_id, rows[:20])
    if errors:
        raise ValueError(f"BigQuery insert errors: {errors}")
    
    logger.info(f"Inserted {min(len(rows), 20)} SHAP driver rows")
    return len(rows)

def main():
    """
    Calculate SHAP drivers for representative horizons (D+7, D+14, D+30)
    Called after predictor job runs
    NOTE: SHAP is expensive - only compute for key horizons to control cost
    """
    logger.info("=" * 80)
    logger.info("CALCULATE SHAP DRIVERS (3-ENDPOINT ARCHITECTURE)")
    logger.info("=" * 80)
    logger.info("⚠️  COST WARNING: SHAP is expensive. Only computing for key horizons (D+7, D+14, D+30)")
    logger.info("=" * 80)
    
    try:
        # Load latest features
        features_path = Path('features_1m_latest.json')
        if not features_path.exists():
            logger.error("Features not found - run feature assembler first")
            return
        
        with open(features_path, 'r') as f:
            features = json.load(f)
        
        # Load models for SHAP (3-endpoint architecture)
        models_dict = load_models_for_shap()
        if models_dict:
            logger.info(f"Loaded {len(models_dict)} model(s) for SHAP calculation")
        else:
            logger.warning("No models loaded - using feature importance fallback")
        
        # Only compute SHAP for key horizons (cost control)
        # For other days, use simplified importance or copy from nearest key day
        key_horizons = [7, 14, 30]
        as_of_timestamp = datetime.utcnow().isoformat() + 'Z'
        total_rows = 0
        
        # Compute SHAP for key horizons
        shap_cache = {}
        for future_day in key_horizons:
            logger.info(f"\nComputing SHAP for D+{future_day}...")
            drivers = compute_shap_drivers(features, future_day, models_dict)
            shap_cache[future_day] = drivers
            row_count = write_shap_to_bigquery(drivers, future_day, as_of_timestamp)
            total_rows += row_count
        
        # For other days (D+1-6, D+8-13, D+15-29), use nearest key day's SHAP
        logger.info("\nPropagating SHAP from key horizons to other days...")
        for future_day in range(1, 31):
            if future_day not in key_horizons:
                # Find nearest key horizon
                nearest = min(key_horizons, key=lambda x: abs(x - future_day))
                drivers = shap_cache[nearest]
                row_count = write_shap_to_bigquery(drivers, future_day, as_of_timestamp)
                total_rows += row_count
        
        logger.info("=" * 80)
        logger.info("✅ SHAP CALCULATION COMPLETE")
        logger.info(f"Total rows written: {total_rows}")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error("❌ SHAP CALCULATION FAILED")
        logger.error(f"Error: {e}")
        logger.error("=" * 80)
        raise

if __name__ == "__main__":
    main()

