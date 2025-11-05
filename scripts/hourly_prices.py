#!/usr/bin/env python3
"""
PHASE 3: Hourly Price Updates
Pulls from Yahoo Finance + Alpha Vantage every hour
"""

import yfinance as yf
import requests
import pandas as pd
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
    'yahoo': [
        # Commodity Futures
        'ZL=F',   # Soybean Oil Futures
        'ZS=F',   # Soybean Futures
        'ZC=F',   # Corn Futures
        'ZM=F',   # Soybean Meal Futures
        'ZW=F',   # Wheat Futures
        'CL=F',   # Crude Oil Futures
        'GC=F',   # Gold Futures

        # Currency Indices (separate from commodities!)
        'DX-Y.NYB',  # US Dollar Index (DXY)

        # Volatility Index
        '^VIX'    # CBOE Volatility Index (not a price!)
    ],
    'alpha_vantage': []  # Primary collection now from Yahoo
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
                # Proper asset classification - NO mixing commodities with currencies!
                if symbol == '^VIX':
                    asset_type = 'volatility_index'
                    volume = 0  # VIX has no trading volume
                elif symbol == 'DX-Y.NYB':
                    asset_type = 'currency_index'
                    volume = 0  # Currency indices have no volume
                elif symbol.endswith('=F'):
                    asset_type = 'commodity_future'
                    volume = int(latest['Volume']) if pd.notna(latest['Volume']) else 0
                else:
                    asset_type = 'unknown'
                    volume = int(latest['Volume']) if pd.notna(latest['Volume']) else 0

                prices.append({
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'asset_type': asset_type,
                    'price': float(latest['Close']),
                    'volume': volume,
                    'source': 'yahoo_finance',
                    'ingest_timestamp': datetime.now()
                })
                logger.info(f"✅ {symbol}: ${latest['Close']:.2f}")
            
            time.sleep(0.5)  # Rate limit protection
            
        except Exception as e:
            logger.error(f"❌ Failed to get {symbol}: {e}")
    
    return prices


def get_alpha_vantage_vix():
    """Get VIX from Alpha Vantage with fallback to Yahoo Finance"""
    try:
        # Try Alpha Vantage first
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=VIX&apikey={ALPHA_VANTAGE_KEY}"
        response = requests.get(url, timeout=10)
        data = response.json()

        logger.info(f"Alpha Vantage response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")

        if 'Global Quote' in data and data['Global Quote']:
            quote_data = data['Global Quote']
            logger.info(f"Global Quote keys: {list(quote_data.keys())}")

            # Try different possible price keys
            price_keys = ['05. price', 'price', 'latestPrice', 'lastPrice']
            price = None

            for key in price_keys:
                if key in quote_data and quote_data[key]:
                    try:
                        price = float(quote_data[key])
                        logger.info(f"✅ Found VIX price using key '{key}': ${price}")
                        break
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Failed to parse price from key '{key}': {quote_data[key]}")
                        continue

            if price is not None:
                return {
                    'timestamp': datetime.now(),
                    'symbol': 'VIX',
                    'price': price,
                    'volume': 0,
                    'source': 'alpha_vantage',
                    'ingest_timestamp': datetime.now()
                }
            else:
                logger.warning(f"No valid price found in Alpha Vantage response: {quote_data}")
        else:
            logger.warning(f"Invalid Alpha Vantage response structure: {data}")

    except Exception as e:
        logger.error(f"❌ Alpha Vantage failed: {e}")

    # Fallback to Yahoo Finance
    logger.info("🔄 Falling back to Yahoo Finance for VIX...")
    try:
        import yfinance as yf

        vix_ticker = yf.Ticker("^VIX")
        hist = vix_ticker.history(period='1d', interval='1m')

        if not hist.empty:
            latest_price = hist['Close'].iloc[-1]
            logger.info(f"✅ Yahoo Finance VIX: ${latest_price:.2f}")

            return {
                'timestamp': datetime.now(),
                'symbol': 'VIX',
                'price': float(latest_price),
                'volume': 0,
                'source': 'yahoo_finance_fallback',
                'ingest_timestamp': datetime.now()
            }
        else:
            logger.error("❌ Yahoo Finance returned empty VIX data")

    except Exception as e:
        logger.error(f"❌ Yahoo Finance fallback failed: {e}")

    return None


def save_to_bigquery(prices):
    """Save prices to BigQuery"""
    if not prices:
        logger.warning("No prices to save")
        return False

    try:
        client = bigquery.Client(project=PROJECT_ID)
        table_id = f"{PROJECT_ID}.forecasting_data_warehouse.hourly_prices"

        df = pd.DataFrame(prices)

        # Ensure proper asset classification for all symbols
        def classify_asset(symbol):
            if symbol == '^VIX' or symbol == 'VIX':
                return 'volatility_index'
            elif symbol == 'DX-Y.NYB':
                return 'currency_index'
            elif symbol.endswith('=F'):
                return 'commodity_future'
            else:
                return 'unknown'

        df['asset_type'] = df['symbol'].apply(classify_asset)

        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()

        # Log breakdown by asset type
        asset_breakdown = df['asset_type'].value_counts()
        logger.info(f"✅ Saved {len(prices)} assets to {table_id}:")
        for asset_type, count in asset_breakdown.items():
            logger.info(f"   • {count} {asset_type} records")

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

    # Get Yahoo prices (including VIX)
    yahoo_prices = get_yahoo_prices()
    all_prices.extend(yahoo_prices)

    # Check if VIX was successfully collected from Yahoo
    vix_from_yahoo = any(p['symbol'] == '^VIX' and p['source'] == 'yahoo_finance' for p in all_prices)
    vix_from_fallback = any(p['symbol'] == 'VIX' and p['source'] == 'yahoo_finance_fallback' for p in all_prices)

    if not (vix_from_yahoo or vix_from_fallback):
        logger.info("🔄 Primary VIX collection failed, trying final fallback...")
        vix_price = get_alpha_vantage_vix()
        if vix_price:
            all_prices.append(vix_price)
            logger.info("✅ VIX collected via final Alpha Vantage fallback")
        else:
            logger.warning("❌ VIX collection failed from all sources")
    else:
        logger.info("✅ VIX successfully collected from Yahoo Finance")

    # Save to BigQuery
    success = save_to_bigquery(all_prices)

    logger.info("="*80)
    logger.info(f"✅ Hourly update complete: {len(all_prices)} prices")
    logger.info("="*80)

    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

