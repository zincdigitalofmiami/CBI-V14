#!/usr/bin/env python3
"""
FOUR-DAILY PRICE FETCHER
Fetches critical commodity prices 4 times per day
Run at: 8:00 AM, 12:00 PM, 4:00 PM, 8:00 PM ET
"""

import yfinance as yf
import requests
from datetime import datetime
from google.cloud import bigquery
import pandas as pd
import logging
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/daily_price_fetcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

# CRITICAL COMPONENTS - Pull 4x daily
CRITICAL_SYMBOLS = {
    # Soybean Complex
    'ZL=F': 'soybean_oil',
    'ZS=F': 'soybean', 
    'ZM=F': 'soybean_meal',
    
    # Energy Complex
    'CL=F': 'crude_oil_wti',
    'BZ=F': 'crude_oil_brent',
    'NG=F': 'natural_gas',
    
    # Palm Oil (via Malaysia exchange - approximate)
    'FCPO': 'palm_oil',
    
    # Key Grains
    'ZC=F': 'corn',
    'ZW=F': 'wheat',
    
    # Financial
    '^VIX': 'vix',
    'DX-Y.NYB': 'dollar_index',
    '^TNX': 'treasury_10y',
    '^FVX': 'treasury_5y',
    '^TYX': 'treasury_30y',
    
    # Stock Indices
    '^GSPC': 'sp500',
    '^DJI': 'dow_jones',
    
    # Metals
    'GC=F': 'gold',
    'SI=F': 'silver',
}

# API Keys
API_KEYS = {
    'ALPHA_VANTAGE': 'BA7CQWXKRFBNFY49',
    'FRED': 'dc195c8658c46ee1df83bcd4fd8a690b',
}

def fetch_yahoo_prices(symbols):
    """Fetch prices from Yahoo Finance"""
    prices = {}
    
    for symbol, name in symbols.items():
        try:
            logger.info(f"Fetching {name} ({symbol})...")
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1d', interval='1m')
            
            if not data.empty:
                # Get latest price
                latest = data.iloc[-1]
                prices[name] = {
                    'symbol': symbol,
                    'price': float(latest['Close']),
                    'open': float(latest['Open']),
                    'high': float(latest['High']),
                    'low': float(latest['Low']),
                    'volume': int(latest['Volume']),
                    'timestamp': latest.name,
                    'source': 'yahoo'
                }
                logger.info(f"  ✓ {name}: ${prices[name]['price']:.2f}")
            else:
                logger.warning(f"  ✗ No data for {symbol}")
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"  ✗ Error fetching {symbol}: {str(e)[:100]}")
            time.sleep(2)
    
    return prices

def fetch_fred_data():
    """Fetch economic data from FRED"""
    fred_data = {}
    
    # Federal Funds Rate
    try:
        url = 'https://api.stlouisfed.org/fred/series/observations'
        params = {
            'series_id': 'DFF',
            'api_key': API_KEYS['FRED'],
            'file_type': 'json',
            'limit': 1,
            'sort_order': 'desc'
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'observations' in data and len(data['observations']) > 0:
                fred_data['fed_funds_rate'] = float(data['observations'][0]['value'])
                logger.info(f"  ✓ Fed Funds Rate: {fred_data['fed_funds_rate']:.2f}%")
    except Exception as e:
        logger.error(f"  ✗ FRED error: {str(e)[:50]}")
    
    return fred_data

def save_to_bigquery(prices_dict, fred_data):
    """Save prices to BigQuery"""
    try:
        # Prepare data
        records = []
        fetch_time = datetime.now()
        
        for name, data in prices_dict.items():
            record = {
                'date': fetch_time.date(),
                'timestamp': fetch_time,
                'instrument': name,
                'symbol': data['symbol'],
                'price': data['price'],
                'open': data['open'],
                'high': data['high'],
                'low': data['low'],
                'volume': data['volume'],
                'source': data['source'],
                'fetch_time': fetch_time.strftime('%H:%M:%S')
            }
            records.append(record)
        
        # Add FRED data
        for name, value in fred_data.items():
            record = {
                'date': fetch_time.date(),
                'timestamp': fetch_time,
                'instrument': name,
                'symbol': 'FRED',
                'price': value,
                'open': value,
                'high': value,
                'low': value,
                'volume': 0,
                'source': 'fred',
                'fetch_time': fetch_time.strftime('%H:%M:%S')
            }
            records.append(record)
        
        df = pd.DataFrame(records)
        
        # Save to BigQuery
        table_id = "cbi-v14.forecasting_data_warehouse.realtime_prices"
        
        job = client.load_table_from_dataframe(
            df,
            table_id,
            job_config=bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND",
                schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION]
            )
        )
        job.result()
        
        logger.info(f"✓ Saved {len(records)} price records to BigQuery")
        
        return True
        
    except Exception as e:
        logger.error(f"BigQuery save failed: {str(e)[:200]}")
        # Save to CSV backup
        try:
            df.to_csv(f'realtime_prices_backup_{datetime.now().strftime("%Y%m%d_%H%M")}.csv', index=False)
            logger.info("Saved to local backup CSV")
        except:
            pass
        return False

def main():
    """Main fetching function"""
    logger.info("="*80)
    logger.info("FOUR-DAILY PRICE FETCH")
    logger.info(f"Fetch Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80)
    
    # Fetch Yahoo Finance prices
    logger.info("\nFetching Yahoo Finance data...")
    prices = fetch_yahoo_prices(CRITICAL_SYMBOLS)
    
    # Fetch FRED data
    logger.info("\nFetching FRED economic data...")
    fred_data = fetch_fred_data()
    
    # Combine and save
    logger.info("\nSaving to BigQuery...")
    success = save_to_bigquery(prices, fred_data)
    
    if success:
        logger.info("\n" + "="*80)
        logger.info("PRICE FETCH COMPLETE")
        logger.info("="*80)
    else:
        logger.error("\nPrice fetch completed with errors - check logs")

if __name__ == "__main__":
    main()

