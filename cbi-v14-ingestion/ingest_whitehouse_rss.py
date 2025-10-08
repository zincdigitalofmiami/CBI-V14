#!/usr/bin/env python3
"""
ingest_whitehouse_rss.py
WhiteHouse.gov RSS feed scraper for presidential actions and statements
CRITICAL: Real-time policy announcements affecting commodity markets
"""

import requests
import pandas as pd
import feedparser
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from google.cloud import bigquery
from bigquery_utils import intelligence_collector
from cache_utils import get_cache
import logging
import time

logger = logging.getLogger(__name__)

class WhiteHouseRSSCollector:
    """
    Collect White House presidential actions and statements via RSS
    Focus on trade, agricultural, and economic policy announcements
    """
    
    def __init__(self):
        self.cache = get_cache()
        
        # RSS feeds to monitor
        self.rss_feeds = {
            'presidential_actions': {
                'url': 'https://www.whitehouse.gov/briefing-room/presidential-actions/feed/',
                'category': 'presidential_action',
                'priority': 1
            },
            'statements_releases': {
                'url': 'https://www.whitehouse.gov/briefing-room/statements-releases/feed/',
                'category': 'statement_release',
                'priority': 2
            },
            'speeches_remarks': {
                'url': 'https://www.whitehouse.gov/briefing-room/speeches-remarks/feed/',
                'category': 'speech_remark',
                'priority': 3
            }
        }
        
        # Keywords for agricultural/trade impact
        self.impact_keywords = {
            'high_impact': [
                'tariff', 'trade war', 'china trade', 'agricultural trade',
                'soybean', 'commodity tariff', 'nafta', 'usmca', 'trade deal'
            ],
            'medium_impact': [
                'agriculture', 'farming', 'rural', 'commodity', 'export',
                'import', 'trade', 'china', 'mexico', 'canada', 'brazil'
            ],
            'policy_indicators': [
                'executive order', 'presidential memorandum', 'proclamation',
                'trade policy', 'agricultural policy', 'economic policy'
            ]
        }
    
    @intelligence_collector('ice_trump_intelligence', cache_ttl_hours=2)
    def collect_whitehouse_announcements(self, hours_back=24):
        """
        Collect White House announcements from RSS feeds
        
        Args:
            hours_back: Hours to look back for new announcements
            
        Returns:
            DataFrame with announcements and impact analysis
        """
        logger.info(f"Collecting White House announcements from last {hours_back} hours")
        
        all_announcements = []
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        for feed_name, feed_config in self.rss_feeds.items():
            logger.info(f"Processing RSS feed: {feed_name}")
            
            try:
                # Check cache first
                cache_key = f"whitehouse_rss_{feed_name}_{datetime.now().strftime('%Y%m%d%H')}"
                cached_feed = self.cache.get_api_response(feed_config['url'], None, ttl_hours=1)
                
                if cached_feed:
                    logger.info(f"Using cached RSS data for {feed_name}")
                    feed_data = cached_feed
                else:
                    # Fetch RSS feed
                    response = requests.get(feed_config['url'], timeout=15)
                    response.raise_for_status()
                    
                    # Parse RSS
                    feed_data = feedparser.parse(response.content)
                    
                    # Cache the parsed feed
                    self.cache.set_api_response(feed_config['url'], None, feed_data.entries)
                    logger.info(f"Fetched and cached {len(feed_data.entries)} entries from {feed_name}")
                
                # Process entries
                for entry in feed_data.entries if hasattr(feed_data, 'entries') else feed_data:
                    try:
                        # Parse publication date
                        pub_date = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now()
                        
                        # Skip old entries
                        if pub_date < cutoff_time:
                            continue
                        
                        # Extract content
                        title = getattr(entry, 'title', '')
                        summary = getattr(entry, 'summary', '')
                        link = getattr(entry, 'link', '')
                        
                        # Get full content if available
                        full_content = self._extract_full_content(link)
                        
                        # Analyze impact
                        impact_analysis = self._analyze_policy_impact(title, summary, full_content)
                        
                        announcement_data = {
                            'source': 'whitehouse_gov_rss',
                            'category': feed_config['category'],
                            'text': f"{title} - {summary}"[:500],
                            'agricultural_impact': impact_analysis['agricultural_impact'],
                            'soybean_relevance': impact_analysis['soybean_relevance'],
                            'timestamp': pub_date,
                            'priority': self._calculate_priority(impact_analysis, feed_config['priority']),
                            'title': title,
                            'summary': summary,
                            'url': link,
                            'feed_source': feed_name,
                            'trade_keywords_found': impact_analysis['trade_keywords'],
                            'agricultural_keywords_found': impact_analysis['agricultural_keywords'],
                            'policy_type': impact_analysis['policy_type'],
                            'market_impact_predicted': impact_analysis['market_impact'],
                            'ingestion_timestamp': datetime.now()
                        }
                        
                        all_announcements.append(announcement_data)
                        
                    except Exception as e:
                        logger.warning(f"Failed to process entry from {feed_name}: {e}")
                        continue
                
                # Rate limiting between feeds
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to process RSS feed {feed_name}: {e}")
                continue
        
        if not all_announcements:
            logger.info("No new White House announcements found")
            return pd.DataFrame()
        
        df = pd.DataFrame(all_announcements)
        
        # Alert on high-impact announcements
        high_impact = df[df['agricultural_impact'] > 0.7]
        if not high_impact.empty:
            logger.warning(f"🚨 {len(high_impact)} HIGH-IMPACT POLICY ANNOUNCEMENTS DETECTED:")
            for _, announcement in high_impact.iterrows():
                logger.warning(f"  - {announcement['title']} (Impact: {announcement['agricultural_impact']:.2f})")
        
        return df
    
    def _extract_full_content(self, url):
        """Extract full content from White House page"""
        if not url:
            return ""
        
        try:
            # Check cache first
            cached_content = self.cache.get_api_response(url, None, ttl_hours=24)
            if cached_content:
                return cached_content
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract main content
            content_selectors = [
                'article.presidential-action',
                '.page-content',
                '.entry-content',
                'main'
            ]
            
            content = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text(strip=True)
                    break
            
            # Truncate for storage
            content = content[:5000]
            
            # Cache the content
            self.cache.set_api_response(url, None, content)
            
            return content
            
        except Exception as e:
            logger.warning(f"Failed to extract content from {url}: {e}")
            return ""
    
    def _analyze_policy_impact(self, title, summary, full_content):
        """
        Analyze policy announcement for agricultural/commodity impact
        
        Returns:
            Dict with impact scores and analysis
        """
        # Combine all text for analysis
        all_text = " ".join([title, summary, full_content]).lower()
        
        # Count keyword occurrences
        high_impact_count = sum(1 for kw in self.impact_keywords['high_impact'] if kw in all_text)
        medium_impact_count = sum(1 for kw in self.impact_keywords['medium_impact'] if kw in all_text)
        policy_indicators = sum(1 for kw in self.impact_keywords['policy_indicators'] if kw in all_text)
        
        trade_keywords = sum(1 for kw in ['trade', 'tariff', 'export', 'import'] if kw in all_text)
        agricultural_keywords = sum(1 for kw in ['agriculture', 'farming', 'soybean', 'commodity'] if kw in all_text)
        
        # Calculate impact scores (0.0 to 1.0)
        agricultural_impact = min((high_impact_count * 0.3 + medium_impact_count * 0.1 + policy_indicators * 0.1), 1.0)
        soybean_relevance = min((high_impact_count * 0.4 + agricultural_keywords * 0.2), 1.0)
        
        # Determine policy type
        if 'executive order' in all_text:
            policy_type = 'executive_order'
        elif 'proclamation' in all_text:
            policy_type = 'proclamation'
        elif 'memorandum' in all_text:
            policy_type = 'memorandum'
        else:
            policy_type = 'statement'
        
        # Predict market impact
        market_impact = 'high' if high_impact_count > 0 else ('medium' if medium_impact_count > 2 else 'low')
        
        return {
            'agricultural_impact': agricultural_impact,
            'soybean_relevance': soybean_relevance,
            'trade_keywords': trade_keywords,
            'agricultural_keywords': agricultural_keywords,
            'policy_type': policy_type,
            'market_impact': market_impact
        }
    
    def _calculate_priority(self, impact_analysis, base_priority):
        """Calculate final priority based on impact analysis"""
        if impact_analysis['agricultural_impact'] > 0.7:
            return 1  # Critical
        elif impact_analysis['agricultural_impact'] > 0.4:
            return 2  # High
        elif impact_analysis['agricultural_impact'] > 0.2:
            return 3  # Medium
        else:
            return max(base_priority, 4)  # Low


def main():
    """Execute White House RSS collection"""
    collector = WhiteHouseRSSCollector()
    
    print("=== WHITE HOUSE RSS INTELLIGENCE ===")
    print("Monitoring presidential actions and policy statements")
    print("=" * 60)
    
    # Collect announcements from last 24 hours
    announcements_df = collector.collect_whitehouse_announcements(hours_back=24)
    
    if not announcements_df.empty:
        print(f"✅ Collected {len(announcements_df)} White House announcements")
        
        # Show high-impact summary
        high_impact = announcements_df[announcements_df['agricultural_impact'] > 0.5]
        if not high_impact.empty:
            print(f"\n🚨 HIGH-IMPACT ANNOUNCEMENTS ({len(high_impact)}):")
            for _, announcement in high_impact.iterrows():
                print(f"  - {announcement['title']} (Impact: {announcement['agricultural_impact']:.2f})")
        
        # Show by category
        category_counts = announcements_df['category'].value_counts()
        print(f"\n📊 BY CATEGORY:")
        for category, count in category_counts.items():
            print(f"  - {category}: {count} announcements")
        
        # Show trade-related announcements
        trade_related = announcements_df[announcements_df['trade_keywords_found'] > 0]
        if not trade_related.empty:
            print(f"\n📈 TRADE-RELATED ANNOUNCEMENTS ({len(trade_related)}):")
            for _, announcement in trade_related.iterrows():
                print(f"  - {announcement['title']} ({announcement['trade_keywords_found']} trade keywords)")
    
    else:
        print("No new White House announcements found in the specified period")
    
    print("✅ White House RSS intelligence collection completed")


if __name__ == "__main__":
    main()

