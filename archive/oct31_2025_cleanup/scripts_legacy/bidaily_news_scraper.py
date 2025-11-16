#!/usr/bin/env python3
'''
WARNING: This file has been cleaned of ALL fake data.
Any functions that relied on fake data have been disabled.
Must be rewritten to use REAL data from BigQuery or APIs.
ZERO TOLERANCE FOR FAKE DATA.
'''

#!/usr/bin/env python3
"""
BI-DAILY NEWS SCRAPER
Automated news collection every 2 days for continuous signal updates
"""

import requests
from datetime import datetime, timedelta
import time
# REMOVED: import random # NO FAKE DATA
from google.cloud import bigquery
import pandas as pd
from bs4 import BeautifulSoup
import feedparser
import concurrent.futures
import hashlib
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bidaily_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

# Only get recent content (last 3 days to ensure overlap)
CUTOFF_DATE = datetime.now() - timedelta(days=3)

# HIGH-VALUE SOURCES FOR BI-DAILY PULLS
BIDAILY_SOURCES = [
    # Financial News
    ('https://feeds.bloomberg.com/markets/news.rss', 'Bloomberg', 'financial'),
    ('https://www.reuters.com/markets/commodities/rss', 'Reuters', 'financial'),
    ('https://www.ft.com/commodities?format=rss', 'FT', 'financial'),
    
    # Agricultural
    ('https://www.agweb.com/rss/news', 'AgWeb', 'agricultural'),
    ('https://www.farmprogress.com/rss.xml', 'Farm Progress', 'agricultural'),
    ('https://brownfieldagnews.com/feed/', 'Brownfield', 'agricultural'),
    
    # Policy/Trade
    ('https://www.politico.com/rss/agriculture.xml', 'Politico', 'policy'),
    ('https://www.opensecrets.org/rss/news.xml', 'OpenSecrets', 'policy'),
    
    # International
    ('https://www.scmp.com/rss/91/feed', 'SCMP', 'international'),
    ('https://en.mercopress.com/rss/agriculture', 'MercoPress', 'international'),
    
    # Biofuel/Energy
    ('http://biodieselmagazine.com/rss', 'Biodiesel Magazine', 'biofuel'),
    ('https://ethanolproducer.com/rss', 'Ethanol Producer', 'biofuel'),
    
    # Reddit Communities
    ('https://www.reddit.com/r/commodities.rss', 'Reddit Commodities', 'social'),
    ('https://www.reddit.com/r/farming.rss', 'Reddit Farming', 'social'),
]

def get_headers():
    """Random headers for requests"""
    return {
# REMOVED:         'User-Agent': random.choice([ # NO FAKE DATA
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        ]),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

def extract_content(url, max_length=5000):
    """Extract article content"""
    try:
# REMOVED:         time.sleep(random.uniform(0.5, 2)) # NO FAKE DATA
        response = requests.get(url, headers=get_headers(), timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer']):
                element.decompose()
            
            # Extract text
            text = soup.get_text(separator=' ', strip=True)
            return text[:max_length]
    except:
        pass
    return ""

def analyze_content(title, content):
    """Analyze content for key signals"""
    combined = (title + ' ' + content).lower()
    
    signals = {
        'soybean_oil_mentions': len([1 for term in ['soybean oil', 'bean oil', 'soy oil'] if term in combined]),
        'tariffs_mentions': len([1 for term in ['tariff', 'trade war', 'duty'] if term in combined]),
        'china_mentions': len([1 for term in ['china', 'chinese', 'beijing'] if term in combined]),
        'brazil_mentions': len([1 for term in ['brazil', 'brazilian'] if term in combined]),
        'argentina_mentions': len([1 for term in ['argentina', 'argentine'] if term in combined]),
        'legislation_mentions': len([1 for term in ['congress', 'senate', 'bill', 'law'] if term in combined]),
        'biofuel_mentions': len([1 for term in ['biodiesel', 'ethanol', 'renewable fuel'] if term in combined]),
        'weather_mentions': len([1 for term in ['drought', 'flood', 'weather', 'rain'] if term in combined]),
    }
    
    # Calculate relevance
    total_score = sum(signals.values())
    if signals['soybean_oil_mentions'] > 0:
        relevance = 'critical'
    elif total_score > 5:
        relevance = 'high'
    elif total_score > 2:
        relevance = 'medium'
    else:
        relevance = 'low'
    
    signals['total_score'] = total_score
    signals['relevance'] = relevance
    
    return signals

def process_feed(feed_info):
    """Process a single feed"""
    url, source, category = feed_info
    articles = []
    
    try:
        logger.info(f"Processing {source}...")
        feed = feedparser.parse(url)
        
        for entry in feed.entries[:10]:  # Limit to 10 most recent
            # Check date
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6])
                if pub_date < CUTOFF_DATE:
                    continue
            else:
                pub_date = datetime.now()
            
            # Extract content
            article_url = entry.get('link', '')
            full_content = extract_content(article_url) if article_url else entry.get('summary', '')
            
            # Analyze
            signals = analyze_content(entry.get('title', ''), full_content)
            
            # Create article record
            article = {
                'source': source,
                'category': category,
                'title': entry.get('title', ''),
                'url': article_url,
                'published_date': pub_date,
                'summary': entry.get('summary', '')[:500],
                'full_content': full_content,
                'content_length': len(full_content),
                'article_id': hashlib.md5(f"{article_url}{entry.get('title', '')}".encode()).hexdigest(),
                'ingested_at': datetime.now(),
                **signals
            }
            
            articles.append(article)
            
        logger.info(f"  Collected {len(articles)} articles from {source}")
        
    except Exception as e:
        logger.error(f"  Error with {source}: {str(e)[:100]}")
    
    return articles

def main():
    """Main scraping function"""
    logger.info("="*80)
    logger.info("BI-DAILY NEWS SCRAPING")
    logger.info("="*80)
    
    # Process all feeds in parallel
    all_articles = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_feed, feed) for feed in BIDAILY_SOURCES]
        
        for future in concurrent.futures.as_completed(futures):
            articles = future.result()
            all_articles.extend(articles)
    
    logger.info(f"\nTotal articles collected: {len(all_articles)}")
    
    if all_articles:
        # Convert to DataFrame
        df = pd.DataFrame(all_articles)
        
        # Filter for relevance
        df_filtered = df[df['relevance'].isin(['critical', 'high', 'medium'])]
        logger.info(f"Relevant articles: {len(df_filtered)}")
        
        # Save to BigQuery
        table_id = "cbi-v14.forecasting_data_warehouse.news_bidaily"
        
        try:
            job = client.load_table_from_dataframe(
                df_filtered,
                table_id,
                job_config=bigquery.LoadJobConfig(
                    write_disposition="WRITE_APPEND",
                    schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION]
                )
            )
            job.result()
            logger.info(f"✓ Saved {len(df_filtered)} articles to BigQuery")
            
        except Exception as e:
            logger.error(f"BigQuery save failed: {str(e)[:200]}")
            # Save locally as backup
            df_filtered.to_csv(f'news_backup_{datetime.now().strftime("%Y%m%d")}.csv', index=False)
            logger.info("Saved to local backup CSV")
        
        # Show summary
        logger.info("\nSignal Summary:")
        signal_cols = ['tariffs_mentions', 'china_mentions', 'brazil_mentions', 'biofuel_mentions']
        for col in signal_cols:
            if col in df_filtered.columns:
                count = (df_filtered[col] > 0).sum()
                logger.info(f"  {col.replace('_mentions', '').title()}: {count} articles")
    
    logger.info("\n" + "="*80)
    logger.info("SCRAPING COMPLETE")
    logger.info("="*80)

if __name__ == "__main__":
    main()
