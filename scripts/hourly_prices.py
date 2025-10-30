#!/usr/bin/env python3
"""
PHASE 3: Hourly Price Updates
Pulls from Yahoo Finance + Alpha Vantage every hour
"""

import yfinance as yf
import requests
from google.cloud import bigquery
from datetime import datetime
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/zincdigital/CBI-V14/logs/prices.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

ALPHA_VANTAGE_KEY = "BA7CQWXKRFBNFY49"
PROJECT_ID = "cbi-v14"

SYMBOLS = {
    'yahoo': ['ZL=F', 'ZS=F', 'ZC=F', 'ZM=F'],  # Soy oil, Soybeans, Corn, Soy meal
    'alpha_vantage': ['^VIX']  # VIX volatility index
}

def get_yahoo_prices():
    """Get latest prices from Yahoo Finance"""
    prices = []
    
    for symbol in SYMBOLS['yahoo']:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='1d', interval='1h')
            
            if not hist.empty:
                latest = hist.iloc[-1]
                prices.append({
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'price': float(latest['Close']),
                    'volume': int(latest['Volume']),
                    'source': 'yahoo_finance',
                    'ingest_timestamp': datetime.now()
                })
                logger.info(f"✅ {symbol}: ${latest['Close']:.2f}")
            
            time.sleep(0.5)  # Rate limit protection
            
        except Exception as e:
            logger.error(f"❌ Failed to get {symbol}: {e}")
    
    return prices


def get_alpha_vantage_vix():
    """Get VIX from Alpha Vantage"""
    try:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=VIX&apikey={ALPHA_VANTAGE_KEY}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if 'Global Quote' in data:
            price = float(data['Global Quote']['05. price'])
            return {
                'timestamp': datetime.now(),
                'symbol': 'VIX',
                'price': price,
                'volume': 0,
                'source': 'alpha_vantage',
                'ingest_timestamp': datetime.now()
            }
        else:
            logger.warning(f"Alpha Vantage response: {data}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Failed to get VIX: {e}")
        return None


def save_to_bigquery(prices):
    """Save prices to BigQuery"""
    if not prices:
        logger.warning("No prices to save")
        return False
    
    try:
        client = bigquery.Client(project=PROJECT_ID)
        table_id = f"{PROJECT_ID}.market_data.hourly_prices"
        
        import pandas as pd
        df = pd.DataFrame(prices)
        
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        
        logger.info(f"✅ Saved {len(prices)} prices to {table_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ BigQuery save failed: {e}")
        return False


def main():
    """Main execution"""
    logger.info("="*80)
    logger.info("HOURLY PRICE UPDATE")
    logger.info("="*80)
    
    all_prices = []
    
    # Get Yahoo prices
    yahoo_prices = get_yahoo_prices()
    all_prices.extend(yahoo_prices)
    
    # Get VIX
    vix_price = get_alpha_vantage_vix()
    if vix_price:
        all_prices.append(vix_price)
    
    # Save to BigQuery
    success = save_to_bigquery(all_prices)
    
    logger.info("="*80)
    logger.info(f"✅ Hourly update complete: {len(all_prices)} prices")
    logger.info("="*80)
    
    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

