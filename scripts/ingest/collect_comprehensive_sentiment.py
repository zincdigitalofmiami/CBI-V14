#!/usr/bin/env python3
"""
Comprehensive sentiment collection using ScrapeCreators API and other sources.
Monitors Truth Social, Facebook, Reddit for real market-moving sentiment.

Author: AI Assistant
Date: November 16, 2025
"""

import os
import json
import time
import requests
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import logging
from typing import Dict, List
import re

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
RAW_DIR = DRIVE / "TrainingData/raw/sentiment"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# API Configuration (MOVE TO ENVIRONMENT VARIABLES!)
SCRAPE_CREATORS_KEY = os.getenv('SCRAPE_CREATORS_KEY', 'B1TOgQvMVSV6TDglqB8lJ2cirqi2')


class ComprehensiveSentimentCollector:
    """
    Collect sentiment from multiple sources for comprehensive market psychology.
    """
    
    def __init__(self):
        self.scrape_key = SCRAPE_CREATORS_KEY
        self.session = requests.Session()
        self.sentiment_cache = {}
        
    def collect_truth_social(self, usernames: List[str]) -> pd.DataFrame:
        """
        Collect posts from Truth Social accounts.
        Focus on Trump and key policy influencers.
        """
        logger.info(f"Collecting Truth Social posts from {len(usernames)} accounts...")
        
        all_posts = []
        
        for username in usernames:
            try:
                url = 'https://api.scrapecreators.com/v1/truthsocial'
                headers = {'x-api-key': self.scrape_key}
                params = {
                    'username': username.replace('@', ''),
                    'limit': 100  # Last 100 posts
                }
                
                response = self.session.get(url, headers=headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    posts = response.json().get('posts', [])
                    
                    for post in posts:
                        processed = self._process_truth_post(post, username)
                        all_posts.append(processed)
                    
                    logger.info(f"✅ {username}: {len(posts)} posts collected")
                else:
                    logger.warning(f"❌ {username}: API returned {response.status_code}")
                    
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error collecting {username}: {e}")
        
        if all_posts:
            df = pd.DataFrame(all_posts)
            return df
        
        return pd.DataFrame()
    
    def _process_truth_post(self, post: Dict, username: str) -> Dict:
        """
        Process Truth Social post and extract sentiment signals.
        """
        text = post.get('text', '')
        
        # Extract key signals
        processed = {
            'timestamp': pd.to_datetime(post.get('created_at', datetime.now())),
            'username': username,
            'text': text,
            'likes': post.get('likes', 0),
            'reposts': post.get('reposts', 0),
            'replies': post.get('replies', 0),
            
            # Market-relevant keywords
            'mentions_china': bool(re.search(r'(?i)china|chinese|beijing|xi', text)),
            'mentions_tariff': bool(re.search(r'(?i)tariff|duty|trade war|import tax', text)),
            'mentions_agriculture': bool(re.search(r'(?i)farmer|crop|soybean|corn|agriculture', text)),
            'mentions_energy': bool(re.search(r'(?i)oil|gas|energy|fuel|diesel', text)),
            'mentions_inflation': bool(re.search(r'(?i)inflation|price|fed|rate|dollar', text)),
            
            # Sentiment indicators
            'exclamation_count': text.count('!'),
            'caps_ratio': sum(1 for c in text if c.isupper()) / max(len(text), 1),
            'length': len(text),
            
            # Policy signals
            'is_announcement': bool(re.search(r'(?i)announce|breaking|just in|news', text)),
            'is_threat': bool(re.search(r'(?i)will|going to|prepare|warning|consequence', text)),
            'is_deal': bool(re.search(r'(?i)deal|agreement|negotiate|talk|meeting', text))
        }
        
        # Calculate engagement rate
        total_engagement = processed['likes'] + processed['reposts'] + processed['replies']
        processed['engagement_rate'] = total_engagement / max(processed['likes'], 1)
        
        # Simple sentiment score
        processed['raw_sentiment'] = self._calculate_simple_sentiment(text)
        
        return processed
    
    def _calculate_simple_sentiment(self, text: str) -> float:
        """
        Calculate simple sentiment score (-1 to 1).
        """
        # Positive words (market positive for commodities)
        positive_words = [
            'great', 'best', 'win', 'strong', 'boom', 'surge', 'high',
            'deal', 'agreement', 'growth', 'demand', 'shortage', 'tight'
        ]
        
        # Negative words (market negative for commodities)
        negative_words = [
            'bad', 'worst', 'lose', 'weak', 'crash', 'plunge', 'low',
            'tariff', 'war', 'surplus', 'glut', 'oversupply', 'collapse'
        ]
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count + negative_count == 0:
            return 0.0
        
        return (positive_count - negative_count) / (positive_count + negative_count)
    
    def collect_facebook_pages(self, pages: List[str]) -> pd.DataFrame:
        """
        Collect posts from Facebook pages (agricultural organizations).
        """
        logger.info(f"Collecting Facebook posts from {len(pages)} pages...")
        
        all_posts = []
        
        for page in pages:
            try:
                url = 'https://api.scrapecreators.com/v1/facebook/post'
                headers = {'x-api-key': self.scrape_key}
                params = {
                    'page_id': page,
                    'limit': 50
                }
                
                response = self.session.get(url, headers=headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    posts = response.json().get('posts', [])
                    
                    for post in posts:
                        processed = self._process_facebook_post(post, page)
                        all_posts.append(processed)
                    
                    logger.info(f"✅ {page}: {len(posts)} posts collected")
                else:
                    logger.warning(f"❌ {page}: API returned {response.status_code}")
                
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error collecting {page}: {e}")
        
        if all_posts:
            return pd.DataFrame(all_posts)
        
        return pd.DataFrame()
    
    def _process_facebook_post(self, post: Dict, page: str) -> Dict:
        """
        Process Facebook post from agricultural organizations.
        """
        text = post.get('message', '')
        
        processed = {
            'timestamp': pd.to_datetime(post.get('created_time', datetime.now())),
            'page': page,
            'text': text,
            'reactions': post.get('reactions', {}).get('summary', {}).get('total_count', 0),
            'comments': post.get('comments', {}).get('summary', {}).get('total_count', 0),
            'shares': post.get('shares', {}).get('count', 0),
            
            # Agricultural sentiment
            'mentions_harvest': bool(re.search(r'(?i)harvest|planting|yield|acre', text)),
            'mentions_weather': bool(re.search(r'(?i)drought|rain|flood|weather|storm', text)),
            'mentions_prices': bool(re.search(r'(?i)price|market|bushel|premium|basis', text)),
            'mentions_policy': bool(re.search(r'(?i)usda|farm bill|subsidy|insurance', text)),
            
            # Farmer sentiment
            'is_optimistic': bool(re.search(r'(?i)optimistic|hopeful|positive|good year', text)),
            'is_concerned': bool(re.search(r'(?i)concern|worry|difficult|challenge', text)),
            
            'raw_sentiment': self._calculate_simple_sentiment(text)
        }
        
        return processed
    
    def collect_reddit_sentiment(self, subreddits: List[str]) -> pd.DataFrame:
        """
        Collect posts from Reddit (retail trader sentiment).
        """
        logger.info(f"Collecting Reddit posts from {len(subreddits)} subreddits...")
        
        all_posts = []
        
        for subreddit in subreddits:
            try:
                # Reddit JSON API (no auth needed for public data)
                url = f'https://www.reddit.com/r/{subreddit}/hot.json'
                headers = {'User-Agent': 'CBI-V14 Sentiment Collector 1.0'}
                params = {'limit': 100}
                
                response = self.session.get(url, headers=headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    posts = data.get('data', {}).get('children', [])
                    
                    for post in posts:
                        post_data = post.get('data', {})
                        processed = self._process_reddit_post(post_data, subreddit)
                        all_posts.append(processed)
                    
                    logger.info(f"✅ r/{subreddit}: {len(posts)} posts collected")
                else:
                    logger.warning(f"❌ r/{subreddit}: API returned {response.status_code}")
                
                # Reddit rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error collecting r/{subreddit}: {e}")
        
        if all_posts:
            return pd.DataFrame(all_posts)
        
        return pd.DataFrame()
    
    def _process_reddit_post(self, post: Dict, subreddit: str) -> Dict:
        """
        Process Reddit post for retail sentiment.
        """
        title = post.get('title', '')
        text = post.get('selftext', '')
        full_text = f"{title} {text}"
        
        processed = {
            'timestamp': pd.to_datetime(post.get('created_utc', 0), unit='s'),
            'subreddit': subreddit,
            'title': title,
            'text': text[:500],  # Truncate long posts
            'score': post.get('score', 0),
            'num_comments': post.get('num_comments', 0),
            'upvote_ratio': post.get('upvote_ratio', 0.5),
            
            # Trading sentiment
            'mentions_long': bool(re.search(r'(?i)long|bull|call|buy', full_text)),
            'mentions_short': bool(re.search(r'(?i)short|bear|put|sell', full_text)),
            'mentions_commodities': bool(re.search(r'(?i)corn|wheat|soybean|oil|commodity', full_text)),
            
            # Retail indicators
            'is_dd': bool(re.search(r'(?i)dd|due diligence|analysis', full_text)),
            'is_yolo': bool(re.search(r'(?i)yolo|all in|bet', full_text)),
            'is_loss': bool(re.search(r'(?i)loss|lost|down', full_text)),
            
            'raw_sentiment': self._calculate_simple_sentiment(full_text)
        }
        
        # Calculate "heat" score (engagement)
        processed['heat_score'] = (
            processed['score'] * 0.7 + 
            processed['num_comments'] * 0.3
        ) * processed['upvote_ratio']
        
        return processed
    
    def calculate_composite_sentiment(self, 
                                    truth_df: pd.DataFrame,
                                    facebook_df: pd.DataFrame,
                                    reddit_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate weighted composite sentiment from all sources.
        """
        logger.info("Calculating composite sentiment...")
        
        # Aggregate by day
        def aggregate_daily(df, source_name, weight):
            if df.empty:
                return pd.DataFrame()
            
            daily = df.groupby(df['timestamp'].dt.date).agg({
                'raw_sentiment': 'mean',
                'text': 'count'  # Volume of posts
            }).rename(columns={
                'raw_sentiment': f'{source_name}_sentiment',
                'text': f'{source_name}_volume'
            })
            
            daily[f'{source_name}_weight'] = weight
            return daily
        
        # Weight by source importance for commodity markets
        truth_daily = aggregate_daily(truth_df, 'truth', 0.40)  # Trump drives markets
        facebook_daily = aggregate_daily(facebook_df, 'facebook', 0.30)  # Industry sentiment
        reddit_daily = aggregate_daily(reddit_df, 'reddit', 0.30)  # Retail speculation
        
        # Combine
        composite = pd.concat([truth_daily, facebook_daily, reddit_daily], axis=1)
        
        # Calculate weighted sentiment
        sentiment_cols = [col for col in composite.columns if 'sentiment' in col and 'weight' not in col]
        weight_cols = [col for col in composite.columns if 'weight' in col]
        
        composite['composite_sentiment'] = 0
        total_weight = 0
        
        for sent_col, weight_col in zip(sentiment_cols, weight_cols):
            if sent_col in composite.columns and weight_col in composite.columns:
                weight = composite[weight_col].iloc[0] if not composite[weight_col].empty else 0
                composite['composite_sentiment'] += composite[sent_col].fillna(0) * weight
                total_weight += weight
        
        if total_weight > 0:
            composite['composite_sentiment'] /= total_weight
        
        # Add metadata
        composite['total_posts'] = composite[[col for col in composite.columns if 'volume' in col]].sum(axis=1)
        
        return composite
    
    def collect_all_sentiment(self):
        """
        Master function to collect all sentiment data.
        """
        print("="*80)
        print("COLLECTING COMPREHENSIVE SENTIMENT")
        print("="*80)
        
        # Truth Social accounts to monitor
        truth_accounts = [
            '@realDonaldTrump',
            '@DevinNunes',
            '@DonaldJTrumpJr',
            '@TuckerCarlson',
            '@RobertKennedyJr'
        ]
        
        # Facebook pages (agricultural organizations)
        facebook_pages = [
            'AmericanSoybeanAssociation',
            'AmericanFarmBureau',
            'USDA',
            'NationalCornGrowers',
            'USWheatAssociates'
        ]
        
        # Reddit subreddits
        subreddits = [
            'agriculture',
            'farming',
            'commodities',
            'wallstreetbets',
            'economics',
            'Soybeans'
        ]
        
        # Collect from each source
        truth_df = self.collect_truth_social(truth_accounts)
        print(f"Truth Social: {len(truth_df)} posts")
        
        facebook_df = self.collect_facebook_pages(facebook_pages)
        print(f"Facebook: {len(facebook_df)} posts")
        
        reddit_df = self.collect_reddit_sentiment(subreddits)
        print(f"Reddit: {len(reddit_df)} posts")
        
        # Calculate composite
        composite_df = self.calculate_composite_sentiment(truth_df, facebook_df, reddit_df)
        print(f"Composite sentiment: {len(composite_df)} days")
        
        # Save all data
        if not truth_df.empty:
            truth_df.to_parquet(RAW_DIR / "truth_social_sentiment.parquet")
        if not facebook_df.empty:
            facebook_df.to_parquet(RAW_DIR / "facebook_sentiment.parquet")
        if not reddit_df.empty:
            reddit_df.to_parquet(RAW_DIR / "reddit_sentiment.parquet")
        if not composite_df.empty:
            composite_df.to_parquet(RAW_DIR / "composite_sentiment.parquet")
        
        print("\n" + "="*80)
        print("SENTIMENT COLLECTION COMPLETE")
        print("="*80)
        
        return {
            'truth_social': len(truth_df),
            'facebook': len(facebook_df),
            'reddit': len(reddit_df),
            'composite_days': len(composite_df)
        }


if __name__ == "__main__":
    # IMPORTANT: Move API key to environment variable!
    # export SCRAPE_CREATORS_KEY='your_key_here'
    
    collector = ComprehensiveSentimentCollector()
    results = collector.collect_all_sentiment()
    print(f"\nResults: {results}")
