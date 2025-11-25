#!/usr/bin/env python3
"""
cached_bigquery.py
Comprehensive BigQuery caching wrapper
Caches all BigQuery operations to minimize costs and improve performance
"""

from google.cloud import bigquery
import pandas as pd
import logging
from cache_utils import get_cache
from datetime import datetime
import functools

logger = logging.getLogger(__name__)

class CachedBigQueryClient:
    """
    BigQuery client wrapper with comprehensive caching
    Caches query results, table metadata, and schema information
    """
    
    def __init__(self, project_id='cbi-v14'):
        self.client = bigquery.Client(project=project_id)
        self.cache = get_cache()
        self.project_id = project_id
    
    def query(self, query_sql, ttl_hours=6):
        """
        Execute BigQuery query with caching
        
        Args:
            query_sql: SQL query string
            ttl_hours: Cache TTL in hours
            
        Returns:
            DataFrame with query results
        """
        # Check cache first
        cached_result = self.cache.get_cached_bigquery_result(query_sql, ttl_hours)
        if cached_result is not None:
            return cached_result
        
        try:
            # Execute query
            logger.info(f"Executing BigQuery query (not cached)")
            query_job = self.client.query(query_sql)
            result_df = query_job.to_dataframe()
            
            # Cache the result
            self.cache.cache_bigquery_result(query_sql, result_df, ttl_hours)
            
            logger.info(f"Query executed: {len(result_df)} rows returned")
            return result_df
            
        except Exception as e:
            logger.error(f"BigQuery query failed: {e}")
            raise
    
    def get_table_info(self, dataset_id, table_id, ttl_hours=24):
        """
        Get table information with caching
        
        Args:
            dataset_id: BigQuery dataset ID
            table_id: BigQuery table ID
            ttl_hours: Cache TTL in hours
            
        Returns:
            Dict with table information
        """
        cache_key = f"table_info_{dataset_id}_{table_id}"
        cached_info = self.cache.get_processed_data(cache_key, ttl_hours)
        
        if cached_info is not None:
            logger.info(f"Table info cache hit: {dataset_id}.{table_id}")
            return cached_info.to_dict('records')[0] if not cached_info.empty else {}
        
        try:
            table_ref = self.client.dataset(dataset_id).table(table_id)
            table = self.client.get_table(table_ref)
            
            table_info = {
                'table_id': table.table_id,
                'dataset_id': table.dataset_id,
                'project_id': table.project,
                'num_rows': table.num_rows,
                'num_bytes': table.num_bytes,
                'created': table.created,
                'modified': table.modified,
                'schema_fields': len(table.schema),
                'table_type': table.table_type,
                'description': table.description
            }
            
            # Cache as DataFrame for consistency
            info_df = pd.DataFrame([table_info])
            self.cache.set_processed_data(cache_key, info_df)
            
            logger.info(f"Table info retrieved: {dataset_id}.{table_id}")
            return table_info
            
        except Exception as e:
            logger.error(f"Failed to get table info for {dataset_id}.{table_id}: {e}")
            return {}
    
    def get_dataset_tables(self, dataset_id, ttl_hours=12):
        """
        List all tables in dataset with caching
        
        Args:
            dataset_id: BigQuery dataset ID
            ttl_hours: Cache TTL in hours
            
        Returns:
            List of table information dicts
        """
        cache_key = f"dataset_tables_{dataset_id}"
        cached_tables = self.cache.get_processed_data(cache_key, ttl_hours)
        
        if cached_tables is not None:
            logger.info(f"Dataset tables cache hit: {dataset_id}")
            return cached_tables.to_dict('records')
        
        try:
            dataset_ref = self.client.dataset(dataset_id)
            tables = list(self.client.list_tables(dataset_ref))
            
            tables_info = []
            for table in tables:
                table_info = {
                    'table_id': table.table_id,
                    'table_type': table.table_type,
                    'created': table.created,
                    'modified': table.modified,
                    'num_rows': getattr(table, 'num_rows', 0),
                    'num_bytes': getattr(table, 'num_bytes', 0)
                }
                tables_info.append(table_info)
            
            # Cache as DataFrame
            tables_df = pd.DataFrame(tables_info)
            self.cache.set_processed_data(cache_key, tables_df)
            
            logger.info(f"Dataset tables retrieved: {dataset_id} ({len(tables_info)} tables)")
            return tables_info
            
        except Exception as e:
            logger.error(f"Failed to list tables in dataset {dataset_id}: {e}")
            return []
    
    def get_table_schema(self, dataset_id, table_id, ttl_hours=24):
        """
        Get table schema with caching
        
        Args:
            dataset_id: BigQuery dataset ID
            table_id: BigQuery table ID
            ttl_hours: Cache TTL in hours
            
        Returns:
            List of schema field dicts
        """
        cache_key = f"table_schema_{dataset_id}_{table_id}"
        cached_schema = self.cache.get_processed_data(cache_key, ttl_hours)
        
        if cached_schema is not None:
            logger.info(f"Table schema cache hit: {dataset_id}.{table_id}")
            return cached_schema.to_dict('records')
        
        try:
            table_ref = self.client.dataset(dataset_id).table(table_id)
            table = self.client.get_table(table_ref)
            
            schema_info = []
            for field in table.schema:
                field_info = {
                    'name': field.name,
                    'field_type': field.field_type,
                    'mode': field.mode,
                    'description': field.description
                }
                schema_info.append(field_info)
            
            # Cache as DataFrame
            schema_df = pd.DataFrame(schema_info)
            self.cache.set_processed_data(cache_key, schema_df)
            
            logger.info(f"Table schema retrieved: {dataset_id}.{table_id} ({len(schema_info)} fields)")
            return schema_info
            
        except Exception as e:
            logger.error(f"Failed to get schema for {dataset_id}.{table_id}: {e}")
            return []
    
    def get_table_sample(self, dataset_id, table_id, limit=10, ttl_hours=6):
        """
        Get sample rows from table with caching
        
        Args:
            dataset_id: BigQuery dataset ID
            table_id: BigQuery table ID
            limit: Number of sample rows
            ttl_hours: Cache TTL in hours
            
        Returns:
            DataFrame with sample rows
        """
        query_sql = f"""
        SELECT *
        FROM `{self.project_id}.{dataset_id}.{table_id}`
        ORDER BY RAND()
        LIMIT {limit}
        """
        
        return self.query(query_sql, ttl_hours)
    
    def get_table_stats(self, dataset_id, table_id, ttl_hours=6):
        """
        Get table statistics with caching
        
        Args:
            dataset_id: BigQuery dataset ID
            table_id: BigQuery table ID
            ttl_hours: Cache TTL in hours
            
        Returns:
            Dict with table statistics
        """
        query_sql = f"""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(DISTINCT DATE(EXTRACT(DATE FROM CURRENT_TIMESTAMP()))) as days_span,
            MIN(DATE(EXTRACT(DATE FROM CURRENT_TIMESTAMP()))) as earliest_date,
            MAX(DATE(EXTRACT(DATE FROM CURRENT_TIMESTAMP()))) as latest_date
        FROM `{self.project_id}.{dataset_id}.{table_id}`
        """
        
        try:
            result_df = self.query(query_sql, ttl_hours)
            if not result_df.empty:
                return result_df.iloc[0].to_dict()
            else:
                return {}
        except Exception as e:
            logger.warning(f"Failed to get table stats for {dataset_id}.{table_id}: {e}")
            return {}


def cached_bigquery_operation(ttl_hours=6):
    """
    Decorator for caching BigQuery operations
    
    Usage:
        @cached_bigquery_operation(ttl_hours=12)
        def get_weather_data():
            return client.query("SELECT * FROM weather_data").to_dataframe()
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Generate cache key from function name and arguments
            cache_key = f"{func.__name__}_{str(args)}_{str(kwargs)}"
            
            # Check cache first
            cached_result = cache.get_processed_data(cache_key, ttl_hours)
            if cached_result is not None:
                logger.info(f"Cached BigQuery operation hit: {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            
            # Cache if result is a DataFrame
            if isinstance(result, pd.DataFrame):
                cache.set_processed_data(cache_key, result)
                logger.info(f"Cached BigQuery operation result: {func.__name__} ({len(result)} rows)")
            
            return result
        
        return wrapper
    return decorator


# Global cached BigQuery client instance
cached_bq_client = CachedBigQueryClient()

def get_cached_bigquery_client():
    """Get the global cached BigQuery client instance"""
    return cached_bq_client











