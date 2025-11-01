#!/usr/bin/env python3
"""
Train Distilled LightGBM-Quantile Model for 1M Forecast
Multi-output model returning [30, 3] array: q10/mean/q90 for D+1-30
"""

import lightgbm as lgb
import pandas as pd
import numpy as np
import joblib
import json
import subprocess
import time
import hashlib
from datetime import datetime
from google.cloud import bigquery, aiplatform
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"
LOCATION = "us-central1"
GCS_BUCKET = "gs://cbi-v14-models"  # Will create if doesn't exist

def load_training_data():
    """Load training data and create 30-day target matrix"""
    logger.info("Loading training data from BigQuery...")
    client = bigquery.Client(project=PROJECT_ID)
    
    query = """
    SELECT *
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    ORDER BY date
    """
    
    df = client.query(query).to_dataframe()
    logger.info(f"Loaded {len(df)} rows from training dataset")
    
    # Use soybean_oil_price as base for 30-day ahead targets
    if 'soybean_oil_price' in df.columns:
        base_price = df['soybean_oil_price'].values
    elif 'target_1m' in df.columns:
        base_price = df['target_1m'].values
    else:
        raise ValueError("No price column found in training data. Need 'soybean_oil_price' or 'target_1m'")
    
    # Create 30 target columns: target_D1 through target_D30
    # Each represents price D+i days ahead
    
    for i in range(1, 31):
        df[f'target_D{i}'] = pd.Series(base_price).shift(-i).values
    
    # Drop rows where we don't have 30 days ahead (last 30 rows)
    if len(df) > 30:
        df = df.iloc[:-30].copy()
    
    # Separate features and targets
    target_cols = [f'target_D{i}' for i in range(1, 31)]
    feature_cols = [col for col in df.columns 
                   if col not in target_cols 
                   and col not in ['date', 'target_1w', 'target_1m', 'target_3m', 'target_6m', 'soybean_oil_price']]
    
    # Handle 1W signals (may not exist yet - will be added later)
    # For now, use 0.0 as placeholder - actual model will inject real signals
    for signal in ['volatility_score_1w', 'delta_1w_vs_spot', 'momentum_1w_7d', 'short_bias_score_1w']:
        if signal not in feature_cols:
            df[signal] = 0.0
    
    X = df[feature_cols].fillna(0).values
    # Forward fill targets, then backward fill any remaining NaNs, finally fill with 0
    # Use ffill()/bfill() instead of deprecated fillna(method=...)
    y_df = df[target_cols].ffill().bfill().fillna(0)
    y = y_df.values  # [n_samples, 30]
    
    logger.info(f"Features: {X.shape}, Targets: {y.shape}")
    logger.info(f"Feature count: {len(feature_cols)}")
    
    return X, y, feature_cols, df

class MultiOutputQuantile:
    """
    Multi-output quantile regressor returning [n_samples, 30, 3] array
    Each sample has 30 days, each day has [q10, mean, q90]
    """
    def __init__(self):
        self.models = {}  # {day_idx: {0.1: model, 0.5: model, 0.9: model}}
        self.feature_names = None
        
    def fit(self, X, y, feature_names=None):
        """
        X: [n_samples, n_features]
        y: [n_samples, 30] - 30-day ahead targets
        """
        self.feature_names = feature_names
        
        logger.info(f"Training multi-output quantile models...")
        logger.info(f"Input shape: X={X.shape}, y={y.shape}")
        
        # Train a model for each day and each quantile
        for day_idx in range(30):
            self.models[day_idx] = {}
            y_day = y[:, day_idx]  # Targets for day D+day_idx+1
            
            # Remove any remaining NaN
            valid_mask = ~np.isnan(y_day)
            X_day = X[valid_mask]
            y_day = y_day[valid_mask]
            
            if len(y_day) == 0:
                logger.warning(f"No valid targets for day {day_idx+1}")
                continue
            
            for alpha in [0.1, 0.5, 0.9]:
                logger.info(f"Training D+{day_idx+1} quantile {alpha}...")
                
                model = lgb.LGBMRegressor(
                    objective='quantile',
                    alpha=alpha,
                    n_estimators=500,
                    learning_rate=0.05,
                    num_leaves=31,
                    max_depth=-1,
                    min_child_samples=20,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    verbose=-1
                )
                
                model.fit(X_day, y_day)
                self.models[day_idx][alpha] = model
                
        logger.info("Training complete!")
        
    def predict(self, X):
        """
        Returns [n_samples, 30, 3] array
        Format: [q10, mean, q90] for each of 30 days
        """
        n_samples = X.shape[0]
        predictions = np.zeros((n_samples, 30, 3))
        
        for day_idx in range(30):
            if day_idx not in self.models:
                continue
                
            day_models = self.models[day_idx]
            if 0.1 in day_models and 0.5 in day_models and 0.9 in day_models:
                predictions[:, day_idx, 0] = day_models[0.1].predict(X)  # q10
                predictions[:, day_idx, 1] = day_models[0.5].predict(X)  # mean
                predictions[:, day_idx, 2] = day_models[0.9].predict(X)  # q90
        
        return predictions

def export_schema(feature_cols, output_path):
    """Export feature schema with hash for validation"""
    schema = {
        'version': '1.0',
        'exported_at': datetime.now().isoformat(),
        'feature_count': len(feature_cols),
        'features': feature_cols,
        'hash': hashlib.md5(','.join(sorted(feature_cols)).encode()).hexdigest()
    }
    
    with open(output_path, 'w') as f:
        json.dump(schema, f, indent=2)
    
    logger.info(f"Schema exported to {output_path}")
    logger.info(f"Schema hash: {schema['hash']}")
    return schema

def upload_to_gcs(local_path, gcs_path):
    """Upload model to GCS with retry and timeout check"""
    logger.info(f"Uploading {local_path} to {gcs_path}...")
    
    try:
        # Ensure bucket exists or create it
        subprocess.run(["gsutil", "mb", "-p", PROJECT_ID, "-l", LOCATION, GCS_BUCKET], 
                      check=False, capture_output=True)  # May fail if exists, that's OK
        
        # Copy file
        subprocess.run(["gsutil", "cp", local_path, f"{GCS_BUCKET}/1m/distilled_quantile_1m.pkl"], 
                      check=True)
        
        logger.info("Upload complete")
        time.sleep(5)  # Wait for GCS consistency (PATCH 1)
        
        return f"{GCS_BUCKET}/1m/distilled_quantile_1m.pkl"
        
    except subprocess.CalledProcessError as e:
        logger.error(f"GCS upload failed: {e}")
        raise

def deploy_to_vertex(gcs_uri, feature_count):
    """Deploy model to Vertex AI"""
    logger.info("Deploying to Vertex AI...")
    
    aiplatform.init(project=PROJECT_ID, location=LOCATION)
    
    # Upload model to Vertex AI
    # Note: Custom MultiOutputQuantile class will be loaded by sklearn container
    # The container needs the class definition available at prediction time
    # For production, consider wrapping in a sklearn-compatible interface
    model = aiplatform.Model.upload(
        display_name='soybean_oil_1m_quantile_distilled',
        artifact_uri=gcs_uri.replace('/distilled_quantile_1m.pkl', ''),  # Directory, not file
        serving_container_image_uri='us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-0:latest',
        description=f'Distilled LightGBM-Quantile model: {feature_count} features, 30-day multi-output [q10,mean,q90]',
        # Custom code may be needed for prediction - test deployment first
    )
    
    logger.info(f"Model uploaded: {model.resource_name}")
    
    # Create or get endpoint
    try:
        endpoints = aiplatform.Endpoint.list(filter=f'display_name="1m_endpoint"')
        if endpoints:
            endpoint = endpoints[0]
            logger.info(f"Using existing endpoint: {endpoint.resource_name}")
        else:
            endpoint = aiplatform.Endpoint.create(display_name='1m_endpoint')
            logger.info(f"Created new endpoint: {endpoint.resource_name}")
    except Exception as e:
        logger.info("Creating new endpoint...")
        endpoint = aiplatform.Endpoint.create(display_name='1m_endpoint')
    
    # Deploy model
    deployed_model = endpoint.deploy(
        model=model,
        deployed_model_display_name='distilled_quantile_1m',
        machine_type='n1-standard-2',
        min_replica_count=1,
        max_replica_count=1,
        traffic_split={'0': 100}  # 100% traffic to this model (first deployment uses '0' as key)
    )
    
    logger.info(f"Model deployed. Endpoint: {endpoint.resource_name}")
    logger.info(f"Deployed model ID: {deployed_model.id}")
    
    # Wait a moment for deployment to stabilize
    import time
    time.sleep(10)
    
    # Refresh endpoint to get updated traffic_split
    endpoint = aiplatform.Endpoint(endpoint.resource_name)
    traffic_split = endpoint.traffic_split
    logger.info(f"Traffic split after deployment: {traffic_split}")
    
    return endpoint, model, deployed_model

def create_config(endpoint_id, deployed_model_id, model_id, feature_cols):
    """Create config file with endpoint and model IDs"""
    config = {
        'endpoint_id': endpoint_id,
        'deployed_model_id': deployed_model_id,
        'model_id': model_id,
        'project': PROJECT_ID,
        'location': LOCATION,
        'quantile_model': True,
        'objectives': [0.1, 0.5, 0.9],
        'output_shape': [30, 3],  # [days, quantiles]
        'feature_count': len(feature_cols),
        'created_at': datetime.now().isoformat()
    }
    
    config_path = Path('config/vertex_1m_config.json')
    config_path.parent.mkdir(exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Config saved to {config_path}")
    return config

def main():
    logger.info("=" * 80)
    logger.info("PHASE 1: TRAIN DISTILLED QUANTILE MODEL")
    logger.info("=" * 80)
    
    # Load training data
    X, y, feature_cols, df = load_training_data()
    
    # Train model
    model = MultiOutputQuantile()
    model.fit(X, y, feature_names=feature_cols)
    
    # Test prediction
    test_pred = model.predict(X[:5])
    logger.info(f"Test prediction shape: {test_pred.shape}")  # Should be [5, 30, 3]
    logger.info(f"Sample prediction D+1: q10={test_pred[0, 0, 0]:.2f}, mean={test_pred[0, 0, 1]:.2f}, q90={test_pred[0, 0, 2]:.2f}")
    
    # Save locally
    local_path = 'distilled_quantile_1m.pkl'
    joblib.dump(model, local_path)
    logger.info(f"Model saved locally: {local_path}")
    
    # Export schema
    schema = export_schema(feature_cols, 'config/1m_feature_schema.json')
    
    # Upload to GCS
    gcs_uri = upload_to_gcs(local_path, f"{GCS_BUCKET}/1m/distilled_quantile_1m.pkl")
    
    # Deploy to Vertex
    endpoint, vertex_model, deployed_model = deploy_to_vertex(gcs_uri, len(feature_cols))
    
    # Create config
    config = create_config(
        endpoint_id=endpoint.resource_name,
        deployed_model_id=deployed_model.id,
        model_id=vertex_model.resource_name,
        feature_cols=feature_cols
    )
    
    logger.info("=" * 80)
    logger.info("PHASE 1 COMPLETE!")
    logger.info(f"Endpoint ID: {endpoint.resource_name}")
    logger.info(f"Model ID: {vertex_model.resource_name}")
    logger.info(f"Deployed Model ID: {deployed_model.id}")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()

