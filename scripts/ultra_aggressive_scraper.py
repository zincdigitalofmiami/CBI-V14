#!/usr/bin/env python3
"""
ULTRA-AGGRESSIVE DATA ACQUISITION SYSTEM
Combines RSS feeds + direct page scraping + site crawling
"""

import requests
from datetime import datetime, timedelta
import json
import time
import random
from google.cloud import bigquery
import pandas as pd
from bs4 import BeautifulSoup
import feedparser
import concurrent.futures
from typing import List, Dict, Any, Tuple, Optional
import re
import hashlib
import urllib.parse
from urllib.robotparser import RobotFileParser

client = bigquery.Client(project='cbi-v14')

print(f"ULTRA-AGGRESSIVE DATA ACQUISITION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

CUTOFF_DATE = datetime.now() - timedelta(days=30)

# COMPREHENSIVE SOURCE LIST WITH MULTIPLE ACCESS PATHS
SOURCES = [
    # VEGETABLE OIL & SPECIALIZED
    {
        'name': 'The Jacobsen',
        'rss': 'https://www.thejacobsen.com/feed',
        'base_url': 'https://www.thejacobsen.com',
        'article_pattern': '/news/',
        'extraction': 'premium'
    },
    {
        'name': 'Oil World',
        'rss': 'https://www.oilworld.biz/feed',
        'base_url': 'https://www.oilworld.biz',
        'article_pattern': '/news/',
        'extraction': 'premium'
    },
    {
        'name': 'ICIS',
        'rss': 'https://www.icis.com/chemicals/feed',
        'base_url': 'https://www.icis.com',
        'article_pattern': '/news/',
        'extraction': 'premium'
    },
    
    # BIOFUEL SOURCES
    {
        'name': 'Biodiesel Magazine',
        'rss': 'http://biodieselmagazine.com/rss',
        'base_url': 'http://biodieselmagazine.com',
        'article_pattern': '/articles/',
        'extraction': 'standard'
    },
    {
        'name': 'Ethanol Producer',
        'rss': 'https://ethanolproducer.com/rss',
        'base_url': 'https://ethanolproducer.com',
        'article_pattern': '/articles/',
        'extraction': 'standard'
    },
    
    # AGRICULTURAL NEWS
    {
        'name': 'AgWeb',
        'rss': 'https://www.agweb.com/rss/news',
        'base_url': 'https://www.agweb.com',
        'article_pattern': '/news/',
        'extraction': 'standard'
    },
    {
        'name': 'Farm Progress',
        'rss': 'https://www.farmprogress.com/rss.xml',
        'base_url': 'https://www.farmprogress.com',
        'article_pattern': '/news/',
        'extraction': 'standard'
    },
    {
        'name': 'Brownfield Ag',
        'rss': 'https://brownfieldagnews.com/feed/',
        'base_url': 'https://brownfieldagnews.com',
        'article_pattern': '/news/',
        'extraction': 'standard'
    },
    {
        'name': 'DTN Progressive Farmer',
        'rss': 'https://www.dtnpf.com/agriculture/web/ag/rss',
        'base_url': 'https://www.dtnpf.com',
        'article_pattern': '/agriculture/',
        'extraction': 'standard'
    },
    
    # FINANCIAL NEWS
    {
        'name': 'Reuters Commodities',
        'rss': 'https://www.reuters.com/markets/commodities/rss',
        'base_url': 'https://www.reuters.com',
        'article_pattern': '/markets/commodities/',
        'extraction': 'sensitive'
    },
    {
        'name': 'Bloomberg Markets',
        'rss': 'https://feeds.bloomberg.com/markets/news.rss',
        'base_url': 'https://www.bloomberg.com',
        'article_pattern': '/markets/',
        'extraction': 'premium'
    },
    
    # TRADE & POLICY
    {
        'name': 'OpenSecrets',
        'rss': 'https://www.opensecrets.org/rss/news.xml',
        'base_url': 'https://www.opensecrets.org',
        'article_pattern': '/news/',
        'extraction': 'standard'
    },
    {
        'name': 'Politico Agriculture',
        'rss': 'https://www.politico.com/rss/agriculture.xml',
        'base_url': 'https://www.politico.com',
        'article_pattern': '/agriculture/',
        'extraction': 'standard'
    },
    
    # INTERNATIONAL
    {
        'name': 'South China Morning Post',
        'rss': 'https://www.scmp.com/rss/91/feed',
        'base_url': 'https://www.scmp.com',
        'article_pattern': '/economy/',
        'extraction': 'sensitive'
    },
    {
        'name': 'MercoPress Argentina',
        'rss': 'https://en.mercopress.com/rss/agriculture',
        'base_url': 'https://en.mercopress.com',
        'article_pattern': '/agriculture/',
        'extraction': 'standard'
    },
]

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
]

def get_random_headers():
    """Randomized headers"""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
    }

def scrape_site_directory(base_url: str, article_pattern: str, max_pages: int = 20) -> List[str]:
    """Crawl site to find article URLs"""
    article_urls = []
    
    try:
        # Try common page patterns
        for i in range(1, max_pages + 1):
            urls_to_try = [
                f"{base_url}{article_pattern}?page={i}",
                f"{base_url}{article_pattern}page/{i}",
                f"{base_url}{article_pattern}page={i}",
                f"{base_url}{article_pattern}{i}",
            ]
            
            for url in urls_to_try:
                try:
                    time.sleep(random.uniform(1, 3))
                    response = requests.get(url, headers=get_random_headers(), timeout=10)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Find article links
                        links = soup.find_all('a', href=True)
                        for link in links:
                            href = link.get('href', '')
                            if article_pattern in href and href not in article_urls:
                                # Convert relative to absolute
                                if href.startswith('/'):
                                    full_url = base_url + href
                                elif href.startswith('http'):
                                    full_url = href
                                else:
                                    full_url = base_url + '/' + href
                                
                                article_urls.append(full_url)
                        
                        if len(article_urls) > 50:
                            break
                            
                except:
                    continue
            
            if len(article_urls) > 50:
                break
                
    except Exception as e:
        pass
    
    return article_urls[:50]  # Limit to 50 articles

def extract_article_content(url: str, extraction_type: str) -> Dict:
    """Extract full article content"""
    try:
        time.sleep(random.uniform(0.5, 2))
        response = requests.get(url, headers=get_random_headers(), timeout=10)
        
        if response.status_code != 200:
            return {'content': '', 'success': False}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript']):
            element.decompose()
        
        # Try multiple extraction strategies
        content = ''
        
        # Strategy 1: Look for article tags
        article_tags = soup.find_all('article')
        if article_tags:
            content = ' '.join([tag.get_text(strip=True) for tag in article_tags])
        
        # Strategy 2: Look for common content classes
        if len(content) < 500:
            selectors = [
                '[class*="article"]',
                '[class*="content"]',
                '[class*="story"]',
                '[class*="post"]',
                '[class*="entry"]',
                'main',
                '.entry-content',
                '.post-content',
                '#content',
                '[itemprop="articleBody"]',
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    text = ' '.join([elem.get_text(strip=True) for elem in elements])
                    if len(text) > len(content):
                        content = text
        
        # Strategy 3: Get all paragraphs
        if len(content) < 500:
            paragraphs = soup.find_all(['p', 'div'])
            content = ' '.join([p.get_text(strip=True) for p in paragraphs[:100]])
        
        # Strategy 4: Fallback to all text
        if len(content) < 500:
            content = soup.get_text(strip=True)
        
        # Extract metadata
        title_elem = soup.find('title')
        title = title_elem.get_text(strip=True) if title_elem else ''
        
        # Try to find date
        pub_date = None
        date_patterns = [
            ('time', {'datetime': True}),
            ('time', {'pubdate': True}),
            ('meta', {'property': 'article:published_time'}),
            ('meta', {'name': 'date'}),
            ('span', {'class': re.compile('date', re.I)}),
        ]
        
        for tag_name, attrs in date_patterns:
            elements = soup.find_all(tag_name, attrs)
            for elem in elements:
                date_str = elem.get('datetime') or elem.get('content') or elem.get_text()
                if date_str:
                    try:
                        pub_date = datetime.strptime(date_str[:10], '%Y-%m-%d')
                        break
                    except:
                        pass
            if pub_date:
                break
        
        if not pub_date:
            pub_date = datetime.now()
        
        # Extract data points
        prices = re.findall(r'\$(\d+\.?\d*)', content)
        percentages = re.findall(r'(\d+\.?\d*)%', content)
        volumes = re.findall(r'(\d+[,\d]*\s*(?:tons?|bushels?|gallons?|barrels?))', content, re.I)
        
        # Add extracted data
        if prices:
            content += f" PRICES_FOUND: {','.join(prices[:10])}"
        if percentages:
            content += f" PERCENTAGES_FOUND: {','.join(percentages[:10])}"
        if volumes:
            content += f" VOLUMES_FOUND: {','.join(volumes[:5])}"
        
        return {
            'content': content[:15000],
            'title': title,
            'published_date': pub_date,
            'success': True
        }
        
    except Exception as e:
        return {'content': f'Error: {str(e)[:100]}', 'success': False}

def process_source(source: Dict) -> List[Dict]:
    """Process a single source using multiple strategies"""
    articles = []
    
    print(f"\n{'='*80}")
    print(f"PROCESSING: {source['name']}")
    print(f"{'='*80}")
    
    # STRATEGY 1: RSS Feed
    print(f"Strategy 1: RSS Feed")
    try:
        time.sleep(random.uniform(1, 3))
        feed = feedparser.parse(source['rss'])
        
        if feed.entries:
            print(f"  ✓ Found {len(feed.entries)} RSS entries")
            
            for entry in feed.entries[:30]:
                try:
                    # Check date
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                        if pub_date < CUTOFF_DATE:
                            continue
                    else:
                        pub_date = datetime.now()
                    
                    # Get article URL
                    url = entry.get('link', '')
                    
                    # Extract content
                    result = extract_article_content(url, source['extraction'])
                    
                    article = {
                        'source': source['name'],
                        'title': entry.get('title', '') or result.get('title', ''),
                        'url': url,
                        'published_date': result.get('published_date', pub_date),
                        'summary': entry.get('summary', '')[:500],
                        'full_content': result['content'],
                        'content_length': len(result['content']),
                        'content_source': 'rss'
                    }
                    
                    if article['content_length'] > 200:
                        articles.append(article)
                        
                except Exception as e:
                    print(f"    Error processing article: {str(e)[:50]}")
        else:
            print(f"  ✗ RSS feed empty")
            
    except Exception as e:
        print(f"  ✗ RSS feed failed: {str(e)[:50]}")
    
    # STRATEGY 2: Direct Site Scraping
    print(f"\nStrategy 2: Direct Site Scraping")
    try:
        article_urls = scrape_site_directory(
            source['base_url'],
            source['article_pattern'],
            max_pages=10
        )
        
        print(f"  Found {len(article_urls)} potential article URLs")
        
        for url in article_urls[:20]:  # Limit to 20
            try:
                result = extract_article_content(url, source['extraction'])
                
                if result['success'] and len(result['content']) > 500:
                    # Check if already exists
                    if not any(a['url'] == url for a in articles):
                        article = {
                            'source': source['name'],
                            'title': result['title'],
                            'url': url,
                            'published_date': result['published_date'],
                            'summary': result['content'][:500],
                            'full_content': result['content'],
                            'content_length': len(result['content']),
                            'content_source': 'direct_scrape'
                        }
                        
                        articles.append(article)
                        
            except Exception as e:
                pass
                
    except Exception as e:
        print(f"  ✗ Direct scraping failed: {str(e)[:50]}")
    
    # STRATEGY 3: Search-Based Discovery
    print(f"\nStrategy 3: Search-Based Discovery")
    try:
        search_terms = ['soybean', 'vegetable oil', 'commodity', 'trade', 'tariff']
        
        for term in search_terms[:3]:  # Limit to 3 searches
            try:
                # Try common search patterns
                search_urls = [
                    f"{source['base_url']}/search?q={term}",
                    f"{source['base_url']}/search/?q={term}",
                    f"{source['base_url']}/?s={term}",
                ]
                
                for search_url in search_urls:
                    try:
                        time.sleep(random.uniform(2, 4))
                        response = requests.get(search_url, headers=get_random_headers(), timeout=10)
                        
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.content, 'html.parser')
                            
                            # Find article links in search results
                            links = soup.find_all('a', href=True)
                            for link in links:
                                href = link.get('href', '')
                                
                                if source['article_pattern'] in href:
                                    if href.startswith('/'):
                                        full_url = source['base_url'] + href
                                    elif href.startswith('http'):
                                        full_url = href
                                    else:
                                        continue
                                    
                                    # Check if already exists
                                    if not any(a['url'] == full_url for a in articles):
                                        result = extract_article_content(full_url, source['extraction'])
                                        
                                        if result['success'] and len(result['content']) > 500:
                                            article = {
                                                'source': source['name'],
                                                'title': result['title'],
                                                'url': full_url,
                                                'published_date': result['published_date'],
                                                'summary': result['content'][:500],
                                                'full_content': result['content'],
                                                'content_length': len(result['content']),
                                                'content_source': 'search'
                                            }
                                            
                                            articles.append(article)
                                            
                                            if len(articles) > 50:
                                                break
                                    
                                    if len(articles) > 50:
                                        break
                        else:
                            break
                            
                    except:
                        continue
                        
            except:
                continue
                
    except Exception as e:
        print(f"  ✗ Search failed: {str(e)[:50]}")
    
    # Calculate relevance scores
    for article in articles:
        # Keywords
        keywords = {
            'soybean_oil': ['soybean oil', 'bean oil', 'soy oil', 'vegetable oil', 'ZL futures'],
            'tariffs': ['tariff', 'trade war', 'customs', 'duty'],
            'china': ['china', 'chinese', 'beijing'],
            'brazil': ['brazil', 'brazilian', 'real'],
            'legislation': ['congress', 'senate', 'bill', 'law'],
        }
        
        combined = (article['title'] + ' ' + article['full_content']).lower()
        
        scores = {}
        total = 0
        
        for category, terms in keywords.items():
            matches = sum(1 for term in terms if term in combined)
            scores[f'{category}_mentions'] = matches
            total += matches * (3 if category in ['soybean_oil', 'tariffs'] else 1)
        
        article['total_score'] = total
        article['relevance'] = 'critical' if scores.get('soybean_oil_mentions', 0) > 0 else \
                               'high' if total > 10 else 'medium' if total > 5 else 'low'
        article.update(scores)
        
        # Generate ID
        article['article_id'] = hashlib.md5(
            f"{article['url']}{article['title']}".encode()
        ).hexdigest()
    
    print(f"\n✓ Collected {len(articles)} articles from {source['name']}")
    
    return articles

# MAIN EXECUTION
print("\n" + "="*80)
print("ULTRA-AGGRESSIVE DATA COLLECTION")
print("="*80)

all_articles = []

# Process all sources
for source in SOURCES:
    try:
        articles = process_source(source)
        all_articles.extend(articles)
        
        # Delay between sources
        time.sleep(random.uniform(2, 5))
        
    except Exception as e:
        print(f"ERROR processing {source['name']}: {str(e)[:100]}")

print(f"\n{'='*80}")
print(f"TOTAL ARTICLES COLLECTED: {len(all_articles)}")
print(f"{'='*80}")

# SAVE TO BIGQUERY
if all_articles:
    df = pd.DataFrame(all_articles)
    df = df[df['content_length'] > 200]
    df = df.sort_values('total_score', ascending=False)
    
    print("\n" + "="*80)
    print("SAVING TO BIGQUERY")
    print("="*80)
    
    df['ingested_at'] = datetime.now()
    df['published_date'] = pd.to_datetime(df['published_date'])
    
    table_id = "cbi-v14.forecasting_data_warehouse.news_ultra_aggressive"
    
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
        
        # Show stats
        print("\nData Quality:")
        print(f"  Total articles: {len(df)}")
        print(f"  Avg content length: {df['content_length'].mean():.0f} chars")
        print(f"  Relevance distribution:")
        print(df['relevance'].value_counts().to_string())
        
    except Exception as e:
        print(f"Error: {str(e)[:200]}")

print("\n" + "="*80)
print("ACQUISITION COMPLETE")
print("="*80)
