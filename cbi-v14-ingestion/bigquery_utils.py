"""
BigQuery loading utilities using db-dtypes for automatic type conversion
Modern decorator pattern for intelligence collection workflows
Enhanced with caching capabilities
"""
from google.cloud import bigquery
import db_dtypes
import logging
import functools
import time
import uuid
from datetime import datetime
import pandas as pd
from cache_utils import get_cache

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


def intelligence_collector(table_name, max_retries=3, backoff_factor=2, cache_ttl_hours=1):
    """
    Modern decorator for intelligence collection workflows with caching
    
    Features:
    - Automatic error handling with exponential backoff
    - Structured logging with correlation IDs
    - Intelligent caching with TTL
    - Performance monitoring
    - Automatic BigQuery loading
    
    Usage:
        @intelligence_collector('social_sentiment', cache_ttl_hours=2)
        def collect_social_data():
            return pd.DataFrame([...])
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate correlation ID for tracking
            correlation_id = str(uuid.uuid4())[:8]
            start_time = time.time()
            
            logger.info(f"[{correlation_id}] Starting {func.__name__} intelligence collection")
            
            # Check cache first
            cache = get_cache()
            cache_key = f"{func.__name__}_{str(args)}_{str(kwargs)}"
            cached_result = cache.get_processed_data(cache_key, cache_ttl_hours)
            
            if cached_result is not None and not cached_result.empty:
                logger.info(f"[{correlation_id}] Cache hit - returning {len(cached_result)} cached rows")
                return cached_result
            
            for attempt in range(max_retries):
                try:
                    # Execute the collection function
                    logger.info(f"[{correlation_id}] Attempt {attempt + 1}/{max_retries}")
                    
                    result = func(*args, **kwargs)
                    
                    # Handle different return types
                    if isinstance(result, pd.DataFrame):
                        df = result
                    elif isinstance(result, (list, dict)):
                        df = pd.DataFrame(result if isinstance(result, list) else [result])
                    else:
                        logger.warning(f"[{correlation_id}] Unexpected return type: {type(result)}")
                        df = pd.DataFrame()
                    
                    # Skip empty results
                    if df.empty:
                        logger.warning(f"[{correlation_id}] No data collected, skipping BigQuery load")
                        return df
                    
                    # Only add timestamp for tables that expect it (not weather_data)
                    if table_name != 'weather_data' and 'timestamp' not in df.columns:
                        df['timestamp'] = datetime.now()
                    
                    # Log metadata without adding to DataFrame (to avoid schema conflicts)
                    logger.info(f"[{correlation_id}] Metadata - Source: {func.__name__}, Rows: {len(df)}")
                    
                    # Load to BigQuery
                    client = bigquery.Client(project='cbi-v14')
                    table_ref = f"cbi-v14.forecasting_data_warehouse.{table_name}"
                    
                    job_config = bigquery.LoadJobConfig(
                        write_disposition="WRITE_APPEND",
                        autodetect=True
                    )
                    
                    job = safe_load_to_bigquery(client, df, table_ref, job_config)
                    
                    # Cache the result for future use
                    cache.set_processed_data(cache_key, df)
                    
                    # Log success metrics
                    duration = time.time() - start_time
                    logger.info(f"[{correlation_id}] SUCCESS: {len(df)} rows loaded to {table_name} in {duration:.2f}s")
                    
                    return df
                    
                except Exception as e:
                    wait_time = backoff_factor ** attempt
                    logger.error(f"[{correlation_id}] Attempt {attempt + 1} failed: {str(e)}")
                    
                    if attempt < max_retries - 1:
                        logger.info(f"[{correlation_id}] Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"[{correlation_id}] All {max_retries} attempts failed")
                        raise
            
        return wrapper
    return decorator


def quick_save_to_bigquery(data, table_name):
    """
    Quick save function for immediate surgical fixes
    Used for scripts that need immediate BigQuery loading
    """
    if not data:
        logger.warning(f"No data to save to {table_name}")
        return
    
    # Convert to DataFrame if needed
    if isinstance(data, (list, dict)):
        df = pd.DataFrame(data if isinstance(data, list) else [data])
    elif isinstance(data, pd.DataFrame):
        df = data
    else:
        logger.error(f"Unsupported data type for {table_name}: {type(data)}")
        return
    
    if df.empty:
        logger.warning(f"Empty DataFrame, skipping {table_name}")
        return
    
    # Add timestamp if not present
    if 'timestamp' not in df.columns and 'ingestion_timestamp' not in df.columns:
        df['ingestion_timestamp'] = datetime.now()
    
    # Load to BigQuery
    client = bigquery.Client(project='cbi-v14')
    table_ref = f"cbi-v14.forecasting_data_warehouse.{table_name}"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        autodetect=True
    )
    
    try:
        job = safe_load_to_bigquery(client, df, table_ref, job_config)
        logger.info(f"✅ Quick save: {len(df)} rows loaded to {table_name}")
        return job
    except Exception as e:
        logger.error(f"❌ Quick save failed for {table_name}: {e}")
        raise