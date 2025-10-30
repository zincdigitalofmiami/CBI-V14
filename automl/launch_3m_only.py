#!/usr/bin/env python3
"""
Launch 3M model only - 6M and 1M are already running
"""

import logging
from google.cloud import aiplatform
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

project_id = "cbi-v14"
region = "us-central1"  
aiplatform.init(project=project_id, location=region)

def launch_3m():
    """Launch only the 3M model since 6M and 1M are running."""
    
    bq_source = f"bq://{project_id}.models_v4.training_dataset_3m_filtered"
    target_col = "target_3m"
    expected_rows = 1168
    budget = 1333
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    dataset_name = f"cbi_v14_3m_final_{timestamp}"
    
    logger.info(f"🚀 LAUNCHING 3M HORIZON TRAINING")
    logger.info(f"Target: {target_col}")
    logger.info(f"BigQuery Source: {bq_source}")
    logger.info(f"Expected Rows: {expected_rows} (NULL-free)")
    logger.info(f"Budget: {budget} milli-node-hours (~${budget/50:.0f})")
    
    try:
        # Create dataset
        logger.info("Creating Vertex AI dataset...")
        dataset = aiplatform.TabularDataset.create(
            display_name=dataset_name,
            bq_source=bq_source
        )
        logger.info(f"✅ Dataset created: {dataset.resource_name}")
        
        # Create training job
        job_display_name = f"cbi_v14_3m_final_{timestamp}"
        job = aiplatform.AutoMLTabularTrainingJob(
            display_name=job_display_name,
            optimization_prediction_type="regression",
            optimization_objective="minimize-rmse",
        )
        
        logger.info(f"🎯 SUBMITTING 3M TO VERTEX AI...")
        
        model = job.run(
            dataset=dataset,
            target_column=target_col,
            training_fraction_split=0.8,
            validation_fraction_split=0.1,
            test_fraction_split=0.1,
            budget_milli_node_hours=budget,
            model_display_name=f"soybean_oil_3m_final_v14_{timestamp}",
            disable_early_stopping=False,
            sync=False
        )
        
        logger.info(f"✅ 3M TRAINING LAUNCHED SUCCESSFULLY")
        logger.info(f"   Job ID: {job.resource_name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ 3M LAUNCH FAILED: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("=== LAUNCHING 3M MODEL (6M and 1M already running) ===")
    success = launch_3m()
    
    if success:
        logger.info("\n🎉 ALL THREE MODELS NOW RUNNING:")
        logger.info("   6M: ✅ Running")
        logger.info("   1M: ✅ Running") 
        logger.info("   3M: ✅ Running")
        logger.info("\n📊 Monitor at: https://console.cloud.google.com/ai/platform/locations/us-central1/training")
        logger.info("💰 Total budget: ~$80 (4,000 milli-node-hours)")
        logger.info("⏱️  Expected completion: 2-4 hours")
    else:
        logger.error("❌ 3M launch failed")



