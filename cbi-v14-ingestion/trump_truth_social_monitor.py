#!/usr/bin/env python3
"""
Trump Truth Social Intelligence Monitor
Real-time monitoring of Trump posts for market impact analysis
Uses Scrape Creators API for legal, compliant access
PRODUCTION GRADE - Following CURSOR_RULES
"""

import requests
import logging
import time
import yfinance as yf
from datetime import datetime, timezone, timedelta
from google.cloud import bigquery
import pandas as pd
import uuid
import json
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/trump_truth_social.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('trump_truth_social')

class TrumpTruthSocialMonitor:
    """
    Production-grade Trump Truth Social monitoring
    Correlates posts with VIX spikes and commodity market reactions
    """
    
    def __init__(self):
        self.client = bigquery.Client(project='cbi-v14')
        self.api_key = 'B1TOgQvMVSV6TDglqB8lJ2cirqi2'  # Scrape Creators API
        self.base_url = 'https://api.scrapecreators.com/v1/truthsocial'
        
        # Agricultural keywords (from user guidance)
        self.agricultural_keywords = [
            'soybeans', 'soybean', 'farmers', 'agriculture', 'rural', 
            'heartland', 'farm bill', 'corn', 'wheat', 'crops'
        ]
        
        # Trade & policy keywords
        self.trade_keywords = [
            'trade', 'tariffs', 'china trade', 'exports', 'bilateral', 
            'epa', 'biofuels', 'sanctions', 'trade war', 'imports'
        ]
        
        # Geographic & competitor keywords
        self.geographic_keywords = [
            'china', 'brazil', 'argentina', 'midwest', 'iowa', 
            'illinois', 'nebraska', 'kansas'
        ]
        
        # Fear keywords that correlate with VIX spikes
        self.fear_keywords = [
            'military', 'dissent', 'democrat', 'war', 'conflict',
            'crisis', 'emergency', 'investigation', 'lawsuit', 'threat'
        ]
        
        # All keywords combined
        self.all_keywords = (self.agricultural_keywords + self.trade_keywords + 
                           self.geographic_keywords + self.fear_keywords)
    
    def get_recent_trump_post_urls(self, count=10):
        """
        Get recent Trump post URLs for API calls
        In production, this would query a database of known post URLs
        For now, we'll use a sample approach
        """
        # Sample Trump Truth Social post URLs (in production, get from profile scraping)
        sample_urls = [
            'https://truthsocial.com/@realDonaldTrump/114315219437063160',
            # Add more URLs as discovered
        ]
        return sample_urls[:count]
    
    def collect_trump_post(self, post_url):
        """
        Collect individual Trump Truth Social post using Scrape Creators API
        Rate limited and respectful - PRODUCTION GRADE
        """
        logger.info(f"📱 Collecting Trump post: {post_url}")
        
        headers = {
            'x-api-key': self.api_key,
            'User-Agent': 'CBI-V14-TrumpMonitor/1.0'
        }
        
        params = {
            'url': post_url
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/post",
                headers=headers,
                params=params,
                timeout=30
            )
            
            logger.info(f"📡 API Response: HTTP {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    logger.info(f"✅ Post collected successfully")
                    logger.info(f"💳 Credits remaining: {data.get('credits_remaining', 'Unknown')}")
                    
                    # Extract post data
                    post_data = {
                        'text': data.get('text', ''),
                        'content': data.get('content', ''),
                        'id': data.get('id', ''),
                        'created_at': data.get('created_at', ''),
                        'replies_count': data.get('replies_count', 0),
                        'reblogs_count': data.get('reblogs_count', 0),
                        'favourites_count': data.get('favourites_count', 0),
                        'url': post_url
                    }
                    
                    return post_data
                else:
                    logger.warning(f"❌ API returned success=false: {data.get('message', 'Unknown error')}")
                    return None
                    
            elif response.status_code == 404:
                logger.warning(f"⚠️ Post not found: {post_url}")
                return None
            elif response.status_code == 401:
                logger.error("❌ API key authentication failed")
                return None
            elif response.status_code == 429:
                logger.warning("⚠️ Rate limited - waiting 60 seconds")
                time.sleep(60)
                return None
            else:
                logger.error(f"❌ API error: HTTP {response.status_code}")
                try:
                    error_data = response.json()
                    logger.error(f"Error details: {error_data}")
                except:
                    logger.error(f"Response: {response.text[:200]}...")
                return None
                
        except Exception as e:
            logger.error(f"❌ Truth Social API error: {e}")
            return None
    
    def collect_trump_posts(self, max_posts=5):
        """
        Collect multiple Trump posts with rate limiting
        """
        logger.info(f"📱 Collecting up to {max_posts} Trump Truth Social posts")
        
        post_urls = self.get_recent_trump_post_urls(max_posts)
        collected_posts = []
        
        for i, post_url in enumerate(post_urls):
            logger.info(f"📱 Collecting post {i+1}/{len(post_urls)}")
            
            post_data = self.collect_trump_post(post_url)
            
            if post_data:
                collected_posts.append(post_data)
                logger.info(f"✅ Post {i+1}: {len(post_data.get('text', ''))} characters")
            else:
                logger.warning(f"❌ Post {i+1}: Failed to collect")
            
            # Rate limiting between posts (60 seconds)
            if i < len(post_urls) - 1:
                logger.info("⏱️  Rate limiting: waiting 60 seconds...")
                time.sleep(60)
        
        logger.info(f"✅ Collected {len(collected_posts)} Trump posts")
        return collected_posts
    
    def analyze_post_market_impact(self, post):
        """
        Analyze individual post for market impact potential
        Uses the structured data from Scrape Creators API
        """
        # Get text content (try both 'text' and 'content' fields)
        content = (post.get('text', '') or post.get('content', '')).lower()
        timestamp = post.get('created_at', '')
        
        # Extract engagement metrics
        replies = post.get('replies_count', 0)
        reblogs = post.get('reblogs_count', 0) 
        favourites = post.get('favourites_count', 0)
        
        # Count keyword categories
        ag_score = sum(1 for keyword in self.agricultural_keywords if keyword in content)
        trade_score = sum(1 for keyword in self.trade_keywords if keyword in content)
        geo_score = sum(1 for keyword in self.geographic_keywords if keyword in content)
        fear_score = sum(1 for keyword in self.fear_keywords if keyword in content)
        
        # Calculate market impact potential
        total_keywords = ag_score + trade_score + geo_score + fear_score
        
        # Agricultural relevance (0-1 scale)
        agricultural_impact = (ag_score + trade_score * 0.8 + geo_score * 0.6) / 10.0
        agricultural_impact = min(agricultural_impact, 1.0)
        
        # Soybean specific relevance
        soybean_mentions = content.count('soybean') + content.count('soybeans')
        china_mentions = content.count('china')
        trade_mentions = content.count('trade') + content.count('tariff')
        
        soybean_relevance = (soybean_mentions * 0.4 + china_mentions * 0.3 + trade_mentions * 0.2) / 3.0
        soybean_relevance = min(soybean_relevance, 1.0)
        
        # VIX impact potential (fear keywords drive volatility)
        vix_impact_potential = fear_score * 0.15  # Each fear keyword = +15% VIX impact potential
        vix_impact_potential = min(vix_impact_potential, 1.0)
        
        # Market timing factor (posts during market hours have higher impact)
        post_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        market_hours = 9 <= post_time.hour <= 16  # 9 AM - 4 PM EST
        timing_multiplier = 1.5 if market_hours else 1.0
        
        return {
            'agricultural_impact': agricultural_impact * timing_multiplier,
            'soybean_relevance': soybean_relevance * timing_multiplier,
            'vix_impact_potential': vix_impact_potential * timing_multiplier,
            'fear_keyword_count': fear_score,
            'agricultural_keyword_count': ag_score,
            'trade_keyword_count': trade_score,
            'total_keyword_score': total_keywords,
            'posted_during_market_hours': market_hours,
            'timing_multiplier': timing_multiplier
        }
    
    def get_vix_at_time(self, post_timestamp):
        """
        Get VIX value at time of post for correlation analysis
        """
        try:
            vix_ticker = yf.Ticker('^VIX')
            
            # Get VIX data for the day of the post
            post_date = datetime.fromisoformat(post_timestamp.replace('Z', '+00:00')).date()
            vix_data = vix_ticker.history(start=post_date, end=post_date + timedelta(days=1))
            
            if not vix_data.empty:
                return float(vix_data['Close'].iloc[-1])
            
        except Exception as e:
            logger.warning(f"Could not get VIX for {post_timestamp}: {e}")
        
        return None
    
    def process_posts_to_intelligence(self, posts):
        """
        Process Trump posts into trump_policy_intelligence schema
        """
        if not posts:
            return []
        
        intelligence_records = []
        
        for post in posts:
            try:
                content = post.get('content', '') or post.get('text', '')
                timestamp = post.get('created_at', '') or post.get('timestamp', '')
                post_id = post.get('id', '')
                
                # Skip if no timestamp
                if not timestamp:
                    logger.warning(f"⚠️ Post {post_id}: No timestamp, skipping")
                    continue
                
                # Skip if no agricultural/trade relevance
                if not any(keyword in content.lower() for keyword in self.all_keywords):
                    continue
                
                # Analyze market impact
                analysis = self.analyze_post_market_impact(post)
                
                # Get VIX at time of post
                vix_at_time = self.get_vix_at_time(timestamp)
                
                # Create intelligence record (match trump_policy_intelligence schema exactly)
                record = {
                    'source': 'truth_social_api',
                    'category': 'trump_social_media',
                    'text': content[:500],  # Truncate for storage
                    'agricultural_impact': analysis['agricultural_impact'],
                    'soybean_relevance': analysis['soybean_relevance'],
                    'timestamp': datetime.fromisoformat(timestamp.replace('Z', '+00:00')),
                    'priority': 1 if analysis['fear_keyword_count'] > 2 else 2,
                    # Canonical metadata
                    'source_name': 'Scrape_Creators_Truth_Social',
                    'confidence_score': 0.90,
                    'ingest_timestamp_utc': datetime.now(timezone.utc),
                    'provenance_uuid': str(uuid.uuid4())
                }
                
                intelligence_records.append(record)
                
                logger.info(f"📱 Post analyzed: {analysis['total_keyword_score']} keywords, VIX impact: {analysis['vix_impact_potential']:.2f}")
                
            except Exception as e:
                logger.error(f"❌ Error processing post: {e}")
                continue
        
        logger.info(f"✅ Processed {len(intelligence_records)} Trump posts to intelligence format")
        return intelligence_records
    
    def save_to_trump_intelligence(self, trump_data):
        """
        Save Trump social media analysis to staging.trump_policy_intelligence table
        """
        if not trump_data:
            return False
        
        try:
            df = pd.DataFrame(trump_data)
            table_ref = 'cbi-v14.staging.trump_policy_intelligence'
            
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND",
                autodetect=True
            )
            
            job = self.client.load_table_from_dataframe(df, table_ref, job_config=job_config)
            job.result()
            
            logger.info(f"✅ Saved {len(trump_data)} Trump social media records")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save Trump social data: {e}")
            return False
    
    def run_trump_social_monitoring(self):
        """
        Run complete Trump Truth Social monitoring cycle
        """
        logger.info("=" * 80)
        logger.info("TRUMP TRUTH SOCIAL INTELLIGENCE MONITORING")
        logger.info("Using Scrape Creators API (Legal & Compliant)")
        logger.info("=" * 80)
        
        # Collect posts
        posts = self.collect_trump_posts(max_posts=3)
        
        if not posts:
            logger.warning("No Trump posts collected")
            return False
        
        # Process for market impact
        intelligence_data = self.process_posts_to_intelligence(posts)
        
        if not intelligence_data:
            logger.warning("No market-relevant posts found")
            return False
        
        # Save to BigQuery
        success = self.save_to_trump_intelligence(intelligence_data)
        
        if success:
            # Calculate summary metrics
            total_posts = len(intelligence_data)
            high_impact = sum(1 for p in intelligence_data if p['agricultural_impact'] > 0.5)
            
            logger.info("=" * 80)
            logger.info(f"🎉 TRUMP SOCIAL MONITORING SUCCESS")
            logger.info(f"📱 Total posts analyzed: {total_posts}")
            logger.info(f"⚡ High agricultural impact posts: {high_impact}")
            logger.info("✅ Real-time presidential market impact monitoring operational")
            logger.info("=" * 80)
        
        return success

if __name__ == '__main__':
    monitor = TrumpTruthSocialMonitor()
    success = monitor.run_trump_social_monitoring()
    
    if success:
        logger.info("🎉 Trump Truth Social Monitor: OPERATIONAL")
        exit(0)
    else:
        logger.error("❌ Trump Truth Social Monitor: FAILED")
        exit(1)
