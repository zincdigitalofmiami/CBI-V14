#!/usr/bin/env python3
"""
TradingEconomics Comprehensive Web Scraper
Hourly scraping schedule with ultra-conservative rate limiting (1 req/hour per URL)
Routes ALL data to EXISTING tables - NO NEW TABLES CREATED

Schedule: Runs every hour via cron
Rate limit: 4-6 second delay between requests
Total: ~50 URLs/hour (well within politeness threshold)
Cost: $0/month
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import json
import os
import hashlib
import uuid
from datetime import datetime, timezone
from functools import lru_cache
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/tradingeconomics_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('te_scraper')

# Constants
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

REQUEST_DELAY_MIN = 4  # seconds
REQUEST_DELAY_MAX = 6  # seconds
CACHE_DIR = '/tmp/te_scraper_cache'
RAW_HTML_DIR = '/tmp/te_scraper_raw'

# Create cache directories
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(RAW_HTML_DIR, exist_ok=True)

# Scraping schedule: (minute_offset, table_name, url)
SCRAPE_SCHEDULE = {
    # Minute 0: FX rates (critical for currency normalization)
    0: [
        ('currency_data', 'https://tradingeconomics.com/currency/usd-myr'),
        ('currency_data', 'https://tradingeconomics.com/currency/usd-brl'),
        ('currency_data', 'https://tradingeconomics.com/currency/usd-ars'),
        ('currency_data', 'https://tradingeconomics.com/currency/usd-idr'),
        ('currency_data', 'https://tradingeconomics.com/currency/usd-cny'),
        ('currency_data', 'https://tradingeconomics.com/currency/usd-sgd'),
    ],
    
    # Minute 2: Front-month commodity prices
    2: [
        ('palm_oil_prices', 'https://tradingeconomics.com/commodity/palm-oil'),
        ('palm_oil_prices', 'https://tradingeconomics.com/commodity/rapeseed-oil'),
        ('palm_oil_prices', 'https://tradingeconomics.com/commodity/sunflower-oil'),
        ('soybean_oil_prices', 'https://tradingeconomics.com/commodity/soybean-oil'),
        ('soybean_oil_prices', 'https://tradingeconomics.com/commodity/soybeans'),
        ('soybean_oil_prices', 'https://tradingeconomics.com/commodity/soybean-meal'),
        ('commodity_prices_archive', 'https://tradingeconomics.com/commodity/brent-crude-oil'),
        ('commodity_prices_archive', 'https://tradingeconomics.com/commodity/wti-crude-oil'),
    ],
    
    # Minute 8: Spreads (precomputed if available)
    8: [
        ('commodity_prices_archive', 'https://tradingeconomics.com/spread/soybean-oil-palm-oil'),
        ('commodity_prices_archive', 'https://tradingeconomics.com/spread/palm-oil-crude-oil'),
    ],
    
    # Minute 10: Freight/Logistics
    10: [
        ('commodity_prices_archive', 'https://tradingeconomics.com/commodity/baltic-dry-index'),
        ('commodity_prices_archive', 'https://tradingeconomics.com/commodity/diesel'),
    ],
    
    # Minute 12: Additional commodities
    12: [
        ('palm_oil_fundamentals', 'https://tradingeconomics.com/country-list/palm-oil-production'),
    ],
    
    # Minute 14: Trade flows (imports/exports)
    14: [
        ('economic_indicators', 'https://tradingeconomics.com/china/imports/soybeans'),
        ('economic_indicators', 'https://tradingeconomics.com/china/imports/soybean-oil'),
        ('economic_indicators', 'https://tradingeconomics.com/brazil/exports/soybeans'),
        ('economic_indicators', 'https://tradingeconomics.com/brazil/exports/soybean-oil'),
        ('economic_indicators', 'https://tradingeconomics.com/india/imports/palm-oil'),
        ('economic_indicators', 'https://tradingeconomics.com/united-states/imports/soybean-oil'),
        ('economic_indicators', 'https://tradingeconomics.com/indonesia/exports/biodiesel'),
        ('economic_indicators', 'https://tradingeconomics.com/united-states/balance-of-trade'),
        ('economic_indicators', 'https://tradingeconomics.com/china/imports'),
    ],
    
    # Minute 20: Policy/Calendar/News
    20: [
        ('news_intelligence', 'https://tradingeconomics.com/calendar'),
        ('news_intelligence', 'https://tradingeconomics.com/news'),
        ('ice_trump_intelligence', 'https://tradingeconomics.com/united-states/tariffs'),
        ('ice_trump_intelligence', 'https://tradingeconomics.com/china/tariffs'),
        ('ice_trump_intelligence', 'https://tradingeconomics.com/united-states/subsidies'),
    ],
    
    # Minute 25: Macro indicators (GDP, industrial production)
    25: [
        ('economic_indicators', 'https://tradingeconomics.com/malaysia/gdp'),
        ('economic_indicators', 'https://tradingeconomics.com/indonesia/gdp'),
        ('economic_indicators', 'https://tradingeconomics.com/brazil/industrial-production'),
        ('economic_indicators', 'https://tradingeconomics.com/china/industrial-production'),
        ('economic_indicators', 'https://tradingeconomics.com/united-states/gdp'),
        ('economic_indicators', 'https://tradingeconomics.com/united-states/currency'),
    ],
    
    # Minute 30: Palm oil fundamentals
    30: [
        ('palm_oil_fundamentals', 'http://bepi.mpob.gov.my/'),  # MPOB
        ('palm_oil_fundamentals', 'https://tradingeconomics.com/malaysia/palm-oil-stocks'),
        ('palm_oil_fundamentals', 'https://tradingeconomics.com/malaysia/palm-oil-exports'),
        ('palm_oil_fundamentals', 'https://tradingeconomics.com/indonesia/palm-oil-production'),
        ('palm_oil_fundamentals', 'https://tradingeconomics.com/indonesia/palm-oil-exports'),
    ],
    
    # Minute 40: Political indicators
    40: [
        ('ice_trump_intelligence', 'https://tradingeconomics.com/united-states/presidential-approval'),
    ],
    
    # Minute 50: Redundancy pass (re-check critical prices)
    50: [
        ('palm_oil_prices', 'https://tradingeconomics.com/commodity/palm-oil'),
        ('soybean_oil_prices', 'https://tradingeconomics.com/commodity/soybean-oil'),
        ('currency_data', 'https://tradingeconomics.com/currency/usd-myr'),
    ],
}


def polite_sleep():
    """Sleep with random jitter for polite scraping"""
    delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
    time.sleep(delay)


def get_cache_key(url):
    """Generate cache key from URL"""
    return hashlib.md5(url.encode()).hexdigest()


def is_cache_valid(cache_file, ttl_hours=1):
    """Check if cache is still valid"""
    if not os.path.exists(cache_file):
        return False
    
    file_time = os.path.getmtime(cache_file)
    current_time = time.time()
    age_hours = (current_time - file_time) / 3600
    
    return age_hours < ttl_hours


def save_raw_html(url, html_content, status_code):
    """Save raw HTML for debugging/reprocessing"""
    cache_key = get_cache_key(url)
    timestamp = datetime.now(timezone.utc).isoformat()
    
    raw_data = {
        'url': url,
        'timestamp': timestamp,
        'status_code': status_code,
        'html': html_content,
        'hash': hashlib.sha256(html_content.encode()).hexdigest()
    }
    
    raw_file = os.path.join(RAW_HTML_DIR, f'{cache_key}_{timestamp[:10]}.json')
    with open(raw_file, 'w') as f:
        json.dump(raw_data, f)


def scrape_url(url, max_retries=3):
    """
    Scrape URL with retry logic and caching
    Returns: (soup, success_flag)
    """
    cache_key = get_cache_key(url)
    cache_file = os.path.join(CACHE_DIR, f'{cache_key}.html')
    
    # Check cache first
    if is_cache_valid(cache_file):
        logger.info(f"Using cached data for {url}")
        with open(cache_file, 'r') as f:
            html = f.read()
            return BeautifulSoup(html, 'html.parser'), True
    
    # Scrape with retries
    for attempt in range(max_retries):
        try:
            logger.info(f"Scraping {url} (attempt {attempt + 1}/{max_retries})")
            
            response = requests.get(url, headers=HEADERS, timeout=30)
            
            if response.status_code == 200:
                html = response.text
                
                # Save to cache
                with open(cache_file, 'w') as f:
                    f.write(html)
                
                # Save raw HTML for debugging
                save_raw_html(url, html, response.status_code)
                
                return BeautifulSoup(html, 'html.parser'), True
            
            else:
                logger.warning(f"HTTP {response.status_code} for {url}")
                save_raw_html(url, response.text, response.status_code)
                
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            
            if attempt < max_retries - 1:
                backoff = (2 ** attempt) * 2  # Exponential backoff: 2s, 4s, 8s
                logger.info(f"Retrying in {backoff}s...")
                time.sleep(backoff)
    
    return None, False


def parse_te_value(soup, selectors=None):
    """
    Parse numeric value from TradingEconomics page
    Tries multiple common selectors
    """
    if selectors is None:
        selectors = [
            '#ctl00_ContentPlaceHolder1_market_value',
            '.market-value',
            '[data-symbol]',
            'div.col-md-4.col-sm-4 > div',
        ]
    
    for selector in selectors:
        try:
            element = soup.select_one(selector)
            if element:
                text = element.text.strip().replace(',', '').replace('%', '')
                # Try to extract first number
                import re
                match = re.search(r'-?\d+\.?\d*', text)
                if match:
                    return float(match.group())
        except Exception as e:
            continue
    
    return None


def scrape_commodity_price(url, symbol):
    """Scrape commodity price from TradingEconomics"""
    soup, success = scrape_url(url)
    
    if not success or soup is None:
        return None
    
    value = parse_te_value(soup)
    
    if value is None:
        logger.warning(f"Could not parse value from {url}")
        return None
    
    return {
        'time': datetime.now(timezone.utc),
        'symbol': symbol,
        'close': value,
        'source_name': 'TradingEconomics',
        'confidence_score': 0.85,
        'ingest_timestamp_utc': datetime.now(timezone.utc),
        'provenance_uuid': str(uuid.uuid4())
    }


def scrape_fx_rate(url, pair):
    """Scrape FX rate"""
    soup, success = scrape_url(url)
    
    if not success or soup is None:
        return None
    
    rate = parse_te_value(soup)
    
    if rate is None:
        logger.warning(f"Could not parse FX rate from {url}")
        return None
    
    return {
        'timestamp': datetime.now(timezone.utc),
        'currency_pair': pair.upper(),
        'rate': rate,
        'source_name': 'TradingEconomics',
        'confidence_score': 0.90,
        'ingest_timestamp_utc': datetime.now(timezone.utc)
    }


def scrape_economic_indicator(url, indicator_name):
    """Scrape economic indicator"""
    soup, success = scrape_url(url)
    
    if not success or soup is None:
        return None
    
    value = parse_te_value(soup)
    
    if value is None:
        logger.warning(f"Could not parse indicator from {url}")
        return None
    
    return {
        'time': datetime.now(timezone.utc),
        'indicator': indicator_name,
        'value': value,
        'source_name': 'TradingEconomics',
        'confidence_score': 0.85,
        'ingest_timestamp_utc': datetime.now(timezone.utc)
    }


def scrape_palm_fundamentals(url, metric):
    """Scrape palm oil fundamentals (MPOB or TradingEconomics)"""
    soup, success = scrape_url(url)
    
    if not success or soup is None:
        return None
    
    value = parse_te_value(soup)
    
    if value is None:
        logger.warning(f"Could not parse palm fundamental from {url}")
        return None
    
    return {
        'date': datetime.now(timezone.utc).date(),
        'country': 'Malaysia' if 'malaysia' in url else 'Indonesia',
        metric: value,
        'source_name': 'MPOB' if 'mpob' in url else 'TradingEconomics',
        'confidence_score': 0.90 if 'mpob' in url else 0.85,
        'ingest_timestamp_utc': datetime.now(timezone.utc),
        'provenance_uuid': str(uuid.uuid4())
    }


def run_scraping_batch(minute_offset):
    """Run scraping for a specific minute offset"""
    if minute_offset not in SCRAPE_SCHEDULE:
        logger.info(f"No scraping scheduled for minute {minute_offset}")
        return
    
    urls = SCRAPE_SCHEDULE[minute_offset]
    logger.info(f"Running scraping batch for minute {minute_offset}: {len(urls)} URLs")
    
    results = {}
    
    for table_name, url in urls:
        try:
            # Polite delay between requests
            polite_sleep()
            
            # Route to appropriate parser based on table
            if table_name == 'currency_data':
                pair = url.split('/')[-1].replace(':cur', '').upper()
                data = scrape_fx_rate(url, pair)
                
            elif table_name in ['palm_oil_prices', 'soybean_oil_prices', 'commodity_prices_archive']:
                symbol = url.split('/')[-1].upper().replace('-', '_')
                data = scrape_commodity_price(url, symbol)
                
            elif table_name == 'economic_indicators':
                indicator_name = url.split('/')[-1] + '_' + url.split('/')[-2]
                data = scrape_economic_indicator(url, indicator_name)
                
            elif table_name == 'palm_oil_fundamentals':
                metric = 'production_mt' if 'production' in url else 'stocks_mt' if 'stocks' in url else 'exports_mt'
                data = scrape_palm_fundamentals(url, metric)
                
            elif table_name in ['news_intelligence', 'ice_trump_intelligence']:
                # TODO: Implement news/policy scraping
                logger.info(f"Skipping news scraping for now: {url}")
                continue
            
            else:
                logger.warning(f"Unknown table: {table_name}")
                continue
            
            # Store result
            if data:
                if table_name not in results:
                    results[table_name] = []
                results[table_name].append(data)
                logger.info(f"Successfully scraped {url} → {table_name}")
            else:
                logger.warning(f"No data from {url}")
                
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            continue
    
    return results


def save_to_bigquery(results):
    """
    Save scraped data to BigQuery tables
    NOTE: Uses existing tables - NO NEW TABLES CREATED
    """
    try:
        from google.cloud import bigquery
        client = bigquery.Client(project='cbi-v14')
        
        for table_name, rows in results.items():
            if not rows:
                continue
            
            df = pd.DataFrame(rows)
            table_id = f'cbi-v14.forecasting_data_warehouse.{table_name}'
            
            # Load to BigQuery
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND",
                autodetect=True
            )
            
            job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()  # Wait for completion
            
            logger.info(f"Loaded {len(df)} rows to {table_name}")
            
    except Exception as e:
        logger.error(f"BigQuery load error: {e}")
        # Save to local CSV as fallback
        for table_name, rows in results.items():
            df = pd.DataFrame(rows)
            csv_file = f'/tmp/{table_name}_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
            df.to_csv(csv_file, index=False)
            logger.info(f"Saved fallback CSV: {csv_file}")


def main():
    """Main scraping entry point - run every hour via cron"""
    logger.info("=" * 80)
    logger.info("Starting TradingEconomics hourly scraping cycle")
    logger.info("=" * 80)
    
    current_minute = datetime.now().minute
    
    # Find the closest scheduled minute offset
    scheduled_minutes = sorted(SCRAPE_SCHEDULE.keys())
    closest_minute = min(scheduled_minutes, key=lambda x: abs(x - current_minute))
    
    logger.info(f"Current minute: {current_minute}, closest schedule: {closest_minute}")
    
    # Run scraping batch
    results = run_scraping_batch(closest_minute)
    
    if results:
        # Save to BigQuery
        save_to_bigquery(results)
    
    logger.info("Scraping cycle complete")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()

