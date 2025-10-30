#!/usr/bin/env python3
"""
EMERGENCY CLEANUP: Delete all endpoints
Run if monthly script fails to cleanup
"""

from google.cloud import aiplatform
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

aiplatform.init(project='cbi-v14', location='us-central1')

# Get all endpoints
endpoints = aiplatform.Endpoint.list()

logger.info("="*80)
logger.info("EMERGENCY ENDPOINT CLEANUP")
logger.info("="*80)

for endpoint in endpoints:
    logger.info(f"Found endpoint: {endpoint.display_name}")
    
    # Undeploy all models
    for deployed_model in endpoint.gca_resource.deployed_models:
        try:
            logger.info(f"  ⏳ Undeploying {deployed_model.display_name}...")
            endpoint.undeploy(deployed_model_id=deployed_model.id, sync=True)
            logger.info(f"  ✅ Undeployed")
        except Exception as e:
            logger.error(f"  ❌ Undeploy failed: {e}")
    
    # Delete endpoint
    try:
        logger.info(f"  🗑️  Deleting endpoint...")
        endpoint.delete(sync=True)
        logger.info(f"  ✅ Deleted")
    except Exception as e:
        logger.error(f"  ❌ Delete failed: {e}")

logger.info("="*80)
logger.info("✅ CLEANUP COMPLETE")
logger.info("="*80)

