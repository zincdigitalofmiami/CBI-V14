#!/usr/bin/env python3
"""
Trump Truth Social Intelligence Monitor
Real-time monitoring of presidential posts for market impact
Uses Scrape Creators API for legal, compliant access

Scheduled: Every 4 hours (cron: 0 */4 * * *)
"""

import requests
import pandas as pd
from datetime import datetime, timezone
from google.cloud import bigquery
try:
    from google.cloud import secretmanager
except ImportError:
    secretmanager = None
import logging
import time
import uuid
from typing import List, Dict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/zincdigital/CBI-V14/logs/trump_social.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('trump_truth_social')

PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"


class TruthSocialMonitor:
    """Monitor Trump's Truth Social posts for agricultural/trade policy impacts"""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        self.api_key = self._get_api_key()
        
        # Agricultural/trade policy keywords
        self.agricultural_keywords = [
            'soybean', 'trade war', 'china tariff', 'agriculture', 'farm bill',
            'biofuel', 'ethanol', 'biodiesel', 'export', 'import', 'usda',
            'farming', 'crop', 'harvest', 'grain', 'commodity', 'farmer'
        ]
        
        # Impact scoring weights
        self.impact_weights = {
            'trade_war': 1.0,
            'china_tariff': 1.0,
            'export_ban': 0.9,
            'farm_bill': 0.7,
            'agriculture': 0.5,
            'biofuel': 0.6,
            'general': 0.3
        }
    
    def _get_api_key(self) -> str:
        """Fetch API key from Secret Manager (fallback to hardcoded for now)"""
        if secretmanager:
            try:
                # Try to get from Secret Manager
                secret_client = secretmanager.SecretManagerServiceClient()
                name = f"projects/{PROJECT_ID}/secrets/scrapecreators-api-key/versions/latest"
                response = secret_client.access_secret_version(request={"name": name})
                api_key = response.payload.data.decode("UTF-8")
                logger.info("✅ API key loaded from Secret Manager")
                return api_key
            except Exception as e:
                logger.warning(f"⚠️  Secret Manager failed: {e}, using fallback")
        # Fallback to hardcoded (will be migrated)
        import os
        from pathlib import Path
        import sys as _sys
        _sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        try:
            from src.utils.keychain_manager import get_api_key as _get_api
        except Exception:
            _get_api = None
        key = os.getenv('SCRAPECREATORS_API_KEY') or (_get_api('SCRAPECREATORS_API_KEY') if _get_api else None)
        if not key:
            raise RuntimeError("SCRAPECREATORS_API_KEY not set. Export or store in Keychain.")
        return key
    
    def fetch_recent_posts(self, hours_back: int = 4) -> List[Dict]:
        """Fetch Trump's Truth Social posts from last N hours"""
        logger.info(f"📱 Fetching Truth Social posts from last {hours_back} hours")
        
        try:
            # Scrape Creators API endpoint
            url = "https://api.scrapecreators.com/v1/truthsocial/user/posts"
            
            headers = {
                'x-api-key': self.api_key,
                'Content-Type': 'application/json'
            }
            
            params = {
                'handle': 'realDonaldTrump',  # Correct parameter name per API docs
                'count': 100  # Get recent posts
            }
            
            logger.info(f"🌐 API Request: {url}")
            logger.info(f"📋 Params: {params}")
            
            response = requests.get(url, headers=headers, params=params, timeout=60)
            logger.info(f"📡 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                posts = data.get('posts', [])
                
                # Filter to last N hours
                recent_posts = []
                cutoff_time = datetime.now(timezone.utc) - pd.Timedelta(hours=hours_back)
                
                for post in posts:
                    post_time = pd.to_datetime(post.get('created_at'))
                    if post_time >= cutoff_time:
                        recent_posts.append(post)
                
                logger.info(f"✅ Retrieved {len(recent_posts)} posts from last {hours_back} hours")
                return recent_posts
                
            elif response.status_code == 401:
                logger.error("🔐 API authentication failed - check API key")
                return []
            elif response.status_code == 429:
                logger.warning("⏳ Rate limited - will retry next cycle")
                return []
            else:
                logger.warning(f"API returned {response.status_code}: {response.text[:200]}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Failed to fetch Truth Social posts: {e}")
            return []
    
    def analyze_agricultural_impact(self, post_text: str) -> Dict:
        """Analyze post for agricultural/trade policy impact"""
        text_lower = post_text.lower()
        
        # Check for agricultural keywords
        agricultural_mentions = sum(1 for keyword in self.agricultural_keywords 
                                   if keyword in text_lower)
        
        # Categorize post
        category = 'general'
        impact_score = 0.0
        
        if any(word in text_lower for word in ['tariff', 'trade war', 'china']):
            category = 'trade_policy'
            impact_score = self.impact_weights['trade_war']
        elif any(word in text_lower for word in ['agriculture', 'farm', 'crop']):
            category = 'agricultural_policy'
            impact_score = self.impact_weights['agriculture']
        elif any(word in text_lower for word in ['biofuel', 'ethanol', 'energy']):
            category = 'energy_policy'
            impact_score = self.impact_weights['biofuel']
        else:
            impact_score = self.impact_weights['general']
        
        # Calculate soybean relevance
        soybean_keywords = ['soybean', 'soy', 'bean', 'oilseed']
        soybean_relevance = sum(1 for keyword in soybean_keywords if keyword in text_lower) * 0.25
        
        # Calculate overall agricultural impact
        agricultural_impact = min((agricultural_mentions * 0.1) + impact_score, 1.0)
        
        # Determine priority (INTEGER for schema compliance)
        combined_score = agricultural_impact + soybean_relevance
        if combined_score >= 0.8:
            priority = 3  # high
        elif combined_score >= 0.4:
            priority = 2  # medium
        else:
            priority = 1  # low
        
        return {
            'category': category,
            'agricultural_impact': agricultural_impact,
            'soybean_relevance': min(soybean_relevance, 1.0),
            'priority': priority,
            'agricultural_mentions': agricultural_mentions
        }
    
    def process_posts(self, posts: List[Dict]) -> List[Dict]:
        """Process posts for agricultural intelligence"""
        processed = []
        
        for post in posts:
            post_text = post.get('text', '')
            
            # Analyze impact
            analysis = self.analyze_agricultural_impact(post_text)
            
            # Only store agriculturally relevant posts
            if analysis['agricultural_impact'] > 0.1 or analysis['soybean_relevance'] > 0.1:
                record = {
                    'source': 'truth_social_monitor',
                    'category': analysis['category'],
                    'text': post_text[:1000],
                    'agricultural_impact': analysis['agricultural_impact'],
                    'soybean_relevance': analysis['soybean_relevance'],
                    'timestamp': pd.to_datetime(post.get('created_at')),
                    'priority': analysis['priority'],
                    'source_name': 'scrapecreators_truth_social',
                    'confidence_score': 0.85,
                    'ingest_timestamp_utc': datetime.now(timezone.utc),
                    'provenance_uuid': str(uuid.uuid4())
                }
                processed.append(record)
        
        logger.info(f"✅ Processed {len(processed)}/{len(posts)} agriculturally relevant posts")
        return processed
    
    def save_to_bigquery(self, records: List[Dict]) -> bool:
        """Save processed intelligence to BigQuery"""
        if not records:
            logger.warning("No records to save")
            return False
        
        try:
            df = pd.DataFrame(records)
            table_ref = f'{PROJECT_ID}.{DATASET_ID}.trump_policy_intelligence'
            
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND",
                autodetect=True
            )
            
            job = self.client.load_table_from_dataframe(df, table_ref, job_config=job_config)
            job.result()
            
            logger.info(f"✅ Saved {len(records)} Trump intelligence records to BigQuery")
            return True
            
        except Exception as e:
            logger.error(f"❌ BigQuery save failed: {e}")
            return False
    
    def run_monitoring_cycle(self) -> Dict:
        """Run complete monitoring cycle"""
        logger.info("=" * 80)
        logger.info("TRUMP TRUTH SOCIAL INTELLIGENCE MONITORING")
        logger.info("=" * 80)
        
        results = {
            'cycle_time': datetime.now(timezone.utc).isoformat(),
            'posts_fetched': 0,
            'posts_processed': 0,
            'records_saved': 0,
            'status': 'unknown'
        }
        
        try:
            # Fetch recent posts
            posts = self.fetch_recent_posts(hours_back=4)
            results['posts_fetched'] = len(posts)
            
            if not posts:
                logger.info("📭 No new posts in last 4 hours")
                results['status'] = 'no_new_posts'
                return results
            
            # Process for agricultural intelligence
            processed = self.process_posts(posts)
            results['posts_processed'] = len(processed)
            
            if not processed:
                logger.info("ℹ️  No agriculturally relevant posts found")
                results['status'] = 'no_relevant_posts'
                return results
            
            # Save to BigQuery
            success = self.save_to_bigquery(processed)
            
            if success:
                results['records_saved'] = len(processed)
                results['status'] = 'success'
                logger.info("=" * 80)
                logger.info(f"✅ MONITORING SUCCESS: {len(processed)} agricultural posts processed")
                logger.info("=" * 80)
            else:
                results['status'] = 'save_failed'
                logger.error("❌ BigQuery save failed")
            
        except Exception as e:
            logger.error(f"❌ Monitoring cycle failed: {e}")
            results['status'] = 'error'
        
        return results


def main():
    """Execute Truth Social monitoring"""
    monitor = TruthSocialMonitor()
    results = monitor.run_monitoring_cycle()
    
    logger.info(f"Cycle results: {results}")
    
    # Exit with appropriate code
    if results['status'] in ['success', 'no_new_posts', 'no_relevant_posts']:
        exit(0)
    else:
        exit(1)


if __name__ == "__main__":
    main()
