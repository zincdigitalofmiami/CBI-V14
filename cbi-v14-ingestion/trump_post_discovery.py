#!/usr/bin/env python3
"""
Trump Post Discovery System
Systematic approach to discover and collect Trump Truth Social posts
Uses Scrape Creators API with intelligent post ID discovery
PRODUCTION GRADE - Following CURSOR_RULES
"""

import requests
import time
import json
import logging
from datetime import datetime, timezone, timedelta
from google.cloud import bigquery
import pandas as pd
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('trump_discovery')

class TrumpPostDiscovery:
    """
    Intelligent Trump post discovery and collection system
    """
    
    def __init__(self):
        self.api_key = 'B1TOgQvMVSV6TDglqB8lJ2cirqi2'
        self.client = bigquery.Client(project='cbi-v14')
        self.credits_used = 0
        
        # Known working post ID as baseline
        self.baseline_post_id = '114315219437063160'
        self.baseline_date = '2025-04-10T19:03:40.023Z'
    
    def test_post_id(self, post_id):
        """
        Test if a post ID exists and collect data
        """
        post_url = f'https://truthsocial.com/@realDonaldTrump/{post_id}'
        
        try:
            response = requests.get(
                'https://api.scrapecreators.com/v1/truthsocial/post',
                headers={'x-api-key': self.api_key},
                params={'url': post_url},
                timeout=15
            )
            
            self.credits_used += 1
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    return {
                        'id': post_id,
                        'found': True,
                        'created_at': data.get('created_at'),
                        'text': data.get('text', ''),
                        'replies_count': data.get('replies_count', 0),
                        'reblogs_count': data.get('reblogs_count', 0),
                        'favourites_count': data.get('favourites_count', 0),
                        'credits_remaining': data.get('credits_remaining', 0)
                    }
                else:
                    return {'id': post_id, 'found': False, 'error': data.get('message')}
            else:
                return {'id': post_id, 'found': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            return {'id': post_id, 'found': False, 'error': str(e)}
    
    def discover_posts_by_range(self, base_id, range_size=1000000, max_tests=20):
        """
        Discover posts by testing ID ranges around known post
        """
        logger.info(f"🔍 Discovering posts around ID {base_id}")
        
        base_id_int = int(base_id)
        discovered_posts = []
        
        # Test IDs in both directions from baseline
        test_ids = []
        
        # Go backwards (older posts)
        for i in range(1, max_tests//2 + 1):
            test_ids.append(str(base_id_int - (i * range_size)))
        
        # Go forwards (newer posts) 
        for i in range(1, max_tests//2 + 1):
            test_ids.append(str(base_id_int + (i * range_size)))
        
        logger.info(f"🔍 Testing {len(test_ids)} post IDs...")
        
        for i, test_id in enumerate(test_ids):
            logger.info(f"📱 Testing {i+1}/{len(test_ids)}: {test_id}")
            
            result = self.test_post_id(test_id)
            
            if result['found']:
                discovered_posts.append(result)
                logger.info(f"  ✅ FOUND: {result['created_at']} - {len(result['text'])} chars")
            else:
                logger.info(f"  ❌ Not found: {result.get('error', 'Unknown')}")
            
            # Rate limiting (10 seconds for discovery)
            if i < len(test_ids) - 1:
                time.sleep(10)
            
            # Stop if we're running low on credits
            if self.credits_used > 80:
                logger.warning("⚠️ Approaching credit limit, stopping discovery")
                break
        
        logger.info(f"✅ Discovery complete: {len(discovered_posts)} posts found")
        return discovered_posts
    
    def analyze_market_relevance(self, posts):
        """
        Analyze posts for agricultural/trade market relevance
        """
        # Keywords from user specification
        agricultural_keywords = ['soybeans', 'soybean', 'farmers', 'agriculture', 'rural', 'heartland', 'farm bill']
        trade_keywords = ['trade', 'tariffs', 'china trade', 'exports', 'bilateral', 'epa', 'biofuels']
        geographic_keywords = ['china', 'brazil', 'argentina']
        fear_keywords = ['military', 'dissent', 'democrat', 'war', 'conflict', 'crisis', 'threat']
        
        market_relevant_posts = []
        
        for post in posts:
            content = post['text'].lower()
            
            # Count keywords
            ag_score = sum(1 for keyword in agricultural_keywords if keyword in content)
            trade_score = sum(1 for keyword in trade_keywords if keyword in content)
            geo_score = sum(1 for keyword in geographic_keywords if keyword in content)
            fear_score = sum(1 for keyword in fear_keywords if keyword in content)
            
            total_relevance = ag_score + trade_score + geo_score + fear_score
            
            if total_relevance > 0:
                post['market_analysis'] = {
                    'agricultural_score': ag_score,
                    'trade_score': trade_score,
                    'geographic_score': geo_score,
                    'fear_score': fear_score,
                    'total_relevance': total_relevance,
                    'vix_impact_potential': fear_score * 0.15
                }
                market_relevant_posts.append(post)
                
                logger.info(f"📊 Market-relevant post found:")
                logger.info(f"   Date: {post['created_at']}")
                logger.info(f"   Keywords: Ag({ag_score}) Trade({trade_score}) Geo({geo_score}) Fear({fear_score})")
                logger.info(f"   Engagement: {post['favourites_count']} likes, {post['replies_count']} replies")
                logger.info(f"   Content: {post['text'][:100]}...")
                logger.info("")
        
        return market_relevant_posts
    
    def run_30_day_discovery(self):
        """
        Run 30-day Trump post discovery and analysis
        """
        logger.info("=" * 80)
        logger.info("TRUMP TRUTH SOCIAL 30-DAY DATA DISCOVERY")
        logger.info("Systematic post discovery and market relevance analysis")
        logger.info("=" * 80)
        
        # Start with known working post
        logger.info(f"🎯 Starting from baseline post: {self.baseline_post_id}")
        
        # Test baseline first
        baseline_result = self.test_post_id(self.baseline_post_id)
        
        if not baseline_result['found']:
            logger.error("❌ Baseline post not accessible")
            return []
        
        logger.info(f"✅ Baseline confirmed: {baseline_result['created_at']}")
        
        # Discover more posts
        discovered_posts = self.discover_posts_by_range(
            self.baseline_post_id, 
            range_size=500000,  # Try smaller increments
            max_tests=15  # Limit to conserve credits
        )
        
        # Add baseline to discovered posts
        all_posts = [baseline_result] + discovered_posts
        
        # Analyze for market relevance
        market_posts = self.analyze_market_relevance(all_posts)
        
        # Summary
        logger.info("=" * 80)
        logger.info("30-DAY DISCOVERY SUMMARY")
        logger.info("=" * 80)
        logger.info(f"📱 Total posts tested: {len(all_posts)}")
        logger.info(f"🎯 Market-relevant posts: {len(market_posts)}")
        logger.info(f"💳 Credits used: {self.credits_used}")
        logger.info(f"📊 Success rate: {len(all_posts)/self.credits_used*100:.1f}%")
        
        if market_posts:
            logger.info("")
            logger.info("🎯 MARKET IMPACT ANALYSIS:")
            total_engagement = sum(p['favourites_count'] + p['replies_count'] for p in market_posts)
            avg_engagement = total_engagement / len(market_posts)
            
            logger.info(f"   Average engagement: {avg_engagement:.0f} interactions per post")
            logger.info(f"   High-impact posts (>10k likes): {sum(1 for p in market_posts if p['favourites_count'] > 10000)}")
            logger.info(f"   Fear-keyword posts: {sum(1 for p in market_posts if p.get('market_analysis', {}).get('fear_score', 0) > 0)}")
        
        logger.info("=" * 80)
        
        return market_posts

if __name__ == '__main__':
    discovery = TrumpPostDiscovery()
    market_posts = discovery.run_30_day_discovery()
    
    if market_posts:
        print(f'🎉 SUCCESS: Found {len(market_posts)} market-relevant Trump posts')
        print('✅ Ready for production VIX correlation analysis')
    else:
        print('⚠️ No market-relevant posts found in discovery range')
