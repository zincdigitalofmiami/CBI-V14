#!/usr/bin/env python3
"""
ingest_executive_orders.py
Federal Register API for Trump executive orders
CRITICAL: Tariffs = 20-40% commodity price shock
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from google.cloud import bigquery
from bigquery_utils import intelligence_collector, quick_save_to_bigquery
from cache_utils import get_cache
import logging

logger = logging.getLogger(__name__)

class ExecutiveOrdersCollector:
    """
    Collect Trump executive orders from Federal Register API
    Focus on trade/tariff/agricultural policy impacts
    """
    
    def __init__(self):
        self.base_url = "https://www.federalregister.gov/api/v1/documents.json"
        self.cache = get_cache()
        
        # Keywords for commodity impact detection
        self.commodity_keywords = [
            'tariff', 'trade', 'import', 'export', 'china', 'mexico', 
            'agriculture', 'soybean', 'commodity', 'farming', 'agricultural',
            'nafta', 'usmca', 'wto', 'customs', 'duty', 'quota'
        ]
        
        self.high_impact_keywords = [
            'tariff', 'trade war', 'china trade', 'agricultural trade',
            'soybean', 'commodity tariff'
        ]
    
    @intelligence_collector('trump_policy_intelligence', cache_ttl_hours=6)
    def collect_executive_orders(self, days_back=30):
        """
        Fetch recent executive orders with commodity impact analysis
        
        Args:
            days_back: Number of days to look back for orders
            
        Returns:
            DataFrame with executive orders and impact analysis
        """
        logger.info(f"Collecting executive orders from last {days_back} days")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        params = {
            'conditions[presidential_document_type][]': 'executive_order',
            'conditions[president]': 'donald-trump',
            'conditions[publication_date][gte]': start_date.strftime('%Y-%m-%d'),
            'order': 'newest',
            'per_page': 100,  # Get up to 100 orders per request
            'fields[]': ['title', 'publication_date', 'executive_order_number', 
                        'abstract', 'full_text_xml_url', 'pdf_url', 'html_url']
        }
        
        # Check cache first
        cache_key = f"executive_orders_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
        cached_response = self.cache.get_api_response(self.base_url, params, ttl_hours=6)
        
        if cached_response:
            logger.info("Using cached executive orders response")
            # Handle cached response format
            if isinstance(cached_response, dict) and 'data' in cached_response:
                orders = cached_response['data']
            elif isinstance(cached_response, list):
                orders = cached_response
            else:
                orders = cached_response
        else:
            try:
                response = requests.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                orders = data['results']
                
                # Cache the response
                self.cache.set_api_response(self.base_url, params, orders)
                logger.info(f"Fetched and cached {len(orders)} executive orders")
                
            except Exception as e:
                logger.error(f"Failed to fetch executive orders: {e}")
                return pd.DataFrame()
        
        if not orders:
            logger.info(f"No new executive orders in last {days_back} days")
            return pd.DataFrame()
        
        # Ensure orders is a list of dicts
        if not isinstance(orders, list):
            logger.error(f"Expected list of orders, got {type(orders)}")
            return pd.DataFrame()
        
        # Process orders
        orders_data = []
        for order in orders:
            if not isinstance(order, dict):
                logger.warning(f"Skipping invalid order format: {type(order)}")
                continue
            # Download full text for analysis
            full_text = self._get_full_text(order.get('full_text_xml_url'))
            
            # Analyze commodity impact
            impact_analysis = self._analyze_commodity_impact(order, full_text)
            
            # Format text to include key details
            text_content = f"EO #{order.get('executive_order_number', 'N/A')}: {order.get('title', '')} - {order.get('abstract', '')}"[:500]
            
            orders_data.append({
                'source': 'federal_register_api',
                'category': 'executive_order',
                'text': text_content,
                'agricultural_impact': impact_analysis['agricultural_impact'],
                'soybean_relevance': impact_analysis['soybean_relevance'],
                'timestamp': pd.to_datetime(order['publication_date']),
                'priority': impact_analysis['priority']
            })
        
        df = pd.DataFrame(orders_data)
        
        # Alert on high-impact orders
        high_impact_orders = df[df['agricultural_impact'] > 0.7]
        if not high_impact_orders.empty:
            logger.warning(f"🚨 {len(high_impact_orders)} HIGH-IMPACT COMMODITY ORDERS DETECTED:")
            for _, order in high_impact_orders.iterrows():
                logger.warning(f"  - {order['text'][:100]}... (Impact: {order['agricultural_impact']:.2f})")
        
        return df
    
    def _get_full_text(self, full_text_url):
        """Download full text of executive order"""
        if not full_text_url:
            return ""
        
        try:
            # Check cache first
            cached_text = self.cache.get_api_response(full_text_url, None, ttl_hours=24)
            if cached_text:
                # Handle cached response format
                if isinstance(cached_text, dict) and 'data' in cached_text:
                    return cached_text['data']
                elif isinstance(cached_text, str):
                    return cached_text
                else:
                    return str(cached_text)
            
            response = requests.get(full_text_url, timeout=15)
            response.raise_for_status()
            
            full_text = response.text[:10000]  # Truncate for BigQuery
            
            # Cache the full text
            self.cache.set_api_response(full_text_url, None, full_text)
            
            return full_text
            
        except Exception as e:
            logger.warning(f"Failed to fetch full text from {full_text_url}: {e}")
            return ""
    
    def _analyze_commodity_impact(self, order, full_text):
        """
        Analyze executive order for commodity market impact
        
        Returns:
            Dict with impact scores and analysis
        """
        # Combine all text for analysis (handle None values)
        all_text = " ".join([
            order.get('title', '') or '',
            order.get('abstract', '') or '',
            full_text or ''
        ]).lower()
        
        # Count keyword occurrences
        commodity_score = sum(1 for kw in self.commodity_keywords if kw in all_text)
        high_impact_score = sum(1 for kw in self.high_impact_keywords if kw in all_text)
        tariff_keywords = sum(1 for kw in ['tariff', 'trade', 'duty'] if kw in all_text)
        
        # Calculate impact scores (0.0 to 1.0)
        agricultural_impact = min(commodity_score / 10.0, 1.0)
        soybean_relevance = min((commodity_score + high_impact_score) / 15.0, 1.0)
        
        # Determine priority
        if high_impact_score > 0 or tariff_keywords > 2:
            priority = 1  # Critical
        elif commodity_score > 3:
            priority = 2  # High
        elif commodity_score > 0:
            priority = 3  # Medium
        else:
            priority = 4  # Low
        
        return {
            'agricultural_impact': agricultural_impact,
            'soybean_relevance': soybean_relevance,
            'priority': priority,
            'tariff_keywords': tariff_keywords,
            'commodity_impact': commodity_score > 0
        }


def main():
    """Execute executive orders collection"""
    collector = ExecutiveOrdersCollector()
    
    print("=== TRUMP EXECUTIVE ORDERS INTELLIGENCE ===")
    print("Monitoring Federal Register for commodity-impacting orders")
    print("=" * 60)
    
    # Collect last 100 executive orders (expand date range)
    orders_df = collector.collect_executive_orders(days_back=365*2)  # 2 years to get 100+ orders
    
    if not orders_df.empty:
        print(f"✅ Collected {len(orders_df)} executive orders")
        
        # Show high-impact summary
        high_impact = orders_df[orders_df['agricultural_impact'] > 0.5]
        if not high_impact.empty:
            print(f"\n🚨 HIGH-IMPACT ORDERS ({len(high_impact)}):")
            for _, order in high_impact.iterrows():
                print(f"  - {order['text'][:80]}... (Impact: {order['agricultural_impact']:.2f})")
        
        # Show priority distribution
        priority_counts = orders_df['priority'].value_counts().sort_index()
        print(f"\n📊 PRIORITY DISTRIBUTION:")
        priority_labels = {1: 'Critical', 2: 'High', 3: 'Medium', 4: 'Low'}
        for priority, count in priority_counts.items():
            label = priority_labels.get(priority, f'Priority {priority}')
            print(f"  - {label}: {count} orders")
    
    else:
        print("No executive orders found in the specified period")
    
    print("✅ Executive orders intelligence collection completed")


if __name__ == "__main__":
    main()
