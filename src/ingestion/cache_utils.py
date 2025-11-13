#!/usr/bin/env python3
"""
Caching utilities for CBI-V14 data pipeline
Implements file-based caching with TTL and intelligent cache management
"""

import os
import json
import pickle
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class DataCache:
    """
    File-based caching system for API responses and processed data
    
    Features:
    - TTL-based expiration
    - Content-based cache keys
    - Automatic cleanup of expired entries
    - Support for JSON, pickle, and CSV formats
    """
    
    def __init__(self, cache_dir=None, default_ttl_hours=6):
        # Auto-detect cache directory relative to repo root
        if cache_dir is None:
            # Try to find repo root by looking for common markers
            current_path = Path(__file__).resolve()
            repo_root = None
            for parent in current_path.parents:
                if (parent / "QUICK_REFERENCE.txt").exists() or (parent / ".git").exists():
                    repo_root = parent
                    break
            if repo_root:
                cache_dir = repo_root / "cache"
            else:
                # Fallback to current directory
                cache_dir = Path.cwd() / "cache"
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl_hours = default_ttl_hours  # Increased default TTL
        
        # Create subdirectories for different data types
        (self.cache_dir / "api_responses").mkdir(exist_ok=True)
        (self.cache_dir / "processed_data").mkdir(exist_ok=True)
        (self.cache_dir / "weather_data").mkdir(exist_ok=True)
        (self.cache_dir / "news_data").mkdir(exist_ok=True)
        (self.cache_dir / "social_data").mkdir(exist_ok=True)
        (self.cache_dir / "economic_data").mkdir(exist_ok=True)
        (self.cache_dir / "trump_intel").mkdir(exist_ok=True)
        (self.cache_dir / "bigquery_results").mkdir(exist_ok=True)
        (self.cache_dir / "file_downloads").mkdir(exist_ok=True)
        
    def _generate_cache_key(self, url, params=None):
        """Generate unique cache key from URL and parameters"""
        key_data = url
        if params:
            # Sort params for consistent keys
            sorted_params = json.dumps(params, sort_keys=True)
            key_data += sorted_params
        
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key, data_type="api_responses", format="json"):
        """Get full path for cache file"""
        filename = f"{cache_key}.{format}"
        return self.cache_dir / data_type / filename
    
    def _is_expired(self, cache_path, ttl_hours):
        """Check if cache file is expired"""
        if not cache_path.exists():
            return True
        
        file_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        expiry_time = file_time + timedelta(hours=ttl_hours)
        
        return datetime.now() > expiry_time
    
    def get_api_response(self, url, params=None, ttl_hours=None):
        """
        Get cached API response if available and not expired
        
        Args:
            url: API endpoint URL
            params: Request parameters dict
            ttl_hours: Time to live in hours (uses default if None)
            
        Returns:
            Cached response dict or None if not cached/expired
        """
        ttl_hours = ttl_hours or self.default_ttl_hours
        cache_key = self._generate_cache_key(url, params)
        cache_path = self._get_cache_path(cache_key, "api_responses", "json")
        
        if self._is_expired(cache_path, ttl_hours):
            logger.debug(f"Cache miss/expired for {url}")
            return None
        
        try:
            with open(cache_path, 'r') as f:
                cached_data = json.load(f)
            
            logger.info(f"Cache hit for {url}")
            return cached_data
            
        except Exception as e:
            logger.warning(f"Cache read error for {url}: {e}")
            return None
    
    def set_api_response(self, url, params, response_data):
        """
        Cache API response data
        
        Args:
            url: API endpoint URL
            params: Request parameters dict
            response_data: Response data to cache
        """
        cache_key = self._generate_cache_key(url, params)
        cache_path = self._get_cache_path(cache_key, "api_responses", "json")
        
        try:
            # Add metadata
            cache_data = {
                'url': url,
                'params': params,
                'cached_at': datetime.now().isoformat(),
                'data': response_data
            }
            
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2, default=str)
            
            logger.info(f"Cached response for {url}")
            
        except Exception as e:
            logger.error(f"Cache write error for {url}: {e}")
    
    def get_processed_data(self, data_key, ttl_hours=None):
        """
        Get cached processed DataFrame
        
        Args:
            data_key: Unique identifier for the processed data
            ttl_hours: Time to live in hours
            
        Returns:
            Cached DataFrame or None if not cached/expired
        """
        ttl_hours = ttl_hours or self.default_ttl_hours
        cache_path = self._get_cache_path(data_key, "processed_data", "pkl")
        
        if self._is_expired(cache_path, ttl_hours):
            logger.debug(f"Processed data cache miss/expired for {data_key}")
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                cached_df = pickle.load(f)
            
            logger.info(f"Processed data cache hit for {data_key}")
            return cached_df
            
        except Exception as e:
            logger.warning(f"Processed data cache read error for {data_key}: {e}")
            return None
    
    def set_processed_data(self, data_key, dataframe):
        """
        Cache processed DataFrame
        
        Args:
            data_key: Unique identifier for the processed data
            dataframe: DataFrame to cache
        """
        cache_path = self._get_cache_path(data_key, "processed_data", "pkl")
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(dataframe, f)
            
            logger.info(f"Cached processed data for {data_key}")
            
        except Exception as e:
            logger.error(f"Processed data cache write error for {data_key}: {e}")
    
    def cleanup_expired(self):
        """Remove all expired cache files"""
        removed_count = 0
        
        for cache_subdir in self.cache_dir.iterdir():
            if cache_subdir.is_dir():
                for cache_file in cache_subdir.iterdir():
                    if cache_file.is_file():
                        # Use default TTL for cleanup
                        if self._is_expired(cache_file, self.default_ttl_hours * 24):  # 24x longer for cleanup
                            try:
                                cache_file.unlink()
                                removed_count += 1
                                logger.debug(f"Removed expired cache file: {cache_file}")
                            except Exception as e:
                                logger.warning(f"Failed to remove cache file {cache_file}: {e}")
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} expired cache files")
        
        return removed_count
    
    def cache_bigquery_result(self, query, result_df, ttl_hours=None):
        """
        Cache BigQuery query results
        
        Args:
            query: SQL query string
            result_df: DataFrame result
            ttl_hours: Time to live in hours
        """
        ttl_hours = ttl_hours or self.default_ttl_hours
        cache_key = hashlib.md5(query.encode()).hexdigest()
        cache_path = self._get_cache_path(cache_key, "bigquery_results", "pkl")
        
        try:
            cache_data = {
                'query': query,
                'cached_at': datetime.now().isoformat(),
                'result': result_df
            }
            
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
            
            logger.info(f"Cached BigQuery result: {len(result_df)} rows")
            
        except Exception as e:
            logger.error(f"Failed to cache BigQuery result: {e}")
    
    def get_cached_bigquery_result(self, query, ttl_hours=None):
        """
        Get cached BigQuery result
        
        Args:
            query: SQL query string
            ttl_hours: Time to live in hours
            
        Returns:
            Cached DataFrame or None
        """
        ttl_hours = ttl_hours or self.default_ttl_hours
        cache_key = hashlib.md5(query.encode()).hexdigest()
        cache_path = self._get_cache_path(cache_key, "bigquery_results", "pkl")
        
        if self._is_expired(cache_path, ttl_hours):
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                cached_data = pickle.load(f)
            
            logger.info(f"BigQuery cache hit: {len(cached_data['result'])} rows")
            return cached_data['result']
            
        except Exception as e:
            logger.warning(f"Failed to read BigQuery cache: {e}")
            return None
    
    def cache_file_download(self, url, file_content, ttl_hours=None):
        """
        Cache downloaded file content
        
        Args:
            url: File URL
            file_content: File content (bytes or string)
            ttl_hours: Time to live in hours
        """
        ttl_hours = ttl_hours or (self.default_ttl_hours * 4)  # Files cached longer
        cache_key = hashlib.md5(url.encode()).hexdigest()
        
        # Determine file extension from URL
        file_ext = url.split('.')[-1] if '.' in url else 'dat'
        cache_path = self._get_cache_path(cache_key, "file_downloads", file_ext)
        
        try:
            mode = 'wb' if isinstance(file_content, bytes) else 'w'
            with open(cache_path, mode) as f:
                f.write(file_content)
            
            logger.info(f"Cached file download: {len(file_content)} bytes")
            
        except Exception as e:
            logger.error(f"Failed to cache file download: {e}")
    
    def get_cached_file_download(self, url, ttl_hours=None):
        """
        Get cached file download
        
        Args:
            url: File URL
            ttl_hours: Time to live in hours
            
        Returns:
            File content or None
        """
        ttl_hours = ttl_hours or (self.default_ttl_hours * 4)
        cache_key = hashlib.md5(url.encode()).hexdigest()
        
        # Try different extensions
        for ext in ['csv', 'json', 'xml', 'txt', 'dat']:
            cache_path = self._get_cache_path(cache_key, "file_downloads", ext)
            if cache_path.exists() and not self._is_expired(cache_path, ttl_hours):
                try:
                    # Try binary first, then text
                    try:
                        with open(cache_path, 'rb') as f:
                            content = f.read()
                        logger.info(f"File cache hit (binary): {len(content)} bytes")
                        return content
                    except:
                        with open(cache_path, 'r') as f:
                            content = f.read()
                        logger.info(f"File cache hit (text): {len(content)} chars")
                        return content
                except Exception as e:
                    logger.warning(f"Failed to read cached file: {e}")
                    continue
        
        return None
    
    def get_cache_stats(self):
        """Get cache statistics"""
        stats = {
            'total_files': 0,
            'total_size_mb': 0,
            'by_type': {}
        }
        
        for cache_subdir in self.cache_dir.iterdir():
            if cache_subdir.is_dir():
                subdir_files = 0
                subdir_size = 0
                
                for cache_file in cache_subdir.iterdir():
                    if cache_file.is_file():
                        subdir_files += 1
                        subdir_size += cache_file.stat().st_size
                
                stats['by_type'][cache_subdir.name] = {
                    'files': subdir_files,
                    'size_mb': round(subdir_size / 1024 / 1024, 2)
                }
                
                stats['total_files'] += subdir_files
                stats['total_size_mb'] += subdir_size / 1024 / 1024
        
        stats['total_size_mb'] = round(stats['total_size_mb'], 2)
        return stats


def cached_api_request(cache_instance, url, params=None, ttl_hours=1):
    """
    Decorator function for caching API requests
    
    Usage:
        cache = DataCache()
        
        @cached_api_request(cache, ttl_hours=2)
        def fetch_weather_data(station_id, start_date):
            # Your API call here
            return requests.get(url, params=params).json()
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key from function arguments
            cache_key_data = f"{func.__name__}_{str(args)}_{str(kwargs)}"
            
            # Check cache first
            cached_result = cache_instance.get_api_response(cache_key_data, None, ttl_hours)
            if cached_result is not None:
                return cached_result['data']
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_instance.set_api_response(cache_key_data, kwargs, result)
            
            return result
        
        return wrapper
    return decorator


# Global cache instance
global_cache = DataCache()

def get_cache():
    """Get the global cache instance"""
    return global_cache
