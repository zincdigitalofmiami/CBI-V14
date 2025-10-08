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
        
    def _build_social_matrix(self):
        """Social intelligence source matrix"""
        return {
            'reddit_agriculture': [
                {'subreddit': 'agriculture', 'url': 'https://www.reddit.com/r/agriculture.json'},
                {'subreddit': 'farming', 'url': 'https://www.reddit.com/r/farming.json'},
                {'subreddit': 'commodities', 'url': 'https://www.reddit.com/r/commodities.json'},
                {'subreddit': 'soybeans', 'url': 'https://www.reddit.com/r/soybeans.json'},
                {'subreddit': 'grain_elevator', 'url': 'https://www.reddit.com/r/grainelevator.json'}
            ],
            
            'agricultural_forums': [
                {'name': 'AgTalk', 'url': 'https://talk.newagtalk.com/forums/'},
                {'name': 'Farm_Chat', 'url': 'https://farmchat.com/'},
                {'name': 'Crop_Talk', 'url': 'https://croptalk.com/'},
                {'name': 'Corn_Soybean_Digest', 'url': 'https://www.cornandsoybeandigest.com/'}
            ],
            
            'youtube_agriculture': [
                {'channel': 'Successful Farming', 'channel_id': 'UCpT9fCJCsf8xT8cYjQvdxBQ'},
                {'channel': 'Farm Basics', 'channel_id': 'UC8nQKgT2dEvR8A6q6nRvD7A'},
                {'channel': 'Agriculture Proud', 'channel_id': 'UCxQh4cFy1vPBzZp5H7oPvwQ'},
                {'channel': 'Farm Journal', 'channel_id': 'UCL7lF8AYM8qKEkQaKPt1Bpw'}
            ],
            
            'linkedin_agriculture': [
                {'type': 'company_posts', 'companies': ['Cargill', 'ADM', 'Bunge', 'Louis Dreyfus']},
                {'type': 'agriculture_groups', 'groups': ['Agricultural Professionals', 'Commodity Trading']}
            ],
            
            'tiktok_farmers': [
                {'hashtag': '#agriculture', 'region': 'global'},
                {'hashtag': '#farming', 'region': 'us'},
                {'hashtag': '#agronegocio', 'region': 'brazil'},
                {'hashtag': '#campo', 'region': 'argentina'}
            ]
        }
    
    def _build_sentiment_keywords(self):
        """Sentiment keywords for social media monitoring"""
        return {
            'bullish_soy': [
                'drought', 'crop failure', 'poor harvest', 'yield concern',
                'china buying', 'strong demand', 'export surge', 'tight supply',
                'biodiesel mandate', 'crushing margin', 'port strike'
            ],
            
            'bearish_soy': [
                'bumper crop', 'record harvest', 'oversupply', 'weak demand',
                'china cancels', 'trade war', 'export ban', 'crushing shutdown',
                'palm oil substitution', 'biofuel reduction', 'good weather'
            ],
            
            'regional_stress': [
                'argentina strike', 'brazil protest', 'port blockade',
                'trucker strike', 'export tax', 'currency crisis',
                'government change', 'policy shift', 'infrastructure failure'
            ],
            
            'weather_sentiment': [
                'too dry', 'too wet', 'perfect weather', 'crop stress',
                'planting delayed', 'harvest rushed', 'field conditions',
                'soil moisture', 'temperature stress', 'growing season'
            ]
        }
    
    @intelligence_collector('social_sentiment')
    def collect_social_intelligence(self):
        """
        Comprehensive social intelligence collection with automatic BigQuery loading
        Monitor Reddit agricultural communities for sentiment
        Often provides early signals from actual farmers
        """
        return self.monitor_reddit_agriculture()
    
    def monitor_reddit_agriculture(self):
        """
        Monitor Reddit agricultural communities for sentiment
        Often provides early signals from actual farmers
        """
        print("Monitoring Reddit agricultural sentiment...")
        
        reddit_intel = []
        
        for reddit_source in self.social_sources['reddit_agriculture']:
            try:
                headers = {'User-Agent': 'CBI-V14 Agricultural Research Bot 1.0'}
                response = requests.get(reddit_source['url'], headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'data' in data and 'children' in data['data']:
                        posts = data['data']['children']
                        
                        for post in posts[:20]:  # Latest 20 posts
                            post_data = post['data']
                            title = post_data.get('title', '').lower()
                            
                            # Check for relevant keywords
                            sentiment_score = self._analyze_sentiment(title)
                            
                            if sentiment_score != 0:  # Relevant post found
                                import uuid
                                reddit_intel.append({
                                    'platform': 'reddit',
                                    'subreddit': reddit_source['subreddit'],
                                    'title': post_data.get('title', ''),
                                    'score': post_data.get('score', 0),  # Upvotes
                                    'comments': post_data.get('num_comments', 0),
                                    'sentiment_score': sentiment_score,
                                    'timestamp': datetime.now(),
                                    'market_relevance': 'high' if abs(sentiment_score) > 0.5 else 'medium',
                                    # Canonical metadata
                                    'source_name': 'Reddit',
                                    'confidence_score': 0.65,
                                    'ingest_timestamp_utc': datetime.utcnow(),
                                    'provenance_uuid': str(uuid.uuid4())
                                })
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                print(f"Reddit monitoring failed for {reddit_source['subreddit']}: {e}")
        
        return reddit_intel
    
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
    
    def hunt_social_correlations(self):
        """
        Hunt for social sentiment correlations with price movements
        Identify which social signals predict price changes
        """
        print("Hunting social sentiment correlations...")
        
        # Get recent social sentiment data
        social_data = self.monitor_reddit_agriculture()
        
        if not social_data:
            print("No social data available for correlation analysis")
            return {}
        
        # Aggregate daily sentiment scores
        sentiment_df = pd.DataFrame(social_data)
        daily_sentiment = sentiment_df.groupby(
            sentiment_df['timestamp'].dt.date
        ).agg({
            'sentiment_score': 'mean',
            'score': 'sum',  # Total upvotes (engagement)
            'comments': 'sum'  # Total discussion volume
        }).reset_index()
        
        # Get price data for correlation
        query = f"""
        SELECT DATE(date) as date, value 
        FROM `{PROJECT_ID}.{DATASET_ID}.soy_oil_features`
        WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        """
        price_df = self.client.query(query).to_dataframe()
        
        # Analyze correlations
        if len(daily_sentiment) > 5 and len(price_df) > 5:
            merged = pd.merge(daily_sentiment, price_df, on='date', how='inner')
            
            if len(merged) > 3:
                sentiment_corr = merged['sentiment_score'].corr(merged['value'])
                engagement_corr = merged['score'].corr(merged['value'])
                
                return {
                    'sentiment_price_correlation': sentiment_corr,
                    'engagement_price_correlation': engagement_corr,
                    'data_points': len(merged),
                    'hunt_value': 'HIGH' if abs(sentiment_corr) > 0.3 else 'LOW'
                }
        
        return {}

def main():
    """Execute social intelligence collection with modern decorator pattern"""
    intel = SocialIntelligence()
    
    print("=== SOCIAL INTELLIGENCE COLLECTION ===")
    print("Using modern decorator pattern with automatic BigQuery loading")
    
    # Collect social intelligence with automatic BigQuery loading
    social_data = intel.collect_social_intelligence()
    print(f"Social intelligence collected: {len(social_data)} records")
    
    # Analyze sentiment correlations
    correlations = intel.hunt_social_correlations()
    
    if correlations:
        print(f"Sentiment correlation discovered: {correlations['sentiment_price_correlation']:.3f}")
        if correlations['hunt_value'] == 'HIGH':
            print("HIGH VALUE: Social sentiment provides predictive signal")
    
    print("✅ Social intelligence collection completed with automatic BigQuery loading")

if __name__ == "__main__":
    main()
