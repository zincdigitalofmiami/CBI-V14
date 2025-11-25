#!/usr/bin/env python3
"""
Hourly Breaking News with AI Analysis
Fetches GDELT headlines, summarizes with Gemini, stores to BigQuery
"""
import requests
from google.cloud import bigquery
from datetime import datetime, timedelta
import logging
import json
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse" 
TABLE_ID = "breaking_news_hourly"
GDELT_API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

def fetch_gdelt_headlines():
    """Fetch recent soybean oil related headlines from GDELT"""
    try:
        # Search for soybean oil, palm oil, vegetable oil news in last 6 hours
        params = {
            'query': '(soybean oil OR palm oil OR vegetable oil OR cooking oil) AND (price OR market OR trade OR export)',
            'mode': 'artlist',
            'maxrecords': '20',
            'timespan': '6h',
            'format': 'json',
            'sort': 'datedesc'
        }
        
        response = requests.get(GDELT_API_URL, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        articles = data.get('articles', [])
        
        headlines = []
        for article in articles[:10]:  # Top 10 most recent
            headlines.append({
                'headline': article.get('title', ''),
                'url': article.get('url', ''),
                'source': article.get('domain', ''),
                'timestamp': article.get('seendate', '')
            })
            
        logger.info(f"Fetched {len(headlines)} headlines from GDELT")
        return headlines
        
    except Exception as e:
        logger.error(f"Failed to fetch GDELT headlines: {e}")
        return []

def analyze_with_ai(headline, url):
    """Analyze headline relevance and sentiment (simplified for now)"""
    try:
        # Simple keyword-based analysis until Gemini integration
        soy_keywords = ['soybean', 'soy oil', 'vegetable oil', 'cooking oil']
        price_keywords = ['price', 'cost', 'expensive', 'cheap', 'rise', 'fall', 'surge', 'drop']
        
        headline_lower = headline.lower()
        
        # Calculate relevance score
        relevance = 0.0
        for keyword in soy_keywords:
            if keyword in headline_lower:
                relevance += 0.3
        for keyword in price_keywords:
            if keyword in headline_lower:
                relevance += 0.2
                
        relevance = min(relevance, 1.0)
        
        # Calculate sentiment score (-1 to 1)
        bullish_words = ['rise', 'surge', 'up', 'gain', 'strong', 'demand', 'shortage']
        bearish_words = ['fall', 'drop', 'down', 'weak', 'surplus', 'decline', 'crash']
        
        sentiment = 0.0
        for word in bullish_words:
            if word in headline_lower:
                sentiment += 0.2
        for word in bearish_words:
            if word in headline_lower:
                sentiment -= 0.2
                
        sentiment = max(-1.0, min(1.0, sentiment))
        
        # Generate simple summary
        summary = f"Market impact analysis: {headline[:100]}..."
        
        return {
            'summary': summary,
            'sentiment_score': sentiment,
            'relevance_score': relevance
        }
        
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        return {
            'summary': headline,
            'sentiment_score': 0.0,
            'relevance_score': 0.5
        }

def save_to_bigquery(news_data):
    """Save processed news to BigQuery"""
    try:
        client = bigquery.Client(project=PROJECT_ID)
        table_ref = client.dataset(DATASET_ID).table(TABLE_ID)
        table = client.get_table(table_ref)
        
        rows_to_insert = []
        for item in news_data:
            rows_to_insert.append({
                'timestamp': datetime.utcnow().isoformat(),
                'headline': item['headline'],
                'summary': item['summary'],
                'sentiment_score': item['sentiment_score'],
                'relevance_score': item['relevance_score'],
                'source': item['source'],
                'url': item['url']
            })
        
        errors = client.insert_rows_json(table, rows_to_insert)
        if errors:
            logger.error(f"BigQuery insert errors: {errors}")
            return False
            
        logger.info(f"Successfully inserted {len(rows_to_insert)} news items")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save to BigQuery: {e}")
        return False

def main():
    """Main execution function"""
    logger.info("Starting hourly news collection...")
    
    # Fetch headlines
    headlines = fetch_gdelt_headlines()
    if not headlines:
        logger.warning("No headlines fetched, exiting")
        return
    
    # Analyze each headline
    processed_news = []
    for headline_data in headlines:
        analysis = analyze_with_ai(headline_data['headline'], headline_data['url'])
        
        processed_item = {
            'headline': headline_data['headline'],
            'url': headline_data['url'],
            'source': headline_data['source'],
            'summary': analysis['summary'],
            'sentiment_score': analysis['sentiment_score'],
            'relevance_score': analysis['relevance_score']
        }
        processed_news.append(processed_item)
    
    # Save to BigQuery
    if save_to_bigquery(processed_news):
        logger.info("Hourly news collection completed successfully")
    else:
        logger.error("Failed to save news data")

if __name__ == "__main__":
    main()











