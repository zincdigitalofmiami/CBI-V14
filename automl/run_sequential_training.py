#!/usr/bin/env python3
"""
CBI-V14 VERTEX AI AUTOML - SEQUENTIAL TRAINING
==============================================

Sequential training approach to avoid quota limits and resource conflicts
- 6M already running, launch 1M next, then 3M
- Full dataset with NULL-free filtered views
- All 209 features (Big 8 + China + Argentina + Industrial)

Author: CBI-V14 Platform Team
Date: October 28, 2025
"""

import logging
from google.cloud import aiplatform
from datetime import datetime
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Initialize Vertex AI
project_id = "cbi-v14"
region = "us-central1"
aiplatform.init(project=project_id, location=region)

# Configuration for remaining horizons (6M already running)
REMAINING_HORIZONS = {
    "1m": {
        "target_column": "target_1m",
        "bq_source": f"bq://{project_id}.models_v4.training_dataset_1m_filtered",
        "expected_rows": 1228
    },
    "3m": {
        "target_column": "target_3m",
        "bq_source": f"bq://{project_id}.models_v4.training_dataset_3m_filtered",
        "expected_rows": 1168
    }
}

BUDGET_PER_HORIZON = 1333  # 4000 / 3 horizons = ~1333 each

def launch_single_horizon(horizon: str) -> dict:
    """Launch AutoML training for a single horizon."""
    
    horizon_config = REMAINING_HORIZONS[horizon]
    target_col = horizon_config["target_column"]
    bq_source = horizon_config["bq_source"]
    expected_rows = horizon_config["expected_rows"]
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    dataset_name = f"cbi_v14_sequential_{horizon}_{timestamp}"
    
    logger.info(f"\n{'='*80}")
    logger.info(f"🚀 LAUNCHING {horizon.upper()} HORIZON TRAINING (SEQUENTIAL)")
    logger.info(f"{'='*80}")
    logger.info(f"Target: {target_col}")
    logger.info(f"BigQuery Source: {bq_source}")
    logger.info(f"Expected Rows: {expected_rows} (NULL-free)")
    logger.info(f"Budget: {BUDGET_PER_HORIZON} milli-node-hours (~${BUDGET_PER_HORIZON/50:.0f})")
    logger.info(f"Dataset: {dataset_name}")
    
    try:
        # Create dataset from filtered BigQuery view
        logger.info("Creating Vertex AI dataset from filtered BigQuery view...")
        dataset = aiplatform.TabularDataset.create(
            display_name=dataset_name,
            bq_source=bq_source
        )
        
        logger.info(f"✅ Dataset created: {dataset.resource_name}")
        
        # Configure training job
        job_display_name = f"cbi_v14_sequential_{horizon}_{timestamp}"
        
        logger.info(f"\n📊 TRAINING CONFIGURATION:")
        logger.info(f"   Job: {job_display_name}")
        logger.info(f"   Target: {target_col}")
        logger.info(f"   Budget: {BUDGET_PER_HORIZON} milli-node-hours")
        logger.info(f"   Features: ALL 209 (Big 8 + China + Argentina + Industrial)")
        logger.info(f"   Training Rows: {expected_rows} (NULL-free)")
        logger.info(f"   Approach: Sequential launch, full dataset")
        
        # Create training job
        job = aiplatform.AutoMLTabularTrainingJob(
            display_name=job_display_name,
            optimization_prediction_type="regression",
            optimization_objective="minimize-rmse",
        )
        
        logger.info(f"\n🎯 SUBMITTING {horizon.upper()} TO VERTEX AI...")
        
        model = job.run(
            dataset=dataset,
            target_column=target_col,
            training_fraction_split=0.8,
            validation_fraction_split=0.1,
            test_fraction_split=0.1,
            budget_milli_node_hours=BUDGET_PER_HORIZON,
            model_display_name=f"soybean_oil_{horizon}_sequential_v14_{timestamp}",
            disable_early_stopping=False,
            sync=False  # Async so we can monitor
        )
        
        logger.info(f"✅ {horizon.upper()} TRAINING LAUNCHED SUCCESSFULLY")
        logger.info(f"   Job ID: {job.resource_name}")
        logger.info(f"   Console: https://console.cloud.google.com/ai/platform/locations/{region}/training")
        
        return {
            "horizon": horizon,
            "status": "LAUNCHED",
            "job": job,
            "job_id": job.resource_name,
            "target": target_col,
            "budget": BUDGET_PER_HORIZON,
            "launch_time": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"❌ FAILED TO LAUNCH {horizon.upper()}: {str(e)}")
        return {
            "horizon": horizon,
            "status": "FAILED",
            "error": str(e),
            "launch_time": datetime.now()
        }

def main():
    """Launch remaining horizons sequentially."""
    
    logger.info("\n" + "🔥" * 60)
    logger.info("CBI-V14 VERTEX AI AUTOML - SEQUENTIAL TRAINING")
    logger.info("6M already running, launching 1M and 3M sequentially")
    logger.info("Budget: 2,666 milli-node-hours (~$53) for remaining")
    logger.info("Features: ALL 209 (Big 8 + China + Argentina + Industrial)")
    logger.info("🔥" * 60)
    
    results = []
    
    # Launch 1M first
    logger.info("\n🚀 LAUNCHING 1M HORIZON...")
    result_1m = launch_single_horizon("1m")
    results.append(result_1m)
    
    if result_1m["status"] == "LAUNCHED":
        logger.info("✅ 1M launched successfully")
        
        # Wait a bit before launching 3M to avoid quota issues
        logger.info("\n⏳ Waiting 30 seconds before launching 3M...")
        time.sleep(30)
        
        # Launch 3M
        logger.info("\n🚀 LAUNCHING 3M HORIZON...")
        result_3m = launch_single_horizon("3m")
        results.append(result_3m)
        
        if result_3m["status"] == "LAUNCHED":
            logger.info("✅ 3M launched successfully")
        else:
            logger.error("❌ 3M launch failed")
    else:
        logger.error("❌ 1M launch failed, skipping 3M")
    
    # Summary
    successful = [r for r in results if r["status"] == "LAUNCHED"]
    failed = [r for r in results if r["status"] == "FAILED"]
    
    logger.info(f"\n{'='*80}")
    logger.info(f"📊 SEQUENTIAL LAUNCH SUMMARY")
    logger.info(f"{'='*80}")
    logger.info(f"Successful: {len(successful)}")
    logger.info(f"Failed: {len(failed)}")
    
    if successful:
        logger.info(f"\n✅ LAUNCHED JOBS:")
        for job in successful:
            logger.info(f"   {job['horizon'].upper()}: {job['job_id'].split('/')[-1]}")
    
    if failed:
        logger.error(f"\n❌ FAILED LAUNCHES:")
        for job in failed:
            logger.error(f"   {job['horizon'].upper()}: {job.get('error', 'Unknown error')}")
    
    # Current status
    logger.info(f"\n🎯 CURRENT TRAINING STATUS:")
    logger.info(f"   6M: Already running (launched earlier)")
    if any(r["horizon"] == "1m" and r["status"] == "LAUNCHED" for r in results):
        logger.info(f"   1M: ✅ Running")
    else:
        logger.info(f"   1M: ❌ Failed to launch")
        
    if any(r["horizon"] == "3m" and r["status"] == "LAUNCHED" for r in results):
        logger.info(f"   3M: ✅ Running")
    else:
        logger.info(f"   3M: ❌ Failed to launch or not attempted")
    
    logger.info(f"\n📊 Monitor all jobs at:")
    logger.info(f"   https://console.cloud.google.com/ai/platform/locations/{region}/training")
    
    return results

if __name__ == "__main__":
    results = main()





