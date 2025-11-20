#!/usr/bin/env python3
"""
CBI-V14 Trump Policy Intelligence Historical Backfill
Priority 3: Fill 18-month gap in Trump policy intelligence data
Current: April 2025 to present (215 records)
Target: Back to October 2023 (18 additional months)
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from google.cloud import bigquery
import logging
import time
import json
import uuid
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"

class TrumpIntelligenceBackfillPipeline:
    """Historical backfill for Trump policy intelligence data"""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        import os
        from pathlib import Path
        import sys as _sys
        _sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        try:
            from src.utils.keychain_manager import get_api_key as _get_api
        except Exception:
            _get_api = None
        self.api_key = os.getenv('SCRAPECREATORS_API_KEY') or (_get_api('SCRAPECREATORS_API_KEY') if _get_api else None)
        if not self.api_key:
            raise RuntimeError("SCRAPECREATORS_API_KEY not set. Export or store in Keychain.")
        
        # Key agricultural/trade policy keywords
        self.agricultural_keywords = [
            'soybean', 'trade war', 'china tariff', 'agriculture', 'farm bill', 
            'biofuel', 'ethanol', 'biodiesel', 'export', 'import', 'usda',
            'farming', 'crop', 'harvest', 'grain', 'commodity'
        ]
        
        # Agricultural impact scoring
        self.impact_categories = {
            'high': ['trade war', 'china tariff', 'export ban', 'import restriction'],
            'medium': ['agriculture', 'farm bill', 'biofuel', 'usda'],
            'low': ['farming', 'crop', 'harvest', 'grain']
        }
    
    def fetch_historical_trump_posts(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch historical Trump posts for agricultural intelligence"""
        logger.info(f"🔍 Fetching Trump posts from {start_date} to {end_date}")
        
        all_posts = []
        
        try:
            # Use Scrape Creators API for historical Truth Social posts
            base_url = "https://api.scrapecreators.com/v1/truth-social/posts"
            
            # Get data in monthly chunks to avoid overloading API
            current_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
            
            while current_date < end_datetime:
                # Get one month at a time
                chunk_end = min(current_date + timedelta(days=30), end_datetime)
                
                params = {
                    'username': 'realDonaldTrump',
                    'start_date': current_date.strftime('%Y-%m-%d'),
                    'end_date': chunk_end.strftime('%Y-%m-%d'),
                    'limit': 100
                }
                
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
                
                logger.info(f"Fetching chunk: {params['start_date']} to {params['end_date']}")
                
                try:
                    response = requests.get(base_url, params=params, headers=headers, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if 'posts' in data and len(data['posts']) > 0:
                            chunk_posts = data['posts']
                            all_posts.extend(chunk_posts)
                            logger.info(f"✅ Retrieved {len(chunk_posts)} posts for {params['start_date']}")
                        else:
                            logger.info(f"📭 No posts found for {params['start_date']}")
                            
                    elif response.status_code == 401:
                        logger.error("🔐 API authentication failed - check API key")
                        break
                    elif response.status_code == 429:
                        logger.warning("⏳ Rate limited - waiting 60 seconds")
                        time.sleep(60)
                        continue
                    else:
                        logger.warning(f"API returned {response.status_code} for {params['start_date']}")
                
                except requests.exceptions.RequestException as e:
                    logger.error(f"Request error for {params['start_date']}: {str(e)}")
                
                # Rate limiting - be respectful to API
                time.sleep(2)
                current_date = chunk_end + timedelta(days=1)
            
            if all_posts:
                # Convert to DataFrame matching existing schema
                processed_posts = []
                
                for post in all_posts:
                    # Extract agricultural intelligence from post
                    post_text = post.get('text', '').lower()
                    
                    # Check for agricultural relevance
                    agricultural_score = self._calculate_agricultural_impact(post_text)
                    soybean_relevance = self._calculate_soybean_relevance(post_text)
                    
                    # Only include posts with agricultural relevance
                    if agricultural_score > 0.1 or soybean_relevance > 0.1:
                        processed_posts.append({
                            'source': 'truth_social_historical',
                            'category': self._categorize_post(post_text),
                            'text': post.get('text', '')[:1000],  # Limit text length
                            'agricultural_impact': float(agricultural_score),
                            'soybean_relevance': float(soybean_relevance),
                            'timestamp': pd.to_datetime(post.get('created_at')),
                            'priority': self._calculate_priority(agricultural_score, soybean_relevance),
                            'source_name': 'scrapecreators_historical_backfill',
                            'confidence_score': 0.8,  # High confidence for historical backfill
                            'ingest_timestamp_utc': datetime.now(),
                            'provenance_uuid': str(uuid.uuid4())
                        })
                
                if processed_posts:
                    df = pd.DataFrame(processed_posts)
                    logger.info(f"✅ Processed {len(df)} agriculturally relevant Trump posts")
                    return df
                else:
                    logger.warning("⚠️ No agriculturally relevant posts found in historical data")
                    return pd.DataFrame()
            else:
                logger.error("❌ No historical posts retrieved")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Critical error in Trump intelligence backfill: {str(e)}")
            return pd.DataFrame()
    
    def _calculate_agricultural_impact(self, text: str) -> float:
        """Calculate agricultural impact score from post text"""
        impact_score = 0.0
        
        for category, keywords in self.impact_categories.items():
            for keyword in keywords:
                if keyword in text:
                    if category == 'high':
                        impact_score += 0.4
                    elif category == 'medium':
                        impact_score += 0.2
                    elif category == 'low':
                        impact_score += 0.1
        
        return min(impact_score, 1.0)  # Cap at 1.0
    
    def _calculate_soybean_relevance(self, text: str) -> float:
        """Calculate specific soybean relevance from post text"""
        soybean_keywords = ['soybean', 'soy', 'bean', 'oilseed', 'crush', 'meal', 'oil']
        
        relevance = 0.0
        for keyword in soybean_keywords:
            if keyword in text:
                relevance += 0.2
        
        return min(relevance, 1.0)
    
    def _categorize_post(self, text: str) -> str:
        """Categorize post by primary topic"""
        if any(word in text for word in ['tariff', 'trade war', 'china']):
            return 'trade_policy'
        elif any(word in text for word in ['agriculture', 'farm', 'crop']):
            return 'agricultural_policy'
        elif any(word in text for word in ['biofuel', 'ethanol', 'energy']):
            return 'energy_policy'
        else:
            return 'general'
    
    def _calculate_priority(self, agricultural_impact: float, soybean_relevance: float) -> str:
        """Calculate priority level for the post"""
        combined_score = agricultural_impact + soybean_relevance
        
        if combined_score >= 0.8:
            return 'high'
        elif combined_score >= 0.4:
            return 'medium'
        else:
            return 'low'
    
    def store_trump_intelligence(self, df: pd.DataFrame) -> bool:
        """Store Trump intelligence data to BigQuery"""
        logger.info("💾 Storing Trump intelligence data to BigQuery...")
        
        try:
            table_id = f'{PROJECT_ID}.{DATASET_ID}.trump_policy_intelligence'
            
            # Check for duplicates based on timestamp
            if len(df) > 0:
                min_date = df['timestamp'].min().strftime('%Y-%m-%d')
                max_date = df['timestamp'].max().strftime('%Y-%m-%d')
                
                duplicate_check_query = f'''
                SELECT COUNT(*) as existing_count
                FROM `{table_id}`
                WHERE DATE(timestamp) BETWEEN '{min_date}' AND '{max_date}'
                AND source_name = 'scrapecreators_historical_backfill'
                '''
                
                existing_result = self.client.query(duplicate_check_query).to_dataframe()
                existing_count = existing_result['existing_count'].iloc[0]
                
                if existing_count > 0:
                    logger.warning(f"Found {existing_count} existing records - will append additional data")
            
            # Store to BigQuery
            job_config = bigquery.LoadJobConfig(
                write_disposition='WRITE_APPEND',
                autodetect=True
            )
            
            job = self.client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()
            
            if job.state == 'DONE':
                logger.info(f"✅ Successfully stored {len(df)} Trump intelligence records")
                return True
            else:
                logger.error("❌ BigQuery job failed for Trump intelligence data")
                return False
            
        except Exception as e:
            logger.error(f"Error storing Trump intelligence data: {str(e)}")
            return False
    
    def run_trump_intelligence_backfill(self) -> Dict[str, Any]:
        """Run Trump intelligence backfill for his PREVIOUS PRESIDENTIAL TERM"""
        logger.info("🇺🇸 Starting Trump policy intelligence backfill...")
        
        # CORRECTED: Truth Social launched Feb 2022, so backfill from launch to present
        # Target gap: Oct 2023 - Apr 2025 (18-month gap in existing data)
        # But we can backfill full history: Feb 2022 - Apr 2025 (when current data starts)
        start_date = '2022-02-15'  # Truth Social launch (Feb 2022)
        end_date = '2025-04-02'    # Day before current data starts (Apr 3, 2025)
        
        results = {
            'start_time': datetime.now().isoformat(),
            'date_range': f'{start_date} to {end_date}',
            'status': 'unknown',
            'records_processed': 0,
            'records_stored': 0,
            'agricultural_posts_found': 0
        }
        
        try:
            # Fetch historical Trump posts
            trump_data = self.fetch_historical_trump_posts(start_date, end_date)
            
            if not trump_data.empty:
                results['records_processed'] = len(trump_data)
                results['agricultural_posts_found'] = len(trump_data)
                
                # Store to BigQuery
                storage_success = self.store_trump_intelligence(trump_data)
                
                if storage_success:
                    results['status'] = 'success'
                    results['records_stored'] = len(trump_data)
                    logger.info(f"🎉 Trump intelligence backfill successful: {len(trump_data)} records")
                else:
                    results['status'] = 'storage_failed'
                    logger.error("❌ Trump intelligence storage failed")
            else:
                results['status'] = 'no_data'
                logger.warning("⚠️ No agricultural Trump posts found for historical period")
            
        except Exception as e:
            logger.error(f"Critical error in Trump intelligence backfill: {str(e)}")
            results['status'] = 'error'
        
        results['end_time'] = datetime.now().isoformat()
        return results

def main():
    """Run Trump intelligence historical backfill"""
    print("=" * 80)
    print("CBI-V14 TRUMP POLICY INTELLIGENCE BACKFILL")
    print("=" * 80)
    print("Target: Fill 18-month gap (Oct 2023 to Apr 2025)")
    print("Focus: Agricultural and trade policy impacts")
    print(f"Started: {datetime.now()}")
    print()
    
    pipeline = TrumpIntelligenceBackfillPipeline()
    results = pipeline.run_trump_intelligence_backfill()
    
    print("=" * 80)
    print("TRUMP INTELLIGENCE BACKFILL RESULTS")
    print("=" * 80)
    
    if results['status'] == 'success':
        print("🎉 SUCCESS: Trump intelligence backfill completed")
        print(f"📊 Records processed: {results['records_processed']:,}")
        print(f"💾 Records stored: {results['records_stored']:,}")
        print(f"📅 Date range: {results['date_range']}")
        print()
        print("✅ Trump policy intelligence now has 2+ year coverage")
        
    elif results['status'] == 'no_data':
        print("⚠️ NO DATA: No agricultural posts found in historical period")
        print("💡 This may indicate Trump was less active on agricultural topics pre-2025")
        
    elif results['status'] == 'storage_failed':
        print("💾❌ STORAGE FAILED: Data retrieved but storage failed")
        print(f"📊 Records processed: {results['records_processed']:,}")
        
    else:
        print("❌ FAILED: Trump intelligence backfill unsuccessful")
        print("🚨 Policy intelligence gap remains")
    
    print(f"Completed: {datetime.now()}")
    print("=" * 80)
    
    return results['status'] == 'success'

if __name__ == "__main__":
    success = main()
    
    # Save results
    with open(f"/Users/zincdigital/CBI-V14/logs/trump_intelligence_backfill_{datetime.now().strftime('%Y%m%d_%H%M')}.json", "w") as f:
        json.dump({'success': success, 'timestamp': datetime.now().isoformat()}, f, indent=2, default=str)
    
    exit(0 if success else 1)
