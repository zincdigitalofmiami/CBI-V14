#!/usr/bin/env python3
"""
CBI-V14 ScrapeCreators Institutional Intelligence
Collects lobbying, congressional, analyst, and China state media intelligence
API Key: B1TOgQvMVSV6TDglqB8lJ2cirqi2
"""

import os
import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timezone
import uuid
import logging
import time
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"
SCRAPECREATORS_API_KEY = "B1TOgQvMVSV6TDglqB8lJ2cirqi2"
SCRAPECREATORS_BASE_URL = "https://api.scrapecreators.com"

class InstitutionalIntelligenceCollector:
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        self.headers = {
            "x-api-key": SCRAPECREATORS_API_KEY,
            "Content-Type": "application/json"
        }
        
        # Key Twitter handles for institutional intelligence
        self.twitter_handles = {
            'lobbying': ['CargillNews', 'ADMupdates', 'BungeInc', 'ASA_Soybeans'],
            'congressional': ['HouseAgGOP', 'SenStabenow', 'ChuckGrassley'],
            'analysts': ['GoldmanSachs', 'JPMorgan', 'AgResource'],
            'china_state': ['XinhuaNews', 'PDChina', 'globaltimesnews']
        }
        
    def fetch_twitter_user_posts(self, username: str, count: int = 10) -> List[Dict]:
        """Fetch posts from Twitter user via ScrapeCreators"""
        url = f"{SCRAPECREATORS_BASE_URL}/v1/twitter/user/posts"
        params = {
            "username": username,
            "count": count
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('posts', [])
            elif response.status_code == 404:
                logger.warning(f"User {username} not found or endpoint changed")
                return []
            else:
                logger.warning(f"ScrapeCreators API returned {response.status_code} for {username}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Failed to fetch {username}: {e}")
            return []
    
    def analyze_tweet_relevance(self, tweet_text: str, category: str) -> Dict:
        """Analyze tweet for soybean oil market relevance"""
        content = tweet_text.lower()
        
        # Keyword sets
        policy_keywords = ['congress', 'senate', 'bill', 'regulation', 'policy']
        china_keywords = ['china', 'tariff', 'trade war', 'beijing']
        soy_keywords = ['soybean', 'soy oil', 'oilseed', 'biodiesel', 'crush']
        urgency_keywords = ['today', 'immediate', 'urgent', 'breaking']
        
        relevance = {
            'policy_score': sum(1 for kw in policy_keywords if kw in content),
            'china_score': sum(1 for kw in china_keywords if kw in content),
            'soy_score': sum(1 for kw in soy_keywords if kw in content),
            'urgency_score': sum(1 for kw in urgency_keywords if kw in content),
            'total_relevance': 0
        }
        
        relevance['total_relevance'] = (
            relevance['policy_score'] +
            relevance['china_score'] * 2 +  # China mentions weighted higher
            relevance['soy_score'] * 3 +     # Soy mentions highest weight
            relevance['urgency_score']
        )
        
        return relevance
    
    def collect_category_intelligence(self, category: str) -> List[Dict[str, Any]]:
        """Collect intelligence for a specific category"""
        intelligence = []
        
        logger.info(f"Collecting {category} intelligence...")
        
        for username in self.twitter_handles.get(category, []):
            posts = self.fetch_twitter_user_posts(username, count=10)
            
            for post in posts:
                relevance = self.analyze_tweet_relevance(post.get('text', ''), category)
                
                # Only save relevant posts
                if relevance['total_relevance'] > 0:
                    intelligence.append({
                        'collection_date': datetime.now().date(),
                        'category': category,
                        'username': username,
                        'tweet_text': post.get('text', '')[:500],
                        'created_at': post.get('created_at', ''),
                        'retweets': post.get('retweet_count', 0),
                        'likes': post.get('favorite_count', 0),
                        'policy_score': relevance['policy_score'],
                        'china_score': relevance['china_score'],
                        'soy_score': relevance['soy_score'],
                        'total_relevance': relevance['total_relevance'],
                        'influence_score': post.get('retweet_count', 0) * 2 + post.get('favorite_count', 0),
                        'source_name': 'ScrapeCreators_Twitter',
                        'confidence_score': 0.75,
                        'ingest_timestamp_utc': datetime.now(timezone.utc),
                        'provenance_uuid': str(uuid.uuid4()),
                        'url': post.get('url', '')
                    })
            
            # Rate limiting - be respectful
            time.sleep(1)
        
        logger.info(f"  ✓ {category}: {len(intelligence)} relevant posts collected")
        return intelligence
    
    def load_to_bigquery(self, category: str, records: List[Dict[str, Any]]) -> bool:
        """Load institutional intelligence to BigQuery"""
        if not records:
            return False
            
        try:
            df = pd.DataFrame(records)
            
            # Ensure proper data types
            df['collection_date'] = pd.to_datetime(df['collection_date']).dt.date
            df['policy_score'] = pd.to_numeric(df['policy_score'])
            df['china_score'] = pd.to_numeric(df['china_score'])
            df['soy_score'] = pd.to_numeric(df['soy_score'])
            df['total_relevance'] = pd.to_numeric(df['total_relevance'])
            df['influence_score'] = pd.to_numeric(df['influence_score'])
            df['retweets'] = pd.to_numeric(df['retweets'])
            df['likes'] = pd.to_numeric(df['likes'])
            df['confidence_score'] = pd.to_numeric(df['confidence_score'])
            df['ingest_timestamp_utc'] = pd.to_datetime(df['ingest_timestamp_utc'])
            
            # Table mapping
            table_map = {
                'lobbying': 'staging.institutional_lobbying_intel',
                'congressional': 'staging.congressional_agriculture_intel',
                'analysts': 'staging.financial_analyst_intel',
                'china_state': 'staging.china_state_media_intel'
            }
            
            table_id = f"{PROJECT_ID}.{table_map.get(category, 'staging.institutional_intel')}"
            
            # Create table schema
            schema = [
                bigquery.SchemaField("collection_date", "DATE"),
                bigquery.SchemaField("category", "STRING"),
                bigquery.SchemaField("username", "STRING"),
                bigquery.SchemaField("tweet_text", "STRING"),
                bigquery.SchemaField("created_at", "STRING"),
                bigquery.SchemaField("retweets", "FLOAT"),
                bigquery.SchemaField("likes", "FLOAT"),
                bigquery.SchemaField("policy_score", "FLOAT"),
                bigquery.SchemaField("china_score", "FLOAT"),
                bigquery.SchemaField("soy_score", "FLOAT"),
                bigquery.SchemaField("total_relevance", "FLOAT"),
                bigquery.SchemaField("influence_score", "FLOAT"),
                bigquery.SchemaField("source_name", "STRING"),
                bigquery.SchemaField("confidence_score", "FLOAT"),
                bigquery.SchemaField("ingest_timestamp_utc", "TIMESTAMP"),
                bigquery.SchemaField("provenance_uuid", "STRING"),
                bigquery.SchemaField("url", "STRING")
            ]
            
            # Create table if not exists
            table = bigquery.Table(table_id, schema=schema)
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="collection_date"
            )
            self.client.create_table(table, exists_ok=True)
            
            # Load data
            job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
            job = self.client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()
            
            logger.info(f"✅ Successfully loaded {len(records)} {category} records to {table_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load {category} data: {e}")
            return False
    
    def execute_complete_collection(self) -> bool:
        """Execute complete institutional intelligence collection"""
        logger.info("🚀 Starting institutional intelligence collection via ScrapeCreators")
        logger.info(f"API Key: {SCRAPECREATORS_API_KEY[:10]}...")
        
        total_intelligence = 0
        success_categories = 0
        
        for category in ['lobbying', 'congressional', 'analysts', 'china_state']:
            intelligence = self.collect_category_intelligence(category)
            
            if intelligence:
                success = self.load_to_bigquery(category, intelligence)
                if success:
                    success_categories += 1
                    total_intelligence += len(intelligence)
        
        logger.info("="*60)
        logger.info(f"✅ Institutional intelligence complete: {success_categories}/4 categories")
        logger.info(f"Total intelligence signals collected: {total_intelligence}")
        logger.info("="*60)
        
        return success_categories > 0

def main():
    """Main execution"""
    collector = InstitutionalIntelligenceCollector()
    success = collector.execute_complete_collection()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())



