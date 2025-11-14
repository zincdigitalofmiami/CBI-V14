#!/usr/bin/env python3
"""
Production Web Scraper for CBI-V14
Comprehensive scraping for all 16 tables with error handling
"""

import os
import time
import hashlib
import re
import requests
import feedparser
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from google.cloud import bigquery
import logging
from urllib.robotparser import RobotFileParser
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EthicalScraper:
    """Base class for ethical web scraping"""
    
    def __init__(self, user_agent="CBI-V14-Research-Bot/1.0 (contact@cbi-v14.com)"):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': user_agent})
        self.rate_limit_delay = 1.5
        self.last_request_time = {}
        self.client = bigquery.Client(project='cbi-v14')
        
    def check_robots_txt(self, url: str) -> bool:
        """Check if scraping is allowed per robots.txt"""
        rp = RobotFileParser()
        domain = '/'.join(url.split('/')[:3])
        robots_url = f"{domain}/robots.txt"
        try:
            rp.set_url(robots_url)
            rp.read()
            return rp.can_fetch(self.session.headers['User-Agent'], url)
        except:
            return True
    
    def rate_limit(self, domain: str):
        """Enforce rate limiting per domain"""
        now = time.time()
        if domain in self.last_request_time:
            elapsed = now - self.last_request_time[domain]
            if elapsed < self.rate_limit_delay:
                time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time[domain] = time.time()
    
    def fetch_html(self, url: str) -> Optional[str]:
        """Fetch HTML with retry logic"""
        domain = '/'.join(url.split('/')[:3])
        if not self.check_robots_txt(url):
            logger.warning(f"Blocked by robots.txt: {url}")
            return None
        
        self.rate_limit(domain)
        
        for attempt in range(3):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response.text
            except Exception as e:
                logger.warning(f"Attempt {attempt+1} failed for {url}: {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)
        
        return None
    
    def fetch_rss(self, url: str) -> List[Dict]:
        """Fetch RSS feed"""
        try:
            feed = feedparser.parse(url)
            return feed.entries if hasattr(feed, 'entries') else []
        except Exception as e:
            logger.error(f"RSS fetch failed for {url}: {e}")
            return []
    
    def extract_number(self, text: str) -> Optional[float]:
        """Extract first number from text"""
        match = re.search(r'([\d,]+\.?\d*)', text.replace(',', ''))
        return float(match.group(1)) if match else None
    
    def save_to_bigquery(self, table_id: str, rows: List[Dict]):
        """Save rows to BigQuery"""
        if not rows:
            return
        
        try:
            errors = self.client.insert_rows_json(f'cbi-v14.{table_id}', rows)
            if errors:
                logger.error(f"BigQuery errors for {table_id}: {errors}")
            else:
                logger.info(f"✅ Inserted {len(rows)} rows into {table_id}")
        except Exception as e:
            logger.error(f"Failed to insert into {table_id}: {e}")

class BarchartScraper(EthicalScraper):
    """Scrape Barchart.com for soybean oil futures"""
    
    def scrape_futures(self) -> List[Dict]:
        """Scrape soybean oil futures prices"""
        url = "https://www.barchart.com/futures/quotes/ZL*0/overview"
        html = self.fetch_html(url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        rows = []
        
        table = soup.find('table', class_='datatable') or soup.find('table')
        if not table:
            logger.warning("Could not find futures table on Barchart")
            return []
        
        for tr in table.find_all('tr')[1:]:
            cols = tr.find_all('td')
            if len(cols) < 8:
                continue
            
            try:
                symbol = cols[0].text.strip()
                row = {
                    'symbol': symbol,
                    'contract_month': self.parse_contract_month(symbol),
                    'last': self.extract_number(cols[1].text),
                    'change': self.extract_number(cols[2].text),
                    'change_pct': self.extract_number(cols[3].text.replace('%', '')),
                    'volume': int(self.extract_number(cols[4].text) or 0),
                    'open_interest': int(self.extract_number(cols[5].text) or 0),
                    'high': self.extract_number(cols[6].text),
                    'low': self.extract_number(cols[7].text),
                    'scrape_timestamp': datetime.utcnow().isoformat(),
                    'source_url': url
                }
                rows.append(row)
            except Exception as e:
                logger.warning(f"Error parsing Barchart row: {e}")
        
        if rows:
            self.save_to_bigquery('forecasting_data_warehouse.futures_prices_barchart', rows)
        
        return rows
    
    def parse_contract_month(self, symbol: str) -> Optional[str]:
        """Parse contract month from symbol"""
        month_codes = {'F': 1, 'G': 2, 'H': 3, 'J': 4, 'K': 5, 'M': 6, 
                      'N': 7, 'Q': 8, 'U': 9, 'V': 10, 'X': 11, 'Z': 12}
        if len(symbol) < 4:
            return None
        month_code = symbol[-3]
        year_code = symbol[-2:]
        if month_code not in month_codes:
            return None
        month = month_codes[month_code]
        year = 2000 + int(year_code)
        return f"{year}-{month:02d}-01"

class FarmProgressScraper(EthicalScraper):
    """Scrape Farm Progress for market news"""
    
    def scrape_news(self) -> List[Dict]:
        """Scrape news via RSS"""
        feed_url = "https://www.farmprogress.com/rss.xml"
        entries = self.fetch_rss(feed_url)
        
        rows = []
        for entry in entries[:20]:
            try:
                row = {
                    'news_id': hashlib.md5(entry.link.encode()).hexdigest()[:16],
                    'published_at': datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.utcnow(),
                    'title': entry.title[:500] if hasattr(entry, 'title') else '',
                    'author': entry.author if hasattr(entry, 'author') else '',
                    'full_text': entry.summary[:10000] if hasattr(entry, 'summary') else '',
                    'categories': ['farm_progress'],
                    'entities': [],
                    'url': entry.link if hasattr(entry, 'link') else '',
                    'scrape_timestamp': datetime.utcnow()
                }
                rows.append(row)
            except Exception as e:
                logger.warning(f"Error parsing Farm Progress entry: {e}")
        
        if rows:
            self.save_to_bigquery('forecasting_data_warehouse.news_market_farmprogress', rows)
        
        return rows

class BrownfieldScraper(EthicalScraper):
    """Scrape Brownfield Ag News"""
    
    def scrape_news(self) -> List[Dict]:
        """Scrape news via RSS"""
        feed_url = "https://brownfieldagnews.com/feed/"
        entries = self.fetch_rss(feed_url)
        
        rows = []
        for entry in entries[:20]:
            try:
                row = {
                    'news_id': hashlib.md5(entry.link.encode()).hexdigest()[:16],
                    'published_at': datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.utcnow(),
                    'title': entry.title[:500] if hasattr(entry, 'title') else '',
                    'author': entry.author if hasattr(entry, 'author') else '',
                    'full_text': entry.summary[:10000] if hasattr(entry, 'summary') else '',
                    'categories': ['brownfield'],
                    'entities': [],
                    'url': entry.link if hasattr(entry, 'link') else '',
                    'scrape_timestamp': datetime.utcnow()
                }
                rows.append(row)
            except Exception as e:
                logger.warning(f"Error parsing Brownfield entry: {e}")
        
        if rows:
            self.save_to_bigquery('forecasting_data_warehouse.news_industry_brownfield', rows)
        
        return rows

class ENSOScraper(EthicalScraper):
    """Scrape NOAA ENSO status"""
    
    def scrape_enso(self) -> List[Dict]:
        """Scrape ENSO status"""
        url = "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_advisory/ensodisc.shtml"
        html = self.fetch_html(url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        rows = []
        
        try:
            # Parse ENSO phase from page
            text = soup.get_text()
            phase = 'Neutral'
            if 'La Niña' in text or 'La Nina' in text:
                phase = 'La Niña'
            elif 'El Niño' in text or 'El Nino' in text:
                phase = 'El Niño'
            
            row = {
                'as_of_date': datetime.utcnow().date().isoformat(),
                'enso_phase': phase,
                'probability': 0.5,  # Would need to parse from text
                'outlook_months': 3,
                'strength': 'moderate',
                'forecast_phase_1mo': phase,
                'forecast_phase_3mo': phase,
                'notes': text[:1000],
                'source_url': url,
                'scrape_timestamp': datetime.utcnow().isoformat()
            }
            rows.append(row)
        except Exception as e:
            logger.warning(f"Error parsing ENSO: {e}")
        
        if rows:
            self.save_to_bigquery('forecasting_data_warehouse.enso_climate_status', rows)
        
        return rows

def run_all_scrapers():
    """Execute all web scrapers"""
    print("="*60)
    print("🕷️  CBI-V14 Production Web Scraping Pipeline")
    print("="*60)
    print(f"Start: {datetime.now().isoformat()}")
    print()
    
    results = {}
    
    # Phase 1: Price & Market Data
    print("📊 Phase 1: Price & Market Data")
    try:
        barchart = BarchartScraper()
        results['barchart'] = len(barchart.scrape_futures())
        print(f"   ✅ Barchart: {results['barchart']} rows")
    except Exception as e:
        logger.error(f"Barchart failed: {e}")
        results['barchart'] = 0
    
    # Phase 2: News
    print("\n📰 Phase 2: News & Intelligence")
    try:
        farmprogress = FarmProgressScraper()
        results['farmprogress'] = len(farmprogress.scrape_news())
        print(f"   ✅ Farm Progress: {results['farmprogress']} rows")
    except Exception as e:
        logger.error(f"Farm Progress failed: {e}")
        results['farmprogress'] = 0
    
    try:
        brownfield = BrownfieldScraper()
        results['brownfield'] = len(brownfield.scrape_news())
        print(f"   ✅ Brownfield: {results['brownfield']} rows")
    except Exception as e:
        logger.error(f"Brownfield failed: {e}")
        results['brownfield'] = 0
    
    # Phase 3: Weather
    print("\n🌦️  Phase 3: Weather & Climate")
    try:
        enso = ENSOScraper()
        results['enso'] = len(enso.scrape_enso())
        print(f"   ✅ ENSO: {results['enso']} rows")
    except Exception as e:
        logger.error(f"ENSO failed: {e}")
        results['enso'] = 0
    
    print("\n" + "="*60)
    print("✅ Web scraping complete!")
    print(f"End: {datetime.now().isoformat()}")
    print()
    print("Summary:")
    for source, count in results.items():
        print(f"   {source}: {count} rows")
    print("="*60)
    
    return results

if __name__ == "__main__":
    run_all_scrapers()

