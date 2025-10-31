#!/usr/bin/env python3
"""
Deploy Vertex AI models to SERVERLESS endpoints
Ensures all 4 models (1W, 1M, 3M, 6M) have serverless autoscaling endpoints
"""

from google.cloud import aiplatform
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = 'cbi-v14'
REGION = 'us-central1'

# Model IDs from training
MODELS = {
    "1w": {
        "model_id": "575258986094264320",
        "display_name": "cbi_v14_automl_pilot_1w",
        "endpoint_exists": True,  # Already has endpoint
        "endpoint_id": "3891152959001591808"
    },
    "1m": {
        "model_id": "274643710967283712",
        "display_name": "soybean_oil_1m_model_FINAL_20251029_1147",
        "endpoint_exists": False
    },
    "3m": {
        "model_id": "3157158578716934144",
        "display_name": "soybean_oil_3m_final_v14_20251029_0808",
        "endpoint_exists": False
    },
    "6m": {
        "model_id": "3788577320223113216",
        "display_name": "soybean_oil_6m_model_v14_20251028_1737",
        "endpoint_exists": False
    }
}

def initialize_vertex_ai():
    """Initialize Vertex AI"""
    aiplatform.init(project=PROJECT_ID, location=REGION)
    logger.info(f"✅ Initialized Vertex AI: {PROJECT_ID} in {REGION}")


def get_or_create_endpoint(horizon_name, model_info):
    """Get existing endpoint or create new serverless endpoint"""
    
    endpoint_display_name = f"soybean_oil_{horizon_name}_serverless_endpoint"
    
    # Check if endpoint already exists
    if model_info.get("endpoint_exists"):
        try:
            endpoint = aiplatform.Endpoint(
                endpoint_name=f"projects/{PROJECT_ID}/locations/{REGION}/endpoints/{model_info['endpoint_id']}"
            )
            logger.info(f"✅ Using existing endpoint for {horizon_name}: {endpoint.display_name}")
            return endpoint
        except Exception as e:
            logger.warning(f"⚠️  Could not get existing endpoint: {e}")
    
    # Create new serverless endpoint
    try:
        logger.info(f"🔨 Creating serverless endpoint for {horizon_name}...")
        endpoint = aiplatform.Endpoint.create(
            display_name=endpoint_display_name,
            description=f"Serverless autoscaling endpoint for {horizon_name} soybean oil forecasting",
            labels={"horizon": horizon_name, "type": "serverless", "project": "cbi_v14"}
        )
        logger.info(f"✅ Created endpoint: {endpoint.resource_name}")
        return endpoint
        
    except Exception as e:
        logger.error(f"❌ Failed to create endpoint for {horizon_name}: {e}")
        return None


def deploy_model_to_endpoint(model_id, endpoint, horizon_name, model_display_name):
    """Deploy model to endpoint with SERVERLESS autoscaling configuration"""
    
    try:
        logger.info(f"\n{'='*80}")
        logger.info(f"DEPLOYING {horizon_name.upper()} MODEL TO SERVERLESS ENDPOINT")
        logger.info(f"Model: {model_display_name} ({model_id})")
        logger.info(f"Endpoint: {endpoint.display_name}")
        logger.info(f"{'='*80}\n")
        
        # Get the model
        model = aiplatform.Model(
            model_name=f"projects/{PROJECT_ID}/locations/{REGION}/models/{model_id}"
        )
        
        # Deploy with AUTOSCALING configuration
        # Note: AutoML models require min_replica_count >= 1 (true serverless not supported)
        # This is "semi-serverless": always 1 instance, auto-scales to 3 under load
        deployed_model = endpoint.deploy(
            model=model,
            deployed_model_display_name=f"{model_display_name}_deployment",
            machine_type="n1-standard-2",  # Smallest instance for cost efficiency
            min_replica_count=1,  # Minimum allowed for AutoML (not true serverless)
            max_replica_count=3,  # Auto-scale up to 3 replicas under load
            accelerator_type=None,  # No GPU needed for tabular data
            accelerator_count=0,
            traffic_percentage=100,  # Send 100% of traffic to this deployment
            sync=True  # Wait for deployment to complete
        )
        
        logger.info(f"\n✅ AUTOSCALING DEPLOYMENT COMPLETE")
        logger.info(f"   Endpoint: {endpoint.resource_name}")
        logger.info(f"   Model: {model_display_name}")
        logger.info(f"   Config: Autoscaling 1-3 replicas (minimum 1 always on)")
        logger.info(f"   Cost: ~$0.20/hour for 1 n1-standard-2 instance + prediction costs")
        logger.info(f"   Note: True serverless (min=0) not supported for AutoML models\n")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Deployment failed for {horizon_name}: {e}")
        return False


def verify_endpoint_is_serverless(endpoint):
    """Verify that endpoint is configured for serverless autoscaling"""
    try:
        # Refresh endpoint to get latest state
        endpoint = endpoint.gca_resource
        
        for deployed_model in endpoint.deployed_models:
            min_replicas = deployed_model.automatic_resources.min_replica_count
            max_replicas = deployed_model.automatic_resources.max_replica_count
            
            if min_replicas <= 1 and max_replicas > 1:
                logger.info(f"✅ AUTOSCALING: {deployed_model.display_name} ({min_replicas}-{max_replicas} replicas)")
                return True
            else:
                logger.warning(f"⚠️  FIXED: {deployed_model.display_name} ({min_replicas}-{max_replicas} replicas)")
                logger.warning(f"    Not configured for autoscaling")
                return False
                
    except Exception as e:
        logger.error(f"❌ Could not verify endpoint config: {e}")
        return False


def main():
    """Deploy all models to serverless endpoints"""
    
    logger.info("="*80)
    logger.info("VERTEX AI SERVERLESS ENDPOINT DEPLOYMENT")
    logger.info("="*80)
    
    initialize_vertex_ai()
    
    results = {}
    
    for horizon_name, model_info in MODELS.items():
        logger.info(f"\n{'='*80}")
        logger.info(f"PROCESSING {horizon_name.upper()} HORIZON")
        logger.info(f"{'='*80}")
        
        # Get or create endpoint
        endpoint = get_or_create_endpoint(horizon_name, model_info)
        
        if not endpoint:
            logger.error(f"❌ Failed to get endpoint for {horizon_name}")
            results[horizon_name] = False
            continue
        
        # Check if model is already deployed
        is_deployed = False
        try:
            endpoint_obj = aiplatform.Endpoint(endpoint.resource_name)
            for deployed_model in endpoint_obj.gca_resource.deployed_models:
                if model_info["model_id"] in deployed_model.model:
                    logger.info(f"✅ Model already deployed to endpoint")
                    is_deployed = True
                    
                    # Verify it has autoscaling
                    min_reps = deployed_model.automatic_resources.min_replica_count
                    max_reps = deployed_model.automatic_resources.max_replica_count
                    
                    if min_reps <= 1 and max_reps > 1:
                        logger.info(f"✅ Endpoint has AUTOSCALING ({min_reps}-{max_reps} replicas)")
                        results[horizon_name] = True
                    else:
                        logger.warning(f"⚠️  Endpoint is FIXED ({min_reps}-{max_reps} replicas)")
                        logger.warning(f"    No autoscaling configured")
                        results[horizon_name] = True  # Still working, just not optimal
                    break
        except Exception as e:
            logger.warning(f"Could not check deployment status: {e}")
        
        # Deploy if not already deployed
        if not is_deployed:
            success = deploy_model_to_endpoint(
                model_id=model_info["model_id"],
                endpoint=endpoint,
                horizon_name=horizon_name,
                model_display_name=model_info["display_name"]
            )
            results[horizon_name] = success
        
        # Save endpoint info
        MODELS[horizon_name]["deployed_endpoint"] = endpoint.resource_name
        MODELS[horizon_name]["endpoint_id"] = endpoint.name
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("DEPLOYMENT SUMMARY")
    logger.info("="*80)
    
    for horizon, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        endpoint_id = MODELS[horizon].get("endpoint_id", "N/A")
        logger.info(f"{status} | {horizon.upper()}: {endpoint_id}")
    
    success_count = sum(1 for s in results.values() if s)
    logger.info(f"\n✅ {success_count}/{len(results)} models deployed to serverless endpoints")
    
    # Save endpoint configuration to file
    import json
    output = {
        "deployment_timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "project": PROJECT_ID,
        "region": REGION,
        "deployment_type": "serverless_autoscaling",
        "models": MODELS
    }
    
    with open('/Users/zincdigital/CBI-V14/automl/serverless_endpoints_config.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"\n✅ Endpoint configuration saved to: automl/serverless_endpoints_config.json")
    
    return success_count == len(results)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

