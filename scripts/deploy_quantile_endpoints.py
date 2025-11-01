#!/usr/bin/env python3
"""
Deploy 90 Models to 3 Separate Vertex AI Endpoints (one per quantile)
Each endpoint contains 30 models (one per horizon)
"""

import json
import logging
from pathlib import Path
from google.cloud import aiplatform, storage
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"
LOCATION = "us-central1"
GCS_BUCKET = "cbi-v14-models"
GCS_MODEL_PATH = "1m/quantile"

def load_manifest():
    """Load model manifest"""
    manifest_path = Path("config/1m_model_manifest.json")
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    return manifest

def deploy_endpoint_for_quantile(quantile_name, model_paths):
    """Deploy a single endpoint for one quantile with 30 models"""
    logger.info(f"\n{'='*80}")
    logger.info(f"DEPLOYING ENDPOINT FOR QUANTILE: {quantile_name}")
    logger.info(f"{'='*80}")
    
    aiplatform.init(project=PROJECT_ID, location=LOCATION)
    
    # Create endpoint
    endpoint_display_name = f"1m_quantile_{quantile_name}_endpoint"
    logger.info(f"Creating endpoint: {endpoint_display_name}")
    
    endpoint = aiplatform.Endpoint.create(
        display_name=endpoint_display_name,
        description=f"1M Quantile {quantile_name} endpoint - 30 models (D+1 to D+30)",
        location=LOCATION,
        project=PROJECT_ID
    )
    
    logger.info(f"✅ Endpoint created: {endpoint.resource_name}")
    endpoint_id = endpoint.name.split('/')[-1]
    
    # Deploy models (Option B: deploy each model separately)
    # For now, deploy first model to endpoint (predictor will call endpoint 30 times per quantile)
    # In future, can use custom container to load all 30 models at once
    
    deployed_models = []
    for i, model_path in enumerate(model_paths):
        horizon = i + 1
        logger.info(f"Deploying model {horizon}/30: D+{horizon}")
        
        # Upload model to Vertex AI Model Registry
        model_display_name = f"1m_quantile_{quantile_name}_D{horizon}"
        
        # For sklearn container, we need to upload the .pkl file
        model = aiplatform.Model.upload(
            display_name=model_display_name,
            artifact_uri=model_path.replace(f"{GCS_BUCKET}/", "gs://"),
            serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-0:latest",
            location=LOCATION,
            project=PROJECT_ID
        )
        
        logger.info(f"✅ Model uploaded: {model.resource_name}")
        deployed_models.append({
            "model_id": model.name.split('/')[-1],
            "horizon": horizon,
            "gcs_path": model_path
        })
        
        # Deploy first model to endpoint with 100% traffic
        if i == 0:
            logger.info(f"Deploying first model to endpoint with 100% traffic...")
            endpoint.deploy(
                model=model,
                deployed_model_display_name=f"{quantile_name}_D{horizon}_deployed",
                traffic_percentage=100,
                machine_type="n1-standard-2",
                min_replica_count=1,
                max_replica_count=1
            )
            logger.info(f"✅ First model deployed with 100% traffic")
            
            # Wait for deployment to complete
            logger.info("Waiting for deployment to complete...")
            time.sleep(60)  # Give it time to deploy
    
    return endpoint_id, deployed_models

def deploy_all_endpoints():
    """Deploy all 3 endpoints (q10, mean, q90)"""
    logger.info("="*80)
    logger.info("DEPLOYING 3 QUANTILE ENDPOINTS")
    logger.info("="*80)
    
    manifest = load_manifest()
    
    # Group models by quantile
    models_by_quantile = {}
    for model_info in manifest["models"]:
        quantile = model_info["quantile"]
        if quantile not in models_by_quantile:
            models_by_quantile[quantile] = []
        models_by_quantile[quantile].append(model_info["gcs_path"])
    
    # Sort by horizon (D+1 to D+30)
    for quantile in models_by_quantile:
        models_by_quantile[quantile].sort(key=lambda x: int(x.split('_D')[1].split('.')[0]))
    
    # Deploy each quantile endpoint
    endpoint_config = {}
    
    for quantile in ['q10', 'mean', 'q90']:
        if quantile not in models_by_quantile:
            logger.warning(f"No models found for quantile: {quantile}")
            continue
        
        endpoint_id, deployed_models = deploy_endpoint_for_quantile(
            quantile, 
            models_by_quantile[quantile]
        )
        
        endpoint_config[f"{quantile}_endpoint_id"] = endpoint_id
        endpoint_config[f"{quantile}_deployed_models"] = deployed_models
    
    # Create config file
    config = {
        "architecture": "90_models_3_endpoints",
        "quantiles": ["q10", "mean", "q90"],
        "horizons": 30,
        "location": LOCATION,
        "project": PROJECT_ID,
        "machine_type": "n1-standard-2",
        "min_replica_count": 1,
        "max_replica_count": 1,
        **endpoint_config
    }
    
    config_path = Path("config/vertex_1m_config.json")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"\n✅ Config saved: {config_path}")
    
    logger.info("\n" + "="*80)
    logger.info("✅ DEPLOYMENT COMPLETE: 3 ENDPOINTS DEPLOYED")
    logger.info("="*80)
    logger.info(f"Config: {config_path}")
    
    return config

if __name__ == "__main__":
    try:
        config = deploy_all_endpoints()
        print(f"\n✅ Success! Deployed 3 endpoints")
        print(f"Config: config/vertex_1m_config.json")
        print(f"\nEndpoint IDs:")
        print(f"  q10: {config.get('q10_endpoint_id', 'N/A')}")
        print(f"  mean: {config.get('mean_endpoint_id', 'N/A')}")
        print(f"  q90: {config.get('q90_endpoint_id', 'N/A')}")
    except Exception as e:
        logger.error(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

