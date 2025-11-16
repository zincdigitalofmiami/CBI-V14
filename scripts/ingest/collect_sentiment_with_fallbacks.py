#!/usr/bin/env python3
"""
Robust sentiment collection with multiple fallback sources.
Three-tier strategy: Social Media → Market Analysts → News APIs

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
from typing import Dict, List, Optional
import re
import feedparser
from bs4 import BeautifulSoup
import yfinance as yf
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
RAW_DIR = DRIVE / "TrainingData/raw/sentiment"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Initialize VADER for sentiment analysis
vader = SentimentIntensityAnalyzer()


class MultiSourceSentimentCollector:
    """
    Collect sentiment from multiple sources with automatic fallback.
    Priority: Social Media → Market Analysts → News → RSS Feeds
    """
    
    def __init__(self):
        # API keys from environment
        self.scrape_key = os.getenv('SCRAPE_CREATORS_KEY')
        self.newsapi_key = os.getenv('NEWSAPI_KEY')
        self.alphavantage_key = os.getenv('ALPHA_VANTAGE_KEY')
        self.finnhub_key = os.getenv('FINNHUB_KEY')
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (CBI-V14 Sentiment Collector)'
        })
        
    # ==================== TIER 1: SOCIAL MEDIA ====================
    
    def collect_social_sentiment(self) -> Optional[pd.DataFrame]:
        """
        Primary: Social media via ScrapeCreators
        """
        if not self.scrape_key:
            logger.warning("ScrapeCreators API key not found, skipping social media")
            return None
            
        try:
            logger.info("Attempting Tier 1: Social Media sentiment...")
            
            # This would use the ScrapeCreators implementation from before
            # Simplified here for fallback demonstration
            
            url = 'https://api.scrapecreators.com/v1/truthsocial'
            headers = {'x-api-key': self.scrape_key}
            
            response = self.session.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Process social data
                df = self._process_social_data(data)
                logger.info(f"✅ Social media sentiment collected: {len(df)} posts")
                return df
            else:
                logger.warning(f"Social media API failed with status {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Social media collection failed: {e}")
            return None
    
    # ==================== TIER 2: MARKET ANALYSTS ====================
    
    def collect_analyst_sentiment(self) -> Optional[pd.DataFrame]:
        """
        Secondary: Market analyst reports and recommendations
        """
        logger.info("Attempting Tier 2: Market Analyst sentiment...")
        
        all_sentiments = []
        
        # 1. Yahoo Finance Analyst Recommendations
        try:
            analyst_data = self._collect_yahoo_analysts()
            if analyst_data:
                all_sentiments.append(analyst_data)
        except Exception as e:
            logger.warning(f"Yahoo analysts failed: {e}")
        
        # 2. Seeking Alpha Articles (via RSS)
        try:
            seeking_alpha = self._collect_seeking_alpha()
            if seeking_alpha:
                all_sentiments.append(seeking_alpha)
        except Exception as e:
            logger.warning(f"Seeking Alpha failed: {e}")
        
        # 3. MarketWatch Analyst Views
        try:
            marketwatch = self._collect_marketwatch_analysts()
            if marketwatch:
                all_sentiments.append(marketwatch)
        except Exception as e:
            logger.warning(f"MarketWatch failed: {e}")
        
        # 4. Bloomberg Commodity Outlook (if available)
        try:
            bloomberg = self._collect_bloomberg_commodities()
            if bloomberg:
                all_sentiments.append(bloomberg)
        except Exception as e:
            logger.warning(f"Bloomberg failed: {e}")
        
        if all_sentiments:
            df = pd.concat(all_sentiments, ignore_index=True)
            logger.info(f"✅ Analyst sentiment collected: {len(df)} items")
            return df
        
        return None
    
    def _collect_yahoo_analysts(self) -> pd.DataFrame:
        """
        Collect analyst recommendations from Yahoo Finance
        """
        symbols = ['SOYB', 'CORN', 'WEAT', 'DBA', 'MOO', 'COW']  # Agricultural ETFs
        
        analyst_data = []
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                
                # Get recommendations
                if hasattr(ticker, 'recommendations'):
                    recs = ticker.recommendations
                    if recs is not None and not recs.empty:
                        latest = recs.tail(10)  # Last 10 recommendations
                        
                        for idx, row in latest.iterrows():
                            analyst_data.append({
                                'timestamp': idx,
                                'source': 'yahoo_analyst',
                                'symbol': symbol,
                                'firm': row.get('Firm', 'Unknown'),
                                'action': row.get('To Grade', 'Hold'),
                                'previous': row.get('From Grade', 'Hold'),
                                'sentiment': self._grade_to_sentiment(row.get('To Grade', 'Hold'))
                            })
                
                # Get analyst price targets
                info = ticker.info
                if info:
                    current_price = info.get('regularMarketPrice', 0)
                    target_price = info.get('targetMeanPrice', 0)
                    
                    if current_price and target_price:
                        upside = (target_price - current_price) / current_price
                        
                        analyst_data.append({
                            'timestamp': datetime.now(),
                            'source': 'yahoo_targets',
                            'symbol': symbol,
                            'current_price': current_price,
                            'target_price': target_price,
                            'upside_pct': upside * 100,
                            'sentiment': 1.0 if upside > 0.1 else (-1.0 if upside < -0.1 else 0.0)
                        })
                
            except Exception as e:
                logger.debug(f"Yahoo analyst data failed for {symbol}: {e}")
        
        if analyst_data:
            return pd.DataFrame(analyst_data)
        return pd.DataFrame()
    
    def _grade_to_sentiment(self, grade: str) -> float:
        """Convert analyst grade to sentiment score"""
        grade = str(grade).lower()
        
        if 'buy' in grade or 'outperform' in grade or 'overweight' in grade:
            return 1.0
        elif 'sell' in grade or 'underperform' in grade or 'underweight' in grade:
            return -1.0
        else:
            return 0.0
    
    def _collect_seeking_alpha(self) -> pd.DataFrame:
        """
        Collect articles from Seeking Alpha commodity section
        """
        url = 'https://seekingalpha.com/api/sa/combined/feed/commodities'
        
        try:
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                articles = []
                for item in data.get('data', [])[:20]:  # Last 20 articles
                    title = item.get('attributes', {}).get('title', '')
                    summary = item.get('attributes', {}).get('summary', '')
                    
                    # Analyze sentiment
                    text = f"{title} {summary}"
                    sentiment = vader.polarity_scores(text)
                    
                    articles.append({
                        'timestamp': pd.to_datetime(item.get('attributes', {}).get('publishOn')),
                        'source': 'seeking_alpha',
                        'title': title,
                        'summary': summary[:200],
                        'sentiment': sentiment['compound'],
                        'sentiment_pos': sentiment['pos'],
                        'sentiment_neg': sentiment['neg'],
                        'sentiment_neu': sentiment['neu']
                    })
                
                if articles:
                    return pd.DataFrame(articles)
        
        except Exception as e:
            logger.debug(f"Seeking Alpha failed: {e}")
        
        return pd.DataFrame()
    
    def _collect_marketwatch_analysts(self) -> pd.DataFrame:
        """
        Collect MarketWatch analyst opinions
        """
        # MarketWatch RSS for commodities
        feed_url = 'https://feeds.marketwatch.com/marketwatch/marketpulse/'
        
        try:
            feed = feedparser.parse(feed_url)
            
            articles = []
            for entry in feed.entries[:20]:  # Last 20 entries
                # Check if commodity related
                if any(word in entry.title.lower() for word in ['soybean', 'corn', 'wheat', 'commodity', 'agriculture']):
                    
                    # Analyze sentiment
                    text = f"{entry.title} {entry.get('summary', '')}"
                    sentiment = vader.polarity_scores(text)
                    
                    articles.append({
                        'timestamp': pd.to_datetime(entry.published),
                        'source': 'marketwatch',
                        'title': entry.title,
                        'link': entry.link,
                        'sentiment': sentiment['compound'],
                        'is_commodity': True
                    })
            
            if articles:
                return pd.DataFrame(articles)
        
        except Exception as e:
            logger.debug(f"MarketWatch failed: {e}")
        
        return pd.DataFrame()
    
    def _collect_bloomberg_commodities(self) -> pd.DataFrame:
        """
        Collect Bloomberg commodity news (via RSS or scraping)
        """
        # Bloomberg Commodities RSS
        feed_url = 'https://www.bloomberg.com/markets/commodities.rss'
        
        try:
            feed = feedparser.parse(feed_url)
            
            articles = []
            for entry in feed.entries[:15]:
                # Analyze sentiment
                text = f"{entry.title} {entry.get('summary', '')}"
                sentiment = vader.polarity_scores(text)
                
                # Extract commodity mentions
                commodities_mentioned = []
                for commodity in ['soybean', 'corn', 'wheat', 'oil', 'gas', 'gold']:
                    if commodity in text.lower():
                        commodities_mentioned.append(commodity)
                
                articles.append({
                    'timestamp': pd.to_datetime(entry.published),
                    'source': 'bloomberg',
                    'title': entry.title,
                    'sentiment': sentiment['compound'],
                    'commodities': ','.join(commodities_mentioned)
                })
            
            if articles:
                return pd.DataFrame(articles)
        
        except Exception as e:
            logger.debug(f"Bloomberg failed: {e}")
        
        return pd.DataFrame()
    
    # ==================== TIER 3: NEWS APIS ====================
    
    def collect_news_sentiment(self) -> Optional[pd.DataFrame]:
        """
        Tertiary: News APIs (NewsAPI, Alpha Vantage, Finnhub)
        """
        logger.info("Attempting Tier 3: News API sentiment...")
        
        all_news = []
        
        # 1. NewsAPI
        if self.newsapi_key:
            try:
                news_data = self._collect_newsapi()
                if news_data:
                    all_news.append(news_data)
            except Exception as e:
                logger.warning(f"NewsAPI failed: {e}")
        
        # 2. Alpha Vantage News
        if self.alphavantage_key:
            try:
                av_news = self._collect_alphavantage_news()
                if av_news:
                    all_news.append(av_news)
            except Exception as e:
                logger.warning(f"Alpha Vantage news failed: {e}")
        
        # 3. Finnhub News
        if self.finnhub_key:
            try:
                finnhub_news = self._collect_finnhub_news()
                if finnhub_news:
                    all_news.append(finnhub_news)
            except Exception as e:
                logger.warning(f"Finnhub news failed: {e}")
        
        if all_news:
            df = pd.concat(all_news, ignore_index=True)
            logger.info(f"✅ News sentiment collected: {len(df)} articles")
            return df
        
        return None
    
    def _collect_newsapi(self) -> pd.DataFrame:
        """
        Collect news from NewsAPI
        """
        url = 'https://newsapi.org/v2/everything'
        
        params = {
            'apiKey': self.newsapi_key,
            'q': 'soybean OR corn OR wheat OR commodity OR agriculture',
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 100
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                articles = []
                for article in data.get('articles', []):
                    # Analyze sentiment
                    text = f"{article.get('title', '')} {article.get('description', '')}"
                    sentiment = vader.polarity_scores(text)
                    
                    articles.append({
                        'timestamp': pd.to_datetime(article.get('publishedAt')),
                        'source': 'newsapi',
                        'outlet': article.get('source', {}).get('name'),
                        'title': article.get('title'),
                        'description': article.get('description', '')[:200],
                        'sentiment': sentiment['compound']
                    })
                
                if articles:
                    return pd.DataFrame(articles)
        
        except Exception as e:
            logger.debug(f"NewsAPI failed: {e}")
        
        return pd.DataFrame()
    
    def _collect_alphavantage_news(self) -> pd.DataFrame:
        """
        Collect news sentiment from Alpha Vantage
        """
        url = 'https://www.alphavantage.co/query'
        
        # Get news for commodity-related tickers
        tickers = ['SOYB', 'CORN', 'WEAT', 'DBA']
        
        all_articles = []
        
        for ticker in tickers:
            params = {
                'function': 'NEWS_SENTIMENT',
                'tickers': ticker,
                'apikey': self.alphavantage_key,
                'limit': 50
            }
            
            try:
                response = self.session.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for item in data.get('feed', []):
                        # Extract sentiment
                        ticker_sentiment = next(
                            (s for s in item.get('ticker_sentiment', []) if s.get('ticker') == ticker),
                            {}
                        )
                        
                        all_articles.append({
                            'timestamp': pd.to_datetime(item.get('time_published')),
                            'source': 'alphavantage_news',
                            'ticker': ticker,
                            'title': item.get('title'),
                            'summary': item.get('summary', '')[:200],
                            'sentiment': float(ticker_sentiment.get('ticker_sentiment_score', 0)),
                            'relevance': float(ticker_sentiment.get('relevance_score', 0))
                        })
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                logger.debug(f"Alpha Vantage news failed for {ticker}: {e}")
        
        if all_articles:
            return pd.DataFrame(all_articles)
        
        return pd.DataFrame()
    
    def _collect_finnhub_news(self) -> pd.DataFrame:
        """
        Collect commodity news from Finnhub
        """
        url = 'https://finnhub.io/api/v1/news'
        
        params = {
            'category': 'commodity',
            'token': self.finnhub_key
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                articles = []
                for item in data[:50]:  # Last 50 articles
                    # Analyze sentiment
                    text = f"{item.get('headline', '')} {item.get('summary', '')}"
                    sentiment = vader.polarity_scores(text)
                    
                    articles.append({
                        'timestamp': pd.to_datetime(item.get('datetime'), unit='s'),
                        'source': 'finnhub',
                        'category': item.get('category'),
                        'headline': item.get('headline'),
                        'summary': item.get('summary', '')[:200],
                        'sentiment': sentiment['compound']
                    })
                
                if articles:
                    return pd.DataFrame(articles)
        
        except Exception as e:
            logger.debug(f"Finnhub failed: {e}")
        
        return pd.DataFrame()
    
    # ==================== TIER 4: RSS FEEDS (ALWAYS AVAILABLE) ====================
    
    def collect_rss_sentiment(self) -> pd.DataFrame:
        """
        Final fallback: RSS feeds (always available, no API needed)
        """
        logger.info("Attempting Tier 4: RSS Feed sentiment...")
        
        rss_feeds = {
            'reuters_commodities': 'https://www.reuters.com/business/commodities/rss',
            'agweb': 'https://www.agweb.com/rss/news',
            'farmprogress': 'https://www.farmprogress.com/rss.xml',
            'agriculture_com': 'https://www.agriculture.com/feed',
            'agrimoney': 'https://www.agrimoney.com/feed/',
            'successful_farming': 'https://www.agriculture.com/successful-farming/rss.xml',
            'grain_central': 'https://www.graincentral.com/feed/',
            'world_grain': 'https://www.world-grain.com/rss'
        }
        
        all_articles = []
        
        for source_name, feed_url in rss_feeds.items():
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:10]:  # Last 10 from each source
                    # Analyze sentiment
                    text = f"{entry.get('title', '')} {entry.get('summary', '')}"
                    sentiment = vader.polarity_scores(text)
                    
                    # Extract commodity mentions
                    commodities = self._extract_commodity_mentions(text)
                    
                    all_articles.append({
                        'timestamp': pd.to_datetime(entry.get('published', datetime.now())),
                        'source': f'rss_{source_name}',
                        'title': entry.get('title', ''),
                        'summary': entry.get('summary', '')[:200],
                        'link': entry.get('link', ''),
                        'sentiment': sentiment['compound'],
                        'sentiment_pos': sentiment['pos'],
                        'sentiment_neg': sentiment['neg'],
                        'commodities_mentioned': ','.join(commodities)
                    })
                
                logger.debug(f"✅ RSS {source_name}: {len(feed.entries)} articles")
                
            except Exception as e:
                logger.debug(f"RSS feed {source_name} failed: {e}")
        
        if all_articles:
            df = pd.DataFrame(all_articles)
            logger.info(f"✅ RSS sentiment collected: {len(df)} articles")
            return df
        
        return pd.DataFrame()
    
    def _extract_commodity_mentions(self, text: str) -> List[str]:
        """Extract commodity mentions from text"""
        text_lower = text.lower()
        
        commodities = []
        commodity_keywords = {
            'soybean': ['soybean', 'soy', 'soymeal', 'soyoil'],
            'corn': ['corn', 'maize'],
            'wheat': ['wheat'],
            'oil': ['crude oil', 'wti', 'brent'],
            'gas': ['natural gas', 'natgas'],
            'gold': ['gold'],
            'silver': ['silver'],
            'copper': ['copper'],
            'palm': ['palm oil'],
            'sugar': ['sugar'],
            'coffee': ['coffee'],
            'cocoa': ['cocoa']
        }
        
        for commodity, keywords in commodity_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                commodities.append(commodity)
        
        return commodities
    
    # ==================== COMPOSITE CALCULATION ====================
    
    def calculate_unified_sentiment(self, 
                                   social_df: Optional[pd.DataFrame],
                                   analyst_df: Optional[pd.DataFrame],
                                   news_df: Optional[pd.DataFrame],
                                   rss_df: Optional[pd.DataFrame]) -> pd.DataFrame:
        """
        Calculate unified sentiment from all available sources.
        Adaptive weighting based on what's available.
        """
        logger.info("Calculating unified sentiment from all sources...")
        
        available_sources = []
        weights = {}
        
        # Determine weights based on availability and reliability
        if social_df is not None and not social_df.empty:
            available_sources.append(('social', social_df, 0.35))
            weights['social'] = 0.35
        
        if analyst_df is not None and not analyst_df.empty:
            available_sources.append(('analyst', analyst_df, 0.30))
            weights['analyst'] = 0.30
        
        if news_df is not None and not news_df.empty:
            available_sources.append(('news', news_df, 0.20))
            weights['news'] = 0.20
        
        if rss_df is not None and not rss_df.empty:
            available_sources.append(('rss', rss_df, 0.15))
            weights['rss'] = 0.15
        
        if not available_sources:
            logger.error("No sentiment sources available!")
            return pd.DataFrame()
        
        # Normalize weights
        total_weight = sum(w for _, _, w in available_sources)
        normalized_sources = [(name, df, w/total_weight) for name, df, w in available_sources]
        
        # Aggregate by day
        daily_sentiments = []
        
        for source_name, df, weight in normalized_sources:
            if 'timestamp' in df.columns and 'sentiment' in df.columns:
                # Convert to daily
                df['date'] = pd.to_datetime(df['timestamp']).dt.date
                
                daily = df.groupby('date').agg({
                    'sentiment': 'mean',
                    'timestamp': 'count'  # Volume
                }).rename(columns={
                    'sentiment': f'{source_name}_sentiment',
                    'timestamp': f'{source_name}_volume'
                })
                
                daily[f'{source_name}_weight'] = weight
                daily_sentiments.append(daily)
        
        # Combine all sources
        if daily_sentiments:
            unified = pd.concat(daily_sentiments, axis=1)
            
            # Calculate weighted sentiment
            unified['unified_sentiment'] = 0
            unified['total_volume'] = 0
            
            for source_name, _, weight in normalized_sources:
                sent_col = f'{source_name}_sentiment'
                vol_col = f'{source_name}_volume'
                
                if sent_col in unified.columns:
                    unified['unified_sentiment'] += unified[sent_col].fillna(0) * weight
                if vol_col in unified.columns:
                    unified['total_volume'] += unified[vol_col].fillna(0)
            
            # Add confidence score based on volume and agreement
            unified['confidence'] = self._calculate_confidence(unified, normalized_sources)
            
            # Add trend
            unified['sentiment_ma_7d'] = unified['unified_sentiment'].rolling(7).mean()
            unified['sentiment_trend'] = unified['unified_sentiment'] - unified['sentiment_ma_7d']
            
            return unified
        
        return pd.DataFrame()
    
    def _calculate_confidence(self, df: pd.DataFrame, sources: List) -> pd.Series:
        """
        Calculate confidence score based on:
        1. Volume of data
        2. Agreement between sources
        """
        confidence = pd.Series(index=df.index, dtype=float)
        
        for idx in df.index:
            # Get all sentiment values for this day
            sentiments = []
            volumes = []
            
            for source_name, _, _ in sources:
                sent_col = f'{source_name}_sentiment'
                vol_col = f'{source_name}_volume'
                
                if sent_col in df.columns and not pd.isna(df.loc[idx, sent_col]):
                    sentiments.append(df.loc[idx, sent_col])
                if vol_col in df.columns:
                    volumes.append(df.loc[idx, vol_col])
            
            if sentiments:
                # Agreement score (low std = high agreement)
                agreement = 1 - min(np.std(sentiments), 1)
                
                # Volume score (more data = higher confidence)
                volume_score = min(sum(volumes) / 100, 1)  # Normalize to 0-1
                
                # Combined confidence
                confidence[idx] = (agreement * 0.6 + volume_score * 0.4)
            else:
                confidence[idx] = 0
        
        return confidence
    
    # ==================== MASTER COLLECTION ====================
    
    def collect_all_sentiment_with_fallbacks(self) -> Dict:
        """
        Collect sentiment from all sources with automatic fallback.
        """
        print("="*80)
        print("COLLECTING SENTIMENT WITH MULTI-SOURCE FALLBACK")
        print("="*80)
        
        results = {}
        
        # Tier 1: Social Media
        social_df = self.collect_social_sentiment()
        if social_df is not None:
            print(f"✅ Tier 1 (Social): {len(social_df)} items")
            results['social'] = len(social_df)
        else:
            print("⚠️ Tier 1 (Social): Failed, trying fallback...")
        
        # Tier 2: Market Analysts
        analyst_df = self.collect_analyst_sentiment()
        if analyst_df is not None:
            print(f"✅ Tier 2 (Analysts): {len(analyst_df)} items")
            results['analysts'] = len(analyst_df)
        else:
            print("⚠️ Tier 2 (Analysts): Failed, trying fallback...")
        
        # Tier 3: News APIs
        news_df = self.collect_news_sentiment()
        if news_df is not None:
            print(f"✅ Tier 3 (News): {len(news_df)} items")
            results['news'] = len(news_df)
        else:
            print("⚠️ Tier 3 (News): Failed, trying fallback...")
        
        # Tier 4: RSS Feeds (always works)
        rss_df = self.collect_rss_sentiment()
        print(f"✅ Tier 4 (RSS): {len(rss_df)} items")
        results['rss'] = len(rss_df)
        
        # Calculate unified sentiment
        unified_df = self.calculate_unified_sentiment(social_df, analyst_df, news_df, rss_df)
        
        if not unified_df.empty:
            print(f"\n✅ Unified sentiment calculated: {len(unified_df)} days")
            print(f"   Average sentiment: {unified_df['unified_sentiment'].mean():.3f}")
            print(f"   Average confidence: {unified_df['confidence'].mean():.3f}")
            results['unified_days'] = len(unified_df)
            
            # Save all data
            if social_df is not None:
                social_df.to_parquet(RAW_DIR / "social_sentiment.parquet")
            if analyst_df is not None:
                analyst_df.to_parquet(RAW_DIR / "analyst_sentiment.parquet")
            if news_df is not None:
                news_df.to_parquet(RAW_DIR / "news_sentiment.parquet")
            rss_df.to_parquet(RAW_DIR / "rss_sentiment.parquet")
            unified_df.to_parquet(RAW_DIR / "unified_sentiment.parquet")
            
            # Create summary report
            self._create_sentiment_report(unified_df)
        else:
            print("❌ Failed to calculate unified sentiment")
        
        print("\n" + "="*80)
        print(f"SENTIMENT COLLECTION COMPLETE")
        print(f"Sources used: {list(results.keys())}")
        print("="*80)
        
        return results
    
    def _create_sentiment_report(self, df: pd.DataFrame):
        """Create a summary report of sentiment analysis"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'date_range': {
                'start': str(df.index.min()),
                'end': str(df.index.max())
            },
            'summary': {
                'mean_sentiment': float(df['unified_sentiment'].mean()),
                'std_sentiment': float(df['unified_sentiment'].std()),
                'current_sentiment': float(df['unified_sentiment'].iloc[-1]),
                'trend_7d': float(df['sentiment_trend'].iloc[-7:].mean()) if len(df) >= 7 else 0,
                'mean_confidence': float(df['confidence'].mean())
            },
            'extremes': {
                'most_positive_day': str(df['unified_sentiment'].idxmax()),
                'most_positive_value': float(df['unified_sentiment'].max()),
                'most_negative_day': str(df['unified_sentiment'].idxmin()),
                'most_negative_value': float(df['unified_sentiment'].min())
            }
        }
        
        # Save report
        with open(RAW_DIR / 'sentiment_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print("\n📊 Sentiment Report Summary:")
        print(f"   Mean sentiment: {report['summary']['mean_sentiment']:.3f}")
        print(f"   Current sentiment: {report['summary']['current_sentiment']:.3f}")
        print(f"   7-day trend: {report['summary']['trend_7d']:.3f}")
        print(f"   Confidence: {report['summary']['mean_confidence']:.3f}")


if __name__ == "__main__":
    # Set environment variables for API keys
    # export SCRAPE_CREATORS_KEY='your_key'
    # export NEWSAPI_KEY='your_key'
    # export ALPHA_VANTAGE_KEY='your_key'
    # export FINNHUB_KEY='your_key'
    
    collector = MultiSourceSentimentCollector()
    results = collector.collect_all_sentiment_with_fallbacks()
    
    print(f"\nFinal results: {results}")
