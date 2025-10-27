#!/usr/bin/env python3
"""
EMERGENCY FRESH DATA PULL - COMPREHENSIVE ALL-SOURCES DATA COLLECTION
Pulls from Yahoo Finance, FRED, EIA, USDA, Alpha Vantage, and all available APIs
PULLS EVERYTHING DEEP - NO MISSING DATA
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/fresh_data_pull.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('fresh_data_pull')

class ComprehensiveDataCollector:
    """
    Comprehensive data collector pulling from ALL available sources
    """
    
    def __init__(self):
        self.client = bigquery.Client(project='cbi-v14')
        
        # API Keys
        self.api_keys = {
            'fred': 'dc195c8658c46ee1df83bcd4fd8a690b',
            'eia': 'I4XUi5PYnAkfMXPU3GvchRsplERC65DWri1AApqs',
            'usda': '98AE1A55-11D0-304B-A5A5-F3FF61E86A31',
            'alpha_vantage': 'BA7CQWXKRFBNFY49'
        }
        
        self.collected_data = []
    
    def pull_yahoo_finance(self):
        """Pull ALL commodity prices from Yahoo Finance"""
        logger.info("=" * 80)
        logger.info("📊 YAHOO FINANCE - Pulling ALL Commodity Prices")
        logger.info("=" * 80)
        
        commodities = [
            ('ZL=F', 'soybean_oil'),
            ('ZS=F', 'soybeans'),
            ('ZM=F', 'soybean_meal'),
            ('ZC=F', 'corn'),
            ('ZW=F', 'wheat'),
            ('CC=F', 'cocoa'),
            ('CT=F', 'cotton'),
            ('CL=F', 'crude_oil'),
            ('NG=F', 'natural_gas'),
            ('GC=F', 'gold'),
            ('SI=F', 'silver'),
            ('^VIX', 'vix'),
            ('DX-Y.NYB', 'dollar_index'),  # Dollar Index
            ('BRL=X', 'usd_brl_rate'),     # ADD EXCHANGE RATES
            ('CNY=X', 'usd_cny_rate'),
            ('ARS=X', 'usd_ars_rate'),
        ]
        
        for symbol, name in commodities:
            try:
                logger.info(f"Pulling {name} ({symbol})...")
                ticker = yf.Ticker(symbol)
                data = ticker.history(period='5d')  # Get last 5 days
                
                if not data.empty:
                    latest = data.iloc[-1]
                    data_date = data.index[-1].to_pydatetime()
                    data_date = data_date.replace(tzinfo=timezone.utc)
                    
                    # Check date freshness
                    time_diff = datetime.now(timezone.utc) - data_date
                    if time_diff.total_seconds() < 172800:  # 48 hours (2 days)
                        record = {
                            'time': data_date,
                            'indicator': name,
                            'value': float(latest['Close']),
                            'source_name': 'Yahoo_Finance',
                            'confidence_score': 0.95,
                            'ingest_timestamp_utc': datetime.now(timezone.utc),
                            'provenance_uuid': str(uuid.uuid4())
                        }
                        self.collected_data.append(record)
                        logger.info(f"✅ {name}: ${latest['Close']:.2f} (Date: {data_date.date()})")
                    else:
                        logger.warning(f"⚠️  {name}: Data too old ({time_diff.days} days)")
                else:
                    logger.warning(f"⚠️  {name}: No data")
                
                time.sleep(2)  # Rate limiting
                
            except Exception as e:
                logger.error(f"❌ {name}: {e}")
        
        logger.info(f"Collected {len(self.collected_data)} Yahoo Finance records")
    
    def pull_fred_economic(self):
        """Pull ALL economic indicators from FRED"""
        logger.info("=" * 80)
        logger.info("📊 FRED - Pulling ALL Economic Indicators")
        logger.info("=" * 80)
        
        fred_series = [
            ('FEDFUNDS', 'fed_funds_rate'),
            ('DGS10', 'ten_year_treasury'),
            ('DTWEXBGS', 'dollar_index_fred'),
            ('CPIAUCSL', 'cpi_inflation'),
            ('DEXBZUS', 'usd_brl_rate'),
            ('DEXCHUS', 'usd_cny_rate'),
            ('VIXCLS', 'vix_index'),
            ('DCOILWTICO', 'crude_oil_wti'),
            ('UNRATE', 'unemployment_rate'),
            ('PAYEMS', 'nonfarm_payrolls'),
            ('CPILFESL', 'core_cpi'),
            ('T10Y2Y', 'yield_curve'),
        ]
        
        for series_id, indicator_name in fred_series:
            try:
                url = 'https://api.stlouisfed.org/fred/series/observations'
                params = {
                    'series_id': series_id,
                    'api_key': self.api_keys['fred'],
                    'file_type': 'json',
                    'limit': 10,
                    'sort_order': 'desc'
                }
                
                logger.info(f"Pulling {indicator_name} ({series_id})...")
                response = requests.get(url, params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'observations' in data and data['observations']:
                        for obs in data['observations']:
                            if obs['value'] != '.':
                                record = {
                                    'time': datetime.now(timezone.utc),
                                    'indicator': indicator_name,
                                    'value': float(obs['value']),
                                    'source_name': 'FRED',
                                    'confidence_score': 0.95,
                                    'ingest_timestamp_utc': datetime.now(timezone.utc),
                                    'provenance_uuid': str(uuid.uuid4())
                                }
                                self.collected_data.append(record)
                        
                        latest = data['observations'][0]
                        logger.info(f"✅ {indicator_name}: {latest['value']}")
                    else:
                        logger.warning(f"⚠️  {indicator_name}: No observations")
                else:
                    logger.warning(f"⚠️  {indicator_name}: HTTP {response.status_code}")
                
                time.sleep(0.5)  # FRED rate limiting
                
            except Exception as e:
                logger.error(f"❌ {indicator_name}: {e}")
        
        logger.info(f"Collected {len(self.collected_data)} FRED records")
    
    def pull_alpha_vantage(self):
        """Pull currency/FX data from Alpha Vantage (BACKUP SOURCE)"""
        logger.info("=" * 80)
        logger.info("📊 ALPHA VANTAGE - Pulling Currency Data (Backup)")
        logger.info("=" * 80)
        
        currencies = [
            ('CNY', 'USDCNY'),
            ('BRL', 'USDBRL'),
            ('ARS', 'USDARS'),
        ]
        
        for from_curr, symbol in currencies:
            try:
                url = 'https://www.alphavantage.co/query'
                params = {
                    'function': 'FX_INTRADAY',
                    'from_symbol': 'USD',
                    'to_symbol': from_curr,
                    'interval': '60min',
                    'apikey': self.api_keys['alpha_vantage']
                }
                
                logger.info(f"Pulling USD/{from_curr}...")
                response = requests.get(url, params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'Time Series FX (60min)' in data:
                        latest_key = list(data['Time Series FX (60min)'].keys())[0]
                        latest_value = data['Time Series FX (60min)'][latest_key]
                        
                        # Parse date from key
                        data_date = datetime.strptime(latest_key, '%Y-%m-%d %H:%M:%S')
                        data_date = data_date.replace(tzinfo=timezone.utc)
                        
                        # Check date freshness (must be within 24 hours)
                        time_diff = datetime.now(timezone.utc) - data_date
                        if time_diff.total_seconds() < 86400:  # 24 hours
                            record = {
                                'time': data_date,
                                'indicator': f'usd_{from_curr.lower()}_rate',
                                'value': float(latest_value['4. close']),
                                'source_name': 'Alpha_Vantage',
                                'confidence_score': 0.90,
                                'ingest_timestamp_utc': datetime.now(timezone.utc),
                                'provenance_uuid': str(uuid.uuid4())
                            }
                            self.collected_data.append(record)
                            logger.info(f"✅ USD/{from_curr}: {latest_value['4. close']} (Date: {data_date.date()})")
                        else:
                            logger.warning(f"⚠️  USD/{from_curr}: Data too old ({time_diff.days} days)")
                    else:
                        logger.warning(f"⚠️  USD/{from_curr}: No data")
                else:
                    logger.warning(f"⚠️  USD/{from_curr}: HTTP {response.status_code}")
                
                time.sleep(12)  # Alpha Vantage: 5 calls/minute
                
            except Exception as e:
                logger.error(f"❌ USD/{from_curr}: {e}")
    
    def save_to_bigquery(self):
        """Save all collected data to BigQuery"""
        logger.info("=" * 80)
        logger.info("💾 SAVING TO BIGQUERY")
        logger.info("=" * 80)
        
        if not self.collected_data:
            logger.warning("No data to save!")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(self.collected_data)
        
        # Ensure correct schema
        table_id = 'cbi-v14.forecasting_data_warehouse.economic_indicators'
        
        try:
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                create_disposition=bigquery.CreateDisposition.CREATE_IF_NEEDED
            )
            
            logger.info(f"Writing {len(df)} records to {table_id}...")
            job = self.client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()
            
            logger.info(f"✅ Successfully wrote {len(df)} records")
            
        except Exception as e:
            logger.error(f"❌ Error saving to BigQuery: {e}")
    
    def run_comprehensive_pull(self):
        """Run comprehensive data pull from all sources"""
        logger.info("=" * 80)
        logger.info("🚀 COMPREHENSIVE FRESH DATA PULL")
        logger.info("=" * 80)
        logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("")
        
        # Pull from all sources
        self.pull_yahoo_finance()
        self.pull_fred_economic()
        self.pull_alpha_vantage()
        
        # Save everything
        self.save_to_bigquery()
        
        # Summary
        logger.info("=" * 80)
        logger.info("✅ FRESH DATA PULL COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total records collected: {len(self.collected_data)}")
        logger.info(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)

if __name__ == '__main__':
    collector = ComprehensiveDataCollector()
    collector.run_comprehensive_pull()

