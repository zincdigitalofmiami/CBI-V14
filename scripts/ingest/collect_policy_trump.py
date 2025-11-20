#!/usr/bin/env python3
"""
Comprehensive Sentiment & Policy Intelligence Collection
========================================================
Collects sentiment and policy signals from multiple sources every 15 minutes.

Coverage Areas:
- Soybean oil sentiment (price direction, market outlook, demand/supply sentiment)
- Biofuel sentiment (market outlook, production trends, demand forecasts)
- Trade relations (US-China, US-Brazil, US-Argentina, global trade relations)
- ICE movements (Intercontinental Exchange announcements, rule changes, price movements)
- Price direction sentiment (bullish, bearish, neutral price movements)
- Tariffs (general tariffs, China tariffs, EU tariffs, other countries - NOT Trump-specific)

Sources:
- Truth Social: Trump + key policy accounts (via ScrapeCreators API)
- Social Media: Facebook, Twitter/X, LinkedIn, Bluesky (NO Reddit, YouTube, TikTok)
- Aggregated News: NewsAPI, Alpha Vantage News, RSS feeds, Google Search
- ICE Data: Intercontinental Exchange announcements, regulatory updates
- Tariffs: USTR announcements, trade policy updates, Section 301/232 actions (non-Trump)
- Executive Orders: White House executive orders, presidential proclamations
- Policy Feeds: USDA announcements, EPA RFS updates, trade news

Prefix: `policy_trump_*` on all columns except `date`, `timestamp`
(Note: Prefix name retained for backward compatibility, but now covers broader sentiment)

Coverage: Real-time (15-min cadence) + historical backfill

ScrapeCreators API:
- Uses ScrapeCreators REST API for Truth Social + social media data collection
- API key stored in macOS keychain: cbi-v14.SCRAPECREATORS_API_KEY
- See docs/setup/SCRAPECREATORS_API.md for full documentation
- To add new pulls: extend account lists and run script

Author: AI Assistant
Date: November 17, 2025
Last Updated: November 17, 2025
Status: Active - Core sentiment collection pipeline
Reference: docs/plans/MASTER_PLAN.md
"""

import requests
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import logging
import time
import sys
import os
import hashlib
from bs4 import BeautifulSoup
import re

# Add src to path for keychain access
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.keychain_manager import get_api_key

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
EXTERNAL_DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
RAW_DIR = EXTERNAL_DRIVE / "TrainingData/raw/policy_trump"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Truth Social accounts to monitor (via ScrapeCreators API)
# Only prominent/verified accounts work due to Truth Social API limitations
TRUTH_SOCIAL_ACCOUNTS = [
    'realDonaldTrump',  # @realDonaldTrump (verified, primary)
    'DonaldJTrumpJr',   # @DonaldJTrumpJr (verified, policy signals)
    'EricTrump',        # @EricTrump (verified, business/policy)
]

# Social Media accounts (Facebook, Twitter/X, LinkedIn only - NO Reddit, YouTube, TikTok)
SOCIAL_MEDIA_ACCOUNTS = {
    'twitter': [
        'realDonaldTrump',  # Twitter/X handle
        'realDonaldTrumpJr',
        'EricTrump',
    ],
    'facebook': [
        'DonaldTrump',  # Facebook page
        'DonaldJTrumpJr',
    ],
    'linkedin': [
        'donald-trump',  # LinkedIn profile/page
        'trump-organization',
    ],
}

# Comprehensive Search Query Taxonomy for Google Search API
# Organized by shock signal category with keywords for each
SEARCH_QUERIES = {
    # Policy & Legislation
    'policy_lobbying': [
        'biofuel credit lobby', 'renewable fuel standard hearing', 'Farm Bill markup',
        'EPA RIN waiver', 'agriculture lobby disclosure', 'crop insurance budget',
    ],
    'policy_legislation': [
        'biofuel mandate bill', 'renewable fuel standard legislation', 'Farm Bill 2024',
        'agriculture subsidy bill', 'trade policy legislation',
    ],
    'policy_regulation': [
        'EPA RFS announcement', 'USDA regulation update', 'CFTC rule change',
        'biofuel mandate regulation', 'agriculture policy update',
    ],
    
    # Supply & Production
    'supply_farm_reports': [
        'soybean yield report', 'corn harvest report', 'crop progress report',
        'USDA crop report', 'agriculture production report',
    ],
    'supply_labour': [
        'farm labor strike', 'agriculture worker shortage', 'harvest labor',
        'farm worker union', 'agriculture employment',
    ],
    'supply_weather': [
        'drought soybean', 'flood corn harvest', 'freeze crop damage',
        'weather agriculture impact', 'crop weather report',
    ],
    
    # Trade & Geopolitics
    'trade_china': [
        'China soybean imports', 'China agriculture trade', 'China soybean purchase',
        'China trade deal soybean', 'China import quota',
    ],
    'trade_argentina': [
        'Argentina crush rate', 'Argentina soybean export', 'Argentina agriculture',
        'Argentina soybean production', 'Argentina trade policy',
    ],
    'trade_palm': [
        'Indonesian palm tax', 'Malaysia palm export', 'palm oil export quota',
        'Indonesia palm policy', 'Malaysia palm production',
    ],
    'trade_currency': [
        'Brazil real soybean', 'Argentina peso agriculture', 'currency agriculture trade',
        'FX agriculture impact', 'exchange rate soybean',
    ],
    
    # Logistics
    'logistics_water': [
        'Mississippi river levels', 'Parana river shipping', 'river navigation agriculture',
        'waterway shipping delay', 'river transport agriculture',
    ],
    'logistics_port': [
        'port congestion agriculture', 'grain port delay', 'agriculture shipping port',
        'export port congestion', 'grain terminal delay',
    ],
    'logistics_strike': [
        'trucker strike agriculture', 'rail strike grain', 'shipping strike agriculture',
        'transport strike crop', 'logistics strike agriculture',
    ],
    
    # Biofuel & Energy
    'biofuel_policy': [
        'EPA biofuel announcement', 'RFS waiver', 'biofuel mandate update',
        'renewable fuel standard', 'biofuel credit policy',
        'RIN price movement', 'biodiesel production', 'ethanol blend mandate',
        'biofuel credit trading', 'renewable fuel volume obligation',
    ],
    'biofuel_sentiment': [
        'biofuel market outlook', 'biodiesel demand forecast', 'ethanol production trend',
        'biofuel industry sentiment', 'renewable fuel market analysis',
        'biofuel credit market sentiment', 'biodiesel price forecast',
    ],
    'biofuel_spread': [
        'petro renewable spread', 'biofuel crude spread', 'ethanol gasoline spread',
        'biodiesel diesel spread', 'renewable fuel spread',
    ],
    'energy_crude': [
        'crude oil agriculture', 'oil price soybean', 'energy price crop',
        'crude impact agriculture', 'oil agriculture correlation',
    ],
    
    # Macro & Risk
    'macro_volatility': [
        'VIX agriculture', 'volatility soybean', 'market volatility crop',
        'VIX spike agriculture', 'volatility agriculture impact',
    ],
    'macro_fx': [
        'Brazil real agriculture', 'Argentina peso crop', 'FX agriculture',
        'currency agriculture', 'exchange rate crop',
    ],
    'macro_rate': [
        'Fed agriculture', 'interest rate soybean', 'Fed policy agriculture',
        'rate hike agriculture', 'monetary policy crop',
    ],
    
    # Market Structure
    'market_positioning': [
        'CFTC soybean positions', 'speculator positions agriculture', 'hedge fund agriculture',
        'CFTC commitment traders', 'positioning agriculture',
    ],
    'market_structure': [
        'CME rule change', 'ICE exchange update', 'margin hike agriculture',
        'exchange rule agriculture', 'futures exchange update',
    ],
    
    # Soybean Oil Specific Sentiment
    'soybean_oil_sentiment': [
        'soybean oil price forecast', 'soybean oil market outlook', 'soybean oil demand',
        'soybean oil supply sentiment', 'soybean oil price direction', 'soybean oil trend',
        'soybean oil market analysis', 'soybean oil price prediction', 'soybean oil sentiment',
        'soybean oil bullish', 'soybean oil bearish', 'soybean oil price movement',
    ],
    
    # Trade Relations (Non-Trump)
    'trade_relations_us_china': [
        'US China trade relations', 'US China agriculture trade', 'China US soybean trade',
        'US China trade agreement agriculture', 'China US trade relations update',
    ],
    'trade_relations_us_brazil': [
        'US Brazil trade relations', 'US Brazil agriculture trade', 'Brazil US trade agreement',
        'US Brazil trade policy', 'Brazil US soybean trade',
    ],
    'trade_relations_us_argentina': [
        'US Argentina trade relations', 'US Argentina agriculture trade', 'Argentina US trade',
        'US Argentina trade policy', 'Argentina US soybean trade',
    ],
    'trade_relations_global': [
        'international trade relations agriculture', 'global trade relations soybean',
        'trade relations commodity markets', 'international agriculture trade',
    ],
    
    # ICE (Intercontinental Exchange) Movements
    'ice_exchange_movements': [
        'ICE exchange announcement', 'ICE futures update', 'ICE rule change',
        'ICE margin requirement', 'ICE contract specification change',
        'ICE trading halt', 'ICE market update', 'ICE exchange news',
        'ICE futures contract change', 'ICE regulatory update',
    ],
    'ice_price_movements': [
        'ICE soybean oil price', 'ICE futures price movement', 'ICE contract price',
        'ICE trading activity', 'ICE volume spike', 'ICE open interest change',
    ],
    
    # Price Direction Sentiment
    'price_direction_bullish': [
        'soybean oil price rise', 'soybean oil rally', 'soybean oil price increase',
        'soybean oil bullish trend', 'soybean oil price up', 'soybean oil surge',
        'soybean oil price gain', 'soybean oil price climb',
    ],
    'price_direction_bearish': [
        'soybean oil price drop', 'soybean oil decline', 'soybean oil price decrease',
        'soybean oil bearish trend', 'soybean oil price down', 'soybean oil fall',
        'soybean oil price loss', 'soybean oil price slide',
    ],
    'price_direction_neutral': [
        'soybean oil price stable', 'soybean oil price range', 'soybean oil consolidation',
        'soybean oil price flat', 'soybean oil sideways', 'soybean oil price steady',
    ],
    
    # Tariffs (Non-Trump Related)
    'tariff_general': [
        'soybean tariff', 'agriculture tariff', 'trade tariff agriculture',
        'import tariff soybean', 'export tariff agriculture', 'tariff policy agriculture',
        'Section 301 tariff agriculture', 'Section 232 tariff agriculture',
        'retaliatory tariff agriculture', 'trade war tariff agriculture',
    ],
    'tariff_china': [
        'China tariff agriculture', 'China soybean tariff', 'China import tariff',
        'China trade tariff', 'China retaliatory tariff',
    ],
    'tariff_eu': [
        'EU tariff agriculture', 'European Union tariff', 'EU import tariff agriculture',
        'EU trade tariff', 'EU soybean tariff',
    ],
    'tariff_other_countries': [
        'India tariff agriculture', 'Brazil tariff', 'Argentina tariff',
        'Mexico tariff agriculture', 'Canada tariff agriculture',
    ],
}

# Region keywords for classification
REGION_KEYWORDS = {
    'US': ['United States', 'USA', 'US', 'America', 'American'],
    'Brazil': ['Brazil', 'Brazilian', 'Brasil'],
    'Argentina': ['Argentina', 'Argentine', 'Argentinian'],
    'China': ['China', 'Chinese', 'Beijing'],
    'SE_Asia': ['Indonesia', 'Malaysia', 'Thailand', 'Philippines', 'Southeast Asia'],
    'EU': ['European Union', 'EU', 'Europe', 'European'],
}

# Source credibility weights (0.50-1.00) for policy shock scoring
SOURCE_CREDIBILITY = {
    # Government sources → 1.00
    'usda.gov': 1.0,
    'epa.gov': 1.0,
    'ustr.gov': 1.0,
    'whitehouse.gov': 1.0,
    'federalregister.gov': 1.0,
    'gov': 1.0,  # Any .gov domain
    
    # Premium press (Reuters/Bloomberg/WSJ) → 0.95
    'reuters.com': 0.95,
    'bloomberg.com': 0.95,
    'wsj.com': 0.95,
    'ft.com': 0.95,
    
    # Major press (CNBC, AP, regional WSJ) → 0.90
    'cnbc.com': 0.90,
    'ap.org': 0.90,
    'apnews.com': 0.90,
    
    # Trade publications (AgWeb, DTN, Co-ops) → 0.80
    'agriculture.com': 0.80,
    'agweb.com': 0.80,
    'dtn.com': 0.80,
    
    # Unknown blog or unverified domain → 0.50
    'default': 0.50,
}

# Topic multipliers for policy shock scoring
# Higher multipliers = higher impact (policy/trade dominate, logistics/market lower)
TOPIC_MULTIPLIERS = {
    # Policy (highest impact) → 1.00
    'policy_lobbying': 1.00,
    'policy_legislation': 1.00,
    'policy_regulation': 1.00,
    
    # Trade (very high impact) → 0.95
    'trade_china': 0.95,
    'trade_argentina': 0.95,
    'trade_palm': 0.95,
    'trade_currency': 0.95,
    
    # Biofuel/Energy policy → 0.85
    'biofuel_policy': 0.85,
    'biofuel_sentiment': 0.85,
    'biofuel_spread': 0.85,
    'energy_crude': 0.85,
    
    # Supply (farm/weather/labor) → 0.80
    'supply_farm_reports': 0.80,
    'supply_labour': 0.80,
    'supply_weather': 0.80,
    
    # Logistics (water/port) → 0.70
    'logistics_water': 0.70,
    'logistics_port': 0.70,
    'logistics_strike': 0.70,
    
    # Macro (volatility/FX/rates) → 0.60
    'macro_volatility': 0.60,
    'macro_fx': 0.60,
    'macro_rate': 0.60,
    
    # Market structure/positioning (lowest impact) → 0.50
    'market_positioning': 0.50,
    'market_structure': 0.50,
    
    # Soybean Oil Sentiment → 0.90 (high impact for ZL)
    'soybean_oil_sentiment': 0.90,
    
    # Trade Relations → 0.88 (very high impact)
    'trade_relations_us_china': 0.88,
    'trade_relations_us_brazil': 0.88,
    'trade_relations_us_argentina': 0.88,
    'trade_relations_global': 0.85,
    
    # ICE Movements → 0.80 (market structure impact)
    'ice_exchange_movements': 0.80,
    'ice_price_movements': 0.75,
    
    # Price Direction → 0.70 (sentiment indicator)
    'price_direction_bullish': 0.70,
    'price_direction_bearish': 0.70,
    'price_direction_neutral': 0.60,
    
    # Tariffs (Non-Trump) → 0.92 (very high impact)
    'tariff_general': 0.92,
    'tariff_china': 0.95,
    'tariff_eu': 0.90,
    'tariff_other_countries': 0.88,
    
    # Default fallback
    'default': 0.75,  # Mid-range for unknown categories
}

# News sources for aggregation
NEWS_SOURCES = {
    'rss_feeds': [
        'https://www.reuters.com/markets/commodities/rss',
        'https://feeds.bloomberg.com/markets/news.rss',
        'https://www.cnbc.com/id/10001147/device/rss/rss.html',
        'https://www.agriculture.com/rss/news',
        'https://www.agweb.com/rss/news',
    ],
    'api_sources': ['newsapi', 'alphavantage'],  # NewsAPI, Alpha Vantage News
}

# ICE (Intercontinental Exchange) data sources
ICE_SOURCES = [
    'https://www.theice.com/news-and-events',
    'https://www.theice.com/publicdocs/news/',
]

# Tariff sources
TARIFF_SOURCES = [
    'https://ustr.gov/about-us/policy-offices/press-office/press-releases',
    'https://ustr.gov/trade-agreements/agreements-under-negotiation',
    'https://www.federalregister.gov/documents/search#conditions%5Btype%5D=PRESDOCU',
]

# Executive Order sources
EXECUTIVE_ORDER_SOURCES = [
    'https://www.federalregister.gov/presidential-documents/executive-orders',
    'https://www.whitehouse.gov/briefing-room/presidential-actions/',
]

# API Keys
SCRAPE_CREATORS_KEY = get_api_key('SCRAPE_CREATORS_KEY') or os.getenv('SCRAPE_CREATORS_KEY')
NEWSAPI_KEY = get_api_key('NEWSAPI_KEY') or os.getenv('NEWSAPI_KEY')
ALPHA_VANTAGE_KEY = get_api_key('ALPHA_VANTAGE_API_KEY') or os.getenv('ALPHA_VANTAGE_API_KEY')

def collect_truth_social_profiles(usernames: list) -> pd.DataFrame:
    """
    Collect Truth Social profile metadata via ScrapeCreators API.
    
    Uses ScrapeCreators REST API endpoint: /v1/truthsocial/profile
    Validates accounts exist and collects profile metadata.
    
    Args:
        usernames: List of Truth Social usernames (without @)
    
    Returns:
        DataFrame with profile metadata
    """
    logger.info(f"Validating Truth Social profiles for {len(usernames)} accounts...")
    
    all_profiles = []
    
    if not SCRAPE_CREATORS_KEY:
        return pd.DataFrame()
    
    for username in usernames:
        try:
            url = 'https://api.scrapecreators.com/v1/truthsocial/profile'
            headers = {'x-api-key': SCRAPE_CREATORS_KEY}
            params = {
                'handle': username.replace('@', ''),  # API requires 'handle' parameter
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    profile = {
                        'username': username,
                        'display_name': data.get('display_name', ''),
                        'account_id': data.get('id', ''),
                        'created_at': pd.to_datetime(data.get('created_at', ''), errors='coerce'),
                        'locked': data.get('locked', False),
                        'bot': data.get('bot', False),
                        'url': data.get('url', ''),
                        'verified': not data.get('locked', True),  # Assume verified if not locked
                    }
                    all_profiles.append(profile)
                    logger.info(f"✅ Profile validated: {username} ({data.get('display_name', '')})")
                else:
                    logger.warning(f"❌ Profile validation failed for {username}")
            
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            logger.debug(f"Error validating profile for {username}: {e}")
    
    if all_profiles:
        return pd.DataFrame(all_profiles)
    
    return pd.DataFrame()

def collect_truth_social_posts(usernames: list, limit: int = 100) -> pd.DataFrame:
    """
    Collect Truth Social posts from specified accounts via ScrapeCreators API.
    
    Uses ScrapeCreators REST API endpoints:
    - /v1/truthsocial/profile (for validation)
    - /v1/truthsocial/user/posts (for posts)
    Only prominent/verified accounts work due to Truth Social API limitations.
    
    Args:
        usernames: List of Truth Social usernames (without @)
        limit: Maximum posts per account
    
    Returns:
        DataFrame with posts and metadata
    """
    logger.info(f"Collecting Truth Social posts from {len(usernames)} accounts (via ScrapeCreators API)...")
    
    all_posts = []
    
    if not SCRAPE_CREATORS_KEY:
        logger.warning("⚠️  No ScrapeCreators API key found. Truth Social collection will be limited.")
        logger.warning("   Set SCRAPE_CREATORS_KEY in keychain or environment for full access.")
        return pd.DataFrame()
    
    # First validate profiles (optional, but helps ensure accounts exist)
    valid_profiles = collect_truth_social_profiles(usernames)
    valid_usernames = set(valid_profiles['username'].tolist()) if not valid_profiles.empty else set(usernames)
    
    for username in usernames:
        # Skip if profile validation failed (unless no profiles were collected)
        if valid_profiles.empty or username in valid_usernames:
            try:
                # ScrapeCreators Truth Social API endpoint for posts
                url = 'https://api.scrapecreators.com/v1/truthsocial/user/posts'
                headers = {'x-api-key': SCRAPE_CREATORS_KEY}
                params = {
                    'handle': username.replace('@', ''),  # API requires 'handle' parameter
                    'limit': limit
                }
                
                response = requests.get(url, headers=headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    posts = data.get('posts', []) or data.get('data', [])
                    
                    for post in posts:
                        # Truth Social API returns: text, id, created_at, in_reply_to_id, quote_id
                        processed = {
                            'timestamp': pd.to_datetime(post.get('created_at', datetime.now()), errors='coerce'),
                            'username': username,
                            'text': post.get('text', '') or post.get('content', ''),
                            'likes': post.get('likes', 0) or post.get('reactionCount', 0) or post.get('like_count', 0),
                            'reposts': post.get('reposts', 0) or post.get('shares', 0) or post.get('repost_count', 0),
                            'replies': post.get('replies', 0) or post.get('commentCount', 0) or post.get('reply_count', 0),
                            'url': post.get('url', '') or post.get('permalink', '') or f"https://truthsocial.com/@{username}/post/{post.get('id', '')}",
                            'post_id': post.get('id', ''),
                        }
                        all_posts.append(processed)
                    
                    logger.info(f"✅ {username}: {len(posts)} posts collected")
                else:
                    logger.warning(f"❌ {username}: API returned {response.status_code}")
                    if response.status_code == 404:
                        logger.debug(f"   Response: {response.text[:200]}")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error collecting {username}: {e}")
    
    if all_posts:
        df = pd.DataFrame(all_posts)
        return df
    
    return pd.DataFrame()

def classify_policy_sentiment(text: str) -> dict:
    """
    Classify policy sentiment for ZL (soybean oil).
    
    Args:
        text: Post text
    
    Returns:
        Dict with sentiment scores and classifications
    """
    text_lower = text.lower()
    
    # Bullish keywords (positive for ZL)
    bullish_keywords = [
        'biofuel', 'ethanol', 'biodiesel', 'renewable', 'mandate', 'RFS',
        'china', 'purchase', 'buy', 'deal', 'agreement', 'trade deal',
        'export', 'demand', 'strong', 'growth'
    ]
    
    # Bearish keywords (negative for ZL)
    bearish_keywords = [
        'tariff', 'tax', 'ban', 'restriction', 'sanction', 'war', 'conflict',
        'weak', 'decline', 'drop', 'fall', 'recession', 'crisis'
    ]
    
    bullish_count = sum(1 for kw in bullish_keywords if kw in text_lower)
    bearish_count = sum(1 for kw in bearish_keywords if kw in text_lower)
    
    # Calculate sentiment score (-1 to +1)
    if bullish_count + bearish_count == 0:
        sentiment_score = 0.0
    else:
        sentiment_score = (bullish_count - bearish_count) / (bullish_count + bearish_count + 1)
    
    # Classify
    if sentiment_score > 0.2:
        sentiment_class = 'bullish'
    elif sentiment_score < -0.2:
        sentiment_class = 'bearish'
    else:
        sentiment_class = 'neutral'
    
    # Identify policy categories
    policy_categories = []
    for category, keywords in POLICY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            policy_categories.append(category)
    
    return {
        'policy_trump_sentiment_score': sentiment_score,
        'policy_trump_sentiment_class': sentiment_class,
        'policy_trump_bullish_keywords': bullish_count,
        'policy_trump_bearish_keywords': bearish_count,
        'policy_trump_categories': ','.join(policy_categories) if policy_categories else None,
    }

def collect_social_media_posts() -> pd.DataFrame:
    """
    Collect posts from Facebook, Twitter/X, LinkedIn, Bluesky (via ScrapeCreators API).
    REPUTABLE/VERIFIED SOURCES ONLY - NO Reddit, YouTube, or TikTok.
    
    Uses ScrapeCreators REST API endpoints:
    - /v1/twitter/user-tweets
    - /v1/facebook/profile/posts
    - /v1/linkedin/profile
    - /bluesky/user/posts
    
    Returns:
        DataFrame with social media posts
    """
    logger.info("Collecting social media posts (Facebook, Twitter/X, LinkedIn, Bluesky via ScrapeCreators API)...")
    
    all_posts = []
    
    if not SCRAPE_CREATORS_KEY:
        logger.warning("⚠️  No ScrapeCreators API key found. Social media collection will be limited.")
        return pd.DataFrame()
    
    # Twitter/X - correct endpoint
    for account in SOCIAL_MEDIA_ACCOUNTS.get('twitter', []):
        try:
            url = 'https://api.scrapecreators.com/v1/twitter/user-tweets'
            headers = {'x-api-key': SCRAPE_CREATORS_KEY}
            params = {
                'handle': account.replace('@', ''),  # Twitter API requires 'handle' parameter
                'limit': 50  # Recent posts (API returns up to 100 popular tweets)
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                posts = data.get('tweets', []) or data.get('posts', []) or data.get('data', [])
                
                for post in posts:
                    processed = {
                        'timestamp': pd.to_datetime(post.get('created_at', post.get('publishTime', datetime.now())), errors='coerce'),
                        'platform': 'twitter',
                        'username': account,
                        'text': post.get('text', '') or post.get('content', ''),
                        'likes': post.get('likes', 0) or post.get('favorite_count', 0),
                        'shares': post.get('retweets', 0) or post.get('retweet_count', 0),
                        'comments': post.get('replies', 0) or post.get('reply_count', 0),
                        'url': post.get('url', ''),
                    }
                    all_posts.append(processed)
                
                logger.info(f"✅ twitter/{account}: {len(posts)} posts collected")
            else:
                logger.warning(f"❌ twitter/{account}: API returned {response.status_code}")
                if response.status_code == 404:
                    logger.debug(f"   Response: {response.text[:200]}")
            
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            logger.debug(f"Error collecting twitter/{account}: {e}")
    
    # Facebook - correct endpoint
    for account in SOCIAL_MEDIA_ACCOUNTS.get('facebook', []):
        try:
            url = 'https://api.scrapecreators.com/v1/facebook/profile/posts'
            headers = {'x-api-key': SCRAPE_CREATORS_KEY}
            # Use pageId if available, otherwise use URL
            params = {
                'url': f'https://www.facebook.com/{account}',
                'limit': 50  # API returns 3 posts at a time, but we request up to 50
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                posts = data.get('posts', []) or data.get('data', [])
                
                for post in posts:
                    processed = {
                        'timestamp': pd.to_datetime(post.get('publishTime', datetime.now()), unit='s', errors='coerce'),
                        'platform': 'facebook',
                        'username': account,
                        'text': post.get('text', ''),
                        'likes': post.get('reactionCount', 0) or post.get('likes', 0),
                        'shares': post.get('shares', 0),
                        'comments': post.get('commentCount', 0) or post.get('comments', 0),
                        'url': post.get('url', '') or post.get('permalink', ''),
                    }
                    all_posts.append(processed)
                
                logger.info(f"✅ facebook/{account}: {len(posts)} posts collected")
            else:
                logger.warning(f"❌ facebook/{account}: API returned {response.status_code}")
                if response.status_code == 404:
                    logger.debug(f"   Response: {response.text[:200]}")
            
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            logger.debug(f"Error collecting facebook/{account}: {e}")
    
    # LinkedIn - profile endpoint (requires URL parameter)
    for account in SOCIAL_MEDIA_ACCOUNTS.get('linkedin', []):
        try:
            url = 'https://api.scrapecreators.com/v1/linkedin/profile'
            headers = {'x-api-key': SCRAPE_CREATORS_KEY}
            # LinkedIn API requires full URL
            linkedin_url = f"https://www.linkedin.com/in/{account}" if not account.startswith('http') else account
            params = {
                'url': linkedin_url,  # LinkedIn API requires 'url' parameter
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                # LinkedIn profile endpoint returns profile info, not posts
                # Posts would need a separate endpoint if available
                logger.info(f"✅ linkedin/{account}: Profile data collected")
            else:
                logger.warning(f"❌ linkedin/{account}: API returned {response.status_code}")
                if response.status_code == 400:
                    logger.debug(f"   Response: {response.text[:200]}")
            
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            logger.debug(f"Error collecting linkedin/{account}: {e}")
    
    # Bluesky - posts endpoint
    for account in SOCIAL_MEDIA_ACCOUNTS.get('bluesky', []):
        try:
            url = 'https://api.scrapecreators.com/bluesky/user/posts'
            headers = {'x-api-key': SCRAPE_CREATORS_KEY}
            params = {
                'handle': account.replace('@', ''),  # Bluesky uses 'handle' parameter
                'limit': 50  # Recent posts
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                posts = data.get('posts', []) or data.get('data', [])
                
                for post in posts:
                    processed = {
                        'timestamp': pd.to_datetime(post.get('created_at', post.get('publishTime', datetime.now())), errors='coerce'),
                        'platform': 'bluesky',
                        'username': account,
                        'text': post.get('text', '') or post.get('content', '') or post.get('record', {}).get('text', ''),
                        'likes': post.get('likes', 0) or post.get('likeCount', 0),
                        'shares': post.get('reposts', 0) or post.get('repostCount', 0),
                        'comments': post.get('replies', 0) or post.get('replyCount', 0),
                        'url': post.get('url', '') or post.get('uri', ''),
                    }
                    all_posts.append(processed)
                
                logger.info(f"✅ bluesky/{account}: {len(posts)} posts collected")
            elif response.status_code == 404:
                # Account doesn't exist - skip gracefully
                logger.info(f"⚠️  bluesky/{account}: Account not found (skipping)")
            else:
                logger.warning(f"❌ bluesky/{account}: API returned {response.status_code}")
                if response.status_code == 400:
                    logger.debug(f"   Response: {response.text[:200]}")
            
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            logger.debug(f"Error collecting bluesky/{account}: {e}")
    
    if all_posts:
        df = pd.DataFrame(all_posts)
        return df
    
    return pd.DataFrame()

def classify_category_to_prefix_buckets(category: str) -> list:
    """
    Map category to prefix-based schema buckets for downstream joins/models.
    
    Schema Taxonomy:
    - policy_*: lobbying, legislation, regulation, executive orders, EPA/USTR/White House
    - trade_*: country-labeled trade (trade_china, trade_argentina, trade_palm, trade_currency)
    - biofuel_*: RFS/RIN/biodiesel/ethanol spreads and policies
    - supply_*: farm reports, weather, labor, crop progress (co-ops, NASS, USDA)
    - logistics_*: river levels, ports, strikes, shipping constraints
    - macro_*: volatility, FX, rates, Fed comments
    - market_*: positioning, market-structure, exchange rules/margin
    - energy_*: crude/refinery/energy shocks (if not covered by biofuel)
    
    Args:
        category: Category from SEARCH_QUERIES (e.g., 'policy_lobbying', 'trade_china')
    
    Returns:
        List of prefix buckets this category belongs to (supports multi-tag)
    """
    # Policy bucket
    if category.startswith('policy_'):
        return ['policy']
    
    # Trade bucket
    if category.startswith('trade_'):
        return ['trade']
    
    # Biofuel bucket
    if category.startswith('biofuel_'):
        return ['biofuel']
    
    # Supply bucket
    if category.startswith('supply_'):
        return ['supply']
    
    # Logistics bucket
    if category.startswith('logistics_'):
        return ['logistics']
    
    # Macro bucket
    if category.startswith('macro_'):
        return ['macro']
    
    # Market bucket
    if category.startswith('market_'):
        return ['market']
    
    # Energy bucket
    if category.startswith('energy_'):
        return ['energy']
    
    # Soybean oil sentiment (affects both market and supply)
    if category.startswith('soybean_oil_'):
        return ['market', 'supply']
    
    # Trade relations (goes to trade bucket)
    if category.startswith('trade_relations_'):
        return ['trade']
    
    # ICE movements (market structure)
    if category.startswith('ice_'):
        return ['market']
    
    # Price direction (market sentiment)
    if category.startswith('price_direction_'):
        return ['market']
    
    # Tariffs (affects both trade and policy)
    if category.startswith('tariff_'):
        return ['trade', 'policy']
    
    # Default fallback
    return ['policy']  # Default to policy for unknown categories

def classify_source_type(url: str, domain: str) -> str:
    """
    Classify source type based on URL/domain.
    
    Returns:
        Source type: 'news_api', 'rss', 'gov_press', 'social_media', 'google_search'
    """
    domain_lower = domain.lower()
    
    # Government sources
    if any(gov in domain_lower for gov in ['.gov', 'whitehouse.gov', 'federalregister.gov']):
        return 'gov_press'
    
    # Social media
    if any(social in domain_lower for social in ['twitter.com', 'facebook.com', 'linkedin.com', 'truthsocial.com']):
        return 'social_media'
    
    # RSS/news aggregators
    if 'google_search' in url or 'scrapecreators' in url:
        return 'google_search'
    
    # Default to news_api for news sites
    return 'news_api'

def collect_google_search_news() -> pd.DataFrame:
    """
    Collect news via Google Search API (ScrapeCreators) with comprehensive taxonomy.
    
    Covers: Policy, Supply, Trade, Logistics, Biofuel, Macro, Market Structure
    Returns structured data with classification, sentiment, and metadata.
    
    Schema Classification:
    - Every record gets prefix buckets (policy_*, trade_*, biofuel_*, etc.)
    - Multi-tag support for categories spanning multiple buckets
    - All fields prefixed with policy_trump_* for consistency
    
    Returns:
        DataFrame with search results and full metadata
    """
    logger.info("Collecting Google Search news (comprehensive shock signal coverage)...")
    
    all_results = []
    
    if not SCRAPE_CREATORS_KEY:
        logger.warning("⚠️  No ScrapeCreators API key found. Google Search collection will be skipped.")
        return pd.DataFrame()
    
    # Collect from all search query categories
    for category, queries in SEARCH_QUERIES.items():
        logger.info(f"  Searching category: {category} ({len(queries)} queries)")
        
        for query in queries:
            try:
                url = 'https://api.scrapecreators.com/v1/google/search'
                headers = {'x-api-key': SCRAPE_CREATORS_KEY}
                params = {
                    'query': query,
                    'limit': 10  # Top 10 results per query
                }
                
                response = requests.get(url, headers=headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', []) or data.get('data', [])
                    
                    for result in results:
                        # Extract domain for credibility scoring
                        result_url = result.get('url', '')
                        domain = result_url.split('/')[2] if '/' in result_url and len(result_url.split('/')) > 2 else ''
                        
                        # Classify region
                        text_lower = (result.get('title', '') + ' ' + result.get('description', '')).lower()
                        regions = [r for r, keywords in REGION_KEYWORDS.items() 
                                  if any(kw.lower() in text_lower for kw in keywords)]
                        region = regions[0] if regions else 'Unknown'
                        
                        # Classify to prefix buckets (supports multi-tag)
                        prefix_buckets = classify_category_to_prefix_buckets(category)
                        
                        # Classify source type
                        source_type = classify_source_type(result_url, domain)
                        
                        # Calculate confidence based on source credibility
                        credibility = SOURCE_CREDIBILITY.get(domain, SOURCE_CREDIBILITY['default'])
                        
                        # Classify sentiment (rule-based, can be enhanced with ML)
                        sentiment_result = classify_policy_sentiment(
                            result.get('title', '') + ' ' + result.get('description', '')
                        )
                        
                        # Create unique ID from URL hash
                        url_hash = hashlib.md5(result_url.encode()).hexdigest()[:16]
                        
                        # Get sentiment score
                        sentiment_score = sentiment_result.get('policy_trump_sentiment_score', 0.0)
                        sentiment_class = sentiment_result.get('policy_trump_sentiment_class', 'neutral')
                        
                        # Calculate topic multiplier
                        topic_multiplier = TOPIC_MULTIPLIERS.get(category, TOPIC_MULTIPLIERS['default'])
                        
                        # Calculate recency decay (exp(-Δhours / 24))
                        # Google Search doesn't provide publish date, so use current time
                        # For other sources with actual publish dates, calculate Δhours
                        recency_decay = 1.0  # Default to 1.0 (current) if no publish date
                        
                        # Frequency penalty (will be calculated later when we have all results)
                        # For now, set to 1.0, will recalculate after deduplication
                        frequency_penalty = 1.0
                        
                        # Calculate policy shock score
                        # policy_trump_score = source_confidence * topic_multiplier * abs(sentiment_score) * recency_decay * frequency_penalty
                        policy_trump_score = credibility * topic_multiplier * abs(sentiment_score) * recency_decay * frequency_penalty
                        
                        # Calculate signed score for training (negative for bearish)
                        policy_trump_score_signed = policy_trump_score * (1.0 if sentiment_score >= 0 else -1.0)
                        
                        # Build record with all required fields
                        processed = {
                            'timestamp': datetime.now(),  # Google Search doesn't provide publish date
                            'date': datetime.now().date(),  # For daily joins
                            
                            # Source identification
                            'policy_trump_source': 'google_search',
                            'policy_trump_source_type': source_type,  # news_api, rss, gov_press, social_media, google_search
                            
                            # Content fields
                            'policy_trump_headline': result.get('title', ''),
                            'policy_trump_text': result.get('description', ''),
                            'policy_trump_url': result_url,
                            
                            # Classification fields
                            'policy_trump_category': category,  # Original category (e.g., 'policy_lobbying')
                            'policy_trump_prefix_buckets': ','.join(prefix_buckets),  # Comma-separated buckets (policy, trade, biofuel, etc.)
                            'policy_trump_query': query,  # Which query triggered this result
                            'policy_trump_region': region,  # US, Brazil, Argentina, China, SE_Asia, EU, Unknown
                            
                            # Metadata fields
                            'policy_trump_domain': domain,
                            'policy_trump_confidence': credibility,  # 0.5-1.0 based on source credibility
                            'policy_trump_unique_id': url_hash,  # MD5 hash for deduplication
                            'policy_trump_language': 'en',  # Default, can be enhanced with language detection
                            
                            # Topic multiplier (for transparency/debugging)
                            'policy_trump_topic_multiplier': topic_multiplier,
                            
                            # Sentiment fields
                            'policy_trump_sentiment_score': sentiment_score,  # -1 to +1
                            'policy_trump_sentiment_class': sentiment_class,  # bullish/bearish/neutral
                            'policy_trump_bullish_keywords': sentiment_result.get('policy_trump_bullish_keywords', 0),
                            'policy_trump_bearish_keywords': sentiment_result.get('policy_trump_bearish_keywords', 0),
                            'policy_trump_categories': sentiment_result.get('policy_trump_categories', ''),
                            
                            # Policy shock scoring
                            'policy_trump_score': policy_trump_score,  # 0-1 (unsigned magnitude)
                            'policy_trump_score_signed': policy_trump_score_signed,  # -1 to +1 (signed for training)
                            'policy_trump_recency_decay': recency_decay,  # exp(-Δhours / 24)
                            'policy_trump_frequency_penalty': frequency_penalty,  # 0.8 if ≥3 similar in 3h, else 1.0
                        }
                        all_results.append(processed)
                    
                    logger.info(f"    ✅ {query}: {len(results)} results")
                else:
                    logger.warning(f"    ❌ {query}: API returned {response.status_code}")
                
                time.sleep(1)  # Rate limiting (1 credit per request)
                
            except Exception as e:
                logger.debug(f"Error searching {query}: {e}")
    
    if all_results:
        df = pd.DataFrame(all_results)
        # Deduplicate by unique_id
        df = df.drop_duplicates(subset=['policy_trump_unique_id'], keep='first')
        
        # Calculate frequency penalty (0.8 if ≥3 similar headlines in past 3 hours)
        # Similar = same domain + same query
        df['policy_trump_frequency_penalty'] = 1.0  # Initialize
        if len(df) > 0:
            df_sorted = df.sort_values('timestamp')
            for idx, row in df_sorted.iterrows():
                # Find similar headlines (same domain + query) in past 3 hours
                similar_mask = (
                    (df_sorted['policy_trump_domain'] == row['policy_trump_domain']) &
                    (df_sorted['policy_trump_query'] == row['policy_trump_query']) &
                    (df_sorted['timestamp'] >= row['timestamp'] - timedelta(hours=3)) &
                    (df_sorted['timestamp'] <= row['timestamp'])
                )
                similar_count = similar_mask.sum()
                if similar_count >= 3:
                    df.loc[idx, 'policy_trump_frequency_penalty'] = 0.8
            
            # Recalculate policy_trump_score with updated frequency_penalty
            df['policy_trump_score'] = (
                df['policy_trump_confidence'] *
                df['policy_trump_topic_multiplier'] *
                df['policy_trump_sentiment_score'].abs() *
                df['policy_trump_recency_decay'] *
                df['policy_trump_frequency_penalty']
            )
            
            # Recalculate signed score
            df['policy_trump_score_signed'] = df['policy_trump_score'] * df['policy_trump_sentiment_score'].apply(lambda x: 1.0 if x >= 0 else -1.0)
        
        logger.info(f"✅ Google Search: {len(df)} unique articles collected")
        logger.info(f"   Prefix buckets: {df['policy_trump_prefix_buckets'].value_counts().to_dict()}")
        logger.info(f"   Score range: {df['policy_trump_score'].min():.3f} - {df['policy_trump_score'].max():.3f}")
        return df
    
    return pd.DataFrame()

def collect_aggregated_news() -> pd.DataFrame:
    """
    Collect aggregated news from NewsAPI, Alpha Vantage, and RSS feeds.
    
    Returns:
        DataFrame with news articles
    """
    logger.info("Collecting aggregated news...")
    
    all_news = []
    
    # 1. NewsAPI
    if NEWSAPI_KEY:
        try:
            url = 'https://newsapi.org/v2/everything'
            params = {
                'q': 'trump OR tariff OR trade OR soybean OR biofuel OR agriculture',
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': 50,
                'apiKey': NEWSAPI_KEY,
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                
                for article in articles:
                    all_news.append({
                        'timestamp': pd.to_datetime(article.get('publishedAt', datetime.now())),
                        'source': 'newsapi',
                        'title': article.get('title', ''),
                        'text': article.get('description', '') or article.get('content', ''),
                        'url': article.get('url', ''),
                        'source_name': article.get('source', {}).get('name', ''),
                    })
                
                logger.info(f"✅ NewsAPI: {len(articles)} articles collected")
            else:
                logger.warning(f"NewsAPI returned {response.status_code}")
        except Exception as e:
            logger.warning(f"NewsAPI error: {e}")
    
    # 2. Alpha Vantage News
    if ALPHA_VANTAGE_KEY:
        try:
            url = 'https://www.alphavantage.co/query'
            params = {
                'function': 'NEWS_SENTIMENT',
                'tickers': 'SOYB,SOYB',
                'apikey': ALPHA_VANTAGE_KEY,
                'limit': 50,
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                feed = data.get('feed', [])
                
                for item in feed:
                    all_news.append({
                        'timestamp': pd.to_datetime(item.get('time_published', datetime.now())),
                        'source': 'alphavantage',
                        'title': item.get('title', ''),
                        'text': item.get('summary', ''),
                        'url': item.get('url', ''),
                        'source_name': item.get('source', ''),
                    })
                
                logger.info(f"✅ Alpha Vantage News: {len(feed)} articles collected")
            else:
                logger.warning(f"Alpha Vantage returned {response.status_code}")
        except Exception as e:
            logger.warning(f"Alpha Vantage error: {e}")
    
    # 3. RSS Feeds
    try:
        import feedparser
        
        for rss_url in NEWS_SOURCES['rss_feeds']:
            try:
                feed = feedparser.parse(rss_url)
                
                for entry in feed.entries[:20]:  # Limit per feed
                    all_news.append({
                        'timestamp': pd.to_datetime(entry.get('published', datetime.now())),
                        'source': 'rss',
                        'title': entry.get('title', ''),
                        'text': entry.get('summary', '') or entry.get('description', ''),
                        'url': entry.get('link', ''),
                        'source_name': feed.feed.get('title', 'RSS Feed'),
                    })
                
                logger.info(f"✅ RSS {rss_url[:50]}...: {len(feed.entries)} entries")
                time.sleep(1)  # Rate limiting
            except Exception as e:
                logger.debug(f"RSS feed error {rss_url}: {e}")
    except ImportError:
        logger.warning("feedparser not installed, skipping RSS feeds")
    
    if all_news:
        df = pd.DataFrame(all_news)
        return df
    
    return pd.DataFrame()

def collect_ice_data() -> pd.DataFrame:
    """
    Collect ICE (Intercontinental Exchange) announcements and regulatory updates.
    
    Returns:
        DataFrame with ICE data
    """
    logger.info("Collecting ICE (Intercontinental Exchange) data...")
    
    ice_items = []
    
    for url in ICE_SOURCES:
        try:
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; CBI-V14-Data-Collector/1.0)'
            })
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Extract news/announcements (adjust selectors based on actual page structure)
                news_items = soup.find_all(['article', 'div', 'li'], class_=re.compile(r'news|announcement|press|update'))
                
                for item in news_items[:20]:  # Limit per source
                    title_elem = item.find(['h1', 'h2', 'h3', 'h4', 'a'])
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        link = title_elem.get('href', '') if title_elem.name == 'a' else item.find('a', href=True)
                        link = link.get('href', '') if hasattr(link, 'get') else ''
                        
                        # Extract date if available
                        date_elem = item.find(['time', 'span'], class_=re.compile(r'date|time|published'))
                        date_str = date_elem.get_text(strip=True) if date_elem else None
                        
                        ice_items.append({
                            'timestamp': pd.to_datetime(date_str) if date_str else datetime.now(),
                            'source': 'ICE',
                            'title': title,
                            'text': item.get_text(strip=True)[:500],
                            'url': link if link.startswith('http') else f"https://www.theice.com{link}",
                        })
            
            time.sleep(2)  # Rate limiting
            
        except Exception as e:
            logger.warning(f"Error scraping ICE {url}: {e}")
    
    if ice_items:
        df = pd.DataFrame(ice_items)
        return df
    
    return pd.DataFrame()

def collect_tariff_data() -> pd.DataFrame:
    """
    Collect tariff announcements from USTR and Federal Register.
    
    Returns:
        DataFrame with tariff data
    """
    logger.info("Collecting tariff data...")
    
    tariff_items = []
    
    for url in TARIFF_SOURCES:
        try:
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; CBI-V14-Data-Collector/1.0)'
            })
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Extract announcements
                items = soup.find_all(['article', 'div', 'li'], class_=re.compile(r'press|release|announcement|document'))
                
                for item in items[:30]:  # Limit per source
                    title_elem = item.find(['h1', 'h2', 'h3', 'h4', 'a'])
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        # Check if title contains tariff-related keywords
                        if any(kw in title.lower() for kw in ['tariff', 'section 301', 'trade', 'duty', 'ustr']):
                            link = title_elem.get('href', '') if title_elem.name == 'a' else item.find('a', href=True)
                            link = link.get('href', '') if hasattr(link, 'get') else ''
                            
                            tariff_items.append({
                                'timestamp': datetime.now(),  # USTR doesn't always have dates
                                'source': 'USTR' if 'ustr' in url else 'Federal Register',
                                'title': title,
                                'text': item.get_text(strip=True)[:500],
                                'url': link if link.startswith('http') else f"https://ustr.gov{link}",
                            })
            
            time.sleep(2)  # Rate limiting
            
        except Exception as e:
            logger.warning(f"Error scraping tariff source {url}: {e}")
    
    if tariff_items:
        df = pd.DataFrame(tariff_items)
        return df
    
    return pd.DataFrame()

def collect_executive_orders() -> pd.DataFrame:
    """
    Collect Trump executive orders and presidential proclamations.
    
    Returns:
        DataFrame with executive orders
    """
    logger.info("Collecting executive orders...")
    
    eo_items = []
    
    for url in EXECUTIVE_ORDER_SOURCES:
        try:
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; CBI-V14-Data-Collector/1.0)'
            })
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Extract executive orders
                items = soup.find_all(['article', 'div', 'li'], class_=re.compile(r'executive|order|proclamation|document'))
                
                for item in items[:30]:  # Limit per source
                    title_elem = item.find(['h1', 'h2', 'h3', 'h4', 'a'])
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        # Filter for trade/agriculture/biofuel related EOs
                        if any(kw in title.lower() for kw in ['trade', 'agriculture', 'biofuel', 'tariff', 'china', 'import', 'export']):
                            link = title_elem.get('href', '') if title_elem.name == 'a' else item.find('a', href=True)
                            link = link.get('href', '') if hasattr(link, 'get') else ''
                            
                            # Extract EO number if available
                            eo_match = re.search(r'EO-?\s*(\d+)', title, re.I)
                            eo_number = eo_match.group(1) if eo_match else None
                            
                            eo_items.append({
                                'timestamp': datetime.now(),
                                'source': 'White House' if 'whitehouse' in url else 'Federal Register',
                                'title': title,
                                'text': item.get_text(strip=True)[:500],
                                'url': link if link.startswith('http') else f"https://www.whitehouse.gov{link}",
                                'eo_number': eo_number,
                            })
            
            time.sleep(2)  # Rate limiting
            
        except Exception as e:
            logger.warning(f"Error scraping executive orders {url}: {e}")
    
    if eo_items:
        df = pd.DataFrame(eo_items)
        return df
    
    return pd.DataFrame()

def scrape_policy_feeds() -> pd.DataFrame:
    """
    Scrape policy feeds from USDA, EPA, trade news sites.
    
    Returns:
        DataFrame with policy announcements
    """
    logger.info("Scraping policy feeds...")
    
    policy_items = []
    
    # USDA Announcements (example - adjust URLs as needed)
    usda_urls = [
        'https://www.usda.gov/newsroom/news',
        'https://www.fas.usda.gov/newsroom/news',
    ]
    
    for url in usda_urls:
        try:
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; CBI-V14-Data-Collector/1.0)'
            })
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Extract news items (adjust selectors based on actual page structure)
                news_items = soup.find_all(['article', 'div'], class_=re.compile(r'news|announcement|press'))
                
                for item in news_items[:10]:  # Limit to recent 10
                    title = item.find(['h1', 'h2', 'h3', 'a'])
                    if title:
                        policy_items.append({
                            'timestamp': datetime.now(),  # Use current time as proxy
                            'source': 'USDA',
                            'title': title.get_text(strip=True),
                            'url': url,
                            'text': item.get_text(strip=True)[:500],  # First 500 chars
                        })
            
            time.sleep(2)  # Rate limiting
            
        except Exception as e:
            logger.warning(f"Error scraping {url}: {e}")
    
    if policy_items:
        df = pd.DataFrame(policy_items)
        return df
    
    return pd.DataFrame()

def main():
    """
    Main collection function: Truth Social + Social Media + News + ICE + Tariffs + Executive Orders.
    """
    logger.info("=" * 80)
    logger.info("POLICY & TRUMP INTELLIGENCE COLLECTION")
    logger.info("=" * 80)
    logger.info("Truth Social + Social Media + Google Search + Aggregated News + ICE + Tariffs + Executive Orders")
    logger.info("(REPUTABLE/VERIFIED SOURCES ONLY - NO Reddit, YouTube, or TikTok)")
    logger.info("")
    
    all_dataframes = []
    
    # 1. Collect Truth Social posts (via ScrapeCreators API)
    # Uses both /v1/truthsocial/profile (validation) and /v1/truthsocial/user/posts (posts)
    truth_posts = collect_truth_social_posts(TRUTH_SOCIAL_ACCOUNTS, limit=100)
    if not truth_posts.empty:
        truth_posts['source_type'] = 'truth_social'
        all_dataframes.append(truth_posts)
    
    # 2. Collect Social Media (Facebook, Twitter/X, LinkedIn, Bluesky via ScrapeCreators API)
    social_posts = collect_social_media_posts()
    if not social_posts.empty:
        social_posts['source_type'] = 'social_media'
        all_dataframes.append(social_posts)
    
    # 3. Collect Google Search News (comprehensive shock signal coverage)
    google_search_df = collect_google_search_news()
    if not google_search_df.empty:
        google_search_df['source_type'] = 'google_search'
        all_dataframes.append(google_search_df)
    
    # 4. Collect Aggregated News (RSS, NewsAPI, Alpha Vantage)
    news_df = collect_aggregated_news()
    if not news_df.empty:
        news_df['source_type'] = 'aggregated_news'
        all_dataframes.append(news_df)
    
    # 5. Collect ICE Data
    ice_df = collect_ice_data()
    if not ice_df.empty:
        ice_df['source_type'] = 'ice'
        all_dataframes.append(ice_df)
    
    # 6. Collect Tariff Data
    tariff_df = collect_tariff_data()
    if not tariff_df.empty:
        tariff_df['source_type'] = 'tariff'
        all_dataframes.append(tariff_df)
    
    # 7. Collect Executive Orders
    eo_df = collect_executive_orders()
    if not eo_df.empty:
        eo_df['source_type'] = 'executive_order'
        all_dataframes.append(eo_df)
    
    # 7. Scrape policy feeds (USDA, EPA)
    policy_feeds = scrape_policy_feeds()
    if not policy_feeds.empty:
        policy_feeds['source_type'] = 'policy_feed'
        all_dataframes.append(policy_feeds)
    
    # 8. Combine all dataframes
    if not all_dataframes:
        logger.error("❌ No policy data collected")
        return
    
    # Standardize columns before merging
    combined_df = pd.DataFrame()
    
    for df in all_dataframes:
        # Ensure timestamp column exists
        if 'timestamp' not in df.columns:
            df['timestamp'] = datetime.now()
        
        # Add date column
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        
        # Get text column (may be named differently)
        text_col = None
        for col in ['text', 'title', 'content', 'message', 'description', 'summary', 'policy_trump_text']:
            if col in df.columns:
                text_col = col
                break
        
        # Classify sentiment if text column exists and sentiment not already classified
        if text_col and 'policy_trump_sentiment_score' not in df.columns:
            sentiment_results = df[text_col].apply(classify_policy_sentiment)
            sentiment_df = pd.DataFrame(sentiment_results.tolist())
            df = pd.concat([df, sentiment_df], axis=1)
        
        # Prefix all columns except date/timestamp (if not already prefixed)
        prefix_map = {}
        for col in df.columns:
            if col not in ['date', 'timestamp'] and not col.startswith('policy_trump_'):
                prefix_map[col] = f'policy_trump_{col}'
        df = df.rename(columns=prefix_map)
        
        # Ensure prefix buckets are set (if not already set by Google Search)
        if 'policy_trump_prefix_buckets' not in df.columns:
            if 'policy_trump_category' in df.columns:
                df['policy_trump_prefix_buckets'] = df['policy_trump_category'].apply(
                    lambda cat: ','.join(classify_category_to_prefix_buckets(cat)) if pd.notna(cat) else 'policy'
                )
            else:
                # Infer from source_type
                source_type_col = df.get('policy_trump_source_type', df.get('source_type', 'unknown'))
                if isinstance(source_type_col, pd.Series):
                    df['policy_trump_prefix_buckets'] = source_type_col.apply(
                        lambda st: 'policy' if st in ['executive_order', 'tariff', 'ice', 'policy_feed', 'gov_press'] else 'policy'
                    )
                else:
                    df['policy_trump_prefix_buckets'] = 'policy'
        
        # Ensure source_type is set
        if 'policy_trump_source_type' not in df.columns:
            if 'source_type' in df.columns:
                df['policy_trump_source_type'] = df['source_type']
            else:
                df['policy_trump_source_type'] = 'unknown'
        
        # Ensure unique_id exists for deduplication
        if 'policy_trump_unique_id' not in df.columns:
            url_col = df.get('policy_trump_url', df.get('url', None))
            if url_col is not None:
                df['policy_trump_unique_id'] = url_col.apply(
                    lambda url: hashlib.md5(str(url).encode()).hexdigest()[:16] if pd.notna(url) and url else ''
                )
            else:
                df['policy_trump_unique_id'] = df.index.astype(str)
        
        # Calculate policy shock scores if not already calculated
        if 'policy_trump_score' not in df.columns:
            # Get source confidence
            if 'policy_trump_confidence' not in df.columns:
                domain_col = df.get('policy_trump_domain', df.get('domain', ''))
                df['policy_trump_confidence'] = domain_col.apply(
                    lambda d: SOURCE_CREDIBILITY.get(str(d).lower(), SOURCE_CREDIBILITY['default'])
                )
            
            # Get topic multiplier
            if 'policy_trump_topic_multiplier' not in df.columns:
                category_col = df.get('policy_trump_category', 'default')
                df['policy_trump_topic_multiplier'] = category_col.apply(
                    lambda cat: TOPIC_MULTIPLIERS.get(str(cat), TOPIC_MULTIPLIERS['default'])
                )
            
            # Get sentiment score
            if 'policy_trump_sentiment_score' not in df.columns:
                df['policy_trump_sentiment_score'] = 0.0
            
            # Calculate recency decay (exp(-Δhours / 24))
            if 'policy_trump_recency_decay' not in df.columns:
                if 'timestamp' in df.columns:
                    now = datetime.now()
                    df['policy_trump_recency_decay'] = (now - pd.to_datetime(df['timestamp'])).dt.total_seconds() / 3600
                    df['policy_trump_recency_decay'] = np.exp(-df['policy_trump_recency_decay'] / 24)
                else:
                    df['policy_trump_recency_decay'] = 1.0
            
            # Frequency penalty (default 1.0, will be recalculated after deduplication)
            if 'policy_trump_frequency_penalty' not in df.columns:
                df['policy_trump_frequency_penalty'] = 1.0
            
            # Calculate policy shock score
            df['policy_trump_score'] = (
                df['policy_trump_confidence'] *
                df['policy_trump_topic_multiplier'] *
                df['policy_trump_sentiment_score'].abs() *
                df['policy_trump_recency_decay'] *
                df['policy_trump_frequency_penalty']
            )
            
            # Calculate signed score
            df['policy_trump_score_signed'] = df['policy_trump_score'] * df['policy_trump_sentiment_score'].apply(lambda x: 1.0 if x >= 0 else -1.0)
        
        # Combine
        if combined_df.empty:
            combined_df = df.copy()
        else:
            # Merge on date (outer join)
            combined_df = pd.concat([combined_df, df], ignore_index=True)
    
    # 9. Sort by date
    combined_df = combined_df.sort_values('date').reset_index(drop=True)
    
    # 10. Segment data by category into separate buckets with appropriate prefixes
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M')
    
    # Define prefix mapping based on category
    def get_prefix_for_category(category: str, source_type: str) -> str:
        """Determine prefix based on category and source type."""
        if pd.isna(category):
            category = 'default'
        category = str(category).lower()
        source_type = str(source_type).lower()
        
        # Trump-specific sources get policy_trump_ prefix
        if 'truth_social' in source_type or 'trump' in category or 'executive_order' in source_type:
            return 'policy_trump'
        
        # Map categories to sentiment prefixes
        if category.startswith('soybean_oil_'):
            return 'sentiment_soybean_oil'
        elif category.startswith('biofuel_'):
            return 'sentiment_biofuel'
        elif category.startswith('trade_relations_'):
            return 'sentiment_trade_relations'
        elif category.startswith('ice_'):
            return 'sentiment_ice'
        elif category.startswith('price_direction_'):
            return 'sentiment_price_direction'
        elif category.startswith('tariff_'):
            return 'sentiment_tariff'
        elif category.startswith('policy_') or category.startswith('trade_'):
            # General policy/trade (non-Trump) - use sentiment prefix
            if 'trump' in category.lower():
                return 'policy_trump'
            else:
                return 'sentiment_policy'  # General policy sentiment
        else:
            # Default to sentiment_market for unknown categories
            return 'sentiment_market'
    
    # Segment data by prefix
    segmented_data = {}
    
    for idx, row in combined_df.iterrows():
        category = row.get('policy_trump_category', 'default')
        source_type = row.get('policy_trump_source_type', row.get('source_type', 'unknown'))
        prefix = get_prefix_for_category(category, source_type)
        
        if prefix not in segmented_data:
            segmented_data[prefix] = []
        segmented_data[prefix].append(row)
    
    # Save segmented files with appropriate prefixes
    saved_files = []
    for prefix, rows in segmented_data.items():
        if not rows:
            continue
        
        segment_df = pd.DataFrame(rows)
        
        # Rename columns to use the appropriate prefix
        rename_dict = {}
        for col in segment_df.columns:
            if col not in ['date', 'timestamp']:
                # Remove old prefix if present
                if col.startswith('policy_trump_'):
                    new_col = col.replace('policy_trump_', f'{prefix}_')
                else:
                    new_col = f'{prefix}_{col}'
                rename_dict[col] = new_col
        
        segment_df = segment_df.rename(columns=rename_dict)
        
        # Save to appropriate directory
        if prefix == 'policy_trump':
            output_dir = RAW_DIR
            filename = f"policy_trump_{timestamp_str}.parquet"
        else:
            # Create sentiment subdirectory
            sentiment_dir = RAW_DIR.parent / "sentiment"
            sentiment_dir.mkdir(parents=True, exist_ok=True)
            output_dir = sentiment_dir
            filename = f"{prefix}_{timestamp_str}.parquet"
        
        output_file = output_dir / filename
        segment_df.to_parquet(output_file, index=False)
        saved_files.append((prefix, len(segment_df), output_file))
        logger.info(f"   ✅ {prefix}: {len(segment_df):,} rows → {output_file.name}")
    
    # Also save combined file for backward compatibility (will be phased out)
    combined_output_file = RAW_DIR / f"policy_trump_{timestamp_str}.parquet"
    combined_df.to_parquet(combined_output_file, index=False)
    
    # Deduplicate by unique_id
    if 'policy_trump_unique_id' in combined_df.columns:
        before_dedup = len(combined_df)
        combined_df = combined_df.drop_duplicates(subset=['policy_trump_unique_id'], keep='first')
        after_dedup = len(combined_df)
        if before_dedup != after_dedup:
            logger.info(f"   Deduplicated: {before_dedup - after_dedup} duplicate records removed")
    
    # Recalculate frequency penalty after deduplication (0.8 if ≥3 similar headlines in past 3 hours)
    if 'policy_trump_frequency_penalty' in combined_df.columns and len(combined_df) > 0:
        combined_df_sorted = combined_df.sort_values('timestamp' if 'timestamp' in combined_df.columns else 'date')
        combined_df['policy_trump_frequency_penalty'] = 1.0  # Reset
        
        for idx, row in combined_df_sorted.iterrows():
            # Find similar headlines (same domain + query) in past 3 hours
            timestamp_col = 'timestamp' if 'timestamp' in combined_df.columns else 'date'
            row_time = pd.to_datetime(row[timestamp_col])
            
            similar_mask = (
                (combined_df_sorted['policy_trump_domain'] == row['policy_trump_domain']) &
                (combined_df_sorted.get('policy_trump_query', pd.Series([''])) == row.get('policy_trump_query', '')) &
                (pd.to_datetime(combined_df_sorted[timestamp_col]) >= row_time - timedelta(hours=3)) &
                (pd.to_datetime(combined_df_sorted[timestamp_col]) <= row_time)
            )
            similar_count = similar_mask.sum()
            if similar_count >= 3:
                combined_df.loc[idx, 'policy_trump_frequency_penalty'] = 0.8
        
        # Recalculate policy_trump_score with updated frequency_penalty
        if all(col in combined_df.columns for col in ['policy_trump_confidence', 'policy_trump_topic_multiplier', 
                                                       'policy_trump_sentiment_score', 'policy_trump_recency_decay']):
            combined_df['policy_trump_score'] = (
                combined_df['policy_trump_confidence'] *
                combined_df['policy_trump_topic_multiplier'] *
                combined_df['policy_trump_sentiment_score'].abs() *
                combined_df['policy_trump_recency_decay'] *
                combined_df['policy_trump_frequency_penalty']
            )
            
            # Recalculate signed score
            combined_df['policy_trump_score_signed'] = (
                combined_df['policy_trump_score'] * 
                combined_df['policy_trump_sentiment_score'].apply(lambda x: 1.0 if x >= 0 else -1.0)
            )
    
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"✅ POLICY & TRUMP COLLECTION COMPLETE")
    logger.info(f"   Truth Social: {len(truth_posts) if not truth_posts.empty else 0:,}")
    logger.info(f"   Social Media: {len(social_posts) if not social_posts.empty else 0:,}")
    logger.info(f"   Google Search: {len(google_search_df) if not google_search_df.empty else 0:,}")
    logger.info(f"   Aggregated News: {len(news_df) if not news_df.empty else 0:,}")
    logger.info(f"   ICE Data: {len(ice_df) if not ice_df.empty else 0:,}")
    logger.info(f"   Tariffs: {len(tariff_df) if not tariff_df.empty else 0:,}")
    logger.info(f"   Executive Orders: {len(eo_df) if not eo_df.empty else 0:,}")
    logger.info(f"   Policy Feeds: {len(policy_feeds) if not policy_feeds.empty else 0:,}")
    logger.info(f"   Total rows: {len(combined_df):,}")
    
    # Print schema classification summary
    if 'policy_trump_prefix_buckets' in combined_df.columns:
        logger.info(f"\n   Schema Classification by Prefix Buckets:")
        bucket_counts = {}
        for buckets_str in combined_df['policy_trump_prefix_buckets'].dropna():
            for bucket in str(buckets_str).split(','):
                bucket_counts[bucket.strip()] = bucket_counts.get(bucket.strip(), 0) + 1
        for bucket, count in sorted(bucket_counts.items()):
            logger.info(f"      {bucket}: {count:,}")
    
    if 'policy_trump_source_type' in combined_df.columns:
        logger.info(f"\n   By Source Type:")
        for source_type, count in combined_df['policy_trump_source_type'].value_counts().head(10).items():
            logger.info(f"      {source_type}: {count:,}")
    if not combined_df.empty:
        logger.info(f"   Date range: {combined_df['date'].min()} to {combined_df['date'].max()}")
    logger.info(f"   Saved to: {output_file}")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()

