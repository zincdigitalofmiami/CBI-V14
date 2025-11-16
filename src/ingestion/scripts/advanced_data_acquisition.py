#!/usr/bin/env python3
'''
WARNING: This file has been cleaned of ALL fake data.
Any functions that relied on fake data have been disabled.
Must be rewritten to use REAL data from BigQuery or APIs.
ZERO TOLERANCE FOR FAKE DATA.
'''

#!/usr/bin/env python3
"""
ADVANCED DATA ACQUISITION SYSTEM WITH ANTI-DETECTION
Implements browser fingerprinting, throttling, fallbacks, and multiple extraction strategies
"""

import requests
from datetime import datetime, timedelta
import json
import time
# REMOVED: import random # NO FAKE DATA
import numpy as np
from google.cloud import bigquery
import pandas as pd
from bs4 import BeautifulSoup
import feedparser
import concurrent.futures
from typing import List, Dict, Any, Tuple, Optional
import re
import hashlib
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

print(f"ADVANCED DATA ACQUISITION SYSTEM - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# CONFIGURATION
CUTOFF_DATE = datetime.now() - timedelta(days=30)
MAX_RETRIES = 3
MIN_DELAY = 0.5
MAX_DELAY = 5.0

# BROWSER FINGERPRINT ROTATION
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

ACCEPT_LANGUAGES = [
    'en-US,en;q=0.9',
    'en-GB,en;q=0.9',
    'en-US,en;q=0.9,zh-CN;q=0.8',
]

SCREEN_RESOLUTIONS = [
    {'width': 1920, 'height': 1080},
    {'width': 1366, 'height': 768},
    {'width': 1440, 'height': 900},
    {'width': 2560, 'height': 1440},
]

class SmartSession:
    """Session with advanced anti-detection and throttling"""
    
    def __init__(self, source_type: str = 'standard'):
        self.session = requests.Session()
        self.source_type = source_type
        self.request_count = 0
        self.start_time = time.time()
        
        # Setup retry strategy
        retry_strategy = Retry(
            total=MAX_RETRIES,
# REMOVED:             backoff_factor=random.uniform(1, 3), # NO FAKE DATA
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def get_random_headers(self) -> Dict[str, str]:
        """Generate randomized headers"""
# REMOVED:         resolution = random.choice(SCREEN_RESOLUTIONS) # NO FAKE DATA
        
        return {
# REMOVED:             'User-Agent': random.choice(USER_AGENTS), # NO FAKE DATA
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
# REMOVED:             'Accept-Language': random.choice(ACCEPT_LANGUAGES), # NO FAKE DATA
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
# REMOVED:             'DNT': random.choice(['1', '0']), # NO FAKE DATA
# REMOVED:             'Referer': random.choice([ # NO FAKE DATA
                'https://www.google.com/',
                'https://www.bing.com/',
                'https://www.duckduckgo.com/',
            ])
        }
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """Smart GET with throttling and randomization"""
        # Throttle based on source type
        if self.source_type == 'premium':
# REMOVED:             delay = random.uniform(3, 10) # NO FAKE DATA
        elif self.source_type == 'sensitive':
# REMOVED:             delay = random.uniform(5, 15) # NO FAKE DATA
        elif self.source_type == 'standard':
# REMOVED:             delay = random.uniform(0.5, 2) # NO FAKE DATA
        else:
# REMOVED:             delay = random.uniform(0.3, 1) # NO FAKE DATA
        
        # Exponential backoff if too many requests
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            rate = self.request_count / elapsed
            if rate > 10:  # More than 10 requests per second
                delay *= 2
        
        time.sleep(delay)
        
        # Add headers
        headers = kwargs.get('headers', {})
        headers.update(self.get_random_headers())
        kwargs['headers'] = headers
        
        # Add timeout
        kwargs['timeout'] = kwargs.get('timeout', 15)
        
        self.request_count += 1
        response = self.session.get(url, **kwargs)
        
        return response
    
    def close(self):
        """Close session"""
        self.session.close()

# SOURCE CONFIGURATION WITH FALLBACKS
SOURCES = {
    # PRIMARY DATA SOURCES
    'primary_vegetable_oil': {
        'weight': 0.15,
        'sources': [
            ('https://www.thejacobsen.com/feed', 'The Jacobsen', 'premium', []),
            ('https://www.oilworld.biz/feed', 'Oil World', 'premium', []),
            ('https://www.icis.com/rss', 'ICIS Vegetable Oils', 'premium', []),
            ('https://www.mintecglobal.com/feed', 'Mintec Global', 'standard', []),
            ('https://www.agrimoney.com/rss', 'Agrimoney', 'standard', []),
        ]
    },
    
    # POLITICAL/REGULATORY
    'political_lobbying': {
        'weight': 0.10,
        'sources': [
            ('https://www.opensecrets.org/rss/news.xml', 'OpenSecrets', 'standard', []),
            ('https://www.followthemoney.org/feed', 'Follow The Money', 'standard', []),
            ('https://www.goodjobsfirst.org/feed', 'Good Jobs First', 'standard', []),
        ]
    },
    
    # FINANCIAL NEWS
    'financial_news': {
        'weight': 0.10,
        'sources': [
            ('https://feeds.bloomberg.com/markets/news.rss', 'Bloomberg', 'premium', []),
            ('https://www.reuters.com/markets/commodities/rss', 'Reuters', 'sensitive', []),
            ('https://www.ft.com/commodities?format=rss', 'Financial Times', 'premium', []),
            ('https://www.wsj.com/xml/rss/3_7031.xml', 'WSJ', 'premium', []),
        ]
    },
    
    # AGRICULTURAL NEWS
    'agricultural_news': {
        'weight': 0.10,
        'sources': [
            ('https://www.agweb.com/rss/news', 'AgWeb', 'standard', []),
            ('https://www.agriculture.com/rss/news', 'Agriculture.com', 'standard', []),
            ('https://www.farmprogress.com/rss.xml', 'Farm Progress', 'standard', []),
            ('https://brownfieldagnews.com/feed/', 'Brownfield Ag', 'standard', []),
            ('https://www.agfax.com/feed/', 'AgFax', 'standard', []),
        ]
    },
    
    # INTERNATIONAL
    'international_sources': {
        'weight': 0.08,
        'sources': [
            ('https://www.scmp.com/rss/91/feed', 'South China Morning Post', 'sensitive', []),
            ('https://en.mercopress.com/rss/agriculture', 'MercoPress Argentina', 'standard', []),
            ('https://www.reuters.com/places/brazil/rss', 'Reuters Brazil', 'sensitive', []),
            ('https://www.caixinglobal.com/rss', 'Caixin China', 'sensitive', []),
        ]
    },
    
    # SOCIAL/REDDIT
    'social_reddit': {
        'weight': 0.05,
        'sources': [
            ('https://www.reddit.com/r/commodities.rss', 'Reddit Commodities', 'standard', []),
            ('https://www.reddit.com/r/farming.rss', 'Reddit Farming', 'standard', []),
            ('https://www.reddit.com/r/agriculture.rss', 'Reddit Agriculture', 'standard', []),
        ]
    },
}

# KEYWORD TRACKING
CORRELATION_KEYWORDS = {
    'soybean_oil': ['soybean oil', 'bean oil', 'soy oil', 'vegetable oil', 'ZL futures'],
    'tariffs': ['tariff', 'trade war', 'customs', 'duty', 'import tax'],
    'china': ['china', 'chinese', 'beijing', 'shanghai', 'yuan'],
    'brazil': ['brazil', 'brazilian', 'real', 'mato grosso', 'bolsonaro', 'lula'],
    'legislation': ['congress', 'senate', 'bill', 'law', 'regulation', 'policy'],
    'lobbying': ['lobby', 'lobbying', 'advocate', 'pac', 'donation'],
    'weather': ['drought', 'flood', 'rain', 'weather', 'climate'],
    'biofuel': ['biodiesel', 'ethanol', 'renewable', 'biofuel', 'rfs'],
}

def extract_with_multiple_strategies(content: str, source_type: str) -> str:
    """Try multiple extraction strategies"""
    soup = BeautifulSoup(content, 'html.parser')
    
    # Remove unwanted elements
    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript']):
        element.decompose()
    
    # Strategy 1: Standard article selectors
    selectors = [
        'article',
        '[class*="article"]',
        '[class*="content"]',
        '[class*="story"]',
        'main',
        '.entry-content',
        '[itemprop="articleBody"]',
        '#content',
        '.post-content',
        'div.story-body',
    ]
    
    extracted = ''
    for selector in selectors:
        elements = soup.select(selector)
        if elements:
            text = ' '.join([elem.get_text(separator=' ', strip=True) for elem in elements])
            if len(text) > len(extracted):
                extracted = text
    
    # Strategy 2: If that fails, get all paragraphs
    if len(extracted) < 500:
        paragraphs = soup.find_all(['p', 'div'])
        extracted = ' '.join([p.get_text(strip=True) for p in paragraphs[:100]])
    
    # Strategy 3: If still insufficient, get all text
    if len(extracted) < 500:
        extracted = soup.get_text(separator=' ', strip=True)
    
    # Extract key data points
    prices = re.findall(r'\$(\d+\.?\d*)', extracted)
    percentages = re.findall(r'(\d+\.?\d*)%', extracted)
    
    if prices:
        extracted += f" PRICES_FOUND: {','.join(prices[:10])}"
    if percentages:
        extracted += f" PERCENTAGES_FOUND: {','.join(percentages[:10])}"
    
    return extracted[:15000]

def calculate_relevance(content: str, title: str, source_weight: float) -> Tuple[float, Dict]:
    """Calculate relevance score"""
    combined = (title + ' ' + content).lower()
    
    scores = {}
    total = 0
    
    for category, keywords in CORRELATION_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in combined)
        weight = 3 if category in ['soybean_oil', 'tariffs', 'china'] else 1
        score = matches * weight
        scores[f'{category}_mentions'] = matches
        total += score
    
    final_score = total * source_weight
    
    if scores.get('soybean_oil_mentions', 0) > 0:
        relevance = 'critical'
    elif total > 10:
        relevance = 'high'
    elif total > 5:
        relevance = 'medium'
    else:
        relevance = 'low'
    
    return final_score, {**scores, 'total_score': final_score, 'relevance': relevance}

def acquire_data_with_fallback(url: str, source_name: str, source_type: str, fallbacks: List[str]) -> Optional[Dict]:
    """Acquire data with fallback strategies"""
    session = SmartSession(source_type)
    
    # Try primary URL
    try:
        logger.info(f"  Attempting {source_name}...")
        response = session.get(url)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.text)
            
            if feed.entries:
                logger.info(f"  ✓ Successfully got {len(feed.entries)} entries from {source_name}")
                return {'feed': feed, 'url': url, 'success': True}
            
    except Exception as e:
        logger.warning(f"  ✗ Primary URL failed for {source_name}: {str(e)[:50]}")
    
    # Try fallback URLs
    for fallback_url in fallbacks:
        try:
            logger.info(f"  Trying fallback for {source_name}...")
            response = session.get(fallback_url)
            
            if response.status_code == 200:
                feed = feedparser.parse(response.text)
                
                if feed.entries:
                    logger.info(f"  ✓ Fallback succeeded for {source_name}")
                    return {'feed': feed, 'url': fallback_url, 'success': True}
                    
        except Exception as e:
            logger.warning(f"  ✗ Fallback failed: {str(e)[:50]}")
    
    # Try RSS feed alternatives
    rss_variants = [
        url.replace('feed', 'rss'),
        url.replace('feed', 'atom'),
        url + '/feed',
        url + '/rss',
    ]
    
    for variant in rss_variants:
        try:
            if variant == url:
                continue
                
            response = session.get(variant)
            
            if response.status_code == 200:
                feed = feedparser.parse(response.text)
                
                if feed.entries:
                    logger.info(f"  ✓ RSS variant succeeded for {source_name}")
                    return {'feed': feed, 'url': variant, 'success': True}
                    
        except:
            pass
    
    session.close()
    logger.error(f"  ✗ All attempts failed for {source_name}")
    return None

def process_source(source_data: Tuple[str, str, str, List[str]]) -> List[Dict]:
    """Process a single source"""
    url, source_name, source_type, fallbacks = source_data
    articles = []
    
    result = acquire_data_with_fallback(url, source_name, source_type, fallbacks)
    
    if not result or not result['success']:
        return articles
    
    feed = result['feed']
    
    for entry in feed.entries[:30]:
        try:
            # Check date
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6])
                if pub_date < CUTOFF_DATE:
                    continue
            else:
                pub_date = datetime.now()
            
            # Create article
            article = {
                'source': source_name,
                'source_type': source_type,
                'title': entry.get('title', ''),
                'url': entry.get('link', ''),
                'published_date': pub_date,
                'summary': entry.get('summary', '')[:1000]
            }
            
            # Extract full content
            if article['url']:
                try:
                    session = SmartSession(source_type)
                    response = session.get(article['url'])
                    full_content = extract_with_multiple_strategies(response.text, source_type)
                    session.close()
                except:
                    full_content = article['summary']
                
                article['full_content'] = full_content
                article['content_length'] = len(full_content)
            else:
                article['full_content'] = article['summary']
                article['content_length'] = len(article['summary'])
            
            # Get source weight
            weight = 0.1  # Default weight
            
            # Calculate relevance
            score, keyword_data = calculate_relevance(
                article['full_content'],
                article['title'],
                weight
            )
            article.update(keyword_data)
            
            # Generate ID
            article['article_id'] = hashlib.md5(
                f"{article['url']}{article['title']}".encode()
            ).hexdigest()
            
            articles.append(article)
            
        except Exception as e:
            logger.warning(f"Error processing article: {str(e)[:50]}")
    
    logger.info(f"  Collected {len(articles)} articles from {source_name}")
    return articles

# MAIN EXECUTION
print("\nStarting comprehensive data collection...")
print("-"*80)

all_articles = []

# Process all sources
for category_name, config in SOURCES.items():
    print(f"\nProcessing {category_name}...")
    
    sources = config['sources']
    
    for source_data in sources:
        articles = process_source(source_data)
        all_articles.extend(articles)
        
        # Small delay between sources
# REMOVED:         time.sleep(random.uniform(0.5, 1.5)) # NO FAKE DATA

print(f"\nTOTAL ARTICLES COLLECTED: {len(all_articles)}")

# SAVE TO BIGQUERY
if all_articles:
    df = pd.DataFrame(all_articles)
    df = df[df['content_length'] > 100]
    df = df.sort_values('total_score', ascending=False)
    
    print("\n" + "="*80)
    print("SAVING TO BIGQUERY")
    print("="*80)
    
    df['ingested_at'] = datetime.now()
    df['published_date'] = pd.to_datetime(df['published_date'])
    
    table_id = "cbi-v14.forecasting_data_warehouse.news_advanced"
    
    try:
        job = client.load_table_from_dataframe(
            df,
            table_id,
            job_config=bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND",
                schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION]
            )
        )
        job.result()
        print(f"✓ Saved {len(df)} articles to {table_id}")
        
    except Exception as e:
        print(f"Error: {str(e)[:200]}")

print("\n" + "="*80)
print("ACQUISITION COMPLETE")
print("="*80)
