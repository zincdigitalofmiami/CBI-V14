#!/usr/bin/env python3
"""
Start ARIMA_PLUS baseline models for all horizons in parallel
Cost: ~$1 total
"""

from google.cloud import bigquery
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = 'cbi-v14'
DATASET_ID = 'models_v4'

HORIZONS = {
    '1w': 7,
    '1m': 30,
    '3m': 90,
    '6m': 180
}

def create_arima_model(horizon_name, horizon_days):
    """Create ARIMA_PLUS model for a specific horizon"""
    
    client = bigquery.Client(project=PROJECT_ID)
    
    model_name = f"arima_baseline_{horizon_name}"
    
    query = f"""
    CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.{model_name}`
    OPTIONS(
        model_type = 'ARIMA_PLUS',
        time_series_timestamp_col = 'date',
        time_series_data_col = 'zl_price_current',
        horizon = {horizon_days},
        auto_arima = TRUE,
        decompose_time_series = TRUE,
        clean_spikes_and_dips = TRUE,
        holiday_region = 'US'
    ) AS
    SELECT 
        date,
        zl_price_current
    FROM `{PROJECT_ID}.{DATASET_ID}.training_dataset_super_enriched`
    WHERE date <= '2024-10-31'
    AND zl_price_current IS NOT NULL
    ORDER BY date
    """
    
    logger.info(f"Starting ARIMA model for {horizon_name} ({horizon_days} days)...")
    
    try:
        job = client.query(query)
        # Don't wait for completion - run in parallel
        logger.info(f"  Job started: {job.job_id}")
        return job
        
    except Exception as e:
        logger.error(f"  Failed to start {horizon_name}: {e}")
        return None


def main():
    """Create all ARIMA baseline models in parallel"""
    
    logger.info("="*80)
    logger.info("STARTING ARIMA BASELINE MODELS (PARALLEL)")
    logger.info("="*80)
    logger.info("Cost: ~$1 total")
    logger.info("")
    
    jobs = {}
    
    # Start all jobs in parallel
    for horizon_name, horizon_days in HORIZONS.items():
        job = create_arima_model(horizon_name, horizon_days)
        if job:
            jobs[horizon_name] = job
    
    logger.info(f"\n✅ Started {len(jobs)} ARIMA jobs in parallel")
    logger.info("Jobs will continue running in background")
    logger.info("\nNext: Proceeding to AutoML pilot while ARIMA trains...")
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)


