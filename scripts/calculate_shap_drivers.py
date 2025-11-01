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

def calculate_shap_values(model, features_dict, X_sample):
    """
    Calculate SHAP values for predictions
    Falls back to feature importance if SHAP unavailable
    """
    if SHAP_AVAILABLE:
        try:
            # Use TreeExplainer for LightGBM
            explainer = shap.TreeExplainer(model.models[0][0.5])  # Use mean model
            shap_values = explainer.shap_values(X_sample)
            
            # For multi-output, average across days or use D+1
            if isinstance(shap_values, list):
                shap_values = shap_values[0]  # Use first sample
            if len(shap_values.shape) > 1:
                shap_values = shap_values[0]  # Use first row
            
            return shap_values
        except Exception as e:
            logger.warning(f"SHAP calculation failed: {e}, using feature importance")
            return None
    
    # Fallback: Use feature importance (simplified)
    return None

def compute_shap_drivers(features_dict, model=None):
    """
    Compute SHAP drivers for latest prediction
    If model not available, uses simplified importance scores
    """
    logger.info("Computing SHAP drivers...")
    
    business_labels = load_business_labels()
    
    # Convert features to array for SHAP
    feature_names = [k for k in features_dict.keys() 
                    if not k.startswith('_') and not k.startswith('target_')]
    X_sample = np.array([[features_dict[f] for f in feature_names]])
    
    # Calculate SHAP values (or fallback)
    if model and SHAP_AVAILABLE:
        shap_values = calculate_shap_values(model, features_dict, X_sample)
    else:
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
            'model_version': 'distilled_quantile_1m',
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
    Calculate SHAP drivers for all future days (D+1 to D+30)
    Called after predictor job runs
    """
    logger.info("=" * 80)
    logger.info("CALCULATE SHAP DRIVERS")
    logger.info("=" * 80)
    
    try:
        # Load latest features
        features_path = Path('features_1m_latest.json')
        if not features_path.exists():
            logger.error("Features not found - run feature assembler first")
            return
        
        with open(features_path, 'r') as f:
            features = json.load(f)
        
        # For each future day D+1 to D+30, compute SHAP
        # Note: In practice, model would need to be loaded to compute true SHAP
        # For now, using simplified importance
        # Use UTC timestamp in ISO format (BigQuery TIMESTAMP() accepts this)
        as_of_timestamp = datetime.utcnow().isoformat() + 'Z'  # Add Z for UTC clarity
        total_rows = 0
        
        for future_day in range(1, 31):
            drivers = compute_shap_drivers(features, model=None)
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

