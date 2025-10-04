"""
BigQuery loading utilities using db-dtypes for automatic type conversion
"""
from google.cloud import bigquery
import db_dtypes
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_load_to_bigquery(client, df, table_id, job_config=None):
    """
    Load DataFrame to BigQuery with db-dtypes handling type conversions
    db-dtypes automatically converts pandas datetime64 -> BigQuery TIMESTAMP
    """
    if df.empty:
        logger.warning(f"Empty DataFrame, skipping load to {table_id}")
        return None
    
    if job_config is None:
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
    
    try:
        logger.info(f"Loading {len(df)} rows to {table_id}")
        logger.info(f"DataFrame columns: {list(df.columns)}")
        logger.info(f"DataFrame dtypes: {df.dtypes.to_dict()}")
        
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        logger.info(f"Successfully loaded {len(df)} rows to {table_id}")
        return job
    except Exception as e:
        logger.error(f"Failed to load to {table_id}: {str(e)}")
        logger.error(f"First row sample: {df.iloc[0].to_dict() if len(df) > 0 else 'empty'}")
        raise