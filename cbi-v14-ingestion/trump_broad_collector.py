#!/usr/bin/env python3
"""
Trump Broad Data Collector - 50 Posts Analysis
Collect ~50 Trump posts to analyze relevance and market correlation patterns
Uses Scrape Creators API with intelligent sampling strategy
PRODUCTION GRADE - Following CURSOR_RULES
"""

import requests
import time
import json
import logging
import yfinance as yf
from datetime import datetime, timezone, timedelta
from google.cloud import bigquery
import pandas as pd
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('trump_broad')

class TrumpBroadCollector:
    """
    Broad Trump post collection for pattern analysis
    Target: ~50 posts to understand relevance and correlation
    """
    
    def __init__(self):
        self.api_key = 'B1TOgQvMVSV6TDglqB8lJ2cirqi2'
        self.client = bigquery.Client(project='cbi-v14')
        self.credits_used = 0
        self.posts_collected = []
        
        # Keywords for market relevance analysis
        self.keyword_categories = {
            'agricultural': ['soybeans', 'soybean', 'farmers', 'agriculture', 'rural', 'heartland', 'farm bill', 'corn', 'wheat'],
            'trade': ['trade', 'tariffs', 'china trade', 'exports', 'bilateral', 'epa', 'biofuels', 'imports', 'wto'],
            'geographic': ['china', 'brazil', 'argentina', 'midwest', 'iowa', 'illinois'],
            'fear': ['military', 'dissent', 'democrat', 'war', 'conflict', 'crisis', 'threat', 'emergency', 'investigation']
        }
    
    def generate_post_id_range(self, base_id, target_count=50):
        """
        Generate a range of post IDs to test
        Strategy: Sample around known working ID with different increments
        """
        base_int = int(base_id)
        test_ids = []
        
        # Strategy 1: Small increments around baseline (recent posts)
        for i in range(-10, 11):
            if i != 0:  # Skip baseline (we'll test it separately)
                test_ids.append(str(base_int + (i * 100000)))
        
        # Strategy 2: Larger increments for older posts
        for i in range(1, 16):
            test_ids.append(str(base_int - (i * 1000000)))
        
        # Strategy 3: Forward increments for newer posts
        for i in range(1, 16):
            test_ids.append(str(base_int + (i * 1000000)))
        
        # Limit to target count
        return test_ids[:target_count]
    
    def collect_post_data(self, post_id):
        """
        Collect individual post with full error handling
        """
        post_url = f'https://truthsocial.com/@realDonaldTrump/{post_id}'
        
        try:
            response = requests.get(
                'https://api.scrapecreators.com/v1/truthsocial/post',
                headers={'x-api-key': self.api_key},
                params={'url': post_url},
                timeout=20
            )
            
            self.credits_used += 1
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    # Extract comprehensive post data
                    post_data = {
                        'id': post_id,
                        'created_at': data.get('created_at'),
                        'text': data.get('text', ''),
                        'replies_count': data.get('replies_count', 0),
                        'reblogs_count': data.get('reblogs_count', 0),
                        'favourites_count': data.get('favourites_count', 0),
                        'url': post_url,
                        'credits_remaining': data.get('credits_remaining', 0)
                    }
                    
                    return post_data
                else:
                    return None
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error collecting post {post_id}: {e}")
            return None
    
    def analyze_market_relevance(self, post):
        """
        Comprehensive market relevance analysis
        """
        content = post['text'].lower()
        
        # Count keywords by category
        scores = {}
        for category, keywords in self.keyword_categories.items():
            scores[f'{category}_score'] = sum(1 for keyword in keywords if keyword in content)
        
        # Calculate total relevance
        total_relevance = sum(scores.values())
        
        # Calculate specific impact scores
        agricultural_impact = (scores['agricultural_score'] + scores['trade_score'] * 0.8) / 10.0
        agricultural_impact = min(agricultural_impact, 1.0)
        
        soybean_relevance = (content.count('soybean') + content.count('soybeans') + 
                           content.count('china') * 0.5 + content.count('trade') * 0.3) / 5.0
        soybean_relevance = min(soybean_relevance, 1.0)
        
        # VIX impact potential (fear keywords)
        vix_impact = scores['fear_score'] * 0.15
        vix_impact = min(vix_impact, 1.0)
        
        # Engagement impact multiplier
        engagement_score = (post['replies_count'] + post['favourites_count']) / 10000.0
        engagement_multiplier = min(1.0 + engagement_score, 3.0)  # Cap at 3x
        
        return {
            **scores,
            'total_relevance': total_relevance,
            'agricultural_impact': agricultural_impact * engagement_multiplier,
            'soybean_relevance': soybean_relevance * engagement_multiplier,
            'vix_impact_potential': vix_impact * engagement_multiplier,
            'engagement_multiplier': engagement_multiplier,
            'is_market_relevant': total_relevance > 0
        }
    
    def get_vix_correlation(self, post_date):
        """
        Get VIX data around post date for correlation analysis
        """
        try:
            post_datetime = datetime.fromisoformat(post_date.replace('Z', '+00:00'))
            
            # Get VIX data for 3 days around the post
            start_date = post_datetime.date() - timedelta(days=1)
            end_date = post_datetime.date() + timedelta(days=2)
            
            vix_ticker = yf.Ticker('^VIX')
            vix_data = vix_ticker.history(start=start_date, end=end_date)
            
            if not vix_data.empty:
                return {
                    'vix_before': float(vix_data['Close'].iloc[0]) if len(vix_data) > 0 else None,
                    'vix_after': float(vix_data['Close'].iloc[-1]) if len(vix_data) > 0 else None,
                    'vix_change': float(vix_data['Close'].iloc[-1] - vix_data['Close'].iloc[0]) if len(vix_data) > 1 else 0
                }
        except Exception as e:
            logger.warning(f"Could not get VIX correlation for {post_date}: {e}")
        
        return {'vix_before': None, 'vix_after': None, 'vix_change': 0}
    
    def run_broad_collection(self, target_posts=50):
        """
        Run broad collection of ~50 Trump posts for analysis
        """
        logger.info("=" * 80)
        logger.info(f"TRUMP BROAD COLLECTION - TARGET: {target_posts} POSTS")
        logger.info("Analyzing market relevance and VIX correlation patterns")
        logger.info("=" * 80)
        
        # Generate post IDs to test
        baseline_id = '114315219437063160'
        test_ids = self.generate_post_id_range(baseline_id, target_posts)
        
        logger.info(f"🎯 Testing {len(test_ids)} post IDs...")
        
        collected_posts = []
        market_relevant_posts = []
        
        for i, post_id in enumerate(test_ids):
            logger.info(f"📱 Testing post {i+1}/{len(test_ids)}: {post_id}")
            
            # Collect post data
            post_data = self.collect_post_data(post_id)
            
            if post_data:
                collected_posts.append(post_data)
                
                # Analyze market relevance
                analysis = self.analyze_market_relevance(post_data)
                post_data['market_analysis'] = analysis
                
                # Get VIX correlation
                vix_correlation = self.get_vix_correlation(post_data['created_at'])
                post_data['vix_correlation'] = vix_correlation
                
                if analysis['is_market_relevant']:
                    market_relevant_posts.append(post_data)
                    logger.info(f"  ✅ MARKET RELEVANT - Total keywords: {analysis['total_relevance']}")
                    logger.info(f"     Ag: {analysis['agricultural_score']}, Trade: {analysis['trade_score']}, Fear: {analysis['fear_score']}")
                    logger.info(f"     Engagement: {post_data['favourites_count']} likes, {post_data['replies_count']} replies")
                else:
                    logger.info(f"  ⚪ Not market relevant")
                
                logger.info(f"  💳 Credits remaining: {post_data.get('credits_remaining', 'Unknown')}")
            else:
                logger.info(f"  ❌ Post not found")
            
            # Rate limiting (but faster for broad collection)
            if i < len(test_ids) - 1:
                time.sleep(5)  # 5 seconds between tests
            
            # Stop if we hit our target of collected posts
            if len(collected_posts) >= target_posts:
                logger.info(f"🎯 Target reached: {len(collected_posts)} posts collected")
                break
            
            # Stop if we're running low on credits
            if self.credits_used > 80:
                logger.warning("⚠️ Approaching credit limit, stopping collection")
                break
        
        # Analysis Summary
        logger.info("=" * 80)
        logger.info("BROAD COLLECTION ANALYSIS")
        logger.info("=" * 80)
        logger.info(f"📱 Total posts tested: {len(test_ids)}")
        logger.info(f"✅ Posts found: {len(collected_posts)}")
        logger.info(f"🎯 Market-relevant posts: {len(market_relevant_posts)}")
        logger.info(f"💳 Credits used: {self.credits_used}")
        logger.info(f"📊 Success rate: {len(collected_posts)/self.credits_used*100:.1f}%")
        logger.info(f"🎯 Relevance rate: {len(market_relevant_posts)/len(collected_posts)*100:.1f}%" if collected_posts else "0%")
        
        if market_relevant_posts:
            # Detailed market analysis
            logger.info("")
            logger.info("🎯 MARKET CORRELATION ANALYSIS:")
            
            total_engagement = sum(p['favourites_count'] + p['replies_count'] for p in market_relevant_posts)
            avg_engagement = total_engagement / len(market_relevant_posts)
            
            high_engagement = [p for p in market_relevant_posts if (p['favourites_count'] + p['replies_count']) > avg_engagement]
            fear_posts = [p for p in market_relevant_posts if p['market_analysis']['fear_score'] > 0]
            ag_posts = [p for p in market_relevant_posts if p['market_analysis']['agricultural_score'] > 0]
            trade_posts = [p for p in market_relevant_posts if p['market_analysis']['trade_score'] > 0]
            
            logger.info(f"   Average engagement: {avg_engagement:.0f} interactions")
            logger.info(f"   High-engagement posts: {len(high_engagement)}")
            logger.info(f"   Fear-keyword posts: {len(fear_posts)} (VIX impact)")
            logger.info(f"   Agricultural posts: {len(ag_posts)} (commodity impact)")
            logger.info(f"   Trade posts: {len(trade_posts)} (soybean impact)")
            
            # VIX correlation analysis
            vix_changes = [p['vix_correlation']['vix_change'] for p in market_relevant_posts 
                          if p['vix_correlation']['vix_change'] != 0]
            
            if vix_changes:
                avg_vix_change = sum(vix_changes) / len(vix_changes)
                logger.info(f"   Average VIX change: {avg_vix_change:.2f}")
                logger.info(f"   VIX spike posts: {sum(1 for change in vix_changes if change > 1.0)}")
        
        logger.info("=" * 80)
        
        return {
            'total_tested': len(test_ids),
            'posts_found': len(collected_posts),
            'market_relevant': len(market_relevant_posts),
            'credits_used': self.credits_used,
            'posts_data': market_relevant_posts
        }

if __name__ == '__main__':
    collector = TrumpBroadCollector()
    results = collector.run_broad_collection(target_posts=50)
    
    if results['market_relevant'] > 0:
        logger.info(f"🎉 SUCCESS: Found {results['market_relevant']} market-relevant posts")
        logger.info("✅ Ready for detailed correlation analysis")
        
        # Save summary to file for analysis
        with open('/tmp/trump_broad_analysis.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info("📄 Analysis saved to /tmp/trump_broad_analysis.json")
    else:
        logger.warning("⚠️ No market-relevant posts found in broad collection")











