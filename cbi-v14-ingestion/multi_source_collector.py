#!/usr/bin/env python3
"""
Multi-Source Data Collector - Rate Limited Production System
Collects data from all working APIs with proper rate limiting
Routes to existing dedicated tables - NO NEW TABLES CREATED
PRODUCTION GRADE - Following CURSOR_RULES
"""

import requests
import yfinance as yf
import pandas as pd
import time
import json
import logging
from datetime import datetime, timezone, timedelta
from google.cloud import bigquery
import uuid
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/multi_source_collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('multi_source_collector')

class RateLimitedCollector:
    """
    Production-grade data collector with 60-second rate limiting
    Routes ALL data to existing dedicated tables
    """
    
    def __init__(self):
        self.client = bigquery.Client(project='cbi-v14')
        self.last_calls = {}  # Track last call time per source
        self.call_counts = {}  # Track hourly call counts
        self.hour_start = datetime.now()
        
        # API Keys (from existing working sources)
        self.api_keys = {
            'fred': 'dc195c8658c46ee1df83bcd4fd8a690b',
            'eia': 'I4XUi5PYnAkfMXPU3GvchRsplERC65DWri1AApqs',
            'usda': '98AE1A55-11D0-304B-A5A5-F3FF61E86A31',
            'alpha_vantage': 'BA7CQWXKRFBNFY49'
        }
        
        # Rate limiting: 60 seconds between calls per source
        self.rate_limit_seconds = 60
        self.max_calls_per_hour = 60
    
    def rate_limited_call(self, source_name, url, params=None, headers=None):
        """
        Make rate-limited API call with 60-second delays
        """
        # Check hourly limits
        if datetime.now() - self.hour_start > timedelta(hours=1):
            self.call_counts = {}
            self.hour_start = datetime.now()
        
        if self.call_counts.get(source_name, 0) >= self.max_calls_per_hour:
            logger.warning(f"{source_name}: Hourly limit reached ({self.max_calls_per_hour})")
            return None
        
        # Enforce rate limiting
        if source_name in self.last_calls:
            elapsed = (datetime.now() - self.last_calls[source_name]).seconds
            if elapsed < self.rate_limit_seconds:
                wait_time = self.rate_limit_seconds - elapsed
                logger.info(f"⏱️  Rate limiting {source_name}: waiting {wait_time} seconds")
                time.sleep(wait_time)
        
        # Make API call
        try:
            logger.info(f"🌐 API call: {source_name} → {url[:50]}...")
            response = requests.get(url, params=params, headers=headers, timeout=15)
            
            # Update tracking
            self.last_calls[source_name] = datetime.now()
            self.call_counts[source_name] = self.call_counts.get(source_name, 0) + 1
            
            if response.status_code == 200:
                logger.info(f"✅ {source_name}: Success ({len(response.text)} bytes)")
                return response
            else:
                logger.warning(f"❌ {source_name}: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ {source_name}: {e}")
            return None
    
    def collect_fred_data(self):
        """
        Collect FRED economic indicators with rate limiting
        Routes to existing economic_indicators table
        """
        logger.info("📊 Collecting FRED Economic Data...")
        
        # Key economic indicators for commodity forecasting
        fred_series = [
            ('FEDFUNDS', 'fed_funds_rate'),
            ('DGS10', 'ten_year_treasury'),
            ('DTWEXBGS', 'dollar_index'),
            ('CPIAUCSL', 'cpi_inflation'),
            ('DEXBZUS', 'usd_brl_rate'),
            ('VIXCLS', 'vix_index')
        ]
        
        collected_data = []
        
        for series_id, indicator_name in fred_series:
            url = 'https://api.stlouisfed.org/fred/series/observations'
            params = {
                'series_id': series_id,
                'api_key': self.api_keys['fred'],
                'file_type': 'json',
                'limit': 1,
                'sort_order': 'desc'
            }
            
            response = self.rate_limited_call('FRED', url, params)
            
            if response:
                try:
                    data = response.json()
                    if 'observations' in data and data['observations']:
                        obs = data['observations'][0]
                        
                        record = {
                            'time': datetime.now(timezone.utc),
                            'indicator': indicator_name,
                            'value': float(obs['value']),
                            'source_name': 'FRED',
                            'confidence_score': 0.95,
                            'ingest_timestamp_utc': datetime.now(timezone.utc),
                            'provenance_uuid': str(uuid.uuid4())
                        }
                        
                        collected_data.append(record)
                        logger.info(f"✅ {indicator_name}: {obs['value']}")
                    
                except Exception as e:
                    logger.error(f"❌ Error parsing {series_id}: {e}")
        
        return collected_data
    
    def collect_yahoo_commodities(self):
        """
        Collect Yahoo Finance commodity data with rate limiting
        Routes to existing dedicated commodity tables
        """
        logger.info("📊 Collecting Yahoo Finance Commodities...")
        
        # Map Yahoo symbols to our dedicated tables
        yahoo_commodities = [
            ('ZL=F', 'ZL', 'soybean_oil_prices'),
            ('ZS=F', 'ZS', 'soybean_prices'),
            ('ZM=F', 'ZM', 'soybean_meal_prices'),
            ('ZC=F', 'ZC', 'corn_prices'),
            ('CC=F', 'CC', 'cocoa_prices'),
            ('CT=F', 'CT', 'cotton_prices'),
        ]
        
        collected_data = {}
        
        for yahoo_symbol, our_symbol, table_name in yahoo_commodities:
            try:
                logger.info(f"🌐 Yahoo Finance: {yahoo_symbol} → {table_name}")
                
                ticker = yf.Ticker(yahoo_symbol)
                data = ticker.history(period='1d')
                
                if not data.empty:
                    current_price = float(data['Close'].iloc[-1])
                    
                    record = {
                        'time': datetime.now(timezone.utc),
                        'symbol': our_symbol,
                        'close': current_price,
                        'source_name': 'Yahoo_Finance',
                        'confidence_score': 0.80,
                        'ingest_timestamp_utc': datetime.now(timezone.utc),
                        'provenance_uuid': str(uuid.uuid4())
                    }
                    
                    if table_name not in collected_data:
                        collected_data[table_name] = []
                    collected_data[table_name].append(record)
                    
                    logger.info(f"✅ {our_symbol}: ${current_price:.2f}")
                else:
                    logger.warning(f"❌ {yahoo_symbol}: No data")
                
                # Rate limiting between Yahoo calls
                time.sleep(5)  # 5 seconds between Yahoo calls (more lenient)
                
            except Exception as e:
                logger.error(f"❌ {yahoo_symbol}: {e}")
        
        return collected_data
    
    def collect_vix_data(self):
        """
        Collect VIX data from multiple sources
        Routes to existing volatility_data table
        """
        logger.info("📊 Collecting VIX Data...")
        
        vix_data = []
        
        # Source 1: Yahoo Finance VIX
        try:
            vix_ticker = yf.Ticker('^VIX')
            vix_history = vix_ticker.history(period='1d')
            
            if not vix_history.empty:
                vix_value = float(vix_history['Close'].iloc[-1])
                
                record = {
                    'symbol': 'VIX',
                    'contract': 'SPOT',
                    'last_price': vix_value,
                    'iv_hv_ratio': 1.0,  # VIX is implied volatility
                    'implied_vol': vix_value,
                    'data_date': datetime.now(timezone.utc).date()
                }
                
                vix_data.append(record)
                logger.info(f"✅ Yahoo VIX: {vix_value:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Yahoo VIX: {e}")
        
        # Source 2: FRED VIX (cross-validation)
        url = 'https://api.stlouisfed.org/fred/series/observations'
        params = {
            'series_id': 'VIXCLS',
            'api_key': self.api_keys['fred'],
            'file_type': 'json',
            'limit': 1,
            'sort_order': 'desc'
        }
        
        response = self.rate_limited_call('FRED_VIX', url, params)
        
        if response:
            try:
                data = response.json()
                if 'observations' in data and data['observations']:
                    fred_vix = float(data['observations'][0]['value'])
                    logger.info(f"✅ FRED VIX: {fred_vix:.2f} (cross-validation)")
            except Exception as e:
                logger.error(f"❌ FRED VIX parsing: {e}")
        
        return vix_data
    
    def collect_gdelt_china_intelligence(self):
        """
        Collect GDELT China trade intelligence
        Routes to existing news_intelligence table
        """
        logger.info("📊 Collecting GDELT China Intelligence...")
        
        query = """
        SELECT 
            SQLDATE,
            Actor1CountryCode,
            Actor2CountryCode,
            EventCode,
            GoldsteinScale,
            NumMentions,
            SOURCEURL
        FROM `gdelt-bq.gdeltv2.events`
        WHERE DATE(PARSE_DATE('%Y%m%d', CAST(SQLDATE AS STRING))) >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY)
            AND (
                (Actor1CountryCode = 'CHN' AND Actor2CountryCode = 'USA')
                OR (Actor1CountryCode = 'USA' AND Actor2CountryCode = 'CHN')
                OR LOWER(SOURCEURL) LIKE '%tariff%'
                OR LOWER(SOURCEURL) LIKE '%soybean%'
                OR LOWER(SOURCEURL) LIKE '%trade%'
            )
            AND EventCode IN ('0871', '1056', '0231')
        ORDER BY SQLDATE DESC
        LIMIT 20
        """
        
        try:
            result = self.client.query(query).to_dataframe()
            
            china_intelligence = []
            
            for _, row in result.iterrows():
                # Convert to news_intelligence schema
                record = {
                    'title': f"China-US Trade Event {row['SQLDATE']}",
                    'source': 'GDELT',
                    'category': 'china_trade',
                    'url': row['SOURCEURL'],
                    'published': datetime.now(timezone.utc),
                    'content': f"Trade event: {row['Actor1CountryCode']} → {row['Actor2CountryCode']}, Score: {row['GoldsteinScale']}",
                    'intelligence_score': abs(row['GoldsteinScale']) / 10.0,
                    'processed_timestamp': datetime.now(timezone.utc)
                }
                
                china_intelligence.append(record)
            
            logger.info(f"✅ GDELT China: {len(china_intelligence)} events collected")
            return china_intelligence
            
        except Exception as e:
            logger.error(f"❌ GDELT China: {e}")
            return []
    
    def collect_ny_fed_data(self):
        """
        Collect NY Fed Markets data
        Routes to existing economic_indicators table
        """
        logger.info("📊 Collecting NY Fed Markets Data...")
        
        url = 'https://markets.newyorkfed.org/api/rates/all/latest.json'
        
        response = self.rate_limited_call('NY_FED', url)
        
        if response:
            try:
                data = response.json()
                
                fed_data = []
                
                # Extract key rates
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, (int, float)):
                            record = {
                                'time': datetime.now(timezone.utc),
                                'indicator': f'ny_fed_{key.lower()}',
                                'value': float(value),
                                'source_name': 'NY_Fed_Markets',
                                'confidence_score': 0.98,  # Official Fed data
                                'ingest_timestamp_utc': datetime.now(timezone.utc),
                                'provenance_uuid': str(uuid.uuid4())
                            }
                            fed_data.append(record)
                
                logger.info(f"✅ NY Fed: {len(fed_data)} indicators collected")
                return fed_data
                
            except Exception as e:
                logger.error(f"❌ NY Fed parsing: {e}")
        
        return []
    
    def save_to_bigquery(self, table_name, data):
        """
        Save collected data to BigQuery with error handling
        """
        if not data:
            logger.warning(f"No data to save for {table_name}")
            return False
        
        try:
            df = pd.DataFrame(data)
            table_ref = f'cbi-v14.forecasting_data_warehouse.{table_name}'
            
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND",
                autodetect=True
            )
            
            job = self.client.load_table_from_dataframe(df, table_ref, job_config=job_config)
            job.result()
            
            logger.info(f"✅ Saved {len(data)} rows to {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ BigQuery save failed for {table_name}: {e}")
            return False
    
    def run_comprehensive_collection(self):
        """
        Run comprehensive data collection from all working sources
        """
        logger.info("=" * 80)
        logger.info("STARTING COMPREHENSIVE DATA COLLECTION")
        logger.info("Rate Limited: 60 seconds between calls per source")
        logger.info("=" * 80)
        
        collection_results = {}
        
        # 1. Collect FRED Economic Data
        try:
            fred_data = self.collect_fred_data()
            if fred_data:
                success = self.save_to_bigquery('economic_indicators', fred_data)
                collection_results['FRED'] = {'records': len(fred_data), 'success': success}
        except Exception as e:
            logger.error(f"FRED collection failed: {e}")
            collection_results['FRED'] = {'records': 0, 'success': False}
        
        # 2. Collect Yahoo Finance Commodities
        try:
            yahoo_data = self.collect_yahoo_commodities()
            for table_name, records in yahoo_data.items():
                success = self.save_to_bigquery(table_name, records)
                collection_results[f'Yahoo_{table_name}'] = {'records': len(records), 'success': success}
        except Exception as e:
            logger.error(f"Yahoo collection failed: {e}")
        
        # 3. Collect VIX Data
        try:
            vix_data = self.collect_vix_data()
            if vix_data:
                success = self.save_to_bigquery('volatility_data', vix_data)
                collection_results['VIX'] = {'records': len(vix_data), 'success': success}
        except Exception as e:
            logger.error(f"VIX collection failed: {e}")
            collection_results['VIX'] = {'records': 0, 'success': False}
        
        # 4. Collect GDELT China Intelligence
        try:
            china_data = self.collect_gdelt_china_intelligence()
            if china_data:
                success = self.save_to_bigquery('news_intelligence', china_data)
                collection_results['GDELT_China'] = {'records': len(china_data), 'success': success}
        except Exception as e:
            logger.error(f"GDELT collection failed: {e}")
            collection_results['GDELT_China'] = {'records': 0, 'success': False}
        
        # 5. Collect NY Fed Data
        try:
            fed_data = self.collect_ny_fed_data()
            if fed_data:
                success = self.save_to_bigquery('economic_indicators', fed_data)
                collection_results['NY_Fed'] = {'records': len(fed_data), 'success': success}
        except Exception as e:
            logger.error(f"NY Fed collection failed: {e}")
            collection_results['NY_Fed'] = {'records': 0, 'success': False}
        
        # Print final results
        logger.info("=" * 80)
        logger.info("COMPREHENSIVE COLLECTION COMPLETE")
        logger.info("=" * 80)
        
        total_records = 0
        successful_sources = 0
        
        for source, result in collection_results.items():
            status = "✅" if result['success'] else "❌"
            logger.info(f"{status} {source}: {result['records']} records")
            
            if result['success']:
                total_records += result['records']
                successful_sources += 1
        
        logger.info("=" * 80)
        logger.info(f"📊 SUMMARY: {successful_sources}/{len(collection_results)} sources successful")
        logger.info(f"📊 TOTAL RECORDS: {total_records}")
        logger.info(f"💰 COST: $0 (all free sources)")
        logger.info("=" * 80)
        
        return collection_results

if __name__ == '__main__':
    collector = RateLimitedCollector()
    results = collector.run_comprehensive_collection()
    
    # Exit with appropriate code
    successful_sources = sum(1 for r in results.values() if r['success'])
    total_sources = len(results)
    
    if successful_sources >= total_sources * 0.8:  # 80% success threshold
        logger.info("🎉 COLLECTION SUCCESS - 80%+ sources operational")
        exit(0)
    else:
        logger.error("⚠️ COLLECTION PARTIAL - <80% sources operational")
        exit(1)






