#!/usr/bin/env python3
"""
MASSIVE DATA ACQUISITION - ALL SOURCES, RECENT DATA ONLY
Pull from existing feeds + new sources with FULL CONTENT
Focus on correlations: tariffs, China, Brazil, Argentina, legislation, lobbying
"""

import requests
from datetime import datetime, timedelta
import json
import time
from google.cloud import bigquery
import pandas as pd
from bs4 import BeautifulSoup
import feedparser
import concurrent.futures
from typing import List, Dict, Any

client = bigquery.Client(project='cbi-v14')

print(f"MASSIVE MULTI-SOURCE DATA ACQUISITION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)
print("PULLING FROM ALL SOURCES - 10 ARTICLES/SECOND TARGET")
print("="*80)

# Date cutoff - nothing older than 1 month
CUTOFF_DATE = datetime.now() - timedelta(days=30)

# COMPREHENSIVE SOURCE LIST
SOURCES = {
    'financial_news': [
        ('https://feeds.bloomberg.com/markets/news.rss', 'Bloomberg Markets'),
        ('https://www.reuters.com/markets/commodities/rss', 'Reuters Commodities'),
        ('https://feeds.ft.com/markets/commodities.rss', 'Financial Times'),
        ('https://www.wsj.com/xml/rss/3_7031.xml', 'WSJ Markets'),
        ('https://www.marketwatch.com/rss/realtimeheadlines', 'MarketWatch'),
    ],
    
    'agriculture_specific': [
        ('https://www.agweb.com/rss/news', 'AgWeb'),
        ('https://www.agriculture.com/rss/news', 'Agriculture.com'),
        ('https://www.farmprogress.com/rss.xml', 'Farm Progress'),
        ('https://www.dtnpf.com/agriculture/web/ag/rss', 'DTN Progressive Farmer'),
        ('https://brownfieldagnews.com/feed/', 'Brownfield Ag'),
    ],
    
    'trade_intelligence': [
        ('https://www.barchart.com/feed/rss', 'Barchart'),
        ('https://seekingalpha.com/feed.xml', 'Seeking Alpha'),
        ('https://www.agfax.com/feed/', 'AgFax'),
        ('https://www.oilworld.biz/feed', 'Oil World'),
    ],
    
    'international': [
        ('https://www.scmp.com/rss/91/feed', 'South China Morning Post'),
        ('https://en.mercopress.com/rss/agriculture', 'MercoPress Argentina'),
        ('https://agenciadenoticias.ibge.gov.br/en/rss', 'Brazil IBGE'),
        ('https://www.agricensus.com/feed.xml', 'AgriCensus'),
    ],
    
    'policy_lobbying': [
        ('https://www.opensecrets.org/rss/news.xml', 'OpenSecrets'),
        ('https://www.politico.com/rss/agriculture.xml', 'Politico Agriculture'),
        ('https://www.law360.com/agriculture/rss', 'Law360 Agriculture'),
    ],
    
    'correlated_markets': [
        ('https://rbnenergy.com/rss', 'RBN Energy'),
        ('http://biodieselmagazine.com/rss', 'Biodiesel Magazine'),
        ('https://www.eia.gov/rss/todayinenergy.xml', 'EIA Energy'),
    ]
}

# Keywords for correlation analysis
CORRELATION_KEYWORDS = {
    'tariffs': ['tariff', 'trade war', 'customs', 'duty', 'import tax', 'export tax'],
    'china': ['china', 'chinese', 'beijing', 'shanghai', 'yuan', 'xi jinping'],
    'brazil': ['brazil', 'brazilian', 'real', 'mato grosso', 'parana', 'bolsonaro', 'lula'],
    'argentina': ['argentina', 'argentine', 'peso', 'buenos aires', 'rosario', 'milei'],
    'legislation': ['congress', 'senate', 'bill', 'law', 'regulation', 'policy', 'act'],
    'lobbying': ['lobby', 'lobbying', 'advocate', 'influence', 'donation', 'pac'],
    'biofuel': ['biodiesel', 'ethanol', 'renewable', 'biofuel', 'rfs', 'renewable fuel'],
    'palm_oil': ['palm oil', 'malaysia', 'indonesia', 'vegetable oil', 'substitution'],
    'weather': ['drought', 'flood', 'rain', 'weather', 'climate', 'el nino', 'la nina'],
    'usda': ['usda', 'wasde', 'crop report', 'export sales', 'commitment'],
    'soybean': ['soybean', 'soy', 'crush', 'meal', 'oil', 'oilseed'],
    'energy': ['crude', 'oil', 'petroleum', 'energy', 'wti', 'brent'],
    'currency': ['dollar', 'usd', 'forex', 'exchange rate', 'currency'],
    'shipping': ['freight', 'shipping', 'vessel', 'export', 'import', 'port']
}

def extract_full_content(url: str, timeout: int = 5) -> str:
    """Aggressively extract full article content"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Try multiple content selectors
        content = ''
        selectors = [
            'article',
            '[class*="article"]',
            '[class*="content"]',
            '[class*="story"]',
            'main',
            '[role="main"]',
            '.post-content',
            '#content',
            '[itemprop="articleBody"]',
            '.entry-content'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                text = ' '.join([elem.get_text(separator=' ', strip=True) for elem in elements])
                if len(text) > len(content):
                    content = text
        
        # Fallback to all paragraphs
        if len(content) < 500:
            paragraphs = soup.find_all(['p', 'div'])
            content = ' '.join([p.get_text(strip=True) for p in paragraphs[:50]])
        
        return content[:10000]  # Limit to 10k chars
        
    except Exception as e:
        return f"Error extracting: {str(e)[:50]}"

def analyze_correlations(content: str, title: str = '') -> Dict[str, Any]:
    """Analyze content for all correlation signals"""
    combined = (title + ' ' + content).lower()
    
    correlations = {}
    total_score = 0
    
    for category, keywords in CORRELATION_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in combined)
        correlations[f'{category}_mentions'] = matches
        total_score += matches * (2 if category in ['tariffs', 'china', 'soybean'] else 1)
    
    # Determine primary topic
    max_category = max(correlations, key=correlations.get)
    primary_topic = max_category.replace('_mentions', '') if correlations[max_category] > 0 else 'general'
    
    return {
        **correlations,
        'correlation_score': total_score,
        'primary_topic': primary_topic
    }

def extract_sentiment(content: str) -> float:
    """Extract market sentiment from content"""
    positive = ['bullish', 'rise', 'gain', 'increase', 'strong', 'surge', 'rally', 
                'record high', 'optimistic', 'growth', 'expand', 'improve']
    negative = ['bearish', 'fall', 'drop', 'decrease', 'weak', 'plunge', 'decline',
                'record low', 'pessimistic', 'shrink', 'worsen', 'crisis']
    
    content_lower = content.lower()
    pos_score = sum(2 if word in content_lower else 0 for word in positive)
    neg_score = sum(2 if word in content_lower else 0 for word in negative)
    
    if pos_score > neg_score:
        return min(1.0, pos_score * 0.1)
    elif neg_score > pos_score:
        return max(-1.0, -neg_score * 0.1)
    return 0.0

def process_feed_parallel(feed_info: tuple) -> List[Dict]:
    """Process a single feed and return articles"""
    feed_url, source_name = feed_info
    articles = []
    
    try:
        print(f"  Processing {source_name}...")
        feed = feedparser.parse(feed_url)
        
        for entry in feed.entries[:20]:  # Get up to 20 articles per feed
            # Check date
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6])
                if pub_date < CUTOFF_DATE:
                    continue
            else:
                pub_date = datetime.now()
            
            # Extract article
            article = {
                'source': source_name,
                'title': entry.get('title', ''),
                'url': entry.get('link', ''),
                'published_date': pub_date,
                'summary': entry.get('summary', '')[:500]
            }
            
            # Get full content
            if article['url']:
                full_content = extract_full_content(article['url'])
                article['full_content'] = full_content
                article['content_length'] = len(full_content)
            else:
                article['full_content'] = article['summary']
                article['content_length'] = len(article['summary'])
            
            # Analyze correlations
            correlation_data = analyze_correlations(article['full_content'], article['title'])
            article.update(correlation_data)
            
            # Extract sentiment
            article['sentiment'] = extract_sentiment(article['full_content'])
            
            # Relevance scoring
            if article['soybean_mentions'] > 0:
                article['relevance'] = 'high'
            elif article['correlation_score'] > 5:
                article['relevance'] = 'medium'
            else:
                article['relevance'] = 'low'
            
            articles.append(article)
            
    except Exception as e:
        print(f"    Error with {source_name}: {str(e)[:50]}")
    
    return articles

# PARALLEL DATA ACQUISITION
print("\n1. PARALLEL FEED ACQUISITION")
print("-"*60)

all_feeds = []
for category, feeds in SOURCES.items():
    all_feeds.extend(feeds)

print(f"Processing {len(all_feeds)} feeds in parallel...")

all_articles = []
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    future_to_feed = {executor.submit(process_feed_parallel, feed): feed for feed in all_feeds}
    
    for future in concurrent.futures.as_completed(future_to_feed):
        articles = future.result()
        all_articles.extend(articles)
        print(f"  Collected {len(articles)} articles from feed")

print(f"\nTotal articles collected: {len(all_articles)}")

# FILTER AND PROCESS
print("\n2. FILTERING AND PROCESSING")
print("-"*60)

# Convert to DataFrame
df = pd.DataFrame(all_articles)

if len(df) > 0:
    # Filter by relevance and content length
    df_filtered = df[(df['content_length'] > 200) & (df['relevance'].isin(['high', 'medium']))]
    print(f"Articles after filtering: {len(df_filtered)}")
    
    # Sort by correlation score
    df_filtered = df_filtered.sort_values('correlation_score', ascending=False)
    
    # Show top correlations
    print("\nTop Correlation Topics:")
    topic_counts = df_filtered['primary_topic'].value_counts().head(10)
    for topic, count in topic_counts.items():
        print(f"  {topic}: {count} articles")
    
    # SAVE TO BIGQUERY
    print("\n3. SAVING TO BIGQUERY")
    print("-"*60)
    
    # Prepare for BigQuery
    df_filtered['ingested_at'] = datetime.now()
    df_filtered['published_date'] = pd.to_datetime(df_filtered['published_date'])
    
    # Define table
    table_id = "cbi-v14.forecasting_data_warehouse.news_comprehensive"
    
    # Save to BigQuery
    try:
        # Append to existing or create new
        job = client.load_table_from_dataframe(
            df_filtered,
            table_id,
            job_config=bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
        )
        job.result()
        print(f"✓ Saved {len(df_filtered)} articles to {table_id}")
        
    except Exception as e:
        print(f"Creating new table and retrying...")
        try:
            # Create table first
            job = client.load_table_from_dataframe(
                df_filtered,
                table_id,
                job_config=bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
            )
            job.result()
            print(f"✓ Created table and saved {len(df_filtered)} articles")
        except Exception as e2:
            print(f"✗ Error: {str(e2)[:200]}")
    
    # VERIFY QUALITY
    print("\n4. DATA QUALITY CHECK")
    print("-"*60)
    
    check_query = f"""
    SELECT 
        COUNT(*) as total_articles,
        COUNT(DISTINCT DATE(published_date)) as unique_days,
        AVG(content_length) as avg_content_length,
        AVG(correlation_score) as avg_correlation_score,
        COUNT(CASE WHEN tariffs_mentions > 0 THEN 1 END) as tariff_articles,
        COUNT(CASE WHEN china_mentions > 0 THEN 1 END) as china_articles,
        COUNT(CASE WHEN soybean_mentions > 0 THEN 1 END) as soybean_articles
    FROM `{table_id}`
    WHERE DATE(ingested_at) = CURRENT_DATE()
    """
    
    try:
        stats = client.query(check_query).to_dataframe()
        print("Today's Data Quality:")
        print(f"  Total articles: {stats['total_articles'].iloc[0]:,.0f}")
        print(f"  Unique days: {stats['unique_days'].iloc[0]:,.0f}")
        print(f"  Avg content length: {stats['avg_content_length'].iloc[0]:,.0f} chars")
        print(f"  Avg correlation score: {stats['avg_correlation_score'].iloc[0]:.2f}")
        print(f"  Tariff articles: {stats['tariff_articles'].iloc[0]:,.0f}")
        print(f"  China articles: {stats['china_articles'].iloc[0]:,.0f}")
        print(f"  Soybean articles: {stats['soybean_articles'].iloc[0]:,.0f}")
    except:
        pass

else:
    print("No articles collected - feeds may be blocking or empty")

print("\n" + "="*80)
print("ACQUISITION COMPLETE")
print("="*80)

print("""
NEXT STEPS:
1. Schedule this to run every hour
2. Add more sources as needed
3. Train models with correlation-rich data

Query the data:
SELECT * FROM `cbi-v14.forecasting_data_warehouse.news_comprehensive`
WHERE correlation_score > 5
ORDER BY published_date DESC
""")
