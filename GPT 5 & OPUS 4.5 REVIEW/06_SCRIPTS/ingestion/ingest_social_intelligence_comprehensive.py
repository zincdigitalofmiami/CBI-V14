#!/usr/bin/env python3
"""
CBI-V14 Comprehensive Social Intelligence Ingestion
Processes scraped social media data and loads to BigQuery with proper signal scoring
"""

import os
import json
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timezone
import uuid
import logging
import glob
from typing import List, Dict, Any
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"

class ComprehensiveSocialIntelligenceProcessor:
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        
        # Keyword scoring weights for commodity relevance
        self.keyword_weights = {
            # Soy and crop terms (EN, PT, ES)
            'soy_keywords': [
                'soy', 'soybean', 'soybeans', 'soy oil', 'soyoil', 'oilseed', 'crush',
                'soja', 'oleaginosa', 'plantio', 'colheita', 'seca', 'geada',
                'soja aceite', 'cosecha', 'siembra', 'sequía', 'helada'
            ],
            # China/trade policy
            'china_keywords': [
                'china', 'tariff', 'tariffs', 'trade war', 'section 301', 'quota', 'trq',
                'cofco', 'sinograin', 'mofcom', 'gacc', 'beijing', 'xi jinping'
            ],
            # Legislative/policy
            'policy_keywords': [
                'congress', 'senate', 'house ag', 'regulation', 'policy', 'mandate', 'executive order', 'sanction'
            ],
            # Urgency language
            'urgency_keywords': ['today', 'now', 'immediate', 'urgent', 'breaking', 'alert'],
            # Biofuels cascade
            'biofuel_keywords': [
                'rfs', 'renewable fuel', 'biodiesel', 'ethanol', 'lcfs', 'hvo', 'hefa', 'saf', 'b35', 'b40'
            ],
            # Weather/logistics
            'weather_keywords': [
                'drought', 'harvest', 'weather', 'crop', 'yield', 'planting',
                'mississippi river', 'draft restriction', 'paraná river'
            ]
        }
        
        # Handle priority weights for institutional intelligence
        self.handle_priorities = {
            'realDonaldTrump': 1.0,
            'USTR': 0.9,
            'USTreasury': 0.9,
            'ICEgov': 0.8,
            'GACC_China': 0.9,
            'XinhuaNews': 0.8,
            'PDChina': 0.8,
            'EPA': 0.7,
            'USDA': 0.7,
            'CMEGroup': 0.8,
            'ASA_Soybeans': 0.7
        }
    
    def score_content_relevance(self, content: str, platform: str, handle: str = '') -> Dict:
        """Score content for soybean oil market relevance"""
        content_lower = content.lower()
        
        # Calculate keyword scores
        scores = {}
        for category, keywords in self.keyword_weights.items():
            scores[category] = sum(1 for kw in keywords if kw in content_lower)
        
        # Handle priority boost
        handle_boost = self.handle_priorities.get(handle, 0.5)
        
        # Platform weight
        platform_weights = {
            'twitter': 1.0,
            'truth_social': 1.2,  # Trump posts get higher weight
            'facebook': 0.8,
            'linkedin': 0.9,
            'youtube': 0.6,
            'reddit': 0.7,
            'tiktok': 0.5
        }
        platform_weight = platform_weights.get(platform, 0.5)
        
        # Total relevance score
        total_relevance = (
            scores['soy_keywords'] * 3 +      # Soy mentions highest weight
            scores['china_keywords'] * 2 +    # China mentions high weight
            scores['policy_keywords'] * 1.5 + # Policy mentions medium weight
            scores['urgency_keywords'] * 1 +  # Urgency mentions
            scores['biofuel_keywords'] * 2 +  # Biofuel mentions high weight
            scores['weather_keywords'] * 1.5  # Weather mentions medium weight
        ) * handle_boost * platform_weight
        
        return {
            'soy_score': scores['soy_keywords'],
            'china_score': scores['china_keywords'],
            'policy_score': scores['policy_keywords'],
            'urgency_score': scores['urgency_keywords'],
            'biofuel_score': scores['biofuel_keywords'],
            'weather_score': scores['weather_keywords'],
            'handle_boost': handle_boost,
            'platform_weight': platform_weight,
            'total_relevance': total_relevance
        }
    
    def process_twitter_data(self, data_dir: str) -> List[Dict[str, Any]]:
        """Process all Twitter JSON files"""
        twitter_records = []
        
        twitter_files = glob.glob(f"{data_dir}/twitter/*_tweets.json")
        logger.info(f"Processing {len(twitter_files)} Twitter files...")
        
        for file_path in twitter_files:
            try:
                handle = os.path.basename(file_path).replace('_tweets.json', '')
                
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # ScrapeCreators schema: top-level { success, credits_remaining, tweets: [...] }
                tweets = []
                if isinstance(data, dict) and 'tweets' in data and isinstance(data['tweets'], list):
                    tweets = data['tweets']
                elif isinstance(data, list):
                    tweets = data
                else:
                    logger.warning(f"  Unrecognized twitter JSON schema in {file_path}; skipping")
                    continue
                logger.info(f"  Processing @{handle}: {len(tweets)} tweets")
                
                for tweet in tweets:
                    # Content may be in legacy.full_text, full_text, or text
                    legacy = tweet.get('legacy', {}) if isinstance(tweet, dict) else {}
                    content = (
                        (legacy.get('full_text') if isinstance(legacy, dict) else None)
                        or tweet.get('full_text')
                        or tweet.get('text')
                        or ''
                    )
                    if not content:
                        continue
                    
                    # Score relevance
                    relevance = self.score_content_relevance(content, 'twitter', handle)
                    
                    # Keep relevant posts; also keep high-priority/influential posts even if keywords are sparse
                    keep_post = relevance['total_relevance'] > 0
                    if not keep_post:
                        # Metrics often live under legacy.{retweet_count, favorite_count, reply_count}
                        rt = (legacy.get('retweet_count') if isinstance(legacy, dict) else None) or tweet.get('retweet_count', 0)
                        fav = (legacy.get('favorite_count') if isinstance(legacy, dict) else None) or tweet.get('favorite_count', 0)
                        influence = (rt or 0) * 2 + (fav or 0)
                        high_priority = self.handle_priorities.get(handle, 0) >= 0.8
                        content_lower = content.lower()
                        weak_keyword = any(k in content_lower for k in ['soy', 'soja', 'tariff', 'rfs', 'biodiesel', 'soybean oil', 'soyoil'])
                        if high_priority and (influence > 0 or weak_keyword):
                            keep_post = True

                    if keep_post:
                        created_at = (
                            (legacy.get('created_at') if isinstance(legacy, dict) else None)
                            or tweet.get('created_at')
                            or ''
                        )
                        url = tweet.get('url') or ''
                        # Interaction metrics fallback
                        retweets = rt or 0
                        likes = fav or 0
                        replies = (legacy.get('reply_count') if isinstance(legacy, dict) else None) or tweet.get('reply_count', 0)
                        
                        record = {
                            'collection_date': datetime.now().date(),
                            'platform': 'twitter',
                            'handle': handle,
                            'content': content[:1000],  # Truncate for BigQuery
                            'created_at': created_at,
                            'retweets': retweets,
                            'likes': likes,
                            'replies': replies,
                            'soy_score': relevance['soy_score'],
                            'china_score': relevance['china_score'],
                            'policy_score': relevance['policy_score'],
                            'urgency_score': relevance['urgency_score'],
                            'biofuel_score': relevance['biofuel_score'],
                            'weather_score': relevance['weather_score'],
                            'total_relevance': relevance['total_relevance'],
                            'handle_priority': relevance['handle_boost'],
                            'influence_score': (retweets or 0) * 2 + (likes or 0),
                            'source_name': 'ScrapeCreators_Twitter',
                            'confidence_score': 0.8,
                            'ingest_timestamp_utc': datetime.now(timezone.utc),
                            'provenance_uuid': str(uuid.uuid4()),
                            'url': url
                        }
                        twitter_records.append(record)
                        
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                continue
        
        logger.info(f"✅ Twitter processing complete: {len(twitter_records)} relevant posts")
        return twitter_records
    
    def process_multi_platform_data(self, data_dir: str) -> Dict[str, List[Dict]]:
        """Process all platform data"""
        all_records = {
            'twitter': self.process_twitter_data(data_dir),
            'facebook': [],  # Will implement if Facebook data exists
            'linkedin': [],  # Will implement if LinkedIn data exists
            'youtube': [],   # Will implement if YouTube data exists
            'reddit': [],    # Will implement if Reddit data exists
            'tiktok': []     # Will implement if TikTok data exists
        }
        
        return all_records
    
    def load_to_bigquery(self, records: List[Dict[str, Any]], table_name: str) -> bool:
        """Load social intelligence to BigQuery"""
        if not records:
            logger.warning(f"No records to load for {table_name}")
            return False
            
        try:
            df = pd.DataFrame(records)
            
            # Ensure proper data types
            df['collection_date'] = pd.to_datetime(df['collection_date']).dt.date
            df['retweets'] = pd.to_numeric(df['retweets'], errors='coerce').fillna(0)
            df['likes'] = pd.to_numeric(df['likes'], errors='coerce').fillna(0)
            df['replies'] = pd.to_numeric(df['replies'], errors='coerce').fillna(0)
            df['soy_score'] = pd.to_numeric(df['soy_score'])
            df['china_score'] = pd.to_numeric(df['china_score'])
            df['policy_score'] = pd.to_numeric(df['policy_score'])
            df['urgency_score'] = pd.to_numeric(df['urgency_score'])
            df['biofuel_score'] = pd.to_numeric(df['biofuel_score'])
            df['weather_score'] = pd.to_numeric(df['weather_score'])
            df['total_relevance'] = pd.to_numeric(df['total_relevance'])
            df['handle_priority'] = pd.to_numeric(df['handle_priority'])
            df['influence_score'] = pd.to_numeric(df['influence_score'])
            df['confidence_score'] = pd.to_numeric(df['confidence_score'])
            df['ingest_timestamp_utc'] = pd.to_datetime(df['ingest_timestamp_utc'])
            
            # Create table schema
            schema = [
                bigquery.SchemaField("collection_date", "DATE"),
                bigquery.SchemaField("platform", "STRING"),
                bigquery.SchemaField("handle", "STRING"),
                bigquery.SchemaField("content", "STRING"),
                bigquery.SchemaField("created_at", "STRING"),
                bigquery.SchemaField("retweets", "FLOAT"),
                bigquery.SchemaField("likes", "FLOAT"),
                bigquery.SchemaField("replies", "FLOAT"),
                bigquery.SchemaField("soy_score", "FLOAT"),
                bigquery.SchemaField("china_score", "FLOAT"),
                bigquery.SchemaField("policy_score", "FLOAT"),
                bigquery.SchemaField("urgency_score", "FLOAT"),
                bigquery.SchemaField("biofuel_score", "FLOAT"),
                bigquery.SchemaField("weather_score", "FLOAT"),
                bigquery.SchemaField("total_relevance", "FLOAT"),
                bigquery.SchemaField("handle_priority", "FLOAT"),
                bigquery.SchemaField("influence_score", "FLOAT"),
                bigquery.SchemaField("source_name", "STRING"),
                bigquery.SchemaField("confidence_score", "FLOAT"),
                bigquery.SchemaField("ingest_timestamp_utc", "TIMESTAMP"),
                bigquery.SchemaField("provenance_uuid", "STRING"),
                bigquery.SchemaField("url", "STRING")
            ]
            
            table_id = f"{PROJECT_ID}.{table_name}"
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
            
            logger.info(f"✅ Successfully loaded {len(records)} records to {table_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load {table_name} data: {e}")
            return False
    
    def execute_comprehensive_ingestion(self, data_dir: str = "./data") -> bool:
        """Execute comprehensive social intelligence ingestion"""
        logger.info("🚀 Starting comprehensive social intelligence ingestion")
        
        # Process all platform data
        all_records = self.process_multi_platform_data(data_dir)
        
        success_count = 0
        total_records = 0
        
        # Load Twitter data
        if all_records['twitter']:
            success = self.load_to_bigquery(
                all_records['twitter'], 
                'staging.comprehensive_social_intelligence'
            )
            if success:
                success_count += 1
                total_records += len(all_records['twitter'])
        
        # Create signal processing views
        self.create_social_signal_views()
        
        logger.info("="*70)
        logger.info(f"✅ Comprehensive social intelligence ingestion complete")
        logger.info(f"Platforms processed: {success_count}")
        logger.info(f"Total relevant records: {total_records}")
        logger.info("="*70)
        
        return success_count > 0
    
    def create_social_signal_views(self):
        """Create BigQuery views for social signal processing"""
        logger.info("Creating social signal processing views...")
        
        # Social sentiment aggregates view
        social_sentiment_sql = """
        CREATE OR REPLACE VIEW `cbi-v14.signals.vw_social_sentiment_aggregates_daily` AS
        WITH daily_sentiment AS (
          SELECT 
            collection_date as date,
            platform,
            COUNT(*) as total_posts,
            AVG(total_relevance) as avg_relevance,
            SUM(soy_score) as daily_soy_mentions,
            SUM(china_score) as daily_china_mentions,
            SUM(policy_score) as daily_policy_mentions,
            SUM(urgency_score) as daily_urgency_signals,
            SUM(biofuel_score) as daily_biofuel_mentions,
            SUM(weather_score) as daily_weather_mentions,
            AVG(influence_score) as avg_influence,
            -- High-priority handle activity
            COUNT(CASE WHEN handle_priority >= 0.8 THEN 1 END) as high_priority_posts,
            -- Sentiment proxy (likes/retweets ratio)
            SAFE_DIVIDE(SUM(likes), SUM(retweets + 1)) as sentiment_proxy
          FROM `cbi-v14.staging.comprehensive_social_intelligence`
          WHERE collection_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
          GROUP BY collection_date, platform
        )
        SELECT 
          date,
          platform,
          total_posts,
          avg_relevance,
          daily_soy_mentions,
          daily_china_mentions,
          daily_policy_mentions,
          daily_urgency_signals,
          daily_biofuel_mentions,
          daily_weather_mentions,
          avg_influence,
          high_priority_posts,
          sentiment_proxy,
          -- Composite social signal (0-1 normalized)
          LEAST(1.0, GREATEST(0.0, 
            (daily_soy_mentions * 0.3 + 
             daily_china_mentions * 0.25 + 
             daily_policy_mentions * 0.2 + 
             daily_urgency_signals * 0.15 + 
             daily_biofuel_mentions * 0.1) / 10.0
          )) as social_signal_composite
        FROM daily_sentiment
        ORDER BY date DESC, platform;
        """
        
        try:
            job = self.client.query(social_sentiment_sql)
            job.result()
            logger.info("✅ Social sentiment aggregates view created")
        except Exception as e:
            logger.error(f"❌ Failed to create social sentiment view: {e}")
        
        # High-priority intelligence view
        priority_intel_sql = """
        CREATE OR REPLACE VIEW `cbi-v14.signals.vw_high_priority_social_intelligence` AS
        SELECT 
          collection_date as date,
          platform,
          handle,
          content,
          created_at,
          retweets,
          likes,
          total_relevance,
          handle_priority,
          influence_score,
          -- Market impact classification
          CASE 
            WHEN handle IN ('realDonaldTrump', 'USTR', 'USTreasury') AND urgency_score > 0 THEN 'IMMEDIATE_IMPACT'
            WHEN handle_priority >= 0.8 AND total_relevance >= 5 THEN 'HIGH_IMPACT'
            WHEN total_relevance >= 3 THEN 'MEDIUM_IMPACT'
            ELSE 'LOW_IMPACT'
          END as market_impact_classification,
          -- Signal category
          CASE 
            WHEN soy_score >= china_score AND soy_score >= policy_score THEN 'SOY_INTELLIGENCE'
            WHEN china_score >= policy_score THEN 'CHINA_INTELLIGENCE'
            WHEN policy_score > 0 THEN 'POLICY_INTELLIGENCE'
            WHEN biofuel_score > 0 THEN 'BIOFUEL_INTELLIGENCE'
            WHEN weather_score > 0 THEN 'WEATHER_INTELLIGENCE'
            ELSE 'GENERAL_INTELLIGENCE'
          END as signal_category,
          url,
          provenance_uuid
        FROM `cbi-v14.staging.comprehensive_social_intelligence`
        WHERE total_relevance > 0
          AND collection_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
        ORDER BY total_relevance DESC, influence_score DESC;
        """
        
        try:
            job = self.client.query(priority_intel_sql)
            job.result()
            logger.info("✅ High-priority social intelligence view created")
        except Exception as e:
            logger.error(f"❌ Failed to create priority intelligence view: {e}")

def main():
    """Main execution"""
    processor = ComprehensiveSocialIntelligenceProcessor()
    success = processor.execute_comprehensive_ingestion()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())


