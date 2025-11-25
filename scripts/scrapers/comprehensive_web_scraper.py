#!/usr/bin/env python3
"""
Comprehensive Web Scraper for CBI-V14
Full HTML scraping - NO BYPASSING, match Grok capability
"""

import os
import time
import hashlib
import re
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from google.cloud import bigquery
import logging
from urllib.robotparser import RobotFileParser
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)
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
    
    def fetch_html(self, url: str, use_selenium: bool = False) -> Optional[str]:
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
    
    def extract_number(self, text: str) -> Optional[float]:
        """Extract first number from text"""
        match = re.search(r'([\d,]+\.?\d*)', text.replace(',', ''))
        return float(match.group(1)) if match else None
    
    def extract_date(self, text: str) -> Optional[str]:
        """Extract date from text"""
        patterns = [
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{1,2}-\d{1,2}-\d{4})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None

class BarchartScraper(EthicalScraper):
    """Scrape Barchart.com for soybean oil futures"""
    
    def scrape_futures(self) -> List[Dict]:
        """Scrape soybean oil futures prices"""
        url = "https://www.barchart.com/futures/quotes/ZL*0/overview"
        html = self.fetch_html(url)
        if not html:
            logger.error("Failed to fetch Barchart data")
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        rows = []
        
        # Find futures table
        table = soup.find('table', class_='datatable') or soup.find('table')
        if not table:
            logger.error("Could not find futures table")
            return []
        
        for tr in table.find_all('tr')[1:]:
            cols = tr.find_all('td')
            if len(cols) < 8:
                continue
            
            try:
                symbol = cols[0].text.strip()
                contract_month = self.parse_contract_month(symbol)
                
                row = {
                    'symbol': symbol,
                    'contract_month': contract_month,
                    'last': self.extract_number(cols[1].text) if len(cols) > 1 else None,
                    'change': self.extract_number(cols[2].text) if len(cols) > 2 else None,
                    'change_pct': self.extract_number(cols[3].text.replace('%', '')) if len(cols) > 3 else None,
                    'volume': int(self.extract_number(cols[4].text) or 0) if len(cols) > 4 else 0,
                    'open_interest': int(self.extract_number(cols[5].text) or 0) if len(cols) > 5 else 0,
                    'high': self.extract_number(cols[6].text) if len(cols) > 6 else None,
                    'low': self.extract_number(cols[7].text) if len(cols) > 7 else None,
                    'scrape_timestamp': datetime.utcnow(),
                    'source_url': url
                }
                rows.append(row)
            except Exception as e:
                logger.warning(f"Error parsing row: {e}")
        
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
    
    def save_to_bigquery(self, table_id: str, rows: List[Dict]):
        """Save rows to BigQuery"""
        try:
            errors = self.client.insert_rows_json(f'cbi-v14.{table_id}', rows)
            if errors:
                logger.error(f"BigQuery errors: {errors}")
            else:
                logger.info(f"Inserted {len(rows)} rows into {table_id}")
        except Exception as e:
            logger.error(f"Failed to insert into BigQuery: {e}")

class EPAScraper(EthicalScraper):
    """Scrape EPA.gov for RFS volumes"""
    
    def scrape_rfs_volumes(self) -> List[Dict]:
        """Scrape RFS volumes and announcements"""
        url = "https://www.epa.gov/renewable-fuel-standard-program/current-renewable-fuel-standard-rfs-volumes"
        html = self.fetch_html(url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        rows = []
        
        for table in soup.find_all('table'):
            for tr in table.find_all('tr')[1:]:
                cols = tr.find_all('td')
                if len(cols) < 2:
                    continue
                
                try:
                    row = {
                        'policy_id': hashlib.md5(f"{url}_{cols[0].text}".encode()).hexdigest()[:16],
                        'announcement_date': datetime.utcnow().date().isoformat(),
                        'category': 'RFS',
                        'value_num': self.extract_number(cols[1].text),
                        'unit': 'billion gallons',
                        'source_url': url,
                        'raw_html_excerpt': str(tr)[:500],
                        'scrape_timestamp': datetime.utcnow()
                    }
                    rows.append(row)
                except Exception as e:
                    logger.warning(f"Error parsing EPA row: {e}")
        
        if rows:
            self.save_to_bigquery('forecasting_data_warehouse.policy_rfs_volumes', rows)
        
        return rows
    
    def save_to_bigquery(self, table_id: str, rows: List[Dict]):
        """Save rows to BigQuery"""
        try:
            errors = self.client.insert_rows_json(f'cbi-v14.{table_id}', rows)
            if not errors:
                logger.info(f"Inserted {len(rows)} rows into {table_id}")
        except Exception as e:
            logger.error(f"Failed to insert: {e}")

class ReutersScraper(EthicalScraper):
    """Scrape Reuters for commodities news"""
    
    def scrape_commodities_news(self) -> List[Dict]:
        """Scrape latest commodities news"""
        url = "https://www.reuters.com/markets/commodities/"
        html = self.fetch_html(url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        rows = []
        
        articles = soup.find_all('article')[:10]
        for article in articles:
            try:
                link = article.find('a', href=True)
                if not link:
                    continue
                
                article_url = link['href']
                if not article_url.startswith('http'):
                    article_url = f"https://www.reuters.com{article_url}"
                
                article_html = self.fetch_html(article_url)
                if not article_html:
                    continue
                
                article_soup = BeautifulSoup(article_html, 'html.parser')
                title = article_soup.find('h1')
                title_text = title.text.strip() if title else ''
                
                body = article_soup.find('article') or article_soup.find('div', class_='article-body')
                full_text = body.get_text(separator=' ', strip=True) if body else ''
                
                row = {
                    'news_id': hashlib.md5(article_url.encode()).hexdigest()[:16],
                    'published_at': datetime.utcnow(),
                    'title': title_text[:500],
                    'full_text': full_text[:10000],
                    'categories': ['commodities', 'reuters'],
                    'entities': [],
                    'sentiment': 0.0,
                    'url': article_url,
                    'scrape_timestamp': datetime.utcnow()
                }
                rows.append(row)
            except Exception as e:
                logger.warning(f"Error parsing Reuters article: {e}")
        
        if rows:
            self.save_to_bigquery('forecasting_data_warehouse.news_reuters', rows)
        
        return rows
    
    def save_to_bigquery(self, table_id: str, rows: List[Dict]):
        """Save rows to BigQuery"""
        try:
            errors = self.client.insert_rows_json(f'cbi-v14.{table_id}', rows)
            if not errors:
                logger.info(f"Inserted {len(rows)} rows into {table_id}")
        except Exception as e:
            logger.error(f"Failed to insert: {e}")

def run_all_scrapers():
    """Execute all web scrapers"""
    print("="*60)
    print("🕷️  CBI-V14 Comprehensive Web Scraping Pipeline")
    print("="*60)
    print(f"Start: {datetime.now().isoformat()}")
    print()
    
    # Phase 1: Price & Market Data
    print("📊 Phase 1: Price & Market Data")
    barchart = BarchartScraper()
    barchart.scrape_futures()
    
    # Phase 2: Policy & Legislation
    print("\n⚖️  Phase 2: Policy & Legislation")
    epa = EPAScraper()
    epa.scrape_rfs_volumes()
    
    # Phase 3: News & Intelligence
    print("\n📰 Phase 3: News & Intelligence")
    reuters = ReutersScraper()
    reuters.scrape_commodities_news()
    
    print("\n" + "="*60)
    print("✅ Web scraping complete!")
    print(f"End: {datetime.now().isoformat()}")
    print("="*60)

if __name__ == "__main__":
    run_all_scrapers()











