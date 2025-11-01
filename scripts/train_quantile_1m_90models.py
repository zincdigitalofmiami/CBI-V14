#!/usr/bin/env python3
"""
Train 90 Standalone LightGBM Models (30 horizons × 3 quantiles)
Zero deployment risk - 100% native LightGBM models
"""

import lightgbm as lgb
import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime
from google.cloud import bigquery, storage
from pathlib import Path
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"
LOCATION = "us-central1"
GCS_BUCKET = "cbi-v14-models"
GCS_MODEL_PATH = "1m/quantile"

def load_training_data():
    """Load training data and create 30-day target columns"""
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
    for signal in ['volatility_score_1w', 'delta_1w_vs_spot', 'momentum_1w_7d', 'short_bias_score_1w']:
        if signal not in feature_cols:
            df[signal] = 0.0
            feature_cols.append(signal)
    
    X = df[feature_cols].fillna(0).values
    # Forward fill targets, then backward fill any remaining NaNs, finally fill with 0
    y_df = df[target_cols].ffill().bfill().fillna(0)
    y = y_df.values  # [n_samples, 30]
    
    logger.info(f"Features: {X.shape}, Targets: {y.shape}")
    logger.info(f"Feature count: {len(feature_cols)}")
    
    return X, y, feature_cols, df

def save_features_to_cache(X, cache_dir="cache"):
    """Cache features to memory-mapped NumPy file for parallel training"""
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = f"{cache_dir}/features.npy"
    np.save(cache_path, X.astype(np.float32), allow_pickle=False)
    logger.info(f"Cached features to {cache_path} (shape: {X.shape}, dtype: float32)")
    return cache_path

def train_90_models():
    """Train 90 standalone LightGBM models with optimizations"""
    logger.info("=" * 80)
    logger.info("TRAINING 90 STANDALONE LIGHTGBM MODELS")
    logger.info("=" * 80)
    
    # Load data
    X, y, feature_names, df = load_training_data()
    
    # Cache features for parallel training
    cache_path = save_features_to_cache(X)
    X_cached = np.load(cache_path, mmap_mode='r')
    
    # Training configuration
    quantiles = {'q10': 0.1, 'mean': 0.5, 'q90': 0.9}
    horizons = list(range(1, 31))  # D+1 to D+30
    
    # Create output directories
    local_model_dir = Path("models/1m/quantile")
    local_model_dir.mkdir(parents=True, exist_ok=True)
    
    # Store model manifest
    manifest = {
        "architecture": "90_models_3_quantiles",
        "quantiles": list(quantiles.keys()),
        "horizons": horizons,
        "feature_count": len(feature_names),
        "feature_names": feature_names,
        "training_date": datetime.utcnow().isoformat() + 'Z',
        "models": []
    }
    
    # Training optimizations: Train mean first for each horizon, then clone for q10/q90
    logger.info("Training strategy: Warm-start + quantile reuse")
    
    previous_models = {}  # For warm-start: {horizon: model}
    quantile_models = {}  # Store all models: {quantile_horizon: model}
    
    for horizon in horizons:
        day_idx = horizon - 1  # 0-indexed
        y_horizon = y[:, day_idx]
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Training horizon D+{horizon} ({horizon}/{len(horizons)})")
        logger.info(f"{'='*80}")
        
        # Train mean first
        logger.info(f"Training mean (quantile 0.5) for D+{horizon}...")
        mean_model = lgb.LGBMRegressor(
            objective='quantile',
            alpha=0.5,
            learning_rate=0.05,
            num_leaves=64,
            n_estimators=500,
            max_bin=128,
            min_data_in_bin=3,
            num_threads=1,
            verbose=-1
        )
        
        # Warm-start: initialize from previous horizon if available
        if horizon > 1 and (horizon - 1) in previous_models:
            logger.info(f"Warm-starting from D+{horizon-1} model...")
            prev_model_path = f"{local_model_dir}/mean_D{horizon-1}.pkl"
            if os.path.exists(prev_model_path):
                prev_model = joblib.load(prev_model_path)
                # Use previous model as init (LightGBM supports init_model parameter)
                mean_model.fit(
                    X_cached, y_horizon,
                    init_model=prev_model,
                    feature_name=feature_names
                )
            else:
                mean_model.fit(X_cached, y_horizon, feature_name=feature_names)
        else:
            mean_model.fit(X_cached, y_horizon, feature_name=feature_names)
        
        previous_models[horizon] = mean_model
        
        # Save mean model
        mean_path = local_model_dir / f"mean_D{horizon}.pkl"
        joblib.dump(mean_model, mean_path)
        quantile_models[f'mean_D{horizon}'] = mean_model
        manifest["models"].append({
            "quantile": "mean",
            "horizon": horizon,
            "local_path": str(mean_path),
            "gcs_path": f"{GCS_BUCKET}/{GCS_MODEL_PATH}/mean_D{horizon}.pkl"
        })
        logger.info(f"✅ Saved: {mean_path}")
        
        # Clone tree structure for q10 and q90 (quantile reuse)
        for quantile_name, alpha in [('q10', 0.1), ('q90', 0.9)]:
            logger.info(f"Training {quantile_name} (quantile {alpha}) for D+{horizon}...")
            
            # Create new model with same structure but different quantile
            quantile_model = lgb.LGBMRegressor(
                objective='quantile',
                alpha=alpha,
                learning_rate=0.05,
                num_leaves=64,
                n_estimators=500,
                max_bin=128,
                min_data_in_bin=3,
                num_threads=1,
                verbose=-1
            )
            
            # Use mean model as init to reuse tree structure
            quantile_model.fit(
                X_cached, y_horizon,
                init_model=mean_model,
                feature_name=feature_names
            )
            
            # Save quantile model
            quantile_path = local_model_dir / f"{quantile_name}_D{horizon}.pkl"
            joblib.dump(quantile_model, quantile_path)
            quantile_models[f'{quantile_name}_D{horizon}'] = quantile_model
            manifest["models"].append({
                "quantile": quantile_name,
                "horizon": horizon,
                "local_path": str(quantile_path),
                "gcs_path": f"{GCS_BUCKET}/{GCS_MODEL_PATH}/{quantile_name}_D{horizon}.pkl"
            })
            logger.info(f"✅ Saved: {quantile_path}")
        
        # Checkpoint every 10 horizons
        if horizon % 10 == 0:
            logger.info(f"✅ Checkpoint: Completed {horizon}/{len(horizons)} horizons")
            # Save manifest at checkpoint
            manifest_path = Path("config/1m_model_manifest.json")
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            logger.info(f"Saved checkpoint manifest: {manifest_path}")
    
    # Save final manifest
    manifest_path = Path("config/1m_model_manifest.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"\n✅ Final manifest saved: {manifest_path}")
    
    # Upload models to GCS
    logger.info("\n" + "="*80)
    logger.info("UPLOADING MODELS TO GCS")
    logger.info("="*80)
    
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(GCS_BUCKET.replace("gs://", ""))
    
    uploaded_count = 0
    for model_info in manifest["models"]:
        local_path = Path(model_info["local_path"])
        gcs_path = model_info["gcs_path"].replace(f"{GCS_BUCKET}/", "")
        
        if local_path.exists():
            blob = bucket.blob(gcs_path)
            blob.upload_from_filename(str(local_path))
            uploaded_count += 1
            logger.info(f"Uploaded: {gcs_path}")
        else:
            logger.warning(f"Local file not found: {local_path}")
    
    logger.info(f"\n✅ Uploaded {uploaded_count}/{len(manifest['models'])} models to GCS")
    logger.info(f"GCS bucket: {GCS_BUCKET}/{GCS_MODEL_PATH}")
    
    logger.info("\n" + "="*80)
    logger.info("✅ TRAINING COMPLETE: 90 MODELS TRAINED AND UPLOADED")
    logger.info("="*80)
    
    return manifest

if __name__ == "__main__":
    try:
        manifest = train_90_models()
        print(f"\n✅ Success! Trained {len(manifest['models'])} models")
        print(f"Manifest: config/1m_model_manifest.json")
    except Exception as e:
        logger.error(f"\n❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

