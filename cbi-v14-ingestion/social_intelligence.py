#!/usr/bin/env python3
"""
Social Intelligence & Sentiment Monitoring
Reddit, Twitter, YouTube, TikTok, LinkedIn agricultural sentiment
Early warning system for market sentiment shifts
"""

import pandas as pd
import requests
from google.cloud import bigquery
import json
import time
from datetime import datetime
import re
from bigquery_utils import intelligence_collector, quick_save_to_bigquery

PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"

class SocialIntelligence:
    """
    Monitor social media and online sentiment for early market signals
    Often provides 24-48 hour advance warning of market moves
    """
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        self.social_sources = self._build_social_matrix()
        self.keywords = self._build_sentiment_keywords()
        self.api_key = "B1TOgQvMVSV6TDglqB8lJ2cirqi2"
        
    def _build_social_matrix(self):
        """Social intelligence source matrix"""
        return {
            'facebook_sources': [
                'https://www.facebook.com/AmericanSoybeanAssociation/',
                'https://www.facebook.com/departmentoflabor',
                'https://www.facebook.com/USDA'
            ]
        }
    
    def _build_sentiment_keywords(self):
        """Sentiment keywords for social media monitoring"""
        return {
            'bullish_soy': [
                'drought', 'crop failure', 'poor harvest', 'yield concern',
                'china buying', 'strong demand', 'export surge', 'tight supply',
                'biodiesel mandate', 'crushing margin', 'port strike', 'planting intentions'
            ],
            
            'bearish_soy': [
                'bumper crop', 'record harvest', 'oversupply', 'weak demand',
                'china cancels', 'trade war', 'export ban', 'crushing shutdown',
                'palm oil substitution', 'biofuel reduction', 'good weather', 'demand destruction'
            ],
            
            'regional_stress': [
                'argentina strike', 'brazil protest', 'port blockade',
                'trucker strike', 'export tax', 'currency crisis',
                'government change', 'policy shift', 'infrastructure failure', 'hatch act'
            ],
            
            'weather_sentiment': [
                'too dry', 'too wet', 'perfect weather', 'crop stress',
                'planting delayed', 'harvest rushed', 'field conditions',
                'soil moisture', 'temperature stress', 'growing season', 'farm bill'
            ]
        }
    
    @intelligence_collector('social_sentiment')
    def collect_social_intelligence(self):
        """
        Comprehensive social intelligence collection with automatic BigQuery loading
        Monitors Facebook pages for agricultural sentiment using Scrape Creators API
        """
        return self.monitor_facebook_sentiment()

    def monitor_facebook_sentiment(self):
        """
        Monitor Facebook pages for agricultural sentiment using Scrape Creators API
        """
        print("Monitoring Facebook for agricultural sentiment...")
        
        fb_intel = []
        
        for url in self.social_sources['facebook_sources']:
            try:
                headers = {'x-api-key': self.api_key}
                params = {'url': url, 'get_comments': 'true', 'days': '30'}
                response = requests.get(
                    "https://api.scrapecreators.com/v1/facebook/post",
                    headers=headers,
                    params=params,
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    posts = data.get('posts', [])
                    
                    for post in posts[:10]:  # Latest 10 posts
                        content = post.get('text', '').lower()
                        comments_text = ' '.join([c.get('text', '') for c in post.get('comments', [])]).lower()
                        full_text = content + ' ' + comments_text
                        
                        sentiment_score = self._analyze_sentiment(full_text)
                        
                        if sentiment_score != 0:
                            import uuid
                            fb_intel.append({
                                'platform': 'facebook',
                                'source_url': url,
                                'post_text': content,
                                'comments_text': comments_text,
                                'sentiment_score': sentiment_score,
                                'timestamp': datetime.now(),
                                'market_relevance': 'high' if abs(sentiment_score) > 0.5 else 'medium',
                                'source_name': 'ScrapeCreators_Facebook',
                                'confidence_score': 0.75,
                                'ingest_timestamp_utc': datetime.utcnow(),
                                'provenance_uuid': str(uuid.uuid4())
                            })
                
                time.sleep(2)  # Rate limiting
                
            except Exception as e:
                print(f"Facebook monitoring failed for {url}: {e}")
        
        return fb_intel

    def _analyze_sentiment(self, text):
        """
        Analyze text for bullish/bearish soybean sentiment
        Returns score: -1 (very bearish) to +1 (very bullish)
        """
        text_lower = text.lower()
        
        bullish_score = sum(1 for keyword in self.keywords['bullish_soy'] 
                          if keyword in text_lower)
        
        bearish_score = sum(1 for keyword in self.keywords['bearish_soy'] 
                           if keyword in text_lower)
        
        # Regional stress affects sentiment
        stress_score = sum(1 for keyword in self.keywords['regional_stress'] 
                          if keyword in text_lower)
        
        # Weather sentiment
        weather_score = sum(1 for keyword in self.keywords['weather_sentiment'] 
                           if keyword in text_lower)
        
        # Calculate net sentiment (-1 to +1)
        total_signals = bullish_score + bearish_score + stress_score + weather_score
        
        if total_signals == 0:
            return 0.0  # No relevant sentiment
        
        net_sentiment = (bullish_score - bearish_score - stress_score) / total_signals
        
        # Weather bonus (weather often leads price moves)
        if weather_score > 0:
            net_sentiment *= 1.2  # Weather sentiment gets 20% bonus
        
        return max(-1.0, min(1.0, net_sentiment))  # Clamp to [-1, 1]

def main():
    """Execute social intelligence collection with modern decorator pattern"""
    intel = SocialIntelligence()
    
    print("=== SOCIAL INTELLIGENCE COLLECTION ===")
    print("Using modern decorator pattern with automatic BigQuery loading")
    
    # Collect social intelligence with automatic BigQuery loading
    social_data = intel.collect_social_intelligence()
    print(f"Social intelligence collected: {len(social_data)} records")
    
    print("✅ Social intelligence collection completed with automatic BigQuery loading")

if __name__ == "__main__":
    main()
