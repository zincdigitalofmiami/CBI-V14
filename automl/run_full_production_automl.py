#!/usr/bin/env python3
"""
CBI-V14 VERTEX AI AUTOML - FULL PRODUCTION RUN
==============================================

Phase 2.2: Full Production Training
- Budget: 4,000 milli-node-hours ($80)
- Horizons: 1M, 3M, 6M (1W already completed)
- Features: 209 including Big 8 + China + Argentina + Industrial
- Approach: BigQuery direct (institutional-grade)

Author: CBI-V14 Platform Team
Date: October 28, 2025
"""

import logging
from google.cloud import aiplatform
from datetime import datetime
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
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

# Configuration
HORIZONS = ["1m", "3m", "6m"]  # 1w already completed
TARGET_COLUMNS = {
    "1m": "target_1m",
    "3m": "target_3m", 
    "6m": "target_6m"
}

EXCLUDED_COLUMNS = [
    "date", "econ_gdp_growth", "econ_unemployment_rate", 
    "treasury_10y_yield", "news_article_count", "news_avg_score",
    "target_1w", "target_1m", "target_3m", "target_6m"  # Exclude all targets, add back specific one
]

BQ_SOURCE = f"bq://{project_id}.models_v4.training_dataset_super_enriched"
BUDGET_PER_HORIZON = 1333  # 4000 / 3 horizons = ~1333 each

def launch_horizon_training(horizon: str) -> dict:
    """Launch AutoML training for a specific horizon using proper SDK parameters."""
    
    target_col = TARGET_COLUMNS[horizon]
    excluded_cols = [col for col in EXCLUDED_COLUMNS if col != target_col]
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    dataset_name = f"cbi_v14_production_{horizon}_{timestamp}"
    
    logger.info(f"\n{'='*80}")
    logger.info(f"🚀 LAUNCHING {horizon.upper()} HORIZON TRAINING")
    logger.info(f"{'='*80}")
    logger.info(f"Target: {target_col}")
    logger.info(f"Budget: {BUDGET_PER_HORIZON} milli-node-hours (~${BUDGET_PER_HORIZON/50:.0f})")
    logger.info(f"Dataset: {dataset_name}")
    
    try:
        # Create dataset from BigQuery directly (proven approach)
        logger.info("Creating Vertex AI dataset from BigQuery...")
        dataset = aiplatform.TabularDataset.create(
            display_name=dataset_name,
            bq_source=BQ_SOURCE
        )
        
        logger.info(f"✅ Dataset created: {dataset.resource_name}")
        
        # Configure training job
        job_display_name = f"cbi_v14_production_{horizon}_{timestamp}"
        
        logger.info(f"\n📊 TRAINING CONFIGURATION:")
        logger.info(f"   Job: {job_display_name}")
        logger.info(f"   Target: {target_col}")
        logger.info(f"   Budget: {BUDGET_PER_HORIZON} milli-node-hours")
        logger.info(f"   Excluded: {len(excluded_cols)} columns")
        logger.info(f"   Features: ~200 (Big 8 + China + Argentina + Industrial)")
        
        # Create column transformations for excluded columns (research-backed approach)
        column_transformations = []
        for column in excluded_cols:
            column_transformations.append({
                "column_name": column, 
                "transformation": "excluded"
            })
        
        logger.info(f"   Column transformations: {len(column_transformations)} exclusions")
        
        # Create training job with REQUIRED optimization_prediction_type
        job = aiplatform.AutoMLTabularTrainingJob(
            display_name=job_display_name,
            optimization_prediction_type="regression",  # REQUIRED parameter
            optimization_objective="minimize-rmse",
        )
        
        logger.info(f"\n🎯 SUBMITTING TO VERTEX AI...")
        
        model = job.run(
            dataset=dataset,
            target_column=target_col,
            training_fraction_split=0.8,
            validation_fraction_split=0.1,
            test_fraction_split=0.1,
            budget_milli_node_hours=BUDGET_PER_HORIZON,
            model_display_name=f"soybean_oil_{horizon}_model_v14_{timestamp}",
            column_transformations=column_transformations,  # Use this instead of excluded_columns
            disable_early_stopping=False,
            sync=False  # Async for parallel execution
        )
        
        logger.info(f"✅ {horizon.upper()} TRAINING LAUNCHED SUCCESSFULLY")
        logger.info(f"   Job ID: {job.resource_name}")
        logger.info(f"   Console: https://console.cloud.google.com/ai/platform/locations/{region}/training/{job.resource_name.split('/')[-1]}?project={project_id}")
        
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

def monitor_training_jobs(jobs: list) -> dict:
    """Monitor all training jobs until completion."""
    
    logger.info(f"\n{'📊'*40}")
    logger.info("MONITORING PRODUCTION TRAINING JOBS")
    logger.info(f"{'📊'*40}")
    
    completed_jobs = []
    failed_jobs = []
    
    # Initial status
    for job_info in jobs:
        if job_info["status"] == "LAUNCHED":
            logger.info(f"   {job_info['horizon'].upper()}: {job_info['job_id'].split('/')[-1]} - RUNNING")
    
    logger.info(f"\n⏱️  Expected completion: 2-4 hours")
    logger.info(f"💰 Total budget: 4,000 milli-node-hours (~$80)")
    
    # Monitor loop
    while True:
        running_count = 0
        
        for job_info in jobs:
            if job_info["status"] == "LAUNCHED":
                try:
                    job = job_info["job"]
                    current_state = job.state
                    
                    if current_state == 4:  # SUCCEEDED
                        job_info["status"] = "COMPLETED"
                        completed_jobs.append(job_info)
                        logger.info(f"✅ {job_info['horizon'].upper()} COMPLETED!")
                        
                    elif current_state == 5:  # FAILED
                        job_info["status"] = "FAILED"
                        failed_jobs.append(job_info)
                        logger.error(f"❌ {job_info['horizon'].upper()} FAILED!")
                        
                    else:
                        running_count += 1
                        
                except Exception as e:
                    logger.error(f"Error checking {job_info['horizon']}: {str(e)}")
        
        # Status update
        total_jobs = len([j for j in jobs if j["status"] in ["LAUNCHED", "COMPLETED", "FAILED"]])
        if total_jobs > 0:
            logger.info(f"\n📈 STATUS UPDATE:")
            logger.info(f"   Running: {running_count}")
            logger.info(f"   Completed: {len(completed_jobs)}")
            logger.info(f"   Failed: {len(failed_jobs)}")
            logger.info(f"   Progress: {(len(completed_jobs) + len(failed_jobs))/total_jobs*100:.1f}%")
        
        if running_count == 0:
            break
            
        # Wait before next check
        time.sleep(300)  # Check every 5 minutes
    
    return {
        "completed": completed_jobs,
        "failed": failed_jobs,
        "total": len(jobs),
        "success_rate": len(completed_jobs) / len(jobs) * 100 if jobs else 0
    }

def main():
    """Main execution function."""
    
    print("\n" + "🔥" * 60)
    print("CBI-V14 VERTEX AI AUTOML - FULL PRODUCTION RUN")
    print("Budget: 4,000 milli-node-hours (~$80)")
    print("Horizons: 1M, 3M, 6M (1W already completed)")
    print("Features: 209 including Big 8 + China + Argentina + Industrial")
    print("🔥" * 60)
    
    # Launch all horizons in parallel
    logger.info("\n🚀 LAUNCHING ALL HORIZONS IN PARALLEL...")
    
    training_jobs = []
    
    # Use ThreadPoolExecutor for parallel launches
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(launch_horizon_training, horizon): horizon 
                  for horizon in HORIZONS}
        
        for future in as_completed(futures):
            horizon = futures[future]
            try:
                result = future.result()
                training_jobs.append(result)
                logger.info(f"✅ {horizon.upper()} launch completed")
            except Exception as e:
                logger.error(f"❌ {horizon.upper()} launch failed: {str(e)}")
                training_jobs.append({
                    "horizon": horizon,
                    "status": "FAILED",
                    "error": str(e)
                })
    
    # Summary of launches
    successful_launches = [j for j in training_jobs if j["status"] == "LAUNCHED"]
    failed_launches = [j for j in training_jobs if j["status"] == "FAILED"]
    
    logger.info(f"\n📊 LAUNCH SUMMARY:")
    logger.info(f"   Successful: {len(successful_launches)}")
    logger.info(f"   Failed: {len(failed_launches)}")
    
    if successful_launches:
        logger.info(f"\n✅ LAUNCHED JOBS:")
        for job in successful_launches:
            logger.info(f"   {job['horizon'].upper()}: {job['job_id'].split('/')[-1]}")
    
    if failed_launches:
        logger.error(f"\n❌ FAILED LAUNCHES:")
        for job in failed_launches:
            logger.error(f"   {job['horizon'].upper()}: {job.get('error', 'Unknown error')}")
    
    # Monitor if any jobs launched successfully
    if successful_launches:
        logger.info(f"\n📊 STARTING MONITORING...")
        results = monitor_training_jobs(training_jobs)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🎉 FULL PRODUCTION RUN COMPLETE!")
        logger.info(f"{'='*80}")
        logger.info(f"Total jobs: {results['total']}")
        logger.info(f"Completed: {len(results['completed'])}")
        logger.info(f"Failed: {len(results['failed'])}")
        logger.info(f"Success rate: {results['success_rate']:.1f}%")
        
        if results['completed']:
            logger.info(f"\n✅ COMPLETED MODELS:")
            for job in results['completed']:
                logger.info(f"   {job['horizon'].upper()}: Ready for deployment")
        
        return results
    else:
        logger.error(f"\n❌ NO JOBS LAUNCHED SUCCESSFULLY")
        return {"status": "FAILED", "error": "All launches failed"}

if __name__ == "__main__":
    results = main()
