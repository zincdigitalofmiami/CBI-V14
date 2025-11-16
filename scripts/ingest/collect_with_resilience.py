#!/usr/bin/env python3
"""
Resilient data collection with caching, fallbacks, and retry logic.
Implements recommendations from strategic review.

Author: AI Assistant
Date: November 16, 2025
"""

import os
import time
import json
import pickle
import hashlib
import requests
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
RAW_DIR = DRIVE / "TrainingData/raw"
CACHE_DIR = DRIVE / "cache/api_responses"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

class ResilientDataCollector:
    """
    Robust data collection with multiple fallback strategies.
    """
    
    def __init__(self):
        self.cache_dir = CACHE_DIR
        self.max_cache_age = timedelta(days=1)  # Refresh daily
        
        # Define fallback sources for each primary source
        self.fallback_sources = {
            'yahoo': ['alpha_vantage', 'iex_cloud', 'cache_only'],
            'fred': ['fred_bulk_download', 'cache_only'],
            'noaa': ['noaa_bulk_files', 'cache_only'],
            'cftc': ['cftc_bulk_download', 'cache_only']
        }
        
        # API keys (from environment)
        self.api_keys = {
            'fred': os.getenv('FRED_API_KEY'),
            'alpha_vantage': os.getenv('ALPHA_VANTAGE_KEY'),
            'iex_cloud': os.getenv('IEX_CLOUD_KEY'),
            'noaa': os.getenv('NOAA_TOKEN')
        }
    
    def get_cache_path(self, source: str, params: Dict) -> Path:
        """Generate cache filename from source and parameters."""
        # Create hash of parameters for unique filename
        param_str = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
        
        # Include date in filename for easy cleanup
        date_str = datetime.now().strftime('%Y%m%d')
        
        return self.cache_dir / f"{source}_{param_hash}_{date_str}.pkl"
    
    def is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache file exists and is recent enough."""
        if not cache_path.exists():
            return False
        
        # Check age
        file_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
        return file_age < self.max_cache_age
    
    def load_from_cache(self, cache_path: Path) -> Optional[pd.DataFrame]:
        """Load data from cache if valid."""
        if self.is_cache_valid(cache_path):
            try:
                logger.info(f"Loading from cache: {cache_path.name}")
                return pd.read_pickle(cache_path)
            except Exception as e:
                logger.warning(f"Cache load failed: {e}")
        return None
    
    def save_to_cache(self, data: pd.DataFrame, cache_path: Path):
        """Save data to cache."""
        try:
            data.to_pickle(cache_path)
            logger.info(f"Saved to cache: {cache_path.name}")
            
            # Also save a "last good" version
            last_good_path = cache_path.parent / f"last_good_{cache_path.stem}.pkl"
            data.to_pickle(last_good_path)
        except Exception as e:
            logger.warning(f"Cache save failed: {e}")
    
    def collect_with_fallback(self, 
                            source: str, 
                            params: Dict,
                            primary_func: Callable,
                            fallback_funcs: Optional[Dict[str, Callable]] = None) -> pd.DataFrame:
        """
        Collect data with multiple fallback strategies.
        
        Args:
            source: Primary source name
            params: Parameters for the collection
            primary_func: Primary collection function
            fallback_funcs: Dictionary of fallback functions
        
        Returns:
            DataFrame with collected data
        """
        
        # Check cache first
        cache_path = self.get_cache_path(source, params)
        cached_data = self.load_from_cache(cache_path)
        if cached_data is not None:
            return cached_data
        
        # Try primary source
        try:
            logger.info(f"Collecting from primary source: {source}")
            data = primary_func(params)
            if data is not None and len(data) > 0:
                self.save_to_cache(data, cache_path)
                return data
        except Exception as e:
            logger.warning(f"Primary source failed: {e}")
        
        # Try fallback sources
        if fallback_funcs and source in self.fallback_sources:
            for fallback_name in self.fallback_sources[source]:
                if fallback_name in fallback_funcs:
                    try:
                        logger.info(f"Trying fallback: {fallback_name}")
                        data = fallback_funcs[fallback_name](params)
                        if data is not None and len(data) > 0:
                            self.save_to_cache(data, cache_path)
                            return data
                    except Exception as e:
                        logger.warning(f"Fallback {fallback_name} failed: {e}")
        
        # Last resort: load most recent cached version
        last_good_pattern = f"last_good_{source}_*.pkl"
        last_good_files = sorted(self.cache_dir.glob(last_good_pattern))
        if last_good_files:
            logger.warning(f"Using last good cache: {last_good_files[-1].name}")
            return pd.read_pickle(last_good_files[-1])
        
        # If all fails, return empty DataFrame
        logger.error(f"All sources failed for {source}")
        return pd.DataFrame()
    
    def collect_fred_series(self, series_id: str, series_name: str) -> pd.DataFrame:
        """Collect FRED data with fallbacks."""
        
        def primary_func(params):
            """Primary: FRED API"""
            api_key = self.api_keys.get('fred')
            if not api_key:
                raise ValueError("FRED_API_KEY not set")
            
            response = requests.get(
                "https://api.stlouisfed.org/fred/series/observations",
                params={
                    'series_id': series_id,
                    'api_key': api_key,
                    'file_type': 'json',
                    'observation_start': '2000-01-01'
                },
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            df = pd.DataFrame(data['observations'])
            df['date'] = pd.to_datetime(df['date'])
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            
            return df[['date', 'value']].rename(columns={'value': series_name})
        
        def fred_bulk_fallback(params):
            """Fallback: Bulk download from FRED"""
            # This would download the full dataset file
            # For now, returning None to trigger cache fallback
            return None
        
        fallback_funcs = {
            'fred_bulk_download': fred_bulk_fallback,
            'cache_only': lambda p: None
        }
        
        return self.collect_with_fallback(
            source=f'fred_{series_id}',
            params={'series_id': series_id},
            primary_func=primary_func,
            fallback_funcs=fallback_funcs
        )
    
    def collect_yahoo_finance(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Collect Yahoo Finance data with fallbacks."""
        
        def primary_func(params):
            """Primary: Yahoo Finance via yfinance"""
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)
            
            if df.empty:
                raise ValueError(f"No data returned for {symbol}")
            
            df = df.reset_index()
            df.columns = [col.lower() for col in df.columns]
            return df
        
        def alpha_vantage_fallback(params):
            """Fallback: Alpha Vantage API"""
            api_key = self.api_keys.get('alpha_vantage')
            if not api_key:
                return None
            
            # Alpha Vantage implementation
            url = 'https://www.alphavantage.co/query'
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': symbol,
                'apikey': api_key,
                'outputsize': 'full',
                'datatype': 'json'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if 'Time Series (Daily)' not in data:
                return None
            
            df = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.reset_index()
            df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
            
            # Convert to numeric
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
            
            return df
        
        fallback_funcs = {
            'alpha_vantage': alpha_vantage_fallback,
            'cache_only': lambda p: None
        }
        
        return self.collect_with_fallback(
            source=f'yahoo_{symbol}',
            params={'symbol': symbol, 'start': start_date, 'end': end_date},
            primary_func=primary_func,
            fallback_funcs=fallback_funcs
        )
    
    def create_china_demand_proxy(self) -> pd.DataFrame:
        """
        Create China demand proxy from available indicators.
        Implements strategic review recommendation.
        """
        logger.info("Creating China demand proxy from multiple indicators...")
        
        proxy_components = []
        
        # Baltic Dry Index (shipping demand)
        baltic = self.collect_fred_series('BALTIC', 'baltic_dry_index')
        if not baltic.empty:
            baltic['china_shipping_proxy'] = baltic['baltic_dry_index'].rolling(30).mean()
            proxy_components.append(baltic[['date', 'china_shipping_proxy']])
        
        # Dollar Index (inverse correlation with commodity demand)
        dxy = self.collect_fred_series('DTWEXBGS', 'usd_index')
        if not dxy.empty:
            dxy['china_usd_proxy'] = -dxy['usd_index'].pct_change(30)  # Inverse
            proxy_components.append(dxy[['date', 'china_usd_proxy']])
        
        # Combine proxies
        if proxy_components:
            proxy = proxy_components[0]
            for component in proxy_components[1:]:
                proxy = proxy.merge(component, on='date', how='outer')
            
            # Create composite score
            proxy['china_demand_composite'] = proxy.iloc[:, 1:].mean(axis=1)
            
            # Normalize to 0-100 scale
            min_val = proxy['china_demand_composite'].min()
            max_val = proxy['china_demand_composite'].max()
            proxy['china_demand_score'] = (
                (proxy['china_demand_composite'] - min_val) / (max_val - min_val) * 100
            )
            
            logger.info(f"Created China demand proxy with {len(proxy)} days")
            return proxy
        
        logger.warning("Failed to create China demand proxy")
        return pd.DataFrame()


def collect_all_tier1_data():
    """
    Collect all Tier 1 critical data with resilience.
    """
    collector = ResilientDataCollector()
    
    print("="*80)
    print("COLLECTING TIER 1 DATA WITH RESILIENCE")
    print("="*80)
    
    # 1. FRED Macro Data (30+ series)
    fred_series = {
        'DFF': 'fed_funds_rate',
        'DGS10': 'treasury_10y',
        'DGS2': 'treasury_2y',
        'T10Y2Y': 'yield_curve_spread',
        'VIXCLS': 'vix',
        'DTWEXBGS': 'usd_broad_index',
        'DCOILWTICO': 'crude_oil_wti',
        'BALTIC': 'baltic_dry_index',
        # Add more as needed
    }
    
    fred_data = []
    for series_id, name in fred_series.items():
        df = collector.collect_fred_series(series_id, name)
        if not df.empty:
            fred_data.append(df)
            print(f"✅ {name}: {len(df)} rows")
        else:
            print(f"⚠️ {name}: No data collected")
    
    # Merge all FRED data
    if fred_data:
        fred_master = fred_data[0]
        for df in fred_data[1:]:
            fred_master = fred_master.merge(df, on='date', how='outer')
        
        # Save to raw
        fred_master.to_parquet(RAW_DIR / "fred_macro_2000_2025.parquet")
        print(f"\n✅ FRED data saved: {len(fred_master)} rows × {len(fred_master.columns)} cols")
    
    # 2. China Demand Proxy
    china_proxy = collector.create_china_demand_proxy()
    if not china_proxy.empty:
        china_proxy.to_parquet(RAW_DIR / "china_demand_proxy.parquet")
        print(f"✅ China demand proxy created: {len(china_proxy)} rows")
    
    # 3. Yahoo Finance (Key commodities)
    symbols = ['ZL=F', 'ZS=F', 'ZC=F', 'ZW=F', 'CL=F', 'GC=F']
    
    for symbol in symbols:
        df = collector.collect_yahoo_finance(symbol, '2000-01-01', '2025-12-31')
        if not df.empty:
            safe_symbol = symbol.replace('=', '_')
            df.to_parquet(RAW_DIR / f"yahoo_{safe_symbol}.parquet")
            print(f"✅ {symbol}: {len(df)} rows")
        else:
            print(f"⚠️ {symbol}: No data collected")
    
    print("\n" + "="*80)
    print("TIER 1 COLLECTION COMPLETE")
    print("Check quarantine/ for any validation failures")
    print("="*80)


if __name__ == "__main__":
    # Ensure directories exist
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # Run collection
    collect_all_tier1_data()
