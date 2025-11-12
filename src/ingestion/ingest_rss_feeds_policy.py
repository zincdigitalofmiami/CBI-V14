#!/usr/bin/env python3
"""
CBI-V14 RSS Policy Feed Ingestion
Monitors EPA, Treasury, USTR, and ICE RSS feeds for policy intelligence
"""

import os
import requests
import feedparser
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timezone
import uuid
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"

class PolicyRSSCollector:
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        
        # RSS feed URLs
        self.feeds = {
            'epa': {
                'url': 'https://www.epa.gov/newsroom',  # Note: EPA may not have direct RSS
                'keywords': ['rfs', 'renewable', 'biofuel', 'biodiesel', 'mandate'],
                'table': 'staging.epa_policy_alerts'
            },
            'treasury': {
                'url': 'https://home.treasury.gov/rss',
                'keywords': ['china', 'sanction', 'trade', 'tariff'],
                'table': 'staging.treasury_policy_alerts'
            },
            'ustr': {
                'url': 'https://ustr.gov/about-us/policy-offices/press-office/press-releases/feed',
                'keywords': ['china', 'tariff', 'section 301', 'trade'],
                'table': 'staging.ustr_policy_alerts'
            },
            'ice': {
                'url': 'https://www.ice.gov/feeds/news.rss',
                'keywords': ['agricultural', 'farm', 'seasonal', 'worker', 'enforcement'],
                'table': 'staging.ice_enforcement_alerts'
            }
        }
        
    def fetch_rss_feed(self, feed_name: str, feed_config: Dict) -> List[Dict[str, Any]]:
        """Fetch and parse RSS feed"""
        alerts = []
        
        try:
            logger.info(f"Fetching {feed_name} RSS: {feed_config['url']}")
            feed = feedparser.parse(feed_config['url'])
            
            if feed.bozo:
                logger.warning(f"{feed_name} RSS parse warning: {feed.bozo_exception}")
            
            for entry in feed.entries[:10]:  # Last 10 entries
                try:
                    # Check relevance
                    content = f"{entry.get('title', '')} {entry.get('summary', '')}".lower()
                    
                    relevance_score = sum(1 for kw in feed_config['keywords'] if kw in content)
                    
                    if relevance_score > 0:
                        alert = {
                            'alert_date': datetime.now().date(),
                            'source_feed': feed_name,
                            'title': entry.get('title', ''),
                            'summary': entry.get('summary', '')[:500] if entry.get('summary') else '',
                            'link': entry.get('link', ''),
                            'published': entry.get('published', ''),
                            'relevance_score': relevance_score,
                            'source_name': f"{feed_name.upper()}_RSS",
                            'confidence_score': 0.85,  # RSS feeds are authoritative
                            'ingest_timestamp_utc': datetime.now(timezone.utc),
                            'provenance_uuid': str(uuid.uuid4())
                        }
                        alerts.append(alert)
                        logger.info(f"  ✓ {feed_name}: {entry.get('title', '')[:50]}...")
                        
                except Exception as e:
                    logger.warning(f"Entry parsing error: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ {feed_name} RSS fetch failed: {e}")
            
        return alerts
    
    def load_to_bigquery(self, feed_name: str, table_name: str, records: List[Dict[str, Any]]) -> bool:
        """Load RSS alerts to BigQuery"""
        if not records:
            logger.warning(f"No records to load for {feed_name}")
            return False
            
        try:
            df = pd.DataFrame(records)
            
            # Ensure proper data types
            df['alert_date'] = pd.to_datetime(df['alert_date']).dt.date
            df['relevance_score'] = pd.to_numeric(df['relevance_score'])
            df['confidence_score'] = pd.to_numeric(df['confidence_score'])
            df['ingest_timestamp_utc'] = pd.to_datetime(df['ingest_timestamp_utc'])
            
            # Create table if not exists
            schema = [
                bigquery.SchemaField("alert_date", "DATE"),
                bigquery.SchemaField("source_feed", "STRING"),
                bigquery.SchemaField("title", "STRING"),
                bigquery.SchemaField("summary", "STRING"),
                bigquery.SchemaField("link", "STRING"),
                bigquery.SchemaField("published", "STRING"),
                bigquery.SchemaField("relevance_score", "FLOAT"),
                bigquery.SchemaField("source_name", "STRING"),
                bigquery.SchemaField("confidence_score", "FLOAT"),
                bigquery.SchemaField("ingest_timestamp_utc", "TIMESTAMP"),
                bigquery.SchemaField("provenance_uuid", "STRING")
            ]
            
            table_id = f"{PROJECT_ID}.{table_name}"
            table = bigquery.Table(table_id, schema=schema)
            self.client.create_table(table, exists_ok=True)
            
            # Load data
            job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
            job = self.client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()
            
            logger.info(f"✅ Successfully loaded {len(records)} alerts to {table_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load {feed_name} data: {e}")
            return False
    
    def execute_complete_rss_collection(self) -> bool:
        """Execute all RSS feed collection"""
        logger.info("🚀 Starting policy RSS feed collection")
        
        success_count = 0
        total_alerts = 0
        
        for feed_name, feed_config in self.feeds.items():
            alerts = self.fetch_rss_feed(feed_name, feed_config)
            
            if alerts:
                success = self.load_to_bigquery(feed_name, feed_config['table'], alerts)
                if success:
                    success_count += 1
                    total_alerts += len(alerts)
        
        logger.info(f"✅ RSS collection complete: {success_count}/4 feeds successful, {total_alerts} total alerts")
        return success_count > 0

def main():
    """Main execution"""
    collector = PolicyRSSCollector()
    success = collector.execute_complete_rss_collection()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())



