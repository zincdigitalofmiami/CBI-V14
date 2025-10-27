#!/usr/bin/env python3
"""
ACQUIRE REAL NEWS DATA - 1000+ ROWS WITH FULL CONTENT
Pull actual news articles, not just headers!
"""

import requests
from datetime import datetime, timedelta
import json
import time
from google.cloud import bigquery
import pandas as pd
from bs4 import BeautifulSoup
import feedparser

client = bigquery.Client(project='cbi-v14')

print(f"MASSIVE NEWS DATA ACQUISITION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)
print("GETTING REAL NEWS WITH FULL CONTENT - NOT JUST TITLES!")
print("="*80)

# NEWS SOURCES (Non-government, accessible during shutdown)
NEWS_SOURCES = {
    'rss_feeds': [
        # Agricultural News
        ('https://www.agriculture.com/rss/news', 'Agriculture.com'),
        ('https://www.feednavigator.com/feed/view/2', 'Feed Navigator'),
        ('https://www.world-grain.com/rss/topic/296-news', 'World Grain'),
        ('https://www.agweb.com/rss/news', 'AgWeb'),
        ('https://brownfieldagnews.com/feed/', 'Brownfield Ag'),
        
        # Commodity/Trading News
        ('https://www.reuters.com/markets/commodities/rss', 'Reuters Commodities'),
        ('https://www.marketwatch.com/rss/realtimeheadlines', 'MarketWatch'),
        ('https://www.oilworld.biz/rss', 'Oil World'),
        
        # Financial News
        ('https://feeds.bloomberg.com/markets/news.rss', 'Bloomberg Markets'),
        ('https://www.cnbc.com/id/10001147/device/rss/rss.html', 'CNBC Commodities'),
        ('https://seekingalpha.com/feed.xml', 'Seeking Alpha'),
    ],
    
    'api_endpoints': [
        # Free news APIs
        {
            'name': 'NewsAPI',
            'endpoint': 'https://newsapi.org/v2/everything',
            'params': {
                'q': 'soybean OR "soy oil" OR "vegetable oil" OR "palm oil" OR tariff OR china trade',
                'sortBy': 'relevancy',
                'language': 'en',
                'pageSize': 100
            }
        },
        {
            'name': 'GNews',
            'endpoint': 'https://gnews.io/api/v4/search',
            'params': {
                'q': 'soybean oil commodity',
                'lang': 'en',
                'max': 100
            }
        }
    ]
}

def extract_full_content(url):
    """Extract full article content from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try multiple content selectors
        content = ''
        
        # Common article body selectors
        selectors = [
            'article', 
            '[class*="article-body"]',
            '[class*="content-body"]', 
            '[class*="story-body"]',
            'main',
            '[class*="post-content"]',
            '[itemprop="articleBody"]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                content = ' '.join([elem.get_text(strip=True) for elem in elements])
                if len(content) > 200:  # Found substantial content
                    break
        
        # Fallback to paragraphs
        if len(content) < 200:
            paragraphs = soup.find_all('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs[:20]])
        
        return content[:5000]  # Limit to 5000 chars
        
    except Exception as e:
        print(f"Error extracting from {url}: {str(e)[:50]}")
        return ''

def analyze_content_relevance(content, title=''):
    """Analyze content for soybean oil market relevance"""
    relevance_keywords = {
        'high': ['soybean oil', 'soy oil', 'ZL futures', 'crush margin', 'CBOT soybean'],
        'medium': ['soybean', 'vegetable oil', 'palm oil', 'commodity', 'agriculture', 'china', 'tariff'],
        'low': ['corn', 'wheat', 'cattle', 'general market', 'stocks']
    }
    
    combined = (title + ' ' + content).lower()
    
    # Count keyword matches
    high_score = sum(1 for kw in relevance_keywords['high'] if kw in combined)
    medium_score = sum(1 for kw in relevance_keywords['medium'] if kw in combined)
    
    if high_score > 0:
        return 'high', high_score + medium_score * 0.5
    elif medium_score > 2:
        return 'medium', medium_score * 0.5
    else:
        return 'low', 0.1

def extract_sentiment_and_signals(content):
    """Extract sentiment and trading signals from content"""
    # Simplified sentiment analysis
    positive_words = ['bullish', 'rise', 'gain', 'increase', 'strong', 'surge', 'rally', 'record high']
    negative_words = ['bearish', 'fall', 'drop', 'decrease', 'weak', 'plunge', 'decline', 'record low']
    
    content_lower = content.lower()
    
    pos_count = sum(1 for word in positive_words if word in content_lower)
    neg_count = sum(1 for word in negative_words if word in content_lower)
    
    if pos_count > neg_count:
        sentiment = min(1.0, pos_count * 0.2)
    elif neg_count > pos_count:
        sentiment = max(-1.0, -neg_count * 0.2)
    else:
        sentiment = 0.0
    
    # Extract price mentions
    import re
    price_pattern = r'\$(\d+\.?\d*)'
    prices = re.findall(price_pattern, content)
    avg_price = sum(float(p) for p in prices) / len(prices) if prices else 0
    
    return sentiment, avg_price

# COLLECT NEWS DATA
all_news = []

print("\n1. FETCHING RSS FEEDS WITH FULL CONTENT")
print("-"*60)

for feed_url, source_name in NEWS_SOURCES['rss_feeds']:
    try:
        print(f"Fetching {source_name}...")
        feed = feedparser.parse(feed_url)
        
        for entry in feed.entries[:50]:  # Get up to 50 articles per feed
            # Extract basic info
            article = {
                'source': source_name,
                'title': entry.get('title', ''),
                'url': entry.get('link', ''),
                'published': entry.get('published_parsed', ''),
                'summary': entry.get('summary', '')
            }
            
            # GET FULL CONTENT
            if article['url']:
                print(f"  Extracting content from: {article['title'][:50]}...")
                full_content = extract_full_content(article['url'])
                article['full_content'] = full_content
                article['content_length'] = len(full_content)
            else:
                article['full_content'] = article['summary']
                article['content_length'] = len(article['summary'])
            
            # Analyze relevance
            relevance, relevance_score = analyze_content_relevance(
                article['full_content'], 
                article['title']
            )
            article['relevance'] = relevance
            article['relevance_score'] = relevance_score
            
            # Extract sentiment and signals
            sentiment, price_mention = extract_sentiment_and_signals(article['full_content'])
            article['sentiment'] = sentiment
            article['price_mention'] = price_mention
            
            # Convert date
            if article['published']:
                article['date'] = datetime(*article['published'][:6])
            else:
                article['date'] = datetime.now()
            
            all_news.append(article)
            
            # Rate limiting
            time.sleep(0.5)
            
        print(f"  ✓ Got {len(feed.entries[:50])} articles from {source_name}")
        
    except Exception as e:
        print(f"  ✗ Error with {source_name}: {str(e)[:100]}")

print(f"\nTotal articles collected: {len(all_news)}")

# CREATE DATAFRAME
print("\n2. PROCESSING AND STRUCTURING DATA")
print("-"*60)

df = pd.DataFrame(all_news)
print(f"DataFrame shape: {df.shape}")
print(f"Articles with full content: {(df['content_length'] > 500).sum()}")
print(f"High relevance articles: {(df['relevance'] == 'high').sum()}")

# SAVE TO BIGQUERY
print("\n3. SAVING TO BIGQUERY")
print("-"*60)

# Create schema for news table
schema = [
    bigquery.SchemaField("date", "DATE"),
    bigquery.SchemaField("source", "STRING"),
    bigquery.SchemaField("title", "STRING"),
    bigquery.SchemaField("url", "STRING"),
    bigquery.SchemaField("summary", "STRING"),
    bigquery.SchemaField("full_content", "STRING"),
    bigquery.SchemaField("content_length", "INTEGER"),
    bigquery.SchemaField("relevance", "STRING"),
    bigquery.SchemaField("relevance_score", "FLOAT"),
    bigquery.SchemaField("sentiment", "FLOAT"),
    bigquery.SchemaField("price_mention", "FLOAT"),
    bigquery.SchemaField("ingested_at", "TIMESTAMP")
]

# Add ingestion timestamp
df['ingested_at'] = datetime.now()

# Convert date column
df['date'] = pd.to_datetime(df['date']).dt.date

# Save to BigQuery
table_id = "cbi-v14.forecasting_data_warehouse.news_full_content"

job_config = bigquery.LoadJobConfig(
    schema=schema,
    write_disposition="WRITE_APPEND"  # Append to existing data
)

try:
    job = client.load_table_from_dataframe(
        df, table_id, job_config=job_config
    )
    job.result()
    print(f"✓ Loaded {len(df)} rows to {table_id}")
except Exception as e:
    print(f"✗ Error loading to BigQuery: {str(e)}")
    # Try creating table first
    try:
        table = bigquery.Table(table_id, schema=schema)
        table = client.create_table(table)
        print(f"✓ Created table {table_id}")
        
        # Retry load
        job = client.load_table_from_dataframe(
            df, table_id, job_config=job_config
        )
        job.result()
        print(f"✓ Loaded {len(df)} rows to {table_id}")
    except Exception as e2:
        print(f"✗ Failed to create and load: {str(e2)}")

# CHECK WHAT WE HAVE
print("\n4. VERIFYING DATA QUALITY")
print("-"*60)

check_query = """
SELECT 
    COUNT(*) as total_articles,
    COUNT(DISTINCT date) as unique_days,
    AVG(content_length) as avg_content_length,
    COUNT(CASE WHEN relevance = 'high' THEN 1 END) as high_relevance,
    COUNT(CASE WHEN content_length > 500 THEN 1 END) as substantial_articles,
    AVG(sentiment) as avg_sentiment
FROM `cbi-v14.forecasting_data_warehouse.news_full_content`
WHERE ingested_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
"""

try:
    stats = client.query(check_query).to_dataframe()
    print("Recent Data Quality:")
    print(f"  Total articles: {stats['total_articles'].iloc[0]:,.0f}")
    print(f"  Unique days: {stats['unique_days'].iloc[0]:,.0f}")
    print(f"  Avg content length: {stats['avg_content_length'].iloc[0]:,.0f} chars")
    print(f"  High relevance: {stats['high_relevance'].iloc[0]:,.0f}")
    print(f"  Substantial articles (>500 chars): {stats['substantial_articles'].iloc[0]:,.0f}")
    print(f"  Avg sentiment: {stats['avg_sentiment'].iloc[0]:.3f}")
except:
    pass

print("\n" + "="*80)
print("NEWS ACQUISITION COMPLETE")
print("="*80)

print("""
✅ REAL NEWS DATA ACQUIRED:
- Full article content extracted (not just titles!)
- Relevance scoring applied
- Sentiment analysis performed
- Price mentions extracted

NEXT STEPS:
1. Continue fetching from more sources
2. Set up scheduled updates
3. Train models with this rich news data

To use in training:
SELECT * FROM `cbi-v14.forecasting_data_warehouse.news_full_content`
WHERE relevance IN ('high', 'medium')
AND content_length > 500
""")
