#!/usr/bin/env python3
"""
Check status of running batch prediction jobs
"""

from google.cloud import aiplatform
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = 'cbi-v14'
REGION = 'us-central1'

aiplatform.init(project=PROJECT_ID, location=REGION)

# The batch job that was created
BATCH_JOB_ID = "6515374901661007872"

# Get the batch prediction job
batch_job = aiplatform.BatchPredictionJob(
    f"projects/1065708057795/locations/{REGION}/batchPredictionJobs/{BATCH_JOB_ID}"
)

logger.info(f"Job: {batch_job.display_name}")
logger.info(f"State: {batch_job.state}")
logger.info(f"Output: {batch_job.output_info}")

if batch_job.state.name == "JOB_STATE_SUCCEEDED":
    logger.info(f"✅ Job completed successfully")
    logger.info(f"   Output table: {batch_job.output_info.bigquery_output_table}")
elif batch_job.state.name == "JOB_STATE_RUNNING":
    logger.info(f"⏳ Job still running...")
elif batch_job.state.name == "JOB_STATE_FAILED":
    logger.error(f"❌ Job failed: {batch_job.error}")

