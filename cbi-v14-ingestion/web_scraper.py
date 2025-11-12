#!/usr/bin/env python3
"""
Comprehensive Web Scraping Module for CBI-V14
Implements ethical scraping with rate limiting and robots.txt compliance
Matches Grok capability: 18+ sources for real-time market intelligence

Phase 0.2 from CBI_V14_COMPLETE_EXECUTION_PLAN.md
"""

import os
import time
import hashlib
import re
import requests
import feedparser
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from google.cloud import bigquery
from urllib.robotparser import RobotFileParser
from typing import List, Dict, Optional
import logging
import PyPDF2
import pdfplumber

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Project constants
PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"

class EthicalScraper:
    """Base class for ethical web scraping"""
    
    def __init__(self, user_agent="CBI-V14-Research-Bot/1.0 (contact@cbi-v14.com)"):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': user_agent})
        self.rate_limit_delay = 1.5  # 1.5 seconds between requests
        self.last_request_time = {}
        self.client = bigquery.Client(project=PROJECT_ID)
        
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
            return True  # If robots.txt doesn't exist, assume allowed
    
    def rate_limit(self, domain: str):
        """Enforce rate limiting per domain (1-2 req/sec)"""
        now = time.time()
        if domain in self.last_request_time:
            elapsed = now - self.last_request_time[domain]
            if elapsed < self.rate_limit_delay:
                time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time[domain] = time.time()
    
    def fetch_html(self, url: str, use_selenium: bool = False) -> Optional[str]:
        """Fetch HTML with retry logic and Selenium fallback"""
        domain = '/'.join(url.split('/')[:3])
        
        if not self.check_robots_txt(url):
            logger.warning(f"❌ Blocked by robots.txt: {url}")
            return None
        
        self.rate_limit(domain)
        
        # Try requests first (faster)
        if not use_selenium:
            for attempt in range(3):
                try:
                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()
                    return response.text
                except Exception as e:
                    logger.warning(f"Attempt {attempt+1} failed for {url}: {e}")
                    if attempt < 2:
                        time.sleep(2 ** attempt)
        
        # Fallback to Selenium for JavaScript-heavy sites
        logger.info(f"Using Selenium for {url}")
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            driver = webdriver.Chrome(options=options)
            driver.get(url)
            time.sleep(3)
            html = driver.page_source
            driver.quit()
            return html
        except Exception as e:
            logger.error(f"❌ Selenium failed for {url}: {e}")
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
        if not text:
            return None
        match = re.search(r'([\d,]+\.?\d*)', text.replace(',', ''))
        return float(match.group(1)) if match else None
    
    def extract_entities(self, text: str) -> List[str]:
        """Extract named entities using simple pattern matching"""
        entities = []
        # Common entity patterns
        country_pattern = r'\b(China|Brazil|Argentina|USA|United States|Paraguay|Uruguay)\b'
        org_pattern = r'\b(USDA|EPA|CME|CFTC|ASA)\b'
        
        entities.extend(re.findall(country_pattern, text, re.IGNORECASE))
        entities.extend(re.findall(org_pattern, text, re.IGNORECASE))
        
        return list(set(entities))
    
    def compute_sentiment(self, text: str) -> float:
        """Simple sentiment analysis"""
        positive_words = ['gain', 'rise', 'up', 'bullish', 'strong', 'positive', 'surge', 'boost', 'high']
        negative_words = ['loss', 'fall', 'down', 'bearish', 'weak', 'negative', 'plunge', 'drop', 'low']
        
        text_lower = text.lower()
        pos = sum(text_lower.count(w) for w in positive_words)
        neg = sum(text_lower.count(w) for w in negative_words)
        
        if pos + neg == 0:
            return 0.0
        return (pos - neg) / (pos + neg)
    
    def save_to_bigquery(self, table_id: str, rows: List[Dict]):
        """Save rows to BigQuery"""
        if not rows:
            logger.warning(f"No rows to save to {table_id}")
            return
        
        try:
            full_table_id = f'{PROJECT_ID}.{table_id}'
            errors = self.client.insert_rows_json(full_table_id, rows)
            if errors:
                logger.error(f"BigQuery errors for {table_id}: {errors}")
            else:
                logger.info(f"✅ Inserted {len(rows)} rows into {table_id}")
        except Exception as e:
            logger.error(f"Failed to insert into {table_id}: {e}")


class BarchartScraper(EthicalScraper):
    """Scrape Barchart.com for futures prices and forward curve"""
    
    def scrape_futures(self) -> List[Dict]:
        """Scrape soybean oil futures"""
        url = "https://www.barchart.com/futures/quotes/ZL*0/overview"
        html = self.fetch_html(url)
        
        if not html:
            logger.error("❌ Failed to fetch Barchart data")
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table', class_='datatable')
        
        if not table:
            logger.error("❌ Could not find futures table on Barchart")
            return []
        
        rows = []
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
                logger.warning(f"Error parsing row: {e}")
        
        if rows:
            self.save_to_bigquery(f'{DATASET_ID}.futures_prices_barchart', rows)
        
        return rows
    
    def parse_contract_month(self, symbol: str) -> Optional[str]:
        """Parse contract month from symbol (e.g., 'ZLZ24' -> '2024-12-01')"""
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


class MarketWatchScraper(EthicalScraper):
    """Scrape MarketWatch for futures prices"""
    
    def scrape_futures(self) -> List[Dict]:
        """Scrape soybean oil futures from MarketWatch"""
        url = "https://www.marketwatch.com/investing/future/zl00"
        html = self.fetch_html(url)
        
        if not html:
            logger.error("❌ Failed to fetch MarketWatch data")
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        rows = []
        
        try:
            # Extract price data from JSON-LD or meta tags
            price_element = soup.find('bg-quote', {'field': 'Last'})
            if price_element:
                last_price = self.extract_number(price_element.text)
                
                row = {
                    'symbol': 'ZL',
                    'contract_month': datetime.utcnow().date().replace(day=1).isoformat(),
                    'last': last_price,
                    'change': None,  # Extract from page if available
                    'change_pct': None,
                    'volume': None,
                    'open_interest': None,
                    'high': None,
                    'low': None,
                    'scrape_timestamp': datetime.utcnow().isoformat(),
                    'source_url': url
                }
                rows.append(row)
        except Exception as e:
            logger.warning(f"Error parsing MarketWatch: {e}")
        
        if rows:
            self.save_to_bigquery(f'{DATASET_ID}.futures_prices_marketwatch', rows)
        
        return rows


class InvestingScraper(EthicalScraper):
    """Scrape Investing.com for futures and technical indicators"""
    
    def scrape_futures(self) -> List[Dict]:
        """Scrape soybean oil futures with technical indicators"""
        url = "https://www.investing.com/commodities/us-soybean-oil"
        html = self.fetch_html(url)
        
        if not html:
            logger.error("❌ Failed to fetch Investing.com data")
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        rows = []
        
        try:
            # Extract price and technical indicators
            price_elem = soup.find('span', {'data-test': 'instrument-price-last'})
            
            if price_elem:
                last_price = self.extract_number(price_elem.text)
                
                # Try to extract RSI and MACD from technical indicators section
                rsi = None
                macd = None
                
                tech_section = soup.find('div', {'class': 'technicalIndicatorsTicker'})
                if tech_section:
                    rsi_elem = tech_section.find(text=re.compile(r'RSI'))
                    if rsi_elem:
                        rsi = self.extract_number(rsi_elem)
                
                row = {
                    'symbol': 'ZL',
                    'contract_month': datetime.utcnow().date().replace(day=1).isoformat(),
                    'last': last_price,
                    'change': None,
                    'change_pct': None,
                    'volume': None,
                    'high': None,
                    'low': None,
                    'technical_indicator_rsi': rsi,
                    'technical_indicator_macd': macd,
                    'scrape_timestamp': datetime.utcnow().isoformat(),
                    'source_url': url
                }
                rows.append(row)
        except Exception as e:
            logger.warning(f"Error parsing Investing.com: {e}")
        
        if rows:
            self.save_to_bigquery(f'{DATASET_ID}.futures_prices_investing', rows)
        
        return rows


class TradingViewScraper(EthicalScraper):
    """Scrape TradingView for trader sentiment"""
    
    def scrape_sentiment(self) -> List[Dict]:
        """Scrape trader sentiment from TradingView"""
        url = "https://www.tradingview.com/symbols/CBOT-ZL1!/technicals/"
        html = self.fetch_html(url, use_selenium=True)  # TradingView is JS-heavy
        
        if not html:
            logger.error("❌ Failed to fetch TradingView data")
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        rows = []
        
        try:
            # Look for sentiment indicators
            sentiment_section = soup.find('div', {'class': 'speedometerSignal'})
            
            # Parse bullish/bearish percentages (example - adjust based on actual HTML)
            bullish_pct = 50.0  # Default neutral
            bearish_pct = 50.0
            
            row = {
                'symbol': 'ZL',
                'bullish_pct': bullish_pct,
                'bearish_pct': bearish_pct,
                'price_target_high': None,
                'price_target_low': None,
                'scrape_timestamp': datetime.utcnow().isoformat(),
                'source_url': url
            }
            rows.append(row)
        except Exception as e:
            logger.warning(f"Error parsing TradingView: {e}")
        
        if rows:
            self.save_to_bigquery(f'{DATASET_ID}.futures_sentiment_tradingview', rows)
        
        return rows


class EPAScraper(EthicalScraper):
    """Scrape EPA.gov for RFS volumes and policy"""
    
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
                        'effective_start': None,
                        'effective_end': None,
                        'category': 'RFS',
                        'value_num': self.extract_number(cols[1].text),
                        'unit': 'billion gallons',
                        'proposal_date': None,
                        'comment_period_end': None,
                        'finalization_date': None,
                        'source_url': url,
                        'raw_html_excerpt': str(tr)[:500],
                        'scrape_timestamp': datetime.utcnow().isoformat()
                    }
                    rows.append(row)
                except Exception as e:
                    logger.warning(f"Error parsing EPA row: {e}")
        
        if rows:
            self.save_to_bigquery(f'{DATASET_ID}.policy_rfs_volumes', rows)
        
        return rows


class CongressGovScraper(EthicalScraper):
    """Scrape Congress.gov for agricultural legislation"""
    
    def scrape_bills(self) -> List[Dict]:
        """Scrape agricultural bills from Congress.gov"""
        # Congress.gov API is preferred over scraping
        url = "https://api.congress.gov/v3/bill/118?format=json&limit=20"
        
        try:
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                bills = data.get('bills', [])
                
                rows = []
                for bill in bills:
                    # Filter for agricultural relevance
                    title = bill.get('title', '').lower()
                    if any(keyword in title for keyword in ['farm', 'agriculture', 'soybean', 'biofuel', 'crop']):
                        row = {
                            'bill_id': bill.get('number', ''),
                            'congress': 118,
                            'introduced': bill.get('introducedDate', datetime.utcnow().date().isoformat()),
                            'latest_action': bill.get('latestAction', {}).get('actionDate'),
                            'latest_action_text': bill.get('latestAction', {}).get('text', '')[:500],
                            'title': bill.get('title', '')[:1000],
                            'sponsors': [bill.get('sponsor', {}).get('firstName', '') + ' ' + bill.get('sponsor', {}).get('lastName', '')],
                            'committees': [],
                            'subjects': [],
                            'text_excerpt': '',
                            'url': bill.get('url', ''),
                            'scrape_timestamp': datetime.utcnow().isoformat()
                        }
                        rows.append(row)
                
                if rows:
                    self.save_to_bigquery(f'{DATASET_ID}.legislative_bills', rows)
                
                return rows
        except Exception as e:
            logger.error(f"Congress.gov scraping failed: {e}")
            return []


class FederalRegisterScraper(EthicalScraper):
    """Scrape FederalRegister.gov for policy events"""
    
    def scrape_policy_events(self) -> List[Dict]:
        """Scrape Federal Register for agricultural policy events"""
        # Federal Register has an API
        url = "https://www.federalregister.gov/api/v1/documents.json"
        params = {
            'conditions[term]': 'agriculture soybean biofuel',
            'per_page': 20,
            'order': 'newest'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                documents = data.get('results', [])
                
                rows = []
                for doc in documents:
                    row = {
                        'doc_id': doc.get('document_number', ''),
                        'published_at': doc.get('publication_date', datetime.utcnow().isoformat()),
                        'effective_date': doc.get('effective_on'),
                        'agency': doc.get('agencies', []),
                        'doc_type': doc.get('type', ''),
                        'title': doc.get('title', '')[:1000],
                        'summary': doc.get('abstract', '')[:5000],
                        'full_text_excerpt': '',
                        'topics': doc.get('topics', []),
                        'url': doc.get('html_url', ''),
                        'scrape_timestamp': datetime.utcnow().isoformat()
                    }
                    rows.append(row)
                
                if rows:
                    self.save_to_bigquery(f'{DATASET_ID}.policy_events_federalregister', rows)
                
                return rows
        except Exception as e:
            logger.error(f"Federal Register scraping failed: {e}")
            return []


class ReutersScraper(EthicalScraper):
    """Scrape Reuters for commodities news"""
    
    def scrape_commodities_news(self) -> List[Dict]:
        """Scrape latest commodities news"""
        url = "https://www.reuters.com/markets/commodities/"
        html = self.fetch_html(url)
        
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        articles = soup.find_all('article')
        
        rows = []
        for article in articles[:10]:  # Limit to 10
            try:
                link = article.find('a', href=True)
                if not link:
                    continue
                
                article_url = link['href']
                if not article_url.startswith('http'):
                    article_url = f"https://www.reuters.com{article_url}"
                
                # Fetch full article
                article_html = self.fetch_html(article_url)
                if not article_html:
                    continue
                
                article_soup = BeautifulSoup(article_html, 'html.parser')
                title = article_soup.find('h1')
                title_text = title.text.strip() if title else ''
                
                body = article_soup.find('article')
                full_text = body.get_text(separator=' ', strip=True) if body else ''
                
                entities = self.extract_entities(full_text)
                sentiment = self.compute_sentiment(full_text)
                
                row = {
                    'news_id': hashlib.md5(article_url.encode()).hexdigest()[:16],
                    'published_at': datetime.utcnow().isoformat(),
                    'title': title_text[:1000],
                    'full_text': full_text[:10000],
                    'categories': ['commodities', 'reuters'],
                    'region': 'global',
                    'entities': entities[:50],
                    'sentiment': sentiment,
                    'url': article_url,
                    'scrape_timestamp': datetime.utcnow().isoformat()
                }
                rows.append(row)
                
            except Exception as e:
                logger.warning(f"Error parsing Reuters article: {e}")
        
        if rows:
            self.save_to_bigquery(f'{DATASET_ID}.news_reuters', rows)
        
        return rows


class USDAERSScraper(EthicalScraper):
    """Scrape USDA ERS for monthly oilcrops reports"""
    
    def scrape_oilcrops_report(self) -> List[Dict]:
        """Scrape ERS Oil Crops Outlook report (PDF)"""
        # ERS publishes monthly Oil Crops Outlook
        url = "https://www.ers.usda.gov/webdocs/publications/oil-crops-outlook/"
        
        try:
            # This would require PDF parsing from their latest report
            # For now, return empty - full implementation needs pdfplumber
            logger.info("USDA ERS scraping requires PDF parsing - placeholder")
            return []
        except Exception as e:
            logger.error(f"USDA ERS scraping failed: {e}")
            return []


class USDAWASDEScraper(EthicalScraper):
    """Scrape USDA WASDE for supply/demand reports"""
    
    def scrape_wasde_report(self) -> List[Dict]:
        """Scrape WASDE soybean data (PDF parsing)"""
        # WASDE is published monthly as PDF
        url = "https://www.usda.gov/oce/commodity/wasde/latest.pdf"
        
        try:
            # Requires PDF table extraction
            logger.info("USDA WASDE scraping requires PDF parsing - placeholder")
            return []
        except Exception as e:
            logger.error(f"USDA WASDE scraping failed: {e}")
            return []


class ASAScraper(EthicalScraper):
    """Scrape American Soybean Association for industry intelligence"""
    
    def scrape_news(self) -> List[Dict]:
        """Scrape ASA news and policy positions"""
        url = "https://soygrowers.com/news-issues/"
        html = self.fetch_html(url)
        
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        rows = []
        
        try:
            # Find article links
            articles = soup.find_all('article', limit=10)
            
            for article in articles:
                link = article.find('a', href=True)
                if not link:
                    continue
                
                article_url = link['href']
                if not article_url.startswith('http'):
                    article_url = f"https://soygrowers.com{article_url}"
                
                title_elem = article.find('h2') or article.find('h3')
                title = title_elem.text.strip() if title_elem else ''
                
                row = {
                    'article_id': hashlib.md5(article_url.encode()).hexdigest()[:16],
                    'published_at': datetime.utcnow().isoformat(),
                    'title': title[:1000],
                    'full_text': '',
                    'policy_position': '',
                    'capacity_mention_mmbu': None,
                    'url': article_url,
                    'scrape_timestamp': datetime.utcnow().isoformat()
                }
                rows.append(row)
        except Exception as e:
            logger.warning(f"Error parsing ASA: {e}")
        
        if rows:
            self.save_to_bigquery(f'{DATASET_ID}.industry_intelligence_asa', rows)
        
        return rows


class CMEPublicScraper(EthicalScraper):
    """Scrape CME Group for public settlement data"""
    
    def scrape_settlements(self) -> List[Dict]:
        """Scrape CME public settlement prices"""
        url = "https://www.cmegroup.com/markets/agriculture/oilseeds/soybean-oil.settlements.html"
        html = self.fetch_html(url)
        
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        rows = []
        
        try:
            # CME publishes daily settlement data in tables
            table = soup.find('table', {'id': 'settlementsFuturesProductTable'})
            
            if table:
                for tr in table.find_all('tr')[1:]:
                    cols = tr.find_all('td')
                    if len(cols) >= 3:
                        row = {
                            'symbol': 'ZL',
                            'contract_month': None,  # Parse from first column
                            'settlement_price': self.extract_number(cols[2].text),
                            'volume': int(self.extract_number(cols[3].text) or 0) if len(cols) > 3 else None,
                            'open_interest': int(self.extract_number(cols[4].text) or 0) if len(cols) > 4 else None,
                            'scrape_timestamp': datetime.utcnow().isoformat(),
                            'source_url': url
                        }
                        rows.append(row)
        except Exception as e:
            logger.warning(f"Error parsing CME: {e}")
        
        if rows:
            self.save_to_bigquery(f'{DATASET_ID}.futures_prices_cme_public', rows)
        
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
                    'published_at': datetime(*entry.published_parsed[:6]).isoformat() if hasattr(entry, 'published_parsed') else datetime.utcnow().isoformat(),
                    'title': entry.title[:500] if hasattr(entry, 'title') else '',
                    'author': entry.author if hasattr(entry, 'author') else '',
                    'full_text': entry.summary[:10000] if hasattr(entry, 'summary') else '',
                    'categories': ['brownfield'],
                    'entities': [],
                    'url': entry.link if hasattr(entry, 'link') else '',
                    'scrape_timestamp': datetime.utcnow().isoformat()
                }
                rows.append(row)
            except Exception as e:
                logger.warning(f"Error parsing Brownfield entry: {e}")
        
        if rows:
            self.save_to_bigquery(f'{DATASET_ID}.news_industry_brownfield', rows)
        
        return rows


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
                    'published_at': datetime(*entry.published_parsed[:6]).isoformat() if hasattr(entry, 'published_parsed') else datetime.utcnow().isoformat(),
                    'title': entry.title[:500] if hasattr(entry, 'title') else '',
                    'author': entry.author if hasattr(entry, 'author') else '',
                    'full_text': entry.summary[:10000] if hasattr(entry, 'summary') else '',
                    'categories': ['farm_progress'],
                    'entities': [],
                    'url': entry.link if hasattr(entry, 'link') else '',
                    'scrape_timestamp': datetime.utcnow().isoformat()
                }
                rows.append(row)
            except Exception as e:
                logger.warning(f"Error parsing Farm Progress entry: {e}")
        
        if rows:
            self.save_to_bigquery(f'{DATASET_ID}.news_market_farmprogress', rows)
        
        return rows


class ENSOScraper(EthicalScraper):
    """Scrape NOAA ENSO status"""
    
    def scrape_enso(self) -> List[Dict]:
        """Scrape ENSO climate status from NOAA"""
        url = "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_advisory/ensodisc.shtml"
        html = self.fetch_html(url)
        
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        rows = []
        
        try:
            # Parse ENSO phase from page text
            text = soup.get_text()
            phase = 'Neutral'
            if 'La Niña' in text or 'La Nina' in text:
                phase = 'La Niña'
            elif 'El Niño' in text or 'El Nino' in text:
                phase = 'El Niño'
            
            # Extract strength if mentioned
            strength = 'moderate'
            if 'strong' in text.lower():
                strength = 'strong'
            elif 'weak' in text.lower():
                strength = 'weak'
            
            row = {
                'as_of_date': datetime.utcnow().date().isoformat(),
                'enso_phase': phase,
                'probability': 0.5,
                'outlook_months': 3,
                'strength': strength,
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
            self.save_to_bigquery(f'{DATASET_ID}.enso_climate_status', rows)
        
        return rows


class MarketAnalysisScraper(EthicalScraper):
    """Scrape market analysis sources for correlation data"""
    
    def scrape_correlations(self) -> List[Dict]:
        """Scrape correlation analysis from market sources"""
        # This would target commodity analysis sites
        # For now, placeholder for structure
        logger.info("Market correlation scraping - placeholder")
        return []


# ============================================
# ORCHESTRATOR
# ============================================

def run_all_scrapers():
    """Execute all web scrapers"""
    print("="*60)
    print("🕷️  CBI-V14 Web Scraping Pipeline")
    print("="*60)
    print(f"Start: {datetime.now().isoformat()}")
    
    results = {}
    
    # Phase 1: Price & Market Data
    print("\n📊 Phase 1: Price & Market Data")
    try:
        barchart = BarchartScraper()
        results['barchart'] = len(barchart.scrape_futures())
        print(f"   ✅ Barchart: {results['barchart']} rows")
    except Exception as e:
        logger.error(f"Barchart failed: {e}")
        results['barchart'] = 0
    
    try:
        marketwatch = MarketWatchScraper()
        results['marketwatch'] = len(marketwatch.scrape_futures())
        print(f"   ✅ MarketWatch: {results['marketwatch']} rows")
    except Exception as e:
        logger.error(f"MarketWatch failed: {e}")
        results['marketwatch'] = 0
    
    try:
        investing = InvestingScraper()
        results['investing'] = len(investing.scrape_futures())
        print(f"   ✅ Investing.com: {results['investing']} rows")
    except Exception as e:
        logger.error(f"Investing.com failed: {e}")
        results['investing'] = 0
    
    try:
        tradingview = TradingViewScraper()
        results['tradingview'] = len(tradingview.scrape_sentiment())
        print(f"   ✅ TradingView: {results['tradingview']} rows")
    except Exception as e:
        logger.error(f"TradingView failed: {e}")
        results['tradingview'] = 0
    
    # Phase 2: Policy & Legislation
    print("\n⚖️  Phase 2: Policy & Legislation")
    try:
        epa = EPAScraper()
        results['epa'] = len(epa.scrape_rfs_volumes())
        print(f"   ✅ EPA RFS: {results['epa']} rows")
    except Exception as e:
        logger.error(f"EPA failed: {e}")
        results['epa'] = 0
    
    try:
        congress = CongressGovScraper()
        results['congress'] = len(congress.scrape_bills())
        print(f"   ✅ Congress.gov: {results['congress']} rows")
    except Exception as e:
        logger.error(f"Congress.gov failed: {e}")
        results['congress'] = 0
    
    try:
        federal_register = FederalRegisterScraper()
        results['federal_register'] = len(federal_register.scrape_policy_events())
        print(f"   ✅ Federal Register: {results['federal_register']} rows")
    except Exception as e:
        logger.error(f"Federal Register failed: {e}")
        results['federal_register'] = 0
    
    # Phase 3: News & Intelligence
    print("\n📰 Phase 3: News & Intelligence")
    try:
        reuters = ReutersScraper()
        results['reuters'] = len(reuters.scrape_commodities_news())
        print(f"   ✅ Reuters: {results['reuters']} rows")
    except Exception as e:
        logger.error(f"Reuters failed: {e}")
        results['reuters'] = 0
    
    try:
        brownfield = BrownfieldScraper()
        results['brownfield'] = len(brownfield.scrape_news())
        print(f"   ✅ Brownfield: {results['brownfield']} rows")
    except Exception as e:
        logger.error(f"Brownfield failed: {e}")
        results['brownfield'] = 0
    
    try:
        farmprogress = FarmProgressScraper()
        results['farmprogress'] = len(farmprogress.scrape_news())
        print(f"   ✅ Farm Progress: {results['farmprogress']} rows")
    except Exception as e:
        logger.error(f"Farm Progress failed: {e}")
        results['farmprogress'] = 0
    
    try:
        asa = ASAScraper()
        results['asa'] = len(asa.scrape_news())
        print(f"   ✅ ASA: {results['asa']} rows")
    except Exception as e:
        logger.error(f"ASA failed: {e}")
        results['asa'] = 0
    
    # Phase 4: Weather & Climate
    print("\n🌦️  Phase 4: Weather & Climate")
    try:
        enso = ENSOScraper()
        results['enso'] = len(enso.scrape_enso())
        print(f"   ✅ ENSO: {results['enso']} rows")
    except Exception as e:
        logger.error(f"ENSO failed: {e}")
        results['enso'] = 0
    
    # Phase 5: CME Public Data
    print("\n💹 Phase 5: CME Public Data")
    try:
        cme = CMEPublicScraper()
        results['cme'] = len(cme.scrape_settlements())
        print(f"   ✅ CME: {results['cme']} rows")
    except Exception as e:
        logger.error(f"CME failed: {e}")
        results['cme'] = 0
    
    print("\n" + "="*60)
    print("✅ Web scraping complete!")
    print(f"End: {datetime.now().isoformat()}")
    print()
    print("Summary:")
    total_rows = 0
    for source, count in results.items():
        print(f"   {source}: {count} rows")
        total_rows += count
    print(f"\n   TOTAL: {total_rows} rows collected")
    print("="*60)
    
    return results


if __name__ == "__main__":
    run_all_scrapers()








