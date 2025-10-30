#!/usr/bin/env python3
"""
SIMPLE SEQUENTIAL TRAINING - ONE AT A TIME
==========================================
Launch 1M, wait for completion, then 3M, then done.
No parallel processing, no complex logic.
"""

import logging
from google.cloud import aiplatform
from datetime import datetime
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

project_id = "cbi-v14"
region = "us-central1"
aiplatform.init(project=project_id, location=region)

def launch_and_wait(horizon, target_col, bq_source, expected_rows):
    """Launch a model and wait for it to complete."""
    
    budget = 1333
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🚀 LAUNCHING {horizon.upper()} MODEL")
    logger.info(f"{'='*60}")
    logger.info(f"Target: {target_col}")
    logger.info(f"Source: {bq_source}")
    logger.info(f"Rows: {expected_rows} (NULL-free)")
    logger.info(f"Budget: ${budget/50:.0f}")
    
    try:
        # Create dataset
        dataset = aiplatform.TabularDataset.create(
            display_name=f"cbi_v14_{horizon}_simple_{timestamp}",
            bq_source=bq_source
        )
        logger.info(f"✅ Dataset created")
        
        # Create and run training job
        job = aiplatform.AutoMLTabularTrainingJob(
            display_name=f"cbi_v14_{horizon}_simple_{timestamp}",
            optimization_prediction_type="regression",
            optimization_objective="minimize-rmse"
        )
        
        logger.info(f"🎯 Starting training...")
        
        # Run with sync=True to wait for completion
        model = job.run(
            dataset=dataset,
            target_column=target_col,
            budget_milli_node_hours=budget,
            model_display_name=f"soybean_oil_{horizon}_simple_{timestamp}",
            sync=True  # WAIT FOR COMPLETION
        )
        
        logger.info(f"✅ {horizon.upper()} MODEL COMPLETED SUCCESSFULLY")
        logger.info(f"Model: {model.resource_name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ {horizon.upper()} FAILED: {str(e)}")
        return False

def main():
    """Run models one at a time, sequentially."""
    
    logger.info("🔥 CBI-V14 SIMPLE SEQUENTIAL TRAINING")
    logger.info("Running models one at a time until completion")
    
    models = [
        ("1m", "target_1m", f"bq://{project_id}.models_v4.training_dataset_1m_filtered", 1228),
        ("3m", "target_3m", f"bq://{project_id}.models_v4.training_dataset_3m_filtered", 1168)
    ]
    
    successful = []
    failed = []
    
    for horizon, target_col, bq_source, rows in models:
        logger.info(f"\n⏳ Starting {horizon.upper()} model...")
        
        success = launch_and_wait(horizon, target_col, bq_source, rows)
        
        if success:
            successful.append(horizon)
            logger.info(f"✅ {horizon.upper()} completed successfully")
        else:
            failed.append(horizon)
            logger.error(f"❌ {horizon.upper()} failed - STOPPING")
            break  # Stop on first failure
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info(f"FINAL RESULTS")
    logger.info(f"{'='*60}")
    logger.info(f"Successful: {len(successful)} - {successful}")
    logger.info(f"Failed: {len(failed)} - {failed}")
    
    if len(successful) == 2:
        logger.info("🎉 ALL MODELS COMPLETED SUCCESSFULLY")
        logger.info("Plus 6M model from earlier = 3 total models ready")
    else:
        logger.error("❌ NOT ALL MODELS COMPLETED")

if __name__ == "__main__":
    main()




