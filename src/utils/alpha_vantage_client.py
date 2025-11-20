#!/usr/bin/env python3
"""Alpha Vantage API client wrapper with rate limiting and validation"""

import time
import pandas as pd
import io
from datetime import datetime
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.keychain_manager import get_api_key
from utils.data_validation import AlphaDataValidator

class AlphaVantageClient:
    """Wrapper around Alpha Vantage API with rate limiting and validation"""
    
    def __init__(self):
        self.api_key = get_api_key('ALPHA_VANTAGE_API_KEY')
        if not self.api_key:
            raise ValueError(
                "ALPHA_VANTAGE_API_KEY not found in Keychain.\n"
                "Store with: security add-generic-password -a default "
                "-s cbi-v14.ALPHA_VANTAGE_API_KEY -w <key> -U"
            )
        
        self.call_count = 0
        self.last_call_time = None
        self.rate_limit_calls_per_minute = 75  # Plan75
        self.cache = {}  # Simple daily cache
        self.validator = AlphaDataValidator()
    
    def _rate_limit(self):
        """Respect 75 calls/minute (Plan75)"""
        if self.last_call_time:
            elapsed = time.time() - self.last_call_time
            min_delay = 60.0 / self.rate_limit_calls_per_minute  # ~0.8 seconds
            
            if elapsed < min_delay:
                sleep_time = min_delay - elapsed
                time.sleep(sleep_time)
        
        self.last_call_time = time.time()
        self.call_count += 1
        
        if self.call_count % 10 == 0:
            print(f"  API calls used: {self.call_count}")
    
    def _check_cache(self, cache_key):
        """Check if we already fetched this today"""
        today = datetime.now().date()
        key = f"{today}_{cache_key}"
        return self.cache.get(key)
    
    def _save_cache(self, cache_key, data):
        """Save to daily cache"""
        today = datetime.now().date()
        key = f"{today}_{cache_key}"
        self.cache[key] = data
    
    def _validate_and_save(self, df, symbol, data_type, save_path):
        """Validate DataFrame and save to disk"""
        # Validate before saving
        self.validator.validate_dataframe(df, data_type, symbol)
        
        # Save to disk
        save_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(save_path, index=False)
        print(f"  ✅ Saved: {save_path} ({len(df)} rows)")
        
        return df
    
    def commodity_daily(self, symbol, outputsize='full', save_path=None):
        """
        Get daily commodity prices from Alpha Vantage
        Uses dedicated endpoints: WTI, BRENT, NATURAL_GAS, WHEAT, CORN, COTTON, SUGAR, COFFEE, COPPER, ALUMINUM
        
        NOTE: This is a stub structure. Actual implementation will use MCP tools
        or direct API calls based on symbol mapping.
        """
        cache_key = f"commodity_{symbol}"
        cached = self._check_cache(cache_key)
        if cached is not None:
            return cached
        
        self._rate_limit()
        
        # TODO: Implement actual API calls using MCP tools or requests
        # For now, return empty DataFrame structure
        # When implementing, map symbols to appropriate endpoints:
        # - WTI -> WTI endpoint
        # - BRENT -> BRENT endpoint
        # - NATURAL_GAS -> NATURAL_GAS endpoint
        # - WHEAT -> WHEAT endpoint
        # - CORN -> CORN endpoint
        # - COTTON -> COTTON endpoint
        # - SUGAR -> SUGAR endpoint
        # - COFFEE -> COFFEE endpoint
        # - COPPER -> COPPER endpoint
        # - ALUMINUM -> ALUMINUM endpoint
        
        df = pd.DataFrame()  # TODO: implement with actual API calls
        
        if save_path:
            df = self._validate_and_save(df, symbol, 'daily', Path(save_path))
        
        self._save_cache(cache_key, df)
        return df
    
    def fx_daily(self, from_currency, to_currency, outputsize='full', save_path=None):
        """
        Get daily FX rates
        Example: from_currency='USD', to_currency='BRL'
        """
        cache_key = f"fx_{from_currency}{to_currency}"
        cached = self._check_cache(cache_key)
        if cached is not None:
            return cached
        
        self._rate_limit()
        
        # TODO: Implement using mcp_alphavantage_FX_DAILY
        df = pd.DataFrame()
        
        if save_path:
            df = self._validate_and_save(df, f"{from_currency}{to_currency}", 'daily', Path(save_path))
        
        self._save_cache(cache_key, df)
        return df
    
    def news_sentiment(self, topics=None, tickers=None, limit=100, save_path=None):
        """Get news with sentiment scores"""
        cache_key = f"news_{topics}_{tickers}"
        cached = self._check_cache(cache_key)
        if cached is not None:
            return cached
        
        self._rate_limit()
        
        # TODO: Implement using mcp_alphavantage_NEWS_SENTIMENT
        df = pd.DataFrame()
        
        if save_path:
            df = self._validate_and_save(df, 'news', 'daily', Path(save_path))
        
        self._save_cache(cache_key, df)
        return df
    
    def options_chain(self, symbol, require_greeks=True, save_path=None):
        """Get options chain with Greeks"""
        # No cache - options change frequently
        
        self._rate_limit()
        
        # TODO: Implement using mcp_alphavantage_REALTIME_OPTIONS
        df = pd.DataFrame()
        
        if save_path:
            df = self._validate_and_save(df, symbol, 'daily', Path(save_path))
        
        return df
    
    def intraday(self, symbol, interval='5min', outputsize='full', save_path=None):
        """
        Get intraday data (e.g., ES=F). No SPY proxy.
        interval: 1min, 5min, 15min, 30min, 60min
        """
        cache_key = f"intraday_{symbol}_{interval}"
        cached = self._check_cache(cache_key)
        if cached is not None:
            return cached
        
        self._rate_limit()
        
        # TODO: Implement using mcp_alphavantage_TIME_SERIES_INTRADAY
        df = pd.DataFrame()
        
        if save_path:
            df = self._validate_and_save(df, symbol, 'intraday', Path(save_path))
        
        self._save_cache(cache_key, df)
        return df
    
    def technical_indicator(self, function, symbol, interval='daily', **params):
        """
        Get technical indicator (for weekly validation)
        function: RSI, MACD, BBANDS, SMA, EMA, etc.
        
        NOTE: This will be used for weekly validation, not daily collection.
        Daily collection uses batch indicator endpoints.
        """
        self._rate_limit()
        
        # TODO: Implement using appropriate MCP tool based on function parameter
        # Map function names to MCP tools:
        # - RSI -> mcp_alphavantage_RSI
        # - MACD -> mcp_alphavantage_MACD
        # - BBANDS -> mcp_alphavantage_BBANDS
        # etc.
        
        df = pd.DataFrame()
        
        return df




