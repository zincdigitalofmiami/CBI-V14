#!/usr/bin/env python3
"""
CBI-V14 Vertex AI AutoML - RESEARCH-BASED 2025 IMPLEMENTATION
============================================================

Based on deep research of 2025 Vertex AI SDK:
1. optimization_prediction_type="regression" REQUIRED in constructor
2. NO excluded_columns parameter - handle at BigQuery level  
3. column_transformations goes in CONSTRUCTOR, not run()
4. Minimal parameters for maximum compatibility

Research Sources:
- Google Cloud Documentation 2024/2025
- Stack Overflow solutions for SDK compatibility
- GitHub google-cloud-aiplatform source code

Author: CBI-V14 Platform Team
Date: October 28, 2025
"""

import logging
from google.cloud import aiplatform
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Vertex AI
project_id = "cbi-v14"
region = "us-central1"
aiplatform.init(project=project_id, location=region)

# Configuration based on research
HORIZONS = {
    '1m': 'target_1m', 
    '3m': 'target_3m',
    '6m': 'target_6m'
}

# Use BigQuery source directly (proven to work in pilot)
BQ_SOURCE = f"bq://{project_id}.models_v4.training_dataset_super_enriched"

def train_horizon_model(horizon_name, target_column, budget_milli_node_hours=1333):
    """
    Train Vertex AI AutoML model using 2025 research-based parameters
    
    Based on research:
    - optimization_prediction_type REQUIRED in constructor
    - column_transformations in constructor (if needed)
    - Minimal run() parameters for compatibility
    """
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    dataset_name = f"cbi_v14_{horizon_name}_{timestamp}"
    job_display_name = f"cbi_v14_automl_{horizon_name}_{timestamp}"
    model_display_name = f"soybean_oil_{horizon_name}_v14_{timestamp}"
    
    logger.info(f"\n{'=' * 80}")
    logger.info(f"🚀 LAUNCHING {horizon_name.upper()} HORIZON TRAINING")
    logger.info(f"{'=' * 80}")
    logger.info(f"Target: {target_column}")
    logger.info(f"Budget: {budget_milli_node_hours} milli-node-hours (~${budget_milli_node_hours/50:.0f})")
    logger.info(f"Dataset: {dataset_name}")
    
    try:
        # Step 1: Create dataset from BigQuery (this worked in pilot)
        logger.info("Creating Vertex AI dataset from BigQuery...")
        dataset = aiplatform.TabularDataset.create(
            display_name=dataset_name,
            bq_source=BQ_SOURCE
        )
        logger.info(f"✅ Dataset created: {dataset.resource_name}")
        
        # Step 2: Create training job with RESEARCH-BASED parameters
        logger.info("Creating AutoML training job with 2025 SDK parameters...")
        
        # CRITICAL: Based on research, optimization_prediction_type is REQUIRED
        job = aiplatform.AutoMLTabularTrainingJob(
            display_name=job_display_name,
            optimization_prediction_type="regression",  # REQUIRED parameter (research confirmed)
            optimization_objective="minimize-rmse"      # Standard objective
            # NOTE: column_transformations would go here if needed, NOT in run()
        )
        
        logger.info("✅ Training job created successfully")
        
        # Step 3: Run with MINIMAL parameters (research-based approach)
        logger.info(f"🎯 Submitting training job to Vertex AI...")
        logger.info(f"   Using MINIMAL parameters for maximum compatibility")
        
        # Based on research: Use only essential parameters in run()
        model = job.run(
            dataset=dataset,
            target_column=target_column,
            budget_milli_node_hours=budget_milli_node_hours,
            model_display_name=model_display_name,
            # Removed ALL problematic parameters based on research:
            # - NO excluded_columns (doesn't exist)
            # - NO column_transformations (goes in constructor)
            # - NO export_evaluated_data_items (version compatibility issue)
        )
        
        logger.info(f"\n✅ TRAINING JOB LAUNCHED SUCCESSFULLY!")
        logger.info(f"   Job: {job_display_name}")
        logger.info(f"   Model: {model_display_name}")
        logger.info(f"   Resource: {model.resource_name if model else 'Pending'}")
        logger.info(f"   Console: https://console.cloud.google.com/ai/platform/locations/{region}/training")
        
        return {
            "status": "SUCCESS",
            "model": model,
            "job": job,
            "horizon": horizon_name,
            "target": target_column,
            "budget": budget_milli_node_hours
        }
        
    except Exception as e:
        logger.error(f"\n❌ FAILED TO LAUNCH {horizon_name.upper()}: {str(e)}")
        logger.error(f"   Error type: {type(e).__name__}")
        logger.error(f"   Full error: {str(e)}")
        
        return {
            "status": "FAILED",
            "error": str(e),
            "horizon": horizon_name,
            "target": target_column
        }

def main():
    """Main execution with research-based approach"""
    
    logger.info("\n" + "🔥" * 60)
    logger.info("CBI-V14 VERTEX AI AUTOML - RESEARCH-BASED 2025 IMPLEMENTATION")
    logger.info("Budget: 4,000 milli-node-hours (~$80)")
    logger.info("Horizons: 1M, 3M, 6M (1W already completed)")
    logger.info("Features: 209 including Big 8 + China + Argentina + Industrial")
    logger.info("🔥" * 60)
    
    # Check SDK version for debugging
    try:
        import google.cloud.aiplatform
        logger.info(f"\n📦 SDK Version: google-cloud-aiplatform {google.cloud.aiplatform.__version__}")
    except:
        logger.warning("Could not determine SDK version")
    
    results = {}
    
    # Launch models sequentially (not parallel) for easier debugging
    logger.info(f"\n🚀 LAUNCHING MODELS SEQUENTIALLY...")
    
    for horizon_name, target_col in HORIZONS.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"PROCESSING {horizon_name.upper()} HORIZON")
        logger.info(f"{'='*60}")
        
        result = train_horizon_model(horizon_name, target_col, 1333)
        results[horizon_name] = result
        
        if result["status"] == "SUCCESS":
            logger.info(f"✅ {horizon_name.upper()} launched successfully")
        else:
            logger.error(f"❌ {horizon_name.upper()} failed: {result.get('error', 'Unknown error')}")
    
    # Summary
    successful = sum(1 for r in results.values() if r["status"] == "SUCCESS")
    failed = len(results) - successful
    
    logger.info(f"\n{'='*80}")
    logger.info(f"📊 FINAL LAUNCH SUMMARY")
    logger.info(f"{'='*80}")
    logger.info(f"Total horizons: {len(results)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Success rate: {successful/len(results)*100:.1f}%")
    
    if successful > 0:
        logger.info(f"\n✅ SUCCESSFUL LAUNCHES:")
        for horizon, data in results.items():
            if data["status"] == "SUCCESS":
                logger.info(f"   {horizon.upper()}: Budget {data['budget']}, Target {data['target']}")
    
    if failed > 0:
        logger.error(f"\n❌ FAILED LAUNCHES:")
        for horizon, data in results.items():
            if data["status"] == "FAILED":
                logger.error(f"   {horizon.upper()}: {data.get('error', 'Unknown error')}")
    
    # Next steps
    if successful > 0:
        logger.info(f"\n🎯 NEXT STEPS:")
        logger.info(f"   Monitor training progress in Vertex AI console")
        logger.info(f"   Expected completion: 2-4 hours")
        logger.info(f"   Total budget: ~${successful * 1333 / 50:.0f}")
    
    return results

if __name__ == "__main__":
    results = main()
